"""Un AFD por cada token del lenguaje AULA."""

from . import tokens as T
from .afd import AFD

MAYUSCULAS = "MAYUSCULAS"  # palabra en mayúsculas; el analizador la convierte en DIA

IDENTIFICADOR = AFD(
    "Identificador", T.IDENTIFICADOR, "[a-z_][a-zA-Z0-9_]*",
    estados=["q0", "q1"], inicial="q0", finales=["q1"],
    transiciones={
        "q0": [("a-z", "q1"), ("_", "q1")],
        "q1": [("a-z", "q1"), ("A-Z", "q1"), ("0-9", "q1"), ("_", "q1")],
    },
)

PALABRA_MAYUS = AFD(
    "Día", MAYUSCULAS, "[A-Z]+   (válida solo si es LU, MA, MI, JU o VI)",
    estados=["q0", "q1"], inicial="q0", finales=["q1"],
    transiciones={
        "q0": [("A-Z", "q1")],
        "q1": [("A-Z", "q1")],
    },
)

CODIGO_MATERIA = AFD(
    "Código de materia", T.CODIGO_MATERIA, "[0-9]{4}",
    estados=["q0", "q1", "q2", "q3", "q4"],
    inicial="q0", finales=["q4"],
    transiciones={
        "q0": [("0-9", "q1")],
        "q1": [("0-9", "q2")],
        "q2": [("0-9", "q3")],
        "q3": [("0-9", "q4")],
    },
)

GRUPO = AFD(
    "Grupo", T.GRUPO, "[0-9][A-Z]{2}[0-9]{3}",
    estados=["q0", "q1", "q2", "q3", "q4", "q5", "q6"],
    inicial="q0", finales=["q6"],
    transiciones={
        "q0": [("0-9", "q1")],
        "q1": [("A-Z", "q2")],
        "q2": [("A-Z", "q3")],
        "q3": [("0-9", "q4")],
        "q4": [("0-9", "q5")],
        "q5": [("0-9", "q6")],
    },
)

AULA = AFD(
    "Aula", T.AULA, "[0-9]{1,2}-[0-9]{3}",
    estados=["q0", "q1", "q2", "q3", "q4", "q5", "q6"],
    inicial="q0", finales=["q6"],
    transiciones={
        "q0": [("0-9", "q1")],
        "q1": [("0-9", "q2"), ("-", "q3")],
        "q2": [("-", "q3")],
        "q3": [("0-9", "q4")],
        "q4": [("0-9", "q5")],
        "q5": [("0-9", "q6")],
    },
)


def _transiciones_hora(p, sig_final):
    """Sub-autómata de ([01]?[0-9]|2[0-3]):[0-5][0-9] con prefijo de estados p."""
    return {
        f"{p}0": [("0-1", f"{p}1"), ("2", f"{p}2"), ("3-9", f"{p}3")],
        f"{p}1": [("0-9", f"{p}4"), (":", f"{p}5")],  # 0 o 1: puede venir otro dígito
        f"{p}2": [("0-3", f"{p}4"), (":", f"{p}5")],  # 2: solo 20-23
        f"{p}3": [(":", f"{p}5")],                    # 3-9: hora de un dígito
        f"{p}4": [(":", f"{p}5")],
        f"{p}5": [("0-5", f"{p}6")],
        f"{p}6": [("0-9", sig_final)],
    }


_HORA_TRANS = _transiciones_hora("h", "h7")
HORA = AFD(
    "Hora", T.HORA, "([01]?[0-9]|2[0-3]):[0-5][0-9]",
    estados=[f"h{i}" for i in range(8)], inicial="h0", finales=["h7"],
    transiciones=_HORA_TRANS,
)

_RANGO_TRANS = {**_transiciones_hora("h", "h7"), **_transiciones_hora("k", "k7")}
_RANGO_TRANS["h7"] = [("-", "k0")]
RANGO_HORA = AFD(
    "Rango de horas", T.RANGO_HORA, "HORA-HORA",
    estados=[f"h{i}" for i in range(8)] + [f"k{i}" for i in range(8)],
    inicial="h0", finales=["k7"],
    transiciones=_RANGO_TRANS,
)

ENTERO = AFD(
    "Entero", T.ENTERO, "[0-9]+",
    estados=["q0", "q1"], inicial="q0", finales=["q1"],
    transiciones={
        "q0": [("0-9", "q1")],
        "q1": [("0-9", "q1")],
    },
)

REAL = AFD(
    "Real", T.REAL, "[0-9]+\\.[0-9]+",
    estados=["q0", "q1", "q2", "q3"], inicial="q0", finales=["q3"],
    transiciones={
        "q0": [("0-9", "q1")],
        "q1": [("0-9", "q1"), (".", "q2")],
        "q2": [("0-9", "q3")],
        "q3": [("0-9", "q3")],
    },
)

CADENA = AFD(
    "Cadena", T.CADENA, '"[^"\\n]*"',
    estados=["q0", "q1", "q2"], inicial="q0", finales=["q2"],
    transiciones={
        "q0": [('"', "q1")],
        "q1": [('Σ-{"}', "q1"), ('"', "q2")],
    },
)

OP_RELACIONAL = AFD(
    "Operador relacional", T.OP_RELACIONAL, "== | != | < | <= | > | >=",
    estados=["q0", "q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8"],
    inicial="q0", finales=["q2", "q4", "q5", "q6", "q7", "q8"],
    transiciones={
        "q0": [("=", "q1"), ("!", "q3"), ("<", "q5"), (">", "q7")],
        "q1": [("=", "q2")],
        "q3": [("=", "q4")],
        "q5": [("=", "q6")],
        "q7": [("=", "q8")],
    },
)

ASIGNACION = AFD(
    "Asignación", T.ASIGNACION, "=",
    estados=["q0", "q1"], inicial="q0", finales=["q1"],
    transiciones={"q0": [("=", "q1")]},
)

DELIMITADOR = AFD(
    "Delimitador", T.DELIMITADOR, ";",
    estados=["q0", "q1"], inicial="q0", finales=["q1"],
    transiciones={"q0": [(";", "q1")]},
)

COMENTARIO = AFD(
    "Comentario", T.COMENTARIO, "#[^\\n]*",
    estados=["q0", "q1"], inicial="q0", finales=["q1"],
    transiciones={
        "q0": [("#", "q1")],
        "q1": [("Σ", "q1")],
    },
)

# Autómatas que reconocen "palabras" (secuencias sin separadores).
# El orden es la prioridad en caso de empate de longitud.
# El orden importa en los empates de la coincidencia más larga: CODIGO_MATERIA
# va antes que ENTERO, así una palabra de exactamente 4 dígitos es un código de
# materia (regla de prioridad, como las palabras reservadas frente a los
# identificadores).
AFD_PALABRAS = [IDENTIFICADOR, PALABRA_MAYUS, CODIGO_MATERIA, GRUPO, AULA,
                RANGO_HORA, HORA, REAL, ENTERO]

# Autómatas de símbolos.
AFD_SIMBOLOS = [OP_RELACIONAL, ASIGNACION, DELIMITADOR]

TODOS = AFD_PALABRAS + [CADENA] + AFD_SIMBOLOS + [COMENTARIO]
