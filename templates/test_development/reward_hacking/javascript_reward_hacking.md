---
template_id: javascript_reward_hacking
template_name: Reward Hacking Validation - Javascript
version: 1.0.0
last_updated: 2025-12-03
language: Javascript
category: test_development
phase: reward_hacking
phase_number: 8
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:

  - test_development/maintenance_cicd/javascript_maintenance_cicd.md
tools:

  - jest (29.7.0)

  - eslint (9.15.0)

  - prettier
tags:

  - test-development

  - javascript
---
# JavaScript/TypeScript Reward Hacking - Test Quality Validation Guide

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                            ► │ [COMPLETE]
│ Phase 3: Test Cases Development                ► │ [COMPLETE]
│ Phase 4: Mocks & Fixtures                      ► │ [COMPLETE]
│ Phase 5: Performance Testing                   ► │ [COMPLETE]
│ Phase 6: Code Coverage                         ► │ [COMPLETE]
│ Phase 7: Maintenance & CI/CD                   ► │ [COMPLETE]
│ Phase 8: Reward Hacking Validation              ► │ ● CURRENT
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 7 (Maintenance & CI/CD) should be completed first
**Next Step:** Testing complete!

---


## Objective

Validate the integrity and robustness of JavaScript/TypeScript test suites by detecting test quality issues, identifying "reward hacking" patterns where tests pass without truly validating functionality, and ensuring comprehensive, meaningful test coverage through mutation testing using Stryker and comprehensive quality analysis.

---

## Output Directory Structure

All generated files should be saved to the following directory structure:

```
${OUTPUT_DIR}/
├── templates/           # Detection scripts and automation tools
│   ├── detectTautologicalTests.js
│   ├── mutationTestRunner.sh
│   ├── qualityMetricsCalculator.js
│   ├── coverageAnalyzer.js
│   └── continuousMonitoringSetup.sh
├── assets/             # Visualizations and charts
│   ├── mutation_coverage_heatmap.png
│   ├── test_quality_scorecard.png
│   ├── phase_validation_matrix.png
│   ├── remediation_timeline.png
│   └── quality_trends_dashboard.png
└── exports/            # Reports and documentation
    ├── test_quality_report.md (25-35 pages)
    ├── mutation_testing_results.md
    ├── test_quality_scorecard.md
    ├── phase_by_phase_validation.md
    ├── remediation_action_plan.md
    ├── continuous_monitoring_setup.md
    └── weak_test_examples.md
```

---

## Implementation Checklist

### Prerequisites Verification
- [ ] All 7 previous testing phases completed

- [ ] Test structure output collected

- [ ] Unit test results available

- [ ] Integration test outputs gathered

- [ ] Mock and fixture implementations documented

- [ ] Performance test results compiled

- [ ] CI/CD pipeline logs obtained

- [ ] Code coverage reports generated

### Mutation Testing Setup
- [ ] Stryker installed and configured

- [ ] stryker.conf.js created

- [ ] Mutation testing baseline established

- [ ] Mutation score thresholds defined

- [ ] Test execution environment prepared

### Quality Analysis
- [ ] Tautological test detection script created

- [ ] Weak assertion analyzer implemented

- [ ] Over-mocking detection configured

- [ ] Coverage integrity validator developed

- [ ] Test independence checker deployed

### Reporting
- [ ] Comprehensive test quality report generated (25-35 pages)

- [ ] Mutation testing results documented

- [ ] Phase-by-phase validation completed

- [ ] Remediation action plan created

- [ ] Continuous monitoring configured

---

## Prompt Template

Copy the prompt below into your AI assistant to generate comprehensive reward hacking validation:

```markdown
# JavaScript/TypeScript Test Quality Validation - Reward Hacking Detection

## Context
I need comprehensive test quality validation for a JavaScript/TypeScript application. All 7 previous testing phases (Test Structure, Unit Tests, Test Cases, Mocks & Fixtures, Performance Testing, Maintenance & CI/CD, Code Coverage) are complete. Generate a thorough analysis detecting reward hacking patterns, validating test effectiveness through mutation testing, and providing actionable remediation guidance.

## CRITICAL: Output Directory Setup

Before starting, create this exact directory structure:

```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

Replace `${OUTPUT_DIR}` with your desired output location (e.g., `javascript_reward_hacking_output`).

---

## Repository Information

To include accurate repository information in documentation:

```bash
git config --get remote.origin.url
```

---

## Phase 1: Unit Test Quality Audit

**Validates:** Phase 2 (Unit Tests)

### 1.1 Tautological Test Detection

Analyze all unit tests for patterns that always pass:

**Detection Criteria:**

- Tests with no expectations/assertions

- Tests with trivial assertions (toBe(true), toBeTruthy())

- Tests that only check types without validating behavior

- Tests with mocked return values used directly in expectations

**Create:** `${OUTPUT_DIR}/templates/detectTautologicalTests.js`

