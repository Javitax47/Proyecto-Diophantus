import re

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
        # §4.1: ancho en bits para la aritmetización de operadores bit a bit.
        self.bit_width = bit_width
        self.existential_vars_count = 0
        self.polynomial_system = []
        self.mode = "PURE" # Default

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
        """Reifica el predicado `d_expr >= 0` en una variable booleana `target`
        (SOUNDNESS §4.1). Tras estas ecuaciones, toda solución entera cumple
        `target in {0,1}` y `target = 1  <=>  d_expr >= 0`:

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
        """Impone `var in {0,1}` (booleanización, §4.1)."""
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
        `value_expr = Σ 2^i·b_i` (SOUNDNESS §4.1). Devuelve la lista de
        variables de bit. La ecuación de descomposición acota implícitamente el
        valor a [0, 2^W − 1], de modo que se asume operando sin signo (coherente
        con el tratamiento unsigned —UDiv/URem— del modo LOGICAL)."""
        bits = [self._new_e_var() for _ in range(self.bit_width)]
        for b in bits:
            self._emit_boolean(b)
        terms = " + ".join(f"{(1 << i)}*{bits[i]}" for i in range(self.bit_width))
        self.polynomial_system.append(f"({value_expr}) - ({terms}) = 0")
        return bits

    def convert(self, mode="PURE"):
        self.mode = mode
        self.polynomial_system = []
        self.existential_vars_count = 0 
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
        
        for var in sorted(self.optimized_f.keys()):
            if var in self.sub_defs or var not in self.state_vars: continue
            lhs = f"{var}[t+1]"
            self._convert_expr_to_poly(lhs, self.optimized_f[var])
            
        for var in sorted(self.optimized_f.keys()):
            if var in self.sub_defs or var in self.state_vars: continue
            self._convert_expr_to_poly(var, self.optimized_f[var])
            
        print(f"  [PolyConverter] {len(self.polynomial_system)} ecuaciones generadas.")
        return self.polynomial_system, function_definitions

    def _convert_expr_to_poly(self, target_var, expr):
        if not isinstance(expr, tuple):
            # Las llaves de los nombres CSE (C_{n}, delimitador anticolisión del
            # optimizer) deben quitarse para que la referencia coincida con su
            # definición ya saneada (C_n) y sea un identificador válido en SymPy.
            # _resolve_operand ya lo hace; aquí cubrimos la asignación directa
            # (p. ej. una variable de estado igualada a un CSE).
            clean = str(expr).replace("{", "").replace("}", "")
            self.polynomial_system.append(f"{target_var} - ({clean}) = 0")
            return

        op = expr[0]
        
        if op == 'call':
            func_name = expr[1]
            args = expr[2]
            resolved_args = [self._resolve_operand(arg) for arg in args]
            args_str = ", ".join(resolved_args + [target_var])
            self.polynomial_system.append(f"P_{func_name}({func_name}, {args_str}) = 0")
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
            
            # --- FIX: COMPARADORES UNSIGNED ---
            # Usamos funciones UGT, ULT, UGE, ULE de Z3 explícitamente
            # Esto asume que el CryptoSolver inyectará estas funciones en el contexto
            elif op == '>':  rhs = f"If(UGT({arg_vars[0]}, {arg_vars[1]}), 1, 0)"
            elif op == '<':  rhs = f"If(ULT({arg_vars[0]}, {arg_vars[1]}), 1, 0)"
            elif op == '>=': rhs = f"If(UGE({arg_vars[0]}, {arg_vars[1]}), 1, 0)"
            elif op == '<=': rhs = f"If(ULE({arg_vars[0]}, {arg_vars[1]}), 1, 0)"
            
            else: 
                rhs = f"({arg_vars[0]} {op} {arg_vars[1]})"
            
            self.polynomial_system.append(f"{target_var} - ({rhs}) = 0")
            return

        # --- MODO PURO (MATEMÁTICO) ---
        if op in ('+', '-', '*'):
            self.polynomial_system.append(f"{target_var} - ({arg_vars[0]} {op} {arg_vars[1]}) = 0")
        elif op in ('&', '|', '^'):
            # OPERADORES BIT A BIT (SOUNDNESS §4.1): antes se emitían como
            # strings (`a & b`) que SymPy no trata como polinomios — y `^` además
            # colisionaba con la potencia en el exportador CAS. Ahora se
            # descomponen ambos operandos en bits y se combina bit a bit con
            # polinomios: AND -> a_i·b_i, OR -> a_i+b_i−a_i·b_i, XOR -> a_i+b_i−2a_i·b_i.
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
        elif op in ('<<', '>>'):
            # Desplazamientos (§4.1): a<<k = a·2^k; a>>k = floor(a / 2^k),
            # reusando la división euclídea acotada. El factor 2^k es constante
            # si k lo es, o un polinomio en los bits de k si k es variable
            # (ver _pow2_expr): 2^k = Π ((2^(2^j)-1)·k_j + 1).
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
        elif op == 'neg': self.polynomial_system.append(f"{target_var} - (-{arg_vars[0]}) = 0")
        elif op == 'if':
            # cond procede de una comparación/booleano ya reificado a {0,1}
            # (ver ramas de comparación más abajo), de modo que esta
            # combinación convexa es una identidad polinómica exacta.
            cond, vt, vf = arg_vars
            self.polynomial_system.append(f"{target_var} - (({cond}) * ({vt}) + (1 - {cond}) * ({vf})) = 0")
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
            # SOUNDNESS (§4.1 del informe): sin acotar el resto, (q, r) no son
            # únicos y el sistema admite soluciones espurias que no corresponden
            # a ninguna ejecución. Imponemos 0 <= r < b mediante el teorema de
            # Lagrange (todo natural es suma de cuatro cuadrados). Se asume
            # divisor b > 0, que es el caso de todo el corpus de ejemplos.
            self._emit_nonneg_four_squares(remainder)                       # r >= 0
            self._emit_nonneg_four_squares(f"({b}) - 1 - ({remainder})")    # r <= b - 1
        # --- COMPARACIONES REIFICADAS (SOUNDNESS §4.1) ---
        # Antes se emitían relacionales simbólicos (`a == b`, `a < b`) que SymPy
        # no trata como polinomios; solo el intérprete propio les daba semántica.
        # Ahora cada comparación produce un resultado booleano {0,1} mediante
        # holguras de cuatro cuadrados, dejando el sistema PURE genuinamente
        # diofántico: sus soluciones enteras están en biyección con las trazas.
        elif op == '<':   # a < b  <=>  b - a - 1 >= 0
            self._reify_ge0(target_var, f"({arg_vars[1]}) - ({arg_vars[0]}) - 1")
        elif op == '>':   # a > b  <=>  a - b - 1 >= 0
            self._reify_ge0(target_var, f"({arg_vars[0]}) - ({arg_vars[1]}) - 1")
        elif op == '<=':  # a <= b <=>  b - a >= 0
            self._reify_ge0(target_var, f"({arg_vars[1]}) - ({arg_vars[0]})")
        elif op == '>=':  # a >= b <=>  a - b >= 0
            self._reify_ge0(target_var, f"({arg_vars[0]}) - ({arg_vars[1]})")
        elif op in ('==', '!='):
            # a == b  <=>  (a <= b) AND (a >= b).  Reificamos ambas y su producto.
            cle = self._new_e_var(); self._reify_ge0(cle, f"({arg_vars[1]}) - ({arg_vars[0]})")
            cge = self._new_e_var(); self._reify_ge0(cge, f"({arg_vars[0]}) - ({arg_vars[1]})")
            if op == '==':
                self.polynomial_system.append(f"{target_var} - ({cle}*{cge}) = 0")
            else:  # a != b  <=>  1 - (a == b)
                self.polynomial_system.append(f"{target_var} - (1 - {cle}*{cge}) = 0")
        elif op in ('&&', '||'):
            # Operandos lógicos booleanizados; AND -> producto, OR -> suma menos producto.
            a, b = arg_vars
            self._emit_boolean(a)
            self._emit_boolean(b)
            if op == '&&':
                self.polynomial_system.append(f"{target_var} - ({a}*{b}) = 0")
            else:
                self.polynomial_system.append(f"{target_var} - ({a} + {b} - {a}*{b}) = 0")
        else:
            if len(arg_vars) == 2:
                self.polynomial_system.append(f"{target_var} - ({arg_vars[0]} {op} {arg_vars[1]}) = 0")
            else:
                raise ValueError(f"Operador desconocido: {op}")

    def _resolve_operand(self, operand):
        if operand is None:
            # ROBUSTEZ: un operando None indica que el generador dejó una
            # expresión sin resolver (p. ej. un nodo AST no soportado). Antes
            # esto se colaba como el literal "None" en las ecuaciones,
            # produciendo un sistema corrupto en silencio. Fallar pronto y con
            # un mensaje accionable (filosofía anti-corrupción de §4.2).
            raise ValueError(
                "operando None: el generador dejó una expresión sin resolver "
                "(probable nodo AST no soportado); el sistema no sería un "
                "polinomio válido."
            )
        if not isinstance(operand, tuple):
            return str(operand).replace("{", "").replace("}", "")
        temp_var = self._new_e_var()
        self._convert_expr_to_poly(temp_var, operand)
        return temp_var