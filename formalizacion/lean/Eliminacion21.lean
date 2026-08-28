/-
  DIOPHANTUS — la eliminación (26,25) ⟶ (21,25), usando la cota de Pell
  =====================================================================
  El mismo tipo de teorema que `Eliminacion.lean`, pero llevándose CINCO
  incógnitas en vez de tres. La diferencia no está en la técnica —siguen siendo
  sustituciones de ecuaciones lineales— sino en que dos de esas sustituciones
  sólo son válidas sobre ℕ si `a` es grande, y eso es justo lo que da
  `Pell.a_ge_e_succ_de_sistema`.

  LA CADENA, entera y sin nada citado:

    ec.(4)                    ⟹  n ≥ 2                (Pell.n_ge_two)
    ec.(3), (4), (5)          ⟹  a ≥ e+1              (Pell.a_ge_e_succ_de_sistema)
    a ≥ e+1  y  e = 2n+p+q+z  ⟹  a ≥ n+1  y  a ≥ p+1
    esas dos                  ⟹  las definiciones de `m` (ec.12) y `x` (ec.13)
                                  son ≥ 0, luego se pueden eliminar

  POR QUÉ `e` Y NO `n`. Las restas que bloqueaban eran `a−n−1`, `a−p−1` y `a−p`,
  y `e = 2n+p+q+z` domina a las tres a la vez. Una sola cota las desbloquea.

  RESULTADO: 25 incógnitas ⟶ 20, mismo grado 12, o sea generador **(21, 25)**
  frente al **(26, 25)** que JSWW publicaron. Cinco variables menos.

  DEPENDENCIAS: `Pell.lean` y nada más. Sin Mathlib.
-/
import Pell
import Eliminacion

namespace Diophantus

/-! ## 1. Las cinco definiciones que se eliminan

Salen de las ecuaciones (1), (9), (3), (12) y (13). El orden importa: `e`
depende de `q`, `a` de `e`, y `m` y `x` de `a`. -/

/-- ec.(1): `q = w·z + h + j`. -/
def vQ (h j w z : Int) : Int := w*z + h + j
/-- La reparametrización `n = N + 2`, que vale porque `n ≥ 2`. -/
def vN (N : Int) : Int := N + 2
/-- ec.(9): `y = n + l + v`. -/
def vY (N l v : Int) : Int := vN N + l + v
/-- ec.(3): `e = 2n + p + q + z`. -/
def vE (N p h j w z : Int) : Int := 2 * vN N + p + vQ h j w z + z
/-- La reparametrización `a = e + 1 + A`, que vale porque `a ≥ e+1`. -/
def vA (N p h j w z A : Int) : Int := vE N p h j w z + 1 + A
/-- ec.(12): `m = p + l(a−n−1) + b(2an + 2a − n² − 2n − 2)`. -/
def vM (a n p l b : Int) : Int :=
  p + l*(a - n - 1) + b*(2*a*n + 2*a - n^2 - 2*n - 2)
/-- ec.(13): `x = q + y(a−p−1) + s(2ap + 2a − p² − 2p − 2)`. -/
def vX (a p q y s : Int) : Int :=
  q + y*(a - p - 1) + s*(2*a*p + 2*a - p^2 - 2*p - 2)

/-! ## 2. Que las cinco son ≥ 0, que es lo que hace válida la VUELTA

Tres son inmediatas (coeficientes no negativos). Las de `m` y `x` no: llevan
`a − n − 1` y `a − p − 1`, y ahí es donde entra la cota. -/

/-- El módulo de Davis `2a(m+1) − (m+1)² − 1` es ≥ 0 en cuanto `a ≥ m+1`.
    Sirve para los dos casos, `m := n` y `m := p`. -/
theorem modulo_nonneg {a m : Int} (hm : 0 ≤ m) (h : m + 1 ≤ a) :
    0 ≤ 2*a*m + 2*a - m^2 - 2*m - 2 := by
  have h1 : (m+1) * (m+1) ≤ a * (m+1) :=
    Int.mul_le_mul_of_nonneg_right h (by omega)
  have h2 : 1 ≤ (m+1) * (m+1) := by
    have := Int.mul_le_mul_of_nonneg_left (by omega : (1:Int) ≤ m+1) (by omega : (0:Int) ≤ m+1)
    omega
  have key : 2*a*m + 2*a - m^2 - 2*m - 2 = 2*(a*(m+1)) - (m+1)*(m+1) - 1 := by grind
  omega

