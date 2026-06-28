#!/usr/bin/env python3
import sys
import re
import math

# Aumentar recursión para parseo inicial
sys.setrecursionlimit(2000000)

# --- OPCODES ---
OP_PUSH_LIT, OP_LOAD_VAR, OP_ADD, OP_SUB, OP_MUL, OP_DIV, OP_MOD = 1, 2, 3, 4, 5, 6, 7
OP_EQ, OP_NEQ, OP_LT, OP_GT, OP_LTE, OP_GTE = 8, 9, 10, 11, 12, 13
OP_AND, OP_OR, OP_JUMP_IF_FALSE, OP_JUMP, OP_CALL, OP_RETURN, OP_POW = 14, 15, 16, 17, 18, 19, 21

class VM:
    def __init__(self): 
        self.functions = {}
        self.global_trace = {} 

    def load_function(self, name, params, ast):
        if ast is None: return
        bytecode = []; self._compile(ast, bytecode); bytecode.append((OP_RETURN, None))
        clean_params = [p.strip() for p in params]
        self.functions[name] = (clean_params, bytecode)

    def _compile(self, node, code):
        if isinstance(node, int): code.append((OP_PUSH_LIT, node)); return
        if isinstance(node, str): code.append((OP_LOAD_VAR, node.strip())); return
        if isinstance(node, list):
            if not node: return
            op = node[0]
            args = node[1:]
            
            if op == 'If':
                self._compile(args[0], code); jf = len(code); code.append((OP_JUMP_IF_FALSE, 0))
                self._compile(args[1], code); jp = len(code); code.append((OP_JUMP, 0))
                code[jf] = (OP_JUMP_IF_FALSE, len(code)); self._compile(args[2], code)
                code[jp] = (OP_JUMP, len(code)); return
            
            if op == 'Call':
                func, cargs = args[0], args[1:]
                if func == 'call' and len(cargs) > 0: func = cargs[0]; cargs = cargs[1:]
                for a in cargs: self._compile(a, code)
                code.append((OP_POW, None) if func=='pow' else (OP_CALL, (str(func), len(cargs))))
                return
            
            if op in BINARY_OPCODES:
                if len(args)==2: self._compile(args[0], code); self._compile(args[1], code); code.append((BINARY_OPCODES[op], None))
                elif len(args)==1 and op=='sub': code.append((OP_PUSH_LIT, 0)); self._compile(args[0], code); code.append((OP_SUB, None))
                return

    def run(self, entry, args):
        if entry not in self.functions: 
            print(f"[VM ERROR] Function '{entry}' not found."); return -999
            
        stack, call_stack = [], []
        params, code = self.functions[entry]
        
        # Arity Fix
        if len(args) != len(params):
            if len(params) == len(args) + 1:
                if params and params[-1] == 'RET': args = args + [0]
                else: args = [0] + args
            elif len(params) == len(args) - 1: args = args[1:]
            while len(args) < len(params): args.append(0)

        local = dict(zip(params, args))
        self.global_trace.update(local)
        pc = 0
        # ops = 0  <-- ELIMINADO CONTADOR DE SEGURIDAD
        
        # Variables locales cacheadas para velocidad extrema
        stack_append = stack.append
        stack_pop = stack.pop
        
        while True:
            # BUCLE INFINITO PERMITIDO (Confiamos en el timeout externo)
            try:
                op, arg = code[pc]; pc += 1
                
                if op == OP_PUSH_LIT: stack_append(arg)
                elif op == OP_LOAD_VAR: 
                    # Optimización: Asumimos que la variable existe si compiló bien
                    # Para velocidad en bucles masivos, quitamos el .get() seguro
                    try:
                        stack_append(local[arg])
                    except KeyError:
                        stack_append(0)
                
                elif op == OP_ADD: b=stack_pop(); a=stack_pop(); stack_append(a+b)
                elif op == OP_SUB: b=stack_pop(); a=stack_pop(); stack_append(a-b)
                elif op == OP_MUL: b=stack.pop(); a=stack.pop(); stack_append(a*b)
                elif op == OP_DIV: b=stack_pop(); a=stack_pop(); stack_append(a//b if b!=0 else 0)
                elif op == OP_MOD: b=stack.pop(); a=stack.pop(); stack_append(a%b if b!=0 else 0)
                elif op == OP_POW: b=stack.pop(); a=stack.pop(); stack_append(pow(a,b))
                
                elif op == OP_EQ: b=stack.pop(); a=stack.pop(); stack_append(1 if a==b else 0)
                elif op == OP_NEQ: b=stack.pop(); a=stack.pop(); stack.append(1 if a!=b else 0)
                elif op == OP_LT: b=stack.pop(); a=stack.pop(); stack.append(1 if a<b else 0)
                elif op == OP_GT: b=stack.pop(); a=stack.pop(); stack.append(1 if a>b else 0)
                elif op == OP_LTE: b=stack.pop(); a=stack.pop(); stack.append(1 if a<=b else 0)
                elif op == OP_GTE: b=stack.pop(); a=stack.pop(); stack.append(1 if a>=b else 0)
                elif op == OP_AND: b=stack.pop(); a=stack.pop(); stack.append(1 if a and b else 0)
                elif op == OP_OR: b=stack.pop(); a=stack.pop(); stack.append(1 if a or b else 0)
                
                elif op == OP_JUMP_IF_FALSE: 
                    if stack.pop() == 0: pc = arg
                elif op == OP_JUMP: pc = arg
                
                elif op == OP_CALL:
                    fname, argc = arg
                    new_args = [0]*argc
                    for i in range(argc-1, -1, -1): new_args[i] = stack.pop()
                    if fname not in self.functions: stack.append(0); continue
                    call_stack.append((code, pc, local))
                    params, code = self.functions[fname]
                    
                    # Arity fix runtime (ligero)
                    if len(params) != argc:
                        if len(params) == argc + 1:
                             if params[-1] == 'RET': new_args.append(0)
                             else: new_args.insert(0, 0)
                        elif len(params) == argc - 1: new_args.pop(0)
                        while len(new_args) < len(params): new_args.append(0)

                    local = dict(zip(params, new_args))
                    pc = 0
                    
                elif op == OP_RETURN:
                    ret = stack.pop()
                    if not call_stack: return ret
                    code, pc, local = call_stack.pop()
                    stack.append(ret)
            except IndexError: return -1

BINARY_OPCODES = {'add': OP_ADD, 'sub': OP_SUB, 'mul': OP_MUL, 'div': OP_DIV, 'mod': OP_MOD, 'eq': OP_EQ, 'neq': OP_NEQ, 'lt': OP_LT, 'gt': OP_GT, 'lte': OP_LTE, 'gte': OP_GTE, 'and': OP_AND, 'or': OP_OR}

class Parser:
    def parse(self, text):
        text = text.replace('&&', ' and ').replace('||', ' or ')
        self.tokens = re.findall(r'[a-zA-Z_]\w*|[0-9]+|==|!=|<=|>=|[-+*/%<>,()]|\^', text)
        self.pos = 0
        return self._parse_expr()
    def _peek(self): return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    def _consume(self): t = self._peek(); self.pos += 1; return t
    def _parse_expr(self):
        t = self._consume()
        if t is None: return None
        if t.isdigit(): return int(t)
        if re.match(r'[a-zA-Z_]', t) or t in ['+', '-', '*', '/', '%', '^', '<', '>', '<=', '>=', '==', '!=']:
            name = t
            op_map = {'+':'add', '-':'sub', '*':'mul', '/':'div', '%':'mod', '^': 'pow', '<':'lt', '>':'gt', '<=':'lte', '>=':'gte', '==':'eq', '!=':'neq'}
            if name in op_map: name = op_map[name]
            if self._peek() == '(':
                self._consume(); args = []
                if self._peek() != ')':
                    while True:
                        args.append(self._parse_expr())
                        if self._peek() == ',': self._consume()
                        elif self._peek() == ')': break
                        else: break
                if self._peek() == ')': self._consume()
                if name == 'If': return ['If'] + args
                if name in BINARY_OPCODES: return [name] + args
                if name.startswith("P_"): name = name[2:]
                return ['Call', name] + args
            return name
        if t == '(':
            left = self._parse_expr()
            if self._peek() in ['+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '^', 'and', 'or']:
                op_tok = self._consume(); right = self._parse_expr(); 
                if self._peek() == ')': self._consume()
                op_map = {'+':'add', '-':'sub', '*':'mul', '/':'div', '%':'mod', '^': 'pow', '<':'lt', '>':'gt', '<=':'lte', '>=':'gte', '==':'eq', '!=':'neq', 'and':'and', 'or':'or'}
                return [op_map.get(op_tok, op_tok), left, right]
            if self._peek() == ')': self._consume()
            return left
        return None

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(); p.add_argument('filepath'); p.add_argument('call_expr')
    args = p.parse_args()

    vm = VM(); parser = Parser()
    try:
        with open(args.filepath, 'r', encoding='utf-8') as f: content = f.read()
        blk = re.search(r'--- \[DEFINICIONES.*?---\n(.*?)\n---', content, re.DOTALL)
        if blk:
            for l in blk.group(1).split('\n'):
                m = re.match(r'P_(\w+)\((.*?)\)\s*=\s*(.*)', l.strip())
                if m: 
                    p_list = [x.strip() for x in m.group(2).split(',') if x.strip()]
                    vm.load_function(m.group(1), p_list, parser.parse(m.group(3)))
    except: pass
    
    m_c = re.match(r'(\w+)\((.*?)\)', args.call_expr)
    if m_c: 
        func, s_args = m_c.groups()
        f_args = [int(x) for x in s_args.split(',')] if s_args.strip() else []
        print(f"Result: {vm.run(func, f_args)}")