#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - FIDELIDAD DE LA TRANSCRIPCION DEL TEOREMA 3.9 DE JSWW
================================================================================
`dioph_jsww3` transcribe el sistema (I)-(XXI) de la seccion 3 (p. 456-457), el
del "metodo del cociente". Es una transcripcion A MANO de 21 condiciones, tres
de las cuales no son ecuaciones polinomicas y hay que convertir. O sea: mucha
superficie para un error de signo que nadie notaria.

Este test no comprueba que el sistema represente los primos --eso es el Teorema
3.9 y se CITA-- sino que lo transcrito sea lo impreso. Cuatro anclajes, y los
cuatro son independientes de la cifra que se quiere obtener:

  1. `U(2k, n)` desarrollado tiene que ser LITERALMENTE la ecuacion (4) del
     sistema (1) de la seccion 2. Las dos secciones comparten esa pieza, asi que
     la Definicion 3.7 queda contrastada contra una transcripcion ya verificada.
  2. Los recuentos que JSWW declaran en la p. 461: 14 incognitas eliminables por
     sustitucion, 10 libres.
  3. Las condiciones que declaran: seis de cuadrado, una de divisibilidad, una
     desigualdad.
  4. Y el anclaje mas fuerte, porque no se impuso al transcribir: el sistema
     convertido tiene 32 incognitas + parametro = 33 variables y grado maximo
     14. Eliminando las 14 quedan **19 variables**, y `1 + 2*14` = **29**. Los
     dos numeros del (19, 29) que anuncian en la p. 449, saliendo de las
     ecuaciones y no de la cifra.
