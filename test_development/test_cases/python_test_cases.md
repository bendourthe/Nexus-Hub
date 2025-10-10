# Python Test Case Development

## Objective
Develop comprehensive, well-structured test cases that validate functionality, cover edge cases, handle error conditions, and provide clear documentation of expected behavior using industry-standard testing patterns.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/test_cases/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/test_cases/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Test Coverage
- [ ] Happy path scenarios tested
- [ ] Edge cases and boundaries covered
- [ ] Error conditions validated
- [ ] Input validation tested
- [ ] State transitions verified
- [ ] Regression tests added for bugs

### Test Quality
- [ ] Tests follow AAA pattern (Arrange-Act-Assert)
- [ ] Test names clearly describe what is tested
- [ ] Tests are isolated and independent
- [ ] Tests execute quickly (<1s for unit tests)
- [ ] Assertions are specific and meaningful
- [ ] No test interdependencies

### Test Organization
- [ ] Tests grouped logically by feature/module
- [ ] Related tests organized in test classes
- [ ] Parametrized tests used for multiple scenarios
- [ ] Setup and teardown properly implemented
- [ ] Test documentation provided

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Python Test Case Development

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/test_cases"
```

Create the required subdirectories:
```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

**Directory Structure:**
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**
- All generated files should be saved with the `${OUTPUT_DIR}/` prefix
- Examples:
  - Reports and documentation → `${OUTPUT_DIR}/exports/report.md`
  - Template files → `${OUTPUT_DIR}/templates/template.yaml`
  - Diagrams and images → `${OUTPUT_DIR}/assets/diagram.png`

Please develop comprehensive test cases for this Python code following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Phase 1: Test Case Planning

1. **Analyze Code to Test**
   - Identify all public functions/methods
   - Document expected behavior
   - List input parameters and types
   - Define expected outputs
   - Note side effects (database, files, API calls)

2. **Identify Test Scenarios**

   **Happy Path**:
   - Normal operation with valid inputs
   - Expected use cases
   - Successful execution flows

   **Edge Cases**:
   - Boundary values (min/max, empty, null)
   - Special characters in strings
   - Large data sets
   - Concurrent operations

   **Error Conditions**:
   - Invalid inputs
   - Missing required parameters
   - Type errors
   - Business rule violations
   - External dependency failures

3. **Create Test Case Matrix**

   | Scenario | Input | Expected Output | Test Type | Priority |
   |----------|-------|-----------------|-----------|----------|
   | [description] | [values] | [result] | [unit/integration] | [high/med/low] |

## Phase 2: Unit Test Implementation

### AAA Pattern (Arrange-Act-Assert)

Follow this structure for clear, maintainable tests:

```python
"""
Unit tests for [module_name] module.

Tests cover [description of what is tested].
"""
import pytest
from myapp.module import function_to_test

class TestFunctionName:
    """Test suite for function_name()."""

    def test_function_with_valid_input_returns_expected_result(self):
        """Test that function_name() returns correct value with valid input."""
        # Arrange - Set up test data and dependencies
        input_value = "valid input"
        expected_result = "expected output"

        # Act - Execute the function being tested
        actual_result = function_to_test(input_value)

        # Assert - Verify the result matches expectations
        assert actual_result == expected_result

    def test_function_with_empty_input_raises_value_error(self):
        """Test that function_name() raises ValueError with empty input."""
        # Arrange
        empty_input = ""

        # Act & Assert - Use pytest.raises for exception testing
        with pytest.raises(ValueError) as exc_info:
            function_to_test(empty_input)

        assert "cannot be empty" in str(exc_info.value)

    def test_function_with_none_input_returns_default_value(self):
        """Test that function_name() handles None gracefully."""
        # Arrange
        none_input = None
        expected_default = "default"

        # Act
        result = function_to_test(none_input)

        # Assert
        assert result == expected_default
```

### Test Naming Conventions

Use descriptive names that explain what is tested:

**Pattern**: `test_<function>_<condition>_<expected_result>`

**Examples**:
```python
# Good test names
def test_add_user_with_valid_data_returns_user_id(self):
def test_add_user_with_duplicate_email_raises_validation_error(self):
def test_get_user_with_nonexistent_id_returns_none(self):
def test_update_user_with_invalid_age_raises_value_error(self):

# Poor test names (avoid these)
def test_add_user(self):              # Too generic
def test_1(self):                     # Non-descriptive
def test_error(self):                 # Unclear what error
def test_user_creation_edge_case(self): # Vague "edge case"
```

### Testing Different Scenarios

