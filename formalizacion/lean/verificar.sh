#!/usr/bin/env bash
# Verifica `CotaA.lean` desde cero: descarga Lean si hace falta, compila y audita
# los axiomas. Sin Mathlib -- solo el nucleo, asi que no hay que construir nada.
set -euo pipefail
VER=4.33.1
DIR="${LEAN_DIR:-/tmp/lean-diophantus}"
AQUI="$(cd "$(dirname "$0")" && pwd)"

if ! command -v lean >/dev/null 2>&1; then
  if [ ! -x "$DIR/lean-$VER-linux/bin/lean" ]; then
    echo ">> descargando Lean $VER (~570 MB comprimidos)"
    mkdir -p "$DIR"
    curl -sSL -o "$DIR/lean.tar.zst" \
      "https://releases.lean-lang.org/lean4/v$VER/lean-$VER-linux.tar.zst"
    # el tar del sistema puede no traer zstd; se descomprime con python
    python3 - "$DIR" <<'PY'
import sys, zstandard
d = sys.argv[1]
with open(f"{d}/lean.tar.zst","rb") as f, open(f"{d}/lean.tar","wb") as o:
    zstandard.ZstdDecompressor().copy_stream(f, o, write_size=1<<22)
PY
    tar xf "$DIR/lean.tar" -C "$DIR"
    rm -f "$DIR/lean.tar" "$DIR/lean.tar.zst"
  fi
  export PATH="$DIR/lean-$VER-linux/bin:$PATH"
fi

echo ">> lean: $(lean --version)"
echo ">> compilando CotaA.lean"
lean -o "$AQUI/CotaA.olean" "$AQUI/CotaA.lean"
echo ">> compilando Eliminacion.lean"
lean -o "$AQUI/Eliminacion.olean" "$AQUI/Eliminacion.lean"
echo ">> compilando Pell.lean"
lean -o "$AQUI/Pell.olean" "$AQUI/Pell.lean"
echo ">> compilando Eliminacion21.lean"
LEAN_PATH="$AQUI" lean -o "$AQUI/Eliminacion21.olean" "$AQUI/Eliminacion21.lean"

echo ">> auditando axiomas (deben ser solo propext / Classical.choice / Quot.sound)"
cat > "$AQUI/.auditoria.lean" <<'LEAN'
import CotaA
open Diophantus
#print axioms lt_of_sq_lt
#print axioms sin_cuadrado_intermedio
#print axioms n_ne_zero
#print axioms n_ne_one
#print axioms n_ge_two
#print axioms e_eq_zero_of_a_one
#print axioms a_ge_two
#check @a_ge_two
LEAN
cat > "$AQUI/.auditoria2.lean" <<'LEAN'
import Eliminacion
open Diophantus
#print axioms defZ_nonneg
#print axioms defQ_nonneg
#print axioms defY_nonneg
#print axioms completo_de_defs
#print axioms equisatisfacible
#check @equisatisfacible
LEAN
cat > "$AQUI/.auditoria3.lean" <<'LEAN'
import Pell
open Diophantus
#print axioms completitud
#print axioms Y_mod
#print axioms Y_mono
#print axioms a_ge_e_succ
#print axioms a_ge_e_succ_de_sistema
#check @a_ge_e_succ_de_sistema
LEAN
cat > "$AQUI/.auditoria4.lean" <<'LEAN'
import Eliminacion21
open Diophantus
#print axioms completo_de_defs21
#print axioms equisatisfacible21
#check @equisatisfacible21
LEAN
LEAN_PATH="$AQUI" lean "$AQUI/.auditoria.lean"
LEAN_PATH="$AQUI" lean "$AQUI/.auditoria2.lean"
LEAN_PATH="$AQUI" lean "$AQUI/.auditoria3.lean"
LEAN_PATH="$AQUI" lean "$AQUI/.auditoria4.lean"
rm -f "$AQUI"/.auditoria*.lean "$AQUI"/*.olean

echo ">> comprobando que el ENUNCIADO es el teorema que se cree demostrar"
cd "$AQUI/../.." && PYTHONPATH=. python3 src/tests/verification/test_lean_cota_a.py
PYTHONPATH=. python3 src/tests/verification/test_lean_eliminacion.py
PYTHONPATH=. python3 src/tests/verification/test_lean_pell.py
PYTHONPATH=. python3 src/tests/verification/test_lean_eliminacion21.py
