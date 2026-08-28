/-
  DIOPHANTUS — la ecuación de Pell `x² − (A²−1)y² = 1`, demostrada desde cero
  ===========================================================================
  Cierra el ÚNICO hueco que quedaba en la cadena del (21, 25): la cota
  `a ≥ e+1` se apoyaba en tres hechos sobre esta ecuación que se estaban
  CITANDO (los de Matiyasevich, que están en Mathlib). Aquí se demuestran.

  LOS TRES HECHOS, y para qué sirve cada uno:

    1. COMPLETITUD — toda solución con `y ≥ 0` es `(X j, Y j)` para algún `j`.
       Es el único que cuesta trabajo (descenso). Sin él no se puede indexar una
       solución arbitraria y los otros dos no sirven de nada.
    2. CONGRUENCIA — `Y j ≡ j (mod A−1)`. Convierte «`e` divide a `Y j`» en
       «`e` divide a `j`», y de ahí `j ≥ e`.
    3. CRECIMIENTO — `Y` es estrictamente creciente, luego `j ≥ 3 → Y j ≥ Y 3`.

  POR QUÉ ES ABORDABLE SIN MATHLIB. La teoría general de Pell es grande, pero
  aquí `D = A² − 1` está un cuadrado por debajo de `A²`, y eso hace que el paso y
  su inverso sean fórmulas cerradas:

      paso:      (x, y) ↦ (A·x + D·y,  x + A·y)
      descenso:  (x, y) ↦ (A·x − D·y,  A·y − x)

  Que sean inversas sale de `A² − D = 1`. Y las tres desigualdades del descenso
  (`x' ≥ 0`, `y' ≥ 0`, `y' < y`) salen todas del mismo truco: comparar cuadrados,
  que es exactamente la técnica de encaje de `CotaA.lean`.

  SOBRE ℤ, con `0 ≤ ·` explícito: el descenso RESTA, y sobre `Nat` la resta
  truncada convertiría un lema falso en uno que compila.

  DEPENDENCIAS: ninguna. Solo el núcleo de Lean 4.
-/

namespace Diophantus

/-! ## 0. Comparar cuadrados: el motor de todo el descenso -/

/-- Sobre los no negativos, `u² ≤ v² → u ≤ v`. -/
theorem le_of_sq_le {u v : Int} (hu : 0 ≤ u) (hv : 0 ≤ v) (h : u * u ≤ v * v) :
    u ≤ v := by
  by_cases hle : u ≤ v
  · exact hle
  · exfalso
    have hvu : v < u := by omega
    have h1 : v * v ≤ v * u := Int.mul_le_mul_of_nonneg_left (by omega) hv
    have h2 : v * u < u * u := Int.mul_lt_mul_of_pos_right hvu (by omega)
    omega

/-- Sobre los no negativos, `u² < v² → u < v`. -/
theorem lt_of_sq_lt {u v : Int} (hu : 0 ≤ u) (hv : 0 ≤ v) (h : u * u < v * v) :
    u < v := by
  by_cases hlt : u < v
  · exact hlt
  · exfalso
    have hvu : v ≤ u := by omega
    have h1 : v * v ≤ v * u := Int.mul_le_mul_of_nonneg_left hvu hv
    have h2 : v * u ≤ u * u := Int.mul_le_mul_of_nonneg_right hvu (by omega)
    omega

theorem one_le_sq {y : Int} (hy : 1 ≤ y) : 1 ≤ y * y := by
  have := Int.mul_le_mul_of_nonneg_left hy (by omega : (0:Int) ≤ y)
  omega

/-! ## 1. La sucesión de soluciones -/

/-- `D A = A² − 1`, el coeficiente de la ecuación. -/
def D (A : Int) : Int := A * A - 1

/-- Un paso hacia adelante: `(x, y) ↦ (A·x + D·y, x + A·y)`. -/
def paso (A : Int) (p : Int × Int) : Int × Int :=
  (A * p.1 + D A * p.2, p.1 + A * p.2)

/-- La sucesión de soluciones, desde la trivial `(1, 0)`. -/
def sol (A : Int) : Nat → Int × Int
  | 0 => (1, 0)
  | j + 1 => paso A (sol A j)

