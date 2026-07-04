import re

class CASExporter:
    """
    Exporta el sistema de ecuaciones a formatos compatibles con CAS (SymPy/Sage).
    CORREGIDO: No usa hashing destructivo. Preserva la estructura de llamadas.
    """
    def __init__(self, poly_system_list, state_vars):
        self.raw_poly_system = poly_system_list
        self.state_vars = state_vars
        self.all_vars = set()
        self.sanitized_system = []

        self._process_system()

    def _process_system(self):
        for eq in self.raw_poly_system:
            # 1. Normalizar sintaxis básica
            clean_eq = self._sanitize_equation_syntax(eq)
            self.sanitized_system.append(clean_eq)

            # 2. Extraer variables para declaración
            self._extract_vars_from_string(clean_eq)

    def _sanitize_equation_syntax(self, eq):
        # Convertir "LHS = 0" o "LHS = RHS" a "LHS - RHS"
        if " = " in eq:
            lhs, rhs = eq.split(" = ", 1)
            poly = f"({lhs}) - ({rhs})"
        else:
            poly = eq

        # Reemplazos de sintaxis C/Diophantus a Python/SymPy
        # Arrays: b[t+1] -> b_next
        poly = poly.replace("[t+1]", "_next").replace("[", "_").replace("]", "")
        # Potencias
        poly = poly.replace("^", "**")

        # IMPORTANTE: Manejo de llamadas P_func(args)
        # Las dejamos tal cual, pero aseguramos que sean interpretables como
        # "Function Symbol" o variables si SymPy se queja.
        # Para evitar problemas con SymPy Function('name')(args),
        # convertimos las llamadas en strings planos sanitizados para que sean variables atómicas
        # PERO preservando la identidad de los argumentos para que Gröbner vea la dependencia.

        # Estrategia: P_func(a, b) -> P_func__a__b
        # Esto crea una variable única que representa ese estado de computación.

        def replace_call(match):
            func_name = match.group(1)
            args_str = match.group(2)
            # Limpiar argumentos
            clean_args = args_str.replace(", ", "__").replace(",", "__").replace(" ", "")
            # Sanitizar caracteres no permitidos en variables
            clean_args = clean_args.replace("+", "_plus_").replace("-", "_minus_").replace("*", "_mul_")
            clean_args = clean_args.replace("(", "_").replace(")", "_")
            return f"CALL_{func_name}__{clean_args}"

        # Regex para capturar P_name(...)
        # Nota: Esto no soporta anidamiento profundo P(P(...)) en una sola regex simple,
        # pero el compilador suele aplanar antes.
        poly = re.sub(r'P_(\w+)\((.*?)\)', replace_call, poly)

        return poly

    def _extract_vars_from_string(self, text):
        # Extraer todo lo que parezca una variable Python
        raw_tokens = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text))
        reserved = {'div', 'floor', 'if', 'pow'} # Keywords matemáticas

        for token in raw_tokens:
            if token not in reserved and not token[0].isdigit():
                self.all_vars.add(token)

    def export_sage_script(self):
        # (Simplificado para este hotfix)
        return "# Sage script placeholder"

    def export_sympy_script(self):
        var_list = sorted(list(self.all_vars))

        # Variables protegidas (Input/Output del algoritmo ECPP)
        protected_base = ['n', 'curve_a', 'curve_b', 'Px', 'Py', 'result']
        # Añadir versiones _next
        protected = protected_base + [p + "_next" for p in protected_base]

        lines = [
            "import sys",
            "import time",
            "try:",
            "    from sympy import symbols, groebner, solve, simplify, Symbol",
            "    print('SymPy cargado correctamente.')",
            "except ImportError:",
            "    sys.exit(1)",
            "",
            f"PROTECTED_VARS = set({protected})",
            "",
            "# 1. Definir Variables",
            f"var_names = {var_list}",
            "# Usamos exec para crear variables dinámicamente en el namespace",
            "for name in var_names:",
            "    globals()[name] = Symbol(name)",
            "",
            "vars_map = {name: globals()[name] for name in var_names}",
            "",
            "# 2. Sistema de Ecuaciones",
            "core_eqs = ["
        ]
        for eq in self.sanitized_system:
            lines.append(f"  {eq},")
        lines.extend([
            "]",
            "print(f'Sistema cargado: {len(core_eqs)} ecuaciones.')"
        ])
        return "\n".join(lines)