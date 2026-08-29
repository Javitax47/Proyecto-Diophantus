/-
  DIOPHANTUS — Las cotas que desbloquean las eliminaciones de la sección 3
  ========================================================================
  Verificación FORMAL de siete de las ocho cotas que bloquean las catorce
  eliminaciones del Teorema 3.9 de Jones-Sato-Wada-Wiens (AMM 83:6 (1976)
  449-464, pp. 456-457).

  QUÉ PROBLEMA RESUELVE. El criterio de soundness del proyecto para eliminar una
  incógnita `u` definida por `u = expr` es que `expr` tenga todos los
  coeficientes ≥ 0, y por tanto sea ≥ 0 automáticamente sobre ℕ. Ese criterio es
  SUFICIENTE pero no necesario, y sobre el sistema de la sección 3 se queda corto:
  de las catorce incógnitas que JSWW eliminan por sustitución, sólo seis lo pasan.
  Las otras ocho están bloqueadas por una resta cada una — `A²−1`, `G²−1`, `F−A`,
  `Mx−1`, `Mnx−1`, `n−k+1`, `(z+1)(k+1)−2` — que son no negativas por razones que
  el criterio no ve. Aquí se demuestran SIETE de esas razones.

  LO QUE NO ESTÁ, y se dice por delante. Sólo queda `S`, que pide
  `(z+1)(k+1) ≥ 2`, y sólo en `k = 0`: para `k ≥ 1` está demostrada aquí
  (`S_nonneg_de_k_pos`). En `k = 0` falla cuando `z = 0`, y NO se deduce de las
  demás ecuaciones porque `z` sólo aparece en (XXI): ninguna otra lo restringe.
  Lo que `S ≥ 0` dice en el sistema original es exactamente que ese par no es
  solución, y al eliminar `S` esa información se pierde. Recuperarla obliga a
  mirar (XIV) con `S+1 = 0` — o sea que `S` y la hipótesis heredada de (XIV) son
  EL MISMO hueco, no dos, y está confinado a un único valor del parámetro.

  DEPENDENCIAS: `Pell.lean` (de este mismo proyecto) — `one_le_sq` y `n_ge_two`
  para la parte elemental, y `completitud`, `Y_mod`, `Y_mono` e `Y_tres` para la
  cota de `K`. Nada de Mathlib.
-/

import Pell

namespace Diophantus

/-! ## 0. Dos piezas de aritmética que se usan por todas partes -/

/-- `1 ≤ a` y `1 ≤ b` dan `1 ≤ a·b`. La versión de `one_le_sq` con dos factores
    distintos; se usa en casi todos los pasos de la cadena. -/
theorem one_le_mul {a b : Int} (ha : 1 ≤ a) (hb : 1 ≤ b) : 1 ≤ a * b := by
  have h1 : a * 1 ≤ a * b := Int.mul_le_mul_of_nonneg_left hb (by omega)
  have h2 : a * 1 = a := Int.mul_one a
  omega

/-- `1 ≤ a` da `a ≤ a·a`. Hace falta para cerrar `F ≥ A` con `omega`, que trata
    `a*a` como un átomo y necesita que la relación con `a` venga dada. -/
theorem self_le_sq {a : Int} (ha : 1 ≤ a) : a ≤ a * a := by
  have h1 : 1 * a ≤ a * a := Int.mul_le_mul_of_nonneg_right ha (by omega)
  have h2 : 1 * a = a := Int.one_mul a
  omega

/-! ## 1. La cadena elemental: `M`, `A`, `C`, `D`, `E`, `F`, `G`, `I`

Cada eslabón se apoya sólo en el anterior y en que las incógnitas vivan en ℕ.
Las ecuaciones son (III), (IV), (V), (VI), (VIII), (IX), (X), (XI), (XIII) del
Teorema 3.9, escritas tal cual. -/

