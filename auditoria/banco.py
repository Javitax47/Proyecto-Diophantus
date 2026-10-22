"""Carga un sistema compilado por Diophantus en Z3, sobre ℤ (QF_NIA) o sobre ℝ (QF_NRA).

Uso:  PYTHONPATH=. python3 auditoria/banco.py auditoria/factorial_15_niveles.txt

Ojo: Z3 no siempre respeta el limite interno de tiempo con aritmetica no lineal; para
casos que pueden colgarse, usar `caso.py` con un `timeout` externo.
"""
import re, sys, time, math
import z3

def cargar(path, dominio):
    eqs = []
    for linea in open(path):
        linea = linea.strip()
        if not linea or '=' not in linea:
            continue
        linea = linea.replace('[t+1]', '__n')
        izq, der = linea.rsplit('=', 1)
        eqs.append((izq.strip(), der.strip()))
    nombres = set()
    for izq, der in eqs:
        nombres |= set(re.findall(r'\b[A-Za-z_][A-Za-z_0-9]*\b', izq + ' ' + der))
    mk = z3.Int if dominio == 'Z' else z3.Real
    V = {n: mk(n) for n in nombres}
    cons = [eval(izq, {}, V) == eval(der, {}, V) for izq, der in eqs]
    return V, cons

def caso(path, dominio, fijar, seg):
    V, cons = cargar(path, dominio)
    s = z3.SolverFor('QF_NIA' if dominio == 'Z' else 'QF_NRA')
    s.set('timeout', seg * 1000)
    s.add(cons)
    for v, val in fijar.items():
        s.add(V[v] == val)
    t = time.time(); r = s.check(); dt = time.time() - t
    extra = ''
    if r == z3.sat:
        m = s.model()
        extra = f"in_k = {m.eval(V['in_k'])}"
    return f"{str(r):8s} {dt:6.1f}s  {extra}"

if __name__ == '__main__':
    path = sys.argv[1]
    F10 = math.factorial(10)
    for etiqueta, dom, fijar in [
        ("Z  directo   k=10      ", 'Z', {'in_k': 10}),
        ("Z  inverso   out=10!   ", 'Z', {'out__n': F10}),
        ("Z  sin sol.  out=10!+1 ", 'Z', {'out__n': F10 + 1}),
        ("R  sin sol.  out=10!+1 ", 'R', {'out__n': F10 + 1}),
    ]:
        print(etiqueta, '->', caso(path, dom, fijar, 60), flush=True)
    t = time.time()
    k = next((k for k in range(1, 100) if math.factorial(k) == F10), None)
    print(f"referencia (ejecutar el programa): k={k} en {(time.time()-t)*1e6:.0f} us", flush=True)
