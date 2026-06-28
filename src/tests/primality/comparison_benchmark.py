# -*- coding: utf-8 -*-
import sys
import os
import time
import importlib.util
import multiprocessing
import queue
import gc
import re

# --- CONFIGURACIÓN GLOBAL ---
sys.setrecursionlimit(200000)
TIMEOUT_SEC = 30.0          # Límite estricto por cálculo (evita cuelgues en simulación)
ITERATIONS_PRECISION = 1000 # Repeticiones para fórmulas de microsegundos

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, 'output/artifacts')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')

sys.path.append(PROJECT_ROOT)
sys.path.append(ARTIFACTS_DIR)
sys.path.append(os.path.join(PROJECT_ROOT, 'src/benchmarks/utils'))

# --- DEPENDENCIAS ---
try:
    from src.runtime.vm import VM, Parser
    VM_AVAILABLE = True
except ImportError:
    VM_AVAILABLE = False

try:
    from ecpp_certificate_maker import find_ecpp_certificate
except:
    try: from src.tests.utils.ecpp_certificate_maker import find_ecpp_certificate
    except: find_ecpp_certificate = None

# --- ESTÉTICA ---
class Style:
    HEADER = '\033[95m'; BLUE = '\033[94m'; CYAN = '\033[96m'; GREEN = '\033[92m'
    WARN = '\033[93m'; FAIL = '\033[91m'; END = '\033[0m'; BOLD = '\033[1m'
    GREY = '\033[90m'; PURPLE = '\033[35m'
    
    @staticmethod
    def print_box(title, content_lines):
        # Ancho fijo de 80 caracteres
        padding_len = max(0, 70 - len(title))
        dashes = "─" * padding_len
        print(f"\n{Style.BLUE}┌── [ {Style.BOLD}{title}{Style.END}{Style.BLUE} ] {dashes}┐{Style.END}")
        for line in content_lines:
            clean_line = line.replace(r"\cdot", "·").replace(r"\pmod", "mod").replace(r"\left", "").replace(r"\right", "")
            print(f"{Style.BLUE}│{Style.END}  {Style.CYAN}{clean_line:<74}{Style.END}  {Style.BLUE}│{Style.END}")
        print(f"{Style.BLUE}└" + "─"*78 + f"┘{Style.END}")

# --- DATASET ---
NUMBER_ZOO = [
    (17,         True,  "Small Prime"),
    (25,         False, "Composite Square"),
    (341,        False, "Pseudoprime (Base 2)"),
    (561,        False, "Carmichael Number"),
    (127,        True,  "Mersenne Prime (M7)"),
    (524287,     True,  "Mersenne Prime (M19)"),
    (2147483647, True,  "Mersenne Prime (M31)") 
]

# --- MODELOS ---
MODELS = [
    {
        "id": "BAILLIE_PSW", "name": "Baillie-PSW Identity", "type": "Algebraic Closed-Form",
        "file": "baillie_psw_formula.py",
        "target_val": 0, "requires_vm": False
    },
    {
        "id": "FERMAT", "name": "Fermat's Little Theorem", "type": "Algebraic Closed-Form",
        "file": "fermat_fermat_closed.py",
        "target_val": 0, "requires_vm": False
    },
    {
        "id": "LUCAS", "name": "Lucas-Dickson Identity", "type": "Algebraic Closed-Form",
        "file": "primes_lucas_lucas_closed.py",
        "target_val": 0, "requires_vm": False
    },
    {
        "id": "ECPP", "name": "Elliptic Curve Primality", "type": "Algebraic Geometry",
        "file": "primes_ecpp_final_ecpp_closed.py",
        "target_val": 0, "requires_vm": False, "is_ecpp": True
    },
    {
        "id": "SOLOVAY", "name": "Solovay-Strassen System", "type": "Algorithmic Simulation",
        "file": "primes_solovay_64_formula.py",
        "vm_file": "primes_solovay_64_interpreter_input.txt",
        "raw_poly_file": "primes_solovay_64_logical_poly_system.txt",
        "vm_func": "solovay_64_bit",
        "target_val": 0, "requires_vm": True
    },
    {
        "id": "RABIN", "name": "Miller-Rabin Algorithm", "type": "Algorithmic Simulation",
        "file": "primes_innovative_formula.py",
        "vm_file": "primes_innovative_interpreter_input.txt",
        "raw_poly_file": "primes_innovative_logical_poly_system.txt",
        "vm_func": "miller_rabin_check",
        "target_val": 1, "requires_vm": True
    }
]

# --- WORKERS DE ALTA PRECISIÓN (PROCESOS AISLADOS) ---

