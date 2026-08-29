"""
================================================================================
   DIOPHANTUS - EL SISTEMA DE LA SECCION 3 DE JSWW (el "metodo del cociente")
================================================================================
Referencia (fuente PRIMARIA, cotejada pagina a pagina sobre el PDF original):
    J. P. Jones, D. Sato, H. Wada, D. Wiens, "Diophantine representation of the
    set of prime numbers", American Mathematical Monthly 83:6 (1976) 449-464.
    Definicion 3.7, Lema 3.8 y TEOREMA 3.9, paginas 456-457.

POR QUE ESTE SISTEMA Y NO EL (1). El sistema (1) --el que transcribe
`dioph_jsww`-- es el unico que ellos ESCRIBEN, y esta exprimido: de sus 26
variables este proyecto ha bajado a 21 y los cinco ataques al aplanado estan
medidos. Los propios autores cierran esa via en la p. 449:

    "The method of proof of Theorem 1 yields a polynomial in 16 variables. To
     reduce the number of variables below 16 requires an entirely different
     construction."

Esa "entirely different construction" es la de aqui: el METODO DEL COCIENTE de
Matijasevic-Robinson [11], que ellos describen (p. 456) como "generally more
economical with respect to the number of variables".

LA CUENTA QUE HACE INTERESANTE ESTE SISTEMA. En la p. 461 dicen exactamente
como se explota:

    "The unknowns M, A, B, C, D, E, F, G, H, I, K, L, R, S eliminate from
     (I)-(XXI) by substitution. This leaves 10 unknowns, n, x, w, m, z, i, j, p,
     l, r, the parameter k, six square conditions, one divisibility condition
     and one inequality. These remaining conditions are definable with one
     unknown, y, by the relation combining theorem of [11]. Thus we obtain a
     definition M_5 in 11 unknowns."

O sea: 14 eliminables por sustitucion --que es EXACTAMENTE lo que hace
`eliminar_lineales`-- y luego el teorema de combinacion de relaciones para
fundir ocho condiciones en una. Ese ultimo paso es el que baja de 19 a 12
variables, y el que dispara el grado a 13.697.

DONDE ESTA EL HUECO. Entre el (21,21) anunciado y el (12,13697) la curva
publicada esta VACIA, y no por casualidad: JSWW y Matijasevic optimizaban
VARIABLES dejando que el grado explotara. Nadie midio los puntos intermedios.
Este proyecto barre fronteras de Pareto; es la herramienta para esa zona.

QUE HAY QUE HACER PARA METERLO EN `Dioph`, y es donde se puede colar un error.
El Teorema 3.9 no es un sistema de ecuaciones polinomicas: tiene SEIS
condiciones de cuadrado, UNA divisibilidad y UNA desigualdad. Convertirlas
cuesta incognitas, y cada conversion se documenta aqui:

  * `X = []` (cuadrado)  ->  `X = c^2` con `c` incognita nueva.  SEIS de estas.
  * `F | H - C`          ->  `H - C = F*d1`, con `d1` incognita nueva. Es SOUND
    sobre N porque `H - C = B + (2j+1)C > 0`: de (XII), `H = B + 2(j+1)C`.
  * la desigualdad (XIV) -> ver `_desigualdad_xiv` abajo.

Total: 10 libres + 14 definidas + 6 raices + 1 cociente + 1 holgura = 32
incognitas, mas el parametro k. Tras eliminar las 14: 18 + k = **19 variables**,
que es exactamente el (19, 29) que anuncian en la p. 449.
"""

import sympy

from src.analysis.dioph_calculus import Dioph

#: El parametro y las 10 incognitas que sobreviven a la eliminacion (p. 461).
k = sympy.Symbol('k', integer=True)
LIBRES = sympy.symbols('n x w m z i j p l r', integer=True)
n, x, w, m, z, i, j, p, l, r = LIBRES

#: Las 14 que "eliminate from (I)-(XXI) by substitution" (p. 461). Mayusculas
#: como en el original; sympy distingue `m` de `M`, `i` de `I`, etc.
DEFINIDAS = sympy.symbols('M A B C D E F G H I K L R S', integer=True)
M, A, B, C, D, E, F, G, H, I, K, L, R, S = DEFINIDAS

#: Las que anade la conversion a forma polinomica: seis raices, un cociente de
#: la divisibilidad y una holgura para la desigualdad.
AUXILIARES = sympy.symbols('c1 c2 c3 c4 c5 c6 d1 s1', integer=True)
c1, c2, c3, c4, c5, c6, d1, s1 = AUXILIARES

INCOGNITAS_3 = list(LIBRES) + list(DEFINIDAS) + list(AUXILIARES)


