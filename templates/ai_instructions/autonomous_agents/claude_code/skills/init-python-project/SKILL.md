---
name: init-python-project
description: Initialize complete Python project with standard structure, configuration files, and documentation
version: 1.0.0
author: Benjamin Dourthe
language: Python
category: Project Initialization
tags: [python, initialization, setup, project-structure, boilerplate]
priority: HIGH
template_source: agent_prompts/autonomous_agents/claude_code/python/
---

# Initialize Python Project

Create a complete, production-ready Python project with standard structure, configuration files, testing framework, and documentation in minutes.

## When to Use This Skill

Use this skill when you need to:

- ✅ Start a new Python project from scratch

- ✅ Establish standard project structure quickly

- ✅ Set up development environment with best practices

- ✅ Initialize testing framework and CI/CD configuration

- ✅ Create documentation templates (README, CHANGELOG, DEVLOG)

- ✅ Configure linting, formatting, and type checking

- ✅ Onboard team with consistent project setup

## What This Skill Does

Creates a complete Python project structure following industry best practices:

### 1. Directory Structure
```
project_name/
├── .venv/                  # Virtual environment
├── src/                    # Source code
│   ├── __init__.py
│   ├── main.py            # Entry point
│   └── core/              # Core modules
│       ├── __init__.py
│       └── utils/
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── run_all_tests.py   # Master test runner
│   ├── common.py          # Shared test utilities
│   ├── test_config.py     # Test configuration
│   └── test_main.py       # Example tests
├── docs/                   # Documentation
├── .gitignore             # Git ignore rules
├── .github/               # GitHub workflows (optional)
│   └── workflows/
│       └── ci.yml
├── CLAUDE.md              # Claude Code configuration
├── CHANGELOG.md           # Version history
├── DEVLOG.md              # Development log
├── README.md              # Project documentation
├── pyproject.toml         # Project configuration
└── requirements.txt       # Dependencies
```

### 2. Configuration Files
- **pyproject.toml**: Project metadata, dependencies, tool configurations

- **requirements.txt**: Pinned dependencies for reproducibility

- **.gitignore**: Comprehensive Python ignore patterns

- **CLAUDE.md**: Claude Code project guidelines

### 3. Documentation
- **README.md**: Installation, usage, and feature documentation

- **CHANGELOG.md**: Version history following Keep a Changelog format

- **DEVLOG.md**: Development task list and decision log

### 4. Testing Framework
- Master test runner with auto-detection

- Shared test utilities and fixtures

- Configuration for pass/fail criteria

- Example test structure

### 5. Development Tools
- Black (code formatter)

- Flake8 (linter)

- mypy (type checker)

- isort (import sorter)

- pytest (test framework)

## Prerequisites

- Python 3.9+ installed

- pip (Python package installer)

- git (version control)

- (Optional) Claude Code for AI assistance

## Instructions

### Step 1: Define Project Requirements

Gather this information before initialization:

**Project Details**:

- **Name**: Project identifier (lowercase, underscores for spaces)

- **Description**: One-line summary of purpose

- **Type**: CLI tool / Web API / Library / Data Processing / GUI Application

- **Author**: Your name and email

**Dependencies**:

- Core dependencies (e.g., fastapi, pandas, requests)

- Development dependencies (testing, linting)

**Features**:

- Key capabilities to document

- Initial version number (default: 0.1.0)

### Step 2: Invoke the Skill

```
"Use the init-python-project skill to create a new Python project.

Project Details:

- Name: my_awesome_project

- Description: A tool for processing data and generating reports

- Type: CLI tool

- Author: Your Name (your.email@example.com)

Dependencies:

- click (CLI framework)

- pandas (data processing)

- jinja2 (template rendering)

Features:

- Load CSV data files

- Apply transformations

- Generate HTML reports

- Export to multiple formats

Please initialize the complete project structure."
```

### Step 3: Review Generated Structure

The skill will create all files and directories. Verify:

```bash
# Check structure
tree my_awesome_project/

# Expected output:
my_awesome_project/
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml
├── CHANGELOG.md
├── CLAUDE.md
├── DEVLOG.md
├── README.md
├── docs/
├── pyproject.toml
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── main.py
│   └── core/
│       ├── __init__.py
│       └── utils/
│           └── __init__.py
└── tests/
    ├── __init__.py
    ├── common.py
    ├── run_all_tests.py
    ├── test_config.py
    └── test_main.py
```

### Step 4: Set Up Development Environment

