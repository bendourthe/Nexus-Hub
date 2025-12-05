---
name: test-driven-development
description: Implement Test-Driven Development (TDD) workflow - write tests first, then code (Anthropic-favorite)
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language
category: Workflow
tags: [workflow, testing, tdd, best-practice, quality, anthropic]
priority: CRITICAL
based_on: Anthropic Claude Code Best Practices 2025, Test Development Templates
---

# Test-Driven Development (TDD)

Implement features using the Test-Driven Development workflow: write tests first, then write code to make them pass. This Anthropic-favorite approach ensures high code quality, comprehensive test coverage, and fewer bugs.

## When to Use This Skill

Use this skill for:

- ✅ Implementing new features from scratch

- ✅ Adding functionality to existing systems

- ✅ Bug fixes (write test that reproduces bug, then fix)

- ✅ Refactoring (tests ensure behavior preservation)

- ✅ API development (test contracts first)

- ✅ Critical business logic

- ✅ Code that will be maintained long-term

- ✅ Team environments (tests document behavior)

**TDD is especially valuable when**:

- Requirements are clear and testable

- You want to ensure comprehensive test coverage

- You're working on complex logic with edge cases

- You need living documentation through tests

## What This Skill Does

This skill implements the **Red-Green-Refactor** TDD cycle:

### 🔴 Red: Write a Failing Test
1. Write a test for the next small piece of functionality

2. Run the test and watch it fail (proves test is working)

3. Test should fail for the right reason (not syntax error)

### 🟢 Green: Make the Test Pass
4. Write the minimal code needed to make the test pass

5. Don't worry about perfect code yet (make it work first)

6. Run the test and see it pass

### 🔵 Refactor: Improve the Code
7. Refactor the implementation while keeping tests green

8. Improve code quality, remove duplication, optimize

9. All tests must still pass after refactoring

### 🔁 Repeat
10. Commit the code

11. Move to the next small piece of functionality

12. Repeat the cycle

## Why TDD Works

**Traditional Approach** (Code-First):
```
Developer: *writes 200 lines of code*
Developer: *writes tests afterward*
Result:

- ❌ Tests influenced by implementation (not requirements)

- ❌ Hard-to-test code (not designed for testability)

- ❌ Missing edge cases

- ❌ Tests feel like a chore

- ❌ Low test coverage

- ❌ Bugs discovered late
```

**TDD Approach** (Test-First):
```
Developer: *writes test for one requirement*
Developer: *writes minimal code to pass test*
Developer: *refactors with confidence*
Developer: *repeats for next requirement*
Result:

- ✅ Tests driven by requirements (not implementation)

- ✅ Code naturally testable (designed for testing)

- ✅ Edge cases discovered early

- ✅ Tests guide development

- ✅ High test coverage (by design)

- ✅ Bugs caught immediately
```

## Benefits of TDD

### Code Quality
- **Better Design**: Forces you to think about interfaces before implementation

- **Simpler Code**: Writing tests first encourages simple, focused solutions

- **Fewer Bugs**: Catch issues immediately, not in production

- **Refactoring Safety**: Comprehensive tests allow confident refactoring

### Development Speed
- **Faster Debugging**: Test failures pinpoint exact problems

- **Less Rework**: Get it right the first time

- **Faster Integration**: Confidence in changes prevents integration issues

- **Reduced Technical Debt**: Clean code from the start

### Documentation
- **Living Documentation**: Tests document how code should behave

- **Usage Examples**: Tests show how to use the code

- **Requirements Traceability**: Each test maps to a requirement

### Team Benefits
- **Onboarding**: New developers understand code through tests

- **Collaboration**: Tests clarify expectations

- **Code Reviews**: Tests validate correctness

- **Regression Prevention**: Tests catch future breaking changes

## Prerequisites

### Required
- Testing framework installed for your language:

  - **Python**: pytest, unittest

  - **JavaScript**: Jest, Mocha, Vitest

  - **Java**: JUnit, TestNG

  - **C#**: xUnit, NUnit, MSTest

  - **Go**: testing package, testify

  - **C**: Unity, Check, CUnit

  - **C++**: Google Test, Catch2, Boost.Test

### Recommended
- Code coverage tool (pytest-cov, Istanbul, JaCoCo, etc.)

- Test watcher for continuous testing

- CI/CD pipeline for automated testing

### Knowledge
- Understanding of unit testing concepts

- Basic testing framework syntax

- Willingness to write tests first (mindset shift!)

## Instructions

### Step 1: Understand the Requirement

