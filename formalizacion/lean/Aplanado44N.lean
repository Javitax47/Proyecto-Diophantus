/-
  DIOPHANTUS — el (44, 5) sobre ℕ, las dos direcciones en un solo enunciado
  ========================================================================
  `Aplanado.lean` demuestra las dos implicaciones entre el sistema (1) y su
  aplanado, pero SOBRE ℤ y sin ninguna hipótesis de signo. Eso no basta para
  sostener la cifra: el generador vive sobre ℕ, y el paso de una cosa a la otra
  —que los veinte testigos de la dirección de completitud son ≥ 0— quedaba
  ensamblado EN PROSA a partir de tres ficheros que no se hablaban entre sí.

  Aquí se compone en un único `↔` entre dos cuantificaciones existenciales con la
  no-negatividad dentro, que es la forma que ya tenían `Eliminacion.lean` y
  `Eliminacion21.lean` y de la que ésta era la excepción.

  De los veinte testigos, dieciocho son sumas de monomios con coeficientes no
  negativos; `μ₁₄` es el cuadrado de `μ₂₀`; y `μ₂₀` es `Nombre20.nombre20_ge_one`,
  cuya hipótesis `a ≥ 2` se obtiene aquí de `Pell.a_ge_e_succ_de_sistema` (que da
  `a ≥ e+1`) junto con `e ≥ 4`.

  DEPENDENCIAS: `Aplanado`, `Nombre20`, `Pell`, de este mismo desarrollo. Sin Mathlib.
-/

import Aplanado
import Nombre20
import Pell

namespace Aplanado

open Diophantus

theorem cubo_nonneg {x : Int} (hx : 0 ≤ x) : 0 ≤ x^3 := by
  have e : x^3 = x^2 * x := by grind
  rw [e]; exact Int.mul_nonneg (Int.sq_nonneg x) hx

theorem cuarta_nonneg (x : Int) : 0 ≤ x^4 := by
  have e : x^4 = x^2 * x^2 := by grind
  rw [e]; exact Int.mul_nonneg (Int.sq_nonneg x) (Int.sq_nonneg x)

/-- **EQUISATISFACIBILIDAD SOBRE ℕ**, que es el enunciado que sostiene el (44, 5).
    El sistema (1) de Jones-Sato-Wada-Wiens tiene solución no negativa para un `k`
    si y sólo si la tiene su aplanado a grado 2 en 44 variables. -/
