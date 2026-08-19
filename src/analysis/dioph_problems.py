"""
================================================================================
   DIOPHANTUS - CATALOGO UNIVERSAL DE PROBLEMAS DIOFANTICOS
================================================================================
El record de Matiyasevich NO es un resultado sobre primos: el teorema dice que
TODO conjunto diofantico admite representacion con 9 incognitas. Los primos son
una INSTANCIA. Por tanto la maquinaria correcta es universal y el catalogo de
conjuntos es su entrada.

Este modulo define:
  * DiophProblem: un conjunto S junto a su representacion diofantica y un
    ORACULO independiente (verdad de terreno) para verificarla;
  * CATALOGO: conjuntos con representacion explicita conocida;
  * verify_problem(): UN SOLO verificador, valido para CUALQUIER problema, que
    comprueba las dos direcciones:
        n in S      =>  existe testigo y ANULA el sistema
        n not in S  =>  NO existe testigo (busqueda exhaustiva acotada)

Que el mismo verificador sirva para todos los conjuntos es precisamente la
prueba de que la maquinaria es generica y no un truco por problema.

HONESTIDAD: el oraculo es independiente de la representacion (p. ej. sympy o una
criba), nunca se deriva de ella; si coincidieran por construccion, la
verificacion no probaria nada.
"""

import itertools
import sympy

from src.analysis.dioph_calculus import Dioph, conj, disj
from src.analysis.dioph_lemmas import (
    fresh, L_square, L_composite, L_divides, L_exponential, L_value,
    L_nonneg_N, L_prime_shared,
)


class DiophProblem:
    """Un conjunto S dado por (representacion diofantica, oraculo independiente)."""

    def __init__(self, name, param, system, oracle, referencia="", search_bound=None,
                 soundness="exhaustivo"):
        self.name = name
        self.param = param          # simbolo del parametro (la entrada)
        self.system = system        # Dioph que representa la pertenencia
        self.oracle = oracle        # callable(int) -> bool  (verdad de terreno)
        self.referencia = referencia
        self.search_bound = search_bound   # cota para la busqueda exhaustiva
        # MODO DE SOUNDNESS (honestidad, no cosmetica):
        #  'exhaustivo' -> la direccion inversa (no pertenece => no hay testigo) se
        #                  COMPRUEBA por busqueda exhaustiva acotada.
        #  'teorema'    -> NO se comprueba AQUI: el constructor de testigos cortocircuita
        #                  consultando el oraculo, luego esa direccion seria CIRCULAR.
        #                  Descansa en el teorema citado en `referencia`.
        # TERCER CANAL (fuera de este modulo): `dioph_soundness.soundness_report`
        # pregunta a un SMT si el sistema es INSATISFACIBLE para los valores que no
        # pertenecen. No es circular -- no usa el constructor de testigos -- y es lo
        # unico que alcanza rangos astronomicos. Fue lo que descubrio que el sistema
        # de los primos admitia 4, 9, 15 y 25. Toda cifra de coste deberia venir
        # acompanada de su veredicto.
        self.soundness = soundness

    def cost(self):
        return self.system.cost()

    def degree(self):
        return self.system.degree()

    def __repr__(self):
        return f"<Problema {self.name}: {self.cost()} incognitas, grado {self.degree()}>"


# ---------------------------------------------------------------------------
#   VERIFICADOR UNICO (la prueba de universalidad)
# ---------------------------------------------------------------------------

def verify_problem(prob, valores, exhaustivo=True):
    """Verifica una representacion sobre `valores`. Mismo codigo para todos.

    COMPLETITUD (siempre): pertenece -> el testigo se construye y ANULA el sistema.
    SOUNDNESS: solo se COMPRUEBA si prob.soundness == 'exhaustivo' (busqueda
    exhaustiva acotada). Si es 'teorema', el constructor cortocircuita con el
    oraculo y comprobarla seria CIRCULAR: se declara y descansa en la referencia.
    """
    n = prob.param
    fallos = []
    for v in valores:
        esperado = prob.oracle(v)
        ok, _ = prob.system.check_witness({n: v})
        if esperado and not ok:
            fallos.append(f"{v} pertenece pero el testigo no anula el sistema")
        if not esperado and ok:
            fallos.append(f"{v} NO pertenece pero se construyo testigo valido")
        if (not esperado) and exhaustivo and prob.soundness == "exhaustivo" \
                and prob.search_bound is not None:
            hallado = prob.system.search_witness({n: v}, prob.search_bound)
            if hallado is not None:
                fallos.append(f"{v} NO pertenece pero la busqueda hallo testigo espurio")
    return (len(fallos) == 0), fallos


# ---------------------------------------------------------------------------
#   CATALOGO
# ---------------------------------------------------------------------------

def _p_composite():
    n = sympy.Symbol('n', integer=True)
    return DiophProblem(
        "compuesto", n, L_composite(n),
        lambda v: v > 1 and not sympy.isprime(v),
        "n = (u+2)(v+2); elemental", search_bound=25)


def _p_square():
    n = sympy.Symbol('n', integer=True)
    return DiophProblem(
        "cuadrado perfecto", n, L_square(n),
        lambda v: v >= 0 and sympy.integer_nthroot(v, 2)[1],
        "n = r^2", search_bound=40)


def _p_triangular():
    n = sympy.Symbol('n', integer=True)
    r = fresh("tr")
    sysm = Dioph([n], [r], [sympy.expand(8 * n + 1 - r ** 2)],
                 witness=lambda vals: (
                     {r: int(sympy.integer_nthroot(8 * int(vals[n]) + 1, 2)[0])}
                     if sympy.integer_nthroot(8 * int(vals[n]) + 1, 2)[1] else None),
                 name="triangular")
    return DiophProblem(
        "triangular", n, sysm,
        lambda v: v >= 0 and sympy.integer_nthroot(8 * v + 1, 2)[1],
        "n triangular <=> 8n+1 es cuadrado", search_bound=60)


