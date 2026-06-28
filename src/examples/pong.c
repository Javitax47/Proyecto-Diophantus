#include <stdio.h>
#include <conio.h>    // Para kbhit() y getch()
#include <windows.h>  // Para Sleep() y system("cls")

//======================================================================
// 1. VARIABLES DE ESTADO (S_t)
//======================================================================
// (El parser identifica estas variables globales como el "Estado")
int b = 40, c = 12, d = 1, e = 1, p = 10, q = 10, f = 0, g = 0;


// Función para mover el cursor (será ignorada por el compilador)
void xy(int x, int y) {
    COORD c;
    c.X = x;
    c.Y = y;
    SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), c);
}

int main() {
    // Ocultar el cursor (será ignorado por el compilador)
    HANDLE h = GetStdHandle(STD_OUTPUT_HANDLE);
    CONSOLE_CURSOR_INFO info = {100, 0};
    SetConsoleCursorInfo(h, &info);

    // Bucle principal del juego
    while (1) {

        //======================================================================
        // 2. ENTRADA (I_t)
        //======================================================================
        // (El parser identifica getch() como una entrada I_t)
        char k = 0; // Resetear la entrada en cada fotograma
        if (kbhit()) {
            k = getch();
        }

        // (Lógica de control de bucle. 'break' aquí es aceptable
        // ya que está fuera de la lógica de estado computable)
        if (k == 'q') {
            break;
        }

        //======================================================================
        // 3. I/O Y RENDERIZADO (IGNORADO POR EL COMPILADOR)
        //======================================================================
        xy(0, 0);
        printf("Score: %d - %d\n", f, g);

        for (int y = 0; y < 24; y++) {
            for (int x = 0; x < 80; x++) {
                if (x == 1 && y >= p && y < p + 5) printf("|");
                else if (x == 78 && y >= q && y < q + 5) printf("|");
                else if (x == b && y == c) printf("O");
                else if (y == 0 || y == 23) printf("-");
                else printf(" ");
            }
            printf("\n");
        }

        //======================================================================
        // 4. LÓGICA COMPUTABLE (La Función F)
        //======================================================================
        // (El parser "aplana" esto en la Ecuación)
        // (Todas las variables aquí son auxiliares, basadas en S_t y I_t)

        // --- 4.1. Lógica de Pala ---
        // (Regla 1: Sin '++' o '--')
        int p_next = p;
        int q_next = q;

        if (k == 'w' && p > 1) {
            p_next = p - 1;
        } else if (k == 's' && p < 18) {
            p_next = p + 1;
        }
        
        if (k == 'i' && q > 1) {
            q_next = q - 1;
        } else if (k == 'k' && q < 18) {
            q_next = q + 1;
        }

        // --- 4.2. Lógica de Movimiento (Piezas Auxiliares) ---
        // (Regla 1: Sin '+=')
        int b_movido = b + d;
        int c_movido = c + e;

        // --- 4.3. Lógica de Colisión (Paredes) ---
        // (Calcula e_next basado en el estado *actual* y las auxiliares)
        int e_next;
        if (c_movido == 1 || c_movido == 22) {
            e_next = 0 - e; // (Regla 3: Sin '-e' unario)
        } else {
            e_next = e;
        }

        // --- 4.4. Lógica de Colisión (Palas) ---
        // (Calcula d_next basado en estado, auxiliares y p_next/q_next)
        int d_next;
        // (Regla 6: Paréntesis completos)
        int colision_p1 = (b_movido == 2 && c_movido >= p_next && c_movido < (p_next + 5));
        int colision_p2 = (b_movido == 77 && c_movido >= q_next && c_movido < (q_next + 5));

        if (colision_p1 || colision_p2) {
            d_next = 0 - d; // (Regla 3: Sin '-d' unario)
        } else {
            d_next = d;
        }

        // --- 4.5. Lógica de Puntuación ---
        // (Decide el estado final de b, c, f, g)
        int f_next = f;
        int g_next = g;
        int b_final = b_movido; // Valor por defecto
        int c_final = c_movido; // Valor por defecto

        if (b_movido < 1) {
            f_next = f + 1; // (Regla 1: Sin 'f++')
            b_final = 40;
            c_final = 12;
        } else if (b_movido > 78) {
            g_next = g + 1; // (Regla 1: Sin 'g++')
            b_final = 40;
            c_final = 12;
        }
        
        //======================================================================
        // 5. COMMIT DE ESTADO (S_t = S_t+1)
        //======================================================================
        // (El parser entiende que este bloque actualiza el estado global S_t
        // para la *siguiente* iteración)
        
        b = b_final;
        c = c_final;
        d = d_next;
        e = e_next;
        p = p_next;
        q = q_next;
        f = f_next;
        g = g_next;
        
        //======================================================================
        // 6. I/O FINAL (IGNORADO POR EL COMPILADOR)
        //======================================================================
        Sleep(50);
    }
    
    return 0;
}