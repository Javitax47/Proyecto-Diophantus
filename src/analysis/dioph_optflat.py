"""
================================================================================
   DIOPHANTUS - APLANADO MINIMO POR OPTIMIZACION (con COTA INFERIOR demostrada)
================================================================================
Las heuristicas dicen "he encontrado 46". Esto dice "46 es el MINIMO, y aqui esta
la prueba". La diferencia importa: sin cota inferior no se sabe si merece la pena
seguir buscando o si el problema esta en otro sitio.

QUE SE OPTIMIZA. Aplanar es elegir que productos NOMBRAR para que ninguna
ecuacion pase de grado `target`. Restringido a nombrar MONOMIOS, es un problema
combinatorio exacto:

    variables:  x_t  para cada monomio t candidato ("t recibe un nombre")
    disponible(t) := grado(t) <= 1  OR  x_t
    para cada monomio m del sistema con grado > target:
        OR sobre las formas de partir m = t1*t2 de  disponible(t1) AND disponible(t2)
    para cada candidato t nombrado con grado >= 3: la misma condicion sobre t
    minimizar:  numero de x_t ciertos

Se resuelve con `z3.Optimize`, que da modelo Y cota inferior.

RESULTADOS MEDIDOS sobre el sistema de Jones-Sato-Wada-Wiens (1976):

| Punto de partida                | Nombres | Total | Generador | Cota |
|---------------------------------|---------|-------|-----------|------|
| original expandido              |      25 |    50 | (51, 5)   |   25 |
| tras `flatten_tree(S, 8)`       |      16 |    46 | (47, 5)   |   16 |
| JSWW 1976, a mano               |      16 |    41 | (42, 5)   |    - |
| forma factorizada, catalogo actual |   15 |    40 | (41, 5)   |   15 |
| ... y post-eliminando e, q, y   |         |    37 | (38, 5)   |      |
| con `a = A+2` y forzando definiciones |  16 |       |           |   16 |
| ... y post-eliminando e, q, y, z |        |    32 | **(33,5)**|      |

Y no es un punto suelto: `barrido_pareto` da la CURVA entera, cada punto con su
veredicto de equivalencia (0 faltan / 0 sobran):

    (33,5) (30,7) (27,9) (26,11) (25,13) (24,15) (23,25) [(22,29) (21,37)]

Los dos ultimos van entre corchetes: el (19,29) que JSWW anuncian los domina en
los dos ejes. Los cinco de en medio caen donde la literatura no tiene NADA --entre
el grado 5 y el 25 no hay ningun par publicado--, y el (25,13) y el (24,15)
dominan en LOS DOS EJES al (26,25) que JSWW si imprimieron.

TRES VECES SE CREYO QUE ESTO ESTABA EN EL OPTIMO, Y LAS TRES ERA EL CATALOGO.
Primero con monomios solos (46). Luego anadiendo los nodos del arbol (17). Y la
tercera vez el aviso fue aritmetico y no habia forma de discutirlo: JSWW pasan de
26 a 42 variables, o sea 16 nombres, y esta codificacion certificaba **17 como
COTA INFERIOR**. Una cota inferior por encima de una construccion publicada es
imposible; el imposible era del instrumento. Faltaban las SUBSUMAS --`g*k + k + 1`
dentro de `g*k + 2*g + k + 1`--, que no son nodos del arbol ni monomios de ningun
desarrollo y por tanto no estaban en ninguno de los dos espacios. Con ellas: 15.

LA LECCION, que vale mas que la cifra: la palabra `optimo_del_encoding` no es
pedanteria. Cada vez que el catalogo crece, el "optimo" baja. La unica cota que
significa algo aqui es la que un resultado imposible todavia no ha refutado.
"""

import itertools

import sympy

try:
    import z3
    Z3_DISPONIBLE = True
except ImportError:                                   # pragma: no cover
    z3 = None
    Z3_DISPONIBLE = False


def _monomios(system, target):
    """(generadores, monomios de grado > target, candidatos a nombrar)."""
    gens = list(system.params) + list(system.unknowns)
    objetivo = set()
    for e in system.eqs:
        try:
            poly = sympy.Poly(e, *gens)
        except (sympy.PolynomialError, sympy.GeneratorsNeeded):
            continue
        for expo in poly.monoms():
            if sum(expo) > target:
                objetivo.add(expo)
    candidatos = set()
    for m in objetivo:
        for dv in itertools.product(*[range(x + 1) for x in m]):
            if 2 <= sum(dv) <= sum(m):
                candidatos.add(dv)
    return gens, objetivo, candidatos


def _dividir(m, d):
    r = tuple(a - b for a, b in zip(m, d))
    return r if all(x >= 0 for x in r) else None


def aplanado_minimo(system, target=2, timeout_s=300):
    """Numero MINIMO de monomios que hay que nombrar, con cota inferior.

    Devuelve dict con `estado`, `nombres` (cuantos), `total` (incognitas
    resultantes), `cota` (inferior demostrada) y `elegidos` (los monomios).

    'optimo' solo se declara cuando el modelo alcanza la cota inferior. Si Z3 se
    queda sin tiempo, el resultado es una cota superior y una inferior, y se dice.
    """
    if not Z3_DISPONIBLE:
        return {"estado": "sin_z3"}
    gens, objetivo, candidatos = _monomios(system, target)
    if not objetivo:
        return {"estado": "optimo", "nombres": 0, "total": system.cost(),
                "cota": 0, "elegidos": []}

    x = {t: z3.Bool("n%d" % i) for i, t in enumerate(sorted(candidatos))}

    def disponible(t):
        if sum(t) <= 1:
            return z3.BoolVal(True)
        return x[t] if t in x else z3.BoolVal(False)

    def partir(m):
        opciones = []
        for d1 in itertools.product(*[range(a + 1) for a in m]):
            s1 = sum(d1)
            if s1 == 0 or s1 == sum(m):
                continue
            d2 = _dividir(m, d1)
            if d2 is None or s1 > sum(d2):
                continue
            opciones.append(z3.And(disponible(d1), disponible(d2)))
        return z3.Or(opciones) if opciones else z3.BoolVal(False)

    opt = z3.Optimize()
    opt.set("timeout", timeout_s * 1000)
    for m in objetivo:
        opt.add(partir(m))
    for t in candidatos:
        if sum(t) >= target + 1:
            opt.add(z3.Implies(x[t], partir(t)))
    objetivo_min = opt.minimize(z3.Sum([z3.If(x[t], 1, 0) for t in candidatos]))

    res = opt.check()
    if res != z3.sat:
        return {"estado": str(res), "nombres": None, "total": None,
                "cota": None, "elegidos": []}
    modelo = opt.model()
    elegidos = [t for t in sorted(candidatos) if z3.is_true(modelo.eval(x[t]))]
    try:
        cota = int(str(opt.lower(objetivo_min)))
    except (ValueError, TypeError):
        cota = None
    estado = "optimo" if cota is not None and cota == len(elegidos) else "cota_superior"
    return {"estado": estado, "nombres": len(elegidos),
            "total": system.cost() + len(elegidos), "cota": cota,
            "elegidos": [dict(zip([str(g) for g in gens], t)) for t in elegidos]}


# ---------------------------------------------------------------------------
#   APLANADO MINIMO SOBRE SUBEXPRESIONES COMPUESTAS (no solo monomios)
# ---------------------------------------------------------------------------

def _nodos(e, acc, sumas_parciales=False, tope_suma=6, productos_subsuma=False):
    """Todos los nodos del arbol de `e`, y los productos parciales de cada Mul.

    Los productos parciales hacen falta porque partir `f1*f2*f3` en dos grupos
    crea subexpresiones (`f1*f2`) que no son nodos del arbol original pero si
    candidatas a recibir nombre.

    `sumas_parciales` anade tambien las SUMAS parciales de cada Add (y de su
    forma desarrollada). Existe porque el catalogo se quedaba corto de forma
    demostrable: JSWW obtienen 42 variables a partir de 26, o sea 16 nombres, y
    esta codificacion certificaba 17 como COTA INFERIOR. Una cota inferior por
    encima de una construccion publicada solo puede significar que al catalogo le
    faltan candidatos. Los que faltaban son subsumas como `2*a*(n+1)` dentro de
    `2*a*n + 2*a - n**2 - 2*n - 2`, que no son nodos del arbol ni monomios de
    ningun desarrollo, y por tanto no estaban en ninguno de los dos espacios.
    """
    e = sympy.sympify(e)
    acc.add(e)
    if e.is_Add or e.is_Mul:
        for a in e.args:
            _nodos(a, acc, sumas_parciales, tope_suma)
    if sumas_parciales and e.is_Add:
        for forma in {e, sympy.expand(e)}:
            if not forma.is_Add:
                continue
            args = list(forma.args)
            if len(args) > tope_suma:
                continue
            for r in range(2, len(args)):
                for comb in itertools.combinations(range(len(args)), r):
                    acc.add(sympy.Add(*[args[i] for i in comb]))
    if productos_subsuma and e.is_Mul:
        # TERCER HUECO DEL CATALOGO, detectado por censo y no por intuicion: un
        # producto en el que UN FACTOR se sustituye por una de SUS subsumas. Ni es
        # nodo del arbol, ni monomio del desarrollo, ni subsuma de ningun Add del
        # sistema -- `(h+j)*(g*k+k+1)` dentro de `(g*k+2*g+k+1)*(h+j)` no estaba en
        # ninguno de los tres espacios anteriores. Medido: 111 expresiones asi
        # faltaban, 35 de ellas nombrables sin demostracion.
        coef, resto = e.as_coeff_Mul()
        fs = list(resto.args) if resto.is_Mul else [resto]
        if len(fs) <= 4:
            for idx, f in enumerate(fs):
                if not f.is_Add or len(f.args) > tope_suma:
                    continue
                args = list(f.args)
                for r in range(1, len(args)):
                    for comb in itertools.combinations(range(len(args)), r):
                        sub = sympy.Add(*[args[i] for i in comb])
                        acc.add(coef * sympy.Mul(
                            *[sub if i == idx else fs[i] for i in range(len(fs))]))
    if e.is_Mul:
        coef, resto = e.as_coeff_Mul()
        fs = list(resto.args) if resto.is_Mul else [resto]
        if 2 <= len(fs) <= 5:
            for r in range(2, len(fs)):
                for comb in itertools.combinations(range(len(fs)), r):
                    acc.add(sympy.Mul(*[fs[i] for i in comb]))
    if e.is_Pow:
        base, exp = e.args
        _nodos(base, acc)
        if exp.is_Integer and 2 <= int(exp) <= 8:
            for k in range(2, int(exp)):
                acc.add(base ** k)
    return acc


