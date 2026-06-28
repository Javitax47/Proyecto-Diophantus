"""
================================================================================
   DIOPHANTUS PRODUCT - RE-VERIFICADOR INDEPENDIENTE  (el diferenciador)
================================================================================
Re-verifica un certificado de corrección con ÁLGEBRA ELEMENTAL, importando SÓLO
sympy: NO importa Z3, NO importa el motor de descubrimiento, NO confía en quien
emitió el certificado. Esto es lo que un auditor, un revisor de grant o un cliente
ejecuta para creerse el veredicto sin creerse al proveedor (a diferencia de un
prover de caja negra como el de Certora).

Las tres comprobaciones son pura identidad polinómica / sustitución:
  * nullstellensatz:  expandir  sum_i cof_i * p_i  y comprobar que es EXACTAMENTE 1
                      => {p_i = 0} no tiene solución (inalcanzable).
  * witness:          sustituir la asignación y comprobar que todo p_i da 0
                      => el estado es alcanzable (contraejemplo válido).
  * sos:              expandir  sum_j c_j * q_j^2  y comprobar que es p, con c_j>=0
                      => p >= 0.

Uso (independiente, sin el resto del proyecto):
    python -m src.product.recheck  certificado.json
Devuelve código 0 si el certificado es VÁLIDO, 1 si NO.
"""

import sys
import json

import sympy


def _symbols(var_names):
    return {n: sympy.Symbol(n) for n in var_names}


def recheck(cert):
    """Re-verifica un dict-certificado. Devuelve (ok: bool, mensaje: str)."""
    if not isinstance(cert, dict) or 'kind' not in cert:
        return False, "certificado mal formado (sin 'kind')"
    kind = cert['kind']
    local = _symbols(cert.get('var_names', []))

    def P(s):
        return sympy.expand(sympy.sympify(s, locals=local))

    if kind == 'nullstellensatz':
        polys = [P(s) for s in cert['system']]
        cof = [P(s) for s in cert['certificate']['cofactors']]
        if len(cof) != len(polys):
            return False, "nº de cofactores != nº de polinomios"
        s = sympy.expand(sum(cof[i] * polys[i] for i in range(len(polys))))
        if sympy.simplify(s - 1) == 0:
            return True, f"Nullstellensatz válido: sum g_i·p_i = 1 ⇒ INALCANZABLE ({len(polys)} ecuaciones)"
        return False, f"Nullstellensatz INVÁLIDO: sum g_i·p_i = {s} (≠ 1)"

    if kind == 'witness':
        polys = [P(s) for s in cert['system']]
        assign = cert['certificate']['assignment']
        subs = {local[k]: sympy.Integer(v) for k, v in assign.items() if k in local}
        bad = [str(p) for p in polys if sympy.expand(p.subs(subs)) != 0]
        if not bad:
            return True, f"Testigo válido: la asignación anula las {len(polys)} ecuaciones ⇒ ALCANZABLE"
        return False, f"Testigo INVÁLIDO: no anula {len(bad)} ecuación(es)"

    if kind == 'sos':
        p = P(cert['polynomial'])
        squares = cert['certificate']['squares']
        acc = sympy.Integer(0)
        for c_str, q_str in squares:
            c = sympy.nsimplify(sympy.sympify(c_str))
            if c < 0:
                return False, "SOS INVÁLIDO: coeficiente negativo"
            acc += c * P(q_str)**2
        if sympy.expand(acc - p) == 0:
            return True, f"SOS válido: sum c_j·q_j² = p, c_j≥0 ⇒ p ≥ 0 ({len(squares)} cuadrados)"
        return False, "SOS INVÁLIDO: la suma de cuadrados no reconstruye p"

    return False, f"tipo de certificado desconocido: {kind}"


def recheck_file(path):
    with open(path, encoding="utf-8") as f:
        cert = json.load(f)
    return recheck(cert)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("uso: python -m src.product.recheck <certificado.json>")
        return 2
    ok, msg = recheck_file(argv[0])
    mark = "VÁLIDO ✓" if ok else "INVÁLIDO ✗"
    print(f"[recheck] {mark}: {msg}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
