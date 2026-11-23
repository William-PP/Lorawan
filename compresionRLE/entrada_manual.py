"""
entrada_manual.py

Comprime un bloque con RLE. La entrada puede ser un archivo generado por
GeneradorDatos o un bloque escrito/pegado en la terminal.
Sin -o muestra el texto serializado; con -o lo escribe en un .txt.
No modifica el algoritmo: solo importa y llama a las funciones existentes.

Uso desde la raíz del proyecto:
    python -B -m compresionRLE.entrada_manual -f datos.txt -o salida.txt -r
    python -B -m compresionRLE.entrada_manual -f datos.txt -r
    python -B -m compresionRLE.entrada_manual
"""
import argparse
import sys
from pathlib import Path

from .pipeline import preparar, reconstruir


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
    ap = argparse.ArgumentParser(description="Comprime un bloque con RLE.")
    ap.add_argument("-f", "--archivo",
                    help="lee el bloque desde este archivo (p. ej. datos.txt)")
    ap.add_argument("-o", "--salida",
                    help="escribe el texto serializado en este .txt; si se omite, lo imprime")
    ap.add_argument("--campos", type=int, default=5,
                    help="número de campos por lectura")
    ap.add_argument("-r", "--roundtrip", action="store_true",
                    help="verifica que reconstruir recupera el bloque")
    p = ap.parse_args(argv)

    if p.campos < 1:
        ap.error("--campos debe ser al menos 1")

    try:
        bloque = leer_bloque(p.archivo)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"Error al leer la entrada: {exc}", file=sys.stderr)
        return 1

    if not bloque:
        print("Sin bloque; nada que comprimir.", file=sys.stderr)
        return 1

    try:
        serializado = preparar(bloque, p.campos)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Original: {len(bloque)} caracteres")
    print(f"RLE:      {len(serializado)} caracteres")

    if p.salida:
        try:
            ruta = Path(p.salida)
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(serializado, encoding="ascii")
        except OSError as exc:
            print(f"Error al escribir la salida: {exc}", file=sys.stderr)
            return 1
        print(f"Escrito:  {ruta} ({len(serializado)} caracteres)", file=sys.stderr)
    else:
        print(f"Texto:    {serializado}")

    if p.roundtrip:
        ok = reconstruir(serializado, p.campos) == bloque
        print(f"Roundtrip: {ok}")
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