def _como_monomio(e, gens):
    """Vector de exponentes si `e` es un monomio sobre `gens`; None si no lo es.

    SEXTO DEFECTO DE ESTE ENCODING, y otra vez la misma causa raiz:
    `sympy.Poly(e, *gens)` NO falla cuando `e` contiene simbolos ajenos a `gens`
    --los trata como COEFICIENTES--. Con la ruta de reescritura activa aparecen
    marcadores de nombres dentro de las expresiones, y entonces `m4**2*a**2`
    devolvia el vector de `a**2`: la ruta monomial lo partia en `a|a` y
    certificaba grado 2 sobre algo que es de grado 4.

    Lo delato, como los cinco anteriores, un resultado imposible: el optimizador
    certificaba 16 nombres y el materializador construia grado 3 con esos mismos
    16. Comprobado a mano: `e^3(e+2)(a+1)^2 = m4^2*m5 + 2*e*m4*m5` con `m4 = e^2`
    y `m5 = (a+1)^2`, y no hay nombre para `e^3`; el grado 3 es inevitable. La
    cifra de 16 era falsa.

    Se exige explicitamente que no haya simbolos fuera de `gens`.
    """
    e = sympy.expand(e)
    if getattr(e, "is_number", False):
        return None
    if not (e.free_symbols <= set(gens)):
        return None
    try:
        poly = sympy.Poly(e, *gens)
    except (sympy.PolynomialError, sympy.GeneratorsNeeded):
        return None
    monoms = poly.monoms()
    return monoms[0] if len(monoms) == 1 else None


def _monomio_expr(expo, gens):
    m = sympy.Integer(1)
    for g, k in zip(gens, expo):
        m *= g ** k
    return m


def _monomio_lider(c, gens):
    """Monomio lider de `c` en grevlex, o None si no es polinomio en `gens`.

    Sirve de FILTRO EXACTO: la reduccion por la regla `c -> marca` dispara si y
    solo si algun monomio de `e` es divisible por este. Comprobarlo cuesta una
    comparacion de vectores de exponentes; llamar a `sympy.reduced` para
    descubrir que no dispara cuesta cuatro ordenes de magnitud mas. Con este
    filtro se puede quitar el tope de intentos y hacer la ruta COMPLETA.
    """
    try:
        poly = sympy.Poly(sympy.expand(c), *gens)
    except (sympy.PolynomialError, sympy.GeneratorsNeeded):
        return None
    monoms = poly.monoms(order='grevlex')
    return monoms[0] if monoms else None


def _puede_disparar(monoms_e, lm_c):
    """Algun monomio de `e` es divisible por el lider de `c`?"""
    if lm_c is None:
        return False
    for m in monoms_e:
        if all(a >= b for a, b in zip(m, lm_c)):
            return True
    return False


def _reescribir(e, c, gens, marca):
    """`e` reescrita como polinomio en `marca`, donde `marca` representa a `c`. O None.

    ESTE ES EL MECANISMO QUE FALTABA, y su ausencia mantuvo la brecha entre la
    cota certificable (21 nombres) y el aplanado exhibible (20).

    Las rutas anteriores --partir el arbol en grupos de factores, partir el vector
    de exponentes de un monomio, desarrollar-- comparten una limitacion: ninguna
    sabe **reescribir** una expresion en terminos de los nombres ya elegidos. Y
    hay casos donde no queda otra. Con `m = E^2` nombrado,

        E^3*(E+2)  =  E^4 + 2*E^3  =  m^2 + 2*m*E

    baja a grado 2, pero NO por ninguna particion de factores: `E^3*(E+2)` tiene
    factores [E,E,E,E+2] y ningun reparto en dos grupos deja ambos en grado 1.
    Hace falta la identidad algebraica.

    Se obtiene por reduccion polinomica con la regla `c -> marca`, orientada
    poniendo los generadores ANTES que la marca en grevlex: asi el termino
    principal de `c - marca` es `c`, y cada aparicion de `c` dentro de `e` se
    sustituye. Dividir con `sympy.div` NO sirve --se probo--: devuelve el cociente
    DESARROLLADO y vuelve a destruir la estructura que el nombre captura, que es
    la misma leccion de siempre apareciendo dentro de la propia ruta que se anadio
    para esquivarla.

    La identidad se COMPRUEBA antes de devolverla (`r|marca=c == e`): una
    reescritura mal orientada da un resto que no representa a `e`, y eso seria un
    aplanado que no preserva el sistema.
    """
    try:
        _, r = sympy.reduced(sympy.expand(e), [sympy.expand(c) - marca],
                             *(list(gens) + [marca]), order='grevlex')
    except (sympy.PolynomialError, sympy.GeneratorsNeeded, ValueError, TypeError):
        return None
    if marca not in r.free_symbols:
        return None                      # no se uso el nombre: no hay progreso
    if sympy.expand(r.subs(marca, c) - sympy.expand(e)) != 0:
        return None                      # la identidad no se sostiene
    return r


def _factores(e, limite=8):   # el tope de particiones lo pone quien llama
    """Factores de `e` con las POTENCIAS DESPLEGADAS: `E**3*(E+2)` -> [E,E,E,E+2].

    CUARTO BUG DE ESTE ENCODING, y del mismo tipo que los tres anteriores: lo
    delato un resultado imposible. Z3 "demostraba" cota inferior 21 para un
    sistema en el que existe --y se exhibe-- un aplanado de 20 nombres.

    La causa: `Mul.args` devuelve `(E**3, E+2)`, asi que la unica particion que se
    consideraba era `(E^3)|(E+2)`, nunca `(E*E)|(E*(E+2))`. Por eso no se veia que
    nombrando `E^2` la ecuacion definitoria `m = E^4+2E^3 = m6^2 + 2*m6*E` ya baja
    a grado 2. Una particion que no se genera no es una particion que no exista:
    el "optimo" era optimo del catalogo de opciones, no del problema.

    Devuelve el coeficiente numerico aparte, porque no afecta al grado.
    """
    coef, resto = e.as_coeff_Mul()
    brutos = list(resto.args) if resto.is_Mul else [resto]
    fs = []
    for f in brutos:
        if f.is_Pow and f.args[1].is_Integer and 0 < int(f.args[1]) <= limite:
            fs.extend([f.args[0]] * int(f.args[1]))
        else:
            fs.append(f)
    return coef, fs


def no_negativo_sobre_N(e):
    """`e >= 0` para toda asignacion de las variables en N, por ESTRUCTURA.

    Criterio SUFICIENTE, no necesario: devuelve False cuando no sabe. Recorre el
    ARBOL en vez de expandir, porque expandir pierde informacion -- por ejemplo
    `(a + u^2(u^2-a))^2` es un cuadrado y por tanto >= 0, pero su desarrollo tiene
    el monomio `-2a^2u^2` y el criterio de coeficientes lo rechazaria.

    Reglas: un simbolo esta en N; una suma o un producto de no negativos lo es;
    una potencia de exponente PAR lo es sea cual sea la base. Como respaldo se
    prueba tambien el criterio de coeficientes sobre el desarrollo, que atrapa
    casos como `(4dy+n)^2` escritos de otra forma.
    """
    e = sympy.sympify(e)
    if e.is_number:
        return bool(e >= 0)
    if e.is_Symbol:
        return True
    if e.is_Add or e.is_Mul:
        if all(no_negativo_sobre_N(t) for t in e.args):
            return True
    elif e.is_Pow:
        base, exp = e.args
        if exp.is_Integer and int(exp) >= 0:
            if int(exp) % 2 == 0 or no_negativo_sobre_N(base):
                return True
    try:
        pol = sympy.Poly(sympy.expand(e))
    except (sympy.PolynomialError, sympy.GeneratorsNeeded):
        return False
    return all(c >= 0 for c in pol.coeffs())


