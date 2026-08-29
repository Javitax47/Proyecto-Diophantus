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
#:
#: OJO CON EL PARAMETRO: aqui `k` esta tal y como se imprime, y esta lista es la
#: que hay que usar para COTEJAR contra la pagina. Para MEDIR hay que usar
#: `ecuaciones_k_positivo()`, que reparametriza al dominio real del teorema
#: (`k >= 1`, ver `PARAMETRO_MINIMO`). La diferencia no es cosmetica: sobre `k`
#: literal la incognita `S` no es eliminable y sobre el dominio correcto si.
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

#: EL DOMINIO DEL PARAMETRO, y no es un detalle: el Teorema 3.9 empieza
#: literalmente (p. 456)
#:
#:     "THEOREM 3.9. For any POSITIVE INTEGER k, in order that k + 1 be prime,
#:      it is necessary and sufficient that the following system of equations
#:      has a solution in nonnegative integers"
#:
#: o sea `k >= 1`, NO `k >= 0`. Y no es un descuido suyo: el teorema se apoya en
#: su Lema 2.9 (Wilson), que tambien empieza "For any number k >= 1". Tiene que
#: ser asi, porque en `k = 0` el criterio de Wilson MIENTE: `k+1 = 1` divide a
#: `k!+1 = 2`, luego el criterio dice "primo" y 1 no lo es.
#:
#: Este proyecto transcribio el sistema con `k` sobre N, que es MAS de lo que el
#: teorema afirma, y de ahi salio el unico hueco que quedaba (ver
#: `RESUELTAS_POR_EL_ENUNCIADO`): el fallo estaba en la transcripcion, no en el
#: teorema, y era exactamente el mismo punto en el que falla Wilson.
PARAMETRO_MINIMO = 1

#: Lo que ellos afirman de este sistema, para comprobarlo en vez de recordarlo.
AFIRMADO = {
    "parametro_minimo": 1,            # "For any positive integer k", p. 456
    "representa": "k + 1 es primo",   # p. 456; el sistema (1) de la seccion 2
                                      # usa k + 2, que es OTRA indexacion
    "unknowns_tras_eliminar": 10,     # n, x, w, m, z, i, j, p, l, r
    "condiciones_cuadrado": 6,        # (I), (II), (VII), (XV), (XVI), (XVII)
    "condiciones_divisibilidad": 1,   # F | H - C
    "condiciones_desigualdad": 1,     # (XIV)
    "con_teorema_de_combinacion": 11,  # + el parametro => 12 variables
    "grado_del_de_12": 13697,
}


def ecuaciones_k_positivo():
    """`ECUACIONES_3` con `k -> k+1`, o sea con el parametro en SU dominio.

    POR QUE ESTO ES LA TRANSCRIPCION CORRECTA Y NO UNA VARIANTE. El Teorema 3.9
    se enuncia "for any positive integer k" (`PARAMETRO_MINIMO`), asi que el
    parametro recorre `k >= 1`. Sustituir `k = k'+1` con `k'` sobre N es la
    reparametrizacion EXACTA de ese dominio: biyectiva, sin perder ni anadir
    valores. El sistema pasa a representar "k'+2 es primo", que ademas es la
    misma indexacion que usa el sistema (1) de la seccion 2.

    Y ARREGLA LO UNICO QUE ESTABA ROTO. La incognita `S` se define por
    `S = (z+1)(k+1) - 2`, que sobre `k >= 0` puede valer -2 y por eso no se podia
    eliminar. Con `k = k'+1` queda

        S = (z+1)(k'+2) - 2 = k'z + k' + 2z

    con TODOS los coeficientes >= 0: eliminable por el criterio estructural, sin
    necesidad de ninguna cota. El hueco no se cierra demostrando nada; se cierra
    transcribiendo bien el enunciado.

    Es la misma tecnica que `dioph_jsww.sistema_desplazado` usa para `a >= 2`:
    una cota conocida se vuelve ESTRUCTURAL reparametrizando, en vez de quedarse
    como una nota al pie que el optimizador no puede ver.
    """
    kp = sympy.Symbol('k', integer=True)
    return [e.subs(k, kp + PARAMETRO_MINIMO) for e in ECUACIONES_3]


