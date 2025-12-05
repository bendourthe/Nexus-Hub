---
template_id: javascript_unit_tests
template_name: Unit Tests - Javascript
version: 1.0.0
last_updated: 2025-12-03
language: Javascript
category: test_development
phase: unit_tests
phase_number: 2
difficulty: intermediate
estimated_time_hours: 3-6
prerequisites:

  - test_development/test_structure/javascript_test_structure.md
related_templates:

  - test_development/test_cases/javascript_test_cases.md
tools:

  - jest (29.7.0)
  - eslint (9.15.0)
  - prettier
tags:

  - test-development
  - testing
  - javascript
---
# JavaScript Unit Tests - Comprehensive Implementation Guide

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                             ► │ ● CURRENT
│ Phase 3: Test Cases Development                    ► │ [NEXT]
│ Phase 4: Mocks & Fixtures                                ► │ 
│ Phase 5: Performance Testing                             ► │ 
│ Phase 6: Code Coverage                                   ► │ 
│ Phase 7: Maintenance & CI/CD                             ► │ 
│ Phase 8: Reward Hacking Validation                       ► │ 
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 1 (Test Structure Setup) should be completed first
**Next Step:** Phase 3 (Test Cases Development)

---


## Objective

Develop a comprehensive unit testing strategy for JavaScript/TypeScript applications using Jest, Mocha, and Vitest frameworks, focusing on test isolation, fast execution, and thorough coverage of individual components following FIRST principles and AAA patterns.

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
- [ ] Jest, Mocha, and Vitest framework comparison completed
- [ ] Test directory structure established
- [ ] Naming conventions documented
- [ ] jest.config.js or vitest.config.js configured
- [ ] Test setup files created

### Test Patterns
- [ ] Pure function tests implemented
- [ ] Class and method tests created
- [ ] Async/await and Promise test patterns established
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
# JavaScript Unit Testing Implementation - Comprehensive Guide

## Context
I need comprehensive guidance for implementing unit tests in a JavaScript/TypeScript application using Jest as the primary framework. Generate a complete implementation guide covering principles, patterns, and practical examples.

## CRITICAL: Output Directory Setup

Before starting, create this exact directory structure:

```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

Replace `${OUTPUT_DIR}` with your desired output location (e.g., `unit_tests_javascript_output`).

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
  - How to identify slow tests with Jest's `--detectSlowTests` flag
  - Techniques to optimize test execution time
  - Avoiding unnecessary I/O operations in tests

- **Independent** - Tests must not depend on each other or shared state
  - How to verify test independence
  - Running tests in random order with `--randomize`
  - Avoiding test pollution with proper cleanup
  - Using `beforeEach` and `afterEach` for isolation

- **Repeatable** - Same results every time, in any environment
  - Dealing with time-dependent code using `jest.useFakeTimers()`
  - Handling randomness with mocking `Math.random()`
  - Environment isolation techniques
  - Freezing time for consistent tests

- **Self-validating** - Clear pass/fail without manual inspection
  - Writing clear assertions with Jest matchers
  - Meaningful error messages
  - Custom matchers for domain-specific assertions
  - Avoiding console.log debugging in tests

- **Timely** - Written before or alongside production code
  - Test-Driven Development (TDD) with JavaScript
  - Benefits of early test writing
  - Maintaining test coverage during refactoring
  - Watch mode for continuous testing

**AAA Pattern (Arrange-Act-Assert):**
```javascript
describe('calculateDiscount', () => {
  test('applies 20% discount correctly', () => {
    // Arrange - Set up test data and preconditions
    const originalPrice = 100;
    const discountRate = 0.20;
    const calculator = new PriceCalculator();

    // Act - Execute the function being tested
    const finalPrice = calculator.calculateDiscount(originalPrice, discountRate);

    // Assert - Verify the expected outcome
    expect(finalPrice).toBe(80);
    expect(calculator.lastDiscount).toBe(20);
  });
});
```

Explain:
- Why separating these phases improves readability
- How to handle tests with complex setup
- When to use helper functions for arrangement
- Dealing with multiple assertions (when appropriate)
- Using `describe` blocks for grouping related tests

### 1.2 Unit vs Integration vs E2E Testing

Create a comparison table:

| Aspect | Unit Test | Integration Test | E2E Test |
|--------|-----------|------------------|----------|
| **Scope** | Single function/class | Multiple modules | Entire application |
| **Dependencies** | Mocked/stubbed | Real (some mocked) | Real |
| **Speed** | <100ms | <1s | Seconds to minutes |
| **Isolation** | Complete | Partial | None |
| **Failure Reason** | Specific function | Module interaction | System behavior |
| **Maintenance** | Easy | Moderate | Complex |
| **Cost** | Low | Medium | High |
| **Tools** | Jest, Vitest | Jest, Mocha | Cypress, Playwright |

Provide guidance on:
- When to write unit tests vs integration tests
- The testing pyramid concept (70% unit, 20% integration, 10% E2E)
- How to identify if a test is truly a unit test
- Converting integration tests to unit tests
- JavaScript-specific testing challenges (callbacks, promises, async/await)

### 1.3 Common Unit Test Anti-Patterns

Document these anti-patterns with examples:

**Anti-Pattern 1: Testing Implementation Instead of Behavior**
```javascript
// BAD - Tests implementation details
test('sort uses quicksort algorithm', () => {
  const sorter = new Sorter();
  sorter.sort([3, 1, 2]);
  expect(sorter.algorithmUsed).toBe('quicksort'); // Implementation detail
});

// GOOD - Tests behavior
test('sort returns ascending order', () => {
  const sorter = new Sorter();
  const result = sorter.sort([3, 1, 2]);
  expect(result).toEqual([1, 2, 3]); // Behavior
});
```

**Anti-Pattern 2: Multiple Unrelated Assertions**
```javascript
// BAD - Tests multiple unrelated concerns
test('user operations', () => {
  const user = new User('John', 'john@example.com');
  expect(user.name).toBe('John');
  expect(user.email).toBe('john@example.com');
  expect(user.createdAt).toBeTruthy();
  expect(user.validateEmail()).toBe(true);
  expect(user.toJSON().name).toBe('John');
});

// GOOD - Separate tests for separate concerns
test('user initialization sets name', () => {
  const user = new User('John', 'john@example.com');
  expect(user.name).toBe('John');
});

test('user initialization sets email', () => {
  const user = new User('John', 'john@example.com');
  expect(user.email).toBe('john@example.com');
});

test('user validates correct email format', () => {
  const user = new User('John', 'john@example.com');
  expect(user.validateEmail()).toBe(true);
});
```

**Anti-Pattern 3: Slow Tests**
```javascript
// BAD - Slow test with unnecessary delays
test('process data with delay', async () => {
  const processor = new DataProcessor();
  await new Promise(resolve => setTimeout(resolve, 1000)); // Unnecessary
  const result = processor.process([1, 2, 3]);
  expect(result).toEqual([2, 4, 6]);
});