def aplanado_minimo_compuesto(system, target=2, timeout_s=600,
                              solo_no_negativos=False, demostrados=(),
                              reescritura=False, tope_reescritura=8,
                              excluir=(), sumas_parciales=True, semilla=None,
                              forzar=(), tope_suma=6, productos_subsuma=False):
    """Minimo numero de SUBEXPRESIONES a nombrar, no solo monomios.

    AVISO DE COHERENCIA, aprendido a base de romperlo dos veces: `reescritura`
    tiene que valer LO MISMO aqui y en `materializar`. Si el optimizador certifica
    un conjunto usando una regla que el materializador no tiene, el conjunto no se
    puede construir --error real: `no se pudo reducir a grado 2: q + s*(2ap+2a-
    p^2-2p-2) - x + y*(a-p-1)`-- y si la tiene el materializador pero no el
    optimizador, sale un sistema de grado mayor que el certificado. Un certificado
    solo vale para el juego de reglas con el que se emitio.

    Es la generalizacion que faltaba. `aplanado_minimo` demostro que 46 es el
    optimo nombrando monomios, y que JSWW llegan a 41 porque nombran cosas como
    `(a + u^2(u^2-a))^2` o `(n+4dy)^2`, que no son monomios de ningun desarrollo.
    Aqui el espacio de candidatos son los NODOS DEL ARBOL de cada ecuacion (mas
    los productos parciales de cada Mul y las potencias intermedias), y Z3 elige
    el subconjunto minimo.

    CODIFICACION. Para cada nodo `e` y cada presupuesto de grado d en {1, 2}:

        R[e][d]  :=  "e se puede escribir con grado <= d"
        R[e][d]  <-  grado(e) <= d                        (cierto de entrada)
        R[e][d]  <-  x_e                                  (nombrarlo lo baja a 1)
        e = Add  :  R[e][d]  <-  AND_i R[arg_i][d]        (una suma es el max)
        e = Mul  :  R[e][2]  <-  OR sobre particiones en dos grupos G1, G2
                                 de  R[prod G1][1] AND R[prod G2][1]
        e = Pow  :  se trata como el Mul de sus factores repetidos

    y por cada nodo nombrado se exige que su ECUACION DEFINITORIA tenga grado <= 2,
    con `R'` = lo mismo pero sin poder usar `x_e` para si mismo (no hay ciclos:
    R' de un nodo solo depende de R de nodos estrictamente menores).

    Objetivo: minimizar el numero de nombres. Devuelve el mismo dict que
    `aplanado_minimo`, con `estado` = 'optimo' solo si se alcanza la cota.

    `sumas_parciales` (por defecto SI): incluye en el catalogo las subsumas de
    cada Add. Medido sobre el sistema de JSWW: 17 nombres sin ellas, 15 con
    ellas, +7 s de tiempo. No es un ajuste fino sino la correccion de una laguna
    DEMOSTRABLE del catalogo: JSWW pasan de 26 a 42 variables, o sea 16 nombres,
    y esta codificacion certificaba 17 como COTA INFERIOR. Una cota inferior por
    encima de una construccion publicada es un resultado imposible, y como
    siempre en este modulo el imposible era del instrumento.

    `excluir`: conjuntos de nombres (listas de cadenas) ya obtenidos, que se
    PROHIBEN con una clausula de bloqueo para poder enumerar OTROS optimos del
    mismo tamano. Existe porque el optimo NO ES UNICO y el numero de nombres no
    es la cifra final: despues viene la post-eliminacion de incognitas
    originales, que el objetivo no puede ver. Dos aplanados de 17 nombres pueden
    admitir distinto numero de post-eliminaciones, asi que quedarse con el primer
    modelo que devuelva Z3 es dejar la cifra final al azar del solucionador.
    """
    if not Z3_DISPONIBLE:
        return {"estado": "sin_z3"}

    gens = list(system.params) + list(system.unknowns)

    # Un MARCADOR por candidato: el simbolo que lo representa cuando se reescribe
    # una expresion en terminos de el. Debe contar como GRADO 1, que es lo que
    # cuesta un nombre, y por eso entra en los generadores del calculo de grado.
    marca = {}

    cache_grado = {}

    def grado(e):
        # MEMOIZADO. Sin esto, `grado` disparaba 310.923 `expand` y 282.348 `Poly`
        # --el 39% del tiempo, mas que la propia reescritura-- porque el encoding
        # la llama por cada nodo, cada candidato y cada nivel de grado. Es la
        # optimizacion que hace viable la ruta completa; el resto eran sintomas.
        clave = sympy.srepr(e)
        if clave not in cache_grado:
            cache_grado[clave] = _grado_crudo(e)
        return cache_grado[clave]

    def _grado_crudo(e):
        e = sympy.expand(e)
        if getattr(e, "is_number", False):
            return 0
        try:
            # Los generadores se toman de la PROPIA expresion, no de la lista
            # global. Meter los ~600 marcadores en cada `Poly` hacia que calcular
            # un grado costase mas que resolver el problema: la funcion se llama
            # constantemente y el encoding dejaba de construirse. Todo simbolo
            # libre --generador original o marcador de un nombre-- cuenta 1, que
            # es justo lo que se quiere.
            libres = sorted(e.free_symbols, key=str)
            if not libres:
                return 0
            return sympy.Poly(e, *libres).total_degree()
        except (sympy.PolynomialError, sympy.GeneratorsNeeded):
            return 99

    cand = set()
    for e in system.eqs:
        _nodos(e, cand, sumas_parciales=sumas_parciales, tope_suma=tope_suma,
               productos_subsuma=productos_subsuma)
    # UNION DE LOS DOS ESPACIOS. Solo con nodos del arbol el optimo salia 51
    # variables, PEOR que la ruta arbol+monomios (47): faltaban monomios utiles
    # que no son nodos de ningun arbol (`a*n`, `k**2`, `l*p`...). Y solo con
    # monomios salia 51 desde el sistema original. Cada espacio ve lo que el otro
    # no; hay que darle a Z3 los dos y que elija.
    _, _, monomios = _monomios(system, target)
    for expo in monomios:
        mon = sympy.Integer(1)
        for g, k in zip(gens, expo):
            mon *= g ** k
        cand.add(mon)
    cand = {c for c in cand if grado(c) >= 2 and not getattr(c, "is_number", False)}
    if solo_no_negativos:
        # REQUISITO DEL GENERADOR, no cosmetica. Q = W*(1 - sum P^2) representa el
        # conjunto sobre variables NO NEGATIVAS. Cada nombre `m = expr` anade una
        # incognita que tambien vive en N, asi que la solucion original solo se
        # extiende si `expr >= 0` en ella. Nombrar una expresion que puede ser
        # negativa preserva la SOUNDNESS (toda solucion del aplanado lo es del
        # original) pero puede romper la COMPLETITUD: el elemento deja de emitirse.
        # Con este filtro la cifra resultante no depende de ninguna suposicion
        # sobre los valores concretos del testigo original.
        # `demostrados`: expresiones que el criterio ESTRUCTURAL rechaza pero
        # de las que existe una demostracion escrita. Se pasan por su forma de
        # texto para que quede constancia de CUAL se esta admitiendo y por que;
        # una lista vacia es la posicion por defecto, que no debe nada a nadie.
        cand = {c for c in cand
                if no_negativo_sobre_N(c) or str(c) in set(demostrados)}
    if not cand:
        return {"estado": "optimo_del_encoding", "nombres": 0, "total": system.cost(),
                "cota": 0, "elegidos": []}

    orden = sorted(cand, key=lambda c: (grado(c), sympy.count_ops(c), sympy.srepr(c)))
    x = {c: z3.Bool("c%d" % i) for i, c in enumerate(orden)}
    for i, c in enumerate(orden):
        marca[c] = sympy.Symbol("_m%d" % i)
    # Candidatos ordenados por grado DESCENDENTE: reescribir con el nombre mas
    # grande que encaje es lo que mas baja el grado.
    orden_reesc = sorted(orden, key=lambda c: -grado(c))
    # PRECOMPUTOS que hacen viable la ruta COMPLETA (sin tope de intentos):
    # el monomio lider de cada candidato --filtro exacto de si la regla dispara--
    # y el grado, ambos calculados UNA vez en vez de por cada nodo.
    # SOLO CANDIDATOS COMPUESTOS. Reescribir con un candidato que ya es un
    # MONOMIO no aporta nada: partir el vector de exponentes sobre los
    # generadores --la ruta monomial-- da exactamente las mismas reducciones. No
    # es una restriccion, es quitar trabajo duplicado; y es lo que hace viable la
    # version sin tope, porque los ~380 monomios candidatos eran casi toda la
    # ramificacion. Lo que la reescritura aporta en exclusiva son los candidatos
    # COMPUESTOS --los que contienen sumas--, que es justo donde el aplanado por
    # particion de factores se queda corto.
    orden_reesc = [c for c in orden_reesc if _como_monomio(c, gens) is None]
    # Candidatos que son SUMAS: los unicos que pueden encajar como subsuma.
    add_cand = [c for c in orden if c.is_Add]
    lider = {c: _monomio_lider(c, gens) for c in orden_reesc}
    grado_c = {c: grado(c) for c in orden_reesc}
    memo_reesc = {}

    def reescribir_memo(e, c):
        clave = (sympy.srepr(e), sympy.srepr(c))
        if clave not in memo_reesc:
            memo_reesc[clave] = _reescribir(e, c, gens, marca[c])
        return memo_reesc[clave]

    opt = z3.Optimize()
    opt.set("timeout", timeout_s * 1000)
    if semilla is not None:
        # DIVERSIFICAR ENTRE OPTIMOS, que no es lo mismo que bloquearlos: las
        # clausulas de `excluir` prohiben asignaciones concretas, la semilla mueve
        # la exploracion. Hace falta porque lo que se compara entre optimos NO es el
        # numero de nombres --todos empatan-- sino cuantas incognitas ORIGINALES
        # dejan eliminar despues, que el objetivo no puede ver.
        #
        # OJO: este bloque estuvo diez commits en `aplanado_minimo` por un
        # `replace(..., 1)` que pego en la primera coincidencia del fichero. Dos
        # consecuencias: `aplanado_minimo` reventaba con NameError (no tiene el
        # parametro), y aqui la semilla NUNCA se aplicaba -- asi que la medida
        # "cambiar la semilla no mueve nada" no medía nada. Octavo defecto de este
        # modulo, y el primero de esta clase: no un encoding mal pensado sino una
        # edicion que aterrizo en la funcion equivocada.
        opt.set("random_seed", int(semilla))

    # CODIFICACION TIPO TSEITIN. Una version anterior INLINEABA la formula
    # recursivamente y memoizaba la expresion z3; al entrar de nuevo en un nodo
    # que se estaba calculando devolvia la constante False, que quedaba CAPTURADA
    # en las formulas de los nodos que la habian consultado. Sintoma: 'unsat' en
    # un sistema y un optimo PEOR (20 nombres en vez de 16) en otro -- una
    # minimizacion no puede empeorar al anadir candidatos, asi que el encoding
    # estaba mal, no el problema.
    # Aqui cada par (nodo, presupuesto) recibe una VARIABLE booleana y su
    # definicion se ASSERTA. El grafo de dependencias es un DAG (las
    # subexpresiones son estrictamente menores), asi que no hay ciclos.
    var = {}
    pendientes = []

    def R(e, d, permitir_nombre=True):
        e = sympy.sympify(e)
        if grado(e) <= d:
            return z3.BoolVal(True)
        clave = (sympy.srepr(e), d, permitir_nombre)
        if clave in var:
            return var[clave]
        v = z3.Bool("r%d" % len(var))
        var[clave] = v
        pendientes.append((e, d, permitir_nombre, v))
        return v

    def opciones_de(e, d, permitir_nombre):
        ops = []
        # `d >= 1` NO es decorativo. Nombrar una subexpresion la convierte en una
        # incognita, que tiene GRADO 1; permitirlo cuando se pide grado 0 rompe el
        # contrato de esta funcion y el error se propaga hacia arriba. Era un bug
        # LATENTE: ninguna ruta pedia grado 0 hasta que llego la de sustitucion,
        # que si lo pide (`intentar(q, d-1)` con d=1). Sintoma: una unica ecuacion
        # de grado 3 --`16*m6*m9**2 - 16*m8*m9*r - u**2 + 1`-- en un sistema que
        # deberia quedar en 2, y con ella un generador de grado 7 en vez de 5.
        if permitir_nombre and d >= 1 and e in x:
            ops.append(x[e])
        if e.is_Add:
            ops.append(z3.And(*[R(a, d) for a in e.args]))
        ex = sympy.expand(e)
        if ex != e and ex.is_Add and len(ex.args) <= 60:
            ops.append(z3.And(*[R(a, d) for a in ex.args]))
        # RUTA DE SUBSUMA. Si un candidato `c` es una suma cuyos sumandos son un
        # SUBCONJUNTO de los de `e`, nombrarlo deja `e = m_c + resto`, y basta
        # reducir el resto. Sin esta regla los candidatos de `sumas_parciales` se
        # anadian al catalogo pero eran INUTILIZABLES, y el optimo no se movia --
        # que es exactamente el sintoma que tendria un catalogo enriquecido de
        # verdad pero inutil. Es la regla espejo de la de `_intentar_crudo`.
        # GUARDA `d >= 1`, la misma que ya fallo una vez (defecto 5): un nombre es
        # una incognita de GRADO 1, asi que esta ruta no puede usarse cuando se
        # pide grado 0. Y NO se condiciona a `permitir_nombre`: ese flag prohibe
        # nombrar `e` a si mismo, no usar OTRO nombre; exigirlo aqui haria al
        # optimizador mas estricto que al materializador -- o al reves-- y esa
        # pareja desalineada ya ha roto la cadena dos veces.
        if d >= 1:
            for forma in ([e] if e.is_Add else []) + ([ex] if ex.is_Add and ex is not e else []):
                args_e = set(forma.args)
                if len(args_e) > 60:
                    continue
                for c in add_cand:
                    args_c = set(c.args)
                    if c is e or not (args_c < args_e):
                        continue
                    resto = sympy.Add(*(args_e - args_c))
                    ops.append(z3.And(x[c], R(resto, d)))
        # RUTA MONOMIAL: si el nodo desarrollado es UN monomio, hay que partir su
        # VECTOR DE EXPONENTES, no sus factores sintacticos. Sin esto, `a**2*y**2`
        # solo se partia como (a^2)*(y^2) --dos nombres-- y no como (a*y)*(a*y),
        # que resuelve `(a^2-1)y^2 + 1 - x^2` con UNO. Fue lo que delato que el
        # encoding fallaba: nuestro "optimo" (21) era MAYOR que las 16 de JSWW, y
        # su metodo es mecanico, luego su cifra tiene que ser una cota SUPERIOR.
        expo = _como_monomio(ex, gens)
        # GUARDA `d >= 2`, imprescindible: partir en dos factores da grado 2, no 1.
        # Sin ella el encoding declaraba `k**2` reducible a grado 1 partiendolo en
        # k*k, y entonces TODO era satisfacible con cero nombres. Otro resultado
        # imposible que delata el instrumento.
        if expo is not None and sum(expo) > d and d >= 2:
            for d1 in itertools.product(*[range(a + 1) for a in expo]):
                s1 = sum(d1)
                if s1 == 0 or s1 == sum(expo):
                    continue
                d2 = _dividir(expo, d1)
                if d2 is None or s1 > sum(d2):
                    continue
                ops.append(z3.And(R(_monomio_expr(d1, gens), 1),
                                  R(_monomio_expr(d2, gens), 1)))
        if e.is_Mul or e.is_Pow:
            _, fs = _factores(e)          # potencias DESPLEGADAS: ver _factores
            if len(fs) == 1:
                # un solo factor no constante: el coeficiente no cambia el grado
                ops.append(R(fs[0], d))
            # TOPE 6, y con motivo medido: desplegar potencias alarga `fs`, y las
            # particiones son 2^len(fs). Subirlo a 8 multiplico por ~4 el tamano
            # del encoding y llevo un test de 10 s a varios minutos, sin mejorar
            # ninguna cifra. La correccion estaba en desplegar; el tope se queda.
            elif fs and d >= 2 and len(fs) <= 6:
                for r in range(1, len(fs)):
                    for comb in itertools.combinations(range(len(fs)), r):
                        g1 = sympy.Mul(*[fs[i] for i in comb])
                        g2 = sympy.Mul(*[fs[i] for i in range(len(fs)) if i not in comb])
                        ops.append(z3.And(R(g1, 1), R(g2, 1)))
        # RUTA DE SUSTITUCION: usar un nombre ya elegido como GENERADOR NUEVO.
        # RUTA DE REESCRITURA: expresar `e` como polinomio en un nombre elegido.
        # Es la que faltaba, y su ausencia mantenia la brecha entre la cota que se
        # sabia certificar (21 nombres) y el aplanado que se sabia exhibir (20):
        # `E^3*(E+2)` con `E^2` nombrado baja a grado 2 por la identidad
        # `m^2 + 2*m*E`, y ninguna particion de factores llega a eso.
        if reescritura and d >= 1 and ops is not None:
            gd = grado(e)
            fs_e = e.free_symbols
            # EL TOPE CUENTA INTENTOS, NO EXITOS. Contando exitos, un nodo para el
            # que casi ningun candidato encaja escaneaba los ~600 y llamaba a
            # `sympy.reduced` en cada uno: construir el encoding no terminaba en
            # 40 minutos. Con el tope sobre intentos el coste queda acotado de
            # verdad, a cambio de que la ruta sea INCOMPLETA -- y eso hay que
            # decirlo, porque significa que la cota resultante sigue siendo del
            # encoding y no del problema.
            # RUTA COMPLETA: se prueban TODOS los candidatos que pueden disparar.
            # Antes habia un tope de intentos --y con el, la cota seguia siendo del
            # encoding--. Se ha podido quitar porque el filtro por monomio lider es
            # EXACTO: la regla `c -> marca` dispara si y solo si algun monomio de
            # `e` es divisible por el lider de `c`. Comprobarlo cuesta comparar
            # vectores de exponentes; descubrirlo llamando a `sympy.reduced` costaba
            # cuatro ordenes de magnitud mas, y era lo que obligaba al tope.
            # NO reescribir lo ya reescrito. `sympy.Poly(expr, *gens)` NO falla
            # cuando `expr` contiene un marcador: lo trata como COEFICIENTE. Por
            # eso la ruta se re-aplicaba a sus propios resultados sin fondo --7.215
            # llamadas en 100 s sin terminar de construir el encoding-- y ademas el
            # test de divisibilidad sobre esos monomios no significaba lo que
            # parecia. Limitar a una reescritura por rama corta el arbol y deja la
            # regla con la semantica que se penso.
            if any(m in e.free_symbols for m in marca.values()):
                monoms_e = []
            else:
                try:
                    monoms_e = sympy.Poly(sympy.expand(e), *gens).monoms(order='grevlex')
                except (sympy.PolynomialError, sympy.GeneratorsNeeded):
                    monoms_e = []
            for c in orden_reesc:
                if c is e or not (c.free_symbols <= fs_e):
                    continue
                if not (2 <= grado_c[c] <= gd):
                    continue
                if not _puede_disparar(monoms_e, lider[c]):
                    continue
                r = reescribir_memo(e, c)
                if r is None or grado(r) >= gd:
                    continue          # sin progreso: la recursion no terminaria
                ops.append(z3.And(x[c], R(r, d)))
        return z3.Or(ops) if ops else z3.BoolVal(False)

    raiz = [R(e, target) for e in system.eqs]
    for c in orden:
        opt.add(z3.Implies(x[c], R(c, target, permitir_nombre=False)))
    while pendientes:
        e, d, pn, v = pendientes.pop()
        opt.add(v == opciones_de(e, d, pn))
    for r in raiz:
        opt.add(r)
    # CLAUSULAS DE BLOQUEO. Empezaron prohibiendo la asignacion COMPLETA ya vista
    # --lo conservador: no descartar ningun optimo legitimo-- y no servian para
    # nada: Z3 respondia con otra asignacion casi identica y diez iteraciones
    # seguidas daban el MISMO resultado final. Cambiar la semilla tampoco movio
    # nada.
    #
    # Aqui se exige algo mas fuerte: que el conjunto nuevo **omita al menos uno**
    # de los candidatos de cada conjunto ya visto. Eso SI puede saltarse optimos
    # (un conjunto que use todos los de uno anterior mas otros distintos queda
    # excluido), y por eso hay que decirlo: la enumeracion es una FUENTE DE
    # DIVERSIDAD, no un recorrido exhaustivo. La cifra que sale sigue siendo una
    # cota superior --construida y verificada-- y nunca se presenta como minimo.
    for prohibido in excluir:
        prohibido = set(prohibido)
        usados = [c for c in orden if str(c) in prohibido]
        if usados:
            opt.add(z3.Or(*[z3.Not(x[c]) for c in usados]))

    # `forzar`: candidatos que DEBEN nombrarse. No es para ayudar al optimizador
    # --el objetivo ya sabe minimizar-- sino para alcanzar aplanados que valen mas
    # de lo que el objetivo puede medir. Caso concreto y reproducible: si se nombra
    # `(g*k+2*g+k+1)*(h+j)+h`, la ecuacion (2) queda `m - z = 0` y entonces `z` se
    # post-elimina sustituyendola por UN SIMBOLO, sin subir el grado. Sin ese
    # nombre, sustituir `z` mete una expresion de grado 3 y la eliminacion se cae.
    # El objetivo no ve nada de esto: cuenta nombres con las originales congeladas.
    for c in orden:
        if str(c) in set(forzar):
            opt.add(x[c])

    objetivo_min = opt.minimize(z3.Sum([z3.If(x[c], 1, 0) for c in orden]))

    res = opt.check()
    if res != z3.sat:
        return {"estado": str(res), "nombres": None, "total": None,
                "cota": None, "elegidos": []}
    modelo = opt.model()
    elegidos = [c for c in orden if z3.is_true(modelo.eval(x[c]))]
    try:
        cota = int(str(opt.lower(objetivo_min)))
    except (ValueError, TypeError):
        cota = None
    # "optimo_del_encoding", NO "optimo". La distincion no es pedanteria: se
    # exhibio un CONTRAEJEMPLO. Sobre el sistema de JSWW con `e` eliminada, esta
    # funcion devuelve cota inferior 21 y existe un aplanado de 20 nombres,
    # construido a mano y comprobado (grado 2 por ecuacion). Luego el numero que
    # sale de `opt.lower()` es una cota inferior de ESTA CODIFICACION --de su
    # catalogo de candidatos y de las particiones que sabe generar-- y no del
    # problema de aplanado. Llamarlo "optimo" a secas llevo a escribir en un test
    # que "aplanar mejor es IMPOSIBLE", que es falso.
    #
    # Ademas el objetivo minimiza NOMBRES con las incognitas originales
    # CONGELADAS: no puede ni representar "eliminar una incognita", que es
    # justamente la jugada que baja de 46 a 44 variables (ver dioph_jsww).
    estado = ("optimo_del_encoding" if cota is not None and cota == len(elegidos)
              else "cota_superior")
    return {"estado": estado, "nombres": len(elegidos),
            "total": system.cost() + len(elegidos), "cota": cota,
            "elegidos": [str(c) for c in elegidos]}


