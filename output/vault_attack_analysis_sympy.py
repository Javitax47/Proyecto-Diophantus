import sys
import time
try:
    from sympy import symbols, groebner, solve, simplify, Symbol
    print('SymPy cargado correctamente.')
except ImportError:
    sys.exit(1)

PROTECTED_VARS = set(['n', 'curve_a', 'curve_b', 'Px', 'Py', 'result', 'n_next', 'curve_a_next', 'curve_b_next', 'Px_next', 'Py_next', 'result_next'])

# 1. Definir Variables
var_names = ['attacker_donation', 'attacker_donation_next', 'convertToShares', 'e_0', 'total_assets', 'total_assets_next', 'total_supply', 'total_supply_next', 'victim_deposit', 'victim_deposit_next', 'victim_shares_next']
# Usamos exec para crear variables dinámicamente en el namespace
for name in var_names:
    globals()[name] = Symbol(name)

vars_map = {name: globals()[name] for name in var_names}

# 2. Sistema de Ecuaciones
core_eqs = [
  (attacker_donation_next - (attacker_donation)) - (0),
  (total_assets_next - (total_assets)) - (0),
  (total_supply_next - (total_supply)) - (0),
  (victim_deposit_next - (victim_deposit)) - (0),
  (e_0 - (convertToShares + total_assets)) - (0),
  (victim_shares_next - (e_0 + victim_deposit)) - (0),
]
print(f'Sistema cargado: {len(core_eqs)} ecuaciones.')