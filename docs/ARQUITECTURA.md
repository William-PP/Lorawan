# Arquitectura del proyecto LoRaWAN

**Fecha:** 2026-11-23
**Actualizado:** 2026-11-23 — CLI de compresión con `-o` y carpeta `salidas/`
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
├── README.md                      guía rápida de comandos (UTF-8)
├── compresionHuffman/
│   ├── __init__.py
│   ├── arbol_Huffman.py
│   ├── codec.py
│   ├── config.py
│   ├── empaquetado.py
│   └── entrada_manual.py          CLI con -f / -o / -r
├── GeneradorDatos/
│   ├── __init__.py
│   ├── config_generador.py
│   ├── generador_lecturas.py
│   └── generar_datos.py
├── compresionRLE/
│   ├── __init__.py
│   ├── lecturas.py
│   ├── pipeline.py
│   ├── serializador.py
│   └── entrada_manual.py          CLI con -f / -o / -r
├── docs/
│   └── ARQUITECTURA.md            este archivo
├── salidas/
│   ├── README.md                  explicación de las carpetas de salida
│   ├── generador/.gitkeep         .txt plano (entrada)
│   ├── huffman/.gitkeep           .bin
│   ├── rle/.gitkeep               .txt
│   ├── combinado/.gitkeep         .bin (RLE -> Huffman)
│   └── descompresion/             .txt recuperados
│       ├── huffman/.gitkeep       desde el .bin de Huffman
│       ├── rle/.gitkeep           desde el texto RLE
│       └── combinado/.gitkeep     texto RLE + bloque final
└── tests/
    ├── __init__.py
    └── pruebas_rle.py             11 pruebas unittest
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
compresionRLE/lecturas.py ───────> compresionRLE/pipeline.py <── compresionRLE/serializador.py
compresionHuffman/entrada_manual.py ──> compresionHuffman/codec.py, config.py
compresionRLE/entrada_manual.py ──────> compresionRLE/pipeline.py
tests/pruebas_rle.py ────────────> compresionRLE/pipeline.py, compresionRLE/serializador.py
```

Todos los módulos internos usan imports relativos (`from .config import ...`)
o imports absolutos desde la raíz (`from compresionHuffman.config import ...`).
Los entry point son `GeneradorDatos/generar_datos.py` y los dos
`entrada_manual.py`, invocados con `python -m`; las pruebas automáticas están en
`tests/pruebas_rle.py`.

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
| `compresionHuffman/entrada_manual.py` | CLI Huffman: `-f`, `-o`, `--alfabeto`, `-r` |
| `compresionRLE/entrada_manual.py` | CLI RLE: `-f`, `-o`, `--campos`, `-r` |
| `compresionRLE/lecturas.py` | Bloque de lecturas ↔ columnas de campos |
| `compresionRLE/pipeline.py` | RLE por columnas: `preparar` y `reconstruir` |
| `compresionRLE/serializador.py` | Texto `N\|valor:veces&...\|...` ↔ columnas RLE |
| `tests/pruebas_rle.py` | 11 pruebas `unittest` del pipeline RLE |

---

## 3. Formato de datos y decisiones de diseño

- **Alfabeto (`ALFABETOS["sensor"]`):** 14 símbolos (`0`-`9`, `.`, `&`, `|`,
  `:`). `|` cierra la lectura, `&` separa los 5 campos y `:` aparece en el
  formato serializado del pipeline RLE:

  ```
  ph&uptime_s&temperature_c&version&conductivity_uS_cm|
  ```

- **Trama codificada:** `N bytes de conteos` + `2 bytes de longitud` + `cuerpo
  de bits con padding a múltiplo de 8`. Con `N = len(alfabeto) = 14`, la
  cabecera mide 16 bytes.
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
contenido termina con un salto de línea. En Windows se guarda como `\r\n`
(2 bytes), así que un bloque de 97 caracteres ocupa 99 bytes en disco. Los
scripts de compresión eliminan `\r` y `\n` al leer con `-f`, por lo que su
`Original:` coincide con el bloque generado en memoria. El generador no crea
carpetas intermedias, pero `salidas/generador` ya existe.

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

ab = ALFABETOS["sensor"]
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

### 4.6 Uso del pipeline RLE

`compresionRLE` aplica RLE por columnas y no conoce Huffman. `preparar` devuelve
texto serializado y `reconstruir` recupera el bloque original:

```python
from compresionRLE.pipeline import preparar, reconstruir

