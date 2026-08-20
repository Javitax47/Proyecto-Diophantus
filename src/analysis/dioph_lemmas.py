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
    "L_prime (WILSON, cadena COMPLETA): 38 incognitas por composicion aditiva.",
    "L_prime_shared: 29 incognitas COMPARTIENDO el contexto de Pell por exponente "
    "comun (17 en vez de 25) y eliminando R por sustitucion. Correccion preservada: "
    "n=2,3 anulan el sistema; los compuestos no admiten testigo.",
]

FRONTERA = [
    "De 29 a 9: la comparticion POR EXPONENTE COMUN esta AGOTADA. Bajar mas exige "
    "reestructurar la construccion entera (no encadenar Wilson->factorial->binomial), "
    "que es el trabajo que costo decadas a los especialistas.",
    "Reduccion del GRADO: el record se enuncia en (variables, grado); aqui solo se "
    "optimiza el primero.",
    "Verificacion mas alla de n=3: el testigo explota (n=6 ~ 2e11 digitos), asi que "
    "la correccion descansa en los teoremas citados, no en el computo.",
]


# ---------------------------------------------------------------------------
#   EXPONENCIACION DIOFANTICA (el eslabon que desbloquea la cadena al record)
# ---------------------------------------------------------------------------

def L_nonneg_N(e):
    """e >= 0 cuando las incognitas recorren N.   COSTE: 0 o 1.

    ATENCION - ESTO COSTABA SIEMPRE 0 Y ERA UN DEFECTO DE SOUNDNESS.
    Sobre N la no-negatividad es gratis para una VARIABLE SUELTA (el dominio ya
    la impone), pero NO para una expresion cualquiera como `2ab - b^2 - 1 - c - 1`.
    La version original devolvia un sistema VACIO en ambos casos, de modo que las
    condiciones laterales del lema exponencial quedaban silenciosamente anuladas
    en modo N -- justo el modo que usa el generador. Z3 encontro por ello
    soluciones espurias para n = 4, 9, 15, 25 (ver dioph_soundness.py).

    CRITERIO CORRECTO Y GENERAL: sobre N todas las variables son >= 0, luego
    **un polinomio con todos sus coeficientes >= 0 es >= 0 automaticamente**.
    Ese es el caso gratis, y contiene como casos particulares la variable suelta,
    las constantes no negativas y sumas como `T + 1` o `E + 2`. En cualquier otro
    caso hace falta una holgura:   e >= 0  <=>  exists u>=0 : e - u = 0.

    Sigue siendo mucho mas barato que sobre Z (4, por Lagrange), que es la brecha
    real entre records segun el rango de las incognitas.
    """
    e = sympy.expand(e)
    if e.is_number:
        if int(e) >= 0:
            return Dioph(params=[], unknowns=[], eqs=[], witness=lambda vals: {},
                         name=f"{e} >= 0 (cierto: gratis)")
        return Dioph(params=[], unknowns=[], eqs=[sympy.Integer(1)],
                     witness=lambda vals: None, name=f"{e} >= 0 (FALSO: insatisfacible)")
    if _coeficientes_no_negativos(e):
        return Dioph(params=sorted(e.free_symbols, key=str), unknowns=[], eqs=[],
                     witness=lambda vals: {},
                     name=f"{e} >= 0 (coeficientes >= 0 sobre N: gratis)")
    u = fresh("u")
    def w(vals):
        ev = int(e.subs(vals))
        return None if ev < 0 else {u: ev}
    return Dioph(params=sorted(e.free_symbols, key=str), unknowns=[u],
                 eqs=[sympy.expand(e - u)], witness=w,
                 name=f"{e} >= 0 (sobre N: 1 holgura)")


def _coeficientes_no_negativos(e):
    """True si todo monomio de `e` tiene coeficiente >= 0 (incluida la constante).

    Sobre N eso basta para concluir e >= 0 sin gastar nada. Si la expresion no es
    polinomica se devuelve False: preferimos pagar de mas a afirmar de mas.
    """
    try:
        syms = sorted(e.free_symbols, key=str)
        poly = sympy.Poly(e, *syms)
    except (sympy.PolynomialError, sympy.GeneratorsNeeded):
        return False
    return all(c >= 0 for c in poly.coeffs()) and poly.as_expr().subs(
        {sy: 0 for sy in syms}) >= 0


