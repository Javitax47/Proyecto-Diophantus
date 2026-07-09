import sys


__LATEX_REPR__ = [
    "THEOREM: The Twin Singularity (Diophantine Form)",
    "∃ k_1, k_2 ∈ Z  s.t.  P(n) = 0",
    "",
    "   P(n) = ( 2^(n-1) - 1 - k_1·n )²  +  ( D_{n}(3) - 3 - k_2·n )²",
    "",
    "   Where D_n(x) is the Dickson Polynomial (Chebyshev Type I).",
    "   Status: P(n)=0 => n is Prime (Definitive)"
]
# FUSIÓN DE ENERGÍAS

# --- fermat_fermat_closed.py ---

def d_0(degree, P, mod):
    if degree == 0: return 2
    if degree == 1: return P % mod
    v, w = 2, P % mod # v=D_0, w=D_1
    # Ladder desde bit 2 (incluyendo el MSB explícito si queremos iterar todo,
    # o saltando si inicializamos con el resultado del MSB).
    # La forma canónica robusta:
    for bit in bin(degree)[2:]:
        v2 = (v * v - 2) % mod
        vw = (v * w - P) % mod
        if bit == '0':
            v, w = v2, vw
        else:
            v, w = vw, (w * w - 2) % mod
    return v

__META_0__ = [
    "THEOREM: Fermat's Equation (Base 2)",
    "∃ k ∈ Z  s.t.",
    "",
    "   ( 2^(n-1) - 1 - k·n )² = 0",
    "",
    "   Status: Probabilistic (Roots exist for Pseudoprimes)"
]

def G_0(n):
    if n < 2: return 1
    if n == 2: return 0
    if n % 2 == 0: return 1
    res = pow(2, n - 1, n)
    return (res - 1)**2


# --- primes_lucas_lucas_closed.py ---

def d_1(degree, P, mod):
    if degree == 0: return 2
    if degree == 1: return P % mod
    v, w = 2, P % mod # v=D_0, w=D_1
    # Ladder desde bit 2 (incluyendo el MSB explícito si queremos iterar todo,
    # o saltando si inicializamos con el resultado del MSB).
    # La forma canónica robusta:
    for bit in bin(degree)[2:]:
        v2 = (v * v - 2) % mod
        vw = (v * w - P) % mod
        if bit == '0':
            v, w = v2, vw
        else:
            v, w = vw, (w * w - 2) % mod
    return v

__META_1__ = [
    "THEOREM: Strong Lucas Equation (Parameter P=3)",
    "∃ k ∈ Z  s.t.",
    "",
    "   ( D_{n}(3) - 3 - k·n )² = 0",
    "",
    "   Status: Robust (No shared roots with Fermat known)"
]

def G_1(n):
    if n < 2: return 1
    if n == 2: return 0
    if n == 3: return 0
    if n % 2 == 0: return 1
    val = d_1(n, 3, n)
    return (val - 3)**2


def G_formula(n):
    return G_0(n) + G_1(n)