bloque = "7.0&0&25.00&1&300|7.0&60&25.01&1&301|"
serializado = preparar(bloque, 5)
# '2|7.0:2|0:1&60:1|25.00:1&25.01:1|1:2|300:1&301:1|'
assert reconstruir(serializado, 5) == bloque
```

El `:` del formato serializado está incluido en `ALFABETOS["sensor"]`, así que
la salida de `preparar` se puede comprimir con Huffman:

```python
from compresionHuffman.codec import codificar, decodificar
from compresionHuffman.config import ALFABETOS

ab = ALFABETOS["sensor"]
assert decodificar(codificar(serializado, ab), ab) == serializado
```

Pruebas automatizadas:

```powershell
python -B -m tests.pruebas_rle
python -B -m unittest discover -s tests -p "pruebas_*.py" -v
```

### 4.7 Comparar Huffman y RLE por separado

Para medir cada compresor sobre el mismo bloque, sin encadenarlos:

1. Genera un bloque reproducible (misma semilla y mismos parámetros).
2. Mide tres tamaños sobre ese mismo bloque:
   - **Original:** `len(bloque)` en bytes ASCII (1 byte por carácter).
   - **Huffman:** `len(codificar(bloque, ab))`; incluye la cabecera de 16 bytes.
   - **RLE:** `len(preparar(bloque, 5))`; es texto serializado ASCII, no una
     trama binaria.
3. Calcula los ratios respecto al original y la diferencia entre métodos.

**¿Archivo o memoria?** Para una comparación puntual basta generar en memoria y
medir en la misma ejecución: así ambos métodos ven exactamente los mismos bytes.
Guardar el bloque en un archivo es útil si quieres repetir la medición después,
auditarla o comparar varias corridas; en ese caso genera con `--formato bloque`
y lee el archivo antes de medir. El generador añade un salto de línea final
(`\r\n` en Windows), así que hay que quitar `\r` y `\n` para que el bloque sea
idéntico al generado en memoria.

Medición en memoria:

```python
from compresionHuffman.codec import codificar
from compresionHuffman.config import ALFABETOS
from compresionRLE.pipeline import preparar
from GeneradorDatos.generar_datos import a_configuracion, leer_argumentos
from GeneradorDatos.generador_lecturas import generar_lecturas

ab = ALFABETOS["sensor"]
bloque = "".join(generar_lecturas(
    a_configuracion(leer_argumentos(["-n", "100", "--semilla", "42"]))))

original = len(bloque)
huffman = len(codificar(bloque, ab))
rle = len(preparar(bloque, 5))
print(original, huffman, rle)
```

Medición desde archivo:

```powershell
python -B -m GeneradorDatos.generar_datos -n 100 --semilla 42 --formato bloque -o datos.txt
```

```python
from pathlib import Path
bloque = (Path("datos.txt").read_text(encoding="ascii")
          .replace("\r", "").replace("\n", ""))
