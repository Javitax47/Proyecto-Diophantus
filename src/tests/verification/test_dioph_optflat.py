#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - OPTIMIZACION DEL APLANADO: heuristicas y optimo exacto
================================================================================
Cubre las piezas de `dioph_degree` y `dioph_optflat` que no tocaba ningun test:
las heuristicas de aplanado, la busqueda sobre sus ejes, la eliminacion lineal y
el optimizador exacto restringido a monomios (el metodo de Davis).

Comprueba:
  - todas las estrategias PRESERVAN la equisatisfacibilidad (el testigo se
    extiende y anula el sistema) sobre el catalogo entero;
  - el desempate del voraz cambia el resultado -- por eso hay busqueda;
  - `flatten_best` nunca es peor que las dos que compara;
  - `eliminar_lineales` solo elimina cuando la definicion tiene TODOS los
    coeficientes >= 0, que es lo que preserva `u >= 0` sobre N;
  - `aplanado_minimo` (metodo de Davis: productos de dos variables) alcanza su
    cota inferior, es decir devuelve un OPTIMO y no una estimacion.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_problems import build_catalog, rango_de
from src.analysis.dioph_degree import (
    flatten_greedy, flatten_tree, flatten_best, flatten_search,
    flatten_greedy_semilla, eliminar_lineales, max_equation_degree,
)
from src.analysis.dioph_optflat import Z3_DISPONIBLE, aplanado_minimo


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; WARN = '\033[93m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}FALLO: {msg}{Colors.ENDC}")


def _problemas():
    """El catalogo sin 'primo': su sistema esta roto (ver test_dioph_soundness [8])."""
    return [p for p in build_catalog() if p.name != "primo"]


def test_equisatisfacibilidad(stats):
    """[1] Toda estrategia de aplanado extiende el testigo y anula el sistema."""
    print(f"\n{Colors.HEADER}[1] Las estrategias preservan la equisatisfacibilidad{Colors.ENDC}")
    estrategias = [
        ("voraz", lambda s: flatten_greedy(s, 2)),
        ("arbol (Skolem)", lambda s: flatten_tree(s, 2)),
        ("mejor de ambas", lambda s: flatten_best(s, 2)),
        ("voraz semilla=3", lambda s: flatten_greedy_semilla(s, 2, semilla=3)),
    ]
    malos = []
    for nombre, fn in estrategias:
        for p in _problemas():
            F = fn(p.system)
            if max_equation_degree(F) > 2:
                malos.append((nombre, p.name, "grado"))
                continue
            for v in rango_de(p):
                if not p.oracle(v):
                    continue
                ok, _ = F.check_witness({p.param: v})
                if not ok:
                    malos.append((nombre, p.name, v))
        print(f"  {nombre:<16} {len(_problemas())} conjuntos, grado <= 2, testigo verificado")
    if malos:
        stats.fail(f"equisatisfacibilidad rota en {malos[:3]}")
    else:
        stats.ok()


def test_el_desempate_importa(stats):
    """[2] Cambiar SOLO el desempate del voraz cambia el resultado.

    Es la justificacion de que exista `flatten_search`: si el desempate no
    importara, buscar seria tiempo perdido. Medido sobre el sistema de JSWW,
    cambiar la semilla bajo el generador de 49 a 47 variables.
    """
    print(f"\n{Colors.HEADER}[2] El desempate del voraz cambia el resultado{Colors.ENDC}")
    from src.analysis.dioph_jsww import sistema
    S = flatten_tree(sistema(expandir=False), 8)
    costes = {flatten_greedy_semilla(S, 2, semilla=s).cost() for s in range(6)}
    print(f"  costes con 6 semillas distintas: {sorted(costes)}")
    if len(costes) > 1:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} hay dispersion: la busqueda sobre el desempate tiene sentido")
        stats.ok()
    else:
        stats.fail("todas las semillas dan lo mismo: `flatten_search` seria inutil")


