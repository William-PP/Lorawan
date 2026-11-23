"""
entrada_manual.py

Comprime un bloque con Huffman. La entrada puede ser un archivo generado por
GeneradorDatos o un bloque escrito/pegado en la terminal.
Sin -o muestra la trama en hex; con -o la escribe como archivo binario (.bin).
No modifica el algoritmo: solo importa y llama a las funciones existentes.

Uso desde la raíz del proyecto:
    python -B -m compresionHuffman.entrada_manual -f datos.txt -o salida.bin -r
    python -B -m compresionHuffman.entrada_manual -f datos.txt -r
    python -B -m compresionHuffman.entrada_manual
"""
import argparse
import sys
from pathlib import Path

from .codec import codificar, decodificar
from .config import ALFABETOS


def leer_bloque(archivo=None):
    """Lee el bloque desde un archivo, desde stdin o de forma interactiva."""
    if archivo:
        return Path(archivo).read_text(encoding="ascii").replace("\r", "").replace("\n", "")

    if not sys.stdin.isatty():
        return sys.stdin.read().replace("\r", "").replace("\n", "")

    print("Pega el bloque (lecturas terminadas en '|').")
    print("Línea vacía para terminar de escribir; Ctrl+Z/Ctrl+D para salir:")
    lineas = []
    while True:
        try:
            linea = input()
        except EOFError:
            break
        if linea == "":
            break
        lineas.append(linea)
    return "".join(lineas)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Comprime un bloque con Huffman.")
    ap.add_argument("-f", "--archivo",
                    help="lee el bloque desde este archivo (p. ej. datos.txt)")
    ap.add_argument("-o", "--salida",
                    help="escribe la trama en este .bin; si se omite, imprime el hex")
    ap.add_argument("--alfabeto", default="sensor", choices=sorted(ALFABETOS),
                    help="clave del alfabeto a usar")
    ap.add_argument("-r", "--roundtrip", action="store_true",
                    help="verifica que decodificar recupera el bloque")
    p = ap.parse_args(argv)

    try:
        bloque = leer_bloque(p.archivo)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"Error al leer la entrada: {exc}", file=sys.stderr)
        return 1

    if not bloque:
        print("Sin bloque; nada que comprimir.", file=sys.stderr)
        return 1

    ab = ALFABETOS[p.alfabeto]
    try:
        trama = codificar(bloque, ab)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Original: {len(bloque)} caracteres")
    print(f"Huffman:  {len(trama)} bytes")

    if p.salida:
        try:
            ruta = Path(p.salida)
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_bytes(trama)
        except OSError as exc:
            print(f"Error al escribir la salida: {exc}", file=sys.stderr)
            return 1
        print(f"Escrito:  {ruta} ({len(trama)} bytes)", file=sys.stderr)
    else:
        print(f"Hex:      {trama.hex()}")

    if p.roundtrip:
        ok = decodificar(trama, ab) == bloque
        print(f"Roundtrip: {ok}")
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