/-- (III): `M = 16nx(w+2)+1`. Todo es ≥ 0, luego `M ≥ 1`. -/
theorem M_ge_one {n x w M : Int} (hn : 0 ≤ n) (hx : 0 ≤ x) (hw : 0 ≤ w)
    (h : M = 16 * n * x * (w + 2) + 1) : 1 ≤ M := by
  have h1 : 0 ≤ 16 * n := by omega
  have h2 : 0 ≤ 16 * n * x := Int.mul_nonneg h1 hx
  have h3 : 0 ≤ 16 * n * x * (w + 2) := Int.mul_nonneg h2 (by omega)
  omega

/-- (IV): `A = M(x+1)` con `M ≥ 1` y `x ≥ 0`, luego `A ≥ 1`. -/
theorem A_ge_one {x M A : Int} (hM : 1 ≤ M) (hx : 0 ≤ x)
    (h : A = M * (x + 1)) : 1 ≤ A := by
  have := one_le_mul hM (by omega : (1:Int) ≤ x + 1)
  omega

/-- (V) y (VI): `B = n+1`, `C = m+B`, luego `C ≥ 1`. -/
theorem C_ge_one {m n B C : Int} (hm : 0 ≤ m) (hn : 0 ≤ n)
    (hB : B = n + 1) (hC : C = m + B) : 1 ≤ C := by omega

/-- (VIII): `D = (A²−1)C²+1`. **Ésta es la cota que desbloquea `D`**: el criterio
    estructural la rechaza por el `−1`, y `A ≥ 1` la salva. -/
theorem D_ge_one {A C D : Int} (hA : 1 ≤ A) (hC : 1 ≤ C)
    (h : D = (A * A - 1) * (C * C) + 1) : 1 ≤ D := by
  have hAA : 1 ≤ A * A := one_le_sq hA
  have hCC : 1 ≤ C * C := one_le_sq hC
  have : 0 ≤ (A * A - 1) * (C * C) := Int.mul_nonneg (by omega) (by omega)
  omega

/-- (IX): `E = 2(i+1)DC²`, luego `E ≥ 2`. Es lo que después da `F ≥ A`. -/
theorem E_ge_two {i C D E : Int} (hi : 0 ≤ i) (hC : 1 ≤ C) (hD : 1 ≤ D)
    (h : E = 2 * (i + 1) * D * (C * C)) : 2 ≤ E := by
  have hCC : 1 ≤ C * C := one_le_sq hC
  have h1 : 1 ≤ (i + 1) * D := one_le_mul (by omega) hD
  have h2 : 1 ≤ (i + 1) * D * (C * C) := one_le_mul h1 hCC
  have h3 : E = 2 * ((i + 1) * D * (C * C)) := by grind
  omega

/-- (X): `F = (A²−1)E²+1`. **Desbloquea `F`** (mismo `−1` que `D`) y de paso da
    `F ≥ A`, que es lo que **desbloquea `G`**.

    La cuenta: `E ≥ 2` da `E² ≥ 4`, luego `F ≥ 4(A²−1)+1 = 4A²−3`, y
    `4A²−3−A = (A−1)(4A+3) ≥ 0` porque `A ≥ 1`. -/
theorem F_ge_A {A E F : Int} (hA : 1 ≤ A) (hE : 2 ≤ E)
    (h : F = (A * A - 1) * (E * E) + 1) : A ≤ F := by
  have hAA : 1 ≤ A * A := one_le_sq hA
  have hAsq : A ≤ A * A := self_le_sq hA
  have hEE : 4 ≤ E * E := by
    have h1 : 2 * 2 ≤ E * E := Int.mul_le_mul hE hE (by omega) (by omega)
    omega
  have hmul : (A * A - 1) * 4 ≤ (A * A - 1) * (E * E) :=
    Int.mul_le_mul_of_nonneg_left hEE (by omega)
  omega

