/*
 * ARB KERNEL V4 (TAX & EXOTIC SUPPORT)
 * Modela tokens con fees de transferencia dinámicos.
 * Esta es la ventaja competitiva: calcular el profit REAL después de impuestos.
 */
typedef unsigned long long uint256;

// --- VARIABLES DE MERCADO ---
uint256 rIn_0; uint256 rOut_0;
uint256 rIn_1; uint256 rOut_1;
uint256 rIn_2; uint256 rOut_2;

// --- TAX VARIABLES (Base 10000) ---
// 0 = Sin tax. 100 = 1%. 500 = 5%.
uint256 tax_0; 
uint256 tax_1;
uint256 tax_2;

// --- INPUT/OUTPUT ---
uint256 amount_in;
uint256 amount_out;

// --- LÓGICA SWAP CON TAX ---
uint256 get_amount_out_taxed(uint256 amountIn, uint256 reserveIn, uint256 reserveOut, uint256 tax) {
    if (amountIn == 0) return 0;
    if (reserveIn == 0) return 0;
    
    // 1. Aplicar Impuesto del Token (Deflationary Logic)
    // El contrato recibe menos de lo que envías.
    uint256 amountAfterTax = amountIn;
    if (tax > 0) {
        amountAfterTax = (amountIn * (10000 - tax)) / 10000;
    }
    
    // 2. Aplicar Fee de Uniswap (0.3%)
    uint256 amountInWithFee = amountAfterTax * 997;
    uint256 numerator = amountInWithFee * reserveOut;
    uint256 denominator = (reserveIn * 1000) + amountInWithFee;
    
    if (denominator == 0) return 0;
    return numerator / denominator;
}

int main() {
    while(1) {
        // Simulamos la ruta aplicando los impuestos específicos de cada token
        uint256 step1 = get_amount_out_taxed(amount_in, rIn_0, rOut_0, tax_0);
        uint256 step2 = get_amount_out_taxed(step1, rIn_1, rOut_1, tax_1);
        
        amount_out = get_amount_out_taxed(step2, rIn_2, rOut_2, tax_2);
        
        break;
    }
    return 0;
}