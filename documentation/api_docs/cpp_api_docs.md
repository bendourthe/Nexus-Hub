# C++ API Documentation

## Objective
Create complete API documentation for C++ libraries and HTTP clients, enabling developers to understand class interfaces, usage patterns, RAII, and error handling.

## Output Directory Structure

All outputs should be saved in organized directories:

```
documentation/api_docs/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `documentation/api_docs/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Class Documentation
- [ ] All public classes documented
- [ ] Member functions with signatures
- [ ] Template parameters explained
- [ ] Exception specifications documented
- [ ] Move/copy semantics clarified

### Interface Design
- [ ] Public vs private interfaces
- [ ] Virtual functions documented
- [ ] RAII patterns explained
- [ ] Smart pointer usage shown

### Error Handling
- [ ] Exception types documented
- [ ] noexcept specifications
- [ ] Error handling patterns
- [ ] std::expected usage (C++23)

### Examples
- [ ] Complete working examples
- [ ] Modern C++ HTTP clients
- [ ] RAII and smart pointer examples
- [ ] Template usage examples

## Prompt Template

~~~markdown
# C++ API Documentation Request

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="documentation/api_docs"
```

Create the required subdirectories:
```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

**Directory Structure:**
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**
- All generated files should be saved with the `${OUTPUT_DIR}/` prefix
- Examples:
  - Reports and documentation → `${OUTPUT_DIR}/exports/report.md`
  - Template files → `${OUTPUT_DIR}/templates/template.yaml`
  - Diagrams and images → `${OUTPUT_DIR}/assets/diagram.png`

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Phase 1: Library API Documentation

### Public Header (mylib.hpp)
```cpp
#pragma once

#include <memory>
#include <string>
#include <optional>
#include <expected> // C++23
#include <vector>

namespace mylib {

/**
 * @brief Error codes for library operations
 */
enum class Error {
    InvalidArgument,
    OutOfMemory,
    NotInitialized,
    IOError
};

/**
 * @brief Configuration for library
 */
struct Config {
    size_t buffer_size = 1024;
    bool enable_logging = false;
};

/**
 * @brief Main library class
 *
 * This class provides the primary interface for library functionality.
 * Instances are not copyable but moveable.
 *
 * @code
 * Config config{.buffer_size = 2048};
 * auto engine = Engine::create(config);
 * if (engine) {
 *     auto result = engine->process("input");
 * }
 * @endcode
 */
class Engine {
public:
    /**
     * @brief Factory method to create engine
     * @param config Configuration options
     * @return Engine instance or nullopt on failure
     */
    [[nodiscard]] static std::optional<Engine> create(const Config& config);

    /**
     * @brief Destructor - automatically cleans up resources
     */
    ~Engine();

    // Rule of Five - Delete copy, allow move
    Engine(const Engine&) = delete;
    Engine& operator=(const Engine&) = delete;
    Engine(Engine&&) noexcept;
    Engine& operator=(Engine&&) noexcept;

    /**
     * @brief Process input data
     * @param input Input string
     * @return Processed string or error
     * @throws Never throws (uses std::expected)
     */
    [[nodiscard]] std::expected<std::string, Error> process(std::string_view input) noexcept;

    /**
     * @brief Get current status
     * @return Status information
     */
    [[nodiscard]] std::string get_status() const noexcept;

private:
    explicit Engine(const Config& config);
    class Impl;  // Pimpl idiom
    std::unique_ptr<Impl> impl_;
};

/**
 * @brief Convert error to string
 */
[[nodiscard]] const char* error_to_string(Error error) noexcept;

} // namespace mylib
```

### Usage Example
```cpp
#include "mylib.hpp"
#include <iostream>

int main() {
    // Create engine with RAII
    mylib::Config config{.buffer_size = 2048, .enable_logging = true};

    auto engine = mylib::Engine::create(config);
    if (!engine) {
        std::cerr << "Failed to create engine\n";
        return 1;
    }

    // Process data
    auto result = engine->process("test input");
    if (result) {
        std::cout << "Result: " << *result << '\n';
    } else {
        std::cerr << "Error: " << mylib::error_to_string(result.error()) << '\n';
        return 1;
    }

    return 0;
    // Engine automatically cleaned up here
}
```

