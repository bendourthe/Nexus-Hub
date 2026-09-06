### Step 1: Master Modern C++ Fundamentals

**Auto and Structured Bindings**:

```cpp
#include <map>
#include <string>
#include <tuple>

// auto deduces the type from the initializer
auto count = 42;                  // int
auto ratio = 3.14;                // double
auto name  = std::string{"Ada"};  // std::string (not const char*)

// Trailing return type for complex deductions
auto divide(int a, int b) -> std::pair<int, int> {
    return {a / b, a % b};
}

// Structured bindings (C++17) unpack aggregates into named variables
auto [quotient, remainder] = divide(17, 5);

// Iterate a map with structured bindings
std::map<std::string, int> scores{{"Alice", 95}, {"Bob", 87}};
for (const auto& [name, score] : scores) {
    std::println("{}: {}", name, score);  // C++23 print
}

// Structured bindings work with arrays and custom types too
int arr[3] = {10, 20, 30};
auto [x, y, z] = arr;
```

**Constexpr, Consteval, and Constinit**:

```cpp
// constexpr: may be evaluated at compile time or runtime
constexpr int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) result *= i;
    return result;
}

// consteval (C++20): must be evaluated at compile time
consteval int compile_time_square(int n) {
    return n * n;
}
static_assert(compile_time_square(5) == 25);

// constinit (C++20): ensures static/thread-local variable is constant-initialized
// Prevents the "static initialization order fiasco"
constinit int global_limit = factorial(5);  // Initialized at compile time

// if constexpr: compile-time branch elimination
template <typename T>
auto stringify(T value) -> std::string {
    if constexpr (std::is_arithmetic_v<T>) {
        return std::to_string(value);
    } else if constexpr (std::is_same_v<T, std::string>) {
        return value;
    } else {
        static_assert(false, "Unsupported type");
    }
}
```

**Designated Initializers and Spaceship Operator**:

```cpp
// Designated initializers (C++20) make aggregate init self-documenting
struct Config {
    std::string host = "localhost";
    int port         = 8080;
    int max_conns    = 100;
    bool tls         = false;
};

Config cfg{.port = 9090, .tls = true};  // Only override what you need

// Three-way comparison / spaceship operator (C++20)
#include <compare>

struct Version {
    int major;
    int minor;
    int patch;

    auto operator<=>(const Version&) const = default;  // Generates all 6 operators
};

Version v1{2, 1, 0}, v2{2, 3, 0};
bool older = (v1 < v2);  // true, generated automatically
```

**Modules (C++20)**:

```cpp
// math.cppm (module interface unit)
export module math;

export int add(int a, int b) { return a + b; }
export int multiply(int a, int b) { return a * b; }

// main.cpp (consumer)
import math;

int main() {
    return add(2, multiply(3, 4));  // No header needed
}
```
