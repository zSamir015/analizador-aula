"""Analizador del lenguaje AULA (horarios universitarios)."""

from .manejador_errores import ManejadorErrores, RegistroError
from .tabla_simbolos import Simbolo, TablaSimbolos
from .tokens import ERRORES, Error, ResultadoLinea, Token
from .validador import analizar_archivo, analizar_cadena, analizar_lineas

__all__ = ["analizar_archivo", "analizar_cadena", "analizar_lineas",
           "Token", "Error", "ResultadoLinea", "ERRORES",
           "TablaSimbolos", "Simbolo", "ManejadorErrores", "RegistroError"]
