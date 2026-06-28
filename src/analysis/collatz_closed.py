"""
================================================================================
   DIOPHANTUS - SISTEMA CERRADO DE COLLATZ (Fase 3, cierre del caso no afin)
================================================================================
Ensambla un SISTEMA DE RESTRICCIONES de tamano CONSTANTE (independiente de la
longitud T de la trayectoria) sobre las historias empaquetadas en base B=2^k
(un digito por paso, sin acarreos). Es la culminacion del colapso beta para la
transicion no afin de collatz, juntando todas las piezas:

Variables empaquetadas (cada una un entero gigante, un digito por paso):
  N_x  historia de x        N_q  historia de q_i=floor(x_i/2)
  N_b  historia del bit b_i  N_p  historia de p_i = b_i*x_i

Restricciones (T+1 digitos, ONES = sum_i B^i = repunit en base B):
  (R1) descomposicion de paridad:     N_x = 2*N_q + N_b           [O(1), aritmetica]
  (R2) bit-ness de b por DOMINANCIA:  N_b ⪯ ONES                  [O(1), Kummer-Lucas]
  (R3) transicion (esqueleto lineal): 2(N_x - x0) =
          B*[ (N_x - xT*B^T) + 2(N_p - pT*B^T) + (N_b - bT*B^T) ] [O(1), empaquetado]
  (R4) frontera:                      x0 = inicio , xT = 1        [O(1)]
  (R5) producto p_i = b_i*x_i                                      [residuo por digito]

R1-R4 colapsan a un numero CONSTANTE de relaciones empaquetadas (incluida la
dominancia para la bit-ness). R5 (el producto digito-a-digito, que codifica la
seleccion par/impar) es el unico residuo que no es aun O(1): su O(1)-ificacion
es exactamente el paso de la maquina de registros (descomponer el producto en
sumas afines), para el que ya tenemos el colapso afin. Aqui R5 se impone y se
verifica explicitamente, dejando el sistema CERRADO y SOLIDO (sin soluciones
espurias), con la frontera de investigacion claramente acotada a R5.
"""

from src.analysis.digit_dominance import dominates, base_pow_digits
from src.analysis.collatz_collapse import collatz_trace


def choose_k(xs):
    """Bits por digito: k tal que la base 2^k sea LIBRE DE ACARREOS para la
    transicion. No basta con x_i < B: el esqueleto lineal coloca cantidades como
    2*x_{i+1} y x_i+2*p_i+b_i (<= 3*x_i+1) en un digito; si alguna alcanza B hay
    acarreo y la ecuacion empaquetada deja de separarse digito-a-digito (admite
    soluciones espurias, como detecto Z3). Con B > 3*max(x_i)+1 no hay acarreos
    y la ecuacion empaquetada equivale a la relacion por-digito (solucion unica)."""
    if not xs:
        return 1
    # B > 4*max(x): deja 2 bits de guarda por digito. Asi, acotando x_i < B/4 y
    # q_i < B/2 (ver build_z3_system), NINGUNA de las cantidades de las ecuaciones
    # (2*x_{i+1}, x_i+2p_i+b_i <= 3x_i+1, 2q_i+b_i) alcanza B: empaquetado SIN
    # acarreos, y cada ecuacion empaquetada equivale a la relacion por-digito.
    return max(2, (4 * max(xs) + 1).bit_length())


def repunit(base, length):
    """ONES = sum_{i=0}^{length-1} base^i (un 1 en el bit bajo de cada digito)."""
    return (base ** length - 1) // (base - 1)


def build_packed(xs, k):
    """Construye (B, N_x, N_q, N_b, N_p, qs, bs, ps) de la traza xs en base 2^k."""
    B = 1 << k
    bs = [x & 1 for x in xs]
    qs = [x >> 1 for x in xs]
    ps = [bs[i] * xs[i] for i in range(len(xs))]
    Nx = base_pow_digits(xs, k)
    Nq = base_pow_digits(qs, k)
    Nb = base_pow_digits(bs, k)
    Np = base_pow_digits(ps, k)
    return B, Nx, Nq, Nb, Np, qs, bs, ps


