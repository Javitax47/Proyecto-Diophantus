"""
================================================================================
   DIOPHANTUS PRODUCT - VERTICAL SAT/CNF  (capa universal de certificados)
================================================================================
Tercer dominio de la capa universal *trustless*: **insatisfacibilidad booleana (SAT)**.
El MISMO certificado portable y el MISMO `recheck.py` (solo sympy) que certifican
programas y coloreado de grafos certifican aquí que una fórmula CNF NO tiene modelo.

Codificación de Hilbert-Nullstellensatz para CNF (proof complexity clásica):
  * cada variable es booleana:           bᵢ² − bᵢ = 0
  * cada cláusula (l₁ ∨ … ∨ l_k) se viola SOLO en una asignación; el monomio que vale 1
    en esa asignación es  Π (1−bᵢ)[lit positivo] · Π bᵢ[lit negativo].  Exigirlo = 0
    PROHÍBE esa asignación ⟹ la cláusula queda satisfecha.
Entonces la CNF es:
  * INSATISFACIBLE  ⟺  el sistema no tiene solución booleana  ⟶  certificado
    Nullstellensatz (Σ gᵢ·pᵢ = 1).   (verdict UNSAT)
  * SATISFACIBLE     ⟶  testigo (un modelo 0/1), re-verificable por sustitución. (SAT)

Cláusulas en formato DIMACS (enteros con signo, 1-based): +i ⇒ bᵢ₋₁ verdadera,
−i ⇒ bᵢ₋₁ falsa. Ej.: [[1,-2],[ -1,2]] = (b0 ∨ ¬b1) ∧ (¬b0 ∨ b1).
"""

from itertools import product as _product

import sympy

from src.product import verifier


def _var_names(n):
    return [f"b{i}" for i in range(n)]


def cnf_system(n_vars, clauses):
    """Sistema polinómico (sympy) cuya solución booleana ⟺ modelo de la CNF.
    Devuelve (polys, var_names)."""
    var_names = _var_names(n_vars)
    syms = {name: sympy.Symbol(name) for name in var_names}
    xs = [syms[name] for name in var_names]
    polys = [xs[i]**2 - xs[i] for i in range(n_vars)]         # booleanidad
    for cl in clauses:
        term = sympy.Integer(1)
        for lit in cl:
            i = abs(lit) - 1
            term *= (1 - xs[i]) if lit > 0 else xs[i]          # monomio falsificador
        polys.append(sympy.expand(term))
    return polys, var_names


def find_model(n_vars, clauses):
    """Busca (fuerza bruta) un modelo 0/1 que satisface todas las cláusulas; None si UNSAT."""
    for bits in _product((0, 1), repeat=n_vars):
        if all(any((bits[abs(l) - 1] == 1) if l > 0 else (bits[abs(l) - 1] == 0) for l in cl)
               for cl in clauses):
            return list(bits)
    return None


def certify_unsat(n_vars, clauses, max_deg=2):
    """Certifica que la CNF es INSATISFACIBLE vía Nullstellensatz portable.
    Devuelve el dict-certificado (mismo formato que verifier) o None."""
    polys, var_names = cnf_system(n_vars, clauses)
    claim = f"la CNF de {n_vars} variables y {len(clauses)} cláusulas es INSATISFACIBLE"
    return verifier.certify_unreachable(polys, var_names, claim=claim, max_deg=max_deg)


def certify_sat_witness(n_vars, clauses):
    """Si la CNF es satisfacible, emite un testigo 0/1 (modelo) re-verificable. None si UNSAT."""
    model = find_model(n_vars, clauses)
    if model is None:
        return None
    polys, var_names = cnf_system(n_vars, clauses)
    assignment = {var_names[i]: int(model[i]) for i in range(n_vars)}
    return verifier.certify_witness(polys, var_names, assignment,
                                    claim="la CNF es satisfacible; testigo (modelo 0/1)")


def certify_sat(n_vars, clauses, max_deg=2):
    """Veredicto unificado: testigo si hay modelo, o certificado de insatisfacibilidad.
    Devuelve (cert_dict, satisfacible:bool). cert puede ser None si no se certifica UNSAT
    a `max_deg`."""
    wit = certify_sat_witness(n_vars, clauses)
    if wit is not None:
        return wit, True
    return certify_unsat(n_vars, clauses, max_deg=max_deg), False