```javascript
/**

 * Tautological Test Detector for JavaScript/TypeScript
 *

 * Analyzes Jest and Mocha tests to identify patterns that always pass.
 */

const fs = require('fs');
const path = require('path');
const { parse } = require('@babel/parser');
const traverse = require('@babel/traverse').default;

class TautologicalTestDetector {
  constructor() {
    this.issues = [];
    this.currentFile = null;
  }

  /**

   * Analyze a test file for tautological patterns
   */
  analyzeFile(filePath) {
    this.currentFile = filePath;
    const content = fs.readFileSync(filePath, 'utf-8');

    try {
      const ast = parse(content, {
        sourceType: 'module',
        plugins: ['typescript', 'jsx']
      });

      this.visitAST(ast);
    } catch (error) {
      console.error(`Error parsing ${filePath}:`, error.message);
    }
  }

  /**

   * Visit AST nodes to detect test patterns
   */
  visitAST(ast) {
    traverse(ast, {
      CallExpression: (path) => {
        const { node } = path;

        // Detect test functions (it, test, specify)
        if (this.isTestFunction(node)) {
          const testName = this.getTestName(node);
          const testFunction = node.arguments[1];

          if (!testFunction) return;

          // Check for assertions
          const hasAssertions = this.hasAssertions(testFunction);
          const assertionQuality = this.checkAssertionQuality(testFunction);

          if (!hasAssertions) {
            this.issues.push({
              file: this.currentFile,
              test: testName,
              line: node.loc.start.line,
              severity: 'CRITICAL',
              issue: 'No expectations found - execution-only test',
              pattern: 'TAUTOLOGICAL'
            });
          } else if (assertionQuality.trivial) {
            this.issues.push({
              file: this.currentFile,
              test: testName,
              line: node.loc.start.line,
              severity: 'HIGH',
              issue: `Trivial assertion: ${assertionQuality.reason}`,
              pattern: 'WEAK_ASSERTION'
            });
          } else if (assertionQuality.typeOnly) {
            this.issues.push({
              file: this.currentFile,
              test: testName,
              line: node.loc.start.line,
              severity: 'HIGH',
              issue: 'Type-only validation without behavior check',
              pattern: 'TYPE_ONLY'
            });
          }
        }
      }
    });
  }

  /**

   * Check if node is a test function call
   */
  isTestFunction(node) {
    const callee = node.callee;
    if (callee.type === 'Identifier') {
      return ['it', 'test', 'specify'].includes(callee.name);
    }
    return false;
  }

  /**

   * Extract test name from test function
   */
  getTestName(node) {
    const firstArg = node.arguments[0];
    if (firstArg && firstArg.type === 'StringLiteral') {
      return firstArg.value;
    }
    return 'unnamed test';
  }

  /**

   * Check if test function has assertions
   */
  hasAssertions(testFunction) {
    let hasAssertion = false;

    traverse(testFunction, {
      CallExpression: (path) => {
        const { node } = path;
        const callee = node.callee;

        // Check for expect() calls
        if (callee.type === 'Identifier' && callee.name === 'expect') {
          hasAssertion = true;
        }

        // Check for assert calls (Mocha)
        if (callee.type === 'MemberExpression' &&
            callee.object.name === 'assert') {
          hasAssertion = true;
        }
      }
    }, path.scope);

    return hasAssertion;
  }

  /**

   * Analyze quality of assertions in test
   */
  checkAssertionQuality(testFunction) {
    const result = { trivial: false, typeOnly: false, reason: '' };
    let assertionCount = 0;

    traverse(testFunction, {
      CallExpression: (path) => {
        const { node } = path;
        const callee = node.callee;

        // Analyze expect() chains
        if (callee.type === 'MemberExpression') {
          const property = callee.property.name;

          // Trivial assertions
          if (['toBe', 'toEqual'].includes(property)) {
            const arg = node.arguments[0];
            if (arg && arg.type === 'BooleanLiteral' && arg.value === true) {
              result.trivial = true;
              result.reason = 'expect(x).toBe(true)';
            }
          }

          // Truthiness checks
          if (['toBeTruthy', 'toBeDefined'].includes(property)) {
            assertionCount++;
            if (assertionCount === 1) {
              // Only flagged if it's the ONLY assertion
              result.trivial = true;
              result.reason = `expect(x).${property}()`;
            }
          }

          // Type checks
          if (property === 'toBeInstanceOf') {
            result.typeOnly = true;
          }
        }
      }
    }, path.scope);

    return result;
  }

  /**

   * Scan directory recursively for test files
   */
  scanDirectory(dir) {
    const files = fs.readdirSync(dir);

    files.forEach(file => {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);

      if (stat.isDirectory()) {
        this.scanDirectory(filePath);
      } else if (this.isTestFile(file)) {
        this.analyzeFile(filePath);
      }
    });
  }

  /**

   * Check if file is a test file
   */
  isTestFile(filename) {
    return /\.(test|spec)\.(js|ts|jsx|tsx)$/.test(filename);
  }

  /**

   * Generate markdown report
   */
  generateReport(outputPath) {
    const critical = this.issues.filter(i => i.severity === 'CRITICAL');
    const high = this.issues.filter(i => i.severity === 'HIGH');

    let report = `# Tautological Test Detection Report

## Summary
- **Total Issues:** ${this.issues.length}

- **Critical:** ${critical.length}

- **High:** ${high.length}

## Critical Issues (No Expectations)

`;

    critical.forEach(issue => {
      report += `### ${issue.file}:${issue.line} - ${issue.test}

- **Pattern:** ${issue.pattern}

- **Issue:** ${issue.issue}

`;
    });

    report += `\n## High Severity Issues (Weak Assertions)\n\n`;

    high.forEach(issue => {
      report += `### ${issue.file}:${issue.line} - ${issue.test}

- **Pattern:** ${issue.pattern}

- **Issue:** ${issue.issue}

`;
    });

    fs.writeFileSync(outputPath, report);
    console.log(`Report generated: ${outputPath}`);
  }
}

// CLI Usage
if (require.main === module) {
  const testDir = process.argv[2] || 'tests';

  console.log(`Scanning ${testDir} for tautological tests...`);

  const detector = new TautologicalTestDetector();
  detector.scanDirectory(testDir);
  detector.generateReport('tautological_tests_report.md');

  const criticalCount = detector.issues.filter(i => i.severity === 'CRITICAL').length;

  if (criticalCount > 0) {
    console.log(`\n❌ CRITICAL: ${criticalCount} tests with no expectations found`);
    process.exit(1);
  } else {
    console.log('\n✅ No critical tautological tests detected');
  }
}

module.exports = TautologicalTestDetector;
```

**Install Dependencies:**
```bash
npm install --save-dev @babel/parser @babel/traverse
```

**Run Detection:**
```bash
node ${OUTPUT_DIR}/templates/detectTautologicalTests.js tests/
```

### 1.2 Test Isolation Verification

**Validates:** Phase 2 (Unit Tests) - Test Independence

Verify that unit tests can run in any order without failures:

**Create:** `${OUTPUT_DIR}/templates/verifyTestIsolation.js`

```javascript
/**

 * Test Isolation Verifier
 *

 * Runs tests in multiple random orders to detect dependencies.
 */

const { execSync } = require('child_process');
const fs = require('fs');

class TestIsolationVerifier {
  constructor(testCommand = 'npm test') {
    this.testCommand = testCommand;
    this.results = [];
  }