def closed_constraints(xs, k, start):
    """Evalua cada restriccion del sistema cerrado sobre la traza empaquetada.
    Devuelve un dict {nombre: bool}. Todas True <=> traza valida de collatz."""
    B, Nx, Nq, Nb, Np, qs, bs, ps = build_packed(xs, k)
    T = len(xs) - 1
    BT = B ** T
    ONES = repunit(B, len(xs))

    r1 = (Nx == 2 * Nq + Nb)                                   # descomposicion paridad
    r2 = dominates(Nb, ONES)                                   # bit-ness via dominancia
    lhs = 2 * (Nx - xs[0])
    rhs = B * ((Nx - xs[-1] * BT) + 2 * (Np - ps[-1] * BT) + (Nb - bs[-1] * BT))
    r3 = (lhs == rhs)                                          # esqueleto lineal
    r4 = (xs[0] == start and xs[-1] == 1)                      # frontera
    r5 = all(ps[i] == bs[i] * xs[i] for i in range(len(xs)))   # producto (residuo)
    return {'R1_paridad': r1, 'R2_bitness_dominancia': r2,
            'R3_transicion': r3, 'R4_frontera': r4, 'R5_producto': r5}


def r5_o1_holds(Nx, Nb, Np, k, length):
    """O(1)-ificacion de R5 (p_i = b_i*x_i) por DOMINANCIA, sin recorrer i.

    Idea: difundir el bit b_i por todo su digito -> mascara B_i = b_i*(2^k-1).
    Entonces p_i = B_i AND x_i (= x_i si b_i=1, 0 si b_i=0). La mascara
    empaquetada es N_Bcast = (2^k-1)*N_b (sin acarreos, pues (2^k-1)*b_i < 2^k).
    El enmascarado se caracteriza por TRES dominancias (numero constante):
        p ⪯ x,   p ⪯ N_Bcast,   (x - p) ⪯ (ALL - N_Bcast)
    donde ALL = (2^k-1)*ONES (todos los bits de todos los digitos). Esto fuerza
    p_i = x_i en los digitos con b_i=1 y p_i = 0 en los demas, i.e. p_i=b_i*x_i.
    Requiere b_i ∈ {0,1} (lo garantiza R2)."""
    B = 1 << k
    if not dominates(Np, Nx):
        return False
    Bcast = (B - 1) * Nb
    if not dominates(Np, Bcast):
        return False
    ALL = (B - 1) * repunit(B, length)
    return dominates(Nx - Np, ALL - Bcast)


def closed_constraints_o1(xs, k, start):
    """Como closed_constraints pero con R5 reemplazado por su forma O(1) (3
    dominancias). Todas las restricciones son ahora de numero CONSTANTE."""
    B, Nx, Nq, Nb, Np, qs, bs, ps = build_packed(xs, k)
    T = len(xs) - 1
    BT = B ** T
    ONES = repunit(B, len(xs))
    r1 = (Nx == 2 * Nq + Nb)
    r2 = dominates(Nb, ONES)
    lhs = 2 * (Nx - xs[0])
    rhs = B * ((Nx - xs[-1] * BT) + 2 * (Np - ps[-1] * BT) + (Nb - bs[-1] * BT))
    r3 = (lhs == rhs)
    r4 = (xs[0] == start and xs[-1] == 1)
    r5 = r5_o1_holds(Nx, Nb, Np, k, len(xs))   # R5 ahora O(1)
    return {'R1_paridad': r1, 'R2_bitness_dominancia': r2,
            'R3_transicion': r3, 'R4_frontera': r4, 'R5_producto_O1': r5}


def closed_system_holds(xs, start, use_o1=True):
    """True si la traza satisface TODO el sistema cerrado. Con use_o1, R5 se
    impone en su forma O(1) (sistema enteramente de tamano constante)."""
    k = choose_k(xs)
    cons = closed_constraints_o1(xs, k, start) if use_o1 else closed_constraints(xs, k, start)
    return all(cons.values())


def collatz_closed_witness(n):
    """Genera la trayectoria de collatz para n y devuelve (xs, k) listos para el
    sistema cerrado. Es el papel del Witness Miner para este sistema."""
    xs = collatz_trace(n)
    return xs, choose_k(xs)
