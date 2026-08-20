"""
================================================================================
   DIOPHANTUS - SOUNDNESS Y UNICIDAD POR SMT (universal, no especifico de primos)
================================================================================
El punto ciego de todo el calculo diofantico construido hasta aqui:

    COMPLETITUD (pertenece => hay testigo) se verifica CONSTRUYENDO el testigo.
    SOUNDNESS   (no pertenece => NO hay testigo) no se verificaba casi nunca,
                porque exige demostrar que un sistema NO tiene solucion, y las
                incognitas viven en rangos astronomicos (r > (n+1)^(n+1)).

Una busqueda exhaustiva no puede tocar ese rango. Un demostrador SMT si: no
enumera, razona. Este modulo traduce cualquier `Dioph` a Z3 y pregunta por
INSATISFACIBILIDAD. Tres resultados posibles, y los tres se reportan tal cual:

    'unsat'   -> DEMOSTRADO que no hay solucion (lo que queriamos para soundness)
    'sat'     -> hay solucion; si el oraculo dice que no deberia, es un DEFECTO
    'unknown' -> Z3 no concluye (la aritmetica entera no lineal es indecidible;
                 esto NO es evidencia a favor ni en contra)

DOS PREGUNTAS DISTINTAS, ambas universales:

 1. SOUNDNESS   `soundness_report`: para v que NO pertenece al conjunto,
    el sistema con param=v debe ser insatisfacible.
 2. UNICIDAD    `uniqueness_report`: un subsistema que "calcula" y = f(x)
    debe FORZAR ese valor. Se comprueba pidiendo `sistema AND y != f(x)`:
    si es unsat, el valor es unico. Es el riesgo real de una cadena larga
    (Wilson -> factorial -> binomial -> exponencial): que un eslabon admita
    un valor espurio y deje pasar un compuesto.

HONESTIDAD: 'unsat' con cota (`bound`) demuestra la ausencia de solucion SOLO
dentro de la caja. Sin cota la afirmacion es global. `bound=None` es lo fuerte;
la cota es el plan B cuando Z3 no concluye. El informe siempre dice cual se uso.
"""

import sympy

try:
    import z3
    Z3_DISPONIBLE = True
except ImportError:                                   # pragma: no cover
    z3 = None
    Z3_DISPONIBLE = False


# ---------------------------------------------------------------------------
#   TRADUCTOR sympy -> Z3  (universal: cualquier polinomio entero)
# ---------------------------------------------------------------------------

UMBRAL_EXPANSION = 20     # incognitas por encima de las cuales NO se expande


class TraduccionImposible(Exception):
    """La expresion no es un polinomio entero traducible (p. ej. exponente simbolico)."""


def sympy_to_z3(expr, varmap):
    """Traduce un polinomio sympy a una expresion Z3 entera.

    varmap: dict {simbolo sympy -> z3.Int}. Se rellena sobre la marcha.
    Solo acepta Add / Mul / Pow-con-exponente-entero-no-negativo / Integer /
    Rational-entero / Symbol. Cualquier otra cosa levanta TraduccionImposible:
    preferimos fallar ruidosamente a traducir mal.
    """
    if isinstance(expr, sympy.Symbol):
        if expr not in varmap:
            varmap[expr] = z3.Int(str(expr))
        return varmap[expr]
    if isinstance(expr, (sympy.Integer, int)):
        return z3.IntVal(int(expr))
    if isinstance(expr, sympy.Rational):
        if expr.q != 1:
            raise TraduccionImposible(f"racional no entero: {expr}")
        return z3.IntVal(int(expr.p))
    if isinstance(expr, sympy.Add):
        term = sympy_to_z3(expr.args[0], varmap)
        for a in expr.args[1:]:
            term = term + sympy_to_z3(a, varmap)
        return term
    if isinstance(expr, sympy.Mul):
        term = sympy_to_z3(expr.args[0], varmap)
        for a in expr.args[1:]:
            term = term * sympy_to_z3(a, varmap)
        return term
    if isinstance(expr, sympy.Pow):
        base, exp = expr.args
        if not (exp.is_Integer and int(exp) >= 0):
            raise TraduccionImposible(f"exponente no entero no negativo: {expr}")
        e = int(exp)
        if e == 0:
            return z3.IntVal(1)
        b = sympy_to_z3(base, varmap)
        out = b
        for _ in range(e - 1):
            out = out * b
        return out
    raise TraduccionImposible(f"nodo no soportado: {type(expr).__name__} en {expr}")


