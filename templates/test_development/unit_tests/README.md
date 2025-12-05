# Unit Tests - Test Development Phase

## Purpose

Establish comprehensive unit testing practices focused on testing individual components in isolation, ensuring fast execution, complete independence, and thorough coverage of all code paths at the function/method level.

---

## What This Review Covers

### 1. Unit Test Principles
- Single responsibility testing

- Test isolation and independence

- Fast execution requirements (<1 second per test)

- Mocking external dependencies

- AAA pattern (Arrange-Act-Assert)

- FIRST principles (Fast, Independent, Repeatable, Self-validating, Timely)

### 2. Test Organization
- Unit test directory structure

- Test naming conventions

- Test grouping strategies

- File organization patterns

- Test discovery optimization

- Separation of unit vs integration tests

### 3. Test Implementation Patterns
- Testing pure functions

- Testing classes and methods

- Testing asynchronous code

- Testing error conditions and exceptions

- Testing edge cases and boundaries

- Parametrized testing patterns

- Testing private/internal methods

### 4. Test Quality Standards
- Test independence verification

- Execution time optimization

- Assertion clarity and specificity

- Test maintainability practices

- Avoiding test anti-patterns

- Test code readability

- Proper use of mocks and stubs

---

## When to Use This Template

- **Starting unit test implementation** for a new codebase

- **Establishing unit testing standards** for a development team

- **Refactoring existing tests** to improve isolation and speed

- **Improving test execution performance** (reducing flaky or slow tests)

- **Teaching unit testing best practices** to developers

- **Migrating from integration-heavy to unit-focused** testing strategy

- **Setting up test infrastructure** before implementing features

- **Code review preparation** to ensure testability

---

## Related Templates

| Template | Relationship | Usage |
|----------|--------------|-------|
| **Test Structure** | Prerequisite | Set up testing infrastructure before implementing unit tests |
| **Mocks & Fixtures** | Companion | Learn isolation techniques for effective unit testing |
| **Test Cases** | Follows | Implement broader test scenarios after unit test foundation |
| **Code Coverage** | Validation | Measure effectiveness of unit test coverage |
| **Reward Hacking** | Quality Gate | Validate that unit tests truly test functionality |

---

## Expected Outcomes

After completing this phase, you will have:

- **Unit Test Implementation Guide** (20-30 pages)

  - Complete methodology for writing effective unit tests

  - Framework-specific best practices

  - Code examples for common patterns

- **Unit Test Suite** (50+ test functions)

  - Tests for all critical functions and methods

  - Edge case and error condition coverage

  - Fast, isolated, independent tests

- **Unit Test Standards Document**

  - Naming conventions

  - Organization patterns

  - Quality criteria

  - Anti-patterns to avoid

- **Test Execution Scripts**

  - Run unit tests in isolation

  - Performance profiling tools

  - Coverage measurement integration

- **Unit Test Checklist Template**

  - Quality verification checklist

  - Code review guidelines

  - Continuous improvement metrics

---

## Available Templates

| Language | Template File | Testing Framework |
|----------|---------------|-------------------|
| Python | [python_unit_tests.md](python_unit_tests.md) | pytest, unittest |
| JavaScript/TypeScript | [javascript_unit_tests.md](javascript_unit_tests.md) | Jest, Mocha, Vitest |
| Java | [java_unit_tests.md](java_unit_tests.md) | JUnit 5 |
| C# | [csharp_unit_tests.md](csharp_unit_tests.md) | xUnit, NUnit |
| Go | [go_unit_tests.md](go_unit_tests.md) | testing package |
| C | [c_unit_tests.md](c_unit_tests.md) | Unity, Check |
| C++ | [cpp_unit_tests.md](cpp_unit_tests.md) | Google Test, Catch2 |

---

## Quick Start

### Step 1: Choose Your Language Template
Select the appropriate template file for your project's primary programming language from the table above.

### Step 2: Review Prerequisites
Ensure you have completed the **Test Structure** phase to set up your testing infrastructure.

### Step 3: Create Output Directory
```bash
mkdir -p unit_tests_output/{templates,assets,exports}
```

### Step 4: Use the Template
Open your selected language template and copy the prompt section into your AI assistant or IDE. Follow the instructions to generate comprehensive unit test guidance.

### Step 5: Implement and Validate
- Implement unit tests following the generated guidelines

- Run tests to ensure they pass independently

- Verify execution time is <1 second per test

- Check test coverage using tools recommended in the template

- Review with the checklist provided in the output

---

## Verify Directory Structure

After using this template, your output should contain:

```
unit_tests_output/
├── templates/
│   ├── unit_test_template.py (or language-specific extension)
│   ├── mock_setup_template.py
│   ├── parametrized_test_template.py
│   └── test_fixtures.py
├── assets/
│   ├── unit_test_principles_diagram.png
│   ├── test_organization_structure.png
│   ├── aaa_pattern_visualization.png
│   └── first_principles_checklist.png
└── exports/
    ├── unit_test_implementation_guide.md (20-30 pages)
    ├── unit_test_examples.md (50+ test functions)
    ├── unit_test_standards.md
    ├── anti_patterns_guide.md
    ├── execution_profiling_report.md
    └── unit_test_quality_checklist.md
```

---

## Key Principles of Effective Unit Tests

### FIRST Principles
- **Fast** - Execute in milliseconds, not seconds

- **Independent** - No dependencies on other tests or external state

- **Repeatable** - Same results every time, in any environment

- **Self-validating** - Clear pass/fail without manual inspection

- **Timely** - Written before or alongside production code

### AAA Pattern
- **Arrange** - Set up test data and preconditions

- **Act** - Execute the function/method being tested

- **Assert** - Verify the expected outcome

### Test Independence
- Each test can run alone or in any order

- Tests don't share state

- Tests clean up after themselves

- No reliance on external systems (databases, APIs, file systems)

---

## Common Unit Test Anti-Patterns to Avoid

- **Testing implementation details** instead of behavior

- **Multiple assertions** testing unrelated concerns

- **Slow tests** that take seconds to execute

- **Test interdependencies** where tests rely on execution order

- **Excessive mocking** that tests mock behavior, not real code

- **Unclear test names** that don't describe what is being tested

- **Test logic complexity** with loops, conditionals, or complex setup

- **Ignoring edge cases** and only testing happy paths

---

## Integration with Other Phases

1. **Complete Test Structure first** - Ensure your testing infrastructure is ready

2. **Use Mocks & Fixtures effectively** - Learn isolation techniques to support unit testing

3. **Expand to Test Cases** - After unit tests, add integration and end-to-end tests

4. **Measure with Code Coverage** - Validate that unit tests cover critical code paths

5. **Validate with Reward Hacking** - Ensure unit tests truly test functionality, not just pass

---

**Next Steps:** Choose your language template and begin implementing comprehensive unit tests following the FIRST principles and AAA pattern.
