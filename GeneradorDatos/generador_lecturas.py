"""
generador_lecturas.py

Genera lecturas en el formato del codec:
    ph&uptime_s&temperature_c&version&conductivity_uS_cm|

Solo contiene lógica. No lee argumentos ni escribe archivos,
así que puede importarse desde cualquier otro script.
"""
import math
import random

from compresionHuffman.config import ALFABETOS

ALFABETO = set(ALFABETOS["concreto"])
NUM_CAMPOS = 5
MODOS = ("uniforme", "normal", "senoidal")


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def ruido(rng, modo, amp, i, periodo):
    """Ruido de un campo en la lectura i, según el modo elegido."""
    if modo == "uniforme":
        return rng.uniform(-amp, amp)
    if modo == "normal":
        return rng.gauss(0.0, amp)
    if modo == "senoidal":
        return amp * math.sin(2 * math.pi * i / periodo) + rng.gauss(0.0, amp * 0.1)
    raise ValueError(f"Modo desconocido: {modo!r}")


def validar_lectura(lectura):
    """Comprueba separador final, alfabeto y número de campos."""
    if not lectura.endswith('|') or lectura.count('|') != 1:
        raise RuntimeError(f"Separador mal colocado: {lectura!r}")
    if not set(lectura) <= ALFABETO:
        raise RuntimeError(f"Carácter fuera del alfabeto: {lectura!r}")
    campos = lectura[:-1].split('&')
    if len(campos) != NUM_CAMPOS or any(c == '' for c in campos):
        raise RuntimeError(f"Número de campos incorrecto: {lectura!r}")
    return lectura


def generar_lecturas(cfg):
    """
    Devuelve una lista de cfg['N_LECTURAS'] lecturas.
    cfg es un diccionario con las claves de config_generador.py en minúscula.
    """
    rng = random.Random(cfg["semilla"])
    modo, periodo = cfg["modo"], cfg["periodo"]
    lecturas = []
    uptime = cfg["uptime_inicial"]

    for i in range(cfg["n"]):
        ph = clamp(cfg["ph_media"] + ruido(rng, modo, cfg["ph_amp"], i, periodo),
                   cfg["ph_min"], cfg["ph_max"])
        temp = clamp(cfg["temp_media"] + cfg["temp_tendencia"] * i
                     + ruido(rng, modo, cfg["temp_amp"], i, periodo),
                     cfg["temp_min"], cfg["temp_max"])
        cond = clamp(round(cfg["cond_media"] + ruido(rng, modo, cfg["cond_amp"], i, periodo)),
                     0, cfg["cond_max"])

        lectura = f"{ph:.1f}&{uptime}&{temp:.2f}&{cfg['version']}&{cond}|"
        lecturas.append(validar_lectura(lectura))
        uptime += cfg["intervalo_s"]
    return lecturas
