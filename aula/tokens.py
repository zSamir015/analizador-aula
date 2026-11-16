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

# Palabras reservadas (26) + días (5) = 31
PALABRAS_RESERVADAS = frozenset({
    # entidades
    "materia", "profesor", "aula", "grupo",
    # acciones
    "asignar", "eliminar", "verificar", "mostrar",
    # conectores
    "a", "con", "en", "de", "capacidad", "horario", "choque",
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

# Catálogo de errores léxicos: código -> (categoría, descripción, lo que se esperaba)
ERRORES = {
    "E01": (LEXICO, "Carácter no válido",
            "un carácter del alfabeto: letras sin tilde ni ñ, dígitos, espacio, ; = < > ! : - . \" #"),
    "E02": (LEXICO, "Cadena sin cerrar", 'CADENA: "[^"\\n]*" (comilla de cierre en la misma línea)'),
    "E03": (LEXICO, "Número mal formado", "ENTERO [0-9]+ o REAL [0-9]+\\.[0-9]+"),
    "E04": (LEXICO, "Hora mal formada",
            "HORA ([01]?[0-9]|2[0-3]):[0-5][0-9] o RANGO_HORA HORA-HORA"),
    "E05": (LEXICO, "Código de materia mal formado", "CODIGO_MATERIA [A-Z]{2,4}-[0-9]{3}"),
    "E06": (LEXICO, "Grupo mal formado", "GRUPO [0-9][A-Z]{2}[0-9]{3}"),
    "E07": (LEXICO, "Identificador mal formado", "IDENTIFICADOR [a-z_][a-zA-Z0-9_]*"),
    "E08": (LEXICO, "Día inválido", "DIA LU | MA | MI | JU | VI"),
    "E09": (LEXICO, "Aula mal formada", "AULA [0-9]{1,2}-[0-9]{3}"),
    "E10": (LEXICO, "Identificador demasiado largo", "IDENTIFICADOR de 31 caracteres como máximo"),
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
    recuperacion: str = ""  # qué hizo el analizador para continuar (modo pánico)

    @property
    def esperado(self):
        return ERRORES[self.codigo][2]

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

    @property
    def valida(self):
        return not self.errores
