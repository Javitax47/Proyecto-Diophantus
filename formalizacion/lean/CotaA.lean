/-
  DIOPHANTUS — `a ≥ 2` y `n ≥ 2` en el sistema (1) de Jones-Sato-Wada-Wiens
  =========================================================================
  Verificacion FORMAL del teorema de la seccion 3.2o del documento: el que
  desbloquea la reparametrizacion `a = A + 2` y con ella la cifra (33, 5).

  POR QUE ESTE TEOREMA Y NO OTRO. Es el unico resultado propio del proyecto que
  NO depende de que el sistema (1) represente los primos: es un enunciado sobre
  las soluciones del sistema, sea cual sea el conjunto que represente. Todo lo
  demas se apoya en el teorema de JSWW, que se CITA; esto no. Por tanto es lo
  unico que se puede verificar de arriba abajo sin importar nada.

  HIPOTESIS: solo CINCO de las catorce ecuaciones -- (3), (4), (5), (6) y (9) --.
  Usar menos hipotesis hace el teorema mas fuerte, y estas cinco bastan.

  FORMA SOBRE ℕ, SIN RESTAS. Las ecuaciones de JSWW estan escritas sobre ℤ con
  variables en ℕ. Aqui se pasan los terminos negativos al otro lado para que todo
  sea aritmetica de ℕ: `(a²-1)y² + 1 - x² = 0` se escribe `a²y² + 1 = y² + x²`.
  Es la misma ecuacion y evita la resta truncada de ℕ, que es una fuente clasica
  de teoremas que dicen algo distinto de lo que parecen.

  DEPENDENCIAS: ninguna. Solo el nucleo de Lean 4 (`omega`, `grind`,
  `Nat.pow_le_pow_left`). No usa Mathlib.
-/

namespace Diophantus

/-! ## 1. El motor: no hay cuadrados estrictamente entre dos consecutivos -/

/-- De `m² < f²` se sigue `m < f`. (Monotonia del cuadrado sobre ℕ.) -/
theorem lt_of_sq_lt {m f : Nat} (h : m ^ 2 < f ^ 2) : m < f := by
  cases Nat.lt_or_ge m f with
  | inl hlt => exact hlt
  | inr hge =>
      have h2 : f ^ 2 ≤ m ^ 2 := Nat.pow_le_pow_left hge 2
      omega

/-- **Lema del encaje.** Si `f²` cae estrictamente entre `m²` y `(m+1)²`, absurdo:
    obligaria a `m < f < m+1`. Es el motor de los tres pasos de la demostracion;
    cada uno se reduce a exhibir el `m` adecuado. -/
theorem sin_cuadrado_intermedio {m f : Nat}
    (h1 : m ^ 2 < f ^ 2) (h2 : f ^ 2 < (m + 1) ^ 2) : False := by
  have hlo : m < f := lt_of_sq_lt h1
  have hhi : f < m + 1 := lt_of_sq_lt h2
  omega

/-! ## 2. Paso 1: la ecuacion (4) fuerza `n ≥ 2` -/

/-- Ecuacion (4) de JSWW sobre ℕ: `16(k+1)³(k+2)(n+1)² + 1 = f²`. -/
def ec4 (k n f : Nat) : Prop := 16 * (k + 1) ^ 3 * (k + 2) * (n + 1) ^ 2 + 1 = f ^ 2

/-- `n = 0` es imposible: `f²` quedaria entre `(4k²+10k+5)²` y su siguiente.
    Los huecos son `4k²+12k+8` y `4k²+8k+3`, ambos con termino constante
    positivo, luego `> 0` para todo `k : ℕ`. -/
theorem n_ne_zero {k f : Nat} (h : ec4 k 0 f) : False := by
  unfold ec4 at h
  have hlo : (4 * k ^ 2 + 10 * k + 5) ^ 2 < f ^ 2 := by grind
  have hhi : f ^ 2 < (4 * k ^ 2 + 10 * k + 5 + 1) ^ 2 := by grind
  exact sin_cuadrado_intermedio hlo hhi

/-- `n = 1` es imposible: mismo encaje con `(8k²+20k+11)²`.
    Huecos: `8k+8` y `16k²+32k+15`. -/