theorem vM_nonneg {a n p l b : Int} (hp : 0 ≤ p) (hl : 0 ≤ l) (hb : 0 ≤ b)
    (hn : 0 ≤ n) (h : n + 1 ≤ a) : 0 ≤ vM a n p l b := by
  have h1 : 0 ≤ l * (a - n - 1) := Int.mul_nonneg hl (by omega)
  have h2 : 0 ≤ b * (2*a*n + 2*a - n^2 - 2*n - 2) :=
    Int.mul_nonneg hb (modulo_nonneg hn h)
  unfold vM; omega

theorem vX_nonneg {a p q y s : Int} (hq : 0 ≤ q) (hy : 0 ≤ y) (hs : 0 ≤ s)
    (hp : 0 ≤ p) (h : p + 1 ≤ a) : 0 ≤ vX a p q y s := by
  have h1 : 0 ≤ y * (a - p - 1) := Int.mul_nonneg hy (by omega)
  have h2 : 0 ≤ s * (2*a*p + 2*a - p^2 - 2*p - 2) :=
    Int.mul_nonneg hs (modulo_nonneg hp h)
  unfold vX; omega

theorem vQ_nonneg {h j w z : Int} (hh : 0 ≤ h) (hj : 0 ≤ j) (hw : 0 ≤ w)
    (hz : 0 ≤ z) : 0 ≤ vQ h j w z := by
  have : 0 ≤ w * z := Int.mul_nonneg hw hz
  unfold vQ; omega

theorem vY_nonneg {N l v : Int} (hN : 0 ≤ N) (hl : 0 ≤ l) (hv : 0 ≤ v) :
    0 ≤ vY N l v := by unfold vY vN; omega

theorem vE_nonneg {N p h j w z : Int} (hN : 0 ≤ N) (hp : 0 ≤ p) (hh : 0 ≤ h)
    (hj : 0 ≤ j) (hw : 0 ≤ w) (hz : 0 ≤ z) : 0 ≤ vE N p h j w z := by
  have := vQ_nonneg hh hj hw hz
  unfold vE vN; omega

theorem vA_nonneg {N p h j w z A : Int} (hN : 0 ≤ N) (hp : 0 ≤ p) (hh : 0 ≤ h)
    (hj : 0 ≤ j) (hw : 0 ≤ w) (hz : 0 ≤ z) (hA : 0 ≤ A) :
    0 ≤ vA N p h j w z A := by
  have := vE_nonneg hN hp hh hj hw hz
  unfold vA; omega

/-- **`a ≥ n+1`**, en la forma reparametrizada. Es aritmética pura una vez que
    `a = e+1+A` y `e = 2n+p+q+z`: la resta se vuelve una suma de no negativos. -/
theorem vA_ge_vN_succ {N p h j w z A : Int} (hN : 0 ≤ N) (hp : 0 ≤ p)
    (hh : 0 ≤ h) (hj : 0 ≤ j) (hw : 0 ≤ w) (hz : 0 ≤ z) (hA : 0 ≤ A) :
    vN N + 1 ≤ vA N p h j w z A := by
  have := vQ_nonneg hh hj hw hz
  unfold vA vE vN; omega

/-- **`a ≥ p+1`**, igual: `e` contiene a `p` con coeficiente 1. -/
theorem vA_ge_p_succ {N p h j w z A : Int} (hN : 0 ≤ N) (_hp : 0 ≤ p)
    (hh : 0 ≤ h) (hj : 0 ≤ j) (hw : 0 ≤ w) (hz : 0 ≤ z) (hA : 0 ≤ A) :
    p + 1 ≤ vA N p h j w z A := by
  have := vQ_nonneg hh hj hw hz
  unfold vA vE vN; omega


/-! ## 3. El sistema reducido: las nueve ecuaciones que sobreviven

Desaparecen (1), (3), (9), (12) y (13) — las cinco que definen a `q`, `e`, `y`,
`m` y `x`. Quedan nueve, escritas con las definiciones dentro; expandidas
tendrían miles de términos y no se podrían cotejar a ojo. -/

