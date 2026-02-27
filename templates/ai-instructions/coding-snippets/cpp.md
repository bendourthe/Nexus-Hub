## C++ Conventions

**Tooling**:
- **Build**: CMake
- **Compiler**: GCC/Clang/MSVC
- **Formatting**: Clang-Format
- **Target**: C++17/20 (structured bindings, `constexpr`, `std::optional`, `std::variant`)

**Naming**: Follow project convention (Google Style: `snake_case` for vars, `PascalCase` for types). Consistency is key.

**Code Patterns**:
- RAII for all resource management
- Smart pointers (`std::unique_ptr`, `std::shared_ptr`) instead of `new`/`delete`
- `std::vector`/`std::array` instead of raw arrays
- `#pragma once` or include guards for headers
- `const` correctness (mark methods/parameters `const` wherever possible)
- Pass complex objects by `const&` to avoid copies
- Standard exceptions (`std::runtime_error`) or error codes per project convention

**Testing**: GoogleTest (GTest) or Catch2.

```cpp
#include <gtest/gtest.h>

TEST(MathTest, AddsNumbers) {
    EXPECT_EQ(add(2, 3), 5);
}
```
