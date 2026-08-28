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

# ---------------------------------------------------------------------------
#   COTA DEMOSTRADA:  toda solucion sobre N del sistema (1) cumple  a >= 2
# ---------------------------------------------------------------------------
#
# POR QUE IMPORTA. `eliminar_lineales` solo puede quitar una incognita cuando el
# miembro derecho tiene todos los coeficientes >= 0, porque sobre N hay que poder
# RECONSTRUIR un valor no negativo. La ecuacion (11) define
#
#       l = k + 1 + i*(a - 1)
#
# que tiene un `-i` y por eso quedaba bloqueada: sin saber `a >= 1` el valor
# reconstruido podria ser negativo y se perderia la completitud. La forma limpia
# de usar una cota de este tipo NO es relajar el criterio (que es lo unico que
# separa este codigo de aceptar sistemas falsos) sino REPARAMETRIZAR: si `a >= 2`
# esta demostrado, escribir `a = A + 2` con `A in N` es un cambio de variable
# biyectivo, y entonces `l = k + 1 + i*(A + 1)` tiene todos los coeficientes
# positivos y el criterio pasa SIN tocarlo.
#
# DEMOSTRACION (elemental, tres pasos; verificada en test_dioph_jsww [8]).
#
# Paso 1: n >= 2.
#   La ecuacion (4) dice  f^2 = 16*K^3*(K+1)*N^2 + 1  con K = k+1 >= 1, N = n+1.
#   * N = 1:  f^2 = 16K^4 + 16K^3 + 1  y
#         (4K^2+2K-1)^2 = f^2 - 4K(K+1)  <  f^2  <  f^2 + (2K-1)(2K+1) = (4K^2+2K)^2.
#   * N = 2:  f^2 = 64K^4 + 64K^3 + 1  y
#         (8K^2+4K-1)^2 = f^2 - 8K       <  f^2  <  f^2 + (4K-1)(4K+1) = (8K^2+4K)^2.
#   En ambos casos f quedaria ESTRICTAMENTE entre dos enteros consecutivos (las
#   cuatro diferencias son > 0 para todo K >= 1: se comprueba sustituyendo
#   K = KK+1 y viendo que todos los coeficientes en KK son >= 0 y no todos nulos).
#   Luego n = 0 y n = 1 son imposibles.
#
# Paso 2: a != 0.
#   Con a = 0 la ecuacion (6) queda  x^2 + y^2 = 1, luego y <= 1. La ecuacion (9)
#   es  n + l + v = y, luego n <= 1, que contradice el paso 1.
#
# Paso 3: a != 1.
#   Con a = 1 la ecuacion (5) queda  o^2 = 4e^4 + 8e^3 + 1. Para e >= 1,
#         (2e^2+2e-1)^2 = o^2 - 4e  <  o^2  <  o^2 + (4e^2-1) = (2e^2+2e)^2,
#   otra vez un encaje estricto: imposible. Luego e = 0. Pero la ecuacion (3) es
#   2n + p + q + z = e, asi que e = 0 fuerza n = 0, que contradice el paso 1.
#
# Por tanto a >= 2.  (De paso queda demostrado n >= 2, que se usa en los pasos 2 y 3
# y que tambien vale por si mismo.)
#
# LO QUE ESTO **NO** DA, y conviene tenerlo escrito porque es la frontera abierta:
# las otras tres eliminaciones necesitan `a >= n+1`, `a >= p+1` y `a >= p`, que son
# relaciones ENTRE incognitas y no se arreglan con un desplazamiento constante.
# Siguen sin demostracion (ver ESTADO_CALCULO_DIOFANTICO 3.2m).
COTA_A = 2
COTA_N = 2


def sistema_desplazado(desplazamiento=COTA_A, expandir=False, agrupado=False):
    """El sistema (1) reparametrizado con `a = A + desplazamiento`.

    Cambio de variable biyectivo N -> {desplazamiento, desplazamiento+1, ...}, y
    por tanto equisatisfacible con `sistema()` SIEMPRE QUE `a >= desplazamiento`
    este demostrado. Para 2 lo esta (ver arriba); no se debe llamar con un valor
    mayor sin una demostracion nueva.
    """
    if desplazamiento > COTA_A:
        raise ValueError(
            f"a >= {desplazamiento} no esta demostrado; la cota probada es {COTA_A}")
    fuente = ECUACIONES_AGRUPADAS if agrupado else ECUACIONES
    A = sympy.Symbol('A', integer=True)
    eqs = [x_.subs(a, A + desplazamiento) for x_ in fuente]
    if expandir:
        eqs = [sympy.expand(x_) for x_ in eqs]
    inc = [A if s is a else s for s in INCOGNITAS]
    D = Dioph(params=[PARAMETRO], unknowns=inc, eqs=eqs, witness=None,
              name=f"JSWW 1976 con a = A+{desplazamiento}")
    D.no_negativos = no_negativos_desplazados(desplazamiento)
    return D