## Phase 2: HTTP Client Examples

### cpr Library (modern C++)
```cpp
#include <cpr/cpr.h>
#include <nlohmann/json.hpp>
#include <string>
#include <expected>

using json = nlohmann::json;

class APIClient {
public:
    explicit APIClient(std::string base_url, std::string api_key)
        : base_url_(std::move(base_url))
        , api_key_(std::move(api_key))
    {
    }

    struct User {
        int id;
        std::string email;
        std::string name;
    };

    [[nodiscard]] std::expected<std::vector<User>, std::string>
    list_users(int page = 1, int limit = 20) {
        auto response = cpr::Get(
            cpr::Url{base_url_ + "/api/v1/users"},
            cpr::Parameters{{"page", std::to_string(page)},
                           {"limit", std::to_string(limit)}},
            cpr::Header{{"Authorization", "Bearer " + api_key_},
                       {"Content-Type", "application/json"}},
            cpr::Timeout{30000}
        );

        if (response.status_code != 200) {
            return std::unexpected("HTTP " + std::to_string(response.status_code));
        }

        try {
            auto j = json::parse(response.text);
            std::vector<User> users;

            for (const auto& item : j["data"]) {
                users.push_back(User{
                    .id = item["id"],
                    .email = item["email"],
                    .name = item["name"]
                });
            }

            return users;
        } catch (const json::exception& e) {
            return std::unexpected(std::string("JSON error: ") + e.what());
        }
    }

    [[nodiscard]] std::expected<User, std::string>
    create_user(const std::string& email, const std::string& name) {
        json request = {
            {"email", email},
            {"name", name}
        };

        auto response = cpr::Post(
            cpr::Url{base_url_ + "/api/v1/users"},
            cpr::Header{{"Authorization", "Bearer " + api_key_},
                       {"Content-Type", "application/json"}},
            cpr::Body{request.dump()},
            cpr::Timeout{30000}
        );

        if (response.status_code != 201) {
            return std::unexpected("HTTP " + std::to_string(response.status_code));
        }

        try {
            auto j = json::parse(response.text);
            return User{
                .id = j["id"],
                .email = j["email"],
                .name = j["name"]
            };
        } catch (const json::exception& e) {
            return std::unexpected(std::string("JSON error: ") + e.what());
        }
    }

private:
    std::string base_url_;
    std::string api_key_;
};

// Usage
int main() {
    APIClient client("https://api.example.com", "your-api-key");

    // List users
    auto users = client.list_users(1, 10);
    if (users) {
        for (const auto& user : *users) {
            std::cout << user.name << " <" << user.email << ">\n";
        }
    } else {
        std::cerr << "Error: " << users.error() << '\n';
    }

    // Create user
    auto new_user = client.create_user("test@example.com", "Test User");
    if (new_user) {
        std::cout << "Created user with ID: " << new_user->id << '\n';
    } else {
        std::cerr << "Error: " << new_user.error() << '\n';
    }

    return 0;
}
```

