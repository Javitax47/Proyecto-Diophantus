#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - LA ELIMINACION FORMALIZADA DICE LO QUE CREEMOS QUE DICE
================================================================================
`formalizacion/lean/Eliminacion.lean` demuestra que el sistema (1) de JSWW --25
incognitas mas el parametro, generador (26, 25)-- es EQUISATISFACIBLE con uno de
22 incognitas del mismo grado, o sea (23, 25). Que compile y no tenga `sorry`
garantiza que la DEMOSTRACION es correcta; no garantiza que el ENUNCIADO sea el
que queremos.

Aqui esta el hueco, y es mas grande que en `CotaA.lean`: alli las hipotesis eran
cinco ecuaciones y se podian leer a ojo; aqui son CATORCE mas ONCE, escritas a
mano en Lean. Un signo mal puesto en la ecuacion (12) daria un teorema que
compila, que suena igual de fuerte, y que habla de otro sistema.

Lo que se comprueba, y las cuatro cosas hacen falta:

  1. las 14 ecuaciones de `completo` son las 14 de `ECUACIONES`, emparejadas
     1 A 1 (que "exista alguna que case" taparia una repetida y una ausente);
  2. `defZ`, `defQ` y `defY` son exactamente las definiciones que usa
     `eliminar_lineales` -- las mismas que el criterio de no negatividad acepta;
  3. las 11 ecuaciones de `reducido` son las 11 del sistema eliminado, tambien
     1 a 1;
  4. las listas de variables cuantificadas en el teorema son 25 y 22, y lo que
     falta en la segunda es EXACTAMENTE {q, y, z}. Sin esto el teorema podria
     estar cuantificando de menos y ser trivialmente cierto.
