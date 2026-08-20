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
| JSWW 1976, a mano               |       - |    41 | (42, 5)   |    - |

LA CONCLUSION, que es la parte util: **nuestra busqueda ya estaba en el optimo**.
Los ~2.000 reinicios aleatorios habian encontrado 46, y Z3 demuestra que 46 es el
minimo para esa base. Luego el problema NO es la busqueda: es la FORMULACION.

POR QUE JSWW llega a 41 y nosotros no. Ellos no nombran solo monomios: nombran
SUBEXPRESIONES COMPUESTAS -- `(a + u^2(u^2-a))^2`, `(n+4dy)^2`-- que no son
monomios de ningun desarrollo. Optimizar sobre ese espacio es el problema del
CIRCUITO ARITMETICO MINIMO con puertas de grado 2 (un straight-line program
minimo), y es un espacio muchisimo mas grande que el de los monomios. Ahi esta
la brecha de 5 variables, y ahi hay que atacar si se quiere bajar de 47.
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

def _nodos(e, acc):
    """Todos los nodos del arbol de `e`, y los productos parciales de cada Mul.

    Los productos parciales hacen falta porque partir `f1*f2*f3` en dos grupos
    crea subexpresiones (`f1*f2`) que no son nodos del arbol original pero si
    candidatas a recibir nombre.
    """
    e = sympy.sympify(e)
    acc.add(e)
    if e.is_Add or e.is_Mul:
        for a in e.args:
            _nodos(a, acc)
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
    """Vector de exponentes si `e` es un monomio sobre `gens`; None si no lo es."""
    e = sympy.expand(e)
    if getattr(e, "is_number", False):
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


def _factores(e, limite=8):
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
                              solo_no_negativos=False, demostrados=()):
    """Minimo numero de SUBEXPRESIONES a nombrar, no solo monomios.

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
    """
    if not Z3_DISPONIBLE:
        return {"estado": "sin_z3"}

    gens = list(system.params) + list(system.unknowns)

    def grado(e):
        e = sympy.expand(e)
        if getattr(e, "is_number", False):
            return 0
        try:
            return sympy.Poly(e, *gens).total_degree()
        except (sympy.PolynomialError, sympy.GeneratorsNeeded):
            return 99

    cand = set()
    for e in system.eqs:
        _nodos(e, cand)
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

    opt = z3.Optimize()
    opt.set("timeout", timeout_s * 1000)

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
        if permitir_nombre and e in x:
            ops.append(x[e])
        if e.is_Add:
            ops.append(z3.And(*[R(a, d) for a in e.args]))
        ex = sympy.expand(e)
        if ex != e and ex.is_Add and len(ex.args) <= 60:
            ops.append(z3.And(*[R(a, d) for a in ex.args]))
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
            elif fs and d >= 2 and len(fs) <= 8:   # 8: desplegar potencias alarga fs
                for r in range(1, len(fs)):
                    for comb in itertools.combinations(range(len(fs)), r):
                        g1 = sympy.Mul(*[fs[i] for i in comb])
                        g2 = sympy.Mul(*[fs[i] for i in range(len(fs)) if i not in comb])
                        ops.append(z3.And(R(g1, 1), R(g2, 1)))
        return z3.Or(ops) if ops else z3.BoolVal(False)

    raiz = [R(e, target) for e in system.eqs]
    for c in orden:
        opt.add(z3.Implies(x[c], R(c, target, permitir_nombre=False)))
    while pendientes:
        e, d, pn, v = pendientes.pop()
        opt.add(v == opciones_de(e, d, pn))
    for r in raiz:
        opt.add(r)
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


def materializar(system, elegidos, target=2, name=None):
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

    def grado(e):
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

    def simbolo(c):
        k = sympy.srepr(sympy.expand(c))
        if k not in nombres:
            w = sympy.Symbol("m%d" % (len(nombres) + 1), integer=True)
            nombres[k] = w
            defs.append((w, c))
        return nombres[k]

    def intentar(e, d, permitir_nombre=True):
        """Reduce `e` a grado <= d, o devuelve None si no puede.

        Devolver None en vez de lanzar es lo que permite PROBAR una particion y,
        si no sale, seguir con la siguiente. Una version anterior lanzaba dentro
        del bucle y abortaba la busqueda en la primera rama muerta, con un mensaje
        enganoso ("no se pudo reducir k**3") sobre una particion que simplemente
        no era la buena.
        """
        e = sympy.sympify(e)
        if grado(e) <= d:
            return e
        k = sympy.srepr(sympy.expand(e))
        if permitir_nombre and k in clave_elegidos:
            return simbolo(clave_elegidos[k])
        if e.is_Add:
            partes = [intentar(a, d) for a in e.args]
            if all(p is not None for p in partes):
                return sympy.Add(*partes)
        ex = sympy.expand(e)
        if ex != e and ex.is_Add:
            partes = [intentar(a, d) for a in ex.args]
            if all(p is not None for p in partes):
                return sympy.Add(*partes)
        expo = _como_monomio(ex, gens)
        if expo is not None and d >= 2:
            for d1 in itertools.product(*[range(a + 1) for a in expo]):
                s1 = sum(d1)
                if s1 == 0 or s1 == sum(expo):
                    continue
                d2 = _dividir(expo, d1)
                if d2 is None or s1 > sum(d2):
                    continue
                r1 = intentar(_monomio_expr(d1, gens), 1)
                if r1 is None:
                    continue
                r2 = intentar(_monomio_expr(d2, gens), 1)
                if r2 is None:
                    continue
                coef = sympy.expand(ex / _monomio_expr(expo, gens))
                return coef * r1 * r2
        if e.is_Mul or e.is_Pow:
            coef, fs = _factores(e)       # la MISMA laguna estaba aqui: sin esto
            if len(fs) == 1:              # el materializador no sabe construir el
                                          # sistema que el optimizador ya eligio
                r = intentar(fs[0], d)
                if r is not None:
                    return coef * r
            elif fs and d >= 2:
                for r in range(1, len(fs)):
                    for comb in itertools.combinations(range(len(fs)), r):
                        g1 = sympy.Mul(*[fs[i] for i in comb])
                        g2 = sympy.Mul(*[fs[i] for i in range(len(fs)) if i not in comb])
                        r1 = intentar(g1, 1)
                        if r1 is None:
                            continue
                        r2 = intentar(g2, 1)
                        if r2 is None:
                            continue
                        return coef * r1 * r2
        return None

    def reducir(e, d, permitir_nombre=True):
        r = intentar(e, d, permitir_nombre)
        if r is None:
            raise ValueError(f"no se pudo reducir a grado {d}: {e}")
        return r

    eqs = [sympy.expand(reducir(e, target)) for e in system.eqs]
    i = 0
    while i < len(defs):
        w, c = defs[i]
        eqs.append(sympy.expand(w - reducir(c, target, permitir_nombre=False)))
        i += 1

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

    return Dioph(list(system.params), incognitas, eqs, witness=w_ext,
                 name=name or f"{system.name} [optimo materializado]")


from src.analysis.dioph_calculus import Dioph          # noqa: E402  (al final: evita ciclo)
