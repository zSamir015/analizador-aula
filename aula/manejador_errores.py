"""Manejador de errores del lenguaje AULA (Etapa 2, punto 4).

Recibe los errores que detecta el analizador léxico (E01-E10), los guarda y
los informa al usuario. Cada reporte dice explícitamente:

    - código y nombre del error,
    - ubicación (línea y columna) y el lexema que causó el error,
    - qué token se esperaba (su expresión regular),
    - el texto de la línea con el lexema subrayado,
    - cómo se recuperó el analizador para seguir (modo pánico),
    - una sugerencia de corrección.

Solo hay errores léxicos: el manejador no valida el orden de los tokens
(sintaxis) ni su significado (semántica).

La interfaz de usuario no se acopla al manejador: se suscribe con
``suscribir(callback)`` y recibe cada error en el momento en que se detecta,
es decir, mientras la cadena de entrada se está evaluando.

Uso:

    from aula import ManejadorErrores, analizar_archivo

    manejador = ManejadorErrores()
    manejador.suscribir(lambda reg: print(manejador.formatear(reg)))

    for r in analizar_archivo("entrada.txt"):
        manejador.procesar(r)       # reporta todos los errores de la línea

    print(manejador.resumen())
"""

from dataclasses import dataclass

from .tokens import ERRORES, Error

SUGERENCIAS = {
    "E01": "Elimine el carácter o reemplácelo por uno del alfabeto del lenguaje "
           "(letras sin tilde ni ñ, dígitos y los símbolos ; = < > ! : - . \" #).",
    "E02": "Cierre la cadena con comillas dobles (\") antes del fin de la línea.",
    "E03": "Escriba el número completo: entero (40) o real con dígitos a ambos lados del punto (71.5).",
    "E04": "Use una hora entre 0:00 y 23:59 con minutos de dos dígitos (7:30) "
           "o un rango de dos horas unidas por '-' (7:00-8:30).",
    "E05": "El código de materia son exactamente 4 dígitos, sin letras ni guion (8242).",
    "E06": "El grupo lleva un dígito, dos letras mayúsculas y tres dígitos (1IL142).",
    "E07": "Los identificadores empiezan con letra minúscula o '_' y solo usan letras, dígitos y '_'.",
    "E08": "Los días válidos son LU, MA, MI, JU y VI (en mayúscula).",
    "E09": "El aula lleva uno o dos dígitos, un guion y tres dígitos (3-105).",
    "E10": "Acorte el identificador a 31 caracteres como máximo.",
}


@dataclass
class RegistroError:
    """Un error reportado, con el contexto necesario para informarlo."""
    error: Error
    texto_linea: str
    sugerencia: str

    @property
    def codigo(self):
        return self.error.codigo

    @property
    def categoria(self):
        return self.error.categoria

    @property
    def linea(self):
        return self.error.linea

    @property
    def columna(self):
        return self.error.columna


class ManejadorErrores:
    def __init__(self):
        self._registros = []
        self._escuchas = []
        self._lineas_analizadas = 0
        self._lineas_con_error = set()

    # --- suscripción --------------------------------------------------------

    def suscribir(self, callback):
        """callback(RegistroError) se invoca al reportar cada error."""
        self._escuchas.append(callback)

    def desuscribir(self, callback):
        self._escuchas.remove(callback)

    # --- recepción de errores ----------------------------------------------

    def reportar(self, error, texto_linea=""):
        """Registra un Error, lo notifica a los suscriptores y devuelve el registro."""
        if error.codigo not in ERRORES:
            raise ValueError(f"Código de error desconocido: {error.codigo!r}")
        registro = RegistroError(error, texto_linea.rstrip("\r\n"),
                                 SUGERENCIAS.get(error.codigo, ""))
        self._registros.append(registro)
        self._lineas_con_error.add(error.linea)
        for escucha in list(self._escuchas):
            escucha(registro)
        return registro

    def procesar(self, resultado):
        """Reporta todos los errores de un ResultadoLinea. Devuelve los registros."""
        self._lineas_analizadas += 1
        return [self.reportar(e, resultado.texto) for e in resultado.errores]

    def limpiar(self):
        self._registros.clear()
        self._lineas_con_error.clear()
        self._lineas_analizadas = 0

    # --- consultas ----------------------------------------------------------

    @property
    def registros(self):
        return list(self._registros)

    @property
    def total(self):
        return len(self._registros)

    @property
    def hay_errores(self):
        return bool(self._registros)

    @property
    def lineas_analizadas(self):
        return self._lineas_analizadas

    @property
    def lineas_con_error(self):
        return sorted(self._lineas_con_error)

    def errores_de_linea(self, numero):
        return [r for r in self._registros if r.linea == numero]

    def por_categoria(self, categoria):
        return [r for r in self._registros if r.categoria == categoria]

    def conteo_por_codigo(self):
        conteo = {}
        for r in self._registros:
            conteo[r.codigo] = conteo.get(r.codigo, 0) + 1
        return dict(sorted(conteo.items()))

    # --- presentación -------------------------------------------------------

    def formatear(self, registro):
        """Mensaje explícito para el usuario sobre un error léxico."""
        e = registro.error
        salida = [
            f"✗ Error léxico {e.codigo}: {e.descripcion}",
            f"    Ubicación:   línea {e.linea}, columna {e.columna}",
            f"    Encontrado:  '{e.lexema}'" if e.lexema else "    Encontrado:  (nada)",
            f"    Se esperaba: {e.esperado}",
            f"    Detalle:     {e.mensaje}",
        ]
        if registro.texto_linea:
            prefijo = f"    {e.linea:>4} | "
            relleno = "".join("\t" if c == "\t" else " "
                              for c in registro.texto_linea[:max(e.columna - 1, 0)])
            salida.append(prefijo + registro.texto_linea)
            salida.append(" " * (len(prefijo) - 2) + "| " + relleno + "^" * max(len(e.lexema), 1))
        if e.recuperacion:
            salida.append(f"    Recuperación: {e.recuperacion}")
        if registro.sugerencia:
            salida.append(f"    Sugerencia:  {registro.sugerencia}")
        return "\n".join(salida)

    def resumen(self):
        """Resumen final: totales y conteo por código."""
        if not self._registros:
            return f"Sin errores léxicos en {self._lineas_analizadas} línea(s) analizada(s)."
        lineas = [
            f"{self.total} error(es) léxico(s) en {len(self._lineas_con_error)} de "
            f"{self._lineas_analizadas} línea(s) analizada(s)."
        ]
        for codigo, cantidad in self.conteo_por_codigo().items():
            lineas.append(f"  {codigo}  {ERRORES[codigo][1]:<35} {cantidad}")
        return "\n".join(lineas)