**Before writing any code or tests**, ensure you understand:

- What functionality needs to be implemented?

- What are the inputs and expected outputs?

- What edge cases exist?

- What should happen when things go wrong?

**Example Requirement**: "Implement a function that validates email addresses"

**Clarifications needed**:

- What makes an email valid? (RFC 5322 compliant?)

- How should invalid emails be handled? (return false, raise exception?)

- What about internationalized email addresses?

- What about edge cases (empty string, null, whitespace)?

### Step 2: Write Your First Failing Test (🔴 Red)

Start with the **simplest** test case. Don't try to test everything at once.

**Python Example**:
```python
# tests/test_email_validator.py
import pytest
from email_validator import validate_email

def test_validate_email_accepts_valid_simple_email():
    """Test that a simple valid email is accepted."""
    result = validate_email("user@example.com")
    assert result is True
```

**JavaScript Example**:
```javascript
// tests/emailValidator.test.js
import { validateEmail } from '../src/emailValidator';

describe('validateEmail', () => {
  test('accepts valid simple email', () => {
    const result = validateEmail('user@example.com');
    expect(result).toBe(true);
  });
});
```

**Run the test**:
```bash
# Python
pytest tests/test_email_validator.py -v

# JavaScript
npm test emailValidator.test.js
```

**Expected Result**: Test should fail because `validate_email()` doesn't exist yet.

### Step 3: Write Minimal Code to Pass (🟢 Green)

Write the **simplest possible code** to make the test pass. Don't overthink it.

**Python Example**:
```python
# src/email_validator.py
def validate_email(email):
    """Validate an email address."""
    # Minimal implementation - just make the test pass
    if "@" in email and "." in email:
        return True
    return False
```

**Run the test again**:
```bash
pytest tests/test_email_validator.py -v
```

**Expected Result**: Test should pass (🟢 Green).

### Step 4: Refactor If Needed (🔵 Refactor)

At this early stage, there's probably nothing to refactor yet. That's OK!

**Move to the next test.**

### Step 5: Add More Tests (One at a Time)

Add the next test case. **Only one test at a time.**

**Python Example** (Testing invalid email):
```python
def test_validate_email_rejects_email_without_at_symbol():
    """Test that email without @ is rejected."""
    result = validate_email("userexample.com")
    assert result is False
```

**Run the test**:
```bash
pytest tests/test_email_validator.py -v
```

**Expected Result**: Test should pass because our implementation already checks for "@".

### Step 6: Add Edge Case Tests

Continue adding tests for edge cases:

**Python Example**:
```python
def test_validate_email_rejects_empty_string():
    """Test that empty string is rejected."""
    result = validate_email("")
    assert result is False

def test_validate_email_rejects_none():
    """Test that None is rejected."""
    result = validate_email(None)
    assert result is False

def test_validate_email_rejects_multiple_at_symbols():
    """Test that email with multiple @ symbols is rejected."""
    result = validate_email("user@@example.com")
    assert result is False

def test_validate_email_accepts_valid_email_with_subdomain():
    """Test that email with subdomain is accepted."""
    result = validate_email("user@mail.example.com")
    assert result is True

def test_validate_email_accepts_valid_email_with_plus():
    """Test that email with + is accepted."""
    result = validate_email("user+tag@example.com")
    assert result is True
```

**Some of these will fail**. That's the point! Now improve the implementation.

### Step 7: Improve Implementation

Update the implementation to handle all test cases:

**Python Example**:
```python
import re

def validate_email(email):
    """
    Validate an email address using a simple regex.

    Args:
        email: Email address to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False

    # Simple email regex (covers most common cases)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
```

**Run all tests**:
```bash
pytest tests/test_email_validator.py -v
```

**Expected Result**: All tests should pass (🟢 Green).

### Step 8: Refactor with Confidence (🔵 Refactor)

Now that you have comprehensive tests, you can refactor safely:

**Python Example** (Improved implementation):
```python
import re
from typing import Optional

class EmailValidationError(ValueError):
    """Raised when email validation fails."""
    pass

def validate_email(email: Optional[str], raise_exception: bool = False) -> bool:
    """
    Validate an email address using RFC 5322 simplified regex.

    Args:
        email: Email address to validate
        raise_exception: If True, raise EmailValidationError instead of returning False

    Returns:
        bool: True if valid, False otherwise

    Raises:
        EmailValidationError: If email is invalid and raise_exception=True
    """
    if not email or not isinstance(email, str):
        if raise_exception:
            raise EmailValidationError(f"Invalid email: {email}")
        return False

    # RFC 5322 simplified regex
    pattern = r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'

    is_valid = bool(re.match(pattern, email))

    if not is_valid and raise_exception:
        raise EmailValidationError(f"Invalid email format: {email}")

    return is_valid
```

