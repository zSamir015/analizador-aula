"""Tabla de símbolos del lenguaje AULA (Etapa 2, punto 3).

Es una tabla hash con encadenamiento separado: un arreglo de cubetas, cada una
con la lista de símbolos cuyo lexema cae en ella. La función hash es
polinomial (base 31) y el índice es ``hash % capacidad``. Cuando el factor de
carga supera 0.75 la tabla se duplica (a un tamaño primo) y se reinserta todo.

Cada símbolo guarda solo información léxica:

    lexema       texto del token
    tipo         tipo de token (IDENTIFICADOR, GRUPO, ENTERO, ...)
    categoria    clase de token (identificador, materia, literal, operador, ...)
    linea/columna  primera aparición
    ocurrencias  lista de (línea, columna) de cada aparición

Los datos semánticos (tipo de dato de una variable, su valor, si fue
declarada, créditos de una materia, ...) los agregarían fases posteriores del
compilador; esta etapa no los calcula.

Uso:

    from aula import TablaSimbolos, analizar_archivo

    tabla = TablaSimbolos()
    for r in analizar_archivo("entrada.txt"):
        tabla.registrar(r)          # instala los tokens reconocidos
    print(tabla.formatear())
    simbolo = tabla.buscar("samaniego")
"""

from dataclasses import dataclass, field

from . import tokens as T
from .tokens import PALABRAS_RESERVADAS

CATEGORIA_POR_TIPO = {
    T.IDENTIFICADOR: "identificador",
    T.RESERVADA: "palabra reservada",
    T.DIA: "día",
    T.CODIGO_MATERIA: "materia",
    T.GRUPO: "grupo",
    T.AULA: "aula",
    T.HORA: "literal",
    T.RANGO_HORA: "literal",
    T.ENTERO: "literal",
    T.REAL: "literal",
    T.CADENA: "literal",
    T.OP_RELACIONAL: "operador",
    T.ASIGNACION: "operador",
    T.DELIMITADOR: "delimitador",
}

CAPACIDAD_INICIAL = 53
FACTOR_CARGA_MAX = 0.75


@dataclass
class Simbolo:
    lexema: str
    tipo: str
    categoria: str
    linea: int = 0
    columna: int = 0
    ocurrencias: list = field(default_factory=list)

    @property
    def veces(self):
        return len(self.ocurrencias)


