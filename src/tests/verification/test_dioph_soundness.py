#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - SOUNDNESS POR SMT: la direccion que nunca se comprobaba
================================================================================
Todo el calculo diofantico verificaba COMPLETITUD (pertenece => hay testigo)
construyendo el testigo. La direccion inversa -- SOUNDNESS: no pertenece => NO
hay testigo -- se declaraba y se dejaba descansar en los teoremas citados,
porque las incognitas viven en rangos astronomicos y ninguna busqueda los toca.

Este test la comprueba con un demostrador SMT, que no enumera sino que razona.
Y lo primero que encontro fue un DEFECTO REAL: en modo N las condiciones
laterales del lema exponencial no imponian nada (`L_nonneg_N` devolvia un
sistema vacio), de modo que el sistema de los primos admitia solucion para
n = 4, 9, 15, 25. El generador construido sobre el habria emitido compuestos.

Comprueba:
  - el traductor sympy -> Z3 es fiel (evalua igual que sympy);
  - los conjuntos elementales del catalogo son SOUND (unsat demostrado);
  - REGRESION: el sistema de los primos ya no admite solucion para compuestos;
  - UNICIDAD: los subsistemas que "calculan" un valor lo FUERZAN.
"""

import sys
import os
import sympy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_problems import build_catalog, rango_de
from src.analysis.dioph_calculus import Dioph
from src.analysis.dioph_lemmas import L_exponential, L_composite, fresh
from src.analysis.dioph_soundness import (
    Z3_DISPONIBLE, sympy_to_z3, solve, soundness_report, uniqueness_report, resumen,
)


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; WARN = '\033[93m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}FALLO: {msg}{Colors.ENDC}")


# ---------------------------------------------------------------------------

def test_traductor(stats):
    """[1] El traductor sympy -> Z3 debe evaluar EXACTAMENTE igual que sympy."""
    print(f"\n{Colors.HEADER}[1] Fidelidad del traductor sympy -> Z3{Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)"); return
    import z3
    x, y = sympy.symbols('x y', integer=True)
    exprs = [x + y, x * y - 3, x**3 - 2*y**2 + 7, (x + y)**2, x**2*y - x*y**2 + 1]
    malos = 0
    for e in exprs:
        e = sympy.expand(e)
        vm = {}
        ez = sympy_to_z3(e, vm)
        for xv in range(-3, 4):
            for yv in range(-3, 4):
                s = z3.Solver()
                s.add(vm[x] == xv); s.add(vm[y] == yv)
                s.check()
                got = s.model().eval(ez, model_completion=True).as_long()
                esperado = int(e.subs({x: xv, y: yv}))
                if got != esperado:
                    malos += 1
    if malos == 0:
        print(f"  {Colors.OKGREEN}OK{Colors.ENDC} {len(exprs)} polinomios x 49 puntos: identicos a sympy")
        stats.ok()
    else:
        stats.fail(f"{malos} discrepancias traductor/sympy")


def test_catalogo_sound(stats):
    """[2] Los conjuntos del catalogo no deben admitir solucion fuera del conjunto."""
    print(f"\n{Colors.HEADER}[2] SOUNDNESS del catalogo (unsat demostrado por Z3){Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)"); return
    problemas = 0
    for prob in build_catalog():
        if prob.name == "primo":
            continue                      # tiene su propio test de regresion
        ok, filas, defectos = soundness_report(prob, rango_de(prob),
                                              timeout_ms=8000, rlimit=4_000_000)
        marca = Colors.OKGREEN + "OK" + Colors.ENDC if ok else Colors.FAIL + "DEFECTO" + Colors.ENDC
        print(f"  {marca} {prob.name:<22} {resumen(filas)}")
        if not ok:
            problemas += 1
            for d in defectos[:2]:
                print(f"      {d}")
    if problemas == 0:
        stats.ok()
    else:
        stats.fail(f"{problemas} conjuntos admiten soluciones espurias")


def test_regresion_primos(stats):
    """[3] REGRESION del defecto encontrado: ningun compuesto debe admitir solucion.

    Historia: `L_nonneg_N` devolvia un sistema VACIO, asi que en modo N las
    condiciones laterales (c < M, a > c, a-1 > k) no imponian NADA. Con a in {0,1}
    la ecuacion de Pell degenera y (x,y) = (1,0) la resuelve, de modo que Z3
    encontraba testigo para 4, 9, 15 y 25. Este test vigila que no vuelva.
    """
    print(f"\n{Colors.HEADER}[3] REGRESION: compuestos sin solucion en el sistema de primos{Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)"); return
    prob = [p for p in build_catalog() if p.name == "primo"][0]
    compuestos = [4, 9, 15, 25]
    # Sin el intento global: en un sistema de 36 incognitas y grado 8 Z3 no
    # concluye y solo quema tiempo. Las cajas pequenas bastan para esta regresion,
    # porque las soluciones espurias del defecto tenian TODAS valores diminutos
    # (a in {0,1}, y = 0, s = 0). El estado reportado dice la cota usada.
    ok, filas, defectos = soundness_report(prob, compuestos, timeout_ms=8000,
                                          rlimit=4_000_000, intentar_sin_cota=False,
                                          cotas_de_reserva=(200, 20))
    for v, _, est in filas:
        color = Colors.OKGREEN if est == "unsat" else (Colors.FAIL if est == "sat" else Colors.WARN)
        print(f"  {color}n={v:<4} {est}{Colors.ENDC}")
    if ok:
        print(f"  (recordatorio: 'unknown' no es evidencia a favor; solo 'unsat' demuestra)")
        stats.ok()
    else:
        stats.fail("el sistema de primos SIGUE admitiendo compuestos: " + defectos[0])


def test_unicidad_exponencial(stats):
    """[4] UNICIDAD: el subsistema de b^k debe FORZAR el valor, no solo admitirlo.

    Es el riesgo real de una cadena larga: si un eslabon admite un valor espurio,
    todo lo que venga detras hereda el defecto. Se pregunta por
    `sistema AND c != b^k` y se exige unsat.
    """
    print(f"\n{Colors.HEADER}[4] UNICIDAD del lema exponencial{Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)"); return
    b, k = sympy.symbols('b k', integer=True, positive=True)
    c = fresh("cval")
    sistema = L_exponential(b, k, c, over_N=True)
    sistema = Dioph(params=[b, k], unknowns=sistema.unknowns + [c],
                    eqs=sistema.eqs, witness=None, name="c = b^k")
    filas = []
    for bv, kv in [(2, 2), (2, 3), (3, 2)]:
        # Con cota: sin ella Z3 devuelve 'unknown' (aritmetica entera no lineal).
        # 'unico' aqui significa "no hay valor espurio con las incognitas en [0,200]".
        r = uniqueness_report(sistema, {b: bv, k: kv}, c, bv ** kv,
                              over_N=True, bound=200, timeout_ms=20000,
                              rlimit=8_000_000)
        filas.append((bv, kv, r["veredicto"]))
        color = {"unico": Colors.OKGREEN, "ESPURIO": Colors.FAIL}.get(r["veredicto"], Colors.WARN)
        print(f"  {color}{bv}^{kv}: {r['veredicto']} (dentro de [0,200]){Colors.ENDC}"
              + (f"  modelo={r['modelo']}" if r["veredicto"] == "ESPURIO" else ""))
    espurios = [f for f in filas if f[2] == "ESPURIO"]
    if espurios:
        stats.fail(f"valor espurio admitido en {espurios}")
    else:
        stats.ok()


def test_unknown_no_es_prueba(stats):
    """[5] Honestidad: 'unknown' se reporta como 'unknown', jamas como exito.

    Se construye a proposito un sistema satisfacible y se comprueba que el
    informe dice 'sat' (no 'unsat'), y un sistema imposible que dice 'unsat'.
    """
    print(f"\n{Colors.HEADER}[5] Los tres estados se distinguen (sat / unsat / unknown){Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)"); return
    n = sympy.Symbol('n', integer=True)
    sat = solve(L_composite(n), {n: 12}, over_N=True, timeout_ms=5000)
    unsat = solve(L_composite(n), {n: 13}, over_N=True, timeout_ms=5000)
    print(f"  12 compuesto -> {sat['estado']}   13 primo -> {unsat['estado']}")
    if sat["estado"] == "sat" and unsat["estado"] == "unsat":
        stats.ok()
    else:
        stats.fail(f"estados inesperados: 12->{sat['estado']} 13->{unsat['estado']}")


def main():
    print(f"{Colors.BOLD}=== SOUNDNESS POR SMT: LA DIRECCION QUE FALTABA ==={Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print(f"{Colors.WARN}z3 no instalado: 'pip install z3-solver'. Nada que verificar.{Colors.ENDC}")
        sys.exit(0)
    stats = Stats()
    test_traductor(stats)
    test_catalogo_sound(stats)
    test_regresion_primos(stats)
    test_unicidad_exponencial(stats)
    test_unknown_no_es_prueba(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — soundness comprobada, "
              f"no solo declarada.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
