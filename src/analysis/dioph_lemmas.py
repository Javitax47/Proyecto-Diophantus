"""
================================================================================
   DIOPHANTUS - BIBLIOTECA DE LEMAS DIOFANTICOS CERTIFICADOS
================================================================================
Cada lema declara: (a) su sistema, (b) su COSTE en incognitas, (c) un TESTIGO
constructivo, (d) su referencia. Componerlos con dioph_calculus preserva la
correccion y permite contabilidad exacta del coste -> ataque al record.

Cadena clasica hacia los PRIMOS (la que produjo el record de 10 variables):

    ecuacion de PELL  ->  crecimiento exponencial  ->  EXPONENCIACION diofantica
    ->  FACTORIAL diofantico  ->  WILSON (n primo <=> n | (n-1)! + 1)

Este modulo implementa la base de esa cadena y las piezas verificables. La
exponenciacion completa (Matiyasevich/Robinson) es el siguiente eslabon y esta
declarada como frontera explicita, no simulada.
"""

import sympy
from src.analysis.dioph_calculus import Dioph, conj, four_squares

_counter = [0]


def fresh(prefix="u"):
    """Simbolo existencial nuevo (evita colisiones al componer)."""
    _counter[0] += 1
    return sympy.Symbol(f"{prefix}{_counter[0]}", integer=True)


# ---------------------------------------------------------------------------
#   LEMAS BASICOS
# ---------------------------------------------------------------------------

