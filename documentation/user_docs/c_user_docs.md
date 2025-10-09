# C User Documentation

## Objective
Create clear, comprehensive user-facing documentation that enables users of all skill levels to quickly understand, install, configure, and effectively use the C software using Makefile/build systems for embedded and system programming.

## Output Directory Structure

All documentation outputs should be saved in organized directories:

```
documentation/
└── user_docs/
    ├── generated_docs/
    ├── templates/
    ├── assets/
    └── exports/
```

**Directory Setup**:
- Create `documentation/` directory in repository root if it doesn't exist
- Create `documentation/user_docs/` subdirectory for this documentation phase
- All documentation files, templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:
- `generated_docs/` - Generated documentation files (HTML, MD, PDF)
- `templates/` - Documentation templates and examples
- `assets/` - Images, diagrams, supplementary files
- `exports/` - Published documentation, release artifacts

## Implementation Checklist

### README Structure
- [ ] Compelling project overview and value proposition
- [ ] Key features highlighted
- [ ] Installation instructions complete and tested
- [ ] Quick start guide for immediate success
- [ ] Usage examples for common scenarios
- [ ] Links to detailed documentation

### Installation Guides
- [ ] Prerequisites clearly listed (compiler, build tools)
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
# C User Documentation Request

Please create comprehensive user documentation for this C project following this protocol:

## Phase 1: Audience Analysis & Documentation Planning

1. **Identify Target Audience**
   - Primary users: [embedded developers/systems programmers/library users/etc.]
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
   - [ ] API.md for function reference

## Phase 2: README.md - Professional Project Overview

Create a comprehensive README.md that serves as the front door to your project:

### README.md Template

```markdown
# [Project Name]

[![C Standard](https://img.shields.io/badge/C-C99%2B-blue)](https://en.wikipedia.org/wiki/C99)
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
- **[Feature 3]**: Emphasize ease of use or performance benefits
- **[Feature 4]**: Note portability or compatibility features

---

## 🚀 Quick Start

Get started in less than 5 minutes:

### Installation

**Linux/macOS**:
```bash
# Clone repository
git clone https://github.com/username/project.git
cd project

# Build
make

# Install
sudo make install
```

**Windows (MinGW)**:
```cmd
REM Clone repository
git clone https://github.com/username/project.git
cd project

REM Build
mingw32-make

REM Install
mingw32-make install
```

### Basic Usage

**As a library**:
```c
#include <project.h>

int main(void) {
    // Initialize library
    project_t *ctx = project_init();
    if (!ctx) {
        fprintf(stderr, "Failed to initialize\n");
        return 1;
    }

    // Process data
    const char *input = "example input";
    char *result = project_process(ctx, input);
    if (result) {
        printf("Result: %s\n", result);
        free(result);
    }

    // Cleanup
    project_cleanup(ctx);
    return 0;
}
```

**Compile and link**:
```bash
gcc -o myapp main.c -lproject
./myapp
# Output: Result: [expected output]
```

**That's it!** You're ready to go. See [Usage Examples](#usage-examples) for more.

---

## 📦 Installation

### Prerequisites

Before installing, ensure you have:
- C compiler (GCC 4.9+, Clang 3.5+, or MSVC 2015+)
- Make (GNU Make 3.81+ or compatible)
- [Optional] CMake 3.10+ for alternative build
- [Optional] pkg-config for dependency management

### Platform-Specific Prerequisites

**Linux**:
```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# Fedora/RHEL
sudo dnf groupinstall "Development Tools"

# Arch Linux
sudo pacman -S base-devel
```

**macOS**:
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Or via Homebrew
brew install gcc make
```

**Windows**:
- Install MinGW-w64 or MSYS2
- Or use Visual Studio 2015+ with C/C++ tools

### Installation Options

#### Option 1: System Installation

```bash
# Clone repository
git clone https://github.com/username/project.git
cd project

# Build
make

# Run tests
make test

# Install (requires sudo on Linux/macOS)
sudo make install

# Or install to custom prefix
make install PREFIX=$HOME/.local
```

#### Option 2: CMake Build