# ---------------------------------------------------------------------------
#   CONSULTA BASICA: tiene solucion el sistema?
# ---------------------------------------------------------------------------

def solve(system, param_vals, over_N=True, bound=None, timeout_ms=10000,
          extra=None, rlimit=20_000_000, fijar=None, igualdades=None):
    """Pregunta a Z3 si `system` tiene solucion con los parametros fijados.

    over_N   : anade x >= 0 para toda incognita (el dominio en que vive todo
               este calculo; el generador n*(1-sum P^2) lo EXIGE).
    bound    : si no es None, anade x <= bound. Debilita el 'unsat' a
               'unsat dentro de la caja'. Se refleja en el informe.
    extra    : lista de expresiones sympy que deben ser DISTINTAS de cero (para
               unicidad se usa la diferencia con el valor esperado).
    fijar    : dict {simbolo: valor} que CLAVA incognitas. Sirve para preguntar
               por una configuracion concreta ("y existe solucion con a = 0?"),
               que es la forma exacta de vigilar un defecto conocido: mucho mas
               barata y mas precisa que barrer una caja.

    Devuelve dict {estado, modelo, acotado}. Nunca lanza por 'unknown'.
    """
    if not Z3_DISPONIBLE:
        return {"estado": "sin_z3", "modelo": None, "acotado": bound is not None}

    varmap = {}
    solver = z3.Solver()
    # DOS limites, no uno. `timeout` es de reloj y nlsat (aritmetica entera no
    # lineal) puede pasarselo por alto durante mucho rato; `rlimit` es un
    # presupuesto DETERMINISTA de trabajo interno y ademas hace reproducible el
    # veredicto entre maquinas. Sin el, un test de la suite podia colgarse.
    solver.set("timeout", timeout_ms)
    solver.set("rlimit", rlimit)

    sust = {s: sympy.Integer(int(v)) for s, v in param_vals.items()}
    try:
        # EXPANDIR O NO: expandir ayuda a Z3 (nlsat trabaja mejor sobre la forma
        # desarrollada) pero en un sistema de grado 8 con decenas de incognitas
        # explota en tiempo y memoria. Se expande solo por debajo del umbral, y
        # el umbral se elige por el numero de incognitas, no por adivinacion.
        expandir = len(system.unknowns) <= UMBRAL_EXPANSION
        prep = (lambda e: sympy.expand(e.subs(sust))) if expandir else (lambda e: e.subs(sust))
        for e in system.eqs:
            solver.add(sympy_to_z3(prep(e), varmap) == 0)
        for e in (extra or []):
            solver.add(sympy_to_z3(prep(e), varmap) != 0)
        for e in (igualdades or []):      # deben anularse ADEMAS de las del sistema
            solver.add(sympy_to_z3(prep(e), varmap) == 0)
    except TraduccionImposible as exc:
        return {"estado": "no_traducible", "modelo": str(exc),
                "acotado": bound is not None}

    for sym, val in (fijar or {}).items():
        if sym not in varmap:
            varmap[sym] = z3.Int(str(sym))
        solver.add(varmap[sym] == int(val))
    for s in system.unknowns:
        if s not in varmap:                    # incognita que no aparece: irrelevante
            continue
        if over_N:
            solver.add(varmap[s] >= 0)
        if bound is not None:
            solver.add(varmap[s] <= int(bound))

    res = solver.check()
    if res == z3.sat:
        modelo = {}
        m = solver.model()
        for s, zv in varmap.items():
            val = m.eval(zv, model_completion=True)
            try:
                modelo[str(s)] = val.as_long()
            except AttributeError:             # pragma: no cover
                modelo[str(s)] = str(val)
        return {"estado": "sat", "modelo": modelo, "acotado": bound is not None}
    if res == z3.unsat:
        return {"estado": "unsat", "modelo": None, "acotado": bound is not None}
    return {"estado": "unknown", "modelo": None, "acotado": bound is not None}


# ---------------------------------------------------------------------------
#   PREGUNTA 1: SOUNDNESS  (no pertenece => no hay testigo)
# ---------------------------------------------------------------------------

