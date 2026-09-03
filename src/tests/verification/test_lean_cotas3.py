#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - LAS COTAS DE LA SECCION 3 DICEN LO QUE CREEMOS QUE DICEN
================================================================================
`formalizacion/lean/Cotas3.lean` demuestra LAS OCHO cotas que bloquean
las catorce eliminaciones del Teorema 3.9 de JSWW. Cada cota licencia eliminar
una incognita cuya definicion el criterio estructural del proyecto --"todos los
coeficientes >= 0"-- rechaza por una resta.

Que el .lean compile y no tenga `sorry` garantiza la DEMOSTRACION. Lo que este
fichero comprueba es el ENUNCIADO, que es donde se cuela el error:

  [1] cada hipotesis del teorema es LITERALMENTE una ecuacion de `ECUACIONES_3`;
  [2] la conclusion cubre exactamente las incognitas de `DESBLOQUEADAS`, que son
      las que `sistema3()` declara licenciadas;
  [3] no queda ninguna PENDIENTE, y `S` --la ultima-- consta como resuelta por
      el ENUNCIADO (el teorema pide `k >= 1`), no por una demostracion nueva;
  [4] el mecanismo `demostradas` de `eliminar_lineales` hace lo que dice: sin la
      licencia no elimina, con ella si;
  [5] sin `sorry`, sin `axiom` propio, sin Mathlib;
  [6] el censo cuadra: con el parametro en su dominio, 7 estructurales +
      7 demostradas + 0 pendientes = 14, y sin el, 13; la diferencia es `S`;
  [7] la conversion de la desigualdad (XIV) no arrastra ninguna hipotesis, y la
      razon por la que no la arrastra es la MISMA que cierra `S`.

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
from src.analysis.dioph_jsww3 import (AFIRMADO, COTAS_DEMOSTRADAS,
                                      COTAS_PENDIENTES, DESBLOQUEADAS,
                                      ECUACIONES_3, INCOGNITAS_3,
                                      PARAMETRO_MINIMO,
                                      RESUELTAS_POR_EL_ENUNCIADO,
                                      censo_eliminaciones, cotas_verificadas, k,
                                      sistema3)
from src.analysis.dioph_jsww3 import _xiv_numerador_denominador

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
    ("XXI", 21, "S = (z + 1) * (k + 1) - 2"),
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
    print(f"  demostradas en el .lean: {sorted(en_lean)}")
    print(f"  licencias que pide el optimizador (DESBLOQUEADAS): "
          f"{sorted(DESBLOQUEADAS)}")
    print(f"  sistema3().no_negativas_incognitas: "
          f"{sorted(sistema3().no_negativas_incognitas)}")
    problemas = []
    # LAS DOS LISTAS NO SON LA MISMA, Y LA DIFERENCIA ES EL RESULTADO. El .lean
    # demuestra OCHO cotas; el optimizador solo necesita SIETE licencias, porque
    # la octava --`S`-- pasa el criterio estructural ella sola una vez el
    # parametro esta en su dominio (`k = k'+1`). O sea: la demostracion de `S`
    # existe y esta auditada, pero ya no hace falta CITARLA para eliminar.
    if en_lean != set(DESBLOQUEADAS) | {'S'}:
        problemas.append(f"la conclusion cubre {sorted(en_lean)}, "
                         f"esperaba {sorted(set(DESBLOQUEADAS) | {'S'})}")
    if 'S' in DESBLOQUEADAS:
        problemas.append("`S` no deberia necesitar licencia: es estructural "
                         "tras reparametrizar")
    print(f"  {Colors.OKGREEN}la diferencia es `S`{Colors.ENDC}: demostrada, pero "
          f"ya no hace falta citarla -- es estructural")
    if set(sistema3().no_negativas_incognitas) != set(DESBLOQUEADAS):
        problemas.append("`sistema3()` no declara exactamente `DESBLOQUEADAS`")
    for nombre in DESBLOQUEADAS:
        if nombre not in COTAS_DEMOSTRADAS:
            problemas.append(f"`{nombre}` esta licenciada pero no tiene cota escrita")
    if 'S' not in RESUELTAS_POR_EL_ENUNCIADO:
        problemas.append("`S` se demuestra en el .lean pero no consta en Python")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} ocho demostradas, siete "
              f"licencias, y la diferencia esta explicada")
        stats.ok()


