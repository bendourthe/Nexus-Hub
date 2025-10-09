# JavaScript Testing Review

## Objective
Systematically assess test suite quality, coverage, and effectiveness. Identify testing gaps, unreliable tests, and opportunities to improve confidence in code correctness and regression prevention.

## Output Directory Structure

All review outputs should be saved in organized directories:

```
review/
└── testing_review/
    ├── testing_review_report.md
    ├── testing_review_findings.json
    ├── analysis_scripts/
    └── supporting_data/
```

**Directory Setup**:
- Create `review/` directory in repository root if it doesn't exist
- Create `review/testing_review/` subdirectory for this review phase
- All reports, scripts, and data files go in the phase-specific directory

**Expected Outputs**:
- `testing_review_report.md` - Main findings and recommendations
- `testing_review_findings.json` - Structured data for tooling integration
- `analysis_scripts/` - Any scripts generated during analysis
- `supporting_data/` - Raw data, logs, profiling results, scan outputs

## Review Checklist

### Test Coverage
- [ ] Line coverage measured (target: 80%+)
- [ ] Branch coverage assessed
- [ ] Critical paths fully tested
- [ ] Edge cases and error conditions covered
- [ ] Coverage gaps identified and prioritized

### Test Quality
- [ ] Tests follow AAA pattern (Arrange, Act, Assert)
- [ ] Test names clearly describe what is being tested
- [ ] Tests are independent and isolated
- [ ] Assertions are specific and meaningful
- [ ] Test data is representative and comprehensive

### Test Organization
- [ ] Test structure mirrors source code structure
- [ ] Test files properly organized
- [ ] Fixtures and test utilities well-organized
- [ ] Test configuration managed appropriately
- [ ] Test documentation present

### Test Types Coverage
- [ ] Unit tests present for core logic
- [ ] Integration tests cover component interactions
- [ ] End-to-end tests validate critical user flows
- [ ] Performance tests for critical operations
- [ ] Accessibility tests for UI components

### Test Reliability
- [ ] Flaky tests identified
- [ ] Tests run independently (no order dependency)
- [ ] External dependencies properly mocked
- [ ] Test data properly managed
- [ ] Tests run consistently in different environments

### CI/CD Integration
- [ ] Tests run automatically on commits/PRs
- [ ] Test failures block merges
- [ ] Coverage reports generated
- [ ] Test execution time reasonable
- [ ] Parallel test execution configured

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# JavaScript Testing Review

Please perform a comprehensive testing review of this JavaScript project following this protocol:

## Phase 1: Test Coverage Analysis

1. **Measure Current Coverage**
   ```bash
   # Jest with coverage
   npm test -- --coverage

   # Istanbul/nyc for general coverage
   npm install --save-dev nyc
   npx nyc npm test

   # View HTML coverage report
   npx nyc --reporter=html npm test
   # Open coverage/index.html

   # Coverage with specific thresholds
   npx jest --coverage --coverageThreshold='{"global": {"branches": 80, "functions": 80, "lines": 80, "statements": 80}}'
   ```

2. **Coverage Analysis**
   - Overall coverage percentage
   - Module-by-module coverage breakdown
   - Identify files with <60% coverage
   - Find critical paths with inadequate coverage
   - Document untested code sections

3. **Branch Coverage**
   ```bash
   # Jest branch coverage
   npm test -- --coverage --coveragePathIgnorePatterns=/node_modules/

   # Focus on:
   - Untested conditional branches
   - Exception handling without tests
   - Uncovered error paths
   - Switch/case statement coverage
   ```

## Phase 2: Test Suite Inventory

1. **Test Count and Organization**
   ```bash
   # Count tests
   npm test -- --listTests

   # Jest test stats
   npm test -- --verbose

   # Find all test files
   find . -name "*.test.js" -o -name "*.spec.js" -o -name "*.test.ts" -o -name "*.spec.ts"
   ```

2. **Test Type Distribution**
   - **Unit Tests**: Count and coverage
   - **Integration Tests**: Count and scope
   - **End-to-End Tests**: Count and critical paths covered
   - **Component Tests**: Visual and interaction coverage
   - **Performance Tests**: Presence and scope

