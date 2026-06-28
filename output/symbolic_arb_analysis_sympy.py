import sys
import time
try:
    from sympy import symbols, groebner, solve, simplify, Symbol
    print('SymPy cargado correctamente.')
except ImportError:
    sys.exit(1)

PROTECTED_VARS = set(['n', 'curve_a', 'curve_b', 'Px', 'Py', 'result', 'n_next', 'curve_a_next', 'curve_b_next', 'Px_next', 'Py_next', 'result_next'])

# 1. Definir Variables
var_names = ['amount_in', 'amount_in_next', 'e_0', 'e_1', 'profit_next', 'rIn_0', 'rIn_0_next', 'rIn_1', 'rIn_1_next', 'rIn_2', 'rIn_2_next', 'rOut_0', 'rOut_0_next', 'rOut_1', 'rOut_1_next', 'rOut_2', 'rOut_2_next']
# Usamos exec para crear variables dinámicamente en el namespace
for name in var_names:
    globals()[name] = Symbol(name)

vars_map = {name: globals()[name] for name in var_names}

# 2. Sistema de Ecuaciones
core_eqs = [
  (amount_in_next - (amount_in)) - (0),
  (e_0 - (0 > amount_in)) - (0),
  (e_1 - (0 - amount_in)) - (0),
  (profit_next - ((e_0) * (e_1) + (1 - e_0) * (0))) - (0),
  (rIn_0_next - (rIn_0)) - (0),
  (rIn_1_next - (rIn_1)) - (0),
  (rIn_2_next - (rIn_2)) - (0),
  (rOut_0_next - (rOut_0)) - (0),
  (rOut_1_next - (rOut_1)) - (0),
  (rOut_2_next - (rOut_2)) - (0),
]
print(f'Sistema cargado: {len(core_eqs)} ecuaciones.')