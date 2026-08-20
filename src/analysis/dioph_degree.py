"""
================================================================================
   DIOPHANTUS - REDUCCION DE GRADO (la otra esquina de la frontera de Pareto)
================================================================================
Los pares (incognitas, grado) forman una FRONTERA DE PARETO: se baja el grado
introduciendo incognitas auxiliares, y se eliminan incognitas pagando grado. Los
extremos universales de Jones (1982) son (58, grado 4) y (9, grado 1.638e45).

dioph_lemmas.PellContext ataca la esquina de POCAS INCOGNITAS (comparticion).
Este modulo ataca la esquina de GRADO BAJO, que es su dual exacto:

    APLANADO DE MONOMIOS: mientras alguna ecuacion tenga grado > d, se elige un
    producto de dos variables v1*v2, se introduce una incognita w con la ecuacion
    definitoria  w - v1*v2 = 0  (grado 2), y se sustituye v1*v2 por w en TODAS
    las ecuaciones. Cada sustitucion cuesta 1 incognita y baja el grado.

Aplanar hasta grado <= 2 por ecuacion da grado 4 en la ecuacion unica (suma de
cuadrados), que es la esquina de grado minimo conocida.

CLAVE DEL COSTE: la sustitucion se COMPARTE entre todas las ecuaciones. Si v1*v2
aparece en varias, una sola incognita sirve a todas — el mismo principio que hace
funcionar a PellContext, aplicado al otro eje.

UNIVERSAL: opera sobre cualquier Dioph. No sabe nada de primos ni de ningun
conjunto concreto.

GARANTIA: equisatisfacibilidad. El testigo original se EXTIENDE calculando cada
w = v1*v2; ninguna solucion nueva aparece porque cada w queda determinado.
"""

import sympy

from src.analysis.dioph_calculus import Dioph


_flat_counter = [0]


def _fresh_flat():
    _flat_counter[0] += 1
    return sympy.Symbol(f"z{_flat_counter[0]}", integer=True)


def max_equation_degree(system):
    """Grado maximo entre las ecuaciones individuales (no la suma de cuadrados)."""
    gens = system.params + system.unknowns
    if not gens:
        return 0
    peor = 0
    for e in system.eqs:
        try:
            peor = max(peor, sympy.Poly(e, *gens).total_degree())
        except sympy.PolynomialError:
            return -1
    return peor


def flatten_to_degree(system, target=2, name=None):
    """Aplana `system` para que toda ecuacion tenga grado <= target.

    Devuelve un Dioph nuevo, equisatisfacible, con incognitas adicionales y el
    testigo EXTENDIDO. El grado de la ecuacion unica pasa a ser <= 2*target.

    Coste: una incognita por cada producto distinto que haya que nombrar
    (compartido entre todas las ecuaciones).
    """
    if target < 2:
        raise ValueError("el objetivo minimo por ecuacion es 2 (w - v1*v2 = 0)")

    gens = list(system.params) + list(system.unknowns)
    prods = {}                      # (str(a), str(b)) ordenado -> simbolo w
    nuevas = []                     # ecuaciones definitorias  w - a*b = 0
    orden = []                      # (w, a, b) en orden de creacion, para el testigo

    def producto(a, b):
        clave = tuple(sorted([str(a), str(b)]))
        if clave not in prods:
            w = _fresh_flat()
            prods[clave] = w
            nuevas.append(sympy.expand(w - a * b))
            orden.append((w, a, b))
        return prods[clave]

    def reducir(vars_mon):
        """Reduce una lista de variables (con multiplicidad) a longitud <= target."""
        vs = list(vars_mon)
        while len(vs) > target:
            a, b = vs[0], vs[1]
            vs = [producto(a, b)] + vs[2:]
        return vs

    eqs_out = []
    for e in system.eqs:
        try:
            poly = sympy.Poly(e, *gens)
        except sympy.PolynomialError:
            eqs_out.append(e)
            continue
        acc = sympy.Integer(0)
        for expo, coef in zip(poly.monoms(), poly.coeffs()):
            vars_mon = []
            for g, k in zip(gens, expo):
                vars_mon.extend([g] * k)
            if len(vars_mon) > target:
                vars_mon = reducir(vars_mon)
            term = sympy.Integer(coef)
            for v in vars_mon:
                term = term * v
            acc = acc + term
        eqs_out.append(sympy.expand(acc))

    unknowns = list(system.unknowns) + [w for w, _, _ in orden]
    eqs_final = eqs_out + nuevas

    def w_ext(param_vals):
        if system.witness is None:
            return None
        base = system.witness(param_vals)
        if base is None:
            return None
        entorno = dict(param_vals)
        entorno.update(base)
        out = dict(base)
        for w, a, b in orden:            # en orden de creacion: las dependencias ya estan
            av = a.subs(entorno)
            bv = b.subs(entorno)
            val = sympy.Integer(av) * sympy.Integer(bv)
            out[w] = int(val)
            entorno[w] = int(val)
        return out

    return Dioph(system.params, unknowns, eqs_final, witness=w_ext,
                 name=name or f"{system.name} [aplanado a grado {target}]")