def test_pendientes(stats):
    """[3] No queda ninguna cota pendiente, y `S` consta resuelta por el enunciado.

    LO QUE ESTE TEST PROTEGE. `S` no se cerro demostrando nada nuevo: se cerro
    leyendo la p. 456, donde el Teorema 3.9 pide `k >= 1`. Si alguien volviera a
    poner el parametro sobre N --que es lo que este proyecto tenia-- el sistema
    afirmaria mas que el teorema y `S` dejaria de ser eliminable. Aqui se ata
    `PARAMETRO_MINIMO` a lo que el sistema construye.
    """
    print(f"\n{Colors.HEADER}[3] El dominio del parametro, que es donde estaba el fallo{Colors.ENDC}")
    problemas = []
    print(f"  Teorema 3.9 (p. 456): \"for any POSITIVE integer k\"  =>  "
          f"PARAMETRO_MINIMO = {PARAMETRO_MINIMO}")
    if PARAMETRO_MINIMO != 1:
        problemas.append(f"PARAMETRO_MINIMO deberia ser 1, es {PARAMETRO_MINIMO}")
    if AFIRMADO.get("parametro_minimo") != 1:
        problemas.append("AFIRMADO no registra el dominio del parametro")
    if COTAS_PENDIENTES:
        problemas.append(f"quedan cotas pendientes: {sorted(COTAS_PENDIENTES)}")
    if set(RESUELTAS_POR_EL_ENUNCIADO) != {'S'}:
        problemas.append(f"esperaba solo S resuelta por el enunciado, veo "
                         f"{sorted(RESUELTAS_POR_EL_ENUNCIADO)}")
    D = sistema3()
    print(f"  sistema3().parametro_minimo = {getattr(D, 'parametro_minimo', None)}   "
          f"(sistema3(k_positivo=False) = "
          f"{getattr(sistema3(k_positivo=False), 'parametro_minimo', None)})")
    if getattr(D, "parametro_minimo", None) != 1:
        problemas.append("`sistema3()` no usa el dominio del teorema por defecto")
    fuente = _fuente()
    if "positive" not in fuente:
        problemas.append("el .lean no cita el dominio del enunciado")
    if "theorem S_nonneg_de_k_pos" not in fuente:
        problemas.append("falta `S_nonneg_de_k_pos`")
    if "theorem S_nonneg_reparametrizado" not in fuente:
        problemas.append("falta `S_nonneg_reparametrizado`")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 8 de 8: la ultima se cerro "
              f"transcribiendo bien el enunciado, no demostrando de mas")
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
    """[6] El censo cuadra, y la diferencia entre los dos dominios es `S`."""
    print(f"\n{Colors.HEADER}[6] Censo de las catorce eliminaciones de JSWW (p. 461){Colors.ENDC}")
    c = censo_eliminaciones()
    for nombre, valor, estado in c['filas']:
        color = (Colors.OKGREEN if estado != 'pendiente' else Colors.WARN)
        print(f"  {color}{estado:12}{Colors.ENDC} {nombre:3} = {valor[:44]}")
    print(f"  {c['cuenta']}  ->  {c['licenciadas']} de {c['total']} licenciadas")
    lit = censo_eliminaciones(k_positivo=False)
    print(f"  con `k` literal (que afirma MAS que el teorema): "
          f"{lit['licenciadas']} de {lit['total']}")
    problemas = []
    if c['total'] != 14:
        problemas.append(f"esperaba 14 definiciones, veo {c['total']}")
    if c['cuenta'] != {'estructural': 7, 'demostrada': 7,
                       'pendiente': 0, 'sin clasificar': 0}:
        problemas.append(f"el censo cambio: {c['cuenta']}")
    if lit['licenciadas'] != 13:
        problemas.append(f"con `k` literal esperaba 13, veo {lit['licenciadas']}")
    # y la diferencia entre los dos censos tiene que ser EXACTAMENTE `S`
    dif = {n for n, _, e in c['filas'] if e != 'pendiente'} - \
          {n for n, _, e in lit['filas'] if e != 'pendiente'}
    if dif != {'S'}:
        problemas.append(f"la diferencia entre dominios deberia ser {{'S'}}, es {dif}")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} de 6 licenciadas se pasa a "
              f"{c['licenciadas']}: las catorce de la p. 461")
        stats.ok()


