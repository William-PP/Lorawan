from .arbol_Huffman import construir_arbol, tabla_codigos
from .config import MAX_CONTEO, BYTES_LONGITUD

def contar(texto, alfabeto):
    idx = indices(alfabeto)
    conteos = [0] * len(alfabeto)
    for ch in texto:
        if ch not in idx:
            raise ValueError(f"Carácter fuera del alfabeto: {ch!r}")
        i = idx[ch]
        if conteos[i] < MAX_CONTEO:            # saturación (artículo)
            conteos[i] += 1
    return conteos


def codificar(texto, alfabeto):
    """Trama = N bytes de conteos + 2 bytes de longitud + bits (DECISIÓN 1)."""
    if len(texto) > 0xFFFF:
        raise ValueError("Texto demasiado largo: máximo 65535 símbolos")
    conteos = contar(texto, alfabeto)
    raiz = construir_arbol(conteos)
    cod = tabla_codigos(raiz)
    idx = indices(alfabeto)

    bits = ''.join(cod[idx[ch]] for ch in texto)
    bits += '0' * (-len(bits) % 8)
    cuerpo = int(bits, 2).to_bytes(len(bits) // 8, 'big') if bits else b''

    longitud = len(texto).to_bytes(BYTES_LONGITUD, 'big')   # DECISIÓN 1
    return bytes(conteos) + longitud + cuerpo


def decodificar(trama, alfabeto):
    N = len(alfabeto)
    if len(trama) < N + BYTES_LONGITUD:
        raise ValueError("Trama demasiado corta")
    conteos = list(trama[:N])
    longitud = int.from_bytes(trama[N:N + BYTES_LONGITUD], 'big')   # DECISIÓN 1
    cuerpo = trama[N + BYTES_LONGITUD:]
    if longitud == 0:
        return ''

    raiz = construir_arbol(conteos)
    if raiz is None:
        raise ValueError("Conteos vacíos: la trama no tiene símbolos")
    bits = ''.join(f'{b:08b}' for b in cuerpo)

    salida = []
    pos = 0
    nodo = raiz
    while len(salida) < longitud:
        if pos >= len(bits):
            raise ValueError("Trama truncada")
        nodo = nodo[int(bits[pos])]
        pos += 1
        if isinstance(nodo, int):
            salida.append(alfabeto[nodo])
            nodo = raiz
    return ''.join(salida)

def indices(alfabeto):
    return {c: i for i, c in enumerate(alfabeto)}