# VS Code Configuration for Google Test Projects

This directory contains ready-to-use VS Code configuration files for C++ projects using Google Test. Copy these files to your project's `.vscode/` directory to enable seamless test development, building, and debugging.

## Quick Setup

```bash
# From your C++ project root
mkdir -p .vscode
cp templates/tests_generation/vscode_config/*.json .vscode/
```

Then reload VS Code: `Ctrl+Shift+P` → "Developer: Reload Window"

---

## Configuration Files

### 1. tasks.json - Build and Test Tasks

**Purpose**: Defines VS Code tasks for building and running tests.

**Available Tasks**:

- **CMake: Configure** - Configures CMake with Ninja generator

- **CMake: Build Tests** (Default Build: `Ctrl+Shift+B`) - Builds all test executables

- **Run All Tests** (Default Test Task) - Runs all tests with CTest

- **Run Tests (Verbose)** - Runs tests with detailed output

- **Run Single Test** - Runs specific test by name pattern

- **Generate Code Coverage** - Builds coverage report

**Usage**:
```
Ctrl+Shift+B         → Build tests
Ctrl+Shift+P         → "Tasks: Run Test Task" → Run All Tests
Ctrl+Shift+P         → "Tasks: Run Task" → Select specific task
```

**Customization**:

- Change build type: Modify `CMAKE_BUILD_TYPE` (Debug/Release/RelWithDebInfo)

- Change generator: Replace `Ninja` with `Unix Makefiles` or `Visual Studio 17 2022`

- Adjust parallel jobs: Change `-j8` to match your CPU cores

---

### 2. launch.json - Debugging Configurations

**Purpose**: Enables debugging Google Test executables with breakpoints and step-through execution.

**Available Configurations**:

- **Debug Current Test Binary** - Debug specific test executable with GTest filter

- **Debug All Tests** - Debug all tests at once

**Usage**:

1. Open test file

2. Set breakpoint (click in gutter)

3. Press `F5` → Select "Debug Current Test Binary"

4. Enter test binary name (e.g., "calculator")

5. Enter GTest filter (e.g., "CalculatorTest.Add*" or "*")

**Keyboard Shortcuts**:
```
F5              → Start debugging
F10             → Step over
F11             → Step into
Shift+F11       → Step out
Ctrl+Shift+F5   → Restart debugging
Shift+F5        → Stop debugging
```

**Platform Notes**:

- **Linux/Mac**: Uses `gdb` (change to `lldb` for LLVM)

- **Windows**: Change `"MIMode": "gdb"` to `"MIMode": "lldb"` or configure MSVC debugger

---

### 3. settings.json - CMake Tools and IntelliSense

**Purpose**: Configures CMake Tools extension, C++ IntelliSense, and editor behavior.

**Key Settings**:

#### CMake Tools
```json
"cmake.configureOnOpen": true          // Auto-configure on project open
"cmake.generator": "Ninja"             // Use Ninja build system
"cmake.buildDirectory": "${workspaceFolder}/build"
```

#### C++ IntelliSense
```json
"C_Cpp.default.configurationProvider": "ms-vscode.cmake-tools"
"C_Cpp.default.compileCommands": "${workspaceFolder}/build/compile_commands.json"
"C_Cpp.default.cppStandard": "c++17"
```

#### Test Explorer Integration
```json
"testMate.cpp.test.advancedExecutables": [
    {"pattern": "build/test_*"}         // Auto-discover test executables
]
```

#### GitHub Copilot
```json
"github.copilot.enable": {
    "*": true,
    "cpp": true
}
```

**Customization**:

- Change C++ standard: Modify `"c++17"` to `"c++11"`, `"c++14"`, `"c++20"`, etc.

- Disable auto-configure: Set `"cmake.configureOnOpen": false`

- Change formatter: Replace `"xaver.clang-format"` with alternative

---

### 4. c_cpp_properties.json - Platform-Specific IntelliSense

**Purpose**: Configures C++ IntelliSense for different platforms with Google Test headers.

**Configurations Included**:

- **Linux**: GCC with `linux-gcc-x64` IntelliSense mode

- **Mac**: Clang with `macos-clang-x64` IntelliSense mode

- **Win32**: MSVC with `windows-msvc-x64` IntelliSense mode

**Key Paths**:
```json
"includePath": [
    "${workspaceFolder}/**",
    "${workspaceFolder}/build/_deps/googletest-src/googletest/include",
    "${workspaceFolder}/build/_deps/googletest-src/googlemock/include"
]
```

**Why This Matters**:

- Prevents red squiggly lines for `#include <gtest/gtest.h>`

- Enables auto-completion for Google Test macros (TEST, EXPECT_EQ, etc.)

- Provides hover documentation for Google Test APIs

**Customization**:

- Update compiler path if not in standard location

- Add additional include directories for your project

- Change C++ standard to match your project

---

## Required VS Code Extensions

Install these extensions for full functionality:

### Essential
- **CMake Tools** (`twxs.cmake`) - CMake integration

- **C/C++** (`ms-vscode.cpptools`) - C++ language support

- **C/C++ Extension Pack** (`ms-vscode.cpptools-extension-pack`) - Full C++ toolkit

### Recommended
- **Test Explorer UI** (`hbenl.vscode-test-explorer`) - Graphical test runner

- **C++ TestMate** (`matepek.vscode-catch2-test-adapter`) - Google Test integration

- **GitHub Copilot** (`GitHub.copilot`) - AI code generation

### Optional
- **clangd** (`llvm-vs-code-extensions.vscode-clangd`) - Alternative IntelliSense