3. **Test Structure Assessment**
   ```
   tests/
   ├── unit/              # Pure logic tests
   ├── integration/       # Component interaction tests
   ├── e2e/              # End-to-end user flow tests (Cypress/Playwright)
   ├── __mocks__/        # Manual mocks
   ├── fixtures/         # Test data
   └── helpers/          # Test utilities

   # Or co-located with source
   src/
   ├── components/
   │   ├── Button.jsx
   │   └── Button.test.jsx
   ```

## Phase 3: Test Quality Assessment

1. **Test Pattern Review**
   ```javascript
   // Good test structure (AAA pattern - Jest)
   describe('UserService', () => {
     describe('createUser', () => {
       it('should create a user with valid data', async () => {
         // Arrange
         const userData = {
           username: 'testuser',
           email: 'test@example.com'
         };

         // Act
         const user = await createUser(userData);

         // Assert
         expect(user).toBeDefined();
         expect(user.username).toBe('testuser');
         expect(user.email).toBe('test@example.com');
         expect(user.isActive).toBe(true);
       });
     });
   });

   // Check for anti-patterns:
   // - Multiple unrelated assertions
   // - Testing implementation details
   // - Unclear test purpose
   // - Missing assertions
   // - Overly complex setup
   // - Tests depending on execution order
   ```

2. **Test Naming Review**
   ```javascript
   // Good: Descriptive test names
   describe('User Authentication', () => {
     it('should return JWT token when credentials are valid', () => {});
     it('should throw UnauthorizedError when password is incorrect', () => {});
     it('should throw NotFoundError when user does not exist', () => {});
   });

   // Bad: Vague test names
   describe('User', () => {
     it('works', () => {});  // What works?
     it('test1', () => {});  // What is being tested?
     it('should work correctly', () => {});  // Too vague
   });

   // BDD style (Mocha/Chai)
   describe('Given a valid user', () => {
     context('When authenticating with correct password', () => {
       it('Then should return success', () => {});
     });
   });
   ```

3. **Assertion Quality**
   ```javascript
   // Good: Specific assertions (Jest)
   expect(user.status).toBe('active');
   expect(results).toHaveLength(3);
   expect(apiCall).rejects.toThrow('Invalid email');
   expect(response).toMatchObject({ success: true, data: expect.any(Object) });

   // Good: Specific assertions (Chai)
   expect(user.status).to.equal('active');
   expect(results).to.have.lengthOf(3);
   expect(() => validateEmail('bad')).to.throw('Invalid email');

   // Bad: Weak assertions
   expect(user).toBeTruthy();  // Too vague
   expect(true).toBe(true);  // Meaningless
   expect(results).toBeDefined();  // What about results?
   ```

## Phase 4: Test Independence & Reliability

1. **Test Isolation Check**
   ```bash
   # Jest: Run tests in random order
   npm test -- --randomize

   # Run specific test file
   npm test -- path/to/test.spec.js

   # Run tests in band (no parallel)
   npm test -- --runInBand

   # Mocha: Run in random order
   mocha --sort
   ```

2. **Flaky Test Detection**
   ```bash
   # Jest: Run tests multiple times
   npm test -- --testNamePattern="potentially flaky" --maxWorkers=1 --runInBand

   # Use jest-circus with custom config
   # jest.config.js
   module.exports = {
     testRunner: 'jest-circus/runner',
     maxWorkers: 1,
   };

   # Custom script to detect flakiness
   for i in {1..50}; do npm test || break; done
   ```

3. **Common Flakiness Sources**
   ```javascript
   // 1. Time-dependent tests
   // BAD: Using real dates
   it('should expire after 1 hour', () => {
     const token = createToken();
     // Wait 1 hour... not practical
   });
   // GOOD: Mock time
   jest.useFakeTimers();
   const token = createToken();
   jest.advanceTimersByTime(3600000);
   expect(token.isExpired()).toBe(true);

   // 2. Async timing issues
   // BAD: Arbitrary waits
   await delay(1000); // Hope it's done by then
   // GOOD: Wait for specific condition
   await waitFor(() => expect(element).toBeInTheDocument());

   // 3. Network calls not mocked
   // BAD: Real API calls
   const data = await fetch('https://api.example.com/data');
   // GOOD: Mocked
   jest.mock('axios');
   axios.get.mockResolvedValue({ data: mockData });

   // 4. Test execution order dependency
   // BAD: Shared state
   let user;
   it('creates user', () => { user = createUser(); });
   it('updates user', () => { updateUser(user); }); // Depends on previous test
   // GOOD: Independent setup
   it('updates user', () => {
     const user = createUser();
     updateUser(user);
   });

   // 5. Random data without seeding
   // BAD: Unpredictable
   const randomId = Math.random();
   // GOOD: Seeded or fixed test data
   const testId = 'test-id-123';
   ```

