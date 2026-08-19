#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - ARSENAL DE PELL (maquinaria real de los records)
================================================================================
Valida src/analysis/dioph_pell.py: las propiedades de las sucesiones y_k(a),
x_k(a) que los records de pocas incognitas explotan. Cada una se verifica
numericamente ANTES de que ningun lema se construya sobre ella.

Incluye el marco correcto para hablar de "records": la frontera de Pareto
(incognitas, grado) de Jones 1982, cuyos extremos confirmados son (58, grado 4)
y (9, grado 1.638e45).
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.analysis.dioph_pell import (
    pell_xy, pell_y, pell_x, index_from_y,
    P1_divisibilidad, P1_gcd, P2_matiyasevich, P3_indice, P4_periodicidad,
    P5_parametro, crecimiento_JR, PARETO_JONES_1982, NOTA_PARETO, DOMINIO_IMPORTA,
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


def _check(stats, nombre, casos, pred, explicacion):
    malos = [c for c in casos if not pred(*c)]
    if malos:
        stats.fail(f"{nombre}: {len(malos)} fallos, p.ej. {malos[:3]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {nombre}: {len(casos)} casos — {explicacion}")


def test_identidad_pell(stats):
    print(f"{Colors.HEADER}[1] Identidad fundamental x_k^2-(a^2-1)y_k^2 = 1{Colors.ENDC}")
    casos = [(a, k) for a in range(2, 9) for k in range(0, 14)]
    malos = [(a, k) for a, k in casos
             if pell_x(a, k) ** 2 - (a * a - 1) * pell_y(a, k) ** 2 != 1]
    if malos:
        stats.fail(f"la identidad falla en {malos[:3]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {len(casos)} pares (a,k) exactos")


def test_arsenal(stats):
    print(f"{Colors.HEADER}[2] Las 5 propiedades que explotan los records{Colors.ENDC}")
    _check(stats, "P1a  y_k|y_l <=> k|l",
           [(a, k, l) for a in range(2, 7) for k in range(1, 13) for l in range(1, 13)],
           P1_divisibilidad, "relaciones de INDICE convertidas en DIVISIBILIDAD")
    _check(stats, "P1b  gcd(y_k,y_l)=y_gcd(k,l)",
           [(a, k, l) for a in range(2, 7) for k in range(1, 13) for l in range(1, 13)],
           P1_gcd, "permite PLEGAR varias divisibilidades en una (CRT)")
    _check(stats, "P2   y_k^2|y_l <=> k*y_k|l",
           [(a, k, l) for a in range(2, 6) for k in range(1, 8) for l in range(1, 60)],
           P2_matiyasevich, "LEMA DE MATIYASEVICH: hace la sucesion DEFINIBLE")
    _check(stats, "P3   y_k=k, x_k=1 (mod a-1)",
           [(a, k) for a in range(2, 12) for k in range(0, 20)],
           P3_indice, "recupera el INDICE sin gastar incognita (por que Pell < beta)")
    _check(stats, "P4   y_{2kn+-j}=+-y_j (mod x_k)",
           [(a, k, n, j, s) for a in range(2, 6) for k in range(1, 6)
            for n in range(0, 3) for j in range(0, k + 1) for s in (1, -1)],
           P4_periodicidad, "unicidad: evita soluciones espurias")
    _check(stats, "P5   a=b (mod c) => y_k(a)=y_k(b)",
           [(a, b, c, k) for c in range(2, 10) for a in range(2, 15)
            for b in range(2, 15) for k in range(0, 8)],
           P5_parametro, "y_k(1)=k da P3 como caso particular")
    _check(stats, "JR   (2a-1)^(k-1)<=y_k<=(2a)^(k-1)",
           [(a, k) for a in range(2, 8) for k in range(1, 12)],
           crecimiento_JR, "crecimiento exponencial: hipotesis de Julia Robinson")


def test_recuperacion_indice(stats):
    print(f"{Colors.HEADER}[3] Recuperacion del indice (P3 en accion){Colors.ENDC}")
    malos = [(a, k) for a in range(2, 8) for k in range(0, 12)
             if index_from_y(a, pell_y(a, k)) != k]
    espurios = [(a, v) for a in (3, 5)
                for v in range(1, 60)
                if index_from_y(a, v) is not None and pell_y(a, index_from_y(a, v)) != v]
    if malos or espurios:
        stats.fail(f"indice mal recuperado: {malos[:3]} / espurios {espurios[:3]}")
    else:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 72 indices recuperados exactamente; "
              f"ningun valor no-Pell acepta indice")


def test_marco_pareto(stats):
    print(f"{Colors.HEADER}[4] EL MARCO CORRECTO: frontera de Pareto, no un ranking{Colors.ENDC}")
    for nu, delta in PARETO_JONES_1982:
        marca = "  <- minimo grado" if nu == 58 else ("  <- minimo incognitas" if nu == 9 else "")
        print(f"    ({nu:2d} incognitas, grado {delta:>9s}){marca}")
    print(f"  {Colors.WARN}{NOTA_PARETO}{Colors.ENDC}")
    print(f"  {Colors.WARN}{DOMINIO_IMPORTA}{Colors.ENDC}")
    extremos = {nu for nu, _ in PARETO_JONES_1982}
    if 9 in extremos and 58 in extremos and len(PARETO_JONES_1982) >= 10:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} frontera declarada con su aviso de confianza "
              f"(solo los extremos estan confirmados por fuente)")
    else:
        stats.fail("frontera incompleta")


def main():
    print(f"{Colors.BOLD}=== ARSENAL DE PELL: LA MAQUINARIA REAL DE LOS RECORDS ==={Colors.ENDC}")
    stats = Stats()
    test_identidad_pell(stats)
    test_arsenal(stats)
    test_recuperacion_indice(stats)
    test_marco_pareto(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — arsenal de Pell verificado "
              f"(P1-P5 + crecimiento JR). Cimiento para la reduccion de incognitas.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