```bash
# Navigate to project
cd my_awesome_project

# Create and activate virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Unix/Mac)
source .venv/bin/activate

# Install dependencies
python -m pip install -e ".[dev]"

# Verify installation
python -m pip list
```

### Step 5: Verify Setup

Run initial tests to verify everything works:

```bash
# Run tests
pytest tests/

# Or use master test runner
python tests/run_all_tests.py

# Format code
black src/ tests/

# Check types
mypy src/

# Lint code
flake8 src/ tests/
```

### Step 6: Initialize Git Repository

```bash
# Initialize git
git init

# Add all files
git add .

# Initial commit
git commit -m "Initial project structure

- Standard Python project layout

- Testing framework configured

- Documentation templates created

- Development tools configured

Generated with init-python-project skill"

# (Optional) Add remote and push
git remote add origin <your-repo-url>
git push -u origin main
```

### Step 7: Start Development

Your project is now ready! Begin developing:

```bash
# Run application
python src/main.py

# Run tests in watch mode
pytest-watch

# Format on save (configure your IDE)
```

## Generated File Contents

### pyproject.toml
```toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools-scm"]
build-backend = "setuptools.build_meta"

[project]
name = "my-awesome-project"
version = "0.1.0"
description = "A tool for processing data and generating reports"
authors = [{name = "Your Name", email = "your.email@example.com"}]
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "click>=8.0",
    "pandas>=2.0",
    "jinja2>=3.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=22.0",
    "flake8>=4.0",
    "mypy>=0.950",
    "isort>=5.10"
]

[tool.black]
line-length = 88
target-version = ['py39']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "-v --cov=src --cov-report=html --cov-report=term"
```

### README.md
```markdown
# My Awesome Project - v0.1.0

## What's New
- Initial release

- CSV data loading

- Data transformations

- HTML report generation

## Overview
A command-line tool for processing data and generating reports. Loads CSV files, applies transformations, and exports results in multiple formats.

## Features
- **Data Loading**: Import CSV files with automatic type detection

- **Transformations**: Apply filters, aggregations, and calculations

- **Report Generation**: Create HTML reports with charts and tables

- **Multi-Format Export**: Save results as CSV, JSON, or Excel

## Installation

### Prerequisites
- Python 3.9 or higher

- pip (Python package installer)

### Setup
```bash
git clone <repository-url>
cd my-awesome-project
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
```

## Usage
```bash
# Basic usage
python src/main.py input.csv --output report.html

# With transformations
python src/main.py input.csv --filter "value > 100" --group-by category

# Export formats
python src/main.py input.csv --export json
python src/main.py input.csv --export xlsx
```

## Development

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Master test runner
python tests/run_all_tests.py
```

### Code Quality
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type check
mypy src/

# Lint
flake8 src/ tests/
```

## Contributing
1. Fork the repository

2. Create a feature branch

3. Make your changes

4. Run tests and quality checks

5. Submit a pull request

## License
[Your chosen license]

## Contact
Your Name - your.email@example.com
```

### CHANGELOG.md
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [0.1.0] - 2025-10-20

### Added
- Initial project structure

- CSV data loading functionality

- Data transformation pipeline

- HTML report generation

- Multi-format export (CSV, JSON, Excel)

- Comprehensive test suite

- CLI interface with click

- Documentation templates
```

### DEVLOG.md
```markdown
# Development Log

## Current Task List

### High Priority
- [ ] Implement CSV data loader

- [ ] Create transformation pipeline

- [ ] Build HTML report generator

- [ ] Add export functionality

### Medium Priority
- [ ] Add data validation

- [ ] Implement caching

- [ ] Create configuration file support

- [ ] Add progress indicators

### Low Priority
- [ ] Support additional input formats (Excel, JSON)

- [ ] Add interactive mode

- [ ] Create web UI

- [ ] Add database export option

## Development History

### Project Architecture
- **Design**: Command-line tool with modular architecture

- **Tech Stack**: Python 3.9+, pandas, Jinja2, click

- **Pattern**: Pipeline-based data processing

### Initial Setup - 2025-10-20
- Created standard Python project structure

- Configured development tools (black, mypy, pytest)

- Set up testing framework

- Initialized documentation

## Troubleshooting History

(Document issues and solutions here as they arise)
```

### src/main.py
```python
"""
My Awesome Project - Main Entry Point

A tool for processing data and generating reports.

Authors:

    - Your Name (your.email@example.com)
"""
import sys
from typing import Optional


