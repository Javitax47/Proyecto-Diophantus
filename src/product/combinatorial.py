"""
================================================================================
   DIOPHANTUS PRODUCT - VERTICAL COMBINATORIO  (capa universal de certificados)
================================================================================
Demuestra que el MISMO certificado algebraico portable y el MISMO re-verificador
mínimo (`recheck`, solo sympy) que certifican propiedades de PROGRAMAS sirven, sin
una sola línea de código de confianza nueva, para INFACTIBILIDAD COMBINATORIA.

Codificación clásica (Hilbert-Nullstellensatz para coloreado de grafos, De Loera
et al.): un grafo es k-coloreable  ⟺  el sistema polinómico

    x_v^k - 1 = 0                 (cada vértice toma un color = raíz k-ésima de 1)
    x_u^{k-1} + ... + x_v^{k-1} = 0   (aristas: u y v difieren)   [= (x_u^k−x_v^k)/(x_u−x_v)]

tiene solución. Entonces:
  * NO k-coloreable  ⟺  el sistema es infactible  ⟶  certificado de Nullstellensatz
    (Σ gᵢ·pᵢ = 1), re-verificable expandiendo un polinomio.  (verdict UNSAT)
  * k-coloreable  ⟶  testigo (un coloreado propio). Para k=2 el testigo es ENTERO
    (colores ±1), re-verificable por sustitución.  (verdict SAT)

Todo se delega a `verifier.py` (mismo formato de certificado) y se re-comprueba con
`recheck.py` (misma base de confianza). El aporte es la UNIFICACIÓN: un sustrato de
certificados trustless que cruza dominios hoy separados (programas ↔ combinatoria).
HONESTO: el finder de Nullstellensatz es de grado acotado (sólido, no completo): si
no certifica a `max_deg`, devuelve None (no afirma nada).
"""

from itertools import product as _product

import sympy

from src.product import verifier


def _vertex_vars(n):
    return [f"x{v}" for v in range(n)]


# --- constructores de grafos (para baterías de ejemplos) --------------------

def cycle(n):
    """Ciclo C_n (n vértices)."""
    return [(i, (i + 1) % n) for i in range(n)]


def complete(n):
    """Grafo completo K_n."""
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def complete_bipartite(m, k):
    """Bipartito completo K_{m,k} sobre m+k vértices (0..m-1 | m..m+k-1)."""
    return [(i, m + j) for i in range(m) for j in range(k)]


def wheel(n):
    """Rueda W_n: un ciclo C_n + un cubo conectado a todos. Devuelve (n_vertices, edges)."""
    edges = cycle(n) + [(n, i) for i in range(n)]
    return n + 1, edges


def petersen():
    """Grafo de Petersen (10 vértices, χ=3). Devuelve (n_vertices, edges)."""
    outer = [(i, (i + 1) % 5) for i in range(5)]
    spokes = [(i, i + 5) for i in range(5)]
    inner = [(5 + i, 5 + (i + 2) % 5) for i in range(5)]
    return 10, outer + spokes + inner


def coloring_system(n, edges, k):
    """Sistema polinómico (sympy) cuya solución ⟺ k-coloreado propio del grafo.
    Devuelve (polys, var_names)."""
    var_names = _vertex_vars(n)
    syms = {name: sympy.Symbol(name) for name in var_names}
    xs = [syms[name] for name in var_names]
    polys = [xs[v]**k - 1 for v in range(n)]                 # color = raíz k-ésima de 1
    for (u, v) in edges:
        # (x_u^k − x_v^k)/(x_u − x_v) = Σ_{i=0}^{k-1} x_u^{k-1-i} x_v^{i}  (u ≠ v)
        edge = sum(xs[u]**(k - 1 - i) * xs[v]**i for i in range(k))
        polys.append(sympy.expand(edge))
    return polys, var_names


def find_coloring(n, edges, k):
    """Busca (fuerza bruta) un k-coloreado propio. Devuelve lista color[v] ∈ 0..k-1
    o None si no existe (grafo pequeño)."""
    adj = [[] for _ in range(n)]
    for (u, v) in edges:
        adj[u].append(v)
        adj[v].append(u)
    for assign in _product(range(k), repeat=n):
        if all(assign[u] != assign[v] for (u, v) in edges):
            return list(assign)
    return None


def certify_not_colorable(n, edges, k, max_deg=2):
    """Certifica que el grafo NO es k-coloreable vía Nullstellensatz portable.
    Devuelve el dict-certificado (mismo formato que verifier) o None."""
    polys, var_names = coloring_system(n, edges, k)
    claim = f"el grafo de {n} vértices y {len(edges)} aristas NO es {k}-coloreable"
    return verifier.certify_unreachable(polys, var_names, claim=claim, max_deg=max_deg)


def certify_coloring_witness(n, edges, k=2):
    """Si el grafo es 2-coloreable (bipartito), emite un testigo ENTERO (colores ±1)
    re-verificable. Devuelve el dict-certificado o None (no bipartito / k≠2)."""
    if k != 2:
        return None
    coloring = find_coloring(n, edges, 2)
    if coloring is None:
        return None
    polys, var_names = coloring_system(n, edges, 2)
    # color 0 -> +1, color 1 -> -1 (raíces cuadradas de 1, enteras)
    assignment = {var_names[v]: (1 if coloring[v] == 0 else -1) for v in range(n)}
    claim = f"el grafo es 2-coloreable; testigo (coloreado ±1)"
    return verifier.certify_witness(polys, var_names, assignment, claim=claim)


def certify_colorability(n, edges, k, max_deg=2):
    """Veredicto unificado: intenta testigo (k=2) o certificado de no-coloreabilidad.
    Devuelve (cert_dict, encontrado:bool)."""
    coloring = find_coloring(n, edges, k)
    if coloring is not None:
        if k == 2:
            return certify_coloring_witness(n, edges, 2), True
        # k>2: el coloreado existe pero el testigo no es entero (raíces complejas);
        # se reporta el coloreado como dato (sin certificado-testigo entero).
        return {'verdict': 'SAT', 'kind': 'coloring', 'coloring': coloring,
                'note': 'coloreado propio hallado; testigo entero solo para k=2'}, True
    cert = certify_not_colorable(n, edges, k, max_deg=max_deg)
    return cert, False
