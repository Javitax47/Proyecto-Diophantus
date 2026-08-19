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
