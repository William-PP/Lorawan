
"""
Genera lecturas de temperatura con la forma <1>&aa.aa&bb.bb&cc.cc&dd.dd
27(caracteres) usando parametros aleatorizables. Es independiende del codec Huffman:
solo produce datos de entrada
"""

import argparse
import json
import math
import random
import sys

LONG_LECTURA= 27  # 27 caracteres de longitud para la lectura de temperatura
VMIN, VMAX=0.0, 99.99  # rango de valores de temperatura (ES EL RANGO VALIDO PARA EL FORMATO)
MODOS=("uniforme", "normal", "senoidal")  # modos de generacion de datos

def valor_canal(i,base,p,rng):
    """valor del canal en la lectura i"""
    if p.modo=="uniforme":
        ruido=rng.uniform(-p.amplitud,p.amplitud)
    elif p.modo=="normal":
        ruido=rng.gauss(0.0,p.amplitud)
    else:  # modo senoidal: ciclo diari+ruido pequeño
        ruido=p.amplitud*math.sin(2*math.pi*i/p.periodo) 
        ruido+=rng.gauss(0.0,p.amplitud*0.1)  # ruido pequeño
    return base + p.tendencia *i + ruido

def generar_lecturas(p):
    """Devuelve una lista de n lecturas en el formato <1>&aa.aa&bb.bb&cc.cc&dd.ddd"""
    rng=random.Random(p.seed)
    
    # Cada canal tiene un desplazamiento propio, para que no sean idénticos.
    offsets = [rng.uniform(-p.dispersion, p.dispersion) for _ in range(4)]

    lecturas = []
    for i in range(p.n):
        vals = []
        for k in range(4):
            v = valor_canal(i, p.media + offsets[k], p, rng)
            vals.append(min(max(v, VMIN), VMAX))
        lecturas.append(formatear(*vals))
    return lecturas

def formatear(a, b, c, d):
    """Forma <1>&aa.aa&bb.bb&cc.cc&dd.dd. Verifica la longitud fija."""
    texto = f"<1>&{a:05.2f}&{b:05.2f}&{c:05.2f}&{d:05.2f}"
    if len(texto) != LONG_LECTURA:
        raise RuntimeError(f"Longitud inesperada ({len(texto)}): {texto!r}")
    return texto
 
 
def estadisticas(lecturas):
    """Resumen simple de los cuatro canales."""
    filas = []
    for k in range(4):
        valores = [float(l.split('&')[k + 1]) for l in lecturas]
        media = sum(valores) / len(valores)
        var = sum((x - media) ** 2 for x in valores) / len(valores)
        filas.append((k + 1, min(valores), max(valores), media, math.sqrt(var)))
    return filas
 
 
def leer_argumentos(argv=None):
    ap = argparse.ArgumentParser(description="Generador aleatorio de lecturas de temperatura.")
    ap.add_argument("-n", type=int, default=40, help="número de lecturas (por defecto 40)")
    ap.add_argument("--seed", type=int, default=42, help="semilla; mismo valor = mismos datos")
    ap.add_argument("--media", type=float, default=25.0, help="temperatura central en °C")
    ap.add_argument("--dispersion", type=float, default=1.0,
                    help="diferencia máxima entre canales, en °C")
    ap.add_argument("--amplitud", type=float, default=0.5,
                    help="magnitud del ruido por lectura, en °C")
    ap.add_argument("--tendencia", type=float, default=0.0,
                    help="cambio por lectura, en °C (negativo = bajada)")
    ap.add_argument("--modo", choices=MODOS, default="normal",
                    help="distribución del ruido")
    ap.add_argument("--periodo", type=int, default=24,
                    help="lecturas por ciclo (solo modo senoidal)")
    ap.add_argument("--formato", choices=("txt", "json"), default="txt")
    ap.add_argument("-o", "--salida", default=None,
                    help="archivo de salida (por defecto, pantalla)")
    ap.add_argument("--estadisticas", action="store_true",
                    help="imprime min, max, media y desviación de cada canal")
    p = ap.parse_args(argv)
 
    if p.n < 1:
        ap.error("-n debe ser al menos 1")
    if p.amplitud < 0 or p.dispersion < 0:
        ap.error("amplitud y dispersión no pueden ser negativas")
    if p.periodo < 1:
        ap.error("--periodo debe ser al menos 1")
    return p
 
 
def main(argv=None):
    p = leer_argumentos(argv)
    lecturas = generar_lecturas(p)
 
    if p.formato == "json":
        contenido = json.dumps(
            {"parametros": {k: v for k, v in vars(p).items() if k not in ("salida",)},
             "lecturas": lecturas},
            ensure_ascii=False, indent=2)
    else:
        contenido = "\n".join(lecturas) + "\n"
 
    if p.salida:
        with open(p.salida, "w", encoding="ascii") as f:
            f.write(contenido)
        print(f"{len(lecturas)} lecturas escritas en {p.salida}", file=sys.stderr)
    else:
        sys.stdout.write(contenido)
 
    if p.estadisticas:
        print("canal      min      max    media  desv.", file=sys.stderr)
        for canal, mn, mx, med, sd in estadisticas(lecturas):
            print(f"{canal:>5}{mn:9.2f}{mx:9.2f}{med:9.2f}{sd:7.2f}", file=sys.stderr)
 
 
if __name__ == "__main__":
    main()