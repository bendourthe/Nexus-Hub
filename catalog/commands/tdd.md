---
description: Execute test-driven development using the RED-GREEN-REFACTOR cycle with an 80% coverage gate. Guides the full TDD workflow for a feature or bug fix, enforcing discipline at each phase transition.
---

# TDD Command

Execute test-driven development for the described feature or bug fix. This command enforces the strict RED → GREEN → REFACTOR → REPEAT cycle. No implementation code is written before a failing test exists.

---

## Step 1: Understand the Target Behavior

Before writing any code or tests:

1. Restate the feature or bug fix in one sentence as a behavioral assertion: "Given X, when Y, then Z."
2. Identify the unit under test (function, class, module, or API endpoint).
3. List the test cases to implement, ordered from simplest to most complex:
   - Happy path (expected input, expected output)
   - Edge cases (empty, null, min, max)
   - Error paths (invalid input, external failure)

If the unit under test does not exist yet, confirm the function signature/interface before writing the first test.

---

## Step 2: RED Phase — Write a Failing Test

Write the first (simplest) failing test:

- The test must fail because the behavior does not yet exist, not because of a syntax error or import failure.
- The test name must read as a sentence: `test_login_fails_when_password_is_expired` or `it('should return 401 when token is missing')`.
- Assert on the outcome (return value, state change, thrown exception) — not on internal implementation details.
- Keep the test under 20 lines.

Run the test and confirm:
- Exit code is non-zero (test fails)
- The failure message matches the expected missing behavior

**Do not proceed until the test is RED for the right reason.**

---

## Step 3: GREEN Phase — Make the Test Pass

Write the minimum production code to make the failing test pass:

- "Minimum" is literal: no abstractions, no handling of cases not yet tested, no premature generalization.
- If the GREEN implementation feels wrong or dirty, that is fine — REFACTOR will clean it.
- Run the full test suite: all previously passing tests must still pass.

**Do not proceed until all tests are GREEN.**

---

## Step 4: REFACTOR Phase — Improve Without Breaking

With all tests green, improve the code:

- Remove duplication (both in tests and production code)
- Clarify variable and function names
- Simplify complex conditional logic
- Extract well-named helper functions where appropriate

Rules during REFACTOR:
- Run the test suite after every change — remain GREEN throughout
- Do not add new behavior in REFACTOR
- Commit after a successful refactor: `git commit -m "refactor: <what improved>"`

---

## Step 5: Coverage Gate

After each RED-GREEN-REFACTOR cycle, check coverage:

```bash
# Python
pytest --cov=src --cov-report=term-missing -q

# TypeScript / Node.js
npx vitest run --coverage

# Go
go test -coverprofile=coverage.out ./... && go tool cover -func=coverage.out

# Rust
cargo tarpaulin --out Stdout
```

**Minimum thresholds:**
- Line coverage: **80%**
- Branch coverage: **70%**

If below threshold: add tests for uncovered paths before starting the next feature.

---

## Step 6: REPEAT

Return to Step 2 for the next test case from the list produced in Step 1.

Continue until all planned test cases have been implemented and the coverage gate passes.

---

## Completion Criteria

The `/tdd` session is complete when:
1. All planned test cases are implemented and passing
2. Coverage gate is satisfied (80% lines, 70% branches)
3. No failing tests exist in the suite

Final step: invoke the `code-reviewer` agent for a review pass before merge:
```
Use the code-reviewer agent to review the changes from this TDD session.
```

---

## Quick Reference

| Phase | What You Do | Exit Condition |
|-------|------------|----------------|
| RED | Write a failing test | Test fails for the right reason |
| GREEN | Write minimum implementation | All tests pass |
| REFACTOR | Clean up code and tests | All tests still pass; code is clearer |
| COVERAGE | Check thresholds | ≥80% lines, ≥70% branches |
| REPEAT | Next test case | All planned cases done |
