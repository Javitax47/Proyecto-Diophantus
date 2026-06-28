#!/usr/bin/env python3
"""
================================================================================
   DIOPHANTUS - CONJETURADOR (generación de conjeturas estilo Ramanujan Machine)
================================================================================
Valida src/analysis/conjecturer.py: el motor genera CONJETURAS (no demostraciones)
identificando fracciones continuas polinómicas (PCF) con transformaciones de Möbius
de constantes fundamentales (π, e, ...), vía precisión arbitraria + PSLQ.

Comprueba:
  - identifica la PCF de Brouncker -> 4/π (relación entera correcta);
  - identifica la PCF de e;
  - SOUNDNESS del filtro: un valor RACIONAL no se reporta (la constante se cancela);
  - un barrido pequeño produce conjeturas GENUINAS (no degeneradas), todas
    re-verificadas a ALTA precisión de forma independiente.

NO se afirma novedad: como en OEIS, la novedad se contrasta con la literatura /
base de la Ramanujan Machine (paso externo). Aquí se garantiza corrección numérica.

Uso:  python src/tests/verification/test_conjecturer.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

try:
    import mpmath as mp
except ImportError:
    print("[SKIP] mpmath no está instalado.")
    sys.exit(0)

from src.analysis.conjecturer import (
    pcf_value, identify, search, search_parallel, verify_conjecture,
    _structured_a_forms, search_structured, identify_open, search_open,
    irrationality_delta, annotate_delta, pcf_convergents,
    search_accelerated, accel_b_coeffs, accel_b_space, named_constants,
    identify_linear, analyze_linear_forms, search_screened,
)


class Colors:
    OKGREEN = '\033[92m'; FAIL = '\033[91m'; HEADER = '\033[95m'
    BOLD = '\033[1m'; ENDC = '\033[0m'


class Stats:
    def __init__(self): self.passed = 0; self.failed = 0
    def ok(self): self.passed += 1
    def fail(self, msg):
        self.failed += 1
        print(f"  {Colors.FAIL}✗ FAIL{Colors.ENDC} {msg}")


def test_brouncker(stats):
    print(f"{Colors.HEADER}[1] Identifica la PCF de Brouncker -> 4/π{Colors.ENDC}")
    v = pcf_value([0, 0, 1], [1, 2], depth=400, dps=60)   # a(n)=n², b(n)=2n+1
    ident = identify(v)
    if ident and ident['constant'] == 'pi' and ident['relation'] == [-4, 0, 0, 1]:
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 1 + 1²/(3 + 2²/(5 + …)) = 4/π  (relación {ident['relation']})")
    else:
        stats.fail(f"Brouncker no identificado: {ident}")


def test_e(stats):
    print(f"{Colors.HEADER}[2] Identifica una PCF de e{Colors.ENDC}")
    v = pcf_value([0, -1, 0], [3, 1], depth=400, dps=60)   # a(n)=-n, b(n)=n+3
    ident = identify(v)
    if ident and ident['constant'] == 'e':
        stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} valor ≈ {mp.nstr(v, 14)} identificado como {ident['closed_form']}")
    else:
        stats.fail(f"e no identificado: {ident}")


def test_rational_rejected(stats):
    print(f"{Colors.HEADER}[3] SOUNDNESS: un valor racional NO se reporta (constante se cancela){Colors.ENDC}")
    for q in (mp.mpf(3) / 4, mp.mpf(7) / 2, mp.mpf(5)):
        if identify(q) is not None:
            stats.fail(f"identificó un racional {q} como constante"); return
    stats.ok(); print(f"  {Colors.OKGREEN}✓{Colors.ENDC} 3/4, 7/2, 5 -> None (filtro de no-degeneración correcto)")


def test_search_genuine(stats):
    print(f"{Colors.HEADER}[4] Barrido: conjeturas genuinas, no degeneradas, re-verificadas{Colors.ENDC}")
    hits = search(a_degree=1, b_degree=1, coeff_range=(-1, 3), depth=160, dps=34)
    if len(hits) < 3:
        stats.fail(f"pocas conjeturas: {len(hits)}"); return
    # todas no degeneradas (p0*p3 != p1*p2) y re-verificadas a alta precisión
    bad = []
    for h in hits[:5]:
        p0, p1, p2, p3 = h['relation']
        nondeg = (p0 * p3 - p1 * p2) != 0
        ok = verify_conjecture(h['a_coeffs'], h['b_coeffs'], h['constant'], h['relation'], dps=80)
        if not (nondeg and ok):
            bad.append(h)
    if not bad:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {len(hits)} conjeturas; las primeras 5 no degeneradas y verificadas a 80 dígitos")
        print(f"      p. ej.: a={hits[0]['a_coeffs']} b={hits[0]['b_coeffs']} -> {hits[0]['closed_form']}")
    else:
        stats.fail(f"conjeturas degeneradas o no verificadas: {bad}")


def test_parallel(stats):
    print(f"{Colors.HEADER}[5] Barrido PARALELO (multiproceso): hits válidos y verificados{Colors.ENDC}")
    hits = search_parallel(a_degree=1, b_degree=1, coeff_range=(-1, 2),
                           depth=140, dps=34, workers=2)
    if not hits:
        stats.fail("el barrido paralelo no encontró nada"); return
    bad = [h for h in hits[:5]
           if not verify_conjecture(h['a_coeffs'], h['b_coeffs'], h['constant'], h['relation'], dps=70)]
    if not bad:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {len(hits)} conjeturas en paralelo; las primeras 5 verificadas a 70 dígitos")
    else:
        stats.fail(f"conjeturas paralelas no verificadas: {bad}")


def test_apery_structured(stats):
    print(f"{Colors.HEADER}[6] Régimen Apéry: recupera la CF de ζ(3) (a(n)=-n⁶, b grado 3){Colors.ENDC}")
    # La CF de Apéry para ζ(3): a(n) = -n⁶, b(n) = 34n³+51n²+27n+5 -> 6/ζ(3).
    # Es el régimen que la fuerza bruta de grado bajo NO alcanza; aquí debe identificarse.
    v = pcf_value([0, 0, 0, 0, 0, 0, -1], [5, 27, 51, 34], depth=400, dps=60)
    ident = identify(v, dps=58)
    apery_ok = ident and ident['constant'] == 'zeta3' and ident['relation'] == [-6, 0, 0, 1]
    # el generador de formas estructuradas debe contener el -n⁶ de Apéry
    forms_ok = tuple([0] * 6 + [-1]) in _structured_a_forms(6, (-2, 2))
    # y un barrido estructurado pequeño debe ejecutarse sin romper
    try:
        hits = search_structured(a_max_degree=3, a_lead_range=(-1, 1), b_degree=2,
                                 b_coeff_range=(-2, 2), depth=200, dps=34,
                                 screen_depth=300, const_names=['pi', 'e'], workers=2)
        run_ok = isinstance(hits, list)
    except Exception as e:
        run_ok = False
        print(f"      barrido estructurado lanzó: {e}")
    if apery_ok and forms_ok and run_ok:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} ζ(3) recuperada vía Apéry (rel {ident['relation']}); "
              f"a(n)=-n⁶ en el espacio; barrido estructurado OK")
    else:
        stats.fail(f"Apéry/estructurado falló: apery={apery_ok} forms={forms_ok} run={run_ok}")


def test_open_identify(stats):
    print(f"{Colors.HEADER}[7] Identificación SIN objetivo: algebraico / nombrado / racional / desconocido{Colors.ENDC}")
    with mp.workdps(70):                       # los valores deben tener precisión suficiente
        phi = (1 + mp.sqrt(5)) / 2             # algebraico grado 2
        v_pi = 4 / mp.pi                       # nombrado (Möbius de π)
        v_q = mp.mpf(22) / 7                   # racional -> descartar
        v_gelfond = mp.e ** mp.pi              # e^π: transcendental, fuera de la base -> desconocido
    i_phi = identify_open(phi, dps=64)
    i_pi = identify_open(v_pi, dps=64)
    i_q = identify_open(v_q, dps=64)
    i_tr = identify_open(v_gelfond, dps=64)
    ok = (i_phi and i_phi['kind'] == 'algebraic' and i_phi['degree'] == 2
          and i_pi and i_pi['kind'] == 'named' and i_pi['constant'] == 'pi'
          and i_q and i_q['kind'] == 'rational'
          and i_tr and i_tr['kind'] == 'unknown')
    if ok:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} φ→algebraico(2) {i_phi['poly']}, 4/π→nombrado(π), "
              f"22/7→racional, e^π→desconocido (sin fijar objetivo)")
    else:
        stats.fail(f"identify_open inesperado: φ={i_phi} 4/π={i_pi} 22/7={i_q} e^π={i_tr}")


def test_open_search(stats):
    print(f"{Colors.HEADER}[8] Barrido ABIERTO: clasifica límites y detecta colisiones PCF↔PCF{Colors.ENDC}")
    res = search_open(a_degree=1, b_degree=1, coeff_range=(-2, 3), depth=160, dps=34,
                      screen_depth=250, max_alg_degree=3, workers=2)
    has_keys = all(k in res for k in ('algebraic', 'named', 'unknown', 'collisions'))
    found_something = (len(res['algebraic']) + len(res['named'])) > 0
    # las colisiones, si las hay, deben involucrar ≥2 PCFs distintas
    coll_ok = all(c['count'] >= 2 and len(c['members']) >= 2 for c in res['collisions'])
    if has_keys and found_something and coll_ok:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} alg={len(res['algebraic'])} nombrados={len(res['named'])} "
              f"desconocidos={len(res['unknown'])} colisiones={len(res['collisions'])} (sin objetivo)")
    else:
        stats.fail(f"barrido abierto inesperado: keys={has_keys} found={found_something} coll_ok={coll_ok}")


def test_irrationality_delta(stats):
    print(f"{Colors.HEADER}[9] Medida de irracionalidad δ: Apéry PRUEBA ζ(3) irracional (δ>0){Colors.ENDC}")
    # convergentes enteros exactos aproximan el límite
    p, q = pcf_convergents([0, 0, 1], [1, 2], depth=15)         # Brouncker -> 4/π
    conv_ok = abs(mp.mpf(p) / q - 4 / mp.pi) < mp.mpf(10) ** -8
    # Apéry: δ>0 (prueba de irracionalidad de ζ(3)); Brouncker: δ≤0 (sin prueba)
    d_apery = irrationality_delta([0, 0, 0, 0, 0, 0, -1], [5, 27, 51, 34], depth=120, dps=240)
    d_brou = irrationality_delta([0, 0, 1], [1, 2], depth=300, dps=240)
    apery_ok = d_apery is not None and d_apery > 0.02
    brou_ok = d_brou is not None and d_brou <= 0.02      # convergencia lenta: sin info
    if conv_ok and apery_ok and brou_ok:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Apéry δ={d_apery:.4f}>0 (ζ(3) irracional, μ≲{1 + 1/d_apery:.1f}); "
              f"Brouncker δ={d_brou:.4f}≤0 (sin prueba). Convergentes enteros OK")
    else:
        stats.fail(f"δ inesperado: conv={conv_ok} Apéry={d_apery} Brouncker={d_brou}")


def test_accelerated(stats):
    print(f"{Colors.HEADER}[10] Aceleración estructural: recupera Apéry (δ>0) para ζ(3){Colors.ENDC}")
    # b(n)=(2n+1)(17n²+17n+5) debe expandirse a 34n³+51n²+27n+5
    b = accel_b_coeffs('factored', (2, 1), (17, 17, 5))
    expand_ok = b == [5, 27, 51, 34]
    # la búsqueda de aceleración (caja que incluye 17,17,5) debe hallar Apéry con δ>0
    hits = search_accelerated(target='zeta3', form='factored', a_powers=(6,), a_leads=(-1,),
                              quad_range=(5, 17), depth=250, dps=55,
                              delta_depth=130, delta_dps=300, workers=2)
    apery = [h for h in hits if h['b_coeffs'] == [5, 27, 51, 34]]
    found = bool(apery) and apery[0].get('delta') is not None and apery[0]['delta'] > 0
    if expand_ok and found:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} (2n+1)(17n²+17n+5)→{b}; aceleración recupera Apéry "
              f"δ={apery[0]['delta']:.4f}>0 (ζ(3) irracional, μ≲{1 + 1/apery[0]['delta']:.1f})")
    else:
        stats.fail(f"aceleración: expand={expand_ok} apery={apery}")


def test_generalized_b(stats):
    print(f"{Colors.HEADER}[11] Forma de b generalizada (factored/quadratic/biquadratic) + ζ(5){Colors.ENDC}")
    # cada forma genera un espacio no vacío y deduplicado; Apéry ∈ factored
    sizes = {f: len(accel_b_space(f, (-3, 3),
                                  lin_factors=[(2, 1), (1, 0)] if f == 'factored' else [(2, 1)]))
             for f in ('quadratic', 'factored', 'biquadratic')}
    apery_b = accel_b_coeffs('factored', (2, 1), (17, 17, 5))
    apery_in = tuple(apery_b) in {tuple(_reduced_sign(b)) for b in
                                  accel_b_space('factored', (5, 17), lin_factors=[(2, 1)])} \
        or any(list(b) == apery_b for b in accel_b_space('factored', (5, 17), lin_factors=[(2, 1)]))
    # ζ(5)/ζ(7) ahora son objetivos disponibles (irracionalidad abierta)
    has_open = 'zeta5' in named_constants() and 'zeta7' in named_constants()
    nonempty = all(v > 0 for v in sizes.values()) and sizes['biquadratic'] > sizes['quadratic']
    if nonempty and apery_in and has_open:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} tamaños {sizes}; Apéry∈factored; "
              f"ζ(5),ζ(7) disponibles como objetivos (irracionalidad abierta)")
    else:
        stats.fail(f"b generalizada: sizes={sizes} apery_in={apery_in} open={has_open}")


def _reduced_sign(coeffs):
    from math import gcd
    g = 0
    for c in coeffs:
        g = gcd(g, int(c))
    if g == 0:
        return tuple(int(c) for c in coeffs)
    fnz = next((int(c) for c in coeffs if c != 0), 0)
    s = -1 if fnz < 0 else 1
    return tuple(s * (int(c) // g) for c in coeffs)


def test_linear_form(stats):
    print(f"{Colors.HEADER}[12] Identificación MULTI-constante (formas lineales){Colors.ENDC}")
    with mp.workdps(80):
        v1 = mp.pi + mp.zeta(3)
        v2 = 2 * mp.pi**2 - 7 * mp.zeta(3)
        v_tr = mp.e ** mp.pi                 # no es forma lineal pequeña de la base
    basis = {'pi': mp.pi, 'zeta3': mp.zeta(3), 'pi^2': mp.pi**2, 'catalan': mp.catalan}
    i1 = identify_linear(v1, basis)
    i2 = identify_linear(v2, basis)
    i_tr = identify_linear(v_tr, basis)
    ok = (i1 and set(i1['constants']) == {'pi', 'zeta3'}
          and i2 and set(i2['constants']) == {'zeta3', 'pi^2'}
          and i_tr is None)
    if ok:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} π+ζ(3) y 2π²−7ζ(3) detectadas como formas lineales; "
              f"e^π rechazada (multi-constante real)")
    else:
        stats.fail(f"identify_linear inesperado: π+ζ3={i1} 2π²-7ζ3={i2} e^π={i_tr}")


def test_checkpoint_resume(stats):
    print(f"{Colors.HEADER}[13] Checkpoint/resume + formas lineales en modo abierto{Colors.ENDC}")
    import os, json, tempfile
    ckpt = os.path.join(tempfile.gettempdir(), "diophantus_test.ckpt")
    if os.path.exists(ckpt):
        os.remove(ckpt)
    # caza pequeña con checkpoint cada 0s (vuelca siempre)
    full = search_screened(a_degree=1, b_degree=1, coeff_range=(-1, 1), depth=120, dps=32,
                           screen_depth=160, workers=2, checkpoint=ckpt, checkpoint_every=0)
    ck = json.load(open(ckpt))
    ck_ok = ck['done'] == ck['total'] and len(ck['hits']) == len(full)
    # resume_from=total salta todo y devuelve los hits precargados (plumbing de reanudación)
    resumed = search_screened(a_degree=1, b_degree=1, coeff_range=(-1, 1), depth=120, dps=32,
                              screen_depth=160, workers=2, resume_from=ck['total'],
                              resume_hits=full)
    resume_ok = len(resumed) == len(full)
    # analyze_linear_forms corre sobre records guardados sin re-ejecutar (plumbing)
    lin = analyze_linear_forms(full[:3], basis_names=['pi', 'zeta3', 'pi^2'], dps=60,
                               min_constants=2)
    lin_ok = isinstance(lin, list)
    # modo abierto expone el bucket 'linear'
    res = search_open(a_degree=1, b_degree=1, coeff_range=(-1, 1), depth=120, dps=32,
                      screen_depth=160, workers=2, linear_basis=['pi', 'zeta3', 'ln2'])
    bucket_ok = 'linear' in res
    if ck_ok and resume_ok and lin_ok and bucket_ok:
        stats.ok()
        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} checkpoint {ck['done']}/{ck['total']} atómico; resume "
              f"reanuda; analyze_linear_forms y bucket 'linear' OK")
    else:
        stats.fail(f"checkpoint/resume: ck={ck_ok} resume={resume_ok} lin={lin_ok} bucket={bucket_ok}")
    if os.path.exists(ckpt):
        os.remove(ckpt)


def main():
    print(f"{Colors.BOLD}=== CONJETURADOR (estilo Ramanujan Machine) ==={Colors.ENDC}")
    stats = Stats()
    test_brouncker(stats)
    test_e(stats)
    test_rational_rejected(stats)
    test_search_genuine(stats)
    test_parallel(stats)
    test_apery_structured(stats)
    test_open_identify(stats)
    test_open_search(stats)
    test_irrationality_delta(stats)
    test_accelerated(stats)
    test_generalized_b(stats)
    test_linear_form(stats)
    test_checkpoint_resume(stats)

    total = stats.passed + stats.failed
    print()
    if stats.failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ {stats.passed}/{total} — genera conjeturas verificables (PCF -> forma "
              f"cerrada en una constante). Novedad: contraste externo con la literatura.{Colors.ENDC}")
        sys.exit(0)
    print(f"{Colors.FAIL}{Colors.BOLD}✗ {stats.failed}/{total} FALLARON.{Colors.ENDC}")
    sys.exit(1)


if __name__ == "__main__":
    main()
