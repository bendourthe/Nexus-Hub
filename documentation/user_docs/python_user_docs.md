# Python User Documentation

## Objective
Create clear, comprehensive user-facing documentation that enables users of all skill levels to quickly understand, install, configure, and effectively use the software.

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
- [ ] Prerequisites clearly listed
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
# Python User Documentation Request

Please create comprehensive user documentation for this Python project following this protocol:

## Phase 1: Audience Analysis & Documentation Planning

1. **Identify Target Audience**
   - Primary users: [developers/end-users/data scientists/etc.]
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

## Phase 2: README.md - Professional Project Overview

Create a comprehensive README.md that serves as the front door to your project:

### README.md Template

```markdown
# [Project Name]

[![Version](https://img.shields.io/badge/version-X.Y.Z-blue)]()
[![Python](https://img.shields.io/badge/python-3.9+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)]()

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
- **[Feature 4]**: Note integration capabilities or extensibility

---

## 🚀 Quick Start

Get started in less than 5 minutes:

### Installation

```bash
# Using pip
pip install [package-name]

# Or install from source
git clone https://github.com/username/project.git
cd project
pip install -e .
```

### Basic Usage

```python
from project import MainClass

# Simple example showing immediate value
instance = MainClass()
result = instance.process("example input")
print(result)
# Output: [expected output]
```

**That's it!** You're ready to go. See [Usage Examples](#usage-examples) for more.

---

## 📦 Installation

### Prerequisites

Before installing, ensure you have:
- Python 3.9 or higher
- pip (usually comes with Python)
- [Optional] Virtual environment tool (venv or conda)

### Installation Options

#### Option 1: Install from PyPI (Recommended)
```bash
pip install [package-name]
```

#### Option 2: Install from Source
```bash
git clone https://github.com/username/project.git
cd project
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .[dev]  # Install with development dependencies
```

#### Option 3: Install with Optional Features
```bash
# With all optional features
pip install [package-name][all]

# With specific features
pip install [package-name][feature1,feature2]
```

### Verify Installation

```bash
# Check version
python -c "import package_name; print(package_name.__version__)"

# Run tests
python -m pytest tests/
```

**Troubleshooting**: See [Installation Issues](#installation-issues) if you encounter problems.

---

## 💡 Usage Examples

### Example 1: Basic Usage

[Description of what this example demonstrates]

```python
from project import MainClass

# Setup
instance = MainClass(param1="value", param2=42)

# Perform operation
result = instance.process("input data")

# Display result
print(f"Result: {result}")
```

**Output**:
```
Result: processed_data
```

### Example 2: Intermediate Usage

[Description of more complex scenario]

```python
from project import MainClass, HelperFunction

# Configure with options
instance = MainClass(
    param1="value",
    param2=42,
    verbose=True,
    custom_config={"option1": "value1"}
)

# Process with error handling
try:
    result = instance.process("complex input")
    processed = HelperFunction.transform(result)
    print(f"Success: {processed}")
except ValueError as e:
    print(f"Error: {e}")
    # Handle error appropriately
```

### Example 3: Advanced Usage

[Description of advanced pattern or integration]

```python
from project import MainClass, AsyncProcessor
import asyncio

async def advanced_workflow():
    """Example of advanced async workflow."""
    # Setup async processor
    processor = AsyncProcessor(max_workers=4)

    # Process multiple items concurrently
    items = ["item1", "item2", "item3"]
    results = await processor.process_batch(items)

    # Aggregate results
    summary = processor.aggregate(results)
    return summary

# Run async workflow
results = asyncio.run(advanced_workflow())
print(f"Processed {len(results)} items")
```

### Example 4: Real-World Use Case

[Description of practical application]

```python
# [Complete, runnable example solving a real problem]
# [Show inputs, processing, and expected outputs]
# [Include error handling and best practices]
```

**More Examples**: See [examples/](examples/) directory for additional use cases.

---

## 🔧 Configuration

### Basic Configuration

```python
from project import MainClass

# Configure through constructor
instance = MainClass(
    option1="value1",  # Description of option1
    option2=42,        # Description of option2
    debug=False        # Enable debug output
)
```

### Configuration File

Alternatively, use a configuration file:

```yaml
# config.yaml
option1: value1
option2: 42
debug: false
advanced:
  timeout: 30
  retry_count: 3
```

```python
from project import load_config

# Load from file
config = load_config("config.yaml")
instance = MainClass(config=config)
```

### Environment Variables

```bash
# Set via environment variables
export PROJECT_OPTION1="value1"
export PROJECT_OPTION2="42"
export PROJECT_DEBUG="false"
```

```python
from project import MainClass