def soundness_report(prob, valores, over_N=True, bound=None, timeout_ms=10000,
                     cotas_de_reserva=(200, 20), rlimit=20_000_000,
                     intentar_sin_cota=True):
    """Para cada v de `valores` que NO pertenece al conjunto, exige 'unsat'.

    ESCALADA. Primero se pregunta SIN cota: un 'unsat' ahi es global y es lo
    fuerte. La aritmetica entera no lineal es indecidible, asi que Z3 devuelve
    'unknown' a menudo; en ese caso se reintenta dentro de cajas cada vez mas
    pequenas (`cotas_de_reserva`). Un 'unsat' con cota B solo dice "no hay
    solucion con todas las incognitas en [0,B]" -- pero es exactamente donde
    vivian las soluciones degeneradas del defecto que motivo este modulo
    (a in {0,1}, (x,y) = (1,0)), asi que sirve de red de seguridad.

    El estado devuelto lleva la cota: 'unsat' o 'unsat<=200'. Un 'sat' SIEMPRE
    es un defecto, con o sin cota. 'unknown' no es evidencia de nada.
    """
    filas, defectos = [], []
    for v in valores:
        pertenece = bool(prob.oracle(v))
        if pertenece:
            continue                            # esta direccion la cubre el testigo
        if bound is not None:
            intentos = [bound]
        else:
            # `intentar_sin_cota=False` para sistemas grandes: el intento global
            # es donde Z3 quema el tiempo sin concluir, y las cajas pequenas son
            # justo donde vivian las soluciones degeneradas del defecto.
            intentos = ([None] if intentar_sin_cota else []) + list(cotas_de_reserva)
        estado = "unknown"
        for b in intentos:
            r = solve(prob.system, {prob.param: v}, over_N=over_N,
                      bound=b, timeout_ms=timeout_ms, rlimit=rlimit)
            if r["estado"] == "sat":
                estado = "sat"
                defectos.append(f"{v} NO pertenece pero Z3 hallo solucion: {r['modelo']}")
                break
            if r["estado"] == "unsat":
                estado = "unsat" if b is None else f"unsat<={b}"
                break
            estado = r["estado"]
        filas.append((v, pertenece, estado))
    return (len(defectos) == 0), filas, defectos


# ---------------------------------------------------------------------------
#   PREGUNTA 2: UNICIDAD  (el subsistema FUERZA el valor calculado?)
# ---------------------------------------------------------------------------

def uniqueness_report(system, param_vals, objetivo, valor_esperado,
                      over_N=True, bound=None, timeout_ms=10000,
                      rlimit=20_000_000):
    """El sistema, ademas de admitir `objetivo = valor_esperado`, lo FUERZA?

    DOS consultas, y la segunda existe para que la primera no mienta:

      (1) ALCANZABILIDAD: `sistema AND objetivo == valor_esperado` debe ser SAT.
      (2) UNICIDAD:       `sistema AND objetivo != valor_esperado` debe ser UNSAT.

    Sin (1), un 'unsat' en (2) es VACUO: si dentro de la caja no hay ninguna
    solucion --ni siquiera la buena, porque los testigos reales son astronomicos--
    entonces "no hay solucion con un valor distinto" es trivialmente cierto y no
    dice nada. Ese es exactamente el tipo de falso consuelo que ya costo caro en
    este proyecto, asi que el veredicto lo declara:

      'unico'   -> alcanzable Y sin alternativas: el subsistema CALCULA el valor
      'ESPURIO' -> hay una solucion con otro valor (el modelo lo exhibe)
      'vacuo'   -> ni siquiera el valor correcto es alcanzable en la caja: la
                   comprobacion no prueba nada
      'unknown' -> Z3 no concluye
    """
    dif = sympy.expand(objetivo - sympy.Integer(int(valor_esperado)))
    alcanzable = solve(system, param_vals, over_N=over_N, bound=bound,
                       timeout_ms=timeout_ms, rlimit=rlimit,
                       fijar=None, extra=None, igualdades=[dif])
    r = solve(system, param_vals, over_N=over_N, bound=bound,
              timeout_ms=timeout_ms, extra=[dif], rlimit=rlimit)
    r["alcanzable"] = alcanzable["estado"]
    if alcanzable["estado"] != "sat":
        r["veredicto"] = "vacuo"
    elif r["estado"] == "unsat":
        r["veredicto"] = "unico"
    elif r["estado"] == "sat":
        r["veredicto"] = "ESPURIO"
    else:
        r["veredicto"] = r["estado"]
    return r


def resumen(filas):
    """Cuenta estados de un informe: {'unsat': n, 'sat': n, 'unknown': n, ...}."""
    out = {}
    for f in filas:
        est = f[-1]
        out[est] = out.get(est, 0) + 1
    return out


# ---------------------------------------------------------------------------
#   PREGUNTA 3: la CONFIGURACION del defecto conocido sigue excluida?
# ---------------------------------------------------------------------------

