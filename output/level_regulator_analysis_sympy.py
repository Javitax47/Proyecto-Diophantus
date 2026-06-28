import sys
import time
try:
    from sympy import symbols, groebner, solve, simplify, Symbol
    print('SymPy cargado correctamente.')
except ImportError:
    sys.exit(1)

PROTECTED_VARS = set(['n', 'curve_a', 'curve_b', 'Px', 'Py', 'result', 'n_next', 'curve_a_next', 'curve_b_next', 'Px_next', 'Py_next', 'result_next'])

# 1. Definir Variables
var_names = ['C_', 'C_0', 'C_1', 'C_2', 'C_3', 'C_4', 'e_0', 'e_1', 'e_10', 'e_11', 'e_12', 'e_13', 'e_14', 'e_15', 'e_16', 'e_17', 'e_18', 'e_19', 'e_2', 'e_20', 'e_21', 'e_22', 'e_23', 'e_24', 'e_25', 'e_26', 'e_27', 'e_28', 'e_3', 'e_4', 'e_5', 'e_6', 'e_7', 'e_8', 'e_9', 'level', 'level_next', 'rate', 'rate_next', 'throttle_input', 'throttle_input_next']
# Usamos exec para crear variables dinámicamente en el namespace
for name in var_names:
    globals()[name] = Symbol(name)

vars_map = {name: globals()[name] for name in var_names}

# 2. Sistema de Ecuaciones
core_eqs = [
  (C_0 - ((C_1) * (C_4) + (1 - C_1) * (level))) - (0),
  (C_1 - (C_2 * C_3)) - (0),
  (e_0 - (throttle_input - 1)) - (0),
  (C_2 * (1 - C_2)) - (0),
  (C_2 * ((e_0) - (0) - (e_1**2 + e_2**2 + e_3**2 + e_4**2))) - (0),
  ((1 - C_2) * ((0) - (e_0) - 1 - (e_5**2 + e_6**2 + e_7**2 + e_8**2))) - (0),
  (e_9 - (rate - 1)) - (0),
  (C_3 * (1 - C_3)) - (0),
  (C_3 * ((e_9) - (5) - (e_10**2 + e_11**2 + e_12**2 + e_13**2))) - (0),
  ((1 - C_3) * ((5) - (e_9) - 1 - (e_14**2 + e_15**2 + e_16**2 + e_17**2))) - (0),
  (C_4 - (level - rate)) - (0),
  (level_next - (C_{0})) - (0),
  (e_19 - (10 - 1)) - (0),
  (e_18 * (1 - e_18)) - (0),
  (e_18 * ((e_19) - (C_0) - (e_20**2 + e_21**2 + e_22**2 + e_23**2))) - (0),
  ((1 - e_18) * ((C_0) - (e_19) - 1 - (e_24**2 + e_25**2 + e_26**2 + e_27**2))) - (0),
  (e_28 - (rate + 1)) - (0),
  (rate_next - ((e_18) * (e_28) + (1 - e_18) * (6))) - (0),
  (throttle_input_next - (throttle_input)) - (0),
]
print(f'Sistema cargado: {len(core_eqs)} ecuaciones.')