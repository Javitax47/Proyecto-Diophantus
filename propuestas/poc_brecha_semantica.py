"""Prototipo: detector de bugs por la BRECHA entre la semantica matematica y la de la maquina.

Idea: cada expresion de un programa tiene dos lecturas.
  * la IDEAL, sobre enteros sin limite: lo que el programador cree que calcula;
  * la de la MAQUINA, sobre enteros de 32 bits con desbordamiento: lo que calcula de verdad.
Si existe una entrada valida en la que las dos difieren, hay un bug, y el solver devuelve
la entrada exacta. Si no existe, el `unsat` es un CERTIFICADO de que no hay desbordamiento.

Uso:  python3 propuestas/poc_brecha_semantica.py
"""
import time
import z3

W = 32


def brecha(nombre, ideal, maquina, precond, variables):
    """Busca una entrada que cumpla `precond` y en la que ideal != maquina."""
    s = z3.Solver()
    s.add(precond)
    s.add(ideal != maquina)
    t = time.time()
    r = s.check()
    dt = time.time() - t
    if r == z3.sat:
        m = s.model()
        vals = ', '.join(f"{v} = {m.eval(v, model_completion=True).as_signed_long()}" for v in variables)
        print(f"  BUG       {nombre:44s} {dt*1000:6.0f} ms   {vals}")
        print(f"            ideal = {m.eval(ideal).as_signed_long()}, "
              f"maquina = {m.eval(maquina).as_signed_long()}")
    elif r == z3.unsat:
        print(f"  CORRECTO  {nombre:44s} {dt*1000:6.0f} ms   (unsat: certificado de que no hay brecha)")
    else:
        print(f"  ?         {nombre:44s} {r}")


def ideal64(bv):
    """El valor 'ideal': extender con signo a 64 bits, donde estas operaciones no desbordan.
    Para entradas de 32 bits equivale a los enteros sin limite, y el solver lo resuelve
    mucho mas rapido que mezclando bits con enteros matematicos."""
    return z3.SignExt(64 - W, bv)


def maquina64(bv):
    """El valor que calcula la maquina en 32 bits, extendido a 64 para compararlo."""
    return z3.SignExt(64 - W, bv)


lo, hi = z3.BitVecs('lo hi', W)
pre = z3.And(lo >= 0, hi >= lo)                     # comparaciones con signo sobre BV

print("1) Busqueda binaria: el punto medio (bug clasico de java.util.Arrays.binarySearch)")
brecha("mid = (lo + hi) / 2",
       (ideal64(lo) + ideal64(hi)) / 2, maquina64((lo + hi) / 2), pre, [lo, hi])
brecha("mid = lo + (hi - lo) / 2   (el arreglo)",
       (ideal64(lo) + ideal64(hi)) / 2, maquina64(lo + (hi - lo) / 2), pre, [lo, hi])

print("\n2) El ejemplo de Collatz del propio proyecto: paso impar (3n+1)/2")
n = z3.BitVec('n', W)
brecha("next = (3*n + 1) / 2,  n impar y positivo",
       (3 * ideal64(n) + 1) / 2, maquina64((3 * n + 1) / 2),
       z3.And(n > 0, z3.Extract(0, 0, n) == 1), [n])

print("\n3) El factorial del propio proyecto: acc * k")
acc, k = z3.BitVecs('acc k', W)
brecha("acc * k,  0 <= acc <= 12!,  1 <= k <= 13",
       ideal64(acc) * ideal64(k), maquina64(acc * k),
       z3.And(acc >= 0, acc <= 479001600, k >= 1, k <= 13), [acc, k])