theorem n_ne_one {k f : Nat} (h : ec4 k 1 f) : False := by
  unfold ec4 at h
  have hlo : (8 * k ^ 2 + 20 * k + 11) ^ 2 < f ^ 2 := by grind
  have hhi : f ^ 2 < (8 * k ^ 2 + 20 * k + 11 + 1) ^ 2 := by grind
  exact sin_cuadrado_intermedio hlo hhi

/-- **`n ≥ 2`.** Consecuencia inmediata de los dos anteriores. -/
theorem n_ge_two {k n f : Nat} (h : ec4 k n f) : 2 ≤ n := by
  match n with
  | 0 => exact absurd h n_ne_zero
  | 1 => exact absurd h n_ne_one
  | (m + 2) => omega

/-! ## 3. Pasos 2 y 3: `a ≠ 0` y `a ≠ 1` -/

/-- Ecuacion (5) sobre ℕ: `e³(e+2)(a+1)² + 1 = o²`. -/
def ec5 (e a o : Nat) : Prop := e ^ 3 * (e + 2) * (a + 1) ^ 2 + 1 = o ^ 2

/-- Con `a = 1`, la ecuacion (5) queda `4e⁴ + 8e³ + 1 = o²`, y para `e ≥ 1` hay
    otro encaje: entre `(2e²+2e-1)²` y `(2e²+2e)²`, con huecos `4e` y `4e²-1`.
    Luego `e = 0` forzosamente. -/
theorem e_eq_zero_of_a_one {e o : Nat} (h : ec5 e 1 o) : e = 0 := by
  unfold ec5 at h
  match e with
  | 0 => rfl
  | (j + 1) =>
      have hlo : (2 * j ^ 2 + 6 * j + 3) ^ 2 < o ^ 2 := by grind
      have hhi : o ^ 2 < (2 * j ^ 2 + 6 * j + 3 + 1) ^ 2 := by grind
      exact absurd (sin_cuadrado_intermedio hlo hhi) (fun x => x)

/-! ## 4. El teorema -/

/-- **`a ≥ 2` en toda solucion sobre ℕ del sistema (1) de Jones-Sato-Wada-Wiens.**

    Se usan solo las ecuaciones (3), (4), (5), (6) y (9):

    * (3) `2n + p + q + z = e`
    * (4) `16(k+1)³(k+2)(n+1)² + 1 = f²`
    * (5) `e³(e+2)(a+1)² + 1 = o²`
    * (6) `a²y² + 1 = y² + x²`   (o sea `(a²-1)y² + 1 = x²`)
    * (9) `n + l + v = y`

    La demostracion: (4) da `n ≥ 2`; con `a = 0`, (6) queda `x² + y² = 1` luego
    `y ≤ 1`, y (9) da `n ≤ y ≤ 1`, contradiccion; con `a = 1`, (5) fuerza `e = 0`
    y (3) da `n = 0`, contradiccion. -/
theorem a_ge_two {a e f k l n o p q v x y z : Nat}
    (h3 : 2 * n + p + q + z = e)
    (h4 : ec4 k n f)
    (h5 : ec5 e a o)
    (h6 : a ^ 2 * y ^ 2 + 1 = y ^ 2 + x ^ 2)
    (h9 : n + l + v = y) : 2 ≤ a := by
  have hn : 2 ≤ n := n_ge_two h4
  match a with
  | 0 =>
      -- (6) con a = 0 queda `1 = y² + x²`, luego `y ≤ 1`; con (9), `n ≤ 1`.
      -- La monotonia del cuadrado hay que darla a mano: `grind` no la aplica
      -- sola, y sin ella `2 ≤ y` no contradice `y² + x² = 1`.
      have hy : y ≤ 1 := by
        cases Nat.lt_or_ge y 2 with
        | inl h => omega
        | inr h =>
            have hy2 : 2 ^ 2 ≤ y ^ 2 := Nat.pow_le_pow_left h 2
            have h4 : 4 ≤ y ^ 2 := by simpa using hy2
            omega
      omega
  | 1 =>
      -- (5) con a = 1 fuerza `e = 0`; con (3), `n = 0`.
      have he : e = 0 := e_eq_zero_of_a_one h5
      omega
  | (m + 2) => omega

end Diophantus
