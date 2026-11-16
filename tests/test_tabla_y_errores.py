import os
import unittest

from aula import (ManejadorErrores, TablaSimbolos, analizar_archivo,
                  analizar_cadena)
from aula import tokens as T

EJEMPLOS = os.path.join(os.path.dirname(__file__), "..", "ejemplos")


def tabla_de(*lineas):
    tabla = TablaSimbolos()
    for n, texto in enumerate(lineas, start=1):
        tabla.registrar(analizar_cadena(texto, n))
    return tabla


class TestTablaSimbolos(unittest.TestCase):
    def test_precarga_reservadas_y_dias(self):
        tabla = TablaSimbolos()
        self.assertEqual(len(tabla), len(T.PALABRAS_RESERVADAS) + len(T.DIAS))
        self.assertEqual(tabla.buscar("asignar").tipo, T.RESERVADA)
        self.assertEqual(tabla.buscar("LU").tipo, T.DIA)
        self.assertEqual(tabla.simbolos_usados(), [])

    def test_hash_determinista_y_en_rango(self):
        tabla = TablaSimbolos()
        self.assertEqual(TablaSimbolos.hash("abc"), TablaSimbolos.hash("abc"))
        self.assertNotEqual(TablaSimbolos.hash("abc"), TablaSimbolos.hash("acb"))
        for lexema in ("x", "max_creditos", "LFAC-301", "7:00-8:30"):
            self.assertTrue(0 <= tabla.indice(lexema) < tabla.capacidad)

    def test_ocurrencias_y_primera_aparicion(self):
        tabla = tabla_de("entero x = 1;", "x = 2;", "mostrar x;")
        x = tabla.buscar("x")
        self.assertEqual(x.veces, 3)
        self.assertEqual((x.linea, x.columna), (1, 8))
        self.assertEqual([o[0] for o in x.ocurrencias], [1, 2, 3])

    def test_no_duplica_simbolos(self):
        tabla = tabla_de("entero x = 1;", "entero z = 1;")
        self.assertEqual(tabla.buscar("1").veces, 2)
        self.assertEqual(sum(1 for s in tabla if s.lexema == "1"), 1)

    def test_atributos_declaracion_variable(self):
        tabla = tabla_de("entero max = 18;", "texto saludo = \"Hola\";",
                         "logico ok = verdadero;")
        self.assertEqual(tabla.buscar("max").atributos["tipo_dato"], "entero")
        self.assertEqual(tabla.buscar("max").atributos["valor"], 18)
        self.assertEqual(tabla.buscar("max").categoria, "variable")
        self.assertEqual(tabla.buscar("saludo").atributos["valor"], "Hola")
        self.assertIs(tabla.buscar("ok").atributos["valor"], True)

    def test_asignacion_actualiza_valor(self):
        tabla = tabla_de("entero x = 1;", "x = 5;")
        self.assertEqual(tabla.buscar("x").atributos["valor"], 5)

    def test_atributos_entidades(self):
        tabla = tabla_de('materia LFAC-301 "Lenguajes" creditos 4;',
                         'profesor sam "Nicolas";', "aula 3-105 capacidad 40;",
                         "grupo 1IL142;")
        m = tabla.buscar("LFAC-301")
        self.assertEqual((m.categoria, m.atributos["nombre"], m.atributos["creditos"]),
                         ("materia", "Lenguajes", 4))
        self.assertEqual(tabla.buscar("sam").categoria, "profesor")
        self.assertEqual(tabla.buscar("3-105").atributos["capacidad"], 40)
        self.assertTrue(tabla.buscar("1IL142").atributos["declarado"])

    def test_redeclaracion(self):
        tabla = tabla_de("entero x = 1;", "entero x = 2;")
        self.assertEqual(tabla.buscar("x").atributos["redeclaraciones"], 1)

    def test_lineas_invalidas_no_se_instalan(self):
        tabla = TablaSimbolos()
        self.assertEqual(tabla.registrar(analizar_cadena("grupo 1IL14;")), 0)
        self.assertEqual(tabla.registrar(analizar_cadena("entero Total = 5;")), 0)
        self.assertIsNone(tabla.buscar("1IL14"))
        self.assertEqual(tabla.simbolos_usados(), [])

    def test_literales_con_valor(self):
        tabla = tabla_de("real r = 71.5;", "hora h = 7:30;")
        self.assertEqual(tabla.buscar("71.5").atributos["valor"], 71.5)
        self.assertEqual(tabla.buscar("7:30").atributos["valor"], "7:30")

    def test_redimensiona_y_conserva_simbolos(self):
        tabla = TablaSimbolos(capacidad=5, precargar=False)
        lexemas = [f"v{i}" for i in range(100)]
        for i, lexema in enumerate(lexemas):
            tabla.instalar(T.Token(lexema, T.IDENTIFICADOR, 1, i + 1))
        self.assertEqual(len(tabla), 100)
        self.assertGreater(tabla.redimensiones, 0)
        self.assertLessEqual(tabla.factor_carga, 0.75)
        for lexema in lexemas:
            self.assertIsNotNone(tabla.buscar(lexema))

    def test_colisiones_se_encadenan(self):
        tabla = TablaSimbolos(capacidad=3, precargar=False)
        for i, lexema in enumerate(["a", "b", "c"]):
            tabla.instalar(T.Token(lexema, T.IDENTIFICADOR, 1, i + 1))
        for lexema in ("a", "b", "c"):
            self.assertEqual(tabla.buscar(lexema).lexema, lexema)

    def test_formatear(self):
        tabla = tabla_de("entero max = 18;")
        texto = tabla.formatear()
        self.assertIn("max", texto)
        self.assertIn("tipo_dato='entero'", texto)
        self.assertNotIn("asignar", texto)
        self.assertIn("asignar", tabla.formatear(incluir_no_usados=True))

    def test_archivo_valido_completo(self):
        tabla = TablaSimbolos()
        for r in analizar_archivo(os.path.join(EJEMPLOS, "horario_valido.txt")):
            tabla.registrar(r)
        self.assertGreater(len(tabla.simbolos_usados()), 10)


