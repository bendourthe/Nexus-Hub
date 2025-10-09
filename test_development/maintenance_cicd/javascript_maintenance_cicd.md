# JavaScript Test Maintenance & CI/CD Integration

## Objective
Establish comprehensive test automation infrastructure, integrate tests into CI/CD pipelines, implement quality gates, manage test maintenance, handle flaky tests, optimize test execution, and ensure sustainable testing practices for JavaScript/TypeScript projects.

## Implementation Checklist

### CI/CD Configuration
- [ ] GitHub Actions/GitLab CI pipeline configured
- [ ] Test stages defined (unit, integration, e2e)
- [ ] Parallel execution enabled
- [ ] Test result reporting set up
- [ ] Artifact storage configured

### Quality Gates
- [ ] Code coverage threshold enforced (80%+)
- [ ] Test pass rate requirement set (100%)
- [ ] Performance regression checks enabled
- [ ] Security scanning integrated
- [ ] Deployment gates configured

### Test Maintenance
- [ ] Flaky test detection implemented
- [ ] Test execution time monitoring enabled
- [ ] Obsolete test cleanup process established
- [ ] Test documentation maintained
- [ ] Test data management automated

### Pre-commit Hooks
- [ ] Code formatting checks (Prettier)
- [ ] Linting (ESLint)
- [ ] Type checking (TypeScript)
- [ ] Fast test subset execution
- [ ] Commit hooks configured

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# JavaScript Test Maintenance & CI/CD Implementation

Please implement comprehensive test automation and maintenance infrastructure for this JavaScript/TypeScript project following this protocol:

## Phase 1: CI/CD Pipeline Configuration

### GitHub Actions Setup

**Create `.github/workflows/tests.yml`**:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  lint:
    name: Lint and Format Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Check formatting with Prettier
        run: npm run format:check

      - name: Lint with ESLint
        run: npm run lint

      - name: Type check with TypeScript
        run: npm run type-check

  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: ['16', '18', '20']

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm run test:unit -- --coverage --ci --maxWorkers=2

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json
          flags: unit-tests
          name: codecov-${{ matrix.node-version }}

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results-${{ matrix.node-version }}
          path: |
            junit.xml
            coverage/

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379
        run: npm run test:integration -- --coverage --ci

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json
          flags: integration-tests

  e2e-tests:
    name: E2E Tests
    runs-on: ubuntu-latest
    needs: integration-tests

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload Playwright report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run npm audit
        run: npm audit --audit-level=moderate || true

      - name: Run Snyk security scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            snyk-report.json

  quality-gate:
    name: Quality Gate
    runs-on: ubuntu-latest
    needs: [lint, unit-tests, integration-tests, e2e-tests, security]
    steps:
      - name: Quality gate passed
        run: echo "All quality checks passed!"
```

### GitLab CI Configuration

**Create `.gitlab-ci.yml`**:

```yaml
stages:
  - lint
  - test
  - quality
  - deploy

variables:
  NODE_VERSION: "18"
  NPM_CONFIG_CACHE: "$CI_PROJECT_DIR/.npm"

cache:
  paths:
    - .npm
    - node_modules

before_script:
  - npm ci

lint:
  stage: lint
  image: node:${NODE_VERSION}
  script:
    - npm run format:check
    - npm run lint
    - npm run type-check

unit-tests:
  stage: test
  image: node:${NODE_VERSION}
  script:
    - npm run test:unit -- --coverage --ci --maxWorkers=2
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
      junit: junit.xml
    paths:
      - coverage/

integration-tests:
  stage: test
  image: node:${NODE_VERSION}
  services:
    - postgres:14
    - redis:7
  variables:
    POSTGRES_DB: testdb
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: testpass
    DATABASE_URL: postgresql://postgres:testpass@postgres:5432/testdb
  script:
    - npm run test:integration -- --coverage --ci
  artifacts:
    paths:
      - coverage/

e2e-tests:
  stage: test
  image: mcr.microsoft.com/playwright:v1.40.0-focal
  script:
    - npm ci
    - npm run test:e2e
  artifacts:
    when: always
    paths:
      - playwright-report/