def test_xiv(stats):
    """[7] La conversion de (XIV) es fiel, y sin hipotesis heredada.

    Este modulo declaro durante meses que (XIV) heredaba `De > 0` --la formula
    (15) de la p. 458 de JSWW-- sin demostrar, y que por eso el sistema servia
    para medir pero no para publicar. Era falso: la codificacion con holgura lo
    fuerza. Aqui se comprueban las tres piezas:

      * que `Nu/De` ES el `beta` impreso (la cancelacion de `L`);
      * que `4u^2 < d^2` con `Nu >= 1` y `S+1 >= 1` obliga a `d > 0`;
      * y la CONTRAPRUEBA: con `S+1 = 0` --el caso `z = k = 0` que el dominio del
        teorema excluye-- las soluciones de denominador negativo reaparecen.

    La tercera es la que importa: dice que el hueco de `S` y el de (XIV) eran el
    mismo hecho, no dos problemas.
    """
    print(f"\n{Colors.HEADER}[7] La desigualdad (XIV): fiel y sin hipotesis heredada{Colors.ENDC}")
    problemas = []
    Nu, De = _xiv_numerador_denominador()
    print(f"  Nu = {Nu}")
    print(f"  De = {De}")
    r = cotas_verificadas()
    print(f"  Nu/De == beta impreso (p. 457), y De>0 forzado: "
          f"{'OK' if r['ok'] else r['fallos'][:1]}")
    if not r['ok']:
        problemas.append(r['fallos'][0])

    # la ecuacion que emite el modulo tiene que ser LA de la conversion
    from src.analysis.dioph_jsww3 import S as S_, s1 as s1_
    esperada = sympy.expand(4 * (Nu - (S_ + 1) * De) ** 2 + 1 + s1_ - De ** 2)
    if sympy.expand(ECUACIONES_3[14] - esperada) != 0:
        problemas.append("(XIV) emitida no es 4(Nu-(S+1)De)^2 + 1 + s1 - De^2")
    print(f"  ECUACIONES_3[14] es 4(Nu-(S+1)De)^2 + 1 + s1 - De^2: "
          f"{sympy.expand(ECUACIONES_3[14] - esperada) == 0}")

    # y el .lean tiene que traer los teoremas que lo sostienen
    fuente = _fuente()
    for nombre, papel in [("holgura_iff", "la holgura es exactamente `<`"),
                          ("De_pos", "el denominador es positivo, no se supone"),
                          ("Nu_ge_one", "Nu = RKC^2 >= 1"),
                          ("xiv_fiel", "S+1 es el entero mas proximo a Nu/De"),
                          ("xiv_desde_las_cotas", "con lo que da el sistema")]:
        if not re.search(r"theorem %s\b" % nombre, fuente):
            problemas.append(f"falta el teorema `{nombre}`")
        else:
            print(f"  {Colors.OKGREEN}OK{Colors.ENDC} `{nombre}` — {papel}")
    if "heredada" not in fuente:
        problemas.append("el .lean ya no explica que hipotesis NO hace falta")

    # TODOS los teoremas del .lean tienen que estar en la auditoria de axiomas.
    # POR QUE ESTA COMPROBACION EXISTE: al renombrar `K_nonneg` -> `K_ge_one` la
    # auditoria se quedo pidiendo el nombre viejo. `verificar.sh` fallaba con
    # codigo 1, pero como la salida se leia por una tuberia (`| tail`), el codigo
    # que se veia era el de `tail`: 0. Un teorema pudo haber quedado sin auditar
    # sin que nada lo dijera. Esto ata las dos listas.
    sh = open(os.path.join(RAIZ, 'formalizacion', 'lean', 'verificar.sh'),
              encoding='utf-8').read()
    teoremas = re.findall(r"^theorem ([A-Za-z_0-9]+)", fuente, re.M)
    auditados = set(re.findall(r"#print axioms (\w+)", sh))
    sin_auditar = [t for t in teoremas if t not in auditados]
    print(f"  {len(teoremas)} teoremas en el .lean, "
          f"{len([t for t in teoremas if t in auditados])} en la auditoria de axiomas")
    if sin_auditar:
        problemas.append(f"teoremas sin auditar en verificar.sh: {sin_auditar}")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} la transcripcion del Teorema 3.9 "
              f"no arrastra ninguna hipotesis heredada")
        stats.ok()


def main():
    print(f"{Colors.BOLD}=== LAS COTAS DE LA SECCION 3: LAS OCHO, Y LAS CATORCE ELIMINACIONES ==={Colors.ENDC}")
    stats = Stats()
    test_hipotesis(stats)
    test_conclusion(stats)
    test_pendientes(stats)
    test_mecanismo(stats)
    test_numerico(stats)
    test_censo(stats)
    test_xiv(stats)

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
