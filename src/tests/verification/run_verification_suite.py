#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - SUITE DE VERIFICACIÓN (runner maestro)
================================================================================
Ejecuta de un tirón todos los tests de verificación basados en Z3/SymPy/VM y
reporta un resumen con código de salida agregado. Resuelve el hueco señalado en
§3.2 del informe ("sin test de integración E2E"): un único comando que valida
la cadena soundness -> SymPy -> VM.

Cada test se ejecuta como subproceso; un test que haga [SKIP] (p. ej. por falta
de z3) cuenta como omitido, no como fallo.

Uso:  python src/tests/verification/run_verification_suite.py
Código de salida: 0 si todos pasan/omiten, 1 si alguno falla.
"""

import os
import sys
import subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))

# (archivo, descripción)
TESTS = [
    ("test_pure_soundness.py",        "Soundness PURE por operador (Z3: solución<=>traza)"),
    ("test_property_based.py",        "Property-based: expresiones compuestas aleatorias"),
    ("test_sympy_system.py",          "Representación SymPy (polinomicidad + equivalencia)"),
    ("test_deep_optimizer_codegen.py","Generador de energía del deep_optimizer (sustitución SymPy)"),
    ("test_vm_ground_truth.py",       "VM contra ground-truth (algoritmos recursivos)"),
    ("test_tail_merge.py",            "Fusión de tail-calls (diferencial: preserva semántica)"),
    ("test_trace_packer.py",          "Trace packer / función beta (Fase 2: colapso de la traza)"),
    ("test_beta_backend.py",          "Beta backend (Fase 2: transición compilada -> testigos beta)"),
    ("test_parser_operators.py",      "Parseo de operadores anidados (regresión de precedencia)"),
    ("test_linear_collapse.py",       "Colapso lineal (Fase 3: ∀i<T -> una ecuación)"),
    ("test_digit_dominance.py",       "Dominancia de dígitos / Kummer-Lucas (Fase 3: colapso general)"),
    ("test_collatz_collapse.py",      "Colapso de Collatz (Fase 3: transición no afín polinómica)"),
    ("test_beta_general.py",          "Generalidad del beta backend (mismo motor, varios programas)"),
    ("test_structural_collapse.py",   "Colapso estructural genérico (detecta afín desde la transición)"),
    ("test_collatz_closed.py",        "Sistema cerrado de Collatz (Fase 3: cierre del caso no afín)"),
    ("test_z3_closed.py",             "Sistema cerrado emitido a Z3 (solver prueba solución⟺traza)"),
    ("test_discovery.py",             "Motor de descubrimiento (Fase 4: identidades no inyectadas)"),
    ("test_conserved.py",             "Cantidades conservadas (Fase 4: primeras integrales, lineal/no lineal)"),
    ("test_collatz_cycles.py",        "No-existencia certificada de ciclos cortos de Collatz (Z3, §6.3)"),
    ("test_primality.py",             "Primalidad CORRECTA: Baillie-PSW (reemplaza la versión errónea)"),
    ("test_primality_audit.py",     "Auditoría de artefactos de primalidad antiguos (defectos documentados)"),
    ("test_lucas_discovery.py",      "Cruce motor<->Lucas (Fase 4: redescubre la base de Baillie-PSW)"),
    ("test_capability.py",            "Umbral de capacidad del motor (integrable encuentra / caótico nada)"),
    ("test_certificates.py",          "Certificados algebraicos portables (re-verificables sin solver, MONETIZACION)"),
    ("test_conjectures.py",           "Resultados parciales certificados de problemas abiertos (banda + GAP)"),
    ("test_lyapunov.py",              "Estructura por desigualdad: funciones de Lyapunov (donde no hay invariante)"),
    ("test_encodings.py",             "Estrategias de codificación (forma cerrada O(log T) vs β-collapse vs unroll)"),
    ("test_sos.py",                   "Certificados de desigualdad: suma de cuadrados / Positivstellensatz"),
    ("test_discovery_campaign.py",    "Campaña de descubrimiento: barrido de familias paramétricas (certificado)"),
    ("test_product.py",               "Producto monetizable: verifier + recheck independiente + metering + atlas"),
    ("test_qubo.py",                  "Exportador a QUBO (sistema diofántico -> optimización binaria / annealing)"),
    ("test_factorize.py",             "Factorización quantum-ready vía annealing + certificado re-verificable"),
    ("test_oeis_candidates.py",       "Candidatos a secuencia OEIS (Markoff-Hurwitz 4D, reproducible + certificado)"),
    ("test_conjecturer.py",           "Conjeturador estilo Ramanujan (PCF -> forma cerrada en constantes, PSLQ)"),
    ("test_conjecture_filter.py",     "Filtro de novedad de conjeturas (clásicas + prior por constante + convergencia)"),
    ("test_combinatorial_certs.py",   "Certificados combinatorios (coloreado vía Nullstellensatz, mismo recheck trustless)"),
    ("test_sat_certs.py",             "Certificados SAT/CNF (insatisfacibilidad booleana, mismo recheck trustless)"),
    ("test_interpreter.py",           "Intérprete de ecuaciones (formato prefijo actual; recursivo + transición, sin eval)"),
    ("test_verifier_engine.py",       "Verificador formal BMC (alcanzabilidad sat/unsat sobre la arithmetización)"),
]


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; WARN = '\033[93m'
    HEADER = '\033[95m'; BOLD = '\033[1m'; ENDC = '\033[0m'


def run_one(filename):
    """Devuelve ('PASS'|'FAIL'|'SKIP', salida_completa)."""
    path = os.path.join(_HERE, filename)
    proc = subprocess.run([sys.executable, path], capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    if "[SKIP]" in out:
        return "SKIP", out
    return ("PASS" if proc.returncode == 0 else "FAIL"), out


def main():
    print(f"{Colors.BOLD}{Colors.HEADER}"
          f"==================================================\n"
          f"   SUITE DE VERIFICACIÓN DIOPHANTUS\n"
          f"=================================================={Colors.ENDC}")
    results = []
    for filename, desc in TESTS:
        print(f"\n{Colors.BOLD}▶ {desc}{Colors.ENDC}  ({filename})")
        status, out = run_one(filename)
        # Mostrar la última línea significativa de cada test
        last = [l for l in out.splitlines() if l.strip()]
        if last:
            print("   " + last[-1])
        tag = {"PASS": f"{Colors.OKGREEN}PASS{Colors.ENDC}",
               "FAIL": f"{Colors.FAIL}FAIL{Colors.ENDC}",
               "SKIP": f"{Colors.WARN}SKIP{Colors.ENDC}"}[status]
        print(f"   -> {tag}")
        if status == "FAIL":
            # Volcar la salida completa del test que falla para depurar.
            print(f"{Colors.FAIL}--- salida de {filename} ---{Colors.ENDC}")
            print(out.rstrip())
            print(f"{Colors.FAIL}--- fin ---{Colors.ENDC}")
        results.append((filename, status))

    passed = sum(1 for _, s in results if s == "PASS")
    skipped = sum(1 for _, s in results if s == "SKIP")
    failed = sum(1 for _, s in results if s == "FAIL")

    print(f"\n{Colors.BOLD}=== RESUMEN: {passed} PASS · {skipped} SKIP · {failed} FAIL ==={Colors.ENDC}")
    if failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ Verificación superada.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ Hay tests en fallo.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