quality-gate:
  stage: quality
  image: node:${NODE_VERSION}
  script:
    - npm run test:coverage-check
  needs:
    - unit-tests
    - integration-tests
```

## Phase 2: Quality Gates Configuration

### Coverage Thresholds

**Configure in `jest.config.js`**:
```javascript
module.exports = {
  // Test environment
  testEnvironment: 'node',

  // Coverage configuration
  collectCoverage: true,
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html', 'cobertura'],

  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    },
    './src/critical/': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    }
  },

  // Paths to ignore
  coveragePathIgnorePatterns: [
    '/node_modules/',
    '/tests/',
    '/__tests__/',
    '/dist/',
    '/build/'
  ],

  // Test matching
  testMatch: [
    '**/__tests__/**/*.[jt]s?(x)',
    '**/?(*.)+(spec|test).[jt]s?(x)'
  ],

  // Timeout
  testTimeout: 10000,

  // Reporters
  reporters: [
    'default',
    [
      'jest-junit',
      {
        outputDirectory: '.',
        outputName: 'junit.xml',
        classNameTemplate: '{classname}',
        titleTemplate: '{title}',
        ancestorSeparator: ' › ',
        usePathForSuiteName: true
      }
    ]
  ]
};
```

### Test Pass Rate Gate

```javascript
// tests/setup/qualityGate.js
/**
 * Quality gate enforcement for test suite.
 */

// Hook into Jest's test results
class QualityGateReporter {
  constructor(globalConfig, options) {
    this._globalConfig = globalConfig;
    this._options = options;
  }

  onRunComplete(contexts, results) {
    const { numFailedTests, numPassedTests, numTotalTests } = results;

    const passRate = (numPassedTests / numTotalTests) * 100;

    console.log('\n' + '='.repeat(60));
    console.log(`Test Pass Rate: ${passRate.toFixed(1)}% (${numPassedTests}/${numTotalTests})`);
    console.log('='.repeat(60));

    if (passRate < 100) {
      console.log('⚠️  WARNING: Not all tests passed');
      console.log(`Failed tests: ${numFailedTests}`);
    } else {
      console.log('✅ Quality Gate Passed: All tests passed');
    }

    // Enforce 100% pass rate
    if (numFailedTests > 0) {
      console.log('\n❌ Quality Gate Failed: Some tests did not pass');
      console.log('All tests must pass before merge.');
      process.exitCode = 1;
    }
  }
}

module.exports = QualityGateReporter;
```

Add to `jest.config.js`:
```javascript
reporters: [
  'default',
  '<rootDir>/tests/setup/qualityGate.js'
]
```

### Performance Regression Gate

```javascript
// tests/benchmarks/performanceGate.js
/**
 * Performance regression detection.
 */
const fs = require('fs');
const path = require('path');

const BASELINE_FILE = path.join(__dirname, 'baseline.json');
const REGRESSION_THRESHOLD = 0.10; // 10% slower fails

class PerformanceGate {
  constructor() {
    this.benchmarks = new Map();
    this.baseline = this.loadBaseline();
  }

  loadBaseline() {
    if (fs.existsSync(BASELINE_FILE)) {
      return JSON.parse(fs.readFileSync(BASELINE_FILE, 'utf8'));
    }
    return {};
  }

  saveBaseline() {
    const data = Object.fromEntries(this.benchmarks);
    fs.writeFileSync(BASELINE_FILE, JSON.stringify(data, null, 2));
  }

  recordBenchmark(name, duration) {
    this.benchmarks.set(name, duration);
  }

