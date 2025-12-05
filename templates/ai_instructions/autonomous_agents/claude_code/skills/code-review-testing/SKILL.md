---
name: code-review-testing
description: Systematically assess test suite quality, coverage, and effectiveness - evaluate test structure, identify gaps, analyze test reliability and maintainability
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language
category: Code Review
tags: [code-review, testing, coverage, quality, workflow, phase-5]
priority: HIGH
based_on: AI Templates Code Review Workflow, Anthropic Claude Code Best Practices 2025
---

# Code Review Testing Assessment

Systematically assess test suite quality, coverage, and effectiveness to ensure confidence in code correctness and regression prevention. This skill is **Phase 5** of the complete code review workflow, examining test structure, coverage metrics, test quality, and identifying gaps that could lead to undiscovered bugs or regressions.

## When to Use This Skill

Use this skill as **Phase 5** after completing context, quality, security, and performance reviews:

- ✅ After [Phase 1: Context](../code-review-context-analysis/SKILL.md), [Phase 2: Quality](../code-review-quality/SKILL.md), [Phase 3: Security](../code-review-security/SKILL.md), and [Phase 4: Performance](../code-review-performance/SKILL.md) complete

- ✅ Evaluating test coverage before production deployment

- ✅ Assessing test suite maintainability

- ✅ Identifying untested critical paths

- ✅ Improving test reliability and reducing flakiness

- ✅ Establishing quality gates for CI/CD

- ✅ Planning testing infrastructure improvements

- ✅ Onboarding to testing best practices

**This skill is essential when**:

- You need to measure and improve test coverage

- You're identifying critical testing gaps

- You want to improve test quality and reliability

- You're reducing flaky tests

- You need to establish testing standards

## What This Skill Does

This skill implements **Phase 5: Testing Review** of the six-phase code review workflow:

### Complete Workflow
- Phase 1: [Context Analysis](../code-review-context-analysis/SKILL.md) - Project understanding

- Phase 2: [Quality Review](../code-review-quality/SKILL.md) - Code maintainability

- Phase 3: [Security Review](../code-review-security/SKILL.md) - Vulnerability identification

- Phase 4: [Performance Review](../code-review-performance/SKILL.md) - Bottleneck analysis

- **Phase 5: Testing Review (This Skill)** - Test coverage evaluation

- Phase 6: [Final Report](../code-review-final-report/SKILL.md) - Consolidated findings

## Why Testing Review Matters

**Without Testing Review**:
```
Team: *writes tests inconsistently*
Tests: *provide false confidence*
Bugs: *slip through to production*
Result:

- ❌ Low coverage leaves bugs undiscovered

- ❌ Flaky tests waste developer time

- ❌ Poor test quality doesn't catch regressions

- ❌ Critical paths remain untested

- ❌ Deployment confidence is low

- ❌ Production incidents increase
```

**With Testing Review**:
```
Team: *follows testing best practices*
Tests: *provide real confidence*
Bugs: *caught before deployment*
Result:

- ✅ High coverage catches bugs early

- ✅ Reliable tests save developer time

- ✅ Quality tests prevent regressions

- ✅ Critical paths thoroughly tested

- ✅ Deployment confidence is high

- ✅ Production incidents decrease
```

## Benefits of Testing Review

### Quality Assurance
- **Bug Prevention**: Catch defects before production

- **Regression Protection**: Prevent old bugs from returning

- **Confidence**: Deploy with assurance code works

- **Documentation**: Tests document expected behavior

### Development Velocity
- **Fast Feedback**: Tests run quickly in CI/CD

- **Safe Refactoring**: Change code without fear

- **Reduced Debugging**: Tests pinpoint issues quickly

- **Developer Productivity**: Less time fixing production bugs

### Cost Reduction
- **Early Detection**: Fixing bugs in development is cheaper

- **Reduced Downtime**: Fewer production incidents

- **Lower Support Costs**: Fewer user-reported issues

- **Faster Releases**: Confidence enables frequent deploys

## Prerequisites

