"""Cazador de criterios de primalidad, parte 1: el catalogo de los conocidos.

Cada criterio es una condicion C(n). Para todos ellos "n primo => C(n)" es un teorema.
La pregunta es el reciproco: ¿hay compuestos que cumplen C(n)? (pseudoprimos)

Se clasifican hasta N:
  * CARACTERIZA hasta N : ningun compuesto <= N lo cumple;
  * FALLA en m          : m es el primer compuesto que lo cumple.

Lo importante es lo que esto NO dice: "caracteriza hasta N" no es una demostracion.
El criterio de Perrin parece perfecto hasta 271.440 (ver criterios_perrin.py).

Uso:  python3 descubrimientos/criterios_clasicos.py [N]
"""
import math
import sys
import time

N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000


def es_primo(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    r = math.isqrt(n)
    return all(n % d for d in range(3, r + 1, 2))


def phi(n):
    r, m, p = n, n, 2
    while p * p <= m:
        if m % p == 0:
            while m % p == 0:
                m //= p
            r -= r // p
        p += 1
    if m > 1:
        r -= r // m
    return r


def fib_mod(k, n):
    """F_k mod n por duplicacion."""
    def f(k):
        if k == 0:
            return (0, 1)
        a, b = f(k >> 1)
        c = a * ((2 * b - a) % n) % n
        d = (a * a + b * b) % n
        return (d, (c + d) % n) if k & 1 else (c, d)
    return f(k)[0]


def jacobi(a, n):
    a %= n
    res = 1
    while a:
        while a % 2 == 0:
            a //= 2
            if n % 8 in (3, 5):
                res = -res
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3:
            res = -res
        a %= n
    return res if n == 1 else 0


def wilson(n):
    f = 1
    for k in range(2, n):
        f = f * k % n
    return f == n - 1


CRITERIOS = [
    ("Wilson:    (n-1)! = -1 (mod n)", "teorema (Wilson, 1770)", wilson, 2),
    ("Fermat:    2^(n-1) = 1 (mod n)", "solo una direccion", lambda n: pow(2, n - 1, n) == 1, 3),
    ("Lucas-Fibonacci: F(n - (5|n)) = 0 (mod n), mcd(n,10)=1", "solo una direccion",
     lambda n: math.gcd(n, 10) == 1 and fib_mod(n - jacobi(5, n), n) == 0, 7),
    ("Giuga:     sum k^(n-1) = -1 (mod n)", "CONJETURA abierta (1950)",
     lambda n: sum(pow(k, n - 1, n) for k in range(1, n)) % n == n - 1, 2),
    ("Lehmer:    phi(n) divide a n-1", "CONJETURA abierta (1932)",
     lambda n: (n - 1) % phi(n) == 0, 2),
    ("Babbage:   C(2n-1, n-1) = 1 (mod n^2)", "solo una direccion (falla en 16843^2)",
     lambda n: math.comb(2 * n - 1, n - 1) % (n * n) == 1, 3),
    ("Wolstenholme reciproco: C(2n-1,n-1) = 1 (mod n^3)", "CONJETURA abierta",
     lambda n: math.comb(2 * n - 1, n - 1) % (n ** 3) == 1, 5),
]

print(f"Criterios de primalidad conocidos, comprobados para 2 <= n <= {N}\n")
for nombre, estado, C, desde in CRITERIOS:
    t = time.time()
    falla = None
    primos_ok = True
    for n in range(desde, N + 1):
        p = es_primo(n)
        c = C(n)
        if p and not c:
            primos_ok = False
        if c and not p:
            falla = n
            break
    veredicto = f"FALLA en {falla}" if falla else f"caracteriza hasta {N}"
    if not primos_ok:
        veredicto += " (y algun primo NO lo cumple)"
    print(f"  {nombre:52s} {veredicto:26s} [{estado}]  {time.time()-t:5.1f}s")
