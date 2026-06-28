"""
================================================================================
   DIOPHANTUS - NO-EXISTENCIA CERTIFICADA DE CICLOS DE COLLATZ (§6.3 del informe)
================================================================================
Codifica "existe un ciclo no trivial de longitud L" de la dinamica de collatz
(variante (3n+1)/2) como un sistema diofantico y deja que Z3 lo refute (UNSAT).
NO prueba la conjetura de Collatz; certifica, para longitudes concretas, que no
hay ciclos no triviales (un resultado conocido -cf. Simons-de Weger- reproducido
aqui como insatisfacibilidad de un sistema concreto, el angulo que el informe
sugiere como publicable: "dinamica -> geometria, certificada").

Transicion de un paso (sin selector de paridad, polinomica):
    2*x_{i+1} = x_i + b_i*(2*x_i + 1),   b_i = x_i mod 2  (x_i par -> x/2 ; impar -> (3x+1)/2)

Un ciclo de longitud L: x_0 -> x_1 -> ... -> x_{L-1} -> x_0, todos enteros >= 1.
"No trivial" = contiene algun valor >= 3 (el unico ciclo con valores <= 2 es {1,2}).
"""

from z3 import Int, Solver, And, Or, sat, unsat


def cycle_system(L):
    """Construye (solver) que es SAT sii existe un ciclo de collatz de longitud L
    con algun elemento >= 3 (ciclo no trivial)."""
    s = Solver()
    xs = [Int(f'x{i}') for i in range(L)]
    bs = [Int(f'b{i}') for i in range(L)]
    qs = [Int(f'q{i}') for i in range(L)]
    for i in range(L):
        s.add(xs[i] >= 1)                       # enteros positivos
        s.add(Or(bs[i] == 0, bs[i] == 1))       # bit de paridad
        s.add(xs[i] == 2 * qs[i] + bs[i])       # b_i = paridad(x_i), q_i >= 0
        s.add(qs[i] >= 0)
        nxt = xs[(i + 1) % L]
        s.add(2 * nxt == xs[i] + bs[i] * (2 * xs[i] + 1))   # transicion (un paso)
    s.add(Or([xs[i] >= 3 for i in range(L)]))   # no trivial (excluye {1,2})
    return s, xs


def no_nontrivial_cycle(L, timeout_ms=15000):
    """Devuelve 'unsat' (no hay ciclo no trivial de longitud L), 'sat' (existe;
    devolveria contraejemplo) o 'unknown' (Z3 no concluyo en el tiempo dado)."""
    s, xs = cycle_system(L)
    s.set("timeout", timeout_ms)
    r = s.check()
    if r == unsat:
        return 'unsat', None
    if r == sat:
        m = s.model()
        return 'sat', [m[x].as_long() for x in xs]
    return 'unknown', None


def certify_up_to(max_len, timeout_ms=15000):
    """Certifica la no-existencia de ciclos no triviales de longitud 1..max_len.
    Devuelve (proven, results) con proven = mayor L tal que 1..L son todos unsat."""
    results = {}
    proven = 0
    for L in range(1, max_len + 1):
        verdict, witness = no_nontrivial_cycle(L, timeout_ms)
        results[L] = (verdict, witness)
        if verdict == 'unsat' and proven == L - 1:
            proven = L
    return proven, results
