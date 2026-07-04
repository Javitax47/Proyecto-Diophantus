import re

from src.compiler.generator import OVERFLOW_MARKER

class PolynomialConverter:
    """
    Toma un AST de tuplas "aritmetizado" y lo convierte en un sistema
    de ecuaciones.
    """
    def __init__(self, optimized_f, sub_defs, state_vars, function_relations,
                 bit_width=32):
        self.optimized_f = optimized_f
        self.sub_defs = sub_defs
        self.state_vars = set(state_vars)
        self.function_relations = function_relations
        # Ancho en bits para la aritmetización de operadores bit a bit.
        self.bit_width = bit_width
        self.existential_vars_count = 0
        self.polynomial_system = []
        self.mode = "PURE" # Default

        # Anclaje de `overflow`: cada expresión convertida deja en `_ind_of` el
        # indicador (string {0,1}) de si la rama seleccionada usa un valor
        # truncado por presupuesto de recursión. Si alguna raíz puede valer 1 se
        # ancla `overflow = 0`, dejando el sistema sin solución para las trazas
        # que exceden el presupuesto en vez de con una solución incorrecta.
        self._ind_of = {}
        self._overflow_terms = []
        self._saw_overflow = False

    def _new_e_var(self):
        var_name = f"e_{self.existential_vars_count}"
        self.existential_vars_count += 1
        return var_name

    def _sum_of_four_squares(self):
        """Devuelve un string `s1*s1 + s2*s2 + s3*s3 + s4*s4` con cuatro nuevas
        variables existenciales. Por el teorema de Lagrange, ese valor recorre
        exactamente los enteros >= 0, de modo que igualar una expresión a esta
        suma equivale a imponer que la expresión es no negativa."""
        s = [self._new_e_var() for _ in range(4)]
        return " + ".join(f"{v}*{v}" for v in s)

    def _emit_nonneg_four_squares(self, expr):
        """Impone `expr >= 0` de forma diofántica: `expr = s1^2+...+s4^2`.
        Usa multiplicación explícita (`s*s`) en lugar de potencia para ser
        inequívoco en todos los consumidores (SymPy, Z3 y la VM), dado que en
        este sistema `^` denota XOR bit a bit en unos contextos y potencia en
        otros."""
        self.polynomial_system.append(f"({expr}) - ({self._sum_of_four_squares()}) = 0")

    def _reify_ge0(self, target, d_expr):
        """Reifica el predicado `d_expr >= 0` en una variable booleana `target`.
        Tras estas ecuaciones, toda solución entera cumple `target in {0,1}` y
        `target = 1  <=>  d_expr >= 0`:

            target*(1 - target) = 0                      (target booleano)
            d_expr = target*s1 - (1 - target)*(1 + s2)    (s1, s2 >= 0)

        Si target=1 entonces d_expr = s1 >= 0; si target=0 entonces
        d_expr = -(1 + s2) <= -1. La equivalencia es exacta y polinómica."""
        self.polynomial_system.append(f"{target}*(1 - {target}) = 0")
        s1 = self._sum_of_four_squares()
        s2 = self._sum_of_four_squares()
        self.polynomial_system.append(
            f"({d_expr}) - ({target}*({s1}) - (1 - {target})*(1 + {s2})) = 0"
        )

    def _emit_boolean(self, var):
        """Impone `var in {0,1}` (booleanización)."""
        self.polynomial_system.append(f"{var}*(1 - {var}) = 0")

    def _pow2_expr(self, exp_operand):
        """Devuelve un string polinómico para `2**exp_operand`, válido para un
        exponente en [0, 2^nbits) con `nbits = ceil(log2(bit_width))` (rango de
        desplazamientos legales). Descompone el exponente en bits k_j y usa la
        identidad `2^(Σ 2^j·k_j) = Π_j ((2^(2^j) - 1)·k_j + 1)` (cada bit activo
        multiplica por 2^(2^j)). Emite las restricciones booleanas y la
        descomposición del exponente; devuelve el producto de factores."""
        nbits = max(1, (self.bit_width - 1).bit_length())
        bits = [self._new_e_var() for _ in range(nbits)]
        for kj in bits:
            self._emit_boolean(kj)
        decomp = " + ".join(f"{(1 << j)}*{bits[j]}" for j in range(nbits))
        self.polynomial_system.append(f"({exp_operand}) - ({decomp}) = 0")
        return " * ".join(f"(({(1 << (1 << j)) - 1})*{bits[j]} + 1)" for j in range(nbits))

    def _bit_decompose(self, value_expr):
        """Descompone `value_expr` en `self.bit_width` bits {0,1} tales que
        `value_expr = Σ 2^i·b_i`. Devuelve la lista de variables de bit. La
        ecuación de descomposición acota implícitamente el valor a [0, 2^W − 1],
        de modo que se asume operando sin signo (coherente con el tratamiento
        unsigned —UDiv/URem— del modo LOGICAL)."""
        bits = [self._new_e_var() for _ in range(self.bit_width)]
        for b in bits:
            self._emit_boolean(b)
        terms = " + ".join(f"{(1 << i)}*{bits[i]}" for i in range(self.bit_width))
        self.polynomial_system.append(f"({value_expr}) - ({terms}) = 0")
        return bits

    def _or(self, x, y):
        """OR booleano de dos indicadores {0,1} (`x + y - x*y`), con
        cortocircuito sobre los literales 0 y 1 para no emitir ecuaciones cuando
        no hace falta."""
        if x == "0": return y
        if y == "0": return x
        if x == "1" or y == "1": return "1"
        iv = self._new_e_var()
        self.polynomial_system.append(f"{iv} - ({x} + {y} - ({x})*({y})) = 0")
        return iv

    def _or_all(self, inds):
        acc = "0"
        for i in inds:
            acc = self._or(acc, i)
        return acc

    def _args_ind(self, arg_vars):
        """Indicador de truncamiento de una operación cuyos operandos se usan
        todos: el OR de los indicadores de los operandos."""
        return self._or_all([self._ind_of.get(a, "0") for a in arg_vars])

    def _select(self, cond, a, b):
        """Indicador seleccionado por una condición {0,1}: el peso phi de una
        rama `if`. Devuelve `cond*a + (1-cond)*b` (PURE) o `If(cond!=0,a,b)`
        (LOGICAL); cortocircuita a 0 cuando ambas ramas están limpias."""
        if a == "0" and b == "0":
            return "0"
        if self.mode == "LOGICAL":
            expr = f"If({cond} != 0, {a}, {b})"
        else:
            expr = f"({cond})*({a}) + (1 - ({cond}))*({b})"
        iv = self._new_e_var()
        self.polynomial_system.append(f"{iv} - ({expr}) = 0")
        return iv

    def convert(self, mode="PURE"):
        self.mode = mode
        self.polynomial_system = []
        self.existential_vars_count = 0
        self._ind_of = {}
        self._overflow_terms = []
        self._saw_overflow = False
        function_definitions = []

        print(f"  [PolyConverter] Iniciando conversión ({self.mode})...")

        if self.function_relations:
            for func_name, func_data in self.function_relations.items():
                body_expr = func_data['body']
                start_idx = len(self.polynomial_system)
                self._convert_expr_to_poly('RET', body_expr)
                func_eqs = self.polynomial_system[start_idx:]
                self.polynomial_system = self.polynomial_system[:start_idx]
                function_definitions.append({'name': func_name, 'equations': func_eqs})

        sorted_defs = sorted(self.sub_defs.items(), key=lambda item: int(re.search(r'\d+', item[0]).group()))
        for name, expr_tuple in sorted_defs:
            clean_name = name.replace("{", "").replace("}", "")
            self._convert_expr_to_poly(clean_name, expr_tuple)
            self._collect_overflow(clean_name)

        for var in sorted(self.optimized_f.keys()):
            if var in self.sub_defs or var not in self.state_vars: continue
            lhs = f"{var}[t+1]"
            self._convert_expr_to_poly(lhs, self.optimized_f[var])
            self._collect_overflow(lhs)

        for var in sorted(self.optimized_f.keys()):
            if var in self.sub_defs or var in self.state_vars: continue
            self._convert_expr_to_poly(var, self.optimized_f[var])
            self._collect_overflow(var)

        self._emit_overflow_anchor()

        print(f"  [PolyConverter] {len(self.polynomial_system)} ecuaciones generadas.")
        return self.polynomial_system, function_definitions

    def _collect_overflow(self, target):
        ind = self._ind_of.get(target, "0")
        if ind != "0":
            self._overflow_terms.append(ind)

    def _emit_overflow_anchor(self):
        """Si alguna raíz depende de un valor truncado, define `overflow` como el
        OR de los indicadores de raíz y lo ancla a 0. Para una traza dentro del
        presupuesto todos los indicadores valen 0 (anclaje satisfecho, valor
        correcto); para una traza que lo excede el indicador vale 1 y el anclaje
        `overflow = 0` vuelve el sistema insatisfacible."""
        if not self._saw_overflow:
            return
        acc = self._or_all(self._overflow_terms)
        self.polynomial_system.append(f"overflow - ({acc}) = 0")
        self.polynomial_system.append("overflow = 0")

    def _convert_expr_to_poly(self, target_var, expr):
        if not isinstance(expr, tuple):
            # Las llaves de los nombres CSE (C_{n}, delimitador anticolisión del
            # optimizer) deben quitarse para que la referencia coincida con su
            # definición ya saneada (C_n) y sea un identificador válido en SymPy.
            clean = str(expr).replace("{", "").replace("}", "")
            if clean == OVERFLOW_MARKER:
                if self.mode == "LOGICAL":
                    # El modo LOGICAL conserva la semántica acotada de un
                    # solucionador BMC: el valor truncado es 0.
                    self.polynomial_system.append(f"{target_var} - (0) = 0")
                    self._ind_of[target_var] = "0"
                else:
                    # El valor truncado queda como variable libre y su indicador
                    # de truncamiento a 1; el anclaje de `overflow` lo neutraliza.
                    self.polynomial_system.append(f"{target_var} - ({OVERFLOW_MARKER}) = 0")
                    self._ind_of[target_var] = "1"
                    self._saw_overflow = True
                return
            self.polynomial_system.append(f"{target_var} - ({clean}) = 0")
            self._ind_of[target_var] = "0"
            return

        op = expr[0]

        if op == 'call':
            func_name = expr[1]
            args = expr[2]
            resolved_args = [self._resolve_operand(arg) for arg in args]
            args_str = ", ".join(resolved_args + [target_var])
            self.polynomial_system.append(f"P_{func_name}({func_name}, {args_str}) = 0")
            self._ind_of[target_var] = self._args_ind(resolved_args)
            return

        arg_vars = [self._resolve_operand(arg) for arg in expr[1:]]

        # --- MODO LÓGICO (Z3 / CRYPTO) ---
        if self.mode == "LOGICAL":
            rhs = ""
            # Aritmética Básica y Bitwise
            if op in ('+', '-', '*', '^', '&', '|', '<<', '>>'):
                rhs = f"({arg_vars[0]} {op} {arg_vars[1]})"
            elif op == 'neg': rhs = f"(-{arg_vars[0]})"
            elif op == '~': rhs = f"(~{arg_vars[0]})"
            elif op == 'if': rhs = f"If({arg_vars[0]} != 0, {arg_vars[1]}, {arg_vars[2]})"
            elif op == '==': rhs = f"If({arg_vars[0]} == {arg_vars[1]}, 1, 0)"
            elif op == '!=': rhs = f"If({arg_vars[0]} != {arg_vars[1]}, 1, 0)"
            elif op == '&&': rhs = f"If(And({arg_vars[0]} != 0, {arg_vars[1]} != 0), 1, 0)"
            elif op == '||': rhs = f"If(Or({arg_vars[0]} != 0, {arg_vars[1]} != 0), 1, 0)"
            elif op == '/':
                 # Z3 Python API uses UDiv for unsigned division
                 rhs = f"UDiv({arg_vars[0]}, {arg_vars[1]})"
            elif op == '%':
                 rhs = f"URem({arg_vars[0]}, {arg_vars[1]})"

            # Comparadores unsigned: funciones UGT, ULT, UGE, ULE de Z3, que el
            # CryptoSolver inyecta en el contexto de evaluación.
            elif op == '>':  rhs = f"If(UGT({arg_vars[0]}, {arg_vars[1]}), 1, 0)"
            elif op == '<':  rhs = f"If(ULT({arg_vars[0]}, {arg_vars[1]}), 1, 0)"
            elif op == '>=': rhs = f"If(UGE({arg_vars[0]}, {arg_vars[1]}), 1, 0)"
            elif op == '<=': rhs = f"If(ULE({arg_vars[0]}, {arg_vars[1]}), 1, 0)"

            else:
                rhs = f"({arg_vars[0]} {op} {arg_vars[1]})"

            self.polynomial_system.append(f"{target_var} - ({rhs}) = 0")
            self._ind_of[target_var] = "0"
            return

        # --- MODO PURO (MATEMÁTICO) ---
        if op in ('+', '-', '*'):
            self.polynomial_system.append(f"{target_var} - ({arg_vars[0]} {op} {arg_vars[1]}) = 0")
            self._ind_of[target_var] = self._args_ind(arg_vars)
        elif op in ('&', '|', '^'):
            # Operadores bit a bit: se descomponen ambos operandos en bits y se
            # combina bit a bit con polinomios: AND -> a_i·b_i,
            # OR -> a_i+b_i−a_i·b_i, XOR -> a_i+b_i−2a_i·b_i.
            a, b = arg_vars
            abits = self._bit_decompose(a)
            bbits = self._bit_decompose(b)
            if op == '&':
                per_bit = lambda ai, bi: f"{ai}*{bi}"
            elif op == '|':
                per_bit = lambda ai, bi: f"({ai} + {bi} - {ai}*{bi})"
            else:  # '^'
                per_bit = lambda ai, bi: f"({ai} + {bi} - 2*{ai}*{bi})"
            terms = " + ".join(
                f"{(1 << i)}*({per_bit(abits[i], bbits[i])})" for i in range(self.bit_width)
            )
            self.polynomial_system.append(f"{target_var} - ({terms}) = 0")
            self._ind_of[target_var] = self._args_ind(arg_vars)
        elif op in ('<<', '>>'):
            # Desplazamientos: a<<k = a·2^k; a>>k = floor(a / 2^k), reusando la
            # división euclídea acotada. El factor 2^k es constante si k lo es, o
            # un polinomio en los bits de k si k es variable (ver _pow2_expr).
            a, b = arg_vars
            try:
                factor = str(1 << int(b))            # exponente constante
            except (ValueError, TypeError):
                factor = f"({self._pow2_expr(b)})"   # exponente variable
            if op == '<<':
                self.polynomial_system.append(f"{target_var} - (({a}) * {factor}) = 0")
            else:  # '>>' == división entera por 2^k
                rem = self._new_e_var()
                self.polynomial_system.append(f"({a}) - ({factor} * {target_var} + {rem}) = 0")
                self._emit_nonneg_four_squares(rem)                       # rem >= 0
                self._emit_nonneg_four_squares(f"({factor}) - 1 - ({rem})")  # rem < 2^k
            self._ind_of[target_var] = self._args_ind(arg_vars)
        elif op == 'neg':
            self.polynomial_system.append(f"{target_var} - (-{arg_vars[0]}) = 0")
            self._ind_of[target_var] = self._ind_of.get(arg_vars[0], "0")
        elif op == 'if':
            # cond procede de una comparación/booleano ya reificado a {0,1}
            # (ver ramas de comparación más abajo), de modo que esta
            # combinación convexa es una identidad polinómica exacta.
            cond, vt, vf = arg_vars
            self.polynomial_system.append(f"{target_var} - (({cond}) * ({vt}) + (1 - {cond}) * ({vf})) = 0")
            # Se trunca si se usa el valor de la condición o si la rama
            # seleccionada por la condición está truncada.
            self._ind_of[target_var] = self._or(
                self._ind_of.get(cond, "0"),
                self._select(cond, self._ind_of.get(vt, "0"), self._ind_of.get(vf, "0")))
        elif op in ('/', '%'):
            a, b = arg_vars
            if op == '/':
                quotient = target_var
                remainder = self._new_e_var()
            else:
                remainder = target_var
                quotient = self._new_e_var()
            # Relación de división euclídea: a = b*q + r
            self.polynomial_system.append(f"({a}) - (({b}) * ({quotient}) + {remainder}) = 0")
            # Sin acotar el resto, (q, r) no son únicos y el sistema admite
            # soluciones espurias. Se impone 0 <= r < b mediante el teorema de
            # Lagrange (todo natural es suma de cuatro cuadrados). Se asume
            # divisor b > 0, que es el caso de todo el corpus de ejemplos.
            self._emit_nonneg_four_squares(remainder)                       # r >= 0
            self._emit_nonneg_four_squares(f"({b}) - 1 - ({remainder})")    # r <= b - 1
            self._ind_of[target_var] = self._args_ind(arg_vars)
        # --- COMPARACIONES REIFICADAS A {0,1} ---
        # Cada comparación produce un resultado booleano {0,1} mediante holguras
        # de cuatro cuadrados, dejando el sistema PURE genuinamente diofántico:
        # sus soluciones enteras están en biyección con las trazas.
        elif op == '<':   # a < b  <=>  b - a - 1 >= 0
            self._reify_ge0(target_var, f"({arg_vars[1]}) - ({arg_vars[0]}) - 1")
            self._ind_of[target_var] = self._args_ind(arg_vars)
        elif op == '>':   # a > b  <=>  a - b - 1 >= 0
            self._reify_ge0(target_var, f"({arg_vars[0]}) - ({arg_vars[1]}) - 1")
            self._ind_of[target_var] = self._args_ind(arg_vars)
        elif op == '<=':  # a <= b <=>  b - a >= 0
            self._reify_ge0(target_var, f"({arg_vars[1]}) - ({arg_vars[0]})")
            self._ind_of[target_var] = self._args_ind(arg_vars)
        elif op == '>=':  # a >= b <=>  a - b >= 0
            self._reify_ge0(target_var, f"({arg_vars[0]}) - ({arg_vars[1]})")
            self._ind_of[target_var] = self._args_ind(arg_vars)
        elif op in ('==', '!='):
            # a == b  <=>  (a <= b) AND (a >= b).  Reificamos ambas y su producto.
            cle = self._new_e_var(); self._reify_ge0(cle, f"({arg_vars[1]}) - ({arg_vars[0]})")
            cge = self._new_e_var(); self._reify_ge0(cge, f"({arg_vars[0]}) - ({arg_vars[1]})")
            if op == '==':
                self.polynomial_system.append(f"{target_var} - ({cle}*{cge}) = 0")
            else:  # a != b  <=>  1 - (a == b)
                self.polynomial_system.append(f"{target_var} - (1 - {cle}*{cge}) = 0")
            self._ind_of[target_var] = self._args_ind(arg_vars)
        elif op in ('&&', '||'):
            # Operandos lógicos booleanizados; AND -> producto, OR -> suma menos producto.
            a, b = arg_vars
            self._emit_boolean(a)
            self._emit_boolean(b)
            if op == '&&':
                self.polynomial_system.append(f"{target_var} - ({a}*{b}) = 0")
            else:
                self.polynomial_system.append(f"{target_var} - ({a} + {b} - {a}*{b}) = 0")
            self._ind_of[target_var] = self._args_ind(arg_vars)
        else:
            if len(arg_vars) == 2:
                self.polynomial_system.append(f"{target_var} - ({arg_vars[0]} {op} {arg_vars[1]}) = 0")
                self._ind_of[target_var] = self._args_ind(arg_vars)
            else:
                raise ValueError(f"Operador desconocido: {op}")

    def _resolve_operand(self, operand):
        if operand is None:
            # Un operando None indica que el generador dejó una expresión sin
            # resolver (p. ej. un nodo AST no soportado). Fallar pronto y con un
            # mensaje accionable en vez de colar el literal "None" en las
            # ecuaciones y producir un sistema corrupto en silencio.
            raise ValueError(
                "operando None: el generador dejó una expresión sin resolver "
                "(probable nodo AST no soportado); el sistema no sería un "
                "polinomio válido."
            )
        if not isinstance(operand, tuple):
            s = str(operand).replace("{", "").replace("}", "")
            if s == OVERFLOW_MARKER:
                if self.mode == "LOGICAL":
                    return "0"
                self._ind_of[OVERFLOW_MARKER] = "1"
                self._saw_overflow = True
                return OVERFLOW_MARKER
            self._ind_of.setdefault(s, "0")
            return s
        temp_var = self._new_e_var()
        self._convert_expr_to_poly(temp_var, operand)
        return temp_var
