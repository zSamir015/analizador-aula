import os
import unittest

from aula import analizar_archivo, analizar_cadena
from aula import tokens as T

EJEMPLOS = os.path.join(os.path.dirname(__file__), "..", "ejemplos")


def codigos(texto):
    return [e.codigo for e in analizar_cadena(texto).errores]


class TestLexico(unittest.TestCase):
    def test_tokens_de_asignacion(self):
        r = analizar_cadena("asignar LFAC-301 a 1IL142 con samaniego en 3-105 LU 7:00-8:30;")
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
            "asignar LFAC-301 a 1IL142 con s en 3-105 LU 9:00-7:00;": "E05",
            "materia LFAC-30 \"X\" creditos 4;": "E06",
            "grupo 1IL14;": "E07",
            "entero 9creditos = 1;": "E08",
            "entero Total = 1;": "E08",
            "asignar LFAC-301 a 1IL142 con s en 3-105 SA 7:00-8:30;": "E09",
            "aula 3-1050 capacidad 40;": "E10",
            "entero " + "a" * 32 + " = 1;": "E11",
        }
        for texto, esperado in casos.items():
            self.assertEqual(codigos(texto), [esperado], texto)

    def test_varios_errores_en_una_linea(self):
        self.assertEqual(codigos("asignar LFAC-30 a 1IL14 con s en 3-105 SA 7:00-8:30;"),
                         ["E06", "E07", "E09"])


class TestSintaxis(unittest.TestCase):
    def test_sentencias_validas(self):
        casos = {
            "entero max_creditos = 18;": "S1",
            "real nota = 71;": "S1",
            "logico ok = verdadero;": "S1",
            "hora h = 7:00;": "S1",
            'materia LFAC-301 "Lenguajes" creditos 4;': "S2",
            'profesor samaniego "Nicolas Samaniego";': "S3",
            "aula 3-105 capacidad 40;": "S4",
            "grupo 1IL142;": "S5",
            "asignar LFAC-301 a 1IL142 con samaniego en 3-105 LU 7:00-8:30;": "S6",
            "eliminar LFAC-301 de 1IL142;": "S7",
            "verificar choque 1IL142;": "S8",
            "mostrar horario de 1IL142;": "S9",
            'mostrar "Hola";': "S9",
            'si x > 18 y y_ok == verdadero o h < 7:00 entonces mostrar "Aviso";': "S10",
            "creditos_grupo = 8;": "S11",
        }
        for texto, esperado in casos.items():
            r = analizar_cadena(texto)
            self.assertTrue(r.valida, f"{texto}: {[str(e) for e in r.errores]}")
            self.assertEqual(r.sentencia, esperado, texto)

    def test_errores_sintacticos(self):
        casos = {
            "capacidad 40;": "S01",
            "18;": "S01",
            "materia LFAC-301 creditos 4;": "S02",
            'entero max = "dieciocho";': "S02",
            "asignar LFAC-301 a 1IL142 con samaniego en 3-105 7:00-8:30 LU;": "S02",
            "mostrar horario 1IL142;": "S02",
            "verificar choque": "S02",
            "grupo 1IL142": "S03",
            "grupo 1IL142; grupo 1IL143;": "S04",
        }
        for texto, esperado in casos.items():
            self.assertEqual(codigos(texto), [esperado], texto)

    def test_error_lexico_omite_sintaxis(self):
        self.assertEqual(codigos("grupo 1IL14"), ["E07"])


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


if __name__ == "__main__":
    unittest.main()
