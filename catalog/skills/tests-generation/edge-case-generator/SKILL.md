---
name: edge-case-generator
description: Systematically generate edge case tests for boundary conditions, empty inputs, overflow, null values, concurrency edges, and type coercion. Use when hardening code against unexpected inputs, finding boundary bugs, testing defensive programming, validating error handling, or stress-testing input validation.
summary_l0: "Generate edge case tests for boundaries, overflow, null values, and concurrency"
overview_l1: "This skill systematically generates edge case tests for boundary conditions, empty inputs, overflow, null values, concurrency edges, and type coercion. Use it when hardening code against unexpected inputs, finding boundary bugs, testing defensive programming, validating error handling, or stress-testing input validation. Key capabilities include boundary value analysis, empty and null input testing, integer and buffer overflow testing, concurrency edge case generation, type coercion and implicit conversion testing, Unicode and encoding edge cases, resource exhaustion scenarios, and timing-dependent edge cases. The expected output is a comprehensive set of edge case test cases organized by category with expected behavior documentation. Trigger phrases: edge cases, boundary testing, null testing, overflow test, empty input, edge case generator, defensive testing, boundary conditions, unexpected input."
---

# Edge Case Test Generator

Systematically generate edge case tests that expose boundary conditions, invalid inputs, overflow scenarios, null/undefined handling, concurrency hazards, and type coercion surprises. This skill applies boundary value analysis, equivalence partitioning, and special-value injection to produce tests that catch the defects most likely to escape basic happy-path coverage.

## When to Use This Skill

Use this skill when you need to:

- Harden a function or API against unexpected, extreme, or adversarial inputs
- Identify boundary bugs around minimum, maximum, and off-by-one values
- Validate null, undefined, empty, and missing-field handling
- Test numeric overflow, underflow, and precision loss scenarios
- Cover Unicode, encoding, and locale-sensitive string edge cases
- Detect type coercion surprises in dynamically typed languages
- Stress-test concurrent access patterns for race conditions and deadlocks
- Satisfy security review requirements for input validation coverage
- Complement existing unit tests that only cover the happy path

**Trigger phrases**: "edge cases", "boundary tests", "null handling tests", "overflow tests", "empty input tests", "special value tests", "corner cases", "defensive tests", "input validation tests", "boundary value analysis", "equivalence partitioning"

## What This Skill Does

### Methodology Overview

The edge case generator follows a structured four-phase approach:

1. **Input Domain Analysis**: Decompose each parameter into its valid domain, boundary values, and equivalence classes
2. **Special Value Injection**: Apply a catalogue of known-problematic values (null, zero, negative, MAX_INT, empty string, Unicode edge cases)
3. **Combination Explosion Management**: Use pairwise or category-partition methods to generate high-value combinations without combinatorial blowup
4. **Oracle Definition**: For each generated input, determine the expected outcome (specific return value, exception type, graceful degradation, or invariant preservation)

### Boundary Value Analysis (BVA)

For every numeric, string-length, or collection-size parameter, test exactly at:

- The minimum valid value
- One below the minimum (invalid)
- One above the minimum
- A nominal (typical) value
- One below the maximum
- The maximum valid value
- One above the maximum (invalid)

### Equivalence Partitioning

Divide the input space into classes that should be treated identically by the code:

- **Valid equivalence classes**: Sets of inputs that should produce a successful result
- **Invalid equivalence classes**: Sets of inputs that should be rejected or handled gracefully
- **Boundary equivalence classes**: Inputs that sit exactly on partition edges

### Special Value Catalogue

| Category | Values to Test |
|---|---|
| Numeric | 0, -1, 1, -0.0, MAX_INT, MIN_INT, MAX_FLOAT, NaN, Infinity, -Infinity, very small floats (5e-324) |
| String | empty string `""`, single character, very long string (10k+ chars), whitespace-only, null character `\0`, multi-byte Unicode, RTL text, emoji, combining characters, surrogate pairs |
| Collection | empty list/array, single element, duplicate elements, very large collection (100k+), nested empty collections |
| Object/Map | empty object, missing required keys, extra unexpected keys, null values for required fields, deeply nested objects, circular references |
| Boolean/Truthy | true, false, null, undefined, 0, 1, empty string (in loosely typed languages) |
| Date/Time | epoch (1970-01-01), far future (9999-12-31), leap year dates (Feb 29), DST transition times, negative timestamps, timezone boundaries |

### Concurrency Edge Cases

- Simultaneous reads and writes to shared state
- Double-submit / double-click scenarios
- Resource exhaustion under concurrent load
- Lock ordering inversions leading to deadlocks
- Check-then-act race conditions (TOCTOU)

## Instructions

### Step 1: Identify the Function Under Test and Its Input Domain

Full walkthrough: [step-1-identify-the-function-under-test-and-its-input-domain.md](references/step-1-identify-the-function-under-test-and-its-input-domain.md) (load this step when you reach it).

### Step 2: Apply Boundary Value Analysis

Full walkthrough: [step-2-apply-boundary-value-analysis.md](references/step-2-apply-boundary-value-analysis.md) (load this step when you reach it).

### Step 3: Apply Special Value Injection

Full walkthrough: [step-3-apply-special-value-injection.md](references/step-3-apply-special-value-injection.md) (load this step when you reach it).

### Step 4: Test Type Coercion Edges (Dynamic Languages)

