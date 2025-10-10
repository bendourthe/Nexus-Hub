# JavaScript Test Structure & Infrastructure

## Objective
Design and implement a robust test infrastructure with optimal framework configuration, logical directory organization, efficient fixture management, and reusable test utilities to support comprehensive testing practices in JavaScript/Node.js projects.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/test_structure/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/test_structure/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Test Framework Setup

- [ ] Test framework selected (Jest/Mocha/Jasmine)

- [ ] Configuration files created (jest.config.js, .mocharc.json)

- [ ] Required plugins installed and configured

- [ ] Test discovery rules established

- [ ] Parallel execution configured

### Directory Structure

- [ ] Standard test layout implemented

- [ ] Test type separation (unit/integration/e2e) organized

- [ ] Naming conventions documented

- [ ] Resource directories created

- [ ] Module resolution configured

### Fixture Infrastructure

- [ ] Setup/teardown hooks established

- [ ] Fixture scopes defined appropriately

- [ ] Fixture factories implemented

- [ ] Fixture documentation added

- [ ] Common fixtures centralized

### Test Utilities

- [ ] Common assertion helpers created

- [ ] Test data generators implemented

- [ ] Custom matchers defined

- [ ] Shared base classes established

- [ ] Helper documentation provided

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# JavaScript Test Infrastructure Setup

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/test_structure"
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

Please design and implement a comprehensive test infrastructure for this JavaScript/Node.js project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Phase 1: Framework Selection & Configuration

1. **Test Framework Analysis**
   - **Current State**: Document existing test setup if any
   - **Framework Recommendation**:
     - **Jest** (recommended): All-in-one, zero-config, great DX, built-in coverage
     - **Mocha**: Flexible, requires additional libraries (chai, sinon)
     - **Jasmine**: Behavior-driven, good for legacy projects
     - **Vitest**: Modern, Vite-native, extremely fast
   - **Rationale**: Justify framework choice based on project needs

2. **Install Core Testing Dependencies**

   **For Jest**:
   ```bash
   npm install --save-dev jest @types/jest
   npm install --save-dev @testing-library/jest-dom  # DOM matchers
   npm install --save-dev jest-environment-jsdom     # For browser tests
   ```

   **For Mocha + Chai + Sinon**:
   ```bash
   npm install --save-dev mocha chai sinon
   npm install --save-dev @types/mocha @types/chai @types/sinon
   npm install --save-dev nyc  # Code coverage
   ```

   **For Vitest**:
   ```bash
   npm install --save-dev vitest @vitest/ui
   npm install --save-dev @testing-library/jest-dom
   ```

3. **Configuration File Setup**

   **Jest Configuration** (`jest.config.js`):
   ```javascript
   module.exports = {
     // Test environment
     testEnvironment: 'node', // or 'jsdom' for browser tests

     // Root directory
     rootDir: './',

     // Test file patterns
     testMatch: [
       '**/__tests__/**/*.test.js',
       '**/?(*.)+(spec|test).js'
     ],

     // Coverage configuration
     collectCoverage: true,
     coverageDirectory: 'coverage',
     coverageReporters: ['text', 'lcov', 'html'],
     collectCoverageFrom: [
       'src/**/*.js',
       '!src/**/*.test.js',
       '!src/**/*.spec.js',
       '!**/node_modules/**',
       '!**/dist/**'
     ],
     coverageThreshold: {
       global: {
         branches: 80,
         functions: 80,
         lines: 80,
         statements: 80
       }
     },

     // Setup files
     setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],

     // Module paths
     modulePaths: ['<rootDir>/src'],
     moduleNameMapper: {
       '^@/(.*)$': '<rootDir>/src/$1'
     },

     // Transform files
     transform: {
       '^.+\\.jsx?$': 'babel-jest'
     },

     // Ignore patterns
     testPathIgnorePatterns: [
       '/node_modules/',
       '/dist/',
       '/build/'
     ],

     // Verbose output
     verbose: true,

     // Parallel execution
     maxWorkers: '50%',

     // Timeouts
     testTimeout: 10000,

     // Clear mocks between tests
     clearMocks: true,
     resetMocks: true,
     restoreMocks: true
   };
   ```

   **TypeScript Jest Configuration** (`jest.config.ts`):
   ```typescript
   import type { Config } from 'jest';

   const config: Config = {
     preset: 'ts-jest',
     testEnvironment: 'node',
     roots: ['<rootDir>/src', '<rootDir>/tests'],
     testMatch: ['**/*.test.ts', '**/*.spec.ts'],
     collectCoverageFrom: [
       'src/**/*.ts',
       '!src/**/*.d.ts',
       '!src/**/*.test.ts'
     ],
     moduleNameMapper: {
       '^@/(.*)$': '<rootDir>/src/$1'
     },
     setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
     coverageThreshold: {
       global: {
         branches: 80,
         functions: 80,
         lines: 80,
         statements: 80
       }
     }
   };

   export default config;
   ```

   **Mocha Configuration** (`.mocharc.json`):
   ```json
   {
     "require": ["tests/setup.js"],
     "spec": ["tests/**/*.test.js"],
     "recursive": true,
     "timeout": 5000,
     "color": true,
     "reporter": "spec",
     "parallel": true,
     "jobs": 4
   }
   ```

   **Vitest Configuration** (`vitest.config.js`):
   ```javascript
   import { defineConfig } from 'vitest/config';

   export default defineConfig({
     test: {
       globals: true,
       environment: 'node',
       coverage: {
         provider: 'v8',
         reporter: ['text', 'html', 'lcov'],
         exclude: [
           'node_modules/',
           'tests/',
           '**/*.test.js',
           '**/*.spec.js'
         ],
         threshold: {
           branches: 80,
           functions: 80,
           lines: 80,
           statements: 80
         }
       },
       include: ['tests/**/*.test.js', 'tests/**/*.spec.js'],
       setupFiles: ['tests/setup.js']
     }
   });
   ```