def U(X, Y):
    """Definicion 3.7:  U(x, y) = (x+2)^3 (x+4) (y+1)^2 + 1.

    COTEJO INDEPENDIENTE, y sale exacto: `U(2k, n)` desarrollado es
    `16(k+1)^3 (k+2)(n+1)^2 + 1`, que es LITERALMENTE la cuarta ecuacion del
    sistema (1) de la seccion 2. Los dos sistemas comparten esta pieza, asi que
    la transcripcion de `U` queda contrastada contra `dioph_jsww.ECUACIONES[3]`.
    """
    return (X + 2) ** 3 * (X + 4) * (Y + 1) ** 2 + 1


def _desigualdad_xiv():
    """(XIV) del Teorema 3.9, la unica condicion que no es una igualdad.

    Tal y como esta impresa (p. 457):

        { R / [ (C/(KL) - (w+1)x) (1 - R/C)^2 L ] - (S+1) }^2 < 1/4

    con `sigma = C/(KL)` y `beta` el cociente entero de las llaves. Quitando
    denominadores:

        beta = R*K*C^2 / [ (C - (w+1)*x*K*L) * (C - R)^2 ]

    y la condicion `(beta - (S+1))^2 < 1/4` pasa a ser, multiplicando por el
    cuadrado del denominador,

        4 * (Nu - (S+1)*De)^2  <  De^2

    con `Nu = R*K*C^2` y `De = (C - (w+1)*x*K*L)*(C - R)^2`. Se vuelve ecuacion
    con una holgura `s1 >= 0`:  `4(...)^2 + 1 + s1 = De^2`.

    LO QUE ESTA CONVERSION SUPONE, y hay que decirlo: que `De > 0`. No es
    gratis, es un paso de SU demostracion --la formula (15) de la p. 458
    establece `4 < sigma - (w+1)x`-- asi que aqui se hereda como hipotesis de la
    transcripcion, no se demuestra. Mientras no se demuestre, este sistema vale
    para MEDIR la frontera pero no para publicar una cifra.
    """
    Nu = R * K * C ** 2
    De = (C - (w + 1) * x * K * L) * (C - R) ** 2
    return 4 * (Nu - (S + 1) * De) ** 2 + 1 + s1 - De ** 2


#: Las 21 condiciones del TEOREMA 3.9 (p. 456-457), en forma `expr = 0`.
ECUACIONES_3 = [
    U(2 * k, n) - c1 ** 2,                       # (I)    U(2k,n) = []
    U(2 * n, x) - c2 ** 2,                       # (II)   U(2n,x) = []
    M - (16 * n * x * (w + 2) + 1),              # (III)
    A - M * (x + 1),                             # (IV)
    B - (n + 1),                                 # (V)
    C - (m + B),                                 # (VI)
    D * F * I - c3 ** 2,                         # (VII)  DFI = []
    (H - C) - F * d1,                            # (VII)  F | H - C
    D - ((A ** 2 - 1) * C ** 2 + 1),             # (VIII)
    E - 2 * (i + 1) * D * C ** 2,                # (IX)
    F - ((A ** 2 - 1) * E ** 2 + 1),             # (X)
    G - (A + F * (F - A)),                       # (XI)
    H - (B + 2 * (j + 1) * C),                   # (XII)
    I - ((G ** 2 - 1) * H ** 2 + 1),             # (XIII)
    _desigualdad_xiv(),                          # (XIV)
    (M ** 2 - 1) * K ** 2 + 1 - c4 ** 2,         # (XV)
    (M ** 2 * x ** 2 - 1) * L ** 2 + 1 - c5 ** 2,        # (XVI)
    (M ** 2 * n ** 2 * x ** 2 - 1) * R ** 2 + 1 - c6 ** 2,  # (XVII)
    K - (n - k + 1 + p * (M - 1)),               # (XVIII)
    L - (k + 1 + l * (M * x - 1)),               # (XIX)
    R - (k + 1 + r * (M * n * x - 1)),           # (XX)
    S - ((z + 1) * (k + 1) - 2),                 # (XXI)
]

#: Las que JSWW dicen que se eliminan por sustitucion (p. 461), en un orden que
#: respeta las dependencias: cada una se define en terminos de las anteriores.
ELIMINABLES_JSWW = ['M', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I',
                    'K', 'L', 'R', 'S']

#: Lo que ellos afirman de este sistema, para comprobarlo en vez de recordarlo.
AFIRMADO = {
    "unknowns_tras_eliminar": 10,     # n, x, w, m, z, i, j, p, l, r
    "condiciones_cuadrado": 6,        # (I), (II), (VII), (XV), (XVI), (XVII)
    "condiciones_divisibilidad": 1,   # F | H - C
    "condiciones_desigualdad": 1,     # (XIV)
    "con_teorema_de_combinacion": 11,  # + el parametro => 12 variables
    "grado_del_de_12": 13697,
}