theorem equisatisfacible44 (k : Int) (hk : 0 ≤ k) :
    (∃ a b c d e f g h i j l m n o p q r s t u v w x y z : Int,
        (
          0 ≤ a ∧ 0 ≤ b ∧ 0 ≤ c ∧ 0 ≤ d ∧ 0 ≤ e ∧ 0 ≤ f ∧ 0 ≤ g ∧ 0 ≤ h ∧ 0 ≤ i ∧ 0 ≤
          j ∧ 0 ≤ l ∧ 0 ≤ m ∧ 0 ≤ n ∧ 0 ≤ o ∧ 0 ≤ p ∧ 0 ≤ q ∧ 0 ≤ r ∧ 0 ≤ s ∧ 0 ≤ t ∧
          0 ≤ u ∧ 0 ≤ v ∧ 0 ≤ w ∧ 0 ≤ x ∧ 0 ≤ y ∧ 0 ≤ z)
        ∧ S k a b c d e f g h i j l m n o p q r s t u v w x y z)
      ↔
    (∃ a b c d e f g h i j l m n o p r s t u v w x z m20 m15 m13 m14 m1 m7 m4 m19 m10 m17 m12 m9 m6 m5 m2 m16 m3 m18 m11 m8 : Int,
        (
          0 ≤ a ∧ 0 ≤ b ∧ 0 ≤ c ∧ 0 ≤ d ∧ 0 ≤ e ∧ 0 ≤ f ∧ 0 ≤ g ∧ 0 ≤ h ∧ 0 ≤ i ∧ 0 ≤
          j ∧ 0 ≤ l ∧ 0 ≤ m ∧ 0 ≤ n ∧ 0 ≤ o ∧ 0 ≤ p ∧ 0 ≤ r ∧ 0 ≤ s ∧ 0 ≤ t ∧ 0 ≤ u ∧
          0 ≤ v ∧ 0 ≤ w ∧ 0 ≤ x ∧ 0 ≤ z ∧ 0 ≤ m20 ∧ 0 ≤ m15 ∧ 0 ≤ m13 ∧ 0 ≤ m14 ∧ 0 ≤
          m1 ∧ 0 ≤ m7 ∧ 0 ≤ m4 ∧ 0 ≤ m19 ∧ 0 ≤ m10 ∧ 0 ≤ m17 ∧ 0 ≤ m12 ∧ 0 ≤ m9 ∧ 0 ≤
          m6 ∧ 0 ≤ m5 ∧ 0 ≤ m2 ∧ 0 ≤ m16 ∧ 0 ≤ m3 ∧ 0 ≤ m18 ∧ 0 ≤ m11 ∧ 0 ≤ m8)
        ∧ M k a b c d e f g h i j l m n o p r s t u v w x z m20 m15 m13 m14 m1 m7 m4 m19 m10 m17 m12 m9 m6 m5 m2 m16 m3 m18 m11 m8) := by
  constructor
  · -- ORIGINAL ⟹ APLANADO. Los testigos son las propias definiciones de los
    -- nombres, resueltas hasta quedar en las variables originales.
    rintro ⟨a, b, c, d, e, f, g, h, i, j, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z, hnn, hS⟩
    obtain ⟨ha, hb, hc, hd, he, hf, hg, hh, hi, hj, hl, hm, hn, ho, hp, hq, hr, hs, ht, hu, hv, hw, hx, hy, hz⟩ := hnn
    have hM := original_implica_aplanado k a b c d e f g h i j l m n o p q r s t u v w x y z hS
    obtain ⟨q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14⟩ := hS
    -- `a ≥ 2`: sale de la cota de Pell `a ≥ e+1` con `e ≥ 4`
    have hn2 : 2 ≤ n := n_ge_two hk hn hf (by grind)
    have he4 : 4 ≤ e := by omega
    have hae : e + 1 ≤ a :=
      a_ge_e_succ_de_sistema hk hn hf hp hq hz ha ho (by grind) (by grind) (by grind)
    have ha2 : 2 ≤ a := by omega
    -- el vigésimo testigo, que es el único que no sale por estructura
    have h20 : 1 ≤ a + u^2 * (u^2 - a) := nombre20_ge_one ha2 hr hy (by grind)
    have h20' : 0 ≤ a + u^4 + -1*a*u^2 := by
      have e20 : a + u^2 * (u^2 - a) = a + u^4 + -1*a*u^2 := by grind
      omega
    refine ⟨a, b, c, d, e, f, g, h, i, j, l, m, n, o, p, r, s, t, u, v, w, x, z, (a + u^4 + -1*a*u^2), (n^2 + 16*d^2*y^2 + 8*d*n*y), (n + 4*d*y), (a^2 + u^8 + a^2*u^4 + -2*a*u^6 + -2*a^2*u^2 + 2*a*u^4), (2*g + g*k), (e^4 + 2*e^3), (2 + k^4 + 5*k^3 + 7*k + 9*k^2), (a*p), (a*r*y^2), (b*n), (c*u), (r*y^2), (a^2), (e^2), (k^2), (l^2), (n^2), (p^2), (u^2), (y^2), ?_, hM⟩
    refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
    · exact ha
    · exact hb
    · exact hc
    · exact hd
    · exact he
    · exact hf
    · exact hg
    · exact hh
    · exact hi
    · exact hj
    · exact hl
    · exact hm
    · exact hn
    · exact ho
    · exact hp
    · exact hr
    · exact hs
    · exact ht
    · exact hu
    · exact hv
    · exact hw
    · exact hx
    · exact hz
    · omega
    · have p1 : 0 ≤ n^2 := Int.sq_nonneg n
      have p2 : 0 ≤ d^2*y^2 := Int.mul_nonneg (Int.sq_nonneg d) (Int.sq_nonneg y)
      have p3 : 0 ≤ d*n*y := Int.mul_nonneg (Int.mul_nonneg hd hn) hy
      grind
    · have p1 : 0 ≤ d*y := Int.mul_nonneg hd hy
      grind
    · have e14 : a^2 + u^8 + a^2*u^4 + -2*a*u^6 + -2*a^2*u^2 + 2*a*u^4
               = (a + u^4 + -1*a*u^2)^2 := by grind
      rw [e14]; exact Int.sq_nonneg _
    · have p1 : 0 ≤ g*k := Int.mul_nonneg hg hk
      grind
    · have p1 : 0 ≤ e^4 := cuarta_nonneg e
      have p2 : 0 ≤ e^3 := cubo_nonneg he
      grind
    · have p1 : 0 ≤ k^4 := cuarta_nonneg k
      have p2 : 0 ≤ k^3 := cubo_nonneg hk
      have p3 : 0 ≤ k^2 := Int.sq_nonneg k
      grind
    · exact Int.mul_nonneg ha hp
    · exact Int.mul_nonneg (Int.mul_nonneg ha hr) (Int.sq_nonneg y)
    · exact Int.mul_nonneg hb hn
    · exact Int.mul_nonneg hc hu
    · exact Int.mul_nonneg hr (Int.sq_nonneg y)
    · exact Int.sq_nonneg a
    · exact Int.sq_nonneg e
    · exact Int.sq_nonneg k
    · exact Int.sq_nonneg l
    · exact Int.sq_nonneg n
    · exact Int.sq_nonneg p
    · exact Int.sq_nonneg u
    · exact Int.sq_nonneg y
  · -- APLANADO ⟹ ORIGINAL. Las dos eliminadas valen su definición, y ambas
    -- tienen todos los coeficientes ≥ 0, luego viven en ℕ sin más.
    rintro ⟨a, b, c, d, e, f, g, h, i, j, l, m, n, o, p, r, s, t, u, v, w, x, z, m20, m15, m13, m14, m1, m7, m4, m19, m10, m17, m12, m9, m6, m5, m2, m16, m3, m18, m11, m8, hnn, hM⟩
    obtain ⟨ha, hb, hc, hd, he, hf, hg, hh, hi, hj, hl, hm, hn, ho, hp, hr, hs, ht, hu, hv, hw, hx, hz, hm20, hm15, hm13, hm14, hm1, hm7, hm4, hm19, hm10, hm17, hm12, hm9, hm6, hm5, hm2, hm16, hm3, hm18, hm11, hm8⟩ := hnn
    have hS := aplanado_implica_original k a b c d e f g h i j l m n o p r s t u v w x z m20 m15 m13 m14 m1 m7 m4 m19 m10 m17 m12 m9 m6 m5 m2 m16 m3 m18 m11 m8 hM
    refine ⟨a, b, c, d, e, f, g, h, i, j, l, m, n, o, p, (h + j + w * z), r, s, t, u, v, w, x, (l + n + v), z, ?_, hS⟩
    have hq : 0 ≤ h + j + w * z := by
      have : 0 ≤ w * z := Int.mul_nonneg hw hz
      omega
    refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> omega

end Aplanado
