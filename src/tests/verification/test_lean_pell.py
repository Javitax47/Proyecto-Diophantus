#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - LA FORMALIZACION DE PELL DICE LO QUE CREEMOS QUE DICE
================================================================================
`formalizacion/lean/Pell.lean` demuestra `a >= e+1` en el sistema (1) de JSWW,
que es la cota que desbloquea las tres eliminaciones bloqueadas y con ellas el
(21, 25). Antes de esto la cota se CITABA: dependia de tres hechos estandar
sobre la ecuacion de Pell --completitud, congruencia y crecimiento-- que estan
en Mathlib pero no en este proyecto. Ahora estan demostrados aqui.

Que compile y no tenga `sorry` garantiza la DEMOSTRACION, no el ENUNCIADO. Y en
este fichero el enunciado tiene mas superficie de error que en los anteriores,
porque la ecuacion (5) se reescribe DOS veces:

  * primero a la forma `o*o = e*e*e*(e+2)*((a+1)*(a+1)) + 1`, sin `^`;
  * y luego, dentro de la demostracion, a la Pell `o^2 - (A^2-1) Z^2 = 1` con
    `A = e+1` y `Z = e(a+1)`, apoyandose en `e^3(e+2) = e^2((e+1)^2 - 1)`.

Si esa factorizacion estuviera mal, el teorema seguiria compilando y hablaria de
otra ecuacion. Aqui se comprueba con sympy: las tres hipotesis contra
`ECUACIONES`, y la factorizacion como identidad polinomica.
"""

import os
import re
import sys

import sympy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_jsww import ECUACIONES, _SIMBOLOS

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
LEAN = os.path.join(RAIZ, 'formalizacion', 'lean', 'Pell.lean')

#: Hipotesis de `a_ge_e_succ_de_sistema` y la ecuacion de JSWW que reproduce
#: cada una. Se escriben A MANO; copiarlas mal solo puede hacer FALLAR el test.
PUENTE = [
    (3, "2*n + p + q + z = e"),
    (4, "16*(k+1)*(k+1)*(k+1)*(k+2)*((n+1)*(n+1)) + 1 = f*f"),
    (5, "e*e*e*(e+2)*((a+1)*(a+1)) + 1 = o*o"),
]


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; WARN = '\033[93m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}FALLO: {msg}{Colors.ENDC}")


def _fuente():
    return open(LEAN, encoding='utf-8').read()


def _a_sympy(texto):
    loc = {str(s): s for s in _SIMBOLOS}
    izq, der = texto.split('=', 1)
    conv = lambda t: sympy.sympify(t.replace('^', '**'), locals=loc)
    return sympy.expand(conv(izq) - conv(der))


def test_hipotesis(stats):
    """[1] Las tres hipotesis son las ecuaciones (3), (4) y (5) de JSWW."""
    print(f"\n{Colors.HEADER}[1] Las hipotesis del teorema son ecuaciones de JSWW{Colors.ENDC}")
    fuente = _fuente()
    problemas = []
    for idx, texto in PUENTE:
        original = sympy.expand(ECUACIONES[idx - 1])
        traducida = _a_sympy(texto)
        casa = (sympy.expand(original - traducida) == 0
                or sympy.expand(original + traducida) == 0)
        presente = texto in fuente
        marca = (Colors.OKGREEN + "OK" + Colors.ENDC if casa and presente
                 else Colors.FAIL + "MAL" + Colors.ENDC)
        print(f"  {marca} ec.({idx})  {texto}")
        if not casa:
            problemas.append(f"ec.({idx}) no equivale: {original} vs {traducida}")
        if not presente:
            problemas.append(f"ec.({idx}) no aparece literalmente en Pell.lean")
    if problemas:
        stats.fail(problemas[0])
    else:
        stats.ok()


def test_factorizacion(stats):
    """[2] La factorizacion que convierte la ec.(5) en una Pell es correcta.

    Es el paso del que cuelga todo el fichero: `e^3(e+2) = e^2((e+1)^2 - 1)`.
    Si fallara, el teorema hablaria de otra ecuacion y seguiria compilando.
    """
    print(f"\n{Colors.HEADER}[2] `e^3(e+2) = e^2((e+1)^2-1)`, que es de donde sale la Pell{Colors.ENDC}")
    e, a, o = sympy.symbols('e a o', integer=True)
    izq = e**3 * (e + 2)
    der = e**2 * ((e + 1)**2 - 1)
    print(f"  {sympy.expand(izq)}  vs  {sympy.expand(der)}")
    if sympy.expand(izq - der) != 0:
        stats.fail("la factorizacion es falsa")
        return
    # y con ella, la ec.(5) ES la Pell de A = e+1 con Z = e(a+1)
    A, Z = e + 1, e * (a + 1)
    pell = sympy.expand(o**2 - (A**2 - 1) * Z**2 - 1)
    ec5 = sympy.expand(o**2 - (e**3 * (e + 2) * (a + 1)**2 + 1))
    print(f"  o^2 - ((e+1)^2-1)*(e(a+1))^2 - 1  ==  o^2 - (e^3(e+2)(a+1)^2 + 1): "
          f"{sympy.expand(pell - ec5) == 0}")
    if sympy.expand(pell - ec5) != 0:
        stats.fail("la ec.(5) no coincide con la Pell de A=e+1, Z=e(a+1)")
    else:
        stats.ok()


def test_conclusion_y_alcance(stats):
    """[3] La conclusion es `e+1 <= a` y las hipotesis son SOLO tres ecuaciones."""
    print(f"\n{Colors.HEADER}[3] Conclusion y alcance{Colors.ENDC}")
    fuente = _fuente()
    m = re.search(r"theorem a_ge_e_succ_de_sistema(.*?):=", fuente, re.S)
    if m is None:
        stats.fail("no encuentro `theorem a_ge_e_succ_de_sistema`")
        return
    cuerpo = m.group(1)
    hip = re.findall(r"\(h(\w+) :", cuerpo)
    ecuaciones = [h for h in hip if h in ('3', '4', '5')]
    print(f"  conclusion: {cuerpo.strip().splitlines()[-1].strip()}")
    print(f"  hipotesis de ECUACION: {sorted(ecuaciones)}   "
          f"(el resto son no-negatividades)")
    problemas = []
    if "e + 1 ≤ a" not in cuerpo:
        problemas.append("la conclusion no es `e + 1 ≤ a`")
    if sorted(ecuaciones) != ['3', '4', '5']:
        problemas.append(f"esperaba las ecuaciones 3, 4 y 5, veo {sorted(ecuaciones)}")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} usa 3 de las 14 ecuaciones: "
              f"menos hipotesis = teorema mas fuerte")
        stats.ok()


def test_no_se_cita_nada(stats):
    """[4] Los tres hechos de Pell estan DEMOSTRADOS aqui, no citados.

    Es el punto entero de este fichero. Si alguno volviera a ser un `axiom` o un
    `sorry`, la cifra (21,25) volveria a ser condicional sin que nada lo dijera.
    """
    print(f"\n{Colors.HEADER}[4] Los tres hechos de Pell son teoremas, no axiomas{Colors.ENDC}")
    fuente = _fuente()
    problemas = []
    if re.search(r"\bsorry\b|\badmit\b|\bnative_decide\b", fuente):
        problemas.append("el .lean contiene `sorry`/`admit`/`native_decide`")
    if re.search(r"^\s*axiom\b", fuente, re.M):
        problemas.append("el .lean declara un `axiom` propio")
    for nombre, papel in [("completitud", "toda solucion esta en la sucesion"),
                          ("Y_mod", "Y j = j (mod A-1)"),
                          ("Y_mono", "crecimiento")]:
        if not re.search(r"theorem %s\b" % nombre, fuente):
            problemas.append(f"falta el teorema `{nombre}`")
        else:
            print(f"  {Colors.OKGREEN}OK{Colors.ENDC} `{nombre}` — {papel}")
    if re.search(r"^import Mathlib", fuente, re.M):
        problemas.append("el .lean importa Mathlib")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} sin Mathlib, sin axiomas propios: "
              f"la cota deja de ser condicional")
        stats.ok()


def main():
    print(f"{Colors.BOLD}=== PELL FORMALIZADO: `a >= e+1` SIN CITAR NADA ==={Colors.ENDC}")
    stats = Stats()
    test_hipotesis(stats)
    test_factorizacion(stats)
    test_conclusion_y_alcance(stats)
    test_no_se_cita_nada(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — el enunciado formalizado "
              f"es el que se cree demostrar.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