/-- (XI): `G = A + F(F−A)` con `A ≥ 1` y `F ≥ A`, luego `G ≥ 1`. **Desbloquea
    `G`**, que el criterio rechaza por la resta `F−A`. -/
theorem G_ge_one {A F G : Int} (hA : 1 ≤ A) (hF : A ≤ F)
    (h : G = A + F * (F - A)) : 1 ≤ G := by
  have : 0 ≤ F * (F - A) := Int.mul_nonneg (by omega) (by omega)
  omega

/-- (XIII): `I = (G²−1)H²+1` con `G ≥ 1`. **Desbloquea `I`** (el `−1` de `G²−1`). -/
theorem I_ge_one {G H I : Int} (hG : 1 ≤ G) (hH : 0 ≤ H)
    (h : I = (G * G - 1) * (H * H) + 1) : 1 ≤ I := by
  have hGG : 1 ≤ G * G := one_le_sq hG
  have hHH : 0 ≤ H * H := Int.mul_nonneg hH hH
  have : 0 ≤ (G * G - 1) * (H * H) := Int.mul_nonneg (by omega) hHH
  omega

/-! ## 2. `n ≥ 2` y `x ≥ 2`: el encaje de cuadrados, reutilizado dos veces

`U(X,Y) = (X+2)³(X+4)(Y+1)²+1` (Definición 3.7). Desarrollado, `U(2k,n)` es
`16(k+1)³(k+2)(n+1)²+1`, que es LITERALMENTE la ecuación (4) del sistema (1) de
la sección 2 — la que `Pell.n_ge_two` ya trata. Así que el mismo lema sirve para
(I) y para (II), sin más que instanciarlo. -/

/-- La forma desarrollada de `U(2k,n)`, para poder aplicar `n_ge_two`. -/
theorem U_desarrollada (k n : Int) :
    (2*k + 2)*(2*k + 2)*(2*k + 2)*(2*k + 4)*((n+1)*(n+1)) + 1
      = 16*(k+1)*(k+1)*(k+1)*(k+2)*((n+1)*(n+1)) + 1 := by grind

/-- **(I) fuerza `n ≥ 2`.** -/
theorem n_ge_two_de_I {k n c : Int} (hk : 0 ≤ k) (hn : 0 ≤ n) (hc : 0 ≤ c)
    (h : (2*k + 2)*(2*k + 2)*(2*k + 2)*(2*k + 4)*((n+1)*(n+1)) + 1 = c*c) :
    2 ≤ n :=
  n_ge_two hk hn hc (by rw [← U_desarrollada]; exact h)

/-- **(II) fuerza `x ≥ 2`.** Misma ecuación con `k := n` y `n := x`; es la razón
    de que baste un solo lema para las dos. -/
theorem x_ge_two_de_II {n x c : Int} (hn : 0 ≤ n) (hx : 0 ≤ x) (hc : 0 ≤ c)
    (h : (2*n + 2)*(2*n + 2)*(2*n + 2)*(2*n + 4)*((x+1)*(x+1)) + 1 = c*c) :
    2 ≤ x :=
  n_ge_two hn hx hc (by rw [← U_desarrollada]; exact h)

/-! ## 3. `L` y `R`: lo que se saca de `n ≥ 2` y `x ≥ 2` -/

/-- (XIX): `L = k+1+l(Mx−1)`. **Desbloquea `L`**: basta `Mx ≥ 1`. -/
theorem L_nonneg {k l M x L : Int} (hk : 0 ≤ k) (hl : 0 ≤ l)
    (hM : 1 ≤ M) (hx : 1 ≤ x) (h : L = k + 1 + l * (M * x - 1)) : 0 ≤ L := by
  have hMx : 1 ≤ M * x := one_le_mul hM hx
  have : 0 ≤ l * (M * x - 1) := Int.mul_nonneg hl (by omega)
  omega