def reducido21 (k b c d f g h i j l o p r s t u v w z N A : Int) : Prop :=
  let n := vN N
  let q := vQ h j w z
  let y := vY N l v
  let e := vE N p h j w z
  let a := vA N p h j w z A
  let m := vM a n p l b
  let x := vX a p q y s
  (g * k + 2 * g + k + 1) * (h + j) + h = z
  ∧ 16 * (k + 1) ^ 3 * (k + 2) * (n + 1) ^ 2 + 1 = f ^ 2
  ∧ e ^ 3 * (e + 2) * (a + 1) ^ 2 + 1 = o ^ 2
  ∧ (a ^ 2 - 1) * y ^ 2 + 1 = x ^ 2
  ∧ 16 * r ^ 2 * y ^ 4 * (a ^ 2 - 1) + 1 = u ^ 2
  ∧ ((a + u ^ 2 * (u ^ 2 - a)) ^ 2 - 1) * (n + 4 * d * y) ^ 2 + 1 = (x + c * u) ^ 2
  ∧ (a ^ 2 - 1) * l ^ 2 + 1 = m ^ 2
  ∧ a * i + k + 1 = l + i
  ∧ z + p * l * (a - p) + t * (2 * a * p - p ^ 2 - 1) = p * m

/-- Sustituir es exacto: las cinco ecuaciones eliminadas se vuelven `rfl`. -/
theorem completo_de_defs21 (k b c d f g h i j l o p r s t u v w z N A : Int) :
    completo k (vA N p h j w z A) b c d (vE N p h j w z) f g h i j l
      (vM (vA N p h j w z A) (vN N) p l b) (vN N) o p (vQ h j w z) r s t u v w
      (vX (vA N p h j w z A) p (vQ h j w z) (vY N l v) s) (vY N l v) z
      ↔ reducido21 k b c d f g h i j l o p r s t u v w z N A := by
  unfold completo reducido21
  simp only []
  constructor
  · intro hh
    obtain ⟨_, e2, _, e4, e5, e6, e7, e8, _, e10, e11, _, _, e14⟩ := hh
    exact ⟨e2, e4, e5, e6, e7, e8, e10, e11, e14⟩
  · intro hh
    obtain ⟨e2, e4, e5, e6, e7, e8, e10, e11, e14⟩ := hh
    refine ⟨?_, e2, ?_, e4, e5, e6, e7, e8, ?_, e10, e11, ?_, ?_, e14⟩
    · unfold vQ; rfl
    · unfold vE vN vQ; rfl
    · unfold vY vN; rfl
    · unfold vM; rfl
    · unfold vX; rfl


/-! ## 4. El teorema: 25 incógnitas ⟶ 20, mismo grado

La ida usa las dos cotas de `Pell.lean`; la vuelta usa que las cinco
definiciones son ≥ 0, que es la sección 2. Sin las cotas la vuelta es FALSA:
`m` y `x` podrían salir negativas y no habría solución sobre ℕ que exhibir. -/

