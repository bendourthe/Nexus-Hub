---
template_id: javascript_test_cases
template_name: Test Cases Development - Javascript
version: 1.0.0
last_updated: 2025-12-03
language: Javascript
category: test_development
phase: test_cases
phase_number: 3
difficulty: intermediate
estimated_time_hours: 4-8
prerequisites:
  - test_development/unit_tests/javascript_unit_tests.md
related_templates:
  - test_development/mocks_fixtures/javascript_mocks_fixtures.md
tools:
  - jest (29.7.0)
  - eslint (9.15.0)
  - prettier
tags:
  - test-development
  - testing
  - javascript
---
# JavaScript Test Case Development

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                            ► │ [COMPLETE]
│ Phase 3: Test Cases Development                 ► │ ● CURRENT
│ Phase 4: Mocks & Fixtures                          ► │ [NEXT]
│ Phase 5: Performance Testing                             ► │ 
│ Phase 6: Code Coverage                                   ► │ 
│ Phase 7: Maintenance & CI/CD                             ► │ 
│ Phase 8: Reward Hacking Validation                       ► │ 
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 2 (Unit Tests) should be completed first
**Next Step:** Phase 4 (Mocks & Fixtures)

---


## Objective
Develop comprehensive, well-structured test cases that validate functionality, cover edge cases, handle error conditions, and provide clear documentation of expected behavior using Jest or Mocha testing frameworks.

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

- [ ] Async operations properly tested

### Test Quality

- [ ] Tests follow AAA pattern (Arrange-Act-Assert)

- [ ] Test names clearly describe what is tested

- [ ] Tests are isolated and independent

- [ ] Tests execute quickly (<1s for unit tests)

- [ ] Assertions are specific and meaningful

- [ ] No test interdependencies

- [ ] Proper cleanup in afterEach/afterAll

### Test Organization

- [ ] Tests grouped logically by feature/module

- [ ] Related tests organized in describe blocks

- [ ] Parametrized tests used for multiple scenarios

- [ ] Setup and teardown properly implemented

- [ ] Test documentation provided

- [ ] Mocks and spies used appropriately

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# JavaScript Test Case Development

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

Please develop comprehensive test cases for this JavaScript code following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Phase 1: Test Case Planning

1. **Analyze Code to Test**
   - Identify all exported functions/methods/classes
   - Document expected behavior
   - List input parameters and types
   - Define expected outputs
   - Note side effects (API calls, DOM manipulation, state changes)
   - Identify async operations

2. **Identify Test Scenarios**

   **Happy Path**:
   - Normal operation with valid inputs
   - Expected use cases
   - Successful execution flows
   - Resolved promises

   **Edge Cases**:
   - Boundary values (0, -1, Infinity, NaN)
   - Empty arrays/objects
   - Null and undefined values
   - Large data sets
   - Special characters in strings
   - Concurrent async operations

   **Error Conditions**:
   - Invalid inputs
   - Missing required parameters
   - Type errors
   - Rejected promises
   - Network failures
   - Timeout scenarios

3. **Create Test Case Matrix**

   | Scenario | Input | Expected Output | Test Type | Priority |
   |----------|-------|-----------------|-----------|----------|
   | [description] | [values] | [result] | [unit/integration] | [high/med/low] |

## Phase 2: Unit Test Implementation (Jest)

### AAA Pattern (Arrange-Act-Assert)

Follow this structure for clear, maintainable tests:

```javascript
/**
 * Unit tests for userService module.
 *
 * Tests cover user creation, validation, and retrieval.
 */
import { createUser, validateEmail, getUserById } from './userService';
import { db } from './database';

// Mock external dependencies
jest.mock('./database');

describe('userService', () => {
  // Clean up after each test
  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('createUser', () => {
    it('should create user with valid data and return user object', () => {
      // Arrange - Set up test data and mocks
      const userData = {
        name: 'Alice',
        email: 'alice@example.com',
        age: 30
      };
      const mockUserId = 123;
      db.insert.mockResolvedValue(mockUserId);

      // Act - Execute the function being tested
      const result = createUser(userData);

      // Assert - Verify the result matches expectations
      expect(result).toEqual({
        id: mockUserId,
        name: 'Alice',
        email: 'alice@example.com',
        age: 30
      });
      expect(db.insert).toHaveBeenCalledWith('users', userData);
    });

    it('should throw error when email is invalid', () => {
      // Arrange
      const invalidData = {
        name: 'Bob',
        email: 'not-an-email',
        age: 25
      };

      // Act & Assert - Use expect().toThrow for exception testing
      expect(() => {
        createUser(invalidData);
      }).toThrow('Invalid email format');
    });

    it('should use default age when age is not provided', () => {
      // Arrange
      const dataWithoutAge = {
        name: 'Charlie',
        email: 'charlie@example.com'
      };
      const expectedDefaultAge = 18;

      // Act
      const result = createUser(dataWithoutAge);

      // Assert
      expect(result.age).toBe(expectedDefaultAge);
    });
  });
});
```

### Test Naming Conventions

Use descriptive names that explain what is tested:

**Pattern**: `should <expected behavior> when <condition>`

**Examples**:
```javascript
// Good test names
it('should return user data when user exists', () => {});
it('should throw ValidationError when email is duplicate', () => {});
it('should return null when user ID does not exist', () => {});
it('should reject promise when network request fails', () => {});

// Poor test names (avoid these)
it('creates user', () => {});                    // Too generic
it('test 1', () => {});                          // Non-descriptive
it('handles error', () => {});                   // Unclear what error
it('edge case', () => {});                       // Vague
```

### Testing Different Scenarios

**1. Testing Return Values**:
```javascript
describe('calculateTotal', () => {
  it('should return correct sum for array of numbers', () => {
    const items = [10.0, 20.0, 30.0];
    const result = calculateTotal(items);
    expect(result).toBe(60.0);
  });

  it('should return zero for empty array', () => {
    expect(calculateTotal([])).toBe(0);
  });

  it('should handle negative values correctly', () => {
    const items = [10.0, -5.0, 15.0];
    expect(calculateTotal(items)).toBe(20.0);
  });

  it('should return NaN when array contains non-numbers', () => {
    const items = [10, 'invalid', 20];
    expect(calculateTotal(items)).toBeNaN();
  });
});
```

**2. Testing Exceptions**:
```javascript
describe('divide', () => {
  it('should throw error when dividing by zero', () => {
    expect(() => divide(10, 0)).toThrow('Cannot divide by zero');
  });

  it('should throw TypeError when arguments are not numbers', () => {
    expect(() => divide('10', 5)).toThrow(TypeError);
  });
});

describe('parseDate', () => {
  it('should throw error with specific message for invalid format', () => {
    expect(() => parseDate('not-a-date')).toThrow(/Invalid date format/);
  });
});
```

**3. Testing Async Operations**:
```javascript
describe('fetchUser', () => {
  it('should return user data when API call succeeds', async () => {
    // Arrange
    const mockUser = { id: 1, name: 'Alice' };
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve(mockUser)
      })
    );

    // Act
    const user = await fetchUser(1);

    // Assert
    expect(user).toEqual(mockUser);
    expect(fetch).toHaveBeenCalledWith('/api/users/1');
  });

  it('should reject promise when API returns error', async () => {
    // Arrange
    global.fetch = jest.fn(() => Promise.reject(new Error('Network error')));

    // Act & Assert
    await expect(fetchUser(1)).rejects.toThrow('Network error');
  });

  it('should timeout after specified duration', async () => {
    // Arrange
    const slowFetch = () => new Promise(resolve => setTimeout(resolve, 5000));

    // Act & Assert
    await expect(fetchUserWithTimeout(1, 1000)).rejects.toThrow('Timeout');
  });
});
```

**4. Testing Side Effects and Mocks**:
```javascript
describe('saveUser', () => {
  it('should call database insert with correct data', () => {
    // Arrange
    const user = { name: 'Alice', email: 'alice@example.com' };
    const mockDb = {
      insert: jest.fn()
    };

    // Act
    saveUser(user, mockDb);

    // Assert - Verify database was called correctly
    expect(mockDb.insert).toHaveBeenCalledTimes(1);
    expect(mockDb.insert).toHaveBeenCalledWith('users', user);
  });
});

describe('sendEmail', () => {
  it('should invoke email service with correct parameters', () => {
    // Arrange
    const emailService = {
      send: jest.fn()
    };

    // Act
    sendEmail('test@example.com', 'Hello', emailService);

    // Assert
    expect(emailService.send).toHaveBeenCalledWith({
      to: 'test@example.com',
      subject: 'Hello'
    });
  });
});
```

