# Python Code Style

## Applies to

All Python source and test files maintained by Example Organization.

## Requirements

- Use type annotations on public functions and on internal functions whose contracts are not obvious from local context.
- Prefer `pathlib.Path` over string-built filesystem paths.
- Return structured validation results for expected user-input failures; reserve exceptions for unexpected program failures.
- Keep tests deterministic and avoid time-based sleeps.
