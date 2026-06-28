"""
================================================================================
   DIOPHANTUS - COLAPSO DE COLLATZ (Fase 3, caso NO afin via seleccion por paridad)
================================================================================
La transicion de collatz (variante de collatz.c: par -> n/2 ; impar -> (3n+1)/2)
no es afin, pero SI admite una forma POLINOMICA por paso introduciendo el bit de
paridad b_i = x_i mod 2:

        2*x_{i+1} = x_i + b_i*(2*x_i + 1)        (relacion de transicion)
        b_i*(1 - b_i) = 0                         (b_i es un bit)
        x_i - b_i ≡ 0 (mod 2)                     (b_i = paridad de x_i)

Comprobacion: si par (b=0) -> 2 x_{i+1}=x_i (x_{i+1}=x_i/2); si impar (b=1) ->
2 x_{i+1}=3 x_i+1 (x_{i+1}=(3 x_i+1)/2).

El termino b_i*(2 x_i+1) es cuadratico. Introduciendo el producto auxiliar
p_i = b_i*x_i, la transicion se vuelve LINEAL en los digitos:

        2*x_{i+1} = x_i + 2*p_i + b_i

y entonces su ESQUELETO LINEAL colapsa por empaquetado (un digito por paso, base
B sin acarreos), igual que el caso afin: TODOS los pasos en UNA sola ecuacion
sobre las historias empaquetadas N_x, N_p, N_b. La no-linealidad residual queda
encapsulada en las definiciones por digito p_i = b_i*x_i y b_i = paridad(x_i),
que es exactamente la frontera que la simulacion de maquinas de registros +
dominancia (Jones-Matiyasevich) resuelve. Este modulo deja validado todo lo
anterior: la transicion polinomica por paso y el colapso del esqueleto lineal.
"""

from src.analysis.linear_collapse import pack_digits, choose_base


def collatz_step(x):
    """Variante de collatz.c: par -> x/2 ; impar -> (3x+1)/2."""
    return x // 2 if x % 2 == 0 else (3 * x + 1) // 2


def collatz_trace(n, max_steps=100000):
    """Trayectoria [n, ..., 1] de la transicion de collatz."""
    xs = [n]
    steps = 0
    while xs[-1] != 1 and steps < max_steps:
        xs.append(collatz_step(xs[-1]))
        steps += 1
    return xs


def step_relation_holds(x, nxt, b):
    """True si (x, nxt, b) cumplen la relacion polinomica de transicion:
    b es bit, b = paridad(x) y 2*nxt = x + b*(2x+1)."""
    if b not in (0, 1):
        return False
    if (x - b) % 2 != 0:          # b = paridad de x
        return False
    return 2 * nxt == x + b * (2 * x + 1)


def verify_trace_relations(xs):
    """Comprueba la relacion polinomica por paso en TODA la traza."""
    for i in range(len(xs) - 1):
        b = xs[i] % 2
        if not step_relation_holds(xs[i], xs[i + 1], b):
            return False
    return True


def linear_skeleton_collapses(xs, base):
    """Verifica que el ESQUELETO LINEAL de la transicion colapsa en UNA ecuacion
    sobre las historias empaquetadas. Con b_i = x_i mod 2 y p_i = b_i*x_i, la
    relacion lineal  2 x_{i+1} = x_i + 2 p_i + b_i  (i=0..T-1) implica:

        2*(N_x - x_0) = B*[ (N_x - x_T*B^T) + 2*(N_p - p_T*B^T) + (N_b - b_T*B^T) ]

    Devuelve True si la traza real la satisface."""
    T = len(xs) - 1
    bs = [x % 2 for x in xs]
    ps = [bs[i] * xs[i] for i in range(len(xs))]
    Nx = pack_digits(xs, base)
    Np = pack_digits(ps, base)
    Nb = pack_digits(bs, base)
    BT = base ** T
    lhs = 2 * (Nx - xs[0])
    rhs = base * ((Nx - xs[-1] * BT) + 2 * (Np - ps[-1] * BT) + (Nb - bs[-1] * BT))
    return lhs == rhs


def safe_base(xs):
    """Base sin acarreos para x, b y p = b*x (todos < base)."""
    ps = [(x % 2) * x for x in xs]
    return choose_base(xs + ps + [x % 2 for x in xs])