def flatten_greedy(system, target=2, name=None):
    """Aplanado VORAZ: en cada paso nombra el producto MAS FRECUENTE.

    El aplanado ingenuo toma los dos primeros factores de cada monomio, lo que
    desperdicia reutilizacion. Aqui se cuenta, entre todos los monomios que aun
    exceden el grado objetivo, que par de variables aparece mas veces, y se nombra
    ese primero: una sola incognita sirve entonces a varios monomios.

    Mismo principio que PellContext, aplicado al eje del grado: COMPARTIR.
    Devuelve un Dioph equisatisfacible con el testigo extendido.
    """
    gens = list(system.params) + list(system.unknowns)

    # (coef, [vars con multiplicidad]) por ecuacion
    desc = []
    for e in system.eqs:
        try:
            poly = sympy.Poly(e, *gens)
        except sympy.PolynomialError:
            desc.append(None)
            continue
        mons = []
        for expo, coef in zip(poly.monoms(), poly.coeffs()):
            vs = []
            for g, k in zip(gens, expo):
                vs.extend([g] * k)
            mons.append([sympy.Integer(coef), vs])
        desc.append(mons)

    orden = []          # (w, a, b) en orden de creacion
    definitorias = []

    def contar():
        c = {}
        for mons in desc:
            if mons is None:
                continue
            for _, vs in mons:
                if len(vs) <= target:
                    continue
                vistos = set()
                for i in range(len(vs)):
                    for j in range(i + 1, len(vs)):
                        clave = tuple(sorted([str(vs[i]), str(vs[j])]))
                        if clave in vistos:
                            continue
                        vistos.add(clave)
                        c[clave] = c.get(clave, 0) + 1
        return c

    simbolos = {str(g): g for g in gens}

    while True:
        cuenta = contar()
        if not cuenta:
            break
        clave = max(cuenta.items(), key=lambda kv: (kv[1], kv[0]))[0]
        a, b = simbolos[clave[0]], simbolos[clave[1]]
        w = _fresh_flat()
        simbolos[str(w)] = w
        orden.append((w, a, b))
        definitorias.append(sympy.expand(w - a * b))
        # sustituir una aparicion del par en cada monomio que lo contenga y siga alto
        for mons in desc:
            if mons is None:
                continue
            for m in mons:
                vs = m[1]
                while len(vs) > target and str(a) in [str(x) for x in vs]:
                    nombres = [str(x) for x in vs]
                    if str(b) not in nombres:
                        break
                    ia = nombres.index(str(a))
                    resto = nombres[:ia] + nombres[ia + 1:]
                    if str(b) not in resto:
                        break
                    ib_rel = resto.index(str(b))
                    vs_new = [vs[i] for i in range(len(vs)) if i != ia]
                    vs_new = [vs_new[i] for i in range(len(vs_new)) if i != ib_rel]
                    vs_new.append(w)
                    vs = vs_new
                m[1] = vs

    eqs_out = []
    for mons, orig in zip(desc, system.eqs):
        if mons is None:
            eqs_out.append(orig)
            continue
        acc = sympy.Integer(0)
        for coef, vs in mons:
            term = coef
            for v in vs:
                term = term * v
            acc = acc + term
        eqs_out.append(sympy.expand(acc))

    unknowns = list(system.unknowns) + [w for w, _, _ in orden]

    def w_ext(param_vals):
        if system.witness is None:
            return None
        base = system.witness(param_vals)
        if base is None:
            return None
        entorno = dict(param_vals)
        entorno.update(base)
        out = dict(base)
        for w, a, b in orden:
            val = int(sympy.Integer(a.subs(entorno)) * sympy.Integer(b.subs(entorno)))
            out[w] = val
            entorno[w] = val
        return out

    return Dioph(system.params, unknowns, eqs_out + definitorias, witness=w_ext,
                 name=name or f"{system.name} [aplanado voraz a grado {target}]")