def sistema3(expandir=False, k_positivo=True):
    """El sistema del Teorema 3.9 como `Dioph`, en forma polinomica.

    OJO: no es "el sistema de JSWW" sin mas. Es su Teorema 3.9 CONVERTIDO, y la
    conversion anade ocho incognitas (seis raices, un cociente, una holgura) y
    hereda una hipotesis de positividad en (XIV). Ver los comentarios de arriba.

    `k_positivo=True` (por defecto) usa `ecuaciones_k_positivo`, que es el
    teorema en SU dominio -- "for any positive integer k", p. 456. Con
    `k_positivo=False` se obtiene la transcripcion literal en `k`, que admite
    `k = 0` y por tanto afirma MAS que el teorema; se conserva solo para poder
    medir la diferencia, no para sacar cifras de ella.
    """
    fuente = ecuaciones_k_positivo() if k_positivo else ECUACIONES_3
    eqs = [sympy.expand(e) for e in fuente] if expandir else list(fuente)
    Dp = Dioph(params=[k], unknowns=list(INCOGNITAS_3), eqs=eqs, witness=None,
               name="JSWW 1976, Teorema 3.9 (metodo del cociente)"
                    + ("" if k_positivo else " [k literal, admite k=0]"))
    Dp.no_negativos = ()
    # Las siete cuya no-negatividad esta DEMOSTRADA (ver `COTAS_DEMOSTRADAS`) y
    # que el test estructural rechaza. Con `k_positivo` la octava, `S`, pasa el
    # test estructural ella sola: son las catorce que JSWW eliminan en la p. 461.
    Dp.no_negativas_incognitas = DESBLOQUEADAS
    Dp.parametro_minimo = PARAMETRO_MINIMO if k_positivo else 0
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


# ===========================================================================
#  LAS OCHO COTAS QUE BLOQUEAN LAS ELIMINACIONES -- SEIS DEMOSTRADAS
# ===========================================================================
#
# El test estructural del proyecto ("todos los coeficientes >= 0") es SUFICIENTE
# pero no necesario, y sobre este sistema se queda corto: de las catorce
# incognitas que JSWW eliminan por sustitucion, solo seis pasan el test. Las
# otras ocho estan bloqueadas por una resta cada una. Abajo estan las ocho, con
# demostracion completa las que la tienen y con el hueco senalado las que no.
#
# TODAS las variables recorren N (>= 0). `k` es el parametro.

#: `U(X, 0) = t^4 + 2t^3 + 1` con `t = X+2`, y ese numero NO es un cuadrado
#: cuando `t >= 2`, porque cae ESTRICTAMENTE entre dos cuadrados consecutivos:
#:
#:     (t^2+t-1)^2  <  t^4 + 2t^3 + 1  <  (t^2+t)^2
#:
#: las dos diferencias son `t^2+2t > 0` y `t^2-1 > 0`. Comprobado ademas por
#: fuerza bruta hasta t = 4000 (`cotas_verificadas`).
#:
#: Consecuencia inmediata, y es la que desbloquea `L` y `R`:
#:   * (I) dice `U(2k,n) = c1^2`, luego **n >= 1**  (si n=0, t=2k+2>=2);
#:   * (II) dice `U(2n,x) = c2^2`, luego **x >= 1**  (si x=0, t=2n+2>=2).
LEMA_CUADRADO = "U(X,0) no es cuadrado para X >= 0: (t^2+t-1)^2 < t^4+2t^3+1 < (t^2+t)^2"

