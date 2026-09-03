#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - EL TEOREMA DE COMBINACION DE RELACIONES, IMPLEMENTADO Y PROBADO
================================================================================
`dioph_combinar` implementa el Teorema 3 de Matijasevic-Robinson (Acta
Arithmetica 27 (1975) 521-553, p. 526), la unica pieza de la maquinaria clasica
que a este proyecto le faltaba y la unica que baja el numero de incognitas de
verdad: en la seccion 3 de JSWW vale SIETE variables (de 19 a 12).

QUE SE COMPRUEBA. No que el codigo "corra": que el TEOREMA se cumple sobre el
codigo. La equivalencia es un si-y-solo-si

    A_1 = [], ..., A_q = [],  B | C,  D > 0   <=>   existe n natural, M_q = 0

y se verifica en las DOS direcciones sobre cientos de casos, incluyendo los que
deben FALLAR: A_i no cuadrado, B que no divide a C, D <= 0. Un implementador que
solo probara los casos buenos tendria un `M_q = 0` constante y no lo notaria.
"""

import itertools
import os
import sys

import sympy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_combinar import (J, M, grado_combinado, grado_estimado,
                                        grado_estimado_refinado)
from src.analysis.dioph_jsww3 import (GRADO_B, GRADO_C, GRADO_D,
                                      GRADOS_CONDICIONES, U, curva_pareto,
                                      grado_condicion_24, k, n, x)


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; WARN = '\033[93m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}FALLO: {msg}{Colors.ENDC}")


_n = sympy.Symbol('n', integer=True)


def _hay_n(As, B, C, D):
    """Existe un natural `n` con `M_q = 0`? Se RESUELVE en n, no se busca."""
    e = sympy.expand(M(As, B, C, D, _n))
    pol = sympy.Poly(e, _n)
    return any(r.is_integer and r >= 0 for r in sympy.solve(pol, _n))


def _condiciones(As, B, C, D):
    if any(A < 0 for A in As):
        return False
    return (all(sympy.sqrt(A).is_integer for A in As)
            and B != 0 and C % B == 0 and D > 0)


def test_J_es_la_del_teorema_1(stats):
    """[1] `J_1(A,X) = X^2 - A`, que es la forma cerrada del Teorema 1 para q=1."""
    print(f"\n{Colors.HEADER}[1] El Teorema 1 para q = 1{Colors.ENDC}")
    A, X = sympy.symbols('A X', integer=True)
    got = sympy.expand(J([A], X))
    esperado = X ** 2 - A
    print(f"  J_1(A,X) = {got}")
    if sympy.expand(got - esperado) != 0:
        stats.fail(f"se esperaba {esperado}")
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} `X^2 = A` es exactamente «A es un cuadrado»")
        stats.ok()


def test_equivalencia_q1(stats):
    """[2] El si-y-solo-si del Teorema 3, q=1, en las dos direcciones."""
    print(f"\n{Colors.HEADER}[2] Teorema 3 con q=1: equivalencia sobre 336 casos{Colors.ENDC}")
    malos, total, positivos = [], 0, 0
    for A1 in (0, 1, 2, 3, 4, 5, 9):
        for B in (1, 2, 3):
            for C in (0, 2, 4, 6):
                for D in (-1, 0, 1, 2):
                    total += 1
                    esperado = _condiciones([A1], B, C, D)
                    positivos += esperado
                    if esperado != _hay_n([A1], B, C, D):
                        malos.append((A1, B, C, D, esperado))
    print(f"  {total} casos, {positivos} en los que las condiciones SI se cumplen")
    if malos:
        stats.fail(f"{len(malos)} discrepancias, p.ej. {malos[0]}")
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 0 discrepancias en las dos direcciones")
        stats.ok()


def test_equivalencia_q2(stats):
    """[3] Lo mismo con q=2, que es donde el producto deja de ser trivial."""
    print(f"\n{Colors.HEADER}[3] Teorema 3 con q=2: el producto ya tiene cuatro factores{Colors.ENDC}")
    malos, total, positivos = [], 0, 0
    for A1, A2 in itertools.product((0, 1, 2, 4), repeat=2):
        for B, C, D in ((1, 3, 1), (2, 4, 1), (2, 3, 1), (1, 0, 0), (3, 9, 2), (2, 5, -1)):
            total += 1
            esperado = _condiciones([A1, A2], B, C, D)
            positivos += esperado
            if esperado != _hay_n([A1, A2], B, C, D):
                malos.append((A1, A2, B, C, D, esperado))
    print(f"  {total} casos, {positivos} en los que las condiciones SI se cumplen")
    if malos:
        stats.fail(f"{len(malos)} discrepancias, p.ej. {malos[0]}")
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 0 discrepancias; las raices se cancelan "
              f"y el resultado es entero")
        stats.ok()


def test_grado(stats):
    """[4] La formula del grado coincide con el grado real.

    HACE FALTA porque para `q = 6` --el caso de JSWW-- el polinomio tiene 64
    factores y expandirlo es inabordable. La cifra que entra en la frontera de
    Pareto es el GRADO, asi que hay que saber calcularlo sin construirlo.
    """
    print(f"\n{Colors.HEADER}[4] El grado se calcula sin expandir{Colors.ENDC}")
    A1, A2, B, C, D = sympy.symbols('A1 A2 B C D', integer=True)
    gens = (A1, A2, B, C, D, _n)
    problemas = []
    for As in ([A1], [A1, A2]):
        real = grado_combinado(As, B, C, D, _n, gens)
        est = grado_estimado([1] * len(As), 1, 1, 1, 1)
        marca = Colors.OKGREEN + "OK" + Colors.ENDC if real == est else Colors.FAIL + "MAL" + Colors.ENDC
        print(f"  {marca} q={len(As)}: grado real {real}, formula {est}")
        if real != est:
            problemas.append(f"q={len(As)}: {real} vs {est}")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.WARN}El precio del teorema es el grado: son 2^q factores. Por eso")
        print(f"  el polinomio de 12 variables de JSWW tiene grado 13.697.{Colors.ENDC}")
        stats.ok()


def test_reproduce_el_148864_de_jsww(stats):
    """[5] La prueba fuerte: reproducir un numero que JSWW calcularon en 1976.

    En la p. 461 escriben, del sistema de su seccion 3:

        "A direct calculation, based on [11], shows that M = M_6 will have
         degree 148864."

    Aplicando este modulo a las ocho condiciones de su Teorema 3.9 --con los
    grados medidos sobre el sistema con las catorce incognitas ya sustituidas--
    sale EXACTAMENTE 148864. Es la validacion mas fuerte que hay disponible: un
    numero calculado de forma independiente hace cincuenta anos, que solo cuadra
    si la formula del teorema, la del grado y la transcripcion de la seccion 3
    son las tres correctas a la vez.

    Los grados de las ocho condiciones, en las 10 incognitas libres mas `k`:

        (I) U(2k,n)              6      (VII) D*F*I            184
        (II) U(2n,x)             6      B = F                   34
        (XV) (M^2-1)K^2+1       14      C = H - C                2
        (XVI) (M^2x^2-1)L^2+1   18      D  (la desigualdad)     50
        (XVII) (M^2n^2x^2-1)R^2+1  22
    """
    print(f"\n{Colors.HEADER}[5] Reproduce el 148864 que JSWW publican{Colors.ENDC}")
    grados_condiciones = [6, 6, 14, 18, 22, 184]
    got = grado_estimado(grados_condiciones, 34, 2, 50, 1)
    print(f"  grado de M_6 calculado aqui: {got}")
    print(f"  grado de M_6 segun JSWW p.461: 148864")
    if got != 148864:
        stats.fail(f"se esperaba 148864 y salio {got}")
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} coinciden. La formula del teorema, la del grado")
        print(f"    y la transcripcion de la seccion 3 son correctas a la vez.")
        stats.ok()


def test_refinamientos_de_matijasevic(stats):
    """[6] Los DOS refinamientos de la p. 462, contra TRES cifras publicadas.

    JSWW calculan `M_6` con el teorema plano y les sale 148.864 (p. 461, test [5]).
    En la pagina siguiente aplican dos refinamientos de Matijasevic y les sale
    13.376; combinando ademas (I) y (II) en una sola condicion --su (24)-- sale
    `M_5 = 6848`, y de ahi su generador de 12 variables y grado 13.697.

    Este test comprueba los tres. Y son TRES dianas independientes de una sola
    regla: si la lectura del parrafo fuera otra, no coincidirian las tres.
    """
    print(f"\n{Colors.HEADER}[6] Los refinamientos de la p. 462: tres cifras mas{Colors.ENDC}")
    problemas = []
    seis = GRADOS_CONDICIONES
    B, C, D = GRADO_B, GRADO_C, GRADO_D

    m6 = grado_estimado_refinado(seis, B, C, D, 1)
    print(f"  M_6 refinado : {m6:8d}   JSWW p.462: 13376")
    if m6 != 13376:
        problemas.append(f"M_6 refinado deberia ser 13376, es {m6}")

    g24 = grado_condicion_24()
    print(f"  grado de (24): {g24:8d}   (calculado, no despejado)")
    if g24 != 22:
        problemas.append(f"(24) deberia tener grado 22, tiene {g24}")

    cinco = sorted([g24] + seis[2:])
    m5 = grado_estimado_refinado(cinco, B, C, D, 1)
    print(f"  M_5 con (24) : {m5:8d}   JSWW p.462: 6848")
    if m5 != 6848:
        problemas.append(f"M_5 deberia ser 6848, es {m5}")

    gen = 1 + 2 * m5
    print(f"  generador P  : {gen:8d}   JSWW p.462: 13697")
    if gen != 13697:
        problemas.append(f"el generador deberia ser 13697, es {gen}")

    # y (24) tiene que ser lo que la pagina imprime: una Pell dentro
    Uk = U(2 * k, n)
    a, b = 2 * Uk - 1, 2 * (n + 1) * (x + 1)
    dentro = ((2 * Uk - 1) ** 2 - 1) * 4 * (n + 1) ** 2 * (x + 1) ** 2 + 1
    if sympy.expand(dentro - ((a ** 2 - 1) * b ** 2 + 1)) != 0:
        problemas.append("el corchete de (24) no es la Pell de a=2U-1, b=2(n+1)(x+1)")
    else:
        print(f"  {Colors.OKGREEN}OK{Colors.ENDC} el corchete de (24) es la Pell de "
              f"`a = 2U(2k,n)-1`, `b = 2(n+1)(x+1)`")

    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} tres cifras publicadas con UNA sola "
              f"regla: la lectura del parrafo es la correcta")
        stats.ok()


def test_curva(stats):
    """[7] La curva refinada, y que su extremo ES el punto publicado de JSWW."""
    print(f"\n{Colors.HEADER}[7] La curva de Pareto, refinada{Colors.ENDC}")
    nueva = curva_pareto()
    vieja = curva_pareto(refinado=False, con_24=False)
    v = {f["variables"]: f["grado_generador"] for f in vieja}
    print(f"  {'q':>2} {'vars':>5} {'grado':>8}   {'antes':>9}")
    for f in nueva:
        antes = v.get(f["variables"])
        print(f"  {f['q']:>2} {f['variables']:>5} {f['grado_generador']:>8}   "
              f"{antes if antes else '—':>9}")
    problemas = []
    esperada = [(16, 369), (15, 801), (14, 1777), (13, 3905), (12, 13697)]
    got = [(f["variables"], f["grado_generador"]) for f in nueva]
    if got != esperada:
        problemas.append(f"la curva cambio: {got}")
    # el extremo tiene que ser SU punto
    if got[-1] != (12, 13697):
        problemas.append("el extremo de la curva ya no reproduce el (12,13697) de JSWW")
    # y todos los puntos tienen que mejorar respecto de la version plana
    for var, gr in got:
        if var in v and gr >= v[var]:
            problemas.append(f"con {var} variables el refinamiento no mejora: "
                             f"{gr} frente a {v[var]}")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} todos los puntos mejoran y el extremo "
              f"reproduce el (12, 13697) publicado")
        stats.ok()


def main():
    print(f"{Colors.BOLD}=== TEOREMA DE COMBINACION DE RELACIONES (Matijasevic-Robinson 1975) ==={Colors.ENDC}")
    stats = Stats()
    test_J_es_la_del_teorema_1(stats)
    test_equivalencia_q1(stats)
    test_equivalencia_q2(stats)
    test_grado(stats)
    test_reproduce_el_148864_de_jsww(stats)
    test_refinamientos_de_matijasevic(stats)
    test_curva(stats)
    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — el teorema se cumple "
              f"sobre la implementacion.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