def materializar(system, elegidos, target=2, name=None, reescritura=False):
    """Construye el sistema REAL a partir del conjunto de nombres que eligio Z3.

    El optimizador devuelve un NUMERO y un conjunto; eso no es un sistema. Sin
    materializar no se puede (a) comprobar que el grado baja de verdad, (b) contar
    las incognitas EFECTIVAMENTE usadas --alguna original puede quedar sin
    aparecer tras las sustituciones-- ni (c) verificar equisatisfacibilidad con
    testigos. Una cifra sin sistema es un numero de un solucionador, no un
    resultado.

    `elegidos` son las subexpresiones a nombrar (las mismas que devuelve
    `aplanado_minimo_compuesto`, como expresiones sympy o cadenas).
    """
    gens = list(system.params) + list(system.unknowns)

    cache_grado = {}
    marcadores = set()

    def grado(e):
        # MEMOIZADO por el mismo motivo que en el optimizador: sin cache, la ruta
        # de reescritura no llegaba a materializar el sistema completo. `grado` se
        # llama por cada nodo y cada candidato, y cada llamada hacia `expand` +
        # `Poly`.
        clave = sympy.srepr(e)
        if clave not in cache_grado:
            cache_grado[clave] = _grado_crudo(e)
        return cache_grado[clave]

    def _grado_crudo(e):
        e = sympy.expand(e)
        if getattr(e, "is_number", False):
            return 0
        try:
            return sympy.Poly(e, *(gens + list(nombres.values()))).total_degree()
        except (sympy.PolynomialError, sympy.GeneratorsNeeded):
            return 99

    # OJO CON LOS SIMBOLOS: `sympify("g*k")` crea variables SIN la hipotesis
    # `integer=True`, y en sympy `Symbol('k')` no es `Symbol('k', integer=True)`.
    # Sin pasar el diccionario de locales, los nombres elegidos no casan con los
    # del sistema y la reduccion falla con un "no se pudo reducir" enganoso.
    locales = {str(g): g for g in gens}
    elegidos = [sympy.sympify(c, locals=locales) if isinstance(c, str) else c
                for c in elegidos]
    clave_elegidos = {sympy.srepr(sympy.expand(c)): c for c in elegidos}
    nombres = {}
    defs = []
    # Orden por grado descendente: dividir primero por lo mas grande tiende a
    # dejar cociente y resto pequenos, que es lo que hace terminar la recursion.
    # (Va DESPUES de `nombres`, que es lo que consulta `grado`.)
    elegidos_expr = sorted(elegidos, key=lambda c: -grado(c))

    def simbolo(c):
        k = sympy.srepr(sympy.expand(c))
        if k not in nombres:
            w = sympy.Symbol("m%d" % (len(nombres) + 1), integer=True)
            nombres[k] = w
            marcadores.add(w)
            defs.append((w, c))
        return nombres[k]

    # PRECOMPUTOS de la ruta de reescritura: orden, grado y monomio lider de cada
    # candidato, UNA vez. Recalcularlos por nodo construia un `Poly` por candidato
    # y llamada, y era lo que impedia materializar el sistema completo.
    reesc_orden = sorted(elegidos, key=lambda t: -grado(t))
    reesc_grado = {c: grado(c) for c in reesc_orden}
    reesc_lider = {c: _monomio_lider(c, gens) for c in reesc_orden}
    elegidos_add = sorted([c for c in elegidos if c.is_Add],
                          key=lambda t: (-grado(t), -len(t.args)))

    cache_intentar = {}

    profundidad = [0]

    def intentar(e, d, permitir_nombre=True, prohibida=None):
        """Reduce `e` a grado <= d, o devuelve None si no puede.

        Devolver None en vez de lanzar es lo que permite PROBAR una particion y,
        si no sale, seguir con la siguiente. Una version anterior lanzaba dentro
        del bucle y abortaba la busqueda en la primera rama muerta, con un mensaje
        enganoso ("no se pudo reducir k**3") sobre una particion que simplemente
        no era la buena.

        MEMOIZADA, y es lo que hace converger la busqueda con reescritura activa.
        El backtracking re-exploraba las MISMAS ramas fallidas desde particiones
        distintas: sin cache, materializar el conjunto de 16 nombres no terminaba
        en mas de ocho minutos. Es sound porque `intentar` es determinista --el
        conjunto de candidatos esta fijado al entrar-- y porque su unico efecto
        lateral, crear el simbolo de un nombre, es idempotente.
        """
        e = sympy.sympify(e)
        clave_memo = (sympy.srepr(e), d, permitir_nombre, prohibida)
        if clave_memo in cache_intentar:
            return cache_intentar[clave_memo]
        # TOPE DE PROFUNDIDAD, y el motivo no es cosmetico. Al prohibir que una
        # definicion se nombre a si misma, el cuerpo de algunos nombres deja de
        # tener CUALQUIER reduccion a grado 2 y la busqueda no termina: la
        # autorreferencia era lo que la cortaba, dando una ecuacion `w - w` que
        # expandia a cero. Sin tope eso es un RecursionError; con tope es un
        # fracaso limpio, que es lo que debe ser -- el conjunto de nombres que
        # certifico el optimizador NO se puede materializar, y hay que descartarlo
        # en vez de construir un sistema falso.
        if profundidad[0] > 220:
            return None
        profundidad[0] += 1
        try:
            r = _intentar_crudo(e, d, permitir_nombre, prohibida)
        finally:
            profundidad[0] -= 1
        cache_intentar[clave_memo] = r
        return r

    def _intentar_crudo(e, d, permitir_nombre=True, prohibida=None):
        # `prohibida` es la CLAVE de la expresion que se esta definiendo. Ninguna
        # ruta puede devolver su nombre, o la ecuacion definitoria saldria `w - w`,
        # que expande a cero y deja el nombre suelto. El booleano `permitir_nombre`
        # solo cubria la ruta directa: las de subsuma y REESCRITURA se anadieron
        # despues y no lo consultaban. Ese fue el noveno defecto, y costo cuatro
        # cifras -- (41,5), (38,5), (36,5) y (33,5).
        def usable(cand):
            return prohibida is None or sympy.srepr(sympy.expand(cand)) != prohibida
        if grado(e) <= d:
            return e
        k = sympy.srepr(sympy.expand(e))
        # Mismo `d >= 1` que en el optimizador, y por el mismo motivo: un nombre
        # es una incognita de grado 1, no de grado 0.
        if permitir_nombre and d >= 1 and k in clave_elegidos and k != prohibida:
            return simbolo(clave_elegidos[k])
        if e.is_Add:
            partes = [intentar(a, d, prohibida=prohibida) for a in e.args]
            if all(p is not None for p in partes):
                return sympy.Add(*partes)
        ex = sympy.expand(e)
        if ex != e and ex.is_Add:
            partes = [intentar(a, d, prohibida=prohibida) for a in ex.args]
            if all(p is not None for p in partes):
                return sympy.Add(*partes)
        # REGLA ESPEJO de la ruta de subsuma del optimizador. Tiene que estar en
        # los dos sitios y con el mismo criterio: un certificado solo vale para el
        # juego de reglas con el que se emitio, y esta pareja ya se rompio dos
        # veces en las dos direcciones (ver el aviso de coherencia de
        # `aplanado_minimo_compuesto`).
        if d >= 1:
            for forma in ([e] if e.is_Add else []) + ([ex] if ex.is_Add and ex is not e else []):
                args_e = set(forma.args)
                for c in elegidos_add:
                    args_c = set(c.args)
                    if not (args_c < args_e) or not usable(c):
                        continue
                    r = intentar(sympy.Add(*(args_e - args_c)), d, prohibida=prohibida)
                    if r is not None:
                        return simbolo(c) + r
        expo = _como_monomio(ex, gens)
        if expo is not None and d >= 2:
            for d1 in itertools.product(*[range(a + 1) for a in expo]):
                s1 = sum(d1)
                if s1 == 0 or s1 == sum(expo):
                    continue
                d2 = _dividir(expo, d1)
                if d2 is None or s1 > sum(d2):
                    continue
                r1 = intentar(_monomio_expr(d1, gens), 1, prohibida=prohibida)
                if r1 is None:
                    continue
                r2 = intentar(_monomio_expr(d2, gens), 1, prohibida=prohibida)
                if r2 is None:
                    continue
                coef = sympy.expand(ex / _monomio_expr(expo, gens))
                return coef * r1 * r2
        if e.is_Mul or e.is_Pow:
            coef, fs = _factores(e)       # la MISMA laguna estaba aqui: sin esto
            if len(fs) == 1:              # el materializador no sabe construir el
                                          # sistema que el optimizador ya eligio
                r = intentar(fs[0], d, prohibida=prohibida)
                if r is not None:
                    return coef * r
            elif fs and d >= 2:
                for r in range(1, len(fs)):
                    for comb in itertools.combinations(range(len(fs)), r):
                        g1 = sympy.Mul(*[fs[i] for i in comb])
                        g2 = sympy.Mul(*[fs[i] for i in range(len(fs)) if i not in comb])
                        r1 = intentar(g1, 1, prohibida=prohibida)
                        if r1 is None:
                            continue
                        r2 = intentar(g2, 1, prohibida=prohibida)
                        if r2 is None:
                            continue
                        return coef * r1 * r2
        # RUTA DE REESCRITURA: expresar `e` como polinomio en un nombre ya
        # elegido. Es la unica que resuelve casos como `E^3*(E+2)` con `E^2`
        # nombrado, donde ninguna particion de factores deja los dos grupos en
        # grado 1 y hace falta la identidad `E^3(E+2) = m^2 + 2*m*E`.
        #
        # Sustituye a un intento anterior basado en `sympy.div`, que devolvia el
        # cociente DESARROLLADO y volvia a destruir la estructura que el nombre
        # captura. `_reescribir` reduce con la regla `c -> marca` y comprueba la
        # identidad antes de devolverla.
        # OPT-IN, y por una razon medida: activarla deja de terminar sobre el
        # sistema completo de JSWW (>20 min sin materializar, frente a ~20 s por
        # el camino de siempre). La ruta es CORRECTA --resuelve el caso que
        # ninguna otra sabe hacer-- pero explora demasiado. Mientras siga asi, la
        # cifra publicada sale del camino rapido y verificado; se activa para los
        # sistemas pequenos donde hace falta. Un atajo que no puedo ejecutar no
        # entra en la cifra.
        if reescritura and d >= 1:
            gd = grado(e)
            fs_e = e.free_symbols
            # Candidatos por grado DESCENDENTE y filtrados antes de llamar a
            # `_reescribir`, que es caro. Sin esto, materializar el sistema de
            # JSWW no terminaba: se reducia con candidatos triviales primero y
            # se reintentaba el trabajo caro una y otra vez.
            # MISMO FILTRO EXACTO que en el optimizador: la regla `c -> marca`
            # dispara si y solo si algun monomio de `e` es divisible por el lider
            # de `c`. Sin el, el materializador llamaba a `sympy.reduced` por cada
            # par y no terminaba de construir el sistema completo.
            if any(m in e.free_symbols for m in marcadores):
                monoms_e = []
            else:
                try:
                    monoms_e = sympy.Poly(sympy.expand(e), *gens).monoms(order='grevlex')
                except (sympy.PolynomialError, sympy.GeneratorsNeeded):
                    monoms_e = []
            if not monoms_e:
                return None
            for c in reesc_orden:
                if c is e or not (c.free_symbols <= fs_e):
                    continue
                gc = reesc_grado[c]
                if gc < 2 or gc > gd or sympy.expand(c - e) == 0:
                    continue
                if not _puede_disparar(monoms_e, reesc_lider[c]):
                    continue
                nc = intentar(c, 1, prohibida=prohibida)
                if nc is None:
                    continue
                r = _reescribir(e, c, gens, nc)
                if r is None or grado(r) >= gd:
                    continue          # sin progreso: la recursion no terminaria
                if grado(r) <= d:
                    return r
                rr = intentar(r, d)
                if rr is not None:
                    return rr
        return None

    def reducir(e, d, permitir_nombre=True, prohibida=None):
        r = intentar(e, d, permitir_nombre, prohibida=prohibida)
        if r is None:
            raise ValueError(f"no se pudo reducir a grado {d}: {e}")
        return r

    eqs = [sympy.expand(reducir(e, target)) for e in system.eqs]
    definitorias = []
    i = 0
    while i < len(defs):
        w, c = defs[i]
        # GUARDA DEL NOVENO DEFECTO, y es el mas caro de los nueve.
        #
        # `permitir_nombre=False` existe para que la definitoria de `w` no se
        # exprese usando `w`. Las rutas de SUBSUMA y de REESCRITURA no consultaban
        # ese flag --se anadieron despues-- asi que `reducir(c)` podia devolver el
        # propio `w`, y entonces la ecuacion emitida era `w - w`, que expande a
        # CERO. El nombre quedaba sin ninguna ecuacion que lo atara.
        #
        # Consecuencia: el sistema resultante es ESTRICTAMENTE MAS DEBIL que el
        # original --tiene soluciones que el original no tiene-- y ademas la
        # incognita original que solo aparecia ahi desaparece del sistema. Medido:
        # forzando el nombre `h + (h+j)(gk+2g+k+1)` se perdian CINCO definitorias,
        # desaparecian `g` y `r`, y con ellas las ecuaciones (2) y (7) enteras.
        #
        # Y lo peor: `verificar_equivalencia` seguia dando 0 faltan / 0 sobran,
        # porque es una identidad polinomica --sustituye por la definicion-- y no
        # comprueba que el sistema IMPONGA esa definicion. Dos comprobaciones que
        # se creian independientes fallaban juntas.
        # La CLAVE PROHIBIDA viaja por todas las llamadas recursivas. El booleano
        # `permitir_nombre` solo protegia la llamada de primer nivel: en cuanto la
        # reduccion recurria --sobre los sumandos, sobre los factores, sobre el
        # resto de una reescritura-- el flag se perdia y la rama directa volvia a
        # poder nombrar la propia expresion que se estaba definiendo. De ahi salia
        # `w - w`.
        cuerpo = reducir(c, target, permitir_nombre=False,
                         prohibida=sympy.srepr(sympy.expand(c)))
        ecuacion = sympy.expand(w - cuerpo)
        if ecuacion == 0:
            raise ValueError(
                f"la ecuacion definitoria de {w} colapsa a 0 = 0: su cuerpo se "
                f"redujo a si mismo ({w} = {cuerpo}). El nombre quedaria libre y el "
                f"sistema seria mas debil que el original. Definicion: {c}")
        eqs.append(ecuacion)
        # SE GUARDA EL CUERPO REDUCIDO, no solo la expresion original que el nombre
        # representa. Son cosas distintas: la ecuacion que va al sistema es
        # `w - reducir(c)`, y `reducir` sustituye subexpresiones por OTROS nombres.
        # La comprobacion estructural --¿existe en el sistema la ecuacion que ata
        # `w`?-- tiene que mirar lo que se emitio, no lo que se pretendia.
        definitorias.append((w, cuerpo))
        i += 1

    # Y la comprobacion estructural, que no depende de como se hayan expresado las
    # definitorias: si una incognita ORIGINAL desaparece de todas las ecuaciones,
    # la ecuacion que la contenia se ha perdido.
    vistas = set()
    for e in eqs:
        vistas |= e.free_symbols
    huerfanas = [u for u in system.unknowns
                 if u not in vistas and any(u in e.free_symbols for e in system.eqs)]
    if huerfanas:
        raise ValueError(
            f"estas incognitas originales desaparecen del sistema materializado: "
            f"{sorted(map(str, huerfanas))}. Las ecuaciones que las contenian se han "
            f"perdido y el sistema no equivale al original.")

    usadas = set()
    for e in eqs:
        usadas |= e.free_symbols
    incognitas = [u for u in system.unknowns if u in usadas]
    incognitas += [w for _, w in sorted(((str(k), v) for k, v in nombres.items()))]

    def w_ext(param_vals):
        if system.witness is None:
            return None
        base = system.witness(param_vals)
        if base is None:
            return None
        asign = dict(param_vals); asign.update(base)
        out = {u: v for u, v in base.items() if u in usadas}
        for k in sorted(nombres, key=lambda z: str(nombres[z])):
            w = nombres[k]
            val = int(sympy.expand(sympy.sympify(k)).subs(asign))
            asign[w] = val
            out[w] = val
        return out

    salida = Dioph(list(system.params), incognitas, eqs, witness=w_ext,
                   name=name or f"{system.name} [optimo materializado]")
    # Se exponen las DEFINICIONES (nombre, expresion original que representa).
    # Re-derivarlas leyendo las ecuaciones --buscando una incognita nueva que
    # aparezca linealmente con coeficiente 1-- funciona mientras cada ecuacion
    # definitoria mencione un solo nombre, y deja de funcionar en cuanto la
    # reescritura hace que una definicion se exprese en terminos de OTROS
    # nombres. Quien las conoce sin ambiguedad es quien las creo.
    salida.definiciones = [(w, sympy.sympify(k)) for k, w in nombres.items()]
    salida.definitorias = definitorias
    return salida


