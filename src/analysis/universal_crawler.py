import sys
import os
import time
import argparse
import importlib.util
import re

# Añadir raíz al path para importar módulos del runtime si es necesario
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

try:
    from src.runtime.vm import VM, Parser
    VM_AVAILABLE = True
except ImportError:
    VM_AVAILABLE = False

class DiophantineCrawler:
    def __init__(self, target_file, entry_point="n"):
        self.target_file = target_file
        self.entry_var = entry_point
        self.vm = None
        self.formula_module = None
        self.mode = self._detect_mode()
        
        print(f"[Crawler] Modo detectado: {self.mode}")
        self._load_engine()

    def _detect_mode(self):
        if self.target_file.endswith(".txt"):
            return "VM_RAW"
        elif self.target_file.endswith(".py"):
            # Analizamos si la fórmula requiere vector 'x'
            with open(self.target_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "def G_formula" in content and ", x)" in content:
                    return "HYBRID_ENERGY" # Deep Opt normal
                else:
                    return "PURE_ENERGY" # Singularidad (Fermat/Lucas/Baillie)
        return "UNKNOWN"

    def _load_engine(self):
        if self.mode == "VM_RAW":
            if not VM_AVAILABLE: 
                raise ImportError("No se encuentra src.runtime.vm")
            self.vm = VM()
            parser = Parser()
            with open(self.target_file, 'r') as f:
                content = f.read()
            count = 0
            for line in content.split('\n'):
                m = re.match(r'P_(\w+)\((.*?)\)\s*=\s*(.*)', line.strip())
                if m:
                    name, p_str, body = m.group(1), m.group(2), m.group(3)
                    params = [x.strip() for x in p_str.split(',') if x.strip()]
                    self.vm.load_function(name, params, parser.parse(body))
                    count += 1
            if count == 0: raise ValueError("Bytecode vacío.")

        elif "ENERGY" in self.mode:
            # Carga dinámica del módulo .py
            spec = importlib.util.spec_from_file_location("math_kernel", self.target_file)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self.formula_module = mod

    def check(self, n):
        """
        Evalúa si 'n' es una solución.
        Retorna True si cumple la condición del sistema.
        """
        # --- CASO 1: SINGULARIDAD (Baillie-PSW, Lucas, Fermat) ---
        # Estándar V4.0: La ecuación devuelve Energía de Error.
        # 0 = Éxito (Primo / Solución válida).
        # >0 = Fallo.
        if self.mode == "PURE_ENERGY":
            try:
                res = self.formula_module.G_formula(n)
                return res == 0 
            except TypeError:
                return False # Argumentos incorrectos (ej. requiere certificado ECPP)

        # --- CASO 2: VM CRUDA (Compilación directa C) ---
        # Estándar C: 1 = True, 0 = False
        elif self.mode == "VM_RAW":
            func = self.entry_var
            # Heurística para encontrar el entry point
            if func == "n" and self.vm:
                # Usar la última función definida (suele ser main o la lógica principal)
                func = list(self.vm.functions.keys())[-1]
            
            try:
                # Intentamos llamar con (n) o (n, 0) para corrección de aridad
                try: res = self.vm.run(func, [n])
                except: res = self.vm.run(func, [n, 0])
                return res == 1
            except: return False

        # --- CASO 3: HÍBRIDO (Fórmulas con vector x) ---
        # Requiere minería. Para este crawler simple, probamos con vector vacío.
        # Si la reducción fue perfecta, funcionará. Si no, fallará (requiere miner.py completo).
        elif self.mode == "HYBRID_ENERGY":
            try:
                dummy_x = [0] * 5000
                res = self.formula_module.G_formula(n, dummy_x)
                return res == 0
            except: return False

        return False

    def crawl(self, start, count):
        print(f"--- INICIANDO BÚSQUEDA ---")
        print(f"Semilla: {start}")
        print(f"Objetivo: {count} hallazgos")
        
        found = 0
        current = start
        t_start = time.time()
        
        # Safety break para no colgar el terminal si no hay soluciones
        max_iter = 1000000 
        
        while found < count and (current - start) < max_iter:
            if self.check(current):
                dt = time.time() - t_start
                print(f"  ★ HALLAZGO #{found+1}: {current} (T+{dt:.2f}s)")
                found += 1
            current += 1
            
        if found == 0:
            print("  (Sin resultados en el rango de búsqueda)")

def main():
    parser = argparse.ArgumentParser(description="Universal Diophantine Crawler")
    parser.add_argument("file", help="Archivo de ecuación (.py) o Bytecode (.txt)")
    parser.add_argument("--start", type=int, default=1, help="Número de inicio")
    parser.add_argument("--count", type=int, default=5, help="Cantidad a encontrar")
    parser.add_argument("--func", default="n", help="Función entry point (Solo modo VM)")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: Archivo no encontrado: {args.file}")
        sys.exit(1)

    crawler = DiophantineCrawler(args.file, args.func)
    crawler.crawl(args.start, args.count)

if __name__ == "__main__":
    main()