#!/usr/bin/env python3
"""
================================================================================
   PROJECT DIOPHANTUS: FINAL SYSTEM AUDIT (V2.0)
================================================================================
Este script certifica la operatividad de todos los módulos del compilador.

VERIFICA:
1. [CORE] Compilación de C a Sistema Diofántico (Parser/Generator).
2. [MATH] Generación de Scripts de Análisis Simbólico (SymPy).
3. [VM]   Ejecución Correcta en la Máquina Virtual (Stack-Based).
4. [LOGIC] Validez Matemática de los 3 Pilares Clásicos.
5. [CHAOS] Validación de trayectorias dinámicas (Collatz).
6. [SINGULARITY] Integridad del pipeline de Transmutación Algebraica (Dickson).
================================================================================
"""

import subprocess
import sys
import os
import random
import time
from pathlib import Path

# --- CONFIGURACIÓN VISUAL ---
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log_header(msg): print(f"\n{Colors.HEADER}{Colors.BOLD}=== {msg} ==={Colors.ENDC}")
def log_pass(msg):   print(f" {Colors.OKGREEN}✓ PASS:{Colors.ENDC} {msg}")
def log_fail(msg):   print(f" {Colors.FAIL}✗ FAIL:{Colors.ENDC} {msg}")
def log_info(msg):   print(f"   ℹ {msg}")

# --- UTILS: PROVER ECPP ---
class ECPP_Prover:
    @staticmethod
    def inverse_mod(a, n): return pow(a, -1, n)

    @staticmethod
    def point_add(p1, p2, a, mod):
        if p1 is None: return p2
        if p2 is None: return p1
        x1, y1 = p1; x2, y2 = p2
        if x1 == x2 and y1 != y2: return None
        if x1 == x2:
            if y1 == 0: return None
            try: m = (3 * x1 * x1 + a) * ECPP_Prover.inverse_mod(2 * y1, mod)
            except: return None
        else:
            try: m = (y2 - y1) * ECPP_Prover.inverse_mod(x2 - x1, mod)
            except: return None
        x3 = (m * m - x1 - x2) % mod
        y3 = (m * (x1 - x3) - y1) % mod
        return (x3, y3)

    @staticmethod
    def point_mul(p, k, a, mod):
        res = None
        for bit in bin(k)[2:]:
            res = ECPP_Prover.point_add(res, res, a, mod)
            if bit == '1': res = ECPP_Prover.point_add(res, p, a, mod)
        return res

    @staticmethod
    def get_cert(n):
        for _ in range(2000):
            a = random.randint(0, n-1); x = random.randint(0, n-1); y = random.randint(0, n-1)
            b = (y*y - x*x*x - a*x) % n
            if (4*a**3 + 27*b**2) % n == 0: continue
            P = (x, y)
            for m in range(3, 30):
                try:
                    if ECPP_Prover.point_mul(P, m, a, n) is None:
                        return a, b, x, y, m
                except: pass
        return None

# --- CLASE DE AUDITORÍA ---