// GOOD - Fast test with no delays
test('process data quickly', () => {
  const processor = new DataProcessor();
  const result = processor.process([1, 2, 3]);
  expect(result).toEqual([2, 4, 6]);
});
```

**Anti-Pattern 4: Test Interdependencies**
```javascript
// BAD - Tests depend on execution order
describe('UserWorkflow', () => {
  let user;

  test('1_create_user', () => {
    user = new User('John');
    expect(user.name).toBe('John');
  });

  test('2_update_user', () => {
    user.name = 'Jane'; // Depends on test 1
    expect(user.name).toBe('Jane');
  });
});

// GOOD - Independent tests
describe('UserWorkflow', () => {
  test('create user', () => {
    const user = new User('John');
    expect(user.name).toBe('John');
  });

  test('update user', () => {
    const user = new User('John'); // Create fresh instance
    user.name = 'Jane';
    expect(user.name).toBe('Jane');
  });
});
```

**Anti-Pattern 5: Excessive Mocking**
```javascript
// BAD - Mocking too much, testing mock behavior
test('calculate total with too many mocks', () => {
  const mockCalculator = {
    add: jest.fn(() => 10),
    multiply: jest.fn(() => 20),
    subtract: jest.fn(() => 5)
  };

  const service = new Service(mockCalculator);
  service.calculateTotal([1, 2, 3]);

  expect(mockCalculator.add).toHaveBeenCalled(); // Testing mock, not real code
});

// GOOD - Test real logic, mock only external dependencies
test('calculate total correctly', () => {
  const calculator = new Calculator(); // Real calculator
  const service = new Service(calculator);
  const result = service.calculateTotal([1, 2, 3]);
  expect(result).toBe(6); // Testing real behavior
});
```

**Anti-Pattern 6: Unclear Test Names**
```javascript
// BAD - Unclear what is being tested
test('user test 1', () => {});
test('edge case', () => {});
test('foo', () => {});

// GOOD - Clear, descriptive names
test('user initialization with valid email succeeds', () => {});
test('division by zero throws error', () => {});
test('empty array returns null', () => {});
```

Provide guidance for identifying and fixing each anti-pattern.

---

## Phase 2: Test Organization and Structure

### 2.1 Directory Structure for Unit Tests

Recommend this structure:

```
project/
├── src/
│   ├── calculator.js
│   ├── user.js
│   └── services/
│       ├── payment.js
│       └── notification.js
├── __tests__/                    # Jest convention
│   ├── unit/                     # Unit tests separate from integration
│   │   ├── calculator.test.js    # Mirrors src structure
│   │   ├── user.test.js
│   │   └── services/
│   │       ├── payment.test.js
│   │       └── notification.test.js
│   ├── integration/
│   │   └── ...
│   └── e2e/
│       └── ...
├── jest.config.js                # Jest configuration
├── jest.setup.js                 # Global test setup
└── package.json
```

Alternative structure for Vitest:
```
project/
├── src/
│   ├── calculator.ts
│   ├── calculator.spec.ts        # Co-located tests
│   ├── user.ts
│   └── user.spec.ts
├── vitest.config.ts
└── package.json
```

Explain:
- Why mirror the source structure
- Benefits of separating unit/integration/e2e tests
- When to deviate from this structure
- How Jest/Vitest discover tests
- Co-located vs separate test directories

### 2.2 Test Naming Conventions

Provide detailed naming guidelines:

**File Naming:**
- `*.test.js` - Jest/Vitest convention
- `*.spec.js` - Alternative convention
- Examples: `calculator.test.js`, `userService.test.js`

**Test Suite Naming (describe blocks):**
- Use descriptive names matching the module/class
- Nest describe blocks for clarity
- Examples:
  ```javascript
  describe('Calculator', () => {
    describe('add', () => {
      test('adds two positive numbers', () => {});
    });

    describe('divide', () => {
      test('divides two numbers correctly', () => {});
      test('throws error when dividing by zero', () => {});
    });
  });
  ```

**Test Naming (test/it):**
- Use `test()` or `it()` interchangeably
- Descriptive names: `test('what_condition_expected')`
- Examples:
  ```javascript
  test('calculates discount with valid rate correctly', () => {});
  test('throws error when dividing by zero', () => {});
  test('returns null for empty array', () => {});
  test('user login with invalid password returns false', () => {});
  ```

**Why This Matters:**
- Test names serve as documentation
- Failed tests clearly indicate what went wrong
- No need to read test code to understand purpose
- Test names appear in reports and CI logs

### 2.3 Jest Configuration

Provide comprehensive `jest.config.js` example:

```javascript
/**

 * Jest configuration for unit tests
 * @type {import('jest').Config}
 */
module.exports = {
  // Test environment
  testEnvironment: 'node', // or 'jsdom' for browser-like environment

  // Test patterns
  testMatch: [
    '**/__tests__/**/*.test.js',
    '**/*.spec.js'
  ],

  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.spec.{js,ts}',
    '!src/**/*.test.{js,ts}'
  ],

  coverageDirectory: 'coverage',
  coverageReporters: ['html', 'text', 'lcov'],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },

  // Module paths
  moduleDirectories: ['node_modules', 'src'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1'
  },

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],

  // Transform configuration (for TypeScript, etc.)
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
    '^.+\\.(js|jsx)$': 'babel-jest'
  },

  // Clear mocks between tests
  clearMocks: true,
  resetMocks: true,
  restoreMocks: true,

  // Verbose output
  verbose: true,

  // Timeout for async tests
  testTimeout: 10000,

  // Ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
    '/build/'
  ],

  // Watch plugins
  watchPlugins: [
    'jest-watch-typeahead/filename',
    'jest-watch-typeahead/testname'
  ]
};
```

Alternative Vitest configuration (`vitest.config.ts`):

```typescript
import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    // Test environment
    environment: 'node', // or 'jsdom', 'happy-dom'

    // Test patterns
    include: ['**/*.{test,spec}.{js,ts,jsx,tsx}'],
    exclude: ['node_modules', 'dist', 'build'],

    // Coverage
    coverage: {
      provider: 'v8',
      reporter: ['html', 'text', 'lcov'],
      include: ['src/**/*.{js,ts,jsx,tsx}'],
      exclude: ['**/*.d.ts', '**/*.spec.{js,ts}'],
      thresholds: {
        branches: 80,
        functions: 80,
        lines: 80,
        statements: 80
      }
    },

    // Globals
    globals: true,

    // Setup files
    setupFiles: ['./vitest.setup.ts'],

    // Clear mocks
    clearMocks: true,
    mockReset: true,
    restoreMocks: true,

    // Timeout
    testTimeout: 10000
  },

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
});
```

### 2.4 Global Test Setup

Provide `jest.setup.js` example:

```javascript
/**

 * Global test setup for Jest
 * This file runs before all tests
 */

// Extend Jest matchers
import '@testing-library/jest-dom'; // For DOM matchers

// Mock console methods to reduce noise
global.console = {
  ...console,
  // Suppress console.log in tests
  log: jest.fn(),
  // Uncomment to suppress other methods
  // error: jest.fn(),
  // warn: jest.fn(),
};

// Set default timeout
jest.setTimeout(10000);

