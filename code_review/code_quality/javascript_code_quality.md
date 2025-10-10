# JavaScript Code Quality Review

## Objective
Systematically evaluate code maintainability, readability, and adherence to JavaScript best practices. Identify technical debt, complexity hotspots, and areas requiring refactoring to improve long-term codebase health.

## Output Directory Structure

All outputs should be saved in organized directories:

```
review/code_quality/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `review/code_quality/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Review Checklist

### Coding Standards

- [ ] ESLint rules compliance verified

- [ ] Code formatting consistent (Prettier or similar)

- [ ] Import organization follows standard order

- [ ] Naming conventions consistent (camelCase, PascalCase, UPPER_CASE)

- [ ] JSDoc or TypeScript type annotations used appropriately

### Code Complexity

- [ ] Functions under 50 lines (flagged if exceeded)

- [ ] Cyclomatic complexity under 10 per function

- [ ] Nesting depth under 4 levels

- [ ] Class/Component size reasonable (<300 lines)

- [ ] Module cohesion evaluated

### Design & Architecture

- [ ] SOLID principles followed

- [ ] DRY principle applied (no significant duplication)

- [ ] Separation of concerns maintained

- [ ] Appropriate use of design patterns

- [ ] Proper use of async/await patterns

### Code Smells

- [ ] Long parameter lists identified (>5 parameters)

- [ ] Callback hell or promise chains flagged

- [ ] Large objects or closures identified

- [ ] God components or modules identified

- [ ] Dead code marked for removal

### Error Handling

- [ ] Errors caught at appropriate level

- [ ] Specific error types used

- [ ] Error messages informative

- [ ] Promises properly handled (no unhandled rejections)

- [ ] Logging appropriate for debugging

### Maintainability

- [ ] Code self-documenting with clear names

- [ ] Comments explain "why" not "what"

- [ ] Magic numbers replaced with named constants

- [ ] Configuration externalized

- [ ] Hardcoded values eliminated

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# JavaScript Code Quality Review

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="review/code_quality"
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

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Review Protocol

Please perform a comprehensive code quality review of this JavaScript project following this protocol:

## Phase 1: Coding Standards Assessment

1. **ESLint Compliance Check**
   ```bash
   # Run ESLint
   npx eslint . --ext .js,.jsx,.ts,.tsx

   # Generate report
   npx eslint . --ext .js,.jsx,.ts,.tsx --format json --output-file eslint-report.json

   # Check for auto-fixable issues
   npx eslint . --ext .js,.jsx,.ts,.tsx --fix-dry-run
   ```

2. **Formatting Consistency**
   ```bash
   # Check Prettier formatting
   npx prettier --check "src/**/*.{js,jsx,ts,tsx}"

   # Or run format check
   npm run format:check
   ```

3. **Style Violations Analysis**
   - Document most common violations
   - Identify patterns of non-compliance
   - Assess consistency across modules
   - Flag formatting inconsistencies

4. **Naming Convention Review**
   - Verify function names are descriptive and camelCase
   - Check class/component names use PascalCase
   - Confirm constants use UPPER_CASE or descriptive names
   - Identify unclear or abbreviated names
   - Check for Hungarian notation or other anti-patterns

## Phase 2: Complexity Analysis

1. **Function-Level Complexity**
   ```bash
   # Calculate cyclomatic complexity
   npx complexity-report src/ --format json

   # Or use escomplex
   npx escomplex src/**/*.js --format json

   # Or use plato for visual report
   npx plato -r -d report src/
   ```

2. **Identify Complexity Hotspots**
   - List functions with complexity >10
   - Flag functions longer than 50 lines
   - Identify deeply nested code (>4 levels)
   - Document complex conditional logic
   - Find excessive use of ternary operators

3. **Module-Level Analysis**
   - Assess module size and cohesion
   - Identify modules with too many responsibilities
   - Check coupling between modules
   - Evaluate package organization
   - Identify circular dependencies

