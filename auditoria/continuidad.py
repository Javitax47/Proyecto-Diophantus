"""El sistema del factorial sobre ℝ, con la entrada fija en dos puntos reales entre 10 y 11.

Resultado medido: `unsat` en ambos. La codificacion exige k >= 2 en la rama `else` de
k <= 1, que equivale a k > 1 solo para enteros.

Uso:  PYTHONPATH=. python3 auditoria/continuidad.py auditoria/factorial_15_niveles.txt
"""
import sys, math
from fractions import Fraction
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from banco import cargar
import z3
F = sys.argv[1]
objetivo = math.factorial(10) + 1
for k in (Fraction(10) + Fraction(1, 10**9), Fraction(10) + Fraction(1, 1000)):
    V, cons = cargar(F, 'R')
    s = z3.Solver(); s.set('timeout', 100000); s.add(cons)
    s.add(V['in_k'] == z3.RealVal(f"{k.numerator}/{k.denominator}"))
    r = s.check()
    if r == z3.sat:
        out = s.model().eval(V['out__n'])
        v = Fraction(out.numerator_as_long(), out.denominator_as_long())
        print(f"R  in_k = 10 + {float(k-10):.0e}  ->  out = {float(v):.4f}  "
              f"({'<' if v < objetivo else '>'} 10!+1 = {objetivo})", flush=True)
    else:
        print(f"R  in_k = {float(k)}  ->  {r}", flush=True)
# referencia exacta, la misma formula que el sistema simula en (10,11)
for k in (Fraction(10) + Fraction(1, 10**9), Fraction(10) + Fraction(1, 1000)):
    p = math.prod([k - i for i in range(10)])
    print(f"   formula k(k-1)...(k-9) en ese punto: {float(p):.4f}")