def no_negativos_desplazados(desplazamiento=COTA_A):
    """`NO_NEGATIVOS_DEMOSTRADOS` reescrito para `sistema_desplazado`.

    NO es cosmetico. El optimizador reconoce una expresion demostrada comparando
    su `str()` contra esta tupla; tras el cambio de variable las cadenas ya no
    coinciden y las dos demostraciones se pierden EN SILENCIO. Medido: eso solo
    subia el aplanado de 17 a 20 nombres, y la cifra habria parecido un empeora-
    miento del desplazamiento cuando era un fallo de emparejado de cadenas.
    """
    A = sympy.Symbol('A', integer=True)
    loc = {str(s): s for s in _SIMBOLOS}
    return tuple(str(sympy.sympify(s, locals=loc).subs(a, A + desplazamiento))
                 for s in NO_NEGATIVOS_DEMOSTRADOS)


# ---------------------------------------------------------------------------
#  LA COTA `a >= n+1`, QUE ES OTRA COSA: DEPENDE DE PELL, NO ES ELEMENTAL
# ---------------------------------------------------------------------------
#
# `COTA_A = 2` de arriba esta demostrada de forma elemental y esta FORMALIZADA en
# Lean. Lo que sigue NO. Se separa deliberadamente porque su garantia es distinta
# y mezclarlas seria repetir el error que este proyecto ya cometio.
#
# AFIRMACION.  En toda solucion sobre N del sistema (1):   a >= n+1.
#
# DEMOSTRACION (modulo tres hechos ESTANDAR sobre la ecuacion de Pell):
#
#   1. La ec.(3) da `e = 2n + p + q + z >= 2n`, luego `n <= e/2`. Y como
#      `n >= 2` (demostrado, COTA_N), es `e >= 4`.
#
#   2. La ec.(5) es `o^2 = e^3(e+2)(a+1)^2 + 1`. La clave es factorizar:
#
#          e^3(e+2) = e^2 * (e^2 + 2e) = e^2 * ((e+1)^2 - 1)
#
#      Poniendo `Z = e(a+1)` queda la Pell CLASICA con `A = e+1`:
#
#          o^2 - ((e+1)^2 - 1) * Z^2 = 1
#
#      cuya solucion fundamental es `(A, 1)`, o sea `(e+1, 1)`.
#
#   3. [PELL 1] Sus soluciones son exactamente `Z = Z_j`, con
#      `Z_0 = 0`, `Z_1 = 1`, `Z_{j+1} = 2A*Z_j - Z_{j-1}`.
#
#   4. [PELL 2] `Z_j = j (mod A-1)`, o sea `mod e`. Como `Z = e(a+1)` es
#      multiplo de `e`, hace falta `e | j`; y `Z > 0` obliga a `j >= 1`, luego
#      `j >= e`.
#
#   5. [PELL 3] `Z_j >= (2A-1)^(j-1) = (2e+1)^(j-1)`. Con `j >= e`:
#
#          a + 1 = Z_j / e >= (2e+1)^(e-1) / e
#
#   6. Para `e >= 4` eso es astronomicamente mayor que `e/2 + 2 >= n + 2`.
#      Luego `a >= n+1`, y con un margen enorme.
#
# COMPROBADO NUMERICAMENTE (test [10]): el minimo `a+1` que admite solucion de la
# ec.(5) es 3, 21, 245, 4061, 87815 para e = 2..6 -- exactamente `Z_e/e`, que es
# lo que predice el argumento, y la fuerza bruta lo confirma hasta donde llega.
#
# LO QUE ESTO CUESTA, dicho claro: [PELL 1..3] son teoremas estandar --son la
# maquinaria con la que Matiyasevich cerro MRDP, y estan en Mathlib justamente
# por eso-- pero AQUI SE CITAN, no se demuestran. La formalizacion de este
# proyecto no usa Mathlib, asi que esta cota NO esta al nivel de `a >= 2`. Se
# marca por separado y las cifras que dependen de ella se publican aparte.
#
#: Cota `a - n >= COTA_A_MENOS_N`. Depende de Pell (ver arriba); NO formalizada.
COTA_A_MENOS_N = 1


def sistema_cota_pell(expandir=False, agrupado=False):
    """El sistema (1) con `n = N+2` y `a = n+1+A`, o sea usando `a >= n+1`.

    Mismo numero de incognitas --`N` y `A` sustituyen a `n` y `a`-- pero ahora
    `a - n - 1 = A >= 0` es estructural, y con ello la ec.(12) permite eliminar
    `m`: una incognita mas que con `a = A+2` a secas.

    OJO CON LA GARANTIA. Esto descansa en `a >= n+1`, que depende de tres hechos
    estandar de Pell CITADOS y no demostrados aqui (ver el comentario de arriba).
    `sistema_desplazado` no depende de nada citado. No son la misma clase de
    resultado y no deben ir en la misma tabla sin decirlo.
    """
    fuente = ECUACIONES_AGRUPADAS if agrupado else ECUACIONES
    N = sympy.Symbol('N', integer=True)
    A = sympy.Symbol('A', integer=True)
    eqs = [x_.subs({n: N + COTA_N, a: N + COTA_N + COTA_A_MENOS_N + A},
                   simultaneous=True) for x_ in fuente]
    if expandir:
        eqs = [sympy.expand(x_) for x_ in eqs]
    inc = [u for u in INCOGNITAS if u not in (a, n)] + [N, A]
    D = Dioph(params=[PARAMETRO], unknowns=inc, eqs=eqs, witness=None,
              name="JSWW 1976 con n = N+2 y a = n+1+A")
    D.no_negativos = ()
    return D


