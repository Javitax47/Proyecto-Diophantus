/-
  DIOPHANTUS — la eliminación (26,25) ⟶ (23,25) en el sistema (1) de JSWW
  =======================================================================
  Verificación FORMAL del único resultado del proyecto que mejora una cifra de
  la literatura: el sistema (1) de Jones-Sato-Wada-Wiens, que ellos publican con
  25 incógnitas más el parámetro (generador de 26 variables y grado 25), es
  equisatisfacible con un sistema de 22 incógnitas del MISMO grado — generador
  de **23 variables y grado 25**, tres por debajo del suyo.

  QUE SE DEMUESTRA, EXACTAMENTE. Que existe una solución del sistema completo
  si y solo si existe una del reducido, para el mismo `k`. Nada más y nada
  menos: no se demuestra que el sistema represente los primos, que es el teorema
  de JSWW y aquí se CITA. Lo que se verifica es que nuestra transformación no
  cambia el conjunto de `k` representados — que es justo donde este proyecto se
  ha equivocado nueve veces.

  POR QUE ES FORMALIZABLE Y LO DEL GRADO 5 NO. Porque no hay aplanado, ni
  optimizador, ni reescritura: son TRES SUSTITUCIONES LINEALES. Las ecuaciones
  (1), (2) y (9) determinan `q`, `z` e `y` como polinomios de las demás
  incógnitas, y esos polinomios tienen todos los coeficientes NO NEGATIVOS. Eso
  último es lo que hace que la vuelta funcione sobre ℕ, y aquí deja de ser un
  criterio implementado en Python para pasar a ser tres LEMAS (`defZ_nonneg`, `defQ_nonneg`, `defY_nonneg`).

  SOBRE ℤ CON `0 ≤ ·` EXPLÍCITO, no sobre ℕ. Las variables de JSWW recorren ℕ,
  pero sus ecuaciones tienen restas (`a² - 1`, `a - n - 1`, `u² - a`) que sobre
  `Nat` se truncarían y dirían otra cosa. Modelarlas en ℤ con la no negatividad
  como hipótesis es exactamente equivalente y deja las ecuaciones LITERALMENTE
  como están publicadas, que es lo que permite cotejar la transcripción a ojo.

  DEPENDENCIAS: ninguna. Solo el núcleo de Lean 4. No usa Mathlib.
-/

namespace Diophantus

/-! ## 1. Las tres definiciones lineales que se eliminan

Salen de las ecuaciones (2), (1) y (9) respectivamente, en ese orden: `q`
depende de `z`, así que `z` tiene que definirse primero. -/

/-- Ecuación (2): `(gk + 2g + k + 1)(h + j) + h = z`. -/
def defZ (g h j k : Int) : Int := (g * k + 2 * g + k + 1) * (h + j) + h

/-- Ecuación (1): `wz + h + j = q`, con `z` ya sustituida. -/
def defQ (g h j k w : Int) : Int := w * defZ g h j k + h + j

/-- Ecuación (9): `n + l + v = y`. -/
def defY (l n v : Int) : Int := n + l + v

/-! ## 2. El sistema (1) completo, tal y como lo imprime el paper

Las catorce ecuaciones, en el orden del artículo y con la misma escritura. Las
restas se conservan porque estamos en ℤ. -/

def completo (k a b c d e f g h i j l m n o p q r s t u v w x y z : Int) : Prop :=
  w * z + h + j = q
  ∧ (g * k + 2 * g + k + 1) * (h + j) + h = z
  ∧ 2 * n + p + q + z = e
  ∧ 16 * (k + 1) ^ 3 * (k + 2) * (n + 1) ^ 2 + 1 = f ^ 2
  ∧ e ^ 3 * (e + 2) * (a + 1) ^ 2 + 1 = o ^ 2
  ∧ (a ^ 2 - 1) * y ^ 2 + 1 = x ^ 2
  ∧ 16 * r ^ 2 * y ^ 4 * (a ^ 2 - 1) + 1 = u ^ 2
  ∧ ((a + u ^ 2 * (u ^ 2 - a)) ^ 2 - 1) * (n + 4 * d * y) ^ 2 + 1 = (x + c * u) ^ 2
  ∧ n + l + v = y
  ∧ (a ^ 2 - 1) * l ^ 2 + 1 = m ^ 2
  ∧ a * i + k + 1 = l + i
  ∧ p + l * (a - n - 1) + b * (2 * a * n + 2 * a - n ^ 2 - 2 * n - 2) = m
  ∧ q + y * (a - p - 1) + s * (2 * a * p + 2 * a - p ^ 2 - 2 * p - 2) = x
  ∧ z + p * l * (a - p) + t * (2 * a * p - p ^ 2 - 1) = p * m

/-- El sistema reducido: las once ecuaciones que quedan al sustituir `q`, `z` e
    `y` por sus definiciones. Las ecuaciones (1), (2) y (9) desaparecen porque
    pasan a ser `defQ = defQ`, `defZ = defZ` y `defY = defY`. -/