"""

import os
import sys

import sympy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_jsww import ECUACIONES
from src.analysis.dioph_jsww3 import (sistema3, U, k, n, AFIRMADO, ELIMINABLES_JSWW,
                                      LIBRES, DEFINIDAS, AUXILIARES)
from src.analysis.dioph_degree import max_equation_degree


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; WARN = '\033[93m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}FALLO: {msg}{Colors.ENDC}")


def test_U_es_la_ecuacion_4(stats):
    """[1] `U(2k,n)` ES la ecuacion (4) del sistema (1)."""
    print(f"\n{Colors.HEADER}[1] La Definicion 3.7 contrastada contra el sistema (1){Colors.ENDC}")
    f = sympy.Symbol('f', integer=True)
    izq = sympy.expand(U(2 * k, n))
    der = sympy.expand(ECUACIONES[3] + f ** 2)   # ec.(4) es  <...> + 1 - f^2
    ok = sympy.expand(izq - der) == 0
    print(f"  U(2k,n) = (2k+2)^3 (2k+4) (n+1)^2 + 1")
    print(f"  ec.(4)  = 16(k+1)^3 (k+2)(n+1)^2 + 1")
    print(f"  {'iguales al desarrollar' if ok else 'NO COINCIDEN'}")
    if ok:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} la pieza compartida entre las dos secciones casa")
        stats.ok()
    else:
        stats.fail("U(2k,n) no reproduce la ecuacion (4) del sistema (1)")


def test_recuentos(stats):
    """[2] Los recuentos de incognitas que JSWW declaran en la p. 461."""
    print(f"\n{Colors.HEADER}[2] Recuento de incognitas, contra lo que declaran{Colors.ENDC}")
    problemas = []
    print(f"  libres (n,x,w,m,z,i,j,p,l,r): {len(LIBRES)}   declaran {AFIRMADO['unknowns_tras_eliminar']}")
    if len(LIBRES) != AFIRMADO["unknowns_tras_eliminar"]:
        problemas.append(f"{len(LIBRES)} libres, declaran {AFIRMADO['unknowns_tras_eliminar']}")
    print(f"  eliminables por sustitucion:  {len(DEFINIDAS)}   declaran {len(ELIMINABLES_JSWW)}")
    if len(DEFINIDAS) != len(ELIMINABLES_JSWW):
        problemas.append("la lista de eliminables no coincide con las definidas")
    if sorted(str(u) for u in DEFINIDAS) != sorted(ELIMINABLES_JSWW):
        problemas.append("los NOMBRES de las eliminables no coinciden")
    print(f"  anadidas por la conversion:   {len(AUXILIARES)} "
          f"(6 raices + 1 cociente + 1 holgura)")
    if problemas:
        stats.fail(problemas[0])
    else:
        stats.ok()


def test_condiciones(stats):
    """[3] Seis condiciones de cuadrado, una divisibilidad, una desigualdad."""
    print(f"\n{Colors.HEADER}[3] Las condiciones no polinomicas, contadas{Colors.ENDC}")
    fuente = open(os.path.join(os.path.dirname(__file__), '..', '..',
                               'analysis', 'dioph_jsww3.py'), encoding='utf-8').read()
    cuadrados = sum(1 for c in ('c1', 'c2', 'c3', 'c4', 'c5', 'c6')
                    if f"{c} ** 2" in fuente)
    print(f"  raices de condicion de cuadrado usadas: {cuadrados}   "
          f"declaran {AFIRMADO['condiciones_cuadrado']}")
    problemas = []
    if cuadrados != AFIRMADO["condiciones_cuadrado"]:
        problemas.append(f"{cuadrados} condiciones de cuadrado, declaran "
                         f"{AFIRMADO['condiciones_cuadrado']}")
    if "F * d1" not in fuente:
        problemas.append("no encuentro la conversion de la divisibilidad F | H - C")
    if "s1" not in fuente:
        problemas.append("no encuentro la holgura de la desigualdad (XIV)")
    print(f"  divisibilidad `F | H - C` -> `H - C = F*d1`: "
          f"{'si' if 'F * d1' in fuente else 'NO'}")
    print(f"  desigualdad (XIV) con holgura `s1`: {'si' if 's1' in fuente else 'NO'}")
    if problemas:
        stats.fail(problemas[0])
    else:
        stats.ok()


def test_anclaje_19_29(stats):
    """[4] El anclaje fuerte: 19 variables y grado 29 salen SOLOS.

    No se impuso nada al transcribir: el grado maximo del sistema convertido y su
    numero de incognitas son consecuencia de las ecuaciones. Que den justo los
    dos numeros del (19,29) anunciado es la comprobacion mas informativa de que
    la transcripcion es la buena.
    """
    print(f"\n{Colors.HEADER}[4] 19 y 29 salen de las ecuaciones, no de la cifra{Colors.ENDC}")
    S = sistema3()
    g = max_equation_degree(S)
    variables = S.cost() + 1
    tras = variables - len(ELIMINABLES_JSWW)
    print(f"  sistema convertido: {S.cost()} incognitas + k = {variables} variables")
    print(f"  grado maximo por ecuacion: {g}  =>  generador de grado {1 + 2*g}")
    print(f"  tras eliminar las {len(ELIMINABLES_JSWW)} que ellos indican: "
          f"{Colors.BOLD}({tras}, {1 + 2*g}){Colors.ENDC}")
    problemas = []
    if tras != 19:
        problemas.append(f"quedan {tras} variables, se esperaban 19")
    if 1 + 2 * g != 29:
        problemas.append(f"grado {1+2*g}, se esperaba 29")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} coincide con el (19, 29) que anuncian en la p. 449")
        print(f"  {Colors.WARN}OJO: esto valida la TRANSCRIPCION, no la cifra. Que las 14")
        print(f"  eliminaciones mantengan el grado 14 es otra cosa, y esta sin medir.{Colors.ENDC}")
        stats.ok()


def main():
    print(f"{Colors.BOLD}=== TEOREMA 3.9 DE JSWW: FIDELIDAD DE LA TRANSCRIPCION ==={Colors.ENDC}")
    stats = Stats()
    test_U_es_la_ecuacion_4(stats)
    test_recuentos(stats)
    test_condiciones(stats)
    test_anclaje_19_29(stats)
    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — la transcripcion "
              f"reproduce lo impreso.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