### Required
- Completion of [Phase 1: Context](../code-review-context-analysis/SKILL.md), [Phase 2: Quality](../code-review-quality/SKILL.md), [Phase 3: Security](../code-review-security/SKILL.md), and [Phase 4: Performance](../code-review-performance/SKILL.md)

- Source code and test suite access

- Test framework understanding

- Coverage measurement tools

### Recommended
- CI/CD pipeline access

- Test execution logs

- Historical test failure data

- Performance benchmarks for tests

### Knowledge
- Testing types (unit, integration, e2e)

- Test patterns (AAA, Given-When-Then)

- Mocking and stubbing techniques

- Test-driven development (TDD)

- Coverage metrics interpretation

## Instructions

### Step 1: Test Coverage Analysis

**Measure current test coverage comprehensively:**

1. **Install Coverage Tools**

   **Python**:
   ```bash
   # Install coverage tools
   pip install coverage pytest-cov

   # Run tests with coverage
   pytest --cov=src --cov-report=html --cov-report=term --cov-report=xml

   # View detailed HTML report
   open htmlcov/index.html

   # Coverage with branch coverage
   pytest --cov=src --cov-branch --cov-report=term-missing
   ```

   **JavaScript/TypeScript**:
   ```bash
   # Install Jest with coverage
   npm install --save-dev jest @types/jest

   # Run with coverage
   npm test -- --coverage --coverageReporters=html --coverageReporters=text

   # Or with NYC (Istanbul)
   npm install --save-dev nyc
   nyc npm test
   ```

   **Java**:
   ```bash
   # JaCoCo with Maven
   mvn clean test jacoco:report

   # View report
   open target/site/jacoco/index.html

   # Or with Gradle
   gradle test jacocoTestReport
   ```

   **Go**:
   ```bash
   # Built-in coverage
   go test -cover ./...

   # Detailed coverage report
   go test -coverprofile=coverage.out ./...
   go tool cover -html=coverage.out

   # Coverage by package
   go test -covermode=count -coverprofile=coverage.out ./...
   ```

   **C/C++**:
   ```bash
   # gcov with gcc
   gcc -fprofile-arcs -ftest-coverage program.c -o program
   ./program
   gcov program.c

   # lcov for HTML reports
   lcov --capture --directory . --output-file coverage.info
   genhtml coverage.info --output-directory coverage-html
   ```

   **C#**:
   ```bash
   # Coverlet with .NET
   dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=opencover

   # ReportGenerator for HTML
   dotnet tool install -g dotnet-reportgenerator-globaltool
   reportgenerator -reports:coverage.opencover.xml -targetdir:coverage-report
   ```

2. **Analyze Coverage Metrics**

   **Line Coverage**:

   - Percentage of code lines executed by tests

   - Target: 80%+ for critical code, 60%+ overall

   **Branch Coverage**:

   - Percentage of conditional branches tested

   - More important than line coverage

   - Target: 75%+ for critical paths

   **Function Coverage**:

   - Percentage of functions called by tests

   - Identifies completely untested functions

   **Example Analysis**:
   ```
   Module          Lines   Branches   Functions   Coverage
   core/auth.py    95%     88%        100%        Excellent
   utils/helpers.py 45%    30%        60%         Poor
   api/endpoints.py 78%    70%        85%         Good
   ```

3. **Identify Coverage Gaps**

   **Python Example**:
   ```python
   # Use --cov-report=term-missing to see uncovered lines
   pytest --cov=src --cov-report=term-missing

   # Output shows which lines aren't covered:
   # src/auth.py    85%    12-15, 23, 45-48
   #                       ^^^ These lines not tested
   ```

   Look for:

   - Critical paths with <80% coverage

   - Error handling code not tested

   - Edge cases not covered

   - Complex logic with low branch coverage

### Step 2: Test Suite Inventory

**Catalog and categorize all tests:**