## Phase 3: Design Quality Review

1. **SOLID Principles**
   - **Single Responsibility**: Check if classes/functions have one clear purpose
   - **Open/Closed**: Evaluate extensibility without modification
   - **Liskov Substitution**: Review inheritance hierarchies (if applicable)
   - **Interface Segregation**: Check for lean interfaces
   - **Dependency Inversion**: Assess dependency on abstractions

2. **DRY Violations**
   ```bash
   # Check for code duplication
   npx jscpd src/ --min-lines 5 --min-tokens 50

   # Generate HTML report
   npx jscpd src/ --format html -o ./duplication-report
   ```
   - Identify duplicated logic
   - Find near-duplicate functions
   - Document consolidation opportunities
   - Check for repeated patterns

3. **Design Patterns**
   - Identify patterns in use (Factory, Observer, Module, etc.)
   - Assess pattern appropriateness
   - Flag pattern misuse or over-engineering
   - Suggest beneficial pattern applications

## Phase 4: Code Smell Detection

1. **Common JavaScript Code Smells**
   - **Long Parameter Lists**: Functions with >5 parameters
   - **Long Functions**: Functions exceeding 50 lines
   - **Large Classes/Components**: Classes with >300 lines or >20 methods
   - **Callback Hell**: Deep nesting of callbacks
   - **Promise Chains**: Excessive .then() chaining
   - **Data Clumps**: Same groups of data appearing together

2. **Anti-Patterns**
   ```javascript
   // Search for common anti-patterns:

   // 1. Modifying parameters
   function bad(obj) {
       obj.property = "modified"; // BAD: mutates input
   }

   // 2. Callback hell
   getData(function(a) {
       getMoreData(a, function(b) {
           getMoreData(b, function(c) {
               // BAD: pyramid of doom
           });
       });
   });

   // 3. Unhandled promise rejections
   promise.then(result => {
       // BAD: no .catch()
   });

   // 4. Using var instead of let/const
   var x = 10; // BAD: use let or const

   // 5. Not using strict mode
   // Missing: 'use strict';

   // 6. Modifying built-in prototypes
   Array.prototype.myMethod = function() {}; // BAD

   // 7. Using eval or Function constructor
   eval(userInput); // DANGEROUS
   new Function(code); // DANGEROUS
   ```

3. **JavaScript-Specific Issues**
   - Using `==` instead of `===`
   - Implicit type coercion issues
   - Scope issues (var hoisting, closure problems)
   - `this` binding confusion
   - Missing `await` on promises
   - Unhandled async errors
   - Memory leaks (event listeners, timers, closures)

## Phase 5: Error Handling & Robustness

1. **Exception Handling Review**
   ```javascript
   // Check for proper error handling patterns:

   // Good: Async/await with try-catch
   async function good() {
       try {
           const result = await asyncOperation();
           return result;
       } catch (error) {
           logger.error('Operation failed:', error);
           throw new CustomError('Failed', error);
       }
   }

   // Good: Promise with .catch()
   promise
       .then(result => process(result))
       .catch(error => handleError(error));

   // Bad: Unhandled promise
   async function bad() {
       const result = await asyncOperation(); // No try-catch!
       return result;
   }
   ```

2. **Promise & Async/Await Review**
   - Check for unhandled promise rejections
   - Verify proper use of async/await
   - Look for missing `await` keywords
   - Check for unnecessary `await` (sequential vs parallel)
   - Review error propagation in async code

3. **Defensive Programming**
   - Input validation assessed
   - Boundary condition handling reviewed
   - Edge case coverage evaluated
   - Null/undefined checks where appropriate
   - Type checking (especially in non-TypeScript projects)

## Phase 6: Documentation Quality

1. **JSDoc Coverage**
   ```bash
   # Check JSDoc coverage
   npx documentation lint src/**/*.js

   # Generate documentation
   npx documentation build src/** -f html -o docs
   ```
   - Measure function/class JSDoc presence
   - Assess JSDoc completeness (@param, @returns, @throws)
   - Verify parameter documentation accuracy
   - Check return value documentation

