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


def main():
    print(f"{Colors.BOLD}=== JSWW 1976: PATRON DE MEDIDA EXTERNO ==={Colors.ENDC}")
    stats = Stats()
    test_transcripcion(stats)
    test_marcador_de_aplanado(stats)
    test_grado_menor_que_5(stats)

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