**1. Testing Return Values**:
```python
def test_calculate_total_with_items_returns_sum(self):
    """Test calculate_total() returns correct sum."""
    items = [10.0, 20.0, 30.0]
    result = calculate_total(items)
    assert result == 60.0

def test_calculate_total_with_empty_list_returns_zero(self):
    """Test calculate_total() returns 0 for empty list."""
    assert calculate_total([]) == 0.0

def test_calculate_total_with_negative_values_returns_correct_sum(self):
    """Test calculate_total() handles negative values."""
    items = [10.0, -5.0, 15.0]
    assert calculate_total(items) == 20.0
```

**2. Testing Exceptions**:
```python
def test_divide_by_zero_raises_zero_division_error(self):
    """Test divide() raises ZeroDivisionError."""
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_parse_date_with_invalid_format_raises_value_error(self):
    """Test parse_date() raises ValueError with message."""
    with pytest.raises(ValueError, match="Invalid date format"):
        parse_date("not-a-date")
```

**3. Testing Side Effects**:
```python
def test_save_user_creates_database_entry(self, mock_database):
    """Test save_user() calls database insert."""
    user = User(name="Alice")
    save_user(user, mock_database)

    # Verify database was called correctly
    mock_database.insert.assert_called_once()
    call_args = mock_database.insert.call_args[0][0]
    assert call_args["name"] == "Alice"

def test_send_email_calls_email_service(self, mock_email_service):
    """Test send_email() invokes email service."""
    send_email("test@example.com", "Hello")

    mock_email_service.send.assert_called_once_with(
        to="test@example.com",
        subject="Hello"
    )
```

**4. Testing State Changes**:
```python
def test_user_login_changes_status_to_active(self):
    """Test login() updates user status."""
    user = User(username="alice", status="inactive")
    user.login()
    assert user.status == "active"
    assert user.last_login is not None

def test_order_cancel_reverts_inventory(self, inventory):
    """Test cancel_order() restores inventory."""
    order = Order(items=[{"id": 1, "quantity": 5}])
    initial_stock = inventory.get_stock(item_id=1)

    order.cancel()

    final_stock = inventory.get_stock(item_id=1)
    assert final_stock == initial_stock + 5
```

### Parametrized Tests

Test multiple scenarios efficiently with parametrize:

```python
import pytest

@pytest.mark.parametrize("input_value,expected", [
    (0, "zero"),
    (1, "one"),
    (5, "five"),
    (10, "ten"),
])
def test_number_to_word_converts_correctly(input_value, expected):
    """Test number_to_word() with various inputs."""
    assert number_to_word(input_value) == expected

@pytest.mark.parametrize("email", [
    "",                           # Empty string
    "not-an-email",              # No @ symbol
    "@example.com",              # Missing local part
    "user@",                     # Missing domain
    "user @example.com",         # Space in email
])
def test_validate_email_rejects_invalid_formats(email):
    """Test validate_email() rejects invalid formats."""
    with pytest.raises(ValueError):
        validate_email(email)

@pytest.mark.parametrize("age,is_adult", [
    (17, False),
    (18, True),
    (21, True),
    (100, True),
])
def test_is_adult_checks_age_threshold(age, is_adult):
    """Test is_adult() with boundary values."""
    assert check_is_adult(age) == is_adult
```

### Testing Edge Cases and Boundaries

```python
class TestBoundaryConditions:
    """Test edge cases and boundary values."""

    def test_with_minimum_valid_value(self):
        """Test with smallest valid input."""
        assert process_value(0) == expected_min_result

    def test_with_maximum_valid_value(self):
        """Test with largest valid input."""
        assert process_value(100) == expected_max_result

    def test_with_below_minimum_value(self):
        """Test with value below valid range."""
        with pytest.raises(ValueError):
            process_value(-1)

    def test_with_above_maximum_value(self):
        """Test with value above valid range."""
        with pytest.raises(ValueError):
            process_value(101)

    def test_with_empty_collection(self):
        """Test with empty list/dict."""
        assert process_collection([]) == []

    def test_with_single_item_collection(self):
        """Test with single element."""
        assert process_collection([1]) == [1]

    def test_with_large_collection(self):
        """Test with large dataset."""
        large_list = list(range(10000))
        result = process_collection(large_list)
        assert len(result) == 10000
```

## Phase 3: Integration Test Implementation

Integration tests verify multiple components working together:

```python
"""
Integration tests for user registration workflow.

Tests the complete user registration process including
validation, database storage, and email notification.
"""
import pytest
from myapp.services import UserService
from myapp.models import User

class TestUserRegistrationIntegration:
    """Integration tests for user registration."""

    def test_register_user_creates_db_entry_and_sends_email(
        self, test_database, mock_email_service
    ):
        """Test complete user registration workflow."""
        # Arrange
        service = UserService(database=test_database, email=mock_email_service)
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePass123!"
        }

        # Act
        user_id = service.register_user(**user_data)

        # Assert - Verify database entry
        user = test_database.get_user(user_id)
        assert user is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.password != "SecurePass123!"  # Should be hashed

        # Assert - Verify email sent
        mock_email_service.send.assert_called_once()
        email_call = mock_email_service.send.call_args
        assert email_call[1]["to"] == "newuser@example.com"
        assert "Welcome" in email_call[1]["subject"]

    def test_register_duplicate_username_raises_error_and_rolls_back(
        self, test_database
    ):
        """Test registration with duplicate username fails cleanly."""
        # Arrange
        service = UserService(database=test_database)
        existing_user = {"username": "alice", "email": "alice@example.com"}
        service.register_user(**existing_user)

        # Act & Assert
        with pytest.raises(ValueError, match="Username already exists"):
            service.register_user(
                username="alice",
                email="different@example.com"
            )

        # Verify no partial data left in database
        users = test_database.get_users_by_email("different@example.com")
        assert len(users) == 0
```

### API Integration Tests

```python
class TestAPIEndpoints:
    """Integration tests for REST API endpoints."""

    def test_post_user_creates_user_and_returns_201(self, api_client):
        """Test POST /users endpoint."""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "test@example.com"
        }

        # Act
        response = api_client.post("/users", json=user_data)

        # Assert
        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["username"] == "testuser"

    def test_get_user_returns_user_data(self, api_client, created_user):
        """Test GET /users/{id} endpoint."""
        # Act
        response = api_client.get(f"/users/{created_user.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_user.id
        assert data["username"] == created_user.username

    def test_update_user_with_invalid_data_returns_400(self, api_client, created_user):
        """Test PUT /users/{id} with invalid data."""
        # Arrange
        invalid_data = {"email": "not-an-email"}

        # Act
        response = api_client.put(f"/users/{created_user.id}", json=invalid_data)

        # Assert
        assert response.status_code == 400
        assert "error" in response.json()
```

## Phase 4: End-to-End Test Implementation

E2E tests validate complete user workflows:

```python
"""
End-to-end tests for e-commerce checkout flow.

Tests the complete user journey from adding items to cart
through payment and order confirmation.
"""
class TestCheckoutWorkflow:
    """E2E tests for checkout process."""

    def test_complete_purchase_workflow_success(
        self,
        browser,
        test_user,
        test_product
    ):
        """Test complete purchase from cart to confirmation."""
        # Login
        browser.navigate_to("/login")
        browser.fill_form({
            "username": test_user.username,
            "password": test_user.password
        })
        browser.click("Login")
        assert browser.current_url == "/dashboard"

        # Add product to cart
        browser.navigate_to(f"/products/{test_product.id}")
        browser.click("Add to Cart")
        assert browser.find_element(".cart-count").text == "1"

        # Proceed to checkout
        browser.navigate_to("/cart")
        browser.click("Checkout")

        # Fill shipping information
        browser.fill_form({
            "address": "123 Test St",
            "city": "Test City",
            "zip": "12345"
        })
        browser.click("Continue")

        # Enter payment information
        browser.fill_form({
            "card_number": "4111111111111111",
            "expiry": "12/25",
            "cvv": "123"
        })
        browser.click("Place Order")

        # Verify confirmation
        assert browser.current_url.startswith("/order-confirmation")
        assert "Thank you" in browser.page_source
        order_number = browser.find_element(".order-number").text
        assert order_number is not None

        # Verify order in database
        order = Order.get_by_number(order_number)
        assert order.user_id == test_user.id
        assert order.status == "confirmed"
        assert len(order.items) == 1
```

## Phase 5: Test Best Practices

### 1. Test Independence

```python
# GOOD - Tests are independent
class TestUserService:
    def test_create_user(self, clean_database):
        """Each test gets fresh database."""
        user = create_user("alice")
        assert user.id is not None

    def test_delete_user(self, clean_database):
        """Independent of previous test."""
        user = create_user("bob")
        delete_user(user.id)
        assert get_user(user.id) is None

# BAD - Tests depend on each other
class TestUserService:
    def test_01_create_user(self):
        """Creates user that test_02 depends on."""
        self.user = create_user("alice")  # Shared state!

    def test_02_delete_user(self):
        """Depends on test_01 running first."""
        delete_user(self.user.id)  # Breaks if test_01 fails
```

### 2. Clear Assertions