**Run all tests**:
```bash
pytest tests/test_email_validator.py -v
```

**Expected Result**: All tests should still pass (you didn't break anything!).

### Step 9: Test the New Functionality

Add tests for the new `raise_exception` parameter:

**Python Example**:
```python
def test_validate_email_raises_exception_for_invalid_email():
    """Test that exception is raised when requested."""
    with pytest.raises(EmailValidationError, match="Invalid email format"):
        validate_email("invalid-email", raise_exception=True)

def test_validate_email_does_not_raise_exception_for_valid_email():
    """Test that no exception is raised for valid email."""
    result = validate_email("user@example.com", raise_exception=True)
    assert result is True
```

**Run all tests**:
```bash
pytest tests/test_email_validator.py -v
```

### Step 10: Check Code Coverage

Ensure your tests cover the implementation:

**Python**:
```bash
pytest tests/test_email_validator.py --cov=src.email_validator --cov-report=term-missing
```

**JavaScript**:
```bash
npm test -- --coverage
```

**Target**: 80%+ code coverage (aim for 90%+ for critical code).

### Step 11: Commit and Continue

Commit your work:
```bash
git add .
git commit -m "feat: add email validation with comprehensive tests"
```

**Move to the next feature and repeat the cycle.**

## TDD Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     TDD Cycle (Red-Green-Refactor)          │
└─────────────────────────────────────────────────────────────┘

    1. Write Test          2. Run Test           3. Write Code
   ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
   │              │       │              │       │              │
   │  Write a     │──────▶│  Test FAILS  │──────▶│  Implement   │
   │  Failing     │       │  (🔴 Red)    │       │  Minimal     │
   │  Test        │       │              │       │  Code        │
   │              │       │              │       │              │
   └──────────────┘       └──────────────┘       └──────────────┘
                                                         │
                                                         ▼

    6. Next Feature       5. Commit            4. Run Test
   ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
   │              │       │              │       │              │
   │  Move to     │◀──────│  Commit      │◀──────│  Test PASSES │
   │  Next Test   │       │  Working     │       │  (🟢 Green)  │
   │              │       │  Code        │       │              │
   │              │       │              │       │              │
   └──────────────┘       └──────────────┘       └──────────────┘
         │                       ▲                       │
         │                       │                       ▼
         │                7. Refactor          5. Run Tests
         │               ┌──────────────┐       ┌──────────────┐
         │               │              │       │              │
         └──────────────▶│  Refactor    │──────▶│  All Tests   │
                         │  Code While  │       │  Still PASS  │
                         │  Tests Green │       │  (🟢 Green)  │
                         │              │       │              │
                         └──────────────┘       └──────────────┘
```

## Common TDD Patterns

### Pattern 1: Test-First for Bug Fixes

**Process**:

1. **Reproduce the bug** with a failing test

2. **Fix the bug** to make the test pass

3. **Verify** the fix with the test

4. **Prevent regression** (test stays forever)

**Example** (Bug: Division by zero not handled):
```python
# Step 1: Write test that reproduces bug
def test_divide_by_zero_raises_error():
    """Test that division by zero raises ValueError."""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)

# Step 2: Fix the implementation
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

# Step 3: Test passes, bug is fixed, regression prevented
```

### Pattern 2: Test Data Builders

Use fixtures or factories for test data:

**Python Example**:
```python
import pytest

