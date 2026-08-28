#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - EL APLANADO FORMALIZADO DICE LO QUE CREEMOS QUE DICE
================================================================================
`formalizacion/lean/Aplanado.lean` es un fichero GENERADO por `dioph_lean.py`, y
justo por eso necesita este test mas que los escritos a mano: nadie lo lee. La
version anterior llevaba en el repo sin compilar, sin estar en `verificar.sh` y
sin que ningun test lo tocara -- era el artefacto del noveno defecto, con una
incognita (`g`) desaparecida de la firma del teorema.

Que compile ya no basta como garantia, porque el generador tuvo TRES defectos de
enunciado seguidos, y dos de ellos habrian dado un fichero que compila:

  * cuantificar las incognitas eliminadas en vez de sustituirlas;
  * nombrar `h` a la hipotesis, siendo `h` una incognita de JSWW;
  * emitir sobre Nat una definitoria con coeficiente negativo.

Lo que se comprueba aqui:

  1. `S` es el sistema (1) de JSWW, emparejado 1 A 1 con `ECUACIONES`;
  2. desnombrar `M` --sustituir cada `m_i` por su definicion hasta punto fijo--
     devuelve exactamente `S`: 0 faltan, 0 sobran. Es la misma comprobacion que
     `verificar_equivalencia` hace en Python, pero sobre el TEXTO del .lean;
  3. la firma del teorema menciona TODAS las incognitas originales -- que es
     exactamente lo que fallaba;
  4. las eliminadas aparecen SUSTITUIDAS en la conclusion, no cuantificadas.