Full walkthrough: [step-4-test-type-coercion-edges-dynamic-languages.md](references/step-4-test-type-coercion-edges-dynamic-languages.md) (load this step when you reach it).

### Step 5: Test Unicode and Encoding Edge Cases

Full walkthrough: [step-5-test-unicode-and-encoding-edge-cases.md](references/step-5-test-unicode-and-encoding-edge-cases.md) (load this step when you reach it).

### Step 6: Test Concurrency Edge Cases

Full walkthrough: [step-6-test-concurrency-edge-cases.md](references/step-6-test-concurrency-edge-cases.md) (load this step when you reach it).

### Step 7: Combine Edge Cases with Equivalence Partitioning

Full walkthrough: [step-7-combine-edge-cases-with-equivalence-partitioning.md](references/step-7-combine-edge-cases-with-equivalence-partitioning.md) (load this step when you reach it).

## Best Practices

- **Start with boundary value analysis**: It catches the most common off-by-one and range errors with minimal test count
- **Use parameterized tests**: Avoid duplicating test boilerplate when only inputs and expected outputs differ
- **Name tests descriptively**: Each test name should describe the specific edge condition, not just "test1", "test2"
- **Test one edge per test method**: Isolate edge cases so that failures pinpoint the exact boundary that broke
- **Include both the input and the expected outcome**: Edge case tests are only valuable when the oracle (expected result) is clearly defined
- **Prioritize edges by risk**: Focus first on edges that involve security (overflow, injection), data loss (null handling), or financial impact (rounding, precision)
- **Keep the special value catalogue project-specific**: Add domain-relevant special values (e.g., for a healthcare app, test with patient ages of 0, 150, and negative)
- **Automate edge case discovery**: Use property-based testing (see the property-based-test-generator skill) to discover edge cases you did not anticipate
- **Revisit edges after bug fixes**: Every production bug reveals a missing edge case test; add it to the suite
- **Document why each edge matters**: A comment explaining "tests integer overflow on 32-bit systems" is more valuable than the test code alone

## Common Pitfalls

- **Testing only the happy path**: Writing 20 tests for valid inputs and zero tests for invalid inputs provides a false sense of security
- **Ignoring implicit boundaries**: Many boundaries are not in the specification but in the implementation (e.g., array index calculations, string encoding limits, database column widths)
- **Combinatorial explosion**: Testing every combination of every edge value is impractical; use pairwise or category-partition to keep the test count manageable
- **Asserting too loosely**: Using `assert result is not None` instead of asserting the specific expected value weakens the test oracle
- **Hardcoding environment-specific values**: Tests that use `MAX_INT` for a 64-bit system will behave differently on 32-bit; use language constants like `sys.maxsize` or `Integer.MAX_VALUE`
- **Forgetting concurrency edges**: Single-threaded tests pass, but the same code fails under concurrent load; always test shared-state operations with multiple threads
- **Not testing error message content**: Verifying that an exception is thrown is good; verifying that the error message is helpful for debugging is better
- **Neglecting cleanup in edge case tests**: Edge cases that allocate large resources (100k-element lists, temporary files) must clean up to avoid test suite resource exhaustion
- **Copy-pasting boundary values incorrectly**: When porting edge case tests between languages, numeric limits differ (JavaScript `Number.MAX_SAFE_INTEGER` is not the same as Java `Integer.MAX_VALUE`)
- **Assuming defensive code exists**: Edge case tests should verify that the code handles the edge, not assume it does; if the code lacks validation, the test exposes the gap

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The happy-path tests pass, so the function works." | A `paginate_results` call with `page=0` or an empty list takes an entirely different code path; the off-by-one and empty-collection defects ship precisely because no happy-path test exercises the boundary. |
| "Null and empty inputs would never reach this function in production." | Untrusted callers, deserialization, and upstream refactors routinely deliver null/empty values; a function that throws an opaque `IndexError` on empty input becomes a production incident, not a caught error. |
| "Unicode edge cases are over-engineering for a name field." | A null character, RTL override, or surrogate pair in a name field is a real injection and rendering vector; skipping these tests leaves the normalization gap that security review will flag. |
| "Testing every boundary combination is impractical, so I will skip them." | The point of boundary value analysis and pairwise partitioning is to cover high-value edges without combinatorial blowup; skipping them entirely is not the same as choosing them wisely. |

## Verification

- [ ] Each parameter has tests at minimum, minimum-minus-one, maximum, and maximum-plus-one boundaries.
- [ ] Empty, null/undefined, and single-element inputs are covered for every collection or string parameter.
- [ ] Each edge-case test asserts the specific expected value or exception type, not merely non-null.
- [ ] Special values relevant to the parameter type (NaN, Infinity, MAX_INT, surrogate pairs) are exercised.
- [ ] All edge-case tests pass and clean up any large allocations they create (`pytest -q` or equivalent exits 0).

## Related Skills

- [[property-based-test-generator]] -- discovers edge cases automatically that this skill enumerates by hand
- [[fuzzing-input-generator]] -- explores adversarial inputs beyond the curated special-value catalogue here
- [[directed-test-input-generator]] -- crafts inputs to reach specific branches these edge cases may not cover
- [[unit-tests]] -- holds the edge-case tests alongside the happy-path unit tests
- [[code-coverage]] -- confirms the boundary and error paths these tests exercise are actually covered
