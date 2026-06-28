#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - FILTRO DE NOVEDAD / INTERÉS DE CONJETURAS
================================================================================
Valida src/analysis/conjecture_filter.py: el contraste de novedad APROXIMADO
(sin acceso externo) que (1) marca PCFs clásicas conocidas, (2) prioriza
constantes poco charteadas (ζ(3), Catalan, γ) sobre e/π, (3) puntúa por tasa de
convergencia. Honesto: "no clásica aquí" ≠ "demostrada nueva".

Uso:  python src/tests/verification/test_conjecture_filter.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import mpmath  # noqa: F401
except ImportError:
    print("[SKIP] mpmath no está instalado.")
    sys.exit(0)

from src.analysis.conjecture_filter import (
    is_classical, mobius_class, mobius_value_class, rank_candidates,
    convergence_digits_per_step, CONSTANT_NOVELTY_PRIOR,
)


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def H(a, b, const, rel, closed="?"):
    return {'a_coeffs': a, 'b_coeffs': b, 'constant': const, 'relation': rel, 'closed_form': closed}


def test_classical_flag(stats):
    print(f"{Colors.HEADER}[1] Marca PCFs clásicas conocidas (Brouncker, e de Euler){Colors.ENDC}")
    if is_classical(H([0, 0, 1], [1, 2], 'pi', [-4, 0, 0, 1])) and is_classical(H([0, -1, 0], [3, 1], 'e', [0, -1, 1, 0])):
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Brouncker (4/π) y e (Euler) reconocidas como clásicas")
    else:
        stats.fail("no reconoció una PCF clásica")


def test_novelty_prior(stats):
    print(f"{Colors.HEADER}[2] Prior: constantes poco charteadas puntúan por encima de e/π{Colors.ENDC}")
    if (CONSTANT_NOVELTY_PRIOR['catalan'] > CONSTANT_NOVELTY_PRIOR['zeta3'] > CONSTANT_NOVELTY_PRIOR['pi']
            and CONSTANT_NOVELTY_PRIOR['euler_gamma'] > CONSTANT_NOVELTY_PRIOR['e']):
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Catalan > ζ(3) > π y γ > e (poco charteadas priorizadas)")
    else:
        stats.fail("prior de novedad incoherente")


def test_ranking_dedup(stats):
    print(f"{Colors.HEADER}[3] Ranking: deduplica por Möbius, separa conocidas de candidatas{Colors.ENDC}")
    hits = [
        H([0, 0, 1], [1, 2], 'pi', [-4, 0, 0, 1]),        # Brouncker (clásica)
        H([1, 1], [2, 1], 'catalan', [3, 1, -2, 0], "catalan"),   # candidata (Catalan, alta novedad)
        H([1, 1], [2, 1], 'catalan', [3, 1, -2, 0], "catalan"),   # DUPLICADA (misma clase)
        H([0, 1], [1, 1], 'e', [1, 1, 0, -1], "e"),       # candidata (e, baja novedad)
    ]
    ranked = rank_candidates(hits, compute_convergence=False)
    cands = [r for r in ranked if r['status'].startswith('CANDIDATA')]
    known = [r for r in ranked if r['status'].startswith('CONOCIDA')]
    # 1 clásica, 2 candidatas únicas (la duplicada se colapsa), Catalan antes que e
    if len(known) == 1 and len(cands) == 2 and cands[0]['hit']['constant'] == 'catalan':
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 1 conocida, 2 candidatas (dedup), Catalan rankea sobre e")
    else:
        stats.fail(f"ranking inesperado: known={len(known)} cands={[c['hit']['constant'] for c in cands]}")


def test_convergence_metric(stats):
    print(f"{Colors.HEADER}[4] Tasa de convergencia: Brouncker converge a ritmo positivo y finito{Colors.ENDC}")
    rate = convergence_digits_per_step([0, 0, 1], [1, 2])   # Brouncker (convergencia lenta, polinómica)
    if rate >= 0 and rate < 5:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Brouncker: {rate:.3f} dígitos/paso (medible y razonable)")
    else:
        stats.fail(f"tasa de convergencia anómala: {rate}")


def test_value_class_dedup(stats):
    print(f"{Colors.HEADER}[5] Dedup por VALOR: mismo número colapsa, distinto número separa{Colors.ENDC}")
    # Dos PCFs distintas (a,b) con la MISMA identificación (4/π) -> misma huella de valor.
    k1 = mobius_value_class(H([0, 0, 1], [1, 2], 'pi', [-4, 0, 0, 1]))
    k2 = mobius_value_class(H([9, 9, 9], [7, 7], 'pi', [-4, 0, 0, 1]))   # otra a,b, mismo valor 4/π
    # Valores distintos (4/π vs una identidad de e) -> huellas distintas.
    ke = mobius_value_class(H([0, -1], [3, 1], 'e', [0, -1, 1, 0]))
    if k1 == k2 and ke != k1:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} dos PCFs -> mismo 4/π colapsan; valor de e queda separado")
    else:
        stats.fail(f"huellas inesperadas: 4/π_a={k1} 4/π_b={k2} e={ke}")


def main():
    print(f"{Colors.BOLD}=== FILTRO DE NOVEDAD / INTERÉS DE CONJETURAS ==={Colors.ENDC}")
    stats = Stats()
    test_classical_flag(stats)
    test_novelty_prior(stats)
    test_ranking_dedup(stats)
    test_convergence_metric(stats)
    test_value_class_dedup(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — filtro de novedad aproximado: marca clásicas, "
              f"prioriza lo poco charteado, puntúa por convergencia. Contraste autoritativo = externo.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