class SystemAudit:
    def __init__(self):
        self.root = Path(__file__).resolve().parent
        self.compiler = self.root / "diophantus.py"
        self.vm = self.root / "src" / "runtime" / "vm.py"

        # Módulos de análisis algebraico
        self.math_kernel = self.root / "src" / "analysis" / "math_kernels.py"
        self.linker = self.root / "src" / "analysis" / "equation_linker.py"
        self.optimizer = self.root / "src" / "analysis" / "deep_optimizer.py"

        self.output_dir = self.root / "output"
        self.artifacts_dir = self.output_dir / "artifacts"
        self.errors = 0

    def check_integrity(self):
        log_header("FASE 1: INTEGRIDAD DEL ENTORNO")

        files = [
            self.compiler,
            self.vm,
            self.optimizer,
            self.math_kernel,
            self.linker,
            self.root / "src" / "compiler" / "parser.py"
        ]

        all_ok = True
        for f in files:
            if f.exists():
                log_pass(f"Encontrado: {f.name}")
            else:
                log_fail(f"Falta archivo crítico: {f}")
                all_ok = False

        if not all_ok:
            print("\n[FATAL] El entorno está incompleto.")
            sys.exit(1)

        # Crear directorios si no existen
        self.output_dir.mkdir(exist_ok=True)
        self.artifacts_dir.mkdir(exist_ok=True)

    def locate_example(self, name):
        for p in self.root.rglob(name):
            if "output" not in p.parts: return p
        return None

    def run_pipeline(self, name, filename, call_gen, validator_func):
        log_header(f"TEST: {name}")

        # 1. Localizar
        c_path = self.locate_example(filename)
        if not c_path:
            log_fail(f"Archivo C no encontrado: {filename}")
            self.errors += 1
            return

        # 2. Compilar
        log_info(f"Compilando {filename}...")
        try:
            cmd = [sys.executable, str(self.compiler), str(c_path.relative_to(self.root))]
            proc = subprocess.run(cmd, cwd=self.root, capture_output=True, text=True)
            if proc.returncode != 0:
                log_fail(f"Error de compilación:\n{proc.stderr[:200]}")
                self.errors += 1
                return
            else:
                log_pass("Compilación exitosa.")
        except Exception as e:
            log_fail(f"Excepción compilador: {e}")
            self.errors += 1
            return

        # 3. Verificar Artefactos
        base_name = c_path.stem
        sympy_file = self.output_dir / f"{base_name}_analysis_sympy.py"
        if sympy_file.exists():
            log_pass(f"Script de análisis algebraico generado.")
        else:
            log_fail(f"Fallo en generación de análisis simbólico.")
            self.errors += 1

        # 4. Generar Input Dinámico
        call_expr = call_gen() if callable(call_gen) else call_gen
        if not call_expr:
            log_fail("Fallo en generación de input dinámico.")
            self.errors += 1
            return
        # log_info(f"Input: {call_expr}")

        # 5. Ejecutar VM
        interpreter_file = self.output_dir / f"{base_name}_interpreter_input.txt"
        cmd_vm = [sys.executable, str(self.vm), str(interpreter_file), call_expr]

        try:
            start = time.time()
            proc_vm = subprocess.run(cmd_vm, cwd=self.root, capture_output=True, text=True, timeout=60)
            dt = time.time() - start

            val = None
            for line in proc_vm.stdout.split('\n'):
                if "Result:" in line:
                    try: val = int(line.split("Result:")[1].strip())
                    except: pass

            if val is not None:
                if validator_func(val):
                    log_pass(f"Ejecución VM Correcta ({val}) en {dt:.3f}s")
                else:
                    log_fail(f"Valor incorrecto: Obtuvo {val}")
                    self.errors += 1
            else:
                log_fail(f"VM Crash: {proc_vm.stderr[:100]}")
                self.errors += 1

        except subprocess.TimeoutExpired:
            log_fail("VM Timeout (>60s)")
            self.errors += 1

    def test_singularity_pipeline(self):
        log_header("TEST: PIPELINE DE SINGULARIDAD (Dickson/Linker)")

        # 1. Crear un dummy formula para testear math_kernels.py
        dummy_file = self.artifacts_dir / "audit_dummy_formula.py"
        with open(dummy_file, "w") as f:
            f.write("def G_formula(n, x): return n")

        # 2. Testear Transmutación (Fermat Kernel)
        log_info("Probando Math Kernel (Fermat)...")
        cmd_kernel = [
            sys.executable, str(self.math_kernel),
            str(dummy_file), "--type", "fermat", "--var", "n"
        ]
        res = subprocess.run(cmd_kernel, cwd=self.root, capture_output=True, text=True)

        fermat_out = self.artifacts_dir / "audit_dummy_fermat_closed.py"
        if res.returncode == 0 and fermat_out.exists():
            log_pass("Math Kernel: Generación Fermat OK")
        else:
            log_fail(f"Math Kernel Fermat Falló: {res.stderr}")
            self.errors += 1
            return

        # 3. Testear Transmutación (Lucas Kernel)
        cmd_kernel[4] = "lucas"
        res = subprocess.run(cmd_kernel, cwd=self.root, capture_output=True, text=True)
        lucas_out = self.artifacts_dir / "audit_dummy_lucas_closed.py"
        if res.returncode == 0 and lucas_out.exists():
            log_pass("Math Kernel: Generación Lucas OK")
        else:
            log_fail("Math Kernel Lucas Falló")
            self.errors += 1
            return

        # 4. Testear Linker (Baillie-PSW)
        log_info("Probando Equation Linker...")
        linker_out = self.artifacts_dir / "audit_linked_final.py"
        cmd_linker = [
            sys.executable, str(self.linker),
            "--inputs", str(fermat_out), str(lucas_out),
            "--output", "audit_linked_final.py",
            "--var", "n"
        ]
        res = subprocess.run(cmd_linker, cwd=self.root, capture_output=True, text=True)

        if res.returncode == 0 and linker_out.exists():
            log_pass("Equation Linker: Fusión Exitosa")
        else:
            log_fail(f"Linker Falló: {res.stderr}")
            self.errors += 1

        # Limpieza
        try:
            os.remove(dummy_file)
            os.remove(fermat_out)
            os.remove(lucas_out)
            os.remove(linker_out)
        except: pass

    def run_all(self):
        self.check_integrity()

        # --- TEST 1: RECURSIÓN ---
        self.run_pipeline(
            "Recursión Básica (Factorial)",
            "recursion_test.c",
            lambda: "factorial(6)",
            lambda x: x == 720
        )

        # --- TEST 2: MILLER-RABIN ---
        self.run_pipeline(
            "Miller-Rabin (Logarítmico)",
            "primes_innovative.c",
            lambda: "find_nth_prime(10, 2, 0)",
            lambda x: x == 29
        )

        # --- TEST 3: COLLATZ ---
        self.run_pipeline(
            "Dinámica del Caos (Collatz)",
            "collatz_cycle.c",
            lambda: "detect_cycle_recursive(5, 5, 0)", # 5 no cicla -> 0
            lambda x: x == 0
        )

        # --- TEST 4: ECPP ---
        def ecpp_setup():
            cert = ECPP_Prover.get_cert(19)
            if cert: return f"verify_ecpp_energy(19, {cert[0]}, {cert[1]}, {cert[2]}, {cert[3]}, {cert[4]})"
            return None

        self.run_pipeline(
            "Geometría Algebraica (ECPP)",
            "primes_ecpp_final.c",
            ecpp_setup,
            lambda x: x == 0
        )

        # --- TEST 5: SINGULARIDAD ---
        self.test_singularity_pipeline()

        # --- CONCLUSIÓN ---
        print("\n" + "="*60)
        if self.errors == 0:
            print(f"{Colors.OKGREEN}>>> SISTEMA 100% OPERATIVO. LISTO PARA PRODUCCIÓN. <<<{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}>>> FALLO DEL SISTEMA. {self.errors} ERRORES DETECTADOS. <<<{Colors.ENDC}")
        print("="*60)

if __name__ == "__main__":
    audit = SystemAudit()
    audit.run_all()