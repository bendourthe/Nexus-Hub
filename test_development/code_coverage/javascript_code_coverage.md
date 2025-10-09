# JavaScript Code Coverage Analysis

## Objective
Implement comprehensive code coverage measurement using Istanbul/nyc and c8, analyze coverage gaps, establish coverage goals (80%+ target), create systematic improvement strategies, integrate coverage into CI/CD, and maintain high-quality test coverage for JavaScript/TypeScript projects.

## Output Directory Structure

All test outputs should be saved in organized directories:

```
tests/
└── code_coverage/
    ├── test_files/
    ├── test_data/
    ├── test_reports/
    └── test_configs/
```

**Directory Setup**:
- Create `tests/` directory in repository root if it doesn't exist
- Create `tests/code_coverage/` subdirectory for this testing phase
- All test files, data, reports, and configurations go in the phase-specific directory

**Expected Outputs**:
- `test_files/` - Actual test implementation files
- `test_data/` - Test fixtures, mock data, sample inputs
- `test_reports/` - Test execution reports, coverage reports, performance results
- `test_configs/` - Framework configurations, test runner settings

## Implementation Checklist

### Coverage Setup
- [ ] Istanbul/nyc or c8 installed and configured
- [ ] Jest/Mocha coverage integration enabled
- [ ] Coverage configuration file created
- [ ] HTML report generation configured
- [ ] CI/CD coverage reporting set up

### Coverage Analysis
- [ ] Current coverage baseline measured
- [ ] Coverage gaps identified and prioritized
- [ ] Critical paths coverage verified
- [ ] Edge cases coverage assessed
- [ ] Untested code documented

### Coverage Goals
- [ ] Target coverage defined (80%+ recommended)
- [ ] Coverage thresholds set by module
- [ ] Critical path coverage requirements established
- [ ] Coverage improvement plan created
- [ ] Timeline for improvements defined

### Coverage Integration
- [ ] Coverage gates in CI/CD configured
- [ ] Coverage reports automated
- [ ] Coverage trends tracked
- [ ] Coverage regression prevention enabled
- [ ] Team coverage standards documented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# JavaScript Code Coverage Implementation

Please implement comprehensive code coverage measurement and improvement for this JavaScript/TypeScript project following this protocol:

## Phase 1: Coverage Setup and Configuration

### Install Coverage Tools

**Option 1: Using c8 (modern V8 coverage)**:
```bash
npm install --save-dev c8
```

**Option 2: Using nyc (Istanbul CLI)**:
```bash
npm install --save-dev nyc
```

**For Jest** (built-in coverage):
```bash
npm install --save-dev jest
```

### Configure Coverage with c8

**package.json configuration**:
```json
{
  "scripts": {
    "test": "c8 mocha",
    "test:coverage": "c8 --reporter=html --reporter=text --reporter=lcov npm test",
    "test:coverage:json": "c8 --reporter=json npm test"
  },
  "c8": {
    "all": true,
    "include": [
      "src/**/*.js",
      "lib/**/*.js"
    ],
    "exclude": [
      "**/*.test.js",
      "**/*.spec.js",
      "**/node_modules/**",
      "**/test/**",
      "**/tests/**",
      "**/__tests__/**",
      "**/coverage/**",
      "**/dist/**"
    ],
    "reporter": [
      "text",
      "html",
      "lcov",
      "json"
    ],
    "lines": 80,
    "functions": 80,
    "branches": 80,
    "statements": 80,
    "check-coverage": true,
    "per-file": false,
    "skip-full": false,
    "clean": true
  }
}
```

**Alternative: .c8rc.json**:
```json
{
  "all": true,
  "include": ["src/**/*.js"],
  "exclude": [
    "**/*.test.js",
    "**/*.spec.js",
    "**/node_modules/**",
    "**/coverage/**"
  ],
  "reporter": ["text", "html", "lcov", "json"],
  "lines": 80,
  "functions": 80,
  "branches": 80,
  "statements": 80,
  "check-coverage": true,
  "watermarks": {
    "lines": [80, 95],
    "functions": [80, 95],
    "branches": [80, 95],
    "statements": [80, 95]
  }
}
```

