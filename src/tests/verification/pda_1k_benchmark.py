# -*- coding: utf-8 -*-
import sys
import os
import time
import subprocess
import multiprocessing
import queue

# --- CONFIGURACIÓN ---
sys.set_int_max_str_digits(1000000)
sys.setrecursionlimit(200000)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, 'output/artifacts')

sys.path.append(PROJECT_ROOT)

class Colors:
    HEADER = '\033[95m'; BLUE = '\033[94m'; GREEN = '\033[92m'
    FAIL = '\033[91m'; END = '\033[0m'; BOLD = '\033[1m'; WARN = '\033[93m'

def get_file_size_kb(path):
    if os.path.exists(path): return os.path.getsize(path) / 1024
    return 0

def run_command(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True, cwd=PROJECT_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError: return False

# --- WORKER VM ---
def worker_vm(root_path, raw_file, func_name, args, out_queue):
    try:
        import sys
        if root_path not in sys.path: sys.path.append(root_path)
        from src.runtime.vm import VM, Parser

        vm = VM(); parser = Parser()
        with open(raw_file, 'r', encoding='utf-8') as f:
            for line in f:
                import re
                m = re.match(r'P_(\w+)\((.*?)\)\s*=\s*(.*)', line.strip())
                if m:
                    p_list = [x.strip() for x in m.group(2).split(',') if x.strip()]
                    vm.load_function(m.group(1), p_list, parser.parse(m.group(3)))

        t0 = time.perf_counter()
        res = vm.run(func_name, args)
        dt = (time.perf_counter() - t0) * 1000
        out_queue.put((res, dt))
    except Exception as e:
        out_queue.put((f"ERR: {e}", 0))

def run_vm_safe(raw_file, func_name, args, timeout=10.0):
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=worker_vm, args=(PROJECT_ROOT, raw_file, func_name, args, q))
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate(); p.join()
        return "TIMEOUT", timeout * 1000
    if not q.empty(): return q.get()
    return "CRASH", 0

# --- ANÁLISIS FORENSE ---
def main():
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== INFORME FORENSE: PROTOCOLO PDA-1k (1000 CICLOS) ==={Colors.END}")

    # 1. Compilación
    print(f"{Colors.BLUE}[1] Compilando 'avalanche.c'...{Colors.END}", end=" ")
    t0 = time.time()
    if run_command("python diophantus.py src/examples/avalanche.c"):
        print(f"{Colors.GREEN}OK ({time.time()-t0:.2f}s){Colors.END}")
    else:
        print(f"{Colors.FAIL}ERROR{Colors.END}"); return

    raw_file = os.path.join(OUTPUT_DIR, "avalanche_interpreter_input.txt")

    # 2. Métricas de Compresión
    size_kb = get_file_size_kb(raw_file)

    # Detección de Recursión Simbólica (H1)
    is_symbolic = False
    try:
        with open(raw_file, 'r') as f:
            content = f.read()
            if "call(avalanche_cycle" in content: is_symbolic = True
            # Buscar el caso base real para confirmar
            if "If(>=(step, 1000)" in content:
                base_case = "DETECTADO (step >= 1000)"
            else:
                base_case = "NO DETECTADO (Peligro)"
    except: base_case = "Error Lectura"

    print(f"\n{Colors.BOLD}>>> ANÁLISIS DE COMPRESIÓN ESPACIAL (Hipótesis H1){Colors.END}")
    print(f"    Tamaño del Archivo:    {Colors.BLUE}{size_kb:.2f} KB{Colors.END}")
    print(f"    Caso Base:             {base_case}")

    if is_symbolic and size_kb < 50:
        print(f"    Estructura:            {Colors.GREEN}RECURSIVA (COMPRIMIDA){Colors.END}")
        print(f"    Veredicto:             {Colors.GREEN}H1 CONFIRMADA{Colors.END} (El compilador capturó la lógica sin desenrollar).")
    else:
        print(f"    Estructura:            {Colors.FAIL}DESENROLLADA (LINEAL){Colors.END}")
        print(f"    Veredicto:             {Colors.WARN}H0 (Fallo de compresión){Colors.END}")

    # 3. Ejecución
    print(f"\n{Colors.BOLD}>>> PRUEBA DE SOLIDEZ (Ejecución VM){Colors.END}")
    print(f"    Ejecutando 1000 ciclos de caos aritmético...")

    # Seed 123456789
    res, dt = run_vm_safe(raw_file, "avalanche_cycle", [123456789, 1, 0], timeout=600.0)

    if str(res).isdigit():
        val_str = str(res)
        print(f"    Estado:                {Colors.GREEN}ÉXITO{Colors.END}")
        print(f"    Tiempo:                {Colors.BLUE}{dt:.2f} ms{Colors.END}")
        print(f"    Resultado (Hash):      {val_str[:15]}... ({len(val_str)} dígitos)")
        print(f"    Integridad:            El sistema resolvió la trayectoria completa.")
    else:
        print(f"    Estado:                {Colors.FAIL}{res}{Colors.END}")

if __name__ == "__main__":
    main()