def sistema3(expandir=False):
    """El sistema del Teorema 3.9 como `Dioph`, en forma polinomica.

    OJO: no es "el sistema de JSWW" sin mas. Es su Teorema 3.9 CONVERTIDO, y la
    conversion anade ocho incognitas (seis raices, un cociente, una holgura) y
    hereda una hipotesis de positividad en (XIV). Ver los comentarios de arriba.
    """
    eqs = [sympy.expand(e) for e in ECUACIONES_3] if expandir else list(ECUACIONES_3)
    Dp = Dioph(params=[k], unknowns=list(INCOGNITAS_3), eqs=eqs, witness=None,
               name="JSWW 1976, Teorema 3.9 (metodo del cociente)")
    Dp.no_negativos = ()
    return Dp


# ---------------------------------------------------------------------------
#  MEDIDO SOBRE ESTE SISTEMA, Y EL RESULTADO ES NEGATIVO PARA LA ELIMINACION
# ---------------------------------------------------------------------------
#
# 1. CON NUESTRO CRITERIO (todos los coeficientes >= 0) solo se eliminan SEIS de
#    las catorce: M, A, B, C, H y E. La frontera, topada a grado 29, da un unico
#    punto: **(27, 29)**.
#
# 2. LAS OCHO BLOQUEADAS lo estan por un coeficiente negativo cada una, y las
#    ocho son de la MISMA forma que la cota `a >= e+1` del sistema (1): hechos
#    sobre el conjunto de soluciones que JSWW establecen en su demostracion.
#
#      D, F, I  el `-1` de `(A^2-1)`, `(G^2-1)`   <- ellos establecen A>1, G>1
#      G        `F - A`                            <- ellos establecen F >= A
#      K        `n - k + 1`                        <- ellos: n > (2k)^(2k) > k
#      L, R     `Mx - 1`, `Mnx - 1`                <- ellos: M >= 32nx
#      S        `(z+1)(k+1) - 2`                   <- trivial salvo z = k = 0
#
#    Casi todas son elementales, mucho mas faciles que la de Pell.
#
# 3. PERO EL TECHO, medido CONCEDIENDOLAS TODAS (voraz por menor grado):
#
#      -M -A -B -C -H -D -G : (26, 29)   <- lo mejor a grado 29
#      -S (25,33)  -K (24,45)  -I (23,51)  -L (22,61)  -E (21,69)
#
#    O sea que la eliminacion sobre este sistema **no llega a ningun sitio
#    nuevo**: el (21,25) que ya tenemos del sistema (1) DOMINA a todos estos
#    puntos. Demostrar las ocho cotas no vale la pena, y eso queda medido ANTES
#    de gastar el esfuerzo -- la misma disciplina que con la cota de Pell.
#
# 4. Y AL MEDIRLO SE ENTIENDE LA CONTABILIDAD ENTERA DE JSWW, que es lo mas
#    valioso de todo esto:
#
#      33 variables  --eliminar las 14-->  19 variables      <- su (19, 29)
#      19 variables  --teorema de combinacion-->  12         <- su Teorema 2
#
#    Las OCHO incognitas que anade nuestra conversion (seis raices, un cociente,
#    una holgura) son EXACTAMENTE el coste de codificar las ocho condiciones. El
#    teorema de combinacion de relaciones las sustituye por UNA. De ahi salen sus
#    12 variables, y de ahi salen las 7 que separan el 19 del 12.
#
#    Corolario sobre el grado: su "29" solo tiene sentido si las ocho condiciones
#    se mantienen COMO CONDICIONES durante las eliminaciones y se convierten al
#    final. Nosotros convertimos al principio, y por eso la desigualdad (XIV)
#    --de grado 14 ya de entrada-- hace explotar el grado al sustituir dentro.
#    No es un error de la transcripcion: es una diferencia de modelo, y explica
#    por que nuestro (19,61) no es su (19,29).
#
# CONCLUSION OPERATIVA. Sobre este sistema no queda nada que hacer con eliminacion
# ni con aplanado. La unica pieza que mueve la aguja es el TEOREMA DE COMBINACION
# DE RELACIONES de [11] --Matijasevic y J. Robinson, "Reduction of an arbitrary
# Diophantine equation to one in 13 unknowns", Acta Arithmetica 27 (1975)
# 521-553-- que vale SIETE variables y sigue sin implementar. Este proyecto midio
# una vez su "techo" y lo descarto, pero lo midio sobre el sistema (1), donde
# apenas hay condiciones que colapsar. Aqui hay ocho.