theorem equisatisfacible21 (k : Int) (hk : 0 ≤ k) :
    (∃ a b c d e f g h i j l m n o p q r s t u v w x y z : Int,
        (0 ≤ a ∧ 0 ≤ b ∧ 0 ≤ c ∧ 0 ≤ d ∧ 0 ≤ e ∧ 0 ≤ f ∧ 0 ≤ g ∧ 0 ≤ h ∧ 0 ≤ i
          ∧ 0 ≤ j ∧ 0 ≤ l ∧ 0 ≤ m ∧ 0 ≤ n ∧ 0 ≤ o ∧ 0 ≤ p ∧ 0 ≤ q ∧ 0 ≤ r
          ∧ 0 ≤ s ∧ 0 ≤ t ∧ 0 ≤ u ∧ 0 ≤ v ∧ 0 ≤ w ∧ 0 ≤ x ∧ 0 ≤ y ∧ 0 ≤ z)
        ∧ completo k a b c d e f g h i j l m n o p q r s t u v w x y z)
      ↔
    (∃ b c d f g h i j l o p r s t u v w z N A : Int,
        (0 ≤ b ∧ 0 ≤ c ∧ 0 ≤ d ∧ 0 ≤ f ∧ 0 ≤ g ∧ 0 ≤ h ∧ 0 ≤ i ∧ 0 ≤ j ∧ 0 ≤ l
          ∧ 0 ≤ o ∧ 0 ≤ p ∧ 0 ≤ r ∧ 0 ≤ s ∧ 0 ≤ t ∧ 0 ≤ u ∧ 0 ≤ v ∧ 0 ≤ w
          ∧ 0 ≤ z ∧ 0 ≤ N ∧ 0 ≤ A)
        ∧ reducido21 k b c d f g h i j l o p r s t u v w z N A) := by
  constructor
  · -- IDA. Las cotas de Pell dan los `N ≥ 0` y `A ≥ 0` de la reparametrización.
    rintro ⟨a, b, c, d, e, f, g, h, i, j, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z,
            ⟨ha, hb, hc, hd, he, hf, hg, hh, hi, hj, hl, hm, hn, ho, hp, hq, hr, hs,
             ht, hu, hv, hw, hx, hy, hz⟩, hsis⟩
    have hcopia := hsis
    obtain ⟨e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12, e13, e14⟩ := hcopia
    -- las dos ecuaciones que piden los lemas de Pell, sin `^`
    have e4' : 16*(k+1)*(k+1)*(k+1)*(k+2)*((n+1)*(n+1)) + 1 = f*f := by grind
    have e5' : e*e*e*(e+2)*((a+1)*(a+1)) + 1 = o*o := by grind
    have hn2 : 2 ≤ n := n_ge_two hk hn hf e4'
    have hae : e + 1 ≤ a := a_ge_e_succ_de_sistema hk hn hf hp hq hz ha ho e3 e4' e5'
    -- reparametrizar
    obtain ⟨N, hNn⟩ : ∃ N, n = N + 2 := ⟨n - 2, by omega⟩
    obtain ⟨A, hAa⟩ : ∃ A, a = e + 1 + A := ⟨a - e - 1, by omega⟩
    subst hNn; subst hAa
    -- y ahora las cinco definiciones son los valores reales, en cascada
    have hqv : q = vQ h j w z := by unfold vQ; omega
    subst hqv
    have hev : e = vE N p h j w z := by unfold vE vN; omega
    subst hev
    have hyv : y = vY N l v := by unfold vY vN; omega
    subst hyv
    have hmv : m = vM (vA N p h j w z A) (vN N) p l b := by
      unfold vM vA vN; omega
    subst hmv
    have hxv : x = vX (vA N p h j w z A) p (vQ h j w z) (vY N l v) s := by
      unfold vX vA; omega
    subst hxv
    refine ⟨b, c, d, f, g, h, i, j, l, o, p, r, s, t, u, v, w, z, N, A,
            ⟨hb, hc, hd, hf, hg, hh, hi, hj, hl, ho, hp, hr, hs, ht, hu, hv, hw, hz,
             by omega, by omega⟩, ?_⟩
    exact (completo_de_defs21 k b c d f g h i j l o p r s t u v w z N A).mp hsis
  · -- VUELTA. Aquí es donde hacen falta las no-negatividades de la sección 2:
    -- hay que EXHIBIR las cinco incógnitas eliminadas dentro de ℕ.
    rintro ⟨b, c, d, f, g, h, i, j, l, o, p, r, s, t, u, v, w, z, N, A,
            ⟨hb, hc, hd, hf, hg, hh, hi, hj, hl, ho, hp, hr, hs, ht, hu, hv, hw, hz,
             hN, hA⟩, hred⟩
    refine ⟨vA N p h j w z A, b, c, d, vE N p h j w z, f, g, h, i, j, l,
            vM (vA N p h j w z A) (vN N) p l b, vN N, o, p, vQ h j w z, r, s, t, u, v, w,
            vX (vA N p h j w z A) p (vQ h j w z) (vY N l v) s, vY N l v, z,
            ⟨vA_nonneg hN hp hh hj hw hz hA, hb, hc, hd,
             vE_nonneg hN hp hh hj hw hz, hf, hg, hh, hi, hj, hl,
             vM_nonneg hp hl hb (by unfold vN; omega)
               (vA_ge_vN_succ hN hp hh hj hw hz hA),
             (by unfold vN; omega), ho, hp, vQ_nonneg hh hj hw hz, hr, hs, ht, hu, hv, hw,
             vX_nonneg (vQ_nonneg hh hj hw hz) (vY_nonneg hN hl hv) hs hp
               (vA_ge_p_succ hN hp hh hj hw hz hA),
             vY_nonneg hN hl hv, hz⟩, ?_⟩
    exact (completo_de_defs21 k b c d f g h i j l o p r s t u v w z N A).mpr hred

end Diophantus
