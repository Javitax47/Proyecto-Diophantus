import sys
import time
try:
    from sympy import symbols, groebner, solve, simplify, Symbol
    print('SymPy cargado correctamente.')
except ImportError:
    sys.exit(1)

PROTECTED_VARS = set(['n', 'curve_a', 'curve_b', 'Px', 'Py', 'result', 'n_next', 'curve_a_next', 'curve_b_next', 'Px_next', 'Py_next', 'result_next'])

# 1. Definir Variables
var_names = ['RET', 'dummy_out', 'dummy_out_next', 'e_0', 'val_next', 'x']
# Usamos exec para crear variables dinámicamente en el namespace
for name in var_names:
    globals()[name] = Symbol(name)

vars_map = {name: globals()[name] for name in var_names}

# 2. Sistema de Ecuaciones
core_eqs = [
  (e_0 - (x * 5)) - (0),
  (RET - (e_0 + 3)) - (0),
  (dummy_out_next - (dummy_out)) - (0),
  (val_next - (0)) - (0),
]
print(f'Sistema cargado: {len(core_eqs)} ecuaciones.')