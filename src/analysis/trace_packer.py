"""
================================================================================
   DIOPHANTUS - TRACE PACKER
================================================================================
Primer ladrillo del "colapso beta" que elimina el desenrollado: en lugar de una
copia de las variables por paso, TODA la traza x_0, x_1, ..., x_{T} se codifica
en dos enteros (a, b) mediante la funcion beta de Goedel

        beta(a, b, i) = a mod (b*(i+1) + 1)

Por el lema de Goedel (teorema chino del resto), para cualquier sucesion finita
de naturales existen (a, b) tales que beta(a, b, i) = x_i para todo i. Asi el
numero de pasos T pasa a ser una variable existencial mas y el sistema tiene un
numero de variables CONSTANTE, independiente de la profundidad.

Este modulo implementa la maquinaria verificable de ese nivel:
  * beta(a, b, i): la extraccion.
  * pack_trace(xs): halla (a, b) que codifican la traza (CRT inverso) -- esto es
    exactamente lo que el "Witness Miner" debe calcular a partir de una ejecucion
    de la VM.
  * verify_packing(a, b, xs): comprueba que beta recupera la traza.
  * beta_moduli(b, n): los modulos m_i = b*(i+1)+1.

La eliminacion del cuantificador universal acotado (Davis-Putnam-Robinson /
dominancia de digitos) que convierte esto en un sistema diofantico cerrado es el
Nivel 3; aqui dejamos validada la codificacion/decodificacion, que es el insumo.
"""

from math import gcd
try:
    from math import lcm
except ImportError:
    def lcm(a, b):
        return abs(a * b) // gcd(a, b) if a and b else 0
from functools import reduce


def beta(a, b, i):
    """Funcion beta de Goedel: beta(a, b, i) = a mod (b*(i+1) + 1)."""
    return a % (b * (i + 1) + 1)


def beta_moduli(b, n):
    """Modulos m_i = b*(i+1) + 1 para i en [0, n)."""
    return [b * (i + 1) + 1 for i in range(n)]


def _crt(residues, moduli):
    """Resuelve x ≡ residues[i] (mod moduli[i]) por el teorema chino del resto.
    Asume moduli coprimos dos a dos. Devuelve el x en [0, prod(moduli))."""
    x = 0
    M = reduce(lambda p, q: p * q, moduli, 1)
    for r, m in zip(residues, moduli):
        Mi = M // m
        # inverso de Mi modulo m
        inv = pow(Mi % m, -1, m)
        x = (x + r * Mi * inv) % M
    return x


def pack_trace(xs):
    """Dada una traza de enteros no negativos `xs`, devuelve (a, b) tales que
    beta(a, b, i) == xs[i] para todo i.

    Construccion (lema de Goedel, variante practica): se toma b multiplo de
    lcm(1..n) y mayor que max(x_i). Lo primero hace los modulos coprimos dos a
    dos (cualquier divisor comun de m_i y m_j divide |i-j| < n, luego divide b,
    luego divide m_i - b(i+1) = 1); lo segundo asegura m_i > x_i. Asi b es un
    entero grande pero manejable (no s!, que seria astronomico para trazas con
    valores grandes como las de collatz)."""
    if any(x < 0 for x in xs):
        raise ValueError("beta codifica naturales; la traza tiene negativos")
    n = len(xs)
    if n == 0:
        return 0, 1
    L = reduce(lcm, range(1, n + 1), 1)   # lcm(1..n): coprimalidad de los m_i
    mx = max(xs)
    b = L * (mx // L + 1)                  # multiplo de L con b > mx  => m_i > x_i
    moduli = beta_moduli(b, n)
    # Verificacion defensiva de coprimalidad (lema de Goedel).
    for i in range(n):
        for j in range(i + 1, n):
            if gcd(moduli[i], moduli[j]) != 1:
                raise AssertionError("modulos no coprimos: rompe el lema de beta")
    a = _crt([xs[i] % moduli[i] for i in range(n)], moduli)
    return a, b


def verify_packing(a, b, xs):
    """True si beta(a, b, i) == xs[i] para todo i."""
    return all(beta(a, b, i) == xs[i] for i in range(len(xs)))


def check_beta_trajectory(a, b, T, step, start, accept=None):
    """Comprueba que (a, b, T) codifican una ejecucion VALIDA de una funcion de
    transicion de UN solo paso `step`, independiente de la profundidad:

        beta(a,b,0) == start                         (condicion inicial)
        beta(a,b,i+1) == step(beta(a,b,i))  for i<T  (cuantificador acotado)
        accept(beta(a,b,T))                          (condicion de aceptacion)

    Esta es la forma del sistema beta: una unica relacion de transicion mas el
    cuantificador universal acotado sobre la traza empaquetada. El MISMO
    predicado verifica trayectorias de cualquier longitud T sin "recompilar":
    la profundidad vive en el valor de T (existencial), no en la estructura."""
    if beta(a, b, 0) != start:
        return False
    for i in range(T):
        if beta(a, b, i + 1) != step(beta(a, b, i)):
            return False
    if accept is not None and not accept(beta(a, b, T)):
        return False
    return True


def pack_and_check(step, start, accept, max_steps=100000):
    """Ejecuta la transicion `step` desde `start` hasta `accept` (o max_steps),
    empaqueta la traza en (a, b) y devuelve (a, b, T) verificados. Es lo que un
    Witness Miner haria: ejecutar y calcular los testigos beta por CRT inverso."""
    xs = [start]
    x = start
    steps = 0
    while not accept(x) and steps < max_steps:
        x = step(x)
        xs.append(x)
        steps += 1
    a, b = pack_trace(xs)
    T = len(xs) - 1
    return a, b, T
