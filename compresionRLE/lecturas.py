"""
lecturas.py

Conoce el formato del sensor:
    ph&uptime_s&temperature_c&version&conductivity_uS_cm|

Convierte un bloque de lecturas en columnas y viceversa.
No sabe nada de RLE ni de Huffman.
"""

SEP_LECTURA = '|'
SEP_CAMPO = '&'


def separar_lecturas(bloque, num_campos):
    """Bloque -> lista de lecturas, cada una con sus campos como texto."""
    if not bloque.endswith(SEP_LECTURA):
        raise ValueError("Bloque sin separador final")
    filas = []
    for lectura in bloque[:-1].split(SEP_LECTURA):
        campos = lectura.split(SEP_CAMPO)
        if len(campos) != num_campos or '' in campos:
            raise ValueError(f"Lectura inválida: {lectura!r}")
        filas.append(campos)
    return filas


def a_columnas(filas, num_campos):
    """Columna k = campo k de todas las lecturas."""
    return [[fila[k] for fila in filas] for k in range(num_campos)]


def a_bloque(columnas):
    """Columnas -> bloque de lecturas. Exige que todas tengan la misma longitud."""
    if not columnas:
        raise ValueError("Sin columnas")
    n = len(columnas[0])
    if any(len(col) != n for col in columnas):
        raise ValueError("Las columnas no tienen la misma longitud")
    return ''.join(
        SEP_CAMPO.join(col[i] for col in columnas) + SEP_LECTURA
        for i in range(n)
    )