"""

import os
import re
import sys

import sympy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_jsww import ECUACIONES, _SIMBOLOS, sistema
from src.analysis.dioph_degree import eliminar_lineales

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
LEAN = os.path.join(RAIZ, 'formalizacion', 'lean', 'Eliminacion.lean')

#: Las tres incognitas que se eliminan. El orden importa: `q` depende de `z`.
ELIMINADAS = ['z', 'q', 'y']


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
    loc = {str(s): s for s in _SIMBOLOS}
    # Las tres definiciones de Lean, como funciones sympy, para poder evaluar
    # `defQ g h j k w` dentro de una ecuacion de `reducido`.
    g, h, j, k, w, l, n, v = (loc[c] for c in 'ghjkwlnv')
    loc['defZ'] = lambda G, H, J, K: (G * K + 2 * G + K + 1) * (H + J) + H
    loc['defQ'] = lambda G, H, J, K, W: W * loc['defZ'](G, H, J, K) + H + J
    loc['defY'] = lambda L, N, V: N + L + V
    return loc


#: `defZ g h j k` en Lean es aplicacion por yuxtaposicion; en Python hace falta
#: `defZ(g, h, j, k)`. Se traduce con el numero exacto de argumentos de cada una.
_ARIDAD = {'defZ': 4, 'defQ': 5, 'defY': 3}


def _aplicaciones(texto):
    """`defQ g h j k w` -> `defQ(g, h, j, k, w)`."""
    for nombre, ar in _ARIDAD.items():
        patron = nombre + r"((?:\s+[a-z]){%d})" % ar
        texto = re.sub(patron,
                       lambda m: "%s(%s)" % (nombre, ", ".join(m.group(1).split())),
                       texto)
    return texto


def _a_sympy(texto, loc):
    """`a ^ 2 * y ^ 2 + 1 = x ^ 2`  ->  expresion sympy `izq - der`."""
    izq, der = texto.split('=', 1)
    conv = lambda t: sympy.sympify(_aplicaciones(t).replace('^', '**'), locals=loc)
    return sympy.expand(conv(izq) - conv(der))


def _cuerpo(fuente, nombre):
    """Extrae el cuerpo de `def <nombre> (...) : Prop := ...` hasta la linea en
    blanco siguiente, y lo devuelve troceado por `∧`."""
    m = re.search(r"def %s \(([^)]*)\) : Prop :=\n(.*?)\n\n" % nombre,
                  fuente, re.S)
    if m is None:
        raise AssertionError(f"no encuentro `def {nombre}` en {LEAN}")
    args = [t for t in m.group(1).split(':')[0].split() if t]
    cuerpo = ' '.join(l.strip() for l in m.group(2).splitlines())
    partes = [p.strip() for p in cuerpo.split('∧')]
    partes[0] = partes[0].lstrip()
    return args, [p for p in partes if p]


def _casa(u, v):
    return sympy.expand(u - v) == 0 or sympy.expand(u + v) == 0


def _emparejar(esperadas, obtenidas):
    """Emparejamiento 1 A 1. Devuelve (faltan, sobran)."""
    pendientes, faltan = list(obtenidas), []
    for e in esperadas:
        for i, o in enumerate(pendientes):
            if _casa(e, o):
                pendientes.pop(i)
                break
        else:
            faltan.append(e)
    return faltan, pendientes


def test_completo_es_el_sistema_1(stats):
    """[1] Las 14 ecuaciones de `completo` son las 14 de JSWW, 1 a 1."""
    print(f"\n{Colors.HEADER}[1] `completo` es el sistema (1) de JSWW{Colors.ENDC}")
    loc = _locales()
    _, partes = _cuerpo(_fuente(), 'completo')
    if len(partes) != 14:
        stats.fail(f"`completo` tiene {len(partes)} ecuaciones, no 14")
        return
    obtenidas = [_a_sympy(p, loc) for p in partes]
    esperadas = [sympy.expand(e) for e in ECUACIONES]
    faltan, sobran = _emparejar(esperadas, obtenidas)
    print(f"  14 ecuaciones leidas del .lean; faltan {len(faltan)}, sobran {len(sobran)}")
    if faltan or sobran:
        stats.fail(f"`completo` no es el sistema (1): faltan {faltan[:1]}, sobran {sobran[:1]}")
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} las 14 casan una a una con `ECUACIONES`")
        stats.ok()


def test_definiciones(stats):
    """[2] `defZ`, `defQ`, `defY` son las de `eliminar_lineales`."""
    print(f"\n{Colors.HEADER}[2] Las tres definiciones son las que elimina el codigo{Colors.ENDC}")
    loc = _locales()
    E = eliminar_lineales(sistema(expandir=False), 99, solo=ELIMINADAS)
    delcodigo = {u: sympy.expand(v) for u, v in E.eliminadas}
    g, h, j, k, w, l, n, v = (loc[c] for c in 'ghjkwlnv')
    dellean = {'z': sympy.expand(loc['defZ'](g, h, j, k)),
               'q': sympy.expand(loc['defQ'](g, h, j, k, w)),
               'y': sympy.expand(loc['defY'](l, n, v))}
    porNombre = {str(u): u for u in delcodigo}
    problemas = []
    for u in ELIMINADAS:
        if u not in porNombre:
            problemas.append(f"`{u}` no la elimina `eliminar_lineales`")
            continue
        # La del codigo puede mencionar otras eliminadas; se despliega hasta
        # punto fijo (`q = h + j + w*z` menciona `z`, que tambien se elimina).
        esperada = delcodigo[porNombre[u]]
        for _ in range(len(delcodigo)):
            esperada = sympy.expand(esperada.subs(delcodigo))
        ok = sympy.expand(esperada - dellean[u]) == 0
        print(f"  {Colors.OKGREEN + 'OK' + Colors.ENDC if ok else Colors.FAIL + 'MAL' + Colors.ENDC}"
              f"  {u} = {dellean[u]}")
        if not ok:
            problemas.append(f"`{u}`: el codigo dice {esperada}, el .lean {dellean[u]}")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} y las tres tienen todos los coeficientes >= 0, "
              f"que es lo que `defZ_nonneg`, `defQ_nonneg` y `defY_nonneg` demuestran en Lean")
        stats.ok()


def test_reducido_es_el_sistema_eliminado(stats):
    """[3] Las 11 ecuaciones de `reducido` son las del sistema eliminado, 1 a 1."""
    print(f"\n{Colors.HEADER}[3] `reducido` es el sistema tras eliminar q, y, z{Colors.ENDC}")
    loc = _locales()
    _, partes = _cuerpo(_fuente(), 'reducido')
    if len(partes) != 11:
        stats.fail(f"`reducido` tiene {len(partes)} ecuaciones, no 11")
        return
    obtenidas = [_a_sympy(p, loc) for p in partes]
    E = eliminar_lineales(sistema(expandir=False), 99, solo=ELIMINADAS)
    esperadas = [sympy.expand(e) for e in E.eqs]
    faltan, sobran = _emparejar(esperadas, obtenidas)
    print(f"  11 ecuaciones leidas del .lean; faltan {len(faltan)}, sobran {len(sobran)}")
    if faltan or sobran:
        stats.fail(f"`reducido` no es el sistema eliminado: faltan {len(faltan)}, "
                   f"sobran {len(sobran)}")
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} las 11 casan una a una con el sistema "
              f"que devuelve `eliminar_lineales`")
        stats.ok()


def test_cuantificadores(stats):
    """[4] El teorema cuantifica 25 incognitas y 22, y la diferencia es {q,y,z}.

    Sin esto el enunciado podria estar cuantificando de menos --por ejemplo
    olvidando una incognita en el lado izquierdo-- y ser cierto por vacio.
    """
    print(f"\n{Colors.HEADER}[4] El teorema cuantifica 25 y 22, y la diferencia es q, y, z{Colors.ENDC}")
    fuente = _fuente()
    m = re.search(r"theorem equisatisfacible.*?:=", fuente, re.S)
    if m is None:
        stats.fail("no encuentro `theorem equisatisfacible`")
        return
    binders = re.findall(r"∃ ([a-z ]+) : Int,", m.group(0))
    if len(binders) != 2:
        stats.fail(f"esperaba dos bloques ∃, encontre {len(binders)}")
        return
    izq, der = [b.split() for b in binders]
    faltan = sorted(set(izq) - set(der))
    print(f"  izquierda: {len(izq)} incognitas    derecha: {len(der)} incognitas")
    print(f"  la derecha no cuantifica: {faltan}")
    problemas = []
    if len(izq) != 25:
        problemas.append(f"el lado completo cuantifica {len(izq)} incognitas, no 25")
    if len(der) != 22:
        problemas.append(f"el lado reducido cuantifica {len(der)} incognitas, no 22")
    if faltan != sorted(ELIMINADAS):
        problemas.append(f"la diferencia es {faltan}, no {sorted(ELIMINADAS)}")
    if set(der) - set(izq):
        problemas.append(f"el lado reducido cuantifica variables nuevas: "
                         f"{sorted(set(der) - set(izq))}")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 25 vs 22: el generador pasa de "
              f"(26, 25) a {Colors.BOLD}(23, 25){Colors.ENDC} "
              f"(las incognitas mas el parametro k)")
        stats.ok()


def test_sin_sorry(stats):
    """[5] El fichero no tiene `sorry` ni axiomas propios."""
    print(f"\n{Colors.HEADER}[5] Sin `sorry` y sin axiomas propios{Colors.ENDC}")
    fuente = _fuente()
    problemas = []
    if re.search(r"\bsorry\b", fuente):
        problemas.append("el .lean contiene `sorry`")
    if re.search(r"^\s*axiom\b", fuente, re.M):
        problemas.append("el .lean declara un `axiom` propio")
    if problemas:
        stats.fail(problemas[0])
    else:
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} ni `sorry` ni `axiom` "
              f"(la auditoria de axiomas del nucleo la hace `verificar.sh`)")
        stats.ok()


def main():
    print(f"{Colors.BOLD}=== LA ELIMINACION (26,25) -> (23,25), FORMALIZADA ==={Colors.ENDC}")
    stats = Stats()
    test_completo_es_el_sistema_1(stats)
    test_definiciones(stats)
    test_reducido_es_el_sistema_eliminado(stats)
    test_cuantificadores(stats)
    test_sin_sorry(stats)

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
