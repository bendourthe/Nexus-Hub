---
name: semantic-bug-detector
description: Detect semantic bugs (logic errors, incorrect assumptions, race conditions) beyond syntactic checks. Use when reviewing code for logic errors, identifying off-by-one mistakes, finding null safety issues, detecting race conditions, or verifying invariants.
summary_l0: "Detect logic errors, race conditions, and invariant violations beyond syntax checks"
overview_l1: "This skill detects semantic bugs that pass compilation and linting but produce incorrect behavior at runtime, including logic flow analysis, type confusion detection, off-by-one errors, null safety analysis, race condition identification, and invariant violation detection. Use it when reviewing code for logic errors compilers cannot catch, finding off-by-one errors in loops and boundaries, detecting null/undefined safety issues, finding type-confusion bugs from silent coercion, identifying race conditions in concurrent code, or verifying invariants (preconditions, postconditions, loop invariants). Key capabilities include control flow path analysis, boundary condition verification, null propagation tracking, type coercion detection, concurrency hazard identification, and invariant assertion generation. The expected output is a categorized bug report with location, severity, explanation, and suggested fix for each detected semantic issue. Trigger phrases: check for logic errors, find semantic bugs, detect off-by-one, null safety review, race condition detection, find logic flaws, check invariants, semantic analysis, detect concurrency bugs."
---

# Semantic Bug Detector

Detect semantic bugs that pass compilation and linting but produce incorrect behavior at runtime. This skill covers logic flow analysis, type confusion detection, off-by-one error detection, null safety analysis, race condition identification, and invariant violation detection.

## When to Use This Skill

Use this skill when you need to:

- Review code for logic errors that compilers and linters cannot catch
- Identify off-by-one errors in loops, array accesses, and boundary conditions
- Detect null/undefined safety issues before they cause runtime crashes
- Find type confusion bugs where values are silently coerced or misinterpreted
- Identify race conditions and concurrency bugs in multi-threaded or async code
- Verify that code invariants (preconditions, postconditions, loop invariants) are maintained
- Audit code for incorrect assumptions about data formats, ranges, or ordering

**Trigger phrases**: "check for logic errors", "find semantic bugs", "detect off-by-one", "null safety review", "race condition detection", "find logic flaws", "check invariants", "semantic analysis", "detect concurrency bugs"

## What This Skill Does

### Methodology Overview

Semantic bug detection operates at a higher level than syntax checking. While compilers verify that code is well-formed and linters check style, semantic analysis verifies that code does what the developer intended. This skill applies six complementary detection techniques:

1. **Logic Flow Analysis** -- Trace the logical paths through code to find unreachable branches, inverted conditions, missing cases, and incorrect boolean logic.
2. **Type Confusion Detection** -- Identify cases where values of one type are silently treated as another (string-to-number coercion, lossy casts, enum misuse).
3. **Off-by-One Detection** -- Examine loop bounds, array indices, range calculations, and boundary conditions for fencepost errors.
4. **Null Safety Analysis** -- Find code paths where null or undefined values can reach operations that require non-null values.
5. **Race Condition Identification** -- Detect shared mutable state accessed without synchronization, time-of-check-to-time-of-use (TOCTOU) patterns, and async ordering issues.
6. **Invariant Violation Detection** -- Verify that preconditions, postconditions, and loop invariants hold across all code paths.

### Bug Category Reference

| Category | Severity | Detection Difficulty | Common Languages |
|----------|----------|---------------------|-----------------|
| Off-by-one | Medium | Medium | All |
| Null dereference | High | Low-Medium | Java, C#, JavaScript, Python |
| Type confusion | Medium-High | High | JavaScript, Python |
| Race condition | Critical | Very High | All (concurrent code) |
| Logic inversion | Medium | Medium | All |
| Invariant violation | High | High | All |
| Integer overflow | High | Medium | C, C++, Java |
| Incorrect comparison | Medium | Low | JavaScript, Python |

## Instructions

### Step 1: Logic Flow Analysis

Full walkthrough: [step-1-logic-flow-analysis.md](references/step-1-logic-flow-analysis.md) (load this step when you reach it).

### Step 2: Off-by-One Detection

Full walkthrough: [step-2-off-by-one-detection.md](references/step-2-off-by-one-detection.md) (load this step when you reach it).

### Step 3: Null Safety Analysis

Full walkthrough: [step-3-null-safety-analysis.md](references/step-3-null-safety-analysis.md) (load this step when you reach it).

### Step 4: Race Condition Identification

Full walkthrough: [step-4-race-condition-identification.md](references/step-4-race-condition-identification.md) (load this step when you reach it).

### Step 5: Invariant Violation Detection

Full walkthrough: [step-5-invariant-violation-detection.md](references/step-5-invariant-violation-detection.md) (load this step when you reach it).

### Step 6: Combine Detectors into a Unified Analysis

Full walkthrough: [step-6-combine-detectors-into-a-unified-analysis.md](references/step-6-combine-detectors-into-a-unified-analysis.md) (load this step when you reach it).

## Best Practices

