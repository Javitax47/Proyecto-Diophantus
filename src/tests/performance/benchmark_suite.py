#!/usr/bin/env python3
"""
=============================================================================
   DIOPHANTUS COMPILER - PERFORMANCE BENCHMARK SUITE (FINAL STABLE)
=============================================================================
"""
import subprocess
import os
import sys
import time
import random
from pathlib import Path

# --- UTILIDADES ECPP (PROVER ROBUSTO) ---
class ECPP_Gen:
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
            try: m = (3 * x1 * x1 + a) * ECPP_Gen.inverse_mod(2 * y1, mod)
            except: return None
        else:
            try: m = (y2 - y1) * ECPP_Gen.inverse_mod(x2 - x1, mod)
            except: return None
        x3 = (m * m - x1 - x2) % mod
        y3 = (m * (x1 - x3) - y1) % mod
        return (x3, y3)

    @staticmethod
    def point_mul(p, k, a, mod):
        res = None
        for bit in bin(k)[2:]:
            res = ECPP_Gen.point_add(res, res, a, mod)
            if bit == '1': res = ECPP_Gen.point_add(res, p, a, mod)
        return res

    @staticmethod
    def get_cert(n):
        # Misma lógica robusta que el test_suite
        for _ in range(5000):
            a = random.randint(0, n-1); x = random.randint(0, n-1); y = random.randint(0, n-1)
            b = (y*y - x*x*x - a*x) % n
            if (4*a**3 + 27*b**2) % n == 0: continue
            P = (x, y)
            for m in range(3, 40):
                try:
                    if ECPP_Gen.point_mul(P, m, a, n) is None:
                        return a, b, x, y, m
                except: pass
        return None

# --- MOTOR ---
class Colors:
    HEADER = '\033[95m'; OKCYAN = '\033[96m'; OKGREEN = '\033[92m';
    FAIL = '\033[91m'; ENDC = '\033[0m'; BOLD = '\033[1m'

class BenchmarkSuite:
    def __init__(self):
        self.root_dir = Path(__file__).resolve().parents[3]
        self.compiler = self.root_dir / "diophantus.py"
        self.vm = self.root_dir / "src" / "runtime" / "vm.py"
        self.output_dir = self.root_dir / "output"

    def _locate_c(self, name):
        for p in self.root_dir.rglob(name):
            if "output" not in p.parts: return p
        return None

    def get_bytecode_size(self, filename):
        path = self.output_dir / f"{Path(filename).stem}_interpreter_input.txt"
        if not path.exists(): return 0
        with open(path, 'rb') as f: return len(f.readlines())

    def run_benchmark(self, name, c_file, call_expr_gen, label):
        print(f"{Colors.BOLD}Running: {name} [{label}]{Colors.ENDC}")
        c_path = self._locate_c(c_file)
        if not c_path: print("  [SKIP] File not found"); return

        call_expr = call_expr_gen() if callable(call_expr_gen) else call_expr_gen
        if not call_expr: print(f"  {Colors.FAIL}[SKIP] Prover failed{Colors.ENDC}"); return

        # 1. Compilación
        t0 = time.time()
        try: rel_path = c_path.relative_to(self.root_dir)
        except: rel_path = c_path
        subprocess.run([sys.executable, str(self.compiler), str(rel_path)], cwd=self.root_dir, capture_output=True)
        time_c = time.time() - t0
        lines = self.get_bytecode_size(c_file)

        # 2. Ejecución VM
        t0 = time.time()
        infile = self.output_dir / f"{c_path.stem}_interpreter_input.txt"

        try:
            proc = subprocess.run([sys.executable, str(self.vm), str(infile), call_expr], cwd=self.root_dir, capture_output=True, text=True, timeout=300)
            time_v = time.time() - t0
            res = "N/A"
            for l in proc.stdout.split('\n'):
                if "Result:" in l: res = l.split(":")[1].strip()

            if res == "0": res_fmt = f"{Colors.OKGREEN}0 (Éxito){Colors.ENDC}"
            elif res == "N/A": res_fmt = f"{Colors.FAIL}ERROR{Colors.ENDC}"
            else:
                if "find_nth" in call_expr: res_fmt = f"{Colors.OKGREEN}{res} (Primo){Colors.ENDC}"
                elif "factorial" in call_expr: res_fmt = f"{Colors.OKGREEN}{res}{Colors.ENDC}"
                else: res_fmt = f"{Colors.FAIL}{res} (Fallo){Colors.ENDC}"

        except subprocess.TimeoutExpired: time_v = 300.0; res_fmt = f"{Colors.FAIL}TIMEOUT{Colors.ENDC}"

        print(f"  Compilación: {time_c:.2f}s | Tamaño: {lines:<5} ops")
        print(f"  Ejecución:   {Colors.OKCYAN}{time_v:.4f}s{Colors.ENDC} -> {res_fmt}")
        print("-" * 60)

def main():
    bench = BenchmarkSuite()
    print(f"\n{Colors.HEADER}=== DIOPHANTUS PERFORMANCE BENCHMARK ==={Colors.ENDC}\n")

    bench.run_benchmark("Factorial", "recursion_test.c", "factorial(10)", "Base Lineal")
    bench.run_benchmark("Miller-Rabin", "primes_innovative.c", "find_nth_prime(10, 2, 0)", "Primo 29")
    bench.run_benchmark("Solovay", "primes_solovay_64.c", "solovay_64_bit(17)", "17 (Primo)")

    def ecpp_setup():
        n = 1013 # Primo pequeño para test rápido
        c = ECPP_Gen.get_cert(n)
        if c: return f"verify_ecpp_energy({n}, {c[0]}, {c[1]}, {c[2]}, {c[3]}, {c[4]})"
        return None

    bench.run_benchmark("ECPP", "primes_ecpp_final.c", ecpp_setup, "n=1013")

if __name__ == "__main__": main()