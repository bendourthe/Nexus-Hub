### Step 3: Design Templates and Concepts

**Function and Class Templates**:

```cpp
// Function template with automatic deduction
template <typename T>
T max_of(T a, T b) {
    return (a > b) ? a : b;
}

auto result = max_of(3.14, 2.71);  // Deduces T = double

// Class template with deduction guide (C++17 CTAD)
template <typename T>
class Stack {
    std::vector<T> data_;
public:
    void push(const T& value) { data_.push_back(value); }
    T pop() {
        T top = std::move(data_.back());
        data_.pop_back();
        return top;
    }
    bool empty() const { return data_.empty(); }
};

Stack s{42};  // CTAD deduces Stack<int>
```

**Variadic Templates and Fold Expressions**:

```cpp
// Variadic template: accept any number of arguments
template <typename... Args>
void log(const std::string& fmt, Args&&... args) {
    std::println(fmt, std::forward<Args>(args)...);
}

// Fold expressions (C++17) collapse parameter packs
template <typename... Args>
auto sum(Args... args) {
    return (args + ...);  // Unary right fold: a1 + (a2 + (a3 + ...))
}

auto total = sum(1, 2, 3, 4, 5);  // 15

// Fold with comma operator for side effects
template <typename... Args>
void print_all(Args&&... args) {
    ((std::cout << args << ' '), ...);
    std::cout << '\n';
}

// Check if all types satisfy a predicate
template <typename... Ts>
constexpr bool all_integral = (std::is_integral_v<Ts> && ...);
static_assert(all_integral<int, long, char>);
```

**C++20 Concepts (Replacing SFINAE)**:

```cpp
#include <concepts>

// Define a concept: a named set of constraints
template <typename T>
concept Numeric = std::integral<T> || std::floating_point<T>;

// Use concept as a constraint (cleaner than SFINAE)
template <Numeric T>
T clamp(T value, T lo, T hi) {
    return (value < lo) ? lo : (value > hi) ? hi : value;
}

// Concept with requires-clause for complex constraints
template <typename C>
concept Sortable = requires(C container) {
    { container.begin() } -> std::random_access_iterator;
    { container.size() }  -> std::convertible_to<std::size_t>;
    requires std::totally_ordered<typename C::value_type>;
};

template <Sortable C>
void sort_container(C& c) {
    std::ranges::sort(c);
}

// Abbreviated function template with auto + concept
void process(Numeric auto value) {
    // value is constrained to Numeric types
}

// Template specialization
template <typename T>
struct Serializer {
    static std::string serialize(const T& value) {
        return std::to_string(value);  // Default for arithmetic types
    }
};

template <>
struct Serializer<std::string> {
    static std::string serialize(const std::string& value) {
        return "\"" + value + "\"";  // Strings get quoted
    }
};
```
