---
name: test-driven-development
description: Implement Test-Driven Development (TDD) workflow - write tests first, then code. Use when implementing new features, fixing bugs, refactoring, or developing critical business logic.
summary_l0: "Implement TDD workflow with red-green-refactor cycle and test-first development"
overview_l1: "This skill implements Test-Driven Development (TDD) workflow where tests are written first, then code. Use it when implementing new features, fixing bugs, refactoring, or developing critical business logic. Key capabilities include red-green-refactor cycle execution, test-first requirement translation, minimal implementation to pass tests, refactoring with test safety net, TDD for bug fixes (write failing test, then fix), incremental feature development through test cycles, and TDD workflow integration with CI/CD. The expected output is code developed through the TDD cycle with comprehensive test coverage, clean implementation, and documented test progression. Trigger phrases: TDD, test-driven development, test first, red-green-refactor, write test first, test then code, failing test first."
---

# Test-Driven Development (TDD)

Implement features using the Test-Driven Development workflow: write tests first, then write code to make them pass. This approach ensures high code quality, comprehensive test coverage, and fewer bugs.

## When to Use This Skill

Use this skill for:

- Implementing new features from scratch
- Adding functionality to existing systems
- Bug fixes (write test that reproduces bug, then fix)
- Refactoring (tests ensure behavior preservation)
- API development (test contracts first)
- Critical business logic
- Code that will be maintained long-term

**Trigger phrases**: "TDD", "test-driven", "write tests first", "red green refactor", "test first development"

## What This Skill Does

Implements the **Red-Green-Refactor** TDD cycle:

| Phase | Color | Action |
|-------|-------|--------|
| 1 | Red | Write a failing test |
| 2 | Green | Write minimal code to pass |
| 3 | Blue | Refactor while keeping tests green |
| 4 | Repeat | Move to next functionality |

## Instructions

### Step 1: Understand the Requirement

Before writing any code or tests, clarify:

- What functionality needs to be implemented?
- What are the inputs and expected outputs?
- What edge cases exist?
- What should happen when things go wrong?

### Step 2: Write First Failing Test (Red)

Start with the **simplest** test case:

```python
# Python with pytest
def test_validate_email_accepts_valid_email():
    """Test that a valid email is accepted."""
    result = validate_email("user@example.com")
    assert result is True
```

```javascript
// JavaScript with Jest
describe('validateEmail', () => {
  test('accepts valid email', () => {
    const result = validateEmail('user@example.com');
    expect(result).toBe(true);
  });
});
```

```java
// Java with JUnit
@Test
@DisplayName("accepts valid email")
void testAcceptsValidEmail() {
    boolean result = EmailValidator.validate("user@example.com");
    assertTrue(result);
}
```

```csharp
// C# with xUnit
[Fact]
public void ValidateEmail_AcceptsValidEmail()
{
    var result = EmailValidator.Validate("user@example.com");
    Assert.True(result);
}
```

**Run the test** - it should fail because the function doesn't exist yet.

### Step 3: Write Minimal Code to Pass (Green)

Write the **simplest possible code** to make the test pass:

```python
def validate_email(email):
    """Validate an email address."""
    if "@" in email and "." in email:
        return True
    return False
```

**Run the test** - it should pass.

### Step 4: Refactor If Needed (Blue)

At this early stage, there may be nothing to refactor. Move to the next test.

### Step 5: Add More Tests (One at a Time)

Add tests for edge cases and invalid inputs:

```python
def test_validate_email_rejects_without_at_symbol():
    """Test that email without @ is rejected."""
    result = validate_email("userexample.com")
    assert result is False

def test_validate_email_rejects_empty_string():
    """Test that empty string is rejected."""
    result = validate_email("")
    assert result is False

def test_validate_email_rejects_none():
    """Test that None is rejected."""
    result = validate_email(None)
    assert result is False

def test_validate_email_rejects_multiple_at_symbols():
    """Test that multiple @ symbols are rejected."""
    result = validate_email("user@@example.com")
    assert result is False
```

Some tests will fail - that's the point! Improve the implementation.

### Step 6: Improve Implementation

Update implementation to handle all cases:

```python
import re

def validate_email(email):
    """
    Validate an email address.

    Args:
        email: Email address to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
```

**Run all tests** - they should all pass.

### Step 7: Refactor with Confidence (Blue)

Now that you have comprehensive tests, refactor safely:

```python
import re
from typing import Optional

class EmailValidationError(ValueError):
    """Raised when email validation fails."""
    pass

def validate_email(
    email: Optional[str],
    raise_exception: bool = False
) -> bool:
    """
    Validate an email address using RFC 5322 simplified regex.

    Args:
        email: Email address to validate
        raise_exception: If True, raise exception for invalid emails

    Returns:
        bool: True if valid, False otherwise

    Raises:
        EmailValidationError: If invalid and raise_exception=True
    """
    if not email or not isinstance(email, str):
        if raise_exception:
            raise EmailValidationError(f"Invalid email: {email}")
        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    is_valid = bool(re.match(pattern, email))

    if not is_valid and raise_exception:
        raise EmailValidationError(f"Invalid email format: {email}")

    return is_valid
```

**Run all tests** - they should still pass!

### Step 8: Add Tests for New Functionality

```python
def test_validate_email_raises_exception_when_requested():
    """Test that exception is raised when requested."""
    with pytest.raises(EmailValidationError):
        validate_email("invalid", raise_exception=True)
```

### Step 9: Check Code Coverage