## Phase 2: Directory Structure Design

1. **Standard Test Layout**

   Implement this recommended structure:
   ```
   project_root/
   ├── src/
   │   ├── index.js
   │   ├── components/
   │   │   ├── UserService.js
   │   │   └── AuthService.js
   │   ├── utils/
   │   │   ├── validation.js
   │   │   └── formatters.js
   │   └── config/
   │       └── database.js
   │
   ├── tests/
   │   ├── setup.js                    # Global test setup
   │   ├── teardown.js                 # Global test teardown
   │   │
   │   ├── unit/                       # Unit tests (fast, isolated)
   │   │   ├── components/
   │   │   │   ├── UserService.test.js
   │   │   │   └── AuthService.test.js
   │   │   └── utils/
   │   │       ├── validation.test.js
   │   │       └── formatters.test.js
   │   │
   │   ├── integration/                # Integration tests
   │   │   ├── api/
   │   │   │   ├── userRoutes.test.js
   │   │   │   └── authRoutes.test.js
   │   │   └── database/
   │   │       └── userRepository.test.js
   │   │
   │   ├── e2e/                        # End-to-end tests
   │   │   ├── user-workflows.test.js
   │   │   └── auth-workflows.test.js
   │   │
   │   ├── fixtures/                   # Test data and fixtures
   │   │   ├── users.js
   │   │   ├── products.js
   │   │   └── database.js
   │   │
   │   ├── helpers/                    # Test utilities
   │   │   ├── assertions.js           # Custom assertions
   │   │   ├── factories.js            # Test data factories
   │   │   ├── builders.js             # Object builders
   │   │   └── testUtils.js            # Helper functions
   │   │
   │   ├── mocks/                      # Mock implementations
   │   │   ├── database.js
   │   │   ├── apiClient.js
   │   │   └── emailService.js
   │   │
   │   └── data/                       # Test data files
   │       ├── sample-data.json
   │       ├── test-config.json
   │       └── fixtures.csv
   │
   ├── jest.config.js                  # Test configuration
   ├── .eslintrc.js                    # Linting config
   ├── babel.config.js                 # Transpilation config
   └── package.json
   ```

2. **Naming Conventions**

   **File Naming**:
   - Test files: `*.test.js` or `*.spec.js`
   - Test suites: `describe('ComponentName', ...)`
   - Test cases: `test('should do something', ...)` or `it('should do something', ...)`

   **Examples**:
   ```javascript
   // tests/unit/UserService.test.js
   describe('UserService', () => {
     describe('createUser', () => {
       test('should create user with valid data', () => {
         // Test implementation
       });

       test('should throw error with invalid email', () => {
         // Test implementation
       });
     });

     describe('getUserById', () => {
       test('should return user when found', () => {
         // Test implementation
       });

       test('should return null when user not found', () => {
         // Test implementation
       });
     });
   });

   // Alternative: BDD style with Jasmine/Mocha
   describe('UserService', () => {
     it('should create user with valid data', () => {
       // Test implementation
     });

     it('should throw error with invalid email', () => {
       // Test implementation
     });
   });
   ```

