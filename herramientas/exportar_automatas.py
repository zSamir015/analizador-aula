"""Exporta cada AFD a JFLAP (.jff) y a diagrama PNG (Graphviz).

    python3 herramientas/exportar_automatas.py

Las posiciones de los estados en los .jff se toman del layout de Graphviz si
`dot` está instalado; si no, se usa una distribución lineal.

En JFLAP cada transición muestra la clase de caracteres que lee ("0-9",
"A-Z", ...). Las clases de un solo carácter (":", "-", ";") son literales.
"""

import os
import shutil
import subprocess
import sys
import unicodedata
from collections import OrderedDict
from xml.sax.saxutils import escape

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from aula import automatas as A  # noqa: E402


def nombre_archivo(afd):
    base = unicodedata.normalize("NFKD", afd.nombre).encode("ascii", "ignore").decode()
    return base.lower().replace(" ", "_")


def aristas(afd):
    """Agrupa las clases que van del mismo origen al mismo destino."""
    grupos = OrderedDict()
    for origen, etiqueta, destino in afd.tabla():
        grupos.setdefault((origen, destino), []).append(etiqueta)
    return grupos


def a_dot(afd):
    lineas = [
        f'digraph "{afd.nombre}" {{',
        "  rankdir=LR; nodesep=0.4; ranksep=0.5;",
        '  node [shape=circle fontname="Helvetica" fontsize=12 width=0.5 fixedsize=true];',
        '  edge [fontname="Helvetica" fontsize=11];',
        '  inicio [shape=point width=0.08];',
    ]
    for q in afd.estados:
        forma = "doublecircle" if q in afd.finales else "circle"
        lineas.append(f'  "{q}" [shape={forma}];')
    lineas.append(f'  inicio -> "{afd.inicial}";')
    for (origen, destino), etiquetas in aristas(afd).items():
        etq = ", ".join(etiquetas).replace("\\", "\\\\").replace('"', '\\"')
        lineas.append(f'  "{origen}" -> "{destino}" [label=" {etq} "];')
    lineas.append("}")
    return "\n".join(lineas)


def posiciones(afd, dot):
    if dot:
        salida = subprocess.run([dot, "-Tplain"], input=a_dot(afd), capture_output=True,
                                text=True, check=True).stdout
        pos = {}
        alto = 0.0
        for linea in salida.splitlines():
            partes = linea.split()
            if partes[0] == "graph":
                alto = float(partes[3])
            elif partes[0] == "node" and partes[1].strip('"') in afd.estados:
                pos[partes[1].strip('"')] = (float(partes[2]), float(partes[3]))
        return {q: (60 + x * 90, 60 + (alto - y) * 90) for q, (x, y) in pos.items()}
    return {q: (60 + i * 110, 120) for i, q in enumerate(afd.estados)}


def a_jff(afd, pos):
    ids = {q: i for i, q in enumerate(afd.estados)}
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
           f"<!--AFD {escape(afd.nombre)}: {escape(afd.expresion)}-->",
           "<structure>", "\t<type>fa</type>", "\t<automaton>"]
    for q in afd.estados:
        x, y = pos[q]
        out.append(f'\t\t<state id="{ids[q]}" name="{q}">')
        out.append(f"\t\t\t<x>{x:.1f}</x>")
        out.append(f"\t\t\t<y>{y:.1f}</y>")
        if q == afd.inicial:
            out.append("\t\t\t<initial/>")
        if q in afd.finales:
            out.append("\t\t\t<final/>")
        out.append("\t\t</state>")
    for origen, etiqueta, destino in afd.tabla():
        out += ["\t\t<transition>",
                f"\t\t\t<from>{ids[origen]}</from>",
                f"\t\t\t<to>{ids[destino]}</to>",
                f"\t\t\t<read>{escape(etiqueta)}</read>",
                "\t\t</transition>"]
    out += ["\t</automaton>", "</structure>", ""]
    return "\n".join(out)


def main():
    dot = shutil.which("dot")
    dir_jff = os.path.join(RAIZ, "jflap")
    dir_png = os.path.join(RAIZ, "diagramas")
    os.makedirs(dir_jff, exist_ok=True)
    if dot:
        os.makedirs(dir_png, exist_ok=True)
    else:
        print("Graphviz (dot) no está instalado: se omiten los PNG.")

    for afd in A.TODOS:
        nombre = nombre_archivo(afd)
        with open(os.path.join(dir_jff, f"{nombre}.jff"), "w", encoding="utf-8") as f:
            f.write(a_jff(afd, posiciones(afd, dot)))
        if dot:
            subprocess.run([dot, "-Tpng", "-Gdpi=200", "-o",
                            os.path.join(dir_png, f"{nombre}.png")],
                           input=a_dot(afd), text=True, check=True)
        print(f"{nombre}: {len(afd.estados)} estados, {len(afd.tabla())} transiciones")


if __name__ == "__main__":
    main()
