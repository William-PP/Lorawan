import heapq

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