3. **Test Type Organization**

   **Unit Tests** (`tests/unit/`):
   - Test single functions/classes in isolation
   - Fast execution (<100ms per test)
   - No external dependencies
   - Extensive mocking

   **Integration Tests** (`tests/integration/`):
   - Test multiple components together
   - Database, API, service interactions
   - Moderate execution time
   - Minimal mocking

   **E2E Tests** (`tests/e2e/`):
   - Test complete user workflows
   - Full system with real dependencies
   - Slowest execution
   - No mocking of core functionality

## Phase 3: Fixture Infrastructure

1. **Global Setup and Teardown**

   **Global Setup** (`tests/setup.js`):
   ```javascript
   /**
    * Global test setup executed before all tests.
    */

   // Jest extended matchers
   import '@testing-library/jest-dom';

   // Global test timeout
   jest.setTimeout(10000);

   // Mock console methods to reduce noise
   global.console = {
     ...console,
     error: jest.fn(),
     warn: jest.fn(),
   };

   // Set test environment variables
   process.env.NODE_ENV = 'test';
   process.env.DATABASE_URL = 'postgresql://localhost:5432/test_db';

   // Global test utilities
   global.testUtils = {
     sleep: (ms) => new Promise(resolve => setTimeout(resolve, ms)),
     randomString: (length = 10) => Math.random().toString(36).substring(length),
   };

   // Setup fake timers
   beforeAll(() => {
     jest.useFakeTimers();
   });

   afterAll(() => {
     jest.useRealTimers();
   });
   ```

   **Global Teardown** (`tests/teardown.js`):
   ```javascript
   /**
    * Global test teardown executed after all tests.
    */
   module.exports = async () => {
     // Close database connections
     await global.__DATABASE__?.close();

     // Stop any running servers
     await global.__SERVER__?.close();

     // Clean up temp files
     await cleanupTempFiles();
   };
   ```

2. **Jest Hooks**

   ```javascript
   describe('UserService', () => {
     let userService;
     let mockDatabase;

     // Run once before all tests in suite
     beforeAll(() => {
       mockDatabase = createMockDatabase();
     });

     // Run once after all tests in suite
     afterAll(async () => {
       await mockDatabase.close();
     });

     // Run before each test
     beforeEach(() => {
       userService = new UserService(mockDatabase);
       mockDatabase.clear(); // Reset state
     });

     // Run after each test
     afterEach(() => {
       jest.clearAllMocks();
     });

     test('should create user', () => {
       const user = userService.create({ name: 'Alice' });
       expect(user.name).toBe('Alice');
     });
   });
   ```

3. **Fixture Factories**

   **User Factory** (`tests/fixtures/users.js`):
   ```javascript
   /**
    * User test data factory.
    */
   let idCounter = 0;

   export const createUser = (overrides = {}) => {
     idCounter++;
     return {
       id: idCounter,
       username: `user${idCounter}`,
       email: `user${idCounter}@example.com`,
       firstName: 'Test',
       lastName: 'User',
       active: true,
       createdAt: new Date(),
       ...overrides
     };
   };

   export const createUsers = (count, overrides = {}) => {
     return Array.from({ length: count }, () => createUser(overrides));
   };

   export const resetUserFactory = () => {
     idCounter = 0;
   };

   // Usage in tests
   import { createUser, createUsers } from '../fixtures/users';

   test('should handle multiple users', () => {
     const users = createUsers(5);
     expect(users).toHaveLength(5);
     expect(users[0].username).toBe('user1');
   });

   test('should create user with custom data', () => {
     const admin = createUser({ username: 'admin', active: true });
     expect(admin.username).toBe('admin');
   });
   ```

4. **Fixture Builders**

   **Builder Pattern** (`tests/helpers/builders.js`):
   ```javascript
   /**
    * Builder pattern for complex test objects.
    */
   export class UserBuilder {
     constructor() {
       this.user = {
         id: null,
         username: 'testuser',
         email: 'test@example.com',
         roles: [],
         preferences: {},
       };
     }

     withId(id) {
       this.user.id = id;
       return this;
     }

     withUsername(username) {
       this.user.username = username;
       return this;
     }

     withEmail(email) {
       this.user.email = email;
       return this;
     }

     withRole(role) {
       this.user.roles.push(role);
       return this;
     }

     withPreference(key, value) {
       this.user.preferences[key] = value;
       return this;
     }

     build() {
       return { ...this.user };
     }
   }

   // Usage
   const admin = new UserBuilder()
     .withId(1)
     .withUsername('admin')
     .withRole('admin')
     .withRole('moderator')
     .withPreference('theme', 'dark')
     .build();
   ```

