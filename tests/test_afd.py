import string
import unittest

from aula import automatas as A


class TestAFD(unittest.TestCase):
    def comprobar(self, afd, aceptadas, rechazadas):
        for cadena in aceptadas:
            self.assertTrue(afd.acepta(cadena), f"{afd.nombre} debería aceptar {cadena!r}")
        for cadena in rechazadas:
            self.assertFalse(afd.acepta(cadena), f"{afd.nombre} debería rechazar {cadena!r}")

    def test_identificador(self):
        self.comprobar(A.IDENTIFICADOR, ["x", "max_creditos", "_tmp", "nota2", "aB9"],
                       ["", "9x", "Total", "max-c", "a.b"])

    def test_palabra_mayusculas(self):
        self.comprobar(A.PALABRA_MAYUS, ["LU", "VI", "SA", "LFAC"], ["", "Lu", "L1"])

    def test_codigo_materia(self):
        self.comprobar(A.CODIGO_MATERIA, ["SO-302", "LFAC-301", "BDA-100"],
                       ["S-302", "LFACX-301", "LFAC-30", "LFAC-3010", "LFAC301", "lfac-301"])

    def test_grupo(self):
        self.comprobar(A.GRUPO, ["1IL142", "2IS131"], ["1IL14", "1I142", "IL142", "1IL1420"])

    def test_aula(self):
        self.comprobar(A.AULA, ["3-105", "12-201"], ["123-105", "3-10", "3-1050", "3105"])

    def test_hora(self):
        self.comprobar(A.HORA, ["0:00", "7:00", "07:30", "19:59", "23:59"],
                       ["24:00", "25:70", "7:60", "7:5", "123:00", "7"])

    def test_rango_hora(self):
        self.comprobar(A.RANGO_HORA, ["7:00-8:30", "13:00-14:45"],
                       ["7:00", "7:00-", "7:00-24:00", "7:00-8:3"])

    def test_numeros(self):
        self.comprobar(A.ENTERO, ["0", "18", "2026"], ["", "1.5", "-3"])
        self.comprobar(A.REAL, ["71.5", "0.0", "100.25"], ["71.", ".5", "71", "1.2.3"])

    def test_cadena(self):
        self.comprobar(A.CADENA, ['""', '"Hola"', '"Lógica y Autómatas"'],
                       ['"Hola', 'Hola"', '"a"b"'])

    def test_operadores(self):
        self.comprobar(A.OP_RELACIONAL, ["==", "!=", "<", "<=", ">", ">="], ["=", "!", "=>"])
        self.comprobar(A.ASIGNACION, ["="], ["=="])
        self.comprobar(A.DELIMITADOR, [";"], [";;"])

    def test_coincidencia_mas_larga(self):
        self.assertEqual(A.RANGO_HORA.reconocer("7:00-8:30;"), 9)
        self.assertEqual(A.HORA.reconocer("7:00-8:30;"), 4)
        self.assertEqual(A.OP_RELACIONAL.reconocer(">=5"), 2)

    def test_deterministas(self):
        """En cada estado ningún carácter puede activar dos transiciones."""
        muestra = string.printable + "ñáéíóúΣ"
        for afd in A.TODOS:
            for estado, salidas in afd.transiciones.items():
                for c in muestra:
                    activas = [d for clase, d in salidas if c in clase]
                    self.assertLessEqual(len(activas), 1, f"{afd.nombre}: δ({estado}, {c!r})")


if __name__ == "__main__":
    unittest.main()
