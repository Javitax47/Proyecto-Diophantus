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

FRONTERA = [
    "L_exponential (c = a^b via Pell): siguiente eslabon, NO implementado.",
    "L_factorial (via exponenciacion): requiere el anterior.",
    "L_prime (Wilson: n | (n-1)!+1): requiere los dos anteriores.",
]
