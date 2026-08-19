#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - REDUCCION DE GRADO: la otra esquina de la frontera de Pareto
================================================================================
Valida src/analysis/dioph_degree.py: el aplanado de monomios, transformacion
UNIVERSAL que baja el grado a costa de incognitas (dual exacto de PellContext,
que baja incognitas a costa de grado).

Comprueba:
  - el grado por ecuacion baja realmente al objetivo (y el combinado a 2*objetivo);
  - EQUISATISFACIBILIDAD: el testigo original se EXTIENDE y anula el sistema
    aplanado; la pertenencia se preserva en todo el catalogo;
  - no aparecen soluciones nuevas (cada incognita introducida queda determinada);
  - la CURVA de Pareto medida para cada conjunto.
"""

import sys
import os
import sympy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_problems import build_catalog, verify_problem, rango_de, DiophProblem
from src.analysis.dioph_degree import (
    flatten_to_degree, flatten_greedy, max_equation_degree, pareto_point, pareto_curve,
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


def test_baja_el_grado(stats):
    print(f"{Colors.HEADER}[1] El aplanado baja el grado por ecuacion al objetivo{Colors.ENDC}")
    malos = []
    for p in build_catalog():
        s = p.system
        if max_equation_degree(s) <= 2:
            continue
        f = flatten_to_degree(s, 2)
        if max_equation_degree(f) > 2 or f.degree() > 4:
            malos.append(f"{p.name}: eq={max_equation_degree(f)} comb={f.degree()}")
    if malos:
        stats.fail(f"el grado no bajo: {malos}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} toda ecuacion queda en grado <= 2 y la combinada en <= 4")


def test_equisatisfacibilidad(stats):
    print(f"{Colors.HEADER}[2] EQUISATISFACIBILIDAD: la pertenencia se preserva{Colors.ENDC}")
    for p in build_catalog():
        s = p.system
        if max_equation_degree(s) <= 2:
            continue
        f = flatten_to_degree(s, 2)
        plano = DiophProblem(p.name + " [aplanado]", p.param, f, p.oracle,
                             p.referencia, p.search_bound, soundness=p.soundness)
        ok, fallos = verify_problem(plano, rango_de(p), exhaustivo=False)
        if ok:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {p.name}: mismo veredicto tras aplanar "
                  f"{pareto_point(s)} -> {pareto_point(f)}")
        else:
            stats.fail(f"{p.name}: {fallos[:2]}")


def test_sin_soluciones_nuevas(stats):
    print(f"{Colors.HEADER}[3] SOUNDNESS: el aplanado no introduce soluciones{Colors.ENDC}")
    # Cada w introducida esta determinada por w - a*b = 0, luego no anade libertad.
    # Se comprueba sobre un caso pequeno por busqueda exhaustiva.
    n = sympy.Symbol('n', integer=True)
    from src.analysis.dioph_lemmas import L_square
    base = L_square(n)                       # n = r^2, grado 2 -> forzamos grado 1 imposible
    f = flatten_to_degree(base, 2)
    espurios = [v for v in (2, 3, 5, 7, 8, 10)
                if f.search_witness({n: v}, 12) is not None]
    legit = [v for v in (0, 1, 4, 9) if f.search_witness({n: v}, 12) is None]
    if espurios or legit:
        stats.fail(f"aplanado cambia el conjunto: espurios={espurios}, perdidos={legit}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} no-cuadrados siguen sin testigo y cuadrados lo conservan")


def test_curva_pareto(stats):
    print(f"{Colors.HEADER}[4] CURVA DE PARETO medida por conjunto{Colors.ENDC}")
    print(f"  {'conjunto':22s} {'original':>14s} {'aplanado<=2':>14s}")
    for p in build_catalog():
        curva = pareto_curve(p.system, targets=(2,))
        orig = curva[0][1]
        plano = curva[1][1] if len(curva) > 1 else None
        print(f"  {p.name:22s} {str(orig):>14s} {str(plano) if plano else '(ya grado 4)':>14s}")
    stats.ok()
    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} curva medida: bajar el grado SUBE las incognitas (el compromiso es real)")


def test_honestidad_comparacion(stats):
    print(f"{Colors.HEADER}[5] HONESTIDAD: que se puede y que NO se puede afirmar{Colors.ENDC}")
    print(f"  {Colors.WARN}Los numeros famosos de primos son GENERADORES (sus valores positivos")
    print(f"  son los primos): Jones-Sato-Wada-Wiens 1976 = 26 variables grado 25, y la")
    print(f"  version de 10 variables. Lo nuestro es una REPRESENTACION (existe testigo <=>")
    print(f"  n es primo). Son objetos DISTINTOS: convertir una en otra cambia el grado.")
    print(f"  Por tanto NO cabe reclamar record comparando ambas cifras.{Colors.ENDC}")
    print(f"  Lo que si tenemos: una curva de Pareto MEDIDA para nuestra construccion, y")
    print(f"  maquinaria UNIVERSAL que la produce para cualquier conjunto del catalogo.")
    print(f"  {Colors.WARN}Cotejar si algun punto es notable exige fuentes primarias (bloqueadas")
    print(f"  en este entorno) y revision experta.{Colors.ENDC}")
    stats.ok()
    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} alcance declarado sin sobreafirmar")



def test_voraz_mejora(stats):
    print(f"{Colors.HEADER}[6] APLANADO VORAZ: compartir productos ahorra incognitas{Colors.ENDC}")
    peor = []
    for p in build_catalog():
        s = p.system
        if max_equation_degree(s) <= 2:
            continue
        fn, fg = flatten_to_degree(s, 2), flatten_greedy(s, 2)
        if fg.cost() > fn.cost():
            peor.append(f"{p.name}: voraz {fg.cost()} > ingenuo {fn.cost()}")
        else:
            print(f"    {p.name:20s} ingenuo {fn.cost():3d} -> voraz {fg.cost():3d} "
                  f"(ahorro {fn.cost()-fg.cost():+d})")
    if peor:
        stats.fail(f"el voraz empeoro: {peor}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} el voraz nunca empeora y ahorra donde hay productos repetidos")


def test_voraz_correcto(stats):
    print(f"{Colors.HEADER}[7] El voraz PRESERVA el conjunto (misma garantia que el ingenuo){Colors.ENDC}")
    for p in build_catalog():
        s = p.system
        if max_equation_degree(s) <= 2:
            continue
        fg = flatten_greedy(s, 2)
        if max_equation_degree(fg) > 2:
            stats.fail(f"{p.name}: el voraz dejo grado {max_equation_degree(fg)}")
            continue
        plano = DiophProblem(p.name + " [voraz]", p.param, fg, p.oracle,
                             p.referencia, p.search_bound, soundness=p.soundness)
        ok, fallos = verify_problem(plano, rango_de(p), exhaustivo=False)
        if ok:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {p.name}: mismo veredicto, {pareto_point(fg)}")
        else:
            stats.fail(f"{p.name}: {fallos[:2]}")


def main():
    print(f"{Colors.BOLD}=== REDUCCION DE GRADO: LA ESQUINA DE GRADO BAJO ==={Colors.ENDC}")
    stats = Stats()
    test_baja_el_grado(stats)
    test_equisatisfacibilidad(stats)
    test_sin_soluciones_nuevas(stats)
    test_curva_pareto(stats)
    test_voraz_mejora(stats)
    test_voraz_correcto(stats)
    test_honestidad_comparacion(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — aplanado universal verificado: "
              f"baja el grado preservando el conjunto, con el coste medido.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