/-- (XX): `R = k+1+r(Mnx−1)`. **Desbloquea `R`**: basta `Mnx ≥ 1`. -/
theorem R_nonneg {k r M n x R : Int} (hk : 0 ≤ k) (hr : 0 ≤ r)
    (hM : 1 ≤ M) (hn : 1 ≤ n) (hx : 1 ≤ x)
    (h : R = k + 1 + r * (M * n * x - 1)) : 0 ≤ R := by
  have hMn : 1 ≤ M * n := one_le_mul hM hn
  have hMnx : 1 ≤ M * n * x := one_le_mul hMn hx
  have : 0 ≤ r * (M * n * x - 1) := Int.mul_nonneg hr (by omega)
  omega

/-! ## 4. `K`: la misma ecuación (I), leída como una Pell

`Pell.lean` demuestra la completitud, la congruencia y el crecimiento para
`x² − (A²−1)y² = 1`. La ecuación (I) parecía no ser de esa forma —el coeficiente
es `16(k+1)³(k+2)`, y con `m = k+1` la Pell natural es la de `d = m(m+1)`, que no
es `A²−1`—. Pero **sí lo es**, y la cuenta es de una línea:

```
16m³(m+1)(n+1)²  =  (4m² + 4m) · (2m(n+1))²  =  ((2m+1)² − 1) · (2m(n+1))²
```

O sea `A = 2m+1 = 2k+3` y `y = 2(k+1)(n+1)`. Con eso, `Pell.lean` se aplica tal
cual: la congruencia manda `2(k+1) ∣ y` al índice, `j ≥ 2(k+1) ≥ 4 > 3`, y el
crecimiento desde `Y 3 = 4A²−1` da `2(k+1)(n+1) ≥ 16k²+48k+35`, de donde
`n+1 ≥ 8k`, y en particular `n+1 ≥ k`. -/

/-- **(I) fuerza `k ≤ n+1`.** Es lo que desbloquea `K`, y de hecho da mucho más:
    `n+1 ≥ 8(k+1)`. La cota fina de JSWW es `n > (2k)^(2k)`; aquí basta la burda.

    Para `k = 0` es trivial y se despacha aparte, porque `j ≥ 2(k+1)` sólo llega
    a `3` cuando `k ≥ 1`. -/
