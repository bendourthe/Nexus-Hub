#include <string>

namespace zoo {

class Greeter {
public:
    Greeter(std::string title) : title_(title) {}

    std::string greet() {
        return hello(title_);
    }

    std::string banner;

private:
    std::string title_;
};

std::string hello(std::string n) {
    return n;
}

}  // namespace zoo
