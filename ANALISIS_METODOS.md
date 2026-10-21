# Análisis de métodos de `algoritmo#1.py`

**Archivo analizado:** `algoritmo#1.py` (180 líneas)
**Contenido:** codec Huffman + empaquetado LoRaWAN + tests (sin métricas ni energía)
**Fecha:** 2026-10-21

---

## 1. Sobre `random.seed(42)` del `main`

`random.seed(42)` está definido **dentro de `algoritmo#1.py`** (línea 177) y viene del módulo estándar `random` (importado en la línea 46). **No trae nada de `datos_Temperatura.py`**: los dos archivos ni se conocen entre sí. Cada uno tiene su propio mecanismo de semilla y no se mezclan.

| | `algoritmo#1.py` | `datos_Temperatura.py` |
|---|---|---|
| Cómo | `random.seed(42)` (generador global) | `rng = random.Random(p.seed)` (instancia propia) |
| Semilla | fija, escrita en el código | configurable con `--seed` |
| Para qué | que el test de 300 símbolos sea reproducible | que los datos generados sean reproducibles |

**El mecanismo:** el módulo `random` usa un generador global (Mersenne Twister). Sin semilla, Python lo inicializa con entropía del sistema, así que cada corrida produce secuencias distintas. Con `seed(42)` fijas el punto de partida: misma semilla → misma secuencia, siempre.

En este código el único consumidor de aleatoriedad es:

```python
ejemplo = ''.join(random.choices(alfabeto, k=300))   # dentro de pruebas()
```

Sin `seed`, cada ejecución probaría con 300 caracteres distintos y un fallo dependiente de una combinación concreta no sería reproducible. El 42 es arbitrario (guiño a *El viaje del autoestopista galáctico*); cualquier constante sirve.

---

## 2. Método por método

### `contar(texto, alfabeto)` — líneas 58-67

**Qué hace:** recorre el texto y cuenta cuántas veces aparece cada símbolo del alfabeto. Primero crea un diccionario `carácter → índice`; por cada carácter busca su índice y suma 1 a su contador, **saturando en 255**. Si aparece un carácter fuera del alfabeto, lanza `ValueError`.

**Mejoras:**

- 🟡 Construye el diccionario `idx` en cada llamada, y `codificar` lo vuelve a construir (línea 108) — duplicación. Se podría crear una sola vez o pasar como parámetro.
- 🟡 Doble búsqueda: `if ch not in idx` y luego `i = idx[ch]`. Con `idx.get(ch)` o `try/except` sería una sola.
- 🟢 La saturación es silenciosa: quizá convenga documentarla en un comentario (aunque ya es decisión del artículo).
- 🟢 Falta test del branch `ValueError` (carácter fuera del alfabeto).

### `construir_arbol(conteos)` — líneas 70-85

**Qué hace:** construye el árbol de Huffman con una cola de prioridad (`heapq`). Cada entrada es `(peso, secuencia, nodo)`; la `secuencia` garantiza el desempate determinista entre pesos iguales. Toma los dos nodos más livianos, los combina y repite hasta quedar uno (la raíz). Casos especiales: sin símbolos → `None`; un solo símbolo → `(s, s)`.

**Mejoras:**

- 🟢 El caso `(s, s)` produce un árbol artificial cuyos dos hijos son el mismo símbolo (de ahí el `'0'`→`'1'` que sobrescribe `tabla_codigos`). Alternativa más limpia: devolver la hoja y que `tabla_codigos` le asigne `'0'`; solo estético.
- 🟢 Vale la pena un comentario explícito de **por qué** la secuencia debe ser única (evita que `heapq` compare `int` contra `tuple` y reviente — ya lo hace bien, pero el "por qué" no está escrito).
- 🟢 Falta test de determinismo: mismos conteos → mismo árbol siempre.

### `tabla_codigos(raiz)` — líneas 88-100

**Qué hace:** recorre el árbol en profundidad (DFS). Cada paso a la izquierda añade un `'0'` al prefijo, a la derecha un `'1'`. Al llegar a una hoja, guarda `codigos[símbolo] = código en bits`. Devuelve un dict `índice → "bits"`.

**Mejoras:**

- 🟢 La recursión es elegante y aquí no hay riesgo (profundidad máxima ~13 con 14 símbolos); solo sería un límite si el alfabeto fuera enorme.
- 🟢 Sin docstring ni tipos — estilo.
- 🟢 Podría devolver también las **longitudes** de código (útiles si algún día quieres calcular entropía/eficiencia sin generar bits).

### `codificar(texto, alfabeto)` — líneas 103-115

**Qué hace:** el compresor completo: cuenta → construye árbol → genera códigos → concatena los bits de cada símbolo → rellena con ceros hasta múltiplo de 8 → escribe la longitud (2 B big-endian) → devuelve `conteos (N B) + longitud (2 B) + cuerpo`.

**Mejoras:**

- 🔴 **No valida el límite de la longitud**: `len(texto).to_bytes(2, ...)` revienta con `OverflowError` si el texto supera 65.535 símbolos. Un `if len(texto) > 0xFFFF: raise ValueError(...)` daría un error claro.
- 🟡 `int(bits, 2).to_bytes(...)` convierte toda la cadena de bits a un entero gigante. Correcto, pero para textos grandes es ineficiente (enteros de miles de bits); un empaquetado directo con `bytearray` sería más rápido y escalable. A escala LoRaWAN (≤222 B) es irrelevante.
- 🟡 Reconstruye `idx` que `contar` ya construyó.
- 🟢 `if bits else b''` es correcto pero poco legible; podría comentarse.

