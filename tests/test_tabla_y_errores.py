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
        for lexema in ("x", "max_creditos", "8242", "7:00-8:30"):
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

    def test_solo_informacion_lexica(self):
        tabla = tabla_de('materia 8242 "Lenguajes";', "entero max = 18;")
        m = tabla.buscar("8242")
        self.assertEqual((m.tipo, m.categoria), (T.CODIGO_MATERIA, "materia"))
        self.assertEqual(tabla.buscar("max").categoria, "identificador")
        self.assertFalse(hasattr(m, "atributos"))

    def test_lexemas_con_error_no_se_instalan(self):
        tabla = TablaSimbolos()
        self.assertEqual(tabla.registrar(analizar_cadena("grupo 1IL14;")), 1)  # solo ';'
        self.assertIsNone(tabla.buscar("1IL14"))
        self.assertEqual(tabla.buscar("grupo").veces, 1)

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
        self.assertNotIn("Atributos", texto)
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

    def test_registra_errores_lexicos(self):
        m = self.procesar("grupo 1IL14;", "grupo 1IL142", "aula 3-1050 capacidad 40;")
        self.assertEqual([r.codigo for r in m.registros], ["E06", "E09"])
        self.assertEqual(m.lineas_con_error, [1, 3])
        self.assertTrue(all(r.categoria == "LEXICO" for r in m.registros))

    def test_varios_errores_en_una_linea(self):
        m = self.procesar("asignar LFAC-30 a 1IL14 con sam en 3-105 LU 7:00-8:30;")
        self.assertEqual([r.codigo for r in m.errores_de_linea(1)], ["E05", "E06"])

    def test_suscriptor_recibe_error_al_detectarse(self):
        m = ManejadorErrores()
        recibidos = []
        m.suscribir(lambda reg: recibidos.append((reg.codigo, m.total)))
        m.procesar(analizar_cadena("grupo 1IL14;", 1))
        self.assertEqual(recibidos, [("E06", 1)])

    def test_formato_con_indicador_de_columna(self):
        m = self.procesar("grupo 1IL14;")
        salida = m.formatear(m.registros[0])
        lineas = salida.splitlines()
        self.assertIn("E06", lineas[0])
        self.assertIn("grupo 1IL14;", salida)
        texto = next(l for l in lineas if "grupo 1IL14;" in l)
        marca = next(l for l in lineas if "^" in l)
        self.assertEqual(marca.index("^"), texto.index("1IL14"))
        self.assertEqual(marca.count("^"), len("1IL14"))
        self.assertIn("Sugerencia:", salida)

    def test_mensaje_explicito(self):
        m = self.procesar("grupo 1IL14;")
        salida = m.formatear(m.registros[0])
        for parte in ("Error léxico E06", "línea 1, columna 7", "Encontrado:  '1IL14'",
                      "Se esperaba: GRUPO [0-9][A-Z]{2}[0-9]{3}", "Recuperación:", "Sugerencia:"):
            self.assertIn(parte, salida)

    def test_resumen_cuenta_por_codigo(self):
        m = self.procesar("grupo 1IL14;", "grupo 1IL15;", "grupo SA;", "grupo 1IL142;")
        self.assertEqual(m.conteo_por_codigo(), {"E06": 2, "E08": 1})
        self.assertIn("3 error(es) léxico(s) en 3 de 4", m.resumen())

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
