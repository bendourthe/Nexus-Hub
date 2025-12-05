---
template_id: python_unit_tests
template_name: Unit Tests - Python
version: 1.0.0
last_updated: 2025-12-03
language: Python
category: test_development
phase: unit_tests
phase_number: 2
difficulty: intermediate
estimated_time_hours: 3-6
prerequisites:

  - test_development/test_structure/python_test_structure.md
related_templates:

  - test_development/test_cases/python_test_cases.md
tools:

  - pytest (8.3.4+)
  - black (24.12.0)
  - mypy (1.13.0)
  - ruff
tags:

  - test-development
  - testing
  - python
---
# Python Unit Tests - Comprehensive Implementation Guide

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup ────────────────────────► │ [COMPLETE]
│ Phase 2: Unit Tests (YOU ARE HERE) ───────────────────► │ ● CURRENT
│ Phase 3: Test Cases Development ──────────────────────► │ [NEXT]
│ Phase 4: Mocks & Fixtures ─────────────────────────────► │
│ Phase 5: Performance Testing ──────────────────────────► │
│ Phase 6: Code Coverage ────────────────────────────────► │
│ Phase 7: Maintenance & CI/CD ──────────────────────────► │
│ Phase 8: Reward Hacking Validation ────────────────────► │
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 1 (Test Structure Setup) should be completed first
**Next Step:** Phase 3 (Test Cases Development) - Integration and E2E tests

---

## Objective

Develop a comprehensive unit testing strategy for Python applications using pytest and unittest frameworks, focusing on test isolation, fast execution, and thorough coverage of individual components following FIRST principles and AAA patterns.

---

## Output Directory Structure

All generated files should be saved to the following directory structure:

```
${OUTPUT_DIR}/
├── templates/           # Reusable test templates and helper scripts
├── assets/             # Diagrams, visualizations, and reference images
└── exports/            # Final documentation and reports
```

---

## Implementation Checklist

### Test Foundation
- [ ] pytest and unittest framework comparison completed
- [ ] Test directory structure established
- [ ] Naming conventions documented
- [ ] conftest.py configuration created
- [ ] pytest.ini or pyproject.toml configured

### Test Patterns
- [ ] Pure function tests implemented
- [ ] Class and method tests created
- [ ] Async/await test patterns established
- [ ] Exception testing patterns documented
- [ ] Parametrized test examples created

### Test Quality
- [ ] Test independence verified
- [ ] Execution time profiled (<1s per test)
- [ ] Mock usage patterns documented
- [ ] Edge case coverage completed
- [ ] Anti-patterns guide created

### Documentation
- [ ] Unit test implementation guide completed (20-30 pages)
- [ ] 50+ example test functions documented
- [ ] Test quality checklist created
- [ ] Code review guidelines established

---

## Prompt Template

Copy the prompt below into your AI assistant to generate comprehensive unit testing guidance:

~~~markdown
# Python Unit Testing Implementation - Comprehensive Guide

## Context
I need comprehensive guidance for implementing unit tests in a Python application using pytest as the primary framework. Generate a complete implementation guide covering principles, patterns, and practical examples.

## CRITICAL: Output Directory Setup

Before starting, create this exact directory structure:

```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

Replace `${OUTPUT_DIR}` with your desired output location (e.g., `unit_tests_python_output`).

---

## Repository Information

To include accurate repository information in documentation:

```bash
git config --get remote.origin.url
```

---

## Phase 1: Unit Testing Fundamentals

### 1.1 What Makes a Good Unit Test

Provide detailed explanation of:

**FIRST Principles:**
- **Fast** - Unit tests should execute in milliseconds (target: <100ms per test)
  - Why speed matters for developer productivity
  - How to identify slow tests
  - Techniques to optimize test execution time

- **Independent** - Tests must not depend on each other or shared state
  - How to verify test independence
  - Running tests in random order
  - Avoiding test pollution

- **Repeatable** - Same results every time, in any environment
  - Dealing with time-dependent code
  - Handling randomness in tests
  - Environment isolation techniques

- **Self-validating** - Clear pass/fail without manual inspection
  - Writing clear assertions
  - Meaningful error messages
  - Avoiding print-debugging in tests

- **Timely** - Written before or alongside production code
  - Test-Driven Development (TDD) overview
  - Benefits of early test writing
  - Maintaining test coverage during refactoring

**AAA Pattern (Arrange-Act-Assert):**
```python
def test_calculate_discount():
    # Arrange - Set up test data and preconditions
    original_price = 100.0
    discount_rate = 0.20
    calculator = PriceCalculator()

    # Act - Execute the function being tested
    final_price = calculator.calculate_discount(original_price, discount_rate)

    # Assert - Verify the expected outcome
    assert final_price == 80.0
    assert calculator.last_discount == 20.0
```

Explain:
- Why separating these phases improves readability
- How to handle tests with complex setup
- When to use helper methods for arrangement
- Dealing with multiple assertions (when appropriate)

### 1.2 Unit vs Integration vs E2E Testing

Create a comparison table:

| Aspect | Unit Test | Integration Test | E2E Test |
|--------|-----------|------------------|----------|
| **Scope** | Single function/method | Multiple components | Entire system |
| **Dependencies** | Mocked/stubbed | Real (some mocked) | Real |
| **Speed** | <100ms | <1s | Seconds to minutes |
| **Isolation** | Complete | Partial | None |
| **Failure Reason** | Specific function | Component interaction | System behavior |
| **Maintenance** | Easy | Moderate | Complex |
| **Cost** | Low | Medium | High |

Provide guidance on:
- When to write unit tests vs integration tests
- The testing pyramid concept (70% unit, 20% integration, 10% E2E)
- How to identify if a test is truly a unit test
- Converting integration tests to unit tests

### 1.3 Common Unit Test Anti-Patterns

Document these anti-patterns with examples:

**Anti-Pattern 1: Testing Implementation Instead of Behavior**
```python
# BAD - Tests implementation details
def test_sort_uses_quicksort():
    sorter = Sorter()
    result = sorter.sort([3, 1, 2])
    assert sorter.algorithm_used == "quicksort"  # Implementation detail

# GOOD - Tests behavior
def test_sort_returns_ascending_order():
    sorter = Sorter()
    result = sorter.sort([3, 1, 2])
    assert result == [1, 2, 3]  # Behavior
```

**Anti-Pattern 2: Multiple Unrelated Assertions**
```python
# BAD - Tests multiple unrelated concerns
def test_user_operations():
    user = User("John", "john@example.com")
    assert user.name == "John"
    assert user.email == "john@example.com"
    assert user.created_at is not None
    assert user.validate_email() is True
    assert user.to_dict()["name"] == "John"

# GOOD - Separate tests for separate concerns
def test_user_initialization_sets_name():
    user = User("John", "john@example.com")
    assert user.name == "John"

def test_user_initialization_sets_email():
    user = User("John", "john@example.com")
    assert user.email == "john@example.com"