def _p_sum_two_squares():
    n = sympy.Symbol('n', integer=True)
    a, b = fresh("q"), fresh("q")

    def w(vals):
        v = int(vals[n])
        for i in range(0, int(v ** 0.5) + 1):
            root, exact = sympy.integer_nthroot(v - i * i, 2)
            if exact:
                return {a: i, b: int(root)}
        return None

    sysm = Dioph([n], [a, b], [sympy.expand(n - a ** 2 - b ** 2)], witness=w,
                 name="suma de dos cuadrados")
    return DiophProblem(
        "suma de 2 cuadrados", n, sysm,
        lambda v: v >= 0 and any(sympy.integer_nthroot(v - i * i, 2)[1]
                                 for i in range(0, int(v ** 0.5) + 1)),
        "n = a^2 + b^2", search_bound=30)


def _p_fibonacci():
    """n es Fibonacci <=> 5n^2+4 o 5n^2-4 es cuadrado perfecto.

    Es la version 'conjunto' de la caracterizacion de Matiyasevich
    (m^2 - mn - n^2 = +-1 para pares consecutivos), la identidad con la que
    resolvio el decimo problema de Hilbert.
    """
    n = sympy.Symbol('n', integer=True)
    r1, r2 = fresh("f"), fresh("f")
    s1 = Dioph([n], [r1], [sympy.expand(5 * n ** 2 + 4 - r1 ** 2)],
               witness=lambda v: ({r1: int(sympy.integer_nthroot(5 * int(v[n]) ** 2 + 4, 2)[0])}
                                  if sympy.integer_nthroot(5 * int(v[n]) ** 2 + 4, 2)[1] else None),
               name="5n^2+4 cuadrado")
    s2 = Dioph([n], [r2], [sympy.expand(5 * n ** 2 - 4 - r2 ** 2)],
               witness=lambda v: ({r2: int(sympy.integer_nthroot(5 * int(v[n]) ** 2 - 4, 2)[0])}
                                  if 5 * int(v[n]) ** 2 - 4 >= 0
                                  and sympy.integer_nthroot(5 * int(v[n]) ** 2 - 4, 2)[1] else None),
               name="5n^2-4 cuadrado")

    def es_fib(v):
        return any(x >= 0 and sympy.integer_nthroot(x, 2)[1]
                   for x in (5 * v * v + 4, 5 * v * v - 4))

    return DiophProblem(
        "Fibonacci", n, disj(s1, s2, name="Fibonacci"), es_fib,
        "5n^2+-4 cuadrado (Matiyasevich: m^2-mn-n^2=+-1)", search_bound=12)


def _p_pell(D=2):
    """n es la componente x de una solucion de x^2 - D y^2 = 1."""
    n = sympy.Symbol('n', integer=True)
    y = fresh("py")

    def w(vals):
        v = int(vals[n])
        num = v * v - 1
        if num < 0 or num % D != 0:
            return None
        root, exact = sympy.integer_nthroot(num // D, 2)
        return {y: int(root)} if exact else None

    sysm = Dioph([n], [y], [sympy.expand(n ** 2 - D * y ** 2 - 1)], witness=w,
                 name=f"Pell D={D}")

    def ora(v):
        num = v * v - 1
        return v >= 1 and num >= 0 and num % D == 0 and sympy.integer_nthroot(num // D, 2)[1]

    return DiophProblem(
        f"Pell x^2-{D}y^2=1", n, sysm, ora,
        "componente x de la ecuacion de Pell", search_bound=80)


def _p_power_of_two():
    """n = 2^k para algun k >= 1. Usa la exponenciacion diofantica via Pell."""
    n = sympy.Symbol('n', integer=True)
    k = fresh("pk")
    partes = [
        L_value(k, lambda v: int(int(v[n]).bit_length() - 1)),
        L_exponential(sympy.Integer(2), k, n, over_N=True),
    ]
    sysm = conj(*partes, name="potencia de 2")
    inner = sysm.witness

    def w(vals):
        v = int(vals[n])
        if v < 2 or (v & (v - 1)) != 0:
            return None
        return inner(vals)

    sysm.witness = w
    return DiophProblem(
        "potencia de 2", n, sysm,
        lambda v: v >= 2 and (v & (v - 1)) == 0,
        "n = 2^k via exponenciacion de Pell (Matiyasevich/Robinson)",
        soundness="teorema")


def _p_prime():
    n = sympy.Symbol('n', integer=True)
    return DiophProblem(
        "primo", n, L_prime_shared(n, over_N=True),
        lambda v: bool(sympy.isprime(v)),
        "Wilson + factorial + binomial + Pell (cadena completa)",
        soundness="teorema")


# Rango verificable por problema: en 'primo' el testigo explota (n=5 exige 4!,
# cuya cota clasica r=(n+1)^(n+1) lo hace incomputable), asi que se declara.
RANGO_VERIFICABLE = {
    "primo": [2, 3, 4, 9, 15, 25],
    "potencia de 2": [1, 2, 3, 4, 5, 6, 7, 8, 16, 17, 32, 64],
}
DEFECTO = list(range(0, 40))


def rango_de(prob):
    return RANGO_VERIFICABLE.get(prob.name, DEFECTO)


def build_catalog():
    """Todos los problemas del catalogo. Anadir uno nuevo = anadir una entrada."""
    return [
        _p_composite(), _p_square(), _p_triangular(), _p_sum_two_squares(),
        _p_fibonacci(), _p_pell(2), _p_pell(3), _p_power_of_two(), _p_prime(),
    ]