```bash
# Python
pytest --cov=src --cov-report=term-missing

# JavaScript
npm test -- --coverage

# Java (Maven)
mvn jacoco:report
```

Target: 80%+ coverage (90%+ for critical code).

### Step 10: Commit and Continue

```bash
git add .
git commit -m "feat: add email validation with comprehensive tests"
```

## TDD Patterns

### Pattern 1: Bug Fix with TDD

1. Write test that reproduces the bug
2. Watch it fail (confirms bug exists)
3. Fix the bug
4. Watch test pass
5. Bug is fixed, test prevents regression

```python
# Step 1: Test that reproduces bug
def test_divide_by_zero_raises_error():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)

# Step 2: Fix
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

### Pattern 2: Arrange-Act-Assert

Structure tests clearly:

```python
def test_user_registration_sends_welcome_email():
    # Arrange: Set up test data and mocks
    user_data = {"email": "new@example.com"}
    email_service = Mock()

    # Act: Execute the functionality
    register_user(user_data, email_service)

    # Assert: Verify the behavior
    email_service.send_email.assert_called_once()
```

### Pattern 3: Test Naming Convention

Format: `test_[unit]_[scenario]_[expected_behavior]`

```python
# Good names
def test_validate_email_accepts_valid_simple_email():
def test_validate_email_rejects_email_without_at():
def test_user_login_fails_with_wrong_password():
def test_order_total_includes_tax_for_taxable_items():

# Bad names
def test_email():
def test_validation():
def test_case_1():
```

### Pattern 4: Test Data Builders

Use fixtures for test data:

```python
@pytest.fixture
def valid_user():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "age": 25
    }

def test_user_creation(valid_user):
    user = create_user(valid_user)
    assert user.username == "testuser"
```

## TDD Cycle Diagram

```
┌─────────────────────────────────────────────────┐
│               TDD Cycle (Red-Green-Refactor)    │
└─────────────────────────────────────────────────┘

    1. Write Test      2. Run Test       3. Write Code
   ┌────────────┐     ┌────────────┐     ┌────────────┐
   │            │     │            │     │            │
   │  Write a   │────▶│  Test FAILS│────▶│ Implement  │
   │  Failing   │     │  (🔴 Red)  │     │  Minimal   │
   │  Test      │     │            │     │  Code      │
   └────────────┘     └────────────┘     └────────────┘
                                                │
                                                ▼
    6. Next Test      5. Commit          4. Run Test
   ┌────────────┐     ┌────────────┐     ┌────────────┐
   │            │     │            │     │            │
   │  Move to   │◀────│  Commit    │◀────│ Test PASSES│
   │  Next Test │     │  Working   │     │ (🟢 Green) │
   │            │     │  Code      │     │            │
   └────────────┘     └────────────┘     └────────────┘
        │                   ▲                   │
        │                   │                   ▼
        │              Refactor          Run All Tests
        │             ┌────────────┐     ┌────────────┐
        │             │            │     │            │
        └────────────▶│  Refactor  │────▶│ All PASS   │
                      │  Code      │     │ (🟢 Green) │
                      │ (🔵 Blue)  │     │            │
                      └────────────┘     └────────────┘
```

## Common Pitfalls

### Pitfall 1: Writing Too Much Code Before Testing
**Solution**: Write **one test**, implement **minimal code**, repeat.

### Pitfall 2: Testing Implementation Instead of Behavior
```python
# Bad: Testing internal implementation
def test_calls_database():
    assert service._db.query.called

# Good: Testing behavior
def test_returns_user_by_id():
    user = service.get_user(123)
    assert user.id == 123
```

### Pitfall 3: Test Dependencies
**Solution**: Use fixtures and reset state between tests.

### Pitfall 4: Skipping Refactoring
**Solution**: Always refactor after tests pass.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Writing tests first takes longer" | TDD studies (including research at Microsoft and IBM) consistently show TDD reduces post-release defect rates by 40-90% while increasing development time by only 15-35%; the defect reduction more than compensates for the extra upfront time. |
| "We'll write tests after the implementation when we know the shape of the code" | Tests written after implementation test the implementation, not the requirement; they systematically miss the behavior the implementation got wrong because the wrong behavior looks correct from inside the implementation. |
| "TDD doesn't work for UI or integration code" | TDD applies at every layer; for UI, tests assert component render output and user interaction behavior; for integration, tests use test containers or mocks to assert request/response contracts. |
| "The red phase is just extra work -- I know what the test should pass" | Skipping the red phase means you never confirm the test can fail; a test that never fails is not a test -- it is decorative code that provides false coverage metrics. |
| "Refactoring in the green phase is fine without running tests again" | Refactoring without re-running the suite is not TDD; it is coding with a net that you chose not to deploy. The suite must be green before and after every refactoring step. |

## Verification

- [ ] Every new function or behavior has a failing test written before any implementation code (red phase documented)
- [ ] All tests pass after implementation: `pytest -q` / `npm test` / equivalent exits with code 0 (green phase)
- [ ] Code coverage is 80% or above: `pytest --cov` or equivalent coverage report shows >= 80%
- [ ] No test is skipped or marked `xfail` without a linked issue explaining why
- [ ] Refactoring was performed with the test suite green before and after each step

## Related Skills

- [[plan-before-code]] -- plan the TDD approach before starting the red-green-refactor cycle
- [[test-structure]] -- set up the testing frameworks the cycle runs against
- [[unit-tests]] -- comprehensive unit test patterns for the tests written first
- [[mocks-fixtures]] -- create test data and mocks needed to isolate the unit under test

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Based on**: Anthropic Claude Code Best Practices 2025


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