// Mock Date for consistent testing
const MOCK_DATE = new Date('2024-01-01T00:00:00.000Z');
global.Date = class extends Date {
  constructor(...args) {
    if (args.length === 0) {
      super(MOCK_DATE);
    } else {
      super(...args);
    }
  }

  static now() {
    return MOCK_DATE.getTime();
  }
};

// Custom matchers
expect.extend({
  toBeWithinRange(received, floor, ceiling) {
    const pass = received >= floor && received <= ceiling;
    if (pass) {
      return {
        message: () =>
          `expected ${received} not to be within range ${floor} - ${ceiling}`,
        pass: true
      };
    } else {
      return {
        message: () =>
          `expected ${received} to be within range ${floor} - ${ceiling}`,
        pass: false
      };
    }
  }
});

// Global test utilities
global.createMockUser = (overrides = {}) => ({
  id: 1,
  name: 'John Doe',
  email: 'john@example.com',
  ...overrides
});

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
});
```

---

## Phase 3: Testing Different Component Types

### 3.1 Testing Pure Functions

Pure functions (no side effects, deterministic) are easiest to test.

**Example Function:**
```javascript
// src/calculator.js
/**

 * Calculate discounted price
 * @param {number} price - Original price
 * @param {number} discountRate - Discount rate (0.0 to 1.0)
 * @returns {number} Final price after discount
 * @throws {Error} If price is negative or discount rate is invalid
 */
export function calculateDiscount(price, discountRate) {
  if (price < 0) {
    throw new Error('Price cannot be negative');
  }
  if (discountRate < 0 || discountRate > 1) {
    throw new Error('Discount rate must be between 0 and 1');
  }

  return price * (1 - discountRate);
}
```

**Comprehensive Tests:**
```javascript
// __tests__/unit/calculator.test.js
import { calculateDiscount } from '../../src/calculator';

describe('calculateDiscount', () => {
  describe('with valid inputs', () => {
    test('no discount returns original price', () => {
      const result = calculateDiscount(100, 0);
      expect(result).toBe(100);
    });

    test('full discount returns zero', () => {
      const result = calculateDiscount(100, 1.0);
      expect(result).toBe(0);
    });

    test('20% discount calculates correctly', () => {
      const result = calculateDiscount(100, 0.20);
      expect(result).toBe(80);
    });

    test('50% discount calculates correctly', () => {
      const result = calculateDiscount(200, 0.50);
      expect(result).toBe(100);
    });

    test('small price with discount', () => {
      const result = calculateDiscount(5, 0.10);
      expect(result).toBeCloseTo(4.5);
    });

    test('large price with discount', () => {
      const result = calculateDiscount(10000, 0.15);
      expect(result).toBe(8500);
    });

    test('floating point precision', () => {
      const result = calculateDiscount(99.99, 0.333);
      expect(result).toBeCloseTo(66.7033, 2); // Within 2 decimal places
    });

    test('zero price returns zero', () => {
      const result = calculateDiscount(0, 0.50);
      expect(result).toBe(0);
    });
  });

  describe('with invalid inputs', () => {
    test('negative price throws error', () => {
      expect(() => calculateDiscount(-100, 0.20))
        .toThrow('Price cannot be negative');
    });

    test('discount rate below zero throws error', () => {
      expect(() => calculateDiscount(100, -0.10))
        .toThrow('Discount rate must be between 0 and 1');
    });

    test('discount rate above one throws error', () => {
      expect(() => calculateDiscount(100, 1.5))
        .toThrow('Discount rate must be between 0 and 1');
    });
  });

  describe('edge cases', () => {
    test.each([
      [100, 0.10, 90],
      [50, 0.20, 40],
      [200, 0.25, 150],
      [75, 0.333, 50.025]
    ])('calculateDiscount(%d, %f) = %d', (price, discount, expected) => {
      const result = calculateDiscount(price, discount);
      expect(result).toBeCloseTo(expected, 2);
    });
  });
});
```

**Key Principles:**
- Test happy path (normal inputs)
- Test edge cases (boundaries: 0%, 100%, 0 price)
- Test error conditions (negative price, invalid discount)
- Test floating-point precision with `toBeCloseTo()`
- Use `test.each()` for parametrized tests
- Group related tests with nested `describe` blocks

### 3.2 Testing Classes and Methods

**Example Class:**
```javascript
// src/user.js
export class User {
  /**

   * Create a new user
   * @param {string} name - User name
   * @param {string} email - User email
   * @param {number} [age] - User age
   */
  constructor(name, email, age = null) {
    if (!name) {
      throw new Error('Name cannot be empty');
    }
    if (!this._isValidEmail(email)) {
      throw new Error('Invalid email format');
    }
    if (age !== null && age < 0) {
      throw new Error('Age cannot be negative');
    }

    this._name = name;
    this._email = email;
    this._age = age;
    this._createdAt = new Date();
    this._active = true;
  }

  get name() {
    return this._name;
  }

  get email() {
    return this._email;
  }

  get age() {
    return this._age;
  }

  get isActive() {
    return this._active;
  }

  deactivate() {
    this._active = false;
  }

  activate() {
    this._active = true;
  }

  _isValidEmail(email) {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email);
  }

  toJSON() {
    return {
      name: this._name,
      email: this._email,
      age: this._age,
      active: this._active,
      createdAt: this._createdAt.toISOString()
    };
  }
}
```

**Comprehensive Tests:**
```javascript
// __tests__/unit/user.test.js
import { User } from '../../src/user';

