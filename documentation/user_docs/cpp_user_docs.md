# C++ User Documentation

## Objective
Create clear, comprehensive user-facing documentation that enables users of all skill levels to quickly understand, install, configure, and effectively use the C++ software using CMake ecosystem and modern C++ standards.

## Output Directory Structure

All outputs should be saved in organized directories:

```
documentation/user_docs/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `documentation/user_docs/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### README Structure

- [ ] Compelling project overview and value proposition

- [ ] Key features highlighted

- [ ] Installation instructions complete and tested

- [ ] Quick start guide for immediate success

- [ ] Usage examples for common scenarios

- [ ] Links to detailed documentation

### Installation Guides

- [ ] Prerequisites clearly listed (compiler, C++ version, CMake)

- [ ] Step-by-step installation process

- [ ] Platform-specific instructions (Windows, macOS, Linux)

- [ ] Troubleshooting common installation issues

- [ ] Verification steps to confirm successful installation

### Quick Start Guides

- [ ] Minimal example to first success

- [ ] Common use cases covered

- [ ] Progressive complexity (simple to advanced)

- [ ] Expected output shown

- [ ] Next steps guidance

### Usage Examples

- [ ] Real-world scenarios

- [ ] Complete, runnable code

- [ ] Input/output examples

- [ ] Edge cases and limitations

- [ ] Best practices demonstrated

### FAQ and Troubleshooting

- [ ] Common questions answered

- [ ] Error messages explained

- [ ] Debugging guidance

- [ ] Known limitations documented

- [ ] Where to get help

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C++ User Documentation Request

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="documentation/user_docs"
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

Please create comprehensive user documentation for this C++ project following this protocol:

## Phase 1: Audience Analysis & Documentation Planning

