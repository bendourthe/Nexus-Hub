---
name: testing-review
description: Assess test coverage, test quality, testing strategy effectiveness, and identify coverage gaps. Use when evaluating test suites, improving test strategy, preparing for releases, or as Phase 5 of comprehensive code review.
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
```

### Step 2: Analyze Test Quality

1. **Test Structure**
   - Clear AAA pattern
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
- Edge cases
- Boundary conditions
- Critical business logic
- Security-sensitive code

### Step 4: Document Findings

```markdown
## Testing Review Finding

**Category**: Coverage Gap
**Severity**: HIGH
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
Immediate - before next release
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

## Quality Checklist

- [ ] Coverage metrics collected
- [ ] Coverage gaps identified
- [ ] Test quality assessed
- [ ] Anti-patterns detected
- [ ] Test performance reviewed
- [ ] Recommendations documented

## Related Skills

- `context-analysis` - Context understanding (Phase 1)
- `unit-tests` - Unit test generation
- `code-coverage` - Coverage improvement
- `final-report` - Consolidated report (Phase 6)

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Based on**: AI Templates code_review/testing_review/


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
