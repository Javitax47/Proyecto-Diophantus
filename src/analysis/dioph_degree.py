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


def _valor_o_none(expr, entorno):
    """Evalua `expr` en `entorno`, o devuelve None si queda algo simbolico.

    Existe porque desde el anclaje por `L_psi` hay TESTIGOS PARCIALES: el testigo
    base no sabe dar valor a todas sus incognitas (su construccion exige el rango
    de aparicion de un K astronomico). Un nombre nuevo que dependa de una de esas
    se deja SIN ASIGNAR en vez de inventarlo o de tirar el testigo entero; lo que
    quede asignado sigue sirviendo (`Dioph.check_witness_parcial`).
    """
    val = sympy.expand(expr.subs(entorno)) if hasattr(expr, 'subs') else expr
    return int(val) if getattr(val, "is_number", False) or isinstance(val, int) else None


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
            # TESTIGO PARCIAL: si el sistema base no supo dar valor a algun
            # simbolo --le pasa a la cadena anclada por L_psi, cuyo testigo sale
            # de un rango de aparicion astronomico-- el nombre nuevo tampoco se
            # puede evaluar. Se DEJA SIN ASIGNAR en vez de inventarlo o de tirar
            # todo el testigo: lo que quede asignado sigue sirviendo para
            # comprobar las ecuaciones que lo alcancen (`check_witness_parcial`).
            val = _valor_o_none(av * bv, {})
            if val is None:
                continue
            out[w] = val
            entorno[w] = val
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
            val = _valor_o_none(a * b, entorno)   # None -> testigo parcial
            if val is None:
                continue
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
            val = _valor_o_none(expr, asign)      # None -> testigo parcial
            if val is None:
                continue
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
    # DOS COPIAS A PROPOSITO. `plano` se expande porque la deteccion de
    # definiciones lineales (`coeff(u,1)`, `coeff(u,2)`) necesita la forma
    # desarrollada. `eqs` conserva el ARBOL, y es la que se devuelve.
    #
    # POR QUE IMPORTA, y no es una micro-optimizacion. Expandir destruye los
    # nodos compuestos, y el catalogo de candidatos del optimizador se construye
    # a partir de la forma SINTACTICA que recibe. Medido sobre el sistema de
    # JSWW: sin tocar tiene 40 nodos Add; tras eliminar una incognita, si se
    # expande, quedan 13 -- y desaparecen justo los utiles (`c*u + x`,
    # `4*d*y + n`, `a + u^2(u^2-a)`, `g*k + 2*g + k + 1`). Con el catalogo
    # empobrecido el optimizador devolvia una "cota inferior" de 21 para un
    # sistema en el que existe un aplanado de 20: la cota era de su catalogo, no
    # del problema. Ese fue el contraejemplo que obligo a retirar la palabra
    # "minimo" (ver ESTADO_CALCULO_DIOFANTICO 3.2i).
    plano = [sympy.expand(e) for e in system.eqs]
    eqs = list(system.eqs)
    eliminadas = []

    cambiado = True
    while cambiado:
        cambiado = False
        gens = params + unknowns
        for idx, e in enumerate(plano):
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
                # La sustitucion se hace sobre el arbol SIN expandir despues:
                # `subs` respeta la estructura, y esa estructura es la que el
                # optimizador aprovecha.
                eqs = [q.subs(u, valor) for k, q in enumerate(eqs) if k != idx]
                plano = [sympy.expand(q.subs(u, valor))
                         for k, q in enumerate(plano) if k != idx]
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


