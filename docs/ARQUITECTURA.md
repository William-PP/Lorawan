# Arquitectura del proyecto LoRaWAN

**Fecha:** 2026-11-23
**Archivo anterior:** `docs/ANALISIS_METODOS.md` (renombrado el 2026-11-23)

El nombre antiguo ya no describía el contenido: el documento ya no analiza los
métodos del eliminado `algoritmo#1.py`, sino la estructura modular del proyecto,
sus contratos de datos y su forma de uso. Por eso ahora se llama
`ARQUITECTURA.md`.

---

## 1. Estructura actual

```
Lorawan/
├── .gitignore
├── README.md                      24 B, UTF-16, solo "# Lorawan"
├── compresionHuffman/
│   ├── __init__.py
│   ├── arbol_Huffman.py
│   ├── codec.py
│   ├── config.py
│   └── empaquetado.py
├── GeneradorDatos/
│   ├── __init__.py
│   ├── config_generador.py
│   ├── generador_lecturas.py
│   └── generar_datos.py
├── docs/
│   └── ARQUITECTURA.md            este archivo
└── tests/                         vacío
```

Ya no existen `algoritmo#1.py`, `datos_Temperatura.py` ni las copias de
`config.py` y `empaquetado.py` en la raíz. El alfabeto y los límites viven solo
en `compresionHuffman/config.py`.

### Grafo de dependencias

```
compresionHuffman/config.py ──────────────> compresionHuffman/codec.py ──> compresionHuffman/empaquetado.py
compresionHuffman/arbol_Huffman.py ───────> compresionHuffman/codec.py
compresionHuffman/config.py ──────────────> GeneradorDatos/generador_lecturas.py ──> GeneradorDatos/generar_datos.py
GeneradorDatos/config_generador.py ─> GeneradorDatos/generar_datos.py
```

Todos los módulos internos usan imports relativos (`from .config import ...`)
o imports absolutos desde la raíz (`from compresionHuffman.config import ...`). No hay
entry point ni pruebas automáticas: `tests/` está vacío.

---

## 2. Responsabilidades

| Archivo | Responsabilidad |
|---|---|
| `compresionHuffman/config.py` | Alfabeto, longitudes, límites por SF y constantes |
| `compresionHuffman/arbol_Huffman.py` | Construcción del árbol con `heapq` y tabla de códigos |
| `compresionHuffman/codec.py` | `indices`, `contar`, `codificar`, `decodificar` |
| `compresionHuffman/empaquetado.py` | `agrupar` (voraz por SF) y `dividir` (por `\|` y `&`) |
| `GeneradorDatos/config_generador.py` | Valores por defecto del generador |
| `GeneradorDatos/generador_lecturas.py` | Lógica pura: ruido, clamp y validación |
| `GeneradorDatos/generar_datos.py` | CLI con `argparse`; imprime o escribe archivo |

---

## 3. Formato de datos y decisiones de diseño

- **Alfabeto:** 13 símbolos (`0`-`9`, `.`, `&`, `|`). `|` cierra la lectura y `&`
  separa los 5 campos:

  ```
  ph&uptime_s&temperature_c&version&conductivity_uS_cm|
  ```

- **Trama codificada:** `N bytes de conteos` + `2 bytes de longitud` + `cuerpo
  de bits con padding a múltiplo de 8`. Con `N = len(alfabeto) = 13`, la
  cabecera mide 15 bytes.
- **Longitud en 2 bytes (`BYTES_LONGITUD = 2`):** necesaria porque en SF7 caben
  17 lecturas de 27 caracteres (459 símbolos), por encima de los 255 que
  cubriría 1 byte.
- **Saturación (`MAX_CONTEO = 255`):** cada contador cabe en 1 byte; por encima
  de 255 deja de incrementarse (decisión del artículo).
- **Desempate del árbol:** por secuencia de creación, para no comparar `int`
  contra `tuple` en el heap.
- **Decodificación:** usa la longitud de la cabecera, así que el padding nunca
  se interpreta como símbolo.
- **`dividir(texto)`:** devuelve una lista de campos por lectura:

  ```python
  dividir("7.0&0&25.00&1&300|") == [['7.0', '0', '25.00', '1', '300']]
  ```

- **Límites de payload:** SF7 = 222 bytes, SF12 = 51 bytes.

---

## 4. Cómo usar el generador de datos

### 4.1 Comando básico

Siempre desde la raíz del proyecto:

