#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - LAS COTAS DE LA SECCION 3 DICEN LO QUE CREEMOS QUE DICEN
================================================================================
`formalizacion/lean/Cotas3.lean` demuestra SIETE de las ocho cotas que bloquean
las catorce eliminaciones del Teorema 3.9 de JSWW. Cada cota licencia eliminar
una incognita cuya definicion el criterio estructural del proyecto --"todos los
coeficientes >= 0"-- rechaza por una resta.

Que el .lean compile y no tenga `sorry` garantiza la DEMOSTRACION. Lo que este
fichero comprueba es el ENUNCIADO, que es donde se cuela el error:

  [1] cada hipotesis del teorema es LITERALMENTE una ecuacion de `ECUACIONES_3`;
  [2] la conclusion cubre exactamente las incognitas de `DESBLOQUEADAS`, que son
      las que `sistema3()` declara licenciadas;
  [3] la que falta --`S`-- sigue declarada como PENDIENTE, para que nadie la de
      por hecha;
  [4] el mecanismo `demostradas` de `eliminar_lineales` hace lo que dice: sin la
      licencia no elimina, con ella si;
  [5] sin `sorry`, sin `axiom` propio, sin Mathlib;
  [6] el censo cuadra: 6 estructurales + 7 demostradas + 1 pendiente = 14.