### Configure Coverage with nyc

**.nycrc.json**:
```json
{
  "all": true,
  "include": [
    "src/**/*.js",
    "lib/**/*.js"
  ],
  "exclude": [
    "**/*.test.js",
    "**/*.spec.js",
    "**/node_modules/**",
    "**/test/**",
    "**/tests/**",
    "**/__tests__/**",
    "**/coverage/**",
    "**/dist/**",
    "**/.next/**"
  ],
  "reporter": [
    "text",
    "text-summary",
    "html",
    "lcov",
    "json"
  ],
  "lines": 80,
  "functions": 80,
  "branches": 80,
  "statements": 80,
  "check-coverage": true,
  "per-file": false,
  "skip-full": false,
  "cache": true,
  "temp-dir": "./coverage/.nyc_output",
  "report-dir": "./coverage",
  "watermarks": {
    "lines": [80, 95],
    "functions": [80, 95],
    "branches": [80, 95],
    "statements": [80, 95]
  },
  "exclude-after-remap": false
}
```

### Configure Coverage with Jest

**jest.config.js**:
```javascript
module.exports = {
  collectCoverage: true,
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.test.{js,jsx,ts,tsx}',
    '!src/**/*.spec.{js,jsx,ts,tsx}',
    '!src/**/__tests__/**',
    '!src/**/node_modules/**',
    '!src/**/dist/**'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: [
    'text',
    'text-summary',
    'html',
    'lcov',
    'json',
    'json-summary'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  coveragePathIgnorePatterns: [
    '/node_modules/',
    '/coverage/',
    '/dist/',
    '/.next/'
  ]
};
```

**package.json scripts**:
```json
{
  "scripts": {
    "test": "jest",
    "test:coverage": "jest --coverage",
    "test:coverage:watch": "jest --coverage --watch",
    "test:coverage:json": "jest --coverage --coverageReporters=json"
  }
}
```

### TypeScript Configuration

**For TypeScript projects, add source map support**:

```json
{
  "compilerOptions": {
    "sourceMap": true,
    "inlineSourceMap": false,
    "declaration": true,
    "declarationMap": true
  }
}
```

**nyc with TypeScript**:
```json
{
  "extension": [".ts", ".tsx"],
  "require": ["ts-node/register"],
  "exclude": ["**/*.d.ts"],
  "source-map": true,
  "produce-source-map": true
}
```

## Phase 2: Measure Current Coverage

### Run Coverage Analysis

**Using c8**:
```bash
# Run tests with coverage
c8 npm test

# Generate HTML report
c8 --reporter=html npm test

# Open HTML report
open coverage/index.html  # macOS
xdg-open coverage/index.html  # Linux
start coverage/index.html  # Windows
```

**Using nyc**:
```bash
# Run tests with coverage
nyc npm test

# Generate all reports
nyc --reporter=html --reporter=text --reporter=lcov npm test

# Open HTML report
open coverage/index.html
```

**Using Jest**:
```bash
# Run tests with coverage
npm test -- --coverage

# Generate JSON summary
npm test -- --coverage --coverageReporters=json-summary

# Open HTML report
open coverage/lcov-report/index.html
```

### Analyze Coverage Report

**Terminal output example**:
```
----------|---------|----------|---------|---------|-------------------
File      | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
----------|---------|----------|---------|---------|-------------------
All files |   76.32 |    68.45 |   81.25 |   76.89 |
 auth.js  |   78.26 |    70.00 |   85.71 |   78.95 | 23-25,45-48,67
 db.js    |   79.41 |    65.22 |   82.35 |   80.00 | 89-95,112-115
 utils.js |   92.11 |    87.50 |   90.00 |   93.33 | 45,67
 user.js  |   67.42 |    55.56 |   70.59 |   68.18 | 45-67,89-102
----------|---------|----------|---------|---------|-------------------
```

