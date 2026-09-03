#!/usr/bin/env python3
"""Comprobacion estructural del LaTeX, ya que no hay toolchain de TeX aqui.

NO sustituye a compilar. Atrapa lo que se rompe mas a menudo al ensamblar un
paper por secciones: llaves y entornos descuadrados, `$` impares, comandos
`\\ref`/`\\cite` a claves que no existen, y `\\input` a ficheros que faltan.
"""
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))


def revisar(ruta):
    txt = open(ruta, encoding='utf-8').read()
    sin_verbatim = re.sub(r'%.*', '', txt)          # comentarios fuera
    problemas = []

    abiertas = sin_verbatim.count('{') - sin_verbatim.count('\\{')
    cerradas = sin_verbatim.count('}') - sin_verbatim.count('\\}')
    if abiertas != cerradas:
        problemas.append(f"llaves descuadradas: {abiertas} abiertas, {cerradas} cerradas")

    pila = []
    for m in re.finditer(r'\\(begin|end)\{([^}]+)\}', sin_verbatim):
        if m.group(1) == 'begin':
            pila.append(m.group(2))
        else:
            if not pila:
                problemas.append(f"\\end{{{m.group(2)}}} sin \\begin")
            elif pila[-1] != m.group(2):
                problemas.append(f"\\end{{{m.group(2)}}} cierra \\begin{{{pila[-1]}}}")
            else:
                pila.pop()
    if pila:
        problemas.append(f"entornos sin cerrar: {pila}")

    dolares = len(re.findall(r'(?<!\\)\$', sin_verbatim.replace('$$', '')))
    if dolares % 2:
        problemas.append(f"numero impar de `$` ({dolares})")

    return problemas, sin_verbatim


def main():
    main_tex = os.path.join(AQUI, 'main.tex')
    fuente = open(main_tex, encoding='utf-8').read()
    inputs = re.findall(r'\\input\{([^}]+)\}', fuente)

    claves = set(re.findall(r'@\w+\{([^,]+),',
                            open(os.path.join(AQUI, 'refs.bib'), encoding='utf-8').read()))
    fallos, citas, etiquetas, refs = [], set(), set(), set()

    for f in ['main.tex'] + [f'{i}.tex' for i in inputs]:
        ruta = os.path.join(AQUI, f)
        if not os.path.exists(ruta):
            fallos.append(f"{f}: NO EXISTE (referenciado por \\input)")
            continue
        probs, limpio = revisar(ruta)
        for p in probs:
            fallos.append(f"{f}: {p}")
        for c in re.findall(r'\\cite\{([^}]+)\}', limpio):
            citas.update(x.strip() for x in c.split(','))
        etiquetas.update(re.findall(r'\\label\{([^}]+)\}', limpio))
        refs.update(re.findall(r'\\(?:eq)?ref\{([^}]+)\}', limpio))

    for c in sorted(citas - claves):
        fallos.append(f"\\cite{{{c}}} no esta en refs.bib")
    for r in sorted(refs - etiquetas):
        fallos.append(f"\\ref{{{r}}} sin \\label correspondiente")

    print(f"ficheros: {1 + len(inputs)}   citas: {len(citas)}   "
          f"etiquetas: {len(etiquetas)}   claves bib: {len(claves)}")
    if fallos:
        print("\nPROBLEMAS:")
        for f in fallos:
            print(f"  - {f}")
        sys.exit(1)
    print("estructura OK (llaves, entornos, $, citas y referencias cruzadas)")


if __name__ == '__main__':
    main()