def reducido (k a b c d e f g h i j l m n o p r s t u v w x : Int) : Prop :=
  2 * n + p + defQ g h j k w + defZ g h j k = e
  ∧ 16 * (k + 1) ^ 3 * (k + 2) * (n + 1) ^ 2 + 1 = f ^ 2
  ∧ e ^ 3 * (e + 2) * (a + 1) ^ 2 + 1 = o ^ 2
  ∧ (a ^ 2 - 1) * (defY l n v) ^ 2 + 1 = x ^ 2
  ∧ 16 * r ^ 2 * (defY l n v) ^ 4 * (a ^ 2 - 1) + 1 = u ^ 2
  ∧ ((a + u ^ 2 * (u ^ 2 - a)) ^ 2 - 1) * (n + 4 * d * defY l n v) ^ 2 + 1
      = (x + c * u) ^ 2
  ∧ (a ^ 2 - 1) * l ^ 2 + 1 = m ^ 2
  ∧ a * i + k + 1 = l + i
  ∧ p + l * (a - n - 1) + b * (2 * a * n + 2 * a - n ^ 2 - 2 * n - 2) = m
  ∧ defQ g h j k w + defY l n v * (a - p - 1)
      + s * (2 * a * p + 2 * a - p ^ 2 - 2 * p - 2) = x
  ∧ defZ g h j k + p * l * (a - p) + t * (2 * a * p - p ^ 2 - 1) = p * m

/-! ## 3. El lema que hace sound la vuelta

Sobre ℕ una eliminación solo es válida en las DOS direcciones si la definición
que se sustituye es ella misma no negativa: al reconstruir la solución del
sistema completo hay que exhibir un valor de `q`, `z` e `y` que esté en el
dominio. Aquí eso se demuestra, en vez de comprobarse mirando los signos de los
coeficientes como hace el criterio de `eliminar_lineales`. -/

theorem defZ_nonneg {g h j k : Int}
    (hg : 0 ≤ g) (hh : 0 ≤ h) (hj : 0 ≤ j) (hk : 0 ≤ k) : 0 ≤ defZ g h j k := by
  unfold defZ
  have h1 : 0 ≤ g * k := Int.mul_nonneg hg hk
  have h2 : 0 ≤ g * k + 2 * g + k + 1 := by omega
  have h3 : 0 ≤ h + j := by omega
  have h4 : 0 ≤ (g * k + 2 * g + k + 1) * (h + j) := Int.mul_nonneg h2 h3
  omega

theorem defQ_nonneg {g h j k w : Int}
    (hg : 0 ≤ g) (hh : 0 ≤ h) (hj : 0 ≤ j) (hk : 0 ≤ k) (hw : 0 ≤ w) :
    0 ≤ defQ g h j k w := by
  unfold defQ
  have hz : 0 ≤ defZ g h j k := defZ_nonneg hg hh hj hk
  have h1 : 0 ≤ w * defZ g h j k := Int.mul_nonneg hw hz
  omega

theorem defY_nonneg {l n v : Int} (hl : 0 ≤ l) (hn : 0 ≤ n) (hv : 0 ≤ v) :
    0 ≤ defY l n v := by
  unfold defY; omega

/-! ## 4. La sustitución, en las dos direcciones -/

/-- Sustituir es exacto: el sistema completo evaluado en las definiciones ES el
    sistema reducido. Las tres ecuaciones eliminadas se vuelven triviales. -/
theorem completo_de_defs (k a b c d e f g h i j l m n o p r s t u v w x : Int) :
    completo k a b c d e f g h i j l m n o p (defQ g h j k w) r s t u v w x
        (defY l n v) (defZ g h j k)
      ↔ reducido k a b c d e f g h i j l m n o p r s t u v w x := by
  unfold completo reducido defQ defY defZ
  constructor
  · intro h
    obtain ⟨_, _, h3, h4, h5, h6, h7, h8, _, h10, h11, h12, h13, h14⟩ := h
    exact ⟨h3, h4, h5, h6, h7, h8, h10, h11, h12, h13, h14⟩
  · intro h
    obtain ⟨h3, h4, h5, h6, h7, h8, h10, h11, h12, h13, h14⟩ := h
    -- Las tres ecuaciones eliminadas son `defQ = defQ`, `defZ = defZ` y
    -- `defY = defY`: literalmente la misma expresión a los dos lados tras
    -- desplegar, luego `rfl`. (`ring` no existe sin Mathlib, y aquí no hace
    -- falta: no hay nada que normalizar.)
    exact ⟨rfl, rfl, h3, h4, h5, h6, h7, h8, rfl, h10, h11, h12, h13, h14⟩

/-! ## 5. El teorema: equisatisfacibilidad

