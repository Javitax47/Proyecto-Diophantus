// Inputs del Certificado
int n = 0;
int a = 0;
int b = 0;
int Gx = 0;
int Gy = 0;
int m = 0;

// Salida: 0 si es Primo Certificado (Energía Nula)
int result = 0;

// Utilidad: Resta Modular
int mod_sub(int x, int y, int mod) {
    int res = (x - y) % mod;
    if (res < 0) return res + mod;
    return res;
}

// Multiplicación Escalar Recursiva (Double-and-Add Jacobiano)
// Coordenadas Jacobianas: El punto real es (x/z^2, y/z^3)
int ecpp_recursive_step(int n_in, int a_in, 
                        int ax, int ay, int az, 
                        int cx, int cy, int cz, 
                        int k) {
    
    if (k == 0) {
        return (az * az) % n_in; // Si Z=0, es el punto infinito -> Éxito
    } else {
        // --- 1. LÓGICA ADD (Mixed Addition: Acc + Curr) ---
        // Asumimos que Curr (cx, cy, cz) está normalizado o es la base, 
        // pero para la recursión general usamos suma completa.
        
        int next_ax = ax; int next_ay = ay; int next_az = az;

        if (k % 2 != 0) {
            if (az == 0) {
                next_ax = cx; next_ay = cy; next_az = cz;
            } else {
                // Fórmulas Jacobianas (Z2 != 1 general)
                // U1 = X1*Z2^2, U2 = X2*Z1^2
                int Z1_2 = (az * az) % n_in;
                int Z2_2 = (cz * cz) % n_in;
                
                int U1 = (ax * Z2_2) % n_in;
                int U2 = (cx * Z1_2) % n_in;
                
                // S1 = Y1*Z2^3, S2 = Y2*Z1^3
                int Z1_3 = (Z1_2 * az) % n_in;
                int Z2_3 = (Z2_2 * cz) % n_in;
                
                int S1 = (ay * Z2_3) % n_in;
                int S2 = (cy * Z1_3) % n_in;
                
                if (U1 == U2) {
                    if (S1 != S2) {
                        // P + (-P) = Infinito (0, 1, 0)
                        next_ax = 0; next_ay = 1; next_az = 0;
                    }
                    // Si S1 == S2, es duplicación. No lo manejamos en ADD para simplificar el grafo.
                    // Asumimos orden k tal que no ocurre duplicación en el paso ADD.
                } else {
                    int H = mod_sub(U2, U1, n_in);
                    int R = mod_sub(S2, S1, n_in);
                    
                    int H2 = (H * H) % n_in;
                    int H3 = (H2 * H) % n_in;
                    
                    // X3 = R^2 - H^3 - 2*U1*H^2
                    int R2 = (R * R) % n_in;
                    int U1H2 = (U1 * H2) % n_in;
                    int temp_x = mod_sub(R2, H3, n_in);
                    next_ax = mod_sub(temp_x, (2 * U1H2) % n_in, n_in);
                    
                    // Y3 = R*(U1*H^2 - X3) - S1*H3
                    int term_y = mod_sub(U1H2, next_ax, n_in);
                    term_y = (R * term_y) % n_in;
                    int S1H3 = (S1 * H3) % n_in;
                    next_ay = mod_sub(term_y, S1H3, n_in);
                    
                    // Z3 = Z1*Z2*H
                    int Z1Z2 = (az * cz) % n_in;
                    next_az = (Z1Z2 * H) % n_in;
                }
            }
        }

        // --- 2. LÓGICA DOUBLE (Curr = 2 * Curr) ---
        // Fórmulas Jacobianas
        
        int dob_x = cx; int dob_y = cy; int dob_z = cz;
        
        if (cz != 0) { // Si no es infinito
            // M = 3*X^2 + a*Z^4
            int XX = (cx * cx) % n_in;
            int ZZ = (cz * cz) % n_in;
            int Z4 = (ZZ * ZZ) % n_in;
            int term_a = (a_in * Z4) % n_in;
            int M = (3 * XX) % n_in;
            M = (M + term_a) % n_in;
            
            // S = 4*X*Y^2
            int YY = (cy * cy) % n_in;
            int S = (4 * cx) % n_in;
            S = (S * YY) % n_in;
            
            // X3 = M^2 - 2*S
            int M2 = (M * M) % n_in;
            dob_x = mod_sub(M2, (2 * S) % n_in, n_in);
            
            // Y3 = M*(S - X3) - 8*Y^4
            int Y4 = (YY * YY) % n_in;
            int term_dy = mod_sub(S, dob_x, n_in);
            term_dy = (M * term_dy) % n_in;
            int term_8Y4 = (8 * Y4) % n_in;
            dob_y = mod_sub(term_dy, term_8Y4, n_in);
            
            // Z3 = 2*Y*Z
            dob_z = (2 * cy) % n_in;
            dob_z = (dob_z * cz) % n_in;
        }

        return ecpp_recursive_step(n_in, a_in, 
                                   next_ax, next_ay, next_az, 
                                   dob_x, dob_y, dob_z, 
                                   k / 2);
    }
}

int verify_ecpp_energy(int n_in, int a_in, int b_in, int Gx_in, int Gy_in, int m_in) {
    // 1. Error Curva: y^2 - (x^3 + ax + b)
    int lhs = (Gy_in * Gy_in) % n_in;
    int x2 = (Gx_in * Gx_in) % n_in;
    int x3 = (x2 * Gx_in) % n_in;
    int ax = (a_in * Gx_in) % n_in;
    int rhs = (x3 + ax + b_in) % n_in;
    int err_curve = mod_sub(lhs, rhs, n_in);
    
    // 2. Error Orden: m*G (en Jacobiano)
    // Acc inicial: (0, 1, 0) Infinito
    // Curr inicial: (Gx, Gy, 1) Punto Base Z=1
    int err_order = ecpp_recursive_step(n_in, a_in, 
                                        0, 1, 0, 
                                        Gx_in, Gy_in, 1, 
                                        m_in);
    
    return (err_curve * err_curve) + err_order;
}

int main() {
    while(1) {
        result = verify_ecpp_energy(n, a, b, Gx, Gy, m);
        break;
    }
    return 0;
}