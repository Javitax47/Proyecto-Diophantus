"""
================================================================================
   DIOPHANTUS - EMISION DEL SISTEMA CERRADO A Z3
================================================================================
Construye el sistema de restricciones cerrado de collatz (R1-R5, todas O(1))
como un sistema de BIT-VECTORS de Z3 y deja que el SOLVER —no `==` de Python—
verifique la propiedad central: solucion <=> traza valida.

Se usan bit-vectors porque la dominancia (R2, R5) es AND bit a bit, nativa en BV.
Las historias se empaquetan en base 2^k (un digito de k bits por paso). Para una
longitud fija (T+1 digitos) el sistema fija la trayectoria: con el inicio dado,
NINGUN otro empaquetado satisface todas las restricciones (UNSAT) -> sin
soluciones espurias, demostrado por Z3.
"""

from z3 import BitVec, BitVecVal, Solver, sat, unsat, And, Or


def _digit(V, i, k, B):
    return (V >> (k * i)) & (B - 1)


def build_z3_system(length, k, start):
    """Construye (solver, vars) con R1-R5 para `length` digitos de k bits y el
    inicio dado. `vars` = (Nx, Nq, Nb, Np). El solver NO fija aun la traza."""
    T = length - 1
    B = 1 << k
    # Margen de DOS digitos: B*RHS puede llegar a ~4*B^(length+1); con un solo
    # digito de margen el bit-vector envolvia (wraparound) y aparecian soluciones
    # espurias para trazas largas (lo detecto Z3). Con (length+2)*k no hay overflow.
    W = (length + 2) * k
    Nx, Nq, Nb, Np = (BitVec('Nx', W), BitVec('Nq', W),
                      BitVec('Nb', W), BitVec('Np', W))
    BV = lambda v: BitVecVal(v, W)

    ONES = sum(1 << (k * i) for i in range(length))          # bit bajo de cada digito
    ALL = (B - 1) * ONES                                     # todos los bits de cada digito
    BT = BV(B ** T)

    s = Solver()
    # Dominio: cada variable cabe en `length` digitos (sin bits por encima).
    for V in (Nx, Nq, Nb, Np):
        s.add((V >> (k * length)) == 0)
    # GUARDA contra acarreos: acotar cada digito a un sub-rango libre de acarreos.
    # x_i < B/4 (2 bits de guarda) -> 2*x_{i+1} y 3*x_i+1 < B ; q_i < B/2 (1 bit)
    # -> 2*q_i+b_i < B. Sin esto, Z3 elige digitos grandes que SE DESBORDAN y
    # satisfacen las ecuaciones via acarreo (soluciones espurias).
    GUARD_x = BV(((1 << (k - 2)) - 1) * ONES)   # low (k-2) bits de cada digito
    GUARD_q = BV(((1 << (k - 1)) - 1) * ONES)   # low (k-1) bits de cada digito
    s.add((Nx & GUARD_x) == Nx)   # cada digito de x < 2^(k-2) = B/4
    s.add((Nq & GUARD_q) == Nq)   # cada digito de q < 2^(k-1) = B/2

    # R1: descomposicion de paridad
    s.add(Nx == 2 * Nq + Nb)
    # R2: bit-ness de b por dominancia  (Nb ⪯ ONES)
    s.add((Nb & BV(ONES)) == Nb)
    # R3: transicion (esqueleto lineal empaquetado)
    x0 = _digit(Nx, 0, k, B); xT = _digit(Nx, T, k, B)
    bT = _digit(Nb, T, k, B); pT = _digit(Np, T, k, B)
    lhs = 2 * (Nx - x0)
    rhs = BV(B) * ((Nx - xT * BT) + 2 * (Np - pT * BT) + (Nb - bT * BT))
    s.add(lhs == rhs)
    # R4: frontera
    s.add(x0 == BV(start))
    s.add(xT == BV(1))
    # R5: producto p_i=b_i*x_i por dominancia (difusion del bit + 3 dominancias)
    Bcast = BV(B - 1) * Nb
    s.add((Np & Nx) == Np)                       # p ⪯ x
    s.add((Np & Bcast) == Np)                    # p ⪯ N_Bcast
    u = Nx - Np                                  # = x - p (exacto porque p ⪯ x)
    v = BV(ALL) - Bcast                          # = ALL - N_Bcast
    s.add((u & v) == u)                          # (x-p) ⪯ (ALL - N_Bcast)
    return s, (Nx, Nq, Nb, Np), W


def pack(xs, k):
    N = 0
    for i, x in enumerate(xs):
        N += x << (k * i)
    return N


def verify_with_z3(xs, start, timeout_ms=20000):
    """Devuelve (sat_true, unsat_other): (a) el sistema es SAT con el testigo
    verdadero de la traza; (b) es UNSAT para cualquier Nx distinto con el mismo
    inicio -> la trayectoria es la UNICA solucion (sin soluciones espurias)."""
    from src.analysis.collatz_closed import choose_k
    k = choose_k(xs)   # base libre de acarreos -> ecuacion empaquetada tight
    length = len(xs)
    s, (Nx, Nq, Nb, Np), W = build_z3_system(length, k, start)
    s.set("timeout", timeout_ms)

    true_Nx = pack(xs, k)
    true_Nb = pack([x & 1 for x in xs], k)
    true_Nq = pack([x >> 1 for x in xs], k)
    true_Np = pack([(x & 1) * x for x in xs], k)

    # (a) el testigo verdadero satisface el sistema
    s.push()
    s.add(Nx == true_Nx, Nq == true_Nq, Nb == true_Nb, Np == true_Np)
    sat_true = (s.check() == sat)
    s.pop()

    # (b) ningun OTRO Nx (con el mismo inicio, ya fijado) satisface el sistema
    s.push()
    s.add(Nx != true_Nx)
    unsat_other = (s.check() == unsat)
    s.pop()

    return sat_true, unsat_other
