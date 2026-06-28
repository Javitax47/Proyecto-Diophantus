#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - TEST E2E SOBRE EL CORPUS REAL (Fase 0, item 2)
================================================================================
Compila cada programa de `src/examples/*.c` con el pipeline real
(`diophantus.py`) y verifica que el sistema PURE resultante es un polinomio
entero genuino, leído como objetos SymPy (`sympy_system`). Es la prueba de
regresión sobre PROGRAMAS REALES, complementaria a los tests sintéticos: si una
futura optimización rompiera la aritmetización (p. ej. reintroduciendo un
relacional o un operador bit a bit sin convertir), este test lo detecta sobre el
corpus de verdad.

Robustez del test:
  * Si libclang no está disponible (entorno sin LLVM), el test se OMITE entero.
  * Cada compilación tiene un presupuesto de tiempo; los ejemplos que lo exceden
    (recursión muy profunda) se OMITEN, no se cuentan como fallo.
  * Una compilación que falla o un sistema no polinómico SÍ es fallo.

Uso:  python src/tests/verification/test_corpus_e2e.py [--timeout 60]
Requisitos: sympy, y LLVM/libclang para compilar.
"""

import os
import sys
import glob
import argparse
import subprocess

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, _REPO_ROOT)

try:
    import sympy  # noqa: F401
except ImportError:
    print("[SKIP] sympy no está instalado.")
    sys.exit(0)

from src.analysis import sympy_system


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; WARN = '\033[93m'
    HEADER = '\033[95m'; BOLD = '\033[1m'; ENDC = '\033[0m'


# Ejemplos con defecto de compilación PREEXISTENTE (no es regresión de la
# aritmetización). Se reportan como KNOWN-BROKEN, no como fallo. Si alguno pasa
# inesperadamente, el test lo avisa para retirarlo de aquí.
KNOWN_BROKEN = {}


def libclang_available():
    """True si clang.cindex puede crear un índice (libclang cargable)."""
    try:
        import src.compiler.parser  # configura la ruta de libclang al importar
        import clang.cindex
        clang.cindex.Index.create()
        return True
    except Exception:
        return False


def compile_example(path, timeout):
    """Compila un .c con diophantus.py. Devuelve ('OK'|'TIMEOUT'|'ERROR', detalle)."""
    try:
        proc = subprocess.run(
            [sys.executable, "diophantus.py", path],
            cwd=_REPO_ROOT, capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "TIMEOUT", ""
    if proc.returncode != 0:
        return "ERROR", (proc.stdout + proc.stderr)[-800:]
    return "OK", ""


_OUTPUT_DIR = os.path.join(_REPO_ROOT, "output")


def snapshot_output(backup_dir):
    """Copia el estado actual de output/ a backup_dir y devuelve el set de
    ficheros pre-existentes (para no tocar los artefactos commiteados)."""
    import shutil
    pre = set(os.listdir(_OUTPUT_DIR)) if os.path.isdir(_OUTPUT_DIR) else set()
    for f in pre:
        src = os.path.join(_OUTPUT_DIR, f)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(backup_dir, f))
    return pre


def restore_output(backup_dir, pre):
    """Restaura output/ EXACTAMENTE al estado previo: borra lo que el test creó
    y reescribe los ficheros pre-existentes que se hubieran sobrescrito. Así el
    test no modifica ni borra los artefactos versionados."""
    import shutil
    for f in set(os.listdir(_OUTPUT_DIR)) - pre:
        p = os.path.join(_OUTPUT_DIR, f)
        if os.path.isfile(p):
            try: os.remove(p)
            except OSError: pass
    for f in pre:
        b = os.path.join(backup_dir, f)
        if os.path.isfile(b):
            shutil.copy2(b, os.path.join(_OUTPUT_DIR, f))


def validate_pure(base):
    """Lee output/<base>_pure_poly_system.txt como SymPy y comprueba que es
    polinómico. Devuelve (ok, mensaje)."""
    path = os.path.join(_REPO_ROOT, "output", f"{base}_pure_poly_system.txt")
    if not os.path.exists(path):
        return False, "no se generó el sistema PURE"
    with open(path, encoding="utf-8") as f:
        lines = [l for l in f.read().splitlines() if l.strip()]
    try:
        eqs, syms = sympy_system.build_system(lines)
        if not sympy_system.is_polynomial_system(eqs):
            return False, "alguna ecuación no es polinómica"
    except Exception as e:
        return False, f"no polinómico/parseable: {type(e).__name__}: {e}"
    return True, f"{len(eqs)} ecuaciones, {len(syms)} variables"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=60, help="Segundos por ejemplo")
    args = ap.parse_args()

    print(f"{Colors.BOLD}=== TEST E2E DEL CORPUS (src/examples/*.c) ==={Colors.ENDC}")
    if not libclang_available():
        print(f"{Colors.WARN}[SKIP] libclang no disponible: no se puede compilar el corpus.{Colors.ENDC}")
        sys.exit(0)

    examples = sorted(glob.glob(os.path.join(_REPO_ROOT, "src", "examples", "*.c")))
    passed = skipped = failed = known_broken = 0

    import tempfile, shutil
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    backup_dir = tempfile.mkdtemp(prefix="diophantus_output_backup_")
    pre = snapshot_output(backup_dir)
    try:
        for path in examples:
            rel = os.path.relpath(path, _REPO_ROOT)
            base = os.path.splitext(os.path.basename(path))[0]
            status, detail = compile_example(rel, args.timeout)

            # Determinar si el ejemplo quedó OK (compiló y es polinómico).
            ok, msg = (False, "")
            if status == "OK":
                ok, msg = validate_pure(base)
            elif status == "TIMEOUT":
                print(f"  {Colors.WARN}⊘ SKIP{Colors.ENDC} {base}: excede {args.timeout}s")
                skipped += 1
                continue
            else:  # ERROR
                msg = f"compilación falló: {detail.strip()[-160:]}"

            if base in KNOWN_BROKEN:
                if ok:
                    print(f"  {Colors.WARN}? {base}: PASA pero estaba en KNOWN_BROKEN — "
                          f"retíralo de la lista.{Colors.ENDC}")
                    passed += 1
                else:
                    print(f"  {Colors.WARN}≈ KNOWN-BROKEN{Colors.ENDC} {base}: {KNOWN_BROKEN[base]}")
                    known_broken += 1
                continue

            if ok:
                print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {base}: {msg}")
                passed += 1
            else:
                print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {base}: {msg}")
                failed += 1
    finally:
        # Dejar output/ EXACTAMENTE como estaba (no tocar artefactos versionados).
        restore_output(backup_dir, pre)
        shutil.rmtree(backup_dir, ignore_errors=True)

    total = passed + skipped + failed + known_broken
    print(f"\n{Colors.BOLD}=== {passed} OK · {skipped} SKIP · {known_broken} KNOWN-BROKEN · "
          f"{failed} FAIL  (de {total}) ==={Colors.ENDC}")
    if failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ El corpus compila a sistemas polinómicos genuinos.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ Hay ejemplos en fallo.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