  /**

   * Get all test file paths
   */
  getTestFiles() {
    try {
      // Use Jest's --listTests to get all test files
      const output = execSync('npm test -- --listTests', { encoding: 'utf-8' });
      return output.trim().split('\n');
    } catch (error) {
      console.error('Error getting test list:', error.message);
      return [];
    }
  }

  /**

   * Run tests in specified order
   */
  runTestsInOrder(testFiles) {
    try {
      // Run tests sequentially
      const command = `npm test -- ${testFiles.join(' ')} --runInBand`;
      execSync(command, { encoding: 'utf-8' });
      return { passed: true, output: '' };
    } catch (error) {
      return {
        passed: false,
        output: error.stdout || error.message
      };
    }
  }

  /**

   * Shuffle array in place
   */
  shuffle(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }

  /**

   * Verify test isolation by running tests in random orders
   */
  async verifyIsolation(iterations = 10) {
    console.log('Collecting test files...');
    const testFiles = this.getTestFiles();
    console.log(`Found ${testFiles.length} test files`);

    console.log(`\nRunning tests in ${iterations} random orders...`);

    for (let i = 0; i < iterations; i++) {
      process.stdout.write(`  Iteration ${i + 1}/${iterations}...`);

      const shuffled = this.shuffle(testFiles);
      const result = this.runTestsInOrder(shuffled);

      this.results.push({
        iteration: i + 1,
        passed: result.passed,
        output: result.output
      });

      console.log(result.passed ? ' ✅' : ' ❌');
    }

    return this.analyzeResults();
  }

  /**

   * Analyze verification results
   */
  analyzeResults() {
    const totalIterations = this.results.length;
    const passedCount = this.results.filter(r => r.passed).length;
    const failedCount = totalIterations - passedCount;
    const isolationScore = (passedCount / totalIterations) * 100;

    return {
      totalIterations,
      passedCount,
      failedCount,
      isolationScore,
      allPassed: failedCount === 0,
      failedIterations: this.results
        .filter(r => !r.passed)
        .map(r => r.iteration)
    };
  }

  /**

   * Generate isolation report
   */
  generateReport(analysis, outputPath) {
    let report = `# Test Isolation Verification Report

## Summary
- **Total Iterations:** ${analysis.totalIterations}

- **All Passed:** ${analysis.allPassed ? '✅ YES' : '❌ NO'}

- **Failed Iterations:** ${analysis.failedCount}

- **Isolation Score:** ${analysis.isolationScore.toFixed(1)}%

`;

    if (analysis.isolationScore === 100) {
      report += `## ✅ Perfect Isolation

All tests passed in every random order. Tests are properly isolated.

`;
    } else {
      report += `## ❌ Isolation Issues Detected

Tests failed in ${analysis.failedCount} out of ${analysis.totalIterations} random orders.

### Failed Iterations

`;
      analysis.failedIterations.forEach(iter => {
        report += `- Iteration ${iter}\n`;
      });

      report += `

### Recommended Actions

1. **Review test setup/teardown** - Ensure clean state between tests

2. **Check for shared resources** - Database, files, global state

3. **Verify mock cleanup** - Ensure mocks are restored after each test

4. **Use \`beforeEach\` and \`afterEach\`** - Properly initialize and clean up

5. **Run tests with \`--runInBand\`** - Identify parallel execution issues

`;
    }

    fs.writeFileSync(outputPath, report);
    console.log(`\nReport generated: ${outputPath}`);
  }
}

// CLI Usage
if (require.main === module) {
  const iterations = parseInt(process.argv[2]) || 10;

  const verifier = new TestIsolationVerifier();
  verifier.verifyIsolation(iterations).then(analysis => {
    verifier.generateReport(analysis, 'test_isolation_report.md');

    if (analysis.isolationScore < 100) {
      console.log(`\n❌ ISOLATION ISSUES: ${(100 - analysis.isolationScore).toFixed(1)}% failure rate`);
      process.exit(1);
    } else {
      console.log('\n✅ Perfect test isolation verified');
    }
  });
}

module.exports = TestIsolationVerifier;
```

**Run Isolation Verification:**
```bash
node ${OUTPUT_DIR}/templates/verifyTestIsolation.js 20
```

### 1.3 Over-Mocking Detection

**Validates:** Phase 2 (Unit Tests) - Mock Usage Patterns

Detect excessive mocking that prevents real code validation:

**Create:** `${OUTPUT_DIR}/templates/detectOverMocking.js`

```javascript
/**

 * Over-Mocking Detector
 *

 * Identifies tests with excessive mocking that may not validate real behavior.
 */

const fs = require('fs');
const path = require('path');
const { parse } = require('@babel/parser');
const traverse = require('@babel/traverse').default;

class OverMockingDetector {
  constructor() {
    this.results = [];
    this.currentFile = null;
  }

  /**

   * Analyze a test file for over-mocking
   */
  analyzeFile(filePath) {
    this.currentFile = filePath;
    const content = fs.readFileSync(filePath, 'utf-8');

    try {
      const ast = parse(content, {
        sourceType: 'module',
        plugins: ['typescript', 'jsx']
      });

      this.visitAST(ast);
    } catch (error) {
      console.error(`Error parsing ${filePath}:`, error.message);
    }
  }

  /**

   * Visit AST to analyze mocking patterns
   */
  visitAST(ast) {
    traverse(ast, {
      CallExpression: (path) => {
        const { node } = path;

        // Detect test functions
        if (this.isTestFunction(node)) {
          const testName = this.getTestName(node);
          const testFunction = node.arguments[1];

          if (!testFunction) return;

          const mockAnalysis = this.analyzeMockUsage(testFunction);

          if (mockAnalysis.severity) {
            this.results.push({
              file: this.currentFile,
              test: testName,
              line: node.loc.start.line,
              ...mockAnalysis
            });
          }
        }
      }
    });
  }

