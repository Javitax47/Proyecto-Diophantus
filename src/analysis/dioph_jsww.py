"""
================================================================================
   DIOPHANTUS - EL POLINOMIO DE JONES-SATO-WADA-WIENS (1976) COMO PATRON DE MEDIDA
================================================================================
Referencia (fuente PRIMARIA, cotejada):
    J. P. Jones, D. Sato, H. Wada, D. Wiens, "Diophantine representation of the
    set of prime numbers", American Mathematical Monthly 83:6 (1976) 449-464.

Por que esta aqui: es el unico punto de la literatura contra el que podemos
medirnos SIN depender de que nuestra cadena de primos sea correcta. Su sistema
esta escrito explicitamente, se transcribe entero, y su grado se REPRODUCE
(25 como generador en 26 variables) -- lo que valida la transcripcion.

LA CITA QUE IMPORTA, textual (p. 450):

    "Our construction here yields a polynomial in 19 variables and degree 29.
     It also yields a polynomial in 42 variables and degree 5. [...] All that is
     necessary to reduce the degree to 5 is the Skolem substitution method
     (cf. [3], p. 263). However, this procedure increases the number of
     variables (to 42 when applied to (1)). We do not know whether there is a
     prime representing polynomial of degree < 5."

Tres consecuencias, y las tres son incomodas de la forma util:

 1. El famoso "record de menor grado, (42, 5)" NO es una construccion aparte:
    es (1) --su polinomio de 26 variables y grado 25-- pasado por la sustitucion
    de Skolem. Es decir, EXACTAMENTE la operacion que hace `flatten_greedy`.
 2. Por tanto tenemos un patron de medida directo: aplicar nuestro aplanado a
    SU sistema y comparar con su 42. Es una comparacion limpia, independiente de
    nuestra cadena de Wilson.
 3. Medido: su Skolem anade 16 incognitas; nuestro voraz anade 30. **Nuestro
    aplanado es la pieza floja**, no una tecnica ya optimizada. El 42 no lo
    batimos con mejor aplanado sino con una representacion de partida mas barata.

`deg < 5` sigue abierto segun los propios autores, lo que concuerda con el
argumento estructural: `Q = n(1 - sum P_i^2)` tiene grado 1 + 2*max deg(P_i) y un
sistema lineal define un conjunto semilineal, que los primos no son.
"""

import sympy

from src.analysis.dioph_calculus import Dioph

# a..z: 26 variables. `k` es el parametro; las otras 25, incognitas.
_SIMBOLOS = sympy.symbols(
    'a b c d e f g h i j k l m n o p q r s t u v w x y z', integer=True)
(a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z) = _SIMBOLOS

#: Los 14 terminos que van al cuadrado dentro de las llaves de (1).
ECUACIONES = [
    w * z + h + j - q,
    (g * k + 2 * g + k + 1) * (h + j) + h - z,
    2 * n + p + q + z - e,
    16 * (k + 1) ** 3 * (k + 2) * (n + 1) ** 2 + 1 - f ** 2,
    e ** 3 * (e + 2) * (a + 1) ** 2 + 1 - o ** 2,
    (a ** 2 - 1) * y ** 2 + 1 - x ** 2,
    16 * r ** 2 * y ** 4 * (a ** 2 - 1) + 1 - u ** 2,
    ((a + u ** 2 * (u ** 2 - a)) ** 2 - 1) * (n + 4 * d * y) ** 2 + 1 - (x + c * u) ** 2,
    n + l + v - y,
    (a ** 2 - 1) * l ** 2 + 1 - m ** 2,
    a * i + k + 1 - l - i,
    p + l * (a - n - 1) + b * (2 * a * n + 2 * a - n ** 2 - 2 * n - 2) - m,
    q + y * (a - p - 1) + s * (2 * a * p + 2 * a - p ** 2 - 2 * p - 2) - x,
    z + p * l * (a - p) + t * (2 * a * p - p ** 2 - 1) - p * m,
]

INCOGNITAS = [a, b, c, d, e, f, g, h, i, j, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z]
PARAMETRO = k
#: El generador es (k+2)*(1 - sum P_i^2): el factor es k+2, no k.
FACTOR = k + 2

#: Cifras PUBLICADAS, para no tener que recordarlas de memoria.
PUBLICADO = {
    "generador": (26, 25),        # (variables, grado) del polinomio (1)
    "skolem": (42, 5),            # (1) tras la sustitucion de Skolem
    "otros": [(19, 29), (12, None)],   # tambien en el paper; el de 12 es de grado enorme
    "grado_menor_que_5": "abierto (declarado por los autores)",
    "referencia": "Jones-Sato-Wada-Wiens, Amer. Math. Monthly 83:6 (1976) 449-464",
}


def sistema(expandir=True):
    """El sistema (1) de JSWW como `Dioph`.

    `expandir=False` conserva la forma FACTORIZADA. No es un detalle cosmetico:
    la sustitucion de Skolem (`flatten_tree`) explota justamente esa estructura, y
    expandir la destruye. Medido sobre este mismo sistema:

        voraz sobre expandido      +30 incognitas
        Skolem sobre expandido     +41 incognitas   (peor: ya no hay arbol)
        Skolem sobre FACTORIZADO   +27 incognitas
        JSWW 1976 (publicado)      +16 incognitas

    Es decir: seguimos 11 incognitas por detras de lo que ellos consiguieron en
    1976 a mano. Nuestro aplanado NO es el estado del arte, y esa brecha es una
    frontera abierta medible, no una impresion.

    Sin testigo: hallar uno es el reto famoso del paper (los valores son
    astronomicos). No hace falta para medir grado ni coste de aplanado.
    """
    eqs = [sympy.expand(x_) for x_ in ECUACIONES] if expandir else list(ECUACIONES)
    return Dioph(params=[PARAMETRO], unknowns=list(INCOGNITAS), eqs=eqs,
                 witness=None, name="JSWW 1976 (26 variables, grado 25)")