def pareto_point(system):
    """(incognitas, grado de la ecuacion unica) — el punto en la frontera."""
    return (system.cost(), system.degree())


def pareto_curve(system, targets=(2, 3, 4)):
    """Curva (incognitas, grado) al aplanar a distintos objetivos.

    Muestra el compromiso de forma explicita: bajar el grado sube las incognitas.
    """
    puntos = [("original", pareto_point(system))]
    for t in targets:
        if max_equation_degree(system) <= t:
            continue
        puntos.append((f"aplanado<={t}", pareto_point(flatten_to_degree(system, t))))
    return puntos


# ---------------------------------------------------------------------------
#   REPRESENTACION -> GENERADOR (para comparar con los records publicados)
# ---------------------------------------------------------------------------

def to_generator(system, param):
    """Convierte una REPRESENTACION en un POLINOMIO GENERADOR.

        Q(param, x) = param * (1 - sum_i P_i(param,x)^2)

    Propiedad: sobre variables NO NEGATIVAS, los VALORES POSITIVOS de Q son
    exactamente los elementos del conjunto representado.
      * si todas las P_i se anulan -> Q = param  (positivo si param > 0);
      * si alguna no se anula      -> sum P_i^2 >= 1 -> Q <= 0.

    POR QUE IMPORTA: los records publicados de primos (Jones-Sato-Wada-Wiens,
    Matiyasevich) son GENERADORES, no representaciones. Sin esta conversion las
    cifras no son comparables. Con ella si lo son.

    GRADO: 1 + 2*max_i deg(P_i). Por eso interesa aplanar a grado 2 por ecuacion:
    da un generador de grado 5, que es la esquina de grado minimo conocida.

    REQUISITO CRITICO: las incognitas deben poder tomarse >= 0. Si el testigo
    produce algun valor negativo, la construccion NO es valida sobre N.
    """
    d = max_equation_degree(system)
    suma = sum(sympy.expand(e ** 2) for e in system.eqs)
    Q = sympy.expand(param * (1 - suma))
    return Q, {
        "variables": len(system.unknowns) + 1,
        "grado": 1 + 2 * d,
        "grado_por_ecuacion": d,
    }


def witness_is_nonnegative(system, param_vals):
    """True si el testigo existe y TODOS sus valores son >= 0.

    Guardarraíl: la conversion a generador sobre N exige no-negatividad. Un solo
    valor negativo la invalida (ya ocurrio una vez: el multiplicador de una
    congruencia escrita en el orden equivocado).
    """
    if system.witness is None:
        return False
    w = system.witness(param_vals)
    if w is None:
        return False
    return all(int(v) >= 0 for v in w.values())


# ---------------------------------------------------------------------------
#   SUSTITUCION DE SKOLEM: aplanar el ARBOL, no los monomios
# ---------------------------------------------------------------------------

