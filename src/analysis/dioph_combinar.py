"""
================================================================================
   DIOPHANTUS - EL TEOREMA DE COMBINACION DE RELACIONES (Matijasevic-Robinson)
================================================================================
Referencia (fuente PRIMARIA, cotejada sobre el escaneo del original):
    Yu. Matijasevic y Julia Robinson, "Reduction of an arbitrary diophantine
    equation to one in 13 unknowns", Acta Arithmetica 27 (1975) 521-553.
    TEOREMA 1 (p. 525) y TEOREMA 3 (p. 526).

QUE ES Y POR QUE IMPORTA. Es la unica pieza de la maquinaria clasica que este
proyecto no tenia, y la unica que baja el numero de incognitas de verdad. Se
declaro "sin implementar" desde el principio y se llego a medir su techo -- pero
sobre el sistema (1) de JSWW, donde apenas hay condiciones que colapsar. La
cuenta real esta en la seccion 3 de JSWW:

    33 variables --eliminar las 14-->  19  --COMBINACION-->  12

O sea que vale SIETE variables. De aqui salen las 12 de su Teorema 2.

TEOREMA 1 (p. 525). Para enteros A_1..A_q:

    A_1 = [] , ... , A_q = []      <=>     J_q(A_1,...,A_q,X) = 0 para algun X

    J_q = PRODUCTO sobre TODAS las combinaciones de signos de
              (X +- sqrt(A_1) +- sqrt(A_2) W +- ... +- sqrt(A_q) W^(q-1))
    W   = 1 + suma de A_i^2

TEOREMA 3 (p. 526), el que se usa. Para enteros A_1..A_q, B, C, D con B != 0:

    A_1 = [], ..., A_q = [],  B | C,  D > 0    <=>    M_q(...,n) = 0 para
                                                      algun NATURAL n
    M_q = PRODUCTO sobre todas las combinaciones de signos de
              ( B^2 n + C^2 - B^2 (2D-1) ( C^2 + W^q
                                           +- sqrt(A_1) +- sqrt(A_2) W
                                           +- ... +- sqrt(A_q) W^(q-1) ) )

COMO SE CALCULA SIN RAICES. El producto sobre los 2^q signos es una NORMA: las
raices se cancelan y el resultado es un polinomio entero. Se calcula iterando,
sin generar los 2^q factores:

    P_0(u) = u
    P_i(u) = P_(i-1)(u + c_i s) * P_(i-1)(u - c_i s),  reduciendo s^2 -> A_i

con `c_i = B^2 (2D-1) W^(i-1)`, y al final `u -> B^2 n + C^2 - B^2(2D-1)(C^2+W^q)`.
Para q = 6 eso son 64 factores; iterando son seis pasos.

EL PRECIO ES EL GRADO, y es brutal: el producto tiene 2^q factores. Por eso el
polinomio de 12 variables de JSWW tiene grado 13.697. Este modulo NO oculta ese
coste: `grado_combinado` lo devuelve para que la cifra entre en la frontera de
Pareto con su grado real, que es justo lo que la literatura no hizo.
"""

import sympy


