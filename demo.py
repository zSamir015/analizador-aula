"""Demostración por consola de la validación de cadenas (Etapa 2, punto 2).

Uso:
    python3 demo.py                      # solicita la ruta del archivo
    python3 demo.py ejemplos/horario_valido.txt
"""

import sys

from aula import analizar_archivo
from aula.sintaxis import SENTENCIAS


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else input("Archivo de entrada: ").strip()
    validas = invalidas = 0
    try:
        for r in analizar_archivo(ruta):
            estado = "VÁLIDA" if r.valida else "INVÁLIDA"
            print(f"\nLínea {r.numero}: {r.texto.strip()}")
            for tok in r.tokens:
                print(f"    {tok.tipo:<15} {tok.lexema}")
            for err in r.errores:
                print(f"    ✗ {err}")
            sufijo = f" ({r.sentencia}: {SENTENCIAS[r.sentencia]})" if r.valida else ""
            print(f"  → {estado}{sufijo}")
            if r.valida:
                validas += 1
            else:
                invalidas += 1
    except FileNotFoundError:
        print(f"No se encontró el archivo '{ruta}'")
        return 1
    print(f"\nResumen: {validas} válidas, {invalidas} inválidas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
