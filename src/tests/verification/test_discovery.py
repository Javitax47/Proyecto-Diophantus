#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST DEL MOTOR DE DESCUBRIMIENTO (Fase 4, §10)
================================================================================
Verifica el criterio de exito de la Fase 4: el motor descubre, sin plantilla,
una identidad cerrada que satisface la trayectoria de un programa no trivial.

  (1) PELL: la recurrencia (x,y)->(3x+4y,2x+3y) vive en la conica x^2-2y^2=1.
      El motor la DESCUBRE (grado 2) por nucleo de monomios, y se valida FUERA
      DE MUESTRA (puntos no usados para descubrirla).
  (2) FIBONACCI: (a,b)->(b,a+b). El motor descubre la identidad de Matiyasevich
      (b^2-ab-a^2)^2 = 1 (grado 4), validada fuera de muestra.
  (3) DESDE EL COMPILADOR: la trayectoria se obtiene del programa COMPILADO
      (extract_transition), no de una sucesion hardcodeada -> descubrimiento
      universal. (Se omite si no hay libclang.)

Uso:  python src/tests/verification/test_discovery.py
"""

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, _REPO_ROOT)
os.chdir(_REPO_ROOT)
sys.setrecursionlimit(200000)

try:
    import sympy
except ImportError:
    print("[SKIP] sympy no está instalado.")
    sys.exit(0)

from src.analysis.discovery_engine import find_invariants, invariant_holds_on


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; WARN = '\033[93m'
    HEADER = '\033[95m'; BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def pell_traj(x, y, n):
    out = [(x, y)]
    for _ in range(n):
        x, y = 3 * x + 4 * y, 2 * x + 3 * y
        out.append((x, y))
    return out


def fib_traj(a, b, n):
    out = [(a, b)]
    for _ in range(n):
        a, b = b, a + b
        out.append((a, b))
    return out


def discovers_nontrivial(invariants):
    """Filtra invariantes no triviales (no el polinomio cero)."""
    return [inv for inv in invariants if inv != 0]


def test_pell(stats):
    print(f"{Colors.HEADER}[1] Pell: descubrir x^2 - 2y^2 = 1 (grado 2, sin plantilla){Colors.ENDC}")
    traj = pell_traj(3, 2, 12)
    train, test = traj[:8], traj[8:]
    invs, _ = find_invariants(train, ['x', 'y'], max_deg=2)
    invs = discovers_nontrivial(invs)
    x, y = sympy.symbols('x y')
    target = x**2 - 2 * y**2 - 1
    # ¿alguna invariante descubierta es equivalente (salvo signo/escala) a x^2-2y^2-1?
    found = any(sympy.simplify(inv - target) == 0 or sympy.simplify(inv + target) == 0
                for inv in invs)
    out_of_sample = invs and all(invariant_holds_on(inv, test, ['x', 'y']) for inv in invs)
    if found and out_of_sample:
        stats.ok()
        print(f"     descubierto: {invs[0]} = 0  (válido fuera de muestra)")
    else:
        stats.fail(f"Pell: invs={invs} found={found} oos={out_of_sample}")


def test_fibonacci(stats):
    print(f"{Colors.HEADER}[2] Fibonacci: descubrir (b^2-ab-a^2)^2 = 1 (grado 4, identidad de Matiyasevich){Colors.ENDC}")
    traj = fib_traj(0, 1, 22)
    train, test = traj[:16], traj[16:]
    invs, _ = find_invariants(train, ['a', 'b'], max_deg=4)
    invs = discovers_nontrivial(invs)
    a, b = sympy.symbols('a b')
    target = (b**2 - a * b - a**2)**2 - 1
    found = any(sympy.simplify(inv - target) == 0 or sympy.simplify(inv + target) == 0
                for inv in invs)
    out_of_sample = invs and all(invariant_holds_on(inv, test, ['a', 'b']) for inv in invs)
    if found and out_of_sample:
        stats.ok()
        print(f"     descubierto un invariante de grado 4 equivalente a la identidad de Matiyasevich (válido fuera de muestra)")
    else:
        stats.fail(f"Fibonacci: found={found} oos={out_of_sample} invs={invs}")


def test_transition_invariant_collatz(stats):
    print(f"{Colors.HEADER}[3] Transición de Collatz descubierta como polinomio grado 2 (sin selector){Colors.ENDC}")
    from src.analysis.discovery_engine import find_transition_invariants
    from src.analysis.collatz_collapse import collatz_trace
    # trayectoria larga -> muchos pasos par e impar (variedad para fijar el invariante)
    train = collatz_trace(27)
    invs, exps, names = find_transition_invariants(train, ['x'], max_deg=2)
    invs = discovers_nontrivial(invs)
    x, xp = sympy.symbols('x xp')
    target = (2 * xp - x) * (2 * xp - 3 * x - 1)   # par: 2x'=x ; impar: 2x'=3x+1
    # ¿alguna invariante es multiplo escalar de target (misma variedad)?
    equiv = None
    for inv in invs:
        q = sympy.cancel(inv / target)
        if not q.free_symbols and q != 0:   # cociente constante => equivalentes
            equiv = inv
            break
    # validar fuera de muestra: en pares de OTRAS trayectorias
    test_pairs = []
    for n in [7, 97, 703]:
        tr = collatz_trace(n)
        test_pairs += [(tr[i], tr[i + 1]) for i in range(len(tr) - 1)]
    oos = equiv is not None and invariant_holds_on(equiv, test_pairs, names)
    if equiv is not None and oos:
        stats.ok()
        print(f"     descubierto: {sympy.factor(equiv)} = 0  (válido fuera de muestra en n=7,97,703)")
    else:
        stats.fail(f"collatz transición: equiv={equiv} oos={oos} invs={invs}")


def test_from_compiler(stats):
    print(f"{Colors.HEADER}[4] Descubrimiento desde el programa COMPILADO (universal){Colors.ENDC}")
    try:
        import src.compiler.parser
        import clang.cindex
        clang.cindex.Index.create()
    except Exception:
        print(f"     {Colors.WARN}[SKIP] libclang no disponible{Colors.ENDC}")
        return
    from src.analysis.beta_backend import extract_transition
    from src.analysis.structural_collapse import run_states
    # trayectoria de Pell desde el .c compilado
    step = extract_transition("src/examples/pell.c", "pell", ["x", "y", "step"])
    states, _ = run_states(step, {"x": 3, "y": 2, "step": 0})
    xy = [(s["x"], s["y"]) for s in states]
    train, test = xy[:8], xy[8:]
    invs, _ = find_invariants(train, ['x', 'y'], max_deg=2)
    invs = discovers_nontrivial(invs)
    x, y = sympy.symbols('x y')
    target = x**2 - 2 * y**2 - 1
    found = any(sympy.simplify(inv - target) == 0 or sympy.simplify(inv + target) == 0 for inv in invs)
    oos = invs and (not test or all(invariant_holds_on(inv, test, ['x', 'y']) for inv in invs))
    if found and oos:
        stats.ok()
        print(f"     desde pell.c compilado: descubierto {invs[0]} = 0")
    else:
        stats.fail(f"desde compilador: found={found} oos={oos} invs={invs}")


def main():
    print(f"{Colors.BOLD}=== TEST DEL MOTOR DE DESCUBRIMIENTO ALGEBRAICO (Fase 4) ==={Colors.ENDC}")
    stats = Stats()
    test_pell(stats)
    test_fibonacci(stats)
    test_transition_invariant_collatz(stats)
    test_from_compiler(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — el motor DESCUBRE identidades "
              f"cerradas no inyectadas, validadas fuera de muestra.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