```python
# GOOD - Specific, clear assertions
def test_user_creation(self):
    user = create_user("alice", "alice@example.com")
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.created_at is not None
    assert user.is_active is True

# BAD - Vague or missing assertions
def test_user_creation(self):
    user = create_user("alice", "alice@example.com")
    assert user  # Too vague - what about user?
    assert user.username  # Checks existence, not value
```

### 3. Test Data Management

```python
# GOOD - Clear, explicit test data
def test_discount_calculation(self):
    """Test 10% discount on order over $100."""
    order = Order(items=[
        {"price": 50.00, "quantity": 2},
        {"price": 25.00, "quantity": 2}
    ])
    discount = calculate_discount(order)
    assert discount == 15.00  # 10% of $150

# BAD - Magic numbers without context
def test_discount_calculation(self):
    order = Order(items=[{"price": 50, "quantity": 2}])
    assert calculate_discount(order) == 10  # Why 10?
```

### 4. Testing Async Code

```python
import pytest

@pytest.mark.asyncio
async def test_async_fetch_user_returns_user_data(self):
    """Test async user fetch operation."""
    user_id = 123
    user = await fetch_user(user_id)
    assert user.id == user_id

@pytest.mark.asyncio
async def test_async_operation_with_timeout(self):
    """Test async operation completes within timeout."""
    import asyncio
    try:
        result = await asyncio.wait_for(slow_operation(), timeout=5.0)
        assert result is not None
    except asyncio.TimeoutError:
        pytest.fail("Operation timed out")
```

## Output Format

Please provide comprehensive test cases with the following structure:

### Test Coverage Summary
- **Total Test Cases**: [count]
- **Unit Tests**: [count]
- **Integration Tests**: [count]
- **E2E Tests**: [count]
- **Test Types**:
  - Happy path: [count]
  - Edge cases: [count]
  - Error conditions: [count]

### Test Case Implementation

For each module/feature:

**Module**: `[module_name]`
**Test File**: `tests/unit/test_[module_name].py`

**Test Cases**:
1. `test_function_with_valid_input_returns_expected_result`
   - **Scenario**: [description]
   - **Input**: [test data]
   - **Expected**: [result]
   - **Type**: [unit/integration/e2e]

2. `test_function_with_invalid_input_raises_error`
   - **Scenario**: [description]
   - **Input**: [test data]
   - **Expected**: [exception type and message]
   - **Type**: [unit/integration/e2e]

### Test Execution Results
```bash
# Run tests
pytest tests/unit/test_module.py -v

# Expected output
test_function_with_valid_input ... PASSED
test_function_with_invalid_input ... PASSED
test_function_edge_case ... PASSED
```

### Coverage Gaps Identified
- [ ] [Function/method]: Missing tests for [scenario]
- [ ] [Function/method]: Need edge case tests for [condition]
- [ ] [Function/method]: Error handling not tested

### Test Quality Metrics
- **Average test execution time**: [milliseconds]
- **Tests following AAA pattern**: [percentage]
- **Tests with clear names**: [percentage]
- **Independent tests**: [percentage]
- **Parametrized tests**: [count]

### Next Steps
- [ ] Implement remaining test cases for coverage gaps
- [ ] Add performance benchmarks for critical functions
- [ ] Set up test fixtures for integration tests
- [ ] Configure CI/CD to run tests automatically
- [ ] Review and refactor slow tests

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p tests/{phase_name}/test_files
mkdir -p tests/{phase_name}/test_data
mkdir -p tests/{phase_name}/test_reports
mkdir -p tests/{phase_name}/test_configs
```

**Save files as follows**:

- Test files → `tests/{phase_name}/test_files/`

- Test data → `tests/{phase_name}/test_data/`

- Test reports → `tests/{phase_name}/test_reports/`

- Test configs → `tests/{phase_name}/test_configs/`

Replace `{phase_name}` with the specific phase (test_cases, mocks_fixtures, performance_testing, maintenance_cicd, or code_coverage).
~~~

## Output Format

The AI assistant should deliver:

1. **Test case matrix** documenting all scenarios
2. **Complete test implementations** with clear AAA structure
3. **Parametrized tests** for multiple scenarios
4. **Integration and E2E tests** for workflows
5. **Test coverage report** showing gaps
6. **Execution instructions** for running tests
7. **Quality metrics** and improvement suggestions
---

## Verify Directory Structure

After completing all phases, verify the output structure:

```bash
tree ${OUTPUT_DIR}
```

Expected structure:
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates and scripts
├── assets/            # Images, diagrams, supplementary files
└── exports/           # Final publishable artifacts and reports
```

**Verification checklist:**
- [ ] All directories created successfully
- [ ] All files saved in correct subdirectories
- [ ] No files created in repository root
- [ ] Directory structure matches expected layout
