## Common Patterns

### Pattern 1: Type-Erased Polymorphism (std::function / std::any)

```cpp
#include <functional>
#include <vector>

// Callback registry using std::function
class EventBus {
    std::unordered_map<std::string, std::vector<std::function<void()>>> handlers_;

public:
    void on(const std::string& event, std::function<void()> handler) {
        handlers_[event].push_back(std::move(handler));
    }

    void emit(const std::string& event) {
        if (auto it = handlers_.find(event); it != handlers_.end()) {
            for (auto& handler : it->second) {
                handler();
            }
        }
    }
};
```

### Pattern 2: CRTP for Static Polymorphism

```cpp
template <typename Derived>
class Comparable {
public:
    bool operator!=(const Derived& other) const {
        return !(static_cast<const Derived&>(*this) == other);
    }
    bool operator>(const Derived& other) const {
        return other < static_cast<const Derived&>(*this);
    }
    bool operator<=(const Derived& other) const {
        return !(static_cast<const Derived&>(*this) > other);
    }
    bool operator>=(const Derived& other) const {
        return !(static_cast<const Derived&>(*this) < other);
    }
};

class Temperature : public Comparable<Temperature> {
    double celsius_;
public:
    explicit Temperature(double c) : celsius_(c) {}
    bool operator==(const Temperature& other) const { return celsius_ == other.celsius_; }
    bool operator<(const Temperature& other) const  { return celsius_ < other.celsius_; }
};
```
