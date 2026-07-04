#!/usr/bin/env python3
"""
=============================================================================
   DIOPHANTUS COMPILER - SUITE DE PRUEBAS MAESTRA (FINAL STABLE)
=============================================================================
Verifica: Compilación, VM y Lógica Matemática.
"""

import subprocess
import os
import sys
import random
from pathlib import Path

# Colores
class Colors:
    HEADER = '\033[95m'; OKGREEN = '\033[92m'; FAIL = '\033[91m'; ENDC = '\033[0m'; BOLD = '\033[1m'

# --- GENERADOR ECPP ROBUSTO ---
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
        """Genera certificado válido garantizado."""
        for _ in range(5000):
            a = random.randint(0, n-1); x = random.randint(0, n-1); y = random.randint(0, n-1)
            b = (y*y - x*x*x - a*x) % n
            if (4*a**3 + 27*b**2) % n == 0: continue # Singular
            P = (x, y)
            # Buscamos m tal que m*P = Infinito
            for m in range(3, 30):
                try:
                    if ECPP_Prover.point_mul(P, m, a, n) is None:
                        return a, b, x, y, m
                except: pass
        return None

# --- MOTOR DE TEST ---

class CompilerTestSuite:
    def __init__(self):
        self.root = Path(__file__).resolve().parents[3]
        self.compiler = self.root / "diophantus.py"
        self.vm = self.root / "src" / "runtime" / "vm.py"
        self.output_dir = self.root / "output"

    def run_test(self, filename, test_name, call_gen, expected):
        print(f"\nTesting: {Colors.BOLD}{test_name}{Colors.ENDC} ({filename})")

        # Localizar archivo
        c_path = None
        for p in self.root.rglob(filename):
            if "output" not in p.parts: c_path = p; break
        if not c_path: print(f"  {Colors.FAIL}[SKIP] Archivo no encontrado{Colors.ENDC}"); return

        # Compilar
        print("  [1] Compilando...", end=" ", flush=True)
        try:
            subprocess.run([sys.executable, str(self.compiler), str(c_path.relative_to(self.root))], cwd=self.root, check=True, capture_output=True)
            print(f"{Colors.OKGREEN}OK{Colors.ENDC}")
        except: print(f"{Colors.FAIL}FAIL{Colors.ENDC}"); return

        # Generar llamada
        call_expr = call_gen() if callable(call_gen) else call_gen
        if not call_expr and expected is not None:
             print(f"  [2] {Colors.FAIL}Prover Failed{Colors.ENDC}"); return
        elif not call_expr:
             print("  [2] Skip VM"); return

        # Ejecutar VM
        infile = self.output_dir / f"{c_path.stem}_interpreter_input.txt"
        print(f"  [2] VM: {call_expr}...", end=" ", flush=True)

        try:
            p = subprocess.run([sys.executable, str(self.vm), str(infile), call_expr], cwd=self.root, capture_output=True, text=True, timeout=120)
            val = None
            for l in p.stdout.split('\n'):
                if "Result:" in l: val = int(l.split(":")[1].strip())

            if val == expected: print(f"{Colors.OKGREEN}[PASS] ({val}){Colors.ENDC}")
            else: print(f"{Colors.FAIL}[FAIL] ({val} != {expected}){Colors.ENDC}")

        except subprocess.TimeoutExpired: print(f"{Colors.FAIL}[TIMEOUT]{Colors.ENDC}")
        except Exception as e: print(f"{Colors.FAIL}[ERR] {e}{Colors.ENDC}")

def main():
    s = CompilerTestSuite()

    # Tests
    s.run_test("simple_counter.c", "Contador", None, None)
    s.run_test("recursion_test.c", "Factorial", "factorial(5)", 120)
    s.run_test("primes_innovative.c", "Miller-Rabin", "find_nth_prime(10, 2, 0)", 29)
    s.run_test("primes_solovay_64.c", "Solovay (17)", "solovay_64_bit(17)", 0)
    s.run_test("primes_solovay_64.c", "Solovay (15)", "solovay_64_bit(15)", 6)

    def ecpp_case():
        c = ECPP_Prover.get_cert(13) # Usamos 13 para variar
        if c: return f"verify_ecpp_energy(13, {c[0]}, {c[1]}, {c[2]}, {c[3]}, {c[4]})"
        return None

    s.run_test("primes_ecpp_final.c", "ECPP (n=13)", ecpp_case, 0)

if __name__ == "__main__": main()