describe('User', () => {
  describe('constructor', () => {
    test('initializes with all parameters', () => {
      const user = new User('John Doe', 'john@example.com', 30);

      expect(user.name).toBe('John Doe');
      expect(user.email).toBe('john@example.com');
      expect(user.age).toBe(30);
      expect(user.isActive).toBe(true);
    });

    test('initializes without age parameter', () => {
      const user = new User('Jane Doe', 'jane@example.com');

      expect(user.name).toBe('Jane Doe');
      expect(user.email).toBe('jane@example.com');
      expect(user.age).toBeNull();
    });

    test('sets createdAt timestamp', () => {
      const before = new Date();
      const user = new User('John', 'john@example.com');
      const after = new Date();

      expect(user._createdAt).toBeInstanceOf(Date);
      expect(user._createdAt.getTime()).toBeGreaterThanOrEqual(before.getTime());
      expect(user._createdAt.getTime()).toBeLessThanOrEqual(after.getTime());
    });

    test('throws error for empty name', () => {
      expect(() => new User('', 'john@example.com'))
        .toThrow('Name cannot be empty');
    });

    test('throws error for invalid email format', () => {
      expect(() => new User('John', 'invalid-email'))
        .toThrow('Invalid email format');
    });

    test('throws error for negative age', () => {
      expect(() => new User('John', 'john@example.com', -5))
        .toThrow('Age cannot be negative');
    });

    test.each([
      'user@example.com',
      'first.last@example.com',
      'user+tag@example.co.uk',
      'user123@subdomain.example.com'
    ])('accepts valid email format: %s', (email) => {
      const user = new User('John', email);
      expect(user.email).toBe(email);
    });

    test.each([
      'invalid',
      '@example.com',
      'user@',
      'user @example.com',
      'user@.com'
    ])('rejects invalid email format: %s', (email) => {
      expect(() => new User('John', email))
        .toThrow('Invalid email format');
    });
  });

  describe('properties', () => {
    let user;

    beforeEach(() => {
      user = new User('John', 'john@example.com', 25);
    });

    test('name property returns correct value', () => {
      expect(user.name).toBe('John');
    });

    test('email property returns correct value', () => {
      expect(user.email).toBe('john@example.com');
    });

    test('age property returns correct value', () => {
      expect(user.age).toBe(25);
    });

    test('isActive property returns true initially', () => {
      expect(user.isActive).toBe(true);
    });
  });

  describe('activation methods', () => {
    let user;

    beforeEach(() => {
      user = new User('John', 'john@example.com');
    });

    test('deactivate sets isActive to false', () => {
      user.deactivate();
      expect(user.isActive).toBe(false);
    });

    test('activate sets isActive to true', () => {
      user.deactivate();
      user.activate();
      expect(user.isActive).toBe(true);
    });

    test('multiple deactivations keep user inactive', () => {
      user.deactivate();
      user.deactivate();
      expect(user.isActive).toBe(false);
    });

    test('multiple activations keep user active', () => {
      user.activate();
      user.activate();
      expect(user.isActive).toBe(true);
    });
  });

  describe('toJSON method', () => {
    test('contains all fields', () => {
      const user = new User('John', 'john@example.com', 30);
      const json = user.toJSON();

      expect(json).toHaveProperty('name');
      expect(json).toHaveProperty('email');
      expect(json).toHaveProperty('age');
      expect(json).toHaveProperty('active');
      expect(json).toHaveProperty('createdAt');
    });

    test('values match user properties', () => {
      const user = new User('John', 'john@example.com', 30);
      const json = user.toJSON();

      expect(json.name).toBe('John');
      expect(json.email).toBe('john@example.com');
      expect(json.age).toBe(30);
      expect(json.active).toBe(true);
    });

    test('handles null age correctly', () => {
      const user = new User('John', 'john@example.com');
      const json = user.toJSON();

      expect(json.age).toBeNull();
    });

    test('createdAt is in ISO format', () => {
      const user = new User('John', 'john@example.com');
      const json = user.toJSON();

      expect(json.createdAt).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
      expect(() => new Date(json.createdAt)).not.toThrow();
    });

    test('reflects deactivated user', () => {
      const user = new User('John', 'john@example.com');
      user.deactivate();
      const json = user.toJSON();

      expect(json.active).toBe(false);
    });
  });
});
```

**Key Principles:**
- Group related tests with nested `describe` blocks
- Use `beforeEach` for common setup
- Test each method independently
- Test properties and state changes
- Test both valid and invalid inputs
- Verify error messages in exceptions
- Use parametrized tests with `test.each()`

### 3.3 Testing Asynchronous Code

**Example Async Functions:**
```javascript
// src/asyncOperations.js
export async function fetchData(url, timeout = 5000) {
  if (!url) {
    throw new Error('URL cannot be empty');
  }

  // Simulate async operation
  await new Promise(resolve => setTimeout(resolve, 100));

  if (url.includes('timeout')) {
    throw new Error('Request timed out');
  }

  return {
    status: 'success',
    url,
    data: { message: 'Data fetched' }
  };
}

export async function fetchMultiple(urls) {
  const promises = urls.map(url =>
    fetchData(url).catch(error => error)
  );
  return Promise.all(promises);
}

export function fetchDataCallback(url, callback) {
  setTimeout(() => {
    if (!url) {
      callback(new Error('URL cannot be empty'));
    } else {
      callback(null, { status: 'success', url });
    }
  }, 100);
}
```

**Comprehensive Tests:**
```javascript
// __tests__/unit/asyncOperations.test.js
import { fetchData, fetchMultiple, fetchDataCallback } from '../../src/asyncOperations';

describe('fetchData', () => {
  describe('with valid inputs', () => {
    test('returns success response', async () => {
      const result = await fetchData('https://example.com');

      expect(result.status).toBe('success');
      expect(result.url).toBe('https://example.com');
      expect(result.data).toHaveProperty('message');
    });

    test('accepts custom timeout', async () => {
      const result = await fetchData('https://example.com', 10000);
      expect(result.status).toBe('success');
    });

    test('handles multiple sequential calls', async () => {
      const result1 = await fetchData('https://example1.com');
      const result2 = await fetchData('https://example2.com');

      expect(result1.url).toBe('https://example1.com');
      expect(result2.url).toBe('https://example2.com');
    });
  });

  describe('with invalid inputs', () => {
    test('empty URL throws error', async () => {
      await expect(fetchData(''))
        .rejects
        .toThrow('URL cannot be empty');
    });

    test('timeout URL throws error', async () => {
      await expect(fetchData('https://timeout.com'))
        .rejects
        .toThrow('Request timed out');
    });
  });

  describe('error handling', () => {
    test('catches and handles async errors', async () => {
      try {
        await fetchData('https://timeout.com');
        fail('Should have thrown error');
      } catch (error) {
        expect(error.message).toBe('Request timed out');
      }
    });
  });
});

describe('fetchMultiple', () => {
  test('returns all results for valid URLs', async () => {
    const urls = [
      'https://example1.com',
      'https://example2.com',
      'https://example3.com'
    ];
    const results = await fetchMultiple(urls);

    expect(results).toHaveLength(3);
    expect(results[0].status).toBe('success');
    expect(results[1].status).toBe('success');
    expect(results[2].status).toBe('success');
  });

  test('handles single URL', async () => {
    const results = await fetchMultiple(['https://example.com']);

    expect(results).toHaveLength(1);
    expect(results[0].status).toBe('success');
  });

  test('returns empty array for empty input', async () => {
    const results = await fetchMultiple([]);
    expect(results).toEqual([]);
  });

  test('handles mix of success and errors', async () => {
    const urls = [
      'https://example.com',
      'https://timeout.com',
      'https://example2.com'
    ];
    const results = await fetchMultiple(urls);

    expect(results).toHaveLength(3);
    expect(results[0].status).toBe('success');
    expect(results[1]).toBeInstanceOf(Error);
    expect(results[2].status).toBe('success');
  });
});

describe('fetchDataCallback', () => {
  test('calls callback with success result', (done) => {
    fetchDataCallback('https://example.com', (error, result) => {
      expect(error).toBeNull();
      expect(result.status).toBe('success');
      expect(result.url).toBe('https://example.com');
      done();
    });
  });

  test('calls callback with error for empty URL', (done) => {
    fetchDataCallback('', (error, result) => {
      expect(error).toBeInstanceOf(Error);
      expect(error.message).toBe('URL cannot be empty');
      expect(result).toBeUndefined();
      done();
    });
  });

  test('handles callback async operation', async () => {
    // Using promise wrapper for callback
    const result = await new Promise((resolve, reject) => {
      fetchDataCallback('https://example.com', (error, result) => {
        if (error) reject(error);
        else resolve(result);
      });
    });

    expect(result.status).toBe('success');
  });
});