**5. Testing DOM Manipulation**:
```javascript
describe('updateCounter', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="counter">0</div>';
  });

  it('should update counter element text', () => {
    // Act
    updateCounter(5);

    // Assert
    const counterElement = document.getElementById('counter');
    expect(counterElement.textContent).toBe('5');
  });

  it('should create counter element if it does not exist', () => {
    // Arrange
    document.body.innerHTML = '';

    // Act
    updateCounter(10);

    // Assert
    const counterElement = document.getElementById('counter');
    expect(counterElement).not.toBeNull();
    expect(counterElement.textContent).toBe('10');
  });
});
```

### Parametrized Tests (Using test.each)

Test multiple scenarios efficiently:

```javascript
describe('numberToWord', () => {
  test.each([
    [0, 'zero'],
    [1, 'one'],
    [5, 'five'],
    [10, 'ten'],
  ])('should convert %i to "%s"', (input, expected) => {
    expect(numberToWord(input)).toBe(expected);
  });
});

describe('validateEmail', () => {
  test.each([
    [''],                           // Empty string
    ['not-an-email'],              // No @ symbol
    ['@example.com'],              // Missing local part
    ['user@'],                     // Missing domain
    ['user @example.com'],         // Space in email
  ])('should reject invalid email: "%s"', (email) => {
    expect(() => validateEmail(email)).toThrow();
  });
});

describe('isAdult', () => {
  test.each([
    [17, false],
    [18, true],
    [21, true],
    [100, true],
  ])('should return %s for age %i', (age, expected) => {
    expect(isAdult(age)).toBe(expected);
  });
});
```

### Testing Edge Cases and Boundaries

```javascript
describe('processValue', () => {
  describe('boundary conditions', () => {
    it('should handle minimum valid value', () => {
      expect(processValue(0)).toBe(expectedMinResult);
    });

    it('should handle maximum valid value', () => {
      expect(processValue(100)).toBe(expectedMaxResult);
    });

    it('should throw error for value below minimum', () => {
      expect(() => processValue(-1)).toThrow('Value out of range');
    });

    it('should throw error for value above maximum', () => {
      expect(() => processValue(101)).toThrow('Value out of range');
    });
  });

  describe('special values', () => {
    it('should handle null input', () => {
      expect(processValue(null)).toBeNull();
    });

    it('should handle undefined input', () => {
      expect(processValue(undefined)).toBeUndefined();
    });

    it('should handle NaN input', () => {
      expect(processValue(NaN)).toBeNaN();
    });

    it('should handle Infinity', () => {
      expect(processValue(Infinity)).toBe(Infinity);
    });
  });
});

describe('processCollection', () => {
  it('should return empty array for empty input', () => {
    expect(processCollection([])).toEqual([]);
  });

  it('should handle single item array', () => {
    expect(processCollection([1])).toEqual([1]);
  });

  it('should handle large arrays efficiently', () => {
    const largeArray = Array.from({ length: 10000 }, (_, i) => i);
    const result = processCollection(largeArray);
    expect(result).toHaveLength(10000);
  });
});
```

## Phase 3: Integration Test Implementation

Integration tests verify multiple components working together:

```javascript
/**
 * Integration tests for user registration workflow.
 *
 * Tests the complete user registration process including
 * validation, database storage, and email notification.
 */
import { UserService } from './UserService';
import { Database } from './Database';
import { EmailService } from './EmailService';

describe('UserRegistration Integration', () => {
  let userService;
  let database;
  let emailService;

  beforeEach(async () => {
    // Set up test database
    database = new Database({ test: true });
    await database.connect();
    await database.clear();

    // Mock email service
    emailService = {
      send: jest.fn().mockResolvedValue(true)
    };

    userService = new UserService(database, emailService);
  });

  afterEach(async () => {
    await database.disconnect();
  });

  it('should create database entry and send welcome email', async () => {
    // Arrange
    const userData = {
      username: 'newuser',
      email: 'newuser@example.com',
      password: 'SecurePass123!'
    };

    // Act
    const userId = await userService.registerUser(userData);

    // Assert - Verify database entry
    const user = await database.findUserById(userId);
    expect(user).not.toBeNull();
    expect(user.username).toBe('newuser');
    expect(user.email).toBe('newuser@example.com');
    expect(user.password).not.toBe('SecurePass123!'); // Should be hashed

    // Assert - Verify email sent
    expect(emailService.send).toHaveBeenCalledTimes(1);
    expect(emailService.send).toHaveBeenCalledWith(
      expect.objectContaining({
        to: 'newuser@example.com',
        subject: expect.stringContaining('Welcome')
      })
    );
  });

  it('should rollback database changes when email fails', async () => {
    // Arrange
    emailService.send.mockRejectedValue(new Error('Email service down'));
    const userData = {
      username: 'testuser',
      email: 'test@example.com',
      password: 'Pass123!'
    };

    // Act & Assert
    await expect(userService.registerUser(userData)).rejects.toThrow('Email service down');

    // Verify no user was created
    const users = await database.findUserByEmail('test@example.com');
    expect(users).toBeNull();
  });
});
```

### API Integration Tests

```javascript
import request from 'supertest';
import app from './app';

describe('API Endpoints', () => {
  describe('POST /api/users', () => {
    it('should create user and return 201 status', async () => {
      // Arrange
      const userData = {
        username: 'testuser',
        email: 'test@example.com'
      };

      // Act
      const response = await request(app)
        .post('/api/users')
        .send(userData)
        .expect('Content-Type', /json/)
        .expect(201);

      // Assert
      expect(response.body).toHaveProperty('id');
      expect(response.body.username).toBe('testuser');
    });

    it('should return 400 for invalid data', async () => {
      // Arrange
      const invalidData = {
        username: '',
        email: 'not-an-email'
      };

      // Act
      const response = await request(app)
        .post('/api/users')
        .send(invalidData)
        .expect(400);

      // Assert
      expect(response.body).toHaveProperty('error');
    });
  });

  describe('GET /api/users/:id', () => {
    it('should return user data when user exists', async () => {
      // Arrange - Create user first
      const createResponse = await request(app)
        .post('/api/users')
        .send({ username: 'alice', email: 'alice@example.com' });
      const userId = createResponse.body.id;

      // Act
      const response = await request(app)
        .get(`/api/users/${userId}`)
        .expect(200);

      // Assert
      expect(response.body.id).toBe(userId);
      expect(response.body.username).toBe('alice');
    });

    it('should return 404 when user does not exist', async () => {
      await request(app)
        .get('/api/users/99999')
        .expect(404);
    });
  });
});
```

## Phase 4: End-to-End Test Implementation

E2E tests validate complete user workflows (using Cypress or Puppeteer):

```javascript
/**
 * End-to-end tests for e-commerce checkout flow.
 *
 * Tests the complete user journey from adding items to cart
 * through payment and order confirmation.
 */
describe('Checkout Workflow', () => {
  beforeEach(() => {
    // Reset database and seed test data
    cy.task('db:seed');
    cy.visit('/');
  });

  it('should complete purchase from cart to confirmation', () => {
    // Login
    cy.visit('/login');
    cy.get('input[name="username"]').type('testuser');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard');

    // Add product to cart
    cy.visit('/products/1');
    cy.get('button').contains('Add to Cart').click();
    cy.get('.cart-count').should('contain', '1');

    // Proceed to checkout
    cy.get('.cart-icon').click();
    cy.get('button').contains('Checkout').click();

    // Fill shipping information
    cy.get('input[name="address"]').type('123 Test St');
    cy.get('input[name="city"]').type('Test City');
    cy.get('input[name="zip"]').type('12345');
    cy.get('button').contains('Continue').click();

    // Enter payment information
    cy.get('input[name="cardNumber"]').type('4111111111111111');
    cy.get('input[name="expiry"]').type('12/25');
    cy.get('input[name="cvv"]').type('123');
    cy.get('button').contains('Place Order').click();

    // Verify confirmation
    cy.url().should('include', '/order-confirmation');
    cy.contains('Thank you').should('be.visible');
    cy.get('.order-number').should('exist');
  });

  it('should show error when payment fails', () => {
    // ... setup steps ...

    // Use invalid card
    cy.get('input[name="cardNumber"]').type('0000000000000000');
    cy.get('button').contains('Place Order').click();

    // Verify error message
    cy.get('.error-message').should('contain', 'Payment failed');
    cy.url().should('include', '/checkout');
  });
});
```

