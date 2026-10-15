---
name: false-confidence-test-audit
description: Audit an existing test suite for FALSE-CONFIDENCE tests - tests that pass regardless of whether the code under test is correct, so a green suite hides real defects. Make sure to use this skill whenever the user says "audit my tests", "are these tests actually testing anything", "do these tests give false confidence", "tautological tests", "the tests pass but the code is broken", "check test quality", "these tests look fake", or otherwise suspects the safety net is hollow, even if they never say "false confidence". SKIP, do NOT use for, generating new tests (use unit-tests / test-cases), running a compute-heavy mutation pass to prove weakness (use mutation-testing), or measuring line coverage (use code-coverage).
summary_l0: "Audit existing tests for false confidence: tests that pass regardless of correctness"
overview_l1: "This skill audits an existing test suite for false-confidence tests - tests that stay green whether or not the code under test is correct, so a passing run gives a false sense of safety. It teaches a fast, read-the-assertions audit distinct from the compute-heavy mutation pass: enumerate the suite, identify each test's real subject and the behavior its name claims, then classify every test REAL, WEAK, or FALSE-CONFIDENCE against a concrete anti-pattern catalog (tautological assertions, asserting on a mock instead of the subject, the subject fully mocked away, no assertion at all, catch-and-pass on any exception, rubber-stamped snapshots). For each false-confidence test it proposes the corrected assertion or a real subject invocation, and optionally verifies the fix by mutating the subject and confirming the test now fails. The output is a classified report plus concrete repairs. Trigger phrases: audit my tests, false confidence, tautological tests, tests pass but code is broken, fake tests, test quality audit."
---

# False-Confidence Test Audit

Find the tests that pass no matter what the code does. A suite can be green, have high line coverage, and still catch nothing - because the assertions are tautological, aimed at a mock, or absent. This skill audits an existing suite for that specific failure and repairs it, so the green checkmark actually means the behavior is protected.

## When to Use This Skill

- A test suite is green but a real bug shipped anyway, and you suspect the tests never exercised the broken path.
- You inherited a suite and want to know how much of it is real protection versus theater.
- Periodically, as a maintenance sweep, to stop false-confidence tests from accumulating.
- After an AI-assisted test-generation run, to catch generated tests that assert on the wrong thing.

**Trigger phrases**: "audit my tests", "are these tests actually testing anything", "false confidence", "tautological tests", "tests pass but the code is broken", "fake tests", "check test quality".

### When NOT to Use

| Want to ... | Use this instead |
|---|---|
| Generate new tests for uncovered code | `unit-tests` / `test-cases` |
| Prove weakness by mutating the code (compute-heavy) | `mutation-testing` |
| Measure which lines execute | `code-coverage` |
| Diagnose a test that fails intermittently | `flaky-test-detector` |

## How this differs from mutation testing

Both target weak tests, from opposite ends. `mutation-testing` *proves* weakness empirically: it mutates the source, re-runs the suite, and reports mutants that survived - thorough, but slow and deliberate, usually a scheduled CI job. This skill is the fast, cheap complement: it *reads* the test bodies and classifies them by inspection, so it can run in seconds on a changed file during review. Use this audit as the frequent first pass; escalate to `mutation-testing` when you need empirical proof on critical logic.

## The false-confidence catalog

Each row is an anti-pattern, why it gives false confidence, and how to detect it.

| Anti-pattern | Why it passes regardless | Detection heuristic |
|---|---|---|
| Tautological assertion | Asserts something always true (`assert True`, `assert x == x`, `expect(1).toBe(1)`) | The asserted expression does not depend on the subject's output |
| Assertion on a mock | Asserts the mock returned what it was configured to return, not what the subject computed | The value asserted traces back to a `mock.return_value` / stub, not a real call |
| Subject fully mocked away | The unit under test is itself patched, so the test exercises the mock | The subject's own module/function appears in the patch/mock setup |
| No assertion | Runs the code, asserts nothing; only fails on an unhandled exception | The test body has zero assert / expect statements |
| Catch-and-pass | Wraps the subject in try/except (or try/catch) and passes on any error | An exception handler with `pass` / empty body, or a test that "passes" by swallowing failure |
| Over-broad exception match | `pytest.raises(Exception)` / `toThrow()` with no type or message | The expected error is unconstrained, so any failure counts as success |
| Rubber-stamped snapshot | Snapshot committed without review; re-baselined blindly on change | Snapshot updated in the same commit that changed behavior, with no other assertion |
| Frozen-clock-only truth | Asserts a value that is only correct because time/randomness was pinned to make it so | The assertion encodes the fixture's frozen value, not the computed relationship |