1. **Count Tests by Type**

   **Python**:
   ```bash
   # Collect test information
   pytest --collect-only

   # Count tests by marker
   pytest --collect-only -m unit
   pytest --collect-only -m integration
   pytest --collect-only -m e2e

   # List all test files
   find tests/ -name "test_*.py" -o -name "*_test.py"
   ```

   **JavaScript**:
   ```bash
   # Jest test inventory
   npm test -- --listTests

   # Count by pattern
   npm test -- --testNamePattern="unit"
   npm test -- --testNamePattern="integration"
   ```

2. **Test Distribution Analysis**

   Ideal distribution:

   - **70% Unit Tests**: Fast, isolated, test individual functions

   - **20% Integration Tests**: Test component interactions

   - **10% E2E Tests**: Test complete user workflows

   **Test Pyramid**:
   ```
        /\
       /  \  E2E Tests (10%) - Slow, brittle, expensive
      /    \
     /      \ Integration Tests (20%) - Medium speed
    /        \
   /          \ Unit Tests (70%) - Fast, reliable, cheap
   ```

3. **Test Organization Review**

   **Good Test Structure**:
   ```
   tests/
   ├── unit/                   # Fast, isolated unit tests
   │   ├── test_auth.py
   │   ├── test_utils.py
   │   └── test_models.py
   ├── integration/            # Component interaction tests
   │   ├── test_api_database.py
   │   └── test_services.py
   ├── e2e/                   # End-to-end user flow tests
   │   ├── test_user_registration.py
   │   └── test_checkout_flow.py
   ├── performance/           # Performance and load tests
   │   └── test_api_load.py
   ├── conftest.py            # Shared fixtures (Python)
   └── setup.js               # Test setup (JavaScript)
   ```

### Step 3: Test Quality Assessment

**Evaluate test code quality and patterns:**

1. **Test Structure Review (AAA Pattern)**

   **Python - Good Example**:
   ```python
   def test_user_registration_with_valid_data():
       """Test that user registration succeeds with valid data."""
       # Arrange - Set up test data and conditions
       username = "testuser"
       email = "test@example.com"
       password = "SecurePassword123!"

       # Act - Execute the operation being tested
       user = create_user(username, email, password)

       # Assert - Verify the expected outcome
       assert user is not None
       assert user.username == username
       assert user.email == email
       assert user.is_active is True
       assert user.created_at is not None
   ```

   **Python - Bad Example**:
   ```python
   def test_user():  # Vague name
       # No clear arrange/act/assert
       u = User("test", "test@test.com")  # What's being tested?
       assert u  # Weak assertion
       u.save()
       assert u.id  # Multiple actions mixed together
   ```

   **JavaScript - Good Example**:
   ```javascript
   describe('User Registration', () => {
       it('should create user with valid data', async () => {
           // Arrange
           const userData = {
               username: 'testuser',
               email: 'test@example.com',
               password: 'SecurePassword123!'
           };

           // Act
           const user = await createUser(userData);

           // Assert
           expect(user).toBeDefined();
           expect(user.username).toBe(userData.username);
           expect(user.email).toBe(userData.email);
           expect(user.isActive).toBe(true);
       });
   });
   ```

   **Java - Good Example**:
   ```java
   @Test
   public void testUserRegistration_WithValidData_CreatesUser() {
       // Arrange
       String username = "testuser";
       String email = "test@example.com";
       String password = "SecurePassword123!";

       // Act
       User user = userService.createUser(username, email, password);

       // Assert
       assertNotNull(user);
       assertEquals(username, user.getUsername());
       assertEquals(email, user.getEmail());
       assertTrue(user.isActive());
   }
   ```

2. **Test Naming Conventions**

   **Good Test Names** (describe what is being tested):
   ```python
   # Pattern: test_<method>_<condition>_<expected_result>
   def test_create_user_with_valid_data_returns_user_object()
   def test_create_user_with_duplicate_email_raises_validation_error()
   def test_authenticate_with_invalid_password_returns_none()
   def test_calculate_discount_for_premium_member_applies_20_percent()
   ```

   **Bad Test Names**:
   ```python
   def test_user()  # What about user?
   def test_1()     # Meaningless
   def test_function()  # Too generic
   ```

