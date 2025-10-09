# JavaScript Mocks & Fixtures

## Objective
Design and implement effective mocking strategies and fixture management using Jest and Sinon.js to isolate components, manage test data efficiently, control external dependencies, and create maintainable, fast-running tests.

## Output Directory Structure

All test outputs should be saved in organized directories:

```
tests/
└── mocks_fixtures/
    ├── test_files/
    ├── test_data/
    ├── test_reports/
    └── test_configs/
```

**Directory Setup**:
- Create `tests/` directory in repository root if it doesn't exist
- Create `tests/mocks_fixtures/` subdirectory for this testing phase
- All test files, data, reports, and configurations go in the phase-specific directory

**Expected Outputs**:
- `test_files/` - Actual test implementation files
- `test_data/` - Test fixtures, mock data, sample inputs
- `test_reports/` - Test execution reports, coverage reports, performance results
- `test_configs/` - Framework configurations, test runner settings

## Implementation Checklist

### Fixture Setup
- [ ] Setup/teardown hooks configured appropriately (beforeEach/afterEach/beforeAll/afterAll)
- [ ] Test data builders created for flexible data generation
- [ ] Fixture factories implemented with realistic data
- [ ] Cleanup and reset logic automated
- [ ] Fixtures documented with clear purposes

### Mocking Strategy
- [ ] External dependencies identified for mocking
- [ ] Mocking approach chosen (mock vs stub vs spy)
- [ ] Mock objects configured with Jest or Sinon
- [ ] Assertion methods used appropriately
- [ ] Over-mocking avoided

### Test Data Management
- [ ] Test data factories implemented
- [ ] Realistic test data patterns established
- [ ] Data builders for complex objects created
- [ ] Test data isolated per test
- [ ] Data cleanup automated

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# JavaScript Mocks & Fixtures Implementation

Please implement comprehensive mocking and fixture strategies for this JavaScript project following this protocol:

## Phase 1: Fixture Architecture Design

### Understanding Jest Setup/Teardown

Jest provides lifecycle hooks for fixture management:

**Basic Setup/Teardown**:
```javascript
describe('User Tests', () => {
  let database;
  let testUser;

  beforeAll(() => {
    // Runs once before all tests in this suite
    database = new Database('test');
  });

  beforeEach(() => {
    // Runs before each test
    testUser = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com'
    };
  });

  afterEach(() => {
    // Runs after each test - cleanup
    database.clearTestData();
  });

  afterAll(() => {
    // Runs once after all tests
    database.disconnect();
  });

  test('should create user', () => {
    const result = database.createUser(testUser);
    expect(result.username).toBe('testuser');
  });
});
```

### Fixture Scopes

Choose appropriate scope for efficiency and isolation:

**1. Suite-Level Fixtures (beforeAll/afterAll)**:
```javascript
describe('Database Operations', () => {
  let connection;

  beforeAll(async () => {
    // Expensive setup - run once
    connection = await Database.connect('test_db');
    await connection.migrate();
  });

  afterAll(async () => {
    // Cleanup after all tests
    await connection.dropTables();
    await connection.close();
  });

  test('should insert user', async () => {
    const user = await connection.insert('users', { name: 'alice' });
    expect(user.name).toBe('alice');
  });

  test('should query users', async () => {
    const users = await connection.query('SELECT * FROM users');
    expect(users.length).toBeGreaterThan(0);
  });
});
```

**2. Test-Level Fixtures (beforeEach/afterEach)**:
```javascript
describe('User Service', () => {
  let userService;
  let mockDatabase;

  beforeEach(() => {
    // Fresh instance for each test
    mockDatabase = {
      users: [],
      insert: jest.fn(),
      query: jest.fn()
    };
    userService = new UserService(mockDatabase);
  });

  afterEach(() => {
    // Reset after each test
    jest.clearAllMocks();
  });

  test('should create user', () => {
    mockDatabase.insert.mockResolvedValue({ id: 1, name: 'alice' });
    const result = userService.createUser('alice');
    expect(mockDatabase.insert).toHaveBeenCalledWith('users', { name: 'alice' });
  });
});
```