def _norma_cuadratica(P, u, c, A):
    """`P(u + c*s) * P(u - c*s)` con `s = sqrt(A)`, ya reducido a polinomio.

    Las potencias IMPARES de `s` se cancelan solas --el producto es par en `s`--
    y las pares se sustituyen `s^(2k) -> A^k`. Se hace con `Poly` en `s` en vez
    de con `subs(s**2, A)`, que no reduce `s**4` ni `s**6`.
    """
    s = sympy.Dummy('s')
    prod = sympy.expand(P.subs(u, u + c * s) * P.subs(u, u - c * s))
    pol = sympy.Poly(prod, s)
    out = 0
    for (e,), coef in zip(pol.monoms(), pol.coeffs()):
        if e % 2:
            if sympy.expand(coef) != 0:
                raise ValueError(f"potencia impar de la raiz no se cancelo: s^{e}")
            continue
        out += coef * A ** (e // 2)
    return sympy.expand(out)


def J(As, X):
    """TEOREMA 1: `J_q(A_1..A_q, X)`, cuyo anularse equivale a que todas sean cuadrados."""
    As = list(As)
    W = 1 + sum(A ** 2 for A in As)
    u = sympy.Dummy('u')
    P = u
    for idx, A in enumerate(As):
        P = _norma_cuadratica(P, u, W ** idx, A)
    return sympy.expand(P.subs(u, X))


def M(As, B, C, D, n):
    """TEOREMA 3: `M_q(A_1..A_q, B, C, D, n)`.

    Se anula para algun `n` natural si y solo si todas las `A_i` son cuadrados,
    `B | C` y `D > 0`. Combina las tres clases de condicion --cuadrado,
    divisibilidad y positividad-- en UNA ecuacion al coste de UNA incognita.
    """
    As = list(As)
    q = len(As)
    W = 1 + sum(A ** 2 for A in As)
    T = B ** 2 * n + C ** 2 - B ** 2 * (2 * D - 1) * (C ** 2 + W ** q)
    u = sympy.Dummy('u')
    P = u
    for idx, A in enumerate(As):
        P = _norma_cuadratica(P, u, B ** 2 * (2 * D - 1) * W ** idx, A)
    return sympy.expand(P.subs(u, T))


def grado_combinado(As, B, C, D, n, gens):
    """Grado total de `M_q`, EXPANDIENDOLO. Solo viable para `q` pequeno."""
    e = M(As, B, C, D, n)
    return sympy.Poly(e, *gens).total_degree()


def grado_estimado(gr_As, gr_B, gr_C, gr_D, gr_n=1):
    """Grado de `M_q` SIN expandirlo, a partir de los grados de las entradas.

    HACE FALTA porque para `q = 6` --el caso de JSWW-- el polinomio tiene 2^6 = 64
    factores y su expansion es inabordable: el suyo tiene grado 13.376. Pero el
    grado se lee de la estructura sin construirlo.

    Cada factor es
        B^2 n + C^2 - B^2 (2D-1) ( C^2 + W^q +- sqrt(A_1) +- ... )
    y el termino dominante es `B^2 (2D-1) W^q`, con `W = 1 + suma A_i^2` de grado
    `2 max deg A_i`. El producto son 2^q factores iguales en grado.
    """
    q = len(gr_As)
    gr_W = 2 * max(gr_As) if gr_As else 0
    gr_factor = max(2 * gr_B + gr_n,           # B^2 n
                    2 * gr_C,                   # C^2
                    2 * gr_B + gr_D + max(2 * gr_C, q * gr_W))
    return 2 ** q * gr_factor


def grado_estimado_refinado(gr_As, gr_B, gr_C, gr_D, gr_n=1):
    """Grado de `M_q` con los DOS refinamientos de Matijasevic (JSWW p. 462).

    JSWW calculan primero `M_6` con el teorema plano de [11] y les sale 148.864
    (p. 461). En la pagina siguiente escriben:

        "However, Yuri Matijasevic has recently worked out a more efficient
         version of the relation combining theorem. If we suppose that
         1 + |A_i| <= V_i, then in M_q we may replace W_i by W_i = V_1 V_2 ... V_i,
         (i = 1, 2, ..., q). Thus when a square condition arises from a Pell
         equation, (a^2-1)b^2 + 1 = [], we may choose any V >= |ab| + 1. Also, if
         the quantities B and C of [11] are non-negative, as they are here, they
         need not be squared in M_q. These refinements yield a polynomial M_6 of
         degree 13376."

    DOS CAMBIOS, y aqui estan los dos:

      1. `W^i` --con `W = 1 + suma A_j^2`, de grado `2 max deg A_j`-- se sustituye
         por `W_i = V_1...V_i`. El grado pasa de `i * 2 max deg A_j` a
         `suma_j deg V_j`, que es mucho menor en cuanto los grados son dispares.

         QUE GRADO TIENE `V_i`, que es la unica lectura no literal. El texto dice
         `V_i >= 1 + |A_i|` (grado `deg A_i`) y luego, para las condiciones que
         vienen de una Pell, `V >= |ab| + 1`, que es del orden de `raiz(A_i)`.
         Aqui se toma **`deg V_i = ceil(deg A_i / 2)` para todas**, que es lo
         natural: la condicion ES que `A_i` sea un cuadrado, asi que `raiz(A_i)`
         es un entero y sirve de cota.

      2. `B` y `C` no se elevan al cuadrado.

    POR QUE SE PUEDE CONFIAR EN ESA LECTURA. Reproduce EXACTAMENTE cuatro numeros
    publicados, tres de ellos con esta funcion y uno con la plana:

        M_6 plano      148864   (p. 461)   <- `grado_estimado`
        M_6 refinado    13376   (p. 462)
        M_5 con (24)     6848   (p. 462)
        generador P     13697   (p. 462)   = 1 + 2*6848

    Cuatro coincidencias exactas con una sola regla no son casualidad. Si la
    lectura fuera otra, fallarian.
    """
    q = len(gr_As)
    gr_W = sum((d + 1) // 2 for d in gr_As)      # W_q = V_1...V_q
    gr_factor = max(gr_B + gr_n,                  # B n   (ya no B^2 n)
                    gr_C,                         # C     (ya no C^2)
                    gr_B + gr_D + max(gr_C, gr_W))
    return 2 ** q * gr_factor
