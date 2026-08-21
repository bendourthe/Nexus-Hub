# Testing Patterns Reference

Quick-reference checklist for test design decisions. Use during code review, TDD setup, or when evaluating test coverage quality.

---

## Test Pyramid Ratios

| Layer | Target % | Characteristics |
|---|---|---|
| Unit | ~70% | Fast (<50ms), isolated, no I/O, pure logic |
| Integration | ~20% | Real dependencies (DB, filesystem), controlled scope |
| E2E | ~10% | Full user flows, slow, run pre-merge not on every commit |

Invert this pyramid = slow, brittle test suite. Flatten it = gaps in edge case coverage.

---

## Unit Test Checklist

- [ ] Test one behavior per test function (single logical assertion)
- [ ] Name: `test_<function>_<condition>_<expected>` (Python) or `it('should <X> when <Y>')` (JS)
- [ ] Follow AAA: Arrange, Act, Assert -- in that order, clearly separated
- [ ] No shared mutable state between tests; each test initializes its own data
- [ ] Use parameterize/table-driven patterns for multiple input/output combinations
- [ ] Mock at the boundary (where code calls external systems), not at internal function calls
- [ ] Verify both the happy path and at least 2 failure/edge cases per function
- [ ] Tests pass in any order (no order-dependent side effects)
- [ ] Target: <50ms execution per unit test

---

## Integration Test Checklist

- [ ] Uses real external dependencies (actual DB, real filesystem) not mocks
- [ ] Each test cleans up its own state (transaction rollback, temp directory cleanup)
- [ ] Isolated from other tests -- no shared database rows or files
- [ ] Tagged separately from unit tests (`@pytest.mark.integration`, `//go:build integration`)
- [ ] Uses `testcontainers` (or equivalent) for services that are impractical to run natively
- [ ] Verifies the contract between components (input/output shape), not internal implementation

---

## E2E Test Checklist

- [ ] Tests complete user flows from the user's perspective (not implementation details)
- [ ] Uses page objects or screen objects to isolate selector fragility
- [ ] Avoids `sleep`; uses explicit waits for async state changes
- [ ] Runs against a staging environment, not production
- [ ] Flakiness rate < 5% -- any flakier test is quarantined and fixed
- [ ] Covers critical paths: auth, primary CRUD, payment, error recovery

---

## Coverage Quality Checklist

- [ ] Line coverage ≥ 80% (gate CI on this)
- [ ] Branch coverage ≥ 70% (catches if/else gaps)
- [ ] All public API surface has at least one test
- [ ] Boundary values are tested: empty input, null, max length, zero, negative
- [ ] Error/exception paths are tested, not just happy paths
- [ ] No tests that only test framework behavior (testing `pytest` works is not a test)

---

## Test Smell Detector

| Smell | Why it matters | Fix |
|---|---|---|
| Test depends on test order | Hidden shared state; breaks parallelization | Isolate state per test |
| Setup > 10 lines | Test is over-specified; coupling to internals | Extract fixture; mock at a higher level |
| Multiple unrelated asserts | Test does too much; hard to diagnose failures | Split into focused tests |
| Mocking 5+ functions | Test is too integrated; not a unit test | Push test to integration layer |
| `time.sleep()` in tests | Non-deterministic; masks real timing bugs | Use fake timers or explicit waits |
| Testing `print()` output | Tests implementation, not behavior | Test side effects or return values |
| `assert True` / `assert 1 == 1` | Passes unconditionally; no signal | Write a real assertion |

---

## Anti-Patterns to Avoid

- **Ice cream cone**: More E2E than unit tests -- slow feedback loop
- **Testing the framework**: Tests that only verify `React.render()` or `ORM.save()` work
- **Assertion roulette**: Multiple asserts with no message -- impossible to know which failed
- **Mystery guest**: Test data from a distant fixture file with no explanation
- **Liar test**: Test name says "returns error on invalid input" but actually tests success case
- **Flaky test left in CI**: A skipped flaky test is technical debt with interest

---

## Quick References

- **Python**: `pytest`, `pytest-cov`, `factory_boy`, `freezegun`, `testcontainers-python`
- **JavaScript/TypeScript**: `vitest`, `@testing-library/react`, `msw`, `playwright`
- **Go**: `testing`, `testify`, `testcontainers-go`, `-race` flag
- **Java**: `JUnit 5`, `Mockito`, `Testcontainers`, `AssertJ`

Related skills: `unit-tests`, `integration-test-generator`, `e2e-testing-automation`, `test-driven-development`, `mutation-testing`