  /**

   * Analyze mock usage in a test function
   */
  analyzeMockUsage(testFunction) {
    const analysis = {
      mockCount: 0,
      spyCount: 0,
      mockFunctions: [],
      deepChains: [],
      directMockAssertions: []
    };

    traverse(testFunction, {
      CallExpression: (path) => {
        const { node } = path;
        const callee = node.callee;

        // Detect jest.mock()
        if (callee.type === 'MemberExpression' &&
            callee.object.name === 'jest' &&
            callee.property.name === 'mock') {
          analysis.mockCount++;
        }

        // Detect jest.fn()
        if (callee.type === 'MemberExpression' &&
            callee.object.name === 'jest' &&
            callee.property.name === 'fn') {
          analysis.mockCount++;
        }

        // Detect jest.spyOn()
        if (callee.type === 'MemberExpression' &&
            callee.object.name === 'jest' &&
            callee.property.name === 'spyOn') {
          analysis.spyCount++;
        }

        // Detect vi.mock() (Vitest)
        if (callee.type === 'MemberExpression' &&
            callee.object.name === 'vi' &&
            ['mock', 'fn', 'spyOn'].includes(callee.property.name)) {
          analysis.mockCount++;
        }

        // Detect sinon stubs
        if (callee.type === 'MemberExpression' &&
            callee.object.name === 'sinon' &&
            ['stub', 'spy', 'mock'].includes(callee.property.name)) {
          analysis.mockCount++;
        }
      },

      // Detect expectations on mock functions
      MemberExpression: (path) => {
        const { node } = path;
        const source = path.toString();

        if (source.includes('mockReturnValue') ||
            source.includes('mockResolvedValue')) {
          // Check if this mock return value is used in an assertion
          const parent = path.parent;
          if (parent.type === 'MemberExpression') {
            analysis.directMockAssertions.push(source);
          }
        }
      }
    }, path.scope);

    // Calculate severity
    const severity = this.calculateMockSeverity(analysis);

    return { ...analysis, severity };
  }

  /**

   * Calculate severity of mocking issues
   */
  calculateMockSeverity(analysis) {
    const totalMocks = analysis.mockCount + analysis.spyCount;

    // Critical: >5 mocks or direct mock assertions
    if (totalMocks > 5 || analysis.directMockAssertions.length > 0) {
      return 'CRITICAL';
    }

    // High: >3 mocks
    if (totalMocks > 3) {
      return 'HIGH';
    }

    // Medium: 2-3 mocks
    if (totalMocks >= 2) {
      return 'MEDIUM';
    }

    return null;
  }

  /**

   * Check if node is a test function
   */
  isTestFunction(node) {
    const callee = node.callee;
    if (callee.type === 'Identifier') {
      return ['it', 'test', 'specify'].includes(callee.name);
    }
    return false;
  }

  /**

   * Get test name from node
   */
  getTestName(node) {
    const firstArg = node.arguments[0];
    if (firstArg && firstArg.type === 'StringLiteral') {
      return firstArg.value;
    }
    return 'unnamed test';
  }

  /**

   * Scan directory for test files
   */
  scanDirectory(dir) {
    const files = fs.readdirSync(dir);

    files.forEach(file => {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);

      if (stat.isDirectory()) {
        this.scanDirectory(filePath);
      } else if (this.isTestFile(file)) {
        this.analyzeFile(filePath);
      }
    });
  }

  /**

   * Check if file is a test file
   */
  isTestFile(filename) {
    return /\.(test|spec)\.(js|ts|jsx|tsx)$/.test(filename);
  }

  /**

   * Generate over-mocking report
   */
  generateReport(outputPath) {
    const critical = this.results.filter(r => r.severity === 'CRITICAL');
    const high = this.results.filter(r => r.severity === 'HIGH');
    const medium = this.results.filter(r => r.severity === 'MEDIUM');

    let report = `# Over-Mocking Detection Report

## Summary
- **Total Tests Analyzed:** ${this.results.length}

- **Critical Issues:** ${critical.length}

- **High Issues:** ${high.length}

- **Medium Issues:** ${medium.length}

## Critical: Excessive Mocking

`;

    critical.forEach(result => {
      const totalMocks = result.mockCount + result.spyCount;
      report += `### ${result.file}:${result.line} - ${result.test}

- **Mock Count:** ${result.mockCount}

- **Spy Count:** ${result.spyCount}

- **Total:** ${totalMocks}

- **Direct Mock Assertions:** ${result.directMockAssertions.length}

`;
    });

    report += `

## Recommendations

### Replace Over-Mocking with Real Objects

**Bad (Over-Mocked):**
\`\`\`javascript
test('process data - over mocked', () => {
  const mockDb = jest.fn().mockReturnValue({ id: 1 });
  const mockApi = jest.fn().mockResolvedValue({ status: 'success' });
  const mockProcessor = jest.fn().mockReturnValue(100);
  const mockValidator = jest.fn().mockReturnValue(true);

  const result = service.process(mockDb, mockApi, mockProcessor, mockValidator);

  // Only validates mock values!
  expect(result).toEqual({ status: 'success' });
});
\`\`\`

**Good (Minimal Mocking):**
\`\`\`javascript
test('process data - minimal mocks', async () => {
  // Only mock external API
  const mockApi = jest.fn().mockResolvedValue({ status: 'success' });

  // Use real test database
  const testDb = await createTestDatabase();
  await testDb.users.create({ id: 1, name: 'Test' });

  // Use real service with real dependencies
  const service = new Service(testDb, mockApi);
  const result = await service.process(1);

  // Validate actual business logic
  expect(result.processed).toBe(true);
  expect(result.userId).toBe(1);
  expect(result.userName).toBe('Test');

  // Verify real database state
  const user = await testDb.users.findOne(1);
  expect(user.processedAt).toBeDefined();
});
\`\`\`

`;

    fs.writeFileSync(outputPath, report);
    console.log(`Report generated: ${outputPath}`);
  }
}

// CLI Usage
if (require.main === module) {
  const testDir = process.argv[2] || 'tests';

  console.log(`Scanning ${testDir} for over-mocking...`);

  const detector = new OverMockingDetector();
  detector.scanDirectory(testDir);
  detector.generateReport('over_mocking_report.md');

  const criticalCount = detector.results.filter(r => r.severity === 'CRITICAL').length;

  if (criticalCount > 0) {
    console.log(`\n❌ CRITICAL: ${criticalCount} tests with excessive mocking`);
    process.exit(1);
  } else {
    console.log('\n✅ No critical over-mocking detected');
  }
}