class TestManejadorErrores(unittest.TestCase):
    def procesar(self, *lineas):
        manejador = ManejadorErrores()
        for n, texto in enumerate(lineas, start=1):
            manejador.procesar(analizar_cadena(texto, n))
        return manejador

    def test_sin_errores(self):
        m = self.procesar("grupo 1IL142;")
        self.assertFalse(m.hay_errores)
        self.assertIn("Sin errores", m.resumen())

    def test_registra_lexicos_y_sintacticos(self):
        m = self.procesar("grupo 1IL14;", "grupo 1IL142")
        self.assertEqual([r.codigo for r in m.registros], ["E07", "S03"])
        self.assertEqual(m.lineas_con_error, [1, 2])
        self.assertEqual(len(m.por_categoria("LEXICO")), 1)
        self.assertEqual(len(m.por_categoria("SINTACTICO")), 1)

    def test_varios_errores_en_una_linea(self):
        m = self.procesar("asignar LFAC-30 a 1IL14 con sam en 3-105 LU 7:00-8:30;")
        self.assertEqual([r.codigo for r in m.errores_de_linea(1)], ["E06", "E07"])

    def test_suscriptor_recibe_error_al_detectarse(self):
        m = ManejadorErrores()
        recibidos = []
        m.suscribir(lambda reg: recibidos.append((reg.codigo, m.total)))
        m.procesar(analizar_cadena("grupo 1IL14;", 1))
        self.assertEqual(recibidos, [("E07", 1)])

    def test_formato_con_indicador_de_columna(self):
        m = self.procesar("grupo 1IL14;")
        salida = m.formatear(m.registros[0])
        lineas = salida.splitlines()
        self.assertIn("[E07]", lineas[0])
        self.assertIn("grupo 1IL14;", salida)
        texto = next(l for l in lineas if "grupo 1IL14;" in l)
        marca = next(l for l in lineas if "^" in l)
        self.assertEqual(marca.index("^"), texto.index("1IL14"))
        self.assertEqual(marca.count("^"), len("1IL14"))
        self.assertIn("Sugerencia:", salida)

    def test_falta_punto_y_coma_apunta_al_final(self):
        m = self.procesar("grupo 1IL142")
        reg = m.registros[0]
        self.assertEqual(reg.codigo, "S03")
        self.assertEqual(reg.columna, len("grupo 1IL142") + 1)
        self.assertEqual(m.formatear(reg).splitlines()[-2].index("^"),
                         m.formatear(reg).splitlines()[-3].index("1IL142") + len("1IL142"))

    def test_resumen_cuenta_por_codigo(self):
        m = self.procesar("grupo 1IL14;", "grupo 1IL15;", "grupo 1IL142", "grupo 1IL142;")
        self.assertEqual(m.conteo_por_codigo(), {"E07": 2, "S03": 1})
        self.assertIn("3 error(es) en 3 de 4", m.resumen())

    def test_codigo_desconocido(self):
        from aula import Error
        with self.assertRaises(ValueError):
            ManejadorErrores().reportar(Error("X99", "?", 1, 1))

    def test_todos_los_codigos_tienen_sugerencia(self):
        from aula import ERRORES
        from aula.manejador_errores import SUGERENCIAS
        self.assertEqual(set(SUGERENCIAS), set(ERRORES))

    def test_archivo_de_errores(self):
        m = ManejadorErrores()
        for r in analizar_archivo(os.path.join(EJEMPLOS, "horario_errores.txt")):
            m.procesar(r)
        self.assertTrue(m.hay_errores)
        self.assertEqual(m.lineas_analizadas, len(m.lineas_con_error))


if __name__ == "__main__":
    unittest.main()