2. **Comment Quality**
   - Evaluate comment necessity and clarity
   - Flag commented-out code for removal
   - Check for TODO/FIXME/HACK comments
   - Verify comments explain "why" not "what"
   - Look for outdated comments

3. **Type Annotations** (TypeScript)
   ```bash
   # Check TypeScript strict mode compliance
   npx tsc --noEmit --strict

   # Check for any usage
   npx tsc --noEmit --noImplicitAny
   ```
   - Assess type annotation coverage
   - Verify type accuracy
   - Check for `any` overuse
   - Review complex type definitions

## Phase 7: Modern JavaScript Best Practices

1. **ES6+ Features Usage**
   ```javascript
   // Prefer modern JavaScript features:

   // ✓ Good: Arrow functions (when appropriate)
   const map = items.map(item => item.value);

   // ✓ Good: Destructuring
   const { name, email } = user;
   const [first, ...rest] = array;

   // ✓ Good: Template literals
   const message = `Hello, ${name}!`;

   // ✓ Good: Spread operator
   const merged = { ...defaults, ...options };

   // ✓ Good: Optional chaining
   const value = obj?.property?.nested;

   // ✓ Good: Nullish coalescing
   const result = value ?? defaultValue;

   // ✗ Bad: Old patterns
   var that = this; // Use arrow functions
   var fullName = firstName + ' ' + lastName; // Use template literals
   ```

2. **Async Patterns**
   ```javascript
   // Good: Parallel async operations
   const [result1, result2] = await Promise.all([
       fetchData1(),
       fetchData2()
   ]);

   // Bad: Sequential when not needed
   const result1 = await fetchData1();
   const result2 = await fetchData2(); // Could be parallel!
   ```

3. **Functional Programming Patterns**
   - Prefer immutability
   - Use array methods (map, filter, reduce) over loops
   - Avoid side effects in functions
   - Use pure functions where possible

## Phase 8: Framework-Specific Quality (if applicable)

### React-Specific

- [ ] Proper use of hooks (rules of hooks)

- [ ] Unnecessary re-renders minimized

- [ ] Key props used correctly in lists

- [ ] Side effects managed with useEffect

- [ ] Custom hooks follow naming conventions

- [ ] PropTypes or TypeScript for props validation

### Vue-Specific

- [ ] Proper reactivity patterns

- [ ] Computed properties used appropriately

- [ ] Component lifecycle understood

- [ ] Props validation implemented

- [ ] Event handling follows conventions

### Node.js/Express-Specific

- [ ] Proper middleware usage

- [ ] Error handling middleware present

- [ ] Async error handling (use async wrapper or try-catch)

- [ ] Request validation implemented

- [ ] Proper use of async/await in routes

## Output Format

Please provide a comprehensive quality report with the following structure:

### Executive Summary

- **Overall Quality Score**: [A-F grade]

- **Maintainability Index**: [score if available]

- **Average Complexity**: [cyclomatic complexity]

- **Critical Issues**: [count]

- **Technical Debt**: [estimated hours to address]

### Coding Standards Compliance

- **ESLint Violations**: [count and severity breakdown]

- **Most Common Issues**:
  1. [Issue type] - [count] occurrences
  2. [Issue type] - [count] occurrences
  3. [Issue type] - [count] occurrences

- **Consistency Score**: [percentage]

- **Auto-fixable Issues**: [count]

### Complexity Analysis
**High Complexity Functions** (Cyclomatic Complexity >10):
| Function | File | Complexity | Lines | Recommendation |
|----------|------|------------|-------|----------------|
| [name] | [path] | [score] | [count] | [refactor suggestion] |

**Large Files/Modules** (>300 lines):
| Module | Lines | Functions | Complexity | Recommendation |
|--------|-------|-----------|------------|----------------|
| [path] | [count] | [count] | [avg] | [split suggestion] |