def refuta_configuracion(system, param_vals, fijar, timeout_ms=10000,
                         rlimit=20_000_000, over_N=True):
    """El sistema debe ser INSATISFACIBLE al clavar `fijar`.

    Por que esto y no una caja: el defecto que motivo este modulo tenia una
    FIRMA concreta -- la base de Pell degeneraba con a in {0,1}, y entonces
    (x,y) = (1,0) resolvia la ecuacion para cualquier a. Preguntar "hay solucion
    con a = 0?" es una consulta SIN COTA, instantanea y exactamente dirigida al
    fallo; barrer [0,B] es caro, no concluye siempre, y aun asi solo cubre la
    caja. Un guardarrail debe apuntar al defecto, no a su vecindario.

    Devuelve el estado ('unsat' es lo que se quiere; 'sat' es el defecto vivo).
    """
    r = solve(system, param_vals, over_N=over_N, bound=None,
              timeout_ms=timeout_ms, rlimit=rlimit, fijar=fijar)
    return r


def cota_desde_testigo(system, param_vals, factor=4, minimo=50):
    """Cota para la caja de Z3 derivada del TESTIGO REAL, no elegida a ojo.

    Motivo, aprendido a base de un falso positivo: una cota fija deja fuera la
    solucion buena en cuanto los testigos crecen (los de Pell crecen
    exponencialmente en el indice), y entonces la comprobacion de unicidad se
    vuelve VACUA -- 'no hay solucion con otro valor' es trivialmente cierto si no
    hay ninguna solucion. `uniqueness_report` lo detecta y lo llama 'vacuo'; esta
    funcion sirve para evitarlo desde el principio.

    Devuelve `factor * max(valores del testigo)`, o None si no hay testigo.
    """
    if system.witness is None:
        return None
    w = system.witness(param_vals)
    if not w:
        return None
    mayor = max(int(v) for v in w.values()) if w else 0
    return max(minimo, factor * mayor)


# ---------------------------------------------------------------------------
#   PREGUNTA 4: UNICIDAD POR ENUMERACION ESTRUCTURADA (donde el SMT no llega)
# ---------------------------------------------------------------------------

def unicidad_exponencial_psi(b, k, c_max):
    """Lo mismo que `unicidad_exponencial`, pero para el lema RECONSTRUIDO.

    QUE CAMBIA. `L_exponential` fijaba el indice con `y == k (mod a-1)`, asi que
    la enumeracion tenia que recorrer TODOS los m congruentes con k, y cada uno
    aportaba su propio c espurio. `L_exponential_psi` fija el indice con `L_psi`,
    que fuerza Y = psi_a(k) para el k exacto: el bucle en m desaparece y solo
    queda el barrido en c.

    QUE SE COMPRUEBA Y QUE SE SUPONE, que no es lo mismo:

      * SE SUPONE, y esta comprobado aparte en `test_dioph_soundness` [9] por
        barrido directo sobre el sistema de 9 ecuaciones: que `L_psi(a,k,Y)`
        implica Y = y_k(a). Aqui se usa como oraculo.
      * SE COMPRUEBA aqui: que, dado eso, el resto del sistema --Pell para X, la
        congruencia de Davis y la cota lineal sobre `a`-- deja UN SOLO c posible.
        Cada candidato se confirma evaluando las ecuaciones REALES del sistema
        que no mencionan incognitas internas de L_psi (`Dioph.holds` sobre esa
        parte), no la enumeracion.

    Por que la comprobacion se parte en dos. Los testigos de L_psi salen del
    rango de aparicion y son astronomicos incluso en casos de juguete (certificar
    y_2(3)=6 exige l=408); evaluarlos para cada candidato del barrido no es
    viable. Partirlo permite comprobar cada mitad con la herramienta adecuada en
    lugar de no comprobar ninguna.

    Devuelve la lista de c admisibles. Si sale [b**k], el lema calcula el valor.
    """
    import sympy
    from src.analysis.dioph_lemmas import L_exponential_psi, pell_seq, L_psi

    bs, ks, cs = sympy.symbols('b k c', integer=True)
    S = L_exponential_psi(bs, ks, cs, over_N=True)

    # Las incognitas internas de L_psi: se identifican por el prefijo con el que
    # `fresh` las bautiza. Las ecuaciones que las mencionan son justo las que
    # este barrido delega en el oraculo.
    internas = {u for u in S.unknowns if str(u).startswith('p')}
    eqs_visibles = [e for e in S.eqs if not (e.free_symbols & internas)]
    visibles = sorted({u for e in eqs_visibles for u in e.free_symbols} & set(S.unknowns),
                      key=str)

    admisibles = []
    for c in range(0, c_max + 1):
        a = b + c + k + 2
        if a < 2:
            continue
        M = 2 * a * b - b * b - 1
        if M <= 0:
            continue
        x, y = pell_seq(a, k)          # ORACULO: L_psi fuerza Y = y_k(a)
        r = (x - (a - b) * y) - c
        if r < 0 or r % M != 0:
            continue
        asign = {bs: b, ks: k, cs: c}
        for u in visibles:
            nombre = str(u)
            if nombre.startswith('ea'):
                asign[u] = a
            elif nombre.startswith('ex'):
                asign[u] = x
            elif nombre.startswith('ey'):
                asign[u] = y
            elif nombre.startswith('es'):
                asign[u] = r // M
            else:                       # holguras de las desigualdades laterales
                asign[u] = None
        # holguras: se resuelven a partir de su propia ecuacion, que sobre N es
        # `expr - holgura = 0` con expr >= 0.
        for e in eqs_visibles:
            libres = [u for u in e.free_symbols & set(visibles) if asign.get(u) is None]
            if len(libres) == 1:
                h = libres[0]
                resto = e.subs({u: v for u, v in asign.items() if v is not None})
                sol = sympy.solve(sympy.Eq(resto, 0), h)
                if sol and int(sol[0]) >= 0:
                    asign[h] = int(sol[0])
        if any(v is None for v in asign.values()):
            continue
        if all(sympy.expand(e.subs(asign)) == 0 for e in eqs_visibles):
            admisibles.append(c)
    return admisibles


