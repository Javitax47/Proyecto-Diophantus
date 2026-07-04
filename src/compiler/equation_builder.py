import re

class EquationExporter:
    """
    Construye y exporta la Ecuación Maestra P=0 en dos formatos.

    Incluye métodos para calcular de forma segura el tamaño de la salida
    antes de generar el contenido completo en la memoria, evitando así
    errores de tipo 'MemoryError' con programas de entrada complejos.
    """
    def __init__(self, unoptimized_f, optimized_f, sub_defs):
        """
        Inicializa el exportador con los AST de tuplas necesarios.

        Args:
            unoptimized_f (dict): La F-Function sin optimizar.
            optimized_f (dict): La F-Function optimizada usando C_n.
            sub_defs (dict): Las definiciones de las subexpresiones C_n.
        """
        self.unoptimized_f = unoptimized_f
        self.optimized_f = optimized_f
        self.sub_defs = sub_defs

    # --- Métodos Públicos ---

    def get_unoptimized_size_estimate(self):
        """
        Calcula el tamaño final en bytes (UTF-8) de la ecuación no optimizada
        de forma segura, sin construir la cadena completa en memoria.

        Returns:
            int: El tamaño estimado en bytes del archivo final.
        """
        total_size = 0
        sorted_vars = sorted(self.unoptimized_f.keys())
        num_terms = len(sorted_vars)

        for i, var in enumerate(sorted_vars):
            expr_tuple = self.unoptimized_f.get(var, var)

            # Formato del término: (var[t+1] - (expr))^2
            lhs_size = len(f"{var}[t+1]".encode('utf-8'))
            expr_size = self._calculate_poly_string_size(expr_tuple, expand=True)

            # Overhead de la plantilla: len( '() - ()^2' ) = 8
            term_size = lhs_size + expr_size + 8
            total_size += term_size

            # Añadir el tamaño de " + \n" entre términos
            if i < num_terms - 1:
                total_size += len(" + \n".encode('utf-8'))

        # Añadir el tamaño de " = 0" al final
        total_size += len(" = 0".encode('utf-8'))
        return total_size

    def export_unoptimized(self):
        """
        Construye la ecuación P=0 en su forma completamente expandida.
        Este método consume memoria y solo debe llamarse tras verificar el tamaño.

        Returns:
            str: La cadena de texto de la ecuación masiva.
        """
        terms = []
        for var in sorted(self.unoptimized_f.keys()):
            expr_tuple = self.unoptimized_f.get(var, var)
            lhs = f"{var}[t+1]"
            rhs = self._expr_to_poly_string(expr_tuple, expand=True)
            terms.append(f"({lhs} - ({rhs}))^2")

        return " + \n".join(terms) + " = 0"

    def export_optimized(self):
        """
        Construye un sistema de ecuaciones legible usando las subexpresiones C_n.

        Returns:
            str: Una cadena de texto que contiene las definiciones de C_n y
                 la ecuación maestra optimizada.
        """
        # 1. Sección de definiciones de C_n
        defs_section = []
        if self.sub_defs:
            # Usamos un nombre más descriptivo para el usuario final
            defs_section.append("--- [DEFINICIONES DE SUBEXPRESIONES COMUNES (C_n)] ---")
            # Ordenar por el número en C_n para una salida consistente
            sorted_defs = sorted(self.sub_defs.items(), key=lambda item: int(re.search(r'\d+', item[0]).group()))
            for name, expr_tuple in sorted_defs:
                # El nombre de la subexpresión no necesita los {} en el .txt
                clean_name = name.replace("{", "").replace("}", "")
                rhs = self._expr_to_poly_string(expr_tuple, expand=False)
                defs_section.append(f"{clean_name} = {rhs}")

        # 2. Ecuación maestra P=0 que utiliza las C_n
        main_eq_section = ["\n--- [ECUACIÓN MAESTRA (OPTIMIZADA)] ---"]
        terms = []
        for var in sorted(self.optimized_f.keys()):
            expr_tuple = self.optimized_f.get(var, var)
            lhs = f"{var}[t+1]"
            rhs = self._expr_to_poly_string(expr_tuple, expand=False)
            terms.append(f"({lhs} - ({rhs}))^2")

        main_eq_section.append(" + \n".join(terms) + " = 0")

        return "\n".join(defs_section) + "\n" + "\n".join(main_eq_section)

    # --- Funciones de Ayuda Internas ---

    def _expr_to_poly_string(self, expr, expand):
        """Convierte recursivamente una tupla de AST a un string de texto plano."""
        if expand and isinstance(expr, str) and expr in self.sub_defs:
            return self._expr_to_poly_string(self.sub_defs[expr], expand)

        if not isinstance(expr, tuple):
            # Limpiar C_{n} a C_n para el archivo de texto
            if isinstance(expr, str):
                return expr.replace("{", "").replace("}", "")
            return str(expr) if expr is not None else "0"

        op = expr[0]
        args = [self._expr_to_poly_string(e, expand) for e in expr[1:]]

        if op == 'if': return f"(({args[0]}) * ({args[1]}) + (1 - {args[0]}) * ({args[2]}))"
        if op == 'neg': return f"(-{args[0]})"
        if op in ('+', '-', '*', '/'): return f"({args[0]} {op} {args[1]})"
        if op == '&&': return f"({args[0]} * {args[1]})"
        if op == '||': return f"({args[0]} + {args[1]} - {args[0]} * {args[1]})"

        op_map = {'==': 'EQ', '!=': 'NEQ', '>': 'GT', '<': 'LT', '>=': 'GTE', '<=': 'LTE'}
        if op in op_map:
            return f"{op_map[op]}({args[0]}, {args[1]})"

        return f"UNKNOWN_OP({op}, {', '.join(args)})"

    def _calculate_poly_string_size(self, expr, expand):
        """
        Recorre el AST y suma las longitudes de los componentes sin concatenar strings.
        La lógica debe reflejar exactamente la de _expr_to_poly_string.
        """
        if expand and isinstance(expr, str) and expr in self.sub_defs:
            return self._calculate_poly_string_size(self.sub_defs[expr], expand)

        if not isinstance(expr, tuple):
            base_str = str(expr) if expr is not None else "0"
            if isinstance(expr, str): # Quitar {} de C_n para el cálculo
                base_str = base_str.replace("{", "").replace("}", "")
            return len(base_str.encode('utf-8'))

        op = expr[0]
        arg_sizes = [self._calculate_poly_string_size(e, expand) for e in expr[1:]]

        if op == 'if': # "(({s0}) * ({s1}) + (1 - {s0}) * ({s2}))"
            return 8 + arg_sizes[0] + 5 + arg_sizes[1] + 8 + arg_sizes[0] + 5 + arg_sizes[2] + 2
        if op == 'neg': # "(-{s0})"
            return 3 + arg_sizes[0]
        if op in ('+', '-', '*', '/'): # "({s0} op {s1})"
            return arg_sizes[0] + arg_sizes[1] + 6
        if op == '&&': # "({s0} * {s1})"
            return arg_sizes[0] + arg_sizes[1] + 7
        if op == '||': # "({s0} + {s1} - {s0} * {s1})"
            return arg_sizes[0] * 2 + arg_sizes[1] * 2 + 13

        op_map = {'==': 'EQ', '!=': 'NEQ', '>': 'GT', '<': 'LT', '>=': 'GTE', '<=': 'LTE'}
        if op in op_map: # "OP(s0, s1)"
            return len(op_map[op]) + 1 + arg_sizes[0] + 2 + arg_sizes[1] + 1

        return len(f"UNKNOWN_OP({op})".encode('utf-8')) # Fallback