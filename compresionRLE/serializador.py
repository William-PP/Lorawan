"""
serializador.py

Convierte N y las columnas RLE en el texto que comprime Huffman:

    N|valor:veces&valor:veces|valor:veces|...|

Separadores de estructura:
    |  separa N y cada columna
    &  separa los pares dentro de una columna
    :  separa el valor de su número de repeticiones

Estos tres símbolos no pueden aparecer dentro de un valor.
"""

SEP_COLUMNA = '|'
SEP_PAR = '&'
SEP_VECES = ':'
SIMBOLOS_ESTRUCTURA = frozenset(SEP_COLUMNA + SEP_PAR + SEP_VECES)


def serializar(n, columnas_rle):
    """(N, columnas RLE) -> texto."""
    partes = [f"{n}{SEP_COLUMNA}"]
    for pares in columnas_rle:
        if not pares:
            raise ValueError("Columna vacía: no se puede serializar")
        partes.append(SEP_PAR.join(f"{v}{SEP_VECES}{k}" for v, k in pares))
        partes.append(SEP_COLUMNA)
    return ''.join(partes)


def deserializar(texto, num_columnas):
    """Texto -> (N, columnas RLE). Valida la estructura antes de usarla."""
    if not texto.endswith(SEP_COLUMNA):
        raise ValueError("Texto sin separador final")

    trozos = texto.split(SEP_COLUMNA)        # [N, col1, ..., colK, '']
    if len(trozos) != num_columnas + 2 or trozos[-1] != '':
        raise ValueError("Número de columnas incorrecto")

    try:
        n = int(trozos[0])
    except ValueError:
        raise ValueError(f"N no es un entero: {trozos[0]!r}")

    columnas_rle = []
    for col in trozos[1:-1]:
        pares = []
        for par in col.split(SEP_PAR):
            valor, sep, veces = par.rpartition(SEP_VECES)
            if not sep or valor == '':
                raise ValueError(f"Par mal formado: {par!r}")
            pares.append((valor, int(veces)))
        columnas_rle.append(pares)
    return n, columnas_rle