### Identify Coverage Gaps

**Create coverage gap analysis script**:

```javascript
// scripts/analyzeCoverage.js
/**
 * Analyze coverage gaps and prioritize improvements.
 */
const fs = require('fs');
const path = require('path');

function analyzeCoverageGaps() {
  const coverageFile = path.join(process.cwd(), 'coverage', 'coverage-summary.json');

  if (!fs.existsSync(coverageFile)) {
    console.error('Run: npm test -- --coverage --coverageReporters=json-summary');
    process.exit(1);
  }

  const coverage = JSON.parse(fs.readFileSync(coverageFile, 'utf8'));
  const gaps = [];

  for (const [filePath, metrics] of Object.entries(coverage)) {
    if (filePath === 'total') continue;

    const avgCoverage = (
      metrics.lines.pct +
      metrics.statements.pct +
      metrics.functions.pct +
      metrics.branches.pct
    ) / 4;

    if (avgCoverage < 80) {
      gaps.push({
        file: filePath.replace(process.cwd(), ''),
        coverage: avgCoverage,
        lines: metrics.lines.pct,
        branches: metrics.branches.pct,
        functions: metrics.functions.pct,
        statements: metrics.statements.pct,
        priority: avgCoverage < 50 ? 'high' : 'medium'
      });
    }
  }

  gaps.sort((a, b) => a.coverage - b.coverage);

  console.log('\n' + '='.repeat(80));
  console.log('Coverage Gap Analysis');
  console.log('='.repeat(80));
  console.log('\nFiles Below 80% Coverage:\n');
  console.log(
    'File'.padEnd(45) +
    'Avg'.padStart(8) +
    'Lines'.padStart(8) +
    'Branch'.padStart(8) +
    'Priority'.padStart(10)
  );
  console.log('-'.repeat(80));

  gaps.forEach(gap => {
    console.log(
      gap.file.padEnd(45) +
      `${gap.coverage.toFixed(1)}%`.padStart(8) +
      `${gap.lines.toFixed(1)}%`.padStart(8) +
      `${gap.branches.toFixed(1)}%`.padStart(8) +
      gap.priority.padStart(10)
    );
  });

  console.log(`\nTotal files needing improvement: ${gaps.length}`);
}

analyzeCoverageGaps();
```

Run analysis:
```bash
# Generate JSON coverage summary
npm test -- --coverage --coverageReporters=json-summary

# Analyze gaps
node scripts/analyzeCoverage.js
```

## Phase 3: Prioritize Coverage Improvements

### Coverage Improvement Matrix

| Priority | Criteria | Action |
|----------|----------|--------|
| **Critical** | Core business logic <50% coverage | Immediate test creation |
| **High** | Public APIs <70% coverage | Test in current sprint |
| **Medium** | Utilities <80% coverage | Test in next sprint |
| **Low** | Internal helpers <80% coverage | Test when modified |

### Identify Critical Paths

