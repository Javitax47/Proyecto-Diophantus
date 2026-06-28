import os
import re
import time

def _escape_tex(text):
    """
    Escapa los caracteres especiales de LaTeX en un string de TEXTO PLANO.
    NO usar para ecuaciones matemáticas.
    """
    if not text:
        return ""
    text = str(text)
    text = text.replace('_', r'\_') 
    return text.replace('%', r'\%') \
               .replace('$', r'\$') \
               .replace('#', r'\#') \
               .replace('&', r'\&') \
               .replace('{', r'\{') \
               .replace('}', r'\}') \
               .replace('^', r'\^') \
               .replace('~', r'\~')

class VerificationExporter:
    """
    Construye un informe .tex basado en los resultados de
    una ejecución de verify_state.py.
    """

    def __init__(self, c_file, bug_condition, poly_system, z3_result, z3_model, time_taken):
        self.c_file = c_file
        self.bug_condition = bug_condition
        self.poly_system = poly_system
        self.z3_result = str(z3_result)
        self.z3_model = z3_model
        self.time_taken = time_taken

    def export(self):
        """Genera el contenido completo del archivo .tex."""
        content = []
        content.append(self._format_header())
        content.append(self._format_summary())
        
        if self.z3_result == "sat" and self.z3_model:
            content.append(self._format_model())
        
        content.append(self._format_equations())
        content.append("\n\\end{document}\n")
        return "\n".join(content)

    def _format_header(self):
        """Crea el preámbulo y el título del documento LaTeX."""
        filename_only = os.path.basename(self.c_file)
        escaped_filename = _escape_tex(filename_only)

        return f"""
\\documentclass[a4paper, 10pt]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{geometry}}
\\geometry{{a4paper, margin=1in}}
\\usepackage{{amsmath}}
\\usepackage{{amsfonts}}
\\usepackage{{array}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{times}}
\\usepackage{{courier}}

% Permite que las ecuaciones largas en align* se rompan entre páginas
\\allowdisplaybreaks

\\title{{Informe de Verificación Formal (Project Diophantus)}}
\\author{{Archivo Verificado: {escaped_filename}}}
\\date{{{time.strftime('%Y-%m-%d %H:%M:%S')}}}

\\begin{{document}}

\\maketitle
"""

    def _format_summary(self):
        """Crea la sección de resumen de la verificación."""
        if self.z3_result == "sat":
            result_text = "\\textbf{{\\Huge {{ESTADO POSIBLE (SAT)}}}}"
            result_desc = "Z3 ha encontrado un conjunto de valores que satisfacen todas las ecuaciones del programa Y la condición del bug."
        elif self.z3_result == "unsat":
            result_text = "\\textbf{{\\Huge {{ESTADO IMPOSIBLE (UNSAT)}}}}"
            result_desc = "Z3 ha demostrado matemáticamente que la condición del bug es INCOMPATIBLE con las ecuaciones del programa."
        else:
            result_text = f"\\textbf{{\\Huge {self.z3_result}}}"
            result_desc = "El solucionador no pudo determinar un resultado."

        return f"""
\\section*{{Resumen de la Verificación}}

\\subsection*{{Condición del Bug Verificada}}
Se ha intentado encontrar un estado del sistema que cumpla la siguiente condición:
\\begin{{verbatim}}
{self.bug_condition}
\\end{{verbatim}}

\\subsection*{{Resultado}}
\\begin{{center}}
    {result_text}
\\end{{center}}

{result_desc}

\\subsection*{{Estadísticas}}
\\begin{{itemize}}
    \\item \\textbf{{Tiempo de resolución:}} {self.time_taken:.4f} segundos
    \\item \\textbf{{Ecuaciones analizadas:}} {len(self.poly_system)}
\\end{{itemize}}
"""

    def _format_model(self):
        """Crea la sección que muestra el modelo encontrado por Z3 (si existe)."""
        if not self.z3_model or not isinstance(self.z3_model, list):
            if isinstance(self.z3_model, dict):
                 # Fallback para modo INVARIANT (diccionario simple)
                 return self._format_model_dict(self.z3_model)
            return ""

        all_keys = set()
        for frame in self.z3_model:
            all_keys.update(frame.keys())
        
        # Filtrar y ordenar claves
        state_keys = sorted([k for k in all_keys if 'I_' not in k and k != 'x_t1' and k != 'x_t0'])
        input_keys = sorted([k for k in all_keys if 'I_' in k])
        
        col_names = ["t"] + state_keys + input_keys
        col_format = "|c|" + "c" * len(state_keys) + "|" + "c" * len(input_keys)
        
        output = [
            "\\subsection*{Camino de Secuencia que Altera el Invariante}",
            "Z3 ha proporcionado la siguiente secuencia de estados y entradas:",
            "\\begin{center}",
            "\\tiny",
            f"\\begin{{tabular}}{{{col_format}}}",
            "\\hline"
        ]
        
        header_row = " & ".join([_escape_tex(k.replace("I_", "In ")) for k in col_names]) + " \\\\ \\hline"
        output.append(header_row)
        
        for t, frame in enumerate(self.z3_model):
            row_data = [str(t)]
            for key in state_keys:
                row_data.append(_escape_tex(str(frame.get(key, '-'))))
            for key in input_keys:
                row_data.append(_escape_tex(str(frame.get(key, '-'))))
            output.append(" & ".join(row_data) + " \\\\ \\hline")
        
        output.extend([
            "\\end{tabular}",
            "\\end{center}"
        ])

        return "\n".join(output)

    def _format_model_dict(self, model_dict):
        output = [
            "\\subsection*{Estado que Altera el Invariante}",
            "Z3 ha encontrado la siguiente asignación de variables:",
            "\\begin{itemize}"
        ]
        for k, v in sorted(model_dict.items()):
            output.append(f"    \\item \\textbf{{{_escape_tex(k)}}}: {_escape_tex(v)}")
        output.append("\\end{itemize}")
        return "\n".join(output)

    def _latexify_equation(self, eq_str):
        """
        Transforma una ecuación en string crudo a formato LaTeX matemático.
        CORRECCIÓN: Agrupa subíndices numéricos en llaves (C_16 -> C_{16}).
        """
        # 1. Reemplazar multiplicación '*' por '\cdot'
        eq_str = eq_str.replace('*', r' \cdot ')
        
        # 2. Transformar accesos a array: b[t+1] -> b_{t+1}
        eq_str = re.sub(r'(\w+)\[([^\]]+)\]', r'\1_{\2}', eq_str)
        
        # 3. CORRECCIÓN: Asegurar que C_n y e_n tengan llaves en el subíndice
        # Busca C_ o e_ seguido de dígitos y los envuelve en {}
        eq_str = re.sub(r'([Ce])_(\d+)', r'\1_{\2}', eq_str)
        
        # 4. Alinear en el igual
        eq_str = eq_str.replace('=', '&=', 1)
        
        return eq_str

    def _format_equations(self):
        """Crea la sección que lista todas las ecuaciones polinómicas."""
        latex_eqs = [self._latexify_equation(eq) for eq in self.poly_system]
        eqs_block = "\\\\ \n".join(latex_eqs)
        
        return f"""
\\section*{{Sistema de Ecuaciones Polinómicas Verificado}}
El solucionador Z3 recibió el siguiente sistema de ecuaciones:
\\begin{{small}}
\\begin{{align*}}
{eqs_block}
\\end{{align*}}
\\end{{small}}
"""