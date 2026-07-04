"""
================================================================================
   DIOPHANTUS PRODUCT - VERIFIER  (API "Certificado de Corrección", C1)
================================================================================
Toma un sistema polinómico (la arithmetización fiel de un programa, posiblemente
anclado a una salida) y emite un VEREDICTO con un CERTIFICADO PORTABLE:

  * UNSAT (inalcanzable): la salida/estado afirmado NO puede ocurrir. Certificado
    de Nullstellensatz (cofactores con sum g_i p_i = 1). Caso de uso: "este
    programa NO puede producir esta salida incorrecta / alcanzar este estado de
    error" -> corrección demostrable.
  * SAT (alcanzable): existe una ejecución que lo produce. Certificado = testigo
    (asignación). Caso de uso: contraejemplo / bug encontrado.
  * NONNEG: un polinomio (p. ej. una función de energía/drift) es >= 0. Certificado
    de suma de cuadrados (SOS / Positivstellensatz).

El certificado es un dict JSON-serializable, RE-VERIFICABLE por un tercero con
`recheck` usando sólo álgebra (sin Z3, sin este motor). Ese es el producto.
"""

import datetime

import sympy

from src.product import TOOL_VERSION, CERT_SCHEMA
from src.analysis.certificates import nullstellensatz_certificate
from src.analysis.sos import sos_certificate


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _exprs(polys, var_names):
    local = {n: sympy.Symbol(n) for n in var_names}
    out = []
    for p in polys:
        out.append(p if isinstance(p, sympy.Expr) else sympy.sympify(str(p), locals=local))
    return out


def certify_unreachable(polys, var_names, claim="", max_deg=2):
    """Intenta certificar que el sistema {p_i = 0} NO tiene solución (estado
    inalcanzable) emitiendo un certificado de Nullstellensatz portable.
    Devuelve el dict-certificado o None si no logra certificar a este grado."""
    polys = _exprs(polys, var_names)
    cof = nullstellensatz_certificate(polys, var_names, max_deg)
    if cof is None:
        return None
    return {
        'schema': CERT_SCHEMA,
        'tool_version': TOOL_VERSION,
        'kind': 'nullstellensatz',
        'verdict': 'UNSAT',
        'claim': claim or "el sistema p_i=0 es inalcanzable",
        'var_names': list(var_names),
        'system': [str(sympy.expand(p)) for p in polys],
        'certificate': {'cofactors': [str(sympy.expand(c)) for c in cof]},
        'created': _now(),
    }


def certify_witness(polys, var_names, assignment, claim=""):
    """Emite un certificado de SATISFACIBILIDAD (testigo): la asignación que anula
    todos los polinomios (estado alcanzable / contraejemplo)."""
    polys = _exprs(polys, var_names)
    return {
        'schema': CERT_SCHEMA,
        'tool_version': TOOL_VERSION,
        'kind': 'witness',
        'verdict': 'SAT',
        'claim': claim or "el sistema p_i=0 es alcanzable (testigo)",
        'var_names': list(var_names),
        'system': [str(sympy.expand(p)) for p in polys],
        'certificate': {'assignment': {k: int(v) for k, v in assignment.items()}},
        'created': _now(),
    }


def certify_nonneg(p, var_names, claim="", max_deg=2):
    """Intenta certificar p >= 0 como suma de cuadrados (SOS). Devuelve el
    dict-certificado o None."""
    p = _exprs([p], var_names)[0]
    cert = sos_certificate(p, var_names, max_deg)
    if cert is None:
        return None
    return {
        'schema': CERT_SCHEMA,
        'tool_version': TOOL_VERSION,
        'kind': 'sos',
        'verdict': 'NONNEG',
        'claim': claim or "el polinomio es no negativo (>= 0)",
        'var_names': list(var_names),
        'polynomial': str(sympy.expand(p)),
        'certificate': {'squares': [[str(c), str(sympy.expand(q))] for c, q in cert['squares']]},
        'created': _now(),
    }


def certify_positivstellensatz(p, constraints, multipliers, constant, var_names, claim=""):
    """Emite un certificado de Positivstellensatz (Handelman lineal): prueba
    `p >= 0` sobre el dominio `{g_j >= 0}` con la identidad
        p = constant + sum_j multipliers_j * constraints_j,
    con `constant >= 0` y cada `multipliers_j >= 0` (constantes). Auto-verifica la
    identidad y los signos; devuelve el dict-certificado o None si no cuadra."""
    p = _exprs([p], var_names)[0]
    gs = _exprs(constraints, var_names)
    if constant < 0 or any(m < 0 for m in multipliers):
        return None
    acc = sympy.Integer(constant) + sum(sympy.Integer(multipliers[j]) * gs[j]
                                        for j in range(len(gs)))
    if sympy.expand(acc - p) != 0:
        return None
    return {
        'schema': CERT_SCHEMA,
        'tool_version': TOOL_VERSION,
        'kind': 'positivstellensatz',
        'verdict': 'NONNEG',
        'claim': claim or "el polinomio es no negativo (>= 0) sobre el dominio",
        'var_names': list(var_names),
        'polynomial': str(sympy.expand(p)),
        'certificate': {
            'constant': str(constant),
            'terms': [[str(multipliers[j]), str(sympy.expand(gs[j]))] for j in range(len(gs))],
        },
        'created': _now(),
    }


# ---------------------------------------------------------------------------
#  Frontend de programa real (C -> sistema PURE -> certificado)
# ---------------------------------------------------------------------------

def system_from_pure_file(path):
    """Lee un fichero PURE (output/<base>_pure_poly_system.txt) y devuelve
    (polys_expr, var_names)."""
    from src.analysis import sympy_system
    with open(path, encoding="utf-8") as f:
        lines = [l for l in f.read().splitlines() if l.strip()]
    eqs, syms = sympy_system.build_system(lines)
    var_names = [s.name for s in syms]
    polys = [e.lhs for e in eqs]
    return polys, var_names