def verificar_estructura(materializado):
    """¿Cada nombre nuevo esta REALMENTE ATADO a su definicion por una ecuacion?

    ESTA ES LA COMPROBACION QUE FALTABA Y QUE COSTO CUATRO CIFRAS. La de abajo
    (`verificar_equivalencia`) es una IDENTIDAD POLINOMICA: sustituye cada nombre
    por su definicion y mira si reaparecen las originales. Esa sustitucion la hace
    ELLA, con el diccionario de definiciones -- no comprueba que el SISTEMA la
    imponga. Si la ecuacion definitoria de `w` se perdio (o colapso a `0 = 0`), la
    identidad sigue cuadrando y el sistema publicado es ESTRICTAMENTE MAS DEBIL
    que el original: `w` queda libre.

    DOS LISTAS, Y NO SON LA MISMA. `definiciones` dice que EXPRESION ORIGINAL
    representa cada nombre; `definitorias` dice que CUERPO REDUCIDO se emitio
    realmente en la ecuacion, y ese cuerpo puede mencionar otros nombres. Mirar la
    primera donde habia que mirar la segunda hace que la comprobacion rechace
    sistemas correctos: fue el primer resultado de esta funcion y era suyo el
    error, no del sistema.

    CUATRO CONDICIONES. Juntas dan una biyeccion entre conjuntos de soluciones;
    ninguna sobra:

      1. Cada nombre `w` con cuerpo emitido `r` tiene EN EL SISTEMA una ecuacion
         igual a `+-(w - r)`, y se empareja 1 A 1 (dos nombres no pueden reclamar
         la misma ecuacion).
      2. `w` no aparece en `r`. Sin esto `w - r` puede expandir a 0 -- que es
         exactamente como se colo el noveno defecto.
      3. El grafo de dependencias entre nombres es ACICLICO. Con un ciclo
         `w1 = f(w2)`, `w2 = g(w1)` las dos ecuaciones existen y ninguna es
         autorreferente, pero el par no determina nada: la sustitucion hacia atras
         no termina.
      4. Desplegando `r` hasta punto fijo se recupera la expresion original que el
         nombre dice representar. Esto ata las dos listas: sin ello, `w` estaria
         bien determinado pero por OTRA cosa, y la identidad polinomica de abajo
         --que usa `definiciones`-- estaria hablando de un sistema distinto.

    Con las cuatro, cada nombre queda determinado por las originales en orden
    topologico, y anadirlos no cambia la satisfacibilidad.
    """
    declaradas = {w: sympy.expand(c)
                  for w, c in getattr(materializado, "definiciones", [])}
    # `definitorias` es lo que se emitio; si no esta (sistemas antiguos), lo unico
    # que hay es la definicion declarada, y entonces 1 y 4 coinciden.
    emitidas = list(getattr(materializado, "definitorias", None)
                    or list(declaradas.items()))
    ecs = [sympy.expand(e) for e in materializado.eqs]
    nombres = set(declaradas) | {w for w, _ in emitidas}

    autorreferentes, sin_ecuacion = [], []
    libres = list(range(len(ecs)))
    cuerpos = {}
    for w, r in emitidas:
        r = sympy.expand(r)
        cuerpos[w] = r
        if w in r.free_symbols:
            autorreferentes.append(str(w))
            continue
        objetivo = sympy.expand(w - r)
        for i in list(libres):
            if ecs[i] - objetivo == 0 or ecs[i] + objetivo == 0:
                libres.remove(i)
                break
        else:
            sin_ecuacion.append(str(w))

    # ACICLICIDAD por eliminacion repetida de fuentes (Kahn). Lo que sobra al
    # final es exactamente el conjunto de nombres metidos en algun ciclo.
    pendientes = {w: (r.free_symbols & nombres) - {w} for w, r in cuerpos.items()}
    while True:
        listos = [w for w, d in pendientes.items() if not (d & set(pendientes))]
        if not listos:
            break
        for w in listos:
            pendientes.pop(w)
    ciclos = sorted(str(w) for w in pendientes)

    # 4: desplegar hasta punto fijo y comparar con lo declarado. Solo tiene
    # sentido si no hay ciclos -- con un ciclo el despliegue no termina.
    discrepantes = []
    if not ciclos and not autorreferentes:
        for w, r in cuerpos.items():
            if w not in declaradas:
                continue
            prev, e = None, r
            for _ in range(len(cuerpos) + 1):
                if prev == e:
                    break
                prev, e = e, sympy.expand(e.subs(cuerpos))
            if sympy.expand(e - declaradas[w]) != 0:
                discrepantes.append(str(w))

    return {
        "ok": not autorreferentes and not sin_ecuacion and not ciclos
              and not discrepantes,
        "definiciones": len(emitidas),
        "autorreferentes": sorted(autorreferentes),
        "sin_ecuacion": sorted(sin_ecuacion),
        "ciclos": ciclos,
        "discrepantes": sorted(discrepantes),
    }