```javascript
// scripts/identifyCriticalPaths.js
/**
 * Identify critical code paths requiring coverage.
 */
const fs = require('fs');
const path = require('path');
const acorn = require('acorn');
const walk = require('acorn-walk');

function analyzeCriticalPaths(filePath) {
  const code = fs.readFileSync(filePath, 'utf8');
  const ast = acorn.parse(code, {
    ecmaVersion: 2022,
    sourceType: 'module'
  });

  const critical = [];

  walk.simple(ast, {
    FunctionDeclaration(node) {
      // Exported functions are critical
      if (node.id && !node.id.name.startsWith('_')) {
        critical.push({
          name: node.id.name,
          line: node.loc.start.line,
          reason: 'Public API'
        });
      }
    },

    TryStatement(node) {
      critical.push({
        name: 'try/catch block',
        line: node.loc.start.line,
        reason: 'Error handling'
      });
    },

    CallExpression(node) {
      if (node.callee.type === 'MemberExpression') {
        const methods = ['fetch', 'axios', 'get', 'post', 'query'];
        if (methods.includes(node.callee.property.name)) {
          critical.push({
            name: node.callee.property.name,
            line: node.loc.start.line,
            reason: 'External dependency'
          });
        }
      }
    }
  });

  return critical;
}

// Usage
const srcDir = path.join(process.cwd(), 'src');
function walkDir(dir) {
  fs.readdirSync(dir).forEach(file => {
    const filePath = path.join(dir, file);
    if (fs.statSync(filePath).isDirectory()) {
      walkDir(filePath);
    } else if (filePath.endsWith('.js')) {
      const critical = analyzeCriticalPaths(filePath);
      if (critical.length > 0) {
        console.log(`\n${filePath}:`);
        critical.forEach(item => {
          console.log(`  Line ${item.line}: ${item.name} (${item.reason})`);
        });
      }
    }
  });
}

walkDir(srcDir);
```

## Phase 4: Systematic Coverage Improvement

### Strategy 1: Fill Happy Path Coverage

```javascript
/**
 * Add tests for basic functionality of uncovered code.
 *
 * Focus on main execution paths first.
 */

// Uncovered function
function calculateDiscount(price, customerType) {
  if (customerType === 'premium') {
    return price * 0.20;
  } else if (customerType === 'regular') {
    return price * 0.10;
  } else {
    return 0;
  }
}

// Add basic coverage tests
describe('calculateDiscount', () => {
  test('should calculate premium customer discount', () => {
    const discount = calculateDiscount(100, 'premium');
    expect(discount).toBe(20);
  });

  test('should calculate regular customer discount', () => {
    const discount = calculateDiscount(100, 'regular');
    expect(discount).toBe(10);
  });

  test('should return zero for other customer types', () => {
    const discount = calculateDiscount(100, 'guest');
    expect(discount).toBe(0);
  });
});
```

### Strategy 2: Cover Edge Cases

```javascript
/**
 * Add tests for boundary conditions and edge cases.
 */

describe('calculateDiscount edge cases', () => {
  test('should handle zero price', () => {
    const discount = calculateDiscount(0, 'premium');
    expect(discount).toBe(0);
  });

  test('should handle negative price', () => {
    const discount = calculateDiscount(-100, 'premium');
    expect(discount).toBe(-20); // Or should throw?
  });

  test('should handle very large price', () => {
    const discount = calculateDiscount(1000000, 'premium');
    expect(discount).toBe(200000);
  });

  test('should handle empty customer type', () => {
    const discount = calculateDiscount(100, '');
    expect(discount).toBe(0);
  });

  test('should handle null customer type', () => {
    const discount = calculateDiscount(100, null);
    expect(discount).toBe(0);
  });

  test('should handle undefined customer type', () => {
    const discount = calculateDiscount(100, undefined);
    expect(discount).toBe(0);
  });

  test('should handle case sensitivity', () => {
    const discount = calculateDiscount(100, 'PREMIUM');
    expect(discount).toBe(0); // Or should normalize case?
  });
});
```

### Strategy 3: Cover Error Paths

