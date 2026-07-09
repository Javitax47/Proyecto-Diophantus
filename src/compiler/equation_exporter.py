import re

class EquationExporter:
    """
    Construye y exporta las representaciones textuales de las ecuaciones.
    Totalmente agnóstico al código C de entrada.
    """
    def __init__(self, unoptimized_f, optimized_f, sub_defs, state_vars, function_relations=None):
        self.unoptimized_f = unoptimized_f
        self.optimized_f = optimized_f
        self.sub_defs = sub_defs
        self.state_vars = set(state_vars)
        self.function_relations = function_relations or {}

    # --- Helpers de AST (Genéricos) ---
    def _get_sort_key(self, item):
        match = re.search(r'\d+', item[0])
        return int(match.group()) if match else float('inf')

    def _tuple_to_generic_string(self, expr):
        if not isinstance(expr, tuple):
            return str(expr).replace("{", "").replace("}", "")
        op = expr[0]
        if op == 'if':
            return f"If({self._tuple_to_generic_string(expr[1])}, {self._tuple_to_generic_string(expr[2])}, {self._tuple_to_generic_string(expr[3])})"

        # Añadir soporte para CALL en prefijo
        if op == 'call':
            func_name = expr[1]
            # args[0] suele ser el nombre de la función en closure
            raw_args = expr[2]
            if raw_args and str(raw_args[0]).replace("{", "").replace("}", "") == func_name:
                args = raw_args[1:]
            else:
                args = raw_args

            arg_strings = [self._tuple_to_generic_string(a) for a in args]
            return f"call({func_name}, {', '.join(arg_strings)})"

        # Operadores binarios/unarios estándar
        args = [self._tuple_to_generic_string(arg) for arg in expr[1:]]
        return f"{op}({', '.join(args)})"

    def _expr_to_readable_string(self, expr):
        if not isinstance(expr, tuple): return str(expr)
        op = expr[0]
        args = [self._expr_to_readable_string(e) for e in expr[1:]]
        if op == 'if': return f"If({args[0]}, {args[1]}, {args[2]})"
        op_map = {'+': '+', '-': '-', '*': '*', '/': '/', '%': '%', '==': '==', '!=': '!=', '<': '<', '>': '>', '<=': '<=', '>=': '>=', '&&': '&&', '||': '||'}
        if op in op_map: return f"({args[0]} {op_map[op]} {args[1]})"
        if op == 'neg': return f"-({args[0]})"

        # --- CORRECCIÓN: Filtrado de argumento de cierre ---
        if op == 'call':
            func_name = expr[1]
            raw_call_args = expr[2]

            # Heurística: Si hay argumentos y el primero parece ser el nombre de la función
            # (o una referencia a ella), lo saltamos. Esto corrige el error de aridad.
            # Verificamos si raw_call_args[0] (como string) es igual a func_name
            clean_args = raw_call_args
            if raw_call_args:
                first_arg_str = str(raw_call_args[0]).replace("{", "").replace("}", "")
                if first_arg_str == func_name:
                    clean_args = raw_call_args[1:]

            call_args_str = [self._expr_to_readable_string(a) for a in clean_args]
            return f"P_{func_name}({', '.join(call_args_str)})"

        return f"{op}({', '.join(args)})"

    # --- Exportaciones Base ---

    # ... dentro de EquationExporter ...

    def export_optimized(self):
        lines = []
        if self.function_relations:
            lines.append("--- [DEFINICIONES DE FUNCIONES RECURSIVAS] ---")
            for func_name, func_data in self.function_relations.items():
                params = func_data['params']
                body_expr = func_data['body']

                # CAMBIO: Usar formato GENÉRICO (Prefijo: +(a,b)) para evitar ambigüedad de parseo
                # Antes: readable_body = self._expr_to_readable_string(body_expr)

                # Usamos el método que ya tenías para formato interno:
                prefix_body = self._tuple_to_generic_string(body_expr)

                lines.append(f"P_{func_name}({', '.join(params)}) = {prefix_body}")
            lines.append("--- [FIN DEFINICIONES] ---\n")
        lines.append(self.export_optimized_for_interpreter())
        return "\n".join(lines)

    def export_optimized_for_interpreter(self):
        lines = []
        sorted_defs = sorted(self.sub_defs.items(), key=self._get_sort_key)
        for name, expr_tuple in sorted_defs:
            clean_name = name.replace("{", "").replace("}", "")
            lines.append(f"{clean_name} := {self._tuple_to_generic_string(expr_tuple)}")
        for var, expr_tuple in self.optimized_f.items():
            lhs = f"{var}[t+1]" if var in self.state_vars else var
            lines.append(f"{lhs} := {self._tuple_to_generic_string(expr_tuple)}")
        return "\n".join(lines)

    def export_single_polynomial(self, poly_system_list):
        if not poly_system_list: return "= 0"
        terms = [f"({eq.rsplit(' =', 1)[0]})^2" for eq in poly_system_list]
        return " + ".join(terms) + " = 0"

    def export_generator_formula(self, poly_system_list, target_var):
        if not poly_system_list: return "0"
        terms = [f"({eq.rsplit(' =', 1)[0]})^2" for eq in poly_system_list]
        p_poly = " + ".join(terms)
        return f"{target_var} * (1 - ({p_poly}))"

    def export_putnam_unified(self, poly_system_list):
        if not poly_system_list: return "1"
        terms = [f"({eq.rsplit(' =', 1)[0]})^2" for eq in poly_system_list]
        p_squared = " + ".join(terms)
        return f"1 - ({p_squared})"

    # =========================================================================
    # GENERACIÓN DE FÓRMULAS MATEMÁTICAS
    # =========================================================================

    def export_formula_symbolic(self, unified_poly_string_no_equals):
        return self._export_formula_logic(unified_poly_string_no_equals, operational=False)

    def export_formula_operational(self, unified_poly_string_no_equals):
        return self._export_formula_logic(unified_poly_string_no_equals, operational=True)

    def _export_formula_logic(self, poly_str, operational):
        output = []
        math_P = poly_str

        # 1. Limpieza base
        math_P = math_P.replace("**2", "^2")
        math_P = math_P.replace("*", " \\cdot ")

        # 2. Identificar TOKENS
        raw_tokens = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', math_P))
        reserved_keywords = {'div', 'mod', 'floor', 'if', 'call', 's', 't'}
        special_vars = {'target', 'result'}

        vars_to_process = []
        for token in raw_tokens:
            if token in reserved_keywords: continue
            if token in special_vars: continue
            vars_to_process.append(token)
        vars_to_process.sort(key=len, reverse=True)

        # 3. Variables E/S
        math_P = math_P.replace("result[t+1]", "R").replace("result", "R")
        math_P = math_P.replace("target[t+1]", "N").replace("target", "N")
        math_P = re.sub(r'\[t\+1\]', '', math_P)

        if operational:
            title = "FÓRMULA OPERACIONAL (Vectorial)"
            rename_map = {var: f"x_{{{i+1}}}" for i, var in enumerate(vars_to_process)}

            pattern = re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b')
            def replace_var(match):
                word = match.group(0)
                return rename_map.get(word, word)
            math_P = pattern.sub(replace_var, math_P)

            num_vars = len(vars_to_process)
            sum_notation = f"\\sum_{{\\mathbf{{x}} \\in \\mathbb{{N}}^{{{num_vars}}}}}"

            output.append(f"=== {title} ===")
            output.append(r"f(N) = \sum_{R=0}^{\infty} R \cdot \left\lfloor \frac{1}{1 + \mathcal{D}(N, R, \mathbf{x})} \right\rfloor")
            output.append(r"\mathcal{D}(N, R, \mathbf{x}) = " + sum_notation + r" \left( " + math_P + r" \right)")
            output.append(f"\nVector de estado: $\\mathbf{{x}} \\in \\mathbb{{R}}^{{{num_vars}}}$ (variables internas anonimizadas).")

        else:
            title = "FÓRMULA SIMBÓLICA (Estructural)"
            rename_map = {}
            for var in vars_to_process:
                if re.match(r'^e_\d+$', var): new_name = var.replace('e_', r'\epsilon_{') + '}'
                elif re.match(r'^C_\d+$', var): new_name = var.replace('C_', r'\mathcal{C}_{') + '}'
                elif var.startswith('P_'):
                    esc = var[2:].replace('_', r'\_')
                    new_name = rf"\Phi_{{\text{{{esc}}}}}"
                else:
                    esc = var.replace('_', r'\_')
                    new_name = rf"\mathit{{{esc}}}"
                rename_map[var] = new_name

            pattern = re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b')
            def replace_var(match):
                word = match.group(0)
                return rename_map.get(word, word)
            math_P = pattern.sub(replace_var, math_P)

            output.append(f"=== {title} ===")
            output.append(r"f(N) = \sum_{R=0}^{\infty} R \cdot \lfloor \frac{1}{1 + \mathcal{D}_{sym}} \rfloor")
            output.append(r"\mathcal{D}_{sym} = " + math_P)

        return "\n".join(output)

    # --- Sistema de Recurrencia ---
    def export_recurrence_system(self):
        """Sistema de recurrencia legible: la transición de estado
        `x(t+1) = F(x(t))` por cada variable de estado, precedida de las
        subexpresiones comunes (C_n) reutilizadas y de las funciones recursivas
        (P_f) que aparezcan. Reutiliza el render infijo del intérprete."""
        lines = [
            "=== SISTEMA DE RECURRENCIA ===",
            "Transición de estado x(t+1) = F(x(t)). Las C_n son subexpresiones",
            "comunes reutilizadas; las P_f, relaciones de funciones recursivas.",
            "",
        ]

        if self.function_relations:
            lines.append("# Funciones recursivas")
            for func_name, func_data in self.function_relations.items():
                params = ", ".join(func_data['params'])
                body = self._expr_to_readable_string(func_data['body'])
                lines.append(f"P_{func_name}({params}) = {body}")
            lines.append("")

        sorted_defs = sorted(self.sub_defs.items(), key=self._get_sort_key)
        if sorted_defs:
            lines.append("# Subexpresiones comunes")
            for name, expr_tuple in sorted_defs:
                clean = name.replace("{", "").replace("}", "")
                lines.append(f"{clean} = {self._expr_to_readable_string(expr_tuple)}")
            lines.append("")

        state_keys = [v for v in self.optimized_f if v in self.state_vars]
        aux_keys = [v for v in self.optimized_f
                    if v not in self.state_vars and v not in self.sub_defs]

        if state_keys:
            lines.append("# Recurrencias de estado")
            for var in sorted(state_keys):
                rhs = self._expr_to_readable_string(self.optimized_f[var])
                lines.append(f"{var}(t+1) = {rhs}")

        if aux_keys:
            lines.append("")
            lines.append("# Variables auxiliares")
            for var in sorted(aux_keys):
                rhs = self._expr_to_readable_string(self.optimized_f[var])
                lines.append(f"{var} = {rhs}")

        return "\n".join(lines)