def X (A : Int) (j : Nat) : Int := (sol A j).1
def Y (A : Int) (j : Nat) : Int := (sol A j).2

theorem X_zero (A : Int) : X A 0 = 1 := rfl
theorem Y_zero (A : Int) : Y A 0 = 0 := rfl
theorem X_succ (A : Int) (j : Nat) : X A (j+1) = A * X A j + D A * Y A j := rfl
theorem Y_succ (A : Int) (j : Nat) : Y A (j+1) = X A j + A * Y A j := rfl

/-- `0 ≤ D A` cuando `A ≥ 2`. Hace falta en casi todos los pasos siguientes. -/
theorem D_nonneg {A : Int} (hA : 2 ≤ A) : 0 ≤ D A := by
  have h : 2 * A ≤ A * A := Int.mul_le_mul_of_nonneg_right hA (by omega)
  unfold D; omega

/-- La identidad del paso: `A² − D = 1` hace que el paso preserve la ecuación. -/
theorem paso_id (A x y : Int) :
    (A*x + (A*A-1)*y) * (A*x + (A*A-1)*y) - (A*A-1) * ((x + A*y) * (x + A*y))
      = x*x - (A*A-1)*(y*y) := by grind

/-- **Cada término de la sucesión ES una solución.** -/
theorem sol_pell (A : Int) (j : Nat) :
    X A j * X A j - D A * (Y A j * Y A j) = 1 := by
  induction j with
  | zero => simp [X_zero, Y_zero, D]
  | succ j ih =>
      rw [X_succ, Y_succ]
      unfold D at ih ⊢
      rw [paso_id]
      exact ih

/-! ## 2. Crecimiento (hecho 3) -/

/-- `X j ≥ 1` y `Y j ≥ 0`, conjuntamente: cada una hace falta para la otra. -/
theorem X_ge_one_and_Y_ge_zero {A : Int} (hA : 2 ≤ A) (j : Nat) :
    1 ≤ X A j ∧ 0 ≤ Y A j := by
  induction j with
  | zero => rw [X_zero, Y_zero]; omega
  | succ j ih =>
      obtain ⟨hx, hy⟩ := ih
      have hD : 0 ≤ D A := D_nonneg hA
      have h1 : A * 1 ≤ A * X A j := Int.mul_le_mul_of_nonneg_left hx (by omega)
      have h2 : 0 ≤ D A * Y A j := Int.mul_nonneg hD hy
      have h3 : 0 ≤ A * Y A j := Int.mul_nonneg (by omega) hy
      rw [X_succ, Y_succ]
      omega

theorem X_ge_one {A : Int} (hA : 2 ≤ A) (j : Nat) : 1 ≤ X A j :=
  (X_ge_one_and_Y_ge_zero hA j).1

theorem Y_ge_zero {A : Int} (hA : 2 ≤ A) (j : Nat) : 0 ≤ Y A j :=
  (X_ge_one_and_Y_ge_zero hA j).2

/-- **Crecimiento estricto:** `Y (j+1) = X j + A·Y j ≥ 1 + 2·Y j > Y j`. -/
theorem Y_lt_succ {A : Int} (hA : 2 ≤ A) (j : Nat) : Y A j < Y A (j+1) := by
  have hx := X_ge_one hA j
  have hy := Y_ge_zero hA j
  have h3 : 2 * Y A j ≤ A * Y A j := Int.mul_le_mul_of_nonneg_right hA hy
  rw [Y_succ]; omega

/-- Monotonía: `k ≤ j → Y k ≤ Y j`. -/
theorem Y_mono {A : Int} (hA : 2 ≤ A) {k j : Nat} (h : k ≤ j) : Y A k ≤ Y A j := by
  induction j with
  | zero =>
      have hk : k = 0 := by omega
      rw [hk]
      exact Int.le_refl _
  | succ j ih =>
      by_cases hk : k ≤ j
      · exact Int.le_trans (ih hk) (Int.le_of_lt (Y_lt_succ hA j))
      · have hkj : k = j + 1 := by omega
        rw [hkj]
        exact Int.le_refl _


/-! ## 3. Congruencia `Y j ≡ j (mod A−1)` (hecho 2)

