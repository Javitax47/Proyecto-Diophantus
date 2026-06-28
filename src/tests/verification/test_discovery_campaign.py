#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - CAMPAÑA DE DESCUBRIMIENTO (barrido de familias paramétricas)
================================================================================
Valida src/analysis/discovery_campaign.py: el motor barre FAMILIAS paramétricas
enteras, descubre el invariante de cada instancia y lo CERTIFICA idénticamente.
Es la infraestructura para una contribución de matemática experimental: descubrir
+ certificar de forma autónoma, y luego contrastar novedad (paso externo).

Comprueba:
  - el barrido produce, por familia, el invariante paramétrico esperado
    (Markov-Hurwitz x²+y²+z²-k·xyz; forma norma x²-k·xy+y²; formas simplécticas);
  - SOUNDNESS: TODO invariante del catálogo está verificado idénticamente;
  - no hay basura: las familias con coordenadas móviles dan el invariante esencial,
    no monomios triviales.

Uso:  python src/tests/verification/test_discovery_campaign.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import sympy
except ImportError:
    print("[SKIP] sympy no está instalado.")
    sys.exit(0)

from src.analysis.discovery_campaign import (
    run_campaign, scan_instances, family_markov3, family_norm_form,
    family_generalized_markov, scan_matrices,
)
from src.analysis.discovery_engine import verify_conserved

x, y, z, w = sympy.symbols('x y z w')


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def _has(hits, target, syms):
    """¿Aparece `target` (salvo signo/escala) entre los invariantes hallados?"""
    for h in hits:
        if sympy.expand(h['invariant'] - target) == 0 or sympy.expand(h['invariant'] + target) == 0:
            return True
    return False


def test_markov3_parametric(stats):
    print(f"{Colors.HEADER}[1] Familia Markov-Hurwitz 3D: descubre x²+y²+z²-k·xyz por cada k{Colors.ENDC}")
    hits = scan_instances(family_markov3(5))
    all_ok = True
    for k in range(1, 6):
        sub = [h for h in hits if h['label'] == f"markov3 k={k}"]
        target = x**2 + y**2 + z**2 - k * x * y * z
        if _has(sub, target, [x, y, z]):
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} k={k}: x²+y²+z²-{k}·xyz (certificado)")
        else:
            all_ok = False
            stats.fail(f"k={k}: no halló x²+y²+z²-{k}·xyz; halló {[str(h['invariant']) for h in sub]}")
    if all_ok:
        stats.ok()


def test_norm_parametric(stats):
    print(f"{Colors.HEADER}[2] Familia forma-norma 2D: descubre x²-k·xy+y² (companion){Colors.ENDC}")
    hits = scan_instances(family_norm_form(6))
    all_ok = True
    for k in (1, 3, 4, 5, 6):   # k=2 degenera a (x-y)²; reduce_powers da el factor x-y
        sub = [h for h in hits if h['label'] == f"norm k={k}"]
        target = x**2 - k * x * y + y**2
        if _has(sub, target, [x, y]):
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} k={k}: x²-{k}xy+y² (certificado)")
        else:
            all_ok = False
            stats.fail(f"k={k}: no halló x²-{k}xy+y²; halló {[str(h['invariant']) for h in sub]}")
    if all_ok:
        stats.ok()


def test_all_verified(stats):
    print(f"{Colors.HEADER}[3] SOUNDNESS: todo invariante del catálogo está verificado{Colors.ENDC}")
    catalog = run_campaign()
    total = sum(len(h) for h in catalog.values())
    bad = [h for hits in catalog.values() for h in hits if not h['verified']]
    if not bad and total >= 15:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {total} invariantes en {len(catalog)} familias, todos verificados")
    else:
        stats.fail(f"total={total}, no verificados={len(bad)}")


def test_reverify_independent(stats):
    print(f"{Colors.HEADER}[4] Re-verificación independiente de un invariante del catálogo{Colors.ENDC}")
    # Toma Markov3 k=3 y re-comprueba con verify_conserved desde cero.
    T = [y, z, 3 * y * z - x]
    Q = x**2 + y**2 + z**2 - 3 * x * y * z
    if verify_conserved(Q, T, ['x', 'y', 'z'], 1):
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Q(T(s))=Q(s) idéntico para x²+y²+z²-3xyz bajo el mapa cíclico")
    else:
        stats.fail("la re-verificación independiente falló")


def test_hunt_boundary(stats):
    print(f"{Colors.HEADER}[5] Caza ampliada: frontera precisa (Markov 2-param, sólo j=1 integra){Colors.ENDC}")
    hits = scan_instances(family_generalized_markov(3, 3))
    labels = set(h['label'] for h in hits)
    only_j1 = all(l.endswith("j=1") for l in labels) and len(labels) == 3
    if only_j1:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} sólo j=1 admite invariante; j≠1 rompe integrabilidad -> 0 (frontera nítida)")
    else:
        stats.fail(f"frontera inesperada: {sorted(labels)}")


def test_census_curated(stats):
    print(f"{Colors.HEADER}[6] Censo lineal 3D: integrables dan invariante, caótico no (todo certificado){Colors.ENDC}")
    integrable = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]   # rotación 2D + eje: conserva forma cuadrática
    chaotic = [[1, 2, 3], [1, 3, 5], [1, 4, 8]]        # det=1, Anosov: sin invariante cuadrático
    h_int = scan_matrices([integrable], 2)
    h_cha = scan_matrices([chaotic], 2)
    cond = bool(h_int) and all(x['verified'] for x in h_int) and not h_cha
    if cond:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} integrable -> {[str(x['invariant']) for x in h_int]}; caótico -> 0 (no inventa)")
    else:
        stats.fail(f"censo curado inesperado: int={[str(x['invariant']) for x in h_int]} cha={[str(x['invariant']) for x in h_cha]}")


def main():
    print(f"{Colors.BOLD}=== CAMPAÑA DE DESCUBRIMIENTO: BARRIDO DE FAMILIAS ==={Colors.ENDC}")
    stats = Stats()
    test_markov3_parametric(stats)
    test_norm_parametric(stats)
    test_all_verified(stats)
    test_reverify_independent(stats)
    test_hunt_boundary(stats)
    test_census_curated(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — barrido autónomo: descubre y CERTIFICA "
              f"el invariante de cada instancia. Infraestructura lista para contrastar novedad.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
