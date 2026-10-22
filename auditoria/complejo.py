"""Construye una solucion COMPLEJA del sistema compilado de factorial.c.

Uso:  python3 auditoria/complejo.py auditoria/factorial_15_niveles.txt 7

En ℂ no hay orden, asi que la codificacion de comparaciones por cuatro cuadrados
(x <= y  <=>  y - x es suma de cuatro cuadrados) no restringe nada: todo numero
complejo es un cuadrado. Cada `if` puede tomar la rama que se quiera.
Ruta elegida: k > 1 en el primer paso, y "caso base" en todos los siguientes.
"""
import re, sys, math, cmath
F = sys.argv[1]
K = int(sys.argv[2])

eqs = []
for l in open(F):
    l = l.strip()
    if not l or '=' not in l:
        continue
    l = l.replace('[t+1]', '__n')
    izq, der = l.rsplit('=', 1)
    eqs.append(f"({izq.strip()}) - ({der.strip()})")

val = {"in_k": K, "in_k__n": K, "overflow": 0, "__OVERFLOW__": 0}
# 1) comparaciones: e_a*(1-e_a)=0  y  (1-X) - (e_a*(sq4) - (1-e_a)*(1+sq4')) = 0
comp = re.compile(r"\(\(1\) - \((\w+)\)\) - \(e_(\d+)\*\(")
bloques = []
for e in eqs:
    m = comp.search(e)
    if m:
        # los nombres de los cuadrados, leidos de la ecuacion: el primer grupo
        # va con e_a (rama "si"), el segundo con (1 - e_a) (rama "no")
        cuadrados = [m2.group(1) for m2 in re.finditer(r"\b(\w+)\*\1\b", e)]
        sq1, sq2 = cuadrados[:4], cuadrados[4:8]
        bloques.append((m.group(1), int(m.group(2)), sq1, sq2))
primero = min(b[1] for b in bloques)

def resolver_definiciones():
    progreso = True
    while progreso:
        progreso = False
        for e in eqs:
            m = re.fullmatch(r"\((\w+) - \((.*)\)\) - \(0\)", e)
            if not m or m.group(1) in val:
                continue
            libres = set(re.findall(r"\b[A-Za-z_]\w*\b", m.group(2))) - val.keys()
            if not libres:
                val[m.group(1)] = eval(m.group(2), {}, dict(val))
                progreso = True

for _ in range(3):
    resolver_definiciones()
    for X, a, sq1, sq2 in bloques:
        if f"e_{a}" in val or X not in val:
            continue
        x = val[X]
        base = (a != primero)                 # rama "caso base" salvo en el primer paso
        val[f"e_{a}"] = 1 if base else 0
        for v in sq1 + sq2:
            val[v] = 0
        if base:                              # 1 - x = sq1[0]^2
            val[sq1[0]] = cmath.sqrt(1 - x)
        else:                                 # 1 - x = -(1 + sq2[0]^2)
            val[sq2[0]] = cmath.sqrt(x - 2)
resolver_definiciones()

faltan = sorted(set(re.findall(r"\b[A-Za-z_]\w*\b", ' '.join(eqs))) - val.keys())
peor = max(abs(complex(eval(e, {}, dict(val)))) / (1 + abs(K)) for e in eqs) if not faltan else None
imag = any(isinstance(v, complex) and abs(v.imag) > 0 for v in val.values())
print(f"entrada in_k = {K}")
print(f"variables sin asignar: {faltan if faltan else 'ninguna'}")
print(f"residuo maximo relativo de las {len(eqs)} ecuaciones: {peor:.2e}" if peor is not None else "no evaluable")
print(f"usa numeros imaginarios: {imag}")
print(f"salida out = {val.get('out__n')}   (el programa real calcula {K}! = {math.factorial(K) if K < 30 else 'un numero enorme'})")