def flatten_tree(system, target=2, name=None):
    """Baja el grado nombrando SUBEXPRESIONES, no monomios expandidos.

    POR QUE EXISTE (y por que `flatten_greedy` se queda corto). El voraz empieza
    por `sympy.expand`, y expandir DESTRUYE la estructura factorizada. En el
    polinomio de Jones-Sato-Wada-Wiens, el termino

        ((a + u^2(u^2-a))^2 - 1)(n + 4dy)^2 + 1 - (x+cu)^2

    expandido es una nube de monomios de grado 12, cada uno de los cuales hay que
    nombrar. Sin expandir bastan seis nombres: u^2, u^2(u^2-a), (a+...)^2, dy,
    (n+4dy)^2, cu. Eso es lo que JSWW llaman "the Skolem substitution method",
    y es la razon de que a ellos les cueste 16 incognitas y al voraz 30.

    Medido sobre el sistema de JSWW (ver src/analysis/dioph_jsww.py), que es el
    unico patron de la literatura contra el que podemos medirnos sin depender de
    que nuestra propia cadena sea correcta.

    ESQUEMA (para `target = 2`, el caso que da generadores de grado 5):
      * `_lineal(e)` devuelve una expresion de grado <= 1 igual a `e`,
        introduciendo definiciones donde haga falta;
      * una suma es lineal si sus sumandos lo son;
      * un producto se pliega por pares, nombrando cada producto parcial;
      * una potencia se hace por CUADRADOS REPETIDOS: coste log2(n), no n;
      * cada subexpresion se MEMOIZA por su forma canonica, de modo que `u^2`
        nombrado una vez sirve a todas las ecuaciones. Ahi esta el ahorro.

    Cada incognita nueva viene con su ECUACION DEFINITORIA, luego no anade
    soluciones: el sistema resultante es equisatisfacible y el testigo se extiende
    evaluando las definiciones en orden de creacion.
    """
    if target < 2:
        raise ValueError("target debe ser >= 2 (grado 1 no permite productos)")

    gens = list(system.params) + list(system.unknowns)
    memo = {}                  # srepr(expr) -> simbolo que la representa
    defs = []                  # (simbolo, expresion) en ORDEN de creacion
    nuevas = []

    def grado(e):
        e = sympy.expand(e)
        if e.is_number:
            return 0
        try:
            return sympy.Poly(e, *(gens + nuevas)).total_degree()
        except (sympy.PolynomialError, sympy.GeneratorsNeeded):
            return 99

    def nombrar(e):
        """Devuelve un simbolo w con la definicion `w = e` (memoizada)."""
        clave = sympy.srepr(sympy.expand(e))
        if clave in memo:
            return memo[clave]
        w = _fresh_flat()
        memo[clave] = w
        nuevas.append(w)
        defs.append((w, e))
        return w

    def _lineal(e):
        """Expresion de grado <= 1 igual a `e`."""
        e = sympy.sympify(e)
        if grado(e) <= 1:
            return e
        if e.is_Add:
            return sympy.Add(*[_lineal(t) for t in e.args])
        if e.is_Mul:
            coef, resto = e.as_coeff_Mul()
            factores = list(resto.args) if resto.is_Mul else [resto]
            partes = [_lineal(f) for f in factores]
            acc = partes[0]
            for sig in partes[1:]:
                acc = nombrar(sympy.expand(acc * sig))
            return coef * acc
        if e.is_Pow:
            base, exp = e.args
            if not (exp.is_Integer and int(exp) >= 0):
                return nombrar(e)
            k = int(exp)
            bl = _lineal(base)
            if k == 0:
                return sympy.Integer(1)
            # cuadrados repetidos: k=4 cuesta 2 nombres, no 3
            resultado, actual, potencia = None, bl, 1
            while True:
                if k & potencia:
                    resultado = actual if resultado is None else nombrar(
                        sympy.expand(resultado * actual))
                if potencia * 2 > k:
                    break
                actual = nombrar(sympy.expand(actual * actual))
                potencia *= 2
            return resultado
        return nombrar(e)

    def _termino(e):
        """Expresion de grado <= target igual a `e` (nivel superior).

        Diferencia con `_lineal`, y no es menor: aqui se permite llegar hasta
        grado `target`, no hasta 1. Forzar todo a grado 1 nombra de mas -- un
        factor unico de grado 2 ya cumple el objetivo y no hace falta partirlo.
        """
        e = sympy.sympify(e)
        if grado(e) <= target:
            return e
        if e.is_Add:
            return sympy.Add(*[_termino(t) for t in e.args])
        if e.is_Mul:
            coef, resto = e.as_coeff_Mul()
            factores = list(resto.args) if resto.is_Mul else [resto]
            if len(factores) == 1:
                # un solo factor: se le permite el grado objetivo entero
                return coef * _termino(factores[0])
            partes = [_lineal(f) for f in factores]
            while len(partes) > target:
                partes = [nombrar(sympy.expand(partes[0] * partes[1]))] + partes[2:]
            return coef * sympy.Mul(*partes)
        if e.is_Pow:
            base, exp = e.args
            if exp.is_Integer and int(exp) >= 0 and int(exp) <= target:
                return _lineal(base) ** int(exp)
            return _lineal(e)
        return _lineal(e)

    nuevas_eqs = [sympy.expand(_termino(e)) for e in system.eqs]
    nuevas_eqs += [sympy.expand(w - d) for w, d in defs]

    orden = list(defs)

    def w_ext(param_vals):
        if system.witness is None:
            return None
        base = system.witness(param_vals)
        if base is None:
            return None
        asign = dict(param_vals); asign.update(base)
        out = dict(base)
        for sym, expr in orden:
            val = int(sympy.expand(expr).subs(asign))
            asign[sym] = val
            out[sym] = val
        return out

    return Dioph(params=list(system.params),
                 unknowns=list(system.unknowns) + [w for w, _ in orden],
                 eqs=nuevas_eqs, witness=w_ext,
                 name=name or f"{system.name} (Skolem, grado<={target})")


