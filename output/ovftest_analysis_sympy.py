import sys
import time
try:
    from sympy import symbols, groebner, solve, simplify, Symbol
    print('SymPy cargado correctamente.')
except ImportError:
    sys.exit(1)

PROTECTED_VARS = set(['n', 'curve_a', 'curve_b', 'Px', 'Py', 'result', 'n_next', 'curve_a_next', 'curve_b_next', 'Px_next', 'Py_next', 'result_next'])

# 1. Definir Variables
var_names = ['__OVERFLOW__', 'c1_countdown_c2_countdown_c3_countdown_c4_countdown_c5_countdown_countdown', 'c1_countdown_c2_countdown_c3_countdown_c4_countdown_countdown', 'c1_countdown_c2_countdown_c3_countdown_countdown', 'c1_countdown_c2_countdown_countdown', 'c1_countdown_countdown', 'countdown', 'e_0', 'e_1', 'e_10', 'e_11', 'e_12', 'e_13', 'e_14', 'e_15', 'e_16', 'e_17', 'e_18', 'e_19', 'e_2', 'e_20', 'e_21', 'e_22', 'e_23', 'e_24', 'e_25', 'e_26', 'e_27', 'e_28', 'e_29', 'e_3', 'e_30', 'e_31', 'e_32', 'e_33', 'e_34', 'e_35', 'e_36', 'e_37', 'e_38', 'e_39', 'e_4', 'e_40', 'e_41', 'e_42', 'e_43', 'e_44', 'e_45', 'e_46', 'e_47', 'e_48', 'e_49', 'e_5', 'e_50', 'e_51', 'e_52', 'e_53', 'e_54', 'e_55', 'e_56', 'e_57', 'e_58', 'e_59', 'e_6', 'e_60', 'e_61', 'e_62', 'e_63', 'e_64', 'e_7', 'e_8', 'e_9', 'input_val', 'input_val_next', 'overflow', 'result_next']
# Usamos exec para crear variables dinámicamente en el namespace
for name in var_names:
    globals()[name] = Symbol(name)

vars_map = {name: globals()[name] for name in var_names}

# 2. Sistema de Ecuaciones
core_eqs = [
  (input_val_next - (input_val)) - (0),
  (e_0*(1 - e_0)) - (0),
  (((0) - (countdown)) - (e_0*(e_1*e_1 + e_2*e_2 + e_3*e_3 + e_4*e_4) - (1 - e_0)*(1 + e_5*e_5 + e_6*e_6 + e_7*e_7 + e_8*e_8))) - (0),
  (e_10*(1 - e_10)) - (0),
  (((0) - (c1_countdown_countdown)) - (e_10*(e_11*e_11 + e_12*e_12 + e_13*e_13 + e_14*e_14) - (1 - e_10)*(1 + e_15*e_15 + e_16*e_16 + e_17*e_17 + e_18*e_18))) - (0),
  (e_20*(1 - e_20)) - (0),
  (((0) - (c1_countdown_c2_countdown_countdown)) - (e_20*(e_21*e_21 + e_22*e_22 + e_23*e_23 + e_24*e_24) - (1 - e_20)*(1 + e_25*e_25 + e_26*e_26 + e_27*e_27 + e_28*e_28))) - (0),
  (e_30*(1 - e_30)) - (0),
  (((0) - (c1_countdown_c2_countdown_c3_countdown_countdown)) - (e_30*(e_31*e_31 + e_32*e_32 + e_33*e_33 + e_34*e_34) - (1 - e_30)*(1 + e_35*e_35 + e_36*e_36 + e_37*e_37 + e_38*e_38))) - (0),
  (e_40*(1 - e_40)) - (0),
  (((0) - (c1_countdown_c2_countdown_c3_countdown_c4_countdown_countdown)) - (e_40*(e_41*e_41 + e_42*e_42 + e_43*e_43 + e_44*e_44) - (1 - e_40)*(1 + e_45*e_45 + e_46*e_46 + e_47*e_47 + e_48*e_48))) - (0),
  (e_50*(1 - e_50)) - (0),
  (((0) - (c1_countdown_c2_countdown_c3_countdown_c4_countdown_c5_countdown_countdown)) - (e_50*(e_51*e_51 + e_52*e_52 + e_53*e_53 + e_54*e_54) - (1 - e_50)*(1 + e_55*e_55 + e_56*e_56 + e_57*e_57 + e_58*e_58))) - (0),
  (e_49 - ((e_50) * (7) + (1 - e_50) * (__OVERFLOW__))) - (0),
  (e_59 - ((e_50)*(0) + (1 - (e_50))*(1))) - (0),
  (e_39 - ((e_40) * (7) + (1 - e_40) * (e_49))) - (0),
  (e_60 - ((e_40)*(0) + (1 - (e_40))*(e_59))) - (0),
  (e_29 - ((e_30) * (7) + (1 - e_30) * (e_39))) - (0),
  (e_61 - ((e_30)*(0) + (1 - (e_30))*(e_60))) - (0),
  (e_19 - ((e_20) * (7) + (1 - e_20) * (e_29))) - (0),
  (e_62 - ((e_20)*(0) + (1 - (e_20))*(e_61))) - (0),
  (e_9 - ((e_10) * (7) + (1 - e_10) * (e_19))) - (0),
  (e_63 - ((e_10)*(0) + (1 - (e_10))*(e_62))) - (0),
  (result_next - ((e_0) * (7) + (1 - e_0) * (e_9))) - (0),
  (e_64 - ((e_0)*(0) + (1 - (e_0))*(e_63))) - (0),
  (overflow - (e_64)) - (0),
  (overflow) - (0),
]
print(f'Sistema cargado: {len(core_eqs)} ecuaciones.')