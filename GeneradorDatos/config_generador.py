"""
config_generador.py

Valores por defecto del generador de lecturas.
Edita este archivo para cambiar el comportamiento habitual.
Cualquier valor puede sobrescribirse desde la línea de comandos.

El alfabeto no vive aquí: se toma de compresionHuffman/config.py, para que
generador y codec usen siempre el mismo.
"""

# --- Cantidad y reproducibilidad --------------------------------------------
N_LECTURAS = 40              # número de lecturas a generar
SEMILLA = 42                 # misma semilla = mismos datos

# --- Forma del ruido ---------------------------------------------------------
MODO = "normal"              # "uniforme", "normal" o "senoidal"
PERIODO = 24                 # lecturas por ciclo (solo modo senoidal)

# --- Campos del sensor -------------------------------------------------------
VERSION = 1

UPTIME_INICIAL = 0           # segundos del primer mensaje
INTERVALO_S = 60             # segundos entre lecturas consecutivas

PH_MEDIA = 7.0
PH_AMP = 0.2                 # ruido del pH
PH_MIN, PH_MAX = 0.0, 14.0

TEMP_MEDIA = 25.0            # °C
TEMP_AMP = 0.5               # ruido de temperatura, °C
TEMP_TENDENCIA = 0.0         # cambio por lectura, °C
TEMP_MIN, TEMP_MAX = 0.0, 99.99

COND_MEDIA = 300.0           # µS/cm
COND_AMP = 20.0              # ruido de conductividad, µS/cm
COND_MAX = 99999             # máximo; determina cuántos dígitos puede tener

# --- Salida ------------------------------------------------------------------
FORMATO = "lineas"           # "lineas" = un mensaje por línea; "bloque" = todo junto
SALIDA = None                # ruta de archivo, o None para pantalla
