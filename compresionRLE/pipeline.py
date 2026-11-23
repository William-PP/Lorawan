"""
pipeline.py

Une los pasos del formato por columnas:

    bloque -> lecturas -> columnas -> RLE por columna -> texto serializado

y la operación inversa. No conoce Huffman: el compresor se aplica fuera.
"""
from .lecturas import a_bloque, a_columnas, separar_lecturas


def _rle_columna(valores):
    """Columna de valores de texto -> pares (valor, veces), solo para este formato."""
    pares = []
    for v in valores:
        if pares and pares[-1][0] == v:
            pares[-1] = (v, pares[-1][1] + 1)
        else:
            pares.append((v, 1))
    return pares


def _des_rle_columna(pares):
    """Pares (valor, veces) -> columna de valores."""
    columna = []
    for valor, veces in pares:
        if veces < 1:
            raise ValueError(f"Repetición no válida: {veces}")
        columna.extend([valor] * veces)
    return columna
from .serializador import deserializar, serializar


def preparar(bloque, num_campos):
    """Bloque de lecturas -> texto serializado, listo para comprimir."""
    filas = separar_lecturas(bloque, num_campos)
    if not filas:
        raise ValueError("El bloque no contiene lecturas")
    columnas = a_columnas(filas, num_campos)
    columnas_rle = [_rle_columna(col) for col in columnas]
    return serializar(len(filas), columnas_rle)


def reconstruir(texto, num_campos):
    """Texto serializado -> bloque de lecturas original."""
    n, columnas_rle = deserializar(texto, num_campos)
    if len(columnas_rle) != num_campos:
        raise ValueError("Número de columnas incorrecto")

    columnas = []
    for pares in columnas_rle:
        col = _des_rle_columna(pares)
        if len(col) != n:
            raise ValueError(f"Columna con {len(col)} valores, se esperaban {n}")
        columnas.append(col)
    return a_bloque(columnas)
