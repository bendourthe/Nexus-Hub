---
title: Python Code Style
category: python
priority: high
---

# Python Code Style Rules

## Formatting and Linting

- Use `ruff` for both linting and formatting (replaces flake8, isort, black). Run `ruff check . && ruff format .` before every commit.
- Line length: 88 characters (ruff/black default).
- Use double quotes for strings unless the string itself contains double quotes.
- Sort imports with `ruff` (isort-compatible): stdlib → third-party → local, each group separated by a blank line.

## Type Annotations

- Annotate all function signatures -- parameters and return types -- without exception.
- Use `from __future__ import annotations` at the top of every module to enable postponed evaluation (Python 3.10+ style unions work everywhere).
- Prefer `X | Y` union syntax over `Optional[X]` or `Union[X, Y]`.
- Use `TypeVar` and `Generic` for reusable typed containers; avoid `Any` unless wrapping untyped third-party code.
- Run `mypy --strict` (or `pyright`) in CI. Zero type errors is the target state.

## Naming Conventions

- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE` at module level
- Private members: single leading underscore `_name` (double underscore only for deliberate name mangling)
- Test functions: `test_<what>_<condition>` (e.g., `test_login_with_expired_token`)

## Functions and Classes

- Keep functions under 30 lines. If longer, extract a helper with a descriptive name.
- One public class per module where possible; private helpers can share the module.
- Use `@dataclass` or Pydantic `BaseModel` for data-carrying classes instead of dicts.
- Prefer composition over inheritance. Inherit only from abstract base classes or well-defined protocols.
- Do not use mutable default arguments (`def f(x=[])` is a bug -- use `None` and initialize inside).

## Error Handling

- Catch specific exceptions, never bare `except:` or `except Exception:` without re-raising or logging.
- Use custom exception classes that inherit from a project-level base exception.
- Log exceptions with `logger.exception("message")` to capture the traceback automatically.
- Never suppress `KeyboardInterrupt` or `SystemExit`.