  checkRegressions() {
    const regressions = [];

    for (const [name, current] of this.benchmarks.entries()) {
      if (this.baseline[name]) {
        const baseline = this.baseline[name];
        const regression = (current - baseline) / baseline;

        if (regression > REGRESSION_THRESHOLD) {
          regressions.push({
            name,
            baseline,
            current,
            regression: `${(regression * 100).toFixed(1)}%`
          });
        }
      }
    }

    if (regressions.length > 0) {
      console.log('\n❌ Performance Regression Detected:');
      regressions.forEach(reg => {
        console.log(`  ${reg.name}: ${reg.regression} slower`);
        console.log(`    Baseline: ${reg.baseline}ms, Current: ${reg.current}ms`);
      });
      throw new Error('Performance regression gate failed');
    }

    console.log('✅ Performance Gate Passed: No regressions detected');
  }

  finish() {
    if (Object.keys(this.baseline).length === 0) {
      // First run - save baseline
      this.saveBaseline();
      console.log('📊 Baseline performance metrics saved');
    } else {
      this.checkRegressions();
    }
  }
}

module.exports = new PerformanceGate();
```

## Phase 3: Pre-commit Hooks

### Install Husky

```bash
npm install --save-dev husky lint-staged
npx husky install
npm pkg set scripts.prepare="husky install"
```

### Configure Pre-commit Hooks

**Create `.husky/pre-commit`**:

```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

npx lint-staged
```

**Configure `package.json`**:

```json
{
  "scripts": {
    "prepare": "husky install",
    "test": "jest",
    "test:unit": "jest --testPathPattern=unit",
    "test:integration": "jest --testPathPattern=integration",
    "test:e2e": "playwright test",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:coverage-check": "jest --coverage --coverageThreshold='{\"global\":{\"branches\":80,\"functions\":80,\"lines\":80,\"statements\":80}}'",
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
    "lint:fix": "eslint . --ext .js,.jsx,.ts,.tsx --fix",
    "format": "prettier --write \"**/*.{js,jsx,ts,tsx,json,css,scss,md}\"",
    "format:check": "prettier --check \"**/*.{js,jsx,ts,tsx,json,css,scss,md}\"",
    "type-check": "tsc --noEmit"
  },
  "lint-staged": {
    "*.{js,jsx,ts,tsx}": [
      "eslint --fix",
      "prettier --write",
      "jest --bail --findRelatedTests --passWithNoTests"
    ],
    "*.{json,css,scss,md}": [
      "prettier --write"
    ]
  }
}
```

### ESLint Configuration

**Create `.eslintrc.js`**:

```javascript
module.exports = {
  root: true,
  env: {
    node: true,
    es2022: true,
    jest: true
  },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:jest/recommended',
    'prettier'
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module'
  },
  plugins: ['@typescript-eslint', 'jest'],
  rules: {
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'warn',
    'jest/expect-expect': 'error',
    'jest/no-disabled-tests': 'warn',
    'jest/no-focused-tests': 'error',
    'jest/no-identical-title': 'error',
    'jest/valid-expect': 'error'
  }
};
```

### Prettier Configuration

**Create `.prettierrc.js`**:

```javascript
module.exports = {
  semi: true,
  trailingComma: 'es5',
  singleQuote: true,
  printWidth: 100,
  tabWidth: 2,
  useTabs: false,
  arrowParens: 'avoid',
  endOfLine: 'lf'
};
```

## Phase 4: Test Parallelization

### Configure Jest for Parallel Execution

```javascript
// jest.config.js
module.exports = {
  // Use all available CPU cores
  maxWorkers: '50%',

  // Or specify exact number
  // maxWorkers: 4,

  // Run tests in parallel
  testTimeout: 10000,

  // Bail after N failures
  bail: 5,

  // Clear mocks between tests
  clearMocks: true,

  // Reset modules between tests for isolation
  resetModules: false,

  // Sharding for CI (run subset of tests)
  // Use with: jest --shard=1/4
};
```

### Optimize for CI

```json
{
  "scripts": {
    "test:ci": "jest --ci --coverage --maxWorkers=2 --silent",
    "test:ci:shard": "jest --ci --coverage --maxWorkers=2 --shard"
  }
}
```

### Handle Non-Thread-Safe Tests

```javascript
// tests/integration/database.test.js
/**
 * Tests that must run serially.
 */