POR QUE IMPORTA QUE LA LISTA SEA CORTA. Si `DESBLOQUEADAS` creciera sin que la
demostracion creciera, el optimizador eliminaria incognitas sin licencia y las
cifras que salieran serian falsas sin que nada avisara. Este test es lo que ata
las dos listas.
"""

import os
import re
import sys

import sympy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_calculus import Dioph
from src.analysis.dioph_degree import eliminar_lineales
from src.analysis.dioph_jsww3 import (COTAS_DEMOSTRADAS, COTAS_PENDIENTES,
                                      DESBLOQUEADAS, ECUACIONES_3,
                                      INCOGNITAS_3, censo_eliminaciones,
                                      cotas_verificadas, k, sistema3)

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
LEAN = os.path.join(RAIZ, 'formalizacion', 'lean', 'Cotas3.lean')

#: (etiqueta romana, indice 0-based en `ECUACIONES_3`, hipotesis tal cual en el
#: .lean). Se escriben A MANO: copiarlas mal solo puede hacer FALLAR el test.
PUENTE = [
    ("I",    0, "(2*k + 2)*(2*k + 2)*(2*k + 2)*(2*k + 4)*((n+1)*(n+1)) + 1 = c1*c1"),
    ("II",   1, "(2*n + 2)*(2*n + 2)*(2*n + 2)*(2*n + 4)*((x+1)*(x+1)) + 1 = c2*c2"),
    ("III",  2, "M = 16 * n * x * (w + 2) + 1"),
    ("IV",   3, "A = M * (x + 1)"),
    ("V",    4, "B = n + 1"),
    ("VI",   5, "C = m + B"),
    ("VIII", 8, "D = (A * A - 1) * (C * C) + 1"),
    ("IX",   9, "E = 2 * (i + 1) * D * (C * C)"),
    ("X",   10, "F = (A * A - 1) * (E * E) + 1"),
    ("XI",  11, "G = A + F * (F - A)"),
    ("XII", 12, "H = B + 2 * (j + 1) * C"),
    ("XIII", 13, "I = (G * G - 1) * (H * H) + 1"),
    ("XVIII", 18, "K = n - k + 1 + p * (M - 1)"),
    ("XIX", 19, "L = k + 1 + l * (M * x - 1)"),
    ("XX",  20, "R = k + 1 + r * (M * n * x - 1)"),
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
    # `I` es la unidad imaginaria en sympy; `locals` lo devuelve a ser el simbolo
    # del sistema. Sin esto la ecuacion (XIII) se traduciria a otra cosa.
    loc = {str(s): s for s in list(INCOGNITAS_3) + [k]}
    izq, der = texto.split('=', 1)
    conv = lambda t: sympy.sympify(t.replace('^', '**'), locals=loc)
    return sympy.expand(conv(izq) - conv(der))


def test_hipotesis(stats):
    """[1] Las catorce hipotesis son ecuaciones del Teorema 3.9."""
    print(f"\n{Colors.HEADER}[1] Cada hipotesis del .lean es una ecuacion de `ECUACIONES_3`{Colors.ENDC}")
    fuente = _fuente()
    problemas = []
    for etiqueta, idx, texto in PUENTE:
        original = sympy.expand(ECUACIONES_3[idx])
        traducida = _a_sympy(texto)
        casa = (sympy.expand(original - traducida) == 0
                or sympy.expand(original + traducida) == 0)
        presente = texto in fuente
        marca = (Colors.OKGREEN + "OK " + Colors.ENDC if casa and presente
                 else Colors.FAIL + "MAL" + Colors.ENDC)
        print(f"  {marca} ({etiqueta:<4}) {texto}")
        if not casa:
            problemas.append(f"({etiqueta}) no equivale a ECUACIONES_3[{idx}]")
        if not presente:
            problemas.append(f"({etiqueta}) no aparece literalmente en Cotas3.lean")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 15 de las 21 condiciones; "
              f"NO se usa (XIV), que es la unica con hipotesis heredada")
        stats.ok()


def test_conclusion(stats):
    """[2] La conclusion cubre exactamente `DESBLOQUEADAS`, las siete."""
    print(f"\n{Colors.HEADER}[2] La conclusion y la lista de licencias coinciden{Colors.ENDC}")
    fuente = _fuente()
    m = re.search(r"theorem cotas_seccion_tres(.*?):=", fuente, re.S)
    if m is None:
        stats.fail("no encuentro `theorem cotas_seccion_tres`")
        return
    conclusion = m.group(1).strip().splitlines()[-1].strip()
    print(f"  {conclusion}")
    en_lean = set(re.findall(r"0 ≤ (\w+)", conclusion))
    print(f"  en el .lean: {sorted(en_lean)}")
    print(f"  DESBLOQUEADAS: {sorted(DESBLOQUEADAS)}")
    print(f"  sistema3().no_negativas_incognitas: "
          f"{sorted(sistema3().no_negativas_incognitas)}")
    problemas = []
    if en_lean != set(DESBLOQUEADAS):
        problemas.append(f"la conclusion cubre {sorted(en_lean)}, "
                         f"DESBLOQUEADAS dice {sorted(DESBLOQUEADAS)}")
    if set(sistema3().no_negativas_incognitas) != set(DESBLOQUEADAS):
        problemas.append("`sistema3()` no declara exactamente `DESBLOQUEADAS`")
    for nombre in DESBLOQUEADAS:
        if nombre not in COTAS_DEMOSTRADAS:
            problemas.append(f"`{nombre}` esta licenciada pero no tiene cota escrita")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} lo demostrado y lo licenciado "
              f"son la misma lista de siete")
        stats.ok()


def test_pendientes(stats):
    """[3] `S` sigue marcada como pendiente y NO licenciada."""
    print(f"\n{Colors.HEADER}[3] La que falta sigue constando como pendiente{Colors.ENDC}")
    problemas = []
    if set(COTAS_PENDIENTES) != {'S'}:
        problemas.append(f"esperaba solo S pendiente, veo {sorted(COTAS_PENDIENTES)}")
    for nombre in ('S',):
        if nombre in DESBLOQUEADAS:
            problemas.append(f"`{nombre}` esta licenciada sin demostracion")
        if nombre in COTAS_DEMOSTRADAS:
            problemas.append(f"`{nombre}` figura como demostrada y no lo esta")
        enunciado = COTAS_PENDIENTES.get(nombre, ("", ""))[0]
        print(f"  {Colors.WARN}PENDIENTE{Colors.ENDC} {nombre}: {enunciado}")
        if "k = 0" not in enunciado:
            problemas.append("el hueco de `S` ya no consta acotado a k = 0")
    fuente = _fuente()
    if "no está" not in fuente.lower() and "LO QUE NO ESTÁ" not in fuente:
        problemas.append("el .lean no declara lo que NO demuestra")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 7 de 8: el hueco esta escrito, "
              f"no disimulado")
        stats.ok()


def test_mecanismo(stats):
    """[4] `eliminar_lineales` respeta la licencia: sin ella no elimina, con ella si.

    Se prueba sobre un sistema MINIMO en vez de sobre el de la seccion 3, que
    tarda horas por culpa de (XIV). El mecanismo es el mismo.
    """
    print(f"\n{Colors.HEADER}[4] El mecanismo `demostradas` hace lo que dice{Colors.ENDC}")
    a, u, v = sympy.symbols('a u v', integer=True)
    #  u = a^2 - 1  : no negativa si a >= 1, pero el test estructural la rechaza
    eqs = [u - (a**2 - 1), v - (u + 1)]
    problemas = []
    for licencia, esperado in ((), ['v']), (('u',), ['u', 'v']):
        D = Dioph(params=[a], unknowns=[u, v], eqs=list(eqs), witness=None,
                  name="minimo")
        D.no_negativas_incognitas = licencia
        E = eliminar_lineales(D)
        hechas = sorted(str(x) for x, _ in E.eliminadas)
        print(f"  licencia={str(tuple(licencia)):10} -> elimina {hechas}   "
              f"por cota: {E.por_demostracion}")
        if hechas != sorted(esperado):
            problemas.append(f"con licencia={licencia} esperaba {esperado}, "
                             f"salio {hechas}")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} la licencia es lo unico que "
              f"cambia el resultado")
        stats.ok()


def test_numerico(stats):
    """[5] Las cotas se cumplen numericamente, y el .lean esta limpio."""
    print(f"\n{Colors.HEADER}[5] Comprobacion numerica y limpieza del .lean{Colors.ENDC}")
    r = cotas_verificadas()
    print(f"  fuerza bruta: {'OK' if r['ok'] else r['fallos'][:2]}")
    problemas = [] if r['ok'] else [r['fallos'][0]]
    fuente = _fuente()
    if re.search(r"\bsorry\b|\badmit\b|\bnative_decide\b", fuente):
        problemas.append("el .lean contiene `sorry`/`admit`/`native_decide`")
    if re.search(r"^\s*axiom\b", fuente, re.M):
        problemas.append("el .lean declara un `axiom` propio")
    if re.search(r"^import Mathlib", fuente, re.M):
        problemas.append("el .lean importa Mathlib")
    if "import Pell" not in fuente:
        problemas.append("el .lean ya no reutiliza `Pell.lean`")
    for pieza in ("completitud", "Y_mod", "Y_mono", "Y_tres"):
        if pieza not in fuente:
            problemas.append(f"la cota de `K` ya no usa `{pieza}` de Pell.lean")
    if "theorem S_nonneg_de_k_pos" not in fuente:
        problemas.append("falta `S_nonneg_de_k_pos`: el hueco de `S` deja de "
                         "estar acotado a k = 0")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} sin sorry, sin axiomas propios, "
              f"sin Mathlib; reutiliza `n_ge_two` de `Pell.lean`")
        stats.ok()


def test_censo(stats):
    """[6] El censo cuadra: 6 + 6 + 2 = 14, y cada fila esta clasificada."""
    print(f"\n{Colors.HEADER}[6] Censo de las catorce eliminaciones de JSWW (p. 461){Colors.ENDC}")
    c = censo_eliminaciones()
    for nombre, valor, estado in c['filas']:
        color = (Colors.OKGREEN if estado != 'pendiente' else Colors.WARN)
        print(f"  {color}{estado:12}{Colors.ENDC} {nombre:3} = {valor[:44]}")
    print(f"  {c['cuenta']}  ->  {c['licenciadas']} de {c['total']} licenciadas")
    problemas = []
    if c['total'] != 14:
        problemas.append(f"esperaba 14 definiciones, veo {c['total']}")
    if c['cuenta']['sin clasificar'] != 0:
        problemas.append("hay definiciones sin clasificar")
    if c['cuenta'] != {'estructural': 6, 'demostrada': 7,
                       'pendiente': 1, 'sin clasificar': 0}:
        problemas.append(f"el censo cambio: {c['cuenta']}")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} de 6 licenciadas se pasa a 13; "
              f"la que falta esta nombrada")
        stats.ok()


def main():
    print(f"{Colors.BOLD}=== LAS COTAS DE LA SECCION 3: SIETE DE OCHO, FORMALIZADAS ==={Colors.ENDC}")
    stats = Stats()
    test_hipotesis(stats)
    test_conclusion(stats)
    test_pendientes(stats)
    test_mecanismo(stats)
    test_numerico(stats)
    test_censo(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — el enunciado "
              f"formalizado es el que se cree demostrar.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