def definiciones_disponibles(system, solo=None):
    """TODAS las parejas (incognita, indice de ecuacion, valor) que se pueden usar.

    POR QUE HACE FALTA, y es un hueco que estuvo abierto toda la vida del
    proyecto. `eliminar_lineales` recorre las ecuaciones y se queda con la
    PRIMERA que define la incognita. Pero una misma incognita suele estar
    definida por VARIAS: en el sistema (1) de JSWW, `q` lo esta por las
    ecuaciones (1), (3) y (13), y `z` por la (2), la (3) y la (14). Cada eleccion
    sustituye una expresion distinta y por tanto **deja el sistema en un grado
    distinto** -- y la que se cogia era la primera del bucle, o sea un accidente
    del orden en que estan escritas.

    RESULTADO DE MEDIRLO, y es NEGATIVO: sobre el sistema (1), sobre el
    desplazado y sobre el de la cota de Pell, ramificar tambien por la eleccion
    de definicion da EXACTAMENTE los mismos puntos --(21,25), (20,37), (19,61)--
    con recetas distintas. La eleccion arbitraria no estaba costando nada.

    Se deja implementado igual, por dos razones. La primera es que el hueco era
    real: el codigo elegia por el orden en que estan escritas las ecuaciones, y
    eso no es una decision, es un accidente. La segunda es que ahora la
    afirmacion "el orden y la eleccion no importan" esta MEDIDA en vez de
    supuesta, que es la diferencia entre las dos clases de resultado que este
    proyecto distingue.

    Lo que NO explica, por tanto, es la brecha entre nuestro (19,61) y el (19,29)
    que JSWW anuncian. Queda la otra hipotesis: que ese (19,29) no salga del
    sistema (1) sino de la seccion 3 (ver `dioph_jsww3`).
    """
    params, unknowns = list(system.params), list(system.unknowns)
    plano = [sympy.expand(e) for e in system.eqs]
    out = []
    for idx, e in enumerate(plano):
        for u in unknowns:
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
                continue
            out.append((u, idx, valor))
    return out


def eliminar_una(system, u, idx, valor, name=None):
    """Elimina `u` usando LA ecuacion `idx`, no la primera que sirva.

    Es `eliminar_lineales` partida en dos para que quien llama pueda elegir la
    definicion. La sustitucion se hace sobre el arbol sin expandir, por el mismo
    motivo documentado alli: expandir destruye los nodos compuestos que el
    optimizador aprovecha.
    """
    eqs = [q.subs(u, valor) for kk, q in enumerate(system.eqs) if kk != idx]
    unknowns = [x for x in system.unknowns if x is not u]

    def w_ext(param_vals):
        if system.witness is None:
            return None
        base = system.witness(param_vals)
        if base is None:
            return None
        return {a: b for a, b in base.items() if a in unknowns}

    out = Dioph(list(system.params), unknowns, eqs, witness=w_ext,
                name=name or f"{system.name} [-{u}]")
    out.eliminadas = list(getattr(system, "eliminadas", [])) + [(u, valor)]
    return out


def frontera_eliminando(system, solo=None, tope_grado=None, max_pasos=None):
    """Frontera (variables, grado) explorando ORDEN **y ELECCION DE DEFINICION**.

    El DFS que habia exploraba todos los ORDENES pero una sola definicion por
    incognita. Aqui se ramifica sobre las parejas (incognita, ecuacion), que es
    el espacio completo.
    """
    puntos, vistos = {}, set()
    pila = [(system, ())]
    while pila:
        cur, hechas = pila.pop()
        clave = frozenset(hechas)
        if clave in vistos:
            continue
        vistos.add(clave)
        g = max_equation_degree(cur)
        v = len(cur.unknowns) + 1
        if g not in puntos or v < puntos[g][0]:
            puntos[g] = (v, sorted(hechas))
        if max_pasos is not None and len(hechas) >= max_pasos:
            continue
        for u, idx, valor in definiciones_disponibles(cur, solo=solo):
            E = eliminar_una(cur, u, idx, valor)
            if tope_grado is not None and max_equation_degree(E) > tope_grado:
                continue
            pila.append((E, hechas + (str(u),)))
    frontera, mejor = [], None
    for g in sorted(puntos):
        v, h = puntos[g]
        if mejor is None or v < mejor:
            frontera.append((v, 1 + 2 * g, h))
            mejor = v
    return frontera