```javascript
/**
 * Add tests for error handling and exceptional conditions.
 */

// Function with error handling
async function loadUserData(userId) {
  try {
    const data = await database.query(`SELECT * FROM users WHERE id=${userId}`);

    if (!data) {
      throw new Error('User not found');
    }

    return parseUser(data);
  } catch (error) {
    if (error instanceof DatabaseError) {
      logger.error(`Database error: ${error.message}`);
      throw error;
    } else if (error.message === 'User not found') {
      logger.warn(`Invalid user: ${userId}`);
      return null;
    } else {
      throw error;
    }
  }
}

// Tests covering error paths
describe('loadUserData error handling', () => {
  let mockDatabase, mockLogger;

  beforeEach(() => {
    mockDatabase = {
      query: jest.fn()
    };
    mockLogger = {
      error: jest.fn(),
      warn: jest.fn()
    };
  });

  test('should handle database error', async () => {
    mockDatabase.query.mockRejectedValue(
      new DatabaseError('Connection failed')
    );

    await expect(loadUserData(123)).rejects.toThrow(DatabaseError);
    expect(mockLogger.error).toHaveBeenCalledWith(
      expect.stringContaining('Connection failed')
    );
  });

  test('should handle user not found', async () => {
    mockDatabase.query.mockResolvedValue(null);

    const result = await loadUserData(999);

    expect(result).toBeNull();
    expect(mockLogger.warn).toHaveBeenCalledWith(
      expect.stringContaining('Invalid user')
    );
  });

  test('should handle parse error', async () => {
    mockDatabase.query.mockResolvedValue({ invalid: 'data' });

    await expect(loadUserData(123)).rejects.toThrow();
  });
});
```

### Strategy 4: Cover Branch Conditions

```javascript
/**
 * Ensure all branches of conditional logic are tested.
 */

function getShippingCost(weight, destination, express = false) {
  let baseCost = weight * 2.5;

  if (destination === 'international') {
    baseCost *= 3;
  } else if (destination === 'remote') {
    baseCost *= 1.5;
  }

  if (express) {
    baseCost *= 2;
  }

  return baseCost;
}

// Tests covering all branches
describe('getShippingCost branches', () => {
  test('domestic standard shipping', () => {
    const cost = getShippingCost(10, 'domestic', false);
    expect(cost).toBe(25.0);
  });

  test('domestic express shipping', () => {
    const cost = getShippingCost(10, 'domestic', true);
    expect(cost).toBe(50.0);
  });

  test('international standard shipping', () => {
    const cost = getShippingCost(10, 'international', false);
    expect(cost).toBe(75.0);
  });

  test('international express shipping', () => {
    const cost = getShippingCost(10, 'international', true);
    expect(cost).toBe(150.0);
  });

  test('remote standard shipping', () => {
    const cost = getShippingCost(10, 'remote', false);
    expect(cost).toBe(37.5);
  });

  test('remote express shipping', () => {
    const cost = getShippingCost(10, 'remote', true);
    expect(cost).toBe(75.0);
  });
});
```

## Phase 5: Coverage Reporting and Tracking

### Generate Comprehensive Reports

```bash
# Generate all report types (Jest)
npm test -- --coverage \
  --coverageReporters=html \
  --coverageReporters=lcov \
  --coverageReporters=text \
  --coverageReporters=json-summary

# Reports generated:
# - coverage/lcov-report/index.html (browsable HTML)
# - coverage/lcov.info (for CI/CD)
# - coverage/coverage-summary.json (for analysis)
# - Terminal output (quick view)
```

### Coverage Badge

```bash
# Install coverage badge generator
npm install --save-dev jest-coverage-badges

# Add to package.json
{
  "scripts": {
    "test:badges": "npm test -- --coverage && jest-coverage-badges"
  }
}

# Generate badges
npm run test:badges

# Add to README.md
# ![Coverage:statements](./coverage/badge-statements.svg)
# ![Coverage:branches](./coverage/badge-branches.svg)
# ![Coverage:functions](./coverage/badge-functions.svg)
# ![Coverage:lines](./coverage/badge-lines.svg)
```

### Track Coverage Over Time

```javascript
// scripts/trackCoverage.js
/**
 * Track coverage metrics over time.
 */
const fs = require('fs');
const path = require('path');

function recordCoverage() {
  const coverageFile = path.join(process.cwd(), 'coverage', 'coverage-summary.json');
  const historyFile = path.join(process.cwd(), 'coverage-history.json');

  if (!fs.existsSync(coverageFile)) {
    console.error('No coverage-summary.json found');
    process.exit(1);
  }

  const coverage = JSON.parse(fs.readFileSync(coverageFile, 'utf8'));
  const total = coverage.total;

  let history = [];
  if (fs.existsSync(historyFile)) {
    history = JSON.parse(fs.readFileSync(historyFile, 'utf8'));
  }

  history.push({
    date: new Date().toISOString(),
    lines: total.lines.pct,
    statements: total.statements.pct,
    functions: total.functions.pct,
    branches: total.branches.pct
  });

  fs.writeFileSync(historyFile, JSON.stringify(history, null, 2));

  console.log(`Coverage recorded: ${total.lines.pct.toFixed(1)}% lines`);
}

recordCoverage();
```