```bash
# Clone repository
git clone https://github.com/username/project.git
cd project
mkdir build && cd build

# Configure
cmake ..

# Build
cmake --build .

# Install
sudo cmake --install .
```

#### Option 3: Static Library

```bash
# Build static library
make static

# Link in your project
gcc -o myapp main.c -L. -lproject-static
```

#### Option 4: Header-Only Integration

For single-header libraries:
```bash
# Just copy header to your project
cp include/project.h /path/to/your/project/
```

### Verify Installation

```bash
# Check library is installed
pkg-config --modversion project

# Check header files
ls /usr/local/include/project.h

# Test compilation
gcc -o test test.c -lproject
```

**Troubleshooting**: See [Installation Issues](#installation-issues) if you encounter problems.

---

## 💡 Usage Examples

### Example 1: Basic Usage

[Description of what this example demonstrates]

```c
#include <stdio.h>
#include <stdlib.h>
#include <project.h>

int main(void) {
    /* Initialize with default options */
    project_options_t opts = {
        .option1 = "value",
        .option2 = 42,
        .debug = 0
    };

    project_t *ctx = project_init_with_options(&opts);
    if (!ctx) {
        fprintf(stderr, "Initialization failed\n");
        return EXIT_FAILURE;
    }

    /* Process data */
    const char *input = "input data";
    char *result = project_process(ctx, input);
    if (!result) {
        fprintf(stderr, "Processing failed\n");
        project_cleanup(ctx);
        return EXIT_FAILURE;
    }

    printf("Result: %s\n", result);

    /* Cleanup */
    free(result);
    project_cleanup(ctx);

    return EXIT_SUCCESS;
}
```

**Compile**:
```bash
gcc -o basic basic.c -lproject
./basic
```

**Output**:
```
Result: processed_data
```

### Example 2: Error Handling

[Description of robust error handling]

```c
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <project.h>

int main(void) {
    project_t *ctx = NULL;
    char *result = NULL;
    int status = EXIT_SUCCESS;

    /* Initialize */
    ctx = project_init();
    if (!ctx) {
        fprintf(stderr, "Error: %s\n", project_strerror(errno));
        return EXIT_FAILURE;
    }

    /* Process with error checking */
    result = project_process(ctx, "input");
    if (!result) {
        int err = project_get_error(ctx);
        fprintf(stderr, "Processing failed: %s\n", project_error_string(err));
        status = EXIT_FAILURE;
        goto cleanup;
    }

    printf("Success: %s\n", result);

cleanup:
    free(result);
    project_cleanup(ctx);
    return status;
}
```

### Example 3: Advanced Usage with Callbacks

[Description of callback pattern]

```c
#include <stdio.h>
#include <project.h>

/* Callback function */
void progress_callback(int percent, void *user_data) {
    printf("Progress: %d%%\n", percent);
}

int main(void) {
    project_t *ctx = project_init();
    if (!ctx) return EXIT_FAILURE;

    /* Set callback */
    project_set_callback(ctx, progress_callback, NULL);

    /* Process with progress updates */
    char *result = project_process_long_operation(ctx, "data");
    if (result) {
        printf("Result: %s\n", result);
        free(result);
    }

    project_cleanup(ctx);
    return EXIT_SUCCESS;
}
```

### Example 4: Multi-threaded Usage

[Description of thread safety]

```c
#include <stdio.h>
#include <pthread.h>
#include <project.h>

#define NUM_THREADS 4

void *worker_thread(void *arg) {
    int id = *(int *)arg;

    /* Each thread gets own context */
    project_t *ctx = project_init();
    if (!ctx) return NULL;

    char input[32];
    snprintf(input, sizeof(input), "thread-%d", id);

    char *result = project_process(ctx, input);
    if (result) {
        printf("Thread %d: %s\n", id, result);
        free(result);
    }

    project_cleanup(ctx);
    return NULL;
}

int main(void) {
    pthread_t threads[NUM_THREADS];
    int thread_ids[NUM_THREADS];

    /* Create threads */
    for (int i = 0; i < NUM_THREADS; i++) {
        thread_ids[i] = i;
        pthread_create(&threads[i], NULL, worker_thread, &thread_ids[i]);
    }

    /* Wait for completion */
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    return EXIT_SUCCESS;
}
```

**Compile with pthread**:
```bash
gcc -o threaded threaded.c -lproject -lpthread
```

**More Examples**: See [examples/](examples/) directory for additional use cases.

---

## 🔧 Configuration

### Compile-Time Configuration

Edit `config.h` before building:

```c
/* config.h */
#define PROJECT_BUFFER_SIZE 4096
#define PROJECT_MAX_CONNECTIONS 100
#define PROJECT_ENABLE_DEBUG 0
#define PROJECT_ENABLE_LOGGING 1
```

### Runtime Configuration

```c
#include <project.h>

int main(void) {
    project_config_t config = {
        .buffer_size = 8192,
        .timeout = 30,
        .enable_debug = 1
    };

    project_t *ctx = project_init_with_config(&config);
    /* Use context... */
    project_cleanup(ctx);
    return 0;
}
```

### Environment Variables

```bash
# Set via environment variables
export PROJECT_LOG_LEVEL=DEBUG
export PROJECT_CONFIG_PATH=/etc/project.conf
```

```c
/* Reads from environment automatically */
project_t *ctx = project_init();
```

---

## 📚 Documentation

- **[User Guide](docs/USER_GUIDE.md)**: Comprehensive usage documentation
- **[API Reference](docs/API.md)**: Complete function reference
- **[Examples](examples/)**: More code examples
- **[FAQ](docs/FAQ.md)**: Frequently asked questions
- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Common issues and solutions

---

## ❓ FAQ

### How do I [common task]?

[Clear, concise answer with code example if relevant]

### Is this thread-safe?

[Thread safety information and examples]

### Can I use this in embedded systems?

[Embedded system compatibility and considerations]

### How do I contribute?

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

**More Questions?** Check the full [FAQ](docs/FAQ.md) or [open an issue](https://github.com/username/project/issues).

---

## 🐛 Troubleshooting

### Compilation Issues

**Problem**: `undefined reference to 'project_init'`

**Solution**: Link against the library:
```bash
gcc -o myapp main.c -lproject
# Or specify library path
gcc -o myapp main.c -L/usr/local/lib -lproject
```

### Runtime Issues

**Error**: `error while loading shared libraries: libproject.so.1: cannot open shared object file`

**Cause**: Shared library not in library path

**Solution**:
```bash
# Add to LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Or run ldconfig (as root)
sudo ldconfig
```

**More Issues?** See full [Troubleshooting Guide](docs/TROUBLESHOOTING.md).

---

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
make test

# Run with valgrind for memory checks
make valgrind

# Run specific test
./tests/test_basic

# Generate coverage report
make coverage
```

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Quick start for contributors:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Check with valgrind (`make valgrind`)
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
- **Mailing List**: [project@lists.example.com](mailto:project@lists.example.com)
- **Documentation**: [https://project-docs.com](https://project-docs.com)

---

## 🗺️ Roadmap

- [ ] v[X+1].0: [Planned major feature]
- [ ] v[X].Y: [Planned minor feature]
- [ ] [Future feature/improvement]

See [ROADMAP.md](ROADMAP.md) for detailed plans.

---

**Made with ❤️ by [Your Name/Organization]**
```

## Phase 3: Installation Guide

Create detailed installation instructions:

### INSTALL.md Template

```markdown
# Installation Guide

Complete installation instructions for [Project Name].

---

## System Requirements

### Minimum Requirements
- **OS**: Linux (kernel 3.x+), macOS 10.10+, Windows 7+
- **Compiler**: GCC 4.9+, Clang 3.5+, or MSVC 2015+
- **Build Tools**: GNU Make 3.81+ or CMake 3.10+
- **RAM**: 512MB minimum
- **Disk Space**: 50MB

### Recommended Requirements
- GCC 9+ or Clang 11+ for best optimization
- 2GB RAM for development
- pkg-config for dependency management

---

## Installation Methods

### Method 1: Standard Installation (Linux/macOS)

```bash
# Clone repository
git clone https://github.com/username/project.git
cd project

# Build
make

# Run tests
make test

# Install (requires sudo)
sudo make install

# Or install to user directory
make install PREFIX=$HOME/.local
```

### Method 2: CMake Build

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

### Method 3: Windows (MinGW)

```cmd
REM Clone repository
git clone https://github.com/username/project.git
cd project

REM Build
mingw32-make

REM Run tests
mingw32-make test

REM Install
mingw32-make install
```

### Method 4: Windows (Visual Studio)

```cmd
REM Open project in Visual Studio
REM Or use CMake:
mkdir build
cd build
cmake .. -G "Visual Studio 16 2019"
cmake --build . --config Release
```

---

## Platform-Specific Instructions

### Linux

#### Ubuntu/Debian
```bash
# Install build tools
sudo apt-get update
sudo apt-get install build-essential git

# Install dependencies (if any)
sudo apt-get install libdependency-dev

# Clone and build
git clone https://github.com/username/project.git
cd project
make
sudo make install
```

#### Fedora/RHEL
```bash
# Install build tools
sudo dnf groupinstall "Development Tools"
sudo dnf install git

# Install dependencies
sudo dnf install dependency-devel

# Clone and build
git clone https://github.com/username/project.git
cd project
make
sudo make install
```

### macOS

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Or install GCC via Homebrew
brew install gcc make

# Clone and build
git clone https://github.com/username/project.git
cd project
make
sudo make install
```

### Windows

**Using MinGW**:
```cmd
REM Install MinGW from mingw-w64.org
REM Add MinGW to PATH

REM Clone and build
git clone https://github.com/username/project.git
cd project
mingw32-make
```

**Using MSYS2**:
```bash
# Install MSYS2 from msys2.org
# In MSYS2 terminal:
pacman -S gcc make git

# Clone and build
git clone https://github.com/username/project.git
cd project
make
make install
```

---

## Build Options

### Makefile Options

```bash
# Build with debug symbols
make DEBUG=1

# Build static library
make static

# Build shared library
make shared

# Build with custom prefix
make PREFIX=/opt/project

# Cross-compile
make CC=arm-linux-gnueabihf-gcc
```

### CMake Options

```bash
# Build type
cmake .. -DCMAKE_BUILD_TYPE=Release  # or Debug

# Install prefix
cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local

# Build static library
cmake .. -DBUILD_SHARED_LIBS=OFF

# Enable/disable features
cmake .. -DENABLE_FEATURE=ON
```

---

## Verification

### Quick Verification

```bash
# Check library is installed
ls /usr/local/lib/libproject.*

# Check headers
ls /usr/local/include/project.h

# Test compilation
cat > test.c << 'EOF'
#include <project.h>
#include <stdio.h>

int main(void) {
    printf("Library version: %s\n", PROJECT_VERSION);
    return 0;
}
EOF

gcc -o test test.c -lproject
./test
```

### Full Verification

```bash
# Clone and test
git clone https://github.com/username/project.git
cd project

# Run test suite
make test

# Run with valgrind
make valgrind

# Check for memory leaks
valgrind --leak-check=full ./tests/test_suite
```

---

## Linking in Your Project

### Using pkg-config

```bash
# Check pkg-config can find library
pkg-config --cflags --libs project

# Compile with pkg-config
gcc -o myapp main.c $(pkg-config --cflags --libs project)
```

### Manual Linking

```bash
# Compile and link
gcc -o myapp main.c -I/usr/local/include -L/usr/local/lib -lproject

# With rpath (Linux)
gcc -o myapp main.c -lproject -Wl,-rpath,/usr/local/lib
```

### CMake Integration

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.10)
project(MyApp)

find_package(Project REQUIRED)

add_executable(myapp main.c)
target_link_libraries(myapp Project::Project)
```

---

## Troubleshooting

### Common Build Errors

**Error**: `make: command not found`
- **Cause**: Make not installed
- **Fix**: Install build tools (see platform instructions above)

**Error**: `gcc: command not found`
- **Cause**: Compiler not installed
- **Fix**: Install GCC or Clang

**Error**: `undefined reference to 'pthread_create'`
- **Cause**: Missing pthread library
- **Fix**: Add `-lpthread` to linker flags

**Error**: `fatal error: project.h: No such file or directory`
- **Cause**: Header not found
- **Fix**: Add include path: `-I/path/to/include`

### Getting Help

If installation fails:
1. Check [GitHub Issues](https://github.com/username/project/issues)
2. Review [Troubleshooting Guide](TROUBLESHOOTING.md)
3. Open a new issue with:
   - Your OS and version
   - Compiler version (`gcc --version`)
   - Full error message
   - Output of `make V=1` (verbose)

---

## Next Steps

After successful installation:
1. Review the [Quick Start Guide](README.md#quick-start)
2. Try the [examples/](examples/) directory
3. Read the [API Reference](docs/API.md)
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
- ✅ Created your first C program using the library
- ✅ Understanding of core concepts
- ✅ Ready to build your own solution

**Time Required**: ~10 minutes

---

## Prerequisites

- C compiler (GCC or Clang)
- Make
- Basic C knowledge

---

## Step 1: Install Build Tools (2 minutes)

**Linux**:
```bash
sudo apt-get install build-essential  # Ubuntu/Debian
# or
sudo dnf groupinstall "Development Tools"  # Fedora
```

**macOS**:
```bash
xcode-select --install
```

**Windows**:
- Install MinGW or MSYS2

---

## Step 2: Build Library (3 minutes)

```bash
# Clone repository
git clone https://github.com/username/project.git
cd project

# Build
make

# Run tests
make test

# Install
sudo make install
```

---

## Step 3: Your First Program (3 minutes)

Create `first.c`:

```c
#include <stdio.h>
#include <stdlib.h>
#include <project.h>

int main(void) {
    /* Initialize */
    project_t *ctx = project_init();
    if (!ctx) {
        fprintf(stderr, "Failed to initialize\n");
        return EXIT_FAILURE;
    }

    /* Process data */
    char *result = project_process(ctx, "Hello, World!");
    if (result) {
        printf("Result: %s\n", result);
        free(result);
    }

    /* Cleanup */
    project_cleanup(ctx);
    return EXIT_SUCCESS;
}
```

Compile and run:
```bash
gcc -o first first.c -lproject
./first
```

**Expected Output**:
```
Result: Processed: Hello, World!
```

✅ **Success!** You've run your first program.

---

## Step 4: Next Steps

### Explore More Examples
- **[Error Handling](examples/error_handling.c)**: Robust error management
- **[Callbacks](examples/callbacks.c)**: Using callback functions
- **[Threading](examples/threading.c)**: Multi-threaded usage

### Read Documentation
- **[API Reference](docs/API.md)**: Function documentation
- **[User Guide](USER_GUIDE.md)**: Comprehensive guide

---

## Need Help?

- **Error Messages**: See [Troubleshooting](TROUBLESHOOTING.md)
- **Questions**: Open an [issue](https://github.com/username/project/issues)
- **Examples**: Check [examples/](examples/) directory

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

### Is this thread-safe?

[Thread safety details]

### Can I use this in embedded systems?

[Embedded compatibility]

---

## Build & Installation

### Which compiler do I need?

GCC 4.9+, Clang 3.5+, or MSVC 2015+ are supported.

### How do I cross-compile?

```bash
make CC=arm-linux-gnueabihf-gcc
```

---

## Usage Questions

### How do I handle errors?

Always check return values:
```c
result = project_process(ctx, input);
if (!result) {
    fprintf(stderr, "Error: %s\n", project_get_error_string(ctx));
    return EXIT_FAILURE;
}
```

---

[Back to README](../README.md)
```

---

~~~

## Output Format Specifications

The user documentation should:
- Be clear and accessible to C developers
- Include complete, compilable examples
- Show proper memory management and error handling
- Cover Makefile and CMake build systems
- Provide platform-specific instructions
- Include troubleshooting for common compiler/linker issues
- Emphasize portability and embedded use cases
- Link to API documentation