module.exports = OverMockingDetector;
```

**Run Over-Mocking Detection:**
```bash
node ${OUTPUT_DIR}/templates/detectOverMocking.js tests/
```

---

## Phase 2: Mutation Testing with Stryker

**Validates:** Phase 7 (Code Coverage)

### 2.1 Stryker Setup

**Install Stryker:**
```bash
npm install --save-dev @stryker-mutator/core
npm install --save-dev @stryker-mutator/jest-runner
npm install --save-dev @stryker-mutator/typescript-checker
```

**Create Configuration:** `stryker.conf.json`

```json
{
  "$schema": "./node_modules/@stryker-mutator/core/schema/stryker-schema.json",
  "packageManager": "npm",
  "reporters": ["html", "clear-text", "progress", "dashboard"],
  "testRunner": "jest",
  "jest": {
    "projectType": "custom",
    "config": {
      "testEnvironment": "node"
    }
  },
  "coverageAnalysis": "perTest",
  "mutate": [
    "src/**/*.ts",
    "src/**/*.js",
    "!src/**/*.spec.ts",
    "!src/**/*.test.js"
  ],
  "thresholds": {
    "high": 90,
    "low": 80,
    "break": 75
  },
  "timeoutMS": 60000,
  "concurrency": 4,
  "checkers": ["typescript"],
  "tsconfigFile": "tsconfig.json"
}
```

**Run Mutation Testing:**
```bash
# Run on entire codebase
npx stryker run

# Run on specific file
npx stryker run --mutate "src/calculator.ts"

# Generate report
npx stryker run --reporters html,dashboard
```

### 2.2 Mutation Score Analysis

**Interpret Stryker Results:**

```
Mutation score: 82.5%
Killed: 165/200
Survived: 25/200
Timeout: 8/200
No Coverage: 2/200
```

**Severity Classification:**

- **Survived (Critical):** Mutations not caught by tests

- **No Coverage (Critical):** Code not executed by any test

- **Timeout (Medium):** Tests running too long

- **Killed (Good):** Tests successfully caught mutations

### 2.3 Analyzing Survived Mutations

For each survived mutation, generate detailed analysis:

**Example Mutation Report:**

```markdown
### Mutation #42: SURVIVED

**File:** src/calculator.ts:15
**Operator:** Arithmetic
**Original:** `return price * (1 - discount)`
**Mutated:** `return price * (1 + discount)`
**Status:** SURVIVED ❌

#### Why This Is Critical
This mutation reverses the discount logic but tests still pass, indicating:

1. No test validates the actual discount calculation

2. Tests may be checking mock return values only

3. Assertions are too weak (e.g., toBeDefined() only)

#### Current Weak Test
\`\`\`typescript
test('calculate discount', () => {
  const result = calculateDiscount(100, 0.1);
  expect(result).toBeDefined(); // ❌ Too weak!
  expect(typeof result).toBe('number'); // ❌ Type check only!
});
\`\`\`

#### Strong Test That Would Catch This
\`\`\`typescript
test('calculate discount correctly', () => {
  // Exact value validation
  expect(calculateDiscount(100, 0.1)).toBe(90);
  expect(calculateDiscount(100, 0)).toBe(100);
  expect(calculateDiscount(100, 0.5)).toBe(50);

  // Edge cases
  expect(calculateDiscount(0, 0.1)).toBe(0);
  expect(calculateDiscount(100, 1)).toBe(0);
});
\`\`\`
```

### 2.4 Mutation Coverage Heatmap

Generate visualization showing mutation scores by module:

```javascript
// ${OUTPUT_DIR}/templates/generateMutationHeatmap.js
const fs = require('fs');

function generateHeatmap(mutationReport) {
  const modules = {};

  // Parse Stryker report
  mutationReport.files.forEach(file => {
    const module = file.path.split('/')[1]; // e.g., 'core' from 'src/core/calculator.ts'

    if (!modules[module]) {
      modules[module] = { total: 0, killed: 0 };
    }

    modules[module].total += file.mutants.length;
    modules[module].killed += file.mutants.filter(m => m.status === 'Killed').length;
  });

  // Calculate scores
  const heatmap = Object.keys(modules).map(module => {
    const { total, killed } = modules[module];
    const score = (killed / total) * 100;

    return {
      module,
      score: score.toFixed(1),
      status: score >= 90 ? '✅' : score >= 80 ? '⚠️' : '❌'
    };
  });

  return heatmap;
}
```

---

## Phase 3: Integration & E2E Test Quality

**Validates:** Phase 3 (Test Cases)

### 3.1 Real Dependency Validation

Check integration tests use real dependencies:

```javascript
// Detection criteria for integration tests
const integrationTestChecks = {
  usesRealDatabase: (test) => {
    // Check for real DB setup, not mocks
    return !test.includes('jest.mock') && test.includes('database.connect');
  },

  usesRealAPI: (test) => {
    // Check for real HTTP requests
    return test.includes('supertest') || test.includes('axios') && !test.includes('mock');
  },

  hasProperCleanup: (test) => {
    // Check for afterEach/afterAll cleanup
    return test.includes('afterEach') || test.includes('afterAll');
  }
};
```

### 3.2 Workflow Completeness Check

Verify E2E tests cover complete user workflows:

**Weak E2E Test:**
```javascript
test('user registration - incomplete', async () => {
  const response = await request(app)
    .post('/api/register')
    .send({ email: 'test@example.com', password: 'pass123' });

  expect(response.status).toBe(200);
  // Missing: email verification, login flow, error cases
});
```

**Strong E2E Test:**
```javascript
describe('complete user registration flow', () => {
  test('successful registration and login', async () => {
    // Step 1: Register
    const registerResponse = await request(app)
      .post('/api/register')
      .send({
        email: 'newuser@example.com',
        password: 'SecurePass123!',
        name: 'New User'
      });

    expect(registerResponse.status).toBe(201);
    expect(registerResponse.body.message).toContain('verification email sent');

    // Step 2: Verify email
    const token = await getVerificationToken('newuser@example.com');
    const verifyResponse = await request(app)
      .get(`/api/verify/${token}`);

    expect(verifyResponse.status).toBe(200);

    // Step 3: Login with verified account
    const loginResponse = await request(app)
      .post('/api/login')
      .send({
        email: 'newuser@example.com',
        password: 'SecurePass123!'
      });

    expect(loginResponse.status).toBe(200);
    expect(loginResponse.body.token).toBeDefined();
    expect(loginResponse.body.user.emailVerified).toBe(true);
  });

  test('registration with existing email fails', async () => {
    // Error path: duplicate registration
    const response = await request(app)
      .post('/api/register')
      .send({
        email: 'newuser@example.com', // Already registered
        password: 'pass123'
      });

    expect(response.status).toBe(409);
    expect(response.body.error).toContain('already exists');
  });
});
```