Es lo que convierte una divisibilidad sobre el VALOR en una divisibilidad sobre
el ÍNDICE: `e ∣ Y j` pasa a ser `e ∣ j`, y de ahí `j ≥ e`. Se demuestra a la vez
con `X j ≡ 1 (mod A−1)`, porque la recurrencia mezcla las dos y por separado no
sale ninguna. -/

theorem X_Y_mod (A : Int) (j : Nat) :
    ∃ s t : Int, X A j = 1 + (A-1)*s ∧ Y A j = (j:Int) + (A-1)*t := by
  induction j with
  | zero => exact ⟨0, 0, by rw [X_zero]; grind, by rw [Y_zero]; simp⟩
  | succ j ih =>
      obtain ⟨s, t, hs, ht⟩ := ih
      refine ⟨1 + A*s + (A+1)*(j:Int) + (A-1)*(A+1)*t, s + (j:Int) + A*t, ?_, ?_⟩
      · rw [X_succ, hs, ht]; unfold D; grind
      · rw [Y_succ, hs, ht]
        have hc : ((j+1 : Nat) : Int) = (j:Int) + 1 := by simp
        rw [hc]; grind

/-- La mitad que se usa: `Y j − j` es múltiplo de `A − 1`. -/
theorem Y_mod (A : Int) (j : Nat) : ∃ t : Int, Y A j = (j:Int) + (A-1)*t := by
  obtain ⟨_, t, _, ht⟩ := X_Y_mod A j
  exact ⟨t, ht⟩

/-! ## 4. Completitud: toda solución está en la sucesión (hecho 1)

El descenso. Dada una solución `(x, y)` con `y ≥ 1`, su predecesora es
`(A·x − D·y, A·y − x)`, y hay que ver tres cosas: que sigue siendo solución
(identidad de anillo), que sigue en el dominio (`x' ≥ 0`, `y' ≥ 0`) y que
DECRECE (`y' < y`). Las tres desigualdades salen del mismo molde: una identidad
que `grind` normaliza, y luego comparar cuadrados. -/

/-- La identidad del descenso, gemela de `paso_id`. -/
theorem desc_id (A x y : Int) :
    (A*x - (A*A-1)*y) * (A*x - (A*A-1)*y)
      - (A*A-1) * ((A*y - x) * (A*y - x))
      = x*x - (A*A-1)*(y*y) := by grind

/-- (a) `x ≤ A·y`. Porque `(A·y)² − x² = y² − 1 ≥ 0`. -/
theorem desc_a {A x y : Int} (hA : 2 ≤ A) (hx : 0 ≤ x) (hy : 1 ≤ y)
    (hp : x*x = (A*A-1)*(y*y) + 1) : x ≤ A * y := by
  have hyy : 1 ≤ y * y := one_le_sq hy
  have key : (A*y)*(A*y) - x*x = y*y - 1 := by grind
  exact le_of_sq_le hx (Int.mul_nonneg (by omega) (by omega)) (by omega)

/-- (b) `D·y ≤ A·x`. Porque `(A·x)² − (D·y)² = D·y² + A² ≥ 0`. -/
theorem desc_b {A x y : Int} (hA : 2 ≤ A) (hx : 0 ≤ x) (hy : 1 ≤ y)
    (hp : x*x = (A*A-1)*(y*y) + 1) : (A*A-1) * y ≤ A * x := by
  have hD : 0 ≤ A*A - 1 := by
    have : 2 * A ≤ A * A := Int.mul_le_mul_of_nonneg_right hA (by omega)
    omega
  have hyy : 0 ≤ y * y := Int.mul_nonneg (by omega) (by omega)
  have hDyy : 0 ≤ (A*A-1) * (y*y) := Int.mul_nonneg hD hyy
  have hAA : 0 ≤ A * A := Int.mul_nonneg (by omega) (by omega)
  have key : (A*x)*(A*x) - ((A*A-1)*y)*((A*A-1)*y) = (A*A-1)*(y*y) + A*A := by grind
  exact le_of_sq_le (Int.mul_nonneg hD (by omega))
                    (Int.mul_nonneg (by omega) hx) (by omega)

