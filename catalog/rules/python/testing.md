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

## Windows Child Processes

- On Windows, a console program started by a process with no console opens a new window that takes keyboard focus. A suite that starts hundreds of children from an agent, an IDE test runner or a detached helper makes the machine unusable until it ends, so every process a test (or a helper the tests call) starts must be launched without a window.
- Give the suite one guard: a top-level `conftest.py` that adds `subprocess.CREATE_NO_WINDOW` to every `subprocess.Popen` on Windows unless the call explicitly asks for `DETACHED_PROCESS` or `CREATE_NEW_CONSOLE`. A child started that way gets a console with no window, and its own children inherit it.
- Do not pass `DETACHED_PROCESS` to simulate "no terminal": the detached child has no console, so every git, bash or PowerShell it starts opens a window. Use `stdin=subprocess.DEVNULL` with `CREATE_NO_WINDOW` instead.
- A launch that must detach or open its own console is the exception: mark it with a `nexus: console-window-ok <reason>` comment on the line or the line above. Nexus-Hub's `console-window-guard` hook blocks a Windows test run while an unmarked unsafe launch remains.

## Coverage and CI

- Run `pytest --cov=src --cov-report=term-missing -q` to see uncovered lines.
- Gate CI on 80% coverage: `pytest --cov=src --cov-fail-under=80`.
- Separate slow tests (`@pytest.mark.slow`) so the fast suite runs on every commit and slow tests run nightly.
- Never mark a failing test as `@pytest.mark.skip` without a linked issue and a deadline.