4. **External Dependency Review**
   ```javascript
   // Check for proper mocking

   // Jest: Mock modules
   jest.mock('./api/userService');
   import { getUser } from './api/userService';
   getUser.mockResolvedValue({ id: 1, name: 'Test' });

   // Jest: Mock fetch
   global.fetch = jest.fn(() =>
     Promise.resolve({
       json: () => Promise.resolve({ data: 'mocked' }),
     })
   );

   // MSW (Mock Service Worker) for realistic API mocking
   import { rest } from 'msw';
   import { setupServer } from 'msw/node';

   const server = setupServer(
     rest.get('/api/user', (req, res, ctx) => {
       return res(ctx.json({ id: 1, name: 'Test User' }));
     })
   );

   beforeAll(() => server.listen());
   afterEach(() => server.resetHandlers());
   afterAll(() => server.close());
   ```

## Phase 5: Test Coverage Gaps Analysis

1. **Critical Path Identification**
   - Authentication and authorization flows
   - Data validation and processing
   - Business logic and calculations
   - Error handling and recovery
   - API endpoints/routes
   - Database operations
   - State management (Redux/Vuex/etc.)

2. **Untested Code Categories**
   ```bash
   # View uncovered lines
   npm test -- --coverage --coverageReporters=text-lcov

   # Focus on:
   - Critical business logic without tests
   - Error handling paths not covered
   - Edge cases not tested
   - New code without tests
   - Complex functions without tests
   ```

3. **Missing Test Types**
   - [ ] Happy path scenarios
   - [ ] Error conditions and exceptions
   - [ ] Boundary values (empty arrays, null, undefined, max values)
   - [ ] Invalid input handling
   - [ ] Race conditions and concurrent access
   - [ ] Performance under load

## Phase 6: Framework-Specific Testing

### React Component Testing

```javascript
// React Testing Library (Recommended)
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('LoginForm', () => {
  it('should submit form with valid credentials', async () => {
    const onSubmit = jest.fn();
    render(<LoginForm onSubmit={onSubmit} />);

    // Query elements
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /submit/i });

    // Interact
    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.type(passwordInput, 'password123');
    await userEvent.click(submitButton);

    // Assert
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      });
    });
  });

  it('should display error message on invalid submit', async () => {
    render(<LoginForm onSubmit={jest.fn()} />);

    const submitButton = screen.getByRole('button', { name: /submit/i });
    await userEvent.click(submitButton);

    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
  });
});

// Snapshot testing (use sparingly)
it('should match snapshot', () => {
  const { container } = render(<Button>Click me</Button>);
  expect(container.firstChild).toMatchSnapshot();
});
```

### Vue Component Testing

```javascript
// Vue Test Utils (Vue 3)
import { mount } from '@vue/test-utils';
import { describe, it, expect } from 'vitest';
import UserProfile from './UserProfile.vue';

describe('UserProfile', () => {
  it('should render user information', () => {
    const wrapper = mount(UserProfile, {
      props: {
        user: { name: 'John Doe', email: 'john@example.com' }
      }
    });

    expect(wrapper.text()).toContain('John Doe');
    expect(wrapper.text()).toContain('john@example.com');
  });

  it('should emit update event when edit button is clicked', async () => {
    const wrapper = mount(UserProfile, {
      props: {
        user: { name: 'John Doe', email: 'john@example.com' }
      }
    });

    await wrapper.find('button.edit').trigger('click');

    expect(wrapper.emitted()).toHaveProperty('update');
    expect(wrapper.emitted('update')).toHaveLength(1);
  });
});
```

### Angular Component Testing

