"""
================================================================================
   DIOPHANTUS PRODUCT - VERTICAL NN-LINEAL  (capa universal de certificados)
================================================================================
Sexto dominio de la capa trustless: certificar una propiedad de robustez de una
CAPA LINEAL (o clasificador afín)   y(x) = Σ_i w_i x_i + b   sobre una caja de
entradas   x_i ∈ [lo_i, hi_i]   (el fragmento lineal de una red neuronal). Mismo
certificado portable, mismo `recheck`.

Propiedad: ¿es y(x) >= L para TODA entrada de la caja? (p. ej. una pre-activación
que nunca cambia de signo — ReLU siempre activa —, o el margen de un clasificador
que nunca cae bajo un umbral).

  * robusto (y >= L en toda la caja)  ->  certificado de Positivstellensatz
    (Handelman lineal):   y - L = c0 + Σ_i λ_i·(x_i - lo_i) + Σ_i μ_i·(hi_i - x_i),
    con c0, λ_i, μ_i >= 0. En cualquier punto de la caja los factores son >= 0,
    luego y - L >= 0. Re-verificable expandiendo un polinomio y comprobando signos.
  * NO robusto  ->  testigo: el vértice de la caja donde y alcanza su mínimo
    (< L), re-verificable por sustitución.

Como y es lineal, su mínimo sobre la caja está en un vértice (x_i = lo_i si w_i>=0,
si no hi_i); el certificado es exacto (Handelman de grado 1 es completo para p
lineal sobre una caja). Se asumen pesos/bias/cotas enteros (vértices enteros -> el
testigo de violación es una asignación entera).
"""

import sympy

from src.product import verifier


def _in_vars(n):
    return [f"x{i}" for i in range(n)]


def margin_poly(weights, bias, var_names):
    """y(x) = Σ w_i x_i + b como expresión sympy."""
    xs = [sympy.Symbol(v) for v in var_names]
    return sympy.expand(sum(weights[i] * xs[i] for i in range(len(weights))) + bias)


def box_min(weights, bias, box):
    """Mínimo de y sobre la caja y el vértice que lo alcanza (y es lineal)."""
    val = bias
    vertex = []
    for i, w in enumerate(weights):
        lo, hi = box[i]
        if w >= 0:
            vertex.append(lo); val += w * lo
        else:
            vertex.append(hi); val += w * hi
    return val, vertex


def certify_lower_bound(weights, bias, box, L=0):
    """Certifica `y(x) >= L` sobre la caja vía Positivstellensatz (Handelman
    lineal). Devuelve el cert o None si el mínimo es < L (no es cota válida)."""
    n = len(weights)
    var_names = _in_vars(n)
    xs = [sympy.Symbol(v) for v in var_names]
    p = margin_poly(weights, bias, var_names) - L
    constraints, multipliers = [], []
    c0 = bias - L
    for i, w in enumerate(weights):
        lo, hi = box[i]
        if w >= 0:
            if w != 0:
                constraints.append(xs[i] - lo); multipliers.append(w)   # w·(x_i - lo)
            c0 += w * lo
        else:
            constraints.append(hi - xs[i]); multipliers.append(-w)      # (-w)·(hi - x_i)
            c0 += w * hi
    if c0 < 0:
        return None
    claim = f"y(x) >= {L} para todo x en la caja"
    return verifier.certify_positivstellensatz(p, constraints, multipliers, c0,
                                               var_names, claim=claim)


def certify_violation(weights, bias, box, L=0):
    """Si el mínimo es < L, emite un testigo: el vértice donde y = mínimo < L,
    re-verificable por sustitución. Requiere vértice entero. Devuelve None si es
    robusto o el vértice no es entero."""
    mn, vertex = box_min(weights, bias, box)
    if mn >= L:
        return None
    if any(v != int(v) for v in vertex):
        return None
    n = len(weights)
    var_names = _in_vars(n)
    xs = [sympy.Symbol(v) for v in var_names]
    # Sistema que fija el punto y su valor: {x_i - vertex_i} + {y(x) - mn}.
    system = [xs[i] - vertex[i] for i in range(n)] + [margin_poly(weights, bias, var_names) - mn]
    assignment = {var_names[i]: int(vertex[i]) for i in range(n)}
    claim = f"existe x en la caja con y(x) = {mn} < {L}"
    return verifier.certify_witness(system, var_names, assignment, claim=claim)


def certify(weights, bias, box, L=0):
    """Veredicto unificado: si y >= L en toda la caja, certificado de robustez
    (Positivstellensatz); si no, testigo de violación. Devuelve (cert, robusto:bool)."""
    mn, _ = box_min(weights, bias, box)
    if mn >= L:
        return certify_lower_bound(weights, bias, box, L), True
    return certify_violation(weights, bias, box, L), False