3. **Assertion Quality**

   **Python - Strong Assertions**:
   ```python
   # Good: Specific, meaningful assertions
   assert user.status == "active", "User should be active after registration"
   assert len(results) == 3, f"Expected 3 results, got {len(results)}"
   assert response.status_code == 200, f"API call failed: {response.text}"

   with pytest.raises(ValueError, match="Invalid email format"):
       create_user("test", "not-an-email")

   # Bad: Weak, vague assertions
   assert user                   # What about user?
   assert True                   # Meaningless
   assert results                # What should results be?
   ```

   **JavaScript - Strong Assertions**:
   ```javascript
   // Good: Descriptive assertions
   expect(user.status).toBe('active');
   expect(results).toHaveLength(3);
   expect(response.status).toBe(200);

   await expect(createUser('test', 'invalid'))
       .rejects
       .toThrow('Invalid email format');

   // Bad: Weak assertions
   expect(user).toBeTruthy();    // Too vague
   expect(results.length > 0).toBeTruthy();  // Use toHaveLength
   ```

4. **Test Anti-Patterns to Find**

   **Testing Implementation Details**:
   ```python
   # Bad: Tests internal implementation
   def test_user_creation():
       user = User("test")
       assert user._internal_state == "initialized"  # Don't test private details
       assert user._cache is not None  # Implementation detail

   # Good: Tests public behavior
   def test_user_creation():
       user = User("test")
       assert user.username == "test"
       assert user.is_valid()
   ```

   **Multiple Unrelated Assertions**:
   ```python
   # Bad: Testing too many things
   def test_everything():
       user = create_user("test", "test@example.com")
       assert user.username == "test"

       order = create_order(user, items)  # Different concern!
       assert order.total == 100

       response = api_call()  # Another concern!
       assert response.status == 200

   # Good: Split into focused tests
   def test_user_creation():
       user = create_user("test", "test@example.com")
       assert user.username == "test"

   def test_order_total_calculation():
       order = create_order(user, items)
       assert order.total == 100
   ```

   **Test Interdependence**:
   ```python
   # Bad: Tests depend on each other
   class TestUserFlow:
       user = None

       def test_01_create_user(self):
           self.user = create_user("test")  # Stores state
           assert self.user

       def test_02_update_user(self):
           self.user.email = "new@example.com"  # Depends on test_01
           assert self.user.email == "new@example.com"

   # Good: Independent tests
   class TestUser:
       def test_create_user(self):
           user = create_user("test")
           assert user

       def test_update_user(self):
           user = create_user("test")  # Fresh setup
           user.email = "new@example.com"
           assert user.email == "new@example.com"
   ```

### Step 4: Test Isolation and Reliability

**Ensure tests are independent and deterministic:**

1. **Test Independence Verification**

   **Python**:
   ```bash
   # Run tests in random order
   pytest --random-order

   # Run specific test alone
   pytest tests/test_specific.py::test_function

   # Run tests in reverse order
   pytest --reverse

   # If tests fail in different orders, they have dependencies
   ```

   **JavaScript**:
   ```bash
   # Jest runs tests in parallel by default
   # Force serial execution to detect dependencies
   npm test -- --runInBand

   # Run specific test file
   npm test -- tests/user.test.js
   ```

2. **Flaky Test Detection**

   **Python**:
   ```bash
   # Run tests multiple times
   pytest --count=10 tests/

   # Or use pytest-repeat
   pip install pytest-repeat
   pytest --count=100 tests/test_potentially_flaky.py

   # Use pytest-flakefinder
   pip install pytest-flakefinder
   pytest --flake-finder --flake-runs=50
   ```

   **JavaScript**:
   ```bash
   # Run tests multiple times
   for i in {1..10}; do npm test; done

   # Or use jest-repeat
   npm install --save-dev jest-repeat
   # Then use test.repeat in tests
   ```