**3. Nested Describe Blocks**:
```javascript
describe('User API', () => {
  let app;

  beforeAll(() => {
    app = createTestApp();
  });

  describe('GET /users', () => {
    let testUsers;

    beforeEach(() => {
      testUsers = [
        { id: 1, name: 'alice' },
        { id: 2, name: 'bob' }
      ];
      app.database.seed(testUsers);
    });

    test('should return all users', async () => {
      const response = await request(app).get('/users');
      expect(response.body).toHaveLength(2);
    });
  });

  describe('POST /users', () => {
    test('should create user', async () => {
      const response = await request(app)
        .post('/users')
        .send({ name: 'charlie' });
      expect(response.status).toBe(201);
    });
  });
});
```

### Fixture Factories

Create factories for flexible test data generation:

```javascript
// tests/factories/userFactory.js
class UserFactory {
  constructor() {
    this.idCounter = 0;
    this.createdUsers = [];
  }

  create(overrides = {}) {
    this.idCounter++;
    const user = {
      id: this.idCounter,
      username: `user_${this.idCounter}`,
      email: `user${this.idCounter}@test.com`,
      age: 25,
      active: true,
      createdAt: new Date(),
      ...overrides
    };
    this.createdUsers.push(user);
    return user;
  }

  createBatch(count, overrides = {}) {
    return Array.from({ length: count }, () => this.create(overrides));
  }

  reset() {
    this.idCounter = 0;
    this.createdUsers = [];
  }
}

// Usage in tests
describe('User Operations', () => {
  let userFactory;

  beforeEach(() => {
    userFactory = new UserFactory();
  });

  test('should create users with defaults', () => {
    const user1 = userFactory.create();
    const user2 = userFactory.create();

    expect(user1.username).toBe('user_1');
    expect(user2.username).toBe('user_2');
  });

  test('should create users with custom data', () => {
    const user = userFactory.create({
      username: 'alice',
      email: 'alice@example.com',
      age: 30
    });

    expect(user.username).toBe('alice');
    expect(user.age).toBe(30);
  });

  test('should create batch of users', () => {
    const users = userFactory.createBatch(5, { active: false });

    expect(users).toHaveLength(5);
    expect(users.every(u => !u.active)).toBe(true);
  });
});
```

### Builder Pattern for Complex Objects

```javascript
// tests/builders/orderBuilder.js
class OrderBuilder {
  constructor() {
    this.order = {
      id: null,
      userId: null,
      items: [],
      status: 'pending',
      total: 0,
      shippingAddress: null
    };
  }

  withId(id) {
    this.order.id = id;
    return this;
  }

  forUser(userId) {
    this.order.userId = userId;
    return this;
  }

  addItem(productId, quantity, price) {
    this.order.items.push({ productId, quantity, price });
    this.order.total += quantity * price;
    return this;
  }

  withStatus(status) {
    this.order.status = status;
    return this;
  }

  withShippingAddress(address) {
    this.order.shippingAddress = address;
    return this;
  }

  build() {
    return { ...this.order };
  }
}

// Usage
test('should process order', () => {
  const order = new OrderBuilder()
    .withId(1)
    .forUser(100)
    .addItem(1, 2, 10.00)
    .addItem(2, 1, 15.00)
    .withStatus('confirmed')
    .withShippingAddress({ street: '123 Main St', city: 'Boston' })
    .build();

  expect(order.total).toBe(35.00);
  expect(order.items).toHaveLength(2);
});
```

## Phase 2: Mocking Strategies with Jest

### Understanding Jest Mocks

Jest provides powerful mocking capabilities built-in:

**Mock Functions**:
```javascript
// Create a mock function
const mockCallback = jest.fn();

// Configure return value
mockCallback.mockReturnValue(42);
expect(mockCallback()).toBe(42);

// Configure different return values per call
mockCallback.mockReturnValueOnce(1)
             .mockReturnValueOnce(2)
             .mockReturnValue(3);

expect(mockCallback()).toBe(1);
expect(mockCallback()).toBe(2);
expect(mockCallback()).toBe(3);

// Mock async functions
const mockAsync = jest.fn().mockResolvedValue({ id: 1, name: 'alice' });
const result = await mockAsync();
expect(result.name).toBe('alice');

// Mock rejection
const mockError = jest.fn().mockRejectedValue(new Error('Failed'));
await expect(mockError()).rejects.toThrow('Failed');
```

