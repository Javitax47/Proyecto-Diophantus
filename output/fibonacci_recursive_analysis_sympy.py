import sys
import time
try:
    from sympy import symbols, groebner, solve, simplify, Symbol
    print('SymPy cargado correctamente.')
except ImportError:
    sys.exit(1)

PROTECTED_VARS = set(['n', 'curve_a', 'curve_b', 'Px', 'Py', 'result', 'n_next', 'curve_a_next', 'curve_b_next', 'Px_next', 'Py_next', 'result_next'])

# 1. Definir Variables
var_names = ['CALL_fib__fib__fib__e_11__e_10', 'CALL_fib__fib__fib__e_13__e_12', 'RET', 'e_0', 'e_1', 'e_10', 'e_11', 'e_12', 'e_13', 'e_2', 'e_3', 'e_4', 'e_5', 'e_6', 'e_7', 'e_8', 'e_9', 'n', 'n_next', 'result_next', 'x']
# Usamos exec para crear variables dinámicamente en el namespace
for name in var_names:
    globals()[name] = Symbol(name)

vars_map = {name: globals()[name] for name in var_names}

# 2. Sistema de Ecuaciones
core_eqs = [
  (e_0 * (1 - e_0)) - (0),
  (e_0 * ((1) - (x) - (e_1**2 + e_2**2 + e_3**2 + e_4**2))) - (0),
  ((1 - e_0) * ((x) - (1) - 1 - (e_5**2 + e_6**2 + e_7**2 + e_8**2))) - (0),
  (e_11 - (x - 1)) - (0),
  (CALL_fib__fib__fib__e_11__e_10) - (0),
  (e_13 - (x - 2)) - (0),
  (CALL_fib__fib__fib__e_13__e_12) - (0),
  (e_9 - (e_10 + e_12)) - (0),
  (RET - ((e_0) * (x) + (1 - e_0) * (e_9))) - (0),
  (n_next - (n)) - (0),
  (result_next - (0)) - (0),
]
print(f'Sistema cargado: {len(core_eqs)} ecuaciones.')