3. **Common Flakiness Causes**

   **Time-Dependent Tests**:
   ```python
   # Bad: Depends on current time
   def test_cache_expiration():
       cache.set('key', 'value', ttl=1)
       time.sleep(1.1)  # Flaky timing
       assert cache.get('key') is None

   # Good: Mock time
   from unittest.mock import patch
   import time

   def test_cache_expiration():
       with patch('time.time') as mock_time:
           mock_time.return_value = 1000
           cache.set('key', 'value', ttl=1)

           mock_time.return_value = 1002  # Advance time
           assert cache.get('key') is None
   ```

   **Network-Dependent Tests**:
   ```python
   # Bad: Depends on external API
   def test_fetch_user_data():
       response = requests.get('https://api.example.com/user/1')
       assert response.status_code == 200

   # Good: Mock network calls
   from unittest.mock import patch, Mock

   def test_fetch_user_data():
       with patch('requests.get') as mock_get:
           mock_get.return_value = Mock(status_code=200, json=lambda: {'id': 1})
           response = requests.get('https://api.example.com/user/1')
           assert response.status_code == 200
   ```

   **Database State Issues**:
   ```python
   # Bad: Doesn't clean up database
   def test_create_user():
       user = User.create(username='test')
       assert user.id is not None
       # Database now has 'test' user for other tests

   # Good: Use fixtures for setup/teardown
   import pytest

   @pytest.fixture
   def db_session():
       session = create_session()
       yield session
       session.rollback()  # Clean up after test

   def test_create_user(db_session):
       user = User.create(username='test')
       assert user.id is not None
       # Automatically rolled back
   ```

   **Race Conditions**:
   ```javascript
   // Bad: Async timing issues
   test('saves data', () => {
       saveData({ id: 1 });  // Async but not awaited
       expect(getData()).toContain({ id: 1 });  // May fail
   });

   // Good: Properly await async operations
   test('saves data', async () => {
       await saveData({ id: 1 });
       const data = await getData();
       expect(data).toContain({ id: 1 });
   });
   ```

### Step 5: Mocking and Test Doubles

**Evaluate use of mocks, stubs, and fakes:**

1. **Mock Quality Assessment**

   **Python - Good Mocking**:
   ```python
   from unittest.mock import patch, Mock

   def test_send_email_notification():
       # Mock external email service
       with patch('app.services.EmailService') as mock_email:
           mock_email.return_value.send.return_value = True

           result = send_welcome_email('user@example.com')

           # Verify email service was called correctly
           mock_email.return_value.send.assert_called_once_with(
               to='user@example.com',
               subject='Welcome',
               template='welcome'
           )
           assert result is True
   ```

   **JavaScript - Good Mocking**:
   ```javascript
   // Mock external dependencies
   jest.mock('../services/emailService');

   test('sends welcome email', async () => {
       const emailService = require('../services/emailService');
       emailService.send.mockResolvedValue(true);

       const result = await sendWelcomeEmail('user@example.com');

       expect(emailService.send).toHaveBeenCalledWith({
           to: 'user@example.com',
           subject: 'Welcome',
           template: 'welcome'
       });
       expect(result).toBe(true);
   });
   ```

   **Java - Good Mocking (Mockito)**:
   ```java
   @Test
   public void testSendEmailNotification() {
       EmailService emailService = mock(EmailService.class);
       when(emailService.send(anyString(), anyString())).thenReturn(true);

       NotificationService notificationService = new NotificationService(emailService);
       boolean result = notificationService.sendWelcome("user@example.com");

       verify(emailService).send(eq("user@example.com"), eq("Welcome"));
       assertTrue(result);
   }
   ```

