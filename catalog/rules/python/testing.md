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
- Use the shared subprocess default in product entry points and every pytest root. On Windows it must add CREATE_NO_WINDOW to every child, including positional creationflags, and reject detached or new-console requests.
- Do not pass `DETACHED_PROCESS` to simulate "no terminal": the detached child has no console, so every git, bash or PowerShell it starts opens a window. Use `stdin=subprocess.DEVNULL` with `CREATE_NO_WINDOW` instead.
- A launch that must detach or open its own console is the exception: mark it with a `nexus: console-window-ok <reason>` comment on its launch line. Nexus-Hub's `console-window-guard` hook blocks a Windows test, installer, or build command while an unmarked unsafe launch remains.

## Coverage and CI

- Run `pytest --cov=src --cov-report=term-missing -q` to see uncovered lines.
- Gate CI on 80% coverage: `pytest --cov=src --cov-fail-under=80`.
- Separate slow tests (`@pytest.mark.slow`) so the fast suite runs on every commit and slow tests run nightly.
- Never mark a failing test as `@pytest.mark.skip` without a linked issue and a deadline.

## Windows Process Launches

On Windows, start every console child without a window: use one shared Python subprocess default with CREATE_NO_WINDOW, Node child_process options with windowsHide: true, or PowerShell ProcessStartInfo with UseShellExecute = $false and CreateNoWindow = $true. Prefer direct or in-process calls; Start-Process must use -WindowStyle Hidden (do not combine it with -NoNewWindow). Route .cmd shims through the same hidden launcher. Apply this to product code, tests, installers, builds, and agent helpers. Never use DETACHED_PROCESS or CREATE_NEW_CONSOLE for console programs. A deliberate exception needs nexus: console-window-ok <reason> on its launch line. Run the console-window-guard before test, installer, and build commands; use targeted checks for targeted changes.