@pytest.fixture
def valid_user():
    """Fixture providing a valid user for tests."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "age": 25
    }

def test_user_creation_with_valid_data(valid_user):
    """Test user creation with valid data."""
    user = create_user(valid_user)
    assert user.username == "testuser"
    assert user.email == "test@example.com"
```

**JavaScript Example**:
```javascript
// test/helpers/userFactory.js
export function createValidUser(overrides = {}) {
  return {
    username: 'testuser',
    email: 'test@example.com',
    age: 25,
    ...overrides
  };
}

// test/userService.test.js
import { createValidUser } from './helpers/userFactory';

test('creates user with valid data', () => {
  const userData = createValidUser();
  const user = createUser(userData);
  expect(user.username).toBe('testuser');
});
```

### Pattern 3: Test Naming Convention

Use descriptive test names that explain behavior:

**Format**: `test_[unit]_[scenario]_[expected_behavior]`

**Examples**:
```python
# Good test names
def test_validate_email_accepts_valid_simple_email():
def test_validate_email_rejects_email_without_at_symbol():
def test_validate_email_rejects_empty_string():
def test_user_login_fails_with_wrong_password():
def test_order_total_includes_tax_for_taxable_items():

# Bad test names (too vague)
def test_email():
def test_validation():
def test_case_1():
```

### Pattern 4: Arrange-Act-Assert (AAA)

Structure tests with clear sections:

**Python Example**:
```python
def test_user_registration_sends_welcome_email():
    """Test that user registration sends a welcome email."""
    # Arrange: Set up test data and mocks
    user_data = {"email": "new@example.com", "username": "newuser"}
    email_service = Mock()

    # Act: Execute the functionality
    register_user(user_data, email_service)

    # Assert: Verify the behavior
    email_service.send_email.assert_called_once_with(
        to="new@example.com",
        subject="Welcome!",
        body=ANY
    )
```

### Pattern 5: Test Isolation

Each test should be independent:

**Python Example**:
```python
import pytest

@pytest.fixture(autouse=True)
def reset_database():
    """Reset database before each test."""
    setup_test_database()
    yield
    teardown_test_database()

def test_user_creation():
    """Test runs in isolated database."""
    user = create_user({"username": "test"})
    assert user.id is not None

def test_user_update():
    """Test runs in fresh database (isolated from previous test)."""
    user = create_user({"username": "test"})
    update_user(user.id, {"username": "updated"})
    assert get_user(user.id).username == "updated"
```

## Language-Specific Examples

### Python with pytest

**Directory Structure**:
```
project/
├── src/
│   └── calculator.py
└── tests/
    └── test_calculator.py
```

**Test File**:
```python
# tests/test_calculator.py
import pytest
from src.calculator import Calculator

class TestCalculator:
    """Test suite for Calculator class."""

    @pytest.fixture
    def calculator(self):
        """Fixture providing a Calculator instance."""
        return Calculator()

    def test_add_two_positive_numbers(self, calculator):
        """Test addition of two positive numbers."""
        result = calculator.add(2, 3)
        assert result == 5

    def test_add_negative_numbers(self, calculator):
        """Test addition of negative numbers."""
        result = calculator.add(-2, -3)
        assert result == -5

    def test_divide_by_zero_raises_error(self, calculator):
        """Test that division by zero raises ValueError."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calculator.divide(10, 0)
```

**Implementation**:
```python
# src/calculator.py
class Calculator:
    """Simple calculator with basic operations."""

    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return a + b

    def divide(self, a: float, b: float) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
```

### JavaScript with Jest

**Directory Structure**:
```
project/
├── src/
│   └── calculator.js
└── tests/
    └── calculator.test.js
```

**Test File**:
```javascript
// tests/calculator.test.js
import { Calculator } from '../src/calculator';

describe('Calculator', () => {
  let calculator;

  beforeEach(() => {
    calculator = new Calculator();
  });

  describe('add', () => {
    test('adds two positive numbers', () => {
      const result = calculator.add(2, 3);
      expect(result).toBe(5);
    });

    test('adds negative numbers', () => {
      const result = calculator.add(-2, -3);
      expect(result).toBe(-5);
    });
  });

  describe('divide', () => {
    test('divides two numbers', () => {
      const result = calculator.divide(10, 2);
      expect(result).toBe(5);
    });

    test('throws error when dividing by zero', () => {
      expect(() => calculator.divide(10, 0))
        .toThrow('Cannot divide by zero');
    });
  });
});
```

**Implementation**:
```javascript
// src/calculator.js
export class Calculator {
  add(a, b) {
    return a + b;
  }

  divide(a, b) {
    if (b === 0) {
      throw new Error('Cannot divide by zero');
    }
    return a / b;
  }
}
```

### Java with JUnit 5

**Directory Structure**:
```
project/
├── src/main/java/com/example/
│   └── Calculator.java
└── src/test/java/com/example/
    └── CalculatorTest.java
```

**Test File**:
```java
// src/test/java/com/example/CalculatorTest.java
package com.example;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

class CalculatorTest {

    private Calculator calculator;

    @BeforeEach
    void setUp() {
        calculator = new Calculator();
    }

    @Test
    @DisplayName("Add two positive numbers")
    void testAddTwoPositiveNumbers() {
        int result = calculator.add(2, 3);
        assertEquals(5, result);
    }

    @Test
    @DisplayName("Add negative numbers")
    void testAddNegativeNumbers() {
        int result = calculator.add(-2, -3);
        assertEquals(-5, result);
    }

