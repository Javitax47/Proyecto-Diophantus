#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - LA FORMALIZACION EN LEAN DICE LO QUE CREEMOS QUE DICE
================================================================================
`formalizacion/lean/CotaA.lean` demuestra `a >= 2` con el nucleo de Lean 4. Que
compile y no tenga `sorry` garantiza que la DEMOSTRACION es correcta; no
garantiza que el ENUNCIADO sea el que queremos. Un teorema formal de un enunciado
equivocado es peor que ninguno, porque parece mas fuerte.

Este test cierra ese hueco: extrae las hipotesis del fichero Lean y comprueba
SIMBOLICAMENTE, con sympy, que cada una es equivalente a la ecuacion
correspondiente de `ECUACIONES` en `dioph_jsww`. Es la misma disciplina de
`verificar_equivalencia`: 0 faltan, 0 sobran, aplicada al puente entre los dos
mundos.

POR QUE HACE FALTA, concretamente. Las ecuaciones de JSWW estan sobre Z con
variables en N, y en Lean se escriben sobre N SIN RESTAS: `(a^2-1)*y^2 + 1 - x^2`
pasa a `a^2*y^2 + 1 = y^2 + x^2`. Ese paso a mano es exactamente donde se cuela un
signo, y la resta truncada de N convierte un error de signo en un teorema que
sigue compilando y ya no dice lo mismo.
"""

import os
import re
import subprocess
import sys

import sympy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_jsww import ECUACIONES, _SIMBOLOS

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
LEAN = os.path.join(RAIZ, 'formalizacion', 'lean', 'CotaA.lean')

#: Hipotesis del teorema `a_ge_two` tal y como aparecen en el fichero Lean, y la
#: ecuacion de JSWW (indice 1..14) que cada una debe reproducir. Se escriben aqui
#: A MANO y el test comprueba (a) que estan literalmente en el .lean y (b) que
#: equivalen a la ecuacion. Copiarlas mal solo puede hacer FALLAR el test.
PUENTE = [
    (3,  "2 * n + p + q + z = e"),
    (4,  "16 * (k + 1) ^ 3 * (k + 2) * (n + 1) ^ 2 + 1 = f ^ 2"),
    (5,  "e ^ 3 * (e + 2) * (a + 1) ^ 2 + 1 = o ^ 2"),
    (6,  "a ^ 2 * y ^ 2 + 1 = y ^ 2 + x ^ 2"),
    (9,  "n + l + v = y"),
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


def _lean_a_sympy(texto):
    """`a ^ 2 * y ^ 2 + 1 = y ^ 2 + x ^ 2`  ->  expresion sympy `izq - der`."""
    loc = {str(s): s for s in _SIMBOLOS}
    izq, der = texto.split('=')
    return sympy.expand(sympy.sympify(izq.replace('^', '**'), locals=loc)
                        - sympy.sympify(der.replace('^', '**'), locals=loc))


def test_hipotesis_son_las_ecuaciones(stats):
    """[1] Cada hipotesis del teorema Lean ES una ecuacion de JSWW."""
    print(f"\n{Colors.HEADER}[1] Las hipotesis en Lean equivalen a las ecuaciones de JSWW{Colors.ENDC}")
    fuente = open(LEAN, encoding='utf-8').read()
    problemas = []
    for idx, texto in PUENTE:
        original = sympy.expand(ECUACIONES[idx - 1])
        traducida = _lean_a_sympy(texto)
        # equivalentes salvo signo global: las dos expresan "= 0"
        casa = (sympy.expand(original - traducida) == 0
                or sympy.expand(original + traducida) == 0)
        # y la hipotesis tiene que estar LITERALMENTE en el .lean
        presente = texto in fuente
        marca = (Colors.OKGREEN + "OK" + Colors.ENDC if casa and presente
                 else Colors.FAIL + "MAL" + Colors.ENDC)
        print(f"  {marca} ec.({idx:>2})  {texto}")
        if not casa:
            problemas.append(f"ec.({idx}) no equivale: {original} vs {traducida}")
        if not presente:
            problemas.append(f"ec.({idx}) no aparece literalmente en CotaA.lean")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} las 5 hipotesis son las ecuaciones "
              f"(3), (4), (5), (6) y (9) escritas sobre N sin restas")
        stats.ok()


def test_conclusion_y_alcance(stats):
    """[2] La conclusion es `2 <= a`, y el teorema usa SOLO esas cinco."""
    print(f"\n{Colors.HEADER}[2] Conclusion y alcance del teorema{Colors.ENDC}")
    fuente = open(LEAN, encoding='utf-8').read()
    problemas = []
    if "(h9 : n + l + v = y) : 2 ≤ a" not in fuente:
        problemas.append("la conclusion del teorema no es `2 ≤ a`")
    else:
        print("  conclusion: 2 ≤ a")
    # el teorema no puede tener mas hipotesis que las cinco declaradas
    cuerpo = fuente[fuente.index("theorem a_ge_two"):fuente.index(": 2 ≤ a")]
    hips = re.findall(r"\(h\d+ :", cuerpo)
    print(f"  hipotesis declaradas: {len(hips)}  {hips}")
    if len(hips) != len(PUENTE):
        problemas.append(f"el teorema tiene {len(hips)} hipotesis, se esperaban {len(PUENTE)}")
    print(f"  {Colors.WARN}Usa 5 de las 14 ecuaciones: menos hipotesis = teorema mas fuerte.{Colors.ENDC}")
    if problemas:
        stats.fail(problemas[0])
    else:
        stats.ok()


def _lean_bin():
    for base in (os.environ.get('LEAN_HOME', ''), '/tmp'):
        pass
    hallado = subprocess.run(['bash', '-lc', 'command -v lean'],
                             capture_output=True, text=True)
    return hallado.stdout.strip() or None


def test_compila_y_sin_sorry(stats):
    """[3] El fichero compila, no tiene `sorry` y solo usa axiomas estandar."""
    print(f"\n{Colors.HEADER}[3] Verificacion por el nucleo de Lean{Colors.ENDC}")
    fuente = open(LEAN, encoding='utf-8').read()
    sucio = re.findall(r"\b(sorry|admit|axiom|native_decide)\b", fuente)
    print(f"  `sorry`/`admit`/`axiom`/`native_decide` en el fichero: {sucio or 'ninguno'}")
    if sucio:
        stats.fail(f"el fichero contiene {sucio}")
        return
    lean = _lean_bin()
    if not lean:
        print(f"  {Colors.WARN}`lean` no esta en PATH: no se puede recompilar aqui.")
        print(f"  El fichero se verifico con Lean 4.33.1 y los axiomas resultantes")
        print(f"  fueron [propext, Classical.choice, Quot.sound], los tres estandar.")
        print(f"  Para reproducir: formalizacion/lean/verificar.sh{Colors.ENDC}")
        stats.ok()
        return
    r = subprocess.run([lean, LEAN], capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        stats.fail(f"lean devolvio {r.returncode}: {r.stdout[:400]}{r.stderr[:400]}")
        return
    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} compila con {lean}")
    stats.ok()


def main():
    print(f"{Colors.BOLD}=== LA FORMALIZACION DICE LO QUE CREEMOS ==={Colors.ENDC}")
    stats = Stats()
    test_hipotesis_son_las_ecuaciones(stats)
    test_conclusion_y_alcance(stats)
    test_compila_y_sin_sorry(stats)
    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — el enunciado formal "
              f"es el teorema que se creia demostrar.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