```typescript
// Angular TestBed
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { UserListComponent } from './user-list.component';
import { UserService } from './user.service';
import { of } from 'rxjs';

describe('UserListComponent', () => {
  let component: UserListComponent;
  let fixture: ComponentFixture<UserListComponent>;
  let userService: jasmine.SpyObj<UserService>;

  beforeEach(async () => {
    const userServiceSpy = jasmine.createSpyObj('UserService', ['getUsers']);

    await TestBed.configureTestingModule({
      declarations: [ UserListComponent ],
      providers: [
        { provide: UserService, useValue: userServiceSpy }
      ]
    }).compileComponents();

    userService = TestBed.inject(UserService) as jasmine.SpyObj<UserService>;
    fixture = TestBed.createComponent(UserListComponent);
    component = fixture.componentInstance;
  });

  it('should display list of users', () => {
    const mockUsers = [
      { id: 1, name: 'User 1' },
      { id: 2, name: 'User 2' }
    ];
    userService.getUsers.and.returnValue(of(mockUsers));

    fixture.detectChanges();

    const compiled = fixture.nativeElement;
    expect(compiled.querySelectorAll('.user-item').length).toBe(2);
  });
});
```

## Phase 7: End-to-End Testing

### Cypress

```javascript
// cypress/e2e/login.cy.js
describe('User Login Flow', () => {
  beforeEach(() => {
    cy.visit('/login');
  });

  it('should successfully log in with valid credentials', () => {
    cy.get('input[name="email"]').type('user@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();

    cy.url().should('include', '/dashboard');
    cy.contains('Welcome back').should('be.visible');
  });

  it('should show error with invalid credentials', () => {
    cy.get('input[name="email"]').type('user@example.com');
    cy.get('input[name="password"]').type('wrongpassword');
    cy.get('button[type="submit"]').click();

    cy.contains('Invalid credentials').should('be.visible');
    cy.url().should('include', '/login');
  });

  it('should handle network errors gracefully', () => {
    cy.intercept('POST', '/api/auth/login', { statusCode: 500 }).as('loginRequest');

    cy.get('input[name="email"]').type('user@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();

    cy.wait('@loginRequest');
    cy.contains('Something went wrong').should('be.visible');
  });
});
```

### Playwright

```javascript
// tests/login.spec.js
import { test, expect } from '@playwright/test';

test.describe('Login functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should log in successfully with valid credentials', async ({ page }) => {
    await page.fill('input[name="email"]', 'user@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('text=Welcome back')).toBeVisible();
  });

  test('should show validation error for empty fields', async ({ page }) => {
    await page.click('button[type="submit"]');

    await expect(page.locator('text=Email is required')).toBeVisible();
  });

  test('should work on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    await page.fill('input[name="email"]', 'user@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/.*dashboard/);
  });
});
```

## Phase 8: Test Maintainability

1. **Test Code Quality**
   ```bash
   # Run linters on test code
   npm run lint tests/

   # ESLint for tests
   eslint '**/*.test.js' '**/*.spec.js'
   ```

2. **Test Helpers & Utilities**
   ```javascript
   // Good: Reusable test utilities
   // tests/helpers/testUtils.js
   export const createMockUser = (overrides = {}) => ({
     id: 1,
     username: 'testuser',
     email: 'test@example.com',
     isActive: true,
     ...overrides
   });

   export const renderWithProviders = (
     ui,
     { initialState = {}, ...renderOptions } = {}
   ) => {
     const store = createStore(initialState);
     const Wrapper = ({ children }) => (
       <Provider store={store}>{children}</Provider>
     );
     return render(ui, { wrapper: Wrapper, ...renderOptions });
   };

   // Usage
   import { createMockUser, renderWithProviders } from './helpers/testUtils';

   it('should display user profile', () => {
     const user = createMockUser({ username: 'john' });
     renderWithProviders(<UserProfile user={user} />);
     expect(screen.getByText('john')).toBeInTheDocument();
   });
   ```