def techo_combinacion_relaciones(system):
    """Cuanto podria ahorrar el TEOREMA DE COMBINACION DE RELACIONES en `system`.

    QUE ES. El teorema de Matiyasevich-Robinson colapsa `q` condiciones del tipo
    "A es un cuadrado" y "S divide a T" en UNA sola ecuacion al coste de UNA
    incognita. Esta declarado en este proyecto como "la unica pieza que reduce el
    conteo" en la esquina de pocas variables, y esta SIN IMPLEMENTAR.

    PARA QUE SIRVE ESTA FUNCION. Para decidir si merece la pena implementarlo
    ANTES de implementarlo. El ahorro no es `q - 1`: es
    `(numero de INCOGNITAS dedicadas a esas condiciones) - 1`, que es menor porque
    una misma incognita puede servir a varias condiciones. Confundir las dos cosas
    infla el techo y hace parecer viable lo que no lo es.

    LO QUE MIDIO SOBRE ESTE PROYECTO, y es la razon de que exista:

        cadena propia (49 incognitas)  ->  techo (35, ?)
        sistema (1) de JSWW            ->  techo (17, ?)

    La primera linea **descarta** aplicar el teorema a la cadena propia: su techo
    TEORICO (35 variables) es peor que el (23, 25) que ya esta construido y
    verificado. La segunda parece prometedora --17 batiria al (19, 29) anunciado--
    pero el techo es en VARIABLES y no dice nada del GRADO, y ahi esta la trampa:
    el punto (17, D) solo sirve si `D < 13.697`, porque si no lo domina el
    (12, 13.697) de la literatura. Los grados que produce este teorema son
    astronomicos por construccion, asi que el punto resultante seria con casi total
    seguridad DOMINADO -- es decir, trabajo perdido.

    NOTA SOBRE LA FUENTE. El enunciado exacto de `M_q` no esta accesible desde este
    entorno (arxiv.org y en.wikipedia.org los rechaza la politica de egress), y
    escribirlo de memoria seria exactamente el error que este proyecto ha pagado
    ocho veces. Por eso se mide el TECHO en vez de implementar a ciegas.

    Devuelve un dict con `incognitas`, `colapsables`, `ahorro`, `techo_variables`
    y el desglose por clase de ecuacion.
    """
    inc = set(system.unknowns)
    gens = system.params + system.unknowns
    colapsables, clases = set(), {}

    def cuenta(k):
        clases[k] = clases.get(k, 0) + 1

    for e in system.eqs:
        ex = sympy.expand(e)
        libres = ex.free_symbols & inc
        marcada = None
        for v in libres:                      # "algo = cuadrado": P - v**2
            if ex.coeff(v, 2) in (1, -1) and ex.coeff(v, 1) == 0:
                if v not in sympy.expand(ex - ex.coeff(v, 2) * v ** 2).free_symbols:
                    marcada, tipo = v, "cuadrado"
                    break
        if marcada is None:
            for v in libres:                  # "S | T": T - S*v con S no constante
                c1 = ex.coeff(v, 1)
                if ex.coeff(v, 2) == 0 and c1 != 0 and not c1.is_number:
                    if v not in sympy.expand(ex - c1 * v).free_symbols:
                        marcada, tipo = v, "divisibilidad"
                        break
        if marcada is not None:
            colapsables.add(marcada)
            cuenta(tipo)
        else:
            try:
                g = sympy.Poly(ex, *gens).total_degree()
            except (sympy.PolynomialError, sympy.GeneratorsNeeded):
                g = 99
            cuenta("lineal" if g <= 1 else "otra")

    ahorro = max(0, len(colapsables) - 1)
    return {
        "incognitas": len(system.unknowns),
        "colapsables": sorted(str(v) for v in colapsables),
        "ahorro": ahorro,
        "techo_variables": len(system.unknowns) - ahorro + 1,
        "clases": clases,
    }