COTAS_DEMOSTRADAS = {
    # ---- las que salen de que todo es >= 0, sin usar ninguna ecuacion ----
    'M': ("M >= 1", "M = 16nx(w+2)+1 y todo es >= 0."),
    'A': ("A >= 1", "A = M(x+1) >= 1*1 con M >= 1."),
    'B': ("B >= 1", "B = n+1."),
    'C': ("C >= 1", "C = m+B >= 0+1."),
    # ---- la cadena, cada una apoyada en la anterior ----
    'D': ("D >= 1",
          "D = (A^2-1)C^2 + 1 y A >= 1, luego A^2-1 >= 0. DESBLOQUEA la "
          "eliminacion de D, que el test rechaza por el -1 de (A^2-1)."),
    'E': ("E >= 2",
          "E = 2(i+1)DC^2 >= 2*1*1*1 con D >= 1 y C >= 1."),
    'F': ("F >= A",
          "F = (A^2-1)E^2 + 1 >= 4(A^2-1)+1 = 4A^2-3 usando E >= 2, y "
          "4A^2-3-A = (A-1)(4A+3) >= 0 porque A >= 1. Tambien F >= 1. "
          "DESBLOQUEA F (mismo -1 que D) y, via F-A >= 0, tambien G."),
    'G': ("G >= 1",
          "G = A + F(F-A) >= A >= 1, porque F >= 0 y F-A >= 0. DESBLOQUEA G, "
          "que el test rechaza por la resta F-A."),
    'I': ("I >= 1",
          "I = (G^2-1)H^2 + 1 y G >= 1. DESBLOQUEA I (el -1 de G^2-1)."),
    # ---- las dos que salen del lema del cuadrado ----
    'L': ("L >= 0  (porque Mx >= 1)",
          "L = k+1 + l(Mx-1); basta Mx >= 1, y eso sale de M >= 1 y x >= 1, "
          "donde x >= 1 es el LEMA_CUADRADO aplicado a (II)."),
    'R': ("R >= 0  (porque Mnx >= 1)",
          "R = k+1 + r(Mnx-1); basta Mnx >= 1, y eso sale de M >= 1, n >= 1 y "
          "x >= 1, donde n >= 1 y x >= 1 son el LEMA_CUADRADO en (I) y (II)."),
    # ---- la que sale de Pell, releyendo la MISMA ecuacion (I) ----
    'K': ("K >= 0  (porque k <= n+1)",
          "K = n-k+1 + p(M-1); basta k <= n+1 y M >= 1. La ecuacion (I) parecia "
          "no ser una Pell de la forma que `Pell.lean` trata --su coeficiente es "
          "16(k+1)^3(k+2)-- pero LO ES: con m = k+1, "
          "16m^3(m+1)(n+1)^2 = ((2m+1)^2 - 1)(2m(n+1))^2, o sea A = 2k+3 e "
          "y = 2(k+1)(n+1). Con eso la congruencia `Y_j = j (mod A-1)` manda "
          "`2(k+1) | y` al indice, `j >= 2(k+1) >= 4 > 3`, y el crecimiento desde "
          "`Y_3 = 4A^2-1` da 2(k+1)(n+1) >= 16k^2+48k+35, luego n+1 >= 8k. La "
          "cota fina de JSWW es n > (2k)^(2k); para eliminar `K` basta la burda."),
}

#: Las incognitas cuya eliminacion queda LICENCIADA por las cotas de arriba.
#: `M`, `A`, `B`, `C`, `E`, `H` ya pasaban el test estructural; estas siete no.
#: Con las dos listas van TRECE de las catorce que JSWW eliminan en la p. 461.
DESBLOQUEADAS = ('D', 'F', 'G', 'I', 'K', 'L', 'R')

#: Ya no queda ninguna cota pendiente. Se conserva el nombre --vacio-- porque
#: el test lo comprueba: si algo volviera a entrar aqui, la lista de licencias y
#: la de demostraciones dejarian de cuadrar y saltaria.
COTAS_PENDIENTES = {}

RESUELTAS_POR_EL_ENUNCIADO = {
    'S': ("(z+1)(k+1) >= 2, para todo k >= 1",
          """LA OCTAVA, Y NO SE CERRO DEMOSTRANDO SINO LEYENDO. `S` pide
          `(z+1)(k+1) >= 2`, que falla en un unico punto: `z = 0` y `k = 0`. Y
          `k = 0` NO ESTA EN EL TEOREMA: el 3.9 se enuncia "for any POSITIVE
          integer k" (p. 456), y su Lema 2.9 (Wilson) tambien pide `k >= 1`.

          NO ES CASUALIDAD QUE SEA EL MISMO PUNTO. En `k = 0` el criterio de
          Wilson miente --`k+1 = 1` divide a `k!+1 = 2`, luego "1 es primo"-- y
          por eso JSWW excluyen ese valor. La incognita `S` es justamente la que
          transporta Wilson al sistema: (XXI) dice `k+1 | S+2`, y la demostracion
          de suficiencia (p. 457) usa `S >= 0` para concluir `1/2 < beta`. Que
          `S >= 0` falle exactamente donde falla Wilson no es una coincidencia:
          es el mismo hecho visto desde el sistema.

          EL ERROR ERA NUESTRO. Este proyecto transcribio `k` sobre N, o sea
          afirmando MAS que el teorema. Con `ecuaciones_k_positivo` --`k = k'+1`,
          la reparametrizacion exacta de "k >= 1"-- la definicion queda
          `S = k'z + k' + 2z`, todos los coeficientes >= 0, y `S` se elimina por
          el criterio ESTRUCTURAL sin demostrar nada.

          Con esto van las CATORCE de la p. 461, y el sistema reducido ya no
          arrastra ninguna condicion sobre `S`. Queda pendiente, aparte y sin
          relacion, la hipotesis heredada de (XIV) (`De > 0`, formula (15) de la
          p. 458), que es de la CONVERSION de la desigualdad, no de `S`."""),
}



