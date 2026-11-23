"""
entrada_manual.py

Comprime o descomprime el pipeline combinado RLE -> Huffman desde la terminal.

Sin -d: bloque de texto -> texto RLE -> trama Huffman (.bin).
Con -d: trama Huffman (.bin) -> texto RLE -> bloque de texto (.txt).

No modifica los algoritmos: usa las funciones existentes de compresionRLE y
compresionHuffman.

Uso desde la raíz del proyecto:
    python -B -m compresionCombinado.entrada_manual -f datos.txt -o combinado.bin --intermedio rle.txt -r
    python -B -m compresionCombinado.entrada_manual -d -f combinado.bin -o recuperado.txt --intermedio rle_recuperado.txt -r
"""
import argparse
import sys
from pathlib import Path

from compresionHuffman.codec import codificar, decodificar
from compresionHuffman.config import ALFABETOS
from compresionRLE.pipeline import preparar, reconstruir


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


def escribir_bytes(ruta, datos):
    """Escribe bytes creando la carpeta si hace falta."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(datos)
    return ruta


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Comprime o descomprime el pipeline RLE -> Huffman.")
    ap.add_argument("-d", "--descomprimir", action="store_true",
                    help="descomprime la trama en vez de comprimir el bloque")
    ap.add_argument("-f", "--archivo",
                    help="entrada: bloque .txt si comprimes, trama .bin si descomprimes")
    ap.add_argument("-o", "--salida",
                    help="salida: .bin si comprimes, .txt si descomprimes")
    ap.add_argument("--intermedio",
                    help="archivo .txt para el texto RLE (se escribe al comprimir "
                         "y también al descomprimir)")
    ap.add_argument("--campos", type=int, default=5,
                    help="número de campos por lectura")
    ap.add_argument("--alfabeto", default="sensor", choices=sorted(ALFABETOS),
                    help="clave del alfabeto a usar")
    ap.add_argument("--sin-salto", action="store_true",
                    help="al descomprimir, no añadir salto de línea al bloque recuperado")
    ap.add_argument("-r", "--roundtrip", action="store_true",
                    help="verifica las dos etapas de la operación inversa")
    p = ap.parse_args(argv)

    if p.campos < 1:
        ap.error("--campos debe ser al menos 1")

    ab = ALFABETOS[p.alfabeto]

    try:
        if p.descomprimir:
            trama = leer_trama(p.archivo)
            if not trama:
                print("Sin trama; nada que descomprimir.", file=sys.stderr)
                return 1
            serializado = decodificar(trama, ab)
            bloque = reconstruir(serializado, p.campos)
            texto = bloque if p.sin_salto else bloque + "\n"

            print(f"Trama:      {len(trama)} bytes")
            print(f"RLE:        {len(serializado)} caracteres")
            print(f"Recuperado: {len(bloque)} caracteres")

            if p.intermedio:
                ruta = escribir_texto(p.intermedio, serializado)
                print(f"Intermedio: {ruta} ({len(serializado)} caracteres)",
                      file=sys.stderr)

            if p.salida:
                ruta = escribir_texto(p.salida, texto)
                print(f"Escrito:    {ruta} ({ruta.stat().st_size} bytes)", file=sys.stderr)
            else:
                print(f"Texto:      {bloque}")

            if p.roundtrip:
                ok = (codificar(serializado, ab) == trama
                      and preparar(bloque, p.campos) == serializado)
                print(f"Roundtrip: {ok}")
                return 0 if ok else 1
            return 0

        bloque = leer_texto(p.archivo)
        if not bloque:
            print("Sin bloque; nada que comprimir.", file=sys.stderr)
            return 1
        serializado = preparar(bloque, p.campos)
        trama = codificar(serializado, ab)

        print(f"Original: {len(bloque)} caracteres")
        print(f"RLE:      {len(serializado)} caracteres")
        print(f"Combinado:{len(trama):>5} bytes")

        if p.intermedio:
            ruta = escribir_texto(p.intermedio, serializado)
            print(f"Intermedio: {ruta} ({len(serializado)} caracteres)",
                  file=sys.stderr)

        if p.salida:
            ruta = escribir_bytes(p.salida, trama)
            print(f"Escrito:  {ruta} ({len(trama)} bytes)", file=sys.stderr)
        else:
            print(f"Hex:      {trama.hex()}")

        if p.roundtrip:
            ok = (decodificar(trama, ab) == serializado
                  and reconstruir(serializado, p.campos) == bloque)
            print(f"Roundtrip: {ok}")
            return 0 if ok else 1
        return 0

    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