## Instructions

1. **Enumerate the suite.** List the test files and, per file, the individual test functions/cases in scope (a changed file, a module, or the whole suite as requested).
2. **Establish intent per test.** For each test, identify (a) the real subject under test (the function/class/endpoint whose behavior is claimed) and (b) the behavior the test name asserts (e.g. `test_discount_rejects_negative_rate` claims rejection of a negative rate).
3. **Read the assertions against the catalog.** Classify each test:
    - **REAL** - at least one assertion depends on the subject's actual output and would fail if the subject were wrong.
    - **WEAK** - asserts something true but under-specified (type-only, non-null, "greater than zero" where an exact value is knowable); it would let some mutations through.
    - **FALSE-CONFIDENCE** - matches a catalog row; it passes regardless of correctness.
4. **Trace mocked values.** Where a test uses mocks, confirm the assertion is on the SUBJECT's output, not on a value the test itself configured into a mock. If the subject is patched, flag it.
5. **Propose a repair per non-REAL test.** For WEAK: tighten to the exact expected value and add the boundary/error cases the name implies. For FALSE-CONFIDENCE: replace the tautology with a real assertion, unmock the subject, add the missing assertion, or narrow the exception to a type + message.
6. **Optionally verify the repair.** Mutate the subject (flip a comparison, change a return) and confirm the repaired test now FAILS, then restore the subject and confirm it PASSES. This is the binary proof the test is no longer false-confidence. (This is a targeted, single-mutation check, not a full `mutation-testing` sweep.)
7. **Report.** Emit a table of tests with their classification and the specific reason, then the proposed repairs. Apply the repairs only when asked; never silently rewrite tests.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The suite is green and coverage is 90 percent, so the tests are fine." | Coverage proves the line ran; it does not prove an assertion would catch a wrong result. A tautological test on a covered line is exactly the failure this audit exists to find. |
| "It asserts the function returned something, that is good enough." | `assert result is not None` survives almost every real defect. A test that cannot distinguish the correct output from a wrong one is not protecting the behavior its name claims. |
| "We mock the dependency and assert the mock was called, so it is tested." | Asserting the mock was called tests the test's own setup, not the subject's logic. If the subject computes the wrong thing before calling the dependency, the test still passes. |
| "The snapshot matches, so the output is correct." | A snapshot re-baselined in the same change that altered behavior asserts nothing - it just records whatever the code now does. Without an independent assertion it is a rubber stamp. |
| "This test has always passed, so it must be solid." | A test that has never failed may be one that cannot fail. Longevity is not strength; the single-mutation check in step 6 is the actual evidence. |

## Verification

- [ ] Every test in scope is classified REAL / WEAK / FALSE-CONFIDENCE with a specific catalog reason (not "looks fine").
- [ ] Each FALSE-CONFIDENCE finding names the exact line/assertion and the anti-pattern it matches.
- [ ] Each proposed repair is concrete (the corrected assertion or the unmocked subject call), not "add more tests".
- [ ] For at least the critical repairs, the single-mutation check was run: the repaired test fails against the mutated subject and passes against the original.
- [ ] The report distinguishes this fast audit from a full `mutation-testing` sweep and recommends escalation where empirical proof is warranted.

## Related Skills

- [[mutation-testing]] -- proves test weakness empirically by mutating code; this audit is the fast read-the-assertions complement, escalate to it for critical logic.
- [[testing-review]] -- broader test-strategy and coverage assessment; this skill is the narrow assertion-quality lens within it.
- [[flaky-test-detector]] -- targets tests that fail non-deterministically; orthogonal to tests that pass non-informatively.
- [[unit-tests]] -- generates the replacement tests once a false-confidence test is condemned.
- [[edge-case-generator]] -- supplies the boundary and error cases a WEAK happy-path-only test is missing.

---

**Version**: 1.0.0
**Last Updated**: July 2026
