"""Exporta cada AFD a JFLAP (.jff) y a diagrama PNG (Graphviz).

    python3 herramientas/exportar_automatas.py

Las posiciones de los estados en los .jff se toman del layout de Graphviz si
`dot` está instalado; si no, se usa una distribución lineal.

En jflap/ cada transición muestra las clases de caracteres que lee ("0-9",
"a-z, _", ...), que es lo legible para el documento. JFLAP toma esas etiquetas
como texto literal, así que además se genera jflap/simulacion/ con una
transición por cada carácter de la clase: esos archivos son los que se
simulan en JFLAP (Input > Multiple Run).

Las clases Σ y Σ-{"} se expanden a ALFABETO_SIMULACION. El espacio queda
fuera porque en JFLAP una etiqueta en blanco es λ.
"""

import os
import shutil
import string
import subprocess
import sys
import unicodedata
from collections import OrderedDict
from xml.sax.saxutils import escape

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from aula import automatas as A  # noqa: E402
from aula.afd import CLASES  # noqa: E402

ALFABETO_SIMULACION = (string.digits + string.ascii_uppercase + string.ascii_lowercase
                       + '_:-.;=<>!#,()"' + "áéíóúñÑ")


def caracteres(etiqueta):
    """Caracteres concretos de una clase, en el orden de ALFABETO_SIMULACION."""
    clase = CLASES[etiqueta]
    return [c for c in ALFABETO_SIMULACION if c in clase]


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
        pos = {q: (60 + x * 80, 60 + (alto - y) * 80) for q, (x, y) in pos.items()}
        return dos_filas(afd, separar(afd, pos))
    return {q: (60 + i * 110, 120) for i, q in enumerate(afd.estados)}


def separar(afd, pos, distancia=40, paso=12):
    """JFLAP dibuja las transiciones en línea recta (Graphviz las curva). Si una
    recta pasa sobre otro estado, ese estado se aleja de la recta."""
    aristas_rectas = {(o, d) for o, _, d in afd.tabla() if o != d}
    for _ in range(40):
        movido = False
        for a, b in aristas_rectas:
            (ax, ay), (bx, by) = pos[a], pos[b]
            dx, dy = bx - ax, by - ay
            largo2 = dx * dx + dy * dy
            for c, (cx, cy) in pos.items():
                if c in (a, b) or not largo2:
                    continue
                t = ((cx - ax) * dx + (cy - ay) * dy) / largo2
                if not 0.05 < t < 0.95:
                    continue
                px, py = ax + t * dx, ay + t * dy
                if (cx - px) ** 2 + (cy - py) ** 2 < distancia ** 2:
                    lado = -1 if cy <= py else 1
                    pos[c] = (cx, cy + lado * paso)
                    movido = True
        if not movido:
            break
    menor_y = min(y for _, y in pos.values())
    return {q: (x, y - menor_y + 100) for q, (x, y) in pos.items()}


def dos_filas(afd, pos):
    """El rango de horas son dos autómatas de hora seguidos (estados h y k); en
    una sola fila queda demasiado ancho. La parte k se dibuja debajo, de derecha
    a izquierda, para que h7 -> k0 sea una flecha corta hacia abajo."""
    if afd.tipo != A.RANGO_HORA.tipo:
        return pos
    h = {q: p for q, p in pos.items() if q.startswith("h")}
    k = {q: p for q, p in pos.items() if q.startswith("k")}
    borde_der = max(x for x, _ in h.values())
    min_xk = min(x for x, _ in k.values())
    min_yk = min(y for _, y in k.values())
    base = max(y for _, y in h.values()) + 75
    for q, (x, y) in k.items():
        pos[q] = (borde_der - (x - min_xk), base + (y - min_yk))
    return pos


def a_jff(afd, pos, expandir=False):
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
    if expandir:
        lecturas = [(o, c, d) for o, etq, d in afd.tabla() for c in caracteres(etq)]
    else:
        # Para ver el diagrama: una sola etiqueta por par de estados ("a-z, _")
        lecturas = [(o, ", ".join(etqs), d) for (o, d), etqs in aristas(afd).items()]
    for origen, leido, destino in lecturas:
        out += ["\t\t<transition>",
                f"\t\t\t<from>{ids[origen]}</from>",
                f"\t\t\t<to>{ids[destino]}</to>",
                f"\t\t\t<read>{escape(leido)}</read>",
                "\t\t</transition>"]
    out += ["\t</automaton>", "</structure>", ""]
    return "\n".join(out)


def main():
    dot = shutil.which("dot")
    dir_jff = os.path.join(RAIZ, "jflap")
    dir_sim = os.path.join(dir_jff, "simulacion")
    dir_png = os.path.join(RAIZ, "diagramas")
    os.makedirs(dir_sim, exist_ok=True)
    if dot:
        os.makedirs(dir_png, exist_ok=True)
    else:
        print("Graphviz (dot) no está instalado: se omiten los PNG.")

    for afd in A.TODOS:
        nombre = nombre_archivo(afd)
        pos = posiciones(afd, dot)
        with open(os.path.join(dir_jff, f"{nombre}.jff"), "w", encoding="utf-8") as f:
            f.write(a_jff(afd, pos))
        with open(os.path.join(dir_sim, f"{nombre}.jff"), "w", encoding="utf-8") as f:
            f.write(a_jff(afd, pos, expandir=True))
        if dot:
            subprocess.run([dot, "-Tpng", "-Gdpi=200", "-o",
                            os.path.join(dir_png, f"{nombre}.png")],
                           input=a_dot(afd), text=True, check=True)
        print(f"{nombre}: {len(afd.estados)} estados, {len(afd.tabla())} transiciones")


if __name__ == "__main__":
    main()