class NonnegPool:
    """Memoiza desigualdades `e >= 0` dentro de una misma construccion.

    Por que existe: una cadena larga impone la MISMA condicion varias veces desde
    eslabones distintos (p. ej. `n >= 2` llega desde el contexto de exponente n-1,
    desde la base n de una relacion y desde Wilson). Cada llamada suelta crearia
    una holgura nueva para repetir una restriccion ya presente. El pool devuelve
    el MISMO sub-sistema para expresiones sintacticamente iguales, de modo que la
    segunda vez cuesta 0.

    Es una optimizacion UNIVERSAL: no sabe nada del problema, solo deduplica.
    """

    def __init__(self, over_N=True):
        self.over_N = over_N
        self._cache = {}
        self._por_resto = {}     # parte no constante -> menor constante ya impuesta

    def __call__(self, e):
        e = sympy.expand(e)
        base = L_nonneg_N if self.over_N else L_nonneg
        clave = sympy.srepr(e)
        if clave in self._cache:
            return self._cache[clave]
        # IMPLICACION POR CONSTANTE. Si ya se impuso `resto + c0 >= 0` y ahora se
        # pide `resto + c >= 0` con c >= c0, la nueva se sigue de la anterior y no
        # cuesta nada. Es el caso real de `n - 1 >= 0` cuando `n - 2 >= 0` ya esta
        # impuesto. Solo compara expresiones que difieren en una CONSTANTE ENTERA:
        # es una implicacion decidible, no una heuristica.
        const, resto = e.as_coeff_Add()
        k_resto = sympy.srepr(resto)
        anterior = self._por_resto.get(k_resto)
        if anterior is not None and anterior <= const:
            vacio = Dioph(params=sorted(e.free_symbols, key=str), unknowns=[], eqs=[],
                          witness=lambda vals: {},
                          name=f"{e} >= 0 (implicada por {resto} + {anterior} >= 0)")
            self._cache[clave] = vacio
            return vacio
        sistema = base(e)
        self._cache[clave] = sistema
        if anterior is None or const < anterior:
            self._por_resto[k_resto] = const
        return sistema

    def sistemas(self):
        """Los sub-sistemas distintos creados (cada uno se compone UNA vez)."""
        return list(self._cache.values())


def _rango_de_aparicion(A, K, limite=200000):
    """Menor l >= 1 con K | y_l(A). Existe: y_.(A) es una sucesion de divisibilidad.

    Iterar la recurrencia modulo K es correcto pero se queda corto: el rango puede
    ser del orden de K, y K = 2*D*(e+1)*C^2 llega a miles de millones enseguida.
    Se usa la propiedad que hace tratable el problema: en una sucesion de
    divisibilidad,

        rango(m*n) = lcm(rango(m), rango(n))   para m, n coprimos

    asi que basta FACTORIZAR K y calcular el rango de cada potencia de primo
    iterando modulo ella --que es pequena-- y tomar el minimo comun multiplo.
    El resultado se comprueba antes de devolverlo (K | y_l de verdad).

    Devuelve None si no se alcanza; el llamante debe distinguir "no hay testigo"
    de "no se ha sabido calcular", que no es lo mismo.
    """
    if K <= 0:
        return None
    if K == 1:
        return 1

    def rango_potencia(pe):
        p, q = 0 % pe, 1 % pe
        for l in range(1, limite + 1):
            if q == 0:
                return l
            p, q = q, (2 * A * q - p) % pe
        return None

    total = 1
    for primo, exp in sympy.factorint(K).items():
        r = rango_potencia(primo ** exp)
        if r is None:
            return None
        total = total * r // sympy.igcd(total, r)
        if total > limite * 64:
            return None
    # comprobacion: el rango calculado debe funcionar de verdad
    p, q = 0 % K, 1 % K
    for _ in range(total - 1):
        p, q = q, (2 * A * q - p) % K
    return total if q % K == 0 else None