## Phase 5: Test Best Practices

### 1. Test Independence

```javascript
// GOOD - Tests are independent
describe('UserService', () => {
  beforeEach(async () => {
    await clearDatabase();
  });

  it('should create user', async () => {
    const user = await createUser('alice');
    expect(user.id).toBeDefined();
  });

  it('should delete user', async () => {
    const user = await createUser('bob');
    await deleteUser(user.id);
    const found = await getUser(user.id);
    expect(found).toBeNull();
  });
});

// BAD - Tests depend on each other
describe('UserService', () => {
  let userId; // Shared state!

  it('should create user', async () => {
    const user = await createUser('alice');
    userId = user.id; // Setting shared state
  });

  it('should delete user', async () => {
    await deleteUser(userId); // Depends on previous test
  });
});
```

### 2. Clear Assertions

```javascript
// GOOD - Specific, clear assertions
it('should create user with correct properties', () => {
  const user = createUser('alice', 'alice@example.com');
  expect(user.username).toBe('alice');
  expect(user.email).toBe('alice@example.com');
  expect(user.createdAt).toBeInstanceOf(Date);
  expect(user.isActive).toBe(true);
});

// BAD - Vague or missing assertions
it('should create user', () => {
  const user = createUser('alice', 'alice@example.com');
  expect(user).toBeTruthy(); // Too vague
  expect(user.username).toBeDefined(); // Checks existence, not value
});
```

### 3. Test Data Management

```javascript
// GOOD - Clear, explicit test data
it('should apply 10% discount on orders over $100', () => {
  const order = {
    items: [
      { price: 50.00, quantity: 2 }, // $100
      { price: 25.00, quantity: 2 }  // $50
    ]
  };
  const discount = calculateDiscount(order);
  expect(discount).toBe(15.00); // 10% of $150
});

// BAD - Magic numbers without context
it('should calculate discount', () => {
  const order = { items: [{ price: 50, quantity: 2 }] };
  expect(calculateDiscount(order)).toBe(10); // Why 10?
});
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
  - Async operations: [count]

### Test Case Implementation

For each module/feature:

**Module**: `[module_name]`
**Test File**: `tests/unit/[module_name].test.js`

**Test Cases**:
1. `should return expected result with valid input`
   - **Scenario**: [description]
   - **Input**: [test data]
   - **Expected**: [result]
   - **Type**: [unit/integration/e2e]

2. `should throw error with invalid input`
   - **Scenario**: [description]
   - **Input**: [test data]
   - **Expected**: [exception type and message]
   - **Type**: [unit/integration/e2e]

### Test Execution Results
```bash
# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Expected output
PASS  tests/unit/userService.test.js
  ✓ should create user with valid data (15ms)
  ✓ should throw error when email is invalid (5ms)
  ✓ should use default age when not provided (3ms)
```

### Coverage Gaps Identified

- [ ] [Function/method]: Missing tests for [scenario]

- [ ] [Function/method]: Need edge case tests for [condition]

- [ ] [Function/method]: Error handling not tested

- [ ] [Function/method]: Async error paths not covered

### Test Quality Metrics

- **Average test execution time**: [milliseconds]

- **Tests following AAA pattern**: [percentage]

- **Tests with clear names**: [percentage]

- **Independent tests**: [percentage]

- **Mock usage**: [appropriate/excessive]

### Next Steps

- [ ] Implement remaining test cases for coverage gaps

- [ ] Add performance benchmarks for critical functions

- [ ] Set up test fixtures for integration tests

- [ ] Configure CI/CD to run tests automatically

- [ ] Review and refactor slow tests

- [ ] Add snapshot tests for component rendering

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