2. **Over-Mocking Detection**

   **Bad: Too much mocking (testing the mock)**:
   ```python
   def test_calculate_order_total():
       # Over-mocked - testing mocks, not real logic
       mock_item1 = Mock(price=10)
       mock_item2 = Mock(price=20)
       mock_order = Mock()
       mock_order.items = [mock_item1, mock_item2]
       mock_calculator = Mock()
       mock_calculator.calculate.return_value = 30

       result = mock_calculator.calculate(mock_order)
       assert result == 30  # Just testing the mock returned what we told it to
   ```

   **Good: Minimal mocking**:
   ```python
   def test_calculate_order_total():
       # Only mock external dependencies, test real logic
       order = Order(items=[
           Item(name="Widget", price=10),
           Item(name="Gadget", price=20)
       ])

       total = calculate_order_total(order)
       assert total == 30  # Testing real calculation
   ```

### Step 6: Edge Cases and Error Handling

**Verify comprehensive edge case coverage:**

1. **Edge Case Checklist**

   **Boundary Values**:
   ```python
   def test_age_validation_boundaries():
       # Test boundary values
       assert validate_age(0) is True      # Minimum valid
       assert validate_age(150) is True    # Maximum valid
       assert validate_age(-1) is False    # Just below minimum
       assert validate_age(151) is False   # Just above maximum
   ```

   **Empty/Null Values**:
   ```python
   def test_process_data_edge_cases():
       assert process_data([]) == []       # Empty list
       assert process_data(None) is None   # Null value
       assert process_data("") == ""       # Empty string
   ```

   **Large Inputs**:
   ```python
   def test_sort_large_dataset():
       large_list = list(range(1000000))
       random.shuffle(large_list)
       sorted_list = custom_sort(large_list)
       assert sorted_list == list(range(1000000))
   ```

2. **Error Handling Tests**

   **Python**:
   ```python
   def test_division_by_zero():
       with pytest.raises(ZeroDivisionError):
           divide(10, 0)

   def test_invalid_input_type():
       with pytest.raises(TypeError, match="Expected int, got str"):
           calculate(10, "invalid")

   def test_file_not_found():
       with pytest.raises(FileNotFoundError):
           read_config("nonexistent.yaml")
   ```

   **JavaScript**:
   ```javascript
   test('throws error on division by zero', () => {
       expect(() => divide(10, 0)).toThrow('Division by zero');
   });

   test('rejects promise on invalid input', async () => {
       await expect(fetchUser('invalid-id'))
           .rejects
           .toThrow('Invalid user ID');
   });
   ```

### Step 7: CI/CD Integration Review

**Assess test automation and integration:**

1. **CI/CD Pipeline Analysis**

   **GitHub Actions Example**:
   ```yaml
   name: Test Suite

   on: [push, pull_request]

   jobs:
     test:
       runs-on: ubuntu-latest

       steps:

         - uses: actions/checkout@v2

         - name: Set up Python
           uses: actions/setup-python@v2
           with:
             python-version: 3.9

         - name: Install dependencies
           run: pip install -r requirements.txt

         - name: Run tests
           run: pytest --cov=src --cov-report=xml

         - name: Upload coverage
           uses: codecov/codecov-action@v2
           with:
             files: ./coverage.xml
   ```

   **Check for**:

   - Tests run on every commit/PR

   - Multiple environments tested (Python versions, Node versions, etc.)

   - Coverage reports generated

   - Test failures block merges

   - Parallel test execution for speed

2. **Test Execution Performance**

   **Measure Test Speed**:
   ```bash
   # Python: Show slowest tests
   pytest --durations=10

   # JavaScript: Jest with timing
   npm test -- --verbose

   # Identify slow tests (>1s each)
   ```

   **Optimization Strategies**:

   - Parallelize test execution

   - Use test selection (run only affected tests)

   - Mock slow dependencies

   - Use in-memory databases for tests

### Step 8: Generate Testing Report

**Compile findings into comprehensive report:**