def _es_primo(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def _siguiente_primo(n):
    while not _es_primo(n):
        n += 1
    return n


class TablaSimbolos:
    def __init__(self, capacidad=CAPACIDAD_INICIAL, precargar=True):
        self._capacidad = _siguiente_primo(max(capacidad, 3))
        self._cubetas = [[] for _ in range(self._capacidad)]
        self._cantidad = 0
        self._orden = []          # símbolos en orden de instalación
        self.colisiones = 0       # inserciones en una cubeta ya ocupada
        self.redimensiones = 0
        if precargar:
            for palabra in sorted(PALABRAS_RESERVADAS):
                self._insertar(palabra, T.RESERVADA)
            for dia in ("LU", "MA", "MI", "JU", "VI"):  # == sorted(DIAS)
                self._insertar(dia, T.DIA)

    # --- función hash -------------------------------------------------------

    @staticmethod
    def hash(lexema):
        """Hash polinomial de 32 bits: h = h*31 + código del carácter."""
        h = 0
        for caracter in lexema:
            h = (h * 31 + ord(caracter)) & 0xFFFFFFFF
        return h

    def indice(self, lexema):
        return self.hash(lexema) % self._capacidad

    # --- operaciones básicas ------------------------------------------------

    def _buscar(self, lexema, tipo=None):
        for simbolo in self._cubetas[self.indice(lexema)]:
            if simbolo.lexema == lexema and (tipo is None or simbolo.tipo == tipo):
                return simbolo
        return None

    def _insertar(self, lexema, tipo):
        if (self._cantidad + 1) / self._capacidad > FACTOR_CARGA_MAX:
            self._redimensionar()
        simbolo = Simbolo(lexema, tipo, CATEGORIA_POR_TIPO.get(tipo, tipo.lower()))
        cubeta = self._cubetas[self.indice(lexema)]
        if cubeta:
            self.colisiones += 1
        cubeta.append(simbolo)
        self._orden.append(simbolo)
        self._cantidad += 1
        return simbolo

    def _redimensionar(self):
        self._capacidad = _siguiente_primo(self._capacidad * 2)
        self._cubetas = [[] for _ in range(self._capacidad)]
        self.colisiones = 0
        for simbolo in self._orden:
            cubeta = self._cubetas[self.indice(simbolo.lexema)]
            if cubeta:
                self.colisiones += 1
            cubeta.append(simbolo)
        self.redimensiones += 1

    def buscar(self, lexema, tipo=None):
        """Devuelve el Simbolo o None."""
        return self._buscar(lexema, tipo)

    def instalar(self, token):
        """Instala un token (o registra una nueva ocurrencia) y devuelve su Simbolo."""
        simbolo = self._buscar(token.lexema, token.tipo)
        if simbolo is None:
            simbolo = self._insertar(token.lexema, token.tipo)
        if not simbolo.ocurrencias:
            simbolo.linea, simbolo.columna = token.linea, token.columna
        simbolo.ocurrencias.append((token.linea, token.columna))
        return simbolo

    def __contains__(self, lexema):
        return self._buscar(lexema) is not None

    def __len__(self):
        return self._cantidad

    def __iter__(self):
        return iter(self._orden)

    @property
    def capacidad(self):
        return self._capacidad

    @property
    def factor_carga(self):
        return self._cantidad / self._capacidad

    # --- integración con el analizador -------------------------------------

    def registrar(self, resultado):
        """Instala cada token reconocido en una línea (ResultadoLinea).

        Los lexemas con error no son tokens y no se instalan; los demás tokens
        de la línea sí, porque léxicamente son correctos.
        Devuelve la cantidad de símbolos nuevos.
        """
        antes = self._cantidad
        for tok in resultado.tokens:
            self.instalar(tok)
        return self._cantidad - antes

    # --- presentación -------------------------------------------------------

    def estadisticas(self):
        ocupadas = sum(1 for c in self._cubetas if c)
        return {
            "simbolos": self._cantidad,
            "capacidad": self._capacidad,
            "cubetas_ocupadas": ocupadas,
            "factor_carga": round(self.factor_carga, 3),
            "colisiones": self.colisiones,
            "redimensiones": self.redimensiones,
            "cadena_mas_larga": max(len(c) for c in self._cubetas),
        }

    def simbolos_usados(self):
        """Símbolos que aparecieron al menos una vez en la entrada."""
        return [s for s in self._orden if s.ocurrencias]

    def formatear(self, incluir_no_usados=False):
        """Tabla de texto con los símbolos instalados (por defecto solo los usados).

        Columnas: índice hash (cubeta = hash % capacidad), lexema, token,
        categoría, primera aparición (línea:columna), cantidad de apariciones
        y todas las posiciones.
        """
        simbolos = list(self._orden) if incluir_no_usados else self.simbolos_usados()
        filas = []
        for s in simbolos:
            filas.append((str(self.indice(s.lexema)), s.lexema, s.tipo, s.categoria,
                          f"{s.linea}:{s.columna}" if s.ocurrencias else "-", str(s.veces),
                          " ".join(f"{l}:{c}" for l, c in s.ocurrencias) or "-"))
        titulos = ("Índice hash", "Lexema", "Token", "Categoría", "1.ª aparición",
                   "Apariciones", "Posiciones (línea:columna)")
        anchos = [max(len(t), *(len(f[i]) for f in filas)) if filas else len(t)
                  for i, t in enumerate(titulos)]

        def linea(valores):
            return "  ".join(v.ljust(anchos[i]) for i, v in enumerate(valores)).rstrip()

        salida = [linea(titulos), "  ".join("-" * a for a in anchos)]
        salida += [linea(f) for f in filas]
        e = self.estadisticas()
        salida.append("")
        salida.append(f"{len(simbolos)} símbolos mostrados | capacidad {e['capacidad']} | "
                      f"factor de carga {e['factor_carga']} | colisiones {e['colisiones']} | "
                      f"redimensiones {e['redimensiones']}")
        return "\n".join(salida)

    def formatear_cubetas(self):
        """Estructura interna: cada cubeta con sus símbolos encadenados."""
        salida = []
        for i, cubeta in enumerate(self._cubetas):
            if cubeta:
                salida.append(f"[{i:>3}] " + " -> ".join(s.lexema for s in cubeta))
        return "\n".join(salida)