### When to Mock vs Use Real Objects

**Use Mocks For**:
- External APIs and services
- Database operations in unit tests
- File system operations
- Network requests
- Date/time operations
- Random number generation
- Third-party libraries

**Use Real Objects For**:
- Pure functions
- Simple utility classes
- Integration tests
- Critical business logic requiring confidence

```javascript
// GOOD - Mock external API
test('should fetch user data', async () => {
  const mockFetch = jest.fn().mockResolvedValue({
    json: () => Promise.resolve({ id: 1, name: 'alice' })
  });
  global.fetch = mockFetch;

  const result = await fetchUserFromApi(1);
  expect(result.name).toBe('alice');
});

// GOOD - Use real object for pure function
test('should calculate total', () => {
  const items = [10, 20, 30];
  expect(calculateTotal(items)).toBe(60);
});

// BAD - Over-mocking simple logic
test('should calculate total', () => {
  const mockSum = jest.fn().mockReturnValue(60);
  Math.sum = mockSum;  // Unnecessary complexity
  expect(calculateTotal([10, 20, 30])).toBe(60);
});
```

### Mocking Modules

**Auto Mocking**:
```javascript
// Auto-mock entire module
jest.mock('../src/database');

const Database = require('../src/database');

test('should use mocked database', () => {
  // All methods are automatically mocked
  Database.connect.mockResolvedValue({ status: 'connected' });

  const db = await Database.connect();
  expect(db.status).toBe('connected');
});
```

**Manual Mocking**:
```javascript
// Manual mock implementation
jest.mock('../src/api', () => ({
  fetchUser: jest.fn().mockResolvedValue({ id: 1, name: 'alice' }),
  fetchPosts: jest.fn().mockResolvedValue([{ id: 1, title: 'Post 1' }])
}));

const api = require('../src/api');

test('should fetch user', async () => {
  const user = await api.fetchUser(1);
  expect(user.name).toBe('alice');
  expect(api.fetchUser).toHaveBeenCalledWith(1);
});
```

**Partial Mocking**:
```javascript
// Mock only specific functions
jest.mock('../src/utils', () => ({
  ...jest.requireActual('../src/utils'),
  getCurrentTime: jest.fn().mockReturnValue('2024-01-15T12:00:00')
}));

const utils = require('../src/utils');

test('should use real and mocked functions', () => {
  expect(utils.formatString('test')).toBe('TEST');  // Real function
  expect(utils.getCurrentTime()).toBe('2024-01-15T12:00:00');  // Mocked
});
```

### Mocking Classes

```javascript
// src/userService.js
class UserService {
  constructor(database) {
    this.database = database;
  }

  async getUser(id) {
    return this.database.query('users', { id });
  }

  async createUser(userData) {
    return this.database.insert('users', userData);
  }
}

// Mock the class
jest.mock('../src/userService');

const UserService = require('../src/userService');

test('should mock class methods', async () => {
  const mockGetUser = jest.fn().mockResolvedValue({ id: 1, name: 'alice' });
  UserService.mockImplementation(() => ({
    getUser: mockGetUser,
    createUser: jest.fn()
  }));

  const service = new UserService();
  const user = await service.getUser(1);

  expect(user.name).toBe('alice');
  expect(mockGetUser).toHaveBeenCalledWith(1);
});
```

### Jest Spy Functions

Spy on existing implementations:

```javascript
const utils = require('../src/utils');

test('should spy on real function', () => {
  const spy = jest.spyOn(utils, 'formatString');

  const result = utils.formatString('test');

  expect(result).toBe('TEST');  // Real implementation runs
  expect(spy).toHaveBeenCalledWith('test');

  spy.mockRestore();  // Restore original
});

test('should spy and mock implementation', () => {
  const spy = jest.spyOn(utils, 'formatString').mockReturnValue('MOCKED');

  const result = utils.formatString('test');

  expect(result).toBe('MOCKED');  // Mocked value
  expect(spy).toHaveBeenCalledWith('test');

  spy.mockRestore();
});
```

### Mock Assertions

