"""
================================================================================
   DIOPHANTUS PRODUCT - VERTICAL SUBSET-SUM  (capa universal de certificados)
================================================================================
Cuarto dominio que emite EL MISMO certificado portable y lo re-verifica con EL
MISMO `recheck` (solo sympy) que los programas, el coloreado de grafos y el
SAT/CNF. Aquí el dominio es numérico: decidir si algún subconjunto de una lista
de enteros `weights` suma exactamente `target`.

Codificación entera (una variable 0/1 por elemento):

    x_i^2 - x_i = 0                 (x_i ∈ {0,1}: dentro / fuera del subconjunto)
    Σ_i weights_i · x_i - target = 0   (el subconjunto elegido suma target)

Entonces:
  * factible  ⟶  testigo ENTERO (el vector 0/1 del subconjunto), re-verificable
    por sustitución.  (verdict SAT)
  * infactible  ⟶  certificado de Nullstellensatz (Σ gᵢ·pᵢ = 1), re-verificable
    expandiendo un polinomio.  (verdict UNSAT)

El finder de Nullstellensatz es de grado acotado (sólido, no completo): si no
certifica hasta `max_deg`, devuelve None y no afirma nada.
"""

import sympy

from src.product import verifier


def _item_vars(n):
    return [f"x{i}" for i in range(n)]


def subset_sum_system(weights, target):
    """Sistema polinómico (sympy) cuya solución 0/1 ⟺ un subconjunto de `weights`
    suma `target`. Devuelve (polys, var_names)."""
    n = len(weights)
    var_names = _item_vars(n)
    xs = [sympy.Symbol(nm) for nm in var_names]
    polys = [xs[i]**2 - xs[i] for i in range(n)]                     # x_i ∈ {0,1}
    polys.append(sum(weights[i] * xs[i] for i in range(n)) - target)  # Σ a_i x_i = target
    return [sympy.expand(p) for p in polys], var_names


def find_subset(weights, target):
    """Fuerza bruta: devuelve el vector 0/1 de un subconjunto que suma `target`,
    o None si no existe. El subconjunto vacío (suma 0) es válido para target 0."""
    n = len(weights)
    for mask in range(1 << n):
        if sum(weights[i] for i in range(n) if (mask >> i) & 1) == target:
            return [(mask >> i) & 1 for i in range(n)]
    return None


def certify_infeasible(weights, target, max_deg=3):
    """Certifica que NINGÚN subconjunto suma `target` vía Nullstellensatz portable.
    Prueba grados crecientes hasta `max_deg`. Devuelve el dict-certificado o None."""
    polys, var_names = subset_sum_system(weights, target)
    claim = f"ningún subconjunto de {list(weights)} suma {target}"
    for deg in range(1, max_deg + 1):
        cert = verifier.certify_unreachable(polys, var_names, claim=claim, max_deg=deg)
        if cert is not None:
            return cert
    return None


def certify_witness(weights, target):
    """Si algún subconjunto suma `target`, emite un testigo ENTERO 0/1
    re-verificable. Devuelve el dict-certificado o None."""
    subset = find_subset(weights, target)
    if subset is None:
        return None
    polys, var_names = subset_sum_system(weights, target)
    assignment = {var_names[i]: subset[i] for i in range(len(weights))}
    claim = f"existe un subconjunto de {list(weights)} que suma {target}"
    return verifier.certify_witness(polys, var_names, assignment, claim=claim)


def certify(weights, target, max_deg=3):
    """Veredicto unificado: intenta testigo (factible) o certificado de
    infactibilidad (Nullstellensatz). Devuelve (cert_dict_o_None, factible:bool)."""
    if find_subset(weights, target) is not None:
        return certify_witness(weights, target), True
    return certify_infeasible(weights, target, max_deg=max_deg), False
