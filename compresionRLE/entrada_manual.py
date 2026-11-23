"""
entrada_manual.py

Comprime o descomprime un bloque con RLE desde la terminal.

Sin -d comprime: la entrada es el bloque y la salida es texto serializado.
Con -d descomprime: la entrada es el texto serializado y la salida es el bloque.

No modifica el algoritmo: solo importa y llama a preparar/reconstruir.

Uso desde la raíz del proyecto:
    python -B -m compresionRLE.entrada_manual -f datos.txt -o salida.txt -r
    python -B -m compresionRLE.entrada_manual -d -f salida.txt -o recuperado.txt -r
"""
import argparse
import sys
from pathlib import Path

from .pipeline import preparar, reconstruir


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


def escribir_texto(ruta, texto):
    """Escribe texto ASCII creando la carpeta si hace falta."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="ascii")
    return ruta


def main(argv=None):
    ap = argparse.ArgumentParser(description="Comprime o descomprime con RLE.")
    ap.add_argument("-d", "--descomprimir", action="store_true",
                    help="reconstruye el bloque en vez de comprimirlo")
    ap.add_argument("-f", "--archivo",
                    help="archivo de entrada (bloque o texto serializado)")
    ap.add_argument("-o", "--salida",
                    help="archivo de salida (.txt en ambos modos)")
    ap.add_argument("--campos", type=int, default=5,
                    help="número de campos por lectura")
    ap.add_argument("--sin-salto", action="store_true",
                    help="al descomprimir, no añadir salto de línea al bloque recuperado")
    ap.add_argument("-r", "--roundtrip", action="store_true",
                    help="verifica que la operación inversa recupera la entrada")
    p = ap.parse_args(argv)

    if p.campos < 1:
        ap.error("--campos debe ser al menos 1")

    try:
        if p.descomprimir:
            serializado = leer_texto(
                p.archivo, "Pega el texto serializado (p. ej. 2|7.0:2|0:1&...).")
            if not serializado:
                print("Sin texto serializado; nada que descomprimir.", file=sys.stderr)
                return 1
            bloque = reconstruir(serializado, p.campos)
            texto = bloque if p.sin_salto else bloque + "\n"

            print(f"Serializado: {len(serializado)} caracteres")
            print(f"Recuperado:  {len(bloque)} caracteres")

            if p.salida:
                ruta = escribir_texto(p.salida, texto)
                print(f"Escrito:     {ruta} ({ruta.stat().st_size} bytes)", file=sys.stderr)
            else:
                print(f"Texto:       {bloque}")

            if p.roundtrip:
                ok = preparar(bloque, p.campos) == serializado
                print(f"Roundtrip: {ok}")
                return 0 if ok else 1
            return 0

        bloque = leer_texto(p.archivo)
        if not bloque:
            print("Sin bloque; nada que comprimir.", file=sys.stderr)
            return 1
        serializado = preparar(bloque, p.campos)

        print(f"Original: {len(bloque)} caracteres")
        print(f"RLE:      {len(serializado)} caracteres")

        if p.salida:
            ruta = escribir_texto(p.salida, serializado)
            print(f"Escrito:  {ruta} ({len(serializado)} caracteres)", file=sys.stderr)
        else:
            print(f"Texto:    {serializado}")

        if p.roundtrip:
            ok = reconstruir(serializado, p.campos) == bloque
            print(f"Roundtrip: {ok}")
            return 0 if ok else 1
        return 0

    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
