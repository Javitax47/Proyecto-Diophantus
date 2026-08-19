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
          extra=None, rlimit=20_000_000):
    """Pregunta a Z3 si `system` tiene solucion con los parametros fijados.

    over_N   : anade x >= 0 para toda incognita (el dominio en que vive todo
               este calculo; el generador n*(1-sum P^2) lo EXIGE).
    bound    : si no es None, anade x <= bound. Debilita el 'unsat' a
               'unsat dentro de la caja'. Se refleja en el informe.
    extra    : lista de expresiones sympy que deben anularse ADEMAS (para
               unicidad se usa su negacion, ver `uniqueness_report`).

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
    except TraduccionImposible as exc:
        return {"estado": "no_traducible", "modelo": str(exc),
                "acotado": bound is not None}

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

    Se pregunta por `system AND objetivo != valor_esperado`:
        unsat   -> el valor es UNICO: el subsistema calcula, no solo admite.
        sat     -> DEFECTO: existe un valor espurio (el modelo lo exhibe).
        unknown -> no concluye.

    `objetivo` es un simbolo (o expresion) del sistema; `valor_esperado`, un int.
    Es la pregunta que decide si una cadena larga es sound: un solo eslabon que
    admita un valor espurio deja pasar todo lo que venga detras.
    """
    dif = sympy.expand(objetivo - sympy.Integer(int(valor_esperado)))
    r = solve(system, param_vals, over_N=over_N, bound=bound,
              timeout_ms=timeout_ms, extra=[dif], rlimit=rlimit)
    if r["estado"] == "unsat":
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
