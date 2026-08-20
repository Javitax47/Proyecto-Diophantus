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