def definiciones_lineales(system, grado_minimo=2):
    """Miembros derechos de las ecuaciones que DEFINEN una incognita sobre N.

    Devuelve la lista de expresiones `R` tales que alguna ecuacion es `u - R` (o
    `R - u`) con `u` de grado 1, coeficiente +-1, `u` ausente de `R`, y `R` con
    TODOS los coeficientes >= 0 -- es decir, exactamente las que `eliminar_lineales`
    sabe usar.

    PARA QUE SIRVE, que no es evidente. Estas expresiones son las que conviene
    pasar como `forzar` al optimizador de aplanado, y la razon es una regla
    general y no un truco:

        si `u = R` y se NOMBRA `R` como `m`, la ecuacion pasa a ser `m - u = 0`,
        y entonces eliminar `u` la sustituye por UN SIMBOLO -- coste de grado cero.

    Sin ese nombre, sustituir `u` mete la expresion `R` entera donde `u` aparecia
    y el grado se dispara: medido sobre el sistema de JSWW, eliminar `z` sin
    nombrar su definicion sube las ecuaciones de grado 2 a grado 4, y la
    eliminacion se descarta. Con el nombre, sale gratis.

    El balance nunca es malo: nombrar cuesta a lo sumo una incognita y eliminar
    quita una. Y suele ser bueno, porque muchas de estas expresiones el
    optimizador iba a nombrarlas de todos modos.

    `grado_minimo` descarta las definiciones que ya son de grado 1 (`e = 2n+p+q+z`):
    esas se eliminan solas, nombrarlas seria gastar una incognita a cambio de nada.
    """
    fuera = []
    gens = system.params + system.unknowns
    for cruda in system.eqs:
        e = sympy.expand(cruda)
        for u in system.unknowns:
            coef = e.coeff(u, 1)
            if coef not in (1, -1) or e.coeff(u, 2) != 0:
                continue
            resto = sympy.expand(e - coef * u)
            if u in resto.free_symbols:
                continue
            valor = sympy.expand(-resto / coef)
            if not _coeficientes_no_negativos_expr(valor):
                continue
            try:
                g = sympy.Poly(valor, *gens).total_degree()
            except (sympy.PolynomialError, sympy.GeneratorsNeeded):
                continue
            if g < grado_minimo:
                continue
            # SE DEVUELVEN LAS DOS FORMAS, y no es por comodidad. El optimizador
            # reconoce un candidato por su `str()`, y su catalogo se construye
            # sobre la forma FACTORIZADA que recibe el sistema. Devolver solo la
            # desarrollada --que es la que hace falta para DETECTAR la definicion--
            # produce cadenas como `g*h*k + 2*g*h + ...` que no casan con ningun
            # candidato: forzar no forzaba nada, en silencio, y la medida salia
            # identica a no forzar.
            formas = [valor]
            if cruda.is_Add:
                # La forma TAL CUAL la escribe el sistema: se quita el termino
                # `coef*u` del Add sin expandir nada mas.
                resto_crudo = sympy.Add(*[t for t in cruda.args if t != coef * u])
                tal_cual = resto_crudo if coef == -1 else -resto_crudo
                if sympy.expand(tal_cual - valor) == 0:
                    formas.append(tal_cual)
            for forma in formas:
                if forma not in fuera:
                    fuera.append(forma)
    return fuera