def L_divides(a, b):
    """a | b.   exists k : b - a*k = 0.   COSTE: 1 incognita.

    Testigo: k = b/a (entero exacto cuando a divide a b).
    """
    k = fresh("k")
    def w(vals):
        av, bv = int(a.subs(vals)), int(b.subs(vals))
        if av == 0 or bv % av != 0:
            return None
        return {k: bv // av}
    return Dioph(params=sorted((a.free_symbols | b.free_symbols), key=str),
                 unknowns=[k], eqs=[sympy.expand(b - a * k)],
                 witness=w, name=f"{a} | {b}")


def L_congruent(a, b, m):
    """a == b (mod m).   exists k : a - b - m*k = 0.   COSTE: 1.

    Referencia: elemental.
    """
    k = fresh("c")
    def w(vals):
        av, bv, mv = int(a.subs(vals)), int(b.subs(vals)), int(m.subs(vals))
        if mv == 0 or (av - bv) % mv != 0:
            return None
        return {k: (av - bv) // mv}
    syms = a.free_symbols | b.free_symbols | m.free_symbols
    return Dioph(params=sorted(syms, key=str), unknowns=[k],
                 eqs=[sympy.expand(a - b - m * k)], witness=w,
                 name=f"{a} = {b} mod {m}")


def L_nonneg(e):
    """e >= 0.   exists s1..s4 : e - (s1^2+s2^2+s3^2+s4^2) = 0.   COSTE: 4.

    Referencia: teorema de los cuatro cuadrados de Lagrange. Es el precio
    estandar de una desigualdad sobre Z; sobre N el coste seria 0, y por eso
    los records distinguen el rango de las incognitas (Sun: ν<=11 sobre Z
    frente a ν<=9 sobre N).
    """
    s = [fresh("s") for _ in range(4)]
    def w(vals):
        ev = int(e.subs(vals))
        d = four_squares(ev)
        return None if d is None else dict(zip(s, d))
    return Dioph(params=sorted(e.free_symbols, key=str), unknowns=s,
                 eqs=[sympy.expand(e - sum(x ** 2 for x in s))],
                 witness=w, name=f"{e} >= 0")


def L_positive(e):
    """e > 0  <=>  e - 1 >= 0.   COSTE: 4."""
    d = L_nonneg(e - 1)
    d.name = f"{e} > 0"
    return d


def L_square(n):
    """n es un cuadrado perfecto.   exists r : n - r^2 = 0.   COSTE: 1."""
    r = fresh("r")
    def w(vals):
        nv = int(n.subs(vals))
        root, exact = sympy.integer_nthroot(nv, 2) if nv >= 0 else (0, False)
        return {r: int(root)} if exact else None
    return Dioph(params=sorted(n.free_symbols, key=str), unknowns=[r],
                 eqs=[sympy.expand(n - r ** 2)], witness=w, name=f"{n} es cuadrado")


def L_composite(n):
    """n es compuesto.   exists u,v : n - (u+2)(v+2) = 0.   COSTE: 2.

    Nota conceptual: lo FACIL es el complemento. Que la PRIMALIDAD (complemento
    de esto) sea diofantica es el contenido profundo de MRDP, y por eso su
    representacion minima es un problema abierto.
    """
    u, v = fresh("u"), fresh("v")
    def w(vals):
        nv = int(n.subs(vals))
        for a in range(2, int(nv ** 0.5) + 1):
            if nv % a == 0:
                return {u: a - 2, v: nv // a - 2}
        return None
    return Dioph(params=sorted(n.free_symbols, key=str), unknowns=[u, v],
                 eqs=[sympy.expand(n - (u + 2) * (v + 2))], witness=w,
                 name=f"{n} compuesto")


# ---------------------------------------------------------------------------
#   ECUACION DE PELL: el cimiento del record
# ---------------------------------------------------------------------------

def pell_seq(a, k):
    """(x_k, y_k): k-esima solucion de x^2 - (a^2-1) y^2 = 1, para a >= 2.

    x_0=1,y_0=0 ; x_1=a,y_1=1 ; recurrencia  z_{k+1} = 2a z_k - z_{k-1}.
    y_k crece exponencialmente en k: es la fuente del crecimiento exponencial
    que hace diofantica a la exponenciacion (Matiyasevich 1970).
    """
    x0, y0, x1, y1 = 1, 0, a, 1
    if k == 0:
        return (x0, y0)
    for _ in range(k - 1):
        x0, x1 = x1, 2 * a * x1 - x0
        y0, y1 = y1, 2 * a * y1 - y0
    return (x1, y1)


def L_pell(a, x, y):
    """x^2 - (a^2-1)*y^2 = 1.   COSTE: 0 incognitas nuevas (relaciona las dadas).

    Referencia: Matiyasevich (1970). Sus soluciones son EXACTAMENTE los pares
    (x_k(a), y_k(a)); esa parametrizacion implicita es lo que permite capturar
    crecimiento exponencial con muy pocas variables.
    """
    syms = a.free_symbols | x.free_symbols | y.free_symbols
    return Dioph(params=sorted(syms, key=str), unknowns=[],
                 eqs=[sympy.expand(x ** 2 - (a ** 2 - 1) * y ** 2 - 1)],
                 witness=lambda vals: {}, name="Pell")


def L_is_pell_y(a, y):
    """y = y_k(a) para algun k.   exists x : x^2-(a^2-1)y^2 = 1.   COSTE: 1.

    Predicado de crecimiento exponencial (Julia Robinson): la pieza que Robinson
    demostro suficiente para que la exponenciacion sea diofantica, y que
    Matiyasevich suministro en 1970 cerrando el decimo problema de Hilbert.
    """
    x = fresh("x")
    def w(vals):
        av, yv = int(a.subs(vals)), int(y.subs(vals))
        if av < 2 or yv < 0:
            return None
        k = 0
        while True:
            xk, yk = pell_seq(av, k)
            if yk == yv:
                return {x: xk}
            if yk > yv:
                return None
            k += 1
    syms = a.free_symbols | y.free_symbols
    return Dioph(params=sorted(syms, key=str), unknowns=[x],
                 eqs=[sympy.expand(x ** 2 - (a ** 2 - 1) * y ** 2 - 1)],
                 witness=w, name=f"{y} es y_k({a})")


# ---------------------------------------------------------------------------
#   MARCADOR
# ---------------------------------------------------------------------------

RECORD_PRIMOS = {
    "variables": 10,
    "incognitas": 9,
    "autor": "Matiyasevich 1975 (prueba completa: Jones)",
    "estado": "menor conocido; minimizar es problema abierto",
    "formalizado": "ITP 2022",
}

LOGRADO = [
    "L_exponential (c = b^k via Pell): 5 incognitas sobre N, 17 sobre Z.",
    "L_binomial (C(r,n) por extraccion de digitos, J. Robinson): 21 incognitas.",
    "L_factorial (n! = floor(r^n/C(r,n))): 36 incognitas.",
    "L_prime (WILSON, cadena COMPLETA hasta los primos): 38 incognitas, grado 8. "
    "Testigo construido y sistema anulado para n=2,3; compuestos sin testigo.",
]

FRONTERA = [
    "BUSQUEDA con COMPARTICION de incognitas entre eslabones: sin ella la "
    "composicion es aditiva (38) y jamas bajara de 9. Es EL problema abierto "
    "de este modulo y la unica via hacia el record.",
    "Reduccion del grado: el record se enuncia en (variables, grado); aqui solo "
    "se optimiza el primero.",
    "Verificacion mas alla de n=3: el testigo explota (n=6 ~ 2e11 digitos), "
    "asi que la correccion descansa en los teoremas citados, no en el computo.",
]


# ---------------------------------------------------------------------------
#   EXPONENCIACION DIOFANTICA (el eslabon que desbloquea la cadena al record)
# ---------------------------------------------------------------------------

def L_nonneg_N(e):
    """e >= 0 cuando las incognitas recorren N.   COSTE: 0.

    Sobre N la no-negatividad es GRATIS; sobre Z cuesta 4 (Lagrange). Esa
    diferencia es exactamente la que separa los records segun el rango de las
    incognitas (Sun: ν<=11 sobre Z frente a ν<=9 sobre N), y por eso el calculo
    la contabiliza por separado en lugar de esconderla.
    """
    return Dioph(params=sorted(e.free_symbols, key=str), unknowns=[], eqs=[],
                 witness=lambda vals: {}, name=f"{e} >= 0 (sobre N: gratis)")


def L_exponential(b, k, c, over_N=False):
    """c = b^k.   Construccion clasica via ecuacion de Pell.

    Referencia: Davis, *Hilbert's Tenth Problem is Unsolvable* (1973); la
    congruencia central es de Matiyasevich/Robinson:

        x_k(a) - (a-b)*y_k(a)  ==  b^k   (mod  2ab - b^2 - 1)

    verificada aqui en 1368 casos sin fallos (ver test_dioph_calculus.py).

    Sistema (incognitas: a, x, y, t, s + holguras):
        (1) x^2 - (a^2-1) y^2 = 1          -> (x,y) = (x_m(a), y_m(a))
        (2) y - k - (a-1) t = 0            -> m == k  (mod a-1)
        (3) (x - (a-b) y) - c - M s = 0    -> congruencia central, M = 2ab-b^2-1
                                              (escrita asi para que s >= 0)
        (4) M - c - 1 >= 0                 -> c queda UNIVOCO en [0, M)
        (5) a - c - 1 >= 0                 -> a > c: agranda M
        (6) a - k - 2 >= 0                 -> a-1 > k: FIJA el indice m = k
                                              (sin esto m, m+(a-1), ... colisionan)

    COSTE: 5 incognitas sobre N; 17 sobre Z (cada desigualdad cuesta 4 por
    Lagrange). Esa brecha 5 vs 17 es exactamente la razon de que los records se
    enuncien indicando el rango de las incognitas.

    Honestidad: las condiciones laterales (4)-(6) son las que exige el teorema
    clasico. Este modulo las IMPONE y las VERIFICA computacionalmente en rango;
    la correccion en general descansa en la referencia, no en estos tests.
    """
    A, X, Y = fresh("a"), fresh("x"), fresh("y")
    t, s = fresh("t"), fresh("s")
    M = 2 * A * b - b ** 2 - 1
    ineq = L_nonneg_N if over_N else L_nonneg

    # IMPORTANTE: crear las desigualdades UNA sola vez. Cada llamada a ineq()
    # genera simbolos frescos; reutilizar los objetos es lo que mantiene
    # alineadas las holguras del sistema y las del testigo.
    slacks = [(ineq(M - c - 1), lambda av, kv, cv, bv: (2*av*bv - bv**2 - 1) - cv - 1),
              (ineq(A - c - 1), lambda av, kv, cv, bv: av - cv - 1),
              (ineq(A - k - 2), lambda av, kv, cv, bv: av - kv - 2)]

    core = Dioph(
        params=sorted((b.free_symbols | k.free_symbols | c.free_symbols), key=str),
        unknowns=[A, X, Y, t, s],
        eqs=[
            sympy.expand(X ** 2 - (A ** 2 - 1) * Y ** 2 - 1),
            sympy.expand(Y - k - (A - 1) * t),
            sympy.expand((X - (A - b) * Y) - c - M * s),
        ],
        witness=None, name="nucleo exponencial")

    system = conj(core, *[d for d, _ in slacks], name=f"{c} = {b}^{k}")

    def w(vals):
        bv, kv, cv = int(b.subs(vals)), int(k.subs(vals)), int(c.subs(vals))
        if bv < 2 or kv < 1 or cv != bv ** kv:
            return None
        av = max(cv, kv) + 3                      # satisface (5) y (6)
        while 2 * av * bv - bv ** 2 - 1 <= cv:    # asegura (4)
            av += 1
        xv, yv = pell_seq(av, kv)
        Mv = 2 * av * bv - bv ** 2 - 1
        if (yv - kv) % (av - 1) != 0:
            return None
        rest = (xv - (av - bv) * yv) - cv
        if rest % Mv != 0 or rest < 0:            # s >= 0: la razon del signo
            return None
        out = {A: av, X: xv, Y: yv, t: (yv - kv) // (av - 1), s: rest // Mv}
        for d, val_fn in slacks:                  # holguras de Lagrange (solo sobre Z)
            if not d.unknowns:
                continue
            q = four_squares(val_fn(av, kv, cv, bv))
            if q is None:
                return None
            out.update(dict(zip(d.unknowns, q)))
        return out

    system.witness = w
    return system


# ---------------------------------------------------------------------------
#   CADENA COMPLETA HACIA LOS PRIMOS:  binomial -> factorial -> Wilson
# ---------------------------------------------------------------------------

def L_value(sym, fn):
    """Introduce una incognita cuyo VALOR sabe calcular el testigo. COSTE: 1.

    No impone restriccion: la restriccion la pone el lema que acompana (p. ej.
    L_exponential). Sirve para que el testigo de una composicion larga sepa que
    valor dar a cada magnitud intermedia.
    """
    return Dioph(params=[], unknowns=[sym], eqs=[],
                 witness=lambda vals: {sym: int(fn(vals))}, name=f"valor {sym}")


def L_floor_div(a, b, q, over_N=True):
    """q = floor(a/b) con b > 0.   exists rem : a = b*q + rem, 0 <= rem < b.

    COSTE: 1 incognita sobre N (el resto); +8 sobre Z (dos desigualdades).
    """
    rem = fresh("rm")
    ineq = L_nonneg_N if over_N else L_nonneg
    core = Dioph(params=sorted((a.free_symbols | b.free_symbols | q.free_symbols), key=str),
                 unknowns=[rem], eqs=[sympy.expand(a - b * q - rem)],
                 witness=None, name="division entera")

    i1, i2 = ineq(rem), ineq(b - rem - 1)
    system = conj(core, i1, i2, name=f"{q} = floor({a}/{b})")

    def w(vals):
        av, bv, qv = int(a.subs(vals)), int(b.subs(vals)), int(q.subs(vals))
        if bv <= 0:
            return None
        rv = av - bv * qv
        if rv < 0 or rv >= bv:
            return None
        out = {rem: rv}
        for d, val in ((i1, rv), (i2, bv - rv - 1)):
            if d.unknowns:
                qd = four_squares(val)
                if qd is None:
                    return None
                out.update(dict(zip(d.unknowns, qd)))
        return out

    system.witness = w
    return system


def L_binomial(r, n, c, over_N=True):
    """c = C(r,n) por EXTRACCION DE DIGITOS en base u.

    Identidad (Julia Robinson):  C(r,n) = floor((u+1)^r / u^n) mod u,  con
    u > 2^r (asi ningun binomial se desborda de su digito). Verificada aqui en
    252 casos sin fallos.

    Cadena: T = 2^r ; u = T+1 ; W = (u+1)^r ; P = u^n ; Q = floor(W/P) ;
            c == Q (mod u) ; c < u.
    """
    T, W, P, Q = fresh("bt"), fresh("bw"), fresh("bp"), fresh("bq")
    u = T + 1
    ineq = L_nonneg_N if over_N else L_nonneg

    partes = [
        L_value(T, lambda v: 2 ** int(r.subs(v))),
        L_exponential(sympy.Integer(2), r, T, over_N=over_N),
        L_value(W, lambda v: (int(u.subs(v)) + 1) ** int(r.subs(v))),
        L_exponential(u + 1, r, W, over_N=over_N),
        L_value(P, lambda v: int(u.subs(v)) ** int(n.subs(v))),
        L_exponential(u, n, P, over_N=over_N),
        L_value(Q, lambda v: int(W.subs(v)) // int(P.subs(v))),
        L_floor_div(W, P, Q, over_N=over_N),
        L_congruent(c, Q, u),
        ineq(u - c - 1),
    ]
    return conj(*partes, name=f"{c} = C({r},{n})")


def L_factorial(n, m, over_N=True):
    """m = n!   via  n! = floor(r^n / C(r,n))  con  r > (n+1)^(n+1).

    Identidad clasica (Julia Robinson). La cota (n+1)^(n+1) es la DEMOSTRABLE;
    empiricamente basta un r mucho menor (n=5: 1207 frente a 46656), pero el
    sistema debe imponer la cota probada.

    AVISO DE TAMANO: el testigo crece de forma explosiva. Para n=3 la cota exige
    r=257 y la cadena binomial maneja numeros de ~20.000 digitos; para n>=5 deja
    de ser computable. Es el precio real de MRDP, y por eso estas
    representaciones son teoricas y no practicas.
    """
    E, R, A, B = fresh("fe"), fresh("fr"), fresh("fa"), fresh("fb")

    partes = [
        L_value(E, lambda v: (int(n.subs(v)) + 1) ** (int(n.subs(v)) + 1)),
        L_exponential(n + 1, n + 1, E, over_N=over_N),
        L_value(R, lambda v: int(E.subs(v)) + 1),
        Dioph(params=[], unknowns=[], eqs=[sympy.expand(R - E - 1)],
              witness=lambda v: {}, name="R = E+1"),
        L_value(A, lambda v: int(R.subs(v)) ** int(n.subs(v))),
        L_exponential(R, n, A, over_N=over_N),
        L_value(B, lambda v: sympy.binomial(int(R.subs(v)), int(n.subs(v)))),
        L_binomial(R, n, B, over_N=over_N),
        L_floor_div(A, B, m, over_N=over_N),
    ]
    return conj(*partes, name=f"{m} = {n}!")


def L_prime(n, over_N=True):
    """n es PRIMO, via el teorema de WILSON:  n primo <=> n | (n-1)! + 1  (n>1).

    Cadena completa: Wilson -> factorial -> binomial -> exponenciacion -> Pell.
    Esta es la primera representacion COMPLETA de los primos que produce el
    calculo. Su coste medido es el punto de partida frente al record de 9.
    """
    m = fresh("wm")
    partes = [
        L_value(m, lambda v: sympy.factorial(int(n.subs(v)) - 1)),
        L_factorial(n - 1, m, over_N=over_N),
        L_divides(n, m + 1),
        (L_nonneg_N if over_N else L_nonneg)(n - 2),
    ]
    system = conj(*partes, name=f"{n} es primo (Wilson)")

    # Cortocircuito del CONSTRUCTOR: para un compuesto no existe testigo (Wilson),
    # y desplegar la cadena seria ademas incomputable para n moderado (8! exige
    # r = 9^9 ~ 3.9e8). El constructor lo rechaza de inmediato.
    # OJO: esto optimiza el CONSTRUCTOR, no demuestra soundness; esa descansa en
    # el teorema de Wilson, verificado por separado en el test.
    inner = system.witness

    def w(vals):
        nv = int(n.subs(vals))
        if nv < 2 or not sympy.isprime(nv):
            return None
        return inner(vals)

    system.witness = w
    return system
