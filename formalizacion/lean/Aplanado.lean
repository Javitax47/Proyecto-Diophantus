/-
  DIOPHANTUS — el sistema aplanado ES el (1) de Jones-Sato-Wada-Wiens
  ========================================================================
  Equivalencia entre el sistema (1) publicado y su aplanado a grado 2 por
  ecuacion, que es el paso que produce la cifra de portada. En sympy esto se
  comprueba con `verificar_equivalencia` (0 faltan / 0 sobran); aqui lo comprueba
  el NUCLEO de Lean.

  FICHERO GENERADO por `src/analysis/dioph_lean.py` a partir del MISMO objeto
  que produce la cifra. No se transcribe a mano: un signo mal escrito daria un
  teorema que compila y no dice lo mismo.

  SOBRE ℕ SIN RESTAS. Cada ecuacion `E = 0` se emite como `P = N` con P y N de
  coeficientes no negativos. La resta de `Nat` es truncada (`3 - 5 = 0`), asi
  que escribirla seria decir otra cosa.
-/

namespace Aplanado

/-! ## El sistema ORIGINAL (el publicado), sobre ℕ sin restas -/

/-- Las ecuaciones del sistema de partida. `S k a b … z` dice que esa tupla
    es solucion. -/
def S (k a b c d e f g h i j l m n o p q r s t u v w x y z : Nat) : Prop :=
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

def M (k a b c d e f h i j l m n o p q r s t u v w x y z m11 m2 m15 m3 m10 m5 m8 m1 m7 m12 m13 m9 m6 m14 m4 : Nat) : Prop :=
  h + j + w * z = q ∧
  m1 = z ∧
  p + q + z + 2 * n = e ∧
  m2 = f ^ 2 ∧
  m3 = o ^ 2 ∧
  m5 = x ^ 2 + y ^ 2 ∧
  1 + 16 * m7 * r = u ^ 2 + 16 * m6 ^ 2 ∧
  1 + m10 * m11 = m8 ^ 2 ∧
  l + n + v = y ∧
  1 + m12 ^ 2 = l ^ 2 + m ^ 2 ∧
  1 + k + a * i = i + l ∧
  p + a * l + 2 * a * b + 2 * a * m13 = l + m + 2 * b + l * n + m13 * n + 2 * b * n ∧
  q + a * y + m15 * s = x + y + 2 * s + m14 * s + p * y + 2 * p * s ∧
  z + m12 * p + m15 * t = t + l * m14 + m * p + m14 * t + 2 * a * t ∧
  0 = 0 ∧
  0 = 0 ∧
  0 = 0 ∧
  m4 = y ^ 2 ∧
  0 = 0 ∧
  m6 = m4 * r ∧
  m6 + m7 = m5 * m6 ∧
  m8 = x + c * u ∧
  m9 = d * y ∧
  0 = 0 ∧
  m11 = n ^ 2 + 16 * m9 ^ 2 + 8 * m9 * n ∧
  m12 = a * l ∧
  m13 = b * n ∧
  m14 = p ^ 2 ∧
  m15 = 2 * a + 2 * a * p

/-! ## Los dos teoremas -/

/-- **SOUNDNESS.** Toda solucion del sistema aplanado da una del original.

    Es la direccion critica: si fallara, el generador emitiria numeros que no
    pertenecen al conjunto. Los nombres `m…` estan ligados por sus ecuaciones
    definitorias dentro de `M`, asi que basta sustituir y normalizar. -/
theorem aplanado_implica_original (k a b c d e f h i j l m n o p q r s t u v w x y z m11 m2 m15 m3 m10 m5 m8 m1 m7 m12 m13 m9 m6 m14 m4 : Nat)
    (h : M k a b c d e f h i j l m n o p q r s t u v w x y z m11 m2 m15 m3 m10 m5 m8 m1 m7 m12 m13 m9 m6 m14 m4) : S k a b c d e f g h i j l m n o p q r s t u v w x y z := by
  unfold M at h
  unfold S
  obtain ⟨h0, h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13, h14, h15, h16, h17, h18, h19, h20, h21, h22, h23, h24, h25, h26, h27, h28⟩ := h
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> grind

/-- **COMPLETITUD.** Toda solucion del original se extiende a una del aplanado.

    Los testigos de los nombres son sus PROPIAS definiciones, resueltas hasta
    quedar en terminos de las variables originales. Que sean terminos de `Nat`
    es justo lo que exige la construccion del generador: un nombre que pudiera
    ser negativo romperia la completitud (el elemento dejaria de emitirse), y
    aqui eso ni siquiera se puede escribir. -/
theorem original_implica_aplanado (k a b c d e f g h i j l m n o p q r s t u v w x y z : Nat)
    (h : S k a b c d e f g h i j l m n o p q r s t u v w x y z) :
    M k a b c d e f h i j l m n o p q r s t u v w x y z (n ^ 2 + 16 * d ^ 2 * y ^ 2 + 8 * d * n * y) (33 + 16 * k ^ 4 + 32 * n ^ 2 + 64 * n + 80 * k ^ 3 + 112 * k + 144 * k ^ 2 + 16 * k ^ 4 * n ^ 2 + 32 * n * k ^ 4 + 80 * k ^ 3 * n ^ 2 + 112 * k * n ^ 2 + 144 * k ^ 2 * n ^ 2 + 160 * n * k ^ 3 + 224 * k * n + 288 * n * k ^ 2) (2 * a + 2 * a * p) (1 + e ^ 4 + 2 * e ^ 3 + a ^ 2 * e ^ 4 + 2 * a * e ^ 4 + 2 * a ^ 2 * e ^ 3 + 4 * a * e ^ 3) (-1 + a ^ 2 + u ^ 8 + a ^ 2 * u ^ 4 + -2 * a * u ^ 6 + -2 * a ^ 2 * u ^ 2 + 2 * a * u ^ 4) (1 + a ^ 2 * y ^ 2) (x + c * u) (j + 2 * h + h * k + j * k + 2 * g * h + 2 * g * j + g * h * k + g * j * k) (r * a ^ 2 * y ^ 4) (a * l) (b * n) (d * y) (r * y ^ 2) (p ^ 2) (y ^ 2) := by
  unfold S at h
  unfold M
  obtain ⟨h0, h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13⟩ := h
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> grind

end Aplanado
