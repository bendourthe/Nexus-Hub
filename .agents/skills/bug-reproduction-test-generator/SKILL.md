---
name: bug-reproduction-test-generator
description: Create minimal reproduction tests from bug reports and error descriptions. Use when writing failing tests from bug reports, creating minimal reproductions, isolating test cases, or building regression test suites from production incidents.
summary_l0: "Create minimal reproduction tests from bug reports and error descriptions"
overview_l1: "This skill transforms bug reports, error descriptions, and production incident logs into minimal, isolated reproduction tests that reliably demonstrate the defect. Use it when converting natural-language bug reports into failing test cases, creating minimal reproductions from complex failures, isolating bugs from surrounding context, generating regression tests from production incidents, building tests that fail before a fix and pass after, or setting up exact conditions for intermittent failures. Key capabilities include bug report parsing and condition extraction, test case minimization, environment condition setup, intermittent failure isolation, regression test scaffolding, and before/after validation patterns. The expected output is a minimal, self-contained test file that reliably reproduces the bug with clear assertions and setup instructions. Trigger phrases: write a reproduction test, create a failing test, reproduce this bug, minimal reproduction, write a test for this bug report, create regression test, isolate the failure."
---

# Bug Reproduction Test Generator

Transform bug reports, error descriptions, and production incident logs into minimal, isolated reproduction tests that reliably demonstrate the defect. These tests serve as the foundation for debugging, patch validation, and long-term regression prevention.

## When to Use This Skill

Use this skill when you need to:

- Convert a natural-language bug report into a failing test case
- Create a minimal reproduction from a complex failure scenario
- Isolate a bug from its surrounding context to simplify debugging
- Generate regression tests from production incidents or customer-reported issues
- Build a test that reliably fails before a fix and passes after it
- Reduce a large, complex test to the smallest case that still triggers the bug
- Set up the exact environment conditions needed to reproduce an intermittent failure

**Trigger phrases**: "write a reproduction test", "create a failing test", "reproduce this bug", "minimal reproduction", "write a test for this bug report", "create regression test", "isolate the failure", "test case from bug report"

## What This Skill Does

### Methodology Overview

The reproduction test generation process follows five stages:

1. **Bug Report Parsing** -- Extract the essential facts from the report: inputs, expected output, actual output, error messages, and environment constraints.
2. **Environment Setup** -- Determine and configure the minimal environment needed to reproduce the bug (dependencies, database state, configuration, mocks).
3. **Minimal Reproduction Construction** -- Build the smallest possible test that triggers the defect, removing all unnecessary setup, data, and code paths.
4. **Assertion Generation** -- Write assertions that capture both the buggy behavior (to confirm the test fails before the fix) and the expected behavior (to confirm the test passes after the fix).
5. **Test Isolation** -- Ensure the test is independent of external state, execution order, and other tests so it can run reliably in any environment.

### Reproduction Quality Criteria

| Criterion | Description |
|-----------|-------------|
| Minimality | The test includes only the code and data necessary to trigger the bug |
| Reliability | The test fails 100% of the time on the buggy code (not flaky) |
| Isolation | The test does not depend on external services, file system state, or other tests |
| Clarity | The test clearly documents what the bug is and what the expected behavior should be |
| Speed | The test runs quickly (under 1 second for unit-level reproductions) |

## Instructions

### Step 1: Parse the Bug Report

Full walkthrough: [step-1-parse-the-bug-report.md](references/step-1-parse-the-bug-report.md) (load this step when you reach it).

### Step 2: Set Up the Minimal Environment

Full walkthrough: [step-2-set-up-the-minimal-environment.md](references/step-2-set-up-the-minimal-environment.md) (load this step when you reach it).

### Step 3: Generate the Minimal Reproduction Test

Full walkthrough: [step-3-generate-the-minimal-reproduction-test.md](references/step-3-generate-the-minimal-reproduction-test.md) (load this step when you reach it).

### Step 4: Apply Test Minimization

Full walkthrough: [step-4-apply-test-minimization.md](references/step-4-apply-test-minimization.md) (load this step when you reach it).

### Step 5: Ensure Test Isolation

Full walkthrough: [step-5-ensure-test-isolation.md](references/step-5-ensure-test-isolation.md) (load this step when you reach it).

