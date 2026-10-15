### Step 2: Apply RAII and Smart Pointers

**unique_ptr for Exclusive Ownership**:

```cpp
#include <memory>
#include <vector>

// unique_ptr: exactly one owner, zero overhead over raw pointer
auto widget = std::make_unique<Widget>("example", 42);
widget->activate();

// Transfer ownership with std::move
auto transferred = std::move(widget);
// widget is now nullptr; transferred owns the object

// unique_ptr in containers
std::vector<std::unique_ptr<Shape>> shapes;
shapes.push_back(std::make_unique<Circle>(5.0));
shapes.push_back(std::make_unique<Rectangle>(3.0, 4.0));

for (const auto& shape : shapes) {
    shape->draw();  // Polymorphic call
}

// Factory functions return unique_ptr to express ownership transfer
auto createParser(const std::string& format) -> std::unique_ptr<Parser> {
    if (format == "json") return std::make_unique<JsonParser>();
    if (format == "xml")  return std::make_unique<XmlParser>();
    return nullptr;
}
```

**shared_ptr and weak_ptr**:

```cpp
// shared_ptr: reference-counted shared ownership
auto config = std::make_shared<Config>();  // One allocation for object + control block

auto worker1 = std::thread([config] { config->read(); });
auto worker2 = std::thread([config] { config->read(); });
// config is destroyed when the last shared_ptr goes out of scope

// weak_ptr: non-owning observer that breaks cycles
struct Node {
    std::shared_ptr<Node> next;
    std::weak_ptr<Node> parent;  // weak_ptr prevents circular reference leak
};

// Check if the observed object still exists
std::weak_ptr<Config> observer = config;
if (auto locked = observer.lock()) {
    locked->read();  // Safe access
} else {
    // Object has been destroyed
}
```

**Custom Deleters and RAII Wrappers for C APIs**:

```cpp
// Custom deleter for C library resources (e.g., FILE*, sqlite3*)
auto file_deleter = [](FILE* fp) {
    if (fp) std::fclose(fp);
};
std::unique_ptr<FILE, decltype(file_deleter)> file(
    std::fopen("data.bin", "rb"), file_deleter
);

// Generic RAII wrapper for any C handle
template <typename Handle, auto Deleter>
class UniqueHandle {
    Handle handle_;
public:
    explicit UniqueHandle(Handle h) : handle_(h) {}
    ~UniqueHandle() { if (handle_) Deleter(handle_); }

    UniqueHandle(const UniqueHandle&) = delete;
    UniqueHandle& operator=(const UniqueHandle&) = delete;
    UniqueHandle(UniqueHandle&& other) noexcept : handle_(std::exchange(other.handle_, {})) {}
    UniqueHandle& operator=(UniqueHandle&& other) noexcept {
        if (this != &other) {
            if (handle_) Deleter(handle_);
            handle_ = std::exchange(other.handle_, {});
        }
        return *this;
    }

    Handle get() const { return handle_; }
    explicit operator bool() const { return handle_ != Handle{}; }
};

// Usage with a C library
using UniqueFd = UniqueHandle<int, +[](int fd) { ::close(fd); }>;
UniqueFd socket(::socket(AF_INET, SOCK_STREAM, 0));
```
