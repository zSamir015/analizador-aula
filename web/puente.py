"""Puente entre la página web y el paquete aula (se ejecuta con Pyodide)."""

import json

from aula import ERRORES, ManejadorErrores, TablaSimbolos, analizar_lineas
from aula.validador import CODIFICACIONES


def decodificar(datos):
    """Igual que leer_archivo: UTF-8 (con o sin BOM) y, si falla, cp1252."""
    datos = bytes(datos)
    for codificacion in CODIFICACIONES[:-1]:
        try:
            return datos.decode(codificacion)
        except UnicodeDecodeError:
            pass
    return datos.decode(CODIFICACIONES[-1], errors="replace")


def analizar(texto):
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    manejador = ManejadorErrores()
    tabla = TablaSimbolos()
    lineas = []
    for r in analizar_lineas(texto.split("\n")):
        registros = manejador.procesar(r)
        tabla.registrar(r)
        lineas.append({
            "numero": r.numero,
            "texto": r.texto,
            "valida": r.valida,
            "tokens": [{"lexema": t.lexema, "tipo": t.tipo, "linea": t.linea,
                        "columna": t.columna, "indice": tabla.indice(t.lexema)}
                       for t in r.tokens],
            "errores": [{"codigo": g.codigo, "descripcion": g.error.descripcion,
                         "mensaje": g.error.mensaje, "linea": g.linea,
                         "columna": g.columna, "lexema": g.error.lexema,
                         "esperado": g.error.esperado,
                         "recuperacion": g.error.recuperacion,
                         "sugerencia": g.sugerencia,
                         "formato": manejador.formatear(g)}
                        for g in registros],
        })
    usados = tabla.simbolos_usados()
    posicion = {id(s): i for i, s in enumerate(tabla)}
    usados.sort(key=lambda s: (tabla.indice(s.lexema), posicion[id(s)]))
    simbolos = [{"indice": tabla.indice(s.lexema), "lexema": s.lexema, "tipo": s.tipo,
                 "categoria": s.categoria, "linea": s.linea, "veces": s.veces}
                for s in usados]
    return json.dumps({
        "lineas": lineas,
        "resumen": manejador.resumen(),
        "total_errores": manejador.total,
        "simbolos": simbolos,
        "estadisticas": tabla.estadisticas(),
        "texto_tabla": tabla.formatear(),
    }, ensure_ascii=False)


def catalogo():
    return json.dumps({c: v[1] for c, v in ERRORES.items()}, ensure_ascii=False)