def main(args: Optional[list] = None) -> int:
    """
    Main entry point for the application.

    Args:
        args: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    if args is None:
        args = sys.argv[1:]

    print("My Awesome Project v0.1.0")
    print("=" * 50)
    print("Project initialized successfully!")
    print("\nNext steps:")
    print("1. Implement core functionality in src/core/")
    print("2. Add tests in tests/")
    print("3. Update documentation")
    print("4. Run 'python tests/run_all_tests.py' to verify")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### tests/run_all_tests.py
```python
"""
Master test runner for My Awesome Project.

Automatically discovers and runs all test suites, providing comprehensive
reporting with pass/fail status, timing, and coverage information.

Authors:

    - Your Name (your.email@example.com)
"""
import sys
import unittest
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main():
    """Run all test suites and report results."""
    print("=" * 100)
    print("=" * 100)
    print(" " * 20 + "MY AWESOME PROJECT - FULL TEST SUITES RUNNER")
    print("─" * 100)
    print("─" * 100)
    print(f"Full test suites execution started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print()
    print("=" * 100)
    print(" " * 30 + "TEST EXECUTION SUMMARY")
    print("─" * 100)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("─" * 100)

    if result.wasSuccessful():
        print("FINAL TESTS STATUS: ✅  All tests passed")
    else:
        print("FINAL TESTS STATUS: ❌  Some tests failed")

    print("=" * 100)
    print("=" * 100)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
```

## Project Types and Variations

### CLI Tool (Default)
- click or argparse for CLI

- Rich for beautiful terminal output

- Progress bars and interactive prompts

### Web API
```
Dependencies:

- fastapi

- uvicorn

- pydantic

- sqlalchemy

Structure additions:

- src/api/routes/

- src/models/

- src/schemas/
```

### Data Science Project
```
Dependencies:

- pandas

- numpy

- matplotlib

- jupyter

- scikit-learn

Structure additions:

- notebooks/

- data/raw/

- data/processed/

- models/
```

### Library/Package
```
Additional files:

- setup.py

- MANIFEST.in

- LICENSE

Focus on:

- Public API design

- Documentation

- Examples/
```

## Customization Options

### Minimal Setup (Fast Start)
```
"Use init-python-project with minimal configuration:

- Basic structure only

- Essential documentation

- Skip CI/CD files

- No example tests"
```

### Full Setup (Production-Ready)
```
"Use init-python-project with full configuration:

- Complete directory structure

- GitHub Actions CI/CD

- Pre-commit hooks

- Comprehensive documentation

- Example tests and fixtures"
```

### Custom Template
```
"Use init-python-project with custom requirements:

- FastAPI web application

- PostgreSQL database

- Docker configuration

- AWS deployment scripts

- OpenAPI documentation"
```

## Common Post-Initialization Tasks

### 1. Configure IDE
- Set Python interpreter to `.venv/bin/python`

- Enable format on save (Black)

- Configure test runner (pytest)

- Set up debugger

### 2. Set Up Pre-Commit Hooks
```bash
pip install pre-commit
pre-commit install
```

Create `.pre-commit-config.yaml`:
```yaml
repos:

  - repo: https://github.com/psf/black
    rev: 22.10.0
    hooks:

      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:

      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 5.0.4
    hooks:

      - id: flake8
```

### 3. Configure GitHub Repository
- Create repository on GitHub

- Add description and topics

- Set up branch protection

- Enable GitHub Actions

- Add README badges

### 4. Start Development
- Review DEVLOG.md task list

- Prioritize features

- Begin with tests (TDD)

- Commit frequently

## Success Criteria

After initialization, verify:

- [ ] All directories created correctly

- [ ] Configuration files are valid

- [ ] Virtual environment created and activated

- [ ] Dependencies installed successfully

- [ ] Tests run and pass

- [ ] Linting and formatting tools work

- [ ] Documentation is complete and accurate

- [ ] Git repository initialized

- [ ] CLAUDE.md configured for Claude Code

- [ ] Ready to begin development

## Related Skills

**Use After Initialization**:

- `setup-python-system-prompt`: Configure Claude Code standards

- `create-claude-md`: Customize project guidelines

- `generate-test-cases`: Add comprehensive tests

- `generate-docstrings`: Document code

**For Development**:

- `plan-before-code`: Plan features before implementing

- `test-driven-development`: Write tests first

- `cleanup-python`: Clean code periodically

## Additional Resources

- [Python Packaging Guide](https://packaging.python.org/)

- [Python Project Structure](https://docs.python-guide.org/writing/structure/)

- [pytest Documentation](https://docs.pytest.org/)

- [Black Code Formatter](https://black.readthedocs.io/)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5 - Python Project Standards
**Priority**: HIGH - Immediate value for new projects
