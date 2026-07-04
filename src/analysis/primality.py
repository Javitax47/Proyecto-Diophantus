"""
================================================================================
   DIOPHANTUS - PRIMALIDAD CORRECTA: Baillie-PSW
================================================================================
La antigua "Ecuacion Suprema" del proyecto (baillie_psw_formula.py) NO era
Baillie-PSW y estaba mal: combinaba un Fermat base 2 DEBIL (no strong) con un
test de Lucas de PARAMETRO FIJO (P=3,Q=1), y se sellaba como "Definitive".
Tiene contraejemplos reales: declara primos a 2465, 6601, 11305, 13981, 30889,
68101 (compuestos; 6601 es Carmichael).

Este modulo implementa el Baillie-PSW DE VERDAD:
  1. Miller-Rabin FUERTE en base 2 (no el Fermat simple).
  2. Test de Lucas FUERTE con parametros de Selfridge (D por Jacobi(D/n)=-1,
     P=1, Q=(1-D)/4).
Baillie-PSW no tiene contraejemplos conocidos y es deterministicamente correcto
para todo n < 2^64 (verificado exhaustivamente). Sigue siendo CONJETURAL en
general (no demostrado) — y asi se documenta, sin sellos "Definitive".
"""

import math


def jacobi(a, n):
    """Simbolo de Jacobi (a/n) para n impar positivo."""
    assert n > 0 and n % 2 == 1
    a %= n
    result = 1
    while a:
        while a % 2 == 0:
            a //= 2
            if n % 8 in (3, 5):
                result = -result
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3:
            result = -result
        a %= n
    return result if n == 1 else 0


def is_perfect_square(n):
    r = math.isqrt(n)
    return r * r == n


def miller_rabin_strong_base2(n):
    """Test de Miller-Rabin FUERTE en base 2 (probable-primo fuerte base 2)."""
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    x = pow(2, d, n)
    if x == 1 or x == n - 1:
        return True
    for _ in range(r - 1):
        x = (x * x) % n
        if x == n - 1:
            return True
    return False


def _selfridge_D(n):
    """Primer D de la sucesion 5,-7,9,-11,13,... con Jacobi(D/n) = -1.
    Devuelve D, o 0 si se detecta que n es compuesto (Jacobi 0) o cuadrado."""
    D = 5
    while True:
        j = jacobi(D % n, n)
        if j == -1:
            return D
        if j == 0:
            # gcd(D, n) > 1 con |D| < n  =>  n compuesto
            return 0
        D = -D - 2 if D > 0 else -D + 2
        if abs(D) > 2_000_000:  # salvaguarda (no deberia ocurrir tras descartar cuadrados)
            return 0


def _lucas_uv(k, P, Q, n):
    """Devuelve (U_k, V_k, Q^k) mod n de las sucesiones de Lucas con parametros
    (P, Q), por el metodo binario desde el bit mas significativo."""
    D = P * P - 4 * Q
    inv2 = pow(2, -1, n)
    U, V, Qk = 1 % n, P % n, Q % n      # U_1, V_1, Q^1
    for b in bin(k)[3:]:                # bits tras el lider (k >= 1)
        U, V = (U * V) % n, (V * V - 2 * Qk) % n
        Qk = (Qk * Qk) % n
        if b == '1':
            U, V = ((P * U + V) * inv2) % n, ((D * U + P * V) * inv2) % n
            Qk = (Qk * Q) % n
    return U, V, Qk


def strong_lucas_prp(n):
    """Test de Lucas FUERTE con parametros de Selfridge (D, P=1, Q=(1-D)/4)."""
    if n % 2 == 0 or is_perfect_square(n):
        return n == 2
    D = _selfridge_D(n)
    if D == 0:
        return False
    P, Q = 1, (1 - D) // 4
    d, s = n + 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    U, V, Qk = _lucas_uv(d, P, Q, n)
    if U % n == 0 or V % n == 0:
        return True
    for _ in range(s - 1):
        V = (V * V - 2 * Qk) % n
        Qk = (Qk * Qk) % n
        if V % n == 0:
            return True
    return False


def _miller_rabin_base(n, a):
    """Probable-primo fuerte de Miller-Rabin en base a."""
    if n % a == 0:
        return n == a
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    x = pow(a, d, n)
    if x == 1 or x == n - 1:
        return True
    for _ in range(r - 1):
        x = (x * x) % n
        if x == n - 1:
            return True
    return False


# Conjunto de bases con determinismo DEMOSTRADO (no conjetural) para n < 3.317e24
# (Sorenson-Webster): cubre todo el rango de 64 bits. Esto es lo que la antigua
# "Bestia" Solovay-Strassen afirmaba ser sin serlo: Solovay-Strassen con bases
# fijas NO es determinista hasta 2^64.
_DETERMINISTIC_MR_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def is_prime_deterministic_64(n):
    """Primalidad DETERMINISTA y DEMOSTRADA para n < 3.317e24 (incluye 64-bit),
    via Miller-Rabin con el conjunto de bases probado de Sorenson-Webster. No es
    conjetural: es correcto con certeza en ese rango."""
    if n < 2:
        return False
    for p in _DETERMINISTIC_MR_BASES:
        if n % p == 0:
            return n == p
    return all(_miller_rabin_base(n, a) for a in _DETERMINISTIC_MR_BASES)


def baillie_psw(n):
    """Test de primalidad Baillie-PSW: Miller-Rabin fuerte base 2 + Lucas fuerte
    de Selfridge. Sin contraejemplos conocidos; deterministico para n < 2^64.
    Conjetural en general (no demostrado)."""
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    if is_perfect_square(n):
        return False
    if not miller_rabin_strong_base2(n):
        return False
    return strong_lucas_prp(n)