def test_user_validates_correct_email_format():
    user = User("John", "john@example.com")
    assert user.validate_email() is True
```

**Anti-Pattern 3: Slow Tests**
```python
# BAD - Slow test with unnecessary delays
def test_process_data():
    processor = DataProcessor()
    time.sleep(1)  # Unnecessary delay
    result = processor.process([1, 2, 3])
    assert result == [2, 4, 6]

# GOOD - Fast test with no delays
def test_process_data():
    processor = DataProcessor()
    result = processor.process([1, 2, 3])
    assert result == [2, 4, 6]
```

**Anti-Pattern 4: Test Interdependencies**
```python
# BAD - Tests depend on execution order
class TestUserWorkflow:
    def test_1_create_user(self):
        self.user = User("John")
        assert self.user.name == "John"

    def test_2_update_user(self):
        self.user.name = "Jane"  # Depends on test_1
        assert self.user.name == "Jane"

# GOOD - Independent tests
class TestUserWorkflow:
    def test_create_user(self):
        user = User("John")
        assert user.name == "John"

    def test_update_user(self):
        user = User("John")  # Create fresh instance
        user.name = "Jane"
        assert user.name == "Jane"
```

**Anti-Pattern 5: Excessive Mocking**
```python
# BAD - Mocking too much, testing mock behavior
def test_calculate_total():
    mock_calculator = Mock()
    mock_calculator.add.return_value = 10
    mock_calculator.multiply.return_value = 20
    mock_calculator.subtract.return_value = 5

    service = Service(mock_calculator)
    result = service.calculate_total([1, 2, 3])

    assert mock_calculator.add.called  # Testing mock, not real code

# GOOD - Test real logic, mock only external dependencies
def test_calculate_total():
    calculator = Calculator()  # Real calculator
    service = Service(calculator)
    result = service.calculate_total([1, 2, 3])
    assert result == 6  # Testing real behavior
```

**Anti-Pattern 6: Unclear Test Names**
```python
# BAD - Unclear what is being tested
def test_user_1():
    pass

def test_edge_case():
    pass

def test_foo():
    pass

# GOOD - Clear, descriptive names
def test_user_initialization_with_valid_email_succeeds():
    pass

def test_division_by_zero_raises_value_error():
    pass

def test_empty_list_returns_none():
    pass
```

Provide guidance for identifying and fixing each anti-pattern.

---

## Phase 2: Test Organization and Structure

### 2.1 Directory Structure for Unit Tests

Recommend this structure:

```
project/
├── src/
│   ├── __init__.py
│   ├── calculator.py
│   ├── user.py
│   └── services/
│       ├── __init__.py
│       ├── payment.py
│       └── notification.py
└── tests/
    ├── conftest.py              # Shared fixtures and configuration
    ├── __init__.py
    ├── unit/                    # Unit tests separate from integration
    │   ├── __init__.py
    │   ├── test_calculator.py   # Mirrors src structure
    │   ├── test_user.py
    │   └── services/
    │       ├── __init__.py
    │       ├── test_payment.py
    │       └── test_notification.py
    ├── integration/
    │   └── ...
    └── e2e/
        └── ...
```

Explain:
- Why mirror the source structure
- Benefits of separating unit/integration/e2e tests
- When to deviate from this structure
- How pytest discovers tests

### 2.2 Test Naming Conventions

Provide detailed naming guidelines:

**File Naming:**
- `test_<module_name>.py` - Always prefix with `test_`
- Examples: `test_calculator.py`, `test_user_service.py`

**Class Naming:**
- `Test<ClassName>` - Use PascalCase with Test prefix
- Group related tests in classes
- Examples: `TestCalculator`, `TestUserRegistration`

**Function Naming:**
- `test_<what>_<condition>_<expected>` - Descriptive pattern
- Use snake_case
- Examples:
  ```python
  def test_calculate_discount_with_valid_rate_returns_discounted_price():
      pass

  def test_divide_by_zero_raises_value_error():
      pass

  def test_empty_list_returns_none():
      pass

  def test_user_login_with_invalid_password_returns_false():
      pass
  ```

**Why This Matters:**
- Test names serve as documentation
- Failed tests should clearly indicate what went wrong
- No need to read test code to understand purpose

### 2.3 conftest.py Configuration

Provide comprehensive `conftest.py` example:

```python
"""
Shared test configuration and fixtures.

This file is automatically discovered by pytest and provides
fixtures and configuration for all tests in the project.
"""
import pytest
import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============================================================================
# Session-scoped fixtures (created once per test session)
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration settings."""
    return {
        "database_url": "sqlite:///:memory:",
        "api_timeout": 5,
        "max_retries": 3
    }


# ============================================================================
# Function-scoped fixtures (created for each test)
# ============================================================================

@pytest.fixture
def sample_user_data():
    """Provide sample user data for testing."""
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30
    }


@pytest.fixture
def calculator():
    """Provide a fresh Calculator instance."""
    from calculator import Calculator
    return Calculator()


# ============================================================================
# Fixture factories (for creating multiple instances)
# ============================================================================

@pytest.fixture
def user_factory():
    """Factory for creating User instances with custom data."""
    from user import User

    def _create_user(name="John", email="john@example.com", age=30):
        return User(name=name, email=email, age=age)

    return _create_user


# ============================================================================
# Cleanup fixtures (with teardown logic)
# ============================================================================

@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file and clean it up after test."""
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("test content")

    yield file_path

    # Cleanup happens automatically with tmp_path, but you can add custom logic
    if file_path.exists():
        file_path.unlink()


# ============================================================================
# Parametrized fixtures
# ============================================================================

@pytest.fixture(params=[1, 2, 3, 10, 100])
def sample_number(request):
    """Provide various numbers for parametrized testing."""
    return request.param


# ============================================================================
# Mock fixtures
# ============================================================================

@pytest.fixture
def mock_api_client(monkeypatch):
    """Mock external API client."""
    from unittest.mock import Mock

    mock_client = Mock()
    mock_client.get.return_value = {"status": "success", "data": [1, 2, 3]}
    mock_client.post.return_value = {"status": "success", "id": 123}

    # Monkeypatch the real client with the mock
    import services.api_client
    monkeypatch.setattr(services.api_client, "APIClient", lambda: mock_client)

    return mock_client


# ============================================================================
# Test markers
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


# ============================================================================
# pytest hooks for custom behavior
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """Automatically add markers based on test location."""
    for item in items:
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
```

Explain each section and when to use different fixture scopes.

### 2.4 pytest Configuration

Provide `pytest.ini` example:

```ini
[pytest]
# Test discovery patterns
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Test paths
testpaths = tests/unit

# Output options
addopts =
    -v                          # Verbose output
    --strict-markers           # Fail on unknown markers
    --tb=short                 # Shorter traceback format
    --cov=src                  # Coverage for src directory
    --cov-report=html          # HTML coverage report
    --cov-report=term-missing  # Show missing lines in terminal
    --durations=10             # Show 10 slowest tests
    -m "not slow"              # Skip slow tests by default