```markdown
# Testing Review Report

**Project**: [Name]
**Date**: [Date]
**Reviewer**: [Name]

## Executive Summary

- **Overall Testing Grade**: [A-F]

- **Coverage**: [%] lines, [%] branches

- **Total Tests**: [count]

- **Test Quality**: [Excellent/Good/Fair/Poor]

- **Flaky Tests**: [count]

- **Critical Gaps**: [count]

## Test Coverage Analysis

### Overall Metrics
- **Line Coverage**: [%]

- **Branch Coverage**: [%]

- **Function Coverage**: [%]

- **Target**: 80% line, 75% branch

### Coverage by Module
| Module | Lines | Branches | Functions | Grade |
|--------|-------|----------|-----------|-------|
| core/auth.py | 95% | 88% | 100% | A |
| utils/helpers.py | 45% | 30% | 60% | D |
| api/endpoints.py | 78% | 70% | 85% | B |

### Critical Coverage Gaps

#### Gap 1: Error Handling Not Tested
- **Location**: src/auth.py lines 45-60

- **Risk**: High - authentication failure paths untested

- **Recommendation**: Add tests for invalid credentials, expired tokens

#### Gap 2: Edge Cases Missing
- **Location**: src/utils/parser.py

- **Risk**: Medium - boundary conditions not validated

- **Recommendation**: Test empty inputs, null values, large datasets

## Test Suite Inventory

### Test Distribution
- **Unit Tests**: [count] ([%])

- **Integration Tests**: [count] ([%])

- **E2E Tests**: [count] ([%])

- **Performance Tests**: [count]

**Assessment**: [Follows test pyramid / Inverted pyramid / Needs rebalancing]

### Test Organization
```
tests/
├── unit/ (123 tests)
├── integration/ (45 tests)
├── e2e/ (12 tests)
└── performance/ (5 tests)
```

**Assessment**: [Well-organized / Needs improvement / Poor structure]

## Test Quality Assessment

### Naming Conventions
- **Good Names**: [%]

- **Poor Names**: [count] tests need renaming

- **Examples of Issues**:

  - test_1, test_2, test_function (non-descriptive)

### Test Structure (AAA Pattern)
- **Following AAA**: [%]

- **Mixed Structure**: [count] tests

- **No Clear Structure**: [count] tests

### Assertion Quality
- **Strong Assertions**: [%]

- **Weak Assertions**: [count] ("assert x", "assert True")

- **Missing Assertions**: [count] tests

### Test Anti-Patterns Found

#### Pattern 1: Testing Implementation Details
- **Occurrences**: [count]

- **Examples**: [list files/lines]

- **Impact**: Tests brittle, break with refactoring

#### Pattern 2: Multiple Unrelated Assertions
- **Occurrences**: [count]

- **Impact**: Tests unclear, hard to debug failures

#### Pattern 3: Test Interdependence
- **Occurrences**: [count]

- **Impact**: Tests fail when run in isolation

## Test Reliability

### Flaky Tests Detected
| Test | Failure Rate | Cause | Fix |
|------|--------------|-------|-----|
| test_cache_expiration | 15% | Timing | Mock time |
| test_api_response | 8% | Network | Mock HTTP |

### Test Independence
- **Independent Tests**: [%]

- **Dependent Tests**: [count]

- **Recommended Fix**: [Use fixtures, clean up state]

### External Dependencies
- **Network Calls**: [count] tests - [mocked/not mocked]

- **Database Calls**: [count] tests - [using test DB/mocked]

- **File System**: [count] tests - [using temp dir/not isolated]

## Mocking Assessment

### Mock Usage
- **Appropriate Mocking**: [count] tests

- **Over-Mocked**: [count] tests (testing mocks, not logic)

- **Under-Mocked**: [count] tests (hitting real external services)

### Mock Quality Issues
- [List issues with mock usage]

## Edge Case Coverage

### Tested Edge Cases
- **Boundary Values**: [Good/Poor]

- **Null/Empty Inputs**: [Good/Poor]

- **Error Conditions**: [Good/Poor]

- **Large Inputs**: [Good/Poor]

### Missing Edge Case Tests
1. **[Feature]**: No tests for [edge case]

   - **Risk**: [description]

   - **Recommended Tests**: [list]

## CI/CD Integration

### Pipeline Status
- **Tests Run Automatically**: [Yes/No]

- **Environments Tested**: [list]

- **Coverage Tracking**: [Yes/No]

- **Failure Blocks Merge**: [Yes/No]

### Test Execution Performance
- **Total Test Time**: [seconds]

- **Slowest Tests**: [list top 5]

- **Parallel Execution**: [Enabled/Disabled]

- **Target**: <5 minutes total

### Recommendations
- [Enable parallel execution]

- [Optimize slow tests]

- [Add test selection]

## Critical Testing Gaps

### Priority 1 (Immediate)
1. **Untested Authentication Failure Paths**

   - **Risk**: High

   - **Location**: auth.py

   - **Tests Needed**: 5

   - **Effort**: 2 hours

### Priority 2 (Short-term)
1. **Missing Integration Tests for API-Database**

   - **Risk**: Medium

   - **Coverage Gap**: 15%

   - **Tests Needed**: 10

   - **Effort**: 1 day

### Priority 3 (Long-term)
1. **E2E Test Coverage for Critical Flows**

   - **Risk**: Medium

   - **Current**: 2 flows tested

   - **Needed**: 8 flows

   - **Effort**: 1 week

## Test Improvement Roadmap

### Immediate Actions (Week 1)
- [ ] Fix flaky tests

- [ ] Add tests for critical gaps

- [ ] Clean up test anti-patterns

### Short-term (Weeks 2-4)
- [ ] Improve coverage to 80%

- [ ] Refactor poorly named tests

- [ ] Add missing edge case tests

### Medium-term (Months 2-3)
- [ ] Establish testing standards

- [ ] Implement test selection

- [ ] Optimize test execution time

### Long-term (Months 4-6)
- [ ] Comprehensive E2E test suite

- [ ] Performance test automation

- [ ] Property-based testing for critical logic

## Positive Findings

- [Good practices observed]

- [Effective test patterns]

## Next Steps

- [ ] Fix critical testing gaps (P1)

- [ ] Eliminate flaky tests

- [ ] Improve coverage to target levels

- [ ] Establish CI/CD quality gates

- [ ] Train team on testing best practices

- [ ] Proceed to [Phase 6: Final Report](../code-review-final-report/SKILL.md)
```

