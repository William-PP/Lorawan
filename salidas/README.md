# Salidas

Carpeta para separar los resultados de cada etapa. Los `.gitkeep` conservan las
subcarpetas mientras no haya archivos.

```text
salidas/
├── generador/                 .txt  bloques originales
├── huffman/                   .bin  trama Huffman del original
├── rle/                       .txt  texto serializado de RLE
├── combinado/                 .bin  trama Huffman del texto RLE
└── descompresion/             .txt  resultados recuperados
    ├── huffman/
    ├── rle/
    └── combinado/             texto RLE intermedio + bloque final
```

El mismo nombre de archivo se usa en carpetas distintas: la carpeta indica si
es el original, un comprimido o un recuperado. Los `.bin` son solo tramas; todo
lo descomprimido es texto. Los bloques recuperados se guardan con el salto final
del generador y el texto RLE intermedio sin salto.

Los comandos para generar, comprimir, descomprimir y verificar están en
[docs/ARQUITECTURA.md](../docs/ARQUITECTURA.md), secciones 4.8, 4.9 y 5.
