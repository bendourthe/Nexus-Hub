---
name: create-user-documentation
description: Generate comprehensive user-facing documentation including README files, installation guides, tutorials, usage examples, and troubleshooting guides
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language (Python, JavaScript, Java, C#, Go, C, C++)
category: Documentation
priority: MEDIUM
tags: [documentation, readme, user-guide, tutorial, installation, troubleshooting, getting-started]
template_sources:

  - documentation/user_docs/python_user_docs.md
  - documentation/user_docs/javascript_user_docs.md
  - documentation/user_docs/java_user_docs.md
  - documentation/user_docs/csharp_user_docs.md
  - documentation/user_docs/go_user_docs.md
  - documentation/user_docs/c_user_docs.md
  - documentation/user_docs/cpp_user_docs.md
---

# Create User Documentation

Generate clear, comprehensive user-facing documentation that enables users to quickly understand, install, configure, and effectively use your software with guides, examples, and troubleshooting help.

## When to Use This Skill

Use this skill when you need to:
- Create professional README files for repositories
- Write installation and setup guides
- Build quick start tutorials
- Generate usage examples and code samples
- Create FAQ sections
- Write troubleshooting guides
- Document configuration options
- Prepare software for public release
- Onboard new users or team members
- Improve software adoption and usability

## What This Skill Does

This skill generates comprehensive user documentation:

### For All Languages
1. **README Files**
   - Project overview and value proposition
   - Feature highlights
   - Installation instructions
   - Quick start examples
   - Usage documentation
   - Contributing guidelines
   - License information

2. **Installation Guides**
   - Prerequisites and requirements
   - Platform-specific instructions
   - Dependency installation
   - Configuration steps
   - Verification procedures
   - Common installation issues

3. **Quick Start Tutorials**
   - First-time setup
   - Basic usage examples
   - Common workflows
   - Expected outcomes
   - Next steps and resources

4. **Usage Documentation**
   - Feature documentation
   - Code examples and snippets
   - Configuration options
   - Command-line interface
   - API usage patterns
   - Best practices

5. **FAQ and Troubleshooting**
   - Common questions
   - Known issues and workarounds
   - Error messages and solutions
   - Performance optimization
   - Debugging tips

6. **Reference Documentation**
   - Configuration file reference
   - Environment variables
   - Command-line options
   - Version compatibility
   - Migration guides

### Language-Specific Features

#### Python
- **Package Installation**: pip, conda, poetry
- **Virtual Environments**: venv, virtualenv, conda
- **Dependencies**: requirements.txt, setup.py, pyproject.toml
- **Examples**:
  ```markdown
  ## Installation

  ### Using pip
  ```bash
  pip install mypackage
  ```

  ### From source
  ```bash
  git clone https://github.com/user/mypackage.git
  cd mypackage
  python -m venv .venv
  source .venv/bin/activate  # On Windows: .venv\Scripts\activate
  pip install -e .[dev]
  ```

  ## Quick Start

  ```python
  from mypackage import MyClass

  # Initialize with configuration
  instance = MyClass(config={'key': 'value'})

  # Process data
  result = instance.process(data)
  print(f"Processed {len(result)} items")
  ```

  ## Configuration

  Create a `config.yaml` file:

  ```yaml
  database:
    host: localhost
    port: 5432
  logging:
    level: INFO
  ```
  ```

#### JavaScript/TypeScript
- **Package Installation**: npm, yarn, pnpm
- **Dependencies**: package.json
- **Module Systems**: CommonJS, ES modules
- **Examples**:
  ```markdown
  ## Installation

  ### Using npm
  ```bash
  npm install mypackage
  ```

  ### Using yarn
  ```bash
  yarn add mypackage
  ```

  ## Quick Start

  ### CommonJS
  ```javascript
  const { MyClass } = require('mypackage');

  const instance = new MyClass({ key: 'value' });
  const result = instance.process(data);
  console.log(`Processed ${result.length} items`);
  ```

  ### ES Modules
  ```javascript
  import { MyClass } from 'mypackage';

  const instance = new MyClass({ key: 'value' });
  const result = instance.process(data);
  console.log(`Processed ${result.length} items`);
  ```

  ## TypeScript Support

  TypeScript definitions are included:

  ```typescript
  import { MyClass, Config } from 'mypackage';

  const config: Config = { key: 'value' };
  const instance = new MyClass(config);
  ```
  ```

#### Java
- **Build Tools**: Maven, Gradle
- **Dependencies**: pom.xml, build.gradle
- **Examples**:
  ```markdown
  ## Installation

  ### Maven
  Add to your `pom.xml`:

  ```xml
  <dependency>
      <groupId>com.example</groupId>
      <artifactId>mypackage</artifactId>
      <version>1.0.0</version>
  </dependency>
  ```

  ### Gradle
  Add to your `build.gradle`:

  ```gradle
  dependencies {
      implementation 'com.example:mypackage:1.0.0'
  }
  ```

  ## Quick Start

  ```java
  import com.example.mypackage.MyClass;

  public class Example {
      public static void main(String[] args) {
          MyClass instance = new MyClass();
          instance.configure("key", "value");

          List<String> result = instance.process(data);
          System.out.println("Processed " + result.size() + " items");
      }
  }
  ```

  ## Configuration

  Create `application.properties`:

  ```properties
  mypackage.database.url=jdbc:postgresql://localhost:5432/mydb
  mypackage.logging.level=INFO
  ```
  ```

#### C#
- **Package Manager**: NuGet
- **Project Files**: .csproj
- **Frameworks**: .NET Framework, .NET Core, .NET 5+
- **Examples**:
  ```markdown
  ## Installation

  ### Using NuGet Package Manager
  ```bash
  dotnet add package MyPackage
  ```

  ### Using Package Manager Console
  ```powershell
  Install-Package MyPackage
  ```

  ## Quick Start

  ```csharp
  using MyPackage;

  class Program
  {
      static void Main(string[] args)
      {
          var instance = new MyClass();
          instance.Configure(new Config { Key = "value" });

          var result = instance.Process(data);
          Console.WriteLine($"Processed {result.Count} items");
      }
  }
  ```

  ## Configuration

  Add to `appsettings.json`:

  ```json
  {
    "MyPackage": {
      "Database": {
        "ConnectionString": "Server=localhost;Database=mydb"
      },
      "Logging": {
        "Level": "Information"
      }
    }
  }
  ```
  ```

#### Go
- **Package Manager**: go modules
- **Dependencies**: go.mod
- **Examples**:
  ```markdown
  ## Installation

  ```bash
  go get github.com/user/mypackage
  ```

  Or add to your `go.mod`:

  ```
  require github.com/user/mypackage v1.0.0
  ```

  ## Quick Start

  ```go
  package main

  import (
      "fmt"
      "github.com/user/mypackage"
  )

  func main() {
      instance := mypackage.New(mypackage.Config{
          Key: "value",
      })

      result, err := instance.Process(data)
      if err != nil {
          log.Fatal(err)
      }

      fmt.Printf("Processed %d items\n", len(result))
  }
  ```

  ## Configuration

  Using environment variables:

  ```bash
  export MYPACKAGE_DATABASE_URL="postgresql://localhost:5432/mydb"
  export MYPACKAGE_LOG_LEVEL="info"
  ```

  Or use a config file:

  ```yaml
  database:
    url: postgresql://localhost:5432/mydb
  logging:
    level: info
  ```
  ```

#### C
- **Build Systems**: Make, CMake, Autotools
- **Dependencies**: Package managers vary by OS
- **Examples**:
  ```markdown
  ## Installation

  ### From Source
  ```bash
  git clone https://github.com/user/mylib.git
  cd mylib
  mkdir build && cd build
  cmake ..
  make
  sudo make install
  ```

  ### Using Package Manager
  ```bash
  # Ubuntu/Debian
  sudo apt-get install libmylib-dev

  # macOS
  brew install mylib

  # Fedora
  sudo dnf install mylib-devel
  ```

  ## Quick Start

  Create `example.c`:

  ```c
  #include <mylib/mylib.h>
  #include <stdio.h>

  int main() {
      mylib_t* instance = mylib_create();
      mylib_configure(instance, "key", "value");

      int result_count;
      char** result = mylib_process(instance, data, &result_count);

      printf("Processed %d items\n", result_count);

      mylib_destroy(instance);
      return 0;
  }
  ```

  Compile:

  ```bash
  gcc -o example example.c -lmylib
  ./example
  ```
  ```

#### C++
- **Build Systems**: CMake, Make, MSBuild
- **Package Managers**: vcpkg, Conan, Hunter
- **Examples**:
  ```markdown
  ## Installation

  ### Using CMake
  ```cmake
  find_package(MyLib REQUIRED)
  target_link_libraries(your_target MyLib::MyLib)
  ```

  ### Using vcpkg
  ```bash
  vcpkg install mylib
  ```

  ### Using Conan
  ```bash
  conan install mylib/1.0.0@
  ```

  ## Quick Start

  Create `example.cpp`:

  ```cpp
  #include <mylib/mylib.hpp>
  #include <iostream>

  int main() {
      mylib::MyClass instance({.key = "value"});

      auto result = instance.process(data);

      std::cout << "Processed " << result.size() << " items\n";

      return 0;
  }
  ```

  Compile:

  ```bash
  g++ -std=c++17 -o example example.cpp -lmylib
  ./example
  ```
  ```

## Prerequisites

- Completed or stable software project
- Understanding of target audience (developers, end-users, admins)
- Knowledge of installation requirements
- Example use cases and workflows
- Common issues and solutions
- Version information and compatibility

## Instructions

### Step 1: Understand Your Audience

1. **Identify User Types**:
   - End users (minimal technical knowledge)
   - Developers (integrating your software)
   - System administrators (deploying/configuring)
   - Contributors (extending/improving)

2. **Determine Technical Level**:
   - Beginner: Step-by-step instructions, screenshots
   - Intermediate: Code examples, explanations
   - Advanced: Reference documentation, architecture

3. **Define User Goals**:
   - What are users trying to accomplish?
   - What problems does your software solve?
   - What are common workflows?

### Step 2: Invoke the Create User Documentation Skill

For **Python** projects:
```
"Use the create-user-documentation skill to generate Python user docs.

Language: Python
Project Type: Library / CLI Tool / Web Application
Target Audience: Developers / Data Scientists / End Users
Documentation Needed:

- Professional README with badges and features
- Installation guide (pip, conda, from source)
- Quick start tutorial with examples
- Usage guide for main features
- Configuration reference
- FAQ and troubleshooting
- Contributing guidelines
Output Directory: docs/"
```

For **JavaScript/TypeScript** projects:
```
"Use the create-user-documentation skill for JavaScript/TypeScript.

Language: JavaScript / TypeScript
Project Type: NPM Package / React Library / Node.js Tool
Target Audience: Frontend Developers / Backend Developers
Documentation Needed:

- README with installation and quick start
- Setup guide (npm, yarn, pnpm)
- Usage examples with code snippets
- API documentation overview
- TypeScript type definitions guide
- Browser compatibility notes
- Troubleshooting common issues
Output Directory: docs/"
```

For **Java** projects:
```
"Use the create-user-documentation skill for Java project docs.

Language: Java
Project Type: Library / Spring Boot Application / CLI Tool
Build System: Maven / Gradle
Target Audience: Java Developers
Documentation Needed:

- README with dependency instructions
- Installation guide (Maven, Gradle)
- Getting started tutorial
- Configuration guide (application.properties)
- Code examples for common tasks
- FAQ section
- Version compatibility matrix
Output Directory: docs/"
```

For **C#** projects:
```
"Use the create-user-documentation skill for C# documentation.

Language: C#
Project Type: .NET Library / ASP.NET Application / Console App
Target Framework: .NET Framework / .NET Core / .NET 5+
Target Audience: .NET Developers
Documentation Needed:

- README with NuGet installation
- Setup guide for Visual Studio / VS Code
- Quick start examples
- Configuration guide (appsettings.json)
- Common usage patterns
- Troubleshooting guide
- Migration guide (if applicable)
Output Directory: docs/"
```

For **Go** projects:
```
"Use the create-user-documentation skill for Go package docs.

Language: Go
Project Type: Library / CLI Tool / Service
Target Audience: Go Developers
Documentation Needed:

- README with installation (go get)
- Quick start guide
- Usage examples
- Configuration guide (env vars, config files)
- Command-line options reference
- FAQ and common pitfalls
- Contributing guide
Output Directory: docs/"
```

For **C/C++** projects:
```
"Use the create-user-documentation skill for C/C++ library docs.

Language: C / C++
Project Type: Library / System Tool / Framework
Build System: CMake / Make / Autotools
Target Audience: C/C++ Developers / System Programmers
Documentation Needed:

- README with build instructions
- Installation guide (multiple platforms)
- Quick start with example code
- API overview
- Configuration and build options
- Platform-specific notes
- Troubleshooting compilation issues
Output Directory: docs/"
```

### Step 3: Structure Documentation Output

The skill generates organized documentation:

```
docs/
├── README.md                    # Main project documentation
├── INSTALLATION.md             # Detailed installation guide
├── QUICK_START.md              # Getting started tutorial
├── USAGE.md                    # Comprehensive usage guide
├── CONFIGURATION.md            # Configuration reference
├── FAQ.md                      # Frequently asked questions
├── TROUBLESHOOTING.md          # Common issues and solutions
├── CONTRIBUTING.md             # Contribution guidelines
├── CHANGELOG.md                # Version history
├── LICENSE                     # License file
├── examples/                   # Code examples
│   ├── basic/
│   │   ├── example1.py
│   │   └── README.md
│   ├── advanced/
│   │   ├── example2.py
│   │   └── README.md
│   └── integration/
│       ├── example3.py
│       └── README.md
├── guides/                     # Detailed guides
│   ├── getting-started.md
│   ├── advanced-usage.md
│   ├── best-practices.md
│   └── migration-guide.md
└── assets/                     # Images, diagrams, screenshots
    ├── architecture.png
    ├── workflow.png
    └── screenshots/
```

### Step 4: Write Effective README

A comprehensive README includes:

```markdown
# Project Name

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](CHANGELOG.md)
[![Build Status](https://img.shields.io/travis/user/project.svg)](https://travis-ci.org/user/project)

> One-sentence description of what the project does

## Features

- ✨ Key feature 1
- 🚀 Key feature 2
- 🔧 Key feature 3

## Quick Start

```python
# Installation
pip install myproject

# Basic usage
from myproject import MyClass

instance = MyClass()
result = instance.process(data)
```

## Installation

See [INSTALLATION.md](docs/INSTALLATION.md) for detailed instructions.

**Quick install:**

```bash
pip install myproject
```

## Documentation

- [Quick Start Guide](docs/QUICK_START.md)
- [Usage Guide](docs/USAGE.md)
- [Configuration](docs/CONFIGURATION.md)
- [API Reference](docs/API.md)
- [FAQ](docs/FAQ.md)

## Examples

See the [examples](examples/) directory for more examples.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE).

## Support

- 📧 Email: support@example.com
- 💬 Discord: [Join our server](https://discord.gg/...)
- 📖 Documentation: https://docs.example.com
- 🐛 Issues: https://github.com/user/project/issues

## Acknowledgments

- Thanks to contributors
- Inspired by similar-project
- Built with awesome-library
```

### Step 5: Create Installation Guide

Comprehensive installation documentation:

```markdown
# Installation Guide

## Prerequisites

- Python 3.8 or higher
- pip 20.0 or higher
- Git (for source installation)

## Installation Methods

### Method 1: Install from PyPI (Recommended)

```bash
pip install myproject
```

### Method 2: Install from Source

```bash
git clone https://github.com/user/myproject.git
cd myproject
pip install -e .
```

### Method 3: Install for Development

```bash
git clone https://github.com/user/myproject.git
cd myproject
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .[dev]
```

## Platform-Specific Instructions

### Windows

1. Install Python from [python.org](https://www.python.org/)
2. Open Command Prompt or PowerShell
3. Run: `pip install myproject`

**Common Issues:**
- If `pip` not found, add Python to PATH
- Use `python -m pip` instead of `pip`

### macOS

```bash
# Using Homebrew
brew install python
pip3 install myproject
```

### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install python3 python3-pip
pip3 install myproject
```

## Verifying Installation

```bash
python -c "import myproject; print(myproject.__version__)"
```

Expected output: `1.0.0`

## Troubleshooting

### Issue: Permission Denied

**Solution:** Use `--user` flag:
```bash
pip install --user myproject
```

### Issue: SSL Certificate Error

**Solution:** Update certificates:
```bash
pip install --upgrade certifi
```

## Next Steps

See [Quick Start Guide](QUICK_START.md) to begin using the software.
```

### Step 6: Write Quick Start Tutorial

Effective quick start guide:

```markdown
# Quick Start Guide

Get up and running with MyProject in 5 minutes.

## Step 1: Install

```bash
pip install myproject
```

## Step 2: Basic Usage

Create a file `example.py`:

```python
from myproject import MyClass

# Initialize
instance = MyClass(config={'key': 'value'})

# Process data
data = [1, 2, 3, 4, 5]
result = instance.process(data)

print(f"Processed {len(result)} items: {result}")
```

Run it:

```bash
python example.py
```

**Expected output:**
```
Processed 5 items: [2, 4, 6, 8, 10]
```

## Step 3: Configuration

Create `config.yaml`:

```yaml
processing:
  multiplier: 2
  filter_odd: false
logging:
  level: INFO
```

Use configuration:

```python
from myproject import MyClass

instance = MyClass.from_config('config.yaml')
result = instance.process(data)
```

## Step 4: Advanced Features

### Feature A: Batch Processing

```python
batches = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]

results = instance.process_batch(batches)
```

### Feature B: Async Processing

```python
import asyncio

async def process_async():
    result = await instance.process_async(data)
    return result

result = asyncio.run(process_async())
```

## Next Steps

- Read the [Usage Guide](USAGE.md) for comprehensive documentation
- Explore [Examples](../examples/) for more use cases
- Check [FAQ](FAQ.md) for common questions
```

### Step 7: Create FAQ and Troubleshooting

```markdown
# FAQ and Troubleshooting

## Frequently Asked Questions

### How do I update to the latest version?

```bash
pip install --upgrade myproject
```

### Is this compatible with Python 3.7?

No, Python 3.8+ is required. Use version 0.9.x for Python 3.7 support.

### Can I use this in production?

Yes, version 1.0+ is production-ready. See [CHANGELOG](../CHANGELOG.md).

### How do I contribute?

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'myproject'"

**Cause:** Package not installed or wrong environment

**Solution:**
1. Verify installation: `pip list | grep myproject`
2. Check Python environment: `which python`
3. Reinstall: `pip install --force-reinstall myproject`

### Error: "Connection timeout"

**Cause:** Network issues or firewall blocking

**Solution:**
1. Check internet connection
2. Try with proxy: `pip install --proxy http://proxy:port myproject`
3. Use alternative index: `pip install --index-url https://pypi.org/simple myproject`

### Performance Issues

**Symptom:** Slow processing

**Solutions:**
- Enable caching: `instance.enable_cache()`
- Use batch processing for large datasets
- Check configuration: `instance.config.get('performance')`
- Profile your code: `python -m cProfile script.py`

### Memory Errors

**Symptom:** Out of memory errors

**Solutions:**
- Process data in chunks
- Use iterator-based methods
- Clear cache periodically: `instance.clear_cache()`
- Monitor memory: `pip install memory_profiler`

## Getting Help

If your issue isn't listed:

1. **Search Issues:** Check [GitHub Issues](https://github.com/user/project/issues)
2. **Ask Community:** Join [Discord](https://discord.gg/...)
3. **Report Bug:** Open [new issue](https://github.com/user/project/issues/new)
4. **Email Support:** support@example.com

When reporting issues, include:
- Python version: `python --version`
- Package version: `pip show myproject`
- Error messages (full traceback)
- Minimal reproducible example
```

## Quality Checklist

Before finalizing user documentation, verify:

- [ ] README is clear and comprehensive
- [ ] Installation instructions tested on target platforms
- [ ] Quick start tutorial works from scratch
- [ ] Code examples are valid and tested
- [ ] Screenshots and diagrams are current
- [ ] Configuration options documented
- [ ] FAQ addresses common questions
- [ ] Troubleshooting covers known issues
- [ ] Links and references are valid
- [ ] Version information is current
- [ ] License and attribution included
- [ ] Contributing guidelines present
- [ ] Contact information provided
- [ ] Documentation accessible to target audience
- [ ] No jargon without explanation

## Common Issues and Solutions

### Issue: Installation Instructions Don't Work
**Solution**:

- Test on fresh system or VM
- Document platform-specific steps
- Include common error messages
- Provide alternative installation methods
- Keep prerequisites list complete

### Issue: Examples Are Outdated
**Solution**:

- Test examples with each release
- Use CI/CD to validate examples
- Include version compatibility notes
- Update examples when API changes
- Link examples to specific versions

### Issue: Documentation Too Technical
**Solution**:

- Write for target audience level
- Define technical terms
- Use analogies and metaphors
- Include visual aids
- Progressive disclosure (basic → advanced)

### Issue: Missing Use Cases
**Solution**:

- Survey users for common tasks
- Document real-world scenarios
- Provide multiple example levels
- Include integration examples
- Show complete workflows

## Success Criteria

After using this skill, you should have:

- [ ] Professional README file
- [ ] Complete installation guide
- [ ] Working quick start tutorial
- [ ] Comprehensive usage documentation
- [ ] Configuration reference
- [ ] FAQ section
- [ ] Troubleshooting guide
- [ ] Code examples (tested)
- [ ] Contributing guidelines
- [ ] License information
- [ ] All documentation accurate and current
- [ ] Target audience can use software independently

## Related Skills

- `generate-docstrings`: Create API documentation
- `generate-api-docs`: Build API reference
- `create-technical-docs`: Document architecture
- `init-*-project`: Initialize projects with docs

## Tools and Resources

### Documentation Generators
- **MkDocs**: Python documentation sites
- **Docusaurus**: React-based documentation
- **VuePress**: Vue-powered documentation
- **GitBook**: Collaborative documentation
- **Read the Docs**: Free documentation hosting

### Markdown Tools
- **Typora**: WYSIWYG Markdown editor
- **VS Code**: Markdown preview
- **Grip**: GitHub-flavored Markdown preview
- **pandoc**: Document conversion

### Diagramming Tools
- **Mermaid**: Text-based diagrams
- **draw.io**: Visual diagramming
- **PlantUML**: UML diagrams from text
- **Excalidraw**: Hand-drawn diagrams

### Badge Services
- **shields.io**: Dynamic badges
- **badgen.net**: Fast badge generation
- **GitHub Actions**: Build status badges

## Additional Resources

- [Write the Docs](https://www.writethedocs.org/)
- [Google Developer Documentation Style Guide](https://developers.google.com/style)
- [Microsoft Writing Style Guide](https://docs.microsoft.com/en-us/style-guide/)
- [The Documentation System](https://documentation.divio.com/)
- [Awesome README](https://github.com/matiassingers/awesome-readme)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5 - documentation/user_docs/