```powershell
python -m GeneradorDatos.generar_datos
```

Es importante usar `-m` en lugar de `python GeneradorDatos/generar_datos.py`:
el módulo usa imports relativos dentro del paquete y necesita que la raíz esté
en `sys.path` para encontrar `compresionHuffman`.

Con los valores por defecto imprime 10 lecturas en pantalla:

```text
7.0&0&24.91&1&298|
7.1&60&24.94&1&270|
...
```

### 4.2 Opciones de la línea de comandos

| Opción | Default | Descripción |
|---|---|---|
| `-n N` | `10` | Número de lecturas (mínimo 1) |
| `--semilla N` | `42` | Misma semilla + mismos parámetros = mismos datos |
| `--modo MODO` | `normal` | `uniforme`, `normal` o `senoidal` |
| `--periodo N` | `24` | Lecturas por ciclo; solo afecta al modo `senoidal` (mínimo 1) |
| `--version N` | `1` | Campo `version` de cada lectura |
| `--uptime-inicial N` | `0` | Segundos del primer mensaje |
| `--intervalo-s N` | `60` | Segundos entre lecturas consecutivas |
| `--ph-media F` | `7.0` | Media del pH |
| `--ph-amp F` | `0.2` | Amplitud del ruido del pH |
| `--temp-media F` | `25.0` | Media de temperatura en °C |
| `--temp-amp F` | `0.5` | Amplitud del ruido de temperatura |
| `--temp-tendencia F` | `0.0` | Cambio de temperatura por lectura |
| `--cond-media F` | `300.0` | Media de conductividad en µS/cm |
| `--cond-amp F` | `20.0` | Amplitud del ruido de conductividad |
| `--cond-max N` | `99999` | Máximo de conductividad |
| `--formato F` | `lineas` | `lineas` (una por línea) o `bloque` (todo junto) |
| `-o, --salida RUTA` | sin salida | Archivo de destino; si se omite, imprime en pantalla |

Los rangos `PH_MIN/PH_MAX = 0.0/14.0` y `TEMP_MIN/TEMP_MAX = 0.0/99.99` no
tienen opción CLI: se editan en `GeneradorDatos/config_generador.py`. Ese mismo
archivo contiene todos los valores por defecto; cámbialo para modificar el
comportamiento habitual.

### 4.3 Ejemplos

```powershell
# Dos lecturas, salida en pantalla
python -m GeneradorDatos.generar_datos -n 2

# 20 lecturas con ruido senoidal, todas en una sola línea
python -m GeneradorDatos.generar_datos -n 20 --modo senoidal --periodo 24 --formato bloque

# 100 lecturas reproducibles, guardadas en archivo
python -m GeneradorDatos.generar_datos -n 100 --semilla 7 -o lecturas.txt

# Sensores con otros valores
python -m GeneradorDatos.generar_datos --modo uniforme --temp-media 22 --temp-amp 0.2 --cond-media 500
```

Salida real del primer ejemplo:

```text
7.0&0&24.91&1&298|
7.1&60&24.94&1&270|
```

Salida real del modo `bloque` con `-n 3 --modo senoidal`:

```text
7.0&0&24.99&1&300|7.1&60&25.12&1&302|7.1&120&25.24&1&310|
```

Con `-o`, el mensaje `N lecturas escritas en RUTA` va a `stderr` y el archivo
se escribe en ASCII; sin `-o`, el contenido va a `stdout`. En ambos casos el
archivo o la salida termina con un salto de línea.

### 4.4 Formato de cada lectura

```
7.0 & 0 & 24.91 & 1 & 298 |
 ┬     ┬    ┬      ┬    ┬  └─ cierre de lectura
 │     │    │      │    └──── conductividad entera (µS/cm)
 │     │    │      └───────── versión
 │     │    └──────────────── temperatura con 2 decimales
 │     └───────────────────── uptime en segundos
 └─────────────────────────── pH con 1 decimal
```

`generar_lecturas` valida cada lectura: debe terminar en `|`, tener exactamente
un `|`, solo caracteres del alfabeto y 5 campos no vacíos. Si cambias
`ALFABETOS` en `compresionHuffman/config.py`, revisa también la plantilla
`f"{ph:.1f}&{uptime}&{temp:.2f}&{cfg['version']}&{cond}|"`.

### 4.5 Uso desde Python (generar + comprimir + recuperar)

