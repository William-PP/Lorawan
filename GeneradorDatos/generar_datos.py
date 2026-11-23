#!/usr/bin/env python3
"""
generar_datos.py

Línea de comandos del generador. Los valores por defecto vienen de
config_generador.py; cualquier argumento los sobrescribe para esa ejecución.

Ejemplos (desde la raíz del proyecto):
    python -m GeneradorDatos.generar_datos
    python -m GeneradorDatos.generar_datos -n 20 --modo senoidal --formato bloque -o bloque.txt
"""
import argparse
import sys

from . import config_generador as C
from .generador_lecturas import MODOS, generar_lecturas


def leer_argumentos(argv=None):
    ap = argparse.ArgumentParser(description="Generador de lecturas para el codec.")
    ap.add_argument("-n", type=int, default=C.N_LECTURAS, help="número de lecturas")
    ap.add_argument("--semilla", type=int, default=C.SEMILLA)
    ap.add_argument("--modo", choices=MODOS, default=C.MODO)
    ap.add_argument("--periodo", type=int, default=C.PERIODO, help="solo modo senoidal")

    ap.add_argument("--version", type=int, default=C.VERSION)
    ap.add_argument("--uptime-inicial", type=int, default=C.UPTIME_INICIAL)
    ap.add_argument("--intervalo-s", type=int, default=C.INTERVALO_S)

    ap.add_argument("--ph-media", type=float, default=C.PH_MEDIA)
    ap.add_argument("--ph-amp", type=float, default=C.PH_AMP)
    ap.add_argument("--temp-media", type=float, default=C.TEMP_MEDIA)
    ap.add_argument("--temp-amp", type=float, default=C.TEMP_AMP)
    ap.add_argument("--temp-tendencia", type=float, default=C.TEMP_TENDENCIA)
    ap.add_argument("--cond-media", type=float, default=C.COND_MEDIA)
    ap.add_argument("--cond-amp", type=float, default=C.COND_AMP)
    ap.add_argument("--cond-max", type=int, default=C.COND_MAX)

    ap.add_argument("--formato", choices=("lineas", "bloque"), default=C.FORMATO)
    ap.add_argument("-o", "--salida", default=C.SALIDA)
    p = ap.parse_args(argv)

    if p.n < 1:
        ap.error("-n debe ser al menos 1")
    if p.periodo < 1:
        ap.error("--periodo debe ser al menos 1")
    if min(p.ph_amp, p.temp_amp, p.cond_amp) < 0:
        ap.error("los ruidos no pueden ser negativos")
    if min(p.intervalo_s, p.uptime_inicial, p.cond_max) < 0:
        ap.error("uptime, intervalo y cond-max no pueden ser negativos")
    return p


def a_configuracion(p):
    """Convierte los argumentos en el diccionario que espera generar_lecturas."""
    return {
        "n": p.n,
        "semilla": p.semilla,
        "modo": p.modo,
        "periodo": p.periodo,
        "version": p.version,
        "uptime_inicial": p.uptime_inicial,
        "intervalo_s": p.intervalo_s,
        "ph_media": p.ph_media,
        "ph_amp": p.ph_amp,
        "ph_min": C.PH_MIN,
        "ph_max": C.PH_MAX,
        "temp_media": p.temp_media,
        "temp_amp": p.temp_amp,
        "temp_tendencia": p.temp_tendencia,
        "temp_min": C.TEMP_MIN,
        "temp_max": C.TEMP_MAX,
        "cond_media": p.cond_media,
        "cond_amp": p.cond_amp,
        "cond_max": p.cond_max,
    }


def main(argv=None):
    p = leer_argumentos(argv)
    lecturas = generar_lecturas(a_configuracion(p))

    separador = "" if p.formato == "bloque" else "\n"
    contenido = separador.join(lecturas) + "\n"

    if p.salida:
        with open(p.salida, "w", encoding="ascii") as f:
            f.write(contenido)
        print(f"{len(lecturas)} lecturas escritas en {p.salida}", file=sys.stderr)
    else:
        sys.stdout.write(contenido)


if __name__ == "__main__":
    main()
