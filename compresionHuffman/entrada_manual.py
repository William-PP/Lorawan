"""
entrada_manual.py

Comprime o descomprime un bloque con Huffman desde la terminal.

Sin -d comprime: la entrada es texto y la salida es una trama binaria (.bin).
Con -d descomprime: la entrada es la trama (.bin) y la salida es el texto.

No modifica el algoritmo: solo importa y llama a codificar/decodificar.

Uso desde la raíz del proyecto:
    python -B -m compresionHuffman.entrada_manual -f datos.txt -o salida.bin -r
    python -B -m compresionHuffman.entrada_manual -d -f salida.bin -o recuperado.txt -r
"""
import argparse
import sys
from pathlib import Path

from .codec import codificar, decodificar
from .config import ALFABETOS


def leer_texto(archivo=None, mensaje="Pega el bloque (lecturas terminadas en '|')."):
    """Lee texto desde un archivo, desde stdin o de forma interactiva."""
    if archivo:
        return Path(archivo).read_text(encoding="ascii").replace("\r", "").replace("\n", "")

    if not sys.stdin.isatty():
        return sys.stdin.read().replace("\r", "").replace("\n", "")

    print(mensaje)
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


def leer_trama(archivo=None):
    """Lee bytes desde un archivo o desde stdin."""
    if archivo:
        return Path(archivo).read_bytes()
    if not sys.stdin.isatty():
        return sys.stdin.buffer.read()
    raise ValueError("Para descomprimir necesitas -f o una tubería con la trama")


def escribir_texto(ruta, texto):
    """Escribe texto ASCII creando la carpeta si hace falta."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="ascii")
    return ruta


def main(argv=None):
    ap = argparse.ArgumentParser(description="Comprime o descomprime con Huffman.")
    ap.add_argument("-d", "--descomprimir", action="store_true",
                    help="descomprime la trama en vez de comprimir el texto")
    ap.add_argument("-f", "--archivo",
                    help="entrada: texto si comprimes, trama .bin si descomprimes")
    ap.add_argument("-o", "--salida",
                    help="salida: .bin si comprimes, .txt si descomprimes")
    ap.add_argument("--alfabeto", default="sensor", choices=sorted(ALFABETOS),
                    help="clave del alfabeto a usar")
    ap.add_argument("--sin-salto", action="store_true",
                    help="al descomprimir, no añadir salto de línea al texto recuperado")
    ap.add_argument("-r", "--roundtrip", action="store_true",
                    help="verifica que la operación inversa recupera la entrada")
    p = ap.parse_args(argv)

    ab = ALFABETOS[p.alfabeto]

    try:
        if p.descomprimir:
            trama = leer_trama(p.archivo)
            if not trama:
                print("Sin trama; nada que descomprimir.", file=sys.stderr)
                return 1
            bloque = decodificar(trama, ab)
            texto = bloque if p.sin_salto else bloque + "\n"

            print(f"Trama:      {len(trama)} bytes")
            print(f"Recuperado: {len(bloque)} caracteres")

            if p.salida:
                ruta = escribir_texto(p.salida, texto)
                print(f"Escrito:    {ruta} ({ruta.stat().st_size} bytes)", file=sys.stderr)
            else:
                print(f"Texto:      {bloque}")

            if p.roundtrip:
                ok = codificar(bloque, ab) == trama
                print(f"Roundtrip: {ok}")
                return 0 if ok else 1
            return 0

        bloque = leer_texto(p.archivo)
        if not bloque:
            print("Sin bloque; nada que comprimir.", file=sys.stderr)
            return 1
        trama = codificar(bloque, ab)

        print(f"Original: {len(bloque)} caracteres")
        print(f"Huffman:  {len(trama)} bytes")

        if p.salida:
            ruta = Path(p.salida)
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_bytes(trama)
            print(f"Escrito:  {ruta} ({len(trama)} bytes)", file=sys.stderr)
        else:
            print(f"Hex:      {trama.hex()}")

        if p.roundtrip:
            ok = decodificar(trama, ab) == bloque
            print(f"Roundtrip: {ok}")
            return 0 if ok else 1
        return 0

    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
