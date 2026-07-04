import re

class LatexExporter:
    """
    Generador de informes final en LaTeX.
    Versión con rotura de líneas agresiva para evitar desbordamientos en ecuaciones masivas.
    """
    def __init__(self, unoptimized_f, optimized_f, sub_defs, state_vars, input_vars,
                 poly_system, single_poly_equation, poly_converter_info,
                 function_definitions=None, logical_func_defs=None,
                 math_formula_content_symbolic=None,
                 math_formula_content_operational=None,
                 recurrence_content=None,
                 generator_content_data=None):
        self.unoptimized_f = unoptimized_f
        self.optimized_f = optimized_f
        self.sub_defs = sub_defs
        self.state_vars = state_vars
        self.input_vars = input_vars
        self.poly_system = poly_system
        self.single_poly_equation = single_poly_equation
        self.poly_converter_info = poly_converter_info
        self.function_definitions = function_definitions or []
        self.logical_func_defs = logical_func_defs or []
        self.math_formula_content_symbolic = math_formula_content_symbolic
        self.math_formula_content_operational = math_formula_content_operational
        self.recurrence_content = recurrence_content
        self.generator_content_data = generator_content_data or []

    def export_latex(self):
        print("  [Exporter] Ensamblando informe final en LaTeX (Modo Seguro de Márgenes)...")
        header = self._build_header()
        intro = self._build_intro()
        part1 = self._build_transition_function_section()
        part2 = self._build_polynomial_conversion_section()
        part3 = self._build_generator_section()
        part4 = self._build_mathematical_formula_section()
        part5 = self._build_recurrence_section()
        footer = r"\end{document}"
        return header + intro + part1 + part2 + part3 + part4 + part5 + footer

    def _escape_var_for_text(self, var_name):
        if not var_name: return "ninguna"
        s = str(var_name).replace('_', r'\_')
        return f"\\texttt{{{s}}}"

    def _build_header(self):
        return r"""
\documentclass[10pt, a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{geometry}
\geometry{a4paper, margin=0.8in}
\usepackage{amssymb}
\usepackage{breqn}
\usepackage{booktabs}
\usepackage{url}

% Ajustes para permitir ecuaciones gigantes
\allowdisplaybreaks
\setlength{\jot}{8pt}

\title{Análisis Matemático de Algoritmo \\ \large Generado por Project Diophantus}
\author{}
\date{\today}
"""

    def _build_intro(self):
        return f"""
\\begin{{document}}
\\maketitle
\\section*{{Resumen Ejecutivo}}
Este documento presenta la traducción completa de un algoritmo computacional a tres formas matemáticas distintas.
Las ecuaciones resultantes, debido a la complejidad logarítmica del algoritmo original (Miller-Rabin), son extensas pero polinomialmente acotadas.
"""

    def _build_transition_function_section(self):
        # Usamos un bloque align* con saltos forzados
        content = "\\part{Función de Transición}\n"
        content += "\\begin{align*}\n"
        for var in sorted(self.state_vars):
            expr_tuple = self.unoptimized_f.get(var, var)
            lhs = f"{self._format_var(var)}[t+1] &="
            rhs = self._format_expanded_latex(expr_tuple, self.sub_defs)
            # Forzar break si es muy largo
            if len(rhs) > 100:
                rhs = f"\\parbox[t]{{0.8\\linewidth}}{{\\raggedright ${rhs}$}}"
            content += f"{lhs} {rhs} \\\\\n"
        content += "\\end{align*}"
        return content

    def _build_polynomial_conversion_section(self):
        # Aquí usamos el formateador agresivo para el polinomio gigante
        single_poly_str = self._format_single_poly(self.single_poly_equation, line_length=80)
        return f"\\part{{Conversión a Polinomio}}\n\\subsection*{{Ecuación Unificada P=0}}\n\\begin{{align*}}\n{single_poly_str}\n\\end{{align*}}"

    def _build_generator_section(self):
        poly_body = self._format_single_poly(self.single_poly_equation, force_no_equals=True, line_length=80)
        return f"\\part{{Fórmulas Generadoras}}\n\\begin{{small}}\n\\begin{{align*}}\nG &= 1 - ({poly_body}) \\\\\n\\end{{align*}}\n\\end{{small}}"

    def _build_mathematical_formula_section(self):
        content = "\\part{Fórmulas Matemáticas (Estilo Willans)}\n"
        if self.math_formula_content_symbolic:
            content += "\\section{Representación Simbólica}\n" + self._process_math_content(self.math_formula_content_symbolic)
        if self.math_formula_content_operational:
            content += "\\newpage\n\\section{Representación Operacional}\n" + self._process_math_content(self.math_formula_content_operational)
        return content

    def _build_recurrence_section(self):
        if not self.recurrence_content: return ""
        content = "\\part{Sistema Dinámico (Recurrencia Infinita)}\n"

        lines = self.recurrence_content.split('\n')
        latex_blocks = []

        for line in lines:
            if "===" in line or not line.strip(): continue

            # Detectar ecuaciones
            if " = " in line:
                parts = line.split(" = ", 1)
                if len(parts) == 2:
                    lhs = parts[0].strip()
                    rhs = parts[1].strip().replace("*", " \\cdot ")
                    # Romper RHS agresivamente para recurrencia
                    rhs_broken = self._break_long_latex_string(rhs, 90)
                    latex_blocks.append(f"{lhs} &= {rhs_broken} \\\\")
            elif line.startswith("R ="):
                 latex_blocks.append(line + r"\\")
            elif line.startswith("---"):
                 latex_blocks.append(r"\intertext{" + line.replace("-","").strip() + r"}")
            else:
                 latex_blocks.append(r"\text{" + line + r"} \\")

        return content + "\\begin{align*}\n" + "\n".join(latex_blocks) + "\n\\end{align*}"

    def _process_math_content(self, raw_content):
        parts = raw_content.split('\n')
        latex_blocks = []
        current_block = []
        for line in parts:
            if "===" in line or not line.strip(): continue
            if line.startswith("Donde") or line.startswith("Nota") or line.startswith("Vector") or line.startswith("Caract"):
                if current_block:
                    latex_blocks.append(r"\begin{dmath*}" + "\n" + " \\\\\n".join(current_block) + "\n" + r"\end{dmath*}")
                    current_block = []
                latex_blocks.append(line + r"\\")
            else:
                clean_line = self._sanitize_math_formula(line)
                # Aplicar wrapping manual
                clean_line = self._break_long_latex_string(clean_line, 100)
                current_block.append(clean_line)
        if current_block:
             latex_blocks.append(r"\begin{dmath*}" + "\n" + " \\\\\n".join(current_block) + "\n" + r"\end{dmath*}")
        return "\n".join(latex_blocks)

    def _sanitize_math_formula(self, line):
        line = re.sub(r'(?<!\\)\bfloor\b', r'\\lfloor', line)
        line = re.sub(r'(?<!\\)\bSUM\b', r'\\sum', line)
        line = re.sub(r'(?<!\\)\bPROD\b', r'\\prod', line)
        if " = " in line and "&" not in line:
            parts = line.split(" = ", 1)
            return f"{parts[0]} &= {parts[1]}"
        return line

    def _break_long_latex_string(self, s, chunk_size):
        """Inserta saltos de línea manuales en cadenas LaTeX muy largas."""
        if len(s) < chunk_size: return s
        # Intentar romper en operadores + o -
        parts = []
        current = ""
        balance = 0
        for char in s:
            current += char
            if char == '(': balance += 1
            if char == ')': balance -= 1

            if len(current) > chunk_size and balance == 0 and char in ['+', '-']:
                parts.append(current)
                current = ""
        parts.append(current)
        return " \\\\\n& ".join(parts)

    def _format_poly_expression(self, expr_str):
        s = expr_str.replace('*', r' \cdot ')
        s = re.sub(r'([a-zA-Z0-9_]+)\[t\+1\]', r'\1[t+1]', s)
        s = re.sub(r'([Ce])_(\d+)', r'\1_{\2}', s)
        s = re.sub(r'\^2', r'^{2}', s)
        return s

    def _format_single_poly(self, line, force_no_equals=False, line_length=100):
        clean_line = line.split(' = ')[0] if ' = ' in line else line
        terms = clean_line.split(' + ')
        formatted_terms = [self._format_poly_expression(term) for term in terms]

        output_lines = []
        current_line = ""

        for term in formatted_terms:
            # Añadir separador
            term_with_sep = (" + " if current_line else "") + term

            if len(current_line) + len(term_with_sep) > line_length:
                # Si el término es monstruoso, lo rompemos también
                if len(term) > line_length:
                     # Caso recursivo o forzado
                     output_lines.append(current_line + " +")
                     current_line = term
                else:
                    output_lines.append(current_line)
                    current_line = "+ " + term
            else:
                current_line += term_with_sep

        if current_line: output_lines.append(current_line)

        body = (" \\\\\n& ").join(output_lines)
        return body if force_no_equals else f"& {body} = 0"

    def _format_var(self, v): return str(v).replace('_', r'\_')
    def _format_tuple_to_latex(self, expr): return str(expr)
    def _format_expanded_latex(self, expr, sub): return str(expr)