```python
from compresionHuffman.config import ALFABETOS
from compresionHuffman.codec import decodificar
from compresionHuffman.empaquetado import agrupar, dividir
from GeneradorDatos.generar_datos import a_configuracion, leer_argumentos
from GeneradorDatos.generador_lecturas import generar_lecturas

ab = ALFABETOS["concreto"]
lecturas = generar_lecturas(a_configuracion(leer_argumentos(["-n", "10"])))

n, trama = agrupar(lecturas, ab, 7)          # SF7: 10 lecturas caben en 102 bytes
recuperadas = dividir(decodificar(trama, ab))
assert recuperadas == [lectura[:-1].split("&") for lectura in lecturas]
```

Verificado: con 10 lecturas, SF7 admite las 10 en 102 bytes; SF12 solo admite 4
en 48 bytes. El roundtrip es correcto.

También puedes generar sin pasar por la CLI:

```python
from GeneradorDatos.generador_lecturas import generar_lecturas

cfg = {
    "n": 5, "semilla": 42, "modo": "normal", "periodo": 24,
    "version": 1, "uptime_inicial": 0, "intervalo_s": 60,
    "ph_media": 7.0, "ph_amp": 0.2, "ph_min": 0.0, "ph_max": 14.0,
    "temp_media": 25.0, "temp_amp": 0.5, "temp_tendencia": 0.0,
    "temp_min": 0.0, "temp_max": 99.99,
    "cond_media": 300.0, "cond_amp": 20.0, "cond_max": 99999,
}
lecturas = generar_lecturas(cfg)
```

---

## 5. Correcciones aplicadas el 2026-11-23

| Problema | Corrección |
|---|---|
| `empaquetado.py` de la raíz importaba `codec`, que ya no estaba allí | Se borraron `config.py` y `empaquetado.py` de la raíz (copias byte-idénticas a las de `compresionHuffman/`) |
| `compresionHuffman/` no funcionaba como paquete (`No module named 'arbol_Huffman'`) | Se añadió `compresionHuffman/__init__.py` y se cambiaron los imports a `from .arbol_Huffman ...`, `from .config ...`, `from .codec ...` |
| El generador no encontraba `config` ni `config_generador` | Se añadió `GeneradorDatos/__init__.py`, se cambió a `from compresionHuffman.config import ALFABETOS` y a `from . import config_generador as C` / `from .generador_lecturas import ...`; se documentó el uso con `python -m` |
| El docstring de `config_generador.py` seguía apuntando a `config.py` | Ahora indica `compresionHuffman/config.py` |

---

## 6. Verificación

Comandos ejecutados sobre el proyecto final (con `python -B`, sin generar
`.pyc`):

```powershell
python -B -c "from compresionHuffman.codec import codificar, decodificar; from compresionHuffman.empaquetado import agrupar, dividir; from compresionHuffman.config import ALFABETOS; ab=ALFABETOS['concreto']; m='7.0&0&25.00&1&300|'; t=codificar(m,ab); print(decodificar(t,ab)==m, dividir(m), agrupar([m]*5,ab,12)[0])"
python -B -m GeneradorDatos.generar_datos -n 2
```

Resultados:

```text
True [['7.0', '0', '25.00', '1', '300']] 5
7.0&0&24.91&1&298|
7.1&60&24.94&1&270|
```

Además se comprobó la sintaxis de los 9 archivos `.py`, el roundtrip de 10
lecturas generadas y la escritura con `--formato bloque -o`.

---

## 7. Estado de Git al escribir este documento

```
## main...origin/main
 D arbol_Huffman.py
 D codec.py
 D config.py
 D datos_Temperatura.py
 D docs/ANALISIS_METODOS.md
 D empaquetado.py
?? GeneradorDatos/
?? compresionHuffman/
?? docs/ARQUITECTURA.md
```

`origin/main` sigue en `e0a024e`. Ninguno de estos cambios está confirmado ni
subido. Git detectará los renombrados al crear el commit.

## 8. Observaciones pendientes

- `tests/` está vacío: no hay pruebas automáticas.
- `README.md` sigue en UTF-16 y contiene solo `# Lorawan`.
- `LONG_MSG = {"concreto": 27}` dice «bytes por lectura» pero 27 es el número de
  caracteres; además, el constante no se usa en ningún módulo.
- `codificar` usa el literal `0xFFFF` en lugar de una constante de configuración.
- `agrupar` no exige que todos los mensajes tengan la misma longitud; si se
  mezclan, `dividir` puede dar campos inconsistentes.
