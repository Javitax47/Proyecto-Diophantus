#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - JONES-SATO-WADA-WIENS 1976 COMO PATRON DE MEDIDA EXTERNO
================================================================================
Es el unico punto de la literatura contra el que este proyecto puede medirse SIN
depender de que su propia cadena de Wilson sea correcta: su sistema esta escrito
explicitamente en el paper y se transcribe entero.

Comprueba:
  - la TRANSCRIPCION es fiel: reproduce (26 variables, grado 25), las cifras
    publicadas. Si alguien altera una ecuacion, esto lo detecta;
  - el coste de NUESTRO aplanado sobre SU sistema, frente a las 16 incognitas que
    ellos anadieron con la sustitucion de Skolem. Es un marcador honesto de una
    pieza que todavia va por detras;
  - que la forma factorizada importa: aplanar el arbol gana solo si no se expando
    antes.

Fuente PRIMARIA cotejada: J. P. Jones, D. Sato, H. Wada, D. Wiens, "Diophantine
representation of the set of prime numbers", Amer. Math. Monthly 83:6 (1976)
449-464, p. 450.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_jsww import sistema, FACTOR, PUBLICADO, INCOGNITAS
from src.analysis.dioph_degree import (
    flatten_greedy, flatten_tree, to_generator, max_equation_degree,
)
from src.analysis.dioph_optflat import (
    Z3_DISPONIBLE, aplanado_minimo_compuesto, materializar,
)


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; WARN = '\033[93m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}FALLO: {msg}{Colors.ENDC}")


def test_transcripcion(stats):
    """[1] La transcripcion debe reproducir las cifras PUBLICADAS: (26, 25)."""
    print(f"\n{Colors.HEADER}[1] Fidelidad de la transcripcion de (1){Colors.ENDC}")
    S = sistema()
    _, g = to_generator(S, FACTOR)
    esperado = PUBLICADO["generador"]
    print(f"  medido: ({g['variables']} variables, grado {g['grado']})   "
          f"publicado: ({esperado[0]}, {esperado[1]})")
    if (g["variables"], g["grado"]) == esperado:
        print(f"  {Colors.OKGREEN}OK{Colors.ENDC} 14 ecuaciones, 25 incognitas + el parametro k")
        stats.ok()
    else:
        stats.fail(f"la transcripcion no reproduce {esperado}: alguna ecuacion esta mal copiada")


def test_marcador_de_aplanado(stats):
    """[2] Cuanto nos cuesta a NOSOTROS lo que a ellos les costo 16 incognitas.

    Este test no exige ganar: exige MEDIR y dejar la brecha por escrito. Un
    marcador que solo se publica cuando favorece no es un marcador.
    """
    print(f"\n{Colors.HEADER}[2] Aplanado a grado 2 sobre SU sistema (= Skolem){Colors.ENDC}")
    base = len(INCOGNITAS)
    Se = sistema(expandir=True)
    Sf = sistema(expandir=False)
    filas = [
        ("voraz sobre expandido", flatten_greedy(Se, 2)),
        ("Skolem sobre expandido", flatten_tree(Se, 2)),
        ("Skolem sobre factorizado", flatten_tree(Sf, 2)),
    ]
    mejor = None
    for etiqueta, F in filas:
        _, g = to_generator(F, FACTOR)
        anadidas = F.cost() - base
        if max_equation_degree(F) > 2:
            stats.fail(f"{etiqueta}: no llego a grado 2 por ecuacion")
            return
        if g["grado"] != 5:
            stats.fail(f"{etiqueta}: generador de grado {g['grado']}, se esperaba 5")
            return
        mejor = anadidas if mejor is None else min(mejor, anadidas)
        print(f"  {etiqueta:<26} +{anadidas:2d} incognitas -> "
              f"({g['variables']} variables, grado {g['grado']})")
    print(f"  {Colors.BOLD}JSWW 1976 (publicado){Colors.ENDC}      +16 incognitas -> (42 variables, grado 5)")
    if mejor <= 16:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} igualamos o mejoramos su sustitucion de Skolem")
    else:
        print(f"  {Colors.WARN}Vamos {mejor - 16} incognitas POR DETRAS de lo que ellos "
              f"hicieron a mano en 1976.{Colors.ENDC}")
        print(f"  {Colors.WARN}-> nuestro generador de primos queda por debajo de 42 por partir de "
              f"una representacion mas barata, NO por aplanar mejor.{Colors.ENDC}")
    stats.ok()


def test_grado_menor_que_5(stats):
    """[3] Que grado < 5 sigue ABIERTO lo dicen los propios autores."""
    print(f"\n{Colors.HEADER}[3] Grado < 5: problema abierto, no descartado{Colors.ENDC}")
    print("  JSWW 1976, p. 450, textual:")
    print("    \"We do not know whether there is a prime representing polynomial")
    print("     of degree < 5.\"")
    print(f"  {Colors.WARN}Concuerda con el argumento estructural: Q = n(1 - sum P_i^2) tiene")
    print(f"  grado 1 + 2*max deg(P_i), y un sistema lineal define un conjunto")
    print(f"  semilineal, que los primos no son. Pero eso solo acota ESTA")
    print(f"  construccion, no todas.{Colors.ENDC}")
    if PUBLICADO["grado_menor_que_5"].startswith("abierto"):
        stats.ok()
    else:
        stats.fail("se ha alterado la nota sobre el estado del problema")