    @Test
    @DisplayName("Divide by zero throws exception")
    void testDivideByZeroThrowsException() {
        Exception exception = assertThrows(
            ArithmeticException.class,
            () -> calculator.divide(10, 0)
        );
        assertEquals("Cannot divide by zero", exception.getMessage());
    }
}
```

**Implementation**:
```java
// src/main/java/com/example/Calculator.java
package com.example;

public class Calculator {

    public int add(int a, int b) {
        return a + b;
    }

    public int divide(int a, int b) {
        if (b == 0) {
            throw new ArithmeticException("Cannot divide by zero");
        }
        return a / b;
    }
}
```

## Common Pitfalls and Solutions

### Pitfall 1: Writing Too Much Code Before Testing

**Problem**: Writing complete features before testing.

**Solution**: Write **one test**, implement **minimal code**, repeat.

### Pitfall 2: Testing Implementation Instead of Behavior

**Problem**:
```python
# Bad: Testing internal implementation
def test_user_service_calls_database_query():
    assert user_service._db.query.called
```

**Solution**:
```python
# Good: Testing behavior
def test_user_service_returns_user_by_id():
    user = user_service.get_user(123)
    assert user.id == 123
    assert user.name == "John"
```

### Pitfall 3: Test Dependencies

**Problem**: Tests that depend on each other or shared state.

**Solution**: Use fixtures and reset state between tests.

### Pitfall 4: Skipping Refactoring

**Problem**: Code gets messy because refactoring is skipped.

**Solution**: **Always refactor** after tests pass. Tests give you confidence.

### Pitfall 5: Testing Too Much at Once

**Problem**: Complex tests that are hard to debug when they fail.

**Solution**: **One assertion per test** (or at least one concept per test).

## Success Criteria

- [ ] All tests are written **before** implementation code

- [ ] Each test tests **one specific behavior**

- [ ] Tests have **descriptive names** explaining what they test

- [ ] All tests follow **Arrange-Act-Assert** pattern

- [ ] Tests are **independent** (no shared state)

- [ ] Code coverage is **80%+** (90%+ for critical code)

- [ ] Tests run **quickly** (< 1 second for unit tests)

- [ ] All tests **pass** before committing

- [ ] Tests are committed **with** the implementation

- [ ] Refactoring was done while keeping tests green

## Related Skills

- [`plan-before-code`](../plan-before-code/SKILL.md) - Plan your TDD approach before starting

- [`setup-test-infrastructure`](../setup-test-infrastructure/SKILL.md) - Set up testing frameworks

- [`generate-test-cases`](../generate-test-cases/SKILL.md) - Generate comprehensive test cases

- [`create-mocks-fixtures`](../create-mocks-fixtures/SKILL.md) - Create test data and mocks

- [`analyze-code-coverage`](../analyze-code-coverage/SKILL.md) - Analyze test coverage gaps

- [`code-review-testing`](../code-review-testing/SKILL.md) - Review test quality

## Additional Resources

### TDD Fundamentals
- [Test-Driven Development by Kent Beck](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530) - The definitive TDD book

- [Growing Object-Oriented Software, Guided by Tests](https://www.amazon.com/Growing-Object-Oriented-Software-Guided-Tests/dp/0321503627)

- [Martin Fowler on TDD](https://martinfowler.com/bliki/TestDrivenDevelopment.html)

### Testing Frameworks
- **Python**: [pytest documentation](https://docs.pytest.org/)

- **JavaScript**: [Jest documentation](https://jestjs.io/), [Vitest](https://vitest.dev/)

- **Java**: [JUnit 5 User Guide](https://junit.org/junit5/docs/current/user-guide/)

- **C#**: [xUnit documentation](https://xunit.net/), [NUnit](https://nunit.org/)

- **Go**: [testing package](https://pkg.go.dev/testing), [testify](https://github.com/stretchr/testify)

- **C++**: [Google Test](https://google.github.io/googletest/), [Catch2](https://github.com/catchorg/Catch2)

### Anthropic Claude Code
- [Claude Code Best Practices](https://docs.anthropic.com/claude/docs/claude-code-best-practices) - Official best practices

- [Test-Driven Development with Claude](https://docs.anthropic.com/claude/docs/tdd-workflow) - TDD workflow guide

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: Anthropic Claude Code Best Practices 2025, ai_templates Test Development Templates
**Template Sources**:

- `test_development/test_structure/*.md`

- `test_development/test_cases/*.md`

- `test_development/code_coverage/*.md`