def flatten_best(system, target=2, name=None):
    """Aplica los dos aplanados y devuelve el que gasta menos incognitas.

    No hay un ganador universal, y conviene no fingir que lo hay:
      * `flatten_greedy` gana cuando el sistema llega YA EXPANDIDO (que es como
        lo construye `dioph_lemmas`), porque entonces no queda arbol que explotar;
      * `flatten_tree` gana cuando se conserva la forma factorizada (el sistema de
        JSWW, por ejemplo: +27 frente a +30).
    Medirlos y quedarse con el mejor cuesta el doble de tiempo y cero riesgo.
    """
    a = flatten_greedy(system, target, name)
    b = flatten_tree(system, target, name)
    return a if a.cost() <= b.cost() else b


def eliminar_redundantes(system, base_unknowns, target=2, name=None):
    """Elimina incognitas de aplanado que se pueden expresar con las demas.

    EL DESPERDICIO QUE ATACA. El aplanado por arbol nombra subexpresiones tal y
    como aparecen, sin darse cuenta de que unas se escriben en terminos de otras:
    nombra `(a+1)^2` y `a^2` por separado, cuando `(a+1)^2 = a^2 + 2a + 1` es de
    grado 1 en lo ya nombrado. En el sistema de Jones-Sato-Wada-Wiens eso pasa con
    `(a+1)^2`, `(n+1)^2` y `(k+1)^2` a la vez.

    COMO. Cada incognita introducida viene con su ecuacion definitoria `w = d_w`.
    Se construye un diccionario monomio -> nombre con las definiciones que son un
    monomio puro (`a^2`, `c*u`, ...), se reescribe `d_w` sustituyendo monomios por
    sus nombres, y si lo que queda tiene grado <= target, `w` sobra: se sustituye
    en todo el sistema y se tira su ecuacion.

    Se itera hasta punto fijo, porque eliminar una puede volver eliminable otra.
    `base_unknowns` son las incognitas ORIGINALES, que nunca se eliminan.
    """
    base = list(base_unknowns)
    unknowns = list(system.unknowns)
    eqs = list(system.eqs)
    params = list(system.params)
    introducidas = [u for u in unknowns if u not in base]

    def grado(e, gens):
        e = sympy.expand(e)
        if getattr(e, "is_number", False):
            return 0
        try:
            return sympy.Poly(e, *gens).total_degree()
        except (sympy.PolynomialError, sympy.GeneratorsNeeded):
            return 99

    cambiado = True
    while cambiado:
        cambiado = False
        # definiciones: w -> expresion (de las ecuaciones de la forma w - expr)
        defin = {}
        for e in eqs:
            ex = sympy.expand(e)
            for w in introducidas:
                if ex.coeff(w, 1) == 1 and ex.coeff(w, 2) == 0:
                    resto = sympy.expand(w - ex)
                    if w not in resto.free_symbols:
                        defin[w] = resto
                        break
        # monomios puros ya nombrados: monomio -> nombre
        gens = params + base + introducidas
        por_monomio = {}
        for w, d in defin.items():
            dd = sympy.expand(d)
            if dd.is_Mul or dd.is_Pow or dd.is_Symbol:
                por_monomio[sympy.srepr(dd)] = w

        for w in list(introducidas):
            d = defin.get(w)
            if d is None:
                continue
            # reescribir d con los monomios ya nombrados (sin usar w)
            reescrito = sympy.expand(d)
            for clave, nombre in por_monomio.items():
                if nombre is w:
                    continue
                mon = sympy.sympify(clave)
                if mon in (0, 1):
                    continue
                cociente, resto = sympy.div(sympy.Poly(reescrito, *gens),
                                            sympy.Poly(mon, *gens))
                if cociente.total_degree() >= 0 and resto.as_expr() != reescrito:
                    cand = sympy.expand(cociente.as_expr() * nombre + resto.as_expr())
                    if grado(cand, gens) < grado(reescrito, gens):
                        reescrito = cand
            if grado(reescrito, gens) <= target:
                # w es redundante: sustituir y eliminar
                nuevas = []
                for e in eqs:
                    ex = sympy.expand(e)
                    if sympy.expand(ex - (w - d)) == 0:
                        continue                      # su propia definicion
                    nuevas.append(sympy.expand(ex.subs(w, reescrito)))
                if all(grado(e, gens) <= target for e in nuevas):
                    eqs = nuevas
                    introducidas.remove(w)
                    unknowns = [u for u in unknowns if u is not w]
                    cambiado = True
                    break

    def w_ext(param_vals):
        if system.witness is None:
            return None
        base_w = system.witness(param_vals)
        if base_w is None:
            return None
        return {u: v for u, v in base_w.items() if u in unknowns}

    return Dioph(params, unknowns, eqs, witness=w_ext,
                 name=name or f"{system.name} [sin redundantes]")