def test_aplanado_optimo(stats):
    """[4] El aplanado OPTIMO, con cota inferior demostrada y sistema materializado.

    Las heuristicas dicen "he encontrado 46". Esto dice "46 es el minimo, y aqui
    esta el sistema". La diferencia importa: sin cota inferior no se sabe si vale
    la pena seguir buscando, y sin materializar la cifra es un numero de un
    solucionador, no un resultado.

    Se comprueba: el optimizador alcanza su cota (optimo demostrado), el sistema
    materializado tiene grado <= 2 por ecuacion, y las cifras salen donde deben.
    """
    print(f"\n{Colors.HEADER}[4] Aplanado optimo sobre el sistema de JSWW{Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)"); return
    S = sistema(expandir=False)
    r = aplanado_minimo_compuesto(S, 2, timeout_s=300)
    print(f"  optimizador: {r['estado']}, {r['nombres']} nombres (cota inferior {r['cota']})")
    if r["estado"] != "optimo":
        stats.fail(f"no se alcanzo la cota: {r['estado']}")
        return
    M = materializar(S, r["elegidos"], 2)
    grado = max_equation_degree(M)
    _, g = to_generator(M, FACTOR)
    usadas = sum(1 for u in INCOGNITAS if u in M.unknowns)
    print(f"  materializado: {M.cost()} incognitas ({usadas} originales + "
          f"{M.cost()-usadas} nombres), grado maximo {grado}")
    print(f"  GENERADOR: ({g['variables']} variables, grado {g['grado']})"
          f"     JSWW 1976: (42, 5)")
    if grado > 2:
        stats.fail(f"el sistema materializado tiene grado {grado}, no 2")
    elif g["grado"] != 5:
        stats.fail(f"generador de grado {g['grado']}, se esperaba 5")
    else:
        distancia = g["variables"] - 42
        print(f"  {Colors.WARN}Distancia al record: {distancia:+d} variables. Y esta demostrado")
        print(f"  que aplanar mejor es IMPOSIBLE: la cota inferior se alcanza. Lo que")
        print(f"  falta tiene que salir de reestructurar el sistema, no de optimizar.{Colors.ENDC}")
        stats.ok()


def test_equivalencia_por_sustitucion(stats):
    """[5] El sistema materializado ES el de JSWW: sustitución hacia atrás.

    POR QUÉ HACE FALTA ESTE TEST Y NO BASTA EL DEL CATALOGO. La materialización
    se verifica en el catalogo comprobando que el testigo se extiende y anula el
    sistema. Con JSWW eso NO se puede hacer: no tenemos testigo, y encontrarlo es
    el reto famoso del paper (los valores son astronomicos). Sin esta comprobacion,
    la equisatisfacibilidad de nuestro (46,5) con el original quedaba SIN VERIFICAR.

    Lo que se hace en su lugar es simbolico y mas fuerte que cualquier muestreo:
    cada incognita nueva `w` viene con su ecuacion definitoria `w = d`. Sustituyendo
    en cascada hacia atras, las ecuaciones no definitorias deben devolver
    EXACTAMENTE las 14 originales -- ninguna de menos, ninguna de mas. Si eso se
    cumple, el sistema aplanado es el mismo objeto matematico escrito de otra forma.
    """
    print(f"\n{Colors.HEADER}[5] Equivalencia simbólica con el sistema original{Colors.ENDC}")
    if not Z3_DISPONIBLE:
        print("  (z3 no disponible: omitido)"); return
    import sympy
    S = sistema(expandir=False)
    r = aplanado_minimo_compuesto(S, 2, timeout_s=300)
    if r["estado"] != "optimo":
        stats.fail(f"el optimizador no alcanzo la cota: {r['estado']}")
        return
    M = materializar(S, r["elegidos"], 2)

    nuevas = [u for u in M.unknowns if u not in INCOGNITAS]
    defs = {}
    for e in M.eqs:
        ex = sympy.expand(e)
        for w in nuevas:
            if ex.coeff(w, 1) == 1 and ex.coeff(w, 2) == 0:
                resto = sympy.expand(w - ex)
                if w not in resto.free_symbols:
                    defs[w] = resto
                    break
    if len(defs) != len(nuevas):
        stats.fail(f"{len(nuevas)} incognitas nuevas pero solo {len(defs)} definiciones")
        return

    def desnombrar(e):
        prev = None
        while prev != e:
            prev = e
            e = sympy.expand(e.subs(defs))
        return e

    originales = [sympy.expand(x) for x in S.eqs]
    no_def = [e for e in M.eqs
              if not any(sympy.expand(e - (w - d)) == 0 for w, d in defs.items())]
    recuperadas = [desnombrar(e) for e in no_def]

    def casa(u, v):
        return sympy.expand(u - v) == 0 or sympy.expand(u + v) == 0

    faltan = [o for o in originales if not any(casa(o, rr) for rr in recuperadas)]
    sobran = [rr for rr in recuperadas if not any(casa(o, rr) for o in originales)]
    print(f"  {len(nuevas)} incognitas nuevas, {len(defs)} definiciones, "
          f"{len(no_def)} ecuaciones no definitorias (originales: {len(originales)})")
    print(f"  originales no recuperadas: {len(faltan)}   recuperadas que no son originales: {len(sobran)}")
    if faltan or sobran:
        stats.fail(f"la sustitucion hacia atras no devuelve el sistema original "
                   f"({len(faltan)} faltan, {len(sobran)} sobran)")
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} el sistema aplanado es el de JSWW escrito de otra forma")
        stats.ok()


def main():
    print(f"{Colors.BOLD}=== JSWW 1976: PATRON DE MEDIDA EXTERNO ==={Colors.ENDC}")
    stats = Stats()
    test_transcripcion(stats)
    test_marcador_de_aplanado(stats)
    test_grado_menor_que_5(stats)
    test_aplanado_optimo(stats)
    test_equivalencia_por_sustitucion(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — medido contra la "
              f"literatura, con la brecha declarada.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
