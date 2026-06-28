
def dickson_eval(degree, P, mod):
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

__LATEX_REPR__ = [
    "THEOREM: Strong Lucas Equation (Parameter P=3)",
    "∃ k ∈ Z  s.t.",
    "",
    "   ( D_{n}(3) - 3 - k·n )² = 0",
    "",
    "   Status: Robust (No shared roots with Fermat known)"
]

def G_formula(n):
    if n < 2: return 1
    if n == 2: return 0
    if n == 3: return 0
    if n % 2 == 0: return 1
    val = dickson_eval(n, 3, n)
    return (val - 3)**2