def L_psi(A, B, C, e=0, over_N=True):
    """C = psi_A(B) = y_B(A):  el B-esimo valor de la sucesion de Pell de parametro A.

    ESTE ES EL LEMA QUE FALTABA. La version anterior de `L_exponential` intentaba
    apanarse con la congruencia del indice (`y_k(a) == k mod a-1`), que fija el
    RESIDUO de k pero no k: valen tambien k + j(a-1), y por eso admitia valores
    espurios (3^2 admitia c en {1,3,5,7,9}). Anclar el indice es justo lo que hace
    falta, y es el contenido profundo del teorema de Matiyasevich.

    FUENTE PRIMARIA, transcrita literalmente. K. Pak, C. Kaliszyk, "Formalizing a
    Diophantine Representation of the Set of Prime Numbers", ITP 2022, Teorema 1
    (formalizado en Mizar como HILB10_8:19), que a su vez sigue a Matiyasevich y
    Robinson:

        Sean A, B, C en N con A > 1, B > 0 y e en N. Entonces C = psi_A(B) si y
        solo si existen i, j en N y auxiliares D, E, F, G, H, I en Z tales que

            D*F*I = cuadrado   AND   F | (H - C)   AND   B <= C

        donde  D = (A^2-1)C^2 + 1,   E = 2(i+1)D(e+1)C^2,   F = (A^2-1)E^2 + 1,
               G = A + F(F-A),       H = B + 2jC,           I = (G^2-1)H^2 + 1.

        Por tanto C = psi_A(B) se representa como

            0 = (D*F*I - alpha^2)^2 + (F*beta - H + C)^2 * (F*beta + H - C)^2
                + (B + gamma - C)^2

        con alpha, beta, gamma en N ocultas.

    POR QUE ESA FORMA. Cada sumando codifica una condicion y los tres se anulan a
    la vez solo si las tres se cumplen:
      * `DFI - alpha^2`            -> DFI es un cuadrado;
      * `(F*beta-H+C)(F*beta+H-C)` -> F*beta = |H-C|, es decir F | (H-C), y el
                                      producto cubre los dos signos sin gastar
                                      una incognita en el signo;
      * `B + gamma - C`            -> B <= C.
    La sucesion aparece implicitamente: D es cuadrado exactamente cuando C es un
    y-valor de A (D = x_B(A)^2), F lo es cuando E lo es, e I cuando H es un
    y-valor de G. Ahi esta anclado el indice.

    COSTE: 11 incognitas -- i, j, alpha, beta, gamma mas los seis intermedios
    D, E, F, G, H, I, que se nombran para que ninguna ecuacion pase de GRADO 5
    (ver el comentario del cuerpo: la ecuacion unica del paper, expandida, pasa
    de grado 300 y es inviable). Frente a las 7 del lema roto, son 4 mas; a
    cambio, este si es correcto.

    VERIFICACION HASTA HOY (honesta, e insuficiente):
      * SOUNDNESS: 5040 tuplas (A<=7, B<=7, C<250, e<3, i<40, j<40) que pasan
        `F|(H-C)` y `B<=C`; de ellas 1 cumple ademas `DFI = cuadrado`, y esa es
        correcta. **0 violaciones**, que es la direccion que nos mato antes.
      * COMPLETITUD: NO verificada. Los testigos (i, j) son astronomicos incluso
        para A, B pequenos, asi que el constructor de testigos de abajo solo los
        encuentra por busqueda en casos diminutos y devuelve None en el resto.
        Mientras eso siga asi, este lema NO puede sostener una cifra de record.
    """
    A = sympy.sympify(A); B = sympy.sympify(B); C = sympy.sympify(C)
    ev = sympy.sympify(e)
    i, j = fresh("pi"), fresh("pj")
    al, be, ga = fresh("pal"), fresh("pbe"), fresh("pga")
    D, E, F, G, H, I = (fresh("pD"), fresh("pE"), fresh("pF"),
                        fresh("pG"), fresh("pH"), fresh("pI"))

    # SISTEMA CON INTERMEDIOS NOMBRADOS, no ecuacion unica.
    # La forma "0 = (DFI-alpha^2)^2 + ..." del paper es compacta sobre el papel y
    # ENORME al expandir: D es de grado 4, E de 7, F de 16, G de 32, I de ~70, y
    # el cuadrado del primer sumando pasa de grado 300. Expandirla es inviable, y
    # ademas seria contraproducente: la esquina que nos interesa es la de GRADO
    # BAJO. Nombrando D..I como incognitas, ninguna ecuacion pasa de grado 5.
    # Es el mismo principio que ya aprendimos con la cota de Pell: donde se paga
    # el coste importa tanto como cuanto se paga.
    eqs = [
        D - (A ** 2 - 1) * C ** 2 - 1,              # grado 4
        E - 2 * (i + 1) * D * (ev + 1) * C ** 2,    # grado 5
        F - (A ** 2 - 1) * E ** 2 - 1,              # grado 4
        G - A - F * (F - A),                        # grado 2
        H - B - 2 * j * C,                          # grado 2
        I - (G ** 2 - 1) * H ** 2 - 1,              # grado 4
        D * F * I - al ** 2,                        # DFI es un cuadrado
        (F * be - H + C) * (F * be + H - C),        # F | (H - C), ambos signos
        B + ga - C,                                 # B <= C
    ]

    def w(vals):
        """Testigo CONSTRUIDO, no buscado.

        La busqueda era inviable: los (i, j) son astronomicos. Pero la estructura
        los determina, y esa es la diferencia entre un lema y una conjetura:

          1. D = x_B(A)^2 automaticamente, porque C = y_B(A).
          2. `F` es cuadrado si y solo si `E` es un y-valor de A. Como
             E = 2(i+1)D(e+1)C^2 = (i+1)*K, hace falta l con K | y_l(A): el RANGO
             DE APARICION de K, que existe porque la sucesion de Pell es una
             sucesion de divisibilidad. Entonces E = y_l(A), F = x_l(A)^2 e
             i = y_l(A)/K - 1.
          3. Para H basta **m = B**, y esto es lo que desatasca todo:
               * G = A + F(F-A) == 1 (mod 2C)  [porque F == 1 (mod 2C)], luego
                 2C | G-1, y por P3  y_B(G) == B (mod G-1) == B (mod 2C):
                 asi que H = y_B(G) tiene la forma B + 2jC exigida;
               * G == A (mod F) y por P5  y_B(G) == y_B(A) = C (mod F):
                 asi que F | (H - C).
             Y de paso I = (G^2-1)H^2+1 = x_B(G)^2 sale cuadrado solo.
          4. Luego DFI = (x_B(A) * x_l(A) * x_B(G))^2, cuadrado POR CONSTRUCCION.

        AVISO DE ESCALA, que no es un detalle: `l` es el rango de aparicion y
        crece muy rapido (para A=3, B=2 --o sea, para certificar que y_2(3)=6--
        ya vale 408, y E = y_408(3) tiene ~317 cifras). Los testigos de este lema
        son astronomicos POR NATURALEZA, no por la implementacion. Evaluarlos solo
        es posible en los casos mas pequenos, y por eso la completitud de la
        cadena no se podra nunca verificar por evaluacion: descansa en el teorema.
        """
        Av, Bv, Cv, evv = (int(A.subs(vals)), int(B.subs(vals)),
                           int(C.subs(vals)), int(ev.subs(vals)))
        if Av < 2 or Bv < 1 or Cv < Bv:
            return None
        xB, yB = pell_seq(Av, Bv)
        if yB != Cv:                      # solo hay testigo si C = psi_A(B)
            return None
        Dv = (Av * Av - 1) * Cv * Cv + 1
        K = 2 * Dv * (evv + 1) * Cv * Cv
        lv = _rango_de_aparicion(Av, K)
        if lv is None:
            return None
        xl, Ev = pell_seq(Av, lv)
        Fv = (Av * Av - 1) * Ev * Ev + 1
        Gv = Av + Fv * (Fv - Av)
        xm, Hv = pell_seq(Gv, Bv)         # m = B
        Iv = (Gv * Gv - 1) * Hv * Hv + 1
        if (Hv - Bv) % (2 * Cv) != 0 or (Hv - Cv) % Fv != 0:
            return None                   # no deberia ocurrir; si ocurre, se declara
        return {i: Ev // K - 1, j: (Hv - Bv) // (2 * Cv),
                al: xB * xl * xm, be: abs(Hv - Cv) // Fv, ga: Cv - Bv,
                D: Dv, E: Ev, F: Fv, G: Gv, H: Hv, I: Iv}

    params = sorted((A.free_symbols | B.free_symbols | C.free_symbols
                     | ev.free_symbols), key=str)
    return Dioph(params=params,
                 unknowns=[i, j, al, be, ga, D, E, F, G, H, I],
                 eqs=eqs, witness=w, name=f"{C} = psi_{A}({B})")


