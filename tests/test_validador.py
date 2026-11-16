import os
import tempfile
import unittest

from aula import analizar_archivo, analizar_cadena
from aula import tokens as T

EJEMPLOS = os.path.join(os.path.dirname(__file__), "..", "ejemplos")


def codigos(texto):
    return [e.codigo for e in analizar_cadena(texto).errores]


class TestLexico(unittest.TestCase):
    def test_tokens_de_asignacion(self):
        r = analizar_cadena("asignar 8242 a 1IL142 con samaniego en 3-105 LU 7:00-8:30;")
        self.assertTrue(r.valida)
        self.assertEqual([t.tipo for t in r.tokens], [
            T.RESERVADA, T.CODIGO_MATERIA, T.RESERVADA, T.GRUPO, T.RESERVADA,
            T.IDENTIFICADOR, T.RESERVADA, T.AULA, T.DIA, T.RANGO_HORA, T.DELIMITADOR])

    def test_posiciones(self):
        r = analizar_cadena("grupo 1IL142;", numero=7)
        self.assertEqual([(t.linea, t.columna) for t in r.tokens], [(7, 1), (7, 7), (7, 13)])

    def test_sin_espacios_entre_operadores(self):
        r = analizar_cadena("si x>=5 entonces mostrar x;")
        self.assertTrue(r.valida)
        self.assertEqual(r.tokens[2].lexema, ">=")

    def test_comentario_al_final(self):
        r = analizar_cadena("grupo 1IL142; # grupo de la mañana")
        self.assertTrue(r.valida)
        self.assertEqual(len(r.tokens), 3)

    def test_errores_lexicos(self):
        casos = {
            "aula 3-105 capacidad $40;": "E01",
            'texto t = "Hola;': "E02",
            "real n = 71.;": "E03",
            "hora h = 25:70;": "E04",
            "materia LFAC-301 \"X\" ;": "E05",
            "grupo 1IL14;": "E06",
            "entero 9creditos = 1;": "E07",
            "entero Total = 1;": "E07",
            "asignar 8242 a 1IL142 con s en 3-105 SA 7:00-8:30;": "E08",
            "aula 3-1050 capacidad 40;": "E09",
            "entero " + "a" * 32 + " = 1;": "E10",
        }
        for texto, esperado in casos.items():
            self.assertEqual(codigos(texto), [esperado], texto)

    def test_varios_errores_en_una_linea(self):
        self.assertEqual(codigos("asignar LFAC-30 a 1IL14 con s en 3-105 SA 7:00-8:30;"),
                         ["E05", "E06", "E08"])

    def test_errores_informan_esperado_y_recuperacion(self):
        e = analizar_cadena("grupo 1IL14;").errores[0]
        self.assertIn("[0-9][A-Z]{2}[0-9]{3}", e.esperado)
        self.assertIn("columna 12", e.recuperacion)

    def test_recupera_y_sigue_reconociendo(self):
        r = analizar_cadena("grupo 1IL14 1IL142;")
        self.assertEqual([t.lexema for t in r.tokens], ["grupo", "1IL142", ";"])


class TestCodigoMateria(unittest.TestCase):
    def test_cuatro_digitos_es_codigo(self):
        tipos = [t.tipo for t in analizar_cadena("materia 8242 \"Lenguajes\";").tokens]
        self.assertEqual(tipos[1], T.CODIGO_MATERIA)

    def test_otros_largos_son_enteros(self):
        for n in ("40", "824", "82420"):
            self.assertEqual(analizar_cadena(n).tokens[0].tipo, T.ENTERO, n)

    def test_formato_viejo_es_error(self):
        self.assertEqual(codigos("materia LFAC-301 \"X\";"), ["E05"])


class TestSoloLexico(unittest.TestCase):
    """El analizador no revisa sintaxis ni semántica."""

    def test_orden_de_tokens_no_se_valida(self):
        for texto in ("capacidad 40;", "grupo 1IL142", "; grupo grupo",
                      "asignar 8242 a 1IL142 con s en 3-105 7:00-8:30 LU;",
                      "si max >> 18 entonces mostrar x;"):
            self.assertTrue(analizar_cadena(texto).valida, texto)

    def test_valores_no_se_validan(self):
        self.assertTrue(analizar_cadena("entero max = \"dieciocho\";").valida)
        r = analizar_cadena("asignar 8242 a 1IL142 con s en 3-105 LU 9:00-7:00;")
        self.assertTrue(r.valida)
        self.assertEqual(r.tokens[-2].tipo, T.RANGO_HORA)

    def test_resultado_sin_sentencia(self):
        self.assertFalse(hasattr(analizar_cadena("grupo 1IL142;"), "sentencia"))


class TestArchivos(unittest.TestCase):
    def test_archivo_valido(self):
        resultados = list(analizar_archivo(os.path.join(EJEMPLOS, "horario_valido.txt")))
        self.assertTrue(resultados)
        self.assertTrue(all(r.valida for r in resultados),
                        [str(e) for r in resultados for e in r.errores])

    def test_archivo_con_errores(self):
        resultados = list(analizar_archivo(os.path.join(EJEMPLOS, "horario_errores.txt")))
        self.assertTrue(resultados)
        self.assertTrue(all(not r.valida for r in resultados))

    def test_omite_vacias_y_comentarios(self):
        from aula import analizar_lineas
        resultados = list(analizar_lineas(["", "  # nota", "grupo 1IL142;"]))
        self.assertEqual([r.numero for r in resultados], [3])


class TestUbicacionErrores(unittest.TestCase):
    def test_e01_senala_el_caracter(self):
        e = analizar_cadena('profesor samañego "Nicolas";').errores[0]
        self.assertEqual((e.codigo, e.columna, e.lexema), ("E01", 14, "ñ"))


class TestCodificacion(unittest.TestCase):
    def analizar_bytes(self, datos):
        with tempfile.NamedTemporaryFile("wb", suffix=".txt", delete=False) as f:
            f.write(datos)
        self.addCleanup(os.remove, f.name)
        return list(analizar_archivo(f.name))

    def test_utf8_con_bom(self):
        r = self.analizar_bytes("\ufeffgrupo 1IL142;\n".encode("utf-8"))
        self.assertTrue(r[0].valida, r[0].errores)

    def test_ansi_windows(self):
        r = self.analizar_bytes('profesor samaniego "Nicolás Samaniego";\r\n'.encode("cp1252"))
        self.assertTrue(r[0].valida, r[0].errores)
        self.assertEqual(r[0].tokens[2].lexema, '"Nicolás Samaniego"')

    def test_saltos_de_linea_mixtos(self):
        r = self.analizar_bytes(b"grupo 1IL142;\r\n\r\ngrupo 1IL143;\rgrupo 2IL101;\n")
        self.assertEqual([x.numero for x in r], [1, 3, 4])
        self.assertTrue(all(x.valida for x in r))


if __name__ == "__main__":
    unittest.main()
