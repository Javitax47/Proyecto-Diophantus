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

#: Las MISMAS ecuaciones en la forma AGRUPADA en que las escribe el paper
#: (Teorema 2.12, p. 454), con k -> k+1 ya aplicado.
#:
#: POR QUE IMPORTA: JSWW escriben (12) como `b(2a(n+1) - (n+1)^2 - 1)`, con
#: `(n+1)` agrupado; nosotros lo guardabamos desarrollado como
#: `b(2an + 2a - n^2 - 2n - 2)`. Son iguales al expandir, pero la forma agrupada
#: EXPONE `(n+1)` y `(n+1)^2` como subexpresiones nombrables -- y `(n+1)^2` ya
#: hace falta en la ecuacion (3). Desarrollar destruye justo lo que el optimizador
#: aprovecha. Es la misma leccion que la cota de Pell y que el aplanado por arbol:
#: la forma en que se ESCRIBE el sistema cambia lo que cuesta aplanarlo.
ECUACIONES_AGRUPADAS = [
    w * z + h + j - q,
    (g * (k + 1) + g + (k + 1)) * (h + j) + h - z,
    2 * n + p + q + z - e,
    (2 * (k + 1)) ** 3 * (2 * (k + 1) + 2) * (n + 1) ** 2 + 1 - f ** 2,
    e ** 3 * (e + 2) * (a + 1) ** 2 + 1 - o ** 2,
    (a ** 2 - 1) * y ** 2 + 1 - x ** 2,
    16 * (a ** 2 - 1) * r ** 2 * y ** 4 + 1 - u ** 2,
    ((a + u ** 2 * (u ** 2 - a)) ** 2 - 1) * (n + 4 * d * y) ** 2 + 1 - (x + c * u) ** 2,
    n + l + v - y,
    (a ** 2 - 1) * l ** 2 + 1 - m ** 2,
    (k + 1) + i * (a - 1) - l,
    p + l * (a - n - 1) + b * (2 * a * (n + 1) - (n + 1) ** 2 - 1) - m,
    q + y * (a - p - 1) + s * (2 * a * (p + 1) - (p + 1) ** 2 - 1) - x,
    z + p * l * (a - p) + t * (2 * a * p - p ** 2 - 1) - p * m,
]

#: Subexpresiones que NO son >= 0 por estructura pero de las que SI hay
#: demostracion. Existe esta lista porque el generador `(k+2)(1 - sum P^2)`
#: representa el conjunto sobre variables NO NEGATIVAS: cada subexpresion que se
#: nombra anade una incognita que vive en N, y la solucion original solo se
#: extiende si esa subexpresion vale >= 0 en ella. Nombrar algo que puede ser
#: negativo conserva la soundness pero puede romper la COMPLETITUD -- el primo
#: deja de emitirse. Y eso no se detecta con este sistema por evaluacion, porque
#: se transcribe sin testigo (los valores de JSWW son astronomicos).
#:
#: DEMOSTRACION de `a + u^2(u^2 - a) >= 1` sobre N, usando SOLO la ecuacion (7):
#:
#:     (7)  16 r^2 y^4 (a^2 - 1) + 1 - u^2 = 0   =>   u^2 = 16 r^2 y^4 (a^2-1) + 1
#:
#:   * Si u^2 = 1:  a + 1*(1 - a) = 1.                                     [>= 1]
#:   * Si u^2 >= 2: entonces 16 r^2 y^4 (a^2-1) >= 1, lo que obliga a a >= 2 y a
#:     r, y >= 1. Luego u^2 >= 16(a^2-1) + 1 = 16a^2 - 15 > a para a >= 2, de modo
#:     que u^2 - a >= 1 y  a + u^2(u^2-a) >= a + 2 > 0.                    [>= 1]
#:   * u^2 = 0 es imposible: exigiria 16 r^2 y^4 (a^2-1) = -1.
#:
#: Comprobada ademas por barrido en test_dioph_jsww [6].
#:
#: La OTRA subexpresion que el criterio estructural rechaza --el modulo de Davis
#: `2a(n+1) - (n+1)^2 - 1` de la ecuacion (12)-- NO esta en esta lista: es
#: positiva en la solucion que construyen JSWW porque un modulo lo es, pero eso
#: descansa en SU construccion y aqui no se demuestra. Dejarla fuera cuesta lo que
#: cueste; resulta que no cuesta nada.
#: Expresiones que NO son >= 0 por estructura (tienen coeficientes negativos) pero
#: SI lo son sobre las soluciones del sistema, con demostracion.
#:
#:  1. `a + u^2(u^2-a) >= 1`. De la ec. (7), `u^2 = 16 r^2 y^4 (a^2-1) + 1`:
#:     * a = 0 -> u^2 = 1-16r^2y^4 >= 0 obliga a ry = 0, luego u = 1 y vale 1;
#:     * a = 1 -> u^2 = 1, vale 1;
#:     * a >= 2 y ry = 0 -> u = 1, vale a + (1-a) = 1;
#:     * a >= 2 y ry >= 1 -> como a^2-1 >= a, sale u^2 >= 16a > a, luego
#:       u^2 - a >= 1 y el total es >= a+1 > 0.
#:     Comprobado ademas en 3.528 ternas (a,r,y) que satisfacen la ec. (7).
#:
#:  2. `(a + u^2(u^2-a))^2 - 1 >= 0`. Corolario inmediato de (1): si t >= 1
#:     entonces t^2 - 1 >= 0. No cuesta demostracion nueva, solo darse cuenta --y
#:     estaba en la lista de "exige demostracion" por no mirarlo.
NO_NEGATIVOS_DEMOSTRADOS = (
    "a + u**2*(-a + u**2)",
    "(a + u**2*(-a + u**2))**2 - 1",
)

INCOGNITAS = [a, b, c, d, e, f, g, h, i, j, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z]
PARAMETRO = k
#: El generador es (k+2)*(1 - sum P_i^2): el factor es k+2, no k.
FACTOR = k + 2

#: Cifras PUBLICADAS, para no tener que recordarlas de memoria.
PUBLICADO = {
    "generador": (26, 25),        # (variables, grado) del polinomio (1)
    "skolem": (42, 5),            # (1) tras la sustitucion de Skolem
    # El de 12 variables NO es "de grado enorme" indeterminado: su grado es 13.697,
    # cifra publicada por Pak-Kaliszyk (arXiv:2204.12311, ITP 2022, introduccion:
    # "the rank of the polynomial is 13,697"), que ademas son quienes formalizaron
    # el de 10 variables en Mizar. Consistencia: 13697 = 1 + 2*6848, impar, luego
    # se lee como GENERADOR. La atribucion primaria (Matiyasevich 1973) carece de
    # literatura por admision del propio JSWW: "reportedly known to Matiyasevich
    # in 1973, although no literature is available".
    "otros": [(19, 29), (12, 13697)],
    "grado_menor_que_5": "abierto (declarado por los autores)",
    "referencia": "Jones-Sato-Wada-Wiens, Amer. Math. Monthly 83:6 (1976) 449-464",
}


def sistema(expandir=True, agrupado=False):
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
    fuente = ECUACIONES_AGRUPADAS if agrupado else ECUACIONES
    eqs = [sympy.expand(x_) for x_ in fuente] if expandir else list(fuente)
    return Dioph(params=[PARAMETRO], unknowns=list(INCOGNITAS), eqs=eqs,
                 witness=None, name="JSWW 1976 (26 variables, grado 25)")