### Coverage Diff for PRs

```javascript
// scripts/coverageDiff.js
/**
 * Show coverage changes in pull request.
 */
const fs = require('fs');

function coverageDiff(basePath, currentPath) {
  const base = JSON.parse(fs.readFileSync(basePath, 'utf8'));
  const current = JSON.parse(fs.readFileSync(currentPath, 'utf8'));

  const baseTotal = base.total.lines.pct;
  const currentTotal = current.total.lines.pct;
  const diff = currentTotal - baseTotal;

  console.log('\n' + '='.repeat(80));
  console.log('Coverage Diff');
  console.log('='.repeat(80));
  console.log(`Base coverage:    ${baseTotal.toFixed(2)}%`);
  console.log(`Current coverage: ${currentTotal.toFixed(2)}%`);
  console.log(`Difference:       ${diff >= 0 ? '+' : ''}${diff.toFixed(2)}%`);

  // File-level changes
  console.log('\n' + '='.repeat(80));
  console.log('Coverage Changes by File');
  console.log('='.repeat(80));

  const changes = [];
  for (const [filePath, metrics] of Object.entries(current)) {
    if (filePath === 'total') continue;

    if (base[filePath]) {
      const baseCov = base[filePath].lines.pct;
      const currentCov = metrics.lines.pct;
      const fileDiff = currentCov - baseCov;

      if (Math.abs(fileDiff) > 0.1) {
        changes.push({
          file: filePath,
          diff: fileDiff,
          current: currentCov
        });
      }
    }
  }

  if (changes.length > 0) {
    changes.sort((a, b) => a.diff - b.diff);
    changes.forEach(change => {
      const symbol = change.diff > 0 ? '📈' : '📉';
      console.log(
        `${symbol} ${change.file}: ${change.diff >= 0 ? '+' : ''}${change.diff.toFixed(1)}% ` +
        `(now ${change.current.toFixed(1)}%)`
      );
    });
  } else {
    console.log('No significant coverage changes');
  }

  // Exit with error if coverage decreased significantly
  if (diff < -0.5) {
    console.log(`\n❌ Coverage decreased by ${Math.abs(diff).toFixed(2)}%`);
    process.exit(1);
  } else if (diff < 0) {
    console.log(`\n⚠️  Coverage decreased slightly by ${Math.abs(diff).toFixed(2)}%`);
  } else {
    console.log('\n✅ Coverage maintained or improved');
  }
}

const [,, basePath, currentPath] = process.argv;
if (!basePath || !currentPath) {
  console.error('Usage: node coverageDiff.js <base_coverage.json> <current_coverage.json>');
  process.exit(1);
}

coverageDiff(basePath, currentPath);
```

## Phase 6: Coverage in CI/CD

### GitHub Actions Coverage Integration

```yaml
# .github/workflows/coverage.yml
name: Coverage

on: [push, pull_request]

jobs:
  coverage:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests with coverage
        run: npm test -- --coverage

      - name: Check coverage threshold
        run: |
          node -e "
            const coverage = require('./coverage/coverage-summary.json');
            const threshold = 80;
            const total = coverage.total.lines.pct;
            if (total < threshold) {
              console.error(\`Coverage \${total.toFixed(2)}% is below threshold \${threshold}%\`);
              process.exit(1);
            }
          "

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
          fail_ci_if_error: true

      - name: Generate coverage badges
        if: github.ref == 'refs/heads/main'
        run: |
          npm install -g jest-coverage-badges
          npm run test:badges

      - name: Commit badges
        if: github.ref == 'refs/heads/main'
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add coverage/*.svg
          git diff --quiet && git diff --staged --quiet || git commit -m "Update coverage badges"
          git push
```

