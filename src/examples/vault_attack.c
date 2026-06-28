/*
 * ERC4626 INFLATION ATTACK SIMULATION
 * Objetivo: Encontrar un estado donde la víctima deposita dinero
 * pero recibe 0 shares a cambio debido al redondeo.
 */

#define DIOPHANTUS_MAX_RECURSION 10
#define DIOPHANTUS_MAX_UNROLL 1

// --- ESTADO DEL VAULT ---
// El atacante manipula esto antes de que llegue la víctima
int total_assets = 0; 
int total_supply = 0;

// --- INPUTS (Lo que buscamos) ---
int attacker_donation = 0; // Cuánto tiene que inflar el pool el atacante
int victim_deposit = 0;    // Cuánto deposita la víctima

// Salida
int victim_shares = 0;

// Fórmula estándar ERC-4626 para convertir Assets -> Shares
// shares = (assets * supply) / totalAssets
int convertToShares(int assets, int currentTotalAssets, int currentSupply) {
    if (currentTotalAssets == 0) return assets; // Initial mint
    return (assets * currentSupply) / currentTotalAssets;
}

int main() {
    // 1. ESTADO INICIAL (El atacante ya tiene 1 share)
    // Supongamos que el atacante depositó 1 wei y obtuvo 1 share.
    total_supply = 1;
    total_assets = 1; 
    
    // 2. EL ATAQUE (Donación)
    // El atacante envía tokens sin mintear shares.
    // Esto infla el precio por share.
    total_assets = total_assets + attacker_donation;
    
    while(1) {
        // 3. LA VÍCTIMA DEPOSITA
        // Calculamos cuántos shares recibe la víctima
        victim_shares = convertToShares(victim_deposit, total_assets, total_supply);
        break;
    }
    return 0;
}