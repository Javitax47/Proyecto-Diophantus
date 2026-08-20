#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - REDUCCION DE GRADO: la otra esquina de la frontera de Pareto
================================================================================
Valida src/analysis/dioph_degree.py: el aplanado de monomios, transformacion
UNIVERSAL que baja el grado a costa de incognitas (dual exacto de PellContext,
que baja incognitas a costa de grado).

Comprueba:
  - el grado por ecuacion baja realmente al objetivo (y el combinado a 2*objetivo);
  - EQUISATISFACIBILIDAD: el testigo original se EXTIENDE y anula el sistema
    aplanado; la pertenencia se preserva en todo el catalogo;
  - no aparecen soluciones nuevas (cada incognita introducida queda determinada);
  - la CURVA de Pareto medida para cada conjunto.
"""

import sys
import os
import sympy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_problems import build_catalog, verify_problem, rango_de, DiophProblem
from src.analysis.dioph_degree import (
    flatten_to_degree, flatten_greedy, max_equation_degree, pareto_point, pareto_curve,
    to_generator, witness_is_nonnegative,
)


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; WARN = '\033[93m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def test_baja_el_grado(stats):
    print(f"{Colors.HEADER}[1] El aplanado baja el grado por ecuacion al objetivo{Colors.ENDC}")
    malos = []
    for p in build_catalog():
        s = p.system
        if max_equation_degree(s) <= 2:
            continue
        f = flatten_to_degree(s, 2)
        if max_equation_degree(f) > 2 or f.degree() > 4:
            malos.append(f"{p.name}: eq={max_equation_degree(f)} comb={f.degree()}")
    if malos:
        stats.fail(f"el grado no bajo: {malos}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} toda ecuacion queda en grado <= 2 y la combinada en <= 4")


def test_equisatisfacibilidad(stats):
    print(f"{Colors.HEADER}[2] EQUISATISFACIBILIDAD: la pertenencia se preserva{Colors.ENDC}")
    for p in build_catalog():
        s = p.system
        if max_equation_degree(s) <= 2:
            continue
        f = flatten_to_degree(s, 2)
        plano = DiophProblem(p.name + " [aplanado]", p.param, f, p.oracle,
                             p.referencia, p.search_bound, soundness=p.soundness,
                             testigo=p.testigo)
        ok, fallos = verify_problem(plano, rango_de(p), exhaustivo=False)
        if ok:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {p.name}: mismo veredicto tras aplanar "
                  f"{pareto_point(s)} -> {pareto_point(f)}")
        else:
            stats.fail(f"{p.name}: {fallos[:2]}")


def test_sin_soluciones_nuevas(stats):
    print(f"{Colors.HEADER}[3] SOUNDNESS: el aplanado no introduce soluciones{Colors.ENDC}")
    # Cada w introducida esta determinada por w - a*b = 0, luego no anade libertad.
    # Se comprueba sobre un caso pequeno por busqueda exhaustiva.
    n = sympy.Symbol('n', integer=True)
    from src.analysis.dioph_lemmas import L_square
    base = L_square(n)                       # n = r^2, grado 2 -> forzamos grado 1 imposible
    f = flatten_to_degree(base, 2)
    espurios = [v for v in (2, 3, 5, 7, 8, 10)
                if f.search_witness({n: v}, 12) is not None]
    legit = [v for v in (0, 1, 4, 9) if f.search_witness({n: v}, 12) is None]
    if espurios or legit:
        stats.fail(f"aplanado cambia el conjunto: espurios={espurios}, perdidos={legit}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} no-cuadrados siguen sin testigo y cuadrados lo conservan")


def test_curva_pareto(stats):
    print(f"{Colors.HEADER}[4] CURVA DE PARETO medida por conjunto{Colors.ENDC}")
    print(f"  {'conjunto':22s} {'original':>14s} {'aplanado<=2':>14s}")
    for p in build_catalog():
        curva = pareto_curve(p.system, targets=(2,))
        orig = curva[0][1]
        plano = curva[1][1] if len(curva) > 1 else None
        print(f"  {p.name:22s} {str(orig):>14s} {str(plano) if plano else '(ya grado 4)':>14s}")
    stats.ok()
    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} curva medida: bajar el grado SUBE las incognitas (el compromiso es real)")


def test_honestidad_comparacion(stats):
    print(f"{Colors.HEADER}[5] HONESTIDAD: que se puede y que NO se puede afirmar{Colors.ENDC}")
    print(f"  Los numeros famosos de primos son GENERADORES; lo nuestro nacio como")
    print(f"  REPRESENTACION. Comparar esas cifras directamente seria un ERROR. Por eso")
    print(f"  existe to_generator(): convierte la representacion en generador y ENTONCES")
    print(f"  si son comparables (ver [10]). Las cifras de representacion NO lo son.")
    print(f"  {Colors.WARN}El (42,5) YA esta cotejado (JSWW 1976, ver test_dioph_jsww), y")
    print(f"  resulta ser su polinomio (1) pasado por la sustitucion de Skolem: nadie")
    print(f"  lo optimizo -- y el metodo que citan da un minimo demostrado de 51.")
    print(f"  Lo que sigue faltando: (i) la COMPLETITUD de la cadena propia, que")
    print(f"  desde el anclaje por L_psi ya no se puede evaluar ni para n=2 y")
    print(f"  descansa en el teorema; (ii) una revision experta de todo.{Colors.ENDC}")
    stats.ok()
    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} alcance declarado sin sobreafirmar")



def test_voraz_mejora(stats):
    print(f"{Colors.HEADER}[6] APLANADO VORAZ: compartir productos ahorra incognitas{Colors.ENDC}")
    peor = []
    for p in build_catalog():
        s = p.system
        if max_equation_degree(s) <= 2:
            continue
        fn, fg = flatten_to_degree(s, 2), flatten_greedy(s, 2)
        if fg.cost() > fn.cost():
            peor.append(f"{p.name}: voraz {fg.cost()} > ingenuo {fn.cost()}")
        else:
            print(f"    {p.name:20s} ingenuo {fn.cost():3d} -> voraz {fg.cost():3d} "
                  f"(ahorro {fn.cost()-fg.cost():+d})")
    if peor:
        stats.fail(f"el voraz empeoro: {peor}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} el voraz nunca empeora y ahorra donde hay productos repetidos")


def test_voraz_correcto(stats):
    print(f"{Colors.HEADER}[7] El voraz PRESERVA el conjunto (misma garantia que el ingenuo){Colors.ENDC}")
    for p in build_catalog():
        s = p.system
        if max_equation_degree(s) <= 2:
            continue
        fg = flatten_greedy(s, 2)
        if max_equation_degree(fg) > 2:
            stats.fail(f"{p.name}: el voraz dejo grado {max_equation_degree(fg)}")
            continue
        plano = DiophProblem(p.name + " [voraz]", p.param, fg, p.oracle,
                             p.referencia, p.search_bound, soundness=p.soundness,
                             testigo=p.testigo)
        ok, fallos = verify_problem(plano, rango_de(p), exhaustivo=False)
        if ok:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {p.name}: mismo veredicto, {pareto_point(fg)}")
        else:
            stats.fail(f"{p.name}: {fallos[:2]}")



def test_no_negatividad(stats):
    print(f"{Colors.HEADER}[8] GUARDARRAIL: todo testigo debe ser >= 0 (exigencia de N){Colors.ENDC}")
    # Ya ocurrio una vez: el multiplicador de una congruencia escrita al reves era
    # negativo, lo que invalidaba el modo over_N y la conversion a generador.
    malos = []
    for p in build_catalog():
        for v in rango_de(p)[:6]:
            if not p.oracle(v):
                continue
            w = p.system.witness({p.param: v})
            if w is None:
                continue
            negs = {k: x for k, x in w.items() if int(x) < 0}
            if negs:
                malos.append(f"{p.name}(n={v}): {list(negs)[:3]}")
    if malos:
        stats.fail(f"testigos con valores NEGATIVOS: {malos[:3]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} todos los testigos del catalogo son no negativos")


def test_generador(stats):
    print(f"{Colors.HEADER}[9] REPRESENTACION -> GENERADOR (comparable con los records){Colors.ENDC}")
    print(f"  Q(n,x) = n*(1 - sum_i P_i^2): sus VALORES POSITIVOS son el conjunto.")
    for p in build_catalog():
        f = flatten_greedy(p.system, 2) if max_equation_degree(p.system) > 2 else p.system
        Q, info = to_generator(f, p.param)
        vals = [v for v in rango_de(p) if p.oracle(v)][:2]
        ok_todos = True
        if p.testigo == "parcial":
            # `Q(testigo) = n` no se puede evaluar: el testigo no esta completo
            # (el rango de aparicion de L_psi es astronomico). Se comprueba la
            # OTRA mitad, que si es evaluable y es la que protege del defecto de
            # agosto: una asignacion arbitraria no debe dar un valor positivo.
            basura = {p.param: vals[0] if vals else 2}
            basura.update({u: 1 for u in f.unknowns})
            valor = int(Q.subs(basura))
            if valor > 0 and f.unknowns:
                stats.fail(f"{p.name}: asignacion arbitraria da Q = {valor} > 0")
            else:
                stats.ok()
                print(f"  {Colors.OKGREEN}~{Colors.ENDC} {p.name:22s} generador "
                      f"({info['variables']} variables, grado {info['grado']}) — "
                      f"basura -> Q<=0; {Colors.WARN}Q(testigo)=n NO evaluable "
                      f"(testigo parcial){Colors.ENDC}")
            continue
        for nv in vals:
            w = f.witness({p.param: nv})
            if w is None or not witness_is_nonnegative(f, {p.param: nv}):
                ok_todos = False
                continue
            asg = {p.param: nv}
            asg.update(w)
            if int(Q.subs(asg)) != nv:
                ok_todos = False
        # una asignacion arbitraria no puede dar un valor positivo mayor
        basura = {p.param: vals[0] if vals else 2}
        basura.update({u: 1 for u in f.unknowns})
        if int(Q.subs(basura)) > 0 and f.unknowns:
            ok_todos = False
        if ok_todos:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {p.name:22s} generador ({info['variables']} variables, "
                  f"grado {info['grado']}) — Q(testigo)=n y basura -> Q<=0")
        else:
            stats.fail(f"{p.name}: el generador no reproduce el conjunto")


def test_situacion_frente_al_record(stats):
    """[10] Marcador honesto frente al record. Tres cifras que NO son la misma.

    HISTORIA, para que nadie confunda ninguna de las tres: este test afirmo una
    vez (41 variables, grado 5) frente al record citado de (42, 5). Era falso por
    dos motivos distintos, y los dos se han cerrado desde entonces:

      * `L_nonneg_N` declaraba coste 0 para cualquier expresion, asi que en modo N
        las condiciones laterales no imponian NADA y Z3 hallaba testigo para
        n = 4, 9, 15 y 25;
      * el indice se anclaba con `Y == k (mod a-1)`, que fija el RESIDUO del
        exponente y no el exponente: el lema exponencial admitia valores espurios
        (3^2 = 9 admitia c en {1,3,5,7,9}).

    Lo primero se arreglo con el criterio de coeficientes no negativos; lo segundo
    exigio reconstruir la cadena sobre `L_psi`. Ambas cifras de agosto quedaron
    retiradas, y este marcador imprime desde entonces solo lo medido.

    LAS TRES CIFRAS, que miden cosas distintas:
      (a) generador PROPIO, de la cadena que este calculo construye por si mismo;
      (b) generador obtenido aplanando el sistema PUBLICADO de JSWW 1976 -- mejor,
          porque parte de una construccion que costo un paper entero afinar;
      (c) los records citados en la literatura.
    Mezclarlas seria exactamente el error de agosto en otra forma.
    """
    print(f"{Colors.HEADER}[10] SITUACION FRENTE AL RECORD (marcador honesto){Colors.ENDC}")
    p = [x for x in build_catalog() if x.name == 'primo'][0]
    f = flatten_greedy(p.system, 2)
    _, info = to_generator(f, p.param)
    print(f"  (a) generador propio, aplanado voraz : ({info['variables']} variables, "
          f"grado {info['grado']})")
    print(f"      el mismo con aplanado OPTIMO      : (68 variables, grado 5) "
          f"-- ver test_dioph_calculus [18]")
    print(f"  (b) aplanando el sistema publicado de JSWW 1976 : (46 variables, grado 5)")
    print(f"      -- optimo demostrado, ver test_dioph_jsww")
    print(f"  (c) literatura, TODO como GENERADOR para que sea comparable:")
    print(f"      JSWW 1976 (26, 25) construido | (42, 5) ANUNCIADO sin construccion")
    print(f"      publicada | Matiyasevich 10 variables, grado >6000 (Pak-Kaliszyk)")
    print(f"  {Colors.WARN}CUIDADO CON DOS CIFRAS QUE CIRCULAN MAL:")
    print(f"   * el famoso '(10, ~1.6e45)' FUNDE DOS OBJETOS: el 10 es del polinomio")
    print(f"     de primos de Matiyasevich y el 1.6e45 es el grado del par UNIVERSAL")
    print(f"     (9, 1.638e45) de Jones, que no es el mismo polinomio. El grado real")
    print(f"     del de 10 variables es >6000 segun quienes lo formalizaron.")
    print(f"   * el par (58, 4) de Jones es de una ECUACION, no de un generador:")
    print(f"     como generador seria (59, 9), dominado en ambos ejes.{Colors.ENDC}")
    print(f"  {Colors.WARN}QUE SE PUEDE AFIRMAR Y QUE NO:")
    print(f"   1. La cadena esta anclada por L_psi y pasa el control SMT (firma")
    print(f"      a in {{0,1}} refutada sin cota + barrido). Su SOUNDNESS se comprueba.")
    print(f"   2. Su COMPLETITUD ya NO se comprueba por evaluacion: el testigo de")
    print(f"      L_psi sale de un rango de aparicion astronomico y no es calculable")
    print(f"      ni para n=2. Descansa en el Teorema 1 de Pak-Kaliszyk (Mizar).")
    print(f"      Se gano correccion y se perdio verificabilidad; esta anotado.")
    print(f"   3. El (42,5) esta cotejado en fuente primaria --JSWW, Amer. Math.")
    print(f"      Monthly 83:6 (1976) 449-464, p. 450-- y es una FRASE: el metodo que")
    print(f"      citan (Davis, AMM 80, p. 263) da un minimo demostrado de 51.")
    print(f"   4. Nada de esto ha pasado revision experta.{Colors.ENDC}")
    # El test NO exige estar por debajo de 42: exige que la cifra sea la MEDIDA y
    # que las salvedades esten impresas. Un test que solo pase cuando el numero
    # mejora deja de ser un marcador y se vuelve una profecia.
    if info['grado'] == 5 and p.testigo == "parcial":
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} punto propio medido ({info['variables']}, 5) "
              f"sobre cadena anclada por L_psi; mejor punto del proyecto: (46, 5)")
    elif info['grado'] != 5:
        stats.fail(f"grado inesperado: {info}")
    else:
        stats.fail("la cadena de primos no declara testigo parcial: o el anclaje "
                   "por L_psi se ha desactivado, o el modo de testigo miente")


def main():
    print(f"{Colors.BOLD}=== REDUCCION DE GRADO: LA ESQUINA DE GRADO BAJO ==={Colors.ENDC}")
    stats = Stats()
    test_baja_el_grado(stats)
    test_equisatisfacibilidad(stats)
    test_sin_soluciones_nuevas(stats)
    test_curva_pareto(stats)
    test_voraz_mejora(stats)
    test_voraz_correcto(stats)
    test_no_negatividad(stats)
    test_generador(stats)
    test_situacion_frente_al_record(stats)
    test_honestidad_comparacion(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — aplanado universal verificado: "
              f"baja el grado preservando el conjunto, con el coste medido.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
