#include <stdio.h>
int main() {
    int a, i, n;
    char str[512]; // auxiliar na leitura com G
    { gets(str);
    sscanf(str, "%d", &n);
    }
    i = 2;
    a = n % i;
    while ( i < n ) {
        {
            if ( a == 0 ) {
                i = n;
            }
            i = i + 1;
            a = n % i;
        }
    }
    if ( a == 0 ) {
        printf("%d\n", 0);
    }
    if ( a != 0 ) {
        printf("%d\n", 1);
    }
    gets(str);
    return 0;
}