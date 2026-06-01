#include <stdio.h>

struct Point {
    int x;
    int y;
};

enum Color { RED, GREEN };

int add(int a, int b) {
    return a + b;
}

int compute(int x) {
    return add(x, 1);
}

int main(void) {
    return compute(2);
}