"""

import os
import re
import sys

import sympy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_jsww import ECUACIONES, _SIMBOLOS

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
LEAN = os.path.join(RAIZ, 'formalizacion', 'lean', 'Aplanado.lean')


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


def _bloque(fuente, nombre):
    m = re.search(r"def %s \(([^)]*)\) : Prop :=\n(.*?)\n\n" % nombre, fuente, re.S)
    if m is None:
        raise AssertionError(f"no encuentro `def {nombre}` en {LEAN}")
    args = [t for t in m.group(1).split(':')[0].split() if t]
    cuerpo = ' '.join(l.strip() for l in m.group(2).splitlines())
    return args, [p.strip() for p in cuerpo.split('∧') if p.strip()]


def _loc(args):
    loc = {str(s): s for s in _SIMBOLOS}
    for a in args:
        loc.setdefault(a, sympy.Symbol(a, integer=True))
    return loc


def _a_sympy(texto, loc):
    izq, der = texto.split('=', 1)
    conv = lambda t: sympy.sympify(t.replace('^', '**'), locals=loc)
    return sympy.expand(conv(izq) - conv(der))


def _casa(u, v):
    return sympy.expand(u - v) == 0 or sympy.expand(u + v) == 0


def _emparejar(esperadas, obtenidas):
    pend, faltan = list(obtenidas), []
    for e in esperadas:
        for i, o in enumerate(pend):
            if _casa(e, o):
                pend.pop(i)
                break
        else:
            faltan.append(e)
    return faltan, pend


def test_S_es_jsww(stats):
    """[1] `S` es el sistema (1) de JSWW, 1 a 1."""
    print(f"\n{Colors.HEADER}[1] `S` es el sistema (1) de JSWW{Colors.ENDC}")
    fuente = _fuente()
    args, partes = _bloque(fuente, 'S')
    loc = _loc(args)
    obtenidas = [_a_sympy(p, loc) for p in partes]
    faltan, sobran = _emparejar([sympy.expand(e) for e in ECUACIONES], obtenidas)
    print(f"  {len(partes)} ecuaciones; faltan {len(faltan)}, sobran {len(sobran)}")
    if len(partes) != 14 or faltan or sobran:
        stats.fail(f"`S` no es el sistema (1): faltan {len(faltan)}, sobran {len(sobran)}")
    else:
        stats.ok()


def test_desnombrar_M_devuelve_S(stats):
    """[2] Sustituir cada nombre por su definicion en `M` devuelve `S`.

    Es `verificar_equivalencia` aplicada al TEXTO del .lean, que es lo unico que
    detecta que el fichero generado se haya quedado desincronizado del codigo.
    """
    print(f"\n{Colors.HEADER}[2] Desnombrar `M` devuelve exactamente `S`{Colors.ENDC}")
    fuente = _fuente()
    argsM, partesM = _bloque(fuente, 'M')
    argsS, partesS = _bloque(fuente, 'S')
    loc = _loc(argsM + argsS)
    ecs = [_a_sympy(p, loc) for p in partesM]
    # las definitorias son `m_i = cuerpo`
    defs = {}
    vivas = []
    for p, e in zip(partesM, ecs):
        izq = p.split('=', 1)[0].strip()
        if re.fullmatch(r"m\d+", izq):
            defs[loc[izq]] = sympy.sympify(
                p.split('=', 1)[1].replace('^', '**'), locals=loc)
        else:
            vivas.append(e)
    print(f"  {len(defs)} definitorias, {len(vivas)} vivas")

    def desnombrar(x):
        prev = None
        while prev != x:
            prev = x
            x = sympy.expand(x.subs(defs))
        return x

    recuperadas = [desnombrar(v) for v in vivas]
    originales = [sympy.expand(e) for e in ECUACIONES]
    # las eliminadas (q, y) se sustituyen tambien en las originales
    elim = {}
    for p in partesS:
        pass
    # `q` e `y` salen de las propias originales: se resuelven por sustitucion
    q, y = loc['q'], loc['y']
    elim = {q: loc['h'] + loc['j'] + loc['w'] * loc['z'],
            y: loc['l'] + loc['n'] + loc['v']}
    originales = [sympy.expand(e.subs(elim)) for e in originales]
    originales = [o for o in originales if o != 0]
    faltan, sobran = _emparejar(originales, recuperadas)
    print(f"  originales vivas {len(originales)}; faltan {len(faltan)}, sobran {len(sobran)}")
    if faltan or sobran:
        stats.fail(f"desnombrar `M` no devuelve `S`: faltan {len(faltan)}, sobran {len(sobran)}")
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 0 faltan / 0 sobran sobre el texto del .lean")
        stats.ok()


def _argumentos(texto):
    """Trocea `S a b (h + j) c ...` en su lista de argumentos, respetando parentesis."""
    args, nivel, actual = [], 0, ""
    for ch in texto:
        if ch == '(':
            nivel += 1
        elif ch == ')':
            nivel -= 1
        if ch == ' ' and nivel == 0:
            if actual:
                args.append(actual)
                actual = ""
        else:
            actual += ch
    if actual:
        args.append(actual)
    return args


def test_firma_completa(stats):
    """[3] La conclusion aplica `S` a los 26 argumentos correctos, EN ORDEN.

    Este es EL test, y es POSICIONAL a proposito. La version anterior del fichero
    cuantificaba 24 incognitas y su conclusion mencionaba `g`, que no estaba
    entre ellas: un argumento de menos desplaza todos los siguientes y el
    teorema pasa a hablar de otro sistema. Comprobar que "aparecen todas las
    letras" no lo habria cazado; comprobar la POSICION si.

    Las eliminadas (`q`, `y`) NO deben aparecer por nombre: van sustituidas por
    su definicion, que es justo el segundo defecto que tenia el generador.
    """
    print(f"\n{Colors.HEADER}[3] La conclusion aplica `S` a los argumentos correctos{Colors.ENDC}")
    fuente = _fuente()
    m = re.search(r"theorem aplanado_implica_original \(([^)]*)\)\s*\n\s*"
                  r"\(hsol : M [^)]*\) : S (.*?) := by", fuente, re.S)
    if m is None:
        stats.fail("no encuentro `theorem aplanado_implica_original` con la forma esperada")
        return
    cuantificadas = m.group(1).split(':')[0].split()
    args = _argumentos(' '.join(m.group(2).split()))
    formales, _ = _bloque(fuente, 'S')
    loc = _loc(formales + cuantificadas)
    problemas = []
    print(f"  `S` tiene {len(formales)} parametros; la conclusion pasa {len(args)}")
    if len(args) != len(formales):
        stats.fail(f"la conclusion pasa {len(args)} argumentos y `S` tiene {len(formales)}")
        return
    elim, sustituidas = [], []
    for formal, arg in zip(formales, args):
        if arg == formal:
            continue
        if not arg.startswith('('):
            problemas.append(f"en la posicion de `{formal}` va `{arg}`, que no es "
                             f"ni esa variable ni una expresion sustituida")
            continue
        sustituidas.append(formal)
        elim.append((formal, sympy.sympify(arg.replace('^', '**'), locals=loc)))
    print(f"  posiciones sustituidas por una expresion: {sustituidas}")
    # y la expresion tiene que ser la definicion correcta, sacada de las propias
    # ecuaciones originales
    esperado = {'q': loc['h'] + loc['j'] + loc['w'] * loc['z'],
                'y': loc['l'] + loc['n'] + loc['v']}
    for formal, expr in elim:
        if formal not in esperado:
            problemas.append(f"`{formal}` aparece sustituida y no deberia")
        elif sympy.expand(expr - esperado[formal]) != 0:
            problemas.append(f"la sustitucion de `{formal}` es {expr}, "
                             f"se esperaba {esperado[formal]}")
    for u in esperado:
        if u in cuantificadas:
            problemas.append(f"`{u}` esta CUANTIFICADA; deberia ir sustituida")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} las 26 posiciones correctas y en orden; "
              f"las eliminadas, exhibidas con su definicion")
        stats.ok()


def test_sin_sorry(stats):
    """[4] Sin `sorry`, sin axiomas propios, y con la guarda de sombras puesta."""
    print(f"\n{Colors.HEADER}[4] Higiene del fichero generado{Colors.ENDC}")
    fuente = _fuente()
    problemas = []
    if re.search(r"\bsorry\b|\badmit\b|\bnative_decide\b", fuente):
        problemas.append("contiene `sorry`/`admit`/`native_decide`")
    if re.search(r"^\s*axiom\b", fuente, re.M):
        problemas.append("declara un `axiom` propio")
    if "(hsol :" not in fuente:
        problemas.append("la hipotesis no se llama `hsol`: `h` es una incognita de JSWW")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} sin `sorry`, sin axiomas, hipotesis `hsol`")
        stats.ok()


def main():
    print(f"{Colors.BOLD}=== EL APLANADO GENERADO DICE LO QUE CREEMOS ==={Colors.ENDC}")
    stats = Stats()
    test_S_es_jsww(stats)
    test_desnombrar_M_devuelve_S(stats)
    test_firma_completa(stats)
    test_sin_sorry(stats)
    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — el fichero generado "
              f"dice lo que se cree.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
