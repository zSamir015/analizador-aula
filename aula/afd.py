"""Autómata finito determinista (AFD) definido por tabla de transiciones.

Para que las tablas sean legibles, el alfabeto se agrupa en clases de
caracteres ("0-9", "A-Z", ":", ...). En cada estado las clases usadas son
disjuntas, por lo que el autómata sigue siendo determinista.
"""

import string


class ClaseCaracter:
    def __init__(self, etiqueta, caracteres=None, excluidos=None):
        self.etiqueta = etiqueta
        self.caracteres = frozenset(caracteres) if caracteres is not None else None
        self.excluidos = frozenset(excluidos or ())

    def __contains__(self, c):
        if self.caracteres is not None:
            return c in self.caracteres
        return c not in self.excluidos  # clase "todo excepto ..."

    def __repr__(self):
        return self.etiqueta


def _clase(caracteres):
    return ClaseCaracter(caracteres, caracteres)


CLASES = {
    "0-9": ClaseCaracter("0-9", string.digits),
    "0-1": ClaseCaracter("0-1", "01"),
    "0-3": ClaseCaracter("0-3", "0123"),
    "0-5": ClaseCaracter("0-5", "012345"),
    "3-9": ClaseCaracter("3-9", "3456789"),
    "A-Z": ClaseCaracter("A-Z", string.ascii_uppercase),
    "a-z": ClaseCaracter("a-z", string.ascii_lowercase),
    "Σ-{\"}": ClaseCaracter("Σ-{\"}", excluidos='"\n'),
    "Σ": ClaseCaracter("Σ", excluidos="\n"),
}
for _c in '2_:-.;=<>!"#':
    CLASES[_c] = _clase(_c)


class AFD:
    """M = (Q, Σ, δ, q0, F).

    transiciones: {estado: [(etiqueta_clase, estado_destino), ...]}
    """

    def __init__(self, nombre, tipo, expresion, estados, inicial, finales,
                 transiciones):
        self.nombre = nombre
        self.tipo = tipo
        self.expresion = expresion
        self.estados = list(estados)
        self.inicial = inicial
        self.finales = frozenset(finales)
        self.transiciones = {
            q: [(CLASES[etq], destino) for etq, destino in salidas]
            for q, salidas in transiciones.items()
        }
        self._validar()

    def _validar(self):
        if self.inicial not in self.estados:
            raise ValueError(f"{self.nombre}: estado inicial desconocido")
        if not self.finales <= set(self.estados):
            raise ValueError(f"{self.nombre}: estado final desconocido")
        for q, salidas in self.transiciones.items():
            for _, destino in salidas:
                if q not in self.estados or destino not in self.estados:
                    raise ValueError(f"{self.nombre}: transición inválida {q}->{destino}")

    def delta(self, estado, c):
        """δ(q, c). Devuelve None si no hay transición (estado de error implícito)."""
        for clase, destino in self.transiciones.get(estado, ()):
            if c in clase:
                return destino
        return None

    def reconocer(self, texto, inicio=0):
        """Longitud del prefijo más largo de texto[inicio:] que el AFD acepta (0 si ninguno)."""
        estado = self.inicial
        aceptado = 0
        i = inicio
        while i < len(texto):
            estado = self.delta(estado, texto[i])
            if estado is None:
                break
            i += 1
            if estado in self.finales:
                aceptado = i - inicio
        return aceptado

    def acepta(self, cadena):
        return len(cadena) > 0 and self.reconocer(cadena) == len(cadena)

    def tabla(self):
        """Tabla de transición como lista de filas (estado, clase, destino)."""
        filas = []
        for q in self.estados:
            for clase, destino in self.transiciones.get(q, ()):
                filas.append((q, clase.etiqueta, destino))
        return filas
