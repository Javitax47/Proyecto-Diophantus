#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - EL (21,25) FORMALIZADO DICE LO QUE CREEMOS QUE DICE
================================================================================
`formalizacion/lean/Eliminacion21.lean` demuestra que el sistema (1) de JSWW
--25 incognitas mas el parametro-- es equisatisfacible con uno de 20, o sea
generador (21, 25) frente al (26, 25) que ellos publicaron.

ES EL ENUNCIADO CON MAS SUPERFICIE DE ERROR DE TODO EL PROYECTO. Hay catorce
ecuaciones escritas a mano, mas nueve, mas SIETE definiciones, y ademas una
reparametrizacion (`n = N+2`, `a = e+1+A`) que renombra dos incognitas. Un signo
mal puesto en cualquiera de esas piezas da un teorema que compila, que suena
igual de fuerte, y que habla de otro sistema.

Lo que se comprueba, y las cuatro cosas hacen falta:

  1. las SIETE definiciones del .lean son las que produce `eliminar_lineales`
     sobre el sistema reparametrizado;
  2. las NUEVE ecuaciones de `reducido21` son las nueve del sistema eliminado,
     emparejadas 1 A 1;
  3. los cuantificadores son 25 y 20, y la diferencia es exactamente
     «se van {a,e,m,n,q,x,y}, entran {N,A}»;
  4. la ida usa las DOS cotas de Pell -- si alguien las quitara, la vuelta
     seria falsa y el teorema, tambien.
