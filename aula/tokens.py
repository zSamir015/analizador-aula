"""Tipos de token, palabras reservadas y estructuras de datos del lenguaje AULA."""

from dataclasses import dataclass, field

# Tipos de token
IDENTIFICADOR = "IDENTIFICADOR"
RESERVADA = "RESERVADA"
DIA = "DIA"
CODIGO_MATERIA = "CODIGO_MATERIA"
GRUPO = "GRUPO"
AULA = "AULA"
HORA = "HORA"
RANGO_HORA = "RANGO_HORA"
ENTERO = "ENTERO"
REAL = "REAL"
CADENA = "CADENA"
OP_RELACIONAL = "OP_RELACIONAL"
ASIGNACION = "ASIGNACION"
DELIMITADOR = "DELIMITADOR"
COMENTARIO = "COMENTARIO"

# Palabras reservadas (27) + días (5) = 32
PALABRAS_RESERVADAS = frozenset({
    # entidades
    "materia", "profesor", "aula", "grupo",
    # acciones
    "asignar", "eliminar", "verificar", "mostrar",
    # conectores
    "a", "con", "en", "de", "creditos", "capacidad", "horario", "choque",
    # control
    "si", "entonces",
    # tipos de dato
    "entero", "real", "texto", "logico", "hora",
    # literales y operadores lógicos
    "verdadero", "falso", "y", "o",
})

DIAS = frozenset({"LU", "MA", "MI", "JU", "VI"})

TIPOS_DATO = frozenset({"entero", "real", "texto", "logico", "hora"})

LONGITUD_MAX_IDENTIFICADOR = 31

LEXICO = "LEXICO"
SINTACTICO = "SINTACTICO"

# Catálogo de errores: código -> (categoría, descripción)
ERRORES = {
    "E01": (LEXICO, "Carácter no válido"),
    "E02": (LEXICO, "Cadena sin cerrar"),
    "E03": (LEXICO, "Número mal formado"),
    "E04": (LEXICO, "Hora inválida"),
    "E05": (LEXICO, "Rango de horas invertido"),
    "E06": (LEXICO, "Código de materia mal formado"),
    "E07": (LEXICO, "Grupo mal formado"),
    "E08": (LEXICO, "Identificador mal formado"),
    "E09": (LEXICO, "Día inválido"),
    "E10": (LEXICO, "Aula mal formada"),
    "E11": (LEXICO, "Identificador demasiado largo"),
    "S01": (SINTACTICO, "Sentencia desconocida"),
    "S02": (SINTACTICO, "Token inesperado"),
    "S03": (SINTACTICO, "Falta ';' al final de la sentencia"),
    "S04": (SINTACTICO, "Tokens sobrantes después de ';'"),
}


@dataclass
class Token:
    lexema: str
    tipo: str
    linea: int
    columna: int

    def __str__(self):
        return f"<{self.tipo}, '{self.lexema}', {self.linea}:{self.columna}>"


@dataclass
class Error:
    codigo: str
    mensaje: str
    linea: int
    columna: int
    lexema: str = ""

    @property
    def categoria(self):
        return ERRORES[self.codigo][0]

    @property
    def descripcion(self):
        return ERRORES[self.codigo][1]

    def __str__(self):
        return (f"[{self.codigo}] Línea {self.linea}, columna {self.columna}: "
                f"{self.mensaje}")


@dataclass
class ResultadoLinea:
    numero: int
    texto: str
    tokens: list = field(default_factory=list)
    errores: list = field(default_factory=list)
    sentencia: str = ""

    @property
    def valida(self):
        return not self.errores