### Boost.Beast (async HTTP)
```cpp
#include <boost/beast/core.hpp>
#include <boost/beast/http.hpp>
#include <boost/asio.hpp>
#include <iostream>

namespace beast = boost::beast;
namespace http = beast::http;
namespace net = boost::asio;
using tcp = net::ip::tcp;

class AsyncAPIClient {
public:
    explicit AsyncAPIClient(net::io_context& ioc)
        : resolver_(ioc)
        , stream_(ioc)
    {
    }

    void get_users(const std::string& host, const std::string& api_key,
                   std::function<void(std::string)> callback) {
        // Resolve host
        resolver_.async_resolve(
            host, "https",
            [this, host, api_key, callback = std::move(callback)]
            (beast::error_code ec, tcp::resolver::results_type results) {
                if (ec) {
                    callback("Resolve error: " + ec.message());
                    return;
                }

                // Connect
                stream_.async_connect(
                    results,
                    [this, host, api_key, callback]
                    (beast::error_code ec, tcp::resolver::results_type::endpoint_type) {
                        if (ec) {
                            callback("Connect error: " + ec.message());
                            return;
                        }

                        // Send HTTP request
                        http::request<http::string_body> req{http::verb::get,
                                                             "/api/v1/users", 11};
                        req.set(http::field::host, host);
                        req.set(http::field::authorization, "Bearer " + api_key);
                        req.set(http::field::content_type, "application/json");

                        http::async_write(
                            stream_, req,
                            [this, callback](beast::error_code ec, std::size_t) {
                                if (ec) {
                                    callback("Write error: " + ec.message());
                                    return;
                                }

                                // Read response
                                http::async_read(
                                    stream_, buffer_, res_,
                                    [callback](beast::error_code ec, std::size_t) {
                                        if (!ec) {
                                            callback(res_.body());
                                        } else {
                                            callback("Read error: " + ec.message());
                                        }
                                    }
                                );
                            }
                        );
                    }
                );
            }
        );
    }

private:
    tcp::resolver resolver_;
    beast::tcp_stream stream_;
    beast::flat_buffer buffer_;
    http::response<http::string_body> res_;
};
```

## Phase 3: Exception Handling

```cpp
class APIException : public std::runtime_exception {
public:
    explicit APIException(const std::string& message)
        : std::runtime_error(message)
    {
    }
};

class ValidationException : public APIException {
    using APIException::APIException;
};

class NotFoundException : public APIException {
    using APIException::APIException;
};

// Using std::expected for error handling (C++23)
template<typename T>
using Result = std::expected<T, std::error_code>;

// Or custom error type
template<typename T>
using APIResult = std::expected<T, std::string>;
```

## Phase 4: Testing

```cpp
#include <gtest/gtest.h>

TEST(APIClientTest, ListUsersSuccess) {
    APIClient client("https://api.example.com", "test-key");

    auto result = client.list_users(1, 10);

    ASSERT_TRUE(result.has_value());
    EXPECT_FALSE(result->empty());
}

TEST(APIClientTest, CreateUserInvalidEmail) {
    APIClient client("https://api.example.com", "test-key");

    auto result = client.create_user("invalid", "Test");

    ASSERT_FALSE(result.has_value());
    EXPECT_THAT(result.error(), testing::HasSubstr("400"));
}
```
```

---

## Best Practices

1. **RAII**: Use RAII for all resource management
2. **Smart Pointers**: Prefer unique_ptr, use shared_ptr sparingly
3. **Move Semantics**: Delete copy, implement move for performance
4. **Const Correctness**: Use const and constexpr liberally
5. **noexcept**: Mark functions noexcept when appropriate
6. **std::expected**: Use for error handling without exceptions
7. **Modern Features**: Use C++17/20/23 features
8. **Rule of Five/Zero**: Follow consistently

---

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/api_docs/generated_docs
mkdir -p ${OUTPUT_DIR}/api_docs/templates
mkdir -p ${OUTPUT_DIR}/api_docs/assets
mkdir -p ${OUTPUT_DIR}/api_docs/exports
```

**Save files as follows**:


- Templates → `documentation/api_docs/templates/`

- Assets → `documentation/api_docs/assets/`

- Exports → `documentation/api_docs/exports/`

Replace `{phase_name}` with the specific phase (docstrings, comments, user_docs, technical_docs, api_docs, or sbom).

~~~

## Output Format Specifications

The API documentation should:
- Document all public classes and functions
- Show modern C++ patterns (RAII, smart pointers, move semantics)
- Include exception specifications and noexcept
- Provide complete working examples
- Show HTTP client usage with modern libraries
- Target C++17/20/23 developers
---

## Verify Directory Structure

After completing all phases, verify the output structure:

```bash
tree ${OUTPUT_DIR}
```

Expected structure:
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates and scripts
├── assets/            # Images, diagrams, supplementary files
└── exports/           # Final publishable artifacts and reports
```

**Verification checklist:**
- [ ] All directories created successfully
- [ ] All files saved in correct subdirectories
- [ ] No files created in repository root
- [ ] Directory structure matches expected layout