# La MISMA demostracion da una cota MAS FUERTE, y es la que vale la pena:
#
#     a >= e + 1     (y no solo a >= n+1)
#
# porque el paso 5 no da `a+1 >= n+2`, da `a+1 >= (2e+1)^(e-1)/e`, que es
# desmesuradamente mayor que `e+2`. Comprobado: `Z_e/e` vale 245, 4061, 87815,
# 2350153, ... frente a `e+2` = 6, 7, 8, 9. Y `e >= 4` esta garantizado porque
# `n >= 2` y `e >= 2n`. (Para `e = 2` la cota fallaria --da 3 y haria falta 4--
# pero `e = 2` es imposible por lo mismo.)
#
# POR QUE IMPORTA QUE SEA `e` Y NO `n`. Las tres restas bloqueadas son
# `a-n-1`, `a-p-1` y `a-p`, y `e = 2n+p+q+z` domina a las tres a la vez:
#
#     a - n - 1 = e + A - n = n + p + q + z + A     >= 0
#     a - p - 1 = e + A - p = 2n + q + z + A        >= 0
#     a - p     = 2n + q + z + A + 1                >= 0
#
# O sea que UNA sola sustitucion afin las arregla las tres, mientras que
# `a = n+1+A` solo arregla la primera. Medido: con `a >= n+1` hay 6 incognitas
# eliminables y con `a >= e+1` hay SIETE -- entra tambien `x`, por la ec.(13).


def no_negativos_pell():
    """`NO_NEGATIVOS_DEMOSTRADOS` reescrito para `sistema_cota_pell_fuerte`.

    LA MISMA TRAMPA QUE CON EL DESPLAZAMIENTO, y volvio a picar. El optimizador
    reconoce una expresion demostrada comparando su `str()`; tras sustituir
    `n = N+2` y `a = e+1+A` las cadenas ya no casan y la demostracion se pierde
    EN SILENCIO. Medido: con la lista vacia el aplanado del sistema de Pell sale
    `unsat` en todos los grados --sin poder nombrar `a + u^2(u^2-a)` la ec.(8) no
    se puede bajar de grado-- y parece que la reparametrizacion destruye la
    esquina de aplanado. No la destruye: faltaba pasar esta lista.
    """
    N = sympy.Symbol('N', integer=True)
    A = sympy.Symbol('A', integer=True)
    nn = N + COTA_N
    sub = {n: nn, a: 2 * nn + p + q + z + 1 + A}
    loc = {str(s_): s_ for s_ in _SIMBOLOS}
    return tuple(str(sympy.sympify(s_, locals=loc).subs(sub, simultaneous=True))
                 for s_ in NO_NEGATIVOS_DEMOSTRADOS)


def sistema_cota_pell_fuerte(expandir=False, agrupado=False):
    """El sistema (1) con `n = N+2` y `a = e+1+A`, o sea usando `a >= e+1`.

    Es la version fuerte de `sistema_cota_pell`: `e = 2n+p+q+z` domina a la vez a
    `n` y a `p`, asi que una sola sustitucion vuelve estructurales las TRES restas
    que bloqueaban eliminaciones. Da siete incognitas eliminables en vez de seis.

    MISMA DEPENDENCIA que `sistema_cota_pell`, ni mas ni menos: los tres hechos de
    Pell citados. No mejora la garantia; mejora lo que se saca de ella.
    """
    fuente = ECUACIONES_AGRUPADAS if agrupado else ECUACIONES
    N = sympy.Symbol('N', integer=True)
    A = sympy.Symbol('A', integer=True)
    nn = N + COTA_N
    ee = 2 * nn + p + q + z
    eqs = [x_.subs({n: nn, a: ee + 1 + A}, simultaneous=True) for x_ in fuente]
    if expandir:
        eqs = [sympy.expand(x_) for x_ in eqs]
    inc = [u for u in INCOGNITAS if u not in (a, n)] + [N, A]
    D = Dioph(params=[PARAMETRO], unknowns=inc, eqs=eqs, witness=None,
              name="JSWW 1976 con n = N+2 y a = e+1+A")
    D.no_negativos = no_negativos_pell()
    return D


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
    D = Dioph(params=[PARAMETRO], unknowns=list(INCOGNITAS), eqs=eqs,
                 witness=None, name="JSWW 1976 (26 variables, grado 25)")
    D.no_negativos = NO_NEGATIVOS_DEMOSTRADOS
    return D