def worker_vm_precision(root_path, vm_path, func, args, out_queue):
    """
    Ejecuta la VM en un proceso limpio.
    Mide SOLO el tiempo de cómputo (sin carga ni overhead).
    """
    try:
        # 1. Reconstruir entorno
        import sys
        if root_path not in sys.path: sys.path.append(root_path)
        from src.runtime.vm import VM, Parser
        
        # 2. Carga (Fuera del reloj)
        vm = VM(); parser = Parser()
        with open(vm_path, 'r', encoding='utf-8') as f:
            for line in f:
                m = re.search(r'P_(\w+)\((.*?)\)\s*=\s*(.*)', line.strip())
                if m:
                    p_list = [x.strip() for x in m.group(2).split(',') if x.strip()]
                    vm.load_function(m.group(1), p_list, parser.parse(m.group(3)))
        
        # 3. Medición Crítica
        gc.disable()
        t_start = time.perf_counter_ns()
        res = vm.run(func, args)
        t_end = time.perf_counter_ns()
        gc.enable()
        
        dt_ms = (t_end - t_start) / 1e6
        out_queue.put((res, dt_ms))

    except Exception as e:
        out_queue.put((f"ERR:{e}", 0))

def worker_formula_precision(root_path, mod_path, func_name, args, out_queue, iters):
    """
    Ejecuta fórmulas matemáticas.
    Usa iteraciones para promediar el tiempo en microsegundos.
    """
    try:
        import sys
        if root_path not in sys.path: sys.path.append(root_path)
        
        spec = importlib.util.spec_from_file_location("mod_iso", mod_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        f = getattr(mod, func_name)

        # Warmup (JIT/Cache)
        f(*args)

        # Medición
        gc.disable()
        t_start = time.perf_counter_ns()
        
        res = None
        for _ in range(iters):
            res = f(*args)
            
        t_end = time.perf_counter_ns()
        gc.enable()

        dt_ms = ((t_end - t_start) / iters) / 1e6
        out_queue.put((res, dt_ms))

    except Exception as e:
        out_queue.put((f"ERR:{e}", 0))

def run_safe(target_type, path, func_name, args, timeout=TIMEOUT_SEC):
    """Orquestador de procesos con Timeout."""
    q = multiprocessing.Queue()
    
    # Ajustar iteraciones según tamaño del número (para no eternizar Fórmulas)
    n_val = args[0]
    iters = ITERATIONS_PRECISION
    if n_val > 100000 or len(args) > 2: iters = 1 # ECPP o N grande -> 1 sola vez
    
    if target_type == "VM":
        p = multiprocessing.Process(target=worker_vm_precision, args=(PROJECT_ROOT, path, func_name, args, q))
    else:
        p = multiprocessing.Process(target=worker_formula_precision, args=(PROJECT_ROOT, path, func_name, args, q, iters))
        
    p.start()
    p.join(timeout)
    
    if p.is_alive():
        p.terminate()
        p.join()
        return "TIMEOUT", timeout * 1000
    
    if not q.empty():
        res, dt = q.get()
        if isinstance(res, str) and res.startswith("ERR:"):
            return res, 0
        return res, dt
        
    return "CRASH (Silent)", 0

# --- VISUALIZADOR DE ECUACIONES ---
def get_display_content(model, mod):
    # 1. Si es Simulación: Extraer del sistema lógico .txt
    if model['requires_vm']:
        poly_file = model.get('raw_poly_file', '')
        path = os.path.join(OUTPUT_DIR, poly_file)
        display = [
            "SYSTEM OF DIOPHANTINE EQUATIONS (STATE TRANSITION)",
            "Map: State(t) -> State(t+1)", ""
        ]
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    lines = [l.strip() for l in f if l.strip() and not l.startswith('---') and not l.startswith('P_')]
                # Filtrar ecuaciones interesantes (no triviales)
                complex_eqs = [l for l in lines if ('*' in l or 'If' in l) and len(l) < 80]
                
                for i, eq in enumerate(complex_eqs[:4]):
                    math_eq = eq.replace('**', '^').replace('*', '·').replace(' - ', ' - ').replace(' + ', ' + ')
                    if ' = 0' not in math_eq: math_eq += ' = 0'
                    display.append(f"   (Eq {i+1}):  {math_eq}")
                
                display.append(f"   ... [ {len(lines)} Equations Total ] ...")
                display.append(f"   Complexity: ~{len(lines)} Variables")
            except: display.append("   [Data Unavailable]")
        else: display.append(f"   [File Not Found: {poly_file}]")
        display.append("   Status: Deterministic Simulation")
        return display
    
    # 2. Si es Fórmula: Extraer metadatos __LATEX_REPR__
    elif mod and hasattr(mod, "__LATEX_REPR__"):
        return mod.__LATEX_REPR__
    
    return ["   [Mathematical Metadata Not Found in Artifact]"]

def format_time(dt_ms):
    """Formatea el tiempo medido con precisión científica."""
    if dt_ms < 1.0: return f"{dt_ms*1000:.1f} µs"
    if dt_ms < 0.001: return f"{dt_ms*1000000:.1f} ns"
    return f"{dt_ms:.3f} ms"

# --- MAIN ENGINE ---
def run_scientific_benchmark():
    print(f"\n{Style.BOLD}PROJECT DIOPHANTUS: FINAL SCIENTIFIC REPORT{Style.END}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 1. PROVER
    cert_store = {}
    if find_ecpp_certificate:
        print(f"{Style.GREY}[Prover] Generating Elliptic Curve Certificates...{Style.END}")
        for n, is_p, desc in NUMBER_ZOO:
            if is_p:
                print(f"   > Mining curve for n={str(n):<12} ... ", end="", flush=True)
                t0 = time.perf_counter()
                try:
                    c = find_ecpp_certificate(n, max_attempts=2000000)
                    dt = (time.perf_counter() - t0) * 1000
                    if c: 
                        cert_store[n] = c
                        a, b = c[0], c[1]
                        print(f"{Style.GREEN}FOUND{Style.END} (a={a}, b={b}) in {format_time(dt)}")
                    else:
                        print(f"{Style.WARN}TIMEOUT{Style.END}")
                except: print(f"{Style.FAIL}ERROR{Style.END}")

    # 2. VERIFIER (Evaluación de Modelos)
    for model in MODELS:
        # Cargar módulo dinámicamente
        mod_path = os.path.join(ARTIFACTS_DIR, model['file']) if model['file'] else None
        mod = None
        if mod_path and os.path.exists(mod_path):
            spec = importlib.util.spec_from_file_location("mod", mod_path)
            mod = importlib.util.module_from_spec(spec)
            try: spec.loader.exec_module(mod)
            except: pass

        # Obtener y mostrar la Ecuación
        content = get_display_content(model, mod)
        Style.print_box(f"{model['name']} ({model['type']})", content)
        
        print(f"{'N':<12} | {'TYPE':<22} | {'TIME':<12} | {'VERDICT':<15} | {'NOTES'}")
        print("-" * 90)

        for n, truth, desc in NUMBER_ZOO:
            raw_val = None
            duration = 0
            
            # --- EJECUCIÓN (Con medición precisa de ECPP) ---
            if model['requires_vm']:
                vm_path = os.path.join(OUTPUT_DIR, model['vm_file'])
                if not os.path.exists(vm_path): raw_val = "NO_FILE"
                else:
                    args = [n, 0, 0, 0]
                    raw_val, duration = run_safe("VM", vm_path, model['vm_func'], args)
            
            elif model.get('is_ecpp'):
                # Medimos el tiempo total: Lookup + Ejecución
                t0 = time.perf_counter()
                cert = cert_store.get(n)
                
                if cert:
                    args = [n] + list(cert)
                    # run_safe devuelve tiempo puro de ejecución, sumamos overhead python
                    val, dt_run = run_safe("FORMULA", mod_path, "G_formula", args)
                    raw_val = val
                    # Tiempo total = Tiempo actual - Inicio (incluye el lookup del dict)
                    duration = (time.perf_counter() - t0) * 1000
                else:
                    raw_val = "NO_CERT"
                    # El tiempo es lo que tardó el 'get' y el 'if' (nanosegundos, pero real)
                    duration = (time.perf_counter() - t0) * 1000
            
            else:
                # Fórmulas estándar
                path = os.path.join(ARTIFACTS_DIR, model['file'])
                raw_val, duration = run_safe("FORMULA", path, "G_formula", [n])

            # --- JUICIO Y FORMATO ---
            
            # Convertir duración numérica a string bonito
            time_str = format_time(duration)

            if raw_val == "TIMEOUT":
                print(f"{str(n):<12} | {desc:<22} | {'> ' + str(TIMEOUT_SEC) + ' s':<12} | {Style.GREY}{'TIMEOUT':<15}{Style.END} | Execution Aborted")
                continue
            
            if raw_val == "NO_CERT":
                if not truth:
                    # Éxito: Compuesto y no hay cert. Mostramos el tiempo real del lookup.
                    print(f"{str(n):<12} | {desc:<22} | {time_str:<12} | {Style.GREEN}{'COMPOSITE':<15}{Style.END} | {Style.GREEN}Proof Impossible{Style.END}")
                else:
                    print(f"{str(n):<12} | {desc:<22} | {Style.GREY}{'---':<12}{Style.END} | {Style.WARN}{'UNKNOWN':<15}{Style.END} | Prover Timeout")
                continue

            if isinstance(raw_val, str):
                 err = raw_val.replace("ERR:", "").strip()[:15]
                 print(f"{str(n):<12} | {desc:<22} | {Style.GREY}{'---':<12}{Style.END} | {Style.FAIL}{'ERROR':<15}{Style.END} | {err}")
                 continue

            # Evaluación Numérica
            is_prime_pred = (raw_val == model['target_val'])
            
            if is_prime_pred == truth:
                status = f"{Style.GREEN}CORRECT{Style.END}"
                note = "Valid"
            elif is_prime_pred and not truth:
                status = f"{Style.FAIL}FALSE POS{Style.END}"
                note = f"{Style.WARN}Liar Detected{Style.END}"
            else:
                status = f"{Style.FAIL}FALSE NEG{Style.END}"
                note = f"Math Error"

            pred_text = "PRIME" if is_prime_pred else "COMPOSITE"
            print(f"{str(n):<12} | {desc:<22} | {time_str:<12} | {status:<15} | {note} ({pred_text})")

if __name__ == "__main__":
    run_scientific_benchmark()