def cotas_verificadas(tope=4000, casos=200000, semilla=0):
    """Comprueba numericamente las seis cotas demostradas. Devuelve un informe.

    No sustituye a la demostracion --esta en `Cotas3.lean`-- pero atrapa erratas
    de transcripcion, que es de lo que este proyecto ha muerto varias veces.
    """
    import math
    import random

    fallos = []
    # el lema del cuadrado, por fuerza bruta
    for t_ in range(2, tope):
        v = t_ ** 4 + 2 * t_ ** 3 + 1
        if math.isqrt(v) ** 2 == v:
            fallos.append(f"U(X,0) cuadrado en t={t_}")
    # el lema del cuadrado, simbolicamente (las dos diferencias)
    T = sympy.Symbol('T')
    medio = T ** 4 + 2 * T ** 3 + 1
    if sympy.expand(U(T - 2, 0) - medio) != 0:
        fallos.append("U(X,0) no es t^4+2t^3+1")
    if sympy.expand(medio - (T ** 2 + T - 1) ** 2) != T ** 2 + 2 * T:
        fallos.append("hueco inferior del lema mal")
    if sympy.expand((T ** 2 + T) ** 2 - medio) != T ** 2 - 1:
        fallos.append("hueco superior del lema mal")

    # LA IDENTIDAD DE LA QUE CUELGA LA COTA DE `K`, y es donde se colaria el
    # error: que (I) SEA la Pell de `A = 2k+3` con `y = 2(k+1)(n+1)`. Si esto
    # fuera falso, `Cotas3.n_succ_ge_k` compilaria hablando de otra ecuacion.
    K_ = sympy.Symbol('K_')
    if sympy.expand(16 * (K_ + 1) ** 3 * (K_ + 2)
                    - ((2 * K_ + 3) ** 2 - 1) * 4 * (K_ + 1) ** 2) != 0:
        fallos.append("(I) no es la Pell de A = 2k+3 con y = 2(k+1)(n+1)")
    # y la cota que se saca de ella:  2(k+1)(n+1) >= 4(2k+3)^2 - 1  =>  n+1 >= 8k
    if sympy.expand((16 * K_ ** 2 + 48 * K_ + 35) - 8 * K_ * (2 * K_ + 2)) \
            != 32 * K_ + 35:
        fallos.append("la cota n+1 >= 8k no se sigue de 4(2k+3)^2 - 1")

    rnd = random.Random(semilla)
    for _ in range(casos):
        kk, nn, xx, ww, mm, ii, jj = [rnd.randint(0, 6) for _ in range(7)]
        M_ = 16 * nn * xx * (ww + 2) + 1
        A_ = M_ * (xx + 1)
        B_ = nn + 1
        C_ = mm + B_
        D_ = (A_ ** 2 - 1) * C_ ** 2 + 1
        E_ = 2 * (ii + 1) * D_ * C_ ** 2
        F_ = (A_ ** 2 - 1) * E_ ** 2 + 1
        G_ = A_ + F_ * (F_ - A_)
        H_ = B_ + 2 * (jj + 1) * C_
        I_ = (G_ ** 2 - 1) * H_ ** 2 + 1
        for cond, etiqueta in ((M_ >= 1, 'M>=1'), (A_ >= 1, 'A>=1'),
                               (B_ >= 1, 'B>=1'), (C_ >= 1, 'C>=1'),
                               (D_ >= 1, 'D>=1'), (E_ >= 2, 'E>=2'),
                               (F_ >= A_, 'F>=A'), (G_ >= 1, 'G>=1'),
                               (H_ >= 1, 'H>=1'), (I_ >= 1, 'I>=1')):
            if not cond:
                fallos.append(f"{etiqueta} falla en {(kk,nn,xx,ww,mm,ii,jj)}")
    return {"ok": not fallos, "fallos": fallos,
            "cotas": sorted(COTAS_DEMOSTRADAS), "desbloqueadas": DESBLOQUEADAS}