def unicidad_exponencial(b, k, c_max, m_max=300, a0_max=0):
    """Para que valores de c tiene solucion REALMENTE el sistema de `c = b^k`?

    POR QUE NO BASTA EL SMT. Medido: `uniqueness_report` sobre este lema solo
    concluye de forma no vacua en el caso mas pequeno (2^2). Los testigos de Pell
    crecen exponencialmente en el indice, la caja necesaria se dispara, y Z3
    devuelve 'unknown' o la solucion buena se queda fuera de la caja. Una busqueda
    ciega tampoco sirve: 7 incognitas en cajas de decenas de miles.

    POR QUE ESTA ENUMERACION SI. El sistema no es una caja negra; su estructura
    fija casi todo:

        a  = a0 + k + b + c + 2       (la reparametrizacion lo determina)
        (x, y) = (x_m(a), y_m(a))     unicas soluciones de x^2-(a^2-1)y^2 = 1
                                       con a >= 2   [teorema clasico de Pell]
        y >= k,  y == k (mod a-1)     ecuacion del indice, con t >= 0
        x - (a-b)y - c == 0 (mod M)   congruencia de Davis, con s >= 0

    Se recorre c en [0, c_max] y m en [0, m_max], y **cada candidato se confirma
    evaluando el sistema real** (`Dioph.holds`), no la enumeracion. Devuelve la
    lista de c admisibles: si sale [b^k], el lema calcula el valor; si sale mas,
    hay valores espurios.

    ESTADO CONOCIDO (agosto 2026): SALE MAS. Ver `test_dioph_soundness.py` [8].
    """
    import sympy
    from src.analysis.dioph_lemmas import L_exponential, pell_seq

    bs, ks, cs = sympy.symbols('b k c', integer=True)
    S = L_exponential(bs, ks, cs, over_N=True)
    A0, X, Y0, t, sl = S.unknowns[:5]
    holguras = S.unknowns[5:]

    admisibles = []
    for c in range(0, c_max + 1):
        encontrado = False
        for a0 in range(a0_max + 1):
            a = a0 + k + b + c + 2
            if a < 2:
                continue
            M = 2 * a * b - b * b - 1
            if M <= 0:
                continue
            for m in range(0, m_max + 1):
                x, y = pell_seq(a, m)
                if y < 1 or y < k or (y - k) % (a - 1) != 0:
                    continue
                r = (x - (a - b) * y) - c
                if r < 0 or r % M != 0:
                    continue
                asign = {bs: b, ks: k, cs: c, A0: a0, X: x, Y0: y - 1,
                         t: (y - k) // (a - 1), sl: r // M}
                for h, val in zip(holguras, (k - 1, b - 2)):
                    asign[h] = val
                if S.holds(asign):        # confirmacion contra el sistema REAL
                    encontrado = True
                    break
            if encontrado:
                break
        if encontrado:
            admisibles.append(c)
    return admisibles
