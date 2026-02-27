## Python Conventions

**Tooling**:
- **Package Manager**: `uv` for 10-100x faster package management (fallback: `pip` with `venv`)
- **Linter/Formatter**: `ruff` (replaces flake8, isort, black)
- **Configuration**: Single `pyproject.toml` (avoid `requirements.txt` or `setup.py`)
- **Target**: Python 3.12+ (new type parameter syntax, better f-strings)

**Naming**: `snake_case` for functions/variables, `PascalCase` for classes

**Code Patterns**:
- Type hints on all public functions
- Return early (guard clauses)
- `pathlib` for all file path operations
- Context managers for resource disposal
- `async/await` for I/O-bound operations

**Imports** (order): standard library, third-party, local application (alphabetical within each)

**Testing**: `pytest` with `tests/` directory. Use fixtures for setup/teardown.

```python
def test_add():
    assert add(2, 3) == 5
```
