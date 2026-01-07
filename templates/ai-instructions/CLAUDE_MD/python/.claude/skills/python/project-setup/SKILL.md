---
name: python-project-setup
description: Complete Python project setup including directory structure, pyproject.toml template, modern toolchain (uv, ruff), Python 3.12+ features, and project initialization sequence. Use when creating new Python projects, setting up project structure, or configuring Python tooling.
---

# Python Project Setup

## Standard Python Application Structure

```
project_name/
├── .venv/                         # Virtual environment
├── src/                           # Main application source
│   ├── main.py                    # Entry point
│   └── core/                      # Core logic
│       ├── __init__.py
│       ├── [feature_modules].py
│       └── utils/                 # Utilities
├── gui/                           # GUI components (if applicable)
│   ├── __init__.py
│   ├── components/
│   └── assets/                    # Graphics, icons, images
├── tests/                         # Testing suite
│   ├── run_all_tests.py           # Master test runner
│   ├── common.py                  # Shared utilities
│   ├── test_config.py             # Configuration
│   ├── temp/                      # Temporary tests (auto-deleted)
│   └── [feature_tests]/           # Test modules
├── docs/                          # Documentation
├── CHANGELOG.md                   # Version history
├── README.md                      # Project documentation
├── DEVLOG.md                      # Development log
├── pyproject.toml                 # Configuration
├── requirements.txt               # Dependencies (legacy support)
└── .gitignore                     # Git ignore rules
```

## Project Initialization Sequence

1. **Create virtual environment**: `python -m venv .venv`
2. **Activate**: `.venv\Scripts\activate` (Windows) / `source .venv/bin/activate` (Unix)
3. **Create directory structure** as outlined above
4. **Create `.gitignore`** in the project root and list all files, folders, and patterns you want Git to ignore (e.g., virtual environments, caches, logs, OS files, IDE configs, and build artifacts)
5. **Create `pyproject.toml`** matching CHANGELOG version
6. **Create `CHANGELOG.md`** starting with version 0.1.0
7. **Create `README.md`** with version and features
8. **Create `DEVLOG.md`** with initial task list
9. **Create `requirements.txt`** with dependencies (for legacy compatibility)

## pyproject.toml Template

```toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools-scm"]
build-backend = "setuptools.build_meta"

[project]
name = "[project-name]"
version = "[version-from-changelog]"
description = "[project description]"
authors = [{name = "Benjamin Dourthe", email = "benjamin.dourthe@gmail.com"}]
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=7.0", "black>=22.0", "flake8>=4.0", "mypy>=0.950", "isort>=5.10"]

[tool.black]
line-length = 88
target-version = ['py39']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## Modern Python Toolchain (2025)

### Package Management - uv

**uv** is the modern replacement for pip, pip-tools, and virtualenv (10-100x faster):

```bash
# Install uv
pip install uv

# Create project with uv
uv init my-project
cd my-project

# Add dependencies
uv add requests pandas pytest

# Add dev dependencies
uv add --dev black ruff mypy

# Install all dependencies
uv sync

# Run in isolated environment
uv run python src/main.py
uv run pytest
```

**Benefits:**
- 10-100x faster than pip
- Automatic virtual environment management
- Lock files for reproducible builds
- Compatible with pip and requirements.txt

### Code Quality - ruff

**ruff** is the modern all-in-one linter (replaces flake8, isort, pydocstyle, pyupgrade):

```bash
# Install ruff
uv add --dev ruff

# Run linter
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code (can replace black)
ruff format .
```

**pyproject.toml configuration:**
```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
]
ignore = ["E501"]  # Line too long (handled by formatter)

[tool.ruff.lint.isort]
known-first-party = ["src"]
```

### Modern Testing Stack

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.3.4",
    "pytest-cov>=6.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-mock>=3.14.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
    "mutmut>=3.2.0",  # Mutation testing
]
```

### Python 3.12+ Features

**Type Parameter Syntax (PEP 695):**
```python
# Old way (Python < 3.12)
from typing import TypeVar, Generic
T = TypeVar('T')

class Stack(Generic[T]):
    def push(self, item: T) -> None: ...

# New way (Python 3.12+)
class Stack[T]:
    def push(self, item: T) -> None: ...
```

**Enhanced f-string Debugging:**
```python
value = 42
print(f"{value=}")  # Prints: value=42
```

**Better Error Messages:**
Python 3.12+ provides more detailed error messages with suggestions for common mistakes.

### Configuration: pyproject.toml Only

**Modern approach:** Single `pyproject.toml` file (NO requirements.txt, setup.py, or setup.cfg)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-project"
version = "0.1.0"
description = "Modern Python project"
authors = [{name = "Your Name", email = "you@example.com"}]
requires-python = ">=3.12"
dependencies = [
    "requests>=2.32.0",
    "pandas>=2.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.4",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "C4", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "--strict-markers --cov=src --cov-report=html --cov-report=term"
```

### Migration Path

**From old toolchain to modern:**

1. Install uv: `pip install uv`
2. Convert to pyproject.toml: `uv init` (if starting fresh)
3. Add ruff: `uv add --dev ruff`
4. Replace flake8/isort with ruff: Remove old configs
5. Update Python to 3.12+: `uv python install 3.12`
6. Remove requirements.txt: Migrate to `[project.dependencies]`

## .gitignore Template

```gitignore
# Virtual environments
.venv/
venv/
ENV/

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.so

# Distribution / packaging
build/
dist/
*.egg-info/
*.egg

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
*.log
*.tmp
.env
.env.local
```