# Automatically loads from environment
instance = MainClass.from_env()
```

---

## 📚 Documentation

- **[User Guide](docs/USER_GUIDE.md)**: Comprehensive usage documentation
- **[API Reference](docs/API.md)**: Complete API documentation
- **[Examples](examples/)**: More code examples and tutorials
- **[FAQ](docs/FAQ.md)**: Frequently asked questions
- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Common issues and solutions

---

## ❓ FAQ

### How do I [common task]?

[Clear, concise answer with code example if relevant]

### What's the difference between [Feature A] and [Feature B]?

[Explanation of differences and when to use each]

### Can I use this with [framework/library]?

[Yes/No with explanation and example if applicable]

### How do I contribute?

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

**More Questions?** Check the full [FAQ](docs/FAQ.md) or [open an issue](https://github.com/username/project/issues).

---

## 🐛 Troubleshooting

### Installation Issues

**Problem**: `ModuleNotFoundError: No module named 'package_name'`

**Solution**: Ensure you've activated your virtual environment and installed the package:
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install package_name
```

### Common Errors

**Error**: `ValueError: Invalid configuration`

**Cause**: Configuration parameter has invalid value

**Solution**: Check configuration values match expected types:
```python
# Incorrect
instance = MainClass(param1=123)  # param1 expects string

# Correct
instance = MainClass(param1="123")
```

**More Issues?** See full [Troubleshooting Guide](docs/TROUBLESHOOTING.md).

---

## 🧪 Testing

Run the test suite to verify everything works:

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test
python -m pytest tests/test_module.py::test_function
```

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Quick start for contributors:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

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
- **Email**: [support@project.com](mailto:support@project.com)
- **Documentation**: [https://project.readthedocs.io](https://project.readthedocs.io)

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

Create detailed installation instructions for all platforms:

### INSTALL.md Template

```markdown
# Installation Guide

Complete installation instructions for [Project Name].

---

## System Requirements

### Minimum Requirements
- **OS**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 20.04+)
- **Python**: 3.9 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 500MB

### Recommended Requirements
- Python 3.11+ for best performance
- 16GB RAM for large datasets
- SSD for faster processing

---

## Installation Methods

### Method 1: Quick Install (Recommended)

For most users, this is the simplest approach:

```bash
pip install [package-name]
```

**Verification**:
```bash
python -c "import package_name; print(package_name.__version__)"
```

### Method 2: Development Installation

For contributors or users who want the latest code:

#### Windows
```powershell
# Clone repository
git clone https://github.com/username/project.git
cd project

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e .[dev]

# Verify installation
pytest tests/
```

#### macOS/Linux
```bash
# Clone repository
git clone https://github.com/username/project.git
cd project

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .[dev]

# Verify installation
pytest tests/
```

### Method 3: Conda Installation

For users preferring conda:

```bash
# Create conda environment
conda create -n project-env python=3.11
conda activate project-env

# Install from conda-forge (if available)
conda install -c conda-forge [package-name]

# Or install via pip in conda environment
pip install [package-name]
```

### Method 4: Docker Installation

For containerized deployment:

```bash
# Pull Docker image
docker pull username/project:latest

# Run container
docker run -it username/project:latest

# Or build from Dockerfile
docker build -t project .
docker run -it project
```

---

## Platform-Specific Instructions

### Windows

