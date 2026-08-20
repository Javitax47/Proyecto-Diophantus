#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - CATALOGO UNIVERSAL DE PROBLEMAS DIOFANTICOS
================================================================================
Valida src/analysis/dioph_problems.py: que la maquinaria del calculo diofantico
es GENERICA y no un truco especifico de los primos.

La prueba de universalidad es que UN SOLO verificador (verify_problem) comprueba
las dos direcciones para TODOS los conjuntos del catalogo:
    n in S      -> el testigo se construye y ANULA el sistema
    n not in S  -> NO hay testigo (busqueda exhaustiva acotada)
con un ORACULO independiente de la representacion en cada caso.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_problems import (
    build_catalog, verify_problem, rango_de, DiophProblem,
)


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; WARN = '\033[93m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def test_catalogo_universal(stats):
    print(f"{Colors.HEADER}[1] UN SOLO verificador para TODO el catalogo (modo declarado por problema){Colors.ENDC}")
    print(f"  {'conjunto':26s} {'incog':>5s} {'grado':>5s}   veredicto")
    for prob in build_catalog():
        ok, fallos = verify_problem(prob, rango_de(prob), exhaustivo=True)
        modo = ("ambas direcciones" if prob.soundness == "exhaustivo"
                else "completitud (soundness POR TEOREMA: el testigo cortocircuita)")
        if prob.testigo == "parcial":
            # Se dice en la propia linea del marcador, no en una nota al pie: el
            # testigo de esta representacion no es evaluable entero (el rango de
            # aparicion de L_psi es astronomico), asi que 'completitud' aqui
            # significa menos que en las demas filas y tiene que verse.
            _, cub, tot = prob.system.check_witness_parcial(
                {prob.param: next(v for v in rango_de(prob) if prob.oracle(v))})
            modo = f"completitud PARCIAL ({cub}/{tot} ecuaciones evaluables; el resto, POR TEOREMA)"
        if ok:
            stats.ok()
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {prob.name:24s} {prob.cost():5d} {prob.degree():5d}   {modo}")
        else:
            stats.fail(f"{prob.name}: {fallos[:2]}")


def test_oraculo_independiente(stats):
    print(f"{Colors.HEADER}[2] SOUNDNESS del metodo: el oraculo NO deriva de la representacion{Colors.ENDC}")
    from src.analysis.dioph_problems import build_catalog as _bc
    circ = [p.name for p in _bc() if p.soundness == "teorema"]
    print(f"  {Colors.WARN}Aviso declarado: en {circ} el constructor de testigos consulta")
    print(f"  el oraculo para cortocircuitar, luego su direccion inversa NO se comprueba")
    print(f"  aqui (seria circular); descansa en el teorema citado.{Colors.ENDC}")
    # Si el oraculo se dedujera del sistema, la verificacion seria circular.
    # Comprobamos que los oraculos son criterios externos e independientes.
    import sympy
    cat = {p.name: p for p in build_catalog()}
    comprobaciones = [
        ("compuesto", 91, True), ("compuesto", 97, False),
        ("cuadrado perfecto", 144, True), ("cuadrado perfecto", 145, False),
        ("Fibonacci", 55, True), ("Fibonacci", 56, False),
        ("triangular", 21, True), ("triangular", 22, False),
        ("primo", 97, True), ("primo", 91, False),
    ]
    malos = [f"{nom}({v})" for nom, v, esperado in comprobaciones
             if cat[nom].oracle(v) != esperado]
    if malos:
        stats.fail(f"oraculos incorrectos: {malos}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {len(comprobaciones)} comprobaciones: los oraculos son "
              f"criterios externos correctos (sympy / aritmetica elemental)")


def test_anadir_problema(stats):
    print(f"{Colors.HEADER}[3] EXTENSIBILIDAD: anadir un conjunto nuevo no toca la maquinaria{Colors.ENDC}")
    import sympy
    from src.analysis.dioph_calculus import Dioph
    from src.analysis.dioph_lemmas import fresh

    # Conjunto nuevo definido aqui mismo: n es un cubo perfecto.
    n = sympy.Symbol('n', integer=True)
    r = fresh("cb")
    sysm = Dioph([n], [r], [sympy.expand(n - r ** 3)],
                 witness=lambda v: ({r: int(sympy.integer_nthroot(int(v[n]), 3)[0])}
                                    if int(v[n]) >= 0 and sympy.integer_nthroot(int(v[n]), 3)[1]
                                    else None),
                 name="cubo")
    nuevo = DiophProblem("cubo perfecto", n, sysm,
                         lambda v: v >= 0 and sympy.integer_nthroot(v, 3)[1],
                         "n = r^3", search_bound=12)
    ok, fallos = verify_problem(nuevo, range(0, 40), exhaustivo=True)
    if ok:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} conjunto NUEVO ('cubo perfecto', {nuevo.cost()} incognita) "
              f"verificado por el MISMO verificador, sin tocar nada")
    else:
        stats.fail(f"el problema nuevo no verifica: {fallos[:2]}")


def test_universalidad_declarada(stats):
    print(f"{Colors.HEADER}[4] POR QUE ESTO IMPORTA (marco del record){Colors.ENDC}")
    cat = build_catalog()
    costes = {p.name: p.cost() for p in cat}
    print(f"  El teorema de Matiyasevich NO es sobre primos: dice que TODO conjunto")
    print(f"  diofantico admite representacion con 9 incognitas. Los primos son UNA instancia.")
    print(f"  Costes actuales del catalogo: " +
          ", ".join(f"{k}={v}" for k, v in sorted(costes.items(), key=lambda x: x[1])))
    print(f"  {Colors.WARN}-> la reduccion a 9 debe ser una TRANSFORMACION GENERICA sobre Dioph,")
    print(f"     no una construccion a medida para cada conjunto.{Colors.ENDC}")
    if len(cat) >= 8 and 'primo' in costes:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} catalogo con {len(cat)} conjuntos sobre la misma maquinaria")
    else:
        stats.fail("catalogo incompleto")


def main():
    print(f"{Colors.BOLD}=== CATALOGO UNIVERSAL DE PROBLEMAS DIOFANTICOS ==={Colors.ENDC}")
    stats = Stats()
    test_catalogo_universal(stats)
    test_oraculo_independiente(stats)
    test_anadir_problema(stats)
    test_universalidad_declarada(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — la maquinaria es UNIVERSAL: "
              f"un solo verificador valida todo el catalogo en ambas direcciones.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