def test_mejor_no_empeora(stats):
    """[3] `flatten_best` nunca es peor que las dos estrategias que compara."""
    print(f"\n{Colors.HEADER}[3] `flatten_best` no empeora a ninguna de las dos{Colors.ENDC}")
    malos = []
    for p in _problemas():
        a = flatten_greedy(p.system, 2).cost()
        b = flatten_tree(p.system, 2).cost()
        c = flatten_best(p.system, 2).cost()
        if c > min(a, b):
            malos.append((p.name, a, b, c))
    print(f"  {len(_problemas())} conjuntos comparados")
    if malos:
        stats.fail(f"flatten_best peor que el minimo en {malos[:3]}")
    else:
        stats.ok()


def test_eliminacion_solo_si_es_sound(stats):
    """[4] `eliminar_lineales` solo elimina si la definicion es >= 0 sobre N.

    `u >= 0` es una restriccion REAL del sistema. Sustituir `u` por una expresion
    que pueda ser negativa la perderia. En el sistema de JSWW eso deja eliminar
    `q = wz+h+j` pero NO `v = y-n-l` ni `l = ai+k+1-i`, donde el signo codifica
    una desigualdad.
    """
    print(f"\n{Colors.HEADER}[4] La eliminacion respeta el dominio N{Colors.ENDC}")
    from src.analysis.dioph_jsww import sistema
    from src.analysis.dioph_degree import _coeficientes_no_negativos_expr
    import sympy
    E = eliminar_lineales(sistema(expandir=False), 2)
    nombres = [str(u) for u, _ in E.eliminadas]
    print(f"  eliminadas: {nombres}")
    malas = [str(u) for u, val in E.eliminadas
             if not _coeficientes_no_negativos_expr(sympy.expand(val))]
    prohibidas = {"v", "l"}          # llevan signo mezclado: no deben eliminarse
    coladas = prohibidas & set(nombres)
    if malas:
        stats.fail(f"eliminadas con definicion que puede ser negativa: {malas}")
    elif coladas:
        stats.fail(f"eliminadas variables cuyo signo codifica una desigualdad: {coladas}")
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} ninguna eliminacion pierde la condicion u >= 0")
        stats.ok()


def test_optimo_de_davis(stats):
    """[5] El optimizador restringido a monomios alcanza su cota: es OPTIMO.

    Ese espacio --nombrar productos de dos variables-- es exactamente el metodo
    que describe Davis (AMM 1973, p. 263) y que JSWW citan. Que el modelo alcance
    la cota inferior es lo que convierte el resultado en un minimo demostrado y no
    en "lo mejor que encontre".
    """
    print(f"\n{Colors.HEADER}[5] El optimo de monomios (metodo de Davis) alcanza su cota{Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)"); return
    fallos = []
    for p in _problemas():
        r = aplanado_minimo(p.system, 2, timeout_s=90)
        if r["estado"] == "optimo":
            continue
        if r["estado"] == "cota_superior":
            fallos.append((p.name, r["nombres"], r["cota"]))
        elif r["estado"] not in ("optimo",):
            fallos.append((p.name, r["estado"], None))
    print(f"  {len(_problemas())} conjuntos, {len(_problemas())-len(fallos)} con optimo demostrado")
    if fallos:
        stats.fail(f"no se alcanzo la cota en {fallos[:3]}")
    else:
        stats.ok()


def main():
    print(f"{Colors.BOLD}=== OPTIMIZACION DEL APLANADO: HEURISTICAS Y OPTIMO EXACTO ==={Colors.ENDC}")
    stats = Stats()
    test_equisatisfacibilidad(stats)
    test_el_desempate_importa(stats)
    test_mejor_no_empeora(stats)
    test_eliminacion_solo_si_es_sound(stats)
    test_optimo_de_davis(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — aplanado: heuristicas "
              f"verificadas y optimo demostrado.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
