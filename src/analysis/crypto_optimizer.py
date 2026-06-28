import sys
import os
import argparse
import re
import time
from z3 import *

"""
=============================================================================
   DIOPHANTUS CRYPTO-OPTIMIZER V5.3 (Variadic Fix)
=============================================================================
Corrección: Soporte para And/Or con múltiples argumentos en condiciones de minado.
=============================================================================
"""

class CryptoSolver:
    def __init__(self, system_file, bits=32):
        self.system_file = system_file
        self.solver = Solver()
        self.vars = {}
        self.BITS = bits # Configurable (32 o 256)
        print(f"  [Config] Arquitectura: {self.BITS}-bit")

    def get_var(self, name):
        clean_name = re.sub(r'\[.*?\]', '', name).strip()
        if not clean_name: return BitVecVal(0, self.BITS)
        
        # Literales
        if clean_name.isdigit(): return BitVecVal(int(clean_name), self.BITS)
        if clean_name.startswith('-') and clean_name[1:].isdigit():
            return BitVecVal(int(clean_name), self.BITS)
        if clean_name.startswith('0x'):
            return BitVecVal(int(clean_name, 16), self.BITS)
        
        if clean_name not in self.vars:
            self.vars[clean_name] = BitVec(clean_name, self.BITS)
        return self.vars[clean_name]

    def parse_and_build(self):
        print(f"  [Crypto] Ingiriendo circuito lógico: {os.path.basename(self.system_file)}...")
        
        if not os.path.exists(self.system_file):
            print(f"  [FATAL] Archivo no encontrado.")
            sys.exit(1)

        with open(self.system_file, 'r') as f: lines = f.readlines()

        success_count = 0
        for line in lines:
            if "---" in line or not line.strip(): continue
            if ' = 0' not in line: continue
            
            content = line.rsplit(' = 0', 1)[0]
            try:
                parts = content.split(' - ', 1)
                if len(parts) != 2: continue
                
                lhs_str = parts[0].strip()
                rhs_str = parts[1].strip()
                
                while rhs_str.startswith('(') and rhs_str.endswith(')'):
                    balance = 0; valid = True
                    for i, c in enumerate(rhs_str[:-1]):
                        if c=='(': balance+=1
                        elif c==')': balance-=1
                        if balance==0 and i>0: valid = False; break
                    if valid: rhs_str = rhs_str[1:-1]
                    else: break

                target_var = self.get_var(lhs_str)
                expr_z3 = self._parse_expression(rhs_str)
                
                if expr_z3 is not None:
                    self.solver.add(target_var == expr_z3)
                    success_count += 1
            except: pass

        print(f"  [Resumen] {success_count} puertas lógicas cargadas.")

    def _parse_expression(self, expr_str):
        # Helper para literales
        def wrap_lit(match):
            s = match.group(0)
            base = 16 if s.startswith('0x') else 10
            try: return f"BitVecVal({int(s, base)}, {self.BITS})"
            except: return s

        expr_fixed = re.sub(r'\b0x[0-9a-fA-F]+\b', wrap_lit, expr_str)
        expr_fixed = re.sub(r'(?<![a-zA-Z_])\b\d+\b', wrap_lit, expr_fixed)
        
        var_matches = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*(?:\[.*?\])?', expr_fixed)
        
        context = {
            'If': If, 'BitVecVal': BitVecVal,
            'And': lambda a, b: a & b, 'Or': lambda a, b: a | b,
            'UGT': UGT, 'ULT': ULT, 'UGE': UGE, 'ULE': ULE # <--- NUEVO
        }
        
        final_eval_str = expr_fixed.replace('^', '^') 
        
        for v_raw in var_matches:
            if v_raw in ['If', 'BitVecVal', 'And', 'Or']: continue
            if "BitVecVal" in v_raw: continue

            v_clean = re.sub(r'\[.*?\]', '', v_raw)
            z3_obj = self.get_var(v_clean)
            
            if '[' in v_raw:
                safe_token = v_clean + "_VAR"
                final_eval_str = final_eval_str.replace(v_raw, safe_token)
                context[safe_token] = z3_obj
            else:
                context[v_clean] = z3_obj

        try: return eval(final_eval_str, {"__builtins__": None}, context)
        except: return None

    def mine(self, target_condition, target_var_name="nonce"):
        print(f"\n{Colors.BOLD}--- INICIANDO MINERÍA INVERSA ---{Colors.END}")
        print(f"Objetivo: {target_condition}")
        
        try:
            cond_fixed = target_condition
            # Wrap literales para la condición
            def wrap_lit(match): return f"BitVecVal({int(match.group(0))}, {self.BITS})"
            cond_fixed = re.sub(r'(?<![a-zA-Z_])\b\d+\b', wrap_lit, cond_fixed)

            context = {k: v for k, v in self.vars.items()}
            
            # FIX: Usar z3.And y z3.Or para soportar múltiples argumentos en condiciones booleanas
            context.update({
                'If': If, 
                'BitVecVal': BitVecVal,
                'And': And, # Z3 nativo (variadic)
                'Or': Or    # Z3 nativo (variadic)
            })
            
            tokens = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', cond_fixed)
            for t in tokens:
                if t not in context and t != 'BitVecVal': context[t] = self.get_var(t)

            z3_cond = eval(cond_fixed, {"__builtins__": None}, context)
            self.solver.add(z3_cond)
            
            print("  [Solver] Resolviendo restricciones (Bit-Blasting)...")
            t0 = time.time()
            status = self.solver.check()
            dt = time.time() - t0
            
            if status == sat:
                print(f"  {Colors.OKGREEN}¡CRACKED! Solución encontrada en {dt:.4f}s{Colors.END}")
                m = self.solver.model()
                
                print(f"\n  {Colors.BOLD}--- VARIABLES DESCIFRADAS (GOD MODE) ---{Colors.END}")
                all_vars = []
                for d in m.decls():
                    name = d.name()
                    val = m[d].as_long()
                    # Mostrar valor positivo (uint) para facilitar el uso en blockchain
                    val_hex = hex(val)
                    all_vars.append((name, val, val_hex))

                all_vars.sort(key=lambda x: (x[0].startswith('e_'), x[0]))
                
                target_clean = re.sub(r'\[.*?\]', '', target_var_name).strip()
                
                for name, val, hx in all_vars:
                    color = Colors.END
                    marker = ""
                    if target_clean in name:
                        color = Colors.OKCYAN
                        marker = " <--- [CLAVE]"
                    
                    if len(all_vars) < 20 or not name.startswith('e_'):
                        print(f"  > {color}{name:<20}: {val:<25} ({hx}){marker}{Colors.END}")
            else:
                print(f"  {Colors.FAIL}UNSATISFIABLE{Colors.END}. (Contradicción Lógica)")

        except Exception as e:
            print(f"  [ERROR] {e}")

class Colors:
    HEADER = '\033[95m'; OKGREEN = '\033[92m'; OKCYAN = '\033[96m'; FAIL = '\033[91m'; END = '\033[0m'; BOLD = '\033[1m'; WARN = '\033[93m'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("system_file")
    parser.add_argument("--condition", required=True)
    parser.add_argument("--target", default="nonce")
    parser.add_argument("--bits", type=int, default=32)
    args = parser.parse_args()

    s = CryptoSolver(args.system_file, args.bits)
    s.parse_and_build()
    s.mine(args.condition, args.target)