"""Analizador léxico: convierte una línea en tokens usando los AFD.

Solo hace trabajo léxico: reconoce lexemas, los clasifica en tokens y reporta
los que no pertenecen a ningún token. No revisa el orden de los tokens
(sintaxis) ni su significado (semántica): por ejemplo, ``9:00-7:00`` es un
RANGO_HORA léxicamente correcto aunque el rango esté invertido.

Regla de la coincidencia más larga: en cada posición se prueban los AFD y se
toma el prefijo aceptado más largo. Un token de tipo "palabra" debe terminar
en un separador; si no, la palabra completa se reporta como error y el
análisis continúa después de ella (recuperación en modo pánico).
"""

import string

from . import automatas as A
from . import tokens as T
from .tokens import Error, Token

ESPACIOS = " \t\r\n"
SIMBOLOS = "=<>!;"
SEPARADORES = set(ESPACIOS) | set(SIMBOLOS) | {'"', "#"}
CARACTERES_PALABRA = set(string.ascii_letters + string.digits + "_-:.")


def _mas_larga(automatas, texto, pos):
    """(afd, longitud) del AFD con el prefijo aceptado más largo."""
    mejor, largo = None, 0
    for afd in automatas:
        n = afd.reconocer(texto, pos)
        if n > largo:
            mejor, largo = afd, n
    return mejor, largo


def clasificar_error(palabra):
    """Elige el código de error según la forma de una palabra que ningún AFD aceptó."""
    p0 = palabra[0]
    if ":" in palabra:
        return "E04", f"Hora o rango de horas mal formado '{palabra}' (formato: 7:00 o 7:00-8:30)"
    if p0.isdigit():
        if "." in palabra:
            return "E03", f"Número real mal formado '{palabra}' (formato: 71.5)"
        if "-" in palabra:
            return "E09", f"Aula mal formada '{palabra}' (formato: 3-105)"
        if any(c.isupper() for c in palabra):
            return "E06", f"Grupo mal formado '{palabra}' (formato: 1IL142)"
        if any(c.islower() or c == "_" for c in palabra):
            return "E07", f"Un identificador no puede comenzar con dígito: '{palabra}'"
        return "E03", f"Número mal formado '{palabra}'"
    if p0 == ".":
        return "E03", f"Número real mal formado '{palabra}' (formato: 71.5)"
    if p0.isupper():
        if "-" in palabra or palabra.rstrip(string.digits).isupper():
            return "E05", f"Código de materia mal formado '{palabra}' (formato: LFAC-301)"
        return "E07", f"Identificador mal formado '{palabra}' (debe comenzar con minúscula)"
    if p0 in "-":
        return "E01", f"Símbolo '-' fuera de contexto en '{palabra}'"
    return "E07", f"Identificador mal formado '{palabra}'"


def _descarte(palabra, fin):
    """Texto de la recuperación en modo pánico para una palabra rechazada."""
    return (f"Modo pánico: se descartó la palabra '{palabra}' completa; "
            f"el análisis sigue en la columna {fin + 1}.")


def _token_palabra(afd, lexema, linea, col):
    """Convierte una palabra aceptada en Token, o en Error si falla una regla extra."""
    if afd is A.IDENTIFICADOR:
        if lexema in T.PALABRAS_RESERVADAS:
            return Token(lexema, T.RESERVADA, linea, col)
        if len(lexema) > T.LONGITUD_MAX_IDENTIFICADOR:
            return Error("E10", f"Identificador de {len(lexema)} caracteres "
                                f"(máximo {T.LONGITUD_MAX_IDENTIFICADOR}): '{lexema}'",
                         linea, col, lexema)
        return Token(lexema, T.IDENTIFICADOR, linea, col)
    if afd is A.PALABRA_MAYUS:
        if lexema in T.DIAS:
            return Token(lexema, T.DIA, linea, col)
        return Error("E08", f"Día inválido '{lexema}' (válidos: LU, MA, MI, JU, VI)",
                     linea, col, lexema)
    return Token(lexema, afd.tipo, linea, col)


def analizar_linea(texto, linea=1):
    """Devuelve (tokens, errores) de una línea. Los comentarios se descartan."""
    tokens, errores = [], []
    pos, n = 0, len(texto)

    while pos < n:
        c = texto[pos]
        col = pos + 1

        if c in ESPACIOS:
            pos += 1
            continue

        if c == "#":  # comentario: se descarta el resto de la línea
            pos += A.COMENTARIO.reconocer(texto, pos)
            continue

        if c == '"':
            largo = A.CADENA.reconocer(texto, pos)
            if largo:
                tokens.append(Token(texto[pos:pos + largo], T.CADENA, linea, col))
                pos += largo
            else:
                resto = texto[pos:].rstrip()
                errores.append(Error("E02", f"Cadena sin cerrar {resto}", linea, col, resto,
                                     "Se descartó desde la comilla hasta el fin de la línea."))
                pos = n
            continue

        if c in SIMBOLOS:
            afd, largo = _mas_larga(A.AFD_SIMBOLOS, texto, pos)
            if largo:
                tokens.append(Token(texto[pos:pos + largo], afd.tipo, linea, col))
                pos += largo
            else:
                errores.append(Error("E01", f"Carácter no válido '{c}'", linea, col, c,
                                     f"Se descartó '{c}'; el análisis sigue en la columna {col + 1}."))
                pos += 1
            continue

        # Palabra: todo hasta el siguiente separador
        fin = pos
        while fin < n and texto[fin] not in SEPARADORES:
            fin += 1
        palabra = texto[pos:fin]

        invalido = next((i for i, ch in enumerate(palabra) if ch not in CARACTERES_PALABRA), None)
        if invalido is not None:
            ch = palabra[invalido]
            errores.append(Error("E01", f"Carácter no válido '{ch}' en '{palabra}'",
                                 linea, col + invalido, ch, _descarte(palabra, fin)))
            pos = fin
            continue

        afd, largo = _mas_larga(A.AFD_PALABRAS, texto, pos)
        if afd is not None and largo == len(palabra):
            resultado = _token_palabra(afd, palabra, linea, col)
            if isinstance(resultado, Error):
                resultado.recuperacion = _descarte(palabra, fin)
                errores.append(resultado)
            else:
                tokens.append(resultado)
        else:
            codigo, mensaje = clasificar_error(palabra)
            errores.append(Error(codigo, mensaje, linea, col, palabra, _descarte(palabra, fin)))
        pos = fin

    return tokens, errores
