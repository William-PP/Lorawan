from .config import LIMITE_PAYLOAD
from .codec import codificar

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


def dividir(texto):
    """
    Separa el texto descomprimido en lecturas (por '|') y campos (por '&').
    Cada lectura debe terminar en '|'; si no, el bloque está corrupto.
    """
    if texto and not texto.endswith('|'):
        raise ValueError("Bloque sin separador final: posible corrupción")

    lecturas = []
    for lectura in texto.split('|')[:-1]:   # el último elemento tras '|' es vacío
        lecturas.append(lectura.split('&'))
    return lecturas