**Prerequisites**:
1. Install Python from [python.org](https://python.org)
2. Ensure "Add Python to PATH" is checked during installation
3. Open Command Prompt or PowerShell as Administrator (if needed)

**Installation**:
```powershell
# Verify Python installation
python --version

# Install package
pip install [package-name]

# If you get SSL errors, try:
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org [package-name]
```

**Common Issues**:
- **Error**: "pip is not recognized"
  - **Fix**: Add Python Scripts directory to PATH
- **Error**: "Access is denied"
  - **Fix**: Run as Administrator or use `--user` flag

### macOS

**Prerequisites**:
1. Install Homebrew (if not installed): `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
2. Install Python: `brew install python@3.11`

**Installation**:
```bash
# Verify Python installation
python3 --version

# Install package
pip3 install [package-name]

# If you need to install system dependencies
brew install [dependency]
```

**Common Issues**:
- **Error**: "Permission denied"
  - **Fix**: Use `pip3 install --user [package-name]`
- **Error**: "Command not found: pip3"
  - **Fix**: Use `python3 -m pip install [package-name]`

### Linux

#### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv

# Install package
pip3 install [package-name]

# Install system dependencies (if needed)
sudo apt install [dependency]
```

#### Fedora/RHEL/CentOS
```bash
# Install Python and pip
sudo dnf install python3 python3-pip

# Install package
pip3 install [package-name]
```

#### Arch Linux
```bash
# Install Python and pip
sudo pacman -S python python-pip

# Install package
pip install [package-name]
```

---

## Optional Dependencies

### Feature Groups

Install optional feature groups as needed:

```bash
# Data processing features
pip install [package-name][data]

# Web/API features
pip install [package-name][web]

# Machine learning features
pip install [package-name][ml]

# All features
pip install [package-name][all]
```

### Individual Optional Packages

```bash
# For database support
pip install sqlalchemy psycopg2-binary

# For async support
pip install aiohttp asyncio

# For visualization
pip install matplotlib seaborn
```

---

## Verification

### Quick Verification

```bash
# Check package version
python -c "import package_name; print(package_name.__version__)"

# Run self-test
python -m package_name.self_test
```

### Full Verification

```bash
# Clone repository (if not already done)
git clone https://github.com/username/project.git
cd project

# Run full test suite
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### Verify Installation Location

```bash
# Find where package is installed
python -c "import package_name; print(package_name.__file__)"

# List installed packages
pip list | grep package-name
```

---

## Upgrading

### Upgrade to Latest Version

```bash
# Upgrade package
pip install --upgrade [package-name]

# Verify new version
python -c "import package_name; print(package_name.__version__)"
```

### Upgrade from Specific Version

```bash
# Upgrade from v1.x to v2.x
pip install --upgrade [package-name]>=2.0.0

# Check for breaking changes
# Review CHANGELOG.md for migration guide
```

---

## Uninstallation

```bash
# Uninstall package
pip uninstall [package-name]

# Remove configuration files (if any)
rm -rf ~/.config/package_name

# Remove virtual environment (if created)
rm -rf .venv
```

---

## Troubleshooting Installation

### Common Installation Errors

**Error**: `Could not find a version that satisfies the requirement`
- **Cause**: Package not available for your Python version or platform
- **Fix**: Check Python version (`python --version`) and upgrade if needed

**Error**: `pip: command not found`
- **Cause**: pip not installed or not in PATH
- **Fix**: Install pip: `python -m ensurepip --upgrade`

**Error**: `SSL: CERTIFICATE_VERIFY_FAILED`
- **Cause**: SSL certificate issues
- **Fix**: Update certificates or use `--trusted-host` flag

**Error**: Compilation errors during installation
- **Cause**: Missing compilers or development libraries
- **Fix**: Install build tools:
  - Windows: Install Visual C++ Build Tools
  - macOS: `xcode-select --install`
  - Linux: `sudo apt install build-essential python3-dev`

### Getting Help

If installation fails:
1. Check [GitHub Issues](https://github.com/username/project/issues)
2. Review [Troubleshooting Guide](TROUBLESHOOTING.md)
3. Open a new issue with:
   - Your OS and version
   - Python version
   - Full error message
   - Installation method attempted

---

## Next Steps

After successful installation:
1. Review the [Quick Start Guide](README.md#quick-start)
2. Try the [examples/](examples/) directory
3. Read the [User Guide](USER_GUIDE.md)
4. Join the [community discussions](https://github.com/username/project/discussions)
```

## Phase 4: Quick Start Guide

Create a focused quick start for immediate success:

### Structure
1. **Goal**: What the user will achieve
2. **Time Estimate**: "5 minutes" or "15 minutes"
3. **Prerequisites**: What they need before starting
4. **Steps**: Clear, numbered steps with code
5. **Expected Output**: Show what success looks like
6. **Next Steps**: Where to go from here

### Quick Start Template

```markdown
# Quick Start Guide

Get started with [Project Name] in under 10 minutes.

---

## What You'll Build

By the end of this guide, you'll have:
- ✅ Installed and configured [Project Name]
- ✅ Run your first example
- ✅ Understanding of core concepts
- ✅ Ready to build your own solution

**Time Required**: ~10 minutes

---

## Prerequisites

- Python 3.9+ installed
- Basic Python knowledge
- Terminal/command line access

---

## Step 1: Installation (2 minutes)

```bash
pip install [package-name]
```

Verify installation:
```bash
python -c "import package_name; print('✅ Installation successful!')"
```

---

## Step 2: Your First Program (3 minutes)

Create a file called `first_example.py`:

```python
from package_name import MainClass

# Create instance with simple configuration
processor = MainClass(option="value")

# Process some data
result = processor.process("Hello, World!")

# Display result
print(f"Result: {result}")
```

Run it:
```bash
python first_example.py
```

**Expected Output**:
```
Result: Processed: Hello, World!
```

✅ **Success!** You've run your first program.

---

## Step 3: Understand the Basics (3 minutes)

Let's break down what happened:

1. **Import**: We imported the main class
2. **Configure**: We created an instance with options
3. **Process**: We processed data
4. **Result**: We got a result back

Now try modifying the example:

```python
# Try different inputs
inputs = ["Hello", "World", "Python"]

for text in inputs:
    result = processor.process(text)
    print(f"{text} -> {result}")
```

---

## Step 4: Next Steps (2 minutes)

Now that you have the basics:

### Explore More Examples
- **[Example 2](examples/example_02.py)**: [Description]
- **[Example 3](examples/example_03.py)**: [Description]

### Read Documentation
- **[User Guide](USER_GUIDE.md)**: Comprehensive usage guide
- **[API Reference](API.md)**: Complete API documentation

### Join Community
- **[GitHub Discussions](https://github.com/username/project/discussions)**: Ask questions
- **[Examples Repository](https://github.com/username/project-examples)**: More examples

---

## Common Next Tasks

### Task: [Common task users want to do]

```python
# [Code example for task]
```

### Task: [Another common task]

```python
# [Code example]
```

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

Common questions about [Project Name].

---

## General Questions

### What is [Project Name]?

[Clear, concise explanation of what the project is and what it does]

### Who is this for?

[Target audience and use cases]

### Is it free?

[License and pricing information]

### How do I get support?

[Support channels and resources]

---

## Installation & Setup

### Which Python version do I need?

Python 3.9 or higher is required. Python 3.11+ is recommended for best performance.

### Can I use this on [platform]?

[Platform compatibility information]

### Do I need [dependency]?

[Dependency requirements and optionals]

---

## Usage Questions

### How do I [common task]?

[Answer with code example]

### What's the difference between [Feature A] and [Feature B]?

[Clear explanation of differences with use case examples]

### Can I use this in production?

[Stability, versioning, and production readiness information]

### How do I handle [specific scenario]?

[Solution with code example]

---

## Troubleshooting

### Why am I getting [common error]?

**Error**: `[error message]`

**Cause**: [Why this happens]

**Solution**: [How to fix with code]

### The program is slow. How can I improve performance?

[Performance optimization tips]

---

## Contributing

### How can I contribute?

[Contribution process overview]

### I found a bug. What should I do?

[Bug reporting process]

---

[Back to README](../README.md)
```

---

## Output Format

Please provide user documentation in this format:

### Documentation Files Created

```markdown
## README.md
[Generated README content]

---

## INSTALL.md (if applicable)
[Generated installation guide]

---

## QUICKSTART.md (if applicable)
[Generated quick start guide]

---

## FAQ.md (if applicable)
[Generated FAQ]

---
```

### Summary Report

```markdown
## User Documentation Summary

**Files Created**: [count]
- README.md: [Complete/Updated]
- Installation Guide: [Yes/No]
- Quick Start Guide: [Yes/No]
- FAQ: [Yes/No]
- Troubleshooting Guide: [Yes/No]

**Target Audience**: [Beginner/Intermediate/Advanced]

**Content Metrics**:
- Code examples: [count]
- Platform-specific instructions: [Windows/macOS/Linux]
- Installation methods documented: [count]
- FAQ entries: [count]
- Troubleshooting scenarios: [count]

**Quality Checks**:
- [ ] All examples tested and functional
- [ ] Installation instructions verified on all platforms
- [ ] Links working and up-to-date
- [ ] Screenshots/diagrams included (if applicable)
- [ ] Accessible to target audience

**Next Steps**:
- [ ] Review documentation for accuracy
- [ ] Test installation on fresh system
- [ ] Get feedback from target users
- [ ] Set up documentation hosting (ReadTheDocs, GitHub Pages)
```

---

## Best Practices

1. **Write for Your Audience**
   - Match technical level to users
   - Explain jargon and concepts
   - Provide context for decisions

2. **Show, Don't Just Tell**
   - Include complete, runnable examples
   - Show expected output
   - Demonstrate common patterns

3. **Make It Easy to Find Information**
   - Clear table of contents
   - Good headings and structure
   - Links between related sections

4. **Test Your Documentation**
   - Follow your own instructions
   - Have others test installation
   - Verify all examples work

5. **Keep It Updated**
   - Update with code changes
   - Version documentation with releases
   - Address user questions in FAQ

6. **Progressive Disclosure**
   - Start simple, add complexity gradually
   - Quick start for immediate success
   - Detailed docs for advanced users

---
~~~

## Output Format Specifications

The user documentation should:
- Be clear and accessible to the target audience skill level
- Include complete, tested, runnable examples
- Provide step-by-step instructions with expected outcomes
- Cover multiple platforms where applicable
- Include troubleshooting for common issues
- Use consistent formatting and structure
- Link between related documentation sections
- Include visual aids (badges, diagrams) where helpful