# Markers
markers =
    slow: marks tests as slow
    unit: marks tests as unit tests
    integration: marks tests as integration tests
    smoke: marks tests as smoke tests

# Coverage options
[coverage:run]
omit =
    tests/*
    */venv/*
    */virtualenv/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False
```

Alternative `pyproject.toml` configuration:

```toml
[tool.pytest.ini_options]
testpaths = ["tests/unit"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
    "--cov=src",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--durations=10",
    "-m", "not slow"
]
markers = [
    "slow: marks tests as slow",
    "unit: marks tests as unit tests",
    "integration: marks tests as integration tests"
]

[tool.coverage.run]
omit = ["tests/*", "*/venv/*"]

[tool.coverage.report]
precision = 2
show_missing = true
```

---

## Phase 3: Testing Different Component Types

### 3.1 Testing Pure Functions

Pure functions (no side effects, deterministic) are easiest to test.

**Example Function:**
```python
# src/calculator.py
def calculate_discount(price: float, discount_rate: float) -> float:
    """
    Calculate discounted price.

    Args:
        price: Original price
        discount_rate: Discount rate (0.0 to 1.0)

    Returns:
        Final price after discount

    Raises:
        ValueError: If price is negative or discount_rate is invalid
    """
    if price < 0:
        raise ValueError("Price cannot be negative")
    if not 0 <= discount_rate <= 1:
        raise ValueError("Discount rate must be between 0 and 1")

    return price * (1 - discount_rate)
```

**Comprehensive Tests:**
```python
# tests/unit/test_calculator.py
import pytest
from calculator import calculate_discount


class TestCalculateDiscount:
    """Tests for calculate_discount function."""

    def test_no_discount_returns_original_price(self):
        """Test that 0% discount returns original price."""
        result = calculate_discount(100.0, 0.0)
        assert result == 100.0

    def test_full_discount_returns_zero(self):
        """Test that 100% discount returns zero."""
        result = calculate_discount(100.0, 1.0)
        assert result == 0.0

    def test_twenty_percent_discount_calculates_correctly(self):
        """Test that 20% discount is calculated correctly."""
        result = calculate_discount(100.0, 0.20)
        assert result == 80.0

    def test_fifty_percent_discount_calculates_correctly(self):
        """Test that 50% discount is calculated correctly."""
        result = calculate_discount(200.0, 0.50)
        assert result == 100.0

    def test_small_price_with_discount(self):
        """Test discount calculation with small price."""
        result = calculate_discount(5.0, 0.10)
        assert result == 4.5

    def test_large_price_with_discount(self):
        """Test discount calculation with large price."""
        result = calculate_discount(10000.0, 0.15)
        assert result == 8500.0

    def test_floating_point_precision(self):
        """Test that floating point calculations are accurate."""
        result = calculate_discount(99.99, 0.333)
        assert abs(result - 66.7033) < 0.01  # Use approximate comparison

    def test_negative_price_raises_value_error(self):
        """Test that negative price raises ValueError."""
        with pytest.raises(ValueError, match="Price cannot be negative"):
            calculate_discount(-100.0, 0.20)

    def test_discount_rate_below_zero_raises_value_error(self):
        """Test that discount rate below 0 raises ValueError."""
        with pytest.raises(ValueError, match="Discount rate must be between 0 and 1"):
            calculate_discount(100.0, -0.10)

    def test_discount_rate_above_one_raises_value_error(self):
        """Test that discount rate above 1 raises ValueError."""
        with pytest.raises(ValueError, match="Discount rate must be between 0 and 1"):
            calculate_discount(100.0, 1.5)

    def test_zero_price_returns_zero(self):
        """Test that zero price returns zero regardless of discount."""
        result = calculate_discount(0.0, 0.50)
        assert result == 0.0

    @pytest.mark.parametrize("price,discount,expected", [
        (100.0, 0.10, 90.0),
        (50.0, 0.20, 40.0),
        (200.0, 0.25, 150.0),
        (75.0, 0.333, 50.025),
    ])
    def test_various_discount_combinations(self, price, discount, expected):
        """Test multiple price and discount combinations."""
        result = calculate_discount(price, discount)
        assert abs(result - expected) < 0.01
```

**Key Principles:**
- Test happy path (normal inputs)
- Test edge cases (boundaries: 0%, 100%, 0 price)
- Test error conditions (negative price, invalid discount)
- Test floating-point precision with approximate comparison
- Use parametrized tests for multiple similar cases

### 3.2 Testing Classes and Methods

**Example Class:**
```python
# src/user.py
from datetime import datetime
from typing import Optional
import re


class User:
    """Represents a user in the system."""

    def __init__(self, name: str, email: str, age: Optional[int] = None):
        """Initialize user with validation."""
        if not name:
            raise ValueError("Name cannot be empty")
        if not self._is_valid_email(email):
            raise ValueError("Invalid email format")
        if age is not None and age < 0:
            raise ValueError("Age cannot be negative")

        self._name = name
        self._email = email
        self._age = age
        self._created_at = datetime.now()
        self._active = True

    @property
    def name(self) -> str:
        """Get user name."""
        return self._name

    @property
    def email(self) -> str:
        """Get user email."""
        return self._email

    @property
    def age(self) -> Optional[int]:
        """Get user age."""
        return self._age

    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self._active

    def deactivate(self) -> None:
        """Deactivate the user."""
        self._active = False

    def activate(self) -> None:
        """Activate the user."""
        self._active = True

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            "name": self._name,
            "email": self._email,
            "age": self._age,
            "active": self._active,
            "created_at": self._created_at.isoformat()
        }
```

**Comprehensive Tests:**
```python
# tests/unit/test_user.py
import pytest
from datetime import datetime
from user import User