3. **Test Data Management**
   ```javascript
   // Fixtures for consistent test data
   // tests/fixtures/users.js
   export const validUser = {
     id: 1,
     username: 'testuser',
     email: 'test@example.com'
   };

   export const users = [
     { id: 1, username: 'user1', email: 'user1@example.com' },
     { id: 2, username: 'user2', email: 'user2@example.com' },
   ];

   // Factory functions (using faker)
   import { faker } from '@faker-js/faker';

   export const userFactory = (overrides = {}) => ({
     id: faker.datatype.uuid(),
     username: faker.internet.userName(),
     email: faker.internet.email(),
     createdAt: faker.date.past(),
     ...overrides
   });
   ```

## Phase 9: CI/CD Integration Review

1. **Test Automation Assessment**
   ```yaml
   # GitHub Actions example
   name: Tests
   on: [push, pull_request]

   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - uses: actions/setup-node@v3
           with:
             node-version: '18'
         - run: npm ci
         - run: npm test -- --coverage
         - uses: codecov/codecov-action@v3
           with:
             files: ./coverage/coverage-final.json
   ```

2. **Quality Gates**
   ```javascript
   // jest.config.js
   module.exports = {
     coverageThreshold: {
       global: {
         branches: 80,
         functions: 80,
         lines: 80,
         statements: 80
       }
     }
   };
   ```

3. **Test Execution Performance**
   ```bash
   # Jest: Show slowest tests
   npm test -- --verbose --maxWorkers=1

   # Identify slow tests (>1s)
   npm test -- --testTimeout=1000

   # Parallel execution
   npm test -- --maxWorkers=4
   ```

## Output Format

Please provide a comprehensive testing report with the following structure:

### Executive Summary
- **Overall Test Health**: [Excellent/Good/Fair/Poor]
- **Test Coverage**: [percentage]
- **Critical Gaps**: [count and brief description]
- **Test Quality**: [High/Medium/Low]
- **Reliability**: [Stable/Some Flakiness/Unreliable]

### Coverage Metrics
- **Line Coverage**: [%]
- **Branch Coverage**: [%]
- **Function Coverage**: [%]
- **Statement Coverage**: [%]

**Coverage by Module**:
| Module | Line Coverage | Branch Coverage | Untested Lines | Priority |
|--------|---------------|-----------------|----------------|----------|
| [name] | [%] | [%] | [count] | [High/Med/Low] |

### Test Suite Inventory
- **Total Tests**: [count]
- **Unit Tests**: [count] ([%])
- **Integration Tests**: [count] ([%])
- **Component Tests**: [count] ([%])
- **End-to-End Tests**: [count] ([%])
- **Visual Regression Tests**: [count]

### Test Framework Analysis
- **Primary Framework**: [Jest/Mocha/Vitest/etc.]
- **Component Testing**: [React Testing Library/Vue Test Utils/etc.]
- **E2E Framework**: [Cypress/Playwright/Puppeteer]
- **Coverage Tool**: [Istanbul/nyc/c8]

### Critical Coverage Gaps (Priority 1)
| Module/Function | Current Coverage | Risk Level | Impact | Recommendation |
|-----------------|------------------|------------|--------|----------------|
| [name] | [%] | [High/Med/Low] | [description] | [test types needed] |

### Test Quality Issues
**Test Smell Detections**:
| Issue | Location | Description | Fix |
|-------|----------|-------------|-----|
| [smell type] | [file:line] | [details] | [recommendation] |

**Common Issues**:
- [ ] Tests with unclear names: [count]
- [ ] Tests with weak assertions: [count]
- [ ] Tests with complex setup: [count]
- [ ] Tests testing implementation details: [count]
- [ ] Snapshot tests without meaning: [count]

### Test Reliability Assessment
**Flaky Tests Detected**: [count]
| Test Name | Failure Rate | Root Cause | Fix |
|-----------|--------------|------------|-----|
| [test] | [%] | [reason] | [solution] |

**Test Independence Issues**:
- [ ] Order-dependent tests: [list]
- [ ] Shared state pollution: [list]
- [ ] External dependencies not mocked: [list]
- [ ] Tests depending on system time: [list]

### Test Execution Performance
- **Total Execution Time**: [seconds]
- **Slowest Tests** (>1s):
  | Test | Duration | Type | Optimization |
  |------|----------|------|--------------|
  | [name] | [seconds] | [unit/integration/e2e] | [suggestion] |

