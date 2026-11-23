# Arquitectura del proyecto LoRaWAN
---

## 1. Estructura actual

```
Lorawan/
├── .gitignore
├── README.md                      descripción del repositorio (UTF-8)
├── compresionHuffman/
│   ├── __init__.py
│   ├── arbol_Huffman.py
│   ├── codec.py
│   ├── config.py
│   ├── empaquetado.py
│   └── entrada_manual.py          CLI con -f / -o / -d / -r
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
│   └── entrada_manual.py          CLI con -f / -o / -d / -r
├── compresionCombinado/
│   ├── __init__.py
│   └── entrada_manual.py      CLI RLE -> Huffman con -f / -o / -d / -r
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


### Grafo de dependencias

```
compresionHuffman/config.py ──────────────> compresionHuffman/codec.py ──> compresionHuffman/empaquetado.py
compresionHuffman/arbol_Huffman.py ───────> compresionHuffman/codec.py
compresionHuffman/config.py ──────────────> GeneradorDatos/generador_lecturas.py ──> GeneradorDatos/generar_datos.py
GeneradorDatos/config_generador.py ─> GeneradorDatos/generar_datos.py
compresionRLE/lecturas.py ───────> compresionRLE/pipeline.py <── compresionRLE/serializador.py
compresionHuffman/entrada_manual.py ──> compresionHuffman/codec.py, config.py
compresionRLE/entrada_manual.py ──────> compresionRLE/pipeline.py
compresionCombinado/entrada_manual.py ─> compresionRLE/pipeline.py, compresionHuffman/codec.py
tests/pruebas_rle.py ────────────> compresionRLE/pipeline.py, compresionRLE/serializador.py
```

Todos los módulos internos usan imports relativos (`from .config import ...`)
o imports absolutos desde la raíz (`from compresionHuffman.config import ...`).
Los entry point son `GeneradorDatos/generar_datos.py` y los tres
`entrada_manual.py` (Huffman, RLE y combinado), invocados con `python -m`; las
pruebas automáticas están en `tests/pruebas_rle.py`.

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
| `compresionHuffman/entrada_manual.py` | CLI Huffman: `-f`, `-o`, `-d`, `--alfabeto`, `-r` |
| `compresionRLE/entrada_manual.py` | CLI RLE: `-f`, `-o`, `-d`, `--campos`, `-r` |
| `compresionCombinado/entrada_manual.py` | CLI RLE → Huffman: `-f`, `-o`, `--intermedio`, `-d`, `-r` |
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


### 4.8 Comandos de compresión

Todo se ejecuta desde la raíz del proyecto. Primero se genera el bloque con la
misma semilla para que los tres métodos vean los mismos datos:

```powershell
python -B -m GeneradorDatos.generar_datos -n 100 --semilla 42 --formato bloque -o salidas\generador\n100_seed42.txt
```

Huffman:

```powershell
python -B -m compresionHuffman.entrada_manual -f salidas\generador\n100_seed42.txt -o salidas\huffman\n100_seed42_huffman.bin -r
```

RLE:

```powershell
python -B -m compresionRLE.entrada_manual -f salidas\generador\n100_seed42.txt -o salidas\rle\n100_seed42_rle.txt -r
```

Combinado (RLE → Huffman):

```powershell
python -B -m compresionCombinado.entrada_manual -f salidas\generador\n100_seed42.txt -o salidas\combinado\n100_seed42_combinado.bin --intermedio salidas\combinado\n100_seed42_rle.txt -r
```

Opciones de los CLI:

| Opción | Default | Descripción |
|---|---|---|
| `-f RUTA`, `--archivo RUTA` | stdin/interactivo | archivo de entrada |
| `-o RUTA`, `--salida RUTA` | pantalla | archivo de salida |
| `--alfabeto CLAVE` | `sensor` | clave de `ALFABETOS` |
| `--campos N` | `5` | campos por lectura (RLE y combinado) |
| `--intermedio RUTA` | sin archivo | texto RLE del pipeline combinado |
| `-r`, `--roundtrip` | desactivado | verifica la operación inversa |

### 4.9 Comandos de descompresión

Se usa la misma herramienta con `-d`. No hay que escribir código Python:

```powershell
python -B -m compresionHuffman.entrada_manual -d -f salidas\huffman\n100_seed42_huffman.bin -o salidas\descompresion\huffman\n100_seed42.txt -r

python -B -m compresionRLE.entrada_manual -d -f salidas\rle\n100_seed42_rle.txt -o salidas\descompresion\rle\n100_seed42.txt -r

python -B -m compresionCombinado.entrada_manual -d -f salidas\combinado\n100_seed42_combinado.bin -o salidas\descompresion\combinado\n100_seed42.txt --intermedio salidas\descompresion\combinado\n100_seed42_rle.txt -r
```

Resultados:

```text
salidas/descompresion/
├── huffman/
│   └── n100_seed42.txt          <- desde el .bin de Huffman
├── rle/
│   └── n100_seed42.txt          <- desde el texto serializado
└── combinado/
    ├── n100_seed42_rle.txt      <- texto RLE intermedio
    └── n100_seed42.txt          <- bloque final
```

Los bloques recuperados se escriben con el salto final del generador (`\r\n`
en Windows), por lo que son byte-idénticos a `salidas/generador/*.txt`. El texto
RLE intermedio no lleva salto. `--sin-salto` desactiva ese comportamiento si
necesitas comparar longitudes internas.

---

## 5. Verificación

```powershell
fc.exe salidas\generador\n100_seed42.txt salidas\descompresion\huffman\n100_seed42.txt
fc.exe salidas\generador\n100_seed42.txt salidas\descompresion\rle\n100_seed42.txt
fc.exe salidas\generador\n100_seed42.txt salidas\descompresion\combinado\n100_seed42.txt
fc.exe salidas\rle\n100_seed42_rle.txt salidas\descompresion\combinado\n100_seed42_rle.txt
python -B -m tests.pruebas_rle
python -B -m unittest discover -s tests -p "pruebas_*.py" -v
```

Usa `fc.exe` con extensión: en PowerShell, `fc` es un alias de `Format-Custom`.
Si todo está bien, las cuatro comparaciones dicen
`FC: no se han encontrado diferencias` y las 11 pruebas terminan en `OK`.

