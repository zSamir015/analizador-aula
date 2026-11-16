"""Validación sintáctica simple: cada línea debe ser una sentencia del lenguaje.

Sentencias (una por línea, terminadas en ';'):

  S1  tipo IDENTIFICADOR = valor ;
  S2  materia CODIGO_MATERIA CADENA creditos ENTERO ;
  S3  profesor IDENTIFICADOR CADENA ;
  S4  aula AULA capacidad ENTERO ;
  S5  grupo GRUPO ;
  S6  asignar CODIGO_MATERIA a GRUPO con IDENTIFICADOR en AULA DIA RANGO_HORA ;
  S7  eliminar CODIGO_MATERIA de GRUPO ;
  S8  verificar choque GRUPO ;
  S9  mostrar horario de GRUPO ;   |   mostrar (CADENA | IDENTIFICADOR) ;
  S10 si condicion ((y | o) condicion)* entonces mostrar (CADENA | IDENTIFICADOR) ;
  S11 IDENTIFICADOR = valor ;

  condicion → IDENTIFICADOR OP_RELACIONAL operando
  operando  → ENTERO | REAL | CADENA | HORA | IDENTIFICADOR | verdadero | falso
"""

from . import tokens as T
from .tokens import Error

SENTENCIAS = {
    "S1": "Declaración de variable",
    "S2": "Declaración de materia",
    "S3": "Declaración de profesor",
    "S4": "Declaración de aula",
    "S5": "Declaración de grupo",
    "S6": "Asignación de clase",
    "S7": "Eliminación de clase",
    "S8": "Verificación de choques",
    "S9": "Mostrar",
    "S10": "Condición",
    "S11": "Asignación de variable",
}

# Valor que admite cada tipo de dato en una declaración (S1)
VALOR_POR_TIPO = {
    "entero": [(T.ENTERO, None)],
    "real": [(T.REAL, None), (T.ENTERO, None)],
    "texto": [(T.CADENA, None)],
    "logico": [(T.RESERVADA, "verdadero"), (T.RESERVADA, "falso")],
    "hora": [(T.HORA, None)],
}

VALOR = [(T.ENTERO, None), (T.REAL, None), (T.CADENA, None), (T.HORA, None),
         (T.RESERVADA, "verdadero"), (T.RESERVADA, "falso")]
OPERANDO = VALOR + [(T.IDENTIFICADOR, None)]

NOMBRES = {
    T.IDENTIFICADOR: "identificador", T.CODIGO_MATERIA: "código de materia",
    T.GRUPO: "grupo", T.AULA: "aula", T.HORA: "hora", T.RANGO_HORA: "rango de horas",
    T.ENTERO: "número entero", T.REAL: "número real", T.CADENA: "cadena",
    T.OP_RELACIONAL: "operador relacional", T.ASIGNACION: "'='",
    T.DELIMITADOR: "';'", T.DIA: "día (LU, MA, MI, JU, VI)",
}


class _ErrorSintaxis(Exception):
    def __init__(self, error):
        self.error = error


def _describir(opciones):
    partes = [f"'{lex}'" if lex else NOMBRES.get(tipo, tipo) for tipo, lex in opciones]
    return partes[0] if len(partes) == 1 else ", ".join(partes[:-1]) + " o " + partes[-1]


