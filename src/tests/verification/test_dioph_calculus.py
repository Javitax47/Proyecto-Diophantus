#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - CALCULO DE CONSTRUCCIONES DIOFANTICAS (ataque al record)
================================================================================
Valida src/analysis/dioph_calculus.py y dioph_lemmas.py: la infraestructura para
buscar representaciones diofanticas con el MINIMO numero de incognitas.

Comprueba, para cada lema:
  - COMPLETITUD: el testigo constructivo existe y ANULA el sistema (evaluacion
    exacta, no busqueda);
  - SOUNDNESS: para elementos que NO estan en el conjunto, la busqueda
    exhaustiva en rango NO encuentra testigo (no hay soluciones espurias);
  - COSTE: el numero de incognitas declarado coincide con el real, y la
    composicion contabiliza correctamente las incognitas COMPARTIDAS.

Y valida el cimiento del record: la ecuacion de Pell y el predicado de
crecimiento exponencial de Julia Robinson.
"""

import sys
import os
import sympy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_calculus import Dioph, conj, disj, four_squares
from src.analysis.dioph_lemmas import (
    L_divides, L_congruent, L_nonneg, L_positive, L_square, L_composite,
    L_pell, L_is_pell_y, pell_seq, fresh, RECORD_PRIMOS, FRONTERA,
)


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; WARN = '\033[93m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


n = sympy.Symbol('n', integer=True)
a = sympy.Symbol('a', integer=True)
y = sympy.Symbol('y', integer=True)


def test_lagrange(stats):
    print(f"{Colors.HEADER}[1] Cuatro cuadrados (Lagrange): el precio de una desigualdad{Colors.ENDC}")
    bad = [v for v in range(0, 200) if (lambda d: d is None or sum(x*x for x in d) != v)(four_squares(v))]
    if bad:
        stats.fail(f"descomposicion incorrecta para {bad[:5]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 200/200 enteros descompuestos y verificados (7={four_squares(7)})")


def test_basic_lemmas(stats):
    print(f"{Colors.HEADER}[2] Lemas basicos: COMPLETITUD (el testigo anula el sistema){Colors.ENDC}")
    cases = [
        (L_divides(sympy.Integer(7), n), {n: 91}, 1, "7 | 91"),
        (L_congruent(n, sympy.Integer(1), sympy.Integer(5)), {n: 31}, 1, "31 = 1 mod 5"),
        (L_nonneg(n - 10), {n: 47}, 4, "n-10 >= 0 en n=47"),
        (L_positive(n), {n: 3}, 4, "n > 0 en n=3"),
        (L_square(n), {n: 49}, 1, "49 es cuadrado"),
        (L_composite(n), {n: 91}, 2, "91 compuesto"),
    ]
    for sysm, vals, cost, label in cases:
        ok, asg = sysm.check_witness(vals)
        if not ok:
            stats.fail(f"{label}: el testigo no anula el sistema")
        elif sysm.cost() != cost:
            stats.fail(f"{label}: coste {sysm.cost()} != {cost} declarado")
        else:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {label}  (coste {cost} incognita(s), grado {sysm.degree()})")


def test_soundness(stats):
    print(f"{Colors.HEADER}[3] SOUNDNESS: sin testigo cuando el elemento NO pertenece{Colors.ENDC}")
    # primos: no deben admitir testigo de 'compuesto' (busqueda exhaustiva)
    spurious = []
    for p in [2, 3, 5, 7, 11, 13, 17, 19, 23]:
        if L_composite(n).search_witness({n: p}, bound=p + 2) is not None:
            spurious.append(p)
    if spurious:
        stats.fail(f"testigo espurio de 'compuesto' para primos {spurious}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 9 primos: ningun testigo de 'compuesto' (sin soluciones espurias)")

    # no-cuadrados no deben admitir testigo de 'cuadrado'
    bad = [v for v in [2, 3, 5, 7, 8, 10, 15] if L_square(n).search_witness({n: v}, bound=v) is not None]
    if bad:
        stats.fail(f"testigo espurio de 'cuadrado' para {bad}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 7 no-cuadrados rechazados")

    # negativos no admiten testigo de no-negatividad (Lagrange)
    if four_squares(-1) is None and L_nonneg(n).witness({n: -5}) is None:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} n<0 no admite descomposicion en 4 cuadrados (correcto)")
    else:
        stats.fail("negativo aceptado como no-negativo")


def test_pell(stats):
    print(f"{Colors.HEADER}[4] Ecuacion de Pell: el cimiento del record{Colors.ENDC}")
    bad = []
    for av in range(2, 8):
        for k in range(0, 12):
            xk, yk = pell_seq(av, k)
            if xk ** 2 - (av ** 2 - 1) * yk ** 2 != 1:
                bad.append((av, k))
    if bad:
        stats.fail(f"la identidad de Pell falla en {bad[:5]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 72 pares (a,k): x_k²-(a²-1)y_k² = 1 exacto  (a=2: {pell_seq(2,4)})")

    # crecimiento exponencial: la propiedad que hace diofantica la exponenciacion
    ys = [pell_seq(3, k)[1] for k in range(1, 9)]
    ratios_ok = all(ys[i+1] >= 4 * ys[i] for i in range(len(ys) - 1))
    if ratios_ok:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} y_k(3) crece exponencialmente: {ys[:6]}… (predicado de J. Robinson)")
    else:
        stats.fail(f"y_k no crece exponencialmente: {ys}")

    # y_k = k mod (a-1): identidad clasica usada en las reducciones
    bad = [(av, k) for av in range(2, 7) for k in range(0, 15)
           if (pell_seq(av, k)[1] - k) % (av - 1) != 0]
    if bad:
        stats.fail(f"y_k != k mod (a-1) en {bad[:5]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} y_k(a) ≡ k (mod a-1) verificado en 75 casos")


def test_is_pell_y(stats):
    print(f"{Colors.HEADER}[5] Predicado 'y es y_k(a)': COMPLETITUD y SOUNDNESS{Colors.ENDC}")
    sysm = L_is_pell_y(a, y)
    ok_all = True
    for av in [2, 3, 5]:
        for k in range(0, 7):
            _, yk = pell_seq(av, k)
            ok, _ = sysm.check_witness({a: av, y: yk})
            if not ok:
                ok_all = False
    if ok_all:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 21 valores y_k(a) admiten testigo x (coste {sysm.cost()} incognita)")
    else:
        stats.fail("un y_k legitimo no admitio testigo")

    # SOUNDNESS: valores que NO son y_k no deben admitir testigo
    reales = {pell_seq(3, k)[1] for k in range(0, 12)}
    falsos = [v for v in range(1, 40) if v not in reales]
    espurios = [v for v in falsos if sysm.witness({a: 3, y: v}) is not None]
    if espurios:
        stats.fail(f"testigo espurio para y no-Pell: {espurios[:5]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {len(falsos)} valores no-Pell rechazados (no inventa)")


def test_composicion_y_coste(stats):
    print(f"{Colors.HEADER}[6] Composicion: contabilidad EXACTA del coste (donde se gana el record){Colors.ENDC}")
    d1 = L_divides(sympy.Integer(3), n)
    d2 = L_square(n)
    c = conj(d1, d2, name="n divisible por 3 y cuadrado")
    if c.cost() != d1.cost() + d2.cost():
        stats.fail(f"coste de conjuncion {c.cost()} != {d1.cost()+d2.cost()}")
    else:
        ok, _ = c.check_witness({n: 36})
        if ok:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} conj: coste {c.cost()} = {d1.cost()}+{d2.cost()}, testigo verificado en n=36")
        else:
            stats.fail("conjuncion: testigo no anula el sistema")

    # COMPARTIR incognitas no las duplica: es la palanca del record
    shared = conj(d1, d1)
    if shared.cost() == d1.cost():
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} incognitas COMPARTIDAS se cuentan una vez ({shared.cost()}, no {2*d1.cost()})")
    else:
        stats.fail(f"compartir incognitas duplico el coste: {shared.cost()}")

    # disyuncion: coste 0 extra, via producto
    dj = disj(L_square(n), L_composite(n))
    ok1, _ = dj.check_witness({n: 49})
    if ok1 and dj.cost() == 3:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} disj: producto de ecuaciones, coste {dj.cost()} sin extras, grado {dj.degree()}")
    else:
        stats.fail(f"disyuncion incorrecta (ok={ok1}, coste={dj.cost()})")


def test_marcador(stats):
    print(f"{Colors.HEADER}[7] MARCADOR: distancia real al record{Colors.ENDC}")
    print(f"  {Colors.BOLD}Record primos:{Colors.ENDC} {RECORD_PRIMOS['variables']} variables "
          f"({RECORD_PRIMOS['incognitas']} incognitas + parametro) — {RECORD_PRIMOS['autor']}")
    print(f"  {Colors.BOLD}Estado:{Colors.ENDC} {RECORD_PRIMOS['estado']}")
    print(f"  {Colors.WARN}Frontera declarada (aun NO implementado):{Colors.ENDC}")
    for f in FRONTERA:
        print(f"    - {f}")
    if RECORD_PRIMOS['incognitas'] == 9 and len(FRONTERA) == 3:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} marcador y frontera declarados sin sobreafirmar")
    else:
        stats.fail("marcador inconsistente")


def main():
    print(f"{Colors.BOLD}=== CALCULO DE CONSTRUCCIONES DIOFANTICAS (ataque al record) ==={Colors.ENDC}")
    stats = Stats()
    test_lagrange(stats)
    test_basic_lemmas(stats)
    test_soundness(stats)
    test_pell(stats)
    test_is_pell_y(stats)
    test_composicion_y_coste(stats)
    test_marcador(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — lemas certificados con coste exacto y "
              f"testigo constructivo; Pell verificado. Infraestructura lista para la busqueda.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