/-- (c) `(A−1)·y < x`, que es lo que hace DECRECER al descenso.
    Porque `x² − ((A−1)y)² = (2A−2)y² + 1 > 0`. -/
theorem desc_c {A x y : Int} (hA : 2 ≤ A) (hx : 0 ≤ x) (hy : 1 ≤ y)
    (hp : x*x = (A*A-1)*(y*y) + 1) : (A-1) * y < x := by
  have hyy : 0 ≤ y * y := Int.mul_nonneg (by omega) (by omega)
  have h2 : 0 ≤ (2*A-2) * (y*y) := Int.mul_nonneg (by omega) hyy
  have key : x*x - ((A-1)*y)*((A-1)*y) = (2*A-2)*(y*y) + 1 := by grind
  exact lt_of_sq_lt (Int.mul_nonneg (by omega) (by omega)) hx (by omega)

theorem sq_eq_one {x : Int} (hx : 0 ≤ x) (h : x * x = 1) : x = 1 := by
  by_cases h2 : 2 ≤ x
  · have := Int.mul_le_mul_of_nonneg_right h2 (by omega : (0:Int) ≤ x)
    omega
  · have h01 : x = 0 ∨ x = 1 := by omega
    cases h01 with
    | inl h0 => rw [h0] at h; simp at h
    | inr h1 => exact h1

/-- **Completitud.** Toda solución con `x, y ≥ 0` es `(X j, Y j)` para algún `j`.

    La inducción va sobre una COTA `n` de `y`, no sobre `y`: así el descenso
    --que baja `y` una cantidad no controlada-- encaja en una inducción
    ordinaria, sin necesidad de recursión bien fundada. -/
theorem completitud {A : Int} (hA : 2 ≤ A) :
    ∀ (n : Nat) (x y : Int), 0 ≤ x → 0 ≤ y → y ≤ (n:Int) →
      x*x - D A * (y*y) = 1 → ∃ j, x = X A j ∧ y = Y A j := by
  intro n
  induction n with
  | zero =>
      intro x y hx hy hyn hp
      have hy0 : y = 0 := by simp at hyn; omega
      rw [hy0] at hp
      have hx1 : x = 1 := sq_eq_one hx (by unfold D at hp; simp at hp; omega)
      exact ⟨0, by rw [hx1, X_zero], by rw [hy0, Y_zero]⟩
  | succ n ih =>
      intro x y hx hy hyn hp
      by_cases hy0 : y = 0
      · rw [hy0] at hp
        have hx1 : x = 1 := sq_eq_one hx (by unfold D at hp; simp at hp; omega)
        exact ⟨0, by rw [hx1, X_zero], by rw [hy0, Y_zero]⟩
      · have hy1 : 1 ≤ y := by omega
        have hp' : x*x = (A*A-1)*(y*y) + 1 := by unfold D at hp; omega
        have ha := desc_a hA hx hy1 hp'
        have hb := desc_b hA hx hy1 hp'
        have hc := desc_c hA hx hy1 hp'
        have hlin : (A-1)*y = A*y - y := by grind
        have hp2 : (A*x - (A*A-1)*y) * (A*x - (A*A-1)*y)
                    - D A * ((A*y - x) * (A*y - x)) = 1 := by
          unfold D; rw [desc_id]; unfold D at hp; exact hp
        have hcota : A*y - x ≤ (n:Int) := by
          have hc1 : ((n+1 : Nat) : Int) = (n:Int) + 1 := by simp
          rw [hc1] at hyn; omega
        obtain ⟨j, hxj, hyj⟩ :=
          ih (A*x - (A*A-1)*y) (A*y - x) (by omega) (by omega) hcota hp2
        refine ⟨j+1, ?_, ?_⟩
        · rw [X_succ, ← hxj, ← hyj]; unfold D; grind
        · rw [Y_succ, ← hxj, ← hyj]; grind

/-! ## 5. La aplicación: `a ≥ e+1` en el sistema (1) de JSWW

Este es el enunciado que se estaba CITANDO y que ahora queda demostrado. Sale de
la ecuación (5) sola, `o² = e³(e+2)(a+1)² + 1`, más `e ≥ 4` (que da `n ≥ 2`, ya
demostrado en `CotaA.lean`, junto con `e ≥ 2n` de la ecuación (3)).

