#!/usr/bin/env python3
"""Genera el LaTeX de los sistemas exhibidos A PARTIR de los ficheros Lean.

POR QUE GENERADO Y NO TRANSCRITO. Es la misma razon por la que `dioph_lean.py`
genera `Aplanado.lean` en vez de escribirlo a mano: un signo mal copiado daria un
paper que se lee bien y afirma otra cosa. Aqui el .tex sale del mismo fichero que
el nucleo de Lean verifica, asi que si divergen es un error de este script y no
una errata silenciosa.
"""
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
LEAN = os.path.join(AQUI, '..', 'formalizacion', 'lean')


def a_latex(expr):
    """Sintaxis de Lean -> LaTeX. Deliberadamente conservador."""
    e = expr.strip()
    e = re.sub(r'\bm(\d+)\b', r'\\mu_{\1}', e)          # nombres m1..m20
    e = re.sub(r'\^ ?(\d+)', r'^{\1}', e)
    e = e.replace('*', r'\cdot ')
    e = re.sub(r'\\cdot\s+', ' ', e)                     # producto por yuxtaposicion
    e = re.sub(r'(\d)\s+([a-zA-Z\\])', r'\1\2', e)       # 16 k -> 16k
    e = ' '.join(e.split())
    e = e.replace(' ^{', '^{')                           # f ^{2} -> f^{2}
    e = re.sub(r'\+ *-1([a-zA-Z\\])', r'- \1', e)          # + -1a -> - a
    e = re.sub(r'\+ *-', '- ', e)
    e = re.sub(r'\}\s+([a-zA-Z\\])', r'} \1', e)
    return e


def ecuaciones_de(fichero, definicion):
    txt = open(os.path.join(LEAN, fichero), encoding='utf-8').read()
    i = txt.index(f'def {definicion} ')
    j = txt.index('\n\n', i)
    cuerpo = txt[i:j]
    cuerpo = cuerpo[cuerpo.index(':= \n') + 4:] if ':= \n' in cuerpo else \
             cuerpo[cuerpo.index('Prop :=') + 7:]
    partes = [p.strip() for p in re.split(r'\n\s*∧\s*|\s+∧\s+', cuerpo) if p.strip()]
    return [p for p in partes if '=' in p and not p.startswith('let')]


def firma(fichero, definicion):
    txt = open(os.path.join(LEAN, fichero), encoding='utf-8').read()
    m = re.search(r'def %s \(([^:]+):' % definicion, txt)
    return m.group(1).split()


def bloque(eqs, cols=1):
    filas = []
    for e in eqs:
        izq, der = e.split('=', 1)
        filas.append(f'  {a_latex(izq)} &= {a_latex(der)}')
    return '\\begin{align}\n' + ',\\\\\n'.join(filas) + '.\n\\end{align}\n'


def main():
    salida = {}

    eqs = ecuaciones_de('Aplanado.lean', 'M')
    vars_M = firma('Aplanado.lean', 'M')
    nombres = [v for v in vars_M if re.fullmatch(r'm\d+', v)]
    principales = [e for e in eqs if not re.match(r'm\d+ =', e)]
    definitorias = [e for e in eqs if re.match(r'm\d+ =', e)]
    salida['aplanado'] = {
        'variables': len(vars_M), 'nombres': len(nombres),
        'principales': principales, 'definitorias': definitorias,
    }

    eqsS = ecuaciones_de('Aplanado.lean', 'S')
    salida['original'] = {'variables': len(firma('Aplanado.lean', 'S')),
                          'ecuaciones': eqsS}

    eqs23 = ecuaciones_de('Eliminacion.lean', 'reducido')
    salida['reducido23'] = {'variables': len(firma('Eliminacion.lean', 'reducido')),
                            'ecuaciones': eqs23}

    if len(sys.argv) > 1 and sys.argv[1] == '--tex':
        a = salida['aplanado']
        print('%% GENERADO por paper/generar_sistemas.py — no editar a mano')
        print(f"%% {a['variables']} variables, "
              f"{len(a['principales'])} ecuaciones principales + "
              f"{len(a['definitorias'])} definitorias")
        print(bloque(a['principales']))
        print(bloque(a['definitorias']))
    else:
        for k, v in salida.items():
            n = len(v.get('ecuaciones', [])) or \
                len(v['principales']) + len(v['definitorias'])
            print(f"{k:12} {v['variables']:3d} variables, {n:3d} ecuaciones")


if __name__ == '__main__':
    main()