## Success Criteria

- [ ] Test coverage measured and analyzed

- [ ] Test suite inventory completed

- [ ] Test quality assessed

- [ ] Flaky tests identified

- [ ] Critical gaps documented

- [ ] Edge case coverage verified

- [ ] CI/CD integration reviewed

- [ ] Test improvement roadmap created

- [ ] Team ready for final report generation

## Related Skills

### Code Review Workflow
1. [Phase 1: Context Analysis](../code-review-context-analysis/SKILL.md)

2. [Phase 2: Quality Review](../code-review-quality/SKILL.md)

3. [Phase 3: Security Review](../code-review-security/SKILL.md)

4. [Phase 4: Performance Review](../code-review-performance/SKILL.md)

5. **Phase 5: Testing Review (This Skill)**

6. [Phase 6: Final Report](../code-review-final-report/SKILL.md)

### Supporting Skills
- [`test-driven-development`](../test-driven-development/SKILL.md) - TDD workflow

## Additional Resources

### Testing Tools
- **Python**: pytest, coverage, pytest-cov, pytest-mock, hypothesis

- **JavaScript**: Jest, Mocha, Chai, Sinon, Testing Library

- **Java**: JUnit 5, Mockito, AssertJ, JaCoCo, TestContainers

- **Go**: testing package, testify, gomock, go-sqlmock

- **C/C++**: Google Test, Catch2, CppUTest, gcov, lcov

- **C#**: xUnit, NUnit, Moq, Coverlet, FluentAssertions

### Testing Best Practices
- [Test-Driven Development by Kent Beck](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)

- [xUnit Test Patterns](http://xunitpatterns.com/)

- [Growing Object-Oriented Software, Guided by Tests](http://www.growing-object-oriented-software.com/)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: AI Templates Code Review Workflow, Anthropic Claude Code Best Practices 2025
**Template Source**: `code_review/testing_review/*.md`