```javascript
const mockFn = jest.fn();

// Call the mock
mockFn('arg1', 'arg2');
mockFn('arg3');

// Assertions
expect(mockFn).toHaveBeenCalled();
expect(mockFn).toHaveBeenCalledTimes(2);
expect(mockFn).toHaveBeenCalledWith('arg1', 'arg2');
expect(mockFn).toHaveBeenLastCalledWith('arg3');
expect(mockFn).toHaveBeenNthCalledWith(1, 'arg1', 'arg2');

// Check call history
expect(mockFn.mock.calls).toEqual([
  ['arg1', 'arg2'],
  ['arg3']
]);

// Check results
mockFn.mockReturnValue('result');
mockFn();
expect(mockFn.mock.results[2].value).toBe('result');
```

## Phase 3: Mocking with Sinon.js

### Understanding Sinon

Sinon provides advanced mocking capabilities:

```bash
npm install --save-dev sinon
```

**Sinon Stubs**:
```javascript
const sinon = require('sinon');
const api = require('../src/api');

describe('User Service with Sinon', () => {
  let fetchStub;

  beforeEach(() => {
    fetchStub = sinon.stub(api, 'fetchUser');
  });

  afterEach(() => {
    fetchStub.restore();
  });

  test('should stub API call', async () => {
    fetchStub.resolves({ id: 1, name: 'alice' });

    const result = await api.fetchUser(1);

    expect(result.name).toBe('alice');
    expect(fetchStub.calledOnce).toBe(true);
    expect(fetchStub.calledWith(1)).toBe(true);
  });

  test('should stub multiple calls differently', async () => {
    fetchStub.onFirstCall().resolves({ name: 'alice' })
             .onSecondCall().resolves({ name: 'bob' });

    const user1 = await api.fetchUser(1);
    const user2 = await api.fetchUser(2);

    expect(user1.name).toBe('alice');
    expect(user2.name).toBe('bob');
  });
});
```

**Sinon Spies**:
```javascript
test('should spy on callback', () => {
  const callback = sinon.spy();

  processItems([1, 2, 3], callback);

  expect(callback.callCount).toBe(3);
  expect(callback.firstCall.args[0]).toBe(1);
  expect(callback.secondCall.args[0]).toBe(2);
  expect(callback.thirdCall.args[0]).toBe(3);
});
```

**Sinon Mocks**:
```javascript
test('should verify expectations', () => {
  const database = {
    insert: () => {},
    query: () => {}
  };

  const mock = sinon.mock(database);

  // Set expectations
  mock.expects('insert').once().withArgs('users', { name: 'alice' });
  mock.expects('query').never();

  // Run code
  database.insert('users', { name: 'alice' });

  // Verify all expectations met
  mock.verify();
  mock.restore();
});
```

### Sinon Fake Timers

```javascript
describe('Timer Tests', () => {
  let clock;

  beforeEach(() => {
    clock = sinon.useFakeTimers(new Date('2024-01-15T12:00:00'));
  });

  afterEach(() => {
    clock.restore();
  });

  test('should control time', () => {
    const callback = sinon.spy();

    setTimeout(callback, 1000);

    expect(callback.called).toBe(false);

    clock.tick(1000);

    expect(callback.called).toBe(true);
  });

  test('should advance date', () => {
    expect(new Date().toISOString()).toBe('2024-01-15T12:00:00.000Z');

    clock.tick(3600000);  // 1 hour

    expect(new Date().toISOString()).toBe('2024-01-15T13:00:00.000Z');
  });
});
```

### Sinon Fake Server

Mock HTTP requests:

```javascript
const sinon = require('sinon');

describe('HTTP Tests', () => {
  let server;

  beforeEach(() => {
    server = sinon.fakeServer.create();
  });

  afterEach(() => {
    server.restore();
  });

  test('should mock HTTP request', (done) => {
    server.respondWith('GET', '/api/users/1', [
      200,
      { 'Content-Type': 'application/json' },
      JSON.stringify({ id: 1, name: 'alice' })
    ]);

    fetch('/api/users/1')
      .then(res => res.json())
      .then(data => {
        expect(data.name).toBe('alice');
        done();
      });

    server.respond();
  });
});
```

## Phase 4: Mocking External Dependencies

### Mocking Axios

