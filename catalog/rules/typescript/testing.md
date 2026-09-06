---
title: TypeScript Testing Standards
category: typescript
priority: high
---

# TypeScript Testing Standards

## Framework and Structure

- Use Vitest for unit and integration tests (faster than Jest, native ESM, compatible API).
- Use Playwright for end-to-end tests.
- Organize: `tests/unit/`, `tests/integration/`, `tests/e2e/`.
- Co-locate unit tests with source files when practical: `Button.tsx` and `Button.test.tsx` in the same directory.

## Test Design

- Follow AAA (Arrange, Act, Assert). Keep each test focused on one behavior.
- Name tests as `describe('ComponentOrFunction', () => { it('should <expected behavior> when <condition>', ...) })`.
- Target unit test execution under 50ms each. Slow tests are integration tests.
- Avoid `setTimeout` or `sleep` inside tests. Use fake timers (`vi.useFakeTimers()`) when testing time-dependent logic.

## Mocking

- Mock at the module boundary using `vi.mock('module-path')`. Do not mock internal functions.
- Prefer dependency injection over `vi.spyOn` on private methods.
- Reset all mocks between tests: `afterEach(() => vi.clearAllMocks())`.
- Use `msw` (Mock Service Worker) for HTTP mocking in integration tests; never mock `fetch` or `axios` directly.

## React Component Testing

- Use `@testing-library/react` -- test behavior, not implementation.
- Query elements by accessible roles, labels, and text; avoid `querySelector` and CSS class selectors.
- Use `data-testid` only as a last resort when no accessible query is available.
- Test user interactions with `userEvent` (async), not `fireEvent`.

## Coverage and CI

- Enforce 80% line and branch coverage: `vitest --coverage --coverage.thresholds.lines=80`.
- E2E stability target: >95% pass rate with <5% flakiness threshold.
- Gate PR merges on unit + integration test pass; run E2E on pre-merge to main only.