def verificar_equivalencia(system, materializado, final, verbose=False):
    """¿Es `final` el mismo objeto matematico que `system`, escrito de otra forma?

    ESTA ES LA COMPROBACION QUE CONVIERTE UNA CIFRA EN UN RESULTADO, y hasta ahora
    solo se le pasaba al punto de grado 5. Los demas puntos de la frontera estaban
    materializados y con el grado medido --que es real-- pero **sin verificar la
    equivalencia**, o sea a un nivel de garantia distinto. Publicarlos en la misma
    tabla sin decirlo era la clase de mezcla que este proyecto ya cometio una vez.

    QUE HACE. Cada incognita nueva `w` viene con su ecuacion definitoria `w = d`.
    Sustituyendo en cascada hacia atras hasta punto fijo, las definitorias deben
    anularse (`0 == 0`, no dicen nada por si mismas) y las demas deben devolver
    EXACTAMENTE las ecuaciones originales: ninguna de menos, ninguna de mas. Es una
    identidad polinomica, no un muestreo -- y es lo unico posible aqui, porque el
    sistema de JSWW se transcribe sin testigo (sus valores son astronomicos).

    TRES TRAMPAS, las tres pisadas ya:

     1. Las definiciones se PIDEN (`materializado.definiciones`), no se adivinan
        leyendo las ecuaciones: con la reescritura activa una definicion puede
        expresarse en terminos de otros nombres y el detector encontraba 15 de 18.
     2. Se aplica la MISMA sustitucion de la post-eliminacion a las definiciones,
        y hasta punto fijo: una definicion puede mencionar una incognita eliminada
        despues.
     3. Las ORIGINALES tambien se desnombran. Si la post-eliminacion mapeo una
        incognita a un NOMBRE (`z -> m1`), el lado "original" lleva un nombre que
        el lado recuperado ya no tiene, y la comparacion falla sin que el sistema
        tenga nada malo.

    Y el emparejamiento es 1 A 1, no "existe alguna que case": dos ecuaciones vivas
    iguales taparian que falta una original distinta.
    """
    # COMPROBACION QUE FALTABA, y su ausencia costo dos cifras. Lo de abajo es una
    # IDENTIDAD POLINOMICA: sustituye cada nombre por su definicion y mira si
    # reaparecen las originales. Eso NO comprueba que el sistema OBLIGUE al nombre
    # a valer eso. Si una incognita original desaparece de todas las ecuaciones del
    # materializado, la ecuacion que la contenia se ha PERDIDO: el sistema es mas
    # DEBIL que el original --tiene soluciones que el original no tiene-- y la
    # sustitucion de arriba sigue cuadrando, porque sustituye por una definicion
    # que el sistema ya no impone.
    #
    # Caso real: forzando el nombre `h + (h+j)(gk+2g+k+1)`, la incognita `g`
    # desaparecia del materializado y la ecuacion (2) quedaba reducida a `m1 = z`,
    # sin nada que atara `m1` a su definicion. `verificar_equivalencia` daba
    # 0 faltan / 0 sobran sobre un sistema que ya no era equivalente.
    en_ecuaciones = set()
    for e in materializado.eqs:
        en_ecuaciones |= e.free_symbols
    perdidas = [u for u in system.unknowns if u not in en_ecuaciones]

    quitadas = {u: v for u, v in getattr(final, "eliminadas", [])}
    for _ in range(len(quitadas)):
        quitadas = {u: sympy.expand(v.subs(quitadas)) for u, v in quitadas.items()}

    defs = {w: sympy.expand(c.subs(quitadas))
            for w, c in getattr(materializado, "definiciones", [])}

    def desnombrar(e):
        prev = None
        while prev != e:
            prev = e
            e = sympy.expand(e.subs(defs))
        return e

    desnombradas = [desnombrar(e) for e in final.eqs]
    definitorias = [x for x in desnombradas if x == 0]
    vivas = [x for x in desnombradas if x != 0]
    originales = [o for o in (desnombrar(sympy.expand(x.subs(quitadas)))
                              for x in system.eqs) if o != 0]

    def casa(u, v):
        return sympy.expand(u - v) == 0 or sympy.expand(u + v) == 0

    pendientes, faltan = list(vivas), []
    for o in originales:
        for i, vv in enumerate(pendientes):
            if casa(o, vv):
                pendientes.pop(i)
                break
        else:
            faltan.append(o)

    est = verificar_estructura(materializado)

    veredicto = {
        "ok": not faltan and not pendientes and not perdidas and est["ok"],
        "estructura": est,
        "perdidas": sorted(str(u) for u in perdidas),
        "definitorias": len(definitorias), "vivas": len(vivas),
        "originales": len(originales),
        "faltan": len(faltan), "sobran": len(pendientes),
        "eliminadas": sorted(str(u) for u in quitadas),
    }
    if verbose:
        print(f"    equivalencia: {veredicto['definitorias']} definitorias se anulan, "
              f"{veredicto['vivas']} vivas vs {veredicto['originales']} originales "
              f"-> faltan {veredicto['faltan']}, sobran {veredicto['sobran']}"
              + (f", INCOGNITAS PERDIDAS {veredicto['perdidas']}" if perdidas else "")
              + ("" if est["ok"] else f", ESTRUCTURA ROTA {est}"),
              flush=True)
    return veredicto


