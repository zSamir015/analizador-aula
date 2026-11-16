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


CODIFICACIONES = ("utf-8-sig", "cp1252")


def leer_archivo(ruta, encoding=None):
    """Devuelve el texto del archivo.

    Sin ``encoding`` se prueba UTF-8 (con o sin BOM) y, si falla, cp1252, que
    es como guarda el Bloc de notas de Windows en modo ANSI.
    """
    with open(ruta, "rb") as archivo:
        datos = archivo.read()
    if encoding:
        return datos.decode(encoding)
    for codificacion in CODIFICACIONES[:-1]:
        try:
            return datos.decode(codificacion)
        except UnicodeDecodeError:
            pass
    return datos.decode(CODIFICACIONES[-1], errors="replace")


def analizar_archivo(ruta, encoding=None):
    """Generador: analiza el archivo línea por línea (permite mostrar el avance)."""
    texto = leer_archivo(ruta, encoding).replace("\r\n", "\n").replace("\r", "\n")
    yield from analizar_lineas(texto.split("\n"))