### E2E Test Coverage
- **Critical User Flows**: [X/Y covered]
- **Browser Coverage**: [Chrome/Firefox/Safari/Edge]
- **Mobile Testing**: [Yes/No]
- **Accessibility Testing**: [Yes/No]

**Missing E2E Tests**:
- [ ] [Critical flow description]
- [ ] [Critical flow description]

### Component Test Coverage (React/Vue/Angular)
- **Components Tested**: [X/Y]
- **Props/Events Coverage**: [Comprehensive/Partial/Missing]
- **Interaction Testing**: [Good/Needs improvement]
- **Accessibility Testing**: [Present/Missing]

### Missing Test Types
- [ ] **Edge Cases**: [specific gaps]
- [ ] **Error Conditions**: [uncovered exceptions]
- [ ] **Boundary Values**: [missing boundary tests]
- [ ] **Integration Points**: [untested interactions]
- [ ] **Performance Tests**: [operations needing perf tests]
- [ ] **Accessibility Tests**: [a11y validations needed]

### CI/CD Integration
- **Automated Test Execution**: [Yes/No/Partial]
- **Coverage Reporting**: [Yes/No]
- **Quality Gates**: [Enforced/Not Enforced]
- **Test Parallelization**: [Yes/No]
- **E2E Tests in CI**: [Yes/No]

**Issues**:
- [List of CI/CD testing gaps or issues]

### Recommendations

**Immediate Actions** (Priority 1 - this week):
1. **[Action]**
   - **Rationale**: [why important]
   - **Implementation**: [how to do it]
   - **Effort**: [hours/days]

**Short-term Goals** (Priority 2 - this month):
[List of medium-priority testing improvements]

**Long-term Initiatives** (Priority 3 - this quarter):
[List of strategic testing enhancements]

### Testing Best Practices Implementation

```javascript
// Recommended test patterns

// 1. Factory functions for test data
const createTestUser = (overrides = {}) => ({
  id: 'test-id',
  username: 'testuser',
  email: 'test@example.com',
  isActive: true,
  ...overrides
});

// 2. Custom render functions with providers (React)
const renderWithRouter = (ui, { route = '/', ...options } = {}) => {
  window.history.pushState({}, 'Test', route);
  return render(ui, { wrapper: BrowserRouter, ...options });
};

// 3. Reusable test setup
const setupTest = () => {
  const user = createTestUser();
  const store = createMockStore({ user });
  return { user, store };
};

// 4. Async utilities
const waitForElement = (selector, timeout = 1000) => {
  return screen.findByTestId(selector, {}, { timeout });
};
```

### Test Coverage Improvement Plan
**Target: [X]% coverage (from current [Y]%)**

**Phase 1** (Week 1-2):
- Add tests for [critical modules]
- Expected coverage gain: +[X]%

**Phase 2** (Week 3-4):
- Add integration tests for [components]
- Expected coverage gain: +[X]%

**Phase 3** (Month 2):
- Add E2E tests for critical flows
- Add edge case and error condition tests
- Expected coverage gain: +[X]%

### Quality Gates Recommendation
```javascript
// jest.config.js
module.exports = {
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    },
    './src/critical/**/*.js': {
      branches: 90,
      functions: 95,
      lines: 95,
      statements: 95
    }
  },
  testTimeout: 5000,
  maxWorkers: '50%',
};

// package.json scripts
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --ci --coverage --maxWorkers=2"
  }
}
```

### Next Steps
- [ ] Address critical coverage gaps (Priority 1 items)
- [ ] Fix or quarantine flaky tests
- [ ] Implement test factories and utilities
- [ ] Set up coverage monitoring in CI/CD
- [ ] Add E2E tests for critical flows
- [ ] Establish team testing guidelines
- [ ] Configure pre-commit hooks for test requirements
- [ ] Add accessibility testing

## Notes
- Focus on testing critical business logic and user flows first
- Aim for meaningful tests, not just coverage percentage
- Balance unit, integration, and e2e test distribution (70/20/10 is common)
- Keep tests fast and reliable (unit <100ms, integration <1s)
- Treat test code with same quality standards as production code
- Use Testing Library principles: test behavior, not implementation
~~~
