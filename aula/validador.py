"""API pública del analizador.

Cada línea del archivo es una cadena de entrada. Las líneas vacías y las que
solo contienen un comentario se omiten. Si una línea tiene errores léxicos no
se analiza su sintaxis, para no reportar errores en cascada.

Uso:

    from aula import analizar_archivo

    for resultado in analizar_archivo("entrada.txt"):
        resultado.numero     # número de línea
        resultado.texto      # texto original
        resultado.tokens     # list[Token] -> lexema, tipo, linea, columna
        resultado.errores    # list[Error] -> codigo, categoria, mensaje, linea, columna, lexema
        resultado.sentencia  # "S1".."S11" si la línea es válida
        resultado.valida     # True si no hay errores
"""

from .lexico import analizar_linea
from .sintaxis import analizar_sentencia
from .tokens import ResultadoLinea


def analizar_cadena(texto, numero=1):
    """Analiza una cadena (una línea) y devuelve un ResultadoLinea."""
    texto = texto.rstrip("\r\n")
    tokens, errores = analizar_linea(texto, numero)
    resultado = ResultadoLinea(numero, texto, tokens, errores)
    if not errores and tokens:
        sentencia, error = analizar_sentencia(tokens, numero, len(texto))
        if error:
            resultado.errores.append(error)
        else:
            resultado.sentencia = sentencia
    return resultado


def analizar_lineas(lineas):
    """Generador de ResultadoLinea para cada línea con contenido."""
    for numero, texto in enumerate(lineas, start=1):
        contenido = texto.strip()
        if not contenido or contenido.startswith("#"):
            continue
        yield analizar_cadena(texto, numero)


def analizar_archivo(ruta, encoding="utf-8"):
    """Generador: analiza el archivo línea por línea (permite mostrar el avance)."""
    with open(ruta, encoding=encoding) as archivo:
        yield from analizar_lineas(archivo)
