"""Un caso aislado del banco, para lanzarlo con un `timeout` externo.

Uso:  PYTHONPATH=. timeout 130 python3 auditoria/caso.py SISTEMA.txt {Z|R} VARIABLE VALOR
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from banco import caso

if __name__ == '__main__':
    sistema, dom, var, val = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    print(caso(sistema, dom, {var: val}, 100), flush=True)