describe('async test patterns', () => {
  test('using async/await', async () => {
    const result = await fetchData('https://example.com');
    expect(result.status).toBe('success');
  });

  test('using .resolves matcher', async () => {
    await expect(fetchData('https://example.com'))
      .resolves
      .toHaveProperty('status', 'success');
  });

  test('using .rejects matcher', async () => {
    await expect(fetchData(''))
      .rejects
      .toThrow('URL cannot be empty');
  });

  test('using return promise', () => {
    return fetchData('https://example.com').then(result => {
      expect(result.status).toBe('success');
    });
  });
});
```

**Key Principles:**
- Use `async/await` for cleaner test code
- Use `.resolves` and `.rejects` matchers for assertions
- Use `done` callback for callback-based async code
- Test promise resolution and rejection
- Test concurrent async operations
- Handle errors properly in async tests
- Use `fail()` in try-catch blocks to ensure errors are thrown

### 3.4 Testing Callbacks and Promises

**Example Functions:**
```javascript
// src/promiseOperations.js
export function delayedPromise(ms, value) {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), ms);
  });
}

export function rejectedPromise(ms, reason) {
  return new Promise((_, reject) => {
    setTimeout(() => reject(new Error(reason)), ms);
  });
}

export function promiseChain(initialValue) {
  return Promise.resolve(initialValue)
    .then(value => value * 2)
    .then(value => value + 10)
    .then(value => value / 2);
}
```

**Comprehensive Tests:**
```javascript
// __tests__/unit/promiseOperations.test.js
import { delayedPromise, rejectedPromise, promiseChain } from '../../src/promiseOperations';

describe('delayedPromise', () => {
  test('resolves with value after delay', async () => {
    const result = await delayedPromise(10, 'test value');
    expect(result).toBe('test value');
  });

  test('resolves with number value', async () => {
    const result = await delayedPromise(10, 42);
    expect(result).toBe(42);
  });

  test('resolves with object value', async () => {
    const obj = { key: 'value' };
    const result = await delayedPromise(10, obj);
    expect(result).toEqual(obj);
  });
});

describe('rejectedPromise', () => {
  test('rejects with error after delay', async () => {
    await expect(rejectedPromise(10, 'Test error'))
      .rejects
      .toThrow('Test error');
  });

  test('rejected promise contains error message', async () => {
    try {
      await rejectedPromise(10, 'Custom error');
      fail('Should have rejected');
    } catch (error) {
      expect(error).toBeInstanceOf(Error);
      expect(error.message).toBe('Custom error');
    }
  });
});

describe('promiseChain', () => {
  test('processes chain correctly with positive number', async () => {
    const result = await promiseChain(10);
    // (10 * 2 + 10) / 2 = 30 / 2 = 15
    expect(result).toBe(15);
  });

  test('processes chain correctly with zero', async () => {
    const result = await promiseChain(0);
    // (0 * 2 + 10) / 2 = 10 / 2 = 5
    expect(result).toBe(5);
  });

  test('processes chain correctly with negative number', async () => {
    const result = await promiseChain(-5);
    // (-5 * 2 + 10) / 2 = 0 / 2 = 0
    expect(result).toBe(0);
  });
});

describe('promise patterns', () => {
  test('Promise.all with multiple promises', async () => {
    const promises = [
      delayedPromise(10, 'one'),
      delayedPromise(20, 'two'),
      delayedPromise(15, 'three')
    ];

    const results = await Promise.all(promises);
    expect(results).toEqual(['one', 'two', 'three']);
  });

  test('Promise.race returns first resolved', async () => {
    const promises = [
      delayedPromise(50, 'slow'),
      delayedPromise(10, 'fast'),
      delayedPromise(30, 'medium')
    ];

    const result = await Promise.race(promises);
    expect(result).toBe('fast');
  });

  test('Promise.allSettled handles mix of resolved and rejected', async () => {
    const promises = [
      delayedPromise(10, 'success'),
      rejectedPromise(10, 'failure'),
      delayedPromise(10, 'another success')
    ];

    const results = await Promise.allSettled(promises);

    expect(results[0].status).toBe('fulfilled');
    expect(results[0].value).toBe('success');
    expect(results[1].status).toBe('rejected');
    expect(results[1].reason.message).toBe('failure');
    expect(results[2].status).toBe('fulfilled');
    expect(results[2].value).toBe('another success');
  });
});
```

**Key Principles:**
- Test both promise resolution and rejection
- Test promise chains and transformations
- Use `Promise.all`, `Promise.race`, `Promise.allSettled` patterns
- Handle async timing with proper awaits
- Test error propagation through promise chains

### 3.5 Testing Event Emitters

**Example Event Emitter:**
```javascript
// src/eventEmitter.js
import { EventEmitter } from 'events';

export class DataProcessor extends EventEmitter {
  constructor() {
    super();
    this.processed = [];
  }

  process(data) {
    this.emit('start', { data });

    try {
      const result = data.map(item => item * 2);
      this.processed.push(...result);
      this.emit('complete', { result });
      return result;
    } catch (error) {
      this.emit('error', error);
      throw error;
    }
  }

  reset() {
    this.processed = [];
    this.emit('reset');
  }
}
```

**Comprehensive Tests:**
```javascript
// __tests__/unit/eventEmitter.test.js
import { DataProcessor } from '../../src/eventEmitter';

describe('DataProcessor', () => {
  let processor;

  beforeEach(() => {
    processor = new DataProcessor();
  });

  describe('event emissions', () => {
    test('emits start event when processing begins', () => {
      const startSpy = jest.fn();
      processor.on('start', startSpy);

      processor.process([1, 2, 3]);

      expect(startSpy).toHaveBeenCalledTimes(1);
      expect(startSpy).toHaveBeenCalledWith({ data: [1, 2, 3] });
    });

    test('emits complete event when processing finishes', () => {
      const completeSpy = jest.fn();
      processor.on('complete', completeSpy);

      processor.process([1, 2, 3]);

      expect(completeSpy).toHaveBeenCalledTimes(1);
      expect(completeSpy).toHaveBeenCalledWith({ result: [2, 4, 6] });
    });

    test('emits error event on processing failure', () => {
      const errorSpy = jest.fn();
      processor.on('error', errorSpy);

      expect(() => processor.process(null)).toThrow();
      expect(errorSpy).toHaveBeenCalledTimes(1);
    });

    test('emits reset event when reset is called', () => {
      const resetSpy = jest.fn();
      processor.on('reset', resetSpy);

      processor.reset();

      expect(resetSpy).toHaveBeenCalledTimes(1);
    });
  });

  describe('processing', () => {
    test('processes data correctly', () => {
      const result = processor.process([1, 2, 3]);
      expect(result).toEqual([2, 4, 6]);
    });

    test('stores processed data', () => {
      processor.process([1, 2, 3]);
      expect(processor.processed).toEqual([2, 4, 6]);
    });

    test('accumulates processed data across multiple calls', () => {
      processor.process([1, 2]);
      processor.process([3, 4]);
      expect(processor.processed).toEqual([2, 4, 6, 8]);
    });

    test('reset clears processed data', () => {
      processor.process([1, 2, 3]);
      processor.reset();
      expect(processor.processed).toEqual([]);
    });
  });

  describe('multiple listeners', () => {
    test('notifies multiple listeners', () => {
      const listener1 = jest.fn();
      const listener2 = jest.fn();

      processor.on('complete', listener1);
      processor.on('complete', listener2);

      processor.process([1, 2]);

      expect(listener1).toHaveBeenCalled();
      expect(listener2).toHaveBeenCalled();
    });

    test('removes listener correctly', () => {
      const listener = jest.fn();
      processor.on('complete', listener);
      processor.off('complete', listener);

      processor.process([1, 2]);

      expect(listener).not.toHaveBeenCalled();
    });
  });
});
```

**Key Principles:**
- Test event emissions with spy functions
- Test event payloads
- Test multiple listeners
- Test listener removal
- Test error events
- Use `jest.fn()` for event listeners

### 3.6 Testing Closures and Higher-Order Functions

**Example Functions:**
```javascript
// src/closures.js
export function createCounter(initialValue = 0) {
  let count = initialValue;

  return {
    increment() {
      count++;
      return count;
    },
    decrement() {
      count--;
      return count;
    },
    getValue() {
      return count;
    },
    reset() {
      count = initialValue;
    }
  };
}