def flatten_hybrid(system, target=2, name=None):
    """Aplanado HIBRIDO: recorre el arbol pero nombra MONOMIOS PUROS y los reusa.

    Junta lo que cada uno de los dos anteriores hacia bien y evita lo que hacia
    mal, medido sobre el sistema de Jones-Sato-Wada-Wiens (25 incognitas):

      * `flatten_greedy` expande primero, y en la ecuacion 8 de JSWW eso convierte
        una expresion anidada en una nube de monomios de grado 12: +30.
      * `flatten_tree` conserva el arbol pero nombra subexpresiones tal cual, sin
        ver que unas se escriben con otras: nombra `(a+1)^2` Y `a^2` por separado
        (y lo mismo con `(n+1)^2`, `(k+1)^2`): +26.

    La observacion que las une: si `w = a^2` ya esta nombrado, entonces
    `(a+1)^2 = w + 2a + 1` es de **grado 1** en el conjunto de generadores, y no
    necesita nombre propio. Asi que se recorre el arbol (para no expandir lo
    anidado) pero cada vez que hay que bajar el grado se REESCRIBE la expresion
    con los monomios ya nombrados antes de decidir si hace falta un nombre nuevo,
    y los nombres que se crean son siempre MONOMIOS PUROS, que son los que se
    comparten entre ecuaciones.

    Devuelve un Dioph equisatisfacible con el testigo extendido.
    """
    if target < 2:
        raise ValueError("target debe ser >= 2")

    gens = list(system.params) + list(system.unknowns)
    tabla = {}                 # srepr(monomio) -> simbolo
    defs = []                  # (simbolo, monomio) en orden de creacion
    nuevas = []

    def todos():
        return gens + nuevas

    def grado(e):
        e = sympy.expand(e)
        if getattr(e, "is_number", False):
            return 0
        try:
            return sympy.Poly(e, *todos()).total_degree()
        except (sympy.PolynomialError, sympy.GeneratorsNeeded):
            return 99

    def nombrar_monomio(mon):
        clave = sympy.srepr(sympy.expand(mon))
        if clave not in tabla:
            w = _fresh_flat()
            tabla[clave] = w
            nuevas.append(w)
            defs.append((w, mon))
        return tabla[clave]

    def reescribir(e):
        """Baja el grado de `e` usando (y creando) nombres de MONOMIOS puros."""
        e = sympy.expand(e)
        while grado(e) > target:
            poly = sympy.Poly(e, *todos())
            # el par de variables mas frecuente entre los monomios que sobran
            cuenta = {}
            for expo in poly.monoms():
                vs = []
                for g, k in zip(todos(), expo):
                    vs.extend([g] * k)
                if len(vs) <= target:
                    continue
                visto = set()
                for x in range(len(vs)):
                    for y in range(x + 1, len(vs)):
                        cl = tuple(sorted([str(vs[x]), str(vs[y])]))
                        if cl in visto:
                            continue
                        visto.add(cl)
                        cuenta[cl] = cuenta.get(cl, 0) + 1
            if not cuenta:
                break
            cl = max(cuenta.items(), key=lambda kv: (kv[1], kv[0]))[0]
            simb = {str(g): g for g in todos()}
            w = nombrar_monomio(simb[cl[0]] * simb[cl[1]])
            e = sympy.expand(e.subs(simb[cl[0]] * simb[cl[1]], w))
            if grado(e) > target and sympy.expand(e.subs(w, simb[cl[0]] * simb[cl[1]])) == e:
                break              # la sustitucion no avanzo: evitar bucle
        return e

    UMBRAL_TERMINOS = 40      # por encima, expandir cuesta mas de lo que ahorra

    def _hasta(e, d):
        """Expresion de grado <= d igual a `e`."""
        e = sympy.sympify(e)
        if grado(e) <= d:
            return e
        # 1) reescribir con lo ya nombrado, SIN tocar el arbol -- pero solo si la
        #    expresion es PEQUENA. Reescribir exige expandir, y en la ecuacion 8
        #    de JSWW expandir es precisamente lo que queriamos evitar (nube de
        #    monomios de grado 12). El umbral es lo que hace que el hibrido sea
        #    hibrido y no un voraz disfrazado.
        ex = sympy.expand(e)
        if len(ex.args) <= UMBRAL_TERMINOS:
            r = reescribir(ex)
            if grado(r) <= d:
                return r
        # 2) si sigue alta, descomponer por la estructura
        if e.is_Add:
            return sympy.Add(*[_hasta(t, d) for t in e.args])
        if e.is_Mul:
            coef, resto = e.as_coeff_Mul()
            factores = list(resto.args) if resto.is_Mul else [resto]
            if len(factores) == 1:
                return coef * _hasta(factores[0], d)
            partes = [_hasta(f, 1) for f in factores]
            while len(partes) > d:
                partes = [nombrar_monomio(sympy.expand(partes[0] * partes[1]))] + partes[2:]
            return coef * sympy.Mul(*partes)
        if e.is_Pow:
            base, exp = e.args
            if exp.is_Integer and 0 <= int(exp) <= d:
                return _hasta(base, 1) ** int(exp)
            if exp.is_Integer and int(exp) > 0:
                bl = _hasta(base, 1)
                acc, k = bl, int(exp)
                res = None
                pot = 1
                while True:
                    if k & pot:
                        res = acc if res is None else nombrar_monomio(sympy.expand(res * acc))
                    if pot * 2 > k:
                        break
                    acc = nombrar_monomio(sympy.expand(acc * acc))
                    pot *= 2
                return res
        return nombrar_monomio(sympy.expand(e))

    eqs_out = [sympy.expand(_hasta(e, target)) for e in system.eqs]
    eqs_out += [sympy.expand(w - d) for w, d in defs]

    orden = list(defs)

    def w_ext(param_vals):
        if system.witness is None:
            return None
        base = system.witness(param_vals)
        if base is None:
            return None
        asign = dict(param_vals); asign.update(base)
        out = dict(base)
        for sym, expr in orden:
            val = int(sympy.expand(expr).subs(asign))
            asign[sym] = val
            out[sym] = val
        return out

    return Dioph(params=list(system.params),
                 unknowns=list(system.unknowns) + [w for w, _ in orden],
                 eqs=eqs_out, witness=w_ext,
                 name=name or f"{system.name} (hibrido, grado<={target})")