Es lo que significa «bajar de 26 a 23 variables sin cambiar el conjunto
representado». El grado no se toca: las ecuaciones (3), (13) y (14) suben de
grado al sustituir, pero el máximo del sistema sigue siendo 12, y por tanto el
generador `(k+2)(1 - Σ Pᵢ²)` sigue teniendo grado `1 + 2·12 = 25`. Eso último se
mide en `dioph_degree`, no aquí: este fichero verifica la parte que importa,
que es que las SOLUCIONES sean las mismas. -/

theorem equisatisfacible (k : Int) (hk : 0 ≤ k) :
    (∃ a b c d e f g h i j l m n o p q r s t u v w x y z : Int,
        (0 ≤ a ∧ 0 ≤ b ∧ 0 ≤ c ∧ 0 ≤ d ∧ 0 ≤ e ∧ 0 ≤ f ∧ 0 ≤ g ∧ 0 ≤ h ∧ 0 ≤ i
          ∧ 0 ≤ j ∧ 0 ≤ l ∧ 0 ≤ m ∧ 0 ≤ n ∧ 0 ≤ o ∧ 0 ≤ p ∧ 0 ≤ q ∧ 0 ≤ r
          ∧ 0 ≤ s ∧ 0 ≤ t ∧ 0 ≤ u ∧ 0 ≤ v ∧ 0 ≤ w ∧ 0 ≤ x ∧ 0 ≤ y ∧ 0 ≤ z)
        ∧ completo k a b c d e f g h i j l m n o p q r s t u v w x y z)
      ↔
    (∃ a b c d e f g h i j l m n o p r s t u v w x : Int,
        (0 ≤ a ∧ 0 ≤ b ∧ 0 ≤ c ∧ 0 ≤ d ∧ 0 ≤ e ∧ 0 ≤ f ∧ 0 ≤ g ∧ 0 ≤ h ∧ 0 ≤ i
          ∧ 0 ≤ j ∧ 0 ≤ l ∧ 0 ≤ m ∧ 0 ≤ n ∧ 0 ≤ o ∧ 0 ≤ p ∧ 0 ≤ r ∧ 0 ≤ s
          ∧ 0 ≤ t ∧ 0 ≤ u ∧ 0 ≤ v ∧ 0 ≤ w ∧ 0 ≤ x)
        ∧ reducido k a b c d e f g h i j l m n o p r s t u v w x) := by
  constructor
  · -- IDA: las ecuaciones (1), (2) y (9) dicen que q, z e y YA valen sus
    -- definiciones, así que basta olvidarlas.
    rintro ⟨a, b, c, d, e, f, g, h, i, j, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z,
            ⟨ha, hb, hc, hd, he, hf, hg, hh, hi, hj, hl, hm, hn, ho, hp, _, hr, hs,
             ht, hu, hv, hw, hx, _, _⟩, hsis⟩
    refine ⟨a, b, c, d, e, f, g, h, i, j, l, m, n, o, p, r, s, t, u, v, w, x,
            ⟨ha, hb, hc, hd, he, hf, hg, hh, hi, hj, hl, hm, hn, ho, hp, hr, hs,
             ht, hu, hv, hw, hx⟩, ?_⟩
    -- `obtain` CONSUME la hipótesis, así que se destruye una copia: `hsis` hace
    -- falta entera al final.
    have hcopia := hsis
    obtain ⟨e1, e2, _, _, _, _, _, _, e9, _, _, _, _, _⟩ := hcopia
    have hz : z = defZ g h j k := e2.symm
    have hy : y = defY l n v := e9.symm
    rw [hz] at e1
    have hq : q = defQ g h j k w := by unfold defQ; exact e1.symm
    subst hz; subst hy; subst hq
    exact (completo_de_defs k a b c d e f g h i j l m n o p r s t u v w x).mp hsis
  · -- VUELTA: se DEFINEN q, z e y, y hay que exhibirlos en el dominio. Ahí es
    -- donde entra que los coeficientes sean no negativos.
    rintro ⟨a, b, c, d, e, f, g, h, i, j, l, m, n, o, p, r, s, t, u, v, w, x,
            ⟨ha, hb, hc, hd, he, hf, hg, hh, hi, hj, hl, hm, hn, ho, hp, hr, hs,
             ht, hu, hv, hw, hx⟩, hred⟩
    exact ⟨a, b, c, d, e, f, g, h, i, j, l, m, n, o, p, defQ g h j k w, r, s, t, u, v,
           w, x, defY l n v, defZ g h j k,
           ⟨ha, hb, hc, hd, he, hf, hg, hh, hi, hj, hl, hm, hn, ho, hp,
            defQ_nonneg hg hh hj hk hw, hr, hs, ht, hu, hv, hw, hx,
            defY_nonneg hl hn hv, defZ_nonneg hg hh hj hk⟩,
           (completo_de_defs k a b c d e f g h i j l m n o p r s t u v w x).mpr hred⟩

end Diophantus