---

## Phase 4: CI/CD Pipeline Validation

**Validates:** Phase 6 (Maintenance & CI/CD)

### 4.1 Flaky Test Detection

**Create:** `${OUTPUT_DIR}/templates/detectFlakyTests.js`

```javascript
/**

 * Flaky Test Detector
 *

 * Runs test suite multiple times to identify inconsistent tests.
 */

const { execSync } = require('child_process');
const fs = require('fs');

class FlakyTestDetector {
  constructor(testCommand = 'npm test') {
    this.testCommand = testCommand;
    this.results = new Map();
  }

  /**

   * Run test suite multiple times
   */
  async runMultipleIterations(iterations = 20) {
    console.log(`Running test suite ${iterations} times...`);

    for (let i = 0; i < iterations; i++) {
      console.log(`Iteration ${i + 1}/${iterations}`);

      try {
        const output = execSync(`${this.testCommand} --json --outputFile=test-results-${i}.json`, {
          encoding: 'utf-8'
        });

        this.parseResults(`test-results-${i}.json`);
      } catch (error) {
        // Test failures are expected for flaky tests
        this.parseResults(`test-results-${i}.json`);
      }
    }

    return this.analyzeResults(iterations);
  }

  /**

   * Parse test results JSON
   */
  parseResults(filename) {
    try {
      const data = JSON.parse(fs.readFileSync(filename, 'utf-8'));

      data.testResults.forEach(testFile => {
        testFile.assertionResults.forEach(test => {
          const testId = `${testFile.name}::${test.title}`;

          if (!this.results.has(testId)) {
            this.results.set(testId, { passed: 0, failed: 0 });
          }

          const stats = this.results.get(testId);
          if (test.status === 'passed') {
            stats.passed++;
          } else {
            stats.failed++;
          }
        });
      });

      // Clean up
      fs.unlinkSync(filename);
    } catch (error) {
      console.error(`Error parsing ${filename}:`, error.message);
    }
  }

  /**

   * Analyze results to identify flaky tests
   */
  analyzeResults(iterations) {
    const flakyTests = [];

    this.results.forEach((stats, testId) => {
      const total = stats.passed + stats.failed;
      const failureRate = stats.failed / total;

      // Flaky: fails sometimes but not always
      if (failureRate > 0 && failureRate < 1.0) {
        flakyTests.push({
          test: testId,
          passed: stats.passed,
          failed: stats.failed,
          total,
          failureRate: failureRate * 100,
          severity: failureRate > 0.3 ? 'CRITICAL' : 'HIGH'
        });
      }
    });

    return flakyTests.sort((a, b) => b.failureRate - a.failureRate);
  }

  /**

   * Generate flaky test report
   */
  generateReport(flakyTests, outputPath) {
    const critical = flakyTests.filter(t => t.severity === 'CRITICAL');
    const high = flakyTests.filter(t => t.severity === 'HIGH');

    let report = `# Flaky Test Detection Report

## Summary
- **Total Flaky Tests:** ${flakyTests.length}

- **Critical (>30% failure rate):** ${critical.length}

- **High (10-30% failure rate):** ${high.length}

## Flaky Tests

`;

    flakyTests.forEach(test => {
      report += `### ${test.test}

- **Failure Rate:** ${test.failureRate.toFixed(1)}%

- **Passed:** ${test.passed}/${test.total}

- **Failed:** ${test.failed}/${test.total}

- **Severity:** ${test.severity}

`;
    });

    report += `

## Common Causes of Flaky Tests in JavaScript

1. **Async/Await Issues**

   - Missing await keywords

   - Race conditions in async operations

   - Improper promise handling

2. **Timing Dependencies**

   - setTimeout/setInterval without proper control

   - Animation or debounce logic

   - Network request timing

3. **Shared State**

   - Global variables not cleaned up

   - Module-level state

   - Jest's module caching

4. **External Dependencies**

   - Real HTTP requests

   - File system operations

   - Date/time dependencies

## Remediation Steps

\`\`\`javascript
// Bad: Timing-dependent
test('flaky animation test', async () => {
  startAnimation();
  await wait(100); // Flaky: might not be enough time
  expect(isAnimationComplete()).toBe(true);
});

// Good: Event-driven
test('stable animation test', async () => {
  const animation = startAnimation();
  await animation.waitForCompletion({ timeout: 5000 });
  expect(animation.isComplete()).toBe(true);
});

// Bad: Shared state
let userData; // Module-level variable

test('test 1', () => {
  userData = { id: 1 };
  expect(processUser(userData)).toBe(true);
});

test('test 2', () => {
  // Depends on userData from test 1! Flaky!
  expect(userData.id).toBe(1);
});

// Good: Isolated state
test('test 1', () => {
  const userData = { id: 1 };
  expect(processUser(userData)).toBe(true);
});

test('test 2', () => {
  const userData = { id: 2 };
  expect(processUser(userData)).toBe(true);
});
\`\`\`
`;

    fs.writeFileSync(outputPath, report);
    console.log(`Report generated: ${outputPath}`);
  }
}

// CLI Usage
if (require.main === module) {
  const iterations = parseInt(process.argv[2]) || 20;

  const detector = new FlakyTestDetector();
  detector.runMultipleIterations(iterations).then(flakyTests => {
    detector.generateReport(flakyTests, 'flaky_tests_report.md');

    if (flakyTests.length > 0) {
      console.log(`\n❌ FLAKY TESTS DETECTED: ${flakyTests.length} inconsistent tests`);
      process.exit(1);
    } else {
      console.log('\n✅ No flaky tests detected');
    }
  });
}

