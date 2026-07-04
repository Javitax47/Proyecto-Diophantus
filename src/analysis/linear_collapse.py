"""
================================================================================
   DIOPHANTUS - COLAPSO LINEAL
================================================================================
Eliminacion del cuantificador universal acotado para recurrencias LINEALES,
empaquetando toda la traza en un solo entero (dominancia de digitos).

Para una transicion afin  x_{i+1} = c*x_i + d  (i = 0..T-1), si se elige una
base B mayor que todos los x_i (sin acarreos) y se empaqueta la traza en

        N = sum_{i=0}^{T} x_i * B^i        (un digito por paso de tiempo)

entonces TODOS los pasos de la recurrencia se cumplen a la vez si y solo si N
satisface UNA sola ecuacion algebraica, independiente de T:

        N - x_0 = c*B*(N - x_T*B^T) + d*B*(B^T - 1)/(B - 1)

(derivacion: sumar x_{i+1}=c*x_i+d ponderado por B^i sobre i=0..T-1 y reagrupar
en terminos de N, x_0 y x_T). El cuantificador "para todo i" desaparece: la
dimension temporal se muda al TAMANO del testigo N, que es donde el MRDP dice
que debe vivir. El numero de ecuaciones es CONSTANTE, independiente de T.

Esto realiza, para el caso lineal, la vision del Nivel 3/5: colapsar la
recursion en una caracterizacion cerrada (cf. matrix_kernel.py y del
informe). El caso no lineal (p. ej. collatz) requiere la simulacion de maquinas
de registros + Kummer-Lucas, fuera de este modulo.
"""


def pack_digits(xs, base):
    """Empaqueta la traza `xs` en N = sum xs[i] * base^i. Requiere 0 <= xs[i] < base."""
    if any(not (0 <= x < base) for x in xs):
        raise ValueError("cada digito debe cumplir 0 <= x < base (sin acarreos)")
    N = 0
    for i, x in enumerate(xs):
        N += x * (base ** i)
    return N


def choose_base(xs):
    """Base segura: mayor que todos los digitos (y >= 2)."""
    return max(2, max(xs) + 1) if xs else 2


def closed_relation_lhs_rhs(N, x0, xT, c, d, base, T):
    """Devuelve (lhs, rhs) de la ecuacion de colapso lineal para inspeccion."""
    BT = base ** T
    geom = (BT - 1) // (base - 1)  # sum_{i=0}^{T-1} base^i, exacto si base>1
    lhs = N - x0
    rhs = c * base * (N - xT * BT) + d * base * geom
    return lhs, rhs


def collapse_holds(N, x0, xT, c, d, base, T):
    """True si N (la traza empaquetada) satisface la ecuacion cerrada de la
    recurrencia x_{i+1} = c*x_i + d. Equivale a que TODOS los pasos se cumplan."""
    lhs, rhs = closed_relation_lhs_rhs(N, x0, xT, c, d, base, T)
    return lhs == rhs


def linear_trace(c, d, x0, T):
    """Genera la traza [x_0, ..., x_T] de x_{i+1} = c*x_i + d."""
    xs = [x0]
    for _ in range(T):
        xs.append(c * xs[-1] + d)
    return xs


def pack_and_collapse(c, d, x0, T):
    """Genera la traza lineal, elige base, empaqueta y devuelve
    (xs, base, N) listos para verificar con collapse_holds."""
    xs = linear_trace(c, d, x0, T)
    base = choose_base(xs)
    return xs, base, pack_digits(xs, base)


# --- GENERALIZACION ACOPLADA: x_{i+1} = A·x_i + d (multi-registro afin) ---
# Cubre cualquier maquina de registros con actualizacion afin (varios registros
# que se mezclan linealmente), p. ej. Fibonacci [a,b] -> [b, a+b]. Cada
# componente j satisface su propia ecuacion cerrada sobre las historias
# empaquetadas N_l; son m ecuaciones, constante en T (cf. y matrix_kernel).

def coupled_trace(A, d, x0, T):
    """Traza de x_{i+1} = A·x_i + d. A es m×m (lista de listas), d y x0 vectores.
    Devuelve [x_0, ..., x_T] como lista de vectores."""
    m = len(d)
    xs = [list(x0)]
    for _ in range(T):
        prev = xs[-1]
        nxt = [sum(A[j][l] * prev[l] for l in range(m)) + d[j] for j in range(m)]
        xs.append(nxt)
    return xs


def coupled_collapse_holds(packed, x0, xT, A, d, base, T):
    """True si las historias empaquetadas `packed` (packed[j] = sum_i x^j_i B^i)
    satisfacen, componente a componente, la ecuacion cerrada del sistema afin
    acoplado:
        N_j - x0_j = B·sum_l A[j][l]·(N_l - xT_l·B^T) + d_j·B·(B^T-1)/(B-1)
    Verifica TODOS los T pasos de TODOS los registros con m ecuaciones."""
    m = len(d)
    BT = base ** T
    geom = (BT - 1) // (base - 1)
    for j in range(m):
        lhs = packed[j] - x0[j]
        rhs = base * sum(A[j][l] * (packed[l] - xT[l] * BT) for l in range(m)) + d[j] * base * geom
        if lhs != rhs:
            return False
    return True


def pack_and_collapse_coupled(A, d, x0, T):
    """Genera la traza acoplada, elige una base segura comun y empaqueta cada
    componente. Devuelve (xs, base, packed) con packed[j] la historia de j."""
    xs = coupled_trace(A, d, x0, T)
    m = len(d)
    flat = [xs[i][j] for i in range(len(xs)) for j in range(m)]
    base = choose_base(flat)
    packed = [pack_digits([xs[i][j] for i in range(len(xs))], base) for j in range(m)]
    return xs, base, packed
