"""
================================================================================
   DIOPHANTUS PRODUCT - VERTICAL COTA-QUBO  (capa universal de certificados)
================================================================================
Quinto dominio de la capa trustless: certificar una COTA INFERIOR (u ÓPTIMO) de
un QUBO   p(x) = Σ_i c_i x_i + Σ_{(i,j)} Q_ij x_i x_j   sobre x ∈ {0,1}^n,
reutilizando EL MISMO certificado portable y EL MISMO `recheck`.

La cota se descompone en piezas estándar, cada una re-verificable por separado:
  * ALCANZABILIDAD: una asignación 0/1 que logra el valor L  ->  testigo.
  * NADIE LO MEJORA: como p es entero sobre el cubo, `p(x) >= L` equivale a que
    p NO toma ningún entero v < L. Cada `{x_i^2 - x_i = 0, p(x) - v = 0}` se
    certifica infactible con un Nullstellensatz portable, para v desde la cota
    trivial Σ min(0, coef) hasta L-1.

Propiedad de soundness clave: NO se puede certificar una cota falsa. Si L es mayor
que el mínimo real, el valor v = mínimo sigue siendo alcanzable, su sistema es
FACTIBLE, no hay Nullstellensatz, y `certify_bound` devuelve None.

El finder de Nullstellensatz es de grado acotado (sólido, no completo).
"""

import itertools

import sympy

from src.product import verifier


def _item_vars(n):
    return [f"x{i}" for i in range(n)]


def qubo_poly(linear, quad, n):
    """Devuelve (bool_polys, p, var_names): la restricción booleana por variable y
    el polinomio objetivo `p(x)` como expresión sympy."""
    var_names = _item_vars(n)
    xs = [sympy.Symbol(v) for v in var_names]
    p = sum(linear.get(i, 0) * xs[i] for i in range(n))
    p += sum(quad[(i, j)] * xs[i] * xs[j] for (i, j) in quad)
    bool_polys = [xs[i]**2 - xs[i] for i in range(n)]
    return bool_polys, sympy.expand(p), var_names


def evaluate(linear, quad, x):
    """Valor de p en una asignación 0/1 `x`."""
    v = sum(linear.get(i, 0) * x[i] for i in range(len(x)))
    v += sum(quad[(i, j)] * x[i] * x[j] for (i, j) in quad)
    return v


def brute_min(linear, quad, n):
    """Mínimo de p sobre {0,1}^n por fuerza bruta. Devuelve (valor, argmin)."""
    best, arg = None, None
    for x in itertools.product((0, 1), repeat=n):
        v = evaluate(linear, quad, list(x))
        if best is None or v < best:
            best, arg = v, list(x)
    return best, arg


def trivial_lower_bound(linear, quad, n):
    """Cota inferior trivial de p sobre el cubo: Σ min(0, coeficiente). Cada término
    c·(0/1) aporta al menos min(0, c)."""
    return (sum(min(0, linear.get(i, 0)) for i in range(n))
            + sum(min(0, c) for c in quad.values()))


def certify_bound(linear, quad, n, L, max_deg=3):
    """Certifica `p(x) >= L` sobre {0,1}^n descartando cada entero v en
    [cota_trivial, L-1] con un Nullstellensatz. Devuelve el dict-certificado
    (lista de sub-certificados) o None si alguno no se certifica a grado <= max_deg
    o si L no es una cota inferior válida (algún v < L es alcanzable)."""
    bool_polys, p, var_names = qubo_poly(linear, quad, n)
    lo = trivial_lower_bound(linear, quad, n)
    certs = []
    for v in range(lo, L):
        polys = bool_polys + [sympy.expand(p - v)]
        claim = f"ninguna asignación 0/1 da p = {v}"
        cert = None
        for deg in range(1, max_deg + 1):
            cert = verifier.certify_unreachable(polys, var_names, claim=claim, max_deg=deg)
            if cert is not None:
                break
        if cert is None:
            return None
        certs.append(cert)
    return {
        'kind': 'qubo_bound',
        'verdict': 'LOWER_BOUND',
        'bound': L,
        'n': n,
        'claim': f"p(x) >= {L} para todo x en {{0,1}}^{n}",
        'infeasible_certs': certs,
    }


def certify_optimum(linear, quad, n, max_deg=3):
    """Certifica el mínimo V de un QUBO: un testigo que ALCANZA V y una cota
    inferior `p >= V`. Devuelve el dict-certificado o None."""
    V, arg = brute_min(linear, quad, n)
    bool_polys, p, var_names = qubo_poly(linear, quad, n)
    witness = verifier.certify_witness(
        bool_polys + [sympy.expand(p - V)], var_names,
        {var_names[i]: arg[i] for i in range(n)},
        claim=f"asignación 0/1 que alcanza p = {V}")
    bound = certify_bound(linear, quad, n, V, max_deg=max_deg)
    if bound is None:
        return None
    return {
        'kind': 'qubo_optimum',
        'verdict': 'OPTIMUM',
        'optimum': V,
        'argmin': arg,
        'claim': f"el mínimo de p sobre {{0,1}}^{n} es {V}",
        'witness': witness,
        'lower_bound': bound,
    }