module.exports = FlakyTestDetector;
```

**Run Flaky Test Detection:**
```bash
node ${OUTPUT_DIR}/templates/detectFlakyTests.js 50
```

---

## Weak vs. Strong Test Examples

### Example 1: Async/Await Issues

**❌ Weak (Missing await):**
```javascript
test('fetch user data - weak', () => {
  const user = fetchUser(1); // Missing await!
  expect(user).toBeDefined(); // Always passes, even if fetch fails
});
```

**✅ Strong:**
```javascript
test('fetch user data - strong', async () => {
  const user = await fetchUser(1);

  expect(user).toEqual({
    id: 1,
    name: 'John Doe',
    email: 'john@example.com'
  });
});
```

### Example 2: Promise Handling

**❌ Weak (Not returning promise):**
```javascript
test('async operation - weak', () => {
  asyncOperation().then(result => {
    expect(result).toBe(true); // May not run before test completes
  });
});
```

**✅ Strong:**
```javascript
test('async operation - strong', async () => {
  const result = await asyncOperation();
  expect(result).toBe(true);
});

// Or with explicit promise return
test('async operation - strong (alternative)', () => {
  return asyncOperation().then(result => {
    expect(result).toBe(true);
  });
});
```

### Example 3: Mock Return Values

**❌ Weak (Testing mock values):**
```javascript
test('process user - weak', () => {
  const mockDb = jest.fn().mockReturnValue({ id: 1, name: 'Mock User' });

  const service = new UserService(mockDb);
  const user = service.getUser(1);

  // Only validates mock return value!
  expect(user.name).toBe('Mock User');
});
```

**✅ Strong:**
```javascript
test('process user - strong', async () => {
  // Use real test database
  const testDb = await createTestDb();
  await testDb.users.create({ id: 1, name: 'Real User', email: 'real@test.com' });

  const service = new UserService(testDb);
  const user = await service.getUser(1);

  // Validates actual business logic
  expect(user.id).toBe(1);
  expect(user.name).toBe('Real User');
  expect(user.email).toBe('real@test.com');
  expect(user.isActive).toBe(true);
});
```

### Example 4: Timing Dependencies

**❌ Weak (Flaky timing):**
```javascript
test('debounced search - weak', async () => {
  const search = createDebouncedSearch(100);

  search('query');
  await wait(50); // Flaky: might not be enough

  expect(search.hasResults()).toBe(true);
});
```

**✅ Strong:**
```javascript
test('debounced search - strong', async () => {
  jest.useFakeTimers();

  const search = createDebouncedSearch(100);
  search('query');

  // Fast-forward time
  jest.advanceTimersByTime(100);
  await Promise.resolve(); // Let promises resolve

  expect(search.hasResults()).toBe(true);

  jest.useRealTimers();
});
```

### Example 5: Snapshot Testing Misuse

**❌ Weak (Brittle snapshot):**
```javascript
test('render component - weak', () => {
  const { container } = render(<UserProfile user={mockUser} />);
  expect(container).toMatchSnapshot(); // Breaks on any CSS change
});
```

**✅ Strong:**
```javascript
test('render component - strong', () => {
  const user = { id: 1, name: 'John', role: 'admin' };
  const { getByText, getByRole } = render(<UserProfile user={user} />);

  // Test specific, meaningful content
  expect(getByText('John')).toBeInTheDocument();
  expect(getByRole('button', { name: 'Edit Profile' })).toBeInTheDocument();

  // If snapshot needed, use inline snapshots for specific parts
  expect(getByRole('heading')).toMatchInlineSnapshot(`
    <h1>
      John
      <span class="badge">admin</span>
    </h1>
  `);
});
```

### Example 6: Error Path Coverage

**❌ Weak (Happy path only):**
```javascript
test('divide numbers - weak', () => {
  expect(divide(10, 2)).toBe(5);
});
```

**✅ Strong:**
```javascript
describe('divide numbers - strong', () => {
  test('valid division', () => {
    expect(divide(10, 2)).toBe(5);
    expect(divide(20, 4)).toBe(5);
    expect(divide(0, 5)).toBe(0);
  });

  test('division by zero throws error', () => {
    expect(() => divide(10, 0)).toThrow('Division by zero');
  });

  test('invalid inputs throw TypeError', () => {
    expect(() => divide('10', 2)).toThrow(TypeError);
    expect(() => divide(10, '2')).toThrow(TypeError);
    expect(() => divide(null, 2)).toThrow(TypeError);
  });

  test('decimal division', () => {
    expect(divide(1, 3)).toBeCloseTo(0.333, 2);
    expect(divide(10, 3)).toBeCloseTo(3.333, 2);
  });
});
```

### Example 7: React Component Testing

**❌ Weak (Testing implementation details):**
```javascript
test('counter component - weak', () => {
  const wrapper = shallow(<Counter />);

  // Testing internal state (implementation detail)
  expect(wrapper.state('count')).toBe(0);

  wrapper.instance().increment(); // Accessing instance methods
  expect(wrapper.state('count')).toBe(1);
});
```

**✅ Strong (Testing user behavior):**
```javascript
test('counter component - strong', () => {
  const { getByText, getByRole } = render(<Counter />);

  // Test what user sees
  expect(getByText('Count: 0')).toBeInTheDocument();

  // Test user interaction
  const incrementButton = getByRole('button', { name: 'Increment' });
  fireEvent.click(incrementButton);

  // Verify user-visible outcome
  expect(getByText('Count: 1')).toBeInTheDocument();
});
```

### Example 8: API Mock Realism

**❌ Weak (Unrealistic mock):**
```javascript
test('fetch user API - weak', async () => {
  global.fetch = jest.fn().mockResolvedValue({
    json: () => ({ id: 1 }) // Oversimplified mock
  });

  const user = await fetchUser(1);
  expect(user.id).toBe(1);
});
```

**✅ Strong (Realistic mock):**
```javascript
test('fetch user API - strong', async () => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    status: 200,
    headers: new Headers({
      'content-type': 'application/json'
    }),
    json: async () => ({
      id: 1,
      name: 'John Doe',
      email: 'john@example.com',
      createdAt: '2024-01-01T00:00:00Z'
    })
  });

  const user = await fetchUser(1);

  expect(user).toEqual({
    id: 1,
    name: 'John Doe',
    email: 'john@example.com',
    createdAt: expect.any(String)
  });

  expect(fetch).toHaveBeenCalledWith(
    'https://api.example.com/users/1',
    expect.objectContaining({
      method: 'GET',
      headers: expect.any(Object)
    })
  );
});