class TestUserInitialization:
    """Tests for User initialization."""

    def test_initialization_with_all_parameters(self):
        """Test user initialization with all parameters."""
        user = User("John Doe", "john@example.com", 30)

        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.age == 30
        assert user.is_active is True

    def test_initialization_without_age(self):
        """Test user initialization without age parameter."""
        user = User("Jane Doe", "jane@example.com")

        assert user.name == "Jane Doe"
        assert user.email == "jane@example.com"
        assert user.age is None

    def test_initialization_sets_created_at(self):
        """Test that created_at is set during initialization."""
        before = datetime.now()
        user = User("John", "john@example.com")
        after = datetime.now()

        # created_at should be between before and after
        assert before <= user._created_at <= after

    def test_empty_name_raises_value_error(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Name cannot be empty"):
            User("", "john@example.com")

    def test_invalid_email_format_raises_value_error(self):
        """Test that invalid email raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email format"):
            User("John", "invalid-email")

    def test_negative_age_raises_value_error(self):
        """Test that negative age raises ValueError."""
        with pytest.raises(ValueError, match="Age cannot be negative"):
            User("John", "john@example.com", -5)

    @pytest.mark.parametrize("email", [
        "user@example.com",
        "first.last@example.com",
        "user+tag@example.co.uk",
        "user123@subdomain.example.com",
    ])
    def test_valid_email_formats_accepted(self, email):
        """Test that various valid email formats are accepted."""
        user = User("John", email)
        assert user.email == email

    @pytest.mark.parametrize("email", [
        "invalid",
        "@example.com",
        "user@",
        "user @example.com",
        "user@.com",
    ])
    def test_invalid_email_formats_rejected(self, email):
        """Test that various invalid email formats are rejected."""
        with pytest.raises(ValueError, match="Invalid email format"):
            User("John", email)


class TestUserProperties:
    """Tests for User properties."""

    def test_name_property_returns_correct_value(self):
        """Test that name property returns correct value."""
        user = User("John", "john@example.com")
        assert user.name == "John"

    def test_email_property_returns_correct_value(self):
        """Test that email property returns correct value."""
        user = User("John", "john@example.com")
        assert user.email == "john@example.com"

    def test_age_property_returns_correct_value(self):
        """Test that age property returns correct value."""
        user = User("John", "john@example.com", 25)
        assert user.age == 25

    def test_age_property_returns_none_when_not_set(self):
        """Test that age property returns None when not provided."""
        user = User("John", "john@example.com")
        assert user.age is None

    def test_is_active_property_returns_true_initially(self):
        """Test that is_active is True for new users."""
        user = User("John", "john@example.com")
        assert user.is_active is True


class TestUserActivation:
    """Tests for User activation/deactivation."""

    def test_deactivate_sets_is_active_to_false(self):
        """Test that deactivate sets is_active to False."""
        user = User("John", "john@example.com")
        user.deactivate()
        assert user.is_active is False

    def test_activate_sets_is_active_to_true(self):
        """Test that activate sets is_active to True."""
        user = User("John", "john@example.com")
        user.deactivate()
        user.activate()
        assert user.is_active is True

    def test_multiple_deactivations_remain_false(self):
        """Test that multiple deactivations keep user inactive."""
        user = User("John", "john@example.com")
        user.deactivate()
        user.deactivate()
        assert user.is_active is False

    def test_multiple_activations_remain_true(self):
        """Test that multiple activations keep user active."""
        user = User("John", "john@example.com")
        user.activate()
        user.activate()
        assert user.is_active is True


class TestUserToDictMethod:
    """Tests for User to_dict method."""

    def test_to_dict_contains_all_fields(self):
        """Test that to_dict returns all user fields."""
        user = User("John", "john@example.com", 30)
        result = user.to_dict()

        assert "name" in result
        assert "email" in result
        assert "age" in result
        assert "active" in result
        assert "created_at" in result

    def test_to_dict_values_match_user_properties(self):
        """Test that to_dict values match user properties."""
        user = User("John", "john@example.com", 30)
        result = user.to_dict()

        assert result["name"] == "John"
        assert result["email"] == "john@example.com"
        assert result["age"] == 30
        assert result["active"] is True

    def test_to_dict_handles_none_age(self):
        """Test that to_dict handles None age correctly."""
        user = User("John", "john@example.com")
        result = user.to_dict()

        assert result["age"] is None

    def test_to_dict_created_at_is_iso_format(self):
        """Test that created_at is returned in ISO format."""
        user = User("John", "john@example.com")
        result = user.to_dict()

        # Should be able to parse ISO format
        datetime.fromisoformat(result["created_at"])

    def test_to_dict_reflects_deactivated_user(self):
        """Test that to_dict reflects user deactivation."""
        user = User("John", "john@example.com")
        user.deactivate()
        result = user.to_dict()

        assert result["active"] is False


# Fixture for creating users in tests
@pytest.fixture
def sample_user():
    """Provide a sample user for testing."""
    return User("John Doe", "john@example.com", 30)


class TestUserFixtureUsage:
    """Example of using fixtures in tests."""

    def test_fixture_provides_valid_user(self, sample_user):
        """Test that fixture provides a valid user."""
        assert sample_user.name == "John Doe"
        assert sample_user.email == "john@example.com"
        assert sample_user.age == 30

    def test_fixture_creates_independent_instances(self, sample_user):
        """Test that fixture creates independent instances for each test."""
        sample_user.deactivate()
        assert sample_user.is_active is False

    def test_fixture_instance_does_not_affect_other_tests(self, sample_user):
        """Test that modifications in one test don't affect others."""
        # This test should pass even if previous test modified the user
        assert sample_user.is_active is True
```

**Key Principles:**
- Group related tests into classes
- Test each method independently
- Test properties and state changes
- Use fixtures for common setup
- Test both valid and invalid inputs
- Verify error messages in exceptions

### 3.3 Testing Asynchronous Code

**Example Async Function:**
```python
# src/async_operations.py
import asyncio
from typing import List


async def fetch_data(url: str, timeout: float = 5.0) -> dict:
    """
    Fetch data from URL asynchronously.

    Args:
        url: URL to fetch from
        timeout: Request timeout in seconds

    Returns:
        Response data as dictionary

    Raises:
        ValueError: If URL is empty
        TimeoutError: If request times out
    """
    if not url:
        raise ValueError("URL cannot be empty")

    # Simulate async operation
    await asyncio.sleep(0.1)

    if "timeout" in url:
        raise TimeoutError("Request timed out")

    return {"status": "success", "url": url}


async def fetch_multiple(urls: List[str]) -> List[dict]:
    """
    Fetch data from multiple URLs concurrently.

    Args:
        urls: List of URLs to fetch

    Returns:
        List of response dictionaries
    """
    tasks = [fetch_data(url) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

**Comprehensive Tests:**
```python
# tests/unit/test_async_operations.py
import pytest
import asyncio
from async_operations import fetch_data, fetch_multiple


class TestFetchData:
    """Tests for async fetch_data function."""

    @pytest.mark.asyncio
    async def test_fetch_data_returns_success_response(self):
        """Test that fetch_data returns success response."""
        result = await fetch_data("https://example.com")

        assert result["status"] == "success"
        assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_fetch_data_with_custom_timeout(self):
        """Test that custom timeout is accepted."""
        result = await fetch_data("https://example.com", timeout=10.0)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_empty_url_raises_value_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            await fetch_data("")

    @pytest.mark.asyncio
    async def test_timeout_url_raises_timeout_error(self):
        """Test that timeout URL raises TimeoutError."""
        with pytest.raises(TimeoutError, match="Request timed out"):
            await fetch_data("https://timeout.com")

    @pytest.mark.asyncio
    async def test_multiple_calls_are_independent(self):
        """Test that multiple async calls work independently."""
        result1 = await fetch_data("https://example1.com")
        result2 = await fetch_data("https://example2.com")

        assert result1["url"] == "https://example1.com"
        assert result2["url"] == "https://example2.com"


class TestFetchMultiple:
    """Tests for async fetch_multiple function."""

    @pytest.mark.asyncio
    async def test_fetch_multiple_returns_all_results(self):
        """Test that fetch_multiple returns results for all URLs."""
        urls = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com"
        ]
        results = await fetch_multiple(urls)

        assert len(results) == 3
        assert all(isinstance(r, dict) for r in results)

    @pytest.mark.asyncio
    async def test_fetch_multiple_with_single_url(self):
        """Test fetch_multiple with single URL."""
        results = await fetch_multiple(["https://example.com"])

        assert len(results) == 1
        assert results[0]["status"] == "success"

    @pytest.mark.asyncio
    async def test_fetch_multiple_with_empty_list(self):
        """Test fetch_multiple with empty list."""
        results = await fetch_multiple([])
        assert results == []

    @pytest.mark.asyncio
    async def test_fetch_multiple_handles_exceptions(self):
        """Test that fetch_multiple handles exceptions gracefully."""
        urls = [
            "https://example.com",
            "https://timeout.com",  # Will raise TimeoutError
            "https://example2.com"
        ]
        results = await fetch_multiple(urls)

        assert len(results) == 3
        assert isinstance(results[0], dict)
        assert isinstance(results[1], TimeoutError)
        assert isinstance(results[2], dict)


# Alternative: Using pytest-asyncio fixtures
@pytest.fixture
async def async_client():
    """Provide an async client for testing."""
    # Setup
    client = {"connected": True}
    yield client
    # Teardown
    client["connected"] = False


class TestAsyncFixtures:
    """Example of using async fixtures."""

    @pytest.mark.asyncio
    async def test_async_fixture_usage(self, async_client):
        """Test using async fixtures."""
        assert async_client["connected"] is True
```

**Key Principles:**
- Use `@pytest.mark.asyncio` for async tests
- Test async functions with `await`
- Install `pytest-asyncio` package
- Test concurrent execution
- Handle exceptions in async code
- Use async fixtures when needed

**Configuration for pytest-asyncio:**
```ini
# pytest.ini
[pytest]
asyncio_mode = auto
```

### 3.4 Testing Generators and Iterators

**Example Generator:**
```python
# src/generators.py
from typing import Iterator, List


def fibonacci(n: int) -> Iterator[int]:
    """
    Generate fibonacci sequence up to n terms.

    Args:
        n: Number of terms to generate

    Yields:
        Next fibonacci number

    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n cannot be negative")

    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b


def chunk_list(items: List, chunk_size: int) -> Iterator[List]:
    """
    Split list into chunks of specified size.

    Args:
        items: List to chunk
        chunk_size: Size of each chunk

    Yields:
        Next chunk

    Raises:
        ValueError: If chunk_size is less than 1
    """
    if chunk_size < 1:
        raise ValueError("Chunk size must be at least 1")

    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]
```

**Comprehensive Tests:**
```python
# tests/unit/test_generators.py
import pytest
from generators import fibonacci, chunk_list


class TestFibonacci:
    """Tests for fibonacci generator."""

    def test_fibonacci_first_five_terms(self):
        """Test that first 5 fibonacci terms are correct."""
        result = list(fibonacci(5))
        assert result == [0, 1, 1, 2, 3]

    def test_fibonacci_first_ten_terms(self):
        """Test that first 10 fibonacci terms are correct."""
        result = list(fibonacci(10))
        assert result == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

    def test_fibonacci_zero_terms_returns_empty(self):
        """Test that 0 terms returns empty sequence."""
        result = list(fibonacci(0))
        assert result == []

    def test_fibonacci_one_term_returns_zero(self):
        """Test that 1 term returns [0]."""
        result = list(fibonacci(1))
        assert result == [0]

    def test_fibonacci_negative_raises_value_error(self):
        """Test that negative n raises ValueError."""
        with pytest.raises(ValueError, match="n cannot be negative"):
            list(fibonacci(-5))

    def test_fibonacci_is_lazy(self):
        """Test that fibonacci is lazy (doesn't compute all at once)."""
        gen = fibonacci(1000000)  # Large number
        first = next(gen)  # Should return quickly
        assert first == 0

    def test_fibonacci_can_be_consumed_partially(self):
        """Test that generator can be consumed partially."""
        gen = fibonacci(10)
        first_three = [next(gen) for _ in range(3)]
        assert first_three == [0, 1, 1]

        # Continue consuming
        next_two = [next(gen) for _ in range(2)]
        assert next_two == [2, 3]


class TestChunkList:
    """Tests for chunk_list generator."""

    def test_chunk_list_with_even_division(self):
        """Test chunking list that divides evenly."""
        result = list(chunk_list([1, 2, 3, 4, 5, 6], 2))
        assert result == [[1, 2], [3, 4], [5, 6]]

    def test_chunk_list_with_remainder(self):
        """Test chunking list with remainder."""
        result = list(chunk_list([1, 2, 3, 4, 5], 2))
        assert result == [[1, 2], [3, 4], [5]]

    def test_chunk_list_with_chunk_size_one(self):
        """Test chunking with size 1."""
        result = list(chunk_list([1, 2, 3], 1))
        assert result == [[1], [2], [3]]

    def test_chunk_list_with_chunk_size_larger_than_list(self):
        """Test chunking with size larger than list."""
        result = list(chunk_list([1, 2, 3], 10))
        assert result == [[1, 2, 3]]

    def test_chunk_list_with_empty_list(self):
        """Test chunking empty list."""
        result = list(chunk_list([], 2))
        assert result == []

    def test_chunk_list_with_invalid_chunk_size(self):
        """Test that chunk size < 1 raises ValueError."""
        with pytest.raises(ValueError, match="Chunk size must be at least 1"):
            list(chunk_list([1, 2, 3], 0))

    def test_chunk_list_is_lazy(self):
        """Test that chunk_list is lazy."""
        gen = chunk_list(list(range(1000000)), 100)
        first_chunk = next(gen)
        assert len(first_chunk) == 100
        assert first_chunk[0] == 0
```

**Key Principles:**
- Convert generators to lists for testing complete sequences
- Test lazy evaluation (generators don't compute all at once)
- Test partial consumption with `next()`
- Test empty cases
- Test boundary conditions
- Verify generator can be exhausted

### 3.5 Testing Decorators

**Example Decorator:**
```python
# src/decorators.py
import time
import functools
from typing import Callable, Any


def timer(func: Callable) -> Callable:
    """Decorator that measures function execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.4f} seconds")
        return result
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0):
    """Decorator that retries function on failure."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def validate_positive(func: Callable) -> Callable:
    """Decorator that validates all numeric arguments are positive."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        for arg in args:
            if isinstance(arg, (int, float)) and arg < 0:
                raise ValueError(f"Argument must be positive, got {arg}")
        for value in kwargs.values():
            if isinstance(value, (int, float)) and value < 0:
                raise ValueError(f"Argument must be positive, got {value}")
        return func(*args, **kwargs)
    return wrapper
```

**Comprehensive Tests:**
```python
# tests/unit/test_decorators.py
import pytest
import time
from unittest.mock import patch, Mock
from decorators import timer, retry, validate_positive


class TestTimerDecorator:
    """Tests for timer decorator."""

    def test_timer_returns_function_result(self, capsys):
        """Test that timer returns original function result."""
        @timer
        def add(a, b):
            return a + b

        result = add(2, 3)
        assert result == 5

    def test_timer_prints_execution_time(self, capsys):
        """Test that timer prints execution time."""
        @timer
        def slow_function():
            time.sleep(0.1)
            return "done"

        result = slow_function()
        captured = capsys.readouterr()

        assert result == "done"
        assert "slow_function took" in captured.out
        assert "seconds" in captured.out

    def test_timer_preserves_function_name(self):
        """Test that timer preserves original function name."""
        @timer
        def my_function():
            pass

        assert my_function.__name__ == "my_function"

    def test_timer_works_with_arguments(self):
        """Test that timer works with function arguments."""
        @timer
        def multiply(a, b, c=1):
            return a * b * c

        result = multiply(2, 3, c=4)
        assert result == 24


class TestRetryDecorator:
    """Tests for retry decorator."""

    def test_retry_returns_result_on_first_success(self):
        """Test that retry returns result immediately on success."""
        @retry(max_attempts=3)
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_retry_attempts_multiple_times_on_failure(self):
        """Test that retry attempts multiple times on failure."""
        attempt_count = {"count": 0}

        @retry(max_attempts=3, delay=0.01)
        def failing_function():
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:
                raise ValueError("Not yet")
            return "success"

        result = failing_function()
        assert result == "success"
        assert attempt_count["count"] == 3

    def test_retry_raises_last_exception_after_max_attempts(self):
        """Test that retry raises last exception after all attempts fail."""
        @retry(max_attempts=3, delay=0.01)
        def always_failing():
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            always_failing()

    def test_retry_with_custom_max_attempts(self):
        """Test retry with custom max attempts."""
        attempt_count = {"count": 0}

        @retry(max_attempts=5, delay=0.01)
        def function_succeeds_on_fifth():
            attempt_count["count"] += 1
            if attempt_count["count"] < 5:
                raise ValueError("Not yet")
            return "success"

        result = function_succeeds_on_fifth()
        assert result == "success"
        assert attempt_count["count"] == 5

    def test_retry_preserves_function_name(self):
        """Test that retry preserves original function name."""
        @retry(max_attempts=3)
        def my_function():
            pass

        assert my_function.__name__ == "my_function"

    @patch('time.sleep')
    def test_retry_delays_between_attempts(self, mock_sleep):
        """Test that retry delays between attempts."""
        attempt_count = {"count": 0}

        @retry(max_attempts=3, delay=1.0)
        def failing_function():
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:
                raise ValueError("Not yet")
            return "success"

        result = failing_function()
        assert result == "success"
        assert mock_sleep.call_count == 2  # 2 delays before success on 3rd attempt
        mock_sleep.assert_called_with(1.0)


class TestValidatePositiveDecorator:
    """Tests for validate_positive decorator."""

    def test_validate_positive_allows_positive_integers(self):
        """Test that positive integers are allowed."""
        @validate_positive
        def add(a, b):
            return a + b

        result = add(5, 10)
        assert result == 15

    def test_validate_positive_allows_positive_floats(self):
        """Test that positive floats are allowed."""
        @validate_positive
        def multiply(a, b):
            return a * b

        result = multiply(2.5, 3.5)
        assert result == 8.75

    def test_validate_positive_rejects_negative_integers(self):
        """Test that negative integers are rejected."""
        @validate_positive
        def add(a, b):
            return a + b

        with pytest.raises(ValueError, match="Argument must be positive"):
            add(-5, 10)

    def test_validate_positive_rejects_negative_floats(self):
        """Test that negative floats are rejected."""
        @validate_positive
        def multiply(a, b):
            return a * b

        with pytest.raises(ValueError, match="Argument must be positive"):
            multiply(2.5, -3.5)

    def test_validate_positive_allows_non_numeric_arguments(self):
        """Test that non-numeric arguments are allowed."""
        @validate_positive
        def concat(a, b):
            return str(a) + str(b)

        result = concat("hello", "world")
        assert result == "helloworld"

    def test_validate_positive_works_with_kwargs(self):
        """Test that validation works with keyword arguments."""
        @validate_positive
        def calculate(a, b, multiplier=1):
            return (a + b) * multiplier

        with pytest.raises(ValueError, match="Argument must be positive"):
            calculate(5, 10, multiplier=-2)

    def test_validate_positive_allows_zero(self):
        """Test that zero is allowed (not negative)."""
        @validate_positive
        def add(a, b):
            return a + b

        result = add(0, 5)
        assert result == 5

    def test_validate_positive_preserves_function_name(self):
        """Test that decorator preserves function name."""
        @validate_positive
        def my_function(a):
            return a * 2

        assert my_function.__name__ == "my_function"
```

**Key Principles:**
- Test that decorator returns function result
- Test that decorator preserves function metadata (`functools.wraps`)
- Test decorator behavior (timing, retrying, validation)
- Use `capsys` fixture to capture print output
- Use `patch` to mock external dependencies (like `time.sleep`)
- Test with and without arguments
- Test with both args and kwargs

### 3.6 Testing Context Managers

**Example Context Manager:**
```python
# src/context_managers.py
from typing import Optional
import os


class TempDirectory:
    """Context manager for creating and cleaning up temporary directories."""

    def __init__(self, base_path: str = "/tmp"):
        """
        Initialize temporary directory context manager.

        Args:
            base_path: Base path for temporary directory
        """
        self.base_path = base_path
        self.temp_dir: Optional[str] = None

    def __enter__(self) -> str:
        """Create temporary directory and return its path."""
        import tempfile
        self.temp_dir = tempfile.mkdtemp(dir=self.base_path)
        return self.temp_dir

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Clean up temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)


class FileWriter:
    """Context manager for safe file writing."""

    def __init__(self, filename: str, mode: str = 'w'):
        """
        Initialize file writer.

        Args:
            filename: File to write to
            mode: File mode
        """
        self.filename = filename
        self.mode = mode
        self.file = None

    def __enter__(self):
        """Open file and return file object."""
        self.file = open(self.filename, self.mode)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close file, even if exception occurred."""
        if self.file:
            self.file.close()
        return False  # Don't suppress exceptions
```

**Comprehensive Tests:**
```python
# tests/unit/test_context_managers.py
import pytest
import os
import tempfile
from pathlib import Path
from context_managers import TempDirectory, FileWriter


class TestTempDirectory:
    """Tests for TempDirectory context manager."""

    def test_temp_directory_creates_directory(self):
        """Test that temp directory is created."""
        with TempDirectory() as temp_dir:
            assert os.path.exists(temp_dir)
            assert os.path.isdir(temp_dir)

    def test_temp_directory_cleans_up_after_use(self):
        """Test that temp directory is deleted after use."""
        temp_dir_path = None
        with TempDirectory() as temp_dir:
            temp_dir_path = temp_dir
            # Directory exists inside context
            assert os.path.exists(temp_dir_path)

        # Directory is deleted after context
        assert not os.path.exists(temp_dir_path)

    def test_temp_directory_can_write_files(self):
        """Test that files can be written in temp directory."""
        with TempDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            with open(file_path, 'w') as f:
                f.write("test content")

            assert os.path.exists(file_path)
            with open(file_path, 'r') as f:
                assert f.read() == "test content"

    def test_temp_directory_cleans_up_files_inside(self):
        """Test that files inside temp directory are cleaned up."""
        file_path = None
        with TempDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            with open(file_path, 'w') as f:
                f.write("test content")

        assert not os.path.exists(file_path)

    def test_temp_directory_cleans_up_on_exception(self):
        """Test that temp directory is cleaned up even if exception occurs."""
        temp_dir_path = None
        try:
            with TempDirectory() as temp_dir:
                temp_dir_path = temp_dir
                raise ValueError("Test exception")
        except ValueError:
            pass

        assert not os.path.exists(temp_dir_path)

    def test_temp_directory_with_custom_base_path(self, tmp_path):
        """Test that custom base path is used."""
        with TempDirectory(base_path=str(tmp_path)) as temp_dir:
            assert temp_dir.startswith(str(tmp_path))
            assert os.path.exists(temp_dir)


class TestFileWriter:
    """Tests for FileWriter context manager."""

    def test_file_writer_creates_file(self, tmp_path):
        """Test that file is created."""
        file_path = tmp_path / "test.txt"

        with FileWriter(str(file_path)) as f:
            f.write("test content")

        assert file_path.exists()
        assert file_path.read_text() == "test content"

    def test_file_writer_closes_file_after_use(self, tmp_path):
        """Test that file is closed after context."""
        file_path = tmp_path / "test.txt"

        with FileWriter(str(file_path)) as f:
            f.write("test content")
            file_obj = f

        assert file_obj.closed

    def test_file_writer_closes_file_on_exception(self, tmp_path):
        """Test that file is closed even if exception occurs."""
        file_path = tmp_path / "test.txt"
        file_obj = None

        try:
            with FileWriter(str(file_path)) as f:
                file_obj = f
                f.write("test content")
                raise ValueError("Test exception")
        except ValueError:
            pass

        assert file_obj.closed

    def test_file_writer_with_append_mode(self, tmp_path):
        """Test that append mode works."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("existing content\n")

        with FileWriter(str(file_path), mode='a') as f:
            f.write("appended content")

        content = file_path.read_text()
        assert "existing content" in content
        assert "appended content" in content

    def test_file_writer_propagates_exceptions(self, tmp_path):
        """Test that exceptions are propagated (not suppressed)."""
        file_path = tmp_path / "test.txt"

        with pytest.raises(ValueError, match="Test exception"):
            with FileWriter(str(file_path)) as f:
                f.write("test")
                raise ValueError("Test exception")
```

**Key Principles:**
- Test that resources are created in `__enter__`
- Test that resources are cleaned up in `__exit__`
- Test cleanup even when exceptions occur
- Use `tmp_path` fixture for file system operations
- Verify file/resource states before and after context
- Test that exceptions are propagated correctly

---

## Phase 4: Edge Cases and Error Handling

### 4.1 Boundary Value Testing

Test values at the edges of valid ranges:

```python
# Example: Testing a function that accepts values 0-100
def test_minimum_boundary():
    assert validate_score(0) is True

def test_below_minimum_boundary():
    assert validate_score(-1) is False

def test_maximum_boundary():
    assert validate_score(100) is True

def test_above_maximum_boundary():
    assert validate_score(101) is False

def test_just_inside_minimum():
    assert validate_score(1) is True

def test_just_inside_maximum():
    assert validate_score(99) is True
```

### 4.2 Null/None Handling

Test behavior with None values:

```python
def test_function_with_none_argument():
    result = process(None)
    assert result is None  # or raises exception

def test_function_returns_none_on_empty_input():
    result = find_item([])
    assert result is None

def test_optional_parameter_defaults_to_none():
    obj = MyClass()
    assert obj.optional_field is None
```

### 4.3 Empty Collections

Test behavior with empty lists, dicts, sets:

```python
def test_empty_list_returns_zero():
    assert sum_list([]) == 0

def test_empty_dict_returns_empty_result():
    assert process_dict({}) == {}

def test_empty_string_raises_value_error():
    with pytest.raises(ValueError):
        parse("")
```

### 4.4 Exception Testing

Test that exceptions are raised correctly:

```python
# Basic exception testing
def test_division_by_zero_raises_error():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

# Test exception message
def test_invalid_input_raises_error_with_message():
    with pytest.raises(ValueError, match="Input must be positive"):
        validate(-5)

# Test exception attributes
def test_custom_exception_contains_details():
    with pytest.raises(ValidationError) as exc_info:
        validate_complex_input(bad_data)

    assert exc_info.value.code == "INVALID_FORMAT"
    assert "field_name" in exc_info.value.details
```

### 4.5 Type Error Testing

Test behavior with incorrect types:

```python
def test_string_instead_of_int_raises_type_error():
    with pytest.raises(TypeError):
        calculate("not a number")

def test_none_instead_of_list_raises_type_error():
    with pytest.raises(TypeError):
        process_list(None)
```

### 4.6 Large Inputs

Test performance and correctness with large inputs:

```python
def test_large_list_processing():
    large_list = list(range(100000))
    result = process_list(large_list)
    assert len(result) == 100000

@pytest.mark.slow
def test_very_large_input_performance():
    huge_list = list(range(1000000))
    import time
    start = time.time()
    process(huge_list)
    elapsed = time.time() - start
    assert elapsed < 1.0  # Should complete within 1 second
```

---

## Phase 5: Test Quality and Maintenance

### 5.1 Test Execution Time Profiling

Profile test execution times:

```python
# Use pytest-benchmark for performance testing
def test_fast_operation(benchmark):
    result = benchmark(fast_function, arg1, arg2)
    assert result == expected

# Or manually time tests
import time

def test_operation_speed():
    start = time.time()
    result = expensive_operation()
    elapsed = time.time() - start

    assert elapsed < 0.1  # Should complete in <100ms
    assert result == expected
```

Run pytest with timing:
```bash
pytest --durations=10  # Show 10 slowest tests
pytest --durations=0   # Show timing for all tests
```

### 5.2 Test Code Smells

Identify and fix test smells:

**Smell 1: Duplicate Setup Code**
```python
# BAD - Duplicate setup
def test_user_creation():
    user = User("John", "john@example.com")
    # test logic

def test_user_update():
    user = User("John", "john@example.com")
    # test logic

# GOOD - Use fixture
@pytest.fixture
def user():
    return User("John", "john@example.com")

def test_user_creation(user):
    # test logic

def test_user_update(user):
    # test logic
```

**Smell 2: Test Logic Complexity**
```python
# BAD - Complex test logic
def test_process_items():
    items = get_items()
    for item in items:
        if item.type == "special":
            result = process_special(item)
            assert result > 0
        else:
            result = process_normal(item)
            assert result == item.value * 2

# GOOD - Simple, focused tests
def test_process_special_items():
    item = create_special_item()
    result = process_special(item)
    assert result > 0

def test_process_normal_items():
    item = create_normal_item()
    result = process_normal(item)
    assert result == item.value * 2
```

**Smell 3: Unclear Assertions**
```python
# BAD - Unclear assertion
def test_calculation():
    assert calculate(5, 10) == 15

# GOOD - Clear assertion with explanation
def test_calculate_adds_two_numbers():
    a, b = 5, 10
    expected_sum = 15

    result = calculate(a, b)

    assert result == expected_sum, f"Expected {a} + {b} = {expected_sum}, got {result}"
```

### 5.3 Test Independence Verification

Verify tests are independent:

```bash
# Run tests in random order
pytest --random-order

# Run single test in isolation
pytest tests/unit/test_module.py::test_specific_test

# Run tests in reverse order
pytest --reverse
```

```python
# In conftest.py, add fixture to detect state pollution
@pytest.fixture(autouse=True)
def reset_state():
    """Reset global state before each test."""
    # Reset any global state
    yield
    # Clean up after test
```

### 5.4 Test Documentation

Document tests effectively:

```python
def test_calculate_discount_with_valid_inputs():
    """
    Test that calculate_discount correctly computes discounted price.

    Given:
        - Original price of $100
        - Discount rate of 20%

    When:
        - calculate_discount is called

    Then:
        - Returns $80 (20% off $100)

    This test validates the core discount calculation logic used
    throughout the application for pricing.
    """
    original_price = 100.0
    discount_rate = 0.20
    expected_price = 80.0

    result = calculate_discount(original_price, discount_rate)

    assert result == expected_price
```

### 5.5 Test Maintenance Checklist

Create a maintenance checklist:

- [ ] All tests pass independently
- [ ] Tests can run in any order
- [ ] Each test has clear, descriptive name
- [ ] Tests execute in <100ms each
- [ ] No duplicate setup code (use fixtures)
- [ ] No test logic complexity (loops, conditionals)
- [ ] Clear assertions with helpful messages
- [ ] Tests are properly documented
- [ ] Mocks are used appropriately (not excessively)
- [ ] Edge cases are covered
- [ ] Error conditions are tested
- [ ] Tests follow AAA pattern
- [ ] Test coverage is >80% for critical code

---

## Output Format

Generate the following deliverables:

### 1. Unit Test Implementation Guide (20-30 pages)
Comprehensive document saved to `${OUTPUT_DIR}/exports/unit_test_implementation_guide.md` covering:

- FIRST principles detailed explanation
- AAA pattern with examples
- Unit vs Integration vs E2E comparison
- Test organization strategies
- Framework-specific best practices
- Common anti-patterns and solutions

### 2. Test Examples Collection
File saved to `${OUTPUT_DIR}/exports/unit_test_examples.md` containing:

- 50+ example test functions
- Pure function tests
- Class and method tests
- Async code tests
- Generator tests
- Decorator tests
- Context manager tests
- Edge case examples
- Error handling examples

### 3. Test Templates
Files saved to `${OUTPUT_DIR}/templates/`:

- `unit_test_template.py` - Basic test template
- `class_test_template.py` - Class testing template
- `async_test_template.py` - Async testing template
- `parametrized_test_template.py` - Parametrized test template
- `conftest_template.py` - Fixture configuration template
- `pytest_ini_template.ini` - pytest configuration

### 4. Configuration Files
Files saved to `${OUTPUT_DIR}/templates/`:

- `pytest.ini` - Complete pytest configuration
- `pyproject.toml` - Alternative configuration
- `.coveragerc` - Coverage configuration

### 5. Visual Assets
Files saved to `${OUTPUT_DIR}/assets/`:

- `first_principles_diagram.png` - Visual representation of FIRST principles
- `aaa_pattern_visualization.png` - AAA pattern flowchart
- `test_pyramid.png` - Testing pyramid diagram
- `test_organization_structure.png` - Directory structure diagram

### 6. Anti-Patterns Guide
File saved to `${OUTPUT_DIR}/exports/anti_patterns_guide.md`:

- Common anti-patterns with examples
- How to identify each anti-pattern
- Refactoring strategies
- Before/after examples

### 7. Unit Test Quality Checklist
File saved to `${OUTPUT_DIR}/exports/unit_test_quality_checklist.md`:

- Test independence checklist
- Performance checklist
- Code quality checklist
- Maintenance checklist
- Review guidelines

### 8. Execution Profiling Report
File saved to `${OUTPUT_DIR}/exports/execution_profiling_report.md`:

- Command to profile test execution times
- How to identify slow tests
- Optimization strategies
- Performance benchmarks

---

## File Output Instructions

**Critical:** Organize all generated files according to this structure:

```
${OUTPUT_DIR}/
├── templates/
│   ├── unit_test_template.py
│   ├── class_test_template.py
│   ├── async_test_template.py
│   ├── parametrized_test_template.py
│   ├── conftest_template.py
│   ├── pytest.ini
│   ├── pyproject.toml
│   └── .coveragerc
├── assets/
│   ├── first_principles_diagram.png
│   ├── aaa_pattern_visualization.png
│   ├── test_pyramid.png
│   └── test_organization_structure.png
└── exports/
    ├── unit_test_implementation_guide.md (20-30 pages)
    ├── unit_test_examples.md (50+ tests)
    ├── anti_patterns_guide.md
    ├── unit_test_quality_checklist.md
    └── execution_profiling_report.md
```

**Directory Creation:**
Before generating content, ensure directories exist:
```bash
mkdir -p ${OUTPUT_DIR}/templates ${OUTPUT_DIR}/assets ${OUTPUT_DIR}/exports
```

---

## Verification Checklist

After generating all content, verify:

- [ ] All 8 deliverables are created
- [ ] Files are saved to correct directories (templates/, assets/, exports/)
- [ ] Implementation guide is 20-30 pages
- [ ] 50+ test examples are included
- [ ] FIRST principles are thoroughly explained
- [ ] AAA pattern is demonstrated in all examples
- [ ] Common anti-patterns are documented
- [ ] pytest and unittest examples are included
- [ ] Configuration files are complete and usable
- [ ] Visual diagrams are included (or placeholders)
- [ ] All code examples are syntactically correct
- [ ] Repository information is included where applicable
- [ ] Quality checklist is comprehensive

---
~~~

End of prompt template.

---

## Additional Notes

- Install pytest: `pip install pytest pytest-cov pytest-asyncio pytest-mock`
- Run unit tests: `pytest tests/unit/ -v`
- Check coverage: `pytest tests/unit/ --cov=src --cov-report=html`
- Profile slow tests: `pytest --durations=10`
- Run tests in random order: `pip install pytest-random-order && pytest --random-order`

---

**Status:** Template ready for use. Copy the prompt section above into your AI assistant to generate comprehensive Python unit testing guidance.