## Phase 4: Test Utilities & Helpers

1. **Custom Matchers** (`tests/helpers/assertions.js`):

   ```javascript
   /**
    * Custom Jest matchers for cleaner test assertions.
    */
   expect.extend({
     toBeValidEmail(received) {
       const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
       const pass = emailRegex.test(received);

       return {
         pass,
         message: () =>
           pass
             ? `expected ${received} not to be a valid email`
             : `expected ${received} to be a valid email`,
       };
     },

     toBeWithinRange(received, floor, ceiling) {
       const pass = received >= floor && received <= ceiling;

       return {
         pass,
         message: () =>
           pass
             ? `expected ${received} not to be within range ${floor} - ${ceiling}`
             : `expected ${received} to be within range ${floor} - ${ceiling}`,
       };
     },

     toHaveBeenCalledWithMatch(received, ...expected) {
       const calls = received.mock.calls;
       const pass = calls.some(call =>
         expected.every((exp, i) =>
           typeof exp === 'function' ? exp(call[i]) : call[i] === exp
         )
       );

       return {
         pass,
         message: () =>
           pass
             ? `expected mock not to have been called with matching args`
             : `expected mock to have been called with matching args`,
       };
     },
   });

   // Usage
   test('email validation', () => {
     expect('user@example.com').toBeValidEmail();
     expect('invalid-email').not.toBeValidEmail();
   });

   test('range validation', () => {
     expect(5).toBeWithinRange(1, 10);
   });
   ```

2. **Test Data Generators** (`tests/helpers/factories.js`):

   ```javascript
   /**
    * Test data generation utilities.
    */
   import { faker } from '@faker-js/faker';

   export const generateUser = (overrides = {}) => ({
     id: faker.string.uuid(),
     username: faker.internet.userName(),
     email: faker.internet.email(),
     firstName: faker.person.firstName(),
     lastName: faker.person.lastName(),
     age: faker.number.int({ min: 18, max: 80 }),
     address: {
       street: faker.location.streetAddress(),
       city: faker.location.city(),
       country: faker.location.country(),
       zipCode: faker.location.zipCode(),
     },
     createdAt: faker.date.past(),
     ...overrides,
   });

   export const generateProduct = (overrides = {}) => ({
     id: faker.string.uuid(),
     name: faker.commerce.productName(),
     description: faker.commerce.productDescription(),
     price: parseFloat(faker.commerce.price()),
     category: faker.commerce.department(),
     inStock: faker.datatype.boolean(),
     ...overrides,
   });

   export const generateOrder = (overrides = {}) => ({
     id: faker.string.uuid(),
     userId: faker.string.uuid(),
     items: Array.from({ length: 3 }, () => ({
       productId: faker.string.uuid(),
       quantity: faker.number.int({ min: 1, max: 5 }),
       price: parseFloat(faker.commerce.price()),
     })),
     total: parseFloat(faker.commerce.price({ min: 100, max: 1000 })),
     status: faker.helpers.arrayElement(['pending', 'confirmed', 'shipped', 'delivered']),
     ...overrides,
   });
   ```

3. **Common Test Utilities** (`tests/helpers/testUtils.js`):

   ```javascript
   /**
    * Common test utility functions.
    */

   // Wait for async operations
   export const waitFor = (condition, timeout = 5000, interval = 100) => {
     return new Promise((resolve, reject) => {
       const startTime = Date.now();

       const check = () => {
         if (condition()) {
           resolve();
         } else if (Date.now() - startTime > timeout) {
           reject(new Error('Timeout waiting for condition'));
         } else {
           setTimeout(check, interval);
         }
       };

       check();
     });
   };

   // Flush promises
   export const flushPromises = () => new Promise(resolve => setImmediate(resolve));

   // Create spy with implementation
   export const createSpyWithImpl = (impl) => jest.fn().mockImplementation(impl);

   // Deep clone object
   export const deepClone = (obj) => JSON.parse(JSON.stringify(obj));

   // Compare objects ignoring specific fields
   export const expectObjectMatch = (received, expected, ignoreFields = []) => {
     const filtered = Object.keys(received)
       .filter(key => !ignoreFields.includes(key))
       .reduce((obj, key) => {
         obj[key] = received[key];
         return obj;
       }, {});

     expect(filtered).toEqual(expected);
   };

   // Retry async operation
   export const retry = async (fn, maxAttempts = 3, delay = 1000) => {
     for (let attempt = 1; attempt <= maxAttempts; attempt++) {
       try {
         return await fn();
       } catch (error) {
         if (attempt === maxAttempts) throw error;
         await new Promise(resolve => setTimeout(resolve, delay));
       }
     }
   };
   ```