test('fetch user API error - strong', async () => {
  global.fetch = jest.fn().mockRejectedValue(
    new Error('Network error')
  );

  await expect(fetchUser(1)).rejects.toThrow('Network error');
});
```

### Example 9: Test Data Quality

**❌ Weak (Unrealistic data):**
```javascript
test('validate user input - weak', () => {
  const input = {
    name: 'a', // Too short
    email: 't@t', // Invalid
    age: 999 // Unrealistic
  };

  // This passes but doesn't test real scenarios
  expect(validateUser(input)).toBeDefined();
});
```

**✅ Strong (Realistic data):**
```javascript
describe('validate user input - strong', () => {
  test('valid user data', () => {
    const input = {
      name: 'John Smith',
      email: 'john.smith@company.com',
      age: 32,
      phone: '+1-555-123-4567'
    };

    const result = validateUser(input);
    expect(result.valid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test('invalid email format', () => {
    const input = {
      name: 'John Smith',
      email: 'invalid-email',
      age: 32
    };

    const result = validateUser(input);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Invalid email format');
  });

  test('age out of range', () => {
    const input = {
      name: 'John Smith',
      email: 'john@example.com',
      age: 150
    };

    const result = validateUser(input);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Age must be between 0 and 120');
  });
});
```

### Example 10: Module Mocking

**❌ Weak (Over-mocked module):**
```javascript
jest.mock('../services/UserService');
jest.mock('../services/EmailService');
jest.mock('../services/DatabaseService');
jest.mock('../services/CacheService');

test('registration - weak', () => {
  // Everything is mocked, not testing real integration
  const result = registerUser(userData);
  expect(result).toBe(true);
});
```

**✅ Strong (Selective mocking):**
```javascript
// Only mock external services
jest.mock('../services/EmailService');

test('registration - strong', async () => {
  // Use real database (test instance)
  const testDb = await createTestDatabase();

  // Use real user service
  const userService = new UserService(testDb);

  // Only email service is mocked (external dependency)
  const mockEmailService = require('../services/EmailService');
  mockEmailService.send.mockResolvedValue({ sent: true });

  // Test real integration
  const result = await registerUser({
    email: 'newuser@example.com',
    password: 'SecurePass123!',
    name: 'New User'
  }, userService, mockEmailService);

  // Verify real database interaction
  const savedUser = await testDb.users.findByEmail('newuser@example.com');
  expect(savedUser).toBeDefined();
  expect(savedUser.name).toBe('New User');

  // Verify email was sent
  expect(mockEmailService.send).toHaveBeenCalledWith(
    'newuser@example.com',
    expect.objectContaining({
      subject: 'Welcome'
    })
  );
});
```

---

## Continuous Monitoring Setup

**Create:** `${OUTPUT_DIR}/templates/continuousMonitoringSetup.sh`

```bash
#!/bin/bash
# Continuous Test Quality Monitoring for JavaScript/TypeScript

set -e

echo "Setting up continuous test quality monitoring..."

# Create monitoring directory
mkdir -p test_quality_monitoring

# Install dependencies
npm install --save-dev @stryker-mutator/core @babel/parser @babel/traverse

# Create daily mutation testing job
cat > test_quality_monitoring/daily_mutation_test.sh <<'EOF'
#!/bin/bash
DATE=$(date +%Y-%m-%d)
OUTPUT_DIR="mutation_reports/$DATE"
mkdir -p "$OUTPUT_DIR"

echo "Running mutation testing..."
npx stryker run --reporters html,json

# Extract mutation score
SCORE=$(node -e "const report = require('./reports/mutation/mutation.json'); console.log(report.mutationScore);")

echo "Mutation Score: $SCORE" > "$OUTPUT_DIR/score.txt"

# Alert if score drops below threshold
THRESHOLD=80
if (( $(echo "$SCORE < $THRESHOLD" | bc -l) )); then
  echo "⚠️  ALERT: Mutation score $SCORE below threshold $THRESHOLD"
fi
EOF

chmod +x test_quality_monitoring/daily_mutation_test.sh

# Create weekly quality report
cat > test_quality_monitoring/weekly_quality_report.sh <<'EOF'
#!/bin/bash
DATE=$(date +%Y-%m-%d)
OUTPUT_DIR="quality_reports/$DATE"
mkdir -p "$OUTPUT_DIR"

echo "Running comprehensive quality analysis..."

node templates/detectTautologicalTests.js tests/ > "$OUTPUT_DIR/tautological.txt"
node templates/verifyTestIsolation.js 20 > "$OUTPUT_DIR/isolation.txt"
node templates/detectOverMocking.js tests/ > "$OUTPUT_DIR/mocking.txt"
node templates/detectFlakyTests.js 50 > "$OUTPUT_DIR/flaky.txt"

echo "✅ Weekly quality report generated in $OUTPUT_DIR"
EOF

chmod +x test_quality_monitoring/weekly_quality_report.sh

echo "✅ Continuous monitoring setup complete!"
echo ""
echo "Add to package.json scripts:"
echo '  "test:mutation": "stryker run"'
echo '  "test:quality": "node templates/detectTautologicalTests.js tests/"'
echo '  "test:flaky": "node templates/detectFlakyTests.js 20"'
```

**Run Setup:**
```bash
bash ${OUTPUT_DIR}/templates/continuousMonitoringSetup.sh
```

---

## Success Criteria

After completing this reward hacking validation phase:

- [ ] Overall test quality score >80/100

- [ ] Mutation score >80% across all modules

- [ ] Zero critical reward hacking incidents

- [ ] <5% high severity issues

- [ ] 100% test independence verified

- [ ] <2% flaky test rate

- [ ] Continuous monitoring configured with Stryker

- [ ] Team trained on strong test patterns

- [ ] CI/CD quality gates active

- [ ] Regular audit schedule established

---

**This template validates all 7 previous testing phases and provides comprehensive test quality assurance for JavaScript/TypeScript applications using Jest, Mocha, and Stryker mutation testing.**