describe.serial('Database Migrations', () => {
  // Use maxConcurrency option
  jest.setTimeout(30000);

  beforeAll(async () => {
    // Acquire exclusive lock
  });

  afterAll(async () => {
    // Release lock
  });

  test('migration 001 runs successfully', async () => {
    // Test implementation
  });
});
```

## Phase 5: Flaky Test Management

### Detect Flaky Tests

```bash
# Install flaky test detection
npm install --save-dev jest-circus

# Run tests multiple times
npm test -- --testSequencer=./tests/setup/flakyDetector.js
```

### Flaky Test Detector

```javascript
// tests/setup/flakyDetector.js
/**
 * Detect flaky tests by running them multiple times.
 */
const Sequencer = require('@jest/test-sequencer').default;

class FlakyTestSequencer extends Sequencer {
  sort(tests) {
    // Run known flaky tests first
    return tests.sort((a, b) => {
      const aFlaky = a.path.includes('flaky');
      const bFlaky = b.path.includes('flaky');
      return bFlaky - aFlaky;
    });
  }
}

module.exports = FlakyTestSequencer;
```

### Mark and Retry Flaky Tests

```javascript
// tests/utils/retry.js
/**
 * Retry wrapper for flaky tests.
 */
export function retryTest(testFn, retries = 3, delay = 1000) {
  return async (...args) => {
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        return await testFn(...args);
      } catch (error) {
        if (attempt === retries) {
          throw error;
        }
        console.warn(`Test failed (attempt ${attempt}/${retries}), retrying...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  };
}

// Usage
import { retryTest } from './utils/retry';

describe('API Tests', () => {
  test('flaky external API call', retryTest(async () => {
    const response = await fetch('https://api.example.com/data');
    expect(response.status).toBe(200);
  }, 3, 2000));
});
```

### Track Flaky Tests

```javascript
// tests/setup/flakyTracker.js
/**
 * Track flaky test occurrences.
 */
const fs = require('fs');
const path = require('path');

const FLAKY_LOG = path.join(__dirname, '../flaky-tests.json');

class FlakyTestTracker {
  constructor() {
    this.flakyTests = this.loadLog();
  }

  loadLog() {
    if (fs.existsSync(FLAKY_LOG)) {
      return JSON.parse(fs.readFileSync(FLAKY_LOG, 'utf8'));
    }
    return {};
  }

  saveLog() {
    fs.writeFileSync(FLAKY_LOG, JSON.stringify(this.flakyTests, null, 2));
  }

  recordFlaky(testName) {
    if (!this.flakyTests[testName]) {
      this.flakyTests[testName] = {
        count: 0,
        lastSeen: null
      };
    }

    this.flakyTests[testName].count++;
    this.flakyTests[testName].lastSeen = new Date().toISOString();
  }

  report() {
    const sorted = Object.entries(this.flakyTests)
      .sort((a, b) => b[1].count - a[1].count)
      .slice(0, 10);

    if (sorted.length > 0) {
      console.log('\n⚠️  Top Flaky Tests:');
      sorted.forEach(([test, data]) => {
        console.log(`  ${test}: ${data.count} failures`);
      });
    }
  }
}

module.exports = new FlakyTestTracker();
```

## Phase 6: Test Maintenance Practices

### Monitor Test Execution Time

```javascript
// tests/setup/slowTestReporter.js
/**
 * Report slow tests.
 */
const SLOW_TEST_THRESHOLD = 1000; // 1 second

class SlowTestReporter {
  constructor(globalConfig, options) {
    this._globalConfig = globalConfig;
    this._options = options;
    this.slowTests = [];
  }

  onTestResult(test, testResult) {
    testResult.testResults.forEach(result => {
      if (result.duration && result.duration > SLOW_TEST_THRESHOLD) {
        this.slowTests.push({
          name: result.fullName,
          file: test.path,
          duration: result.duration
        });
      }
    });
  }

  onRunComplete() {
    if (this.slowTests.length > 0) {
      console.log('\n' + '='.repeat(60));
      console.log('Slow Tests Detected:');

      this.slowTests
        .sort((a, b) => b.duration - a.duration)
        .slice(0, 10)
        .forEach(test => {
          console.log(`  ${(test.duration / 1000).toFixed(2)}s: ${test.name}`);
        });

      console.log('='.repeat(60));
    }
  }
}

module.exports = SlowTestReporter;
```

### Cleanup Obsolete Tests

```javascript
// scripts/findObsoleteTests.js
/**
 * Find tests that may be obsolete.
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function findTestFiles(dir) {
  const files = [];
  const items = fs.readdirSync(dir);

  items.forEach(item => {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      files.push(...findTestFiles(fullPath));
    } else if (item.match(/\.(test|spec)\.(js|ts)$/)) {
      files.push(fullPath);
    }
  });

  return files;
}

function getLastModified(file) {
  try {
    const output = execSync(`git log -1 --format=%ci "${file}"`).toString().trim();
    return new Date(output);
  } catch {
    return new Date(0);
  }
}

function findObsoleteTests(daysThreshold = 180) {
  const testFiles = findTestFiles('tests');
  const threshold = Date.now() - (daysThreshold * 24 * 60 * 60 * 1000);
  const obsolete = [];

  testFiles.forEach(file => {
    const lastModified = getLastModified(file);
    if (lastModified.getTime() < threshold) {
      const content = fs.readFileSync(file, 'utf8');
      const hasAssertions = /expect\(|assert\(/.test(content);

      if (!hasAssertions) {
        obsolete.push({
          file,
          lastModified: lastModified.toISOString(),
          reason: 'No assertions found'
        });
      }
    }
  });

  if (obsolete.length > 0) {
    console.log('\n⚠️  Potentially Obsolete Tests:');
    obsolete.forEach(({ file, lastModified, reason }) => {
      console.log(`  ${file}`);
      console.log(`    Last modified: ${lastModified}`);
      console.log(`    Reason: ${reason}`);
    });
  } else {
    console.log('✅ No obsolete tests found');
  }
}

findObsoleteTests();
```

### Document Test Purpose

```javascript
/**
 * User Authentication Test Suite
 *
 * Purpose:
 *   Validate user login, logout, and session management functionality.
 *
 * Coverage:
 *   - Valid credential login
 *   - Invalid credential handling
 *   - Session token generation and validation
 *   - Multi-factor authentication flow
 *   - Password reset process
 *
 * Maintenance Notes:
 *   - Update testValidLogin() if authentication logic changes
 *   - mockEmailService fixture required for password reset tests
 *   - Tests use in-memory database for speed
 *   - External API calls are mocked
 *
 * Dependencies:
 *   - @/services/auth
 *   - @/models/User
 *   - @/utils/jwt
 *
 * Last Review: 2024-01-15
 * Reviewed By: alice@example.com
 */

import { describe, test, expect, beforeEach } from '@jest/globals';
import { AuthService } from '@/services/auth';

describe('User Authentication', () => {
  // Test implementation
});
```

## Phase 7: Test Result Reporting

### JUnit XML Reports

Configure in `jest.config.js`:
```javascript
reporters: [
  'default',
  [
    'jest-junit',
    {
      outputDirectory: './junit',
      outputName: 'test-results.xml',
      classNameTemplate: '{classname}',
      titleTemplate: '{title}',
      ancestorSeparator: ' › ',
      usePathForSuiteName: true,
      suiteNameTemplate: '{filepath}'
    }
  ]
]
```

### HTML Reports

```bash
npm install --save-dev jest-html-reporter

# Configure in jest.config.js
reporters: [
  'default',
  [
    'jest-html-reporter',
    {
      pageTitle: 'Test Report',
      outputPath: 'test-report.html',
      includeFailureMsg: true,
      includeConsoleLog: true,
      theme: 'darkTheme'
    }
  ]
]
```

### Custom Test Report

```javascript
// tests/setup/customReporter.js
/**
 * Generate custom JSON test report.
 */
const fs = require('fs');
const path = require('path');

class CustomReporter {
  constructor(globalConfig, options) {
    this._globalConfig = globalConfig;
    this._options = options;
    this.results = [];
  }

  onTestResult(test, testResult) {
    this.results.push({
      file: test.path,
      tests: testResult.testResults.map(result => ({
        name: result.fullName,
        status: result.status,
        duration: result.duration,
        failureMessages: result.failureMessages
      }))
    });
  }

  onRunComplete(contexts, results) {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        total: results.numTotalTests,
        passed: results.numPassedTests,
        failed: results.numFailedTests,
        pending: results.numPendingTests,
        duration: results.testResults.reduce((acc, r) => acc + r.perfStats.runtime, 0)
      },
      results: this.results
    };

    const outputPath = path.join(process.cwd(), 'test-report.json');
    fs.writeFileSync(outputPath, JSON.stringify(report, null, 2));

    console.log(`\n📊 Custom test report saved to: ${outputPath}`);
  }
}

module.exports = CustomReporter;
```

## Output Format

Please provide a comprehensive CI/CD and maintenance implementation with the following structure:

### CI/CD Configuration Summary
- **Platform**: [GitHub Actions/GitLab CI/Jenkins]
- **Pipeline Stages**: [list stages]
- **Parallel Execution**: [enabled/disabled, worker count]
- **Test Types Automated**: [unit, integration, e2e]
- **Quality Gates**: [list gates]

### Quality Gate Configuration
| Gate | Threshold | Current | Status |
|------|-----------|---------|--------|
| Code Coverage | 80% | [value] | ✅/❌ |
| Test Pass Rate | 100% | [value] | ✅/❌ |
| Performance | <10% regression | [value] | ✅/❌ |

### Pre-commit Hooks Configured
- [ ] Code formatting (Prettier)
- [ ] Import sorting
- [ ] Linting (ESLint)
- [ ] Type checking (TypeScript)
- [ ] Fast test execution
- [ ] Coverage check

### Test Maintenance Status
**Slow Tests Identified**:
| Test | Duration | Recommendation |
|------|----------|----------------|
| [test_name] | [time] | [optimization] |

**Flaky Tests**:
| Test | Failure Rate | Action |
|------|--------------|--------|
| [test_name] | [rate] | [fix planned] |

### Test Execution Metrics
- **Total Tests**: [count]
- **Average Execution Time**: [duration]
- **Parallel Workers**: [count]
- **Tests per Second**: [rate]
- **Coverage**: [percentage]

### CI/CD Pipeline Visualization
```
┌─────────┐     ┌──────────┐     ┌────────────┐     ┌────────┐
│  Lint   │────▶│   Unit   │────▶│Integration │────▶│ Deploy │
└─────────┘     │  Tests   │     │   Tests    │     └────────┘
                └──────────┘     └────────────┘
                     │                 │
                     ▼                 ▼
                ┌─────────┐       ┌─────────┐
                │Coverage │       │Security │
                │  Gate   │       │  Scan   │
                └─────────┘       └─────────┘
```

### Best Practices Implemented
- [ ] All tests automated in CI/CD
- [ ] Quality gates prevent regressions
- [ ] Pre-commit hooks catch issues early
- [ ] Parallel execution for speed
- [ ] Flaky tests tracked and fixed
- [ ] Test maintenance schedule established

### Next Steps
- [ ] Monitor and optimize slow tests
- [ ] Fix identified flaky tests
- [ ] Review and update obsolete tests
- [ ] Enhance test documentation
- [ ] Set up test result dashboard
- [ ] Schedule regular test maintenance reviews
~~~

## Output Format

The AI assistant should deliver:

1. **Complete CI/CD pipeline configuration** (GitHub Actions or GitLab CI)
2. **Quality gate implementation** with thresholds
3. **Pre-commit hook configuration** with all checks
4. **Test parallelization setup** for faster execution
5. **Flaky test detection and tracking** system
6. **Test maintenance procedures** and documentation
7. **Test reporting infrastructure** with dashboards
8. **Execution metrics and monitoring** setup