## Phase 5: Test Discovery & Execution

1. **Configure Test Discovery**

   **package.json scripts**:
   ```json
   {
     "scripts": {
       "test": "jest",
       "test:unit": "jest tests/unit",
       "test:integration": "jest tests/integration",
       "test:e2e": "jest tests/e2e",
       "test:watch": "jest --watch",
       "test:coverage": "jest --coverage",
       "test:verbose": "jest --verbose",
       "test:debug": "node --inspect-brk node_modules/.bin/jest --runInBand"
     }
   }
   ```

2. **Run Tests**

   ```bash
   # Run all tests
   npm test

   # Run specific test file
   npm test -- UserService.test.js

   # Run tests matching pattern
   npm test -- --testNamePattern="should create"

   # Run tests in watch mode
   npm run test:watch

   # Run with coverage
   npm run test:coverage

   # Run in debug mode
   npm run test:debug
   ```

3. **Parallel Test Execution**

   Jest runs tests in parallel by default:
   ```javascript
   // jest.config.js
   module.exports = {
     maxWorkers: '50%',  // Use 50% of available CPUs
     // or
     maxWorkers: 4,      // Use specific number of workers
   };
   ```

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

Replace `{phase_name}` with the specific phase (test_structure, test_cases, mocks_fixtures, performance_testing, maintenance_cicd, or code_coverage).

## Output Format

Please provide a comprehensive test infrastructure design with the following structure:

### Infrastructure Summary

- **Test Framework**: [Jest/Mocha/Vitest with justification]

- **Total Test Files**: [count]

- **Test Organization**: [structure description]

- **Setup Files**: [list of configuration files]

- **Utility Modules**: [list of helper modules]

### Directory Structure
```
[Complete directory tree with all test folders and key files]
```

### Configuration Files Created

- **jest.config.js** or **vitest.config.js**: [Key settings configured]

- **setup.js**: [Global setup description]

- **Custom configurations**: [Any project-specific settings]

### Fixture Infrastructure
**Global Setup**:

- [setup_item]: [description and purpose]

**Factories**:

- [factory_name]: [description and usage]

**Builders**:

- [builder_name]: [description and fluent interface]

### Test Utilities
**Custom Matchers** (`tests/helpers/assertions.js`):

- [matcher_name]: [purpose]

**Data Generators** (`tests/helpers/factories.js`):

- [generator_name]: [purpose]

**Helper Functions** (`tests/helpers/testUtils.js`):

- [helper_name]: [purpose]

### Test Execution Commands
```bash
# Run all tests
npm test

# Run specific test types
npm run test:unit
npm run test:integration
npm run test:e2e

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Debug tests
npm run test:debug
```

### Testing Conventions Established
1. **File Naming**: [convention]
2. **Test Naming**: [convention]
3. **Suite Organization**: [convention]
4. **Mock Usage**: [guidelines]
5. **Test Data**: [where to store, how to organize]

### Best Practices Implemented

- Clear test organization by type

- Reusable fixtures and factories

- Custom matchers for domain-specific assertions

- Comprehensive test utilities

- Parallel execution support

- Coverage measurement integrated

- Watch mode for development

### Next Steps

- [ ] Implement actual test cases using this infrastructure

- [ ] Add project-specific fixtures

- [ ] Configure CI/CD integration

- [ ] Set up code coverage reporting

- [ ] Document testing guidelines for team

- [ ] Create test templates for common scenarios
~~~

## Output Format

The AI assistant should deliver:

1. **Test infrastructure design document** with complete directory structure
2. **Configuration files** (jest.config.js, .mocharc.json, or vitest.config.js)
3. **Setup files** with global configuration
4. **Fixture factories** for common test data
5. **Test utility modules** in helpers/ directory
6. **Custom matchers** for domain-specific assertions
7. **Documentation** of conventions and best practices
8. **Execution commands** for common test scenarios
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
