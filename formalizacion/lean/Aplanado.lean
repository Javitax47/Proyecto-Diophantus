/-
  DIOPHANTUS — el sistema aplanado ES el (1) de Jones-Sato-Wada-Wiens
  ========================================================================
  REGENERADO tras el noveno defecto. La version anterior de este fichero
  no compilaba: su teorema cuantificaba 24 incognitas y su conclusion
  mencionaba `g`, que no estaba entre ellas. Ese hueco ERA el defecto.

  FICHERO GENERADO por `src/analysis/dioph_lean.py` a partir del MISMO objeto
  que produce la cifra. No se transcribe a mano: un signo mal escrito daria un
  teorema que compila y no dice lo mismo.

  SOBRE ℤ, con las incognitas en ℕ por hipotesis SEPARADA. Las ecuaciones de
  coeficientes no negativos. La resta de `Nat` es truncada (`3 - 5 = 0`), asi
  que escribirla seria decir otra cosa.
-/

namespace Aplanado

/-! ## El sistema ORIGINAL (el publicado), sobre ℕ sin restas -/

/-- Las ecuaciones del sistema de partida. `S k a b … z` dice que esa tupla
    es solucion. -/
def S (k a b c d e f g h i j l m n o p q r s t u v w x y z : Int) : Prop :=
  h + j + w * z = q ∧
  j + 2 * h + h * k + j * k + 2 * g * h + 2 * g * j + g * h * k + g * j * k = z ∧
  p + q + z + 2 * n = e ∧
  33 + 16 * k ^ 4 + 32 * n ^ 2 + 64 * n + 80 * k ^ 3 + 112 * k + 144 * k ^ 2 + 16 * k ^ 4 * n ^ 2 + 32 * n * k ^ 4 + 80 * k ^ 3 * n ^ 2 + 112 * k * n ^ 2 + 144 * k ^ 2 * n ^ 2 + 160 * n * k ^ 3 + 224 * k * n + 288 * n * k ^ 2 = f ^ 2 ∧
  1 + e ^ 4 + 2 * e ^ 3 + a ^ 2 * e ^ 4 + 2 * a * e ^ 4 + 2 * a ^ 2 * e ^ 3 + 4 * a * e ^ 3 = o ^ 2 ∧
  1 + a ^ 2 * y ^ 2 = x ^ 2 + y ^ 2 ∧
  1 + 16 * a ^ 2 * r ^ 2 * y ^ 4 = u ^ 2 + 16 * r ^ 2 * y ^ 4 ∧
  1 + a ^ 2 * n ^ 2 + n ^ 2 * u ^ 8 + a ^ 2 * n ^ 2 * u ^ 4 + 2 * a * n ^ 2 * u ^ 4 + 16 * a ^ 2 * d ^ 2 * y ^ 2 + 16 * d ^ 2 * u ^ 8 * y ^ 2 + 8 * d * n * y * a ^ 2 + 8 * d * n * y * u ^ 8 + 16 * a ^ 2 * d ^ 2 * u ^ 4 * y ^ 2 + 32 * a * d ^ 2 * u ^ 4 * y ^ 2 + 8 * d * n * y * a ^ 2 * u ^ 4 + 16 * a * d * n * y * u ^ 4 = n ^ 2 + x ^ 2 + c ^ 2 * u ^ 2 + 16 * d ^ 2 * y ^ 2 + 2 * a * n ^ 2 * u ^ 6 + 2 * c * u * x + 2 * a ^ 2 * n ^ 2 * u ^ 2 + 8 * d * n * y + 32 * a * d ^ 2 * u ^ 6 * y ^ 2 + 32 * a ^ 2 * d ^ 2 * u ^ 2 * y ^ 2 + 16 * a * d * n * y * u ^ 6 + 16 * d * n * y * a ^ 2 * u ^ 2 ∧
  l + n + v = y ∧
  1 + a ^ 2 * l ^ 2 = l ^ 2 + m ^ 2 ∧
  1 + k + a * i = i + l ∧
  p + a * l + 2 * a * b + 2 * a * b * n = l + m + 2 * b + b * n ^ 2 + l * n + 2 * b * n ∧
  q + a * y + 2 * a * s + 2 * a * p * s = x + y + 2 * s + p * y + s * p ^ 2 + 2 * p * s ∧
  z + a * l * p + 2 * a * p * t = t + l * p ^ 2 + m * p + t * p ^ 2

/-! ## El sistema APLANADO (grado ≤ 2 por ecuacion) -/

