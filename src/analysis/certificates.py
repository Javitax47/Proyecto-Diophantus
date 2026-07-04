"""
================================================================================
   DIOPHANTUS - CERTIFICADOS ALGEBRAICOS PORTABLES (el "producto estrella")
================================================================================
Genera certificados de corrección RE-VERIFICABLES SIN CONFIAR EN EL SOLVER, que
es lo que identifica como el producto recurrente:
un tercero re-comprueba el veredicto con álgebra elemental, sin ejecutar Z3.

Dos tipos:

  * CERTIFICADO DE SATISFACIBILIDAD (testigo). Veredicto "existe solución / la
    traza es alcanzable": el certificado es la asignación; re-verificar =
    sustituir y comprobar que toda ecuación da 0. Trivial e independiente del
    solver.

  * CERTIFICADO DE INSATISFACIBILIDAD (Nullstellensatz). Veredicto "el sistema
    p_1=...=p_m=0 NO tiene solución" (p. ej. "este programa NO puede alcanzar el
    estado de error X"): el certificado son cofactores g_i tales que
        sum_i g_i * p_i = 1   (identidad polinómica).
    Si tal identidad existe, el sistema no tiene solución (ni compleja, luego
    tampoco entera): cualquier solución daría 0 = 1. Re-verificar = EXPANDIR el
    polinomio y comprobar que es 1. Pura álgebra, sin solver.

Garantías honestas:
  - SOUNDNESS: si el verificador acepta el certificado, el veredicto es correcto
    con CERTEZA (la identidad se expande a 1 / el testigo anula las ecuaciones).
  - El finder de Nullstellensatz es de GRADO ACOTADO (Nullstellensatz efectivo):
    si encuentra cofactores, el certificado es válido; si no, devuelve None (no
    afirma nada). Es decir, COMPLETO no, pero SÓLIDO sí — apto para certificados.
"""

from itertools import combinations_with_replacement

import sympy


def _monomials(syms, max_deg):
    out = []
    n = len(syms)
    for deg in range(max_deg + 1):
        for combo in combinations_with_replacement(range(n), deg):
            m = sympy.Integer(1)
            for c in combo:
                m *= syms[c]
            out.append(m)
    return out


# ---------------------------------------------------------------------------
# Certificado de SATISFACIBILIDAD (testigo)
# ---------------------------------------------------------------------------

def verify_witness(polys, assignment, var_names):
    """Re-verifica (SIN solver) que `assignment` anula todos los polinomios
    -> es un certificado de que el sistema es satisfacible / la traza existe."""
    syms = sympy.symbols(var_names)
    subs = {syms[i]: assignment[var_names[i]] for i in range(len(var_names))
            if var_names[i] in assignment}
    return all(sympy.expand(p.subs(subs)) == 0 for p in polys)


# ---------------------------------------------------------------------------
# Certificado de INSATISFACIBILIDAD (Nullstellensatz: sum g_i p_i = 1)
# ---------------------------------------------------------------------------

def nullstellensatz_certificate(polys, var_names, max_deg=2):
    """Busca cofactores g_i (grado <= max_deg) con sum_i g_i*p_i = 1, por álgebra
    lineal sobre los coeficientes. Devuelve la lista de g_i (certificado) o None.
    Encontrarlo PRUEBA que el sistema no tiene solución."""
    syms = sympy.symbols(var_names) if len(var_names) != 1 else (sympy.symbols(var_names[0]),)
    syms = list(syms)
    monos = _monomials(syms, max_deg)
    # cofactor g_i = sum_j c[i][j] * mono_j  (incognitas c)
    cs = []
    gs = []
    for i in range(len(polys)):
        ci = sympy.symbols(f'c{i}_0:{len(monos)}')
        ci = (ci,) if not isinstance(ci, tuple) else ci
        cs.extend(ci)
        gs.append(sum(ci[j] * monos[j] for j in range(len(monos))))
    target = sympy.expand(sum(gs[i] * polys[i] for i in range(len(polys))) - 1)
    poly = sympy.Poly(target, *syms)
    # cada coeficiente (lineal en cs) debe ser 0
    lin_eqs = poly.coeffs()
    sol = sympy.linsolve(lin_eqs, cs)
    if not sol:
        return None
    point = next(iter(sol))
    subs = {cs[i]: point[i] for i in range(len(cs))}
    # fijar parametros libres a 0
    free = {s: 0 for tup in [point] for s in tup if isinstance(s, sympy.Symbol)}
    cofactors = [sympy.expand(g.subs(subs).subs(free)) for g in gs]
    # comprobacion interna
    if sympy.expand(sum(cofactors[i] * polys[i] for i in range(len(polys)))) != 1:
        return None
    return cofactors


def verify_nullstellensatz(polys, cofactors, var_names):
    """Re-verificador PORTABLE (SIN solver): expande sum g_i p_i y comprueba que
    es exactamente 1. Si lo es, el sistema p_i=0 no tiene solución -> certificado
    de insatisfacibilidad válido, comprobable por cualquiera con álgebra."""
    if cofactors is None or len(cofactors) != len(polys):
        return False
    s = sympy.expand(sum(cofactors[i] * polys[i] for i in range(len(polys))))
    return sympy.simplify(s - 1) == 0


# ---------------------------------------------------------------------------
# Certificado unificado de un VEREDICTO de alcanzabilidad
# ---------------------------------------------------------------------------

def certify_unreachable(polys, var_names, max_deg=2):
    """Intenta CERTIFICAR que el sistema p_i=0 es inalcanzable (sin solución)
    emitiendo un certificado de Nullstellensatz portable. Devuelve dict con
    {'verdict','certificate','reverify'} o None si no logra certificar."""
    cof = nullstellensatz_certificate(polys, var_names, max_deg)
    if cof is None:
        return None
    return {
        'verdict': 'UNSAT (inalcanzable)',
        'certificate': cof,
        'reverify': lambda: verify_nullstellensatz(polys, cof, var_names),
    }