def eliminar_maximo(system, tope=2, solo=None, name=None):
    """Post-eliminacion que explora TODOS LOS ORDENES y devuelve el mejor sistema.

    POR QUE NO BASTA `eliminar_lineales` A SECAS. Dos motivos, los dos medidos:

     1. EL ORDEN IMPORTA. Sobre el aplanado a grado 2 del sistema de JSWW, quitar
        `e` primero deja `q` inutilizable --sustituirla subiria el grado a 4-- y
        quitar `q` primero deja fuera a `e`. Cualquier recorrido voraz se queda
        con lo primero que encuentra y la cifra depende del orden de iteracion.
     2. HAY QUE VIGILAR EL GRADO. `eliminar_lineales` acepta `tope` pero no lo
        usa: sin restringir `solo` tambien deshace los NOMBRES --toda definicion
        `w = d` es lineal en `w`-- y el aplanado se pierde entero. Medido: sobre
        el sistema de 42 incognitas y grado 2, la eliminacion libre devuelve 24
        variables y grado 37.

    Aqui se prueba incognita a incognita, se descarta la que suba el grado por
    encima de `tope`, y se exploran todas las ramas. `solo` restringe el conjunto
    de candidatas (lo normal: las incognitas ORIGINALES, nunca los nombres).
    """
    candidatas = None if solo is None else {str(s) for s in solo}
    vistos = set()
    mejor, mejor_defs = system, []
    pila = [(system, frozenset(), [])]
    while pila:
        cur, hechas, defs = pila.pop()
        if hechas in vistos:
            continue
        vistos.add(hechas)
        if cur.cost() < mejor.cost():
            mejor, mejor_defs = cur, defs
        for c in [str(u) for u in cur.unknowns
                  if candidatas is None or str(u) in candidatas]:
            E = eliminar_lineales(cur, tope, solo=[c])
            hechas_E = list(getattr(E, "eliminadas", []))
            if not hechas_E or max_equation_degree(E) > tope:
                continue
            pila.append((E, hechas | {str(t) for t, _ in hechas_E}, defs + hechas_E))
    # `eliminadas` ACUMULADA a lo largo del camino ganador. Es lo que necesita la
    # verificacion por sustitucion hacia atras, y ojo: un valor puede mencionar
    # una incognita eliminada DESPUES, asi que hay que sustituir hasta punto fijo,
    # no una sola vez. Comparar definiciones tomadas antes de eliminar con
    # ecuaciones tomadas despues ya dio un fallo falso una vez.
    mejor.eliminadas = mejor_defs
    if name:
        mejor.name = name
    return mejor


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


def flatten_greedy_semilla(system, target=2, semilla=0):
    """Voraz con desempate ALEATORIO controlado por `semilla`.

    Por que existe: el criterio "nombrar el par mas frecuente" deja MUCHOS
    empates, y cual se elija cambia el resultado final mas de lo que parece.
    Medido sobre el sistema de Jones-Sato-Wada-Wiens, cambiar solo el desempate
    baja el generador de 49 a 47 variables en las dos primeras semillas. El
    aplanado optimo es un problema de optimizacion combinatoria (el mismo que la
    *common subexpression elimination*), y una heuristica con un unico camino
    deja valor sobre la mesa.

    Identico a `flatten_greedy` salvo por el desempate. Con `semilla=None` se
    comporta de forma determinista (primer candidato en orden lexicografico).
    """
    import random
    rnd = random.Random(semilla) if semilla is not None else None
    gens = list(system.params) + list(system.unknowns)

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

    orden, definitorias = [], []
    simbolos = {str(g): g for g in gens}

    while True:
        cuenta = {}
        for mons in desc:
            if mons is None:
                continue
            for _, vs in mons:
                if len(vs) <= target:
                    continue
                visto = set()
                for i in range(len(vs)):
                    for j in range(i + 1, len(vs)):
                        cl = tuple(sorted([str(vs[i]), str(vs[j])]))
                        if cl in visto:
                            continue
                        visto.add(cl)
                        cuenta[cl] = cuenta.get(cl, 0) + 1
        if not cuenta:
            break
        top = max(cuenta.values())
        candidatos = sorted(k for k, v in cuenta.items() if v == top)
        cl = rnd.choice(candidatos) if rnd is not None else candidatos[0]
        a, b = simbolos[cl[0]], simbolos[cl[1]]
        w = _fresh_flat()
        simbolos[str(w)] = w
        orden.append((w, a, b))
        definitorias.append(sympy.expand(w - a * b))
        for mons in desc:
            if mons is None:
                continue
            for m in mons:
                vs = m[1]
                while len(vs) > target:
                    nombres = [str(x) for x in vs]
                    if str(a) in nombres and str(b) in nombres:
                        nuevo = list(vs)
                        nuevo.remove(a)
                        try:
                            nuevo.remove(b)
                        except ValueError:
                            break
                        nuevo.append(w)
                        vs = nuevo
                        m[1] = vs
                    else:
                        break

    eqs_out = []
    for mons in desc:
        if mons is None:
            continue
        acc = sympy.Integer(0)
        for coef, vs in mons:
            t = coef
            for v in vs:
                t = t * v
            acc = acc + t
        eqs_out.append(sympy.expand(acc))

    def w_ext(param_vals):
        if system.witness is None:
            return None
        base = system.witness(param_vals)
        if base is None:
            return None
        entorno = dict(param_vals); entorno.update(base)
        out = dict(base)
        for w, a, b in orden:
            val = _valor_o_none(a * b, entorno)   # None -> testigo parcial
            if val is None:
                continue
            out[w] = val
            entorno[w] = val
        return out

    return Dioph(system.params, list(system.unknowns) + [w for w, _, _ in orden],
                 eqs_out + definitorias, witness=w_ext,
                 name=f"{system.name} [voraz semilla={semilla}]")


