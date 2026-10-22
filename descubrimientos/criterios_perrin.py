"""Cazador de criterios de primalidad, parte 2: la familia de Perrin.

Para cada polinomio cubico  x^3 - a x^2 - b x - c  con coeficientes enteros pequenos, la
sucesion de trazas  s(n) = r1^n + r2^n + r3^n  (r_i sus raices) es entera y cumple

        n primo  =>  s(n) = a  (mod n)                (teorema: Frobenius)

Perrin es  x^3 - x - 1  (a=0, b=1, c=1). El reciproco falla: el primer compuesto que lo
cumple es 271441 (Adams y Shanks, 1982). Cada polinomio da un criterio candidato, y la
pregunta medible es: ¿cual tarda mas en fallar?

s(n) mod n se calcula como la traza de M^n, con M la matriz companera, para TODOS los n
a la vez con numpy (exponenciacion binaria con mascaras por bit).

Uso:  python3 descubrimientos/criterios_perrin.py N            (barrido, coeficientes en [-2,2])
      python3 descubrimientos/criterios_perrin.py N R          (barrido, coeficientes en [-R,R])
      python3 descubrimientos/criterios_perrin.py N a b c      (un solo polinomio)
"""
import sys
import time

import numpy as np


def criba(N):
    es = np.ones(N + 1, dtype=bool)
    es[:2] = False
    for p in range(2, int(N ** 0.5) + 1):
        if es[p]:
            es[p * p::p] = False
    return es


def trazas_mod_n(a, b, c, N, desde=2):
    n = np.arange(desde, N + 1, dtype=np.int64)
    M = [[a, b, c], [1, 0, 0], [0, 1, 0]]
    B = [[np.full_like(n, v) % n for v in fila] for fila in M]
    uno, cero = np.ones_like(n) % n, np.zeros_like(n)
    R = [[uno if i == j else cero for j in range(3)] for i in range(3)]

    def mul(X, Y):
        return [[(X[i][0] * Y[0][j] + X[i][1] * Y[1][j] + X[i][2] * Y[2][j]) % n
                 for j in range(3)] for i in range(3)]

    e = n.copy()
    while True:
        bit = (e & 1).astype(bool)
        if bit.any():
            P = mul(R, B)
            R = [[np.where(bit, P[i][j], R[i][j]) for j in range(3)] for i in range(3)]
        e >>= 1
        if not e.any():
            break
        B = mul(B, B)
    return n, (R[0][0] + R[1][1] + R[2][2]) % n


def analizar(a, b, c, N, es_primo):
    n, s = trazas_mod_n(a, b, c, N)
    cumple = s == (a % n)
    primos_ok = bool(np.all(cumple[es_primo[n]]))
    psp = n[cumple & ~es_primo[n]]
    return primos_ok, psp


if __name__ == '__main__':
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 300000
    es_primo = criba(N)
    if len(sys.argv) == 5:
        a, b, c = map(int, sys.argv[2:5])
        t = time.time()
        ok, psp = analizar(a, b, c, N, es_primo)
        print(f"x^3 - ({a})x^2 - ({b})x - ({c}):  todos los primos lo cumplen: {ok};  "
              f"pseudoprimos <= {N}: {len(psp)};  primero: {psp[0] if len(psp) else 'ninguno'};  "
              f"{time.time()-t:.1f}s")
        sys.exit(0)

    # barrido: todos los cubicos con a,b,c en [-R,R], c != 0  (R = 2 por defecto)
    R = int(sys.argv[2]) if len(sys.argv) == 3 else 2
    filas = []
    t = time.time()
    for a in range(-R, R + 1):
        for b in range(-R, R + 1):
            for c in [v for v in range(-R, R + 1) if v != 0]:
                ok, psp = analizar(a, b, c, N, es_primo)
                primero = int(psp[0]) if len(psp) else None
                filas.append((primero if primero else 10 ** 18, a, b, c, ok, len(psp)))
    filas.sort(reverse=True)
    print(f"Barrido de {len(filas)} cubicos (a,b,c en [-{R},{R}], c != 0) hasta N = {N}  "
          f"({time.time()-t:.0f}s)\n")
    print(f"  {'polinomio':24s} {'primer pseudoprimo':>20s} {'pseudoprimos <= N':>18s}  primos ok")
    for primero, a, b, c, ok, k in filas[:15]:
        pol = f"x^3 - ({a})x^2 - ({b})x - ({c})"
        pp = "ninguno" if primero == 10 ** 18 else str(primero)
        print(f"  {pol:24s} {pp:>20s} {k:>18d}  {ok}")
    print("  ...")
    peores = [f for f in filas if f[0] != 10 ** 18][-3:]
    for primero, a, b, c, ok, k in peores:
        print(f"  {'x^3 - (%d)x^2 - (%d)x - (%d)' % (a, b, c):24s} {primero:>20d} {k:>18d}  {ok}")