- Run semantic analysis on every pull request, not just when bugs are suspected. Many semantic bugs are easier to prevent than to find after the fact.
- Combine automated detection with manual review. Automated tools catch common patterns, but experienced developers catch subtle logic errors that no tool can detect.
- Use precondition and postcondition checks in development and testing builds, but consider disabling them in production for performance-sensitive paths.
- Document invariants explicitly in code comments or assertion statements. An invariant that exists only in a developer's mind will eventually be violated.
- Pay special attention to boundary conditions: empty collections, zero values, maximum values, null inputs, and single-element collections. These are where off-by-one and null safety bugs cluster.
- For race condition detection, prefer designs that eliminate shared mutable state (immutable data, message passing, actor model) over designs that rely on correct synchronization.
- When reviewing code for semantic bugs, read the code as if you were an adversarial tester trying to break it. Ask "what happens if this value is null?" and "what happens if this collection is empty?" at every step.
- Maintain a catalog of semantic bug patterns specific to your codebase and language. Each time a semantic bug is found and fixed, add its pattern to the catalog so it can be detected automatically in the future.

## Common Pitfalls

- **Assuming the compiler catches logic errors.** Compilers verify syntax and type safety (in statically typed languages), not whether your algorithm is correct. A function that compiles and runs without errors can still produce wrong results.
- **Ignoring implicit type coercion.** In JavaScript, `"5" + 3` yields `"53"` (string concatenation), not `8`. In Python, `True + 1` yields `2`. These coercions are language-defined behavior, not errors, but they are a rich source of semantic bugs.
- **Treating absence of errors as correctness.** A function that silently returns a wrong value is harder to detect than one that throws an exception. Prefer "fail loudly" designs with explicit assertions over silent fallbacks.
- **Overlooking edge cases in boolean logic.** De Morgan's laws (`not (A and B)` equals `not A or not B`) are frequently applied incorrectly. Complex conditions with mixed `and`/`or` operators are prone to precedence errors.
- **Underestimating race condition complexity.** Race conditions can be extremely difficult to reproduce because they depend on timing. A test that passes 99% of the time can still harbor a critical race condition. Use race condition detectors, stress tests, and formal analysis tools (such as ThreadSanitizer) rather than relying on test pass rates.
- **Relying on a single detection technique.** No single technique catches all semantic bugs. Logic flow analysis misses race conditions; null safety analysis misses off-by-one errors. Use all available techniques together for comprehensive coverage.
- **Not verifying assumptions about external APIs.** If your code assumes that an API returns a non-null value but the documentation says it may return null, you have a semantic bug waiting to happen. Always verify your assumptions against documentation and test with edge-case inputs.
- **Assuming that "it works on my machine" means correctness.** Semantic bugs often depend on data, timing, or environment. A function that works correctly with your test data may fail with different input values, larger datasets, or concurrent access.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The code compiles and passes linting, so it's correct" | Linters and type checkers verify syntax and type safety, not algorithmic correctness; a function that always returns the first element of a list instead of the minimum compiles cleanly and passes all linters. |
| "Off-by-one errors are trivial and easy to spot" | Off-by-one errors in loop bounds and array indices are among the most common bugs in production systems; they are invisible to static analysis and often manifest only with specific input sizes or boundary values. |
| "We run the test suite, which covers logic errors" | Tests cover paths explicitly written by developers; semantic bugs live in the paths developers did not think to test -- null inputs, zero values, empty collections, and boundary conditions that were assumed impossible. |
| "Race conditions only occur in high-throughput systems" | Check-Then-Act race conditions in balance checks and permission verifications have been exploited with two simultaneous browser tabs at zero scale; concurrency is not a prerequisite for race condition bugs. |
| "Type coercion issues only matter in dynamically typed languages" | Static languages have their own coercion hazards: integer overflow in Java/C# silently wraps to negative values, implicit numeric promotions in C change signedness, and Go's integer division silently truncates decimals. |
| "Invariant checking is theoretical and rarely finds bugs in practice" | Explicit precondition and postcondition assertions (even as comments) have been shown in code review studies to surface incorrect assumptions about function contracts that would otherwise remain latent bugs. |

## Verification

- [ ] All loop bounds and array index operations reviewed for off-by-one conditions with boundary inputs (0, 1, n-1, n)
- [ ] Null/undefined propagation traced for all inputs that reach the reviewed code from external sources
- [ ] Concurrency hazards checked: any shared state accessed from multiple goroutines/threads/async tasks is identified
- [ ] Type coercion risk assessed: implicit conversions in conditions and arithmetic expressions reviewed
- [ ] At least one property-based or parameterized test added for each logic-heavy function to cover non-obvious inputs
- [ ] Semantic bug report produced with location, severity, explanation, and suggested fix for each detected issue

## Related Skills

- [[bug-localization]] -- pinpoints the file and line for a semantic bug this skill surfaces
- [[bug-to-patch-generator]] -- generates the fix for a detected logic error
- [[edge-case-generator]] -- produces the boundary inputs this skill checks off-by-one conditions against
- [[property-based-test-generator]] -- generates the property-based tests the Verification step calls for
- [[code-quality]] -- broader maintainability review that complements semantic-defect detection