```

Resultados verificados (semilla 42, modo `normal`):

| Lecturas | Original | Huffman | RLE | Huffman/original | RLE/original |
|---|---|---|---|---|---|
| 10 | 197 | 103 | 259 | 0.523 | 1.315 |
| 50 | 1030 | 474 | 1276 | 0.460 | 1.239 |
| 100 | 2080 | 947 | 2580 | 0.455 | 1.240 |

Con ruido cero (`--ph-amp 0 --temp-amp 0 --cond-amp 0`), 100 lecturas:

| Original | Huffman | RLE |
|---|---|---|
| 2080 | 863 | 716 |

Lectura de los resultados:

- Huffman comprime siempre (≈45–52 %) porque el alfabeto es pequeño y los
  dígitos se repiten mucho.
- RLE por sí solo **expande** los datos ruidosos (≈1.24×): cada par
  `valor:veces` añade `:` y dígitos de conteo, y casi no hay repeticiones
  consecutivas en una columna.
- RLE gana cuando hay columnas constantes o casi constantes (versión, pH
  estable): 716 bytes frente a 863 de Huffman.
- Esta comparación mide compresión pura, sin `agrupar`; para payloads LoRaWAN
  reales hay que respetar además `LIMITE_PAYLOAD`.

### 4.8 Línea de comandos de los compresores (`-o`)

Los scripts `entrada_manual.py` no tocan los algoritmos: leen la entrada,
llaman a `codificar` o `preparar` y escriben el resultado. Se ejecutan con `-m`
desde la raíz del proyecto.

**Huffman**

```powershell
python -B -m compresionHuffman.entrada_manual -f salidas\generador\n100_seed42.txt -o salidas\huffman\n100_seed42_huffman.bin -r
```

| Opción | Default | Descripción |
|---|---|---|
| `-f RUTA`, `--archivo RUTA` | stdin/interactivo | lee el bloque desde un archivo ASCII |
| `-o RUTA`, `--salida RUTA` | sin archivo | escribe la trama en un `.bin`; si se omite, imprime `Hex: ...` |
| `--alfabeto CLAVE` | `sensor` | clave de `ALFABETOS` |
| `-r`, `--roundtrip` | desactivado | verifica `decodificar(trama, ab) == bloque` |

**RLE**

```powershell
python -B -m compresionRLE.entrada_manual -f salidas\generador\n100_seed42.txt -o salidas\rle\n100_seed42_rle.txt -r
```

| Opción | Default | Descripción |
|---|---|---|
| `-f RUTA`, `--archivo RUTA` | stdin/interactivo | lee el bloque desde un archivo ASCII |
| `-o RUTA`, `--salida RUTA` | sin archivo | escribe el texto serializado en un `.txt`; si se omite, imprime `Texto: ...` |
| `--campos N` | `5` | número de campos por lectura |
| `-r`, `--roundtrip` | desactivado | verifica `reconstruir(serializado, 5) == bloque` |

**Combinado (RLE → Huffman)**

```powershell
python -B -c "from pathlib import Path; from compresionRLE.pipeline import preparar; from compresionHuffman.codec import codificar; from compresionHuffman.config import ALFABETOS; b=Path('salidas/generador/n100_seed42.txt').read_text(encoding='ascii').replace('\r','').replace('\n',''); r=preparar(b,5); t=codificar(r, ALFABETOS['sensor']); Path('salidas/combinado/n100_seed42_combinado.bin').write_bytes(t); print('original',len(b),'rle',len(r),'combinado',len(t))"
```

**Entrada:** con `-f` se lee un archivo y se eliminan `\r` y `\n`. Sin `-f`, si
hay datos por tubería se usa `stdin`; si no, se entra en modo interactivo
(línea vacía para terminar, `Ctrl+Z`/`Ctrl+D` para salir).

**Salida:** sin `-o` el resultado va a pantalla; con `-o` Huffman usa
`write_bytes` (bytes crudos, `.bin`) y RLE usa `write_text` (ASCII, `.txt`).
Guardar `trama.hex()` como texto duplicaría el tamaño (30 bytes → 60
caracteres). Los compresores crean las carpetas intermedias y sobrescriben sin
preguntar; la extensión es una convención, no una validación.

El salto de línea del generador (`\r\n` en Windows) explica que `demo5.txt`
ocupe 99 bytes en disco mientras el bloque tiene 97 caracteres. Los
compresores lo limpian al leer, así que los tamaños que imprimen coinciden con
los archivos que escriben.

Verificado con 5 lecturas, semilla 42:

```text
demo5.txt              99 bytes en disco (97 caracteres + CRLF)
demo5_huffman.bin      58 bytes, roundtrip True
demo5_rle.txt         127 bytes, roundtrip True
demo5_combinado.bin    72 bytes
```

### 4.9 Descompresión de las salidas

Estructura acordada para los resultados recuperados:

```text
salidas/descompresion/
├── huffman/
│   └── n100_seed42.txt          <- desde huffman/n100_seed42_huffman.bin
├── rle/
│   └── n100_seed42.txt          <- desde rle/n100_seed42_rle.txt
└── combinado/
    ├── n100_seed42_rle.txt      <- paso 1: decodificar Huffman
    └── n100_seed42.txt          <- paso 2: reconstruir RLE