def aplanado_y_eliminacion(system, target=2, k_optimos=8, solo_eliminar=None,
                           timeout_s=900, solo_no_negativos=True, demostrados=(),
                           reescritura=True, sumas_parciales=True,
                           forzar_definiciones=True, verbose=False):
    """Aplana y post-elimina, quedandose con el MEJOR de varios optimos distintos.

    POR QUE NO BASTA LLAMAR AL OPTIMIZADOR UNA VEZ. El optimo en numero de
    nombres **no es unico**, y el numero de nombres **no es la cifra final**:
    despues viene la post-eliminacion de incognitas originales, que el objetivo
    no puede ver --minimiza nombres con las originales congeladas--. Dos aplanados
    de 15 nombres pueden admitir distinto numero de post-eliminaciones.

    Y no es teorico: dos tests que llamaban al optimizador con los MISMOS
    argumentos obtuvieron modelos distintos y publicaron (36,5) y (38,5). Una
    cifra que depende de que modelo devuelva Z3 esa vez no es un resultado.

    Aqui se enumeran hasta `k_optimos` conjuntos DISTINTOS del mismo tamano con
    clausulas de bloqueo, se materializa cada uno y se post-elimina explorando
    todos los ordenes, y se devuelve el mejor. La cifra pasa a depender solo de
    `k_optimos`, que es un parametro declarado -- y sigue siendo una COTA
    SUPERIOR: subir `k_optimos` solo puede mejorarla.

    Devuelve un dict con `sistema` (el `Dioph` final), `variables`, `grado`
    (el del GENERADOR), `nombres`, `cota`, `eliminadas`, `elegidos` y
    `optimos_vistos`.
    """
    from src.analysis.dioph_degree import eliminar_maximo, max_equation_degree

    if solo_eliminar is None:
        solo_eliminar = list(system.unknowns)
    # DOS TANDAS, y la segunda es la que gana. `forzar_definiciones` obliga a
    # nombrar el miembro derecho de cada ecuacion que DEFINE una incognita: eso
    # convierte la ecuacion en `m - u = 0` y entonces eliminar `u` la sustituye por
    # UN SIMBOLO, sin subir el grado. Cuesta a lo sumo un nombre y quita una
    # incognita, asi que el balance nunca es malo -- medido sobre JSWW: 15 nombres
    # y 3 eliminaciones (38,5) frente a 16 nombres y 4 eliminaciones (36,5).
    #
    # Se corren LAS DOS y se toma la mejor porque el forzado no domina siempre: si
    # la definicion iba a nombrarse igualmente, forzarla no cuesta nada; si no,
    # cuesta uno y puede no recuperarlo.
    from src.analysis.dioph_degree import definiciones_lineales
    tandas = [()]
    if forzar_definiciones:
        tandas.append(tuple(str(d) for d in definiciones_lineales(system)))

    # REPLIEGUE A `reescritura=False`, y no es una preferencia de estilo.
    # La ruta de reescritura produce certificados que el materializador NO puede
    # construir: al prohibir que una definicion se nombre a si misma, el cuerpo de
    # algunos nombres se queda sin reduccion a grado 2. Antes eso pasaba
    # desapercibido porque la autorreferencia colapsaba la definitoria a `0 = 0` y
    # el sistema salia -- roto. Ahora falla limpio, y hay que tener a donde caer:
    # sin reescritura el aplanado es peor en numero de nombres pero SE PUEDE
    # CONSTRUIR, que es la unica clase de cifra que este proyecto publica.
    modos = [reescritura] if not reescritura else [True, False]

    mejor, total_vistos = None, 0
    for reesc in modos:
      if mejor is not None and reesc != modos[0]:
          break                        # ya hay algo construible con el modo mejor
      for forzar in tandas:
          vistos = []
          for i in range(max(1, k_optimos)):
              r = aplanado_minimo_compuesto(system, target, timeout_s=timeout_s,
                                            solo_no_negativos=solo_no_negativos,
                                            demostrados=demostrados,
                                            reescritura=reesc,
                                            sumas_parciales=sumas_parciales,
                                            excluir=vistos, semilla=i, forzar=forzar)
              if r["estado"] != "optimo_del_encoding":
                  break                  # se agotaron los optimos de ese tamano
              vistos.append(r["elegidos"])
              total_vistos += 1
              try:
                  M = materializar(system, r["elegidos"], target, reescritura=reesc)
              except ValueError as err:
                  # El conjunto elegido no se puede MATERIALIZAR de forma valida: o
                  # una definitoria colapsa a 0 = 0, o una incognita original
                  # desaparece. Se descarta el candidato, no se publica la cifra.
                  # Esto es lo que ocurre con `forzar_definiciones` sobre el sistema
                  # de JSWW: ver la guarda en `materializar`.
                  if verbose:
                      print(f"    [{'forzado' if forzar else 'libre  '}"
                            f"{'/reesc' if reesc else '/sin-reesc'}] descartado: "
                            f"{str(err)[:110]}", flush=True)
                  continue
              if max_equation_degree(M) > target:
                  continue               # el materializado no alcanza lo certificado
              E = eliminar_maximo(M, target, solo=solo_eliminar)
              gen = 1 + 2 * max_equation_degree(E)
              v = len(E.unknowns) + 1
              if verbose:
                  print(f"    [{'forzado' if forzar else 'libre  '}"
                        f"{'/reesc' if reesc else '/sin-reesc'}] optimo #{len(vistos)}: "
                        f"{r['nombres']} nombres, post-elim "
                        f"{sorted(str(t) for t, _ in E.eliminadas)} -> ({v}, {gen})", flush=True)
              if mejor is None or (v, gen) < (mejor["variables"], mejor["grado"]):
                  mejor = {"sistema": E, "variables": v, "grado": gen,
                           "nombres": r["nombres"], "cota": r["cota"],
                           "eliminadas": list(E.eliminadas), "elegidos": r["elegidos"],
                           "materializado": M, "forzado": bool(forzar),
                           "reescritura": reesc}
    if mejor is not None:
        mejor["optimos_vistos"] = total_vistos
    return mejor


