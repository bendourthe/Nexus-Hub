---
name: python-command-preferences
description: Python command execution preferences including the CRITICAL rule to never run commands in chat, PowerShell syntax, virtual environment management, package management, and development tools. Use when discussing terminal commands, running tests, or managing Python environments.
---

# Python Command Preferences

## Execution Protocol

**CRITICAL: Never run commands in chat. Always request user execution.**

### Response Pattern
```
Please run in your terminal:

1. Activate venv:
   .venv\Scripts\Activate.ps1

2. Navigate to project:
   cd [project-name]

3. Execute test:
   python tests/run_all_tests.py

4. Share any errors for assistance.
```

### Never Say:
- "Let me run this command"
- "I'll execute this"
- "Running the application"
- "Executing the script"

### Always Say:
- "Please run this in your terminal"
- "Execute after activating venv"
- "Run and share results"
- "Please execute the following"

## PowerShell Syntax

### Project Setup
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Verify Python location
where python
```

### Package Installation
```powershell
# Development install
python -m pip install -e .[dev]

# Install specific package
python -m pip install package_name

# Install from requirements
python -m pip install -r requirements.txt

# Upgrade package
python -m pip install --upgrade package_name
```

### Testing
```powershell
# Run all tests
python tests/run_all_tests.py

# Run pytest
python -m pytest tests/ -v

# Run with coverage
python -m coverage run -m pytest
python -m coverage report
python -m coverage html
```

### Code Quality
```powershell
# Formatting
python -m black src/ tests/
python -m isort src/ tests/

# Or with ruff (modern alternative)
ruff format .
ruff check .
ruff check --fix .

# Linting
python -m flake8 src/ tests/
python -m mypy src/
```

## Virtual Environment Management

### Standard Workflow
1. **Create**: `python -m venv .venv`
2. **Activate**: `.venv\Scripts\Activate.ps1` (Windows PowerShell)
3. **Verify**: `where python` (should show .venv path)
4. **Install**: `python -m pip install -e .[dev]`
5. **Deactivate**: `deactivate`

### Unix/Linux/Mac Activation
```bash
# Bash/Zsh
source .venv/bin/activate

# Fish
source .venv/bin/activate.fish
```

### Troubleshooting
```powershell
# Check current Python
where python
python --version

# Check pip packages
python -m pip list

# Reinstall virtual environment
Remove-Item -Recurse -Force .venv
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

## Package Management Rules

### Best Practices
- **Never install globally** - always use virtual environment
- **Use development install**: `pip install -e .[dev]`
- **Keep requirements.txt updated** (if using legacy approach)
- **Pin major versions** for stability
- **Use pyproject.toml** as single source of truth (modern approach)

### Commands
```powershell
# Check installed packages
python -m pip list

# Generate requirements (legacy)
python -m pip freeze > requirements.txt

# Show package info
python -m pip show package_name

# Check for outdated packages
python -m pip list --outdated

# Update all packages (careful!)
python -m pip list --outdated --format=freeze | %{$_.split('==')[0]} | %{python -m pip install --upgrade $_}
```

## Development Tools Commands

### Formatting
```powershell
# Black (code formatter)
python -m black src/ tests/
python -m black --check src/  # Check without modifying

# isort (import sorter)
python -m isort src/ tests/
python -m isort --check-only src/  # Check without modifying

# ruff (modern all-in-one)
ruff format .
ruff format --check .
```

### Linting
```powershell
# flake8 (style checker)
python -m flake8 src/ tests/
python -m flake8 --max-line-length=88 src/

# pylint (comprehensive linting)
python -m pylint src/

# ruff (modern alternative to flake8)
ruff check .
ruff check --fix .  # Auto-fix issues
```

### Type Checking
```powershell
# mypy (static type checker)
python -m mypy src/
python -m mypy --strict src/

# pyright (alternative type checker)
pyright src/
```

### Testing
```powershell
# pytest
python -m pytest tests/ -v
python -m pytest tests/ -v --tb=short  # Shorter traceback
python -m pytest tests/ -x  # Stop on first failure
python -m pytest tests/ -k "test_name"  # Run specific tests

# Coverage
python -m coverage run -m pytest
python -m coverage report
python -m coverage html  # Generate HTML report

# Mutation testing
python -m mutmut run
python -m mutmut results
```

## Modern Toolchain (uv + ruff)

### uv Commands
```powershell
# Create project
uv init my-project
cd my-project

# Add dependencies
uv add requests pandas
uv add --dev pytest ruff mypy

# Install/sync
uv sync

# Run commands
uv run python src/main.py
uv run pytest tests/
uv run ruff check .
```

### ruff Commands
```powershell
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .

# Check formatting without changes
ruff format --check .
```

## Common Command Patterns

### Before Committing
```powershell
# Full quality check
python -m black src/ tests/
python -m isort src/ tests/
python -m flake8 src/ tests/
python -m mypy src/
python -m pytest tests/ -v
```

### Or with modern tools
```powershell
ruff format .
ruff check .
python -m mypy src/
python -m pytest tests/ -v
```

### Quick Test Run
```powershell
python -m pytest tests/ -x -v --tb=short
```

### Full Test with Coverage
```powershell
python -m coverage run -m pytest tests/ -v
python -m coverage report --fail-under=80
python -m coverage html
```