export function createMultiplier(factor) {
  return function(value) {
    return value * factor;
  };
}

export function compose(...fns) {
  return function(initialValue) {
    return fns.reduceRight((value, fn) => fn(value), initialValue);
  };
}

export function memoize(fn) {
  const cache = new Map();

  return function(...args) {
    const key = JSON.stringify(args);
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = fn(...args);
    cache.set(key, result);
    return result;
  };
}
```

**Comprehensive Tests:**
```javascript
// __tests__/unit/closures.test.js
import { createCounter, createMultiplier, compose, memoize } from '../../src/closures';

describe('createCounter', () => {
  test('initializes with default value of zero', () => {
    const counter = createCounter();
    expect(counter.getValue()).toBe(0);
  });

  test('initializes with custom value', () => {
    const counter = createCounter(10);
    expect(counter.getValue()).toBe(10);
  });

  test('increment increases count', () => {
    const counter = createCounter();
    counter.increment();
    expect(counter.getValue()).toBe(1);
  });

  test('increment returns new value', () => {
    const counter = createCounter();
    const result = counter.increment();
    expect(result).toBe(1);
  });

  test('decrement decreases count', () => {
    const counter = createCounter(5);
    counter.decrement();
    expect(counter.getValue()).toBe(4);
  });

  test('multiple operations work correctly', () => {
    const counter = createCounter();
    counter.increment();
    counter.increment();
    counter.decrement();
    expect(counter.getValue()).toBe(1);
  });

  test('reset returns to initial value', () => {
    const counter = createCounter(10);
    counter.increment();
    counter.increment();
    counter.reset();
    expect(counter.getValue()).toBe(10);
  });

  test('multiple counters are independent', () => {
    const counter1 = createCounter();
    const counter2 = createCounter();

    counter1.increment();
    counter1.increment();
    counter2.increment();

    expect(counter1.getValue()).toBe(2);
    expect(counter2.getValue()).toBe(1);
  });
});

describe('createMultiplier', () => {
  test('creates function that multiplies by factor', () => {
    const double = createMultiplier(2);
    expect(double(5)).toBe(10);
  });

  test('works with different factors', () => {
    const triple = createMultiplier(3);
    expect(triple(4)).toBe(12);
  });

  test('handles zero factor', () => {
    const zero = createMultiplier(0);
    expect(zero(5)).toBe(0);
  });

  test('handles negative factor', () => {
    const negate = createMultiplier(-1);
    expect(negate(5)).toBe(-5);
  });

  test('multiple multipliers are independent', () => {
    const double = createMultiplier(2);
    const triple = createMultiplier(3);

    expect(double(5)).toBe(10);
    expect(triple(5)).toBe(15);
  });
});

describe('compose', () => {
  const add10 = x => x + 10;
  const multiply2 = x => x * 2;
  const subtract5 = x => x - 5;

  test('composes two functions', () => {
    const composed = compose(add10, multiply2);
    expect(composed(5)).toBe(20); // (5 * 2) + 10
  });

  test('composes three functions', () => {
    const composed = compose(subtract5, add10, multiply2);
    expect(composed(5)).toBe(15); // ((5 * 2) + 10) - 5
  });

  test('composes single function', () => {
    const composed = compose(add10);
    expect(composed(5)).toBe(15);
  });

  test('composes no functions returns identity', () => {
    const composed = compose();
    expect(composed(5)).toBe(5);
  });

  test('applies functions right to left', () => {
    const composed = compose(multiply2, add10);
    expect(composed(5)).toBe(30); // (5 + 10) * 2
  });
});