class _Parser:
    def __init__(self, tokens, linea, largo_linea):
        self.tokens = tokens
        self.i = 0
        self.linea = linea
        self.col_fin = largo_linea + 1

    def actual(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def es(self, tipo, lexema=None):
        tok = self.actual()
        return tok is not None and tok.tipo == tipo and (lexema is None or tok.lexema == lexema)

    def esperar(self, *opciones):
        """opciones: pares (tipo, lexema|None). Consume el token si coincide."""
        for tipo, lexema in opciones:
            if self.es(tipo, lexema):
                tok = self.actual()
                self.i += 1
                return tok
        esperado = _describir(opciones)
        tok = self.actual()
        if tok is None:
            if opciones == ((T.DELIMITADOR, ";"),):
                raise _ErrorSintaxis(Error("S03", "Falta ';' al final de la sentencia",
                                           self.linea, self.col_fin))
            raise _ErrorSintaxis(Error("S02", f"Se esperaba {esperado} y la línea terminó",
                                       self.linea, self.col_fin))
        raise _ErrorSintaxis(Error("S02", f"Se esperaba {esperado} y se encontró '{tok.lexema}'",
                                   self.linea, tok.columna, tok.lexema))

    def palabra(self, lexema):
        return self.esperar((T.RESERVADA, lexema))

    def fin(self):
        self.esperar((T.DELIMITADOR, ";"))
        tok = self.actual()
        if tok is not None:
            raise _ErrorSintaxis(Error("S04", f"Tokens sobrantes después de ';': '{tok.lexema}'",
                                       self.linea, tok.columna, tok.lexema))

    def condicion(self):
        self.esperar((T.IDENTIFICADOR, None))
        self.esperar((T.OP_RELACIONAL, None))
        self.esperar(*OPERANDO)

    # --- sentencias ---------------------------------------------------------

    def sentencia(self):
        tok = self.actual()
        if tok.tipo == T.RESERVADA and tok.lexema in T.TIPOS_DATO:
            tipo = self.esperar((T.RESERVADA, None)).lexema
            self.esperar((T.IDENTIFICADOR, None))
            self.esperar((T.ASIGNACION, None))
            self.esperar(*VALOR_POR_TIPO[tipo])
            codigo = "S1"
        elif tok.tipo == T.IDENTIFICADOR:
            self.esperar((T.IDENTIFICADOR, None))
            self.esperar((T.ASIGNACION, None))
            self.esperar(*OPERANDO)
            codigo = "S11"
        elif tok.tipo != T.RESERVADA:
            raise _ErrorSintaxis(Error("S01", f"Sentencia desconocida: una línea no puede "
                                              f"comenzar con '{tok.lexema}'",
                                       self.linea, tok.columna, tok.lexema))
        else:
            metodo = getattr(self, f"_s_{tok.lexema}", None)
            if metodo is None:
                raise _ErrorSintaxis(Error("S01", f"Sentencia desconocida: una línea no puede "
                                                  f"comenzar con '{tok.lexema}'",
                                           self.linea, tok.columna, tok.lexema))
            self.i += 1
            codigo = metodo()
        self.fin()
        return codigo

    def _s_materia(self):
        self.esperar((T.CODIGO_MATERIA, None))
        self.esperar((T.CADENA, None))
        self.palabra("creditos")
        self.esperar((T.ENTERO, None))
        return "S2"

    def _s_profesor(self):
        self.esperar((T.IDENTIFICADOR, None))
        self.esperar((T.CADENA, None))
        return "S3"

    def _s_aula(self):
        self.esperar((T.AULA, None))
        self.palabra("capacidad")
        self.esperar((T.ENTERO, None))
        return "S4"

    def _s_grupo(self):
        self.esperar((T.GRUPO, None))
        return "S5"

    def _s_asignar(self):
        self.esperar((T.CODIGO_MATERIA, None))
        self.palabra("a")
        self.esperar((T.GRUPO, None))
        self.palabra("con")
        self.esperar((T.IDENTIFICADOR, None))
        self.palabra("en")
        self.esperar((T.AULA, None))
        self.esperar((T.DIA, None))
        self.esperar((T.RANGO_HORA, None))
        return "S6"

    def _s_eliminar(self):
        self.esperar((T.CODIGO_MATERIA, None))
        self.palabra("de")
        self.esperar((T.GRUPO, None))
        return "S7"

    def _s_verificar(self):
        self.palabra("choque")
        self.esperar((T.GRUPO, None))
        return "S8"

    def _s_mostrar(self):
        if self.es(T.RESERVADA, "horario"):
            self.i += 1
            self.palabra("de")
            self.esperar((T.GRUPO, None))
        else:
            self.esperar((T.RESERVADA, "horario"), (T.CADENA, None), (T.IDENTIFICADOR, None))
        return "S9"

    def _s_si(self):
        self.condicion()
        while self.es(T.RESERVADA, "y") or self.es(T.RESERVADA, "o"):
            self.i += 1
            self.condicion()
        self.palabra("entonces")
        self.palabra("mostrar")
        self.esperar((T.CADENA, None), (T.IDENTIFICADOR, None))
        return "S10"


def analizar_sentencia(tokens, linea=1, largo_linea=0):
    """Devuelve (codigo_sentencia, error). Uno de los dos es None."""
    if not tokens:
        return None, None
    parser = _Parser(tokens, linea, largo_linea)
    try:
        return parser.sentencia(), None
    except _ErrorSintaxis as e:
        return None, e.error
