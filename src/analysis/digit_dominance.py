"""
================================================================================
   DIOPHANTUS - DOMINANCIA DE DIGITOS / KUMMER-LUCAS
================================================================================
Herramienta para colapsar el cuantificador
universal acotado del sistema beta en el caso GENERAL (no solo lineal): empaquetar
la historia de cada registro en un entero gigante en base 2^k (un digito por paso)
e imponer la correccion de TODOS los pasos a la vez mediante la relacion de
dominancia de digitos.

Relacion de dominancia:  a ⪯ b  <=>  cada bit de a es <= el bit correspondiente
de b  <=>  a AND b == a  <=>  sumar a y (b-a) no produce acarreo.

Teorema de Kummer-Lucas (el "truco"):
        binom(b, a) es IMPAR  <=>  a ⪯ b
(la maxima potencia de 2 que divide binom(b,a) es el numero de acarreos al sumar
a y b-a en base 2; cero acarreos <=> dominancia <=> binomial impar).

La dominancia es diofantica-friendly: `a ⪯ b` equivale a la existencia de c con
a + c == b y a AND c == 0, y se caracteriza por la paridad de un coeficiente
binomial (exponencial-diofantico). Por eso permite expresar "para toda posicion
de digito se cumple la relacion" con un PUNADO de ecuaciones, sin recorrer i.
Este modulo implementa y valida ese primitivo; el ensamblaje del sistema de la
maquina de registros completa se apoya en el.
"""


def dominates(a, b):
    """a ⪯ b: los bits de a estan contenidos en los de b (a AND b == a)."""
    if a < 0 or b < 0:
        raise ValueError("la dominancia se define sobre naturales")
    return (a & b) == a


def carry_free_sum(a, c):
    """True si a + c no produce acarreo en binario (a AND c == 0). Equivale a
    a ⪯ (a+c) y a que a+c == a OR c == a XOR c."""
    return (a & c) == 0


def binom_parity(n, k):
    """Paridad de binom(n, k) (0 = par, 1 = impar) por el teorema de Lucas en
    base 2: impar sii k ⪯ n. Se calcula sin construir el binomial."""
    if k < 0 or k > n:
        return 0
    return 1 if (k & n) == k else 0


def binom_parity_bruteforce(n, k):
    """Paridad de binom(n, k) calculando el coeficiente (para validar Lucas)."""
    from math import comb
    if k < 0 or k > n:
        return 0
    return comb(n, k) % 2


def base_pow_digits(xs, k):
    """Empaqueta la traza `xs` en base 2^k (un digito por paso): N = sum xs_i * 2^(k*i).
    Requiere 0 <= xs_i < 2^k (digitos sin acarreo entre pasos)."""
    B = 1 << k
    if any(not (0 <= x < B) for x in xs):
        raise ValueError(f"cada digito debe cumplir 0 <= x < 2^{k}")
    N = 0
    for i, x in enumerate(xs):
        N += x << (k * i)
    return N


def all_digits_dominated(k, n_packed, m_packed, length):
    """Comprueba que, posicion a posicion, el digito de `n_packed` esta dominado
    por el de `m_packed` (en base 2^k) PARA TODA posicion < length, mediante una
    UNICA relacion de dominancia global en lugar de un bucle sobre posiciones.

    Vale porque, sin acarreos entre digitos, `n_packed ⪯ m_packed` (dominancia
    de los enteros completos) equivale a la dominancia digito-a-digito. Es la
    forma en que la dominancia colapsa el "para toda posicion" en O(1)."""
    return dominates(n_packed, m_packed)