describe('memoize', () => {
  test('returns cached result for same arguments', () => {
    const expensiveFn = jest.fn((x) => x * 2);
    const memoized = memoize(expensiveFn);

    expect(memoized(5)).toBe(10);
    expect(memoized(5)).toBe(10);
    expect(memoized(5)).toBe(10);

    expect(expensiveFn).toHaveBeenCalledTimes(1);
  });

  test('computes new result for different arguments', () => {
    const expensiveFn = jest.fn((x) => x * 2);
    const memoized = memoize(expensiveFn);

    expect(memoized(5)).toBe(10);
    expect(memoized(10)).toBe(20);

    expect(expensiveFn).toHaveBeenCalledTimes(2);
  });

  test('handles multiple arguments', () => {
    const add = jest.fn((a, b) => a + b);
    const memoized = memoize(add);

    expect(memoized(2, 3)).toBe(5);
    expect(memoized(2, 3)).toBe(5);

    expect(add).toHaveBeenCalledTimes(1);
  });

  test('distinguishes between different argument combinations', () => {
    const add = jest.fn((a, b) => a + b);
    const memoized = memoize(add);

    expect(memoized(2, 3)).toBe(5);
    expect(memoized(3, 2)).toBe(5);

    expect(add).toHaveBeenCalledTimes(2);
  });
});
```

**Key Principles:**
- Test closure state management
- Test function independence
- Test higher-order function composition
- Test memoization caching behavior
- Use `jest.fn()` to track function calls

---

## Phase 4: Edge Cases and Error Handling

### 4.1 Boundary Value Testing

Test values at the edges of valid ranges:

```javascript
describe('validateScore', () => {
  test('minimum boundary (0)', () => {
    expect(validateScore(0)).toBe(true);
  });

  test('below minimum boundary (-1)', () => {
    expect(validateScore(-1)).toBe(false);
  });

  test('maximum boundary (100)', () => {
    expect(validateScore(100)).toBe(true);
  });

  test('above maximum boundary (101)', () => {
    expect(validateScore(101)).toBe(false);
  });

  test('just inside minimum (1)', () => {
    expect(validateScore(1)).toBe(true);
  });

  test('just inside maximum (99)', () => {
    expect(validateScore(99)).toBe(true);
  });
});
```

### 4.2 Null/Undefined Handling

Test behavior with null and undefined values:

```javascript
describe('null and undefined handling', () => {
  test('function with null argument', () => {
    expect(process(null)).toBeNull();
  });

  test('function with undefined argument', () => {
    expect(process(undefined)).toBeUndefined();
  });

  test('function returns null for empty input', () => {
    expect(findItem([])).toBeNull();
  });

  test('optional parameter defaults to undefined', () => {
    const obj = new MyClass();
    expect(obj.optionalField).toBeUndefined();
  });

  test('distinguishes between null and undefined', () => {
    expect(getValue(null)).not.toBe(getValue(undefined));
  });
});
```

### 4.3 Empty Collections

Test behavior with empty arrays, objects, and strings:

```javascript
describe('empty collections', () => {
  test('empty array returns zero', () => {
    expect(sumArray([])).toBe(0);
  });

  test('empty object returns empty result', () => {
    expect(processObject({})).toEqual({});
  });

  test('empty string throws error', () => {
    expect(() => parse('')).toThrow();
  });

  test('empty set returns false', () => {
    expect(hasElements(new Set())).toBe(false);
  });

  test('empty map is handled correctly', () => {
    expect(getFromMap(new Map(), 'key')).toBeUndefined();
  });
});
```

### 4.4 Exception Testing

Test that exceptions are raised correctly:

```javascript
describe('exception handling', () => {
  test('division by zero throws error', () => {
    expect(() => divide(10, 0)).toThrow();
  });

  test('invalid input throws specific error', () => {
    expect(() => validate(-5))
      .toThrow('Input must be positive');
  });

  test('error type is correct', () => {
    expect(() => validate(-5))
      .toThrow(ValidationError);
  });

  test('error message matches pattern', () => {
    expect(() => validate(-5))
      .toThrow(/must be positive/);
  });

  test('async function rejects with error', async () => {
    await expect(asyncFunction())
      .rejects
      .toThrow('Async error');
  });

  test('custom error contains details', () => {
    try {
      validateComplexInput(badData);
      fail('Should have thrown error');
    } catch (error) {
      expect(error).toBeInstanceOf(ValidationError);
      expect(error.code).toBe('INVALID_FORMAT');
      expect(error.details).toHaveProperty('fieldName');
    }
  });
});
```

### 4.5 Type Coercion Testing

Test JavaScript's type coercion behavior:

```javascript
describe('type coercion', () => {
  test('string coercion', () => {
    expect(add('5', '10')).toBe('510'); // String concatenation
  });

  test('number coercion', () => {
    expect(multiply('5', 2)).toBe(10); // String to number
  });

  test('boolean coercion', () => {
    expect(isTrue('false')).toBe(true); // Truthy string
  });

  test('null coercion', () => {
    expect(Number(null)).toBe(0);
  });

  test('undefined coercion', () => {
    expect(Number(undefined)).toBeNaN();
  });
});
```

### 4.6 Large Inputs and Performance

Test performance and correctness with large inputs:

```javascript
describe('performance and large inputs', () => {
  test('processes large array', () => {
    const largeArray = Array.from({ length: 100000 }, (_, i) => i);
    const result = processList(largeArray);
    expect(result).toHaveLength(100000);
  });

  test('handles deep recursion', () => {
    const result = fibonacci(50);
    expect(result).toBeGreaterThan(0);
  });

  test('performance test', () => {
    const start = Date.now();
    processLargeData(hugeDataset);
    const elapsed = Date.now() - start;
    expect(elapsed).toBeLessThan(1000); // Should complete within 1 second
  });

  test('memory usage with large objects', () => {
    const largeObject = createLargeObject();
    expect(Object.keys(largeObject).length).toBe(10000);
  });
});
```

---

## Phase 5: Test Quality and Maintenance

### 5.1 Using Jest Mocks

**Mock Functions:**
```javascript
describe('jest mock functions', () => {
  test('mock function basic usage', () => {
    const mockFn = jest.fn();
    mockFn('arg1', 'arg2');

    expect(mockFn).toHaveBeenCalled();
    expect(mockFn).toHaveBeenCalledWith('arg1', 'arg2');
    expect(mockFn).toHaveBeenCalledTimes(1);
  });

  test('mock function with return value', () => {
    const mockFn = jest.fn(() => 42);
    const result = mockFn();

    expect(result).toBe(42);
    expect(mockFn).toHaveBeenCalled();
  });

  test('mock function with different return values', () => {
    const mockFn = jest.fn()
      .mockReturnValueOnce('first')
      .mockReturnValueOnce('second')
      .mockReturnValue('default');

    expect(mockFn()).toBe('first');
    expect(mockFn()).toBe('second');
    expect(mockFn()).toBe('default');
  });

  test('mock implementation', () => {
    const mockFn = jest.fn((a, b) => a + b);
    expect(mockFn(2, 3)).toBe(5);
  });

  test('mock resolved value for async', async () => {
    const mockFn = jest.fn().mockResolvedValue('success');
    const result = await mockFn();
    expect(result).toBe('success');
  });

  test('mock rejected value for async', async () => {
    const mockFn = jest.fn().mockRejectedValue(new Error('failed'));
    await expect(mockFn()).rejects.toThrow('failed');
  });
});
```

**Mock Modules:**
```javascript
// __tests__/unit/userService.test.js
import { UserService } from '../../src/userService';
import { apiClient } from '../../src/apiClient';

// Mock the entire module
jest.mock('../../src/apiClient');

describe('UserService with mocked API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('getUser calls API with correct ID', async () => {
    apiClient.get.mockResolvedValue({ id: 1, name: 'John' });

    const service = new UserService();
    const user = await service.getUser(1);

    expect(apiClient.get).toHaveBeenCalledWith('/users/1');
    expect(user.name).toBe('John');
  });

  test('handles API error', async () => {
    apiClient.get.mockRejectedValue(new Error('API Error'));

    const service = new UserService();
    await expect(service.getUser(1)).rejects.toThrow('API Error');
  });
});
```

**Spy on Methods:**
```javascript
describe('spying on methods', () => {
  test('spy on object method', () => {
    const calculator = {
      add: (a, b) => a + b
    };

    const spy = jest.spyOn(calculator, 'add');
    const result = calculator.add(2, 3);

    expect(spy).toHaveBeenCalledWith(2, 3);
    expect(result).toBe(5);

    spy.mockRestore();
  });

  test('spy and override implementation', () => {
    const user = {
      getName: () => 'John'
    };

    const spy = jest.spyOn(user, 'getName').mockReturnValue('Jane');
    expect(user.getName()).toBe('Jane');
    expect(spy).toHaveBeenCalled();

    spy.mockRestore();
    expect(user.getName()).toBe('John');
  });
});
```

### 5.2 Test Coverage

**Running Coverage:**
```bash
# Run tests with coverage
jest --coverage

# Coverage for specific directory
jest --coverage --collectCoverageFrom='src/**/*.js'