- **CodeLLDB** (`vadimcn.vscode-lldb`) - Advanced LLVM debugger

- **CMake** (`twxs.cmake`) - CMake language support

Install all at once:
```bash
code --install-extension twxs.cmake
code --install-extension ms-vscode.cpptools
code --install-extension ms-vscode.cpptools-extension-pack
code --install-extension hbenl.vscode-test-explorer
code --install-extension matepek.vscode-catch2-test-adapter
code --install-extension GitHub.copilot
```

---

## Troubleshooting

### Issue: CMake doesn't auto-configure

**Solution**:

1. Check bottom status bar for CMake kit selection

2. Press `Ctrl+Shift+P` → "CMake: Select a Kit"

3. Choose your compiler (GCC, Clang, or MSVC)

4. Press `Ctrl+Shift+P` → "CMake: Configure"

### Issue: IntelliSense shows errors for Google Test headers

**Solution**:

1. Ensure CMake has run at least once: `cmake -B build`

2. Check `build/_deps/googletest-src/` exists

3. Reload window: `Ctrl+Shift+P` → "Developer: Reload Window"

4. Verify `c_cpp_properties.json` paths match your system

### Issue: Tests don't appear in Test Explorer

**Solution**:

1. Install "C++ TestMate" extension

2. Build tests first: `Ctrl+Shift+B`

3. Check `settings.json` has correct test pattern:
   ```json
   "testMate.cpp.test.advancedExecutables": [
       {"pattern": "build/test_*"}
   ]
   ```
4. Reload window

### Issue: Debugger doesn't start

**Solution**:

1. Verify test binary exists: `ls build/test_*`

2. Check debugger is installed:

   - **Linux**: `sudo apt-get install gdb`

   - **Mac**: `xcode-select --install` (includes lldb)

   - **Windows**: Install Visual Studio Build Tools

3. Update `launch.json` with correct `MIMode` for your platform

### Issue: Build fails with "Ninja not found"

**Solution**:

1. Install Ninja:

   - **Linux**: `sudo apt-get install ninja-build`

   - **Mac**: `brew install ninja`

   - **Windows**: `choco install ninja`

2. Or change generator in `tasks.json`:

   - Replace `"Ninja"` with `"Unix Makefiles"` (Linux/Mac)

   - Replace with `"Visual Studio 17 2022"` (Windows)

---

## Integration with Google Test Workflow

These configurations are designed to work with the Google Test + GitHub Copilot workflow:

1. **Clone repo** → Open in VS Code

2. **Copy `.vscode/` configs** → Auto-configure CMake

3. **Generate tests with Copilot** → Use prompt templates

4. **Build tests** → `Ctrl+Shift+B`

5. **Run tests** → Command Palette → "Tasks: Run Test Task"

6. **Debug failures** → Set breakpoints → `F5`

For complete workflow documentation, see:

- [templates/tests_generation/GOOGLE_TEST_VSCODE_WORKFLOW.md](../GOOGLE_TEST_VSCODE_WORKFLOW.md)

- [templates/tests_generation/unit_tests/COPILOT_QUICK_REFERENCE.md](../unit_tests/COPILOT_QUICK_REFERENCE.md)

---

## Customization Guide

### Change Build Type
Edit `tasks.json`:
```json
"-DCMAKE_BUILD_TYPE=Release"  // Instead of Debug
```

### Add Custom CMake Options
Edit `settings.json`:
```json
"cmake.configureSettings": {
    "CUSTOM_OPTION": "ON",
    "ANOTHER_OPTION": "value"
}
```

### Use Different Compiler
1. Press `Ctrl+Shift+P` → "CMake: Edit User-Local CMake Kits"

2. Add custom kit:
```json
{
    "name": "Custom GCC",
    "compilers": {
        "C": "/usr/bin/gcc-11",
        "CXX": "/usr/bin/g++-11"
    }
}
```

### Multi-Configuration Projects
For projects with multiple test suites:
```json
// tasks.json - Add separate tasks per suite
{
    "label": "Run Unit Tests Only",
    "command": "ctest",
    "args": ["--test-dir", "${workspaceFolder}/build", "-R", "unit"]
}
```

---

## Platform-Specific Notes

### Linux
- Default debugger: GDB

- Compiler: GCC or Clang

- Package manager: apt/yum/dnf

### macOS
- Default debugger: LLDB (change in `launch.json`)

- Compiler: Apple Clang

- Package manager: Homebrew

### Windows
- Default debugger: MSVC (requires configuration update)

- Compiler: MSVC 2022

- Package manager: Chocolatey or winget

- **Note**: Use PowerShell or CMD, not Git Bash, for tasks

For Windows MSVC debugging, update `launch.json`:
```json
{
    "name": "Debug Test (Windows MSVC)",
    "type": "cppvsdbg",                    // Instead of cppdbg
    "request": "launch",
    "program": "${workspaceFolder}/build/Debug/test_${input:testBinary}.exe",
    "preLaunchTask": "CMake: Build Tests"
}
```

---

## Additional Resources

- [CMake Tools Documentation](https://vector-of-bool.github.io/docs/vscode-cmake-tools/)

- [VS Code C++ Documentation](https://code.visualstudio.com/docs/languages/cpp)

- [Google Test Primer](https://google.github.io/googletest/primer.html)

- [Debugging in VS Code](https://code.visualstudio.com/docs/editor/debugging)

---

## License

These configuration files are part of the AI Templates repository and can be freely used in any project.
