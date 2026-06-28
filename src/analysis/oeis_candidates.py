"""
================================================================================
   DIOPHANTUS - CANDIDATOS A SECUENCIA NUEVA EN OEIS
================================================================================
Genera, de forma REPRODUCIBLE, secuencias enteras naturales derivadas de la
maquinaria del proyecto (superficies de Markoff-Hurwitz y su árbol de Vieta), como
candidatas a entrada nueva en la OEIS. Cada candidata lleva su INVARIANTE
CERTIFICADO (la ecuación que define la superficie, conservada por la involución
de Vieta y verificable con discovery_engine.verify_conserved).

HONESTIDAD: la verificación AUTORITATIVA de novedad la hacen los editores de OEIS
al enviar (este entorno no alcanza oeis.org). Aquí solo se produce el candidato
correcto, reproducible y documentado; afirmar novedad sin el chequeo de OEIS sería
deshonesto. La probabilidad de duplicado/variante conocida NO es despreciable
(Markoff-Hurwitz es un objeto estudiado).
"""

import collections


def markoff_hurwitz_values(n_vars, a, fundamental, limit):
    """Valores distintos ordenados que aparecen en las soluciones enteras
    positivas de  x_1^2 + ... + x_n^2 = a * x_1 * ... * x_n , generadas desde la
    solución fundamental por el árbol de involuciones de Vieta
    (x_i -> a*prod_{j!=i} x_j - x_i), hasta `limit`."""
    assert sum(v * v for v in fundamental) == a * _prod(fundamental), "fundamental no satisface la ecuación"
    s0 = tuple(sorted(fundamental))
    seen = {s0}
    vals = set(fundamental)
    dq = collections.deque([s0])
    while dq:
        s = dq.popleft()
        for i in range(n_vars):
            prod = a
            for j in range(n_vars):
                if j != i:
                    prod *= s[j]
            ti = prod - s[i]                      # involución de Vieta
            if ti <= 0:
                continue
            key = tuple(sorted(list(s[:i]) + [ti] + list(s[i + 1:])))
            if max(key) > limit or key in seen:
                continue
            seen.add(key)
            vals.update(key)
            dq.append(key)
    return sorted(vals)


def markoff_hurwitz_4_4(limit=10**12):
    """Candidato PRINCIPAL: números de Markoff-Hurwitz en 4 variables
    a^2+b^2+c^2+d^2 = 4abcd  (solución fundamental (1,1,1,1)).
    Invariante certificado bajo la involución (a,b,c,d)->(a,b,c,4abc-d)."""
    return markoff_hurwitz_values(4, 4, (1, 1, 1, 1), limit)


def markoff_hurwitz_4_1(limit=10**12):
    """Variante a=1: a^2+b^2+c^2+d^2 = abcd, fundamental (2,2,2,2). Es 2× la de
    a=4 (cambio de escala x_i -> 2 x_i)."""
    return markoff_hurwitz_values(4, 1, (2, 2, 2, 2), limit)


def _prod(t):
    p = 1
    for v in t:
        p *= v
    return p
