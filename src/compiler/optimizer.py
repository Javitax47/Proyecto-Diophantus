from collections import defaultdict

class Optimizer:
    """
    Aplica la optimización de Eliminación de Subexpresiones Comunes (CSE)
    a un AST de tuplas de la Función de Transición.

    Esta clase es un componente clave en el pipeline del compilador, transformando
    ecuaciones largas y repetitivas en un sistema de ecuaciones más simple y
    legible, ideal para la exportación.
    """
    def __init__(self, f_function_tuples):
        """
        Inicializa el optimizador.

        Args:
            f_function_tuples (dict): Un diccionario que mapea nombres de variables
                de estado a sus AST de tuplas de transición correspondientes.
        """
        self.f_function = f_function_tuples
        self.sub_map = {}
        self.sub_defs = {}
        self.sub_counter = 0

    def optimize(self):
        """
        Punto de entrada principal. Realiza el proceso de CSE.

        El proceso sigue tres pasos:
        1. Recorre el AST para contar la frecuencia de cada subexpresión.
        2. Identifica las subexpresiones que son candidatas para la optimización
           (se repiten y son suficientemente complejas).
        3. Reemplaza estas subexpresiones con identificadores (C_n) y genera
           sus definiciones.

        Returns:
            tuple: Una tupla conteniendo:
            - optimized_f_func (dict): La F-Function con subexpresiones reemplazadas.
            - optimized_sub_defs (dict): Un diccionario con las definiciones de C_n.
        """
        # 1. Contar la frecuencia de cada subexpresión (tupla) en todo el árbol.
        counts = defaultdict(int)
        for expr_tuple in self.f_function.values():
            self._collect_subexpressions(expr_tuple, counts)
            
        # 2. Identificar las subexpresiones que vale la pena reemplazar.
        #    Criterios: se repiten más de una vez y tienen una longitud mínima.
        for expr_tuple, count in counts.items():
            if count > 1 and len(str(expr_tuple)) > 10: 
                sub_name = f"C_{{{self.sub_counter}}}"
                self.sub_map[expr_tuple] = sub_name
                self.sub_defs[sub_name] = expr_tuple
                self.sub_counter += 1
        
        print(f"  [Optimizer] ...{len(self.sub_defs)} subexpresiones comunes encontradas y extraídas.")
        
        # 3. Construir la función F optimizada reemplazando las subexpresiones.
        optimized_f_func = {}
        for var, expr_tuple in self.f_function.items():
            optimized_f_func[var] = self._replace_subexpressions(expr_tuple)
        
        # 4. Optimizar las propias definiciones (pueden anidarse, ej. C_5 usa C_2).
        optimized_sub_defs = {}
        for name, expr_tuple in self.sub_defs.items():
            op = expr_tuple[0]
            args = [self._replace_subexpressions(child) for child in expr_tuple[1:]]
            optimized_sub_defs[name] = (op,) + tuple(args)
            
        return optimized_f_func, optimized_sub_defs

    def _collect_subexpressions(self, expr, counts):
        """
        Recorre recursivamente una expresión y actualiza el contador de frecuencia
        para cada subexpresión (tupla) que encuentra.
        """
        if not isinstance(expr, tuple):
            return
        
        counts[expr] += 1
        
        for child in expr[1:]:
            self._collect_subexpressions(child, counts)

    def _replace_subexpressions(self, expr):
        """
        Recorre recursivamente una expresión y la reconstruye, reemplazando
        cualquier subexpresión común con su identificador C_n.
        """
        if not isinstance(expr, tuple):
            return expr # Caso base: es una variable, constante o C_n ya reemplazado.
        
        # Si la expresión completa es una subexpresión común, la reemplazamos.
        if expr in self.sub_map:
            return self.sub_map[expr]
        
        # Si no, reemplazamos recursivamente a sus hijos y reconstruimos la tupla.
        op = expr[0]
        args = [self._replace_subexpressions(child) for child in expr[1:]]
        return (op,) + tuple(args)