LA CLAVE ES UNA FACTORIZACIÓN, y es lo único que hay que ver para creerse el
resto:

    e³(e+2) = e²·(e² + 2e) = e²·((e+1)² − 1)

O sea que poniendo `Z = e·(a+1)` la ecuación (5) ES la Pell de `A = e+1`. Y
entonces `e ∣ Z` obliga, vía la congruencia, a que el índice `j` sea múltiplo de
`e`; como `j ≥ 1`, resulta `j ≥ e ≥ 4`, y el crecimiento hace el resto. -/

/-- `Y A 3 = 4A² − 1`, que es el término al que llega el crecimiento. -/
theorem Y_tres (A : Int) : Y A 3 = 4*A*A - 1 := by
  simp [Y, sol, paso, D]; grind

/-- **`a ≥ e+1`.** El hueco cerrado.

    Hipótesis: la ecuación (5) de JSWW y `e ≥ 4`. Nada más — ni el resto del
    sistema, ni que represente los primos. -/
theorem a_ge_e_succ {e a o : Int}
    (he : 4 ≤ e) (ha : 0 ≤ a) (ho : 0 ≤ o)
    (h5 : o * o = e*e*e * (e+2) * ((a+1) * (a+1)) + 1) : e + 1 ≤ a := by
  -- `A = e+1`, y la ec.(5) es la Pell de `A` con `Z = e(a+1)`.
  have hA : 2 ≤ e + 1 := by omega
  have hZ0 : 0 ≤ e * (a+1) := Int.mul_nonneg (by omega) (by omega)
  have hpell : o * o - D (e+1) * ((e*(a+1)) * (e*(a+1))) = 1 := by
    unfold D; grind
  -- toda solucion esta en la sucesion (hecho 1)
  have hcota : e * (a+1) ≤ (((e * (a+1)).toNat : Nat) : Int) := by
    rw [Int.toNat_of_nonneg hZ0]; exact Int.le_refl _
  obtain ⟨j, _, hj⟩ :=
    completitud hA (e * (a+1)).toNat o (e*(a+1)) ho hZ0 hcota hpell
  -- la congruencia (hecho 2) manda la divisibilidad al INDICE
  obtain ⟨t, ht⟩ := Y_mod (e+1) j
  have hje : (j:Int) = e * ((a+1) - t) := by
    have : e * (a+1) = (j:Int) + ((e+1) - 1) * t := by rw [hj, ht]
    grind
  -- `j ≥ 1`: si fuera 0, `Z = Y 0 = 0`, pero `Z = e(a+1) ≥ 4`
  have hj1 : 1 ≤ (j:Int) := by
    by_cases h0 : j = 0
    · exfalso
      rw [h0, Y_zero] at hj
      have : 1 * 1 ≤ e * (a+1) :=
        Int.mul_le_mul (by omega) (by omega) (by omega) (by omega)
      omega
    · omega
  -- `e ∣ j` y `j ≥ 1` dan `j ≥ e`
  have hjge : e ≤ (j:Int) := by
    have hm : 1 ≤ (a+1) - t := by
      by_cases h : 1 ≤ (a+1) - t
      · exact h
      · exfalso
        have : e * ((a+1) - t) ≤ e * 0 :=
          Int.mul_le_mul_of_nonneg_left (by omega) (by omega)
        omega
    have := Int.mul_le_mul_of_nonneg_left hm (by omega : (0:Int) ≤ e)
    omega
  -- el crecimiento (hecho 3) desde `Y 3`
  have hj3 : 3 ≤ j := by omega
  have hmono : Y (e+1) 3 ≤ Y (e+1) j := Y_mono hA hj3
  rw [Y_tres] at hmono
  -- `4(e+1)² − 1 ≥ e(e+2)`, y se cancela el factor `e`
  -- `4(e+1)² − 1 ≥ e(e+2)`: la diferencia es `3(e+1)²`, un cuadrado.
  rw [← hj] at hmono
  have hee : 0 ≤ e * e := Int.mul_nonneg (by omega) (by omega)
  have hcuad : e * (e+2) ≤ 4*(e+1)*(e+1) - 1 := by grind
  have hfin : e * (e+2) ≤ e * (a+1) := Int.le_trans hcuad hmono
  have := Int.le_of_mul_le_mul_left hfin (by omega : (0:Int) < e)
  omega


