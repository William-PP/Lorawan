from config import LIMITE_PAYLOAD
from codec import codificar

def agrupar(mensajes, alfabeto, sf):
    if sf not in LIMITE_PAYLOAD:
        raise ValueError(f"SF no soportado: {sf}. Válidos: {sorted(LIMITE_PAYLOAD)}")
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
    if mensajes and n == 0:
        raise ValueError("El primer mensaje no cabe en el payload de este SF")
    return n, trama


def dividir(texto, longitud):
    # DECISIÓN 3: longitud fija por lectura.
    if longitud <= 0:
        raise ValueError("La longitud de lectura debe ser mayor que 0")
    if len(texto) % longitud:
        raise ValueError("Texto no múltiplo de la longitud de lectura")
    return [texto[i:i + longitud] for i in range(0, len(texto), longitud)]
