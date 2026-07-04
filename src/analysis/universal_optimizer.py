import sys
import os
import argparse
import re

# Configuración de rutas para importar la VM
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_ROOT)

try:
    from src.runtime.vm import VM, Parser
    import src.analysis.matrix_kernel as matrix_kernel
except ImportError as e:
    print(f"[ERROR] Fallo de importación: {e}")
    sys.exit(1)

class UniversalOptimizer:
    def __init__(self, vm_file):
        self.vm_file = vm_file
        self.vm = VM()
        self.parser = Parser()
        self._load_vm()

    def _load_vm(self):
        if not os.path.exists(self.vm_file):
            raise FileNotFoundError(f"No existe: {self.vm_file}")

        with open(self.vm_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Cargar funciones del bytecode
        count = 0
        for line in content.split('\n'):
            m = re.match(r'P_(\w+)\((.*?)\)\s*=\s*(.*)', line.strip())
            if m:
                name, p_str, body = m.group(1), m.group(2), m.group(3)
                params = [x.strip() for x in p_str.split(',') if x.strip()]
                self.vm.load_function(name, params, self.parser.parse(body))
                count += 1

        if count == 0:
            raise ValueError("Bytecode vacío o inválido.")

    def mine_trajectory(self, func_name, start_val, probes=5):
        """Ejecuta la función paso a paso para obtener una secuencia."""
        print(f"  [Miner] Ejecutando sonda en '{func_name}' con semilla {start_val}...")
        trajectory = [start_val]
        current = start_val

        for _ in range(probes):
            try:
                # Intentamos ejecutar un paso.
                # Asumimos firma (val, step) o (val)
                try:
                    next_val = self.vm.run(func_name, [current, 0])
                except:
                    next_val = self.vm.run(func_name, [current])

                trajectory.append(next_val)
                current = next_val
            except Exception as e:
                print(f"  [Miner] Error en ejecución: {e}")
                break

        return trajectory

    def infer_pattern(self, traj):
        """Motor de Inferencia Algebraica."""
        if len(traj) < 4: return None

        x0, x1, x2, x3 = traj[0], traj[1], traj[2], traj[3]
        print(f"  [Analyst] Traza observada: {traj} ...")

        # CASO 1: Estática (No hace nada)
        if x0 == x1 == x2:
            print("  [DETECTADO] Identidad (A=1, B=0)")
            return 1, 0

        # CASO 2: Aritmética (Contador) -> x_new = x + B
        d1 = x1 - x0
        d2 = x2 - x1
        if d1 == d2:
            print(f"  [DETECTADO] Progresión Aritmética (x -> x + {d1})")
            return 1, d1

        # CASO 3: Geométrica (Multiplicación) -> x_new = A * x
        if x0 != 0 and x1 != 0:
            if x1 % x0 == 0 and x2 % x1 == 0:
                r1 = x1 // x0
                r2 = x2 // x1
                if r1 == r2:
                    print(f"  [DETECTADO] Progresión Geométrica (x -> {r1}*x)")
                    return r1, 0

        # CASO 4: Lineal Afín -> x_new = A*x + B
        # A = (x2 - x1) / (x1 - x0)
        denom = (x1 - x0)
        if denom != 0:
            num = (x2 - x1)
            if num % denom == 0:
                A = num // denom
                B = x1 - A * x0
                # Verificación con x3
                if A * x2 + B == x3:
                    print(f"  [DETECTADO] Recurrencia Lineal (x -> {A}*x + {B})")
                    return 'AFFINE', (A, B)

        # CASO 5: Exponenciación Modular (Miller-Rabin Core) -> x_new = x^2 % M
        # Detectar si crece cuadráticamente antes de módulo
        # Heurística simple: ver si x1 == x0^2 (si no hay mod) o buscar M
        # Dado que M es desconocido, probamos M = x0^2 - x1
        if x0 > 1:
            pos_M = (x0 * x0) - x1
            if pos_M > 1: # Candidato a Módulo
                if (x1 * x1) % pos_M == x2 and (x2 * x2) % pos_M == x3:
                     print(f"  [DETECTADO] Cuadrática Modular (x -> x^2 % {pos_M})")
                     return 'MOD_SQUARE', (pos_M,)

        # CASO 6: Producto Modular (Linear Congruential) -> x_new = (A * x) % M
        # x1 = A*x0 % M
        # x2 = A*x1 % M
        # M es difícil de encontrar ciegamente solo con 3 puntos sin fuerza bruta,
        # pero para tests de primalidad M suele ser el input 'n'.
        # (Aquí podríamos inyectar 'n' si lo tuviéramos en el contexto)

        print("  [Analyst] No se detectó patrón simple (Posible Caos/Curva Elíptica).")
        return None

def main():
    parser = argparse.ArgumentParser(description="Universal Optimizer (Matrix Compressor)")
    parser.add_argument("vm_file", help="Archivo bytecode (.txt)")
    parser.add_argument("--func", required=True, help="Nombre de la función de transición")
    parser.add_argument("--steps", type=int, required=True, help="Pasos a comprimir")
    parser.add_argument("--seed", type=int, default=1, help="Valor inicial para análisis")
    args = parser.parse_args()

    print("--- UNIVERSAL OPTIMIZER V1.0 ---")

    opt = UniversalOptimizer(args.vm_file)

    # 1. Minería
    traj = opt.mine_trajectory(args.func, args.seed)

    # 2. Inferencia
    coeffs = opt.infer_pattern(traj)

    if coeffs:
        A, B = coeffs
        # 3. Síntesis
        code = matrix_kernel.get_matrix_code(A, B, args.steps)

        base_name = os.path.basename(args.vm_file).replace('_interpreter_input.txt', '')
        out_path = f"output/artifacts/{base_name}_compressed.py"
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        with open(out_path, "w") as f:
            f.write(code)

        print(f"\n[ÉXITO] Compresión Temporal Completada.")
        print(f"        Archivo: {out_path}")
        print(f"        Reducción: {args.steps} ops -> ~{len(bin(args.steps))} ops (Matriciales)")
    else:
        print("\n[INFO] El algoritmo es irreducible linealmente.")

if __name__ == "__main__":
    main()