/-! ## 6. Cerrar la cadena: `e ≥ 4` también se demuestra

`a_ge_e_succ` pide `e ≥ 4`. Eso sale de `n ≥ 2` --que ya está demostrado en
`CotaA.lean`, pero sobre ℕ-- más la ecuación (3). Para no dejar el eslabón
colgando entre dos formalizaciones con dominios distintos, se rehace aquí sobre
ℤ: es el mismo encaje de cuadrados, y así el teorema final tiene por hipótesis
sólo las ecuaciones (3), (4) y (5) del sistema (1) y las no negatividades. -/

/-- Encaje sobre ℤ: no hay cuadrados estrictamente entre `m²` y `(m+1)²`. -/
theorem sin_cuadrado_intermedio {m f : Int} (hm : 0 ≤ m) (hf : 0 ≤ f)
    (h1 : m*m < f*f) (h2 : f*f < (m+1)*(m+1)) : False := by
  have hlo : m < f := lt_of_sq_lt hm hf h1
  have hhi : f < m + 1 := lt_of_sq_lt hf (by omega) h2
  omega

/-- **`n ≥ 2`** desde la ecuación (4), sobre ℤ. Los dos casos imposibles son
    encajes: para `n = 0` entre `(4k²+10k+5)²` y su siguiente (huecos `4k²+12k+8`
    y `4k²+8k+3`), y para `n = 1` entre `(8k²+20k+11)²` y su siguiente (huecos
    `8k+8` y `16k²+32k+15`). Todos con término constante positivo. -/
theorem n_ge_two {k n f : Int} (hk : 0 ≤ k) (hn : 0 ≤ n) (hf : 0 ≤ f)
    (h4 : 16*(k+1)*(k+1)*(k+1)*(k+2)*((n+1)*(n+1)) + 1 = f*f) : 2 ≤ n := by
  have hkk : 0 ≤ k * k := Int.mul_nonneg hk hk
  by_cases h2 : 2 ≤ n
  · exact h2
  · exfalso
    have h01 : n = 0 ∨ n = 1 := by omega
    cases h01 with
    | inl h0 =>
        subst h0
        refine sin_cuadrado_intermedio (m := 4*(k*k) + 10*k + 5) (by omega) hf ?_ ?_
        · grind
        · grind
    | inr h1 =>
        subst h1
        refine sin_cuadrado_intermedio (m := 8*(k*k) + 20*k + 11) (by omega) hf ?_ ?_
        · grind
        · grind

/-- **EL TEOREMA, con la cadena entera.** Las hipótesis son exactamente las
    ecuaciones (3), (4) y (5) del sistema (1) de Jones-Sato-Wada-Wiens, más que
    las incógnitas vivan en ℕ. La conclusión es la cota que desbloquea las tres
    eliminaciones y con ellas el **(21, 25)**.

    Ya no se cita nada: `n ≥ 2` es el encaje de aquí arriba, `e ≥ 2n` es la
    ecuación (3), y `a ≥ e+1` es toda la maquinaria de Pell de las secciones 1-5. -/
theorem a_ge_e_succ_de_sistema {k n f p q z e a o : Int}
    (hk : 0 ≤ k) (hn : 0 ≤ n) (hf : 0 ≤ f) (hp : 0 ≤ p) (hq : 0 ≤ q) (hz : 0 ≤ z)
    (ha : 0 ≤ a) (ho : 0 ≤ o)
    (h3 : 2*n + p + q + z = e)
    (h4 : 16*(k+1)*(k+1)*(k+1)*(k+2)*((n+1)*(n+1)) + 1 = f*f)
    (h5 : e*e*e*(e+2)*((a+1)*(a+1)) + 1 = o*o) : e + 1 ≤ a := by
  have hn2 : 2 ≤ n := n_ge_two hk hn hf h4
  have he : 4 ≤ e := by omega
  exact a_ge_e_succ he ha ho h5.symm

end Diophantus