def eliminar_lineales(system, target=2, solo=None, name=None):
    """Elimina incognitas definidas por una ecuacion lineal, ANTES de aplanar.

    Si una ecuacion tiene la forma `u = expr` con `u` de grado 1 y coeficiente
    +-1, y `u` no aparece en `expr`, entonces `u` sobra: se sustituye en todo el
    sistema y desaparecen la incognita Y su ecuacion.

    CONDICION DE SOUNDNESS SOBRE N, que no es opcional: `u >= 0` es una
    restriccion real del sistema, asi que solo se puede eliminar si `expr` tiene
    TODOS los coeficientes >= 0 y por tanto es automaticamente >= 0. En el sistema
    de Jones-Sato-Wada-Wiens eso deja eliminar `q = wz+h+j`, `z = (gk+2g+k+1)(h+j)+h`
    y `e = 2n+p+q+z`, pero NO `v = y-n-l` ni `l = ai+k+1-i`, que llevan signos
    mezclados: ahi `v >= 0` y `l >= 0` codifican desigualdades que se perderian.

    Compensacion: la sustitucion SUBE el grado donde `u` aparecia, asi que puede
    salir cara al aplanar despues. `solo` permite fijar que incognitas eliminar
    (por nombre) para medir cada una por separado en vez de aplicarlas a ciegas.
    """
    params = list(system.params)
    unknowns = list(system.unknowns)
    eqs = [sympy.expand(e) for e in system.eqs]
    eliminadas = []

    cambiado = True
    while cambiado:
        cambiado = False
        gens = params + unknowns
        for idx, e in enumerate(eqs):
            for u in list(unknowns):
                if solo is not None and str(u) not in solo:
                    continue
                coef = e.coeff(u, 1)
                if coef not in (1, -1) or e.coeff(u, 2) != 0:
                    continue
                resto = sympy.expand(e - coef * u)
                if u in resto.free_symbols:
                    continue
                valor = sympy.expand(-resto / coef)
                if not _coeficientes_no_negativos_expr(valor):
                    continue          # u >= 0 dejaria de estar garantizado
                nuevas = [sympy.expand(q.subs(u, valor))
                          for k, q in enumerate(eqs) if k != idx]
                eqs = nuevas
                unknowns = [x for x in unknowns if x is not u]
                eliminadas.append((u, valor))
                cambiado = True
                break
            if cambiado:
                break

    def w_ext(param_vals):
        if system.witness is None:
            return None
        base = system.witness(param_vals)
        if base is None:
            return None
        return {u: v for u, v in base.items() if u in unknowns}

    out = Dioph(params, unknowns, eqs, witness=w_ext,
                name=name or f"{system.name} [sin lineales]")
    out.eliminadas = eliminadas
    return out


def _coeficientes_no_negativos_expr(e):
    """True si todo monomio de `e` tiene coeficiente >= 0 (constante incluida)."""
    e = sympy.expand(e)
    if getattr(e, "is_number", False):
        return e >= 0
    try:
        syms = sorted(e.free_symbols, key=str)
        poly = sympy.Poly(e, *syms)
    except (sympy.PolynomialError, sympy.GeneratorsNeeded):
        return False
    return all(c >= 0 for c in poly.coeffs())