def censo_eliminaciones(k_positivo=True):
    """Cuenta cuantas de las catorce eliminaciones estan licenciadas, y por que.

    `k_positivo=True` usa el teorema en su dominio (`k >= 1`), que es lo que dice
    la p. 456. Con `False` se obtiene el censo de la transcripcion literal, que
    deja `S` fuera; la diferencia entre los dos es exactamente una incognita, y
    el test la comprueba.

    ESTATICO A PROPOSITO, y la razon es una medida, no una preferencia. Mirar
    cada ecuacion definitoria POR SEPARADO --sin sustituir en cascada-- da la
    respuesta en dos segundos. Hacerlo de verdad, con `eliminar_lineales`, es
    INABORDABLE: al sustituir `A` dentro de `D`, `D` dentro de `E`, `E` dentro
    de `F`, `F` dentro de `G` y `G` dentro de `I`, el grado se dobla en cada
    paso y `sympy.expand` no termina (medido: >10 minutos sin salida ni con
    (XIV) fuera, que es la ecuacion cara). Los grados de la seccion 3 hay que
    calcularlos recorriendo el arbol, como hace `dioph_combinar.grado_combinado`;
    expandir no es una opcion en este sistema y conviene tenerlo escrito.

    Lo que este censo SI decide, que es lo que importa, es CUALES se pueden
    eliminar -- y eso no depende del orden: la cota es un hecho sobre el valor
    de la incognita en toda solucion.
    """
    from src.analysis.dioph_degree import _coeficientes_no_negativos_expr

    sim = {str(s): s for s in INCOGNITAS_3 + [k]}
    fuente = ecuaciones_k_positivo() if k_positivo else ECUACIONES_3
    filas = []
    for nombre in ELIMINABLES_JSWW:
        u = sim[nombre]
        for e in fuente:
            if u not in e.free_symbols:
                continue
            ex = sympy.expand(e)
            coef = ex.coeff(u, 1)
            if coef not in (1, -1) or ex.coeff(u, 2) != 0:
                continue
            resto = sympy.expand(ex - coef * u)
            if u in resto.free_symbols:
                continue
            valor = sympy.expand(-resto / coef)
            libre = _coeficientes_no_negativos_expr(valor)
            estado = ("estructural" if libre else
                      "demostrada" if nombre in DESBLOQUEADAS else
                      "pendiente" if nombre in COTAS_PENDIENTES
                      or nombre in RESUELTAS_POR_EL_ENUNCIADO else "sin clasificar")
            filas.append((nombre, str(sympy.factor(valor)), estado))
            break
    cuenta = {est: sum(1 for _, _, e in filas if e == est)
              for est in ("estructural", "demostrada", "pendiente", "sin clasificar")}
    return {"filas": filas, "cuenta": cuenta,
            "licenciadas": cuenta["estructural"] + cuenta["demostrada"],
            "total": len(filas)}


# ---------------------------------------------------------------------------
#  LO QUE CAMBIA CON LAS SEIS COTAS, Y LO QUE NO
# ---------------------------------------------------------------------------
#
# ANTES:  6 de 14 eliminaciones licenciadas (M, A, B, C, E, H).
# AHORA: LAS 14. Siete por demostracion (D, F, G, I, K, L, R) en `Cotas3.lean`
#        --sin Mathlib, sin axiomas propios y sin usar la desigualdad (XIV)-- y
#        la octava, `S`, por ESCRIBIR BIEN EL ENUNCIADO: el Teorema 3.9 pide
#        `k >= 1` (p. 456) y con `k = k'+1` su definicion pierde la resta.
# FALTA:  nada de esta lista.
#
# LO QUE ESTO NO ARREGLA, y hay que decirlo antes que nada:
#
#   1. Los tres puntos (17,521), (16,1137) y (15,3233) del teorema de combinacion
#      dejan de depender de las eliminaciones, que ya estan las catorce. Siguen
#      dependiendo de UNA cosa, y solo una: la hipotesis heredada al convertir la
#      desigualdad (XIV) en ecuacion (`De > 0`, la formula (15) de la p. 458).
#      Esa es de la CONVERSION que hace esta transcripcion, no de JSWW.
#
#   2. La frontera de Pareto no se mueve. Ya estaba medido --concediendo las ocho
#      cotas, lo mejor era (26,29) y de ahi hacia abajo hasta (21,69)-- y todo
#      eso lo domina el (21,25) que ya tenemos del sistema (1).
#
# LO QUE SI CAMBIA: los ocho pasos que la literatura da por sabidos ("the
# unknowns ... eliminate by substitution", p. 461) pasan de creidos a verificados
# por maquina. Y el ultimo enseno algo que no se sabia: el punto donde fallaba
# --`k = 0`-- es EXACTAMENTE el punto donde falla el criterio de Wilson en el que
# se apoya el teorema. No eran dos problemas; era el mismo, y estaba en nuestra
# transcripcion por poner el parametro sobre N cuando el teorema dice `k >= 1`.