## Best Practices

- Write the reproduction test before attempting any fix. This ensures you have a reliable way to confirm the bug exists and to validate the fix.
- Make the test name descriptive and include the bug ID. Future developers searching for the test should be able to find it from the bug report and vice versa.
- Include the bug report details (expected behavior, actual behavior) as comments in the test. The test should serve as living documentation of the defect.
- Use the Arrange-Act-Assert pattern consistently. Each section should be clearly labeled and separated so readers can quickly understand the test structure.
- Prefer in-memory fixtures over file system or database fixtures. In-memory setup is faster, more portable, and less likely to cause test pollution.
- Minimize the test aggressively. Every line of setup code that is not strictly necessary to reproduce the bug is noise that makes the test harder to understand and maintain.
- Verify that the test fails before the fix and passes after it. A reproduction test that passes even without the fix is useless.
- Run the reproduction test in isolation (not as part of a larger suite) to confirm it does not depend on side effects from other tests.
- Tag reproduction tests with the bug ID so they can be easily filtered and run as a group (for example, `@pytest.mark.bug_123` or `@Tag("BUG-123")`).

## Common Pitfalls

- **Writing a test that passes without the fix.** If the test does not actually fail on the buggy code, it cannot serve as a reproduction. Always verify the test against the unfixed code first.
- **Including unnecessary setup.** A reproduction test with 50 lines of database setup for a bug that only requires two input parameters is misleading. Minimize ruthlessly.
- **Depending on external state.** A reproduction test that requires a running database, a specific file on disk, or a network service is fragile. Mock or stub external dependencies.
- **Making the test order-dependent.** If the reproduction test only fails when run after another specific test, it is not a true reproduction. Ensure it fails when run in isolation.
- **Forgetting to document what the test reproduces.** A test named `test_bug_fix` with no comments tells future developers nothing. Include the bug ID, the expected behavior, and the actual behavior.
- **Not testing the negative case.** After the fix is applied, verify that the test now passes. Also verify that removing the fix causes the test to fail again. This round-trip confirms the test is genuinely tied to the bug.
- **Reproduction tests that are too slow.** A reproduction test that takes 30 seconds to run will be skipped or ignored. Keep reproduction tests fast (under 1 second for unit-level, under 10 seconds for integration-level).
- **Hardcoding environment-specific values.** File paths, port numbers, and hostnames that work on your machine will fail in CI. Use environment variables, temporary directories, and dynamic port allocation.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I can see the bug in the code, I do not need to write a reproduction first" | Without a test that fails on the unfixed code you have no way to prove the fix worked; many 'fixes' address a symptom while the reproduction would have shown the bug still triggers on a second input. |
| "The reproduction needs the full production setup to be realistic" | A reproduction that requires the whole database and service mesh is slow and fragile and gets skipped; minimizing to the two inputs that trigger the defect makes the test fast, portable, and the actual root cause obvious. |
| "The test passes now, so the bug is reproduced" | A reproduction test that passes on the buggy code reproduces nothing; it must fail before the fix and pass after, or it is asserting the wrong condition. |
| "It only fails when run after the integration suite, that is close enough" | An order-dependent test is not a reproduction of the reported bug; it is reproducing test pollution, and it will give false confidence when the real bug is still live in isolation. |

## Verification

- [ ] The generated test fails on the unfixed code (the bug is genuinely reproduced)
- [ ] The same test passes once the fix is applied, and fails again if the fix is reverted
- [ ] The test runs in isolation without depending on other tests, network, or pre-existing filesystem state
- [ ] The test is minimized to only the setup and inputs needed to trigger the defect
- [ ] The test documents the bug ID, expected behavior, and actual behavior in comments
- [ ] Unit-level reproductions complete in under 1 second

## Related Skills

- [[bug-localization]] -- requires the deterministic reproduction this skill produces before localizing
- [[bug-to-patch-generator]] -- consumes the failing test as the gate its patch must turn green
- [[regression-root-cause-analyzer]] -- uses the reproduction as the bisect test command
- [[unit-tests]] -- general unit-test authoring patterns the reproduction follows
- [[test-driven-development]] -- the red-green-refactor cycle this failing-test-first approach mirrors
