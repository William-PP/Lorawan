# Salidas

Carpeta para separar los resultados de cada etapa. Los archivos `.gitkeep`
existen solo para que Git conserve las subcarpetas mientras no haya salidas.

```
salidas/
├── generador/                 .txt  bloques originales, salida de GeneradorDatos
├── huffman/                   .bin  trama binaria de Huffman sobre el original
├── rle/                       .txt  texto serializado de RLE sobre el original
├── combinado/                 .bin  trama binaria de Huffman aplicada al texto RLE
└── descompresion/             todo lo recuperado es .txt
    ├── huffman/               .txt  bloque recuperado del .bin de Huffman
    ├── rle/                   .txt  bloque recuperado del texto RLE
    └── combinado/             .txt  paso 1 (texto RLE) y paso 2 (bloque)
```

Ejecuta todos los comandos desde la raíz del proyecto.

## Tipo de archivo según la etapa

| Etapa | Extensión | Cómo se escribe | Contenido |
|---|---|---|---|
| Generador | `.txt` | `open(..., "w", encoding="ascii")` | `ph&uptime&temp&version&cond\|`, con salto de línea final |
| RLE | `.txt` | `write_text(..., encoding="ascii")` | `N\|valor:veces&...\|...`, sin salto final |
| Huffman | `.bin` | `write_bytes(trama)` | conteos (14 B) + longitud (2 B) + cuerpo de bits |
| Combinado | `.bin` | `write_bytes(trama)` | Huffman sobre el texto RLE |
| Desc. Huffman | `.txt` | `write_text(bloque + '\n')` | bloque original recuperado |
| Desc. RLE | `.txt` | `write_text(bloque + '\n')` | bloque original recuperado |
| Desc. combinado, paso 1 | `.txt` | `write_text(texto_rle)` | texto RLE intermedio |
| Desc. combinado, paso 2 | `.txt` | `write_text(bloque + '\n')` | bloque original recuperado |

`.txt` se puede abrir con cualquier editor. `.bin` es binario: se lee y se
escribe con Python (`read_bytes()` / `write_bytes()`), no con un editor de
texto. Si guardaras `trama.hex()` como texto, ocuparía el doble: 30 bytes →
60 caracteres.

## Comandos para llenar las carpetas

### 1. Generador

```powershell
python -B -m GeneradorDatos.generar_datos -n 100 --semilla 42 --formato bloque -o salidas\generador\n100_seed42.txt
```

### 2. Huffman

```powershell
python -B -m compresionHuffman.entrada_manual -f salidas\generador\n100_seed42.txt -o salidas\huffman\n100_seed42_huffman.bin -r
```

Sin `-o`, este script imprime `Hex: ...` en pantalla. Con `-o`, escribe los
bytes directamente en el `.bin`.

### 3. RLE

```powershell
python -B -m compresionRLE.entrada_manual -f salidas\generador\n100_seed42.txt -o salidas\rle\n100_seed42_rle.txt -r
```

Sin `-o`, imprime `Texto: ...`. Con `-o`, escribe texto ASCII en el `.txt`.

### 4. Combinado (RLE → Huffman)

```powershell
python -B -c "from pathlib import Path; from compresionRLE.pipeline import preparar; from compresionHuffman.codec import codificar; from compresionHuffman.config import ALFABETOS; b=Path('salidas/generador/n100_seed42.txt').read_text(encoding='ascii').replace('\r','').replace('\n',''); r=preparar(b,5); t=codificar(r, ALFABETOS['sensor']); Path('salidas/combinado/n100_seed42_combinado.bin').write_bytes(t); print('original',len(b),'rle',len(r),'combinado',len(t))"
```

El `:` del texto RLE ya está en `ALFABETOS["sensor"]`, así que Huffman puede
comprimirlo sin cambiar el alfabeto.

## Comandos para descomprimir

No hay scripts nuevos: se usan `decodificar` y `reconstruir`, que ya existen.
Todo lo recuperado es texto. Se repiten los nombres de los originales para
poder compararlos directamente.

### Huffman → bloque original

```powershell
python -B -c "from pathlib import Path; from compresionHuffman.codec import decodificar; from compresionHuffman.config import ALFABETOS; t=Path('salidas/huffman/n100_seed42_huffman.bin').read_bytes(); b=decodificar(t, ALFABETOS['sensor']); Path('salidas/descompresion/huffman/n100_seed42.txt').write_text(b + '\n', encoding='ascii'); print('huffman', len(b))"
```

### RLE → bloque original

```powershell
python -B -c "from pathlib import Path; from compresionRLE.pipeline import reconstruir; s=Path('salidas/rle/n100_seed42_rle.txt').read_text(encoding='ascii'); b=reconstruir(s, 5); Path('salidas/descompresion/rle/n100_seed42.txt').write_text(b + '\n', encoding='ascii'); print('rle', len(b))"
```

### Combinado → texto RLE → bloque original

```powershell
python -B -c "from pathlib import Path; from compresionHuffman.codec import decodificar; from compresionHuffman.config import ALFABETOS; from compresionRLE.pipeline import reconstruir; ab=ALFABETOS['sensor']; t=Path('salidas/combinado/n100_seed42_combinado.bin').read_bytes(); r=decodificar(t, ab); Path('salidas/descompresion/combinado/n100_seed42_rle.txt').write_text(r, encoding='ascii'); b=reconstruir(r, 5); Path('salidas/descompresion/combinado/n100_seed42.txt').write_text(b + '\n', encoding='ascii'); print('intermedio', len(r), 'bloque', len(b))"
```

