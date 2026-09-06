### Step 4: Apply Move Semantics and Perfect Forwarding

**Rvalue References and std::move**:

```cpp
#include <utility>
#include <vector>
#include <string>

// std::move casts to rvalue reference, enabling move instead of copy
std::string source = "large payload";
std::string dest = std::move(source);
// source is now in a valid but unspecified state (likely empty)

// Moving into containers avoids copies
std::vector<std::string> names;
std::string name = "temporary";
names.push_back(std::move(name));  // Moves instead of copying
```

**Move Constructor and Rule of Five/Zero**:

```cpp
// Rule of Zero: if your class manages no resources, declare nothing
struct Point {
    double x, y, z;
    // Compiler generates copy, move, destructor automatically
};

// Rule of Five: if you manage a resource, declare all five
class Buffer {
    std::size_t size_;
    std::byte* data_;

public:
    explicit Buffer(std::size_t size)
        : size_(size), data_(new std::byte[size]{}) {}

    ~Buffer() { delete[] data_; }

    // Copy constructor
    Buffer(const Buffer& other)
        : size_(other.size_), data_(new std::byte[other.size_]) {
        std::memcpy(data_, other.data_, size_);
    }

    // Copy assignment
    Buffer& operator=(const Buffer& other) {
        if (this != &other) {
            Buffer tmp(other);       // Copy-and-swap idiom
            swap(*this, tmp);
        }
        return *this;
    }

    // Move constructor (noexcept enables optimizations in containers)
    Buffer(Buffer&& other) noexcept
        : size_(std::exchange(other.size_, 0)),
          data_(std::exchange(other.data_, nullptr)) {}

    // Move assignment
    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            size_ = std::exchange(other.size_, 0);
            data_ = std::exchange(other.data_, nullptr);
        }
        return *this;
    }

    friend void swap(Buffer& a, Buffer& b) noexcept {
        std::swap(a.size_, b.size_);
        std::swap(a.data_, b.data_);
    }
};
```

**Perfect Forwarding**:

```cpp
// std::forward preserves the value category (lvalue or rvalue) of arguments
template <typename... Args>
auto make_widget(Args&&... args) -> std::unique_ptr<Widget> {
    return std::make_unique<Widget>(std::forward<Args>(args)...);
}

// Without forward, rvalues would be treated as lvalues inside the function
// With forward, temporaries remain temporaries and trigger move constructors

// Emplace uses perfect forwarding to construct in-place
std::vector<std::pair<std::string, int>> entries;
entries.emplace_back("key", 42);  // Constructs pair directly, no copies

// Forwarding reference vs rvalue reference
template <typename T>
void wrapper(T&& arg) {           // Forwarding reference (deduced context)
    inner(std::forward<T>(arg));  // Preserves lvalue/rvalue
}

void takes_rvalue(std::string&& s);  // Rvalue reference (concrete type)
```