def barrido_pareto(system, grados=(2, 3, 4, 5, 6), eliminables=None,
                   timeout_s=900, solo_no_negativos=True, demostrados=(),
                   reescritura=True, sumas_parciales=True, k_optimos=4,
                   verbose=False):
    """FRONTERA DE PARETO (variables, grado), no un punto suelto.

    POR QUE EXISTE. Se venian midiendo dos esquinas --grado 5 y grado 25-- como
    si fueran los dos unicos sitios donde hay algo que decir. Pero hay dos
    palancas continuas y opuestas:

      * aplanar a grado por ecuacion `d` da un generador de grado `1 + 2d`, y
        cuanto mas alto `d`, menos nombres hacen falta;
      * eliminar una incognita lineal quita una variable y SUBE el grado.

    Barrerlas juntas da una CURVA. Publicar un punto de ella es publicar menos de
    lo que se tiene, y --peor-- deja sin medir la zona intermedia, que en la
    literatura esta literalmente vacia: entre el (42,5) de JSWW y su (26,25) no
    hay ningun par publicado.

    Devuelve la lista de puntos NO DOMINADOS como (variables, grado, receta),
    ordenada por grado creciente. Cada punto viene de un sistema realmente
    MATERIALIZADO y con el grado medido sobre el, no de una formula.

    Las eliminaciones se prueban en TODOS LOS ORDENES posibles porque el orden
    importa: quitar `e` primero deja `q` inutilizable y viceversa, y un voraz se
    queda con lo primero que encuentra.
    """
    from src.analysis.dioph_degree import eliminar_lineales, max_equation_degree

    originales = [str(u) for u in system.unknowns]
    if eliminables is None:
        eliminables = originales
    eliminables = set(eliminables)
    puntos = {}

    def registrar(v, g, receta, base, cur):
        if g not in puntos or v < puntos[g][0]:
            puntos[g] = (v, receta, base, cur)
            if verbose:
                print(f"    ({v:3d} variables, grado {g:3d})  {receta}", flush=True)

    def explorar(M, receta, tope):
        vistos, pila = set(), [(M, ())]
        while pila:
            cur, hechas = pila.pop()
            if frozenset(hechas) in vistos:
                continue
            vistos.add(frozenset(hechas))
            registrar(len(cur.unknowns) + 1, 1 + 2 * max_equation_degree(cur),
                      f"{receta} + eliminar {sorted(hechas)}", M, cur)
            for c in [str(u) for u in cur.unknowns if str(u) in eliminables]:
                E = eliminar_lineales(cur, tope, solo=[c])
                nuevas = tuple(str(t) for t, _ in getattr(E, "eliminadas", []))
                if nuevas:
                    # `eliminadas` ACUMULADA: la verificacion necesita el camino
                    # entero, no solo el ultimo paso.
                    E.eliminadas = list(getattr(cur, "eliminadas", [])) + list(E.eliminadas)
                    pila.append((E, hechas + nuevas))

    explorar(system, "sin aplanar", 99)
    for d in grados:
        # POR K OPTIMOS, no por el primero: el optimo no es unico y la cifra final
        # dependia de que modelo devolviera Z3. Cada punto de la frontera se toma
        # del mejor de `k_optimos` aplanados distintos del mismo tamano.
        best = aplanado_y_eliminacion(system, d, k_optimos=k_optimos,
                                      solo_eliminar=list(system.unknowns),
                                      timeout_s=timeout_s,
                                      solo_no_negativos=solo_no_negativos,
                                      demostrados=demostrados, reescritura=reescritura,
                                      sumas_parciales=sumas_parciales)
        if best is None:
            if verbose:
                print(f"  [grado {d}] el optimizador no alcanzo su cota", flush=True)
            continue
        if verbose:
            print(f"  [aplanado a {d}] {best['nombres']} nombres, mejor de "
                  f"{best['optimos_vistos']} optimos", flush=True)
        explorar(best["materializado"], f"aplanado a {d}", d)

    # VERIFICAR SOLO LOS PUNTOS DE LA FRONTERA. Comprobar la equivalencia de cada
    # nodo del DFS costaria expandir polinomios de grado 25 cientos de veces sin
    # aportar nada: los puntos dominados no se publican. Pero los que SI se
    # publican van todos con veredicto -- no se vuelve a poner en la misma tabla
    # una cifra verificada junto a otra que solo esta materializada.
    frontera, mejor = [], None
    for g in sorted(puntos):
        v, receta, base, cur = puntos[g]
        if mejor is None or v < mejor:
            ver = verificar_equivalencia(system, base, cur)
            if verbose:
                print(f"    verificando ({v}, {g}): "
                      f"{'EQUIVALENTE' if ver['ok'] else 'NO VERIFICADO'} "
                      f"(faltan {ver['faltan']}, sobran {ver['sobran']})", flush=True)
            frontera.append((v, g, receta, ver))
            mejor = v
    return frontera


from src.analysis.dioph_calculus import Dioph          # noqa: E402  (al final: evita ciclo)