### `decodificar(trama, alfabeto)` — líneas 118-142

**Qué hace:** invierte el proceso: lee los N conteos, los 2 B de longitud y el cuerpo; reconstruye el árbol; luego lee bits uno a uno bajando por el árbol hasta llegar a una hoja, la emite y vuelve a la raíz; se detiene exactamente al recuperar `longitud` símbolos (por eso el padding nunca se interpreta como dato).

**Mejoras:**

- 🔴 **Falta el guard de `raiz is None`**: si llega una trama corrupta con `longitud > 0` y conteos todos en 0, la línea 137 hace `None[bit]` → `TypeError` criptico. Un `if raiz is None: raise ValueError("Conteos vacíos...")` lo resuelve.
- 🟡 Falta docstring (la función más compleja del archivo).
- 🟡 Convierte todo el cuerpo a string de bits de una vez; aceptable aquí, pero se podría leer bit a bit sobre `bytes` y ahorrar memoria.
- 🟢 No verifica que sobren bytes al final (los ignora). Ser tolerante está bien en radio; si quieres modo estricto, añadir un check.
- 🟢 `longitud` podría validarse contra `len(cuerpo)*8` al inicio para fallar rápido y con mensaje claro.

### `agrupar(mensajes, alfabeto, sf)` — líneas 145-157

**Qué hace:** empaquetador voraz estilo LoRaWAN. Recorre los mensajes en orden de llegada y prueba a comprimir el lote acumulado + el candidato; si la trama resultante cabe en `LIMITE_PAYLOAD[sf]`, lo acepta; si no, corta. Devuelve `(cuántos mensajes caben, trama)`.

**Mejoras:**

- 🟡 **O(n²)**: recodifica el lote completo por cada candidato. A tamaño LoRaWAN es despreciable, pero conviene saberlo.
- 🟡 **No maneja `n == 0`**: si ni el primer mensaje cabe, devuelve `(0, b'')` sin avisar; el que lo use debe comprobarlo (así lo hacía `medir`). Un comentario o excepción lo haría más seguro.
- 🟡 `LIMITE_PAYLOAD[sf]` lanza `KeyError` poco amigable para un SF no definido (solo 7 y 12).
- 🟢 Ahora es función de biblioteca: no la llama nadie — le falta un test de integración con `dividir`.
- 🟢 El `break` (no buscar mensajes más pequeños que sí quepan) es coherente con "orden de llegada" y está documentado en la DECISIÓN 4.

### `dividir(texto, longitud)` — líneas 160-164

**Qué hace:** corta un texto en trozos de longitud fija. Si la longitud total no es múltiplo exacto, lanza `ValueError`. Es la regla del receptor para separar lecturas (DECISIÓN 3).

**Mejoras:**

- 🟡 **No valida `longitud > 0`** → con 0 da `ZeroDivisionError` en el operador `%`. Dos líneas de guard.
- 🟢 Función de biblioteca sin llamador actual.
- 🟢 Correcta con texto vacío (devuelve `[]`).

### `pruebas()` — líneas 167-173

**Qué hace:** tres tests de ida y vuelta por cada alfabeto: texto vacío, un solo símbolo repetido 40 veces y 300 símbolos aleatorios. Imprime `"Pruebas: OK"` si todo pasa.

**Mejoras:**

- 🔴 **El comentario "supera 255: prueba la saturación" es falso** — la saturación nunca se activa. Cambiar por `'0' * 300` y añadir `assert sum(contar(sat, alfabeto)) == 255`.
- 🟡 Faltan: error de alfabeto, tramas corruptas, determinismo (misma entrada → misma trama) e integración `agrupar`/`dividir`.
- 🟢 Usa el generador global; el `seed` del main lo hace reproducible.

### Bloque `main` — líneas 176-178

**Qué hace:** si se ejecuta el archivo como programa, siembra el generador y corre los tests. Nada más.

**Mejoras:**

- 🟡 Al no haber CLI (comprimir/descomprimir un archivo), hoy el programa solo se autotestea. Cuando reconectes datos, aquí irían los argumentos.
- 🟢 El `seed` global afecta solo a los tests; correcto para un script.

---

## 3. Prioridad global de mejoras

| Prioridad | Mejora | Dónde |
|---|---|---|
| 🔴 Alta | Guard `raiz is None` en `decodificar` | 133-137 |
| 🔴 Alta | Validar `len(texto) ≤ 65535` en `codificar` | 114 |
| 🔴 Alta | Arreglar test de saturación | 171 |
| 🟡 Media | Guard `longitud > 0` en `dividir` | 162 |
| 🟡 Media | Documentar/validar `n == 0` en `agrupar` | 145 |
| 🟢 Baja | Docstrings/tipos en codec, deduplicar `idx`, limpiar comentarios Markdown y referencias GPS del docstring | varios |

---

## 4. Notas adicionales

- **Referencias stale en el docstring:** la DECISIÓN 3 (línea 21) aún menciona "28 bytes (concreto) y 22 bytes (GPS)", y la nota de la línea 39 habla de "21 lecturas GPS de 22 bytes". Hoy el formato es de 27 B y no existe GPS.
- **Código de biblioteca sin llamador:** `agrupar`, `dividir` y `LONG_MSG` no son usados por nada interno tras eliminar `medir` y `tabla_por_n`; se conservan para cuando se reconecten los datos.
- **Nombre del archivo:** `algoritmo#1.py` no se puede importar con `import` normal (el `#` es inválido en sintaxis). Si en el futuro otro módulo debe usarlo, renombrar (p. ej. `algoritmo_1.py`) o cargar con `runpy`/`importlib`.