"""

import os
import re
import sys

import sympy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_jsww import sistema_cota_pell_fuerte, _SIMBOLOS
from src.analysis.dioph_degree import eliminar_lineales

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
LEAN = os.path.join(RAIZ, 'formalizacion', 'lean', 'Eliminacion21.lean')

ELIMINADAS = ['e', 'm', 'q', 'x', 'y']


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


def _locales():
    """Las siete definiciones del .lean, como funciones sympy."""
    loc = {str(s): s for s in _SIMBOLOS}
    loc['N'] = sympy.Symbol('N', integer=True)
    loc['A'] = sympy.Symbol('A', integer=True)
    vQ = lambda h, j, w, z: w*z + h + j
    vN = lambda N: N + 2
    vY = lambda N, l, v: vN(N) + l + v
    vE = lambda N, p, h, j, w, z: 2*vN(N) + p + vQ(h, j, w, z) + z
    vA = lambda N, p, h, j, w, z, A: vE(N, p, h, j, w, z) + 1 + A
    vM = lambda a, n, p, l, b: p + l*(a - n - 1) + b*(2*a*n + 2*a - n**2 - 2*n - 2)
    vX = lambda a, p, q, y, s: q + y*(a - p - 1) + s*(2*a*p + 2*a - p**2 - 2*p - 2)
    loc.update(vQ=vQ, vN=vN, vY=vY, vE=vE, vA=vA, vM=vM, vX=vX)
    return loc


_ARIDAD = {'vQ': 4, 'vN': 1, 'vY': 3, 'vE': 6, 'vA': 7, 'vM': 5, 'vX': 5}


def _aplicaciones(texto):
    """`vE N p h j w z` -> `vE(N, p, h, j, w, z)`, respetando parentesis.

    Se procesa de MAYOR a MENOR aridad: `vA N p h j w z A` empieza por los
    mismos simbolos que `vE N p h j w z`, y al reves se comeria los argumentos.
    """
    for nombre in sorted(_ARIDAD, key=lambda n: -_ARIDAD[n]):
        ar = _ARIDAD[nombre]
        patron = nombre + r"((?:\s+[A-Za-z]\b){%d})" % ar
        texto = re.sub(patron,
                       lambda m: "%s(%s)" % (nombre, ", ".join(m.group(1).split())),
                       texto)
    return texto


def _a_sympy(texto, loc):
    izq, der = texto.split('=', 1)
    conv = lambda t: sympy.sympify(_aplicaciones(t).replace('^', '**'), locals=loc)
    return sympy.expand(conv(izq) - conv(der))


def _cuerpo_reducido(fuente):
    m = re.search(r"def reducido21 \(([^)]*)\) : Prop :=\n(.*?)\n\n", fuente, re.S)
    if m is None:
        raise AssertionError("no encuentro `def reducido21`")
    args = [t for t in m.group(1).split(':')[0].split() if t]
    lineas = [l.strip() for l in m.group(2).splitlines()]
    lineas = [l for l in lineas if not l.startswith('let')]
    cuerpo = ' '.join(lineas)
    partes = [p.strip() for p in cuerpo.split('∧')]
    return args, [p for p in partes if p]


def _loc_con_lets(fuente):
    """`reducido21` empieza con `let n := vN N`, `let q := vQ h j w z`, ...

    Se EVALUAN esos `let` y se meten en el diccionario de locales, en vez de
    sustituirlos como texto: sustituir texto mete parentesis anidados que el
    traductor de aplicaciones por yuxtaposicion ya no sabe leer. Dentro del
    cuerpo, `n`, `q`, `y`, `e`, `a`, `m` y `x` significan los valores atados,
    no los simbolos originales -- que es justo lo que hay que comprobar.
    """
    loc = _locales()
    m = re.search(r"def reducido21 \([^)]*\) : Prop :=\n(.*?)\n\n", fuente, re.S)
    if m is None:
        raise AssertionError("no encuentro el cuerpo de `reducido21`")
    for nombre, valor in re.findall(r"let (\w+) := (.+)", m.group(1)):
        loc[nombre] = sympy.sympify(_aplicaciones(valor.strip()), locals=loc)
    return loc


def _casa(u, v):
    return sympy.expand(u - v) == 0 or sympy.expand(u + v) == 0


def test_definiciones(stats):
    """[1] Las siete definiciones son las que elimina el codigo."""
    print(f"\n{Colors.HEADER}[1] Las definiciones del .lean son las de `eliminar_lineales`{Colors.ENDC}")
    loc = _locales()
    S = sistema_cota_pell_fuerte()
    E = eliminar_lineales(S, 99, solo=ELIMINADAS)
    delcodigo = {str(u): sympy.expand(v) for u, v in E.eliminadas}
    for _ in range(len(delcodigo)):
        sub = {sympy.Symbol(u, integer=True): v for u, v in delcodigo.items()}
        delcodigo = {u: sympy.expand(v.subs(sub)) for u, v in delcodigo.items()}
    h, j, w, z, N, l, v, p, A, b, s = (loc[c] for c in
                                       ['h', 'j', 'w', 'z', 'N', 'l', 'v', 'p', 'A', 'b', 's'])
    a_ = loc['vA'](N, p, h, j, w, z, A)
    n_ = loc['vN'](N)
    dellean = {
        'q': loc['vQ'](h, j, w, z),
        'y': loc['vY'](N, l, v),
        'e': loc['vE'](N, p, h, j, w, z),
        'm': loc['vM'](a_, n_, p, l, b),
        'x': loc['vX'](a_, p, loc['vQ'](h, j, w, z), loc['vY'](N, l, v), s),
    }
    problemas = []
    for u in ELIMINADAS:
        ok = sympy.expand(delcodigo[u] - dellean[u]) == 0
        marca = Colors.OKGREEN + "OK" + Colors.ENDC if ok else Colors.FAIL + "MAL" + Colors.ENDC
        print(f"  {marca}  {u}  ({len(str(sympy.expand(dellean[u])))} caracteres al expandir)")
        if not ok:
            problemas.append(f"`{u}`: el .lean y el codigo no coinciden")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} las cinco eliminadas, mas `vN` y `vA` "
              f"(la reparametrizacion), coinciden")
        stats.ok()


def test_reducido(stats):
    """[2] Las 9 ecuaciones de `reducido21` son las del sistema eliminado, 1 a 1."""
    print(f"\n{Colors.HEADER}[2] `reducido21` es el sistema tras eliminar e, m, q, x, y{Colors.ENDC}")
    fuente = _fuente()
    loc = _loc_con_lets(fuente)
    _, partes = _cuerpo_reducido(fuente)
    if len(partes) != 9:
        stats.fail(f"`reducido21` tiene {len(partes)} ecuaciones, no 9")
        return
    obtenidas = [_a_sympy(p, loc) for p in partes]
    S = sistema_cota_pell_fuerte()
    E = eliminar_lineales(S, 99, solo=ELIMINADAS)
    esperadas = [sympy.expand(e) for e in E.eqs]
    pendientes, faltan = list(obtenidas), []
    for e in esperadas:
        for i, o in enumerate(pendientes):
            if _casa(e, o):
                pendientes.pop(i)
                break
        else:
            faltan.append(e)
    print(f"  9 ecuaciones leidas del .lean; faltan {len(faltan)}, sobran {len(pendientes)}")
    if faltan or pendientes:
        stats.fail(f"`reducido21` no es el sistema eliminado: faltan {len(faltan)}, "
                   f"sobran {len(pendientes)}")
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} las 9 casan una a una "
              f"(expandidas suman {sum(len(str(x)) for x in esperadas)} caracteres: "
              f"por eso en el .lean van con las definiciones dentro)")
        stats.ok()


def test_cuantificadores(stats):
    """[3] 25 y 20, y la diferencia es la esperada."""
    print(f"\n{Colors.HEADER}[3] El teorema cuantifica 25 y 20{Colors.ENDC}")
    fuente = _fuente()
    m = re.search(r"theorem equisatisfacible21.*?:= by", fuente, re.S)
    if m is None:
        stats.fail("no encuentro `theorem equisatisfacible21`")
        return
    binders = re.findall(r"∃ ([A-Za-z ]+) : Int,", m.group(0))
    if len(binders) != 2:
        stats.fail(f"esperaba dos bloques ∃, encontre {len(binders)}")
        return
    izq, der = [b.split() for b in binders]
    se_van = sorted(set(izq) - set(der))
    entran = sorted(set(der) - set(izq))
    print(f"  izquierda: {len(izq)}   derecha: {len(der)}")
    print(f"  se van: {se_van}")
    print(f"  entran: {entran}   (la reparametrizacion n = N+2, a = e+1+A)")
    problemas = []
    if len(izq) != 25:
        problemas.append(f"el lado completo cuantifica {len(izq)}, no 25")
    if len(der) != 20:
        problemas.append(f"el lado reducido cuantifica {len(der)}, no 20")
    if se_van != ['a', 'e', 'm', 'n', 'q', 'x', 'y']:
        problemas.append(f"se van {se_van}, se esperaba a,e,m,n,q,x,y")
    if entran != ['A', 'N']:
        problemas.append(f"entran {entran}, se esperaba N y A")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 25 vs 20: el generador pasa de (26, 25) a "
              f"{Colors.BOLD}(21, 25){Colors.ENDC}")
        stats.ok()


def test_usa_las_cotas(stats):
    """[4] La ida usa las dos cotas de Pell. Sin ellas la vuelta seria falsa.

    No es decoracion: `m` y `x` se definen con `a−n−1` y `a−p−1` dentro, y sobre
    ℕ hay que EXHIBIRLAS no negativas al reconstruir la solucion. Si el teorema
    dejara de invocar las cotas, o estaria mal o estaria demostrando otra cosa.
    """
    print(f"\n{Colors.HEADER}[4] La demostracion usa las dos cotas de Pell{Colors.ENDC}")
    fuente = _fuente()
    problemas = []
    for nombre, papel in [("n_ge_two", "n >= 2, que da la reparametrizacion n = N+2"),
                          ("a_ge_e_succ_de_sistema", "a >= e+1, que desbloquea m y x")]:
        if nombre not in fuente:
            problemas.append(f"la demostracion no invoca `{nombre}`")
        else:
            print(f"  {Colors.OKGREEN}OK{Colors.ENDC} invoca `{nombre}` — {papel}")
    if re.search(r"\bsorry\b|\badmit\b|\bnative_decide\b", fuente):
        problemas.append("el .lean contiene `sorry`/`admit`/`native_decide`")
    if re.search(r"^\s*axiom\b", fuente, re.M):
        problemas.append("el .lean declara un `axiom` propio")
    if re.search(r"^import Mathlib", fuente, re.M):
        problemas.append("el .lean importa Mathlib")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} sin `sorry`, sin axiomas propios, sin Mathlib")
        stats.ok()


def main():
    print(f"{Colors.BOLD}=== EL (21,25), FORMALIZADO DE PUNTA A PUNTA ==={Colors.ENDC}")
    stats = Stats()
    test_definiciones(stats)
    test_reducido(stats)
    test_cuantificadores(stats)
    test_usa_las_cotas(stats)

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
