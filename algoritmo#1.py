# Decisiones propias y desviaciones respecto a Júnior et al. (2023)

## Decisiones propias
"""
1. Campo de longitud de 2 bytes

El artículo no define cómo el receptor sabe cuántos símbolos decodificar. Esta versión añade un campo de longitud de 2 bytes (big-endian) entre la cabecera y el cuerpo comprimido.

Motivo: la suma de conteos sólo sirve si no hubo saturación en 255. Como el artículo no excluye la saturación, necesitamos un campo independiente.

Coste: la cabecera pasa de N bytes a N + 2 bytes.

2. Desempate determinista en el árbol

El artículo no especifica el orden de los nodos con igual peso. Esta versión desempata por la secuencia de creación (hojas por índice, nodos internos por orden de creación).

Motivo: sin un desempate fijo, emisor y receptor pueden construir árboles distintos a partir de los mismos conteos.

3. Longitud fija por lectura

El artículo no describe cómo separar las lecturas del bloque decodificado. Se asume longitud fija por aplicación: 28 bytes (concreto) y 22 bytes (GPS), según el artículo.

Motivo: sin separadores ni campos de longitud por lectura, el receptor no puede recuperar la frontera entre mensajes.

4. Agrupamiento voraz en orden de llegada

El artículo habla de empaquetar hasta N mensajes sin describir la estrategia. Esta versión añade lecturas en orden hasta superar el límite de carga útil del SF.

5. Modo de respaldo sin comprimir

Esta versión no implementa este punto. Lo incluye la versión 3.

## Problema con la justificación de la saturación

El artículo afirma que, como la carga útil es de 222 bytes en SF7, ningún símbolo puede aparecer más de 222 veces en un paquete. Esta afirmación no es correcta para Huffman: lo que limita el paquete son los **bits**, no el número de símbolos. Un símbolo con código de 1 bit puede aparecer unas 1.776 veces en 222 bytes.

Por eso el campo de longitud de 2 bytes es necesario y no sólo una comodidad: sin él, un lote con un símbolo saturado no se puede decodificar.

**Nota sobre el tamaño de la longitud:** con 1 byte, el máximo son 255 símbolos por bloque. Para SF7 con 21 lecturas GPS de 22 bytes, el bloque tiene 462 símbolos, así que 2 bytes son necesarios.
"""
## Código

##Réplica de Júnior et al. (2023) con las decisiones propias marcadas como DECISIÓN.

import heapq
import random

ALFABETOS = {
    "concreto": ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                 '.', '<', '>', '&'],          # N = 14 (artículo)
}
LONG_MSG = {"concreto": 27}                    # bytes por lectura
LIMITE_PAYLOAD = {7: 222, 12: 51}              # bytes (artículo)
MAX_CONTEO = 255                               # (artículo)
BYTES_LONGITUD = 2                             # DECISIÓN 1


def contar(texto, alfabeto):
    idx = {c: i for i, c in enumerate(alfabeto)}
    conteos = [0] * len(alfabeto)
    for ch in texto:
        if ch not in idx:
            raise ValueError(f"Carácter fuera del alfabeto: {ch!r}")
        i = idx[ch]
        if conteos[i] < MAX_CONTEO:            # saturación (artículo)
            conteos[i] += 1
    return conteos


def construir_arbol(conteos):
    # DECISIÓN 2: desempate por secuencia de creación (hojas por índice).
    heap = [(n, i, i) for i, n in enumerate(conteos) if n > 0]
    if not heap:
        return None
    if len(heap) == 1:
        s = heap[0][2]
        return (s, s)
    heapq.heapify(heap)
    seq = len(conteos)
    while len(heap) > 1:
        p1, _, n1 = heapq.heappop(heap)
        p2, _, n2 = heapq.heappop(heap)
        heapq.heappush(heap, (p1 + p2, seq, (n1, n2)))
        seq += 1
    return heap[0][2]


def tabla_codigos(raiz):
    codigos = {}

    def recorrer(nodo, prefijo):
        if isinstance(nodo, int):
            codigos[nodo] = prefijo
            return
        recorrer(nodo[0], prefijo + '0')
        recorrer(nodo[1], prefijo + '1')

    if raiz is not None:
        recorrer(raiz, '')
    return codigos


def codificar(texto, alfabeto):
    """Trama = N bytes de conteos + 2 bytes de longitud + bits (DECISIÓN 1)."""
    conteos = contar(texto, alfabeto)
    raiz = construir_arbol(conteos)
    cod = tabla_codigos(raiz)
    idx = {c: i for i, c in enumerate(alfabeto)}

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


def agrupar(mensajes, alfabeto, sf):
    # DECISIÓN 4: agrupamiento voraz en orden de llegada.
    limite = LIMITE_PAYLOAD[sf]
    n = 0
    texto = ''
    trama = b''
    for m in mensajes:
        candidato = texto + m
        t = codificar(candidato, alfabeto)
        if len(t) > limite:
            break
        texto, trama, n = candidato, t, n + 1
    return n, trama


def dividir(texto, longitud):
    # DECISIÓN 3: longitud fija por lectura.
    if len(texto) % longitud:
        raise ValueError("Texto no múltiplo de la longitud de lectura")
    return [texto[i:i + longitud] for i in range(0, len(texto), longitud)]


def pruebas():
    for alfabeto in ALFABETOS.values():
        assert decodificar(codificar('', alfabeto), alfabeto) == ''
        assert decodificar(codificar('0' * 40, alfabeto), alfabeto) == '0' * 40
        ejemplo = ''.join(random.choices(alfabeto, k=300))   # supera 255: prueba la saturación
        assert decodificar(codificar(ejemplo, alfabeto), alfabeto) == ejemplo
    print("Pruebas: OK")


if __name__ == '__main__':
    random.seed(42)
    pruebas()


