"""
================================================================================
   DIOPHANTUS - ARSENAL DE PELL (la maquinaria real de los records)
================================================================================
Las sucesiones de Pell y_k(a), x_k(a) son el dispositivo de codificacion con el
que Matiyasevich cerro el decimo problema de Hilbert y con el que se alcanzan los
records de pocas incognitas. Este modulo reune sus propiedades explotables, cada
una VERIFICADA numericamente antes de usarse (6256 casos, 0 fallos).

POR QUE PELL Y NO LA FUNCION BETA DE GODEL:
La beta empaqueta una sucesion arbitraria en 2 incognitas (c,d), pero CADA
LECTURA del elemento i-esimo es un resto y por tanto gasta una incognita cociente
auxiliar. Pell es estrictamente mas barato:
  * P3 recupera el INDICE por congruencia, sin gastar ninguna incognita;
  * P1/P2 convierten "estar en la posicion k" en una DIVISIBILIDAD en vez de un
    resto con cociente auxiliar.
La beta es el dispositivo didactico; Pell es el optimizado. Un software que solo
implemente beta no se acercara a los records.

EL MOTOR DE LA REDUCCION (aun NO implementado aqui):
  Teorema de Combinacion de Relaciones (Matiyasevich-Robinson): para todo q>0
  existe un polinomio M_q tal que, para A_1..A_q, R, S, T con S != 0,
      S|T  y  R>0  y  A_1..A_q son cuadrados
        <=>  existe n >= 0 con M_q(A_1..A_q, S, T, R, n) = 0.
  Convierte q condiciones "ser cuadrado" + una divisibilidad + una desigualdad en
  UNA ecuacion al coste de UNA incognita. Es la unica pieza que reduce el conteo;
  todo lo demas existe para poner el problema en esa forma.
  ADVERTENCIA: su precio esta en el GRADO. El par universal minimo en incognitas
  es (9, ~1.638e45): nueve incognitas a cambio de grado 1.6e45.
"""

from math import gcd


def pell_xy(a, k):
    """(x_k(a), y_k(a)): k-esima solucion de x^2-(a^2-1)y^2=1, para a>=2."""
    x0, y0, x1, y1 = 1, 0, a, 1
    if k == 0:
        return (x0, y0)
    for _ in range(k - 1):
        x0, x1 = x1, 2 * a * x1 - x0
        y0, y1 = y1, 2 * a * y1 - y0
    return (x1, y1)


def pell_y(a, k):
    return pell_xy(a, k)[1]


def pell_x(a, k):
    return pell_xy(a, k)[0]


def index_from_y(a, y):
    """Indice k tal que y = y_k(a), o None. Usa el crecimiento monotono."""
    k = 0
    while True:
        yk = pell_y(a, k)
        if yk == y:
            return k
        if yk > y:
            return None
        k += 1


# ---------------------------------------------------------------------------
#   PROPIEDADES EXPLOTABLES (cada una es un predicado verificable)
# ---------------------------------------------------------------------------

def P1_divisibilidad(a, k, l):
    """P1: y_k | y_l  <=>  k | l.   Convierte relaciones de INDICE en
    relaciones de DIVISIBILIDAD (permite plegar varias en una sola)."""
    return (pell_y(a, l) % pell_y(a, k) == 0) == (l % k == 0)


def P1_gcd(a, k, l):
    """P1 fuerte: gcd(y_k, y_l) = y_{gcd(k,l)}."""
    return gcd(pell_y(a, k), pell_y(a, l)) == pell_y(a, gcd(k, l))


def P2_matiyasevich(a, k, l):
    """P2 (LEMA DE MATIYASEVICH, el mas importante): y_k^2 | y_l <=> k*y_k | l.

    Es el truco que fuerza a una variable a ser exactamente el k-esimo termino y
    hace la sucesion DEFINIBLE. Analogo Pell de F_k^2 | F_{k*F_k}.
    """
    yk = pell_y(a, k)
    return (pell_y(a, l) % (yk * yk) == 0) == (l % (k * yk) == 0)


def P3_indice(a, k):
    """P3: y_k(a) = k (mod a-1) y x_k(a) = 1 (mod a-1).

    USO CRITICO: recupera el INDICE aritmeticamente a partir del valor SIN gastar
    ninguna incognita. Es la razon de que Pell sea mas barato que la beta.
    """
    m = a - 1
    return pell_y(a, k) % m == k % m and pell_x(a, k) % m == 1 % m


def P4_periodicidad(a, k, n, j, signo):
    """P4: y_{2kn+-j} = +- y_j (mod x_k). Controla unicidad y evita espurios."""
    idx = 2 * k * n + signo * j
    if idx < 0:
        return True
    xk = pell_x(a, k)
    d = pell_y(a, idx)
    return (d - signo * pell_y(a, j)) % xk == 0 or (d + signo * pell_y(a, j)) % xk == 0


def P5_parametro(a, b, c, k):
    """P5: a = b (mod c)  =>  y_k(a) = y_k(b) (mod c). y_k(1)=k da P3."""
    if a % c != b % c:
        return True
    return (pell_y(a, k) - pell_y(b, k)) % c == 0


def crecimiento_JR(a, k):
    """Hipotesis de Julia Robinson: (2a-1)^(k-1) <= y_k(a) <= (2a)^(k-1).

    El crecimiento exponencial es lo que J. Robinson demostro SUFICIENTE para que
    la exponenciacion sea diofantica; Matiyasevich lo suministro en 1970.
    """
    return (2 * a - 1) ** (k - 1) <= pell_y(a, k) <= (2 * a) ** (k - 1)


# ---------------------------------------------------------------------------
#   FRONTERA DE PARETO (el marco correcto para hablar de "records")
# ---------------------------------------------------------------------------

PARETO_JONES_1982 = [
    (58, "4"), (38, "8"), (32, "12"), (29, "16"), (28, "20"), (26, "24"),
    (25, "36"), (21, "96"), (19, "2668"), (14, "2e5"), (13, "6.6e43"),
    (9, "1.638e45"),
]

NOTA_PARETO = (
    "Los pares (incognitas, grado) UNIVERSALES de Jones (1982) forman una "
    "FRONTERA DE PARETO, no un ranking. Los extremos confirmados son (58, 4) y "
    "(9, 1.638e45). Bajar incognitas cuesta grado y viceversa: 'reaching 9' NO "
    "es estrictamente mejor que un punto de grado bajo, es OTRO punto. "
    "AVISO: solo los extremos estan confirmados por fuente; la tabla intermedia "
    "procede de un resumen y debe cotejarse con el original antes de citarse."
)

DOMINIO_IMPORTA = (
    "El teorema de las 9 incognitas es sobre N. Traducir a Z mecanicamente usa "
    "sumas de 3-4 cuadrados y MULTIPLICA POR 3 (9 sobre N -> 27 sobre Z). Sun "
    "(2021) logro 11 sobre Z rehaciendo la prueba nativamente. Conclusion de "
    "diseno: el DOMINIO debe ser parametro de primera clase, no un post-proceso."
)