def M (k a b c d e f g h i j l m n o p r s t u v w x z m20 m15 m13 m14 m1 m7 m4 m19 m10 m17 m12 m9 m6 m5 m2 m16 m3 m18 m11 m8 : Int) : Prop :=
  j + 2 * h + h * k + h * m1 + j * k + j * m1 = z ∧
  h + j + p + z + 2 * n + w * z = e ∧
  1 + 16 * m4 + 16 * m3 * m4 + 32 * m4 * n = f ^ 2 ∧
  1 + m7 + m6 * m7 + 2 * a * m7 = o ^ 2 ∧
  1 + m6 * m8 = l ^ 2 + n ^ 2 + v ^ 2 + x ^ 2 + 2 * l * n + 2 * l * v + 2 * n * v ∧
  1 + 16 * m10 ^ 2 = u ^ 2 + 16 * m9 ^ 2 ∧
  1 + m14 * m15 = m15 + m12 ^ 2 + x ^ 2 + 2 * m12 * x ∧
  1 + m16 * m6 = l ^ 2 + m ^ 2 ∧
  1 + k + a * i = i + l ∧
  p + a * l + 2 * a * b + 2 * a * m17 = l + m + 2 * b + l * n + m17 * n + 2 * b * n ∧
  h + j + a * l + a * n + a * v + w * z + 2 * a * s + 2 * m19 * s = l + n + v + x + 2 * s + l * p + m18 * s + n * p + p * v + 2 * p * s ∧
  z + l * m19 + 2 * m19 * t = t + l * m18 + m * p + m18 * t ∧
  m1 = 2 * g + g * k ∧
  m2 = k ^ 2 ∧
  m3 = n ^ 2 ∧
  m4 = 2 + m2 ^ 2 + 7 * k + 9 * k ^ 2 + 5 * k * m2 ∧
  m5 = e ^ 2 ∧
  m6 = a ^ 2 ∧
  m7 = m5 ^ 2 + 2 * e * m5 ∧
  m8 = l ^ 2 + n ^ 2 + v ^ 2 + 2 * l * n + 2 * l * v + 2 * n * v ∧
  m9 = m8 * r ∧
  m10 = a * m9 ∧
  m11 = u ^ 2 ∧
  m12 = c * u ∧
  m13 = n + 4 * d * l + 4 * d * n + 4 * d * v ∧
  m14 = m20 ^ 2 ∧
  m15 = m13 ^ 2 ∧
  m16 = l ^ 2 ∧
  m17 = b * n ∧
  m18 = p ^ 2 ∧
  m19 = a * p ∧
  m20 = a + m11 ^ 2 + -1 * a * m11

/-! ## Los dos teoremas -/

/-- **SOUNDNESS.** Toda solucion del sistema aplanado da una del original.

    Es la direccion critica: si fallara, el generador emitiria numeros que no
    pertenecen al conjunto. Los nombres `m…` estan ligados por sus ecuaciones
    definitorias dentro de `M`, asi que basta sustituir y normalizar. -/
theorem aplanado_implica_original (k a b c d e f g h i j l m n o p r s t u v w x z m20 m15 m13 m14 m1 m7 m4 m19 m10 m17 m12 m9 m6 m5 m2 m16 m3 m18 m11 m8 : Int)
    (hsol : M k a b c d e f g h i j l m n o p r s t u v w x z m20 m15 m13 m14 m1 m7 m4 m19 m10 m17 m12 m9 m6 m5 m2 m16 m3 m18 m11 m8) : S k a b c d e f g h i j l m n o p (h + j + w * z) r s t u v w x (l + n + v) z := by
  unfold M at hsol
  unfold S
  obtain ⟨h0, h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13, h14, h15, h16, h17, h18, h19, h20, h21, h22, h23, h24, h25, h26, h27, h28, h29, h30, h31⟩ := hsol
  -- cada nombre vale su definicion: se sustituyen y lo que queda son
  -- identidades polinomicas en las variables ORIGINALES
  subst h12 h13 h14 h15 h16 h17 h18 h19 h20 h21 h22 h23 h24 h25 h26 h27 h28 h29 h30 h31
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> grind

/-- **COMPLETITUD.** Toda solucion del original se extiende a una del aplanado.

    Los testigos de los nombres son sus PROPIAS definiciones, resueltas hasta
    quedar en terminos de las variables originales. Que sean terminos de `Nat`
    es justo lo que exige la construccion del generador: un nombre que pudiera
    ser negativo romperia la completitud (el elemento dejaria de emitirse), y
    aqui eso ni siquiera se puede escribir. -/
theorem original_implica_aplanado (k a b c d e f g h i j l m n o p q r s t u v w x y z : Int)
    (hsol : S k a b c d e f g h i j l m n o p q r s t u v w x y z) :
    M k a b c d e f g h i j l m n o p r s t u v w x z (a + u ^ 4 + -1 * a * u ^ 2) (n ^ 2 + 16 * d ^ 2 * y ^ 2 + 8 * d * n * y) (n + 4 * d * y) (a ^ 2 + u ^ 8 + a ^ 2 * u ^ 4 + -2 * a * u ^ 6 + -2 * a ^ 2 * u ^ 2 + 2 * a * u ^ 4) (2 * g + g * k) (e ^ 4 + 2 * e ^ 3) (2 + k ^ 4 + 5 * k ^ 3 + 7 * k + 9 * k ^ 2) (a * p) (a * r * y ^ 2) (b * n) (c * u) (r * y ^ 2) (a ^ 2) (e ^ 2) (k ^ 2) (l ^ 2) (n ^ 2) (p ^ 2) (u ^ 2) (y ^ 2) := by
  unfold S at hsol
  unfold M
  obtain ⟨h0, h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13⟩ := hsol
  -- las eliminadas valen su definicion: se sustituyen en las hipotesis
  subst h0 h8
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> grind

end Aplanado