theorem n_succ_ge_k {k n c : Int} (hk : 0 ≤ k) (hn : 0 ≤ n) (hc : 0 ≤ c)
    (h : (2*k + 2)*(2*k + 2)*(2*k + 2)*(2*k + 4)*((n+1)*(n+1)) + 1 = c*c) :
    k ≤ n + 1 := by
  by_cases hk0 : k ≤ 0
  · omega
  · have hk1 : 1 ≤ k := by omega
    have hA : (2:Int) ≤ 2*k + 3 := by omega
    have hZ0 : 0 ≤ 2*(k+1)*(n+1) :=
      Int.mul_nonneg (by omega) (by omega)
    -- (I) ES la Pell de `A = 2k+3` con `y = 2(k+1)(n+1)`
    have hpell : c*c - D (2*k + 3) * ((2*(k+1)*(n+1)) * (2*(k+1)*(n+1))) = 1 := by
      unfold D; grind
    have hcota : 2*(k+1)*(n+1) ≤ (((2*(k+1)*(n+1)).toNat : Nat) : Int) := by
      rw [Int.toNat_of_nonneg hZ0]; exact Int.le_refl _
    obtain ⟨j, _, hj⟩ :=
      completitud hA (2*(k+1)*(n+1)).toNat c (2*(k+1)*(n+1)) hc hZ0 hcota hpell
    -- la congruencia manda la divisibilidad al ÍNDICE
    obtain ⟨t, ht⟩ := Y_mod (2*k + 3) j
    have hje : (j:Int) = (2*(k+1)) * ((n+1) - t) := by
      have : 2*(k+1)*(n+1) = (j:Int) + ((2*k + 3) - 1) * t := by rw [hj, ht]
      grind
    have hj1 : 1 ≤ (j:Int) := by
      by_cases h0 : j = 0
      · exfalso
        rw [h0, Y_zero] at hj
        have : 1 * 1 ≤ 2*(k+1)*(n+1) :=
          Int.mul_le_mul (by omega) (by omega) (by omega) (by omega)
        omega
      · omega
    have hjge : 2*(k+1) ≤ (j:Int) := by
      have hpos : 1 ≤ (n+1) - t := by
        by_cases hb : 1 ≤ (n+1) - t
        · exact hb
        · exfalso
          have : (2*(k+1)) * ((n+1) - t) ≤ (2*(k+1)) * 0 :=
            Int.mul_le_mul_of_nonneg_left (by omega) (by omega)
          omega
      have := Int.mul_le_mul_of_nonneg_left hpos (by omega : (0:Int) ≤ 2*(k+1))
      omega
    -- el crecimiento desde `Y 3`
    have hj3 : 3 ≤ j := by omega
    have hmono : Y (2*k + 3) 3 ≤ Y (2*k + 3) j := Y_mono hA hj3
    rw [Y_tres, ← hj] at hmono
    have hkk : 0 ≤ k * k := Int.mul_nonneg hk hk
    have hexp : 4*(2*k + 3)*(2*k + 3) - 1 = 16*(k*k) + 48*k + 35 := by grind
    have hexp2 : (2*(k+1)) * k = 2*(k*k) + 2*k := by grind
    have hstep : (2*(k+1)) * k ≤ (2*(k+1)) * (n+1) := by omega
    exact Int.le_of_mul_le_mul_left hstep (by omega)

/-- (XVIII): `K = n−k+1+p(M−1)`. **Desbloquea `K`**: basta `k ≤ n+1` y `M ≥ 1`. -/
theorem K_nonneg {k n p M K : Int} (hp : 0 ≤ p) (hM : 1 ≤ M) (hkn : k ≤ n + 1)
    (h : K = n - k + 1 + p * (M - 1)) : 0 ≤ K := by
  have : 0 ≤ p * (M - 1) := Int.mul_nonneg hp (by omega)
  omega

/-! ## 5. `S`: el hueco, acotado a un único valor del parámetro

`S = (z+1)(k+1) − 2` pide `(z+1)(k+1) ≥ 2`, y eso **falla en un solo punto**:
`z = 0` y `k = 0`. Para `k ≥ 1` sale gratis, porque `(z+1)(k+1) ≥ 1·2 = 2` sin
usar ninguna otra ecuación. Así que el hueco no es «`S` no está demostrada»: es
«`S` no está demostrada **en `k = 0`**», y ahí coincide con la hipótesis heredada
de (XIV). Vale la pena tenerlo dicho con esta precisión, porque cualquier cifra
que se saque del sistema reducido es correcta para todo `k ≥ 1`. -/

/-- (XXI) con `k ≥ 1`: `S = (z+1)(k+1)−2 ≥ 0`. Sin usar ninguna otra ecuación. -/
theorem S_nonneg_de_k_pos {k z S : Int} (hk : 1 ≤ k) (hz : 0 ≤ z)
    (h : S = (z + 1) * (k + 1) - 2) : 0 ≤ S := by
  have : 1 * 2 ≤ (z + 1) * (k + 1) :=
    Int.mul_le_mul (by omega) (by omega) (by omega) (by omega)
  omega

/-! ## 6. El teorema: las siete cotas a la vez, desde las ecuaciones -/