def flatten_search(system, target=2, intentos=100, objetivos=(8, 10, 3, 2), verbose=False):
    """Busca el mejor aplanado sobre dos ejes: objetivo intermedio y desempate.

    El aplanado minimo es optimizacion combinatoria, no una formula. Aqui se
    explora el espacio con lo que ya esta verificado:

      * `objetivos`: grado intermedio al que se aplana primero por ARBOL antes de
        rematar con el voraz. Medido sobre JSWW, el optimo esta en 8-11 y se
        degrada fuera; encadenar los dos gana a cualquiera por separado.
      * `intentos`: reinicios del voraz con desempate aleatorio distinto.

    Devuelve el Dioph con MENOS incognitas de todos los probados. Es una busqueda,
    no una garantia: no se afirma que sea el minimo.
    """
    mejor = None
    for d in objetivos:
        try:
            base = flatten_tree(system, d) if d > target else system
        except Exception:
            continue
        for s in range(intentos):
            try:
                F = flatten_greedy_semilla(base, target, semilla=s)
            except Exception:
                continue
            if max_equation_degree(F) > target:
                continue
            if mejor is None or F.cost() < mejor.cost():
                mejor = F
                if verbose:
                    print(f"    objetivo={d} semilla={s} -> {F.cost()} incognitas")
    return mejor if mejor is not None else flatten_greedy(system, target)


# NOTA sobre dos funciones RETIRADAS, para que nadie las reinvente:
#
#   * `flatten_hybrid` (aplanado por arbol + reescritura con monomios ya
#     nombrados). La idea era correcta --el arbol nombra `(a+1)^2` y `a^2` por
#     separado cuando el primero es de grado 1 si el segundo ya existe-- pero la
#     implementacion se colgaba: `subs` no reduce potencias dentro de monomios y
#     hay que trabajar con vectores de exponentes. La superó `dioph_optflat`,
#     que resuelve el mismo problema de forma EXACTA y con cota inferior.
#   * `eliminar_redundantes` (quitar a posteriori los nombres expresables con
#     otros). Medido: no eliminaba ninguno. El optimizador exacto ya no los crea.
#
# Se retiran en vez de dejarlas rotas: este modulo es una capacidad del proyecto,
# y codigo muerto en una capacidad es un pasivo.