1. **Identify Target Audience**
   - Primary users: [game developers/systems programmers/library users/etc.]
   - Technical skill level: [beginner/intermediate/advanced]
   - Use cases: [what problems they're solving]
   - Context: [how they'll use the software]

2. **Document Existing Features**
   - List all major features and capabilities
   - Identify most common use cases
   - Note any complex or non-obvious functionality
   - Document prerequisites and dependencies

3. **Outline Documentation Structure**
   Plan what documentation is needed:
   - [ ] README.md (essential)
   - [ ] INSTALL.md or installation section
   - [ ] QUICKSTART.md or quick start guide
   - [ ] USER_GUIDE.md for detailed usage
   - [ ] EXAMPLES.md with common patterns
   - [ ] FAQ.md for common questions
   - [ ] TROUBLESHOOTING.md for common issues
   - [ ] API.md for class/function reference

## Phase 2: README.md - Professional Project Overview

Create a comprehensive README.md that serves as the front door to your project:

### README.md Template

```markdown
# [Project Name]

[![C++](https://img.shields.io/badge/C%2B%2B-17%2B-blue)](https://isocpp.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/github/workflow/status/username/project/CI)](https://github.com/username/project/actions)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)]()

[One-sentence description of what the project does]

---

## ✨ What's New in v[X.Y.Z]

- 🚀 [New Feature 1]: Brief description

- ⚡ [Performance Improvement]: Specific metric (e.g., "50% faster")

- 🐛 [Important Bug Fix]: What was fixed

- 📝 [Documentation Update]: What was improved

[See full changelog](CHANGELOG.md)

---

## 📋 Overview

[2-3 paragraph description of the project]

**Problem**: [What problem does this solve?]

**Solution**: [How does this project solve it?]

**Benefits**:

- ✅ [Key benefit 1]

- ✅ [Key benefit 2]

- ✅ [Key benefit 3]

---

## 🎯 Key Features

- **[Feature 1]**: Description of what it does and why it matters

- **[Feature 2]**: Highlight unique or powerful capabilities

- **[Feature 3]**: Emphasize modern C++ features used

- **[Feature 4]**: Note compatibility and portability features

---

## 🚀 Quick Start

Get started in less than 5 minutes:

### Installation

**Using CMake (Recommended)**:
```bash
# Clone repository
git clone https://github.com/username/project.git
cd project

# Build
mkdir build && cd build
cmake ..
cmake --build .

# Install
sudo cmake --install .
```

**Using package managers**:
```bash
# vcpkg
vcpkg install project

# Conan
conan install project/1.2.3@

# Homebrew (macOS)
brew install project
```

### Basic Usage

**Header-only library**:
```cpp
#include <project/project.hpp>

int main() {
    // Simple example showing immediate value
    project::Client client;
    auto result = client.process("example input");
    std::cout << result << std::endl;
    // Output: [expected output]
    return 0;
}
```

**Compiled library**:
```cpp
#include <project/project.hpp>

int main() {
    try {
        project::Client client;
        auto result = client.process("example input");
        std::cout << "Result: " << result << std::endl;
    } catch (const project::Exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    return 0;
}
```

**Compile**:
```bash
g++ -std=c++17 -o myapp main.cpp -lproject
# Or with CMake
cmake --build . --target myapp
```

**That's it!** You're ready to go. See [Usage Examples](#usage-examples) for more.

---

## 📦 Installation

### Prerequisites

Before installing, ensure you have:

- C++17 compiler or higher (GCC 7+, Clang 5+, MSVC 2017+)

- CMake 3.15 or higher

- [Optional] Package manager (vcpkg, Conan, or system package manager)

### Compiler Support

| Compiler | Minimum Version | Recommended |
|----------|----------------|-------------|
| GCC      | 7.0            | 11+         |
| Clang    | 5.0            | 13+         |
| MSVC     | 2017 (19.14)   | 2022        |
| AppleClang | 10.0         | Latest      |

### Installation Options

#### Option 1: CMake (System Installation)

```bash
# Clone repository
git clone https://github.com/username/project.git
cd project

# Create build directory
mkdir build && cd build

# Configure
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build
cmake --build . --config Release

# Run tests
ctest

# Install
sudo cmake --install .
```

#### Option 2: CMake (FetchContent)

Add to your `CMakeLists.txt`:
```cmake
include(FetchContent)

FetchContent_Declare(
  project
  GIT_REPOSITORY https://github.com/username/project.git
  GIT_TAG        v1.2.3
)

FetchContent_MakeAvailable(project)

target_link_libraries(myapp PRIVATE project::project)
```

#### Option 3: CMake (find_package)

After system installation:
```cmake
find_package(Project REQUIRED)
target_link_libraries(myapp PRIVATE Project::Project)
```

#### Option 4: vcpkg

```bash
# Install vcpkg
git clone https://github.com/Microsoft/vcpkg.git
./vcpkg/bootstrap-vcpkg.sh

# Install package
./vcpkg/vcpkg install project
```

Then in `CMakeLists.txt`:
```cmake
find_package(Project CONFIG REQUIRED)
target_link_libraries(myapp PRIVATE Project::Project)
```

#### Option 5: Conan

Create `conanfile.txt`:
```ini
[requires]
project/1.2.3

[generators]
CMakeDeps
CMakeToolchain
```

```bash
# Install dependencies
conan install . --build=missing

# Build with Conan toolchain
cmake .. -DCMAKE_TOOLCHAIN_FILE=conan_toolchain.cmake
cmake --build .
```

#### Option 6: Header-Only

For header-only libraries:
```bash
# Copy include directory to your project
cp -r include/project /path/to/your/project/include/
```

### Verify Installation

```bash
# Check installation
ls /usr/local/include/project/
ls /usr/local/lib/libproject.*

# Test compilation
cat > test.cpp << 'EOF'
#include <project/project.hpp>
#include <iostream>

int main() {
    std::cout << "Version: " << PROJECT_VERSION << std::endl;
    return 0;
}
EOF

g++ -std=c++17 test.cpp -lproject
./a.out
```

**Troubleshooting**: See [Installation Issues](#installation-issues) if you encounter problems.

---

## 💡 Usage Examples

### Example 1: Basic Usage

[Description of what this example demonstrates]

```cpp
#include <project/project.hpp>
#include <iostream>

int main() {
    // Setup with options
    project::Options opts{
        .option1 = "value",
        .option2 = 42,
        .debug = false
    };

    project::Client client(opts);

    // Process data
    try {
        auto result = client.process("input data");
        std::cout << "Result: " << result << std::endl;
    } catch (const project::ProcessingException& e) {
        std::cerr << "Processing failed: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
```

**Compile**:
```bash
g++ -std=c++17 -o basic basic.cpp -lproject
./basic
```

**Output**:
```
Result: processed_data
```

### Example 2: Modern C++ Features

[Description using modern C++ patterns]

```cpp
#include <project/project.hpp>
#include <iostream>
#include <memory>
#include <vector>
#include <algorithm>

int main() {
    // Use smart pointers
    auto client = std::make_unique<project::Client>();

    // Range-based for loop with structured bindings
    std::vector<std::string> inputs{"item1", "item2", "item3"};

    // Use STL algorithms with lambdas
    std::vector<std::string> results;
    std::transform(inputs.begin(), inputs.end(),
                   std::back_inserter(results),
                   [&client](const auto& input) {
                       return client->process(input);
                   });

    // Print results
    for (const auto& [idx, result] : std::views::enumerate(results)) {
        std::cout << idx << ": " << result << std::endl;
    }

    return 0;
}
```

### Example 3: Async/Concurrent Processing

[Description of async patterns]

```cpp
#include <project/project.hpp>
#include <iostream>
#include <future>
#include <vector>

int main() {
    project::Client client;

    // Launch async tasks
    std::vector<std::future<std::string>> futures;
    std::vector<std::string> inputs{"item1", "item2", "item3"};

    for (const auto& input : inputs) {
        futures.push_back(
            std::async(std::launch::async, [&client, input]() {
                return client.process(input);
            })
        );
    }

    // Collect results
    for (auto& future : futures) {
        try {
            auto result = future.get();
            std::cout << "Result: " << result << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "Error: " << e.what() << std::endl;
        }
    }

    return 0;
}
```

### Example 4: RAII and Exception Safety

[Description of resource management]

```cpp
#include <project/project.hpp>
#include <iostream>
#include <fstream>

// RAII wrapper for custom resource
class ResourceGuard {
public:
    explicit ResourceGuard(project::Resource* res)
        : resource_(res) {}

    ~ResourceGuard() {
        if (resource_) {
            project::release_resource(resource_);
        }
    }

    // Prevent copying, allow moving
    ResourceGuard(const ResourceGuard&) = delete;
    ResourceGuard& operator=(const ResourceGuard&) = delete;
    ResourceGuard(ResourceGuard&& other) noexcept
        : resource_(std::exchange(other.resource_, nullptr)) {}
    ResourceGuard& operator=(ResourceGuard&& other) noexcept {
        std::swap(resource_, other.resource_);
        return *this;
    }

    project::Resource* get() const { return resource_; }

private:
    project::Resource* resource_;
};

int main() {
    try {
        project::Client client;

        // RAII ensures cleanup even if exceptions occur
        ResourceGuard guard(project::acquire_resource());

        auto result = client.process_with_resource(
            guard.get(), "complex input"
        );

        std::cout << "Result: " << result << std::endl;

    } catch (const project::Exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    // ResourceGuard destructor called automatically

    return 0;
}
```

### Example 5: Template Usage

[Description of generic programming]

```cpp
#include <project/project.hpp>
#include <iostream>
#include <vector>
#include <string>

// Generic processing function
template<typename Container>
auto process_all(project::Client& client, const Container& items) {
    using ValueType = typename Container::value_type;
    std::vector<std::string> results;

    for (const auto& item : items) {
        if constexpr (std::is_same_v<ValueType, std::string>) {
            results.push_back(client.process(item));
        } else {
            results.push_back(client.process(std::to_string(item)));
        }
    }

    return results;
}

int main() {
    project::Client client;

    // Works with strings
    std::vector<std::string> strings{"a", "b", "c"};
    auto string_results = process_all(client, strings);

    // Works with numbers
    std::vector<int> numbers{1, 2, 3};
    auto number_results = process_all(client, numbers);

    // Print results
    for (const auto& result : string_results) {
        std::cout << result << std::endl;
    }

    return 0;
}
```

**More Examples**: See [examples/](examples/) directory for additional use cases.

---

## 🔧 Configuration

### CMake Configuration Options

```bash
# Standard CMake options
cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_STANDARD=17 \
  -DCMAKE_INSTALL_PREFIX=/usr/local

# Project-specific options
cmake .. \
  -DBUILD_SHARED_LIBS=ON \
  -DENABLE_TESTING=ON \
  -DENABLE_EXAMPLES=ON \
  -DENABLE_FEATURE_X=ON
```

### Runtime Configuration

```cpp
#include <project/project.hpp>

int main() {
    project::Config config{
        .buffer_size = 8192,
        .timeout = std::chrono::seconds(30),
        .enable_caching = true
    };

    project::Client client(config);
    // Use client...
    return 0;
}
```

### Compiler Flags

```bash
# Enable optimizations
g++ -std=c++17 -O3 -march=native -DNDEBUG main.cpp -lproject

# Debug build
g++ -std=c++17 -g -O0 -fsanitize=address,undefined main.cpp -lproject

# With warnings
g++ -std=c++17 -Wall -Wextra -Wpedantic main.cpp -lproject
```

---

## 📚 Documentation

- **[User Guide](docs/USER_GUIDE.md)**: Comprehensive usage documentation

- **[API Reference](https://username.github.io/project/api/)**: Complete API documentation

- **[Examples](examples/)**: More code examples and patterns

- **[FAQ](docs/FAQ.md)**: Frequently asked questions

- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Common issues and solutions

---

## ❓ FAQ

### How do I [common task]?

[Clear, concise answer with code example if relevant]

### Which C++ standard should I use?

C++17 is the minimum requirement. C++20 is recommended for best features and performance.

### Is this thread-safe?

[Thread safety information and guidelines]

### Can I use this with [framework/library]?

[Compatibility information]

### How do I contribute?

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

**More Questions?** Check the full [FAQ](docs/FAQ.md) or [open an issue](https://github.com/username/project/issues).

---

## 🐛 Troubleshooting

### Compilation Issues

**Problem**: `error: 'optional' is not a member of 'std'`

**Cause**: Compiler doesn't support C++17

**Solution**: Ensure C++17 is enabled:
```bash
g++ -std=c++17 main.cpp -lproject
# Or in CMakeLists.txt:
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
```

### Linking Issues

**Error**: `undefined reference to 'project::Client::process(std::string const&)'`

**Cause**: Missing library link or ABI mismatch

**Solution**:
```bash
# Ensure library is linked
g++ main.cpp -lproject

# Check library location
ldconfig -p | grep project

# Specify library path if needed
g++ main.cpp -L/usr/local/lib -lproject
```

**More Issues?** See full [Troubleshooting Guide](docs/TROUBLESHOOTING.md).

---

## 🧪 Testing

Run the test suite:

```bash
# CMake
mkdir build && cd build
cmake .. -DENABLE_TESTING=ON
cmake --build .
ctest

# With verbose output
ctest --verbose

# Run specific test
ctest -R TestName

# With sanitizers
cmake .. -DENABLE_SANITIZERS=ON
cmake --build .
ctest
```

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Quick start for contributors:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Format code (`clang-format -i src/*.cpp`)
5. Run tests (`ctest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- [Contributor/Library]: For [contribution/inspiration]

- [Resource]: For [helpful resource]

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/username/project/issues)

- **Discussions**: [GitHub Discussions](https://github.com/username/project/discussions)

- **Discord**: [C++ Community](https://discord.gg/...)

- **Documentation**: [https://username.github.io/project](https://username.github.io/project)

---

## 🗺️ Roadmap

- [ ] v[X+1].0: [Planned major feature]

- [ ] v[X].Y: [Planned minor feature]

- [ ] C++20 module support

- [ ] [Future feature/improvement]

See [ROADMAP.md](ROADMAP.md) for detailed plans.

---

**Made with ❤️ by [Your Name/Organization]**
```

## Phase 3: Installation Guide

### INSTALL.md Template

```markdown
# Installation Guide

Complete installation instructions for [Project Name].

---

## System Requirements

### Minimum Requirements

- **OS**: Linux (kernel 3.x+), macOS 10.15+, Windows 10+

- **Compiler**: GCC 7+, Clang 5+, or MSVC 2017+

- **C++ Standard**: C++17 or higher

- **CMake**: 3.15 or higher

- **RAM**: 2GB minimum, 4GB recommended

- **Disk Space**: 200MB

### Recommended Requirements

- GCC 11+ or Clang 13+ or MSVC 2022

- C++20 support for latest features

- CMake 3.20+

- 8GB RAM for development

---

## Installation Methods

### Method 1: CMake (System Installation)

```bash
# Clone repository
git clone https://github.com/username/project.git
cd project

# Create build directory
mkdir build && cd build

# Configure
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build
cmake --build . --config Release -j4

# Run tests
ctest

# Install
sudo cmake --install .
# Or for user installation:
cmake --install . --prefix ~/.local
```

### Method 2: CMake FetchContent

Add to your `CMakeLists.txt`:
```cmake
cmake_minimum_required(VERSION 3.15)
project(MyApp)

include(FetchContent)

FetchContent_Declare(
  project
  GIT_REPOSITORY https://github.com/username/project.git
  GIT_TAG        v1.2.3  # or main for latest
)

FetchContent_MakeAvailable(project)

add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE project::project)
target_compile_features(myapp PRIVATE cxx_std_17)
```

### Method 3: vcpkg

```bash
# Install vcpkg
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
./bootstrap-vcpkg.sh

# Install package
./vcpkg install project

# Use in CMake
cmake .. -DCMAKE_TOOLCHAIN_FILE=/path/to/vcpkg/scripts/buildsystems/vcpkg.cmake
```

### Method 4: Conan

Create `conanfile.txt`:
```ini
[requires]
project/1.2.3

[generators]
CMakeDeps
CMakeToolchain

[options]
project:shared=True
```

```bash
# Install dependencies
conan install . --output-folder=build --build=missing

# Configure and build
cd build
cmake .. -DCMAKE_TOOLCHAIN_FILE=conan_toolchain.cmake
cmake --build .
```

---

## Platform-Specific Instructions

### Linux

#### Ubuntu/Debian
```bash
# Install build tools
sudo apt-get update
sudo apt-get install build-essential cmake git

# For C++20 support
sudo apt-get install g++-11

# Install dependencies (example)
sudo apt-get install libdependency-dev

# Clone and build
git clone https://github.com/username/project.git
cd project
mkdir build && cd build
cmake .. -DCMAKE_CXX_COMPILER=g++-11
cmake --build . -j4
sudo cmake --install .
```

#### Fedora/RHEL
```bash
# Install build tools
sudo dnf groupinstall "Development Tools"
sudo dnf install cmake git gcc-c++

# Clone and build
git clone https://github.com/username/project.git
cd project
mkdir build && cd build
cmake ..
cmake --build . -j4
sudo cmake --install .
```

### macOS

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Or install via Homebrew
brew install cmake

# Clone and build
git clone https://github.com/username/project.git
cd project
mkdir build && cd build
cmake ..
cmake --build . -j4
sudo cmake --install .

# Or install via Homebrew (if available)
brew install project
```

### Windows

**Using Visual Studio**:
```cmd
REM Open Visual Studio 2019/2022
REM File -> Open -> CMake...
REM Select CMakeLists.txt
REM Build -> Build All
```

**Using CMake GUI**:
1. Open CMake GUI
2. Set source directory to project root
3. Set build directory to `project/build`
4. Click "Configure"
5. Select compiler (Visual Studio or MinGW)
6. Click "Generate"
7. Click "Open Project" or build from command line

**Using Command Line (VS)**:
```cmd
git clone https://github.com/username/project.git
cd project
mkdir build && cd build
cmake .. -G "Visual Studio 16 2019" -A x64
cmake --build . --config Release
cmake --install . --prefix C:\Program Files\Project
```

**Using MinGW**:
```cmd
git clone https://github.com/username/project.git
cd project
mkdir build && cd build
cmake .. -G "MinGW Makefiles"
cmake --build .
cmake --install .
```

---

## CMake Options

```bash
# Build type
cmake .. -DCMAKE_BUILD_TYPE=Release  # or Debug, RelWithDebInfo

# C++ standard
cmake .. -DCMAKE_CXX_STANDARD=17  # or 20, 23

# Install prefix
cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local

# Build shared/static library
cmake .. -DBUILD_SHARED_LIBS=ON

# Enable testing
cmake .. -DENABLE_TESTING=ON

# Enable examples
cmake .. -DENABLE_EXAMPLES=ON

# Parallel build
cmake --build . -j4
```

---

## Using in Your Project

### CMake find_package

After system installation:
```cmake
cmake_minimum_required(VERSION 3.15)
project(MyApp)

find_package(Project REQUIRED)

add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE Project::Project)
target_compile_features(myapp PRIVATE cxx_std_17)
```

### CMake FetchContent

```cmake
include(FetchContent)
FetchContent_Declare(
  project
  GIT_REPOSITORY https://github.com/username/project.git
  GIT_TAG v1.2.3
)
FetchContent_MakeAvailable(project)

target_link_libraries(myapp PRIVATE project::project)
```

### Manual Compilation

```bash
# Compile with installed library
g++ -std=c++17 -o myapp main.cpp -lproject

# With include path
g++ -std=c++17 -I/usr/local/include -o myapp main.cpp -L/usr/local/lib -lproject

# Header-only
g++ -std=c++17 -I/path/to/project/include -o myapp main.cpp
```

---

## Verification

### Quick Verification

```bash
# Check installation
ls /usr/local/include/project/
ls /usr/local/lib/libproject.*

# Test program
cat > test.cpp << 'EOF'
#include <project/project.hpp>
#include <iostream>

int main() {
    std::cout << "Version: " << PROJECT_VERSION << std::endl;
    return 0;
}
EOF

g++ -std=c++17 test.cpp -lproject
./a.out
```

### Full Verification

```bash
# Clone and test
git clone https://github.com/username/project.git
cd project
mkdir build && cd build
cmake .. -DENABLE_TESTING=ON
cmake --build .
ctest --verbose
```

---

## Troubleshooting

### Common CMake Errors

**Error**: `CMake Error: CMake was unable to find a build program corresponding to "Ninja"`

- **Cause**: Build tool not found

- **Fix**: Install ninja or specify generator: `cmake .. -G "Unix Makefiles"`

**Error**: `Could NOT find Project (missing: Project_DIR)`

- **Cause**: Package not installed or not in CMake search path

- **Fix**: Specify location: `cmake .. -DProject_DIR=/path/to/ProjectConfig.cmake`

### Common Compiler Errors

**Error**: `error: 'filesystem' is not a member of 'std'`

- **Cause**: C++17 not enabled or old compiler

- **Fix**: Add `-std=c++17` and link `-lstdc++fs` (GCC < 9)

**Error**: ABI compatibility issues

- **Cause**: Different C++ standard between library and application

- **Fix**: Use same standard for both

### Getting Help

If installation fails:
1. Check [GitHub Issues](https://github.com/username/project/issues)
2. Review [Troubleshooting Guide](TROUBLESHOOTING.md)
3. Open a new issue with:
   - Your OS and version
   - Compiler version (`g++ --version`)
   - CMake version (`cmake --version`)
   - Full error message
   - CMake output

---

## Next Steps

After successful installation:
1. Review the [Quick Start Guide](README.md#quick-start)
2. Try the [examples/](examples/) directory
3. Read the [API Reference](https://username.github.io/project/api/)
4. Check the [User Guide](USER_GUIDE.md)
```

## Phase 4: Quick Start Guide

### Quick Start Template

```markdown
# Quick Start Guide

Get started with [Project Name] in under 10 minutes.

---

## What You'll Build

By the end of this guide, you'll have:

- ✅ Built and installed [Project Name]

- ✅ Created your first C++ program using the library

- ✅ Understanding of core concepts

- ✅ Ready to build your own solution

**Time Required**: ~10 minutes

---

## Prerequisites

- C++17 compiler

- CMake 3.15+

- Basic C++ knowledge

---

## Step 1: Install Tools (2 minutes)

**Linux**:
```bash
sudo apt-get install build-essential cmake
```

**macOS**:
```bash
xcode-select --install
brew install cmake
```

**Windows**:

- Install Visual Studio 2019+ with C++ tools

---

## Step 2: Build Library (3 minutes)

```bash
# Clone
git clone https://github.com/username/project.git
cd project

# Build
mkdir build && cd build
cmake ..
cmake --build .

# Test
ctest

# Install
sudo cmake --install .
```

---

## Step 3: Your First Program (3 minutes)

Create `first.cpp`:

```cpp
#include <project/project.hpp>
#include <iostream>

int main() {
    try {
        project::Client client;
        auto result = client.process("Hello, World!");
        std::cout << "Result: " << result << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    return 0;
}
```

**Compile and run**:
```bash
g++ -std=c++17 -o first first.cpp -lproject
./first
```

**Expected Output**:
```
Result: Processed: Hello, World!
```

✅ **Success!** You've run your first program.

---

## Step 4: Use Modern C++ (2 minutes)

Update to use modern features:

```cpp
#include <project/project.hpp>
#include <iostream>
#include <vector>
#include <algorithm>

int main() {
    project::Client client;

    std::vector<std::string> inputs{"Hello", "World", "C++"};

    // Use ranges and algorithms
    std::ranges::for_each(inputs, [&](const auto& input) {
        if (auto result = client.process(input); result) {
            std::cout << *result << std::endl;
        }
    });

    return 0;
}
```

---

## Next Steps

### Explore Examples

- **[Modern C++](examples/modern_cpp.cpp)**: Latest features

- **[Async](examples/async.cpp)**: Concurrent processing

- **[Templates](examples/templates.cpp)**: Generic programming

### Read Documentation

- **[API Reference](https://username.github.io/project/api/)**: Class documentation

- **[User Guide](USER_GUIDE.md)**: Comprehensive guide

---

## Need Help?

- **Errors**: See [Troubleshooting](TROUBLESHOOTING.md)

- **Questions**: Open an [issue](https://github.com/username/project/issues)

**Congratulations!** You're ready to use [Project Name].
```

## Phase 5: FAQ and Troubleshooting

### FAQ.md Template

```markdown
# Frequently Asked Questions

---

## General Questions

### What is [Project Name]?

[Explanation]

### Which C++ standard should I use?

C++17 minimum. C++20 recommended for best features.

### Is this thread-safe?

[Thread safety details]

---

## Build & Installation

### How do I use this with CMake?

```cmake
find_package(Project REQUIRED)
target_link_libraries(myapp PRIVATE Project::Project)
```

### Can I use this as header-only?

[Header-only instructions if applicable]

---

## Usage Questions

### How do I handle errors?

Use exceptions:
```cpp
try {
    auto result = client.process(input);
} catch (const project::Exception& e) {
    std::cerr << "Error: " << e.what() << std::endl;
}
```

---

[Back to README](../README.md)
```

~~~
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
