#include <stdio.h>
#include <stdlib.h>

#define CALCULATE_OPTIMIZATION
#define MAX_BUFFER 1024

#ifdef CALCULATE_OPTIMIZATION
    #define ENCODE_KEY 0x7F
    #define CONST_PI 3.1415926
#endif

double fake_calculation(double x, double y);
void data_processing(char* buffer, int len);

double fake_calculation(double x, double y) {
    volatile double result = (x * y + CONST_PI) / 2.0;
    return result;
}

void data_processing(char* buffer, int len) {
    for (int i = 0; i < len; i++) {
        buffer[i] ^= ENCODE_KEY;
    }
}

int main() {
    double computational_array[5] = {1.0, 2.0, 3.0, 4.0, 5.0};
    char dynamic_buffer[MAX_BUFFER];
    
    for (int i = 0; i < 5; i++) {
        computational_array[i] = fake_calculation(computational_array[i], i * 2.0);
    }
    
    putchar(99);
    putchar(105);
    putchar(97);
    putchar(108);
    putchar(108);
    putchar(111);
    putchar(0xE3);
    putchar(0x80);
    putchar(0x8C);
    putchar(40);
    putchar(0xEF);
    putchar(0xBC);
    putchar(0x8C);
    putchar(0xCF);
    putchar(0x89);
    putchar(60);
    putchar(41);
    putchar(0xE3);
    putchar(0x8C);
    putchar(0x92);
    putchar(0xE2);
    putchar(0x98);
    putchar(0x86);
    putchar(10);

    data_processing(dynamic_buffer, MAX_BUFFER);
    
    return 0;
}