# Watch mode with coverage
jest --watch --coverage

# Generate HTML report
jest --coverage --coverageReporters='html'
```

**Coverage Thresholds in jest.config.js:**
```javascript
module.exports = {
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    },
    './src/critical/': {
      branches: 95,
      functions: 95,
      lines: 95,
      statements: 95
    }
  }
};
```

### 5.3 Test Maintenance Checklist

Create a maintenance checklist:

- [ ] All tests pass independently
- [ ] Tests can run in any order
- [ ] Each test has clear, descriptive name
- [ ] Tests execute in <100ms each
- [ ] No duplicate setup code (use beforeEach/fixtures)
- [ ] No test logic complexity (loops, conditionals)
- [ ] Clear assertions with helpful messages
- [ ] Tests are properly documented
- [ ] Mocks are used appropriately (not excessively)
- [ ] Edge cases are covered
- [ ] Error conditions are tested
- [ ] Tests follow AAA pattern
- [ ] Test coverage is >80% for critical code
- [ ] No console.log statements in tests
- [ ] Async tests properly handle promises
- [ ] Mock cleanup in afterEach

### 5.4 Debugging Tests

**Debug individual test:**
```bash
# Run specific test file
jest path/to/test.js

# Run specific test by name
jest -t 'test name pattern'

# Run in debug mode
node --inspect-brk node_modules/.bin/jest --runInBand

# Verbose output
jest --verbose

# No coverage (faster debugging)
jest --no-coverage
```

**Debug in VS Code:**
```json
{
  "type": "node",
  "request": "launch",
  "name": "Jest Debug",
  "program": "${workspaceFolder}/node_modules/.bin/jest",
  "args": ["--runInBand", "--no-cache"],
  "console": "integratedTerminal",
  "internalConsoleOptions": "neverOpen"
}
```

---

## Output Format

Generate the following deliverables:

### 1. Unit Test Implementation Guide (20-30 pages)
Comprehensive document saved to `${OUTPUT_DIR}/exports/unit_test_implementation_guide.md` covering:

- FIRST principles detailed explanation
- AAA pattern with examples
- Unit vs Integration vs E2E comparison
- Test organization strategies
- Framework-specific best practices (Jest, Mocha, Vitest)
- Common anti-patterns and solutions

### 2. Test Examples Collection
File saved to `${OUTPUT_DIR}/exports/unit_test_examples.md` containing:

- 50+ example test functions
- Pure function tests
- Class and method tests
- Async code tests (async/await, Promises, callbacks)
- Event emitter tests
- Closure and higher-order function tests
- Edge case examples
- Error handling examples

### 3. Test Templates
Files saved to `${OUTPUT_DIR}/templates/`:

- `unit_test_template.js` - Basic test template
- `class_test_template.js` - Class testing template
- `async_test_template.js` - Async testing template
- `mock_test_template.js` - Mocking patterns template
- `jest.config.js` - Complete Jest configuration
- `vitest.config.ts` - Complete Vitest configuration
- `jest.setup.js` - Global test setup

### 4. Configuration Files
Files saved to `${OUTPUT_DIR}/templates/`:

- `jest.config.js` - Complete Jest configuration
- `vitest.config.ts` - Complete Vitest configuration
- `mocha.opts` - Mocha configuration
- `.babelrc` - Babel configuration for ES6+
- `tsconfig.json` - TypeScript configuration

### 5. Visual Assets
Files saved to `${OUTPUT_DIR}/assets/`:

- `first_principles_diagram.png` - Visual representation of FIRST principles
- `aaa_pattern_visualization.png` - AAA pattern flowchart
- `test_pyramid.png` - Testing pyramid diagram
- `test_organization_structure.png` - Directory structure diagram
- `async_testing_patterns.png` - Async testing patterns

### 6. Anti-Patterns Guide
File saved to `${OUTPUT_DIR}/exports/anti_patterns_guide.md`:

- Common anti-patterns with examples
- How to identify each anti-pattern
- Refactoring strategies
- Before/after examples
- JavaScript-specific anti-patterns

### 7. Unit Test Quality Checklist
File saved to `${OUTPUT_DIR}/exports/unit_test_quality_checklist.md`:

- Test independence checklist
- Performance checklist
- Code quality checklist
- Maintenance checklist
- Review guidelines

### 8. Mocking and Stubbing Guide
File saved to `${OUTPUT_DIR}/exports/mocking_guide.md`:

- When to use mocks vs stubs
- Jest mocking patterns
- Module mocking strategies
- Spy usage examples
- Mock cleanup best practices

---

## File Output Instructions

**Critical:** Organize all generated files according to this structure:

```
${OUTPUT_DIR}/
├── templates/
│   ├── unit_test_template.js
│   ├── class_test_template.js
│   ├── async_test_template.js
│   ├── mock_test_template.js
│   ├── jest.config.js
│   ├── vitest.config.ts
│   ├── jest.setup.js
│   ├── mocha.opts
│   ├── .babelrc
│   └── tsconfig.json
├── assets/
│   ├── first_principles_diagram.png
│   ├── aaa_pattern_visualization.png
│   ├── test_pyramid.png
│   ├── test_organization_structure.png
│   └── async_testing_patterns.png
└── exports/
    ├── unit_test_implementation_guide.md (20-30 pages)
    ├── unit_test_examples.md (50+ tests)
    ├── anti_patterns_guide.md
    ├── unit_test_quality_checklist.md
    └── mocking_guide.md
```

**Directory Creation:**
Before generating content, ensure directories exist:
```bash
mkdir -p ${OUTPUT_DIR}/templates ${OUTPUT_DIR}/assets ${OUTPUT_DIR}/exports
```

---

## Verification Checklist

After generating all content, verify:

- [ ] All 8+ deliverables are created
- [ ] Files are saved to correct directories (templates/, assets/, exports/)
- [ ] Implementation guide is 20-30 pages
- [ ] 50+ test examples are included
- [ ] FIRST principles are thoroughly explained
- [ ] AAA pattern is demonstrated in all examples
- [ ] Common anti-patterns are documented
- [ ] Jest, Mocha, and Vitest examples are included
- [ ] Configuration files are complete and usable
- [ ] Visual diagrams are included (or placeholders)
- [ ] All code examples are syntactically correct
- [ ] Repository information is included where applicable
- [ ] Quality checklist is comprehensive
- [ ] Async testing patterns (async/await, Promises, callbacks) are covered
- [ ] Mock and spy usage is thoroughly documented

---
~~~

End of prompt template.

---

## Additional Notes

- Install Jest: `npm install --save-dev jest @types/jest`
- Install Vitest: `npm install --save-dev vitest`
- Install Mocha: `npm install --save-dev mocha chai`
- Run unit tests: `jest` or `npm test`
- Check coverage: `jest --coverage`
- Watch mode: `jest --watch`
- Debug tests: `node --inspect-brk node_modules/.bin/jest --runInBand`

---

**Status:** Template ready for use. Copy the prompt section above into your AI assistant to generate comprehensive JavaScript unit testing guidance.