def L_exponential_psi(b, k, c, over_N=True):
    """c = b^k, RECONSTRUIDO sobre L_psi (con el indice anclado).

    Sustituye a `L_exponential`, que no era sound: sus tres ecuaciones solo
    forzaban `b^m == c (mod M)` con `m == k (mod a-1)`, y eso admite
    m = k + j(a-1). Aqui el indice lo ancla `L_psi`, asi que la congruencia de
    Davis ya dice lo que parecia decir.

    SISTEMA:
        Y = psi_a(k)                        [L_psi: 11 incognitas]
        X^2 - (a^2-1) Y^2 = 1               [X queda determinado sobre N]
        X - (a-b)Y - c - M*s = 0            [congruencia de Davis, M = 2ab-b^2-1]
        c < M,  a > c,  b >= 2,  k >= 1     [condiciones laterales]

    y `a` se fija por ecuacion lineal a una cota que garantiza a > c y M > c
    (mismo patron que PellContext: cota por ecuacion, no por sustitucion, para no
    destrozar el grado al aplanar).

    POR QUE ES CORRECTO AHORA. La congruencia de Davis
        x_k(a) - (a-b) y_k(a) == b^k   (mod 2ab - b^2 - 1)
    esta verificada en 1368 casos (test_dioph_calculus). Con `c < M` el residuo
    determina c UNIVOCAMENTE, y con el indice anclado por L_psi el residuo es
    b^k y no b^m para otro m. Los dos ingredientes estaban; faltaba el segundo.

    COSTE: mucho mayor que las 7 del lema roto. Es el precio de que sea cierto.
    """
    b = sympy.sympify(b); k = sympy.sympify(k); c = sympy.sympify(c)
    A, X, s = fresh("ea"), fresh("ex"), fresh("es")
    Y = fresh("ey")
    ineq = L_nonneg_N if over_N else L_nonneg

    M = 2 * A * b - b ** 2 - 1
    cota = b + c + k + 2                  # asegura a > c, a > b, y M > c

    partes = [
        L_value(A, lambda v: int(b.subs(v)) + int(c.subs(v)) + int(k.subs(v)) + 2),
        Dioph(params=sorted((b.free_symbols | c.free_symbols | k.free_symbols), key=str),
              unknowns=[A], eqs=[A - cota], witness=lambda v: {}, name="cota de a"),
        L_value(Y, lambda v: pell_seq(int(A.subs(v)), int(k.subs(v)))[1]),
        L_psi(A, k, Y, over_N=over_N),
        # witness={} a proposito: X y s los rellena el testigo exterior, que ya
        # conoce a, k y c. `conj` aborta si algun sub-testigo es None.
        Dioph(params=[], unknowns=[X, Y, A],
              eqs=[X ** 2 - (A ** 2 - 1) * Y ** 2 - 1],
              witness=lambda v: {}, name="Pell x"),
        Dioph(params=sorted((b.free_symbols | c.free_symbols), key=str),
              unknowns=[X, Y, A, s],
              eqs=[(X - (A - b) * Y) - c - M * s],
              witness=lambda v: {}, name="Davis"),
        ineq(b - 2),
        ineq(k - 1),
    ]
    sistema = conj(*partes, name=f"{c} = {b}^{k} (via psi)")

    interno = sistema.witness

    def w(vals):
        bv, kv, cv = int(b.subs(vals)), int(k.subs(vals)), int(c.subs(vals))
        if bv < 2 or kv < 1 or cv != bv ** kv:
            return None
        av = bv + cv + kv + 2
        xv, yv = pell_seq(av, kv)
        Mv = 2 * av * bv - bv ** 2 - 1
        resto = (xv - (av - bv) * yv) - cv
        if Mv <= 0 or resto < 0 or resto % Mv != 0:
            return None
        base = interno(vals)
        if base is None:
            return None
        base[X] = xv
        base[s] = resto // Mv
        return base

    sistema.witness = w
    return sistema


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
    A0, X, Y0 = fresh("a"), fresh("x"), fresh("y")
    t, s = fresh("t"), fresh("s")
    ineq = L_nonneg_N if over_N else L_nonneg

    # REPARAMETRIZACION: en vez de una holgura por condicion lateral, se sustituye
    # la propia incognita por su cota. Coste CERO y ademas testigo mas barato
    # (no hay que calcular holguras astronomicas). Ver PellContext.build.
    cota = k + b + c + 2
    A = A0 + cota                      # a >= k+2, a > c, a >= b  por construccion
    Y = Y0 + 1                         # y >= 1: mata la solucion trivial (x,y)=(1,0)
    M = 2 * A * b - b ** 2 - 1

    # Lo unico que NO es cota sobre una incognita propia: k y b son expresiones.
    slacks = [ineq(k - 1), ineq(b - 2)]

    core = Dioph(
        params=sorted((b.free_symbols | k.free_symbols | c.free_symbols), key=str),
        unknowns=[A0, X, Y0, t, s],
        eqs=[                                   # sin expandir: ver PellContext.build
            X ** 2 - (A ** 2 - 1) * Y ** 2 - 1,
            Y - k - (A - 1) * t,
            (X - (A - b) * Y) - c - M * s,
        ],
        witness=None, name="nucleo exponencial")

    system = conj(core, *slacks, name=f"{c} = {b}^{k}")

    def w(vals):
        bv, kv, cv = int(b.subs(vals)), int(k.subs(vals)), int(c.subs(vals))
        if bv < 2 or kv < 1 or cv != bv ** kv:
            return None
        cota_v = kv + bv + cv + 2
        av = cota_v
        xv, yv = pell_seq(av, kv)
        Mv = 2 * av * bv - bv ** 2 - 1
        if Mv <= 0 or (yv - kv) % (av - 1) != 0:
            return None
        rest = (xv - (av - bv) * yv) - cv
        if rest % Mv != 0 or rest < 0:            # s >= 0: la razon del signo
            return None
        out = {A0: av - cota_v, X: xv, Y0: yv - 1,
               t: (yv - kv) // (av - 1), s: rest // Mv}
        vals_ext = dict(vals); vals_ext.update(out)
        for d in slacks:
            if not d.unknowns:
                continue
            sub = d.witness(vals_ext)
            if sub is None:
                return None
            out.update(sub)
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
        # Se delega en el testigo de cada desigualdad en vez de asumir Lagrange:
        # sobre N una desigualdad es UNA holgura, no cuatro cuadrados. Asumirlo
        # llamaba a four_squares con numeros astronomicos y colgaba el proceso.
        vals_ext = dict(vals); vals_ext.update(out)
        for d in (i1, i2):
            if not d.unknowns:
                continue
            sub = d.witness(vals_ext)
            if sub is None:
                return None
            out.update(sub)
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


# ---------------------------------------------------------------------------
#   BUSQUEDA CON COMPARTICION DE INCOGNITAS (la unica via hacia el record)
# ---------------------------------------------------------------------------

class PellBase:
    """Base `a` de Pell COMPARTIDA por contextos con exponentes DISTINTOS.

    La comparticion que ya existia (`PellContext`) exige el MISMO exponente,
    porque x_k(a) e y_k(a) dependen de (a,k). Pero `a` solo depende de a: es un
    parametro libre de la familia de Pell, sujeto unicamente a ser bastante
    grande. Nada obliga a que cada exponente use el suyo.

    Asi que todos los contextos comparten (a, u) y cada uno aporta su cota. Como
    todas las cotas son positivas sobre N, exigir

        a = (suma de todas las cotas) + u,   u >= 0

    implica  a >= cota_j  para cada contexto j (la suma domina a cada sumando).
    No se puede escribir un `max` en una ecuacion diofantica; una suma de
    terminos no negativos hace el mismo trabajo y es lineal.

    Ahorro: 2 incognitas (a y su holgura) por cada contexto adicional.
    """

    def __init__(self, over_N=True):
        self.over_N = over_N
        self.A = fresh("ca")
        self.cotas = []

    def require(self, cota):
        """Registra una cota inferior que `a` debe superar."""
        self.cotas.append(cota)

    def build(self):
        total = sympy.Integer(0)
        for c in self.cotas:
            total = total + c
        # IGUALDAD, no desigualdad: `a` no necesita ser "suficientemente grande",
        # basta con FIJARLO a un valor que lo sea. La suma de cotas lo es, y una
        # igualdad no gasta holgura. Es mas restrictivo que `a >= suma`, luego
        # sigue siendo sound; y la completitud se conserva porque el testigo
        # elegia exactamente ese valor.
        eq = sympy.expand(self.A - total)
        params = sorted(eq.free_symbols - {self.A}, key=str)

        def w(vals):
            tv = int(total.subs(vals)) if hasattr(total, 'subs') else int(total)
            return {self.A: tv}

        return Dioph(params, [self.A], [eq], witness=w,
                     name="base de Pell compartida (a = suma de cotas)")


class PellContext:
    """Contexto de Pell COMPARTIDO por todas las relaciones con el mismo exponente.

    Observacion que lo hace posible: x_k(a) e y_k(a) dependen SOLO de (a,k). Por
    tanto varias relaciones  c_i = b_i^k  con el MISMO exponente k pueden usar el
    mismo (a, x, y, t); solo difiere s_i, porque el modulo M_i = 2*a*b_i - b_i^2 - 1
    depende de la base. Verificado en 24 relaciones sin fallos.

    Coste: 4 incognitas compartidas + 1 por relacion, en vez de 5 por relacion.
    """

    def __init__(self, k, over_N=True, pool=None, base=None):
        self.k = k
        self.over_N = over_N
        # Pool compartido con el resto de la construccion: si `k >= 1` o `b >= 2`
        # ya se impuso en otro eslabon, aqui cuesta 0.
        self.pool = pool
        # Base `a` compartida entre exponentes distintos (PellBase). Si no se da,
        # el contexto crea la suya y paga las 2 incognitas.
        self.base = base
        self.A = base.A if base is not None else fresh("ca")
        self.X, self.Y = fresh("cx"), fresh("cy")
        self.t = fresh("ct")
        self.rels = []          # (base, valor, s)

    def relate(self, b, c):
        """Registra c = b^k dentro de este contexto. COSTE: 1 incognita (s)."""
        s = fresh("cs")
        self.rels.append((b, c, s))
        return s

    def build(self):
        """Sistema completo del contexto (base compartida + todas las relaciones).

        COTA POR ECUACION LINEAL, NO POR SUSTITUCION (esto importa para el grado).
        Las condiciones laterales clasicas son cotas inferiores sobre la incognita
        compartida `a`:  a-1 > k,  a > c_i,  a >= b_i,  c_i < M_i. Imponerlas con
        una holgura cada una costaria ~2 incognitas por relacion.

        Una version anterior las resolvia SUSTITUYENDO `a := a' + cota` dentro de
        las ecuaciones. Correcto y de coste cero en la representacion, pero
        desastroso al aplanar: `a` aparece al cuadrado en la ecuacion de Pell, y
        elevar al cuadrado una suma de 6 simbolos genera decenas de monomios de
        grado 4, cada uno de los cuales hay que nombrar. La representacion era
        barata y el GENERADOR carisimo.

        Ahora `a` sigue siendo UN simbolo y la cota se impone con una ecuacion
        LINEAL aparte:

            a - cota - u = 0,     cota = k + 2 + sum_i (b_i + c_i),   u >= 0 fresca

        Cuesta 1 incognita por contexto, pero deja la ecuacion de Pell con 4
        monomios en vez de decenas. Es el mismo intercambio incognitas<->grado que
        hace `flatten_greedy`, aplicado en el sitio correcto: antes de expandir.

        Con `a >= k+2`, `a >= c_i+2`, `a >= b_i` y `b_i >= 2` se sigue:
            M_i - c_i - 1 = b_i(2a-b_i) - c_i - 2 >= b_i*a - c_i - 2
                          >= 2a - c_i - 2 >= 2c_i + 2 - c_i > 0
        Y `y >= 1` NO hace falta imponerlo: la ecuacion del indice da
        y = k + (a-1)t con k >= 1, a >= 2, t >= 0, luego y >= 1 ya se sigue.
        (Antes se imponia con y := y'+1, otra sustitucion que solo inflaba
        monomios.)
        """
        A, X, Y, t, k = self.A, self.X, self.Y, self.t, self.k
        ineq = self.pool if self.pool is not None else (
            L_nonneg_N if self.over_N else L_nonneg)

        cota = k + 2
        for b, c, _ in self.rels:
            cota = cota + b + c
        self.cota = cota

        # SIN expandir: se conserva el ARBOL, que es lo que explota la sustitucion
        # de Skolem (`flatten_tree`). Expandir aqui abarata nada y encarece el
        # generador: medido sobre el sistema de JSWW, aplanar la forma factorizada
        # cuesta +27 incognitas y la expandida +41.
        eqs = [X ** 2 - (A ** 2 - 1) * Y ** 2 - 1,                  # Pell
               Y - k - (A - 1) * t]                                 # indice
        unknowns = [X, Y, t]
        if self.base is None:
            u = fresh("cu")                 # holgura propia: a = cota + u
            eqs.append(A - cota - u)
            unknowns = [A] + unknowns + [u]
        else:
            self.base.require(cota)         # la impone la base compartida
        # Lo unico que no es cota sobre una incognita propia: k y b_i son
        # EXPRESIONES de la cadena. Sin estas dos el sistema era INSOUND (Z3 lo
        # exhibio: con a in {0,1} la ecuacion de Pell degenera y (x,y)=(1,0) la
        # resuelve; con b in {0,1} el modulo M = 2ab-b^2-1 se vuelve <= 0).
        extras = [ineq(k - 1)]                                      # k >= 1

        for b, c, s in self.rels:
            M = 2 * A * b - b ** 2 - 1
            eqs.append((X - (A - b) * Y) - c - M * s)
            unknowns.append(s)
            extras.append(ineq(b - 2))                              # base >= 2

        params = set()
        for e in eqs:
            params |= e.free_symbols
        params = sorted(params - set(unknowns), key=str)
        core = Dioph(params, unknowns, eqs, witness=None,
                     name=f"contexto Pell k={k} ({len(self.rels)} rel.)")
        system = conj(core, *extras, name=core.name)

        def w(vals):
            kv = int(self.k.subs(vals)) if hasattr(self.k, 'subs') else int(self.k)
            bs = [(int(b.subs(vals)), int(c.subs(vals)), s) for b, c, s in self.rels]
            if kv < 1 or any(bv < 2 for bv, _, _ in bs):
                return None
            cota_v = kv + 2 + sum(bv + cv for bv, cv, _ in bs)
            if self.base is None:
                av = cota_v                   # la cota ya garantiza (4)-(6)
            else:
                # La base compartida ya fijo `a` (y es >= esta cota, porque la
                # suma de cotas domina a cada sumando). Se LEE, no se elige.
                av = int(self.base.A.subs(vals))
                if av < cota_v:
                    return None
            xv, yv = pell_seq(av, kv)
            if (yv - kv) % (av - 1) != 0:
                return None
            out = {X: xv, Y: yv, t: (yv - kv) // (av - 1)}
            if self.base is None:
                out[A] = av
                out[u] = av - cota_v
            for bv, cv, s in bs:
                Mv = 2 * av * bv - bv ** 2 - 1
                rest = (xv - (av - bv) * yv) - cv
                if Mv <= 0 or rest % Mv != 0 or rest < 0:
                    return None
                out[s] = rest // Mv
            vals_ext = dict(vals); vals_ext.update(out)
            for d in extras:
                if not d.unknowns:
                    continue
                sub = d.witness(vals_ext)
                if sub is None:
                    return None
                out.update(sub)
            return out

        system.witness = w
        return system


def L_prime_shared(n, over_N=True):
    """n es PRIMO (Wilson) con COMPARTICION de incognitas entre eslabones.

    Misma matematica que L_prime, pero agrupando las 5 exponenciaciones por
    EXPONENTE en contextos de Pell compartidos:

        exponente n     : {E = n^n}                   -> 4 + 1 = 5
        exponente n-1   : {A = R^(n-1), P = u^(n-1)}  -> 4 + 2 = 6
        exponente R     : {T = 2^R,  W = (u+1)^R}     -> 4 + 2 = 6
                                             total 17  (frente a 5x5 = 25)

    Resultado medido: 30 incognitas frente a las 38 de la composicion aditiva.
    Sigue lejos de las 9 del record, pero demuestra que el mecanismo funciona y
    cuantifica cuanto da la comparticion "facil" (por exponente comun).
    """
    contexts = {}
    pool = NonnegPool(over_N)          # deduplica las desigualdades de TODA la cadena
    base = PellBase(over_N)            # UNA sola `a` para los tres exponentes

    def rel(b, k, c):
        key = sympy.srepr(sympy.sympify(k))
        if key not in contexts:
            contexts[key] = PellContext(k, over_N, pool=pool, base=base)
        contexts[key].relate(b, c)

    m = fresh("wm")
    Ev, A, B = fresh("se"), fresh("sa"), fresh("sb")
    Tv, W, P, Q = fresh("st"), fresh("sw"), fresh("sp"), fresh("sq")
    # NOTA: se probo ELIMINAR Q sustituyendola por su forma general `B + u*cq`
    # (la congruencia Q == B (mod u) queda dentro y Q deja de ser incognita).
    # Ahorra 1 incognita en la REPRESENTACION y CERO en el generador -- el
    # aplanado la vuelve a gastar, porque `P*u*cq` es un producto de tres
    # incognitas. Y a cambio dispara el coste para Z3: la comprobacion de
    # soundness paso de ~84 s a mas de 28 min sin concluir. Se descarta: la
    # verificabilidad vale mas que una incognita que no se traduce en nada.
    nn = n - 1                       # Wilson usa (n-1)!

    # DESPLAZAMIENTO DE ORIGEN (coste 0, ahorra holguras).
    # Las condiciones `R >= 2` y `u >= 2` -- ambas de la forma `base >= 2` -- se
    # convierten en condiciones sobre polinomios de coeficientes no negativos, que
    # sobre N son GRATIS. Basta almacenar E y T desplazados una unidad:
    #     E = Ev + 1  (E = n^n >= 4 para n >= 2, luego Ev >= 0 no pierde nada)
    #     T = Tv + 1  (T = 2^R >= 2)
    # Con eso  R = Ev + 2  y  u = Tv + 2: `R - 2 = Ev` y `u - 2 = Tv` tienen todos
    # los coeficientes >= 0. Antes costaban una holgura cada una.
    E = Ev + 1                       # E = n^(n-1)
    T = Tv + 1
    u = T + 1                        # = Tv + 2
    R = n * E + 1                    # = n * n^(n-1) + 1 = n^n + 1

    # UN CONTEXTO DE PELL MENOS (ahorro: 3 incognitas, coste 0).
    # Antes E = n^n, con exponente n: eso obligaba a un TERCER contexto de Pell
    # solo para esa relacion. Pero lo unico que se necesita de E es que
    # R = n^n + 1 supere la cota (n-1+1)^(n-1+1) = n^n del lema del factorial.
    # Tomando E = n^(n-1) y R = n*E + 1 se obtiene EXACTAMENTE el mismo R, y la
    # relacion pasa al contexto del exponente n-1, que ya existia. Multiplicar por
    # n es gratis; una exponenciacion nueva cuesta x, y, t.
    # Las condiciones laterales tampoco empeoran: como exponente, k-1 = n-2 ya
    # estaba en el pool; como base de R, b-2 = n*E-1 cuesta la misma holgura que
    # costaba E-1.

    # SEMILLA DEL POOL: se impone `n >= 2` ANTES que nada para que `n >= 1`
    # (exponente n de la primera relacion) quede IMPLICADA y no gaste holgura.
    # La regla de implicacion del pool se queda con la primera cota registrada.
    pool(n - 2)

    rel(n, nn, E)                    # E = n^(n-1)  -> mismo contexto que A y P
    rel(R, nn, A)                    # A = R^nn
    rel(sympy.Integer(2), R, T)      # T = 2^R
    rel(u + 1, R, W)                 # W = (u+1)^R
    rel(u, nn, P)                    # P = u^nn

    ineq = pool
    partes = [
        L_value(m, lambda v: sympy.factorial(int(n.subs(v)) - 1)),
        L_value(Ev, lambda v: int(n.subs(v)) ** (int(n.subs(v)) - 1) - 1),
        L_value(A, lambda v: int(R.subs(v)) ** (int(n.subs(v)) - 1)),
        L_value(Tv, lambda v: 2 ** int(R.subs(v)) - 1),
        L_value(W, lambda v: (int(u.subs(v)) + 1) ** int(R.subs(v))),
        L_value(P, lambda v: int(u.subs(v)) ** (int(n.subs(v)) - 1)),
        L_value(Q, lambda v: int(W.subs(v)) // int(P.subs(v))),
        L_value(B, lambda v: int(sympy.binomial(int(R.subs(v)), int(n.subs(v)) - 1))),
    ]
    # ORDEN: los contextos se construyen primero para que registren sus cotas en
    # la base, pero la base va ANTES en la conjuncion porque su testigo fija `a`
    # y los contextos lo LEEN.
    sistemas_ctx = [c.build() for c in contexts.values()]
    partes += [base.build()] + sistemas_ctx
    partes += [
        L_floor_div(W, P, Q, over_N=over_N),
        # ORDEN IMPORTANTE: Q - B - u*k = 0 (no B - Q - ...), porque Q >> B y asi
        # el multiplicador k queda >= 0. Con el orden inverso k es NEGATIVO y el
        # sistema deja de estar sobre N.
        L_congruent(Q, B, u),
        ineq(u - B - 1),
        L_floor_div(A, B, m, over_N=over_N),
        L_divides(n, m + 1),
        ineq(n - 2),
    ]
    system = conj(*partes, name=f"{n} es primo (Wilson, compartido)")

    inner = system.witness

    def w(vals):
        nv = int(n.subs(vals))
        if nv < 2 or not sympy.isprime(nv):
            return None
        return inner(vals)

    system.witness = w
    return system