```

No se añadieron scripts ni banderas nuevas: se usan `decodificar` (de
`compresionHuffman.codec`) y `reconstruir` (de `compresionRLE.pipeline`). Todo
lo recuperado es texto. Se repite el nombre del archivo de origen para que la
comparación sea directa entre carpetas.

**Huffman → bloque**

```powershell
python -B -c "from pathlib import Path; from compresionHuffman.codec import decodificar; from compresionHuffman.config import ALFABETOS; t=Path('salidas/huffman/n100_seed42_huffman.bin').read_bytes(); b=decodificar(t, ALFABETOS['sensor']); Path('salidas/descompresion/huffman/n100_seed42.txt').write_text(b + '\n', encoding='ascii'); print('huffman', len(b))"
```

**RLE → bloque**

```powershell
python -B -c "from pathlib import Path; from compresionRLE.pipeline import reconstruir; s=Path('salidas/rle/n100_seed42_rle.txt').read_text(encoding='ascii'); b=reconstruir(s, 5); Path('salidas/descompresion/rle/n100_seed42.txt').write_text(b + '\n', encoding='ascii'); print('rle', len(b))"
```

**Combinado → texto RLE → bloque**

```powershell
python -B -c "from pathlib import Path; from compresionHuffman.codec import decodificar; from compresionHuffman.config import ALFABETOS; from compresionRLE.pipeline import reconstruir; ab=ALFABETOS['sensor']; t=Path('salidas/combinado/n100_seed42_combinado.bin').read_bytes(); r=decodificar(t, ab); Path('salidas/descompresion/combinado/n100_seed42_rle.txt').write_text(r, encoding='ascii'); b=reconstruir(r, 5); Path('salidas/descompresion/combinado/n100_seed42.txt').write_text(b + '\n', encoding='ascii'); print('intermedio', len(r), 'bloque', len(b))"
```

**Verificación:**

```powershell
fc.exe salidas\generador\n100_seed42.txt salidas\descompresion\huffman\n100_seed42.txt
fc.exe salidas\generador\n100_seed42.txt salidas\descompresion\rle\n100_seed42.txt
fc.exe salidas\generador\n100_seed42.txt salidas\descompresion\combinado\n100_seed42.txt
fc.exe salidas\rle\n100_seed42_rle.txt salidas\descompresion\combinado\n100_seed42_rle.txt
```

`fc.exe` lleva extensión porque en PowerShell `fc` es un alias de
`Format-Custom`. Los bloques se escriben con `+ '\n'` (`\r\n` en Windows) para
que sean byte-idénticos al `.txt` del generador; la comprobación interna usa el
bloque sin salto. El texto RLE intermedio no añade salto, igual que el original
en `salidas/rle/`.

Verificado con 5 lecturas, semilla 42: los tres bloques recuperados tienen 97
caracteres y 99 bytes en disco; el texto RLE intermedio tiene 127 bytes; las
cuatro comparaciones con `fc.exe` dieron `FC: no se han encontrado diferencias`.

---

## 5. Correcciones aplicadas el 2026-11-23

| Problema | Corrección |
|---|---|
| `empaquetado.py` de la raíz importaba `codec`, que ya no estaba allí | Se borraron `config.py` y `empaquetado.py` de la raíz (copias byte-idénticas a las de `compresionHuffman/`) |
| `compresionHuffman/` no funcionaba como paquete (`No module named 'arbol_Huffman'`) | Se añadió `compresionHuffman/__init__.py` y se cambiaron los imports a `from .arbol_Huffman ...`, `from .config ...`, `from .codec ...` |
| El generador no encontraba `config` ni `config_generador` | Se añadió `GeneradorDatos/__init__.py`, se cambió a `from compresionHuffman.config import ALFABETOS` y a `from . import config_generador as C` / `from .generador_lecturas import ...`; se documentó el uso con `python -m` |
| El docstring de `config_generador.py` seguía apuntando a `config.py` | Ahora indica `compresionHuffman/config.py` |
| `tests/pruebas_rle.py` importaba un paquete `rle` inexistente | Ahora importa `compresionRLE.pipeline` y `compresionRLE.serializador`; su docstring indica `python -B -m tests.pruebas_rle` |
| La clave del alfabeto tenía un nombre poco descriptivo | Se renombró a `sensor` en `config.py`, el generador y esta documentación |
| El `:` del serializador RLE no estaba en el alfabeto | Se añadió `:` a `ALFABETOS["sensor"]` (14 símbolos); la integración RLE → Huffman ya funciona |

---

## 6. Verificación

Comandos ejecutados sobre el proyecto final (con `python -B`, sin generar
`.pyc`):

```powershell
python -B -c "from compresionHuffman.codec import codificar, decodificar; from compresionHuffman.empaquetado import agrupar, dividir; from compresionHuffman.config import ALFABETOS; ab=ALFABETOS['sensor']; m='7.0&0&25.00&1&300|'; t=codificar(m,ab); print(decodificar(t,ab)==m, dividir(m), agrupar([m]*5,ab,12)[0])"
python -B -m GeneradorDatos.generar_datos -n 2
python -B -m GeneradorDatos.generar_datos -n 5 --semilla 42 --formato bloque -o salidas\generador\demo5.txt
python -B -m compresionHuffman.entrada_manual -f salidas\generador\demo5.txt -o salidas\huffman\demo5_huffman.bin -r
python -B -m compresionRLE.entrada_manual -f salidas\generador\demo5.txt -o salidas\rle\demo5_rle.txt -r
python -B -c "from pathlib import Path; from compresionRLE.pipeline import preparar; from compresionHuffman.codec import codificar; from compresionHuffman.config import ALFABETOS; b=Path('salidas/generador/demo5.txt').read_text(encoding='ascii').replace('\r','').replace('\n',''); Path('salidas/combinado/demo5_combinado.bin').write_bytes(codificar(preparar(b,5), ALFABETOS['sensor']))"
python -B -c "from pathlib import Path; from compresionHuffman.codec import decodificar; from compresionHuffman.config import ALFABETOS; t=Path('salidas/huffman/demo5_huffman.bin').read_bytes(); b=decodificar(t, ALFABETOS['sensor']); Path('salidas/descompresion/huffman/demo5.txt').write_text(b + '\n', encoding='ascii'); print('huffman', len(b))"
python -B -c "from pathlib import Path; from compresionRLE.pipeline import reconstruir; s=Path('salidas/rle/demo5_rle.txt').read_text(encoding='ascii'); b=reconstruir(s, 5); Path('salidas/descompresion/rle/demo5.txt').write_text(b + '\n', encoding='ascii'); print('rle', len(b))"
python -B -c "from pathlib import Path; from compresionHuffman.codec import decodificar; from compresionHuffman.config import ALFABETOS; from compresionRLE.pipeline import reconstruir; ab=ALFABETOS['sensor']; t=Path('salidas/combinado/demo5_combinado.bin').read_bytes(); r=decodificar(t, ab); Path('salidas/descompresion/combinado/demo5_rle.txt').write_text(r, encoding='ascii'); b=reconstruir(r, 5); Path('salidas/descompresion/combinado/demo5.txt').write_text(b + '\n', encoding='ascii'); print('intermedio', len(r), 'bloque', len(b))"
fc.exe salidas\generador\demo5.txt salidas\descompresion\huffman\demo5.txt
fc.exe salidas\generador\demo5.txt salidas\descompresion\rle\demo5.txt
fc.exe salidas\generador\demo5.txt salidas\descompresion\combinado\demo5.txt
fc.exe salidas\rle\demo5_rle.txt salidas\descompresion\combinado\demo5_rle.txt
python -B -m tests.pruebas_rle
python -B -m unittest discover -s tests -p "pruebas_*.py" -v
```

Resultados:

```text
True [['7.0', '0', '25.00', '1', '300']] 5
7.0&0&24.91&1&298|
7.1&60&24.94&1&270|
5 lecturas escritas en salidas\generador\demo5.txt
Original: 97 caracteres / Huffman: 58 bytes / Roundtrip: True
Original: 97 caracteres / RLE: 127 caracteres / Roundtrip: True
huffman 97
rle 97
intermedio 127 bloque 97
FC: no se han encontrado diferencias (4 comparaciones)
Ran 11 tests ... OK
```

Integración completa con 10 lecturas generadas (alfabeto de 14 símbolos):

```text
alfabeto 14 rle True huffman True bytes 129
```

Además se comprobó la sintaxis de los 17 archivos `.py`, el roundtrip de 10
lecturas generadas, la escritura con `--formato bloque -o`, los dos CLI con
`-f`/`-o`/`-r` y el encadenado RLE → Huffman (72 bytes para 5 lecturas).
También se verificó la descompresión de las tres salidas: bloques de 97
caracteres, texto RLE intermedio de 127 e igualdad byte a byte con `fc.exe`.

---

## 7. Estado de Git al escribir este documento

```
## main...origin/main
 M GeneradorDatos/generador_lecturas.py
 M compresionHuffman/config.py
 M docs/ARQUITECTURA.md
