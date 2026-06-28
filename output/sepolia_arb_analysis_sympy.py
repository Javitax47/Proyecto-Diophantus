import sys
import time
try:
    from sympy import symbols, groebner, solve, simplify, Symbol
    print('SymPy cargado correctamente.')
except ImportError:
    sys.exit(1)

PROTECTED_VARS = set(['n', 'curve_a', 'curve_b', 'Px', 'Py', 'result', 'n_next', 'curve_a_next', 'curve_b_next', 'Px_next', 'Py_next', 'result_next'])

# 1. Definir Variables
var_names = ['C_0', 'amount_in', 'amount_in_next', 'c1_execute_path_get_amount_out', 'e_0', 'e_1', 'e_10', 'e_11', 'e_12', 'e_13', 'e_14', 'e_15', 'e_16', 'e_17', 'e_18', 'e_2', 'e_3', 'e_4', 'e_5', 'e_6', 'e_7', 'e_8', 'e_9', 'execute_path', 'profit_next']
# Usamos exec para crear variables dinámicamente en el namespace
for name in var_names:
    globals()[name] = Symbol(name)

vars_map = {name: globals()[name] for name in var_names}

# 2. Sistema de Ecuaciones
core_eqs = [
  (C_0 - (c1_execute_path_get_amount_out * 997)) - (0),
  (amount_in_next - (amount_in)) - (0),
  (e_1 - (amount_in >= 1000)) - (0),
  (e_2 - (amount_in <= 100000000)) - (0),
  (e_0 - (e_1 && e_2)) - (0),
  (e_5 - (C_0 * 6383170606819)) - (0),
  (e_9 - (C_0 * 0)) - (0),
  (e_13 - (C_0 * 3551072005)) - (0),
  (e_15 - (execute_path * 1000)) - (0),
  (e_14 - (e_15 + C_0)) - (0),
  ((e_13) - ((e_14) * (e_12) + e_16)) - (0),
  (e_11 - (e_12 * 1000)) - (0),
  (e_10 - (e_11 + C_0)) - (0),
  ((e_9) - ((e_10) * (e_8) + e_17)) - (0),
  (e_7 - (e_8 * 1000)) - (0),
  (e_6 - (e_7 + C_0)) - (0),
  ((e_5) - ((e_6) * (e_4) + e_18)) - (0),
  (e_3 - (e_4 - execute_path)) - (0),
  (profit_next - ((e_0) * (e_3) + (1 - e_0) * (0))) - (0),
]
print(f'Sistema cargado: {len(core_eqs)} ecuaciones.')