/-- **LAS SIETE COTAS QUE DESBLOQUEAN LAS SIETE ELIMINACIONES.**

    Hipótesis: que las incógnitas vivan en ℕ, y quince de las veintiuna
    condiciones del Teorema 3.9 — (I), (II), (III), (IV), (V), (VI), (VIII), (IX),
    (X), (XI), (XII), (XIII), (XVIII), (XIX), (XX). No se usa (VII), ni (XV)-(XVII),
    ni (XXI); en particular **no se usa la desigualdad (XIV)**, que es la única
    condición de la transcripción que arrastra una hipótesis heredada.

    Conclusión: `D`, `F`, `G`, `I`, `K`, `L` y `R` son ≥ 0 en toda solución, luego
    las siete se pueden eliminar por sustitución sin perder soluciones. Con las
    seis que ya pasaban el criterio estructural (`M`, `A`, `B`, `C`, `E`, `H`) son
    **trece de las catorce** que JSWW eliminan en la p. 461. La que falta es `S`. -/
theorem cotas_seccion_tres
    {k n x w m i j l p r c1 c2 M A B C D E F G H I K L R : Int}
    (hk : 0 ≤ k) (hn : 0 ≤ n) (hx : 0 ≤ x) (hw : 0 ≤ w) (hm : 0 ≤ m)
    (hi : 0 ≤ i) (hj : 0 ≤ j) (hl : 0 ≤ l) (hp : 0 ≤ p) (hr : 0 ≤ r)
    (hc1 : 0 ≤ c1) (hc2 : 0 ≤ c2)
    (eI  : (2*k + 2)*(2*k + 2)*(2*k + 2)*(2*k + 4)*((n+1)*(n+1)) + 1 = c1*c1)
    (eII : (2*n + 2)*(2*n + 2)*(2*n + 2)*(2*n + 4)*((x+1)*(x+1)) + 1 = c2*c2)
    (eIII : M = 16 * n * x * (w + 2) + 1)
    (eIV : A = M * (x + 1))
    (eV : B = n + 1)
    (eVI : C = m + B)
    (eVIII : D = (A * A - 1) * (C * C) + 1)
    (eIX : E = 2 * (i + 1) * D * (C * C))
    (eX : F = (A * A - 1) * (E * E) + 1)
    (eXI : G = A + F * (F - A))
    (eXII : H = B + 2 * (j + 1) * C)
    (eXIII : I = (G * G - 1) * (H * H) + 1)
    (eXVIII : K = n - k + 1 + p * (M - 1))
    (eXIX : L = k + 1 + l * (M * x - 1))
    (eXX : R = k + 1 + r * (M * n * x - 1)) :
    0 ≤ D ∧ 0 ≤ F ∧ 0 ≤ G ∧ 0 ≤ I ∧ 0 ≤ K ∧ 0 ≤ L ∧ 0 ≤ R := by
  have hn2 : 2 ≤ n := n_ge_two_de_I hk hn hc1 eI
  have hx2 : 2 ≤ x := x_ge_two_de_II hn hx hc2 eII
  have hM : 1 ≤ M := M_ge_one hn hx hw eIII
  have hA : 1 ≤ A := A_ge_one hM hx eIV
  have hC : 1 ≤ C := C_ge_one hm hn eV eVI
  have hD : 1 ≤ D := D_ge_one hA hC eVIII
  have hE : 2 ≤ E := E_ge_two hi hC hD eIX
  have hF : A ≤ F := F_ge_A hA hE eX
  have hG : 1 ≤ G := G_ge_one hA hF eXI
  have hH : 0 ≤ H := by
    have : 0 ≤ 2 * (j + 1) * C := Int.mul_nonneg (by omega) (by omega)
    omega
  have hI : 1 ≤ I := I_ge_one hG hH eXIII
  have hK : 0 ≤ K := K_nonneg hp hM (n_succ_ge_k hk hn hc1 eI) eXVIII
  have hL : 0 ≤ L := L_nonneg hk hl hM (by omega) eXIX
  have hR : 0 ≤ R := R_nonneg hk hr hM (by omega) (by omega) eXX
  exact ⟨by omega, by omega, by omega, by omega, hK, hL, hR⟩

end Diophantus