?? compresionHuffman/entrada_manual.py
?? compresionRLE/
?? salidas/
?? tests/
```

`README.md` pasó de UTF-16 (solo `# Lorawan`) a UTF-8 con la guía de comandos.
`origin/main` está en `eaa995a`. El rename a `sensor`, el `:` en el alfabeto, el
pipeline RLE, las pruebas, los CLI con `-o`, la carpeta `salidas/` y su nueva
subcarpeta `descompresion/` todavía no están confirmados ni subidos.

## 8. Observaciones pendientes

- `salidas/` no está en `.gitignore`: los resultados generados aparecerán como
  nuevos; los `.gitkeep` solo conservan las carpetas vacías.
- `compresionRLE/serializador.py` define `SIMBOLOS_ESTRUCTURA` pero no lo usa.
- RLE por sí solo expande bloques ruidosos; solo conviene con columnas
  repetitivas. La comparación Huffman vs RLE está en la sección 4.7.
- `deserializar` no valida que las repeticiones sean enteros positivos; confía en
  `_des_rle_columna`, que sí lo hace.
- `LONG_MSG = {"sensor": 27}` dice «bytes por lectura» pero 27 es el número de
  caracteres; además, el constante no se usa en ningún módulo.
- `codificar` usa el literal `0xFFFF` en lugar de una constante de configuración.
- `agrupar` no exige que todos los mensajes tengan la misma longitud; si se
  mezclan, `dividir` puede dar campos inconsistentes.
