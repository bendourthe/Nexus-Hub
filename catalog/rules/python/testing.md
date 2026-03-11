---
title: Python Testing Standards
category: python
priority: high
---

# Python Testing Standards

## Framework and Structure

- Use `pytest` as the test runner. Never use `unittest` for new tests.
- Organize tests to mirror source structure: `tests/unit/`, `tests/integration/`, `tests/e2e/`.
- Name test files `test_<module>.py` and test functions `test_<scenario>_<expected>`.
- Target: 80% line coverage minimum, 70% branch coverage.

## Test Design

- Follow AAA (Arrange, Act, Assert) within each test function.
- One logical assertion per test. Multiple `assert` statements are fine only when they verify the same logical outcome.
- Use `pytest.mark.parametrize` for data-driven tests instead of loops inside test functions.
- Never depend on test execution order. Each test must be fully independent.
- Use `pytest.raises(ExceptionType)` as a context manager to assert exceptions; never `try/except` inside tests.

## Fixtures and Mocking

- Define shared fixtures in `conftest.py` at the appropriate scope level (function, module, session).
- Use `pytest-factory-boy` (Factory Boy) for ORM model creation; avoid raw `Model.objects.create()` in test bodies.
- Mock at the boundary: patch where the object is *used*, not where it is *defined*.
- Prefer `monkeypatch` over `unittest.mock.patch` for patching in pytest tests.
- Use `pytest-freezegun` or `freezegun` to control time in tests involving dates or timeouts.

## Coverage and CI

- Run `pytest --cov=src --cov-report=term-missing -q` to see uncovered lines.
- Gate CI on 80% coverage: `pytest --cov=src --cov-fail-under=80`.
- Separate slow tests (`@pytest.mark.slow`) so the fast suite runs on every commit and slow tests run nightly.
- Never mark a failing test as `@pytest.mark.skip` without a linked issue and a deadline.