### Verificación

```powershell
fc.exe salidas\generador\n100_seed42.txt salidas\descompresion\huffman\n100_seed42.txt
fc.exe salidas\generador\n100_seed42.txt salidas\descompresion\rle\n100_seed42.txt
fc.exe salidas\generador\n100_seed42.txt salidas\descompresion\combinado\n100_seed42.txt
fc.exe salidas\rle\n100_seed42_rle.txt salidas\descompresion\combinado\n100_seed42_rle.txt
```

Usa `fc.exe` con extensión: en PowerShell, `fc` solo es un alias de
`Format-Custom`. Si los archivos coinciden imprime
`FC: no se han encontrado diferencias`.

Los archivos recuperados se escriben con `+ '\n'`, que en Windows se guarda como
`\r\n`, para que sean byte-idénticos al `.txt` del generador. La comprobación
interna se hace con el bloque sin salto (`len(bloque) = 97`). El texto RLE
intermedio no lleva salto, igual que `salidas/rle/*.txt`.

## Qué hace `-o` y por qué importa

`-o RUTA` indica el archivo de destino. No cambia el algoritmo, solo la salida:

- Sin `-o`: resultado en pantalla (o entrada interactiva/por tubería si no hay `-f`).
- Con `-o`: archivo en disco. Los compresores crean las carpetas intermedias;
  el generador no, pero estas carpetas ya existen.
- Sobrescribe sin preguntar si el archivo ya está.
- La extensión es una convención: el script no valida `.bin` ni `.txt`.

### El salto de línea del generador

El generador añade siempre `\n` al final. En Windows se guarda como `\r\n`:

```text
demo5.txt en disco                     → 99 bytes
bloque leído por -f (sin \r ni \n)     → 97 caracteres
```

Los compresores eliminan `\r` y `\n` al leer con `-f`, por eso imprimen
`Original: 97 caracteres`. Ese detalle **solo** afecta al tamaño del `.txt`
original; no cambia los bytes comprimidos.

Para comparar con exactitud:

- usa el valor `Original:` que imprime el compresor, o
- réstale 2 bytes en Windows (1 en Linux) a `Get-Item ...\generador\...txt`.

## Convención de nombres sugerida

```
salidas/generador/n100_seed42_modo-normal.txt
salidas/huffman/n100_seed42_modo-normal_huffman.bin
salidas/rle/n100_seed42_modo-normal_rle.txt
salidas/combinado/n100_seed42_modo-normal_combinado.bin
salidas/descompresion/huffman/n100_seed42_modo-normal.txt
salidas/descompresion/rle/n100_seed42_modo-normal.txt
salidas/descompresion/combinado/n100_seed42_modo-normal_rle.txt
salidas/descompresion/combinado/n100_seed42_modo-normal.txt
```

Así se sabe de qué corrida viene cada archivo y no se sobrescriben entre sí.
El mismo nombre en carpetas distintas indica origen y destino de la comparación.

## Medición de tamaño

```powershell
Get-Item salidas\generador\n100_seed42.txt, `
         salidas\huffman\n100_seed42_huffman.bin, `
         salidas\rle\n100_seed42_rle.txt, `
         salidas\combinado\n100_seed42_combinado.bin, `
         salidas\descompresion\huffman\n100_seed42.txt, `
         salidas\descompresion\rle\n100_seed42.txt, `
         salidas\descompresion\combinado\n100_seed42_rle.txt, `
         salidas\descompresion\combinado\n100_seed42.txt |
    Select-Object Name,Length
```

```python
from pathlib import Path

for ruta in [
    "salidas/generador/n100_seed42.txt",
    "salidas/huffman/n100_seed42_huffman.bin",
    "salidas/rle/n100_seed42_rle.txt",
    "salidas/combinado/n100_seed42_combinado.bin",
    "salidas/descompresion/huffman/n100_seed42.txt",
    "salidas/descompresion/rle/n100_seed42.txt",
    "salidas/descompresion/combinado/n100_seed42_rle.txt",
    "salidas/descompresion/combinado/n100_seed42.txt",
]:
    print(ruta, Path(ruta).stat().st_size)
```

Comprobación real con `-n 5 --semilla 42`:

| Archivo | Bytes en disco | Medida interna |
|---|---|---|
| `demo5.txt` | 99 | `len(bloque)` = 97 |
| `demo5_huffman.bin` | 58 | `len(codificar(bloque, ab))` = 58 |
| `demo5_rle.txt` | 127 | `len(preparar(bloque, 5))` = 127 |
| `demo5_combinado.bin` | 72 | `len(codificar(preparar(bloque, 5), ab))` = 72 |
| `descompresion/huffman/demo5.txt` | 99 | mismo bloque que el generador |
| `descompresion/rle/demo5.txt` | 99 | mismo bloque que el generador |
| `descompresion/combinado/demo5_rle.txt` | 127 | mismo texto que `demo5_rle.txt` |
| `descompresion/combinado/demo5.txt` | 99 | mismo bloque que el generador |

Nota: esta carpeta todavía no está configurada en `.gitignore` ni versionada.
Los `.gitkeep` se conservarán, incluidos los de `descompresion/`; los archivos
de resultados aparecerán como nuevos hasta que decidas qué hacer con ellos.