### Coverage Regression Prevention

```yaml
# Add to existing workflow
- name: Check for coverage regression
  run: |
    # Download base coverage from main branch
    git fetch origin main
    git show origin/main:coverage/coverage-summary.json > base-coverage.json

    # Compare with current
    node scripts/coverageDiff.js base-coverage.json coverage/coverage-summary.json
```

## Output Format

Please provide a comprehensive coverage analysis with the following structure:

### Coverage Summary
- **Overall Coverage**: [percentage]
- **Line Coverage**: [percentage]
- **Branch Coverage**: [percentage]
- **Function Coverage**: [percentage]
- **Statement Coverage**: [percentage]
- **Total Statements**: [count]
- **Uncovered Lines**: [count]

### Coverage by Module
| Module | Lines | Branches | Functions | Statements | Priority |
|--------|-------|----------|-----------|------------|----------|
| src/auth.js | 78% | 70% | 86% | 79% | High |
| src/services/user.js | 67% | 56% | 71% | 68% | Critical |
| src/utils/helpers.js | 92% | 88% | 90% | 93% | Low |

### Critical Coverage Gaps
1. **src/services/user.js** (67% average coverage)
   - **Missing**: Error handling paths (lines 45-67)
   - **Priority**: Critical - core business logic
   - **Action**: Add tests for error scenarios

2. **src/auth.js** (78% average coverage)
   - **Missing**: Edge cases (lines 23-25, 45-48)
   - **Priority**: High - security-critical
   - **Action**: Add boundary condition tests

### Coverage Improvement Plan
**Sprint 1** (Target: 75% → 80%):
- [ ] Add error handling tests for user service
- [ ] Cover authentication edge cases
- [ ] Test database connection failures

**Sprint 2** (Target: 80% → 85%):
- [ ] Add branch coverage for conditionals
- [ ] Test input validation thoroughly
- [ ] Cover integration scenarios

**Sprint 3** (Target: 85% → 90%):
- [ ] Add performance edge cases
- [ ] Cover concurrent operations
- [ ] Test all error messages

### Coverage Reports Generated
- **HTML Report**: `coverage/lcov-report/index.html`
- **LCOV Report**: `coverage/lcov.info` (for CI/CD)
- **JSON Summary**: `coverage/coverage-summary.json` (for analysis)
- **Badges**: `coverage/badge-*.svg` (for README)

### Coverage Thresholds
- **Minimum Overall**: 80%
- **Critical Modules**: 90%
- **New Code**: 100%
- **CI/CD Gate**: Fail if <80%

### Best Practices Implemented
- [ ] Coverage measured on every test run
- [ ] HTML reports for detailed analysis
- [ ] Coverage tracked over time
- [ ] Regression prevention in CI/CD
- [ ] Critical paths prioritized
- [ ] Team coverage goals established

### Next Steps
- [ ] Fix identified coverage gaps
- [ ] Set up coverage dashboard
- [ ] Schedule coverage review meetings
- [ ] Document coverage standards
- [ ] Integrate coverage diff in PRs
- [ ] Track coverage trends monthly
~~~

## Output Format

The AI assistant should deliver:

1. **Complete coverage configuration** (package.json, jest.config.js, or .nycrc.json)
2. **Current coverage analysis** with gaps identified
3. **Prioritized improvement plan** with specific actions
4. **Test implementations** to fill critical gaps
5. **Coverage reporting infrastructure** (HTML, LCOV, JSON, badges)
6. **CI/CD integration** with coverage gates
7. **Coverage tracking scripts** for trends
8. **Coverage diff tools** for PR reviews
9. **Team documentation** on coverage standards