```javascript
jest.mock('axios');
const axios = require('axios');

test('should mock axios request', async () => {
  axios.get.mockResolvedValue({
    data: { id: 1, name: 'alice' }
  });

  const result = await fetchUser(1);

  expect(result.name).toBe('alice');
  expect(axios.get).toHaveBeenCalledWith('/api/users/1');
});
```

### Mocking Fetch API

```javascript
global.fetch = jest.fn();

test('should mock fetch', async () => {
  fetch.mockResolvedValue({
    ok: true,
    json: async () => ({ id: 1, name: 'alice' })
  });

  const result = await fetchUser(1);

  expect(result.name).toBe('alice');
  expect(fetch).toHaveBeenCalledWith('/api/users/1');
});
```

### Mocking File System

```javascript
jest.mock('fs');
const fs = require('fs');

test('should mock file read', () => {
  fs.readFileSync.mockReturnValue('file content');

  const content = readConfigFile('config.json');

  expect(content).toBe('file content');
  expect(fs.readFileSync).toHaveBeenCalledWith('config.json', 'utf8');
});
```

### Mocking Date and Time

```javascript
beforeEach(() => {
  jest.useFakeTimers('modern');
  jest.setSystemTime(new Date('2024-01-15T12:00:00'));
});

afterEach(() => {
  jest.useRealTimers();
});

test('should use fake time', () => {
  const timestamp = new Date().toISOString();
  expect(timestamp).toBe('2024-01-15T12:00:00.000Z');
});
```

## Output Format

Please provide a comprehensive mocks and fixtures implementation with the following structure:

### Fixture Architecture
**Suite-Level Setup** (beforeAll/afterAll):
- [fixture_name]: [purpose, setup, teardown]

**Test-Level Setup** (beforeEach/afterEach):
- [fixture_name]: [purpose, when to use]

**Fixture Factories**:
- [factory_name]: [creates what, customization options]

### Mocking Strategy
**External Dependencies to Mock**:
| Dependency | Mocking Approach | Tool (Jest/Sinon) | Reason |
|------------|------------------|-------------------|--------|
| [API/Service] | [mock/stub/spy] | [Jest/Sinon] | [justification] |

**Mock Configurations**:
```javascript
// Example mock setup
const mockApiClient = jest.fn();
mockApiClient.get.mockResolvedValue({ status: 'ok' });
```

### Test Data Factories
**Factory Classes**:
- UserFactory: [customization options]
- OrderFactory: [customization options]

**Builder Classes**:
- [builder_name]: [purpose, fluent interface methods]

### Usage Examples
```javascript
// Example test using fixtures and mocks
describe('User Registration', () => {
  let userFactory;
  let mockEmailService;

  beforeEach(() => {
    userFactory = new UserFactory();
    mockEmailService = jest.fn();
  });

  test('should register user', async () => {
    mockEmailService.send.mockResolvedValue(true);

    const userData = userFactory.create({ username: 'alice' });
    const result = await registerUser(userData);

    expect(result.success).toBe(true);
    expect(mockEmailService.send).toHaveBeenCalledTimes(1);
  });
});
```

### Best Practices Implemented
- [ ] Setup/teardown use appropriate hooks
- [ ] Mocks are used for external dependencies only
- [ ] Test data factories provide flexible data creation
- [ ] Mock cleanup ensures isolation between tests
- [ ] Assertions verify behavior, not implementation
- [ ] Fake timers used for time-dependent tests

### Common Pitfalls Avoided
- Over-mocking simple functions
- Not restoring mocks after tests
- Mock leaking between tests
- Complex fixture dependencies
- Testing mock behavior instead of real code

### Next Steps
- [ ] Implement remaining fixtures for integration tests
- [ ] Add factories for all domain models
- [ ] Document fixture usage for team
- [ ] Set up shared mock configurations
- [ ] Review mock coverage and necessity
~~~

## Output Format

The AI assistant should deliver:

1. **Comprehensive fixture setup** using Jest hooks
2. **Mock configurations** for external dependencies
3. **Test data factories** for domain objects
4. **Builder patterns** for complex test data
5. **Usage documentation** with examples
6. **Best practices guide** for Jest and Sinon
7. **Fixture and mock catalog** for easy reference
