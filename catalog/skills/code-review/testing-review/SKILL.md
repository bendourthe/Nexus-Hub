---
name: testing-review
description: Assess test coverage, test quality, testing strategy effectiveness, and identify coverage gaps. Use when evaluating test suites, improving test strategy, preparing for releases, or as Phase 5 of comprehensive code review.
summary_l0: "Assess test coverage, quality, and strategy effectiveness with gap identification"
overview_l1: "This skill evaluates test coverage, quality, and effectiveness, serving as Phase 5 of the 6-phase code review methodology. Use it when evaluating test suite quality, identifying coverage gaps, assessing testing strategy, reviewing test maintainability, preparing for releases, or improving test effectiveness. Key capabilities include line and branch coverage analysis, test quality scoring (assertion density, test isolation, naming conventions), testing strategy assessment (unit, integration, E2E balance), coverage gap identification by feature and risk area, test maintainability review, flaky test detection, and test pyramid evaluation. The expected output is a testing review report with coverage metrics, quality scores, identified gaps, and recommendations for improving the test suite. Trigger phrases: testing review, test coverage, test quality, test assessment, coverage gaps, test strategy."
---

# Code Review - Testing Review

Evaluate test coverage, quality, and effectiveness. This skill is **Phase 5** of the 6-phase code review methodology.

## When to Use This Skill

Use this skill when you need to:

- Evaluate test suite quality
- Identify coverage gaps
- Assess testing strategy
- Review test maintainability
- Prepare for releases
- Improve test effectiveness

**Trigger phrases**: "testing review", "test coverage", "test quality", "test assessment", "coverage gaps", "test strategy"

## What This Skill Does

### Assessment Areas

| Area | Focus |
|------|-------|
| **Coverage** | Line, branch, function coverage |
| **Quality** | Test clarity, maintainability |
| **Strategy** | Unit, integration, E2E balance |
| **Effectiveness** | Real bug detection ability |
| **Performance** | Test execution time |

### Coverage Targets

- **Line Coverage**: 80%+
- **Branch Coverage**: 75%+
- **Function Coverage**: 90%+
- **Critical Paths**: 95%+

### Severity Classification

| Level | Alias | Description |
|-------|-------|-------------|
| **P0** | CRITICAL | Critical paths completely untested |
| **P1** | HIGH | Significant coverage gaps in important code |
| **P2** | MEDIUM | Test quality issues or moderate gaps |
| **P3** | LOW | Minor test improvements |

## Instructions

### Step 1: Measure Coverage

```bash
# Python
pytest --cov=src --cov-report=html

# JavaScript
npm test -- --coverage

# Java
mvn jacoco:report

# Go
go test -coverprofile=coverage.out ./...

# C# / .NET
dotnet test --collect:"XPlat Code Coverage"
```

### Step 2: Analyze Test Quality

1. **Test Structure**
   - Clear AAA pattern (Arrange-Act-Assert)
   - Descriptive names
   - Single responsibility

2. **Test Isolation**
   - No shared state
   - Independent execution
   - Proper mocking

3. **Test Types Balance**
   - Unit tests (70%)
   - Integration tests (20%)
   - E2E tests (10%)

### Step 3: Identify Gaps

Check for missing tests in:
- Error handling paths
- Edge cases and boundary conditions
- Critical business logic
- Security-sensitive code
- Recently changed code (in git-changes mode)

### Step 4: Document Findings

```markdown
## Testing Review Finding

**Category**: Coverage Gap
**Severity**: P1 (HIGH)
**File**: [src/services/payment.py]

### Issue
Payment processing has 45% coverage, critical path untested

### Missing Tests
- [ ] Failed payment handling
- [ ] Partial refund logic
- [ ] Currency conversion edge cases

### Recommendation
Add tests for error scenarios and edge cases

### Priority
Immediate (before next release)
```

## Test Quality Indicators

### Good Tests
- Clear, descriptive names
- Single assertion focus
- Fast execution (<100ms)
- No flaky behavior
- Proper isolation

### Bad Tests (Anti-patterns)
- Multiple unrelated assertions
- Testing implementation details
- Slow execution
- Shared mutable state
- No assertions (always pass)

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Coverage is 85%, so the test suite is good" | High line coverage with assertion-free or always-passing tests detects no bugs; the 45%-covered payment path in this skill's example is more dangerous than a low number suggests because the uncovered 55% is the error-handling and refund logic. |
| "These tests pass, so we don't need to review their quality" | Tests that assert implementation details break on every refactor and tests that share mutable state pass in isolation but fail in CI; passing today says nothing about whether the suite is maintainable or catches regressions. |
| "We have lots of E2E tests, so unit coverage doesn't matter" | An inverted test pyramid (heavy E2E, thin unit) produces slow, flaky suites where a single failure could be any of dozens of layers; the 70/20/10 balance exists so failures localize quickly. |
| "Edge cases are unlikely, so testing the happy path is enough" | Production failures cluster at boundaries (empty collections, null inputs, currency rounding); the coverage-gap step targets exactly the error and boundary paths that happy-path-only suites leave unguarded. |

## Verification

- [ ] Coverage metrics collected (line, branch, function) and recorded
- [ ] Coverage gaps identified by feature and risk area
- [ ] Test quality assessed (AAA pattern, descriptive naming, isolation)
- [ ] Anti-patterns detected (no-assertion tests, shared mutable state, implementation-detail tests)
- [ ] Test type balance evaluated against the 70/20/10 pyramid
- [ ] Test execution performance reviewed (slow tests flagged)
- [ ] Critical path coverage verified against the 95%+ target
- [ ] Recommendations documented with severity (P0-P3)

## Related Skills

- [[functional-verification]] -- owns dynamic exercise of the built artifact; this skill reviews the test suite's coverage, quality, and strategy.
- [[context-analysis]] -- Context understanding (Phase 1)
- [[code-quality]] -- Code quality + SOLID review (Phase 2)
- [[security-review]] -- Security analysis (Phase 3)
- [[performance-review]] -- Performance analysis (Phase 4)
- [[unit-tests]] -- generate the unit tests that close the gaps this review identifies
- [[code-coverage]] -- raise coverage toward the targets this review measures against
- [[final-report]] -- Consolidated report (Phase 6)

---

**Version**: 2.0.0
**Last Updated**: February 2026
**Based on**: Nexus-Hub code review methodology + code-review-expert


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