### Design Quality Issues
1. **SOLID Violations**:
   - [Principle]: [specific examples and impact]

2. **DRY Violations**:
   - [Location]: [description of duplication]
   - **Consolidation Opportunity**: [suggestion]

3. **Missing Patterns**:
   - [Location]: [beneficial pattern suggestion]

### Code Smells Identified
| Smell Type | Location | Severity | Description | Remediation |
|------------|----------|----------|-------------|-------------|
| [type] | [file:line] | [High/Med/Low] | [details] | [suggestion] |

### Error Handling Assessment

- **Unhandled Promise Rejections**: [count and locations]

- **Missing Error Handling**: [locations]

- **Inadequate Input Validation**: [locations]

- **Poor Error Messages**: [examples]

### Documentation Score

- **JSDoc Coverage**: [percentage]

- **Type Coverage** (TypeScript): [percentage]

- **Comment Quality**: [Good/Fair/Poor]

- **Areas Needing Documentation**: [list]

### Modern JavaScript Usage

- **ES6+ Features**: [Good/Inconsistent/Poor adoption]

- **Async/Await Usage**: [Proper/Needs improvement]

- **Functional Programming**: [score]

- **Legacy Patterns to Update**: [list]

### Technical Debt Summary
**Priority 1 (Critical)**: [Estimated hours]

- [Issue description and location]

**Priority 2 (High)**: [Estimated hours]

- [Issue description and location]

**Priority 3 (Medium)**: [Estimated hours]

- [Issue description and location]

**Priority 4 (Low)**: [Estimated hours]

- [Issue description and location]

### Refactoring Recommendations
1. **Immediate Actions** (within 1 sprint):
   - [Specific refactoring with location and rationale]

2. **Short-term Goals** (1-2 months):
   - [Improvement initiative with expected impact]

3. **Long-term Initiatives** (3-6 months):
   - [Strategic refactoring with business justification]

### Positive Patterns
Acknowledge what's done well:

- [Good practice observed and locations]

- [Effective pattern usage examples]

### Next Steps

- [ ] Address critical complexity hotspots

- [ ] Implement automated quality gates (ESLint, Prettier)

- [ ] Plan refactoring sprints for high-priority technical debt

- [ ] Establish team coding standards documentation

- [ ] Set up pre-commit hooks for style enforcement

- [ ] Consider TypeScript migration (if not already using)

## Automation Recommendations
Suggest tools and configuration for continuous quality monitoring:

```json
// package.json scripts
{
  "scripts": {
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
    "lint:fix": "eslint . --ext .js,.jsx,.ts,.tsx --fix",
    "format": "prettier --write \"src/**/*.{js,jsx,ts,tsx,json,css,md}\"",
    "format:check": "prettier --check \"src/**/*.{js,jsx,ts,tsx,json,css,md}\"",
    "type-check": "tsc --noEmit",
    "complexity": "complexity-report src/",
    "duplication": "jscpd src/"
  }
}
```

```yaml
# Example .husky/pre-commit hook
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npm run lint
npm run format:check
npm run type-check
```

```javascript
// .eslintrc.js recommended configuration
module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'prettier'
  ],
  rules: {
    'complexity': ['warn', 10],
    'max-lines-per-function': ['warn', 50],
    'max-depth': ['warn', 4],
    'max-params': ['warn', 5],
    'no-console': 'warn',
    'no-var': 'error',
    'prefer-const': 'error',
    'no-eval': 'error',
    'eqeqeq': ['error', 'always']
  }
};
```

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/code_quality/analysis_scripts
mkdir -p ${OUTPUT_DIR}/code_quality/supporting_data
```

**Save files as follows**:

- Main report → `review/code_quality/code_quality_report.md`

- Findings data → `review/code_quality/code_quality_findings.json`

- Analysis scripts → `review/code_quality/analysis_scripts/`

- Supporting data → `review/code_quality/supporting_data/`
~~~
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
