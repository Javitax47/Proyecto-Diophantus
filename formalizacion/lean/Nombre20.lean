/-
  DIOPHANTUS — el único nombre del aplanado que no es ≥ 0 por estructura
  ======================================================================
  El generador de grado 5 se obtiene aplanando el sistema (1) de
  Jones-Sato-Wada-Wiens con veinte nombres. Diecinueve de los veinte testigos que
  la dirección de COMPLETITUD exhibe son sumas y productos de cosas no negativas,
  y por tanto viven en ℕ sin más. El vigésimo no:

      m₂₀ = a + u²(u² − a)

  Si `m₂₀` pudiera ser negativo, el sistema aplanado no tendría solución para ese
  primo y el generador **dejaría de emitirlo**: sería un fallo de completitud, no
  de soundness, y por tanto silencioso.

  Hasta ahora esto se comprobaba por BARRIDO NUMÉRICO sobre las ternas `(a,r,y)`
  que satisfacen la ecuación (7) (`test_dioph_jsww`, comprobación [4]). Un barrido
  no es una demostración. Aquí se demuestra.

  LA IDENTIDAD QUE LO CIERRA, y es todo lo que hay que ver:

      a + t(t − a) − 1  =  (t − 1)(t − a + 1)

  Con `t = u²` y la ecuación (7), `t − 1 = 16r²y⁴(a² − 1) =: P ≥ 0`, así que el
  primer factor es `P` y el segundo `P + 2 − a`. Basta entonces distinguir dos
  casos según `s = r²y⁴` sea cero o no.

  DEPENDENCIAS: ninguna. Sólo el núcleo de Lean 4.
-/

namespace Diophantus

/-- **El vigésimo nombre es positivo en toda solución.**

    Hipótesis: la ecuación (7) del sistema (1) —`16r²y⁴(a²−1) + 1 = u²`— más
    `a ≥ 2`, que está demostrada aparte (`CotaA.a_ge_two`) desde las ecuaciones
    (3), (4), (5), (6) y (9), y `r, y ≥ 0`. Nada más: ni el resto del sistema, ni
    que represente los primos.

    Conclusión: `1 ≤ a + u²(u² − a)`, luego el testigo vive en ℕ y la dirección
    de completitud del aplanado es correcta sobre ℕ. -/
theorem nombre20_ge_one {a r y u : Int}
    (ha : 2 ≤ a) (hr : 0 ≤ r) (hy : 0 ≤ y)
    (h7 : 16 * r^2 * y^4 * (a^2 - 1) + 1 = u^2) :
    1 ≤ a + u^2 * (u^2 - a) := by
  -- `s = r²y⁴ ≥ 0`, escrito sin potencias para que `omega` lo trate como un átomo
  have hrr : 0 ≤ r * r := Int.mul_nonneg hr hr
  have hyy : 0 ≤ y * y := Int.mul_nonneg hy hy
  have hy4 : 0 ≤ (y * y) * (y * y) := Int.mul_nonneg hyy hyy
  have hs : 0 ≤ (r * r) * ((y * y) * (y * y)) := Int.mul_nonneg hrr hy4
  -- `a·a ≥ 4`, luego `a·a − 1 ≥ 3`
  have haa : 2 * 2 ≤ a * a := Int.mul_le_mul ha ha (by omega) (by omega)
  -- `a ≤ a·a`, que hace falta para comparar `u²` con `a`
  have hale : 1 * a ≤ a * a := Int.mul_le_mul_of_nonneg_right (by omega) (by omega)
  -- la ecuación (7) sin potencias, y con el producto `s·(a·a−1)` como UN átomo:
  -- si se deja `16·s·(a·a−1)`, `omega` lo lee como `(16·s)·(a·a−1)` y deja de
  -- casar con la cota de abajo. Es el detalle que hace que la prueba salga.
  have h7' : 16 * (((r * r) * ((y * y) * (y * y))) * (a * a - 1)) + 1 = u * u := by
    grind
  -- LA IDENTIDAD, que es todo lo que hay que ver
  have hid : a + u^2 * (u^2 - a) - 1 = (u * u - 1) * (u * u - a + 1) := by grind
  have hprod : 0 ≤ (u * u - 1) * (u * u - a + 1) := by
    by_cases hs0 : (r * r) * ((y * y) * (y * y)) = 0
    · -- `s = 0`: entonces `u² = 1` y el primer factor se anula
      have h1 : u * u - 1 = 0 := by rw [hs0] at h7'; omega
      rw [h1]; omega
    · -- `s ≥ 1`: entonces `u² − 1 ≥ 16(a·a − 1)`, y de ahí `u² ≥ a`
      have hs1 : 1 ≤ (r * r) * ((y * y) * (y * y)) := by omega
      have hmul : 1 * (a * a - 1) ≤ ((r * r) * ((y * y) * (y * y))) * (a * a - 1) :=
        Int.mul_le_mul_of_nonneg_right hs1 (by omega)
      -- `u² − 1 = 16·s·(a·a−1) ≥ 16(a·a−1) ≥ 16a − 16`, luego `u² ≥ a`
      have hlo : 0 ≤ u * u - 1 := by omega
      have hhi : 0 ≤ u * u - a + 1 := by omega
      exact Int.mul_nonneg hlo hhi
  omega

end Diophantus
