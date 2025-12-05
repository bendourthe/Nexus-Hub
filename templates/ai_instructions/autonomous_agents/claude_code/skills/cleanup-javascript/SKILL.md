---
name: cleanup-javascript
description: Remove dead code, consolidate duplicates, and modernize JavaScript/TypeScript codebases for improved maintainability
version: 1.0.0
author: Benjamin Dourthe
language: JavaScript/TypeScript
category: Code Cleanup
priority: MEDIUM
tags: [javascript, typescript, cleanup, refactoring, modernization, dead-code, es6]
template_source: code_cleanup/javascript_cleanup.md
---

# JavaScript/TypeScript Code Cleanup

Systematically identify and remove dead code, consolidate duplicate logic, and modernize legacy JavaScript/TypeScript patterns to maintain a lean, current, and maintainable codebase.

## When to Use This Skill

Use this skill when you need to:
- Remove unused imports, functions, classes, and modules
- Consolidate duplicate code and near-duplicate implementations
- Modernize legacy patterns (callbacks to async/await, var to const/let, ES5 to ES6+)
- Clean up console.log statements and commented code
- Optimize import organization and code structure
- Prepare codebase for new features or refactoring
- Reduce technical debt before major releases
- Remove unused npm dependencies

## What This Skill Does

This skill performs comprehensive JavaScript/TypeScript code cleanup:

### 1. Dead Code Detection
- **Unused Imports**: Identifies and removes unused import statements
- **Unused Functions**: Finds functions never called in codebase
- **Unused Classes**: Detects classes without instantiation
- **Unused Variables**: Identifies variables assigned but never used
- **Unreachable Code**: Finds code after return/break/continue statements
- **Empty Blocks**: Detects empty functions, classes, or try/catch blocks
- **Unused npm Dependencies**: Identifies packages in package.json not imported anywhere

### 2. Duplicate Code Consolidation
- **Exact Duplicates**: Finds identical code blocks for consolidation
- **Near Duplicates**: Detects similar code with minor variations
- **Duplicate Logic**: Identifies functionally equivalent implementations
- **Copy-Paste Detection**: Finds code copied across modules
- **Consolidation Strategy**: Recommends refactoring approach

### 3. Code Modernization
- **ES6+ Features**: Updates to arrow functions, destructuring, spread operators
- **Async/Await**: Converts promise chains to async/await
- **Template Literals**: Replaces string concatenation with template literals
- **Const/Let**: Converts var to const/let as appropriate
- **Optional Chaining**: Uses `?.` operator for null checks
- **Nullish Coalescing**: Uses `??` for default values
- **Modern Imports**: Converts require() to ES6 import statements (where appropriate)

### 4. Debug Statement Cleanup
- **Console Statements**: Removes debug console.log(), console.debug()
- **Commented Code**: Cleans up old commented-out code
- **TODO Comments**: Catalogs and prioritizes TODO items
- **Debugger Statements**: Removes debugger breakpoints
- **Temporary Variables**: Identifies debug-only variables

### 5. Import Organization
- **Node.js Built-ins**: Groups and sorts Node.js core modules
- **External Dependencies**: Organizes third-party packages
- **Internal Modules**: Structures local module imports
- **Type Imports**: Organizes TypeScript type-only imports
- **Unused Removal**: Eliminates unnecessary imports
- **Duplicate Imports**: Consolidates repeated imports from same module

### 6. Code Simplification
- **Complex Conditionals**: Simplifies nested if/else statements
- **Excessive Nesting**: Reduces deeply nested code
- **Long Functions**: Identifies candidates for decomposition
- **Magic Numbers**: Converts literals to named constants
- **Redundant Code**: Removes unnecessary operations
- **Unnecessary Else**: Simplifies if-return patterns

## Prerequisites

- JavaScript/TypeScript codebase to clean up
- Version control (git) for safe cleanup with rollback capability
- Test suite for regression verification (recommended)
- Backup of codebase or committed state
- Node.js and npm/yarn installed

## Instructions

### Step 1: Prepare for Cleanup

1. **Commit Current State**:
   ```bash
   git add .
   git commit -m "Pre-cleanup snapshot"
   ```

2. **Create Cleanup Branch** (recommended):
   ```bash
   git checkout -b code-cleanup
   ```

3. **Run Existing Tests** (if available):
   ```bash
   npm test
   # or
   yarn test
   ```

4. **Run Linting** (if configured):
   ```bash
   npm run lint
   # For TypeScript
   npm run type-check
   ```

5. **Create Output Directory**:
   ```bash
   mkdir -p cleanup_report/{templates,assets,exports}
   ```

### Step 2: Invoke the Cleanup Skill

Tell Claude Code to use this skill:

```
"Use the cleanup-javascript skill to analyze and clean up this JavaScript/TypeScript codebase.
Focus on:

1. Removing all unused imports and functions
2. Consolidating duplicate code
3. Modernizing to ES6+ patterns
4. Removing console.log statements
5. Organizing imports properly
6. Identifying unused npm packages

Save all reports to cleanup_report/ directory."
```

### Step 3: Review Cleanup Plan

Claude Code will generate a comprehensive cleanup plan including:

1. **Dead Code Candidates** - List of unused code with usage analysis
2. **Duplication Report** - Duplicate code locations with consolidation strategy
3. **Modernization Opportunities** - Legacy patterns to update
4. **Risk Assessment** - Impact analysis for each cleanup operation
5. **Implementation Plan** - Ordered steps with dependencies
6. **Package Analysis** - Unused dependencies in package.json

**Review the plan before proceeding with changes!**

### Step 4: Execute Cleanup in Phases

The skill will execute cleanup in safe phases:

**Phase 1: Low-Risk Cleanup**
- Remove unused imports
- Clean console.log statements
- Remove commented code
- Organize imports

**Phase 2: Code Modernization**
- Update to arrow functions
- Apply template literals
- Convert to const/let
- Add optional chaining
- Apply async/await patterns

**Phase 3: Structural Changes**
- Consolidate duplicates
- Remove dead functions
- Simplify complex code
- Extract constants

**Phase 4: Verification**
- Run tests after each phase
- Run linting and type checking
- Verify no functionality changes
- Document any issues

**Phase 5: Multi-Pass Protocol**
- First pass: Apply cleanup across all files
- Verification pass: Check for missed opportunities
- Repeat until complete
- Track statistics for each pass

### Step 5: Test After Cleanup

1. **Run Full Test Suite**:
   ```bash
   npm test
   # or
   yarn test
   ```

2. **Type Checking** (TypeScript):
   ```bash
   npm run type-check
   # or
   tsc --noEmit
   ```

3. **Linting**:
   ```bash
   npm run lint
   # or
   eslint src/
   ```

4. **Build Verification**:
   ```bash
   npm run build
   ```

5. **Manual Testing** (if no automated tests):
   - Test critical user workflows
   - Verify application starts correctly
   - Check key features still work

### Step 6: Review and Commit

1. **Review Changes**:
   ```bash
   git diff
   ```

2. **Stage and Commit** (in logical chunks):
   ```bash
   git add src/
   git commit -m "Remove unused imports and functions"

   git add src/
   git commit -m "Modernize to ES6+ arrow functions and template literals"

   git add src/
   git commit -m "Consolidate duplicate validation logic"
   ```

3. **Update Dependencies** (if needed):
   ```bash
   npm uninstall unused-package-1 unused-package-2
   git add package.json package-lock.json
   git commit -m "Remove unused npm dependencies"
   ```

4. **Merge to Main** (when satisfied):
   ```bash
   git checkout main
   git merge code-cleanup
   git push
   ```

## Cleanup Categories and Examples

### Category 1: Unused Imports
**Before:**
```javascript
import fs from 'fs';
import path from 'path';
import { map, filter, reduce } from 'lodash';
import axios from 'axios';
import moment from 'moment';

export function processData(data) {
    return JSON.parse(data);
}
```

**After:**
```javascript
export function processData(data) {
    return JSON.parse(data);
}
```

### Category 2: Console Statements
**Before:**
```javascript
function calculateTotal(items) {
    console.log('DEBUG: items =', items);
    const total = items.reduce((sum, item) => sum + item.price, 0);
    console.log('DEBUG: total =', total);
    return total;
}
```

**After:**
```javascript
function calculateTotal(items) {
    return items.reduce((sum, item) => sum + item.price, 0);
}
```

### Category 3: Modern JavaScript Patterns
**Before:**
```javascript
var message = "Hello, " + name + "! You have " + count + " messages.";

function oldFunction(data, callback) {
    fetchData()
        .then(function(result) {
            return processData(result);
        })
        .then(function(processed) {
            callback(null, processed);
        })
        .catch(function(error) {
            callback(error);
        });
}
```

**After:**
```javascript
const message = `Hello, ${name}! You have ${count} messages.`;

async function modernFunction(data) {
    try {
        const result = await fetchData();
        return processData(result);
    } catch (error) {
        throw error;
    }
}
```

### Category 4: Optional Chaining and Nullish Coalescing
**Before:**
```javascript
const userName = user && user.profile && user.profile.name ? user.profile.name : 'Anonymous';
const userAge = user && user.age !== null && user.age !== undefined ? user.age : 0;
```

**After:**
```javascript
const userName = user?.profile?.name ?? 'Anonymous';
const userAge = user?.age ?? 0;
```

### Category 5: Destructuring and Spread
**Before:**
```javascript
function processUser(user) {
    const name = user.name;
    const email = user.email;
    const age = user.age;

    const newUser = Object.assign({}, user, { verified: true });
    return newUser;
}
```

**After:**
```javascript
function processUser(user) {
    const { name, email, age } = user;
    return { ...user, verified: true };
}
```

### Category 6: Duplicate Code Consolidation
**Before:**
```javascript
function validateUser(user) {
    if (!user.name) return false;
    if (!user.email) return false;
    if (!user.email.includes('@')) return false;
    return true;
}

function validateAdmin(admin) {
    if (!admin.name) return false;
    if (!admin.email) return false;
    if (!admin.email.includes('@')) return false;
    return true;
}
```

**After:**
```javascript
function validateAccount(account) {
    if (!account?.name) return false;
    if (!account?.email) return false;
    if (!account.email.includes('@')) return false;
    return true;
}

const validateUser = validateAccount;
const validateAdmin = validateAccount;
```

### Category 7: Useless Variables and Properties
**Before:**
```javascript
// React component with ignored CSS-in-JS
const BadProgressBar = styled.div`
  border: 1px solid #d0d0d0;      /* IGNORED by canvas */
  border-radius: 12px;             /* IGNORED by canvas */
  background-color: #e5e7eb;       /* IGNORED by canvas */
`;

function CustomProgressBar() {
  return (
    <BadProgressBar>
      <canvas ref={canvasRef} />  {/* Custom drawing ignores CSS */}
    </BadProgressBar>
  );
}
```

**After:**
```javascript
// Constants at module top
const BORDER_RADIUS = 12;
const BORDER_COLOR = '#d0d0d0';
const BACKGROUND_COLOR = '#e5e7eb';

const GoodProgressBar = styled.div`
  position: relative;
  overflow: hidden;
`;

function CustomProgressBar() {
  const drawProgress = (ctx) => {
    ctx.strokeStyle = BORDER_COLOR;
    ctx.fillStyle = BACKGROUND_COLOR;
    // Use constants in drawing
  };

  return <GoodProgressBar><canvas ref={canvasRef} /></GoodProgressBar>;
}
```

## Output Structure

The skill generates organized output in `cleanup_report/`:

```
cleanup_report/
├── templates/
│   ├── cleanup_checklist.md       # Reusable cleanup checklist
│   ├── modernization_guide.md     # ES6+ modernization patterns
│   └── eslint_config.js           # Recommended ESLint config
├── assets/
│   ├── duplication_graph.png      # Visual duplication analysis
│   └── complexity_heatmap.png     # Code complexity visualization
└── exports/
    ├── cleanup_report.md           # Comprehensive cleanup report
    ├── dead_code_list.md           # Dead code candidates
    ├── duplication_analysis.md     # Duplicate code analysis
    ├── modernization_plan.md       # Modernization strategy
    ├── unused_packages.md          # Unused npm dependencies
    └── risk_assessment.md          # Impact and risk analysis
```

## Safety Measures

### 1. Version Control Required
- Always commit before cleanup
- Create dedicated cleanup branch
- Commit changes in logical phases

### 2. Test Coverage
- Run tests before cleanup (baseline)
- Run tests after each phase
- Document any test failures immediately

### 3. Incremental Approach
- Apply changes in small batches
- Verify after each batch
- Don't proceed if tests fail

### 4. Risk Assessment
- High-risk changes reviewed manually
- Critical paths tested thoroughly
- Rollback plan documented

### 5. Documentation
- Document all changes in commit messages
- Update DEVLOG.md with cleanup history
- Note any behavioral changes

## Common Issues and Solutions

### Issue: Tests Fail After Cleanup
**Solution**:

1. Review git diff for the failing area
2. Use `git checkout -- <file>` to revert specific files
3. Re-run tests to isolate issue
4. Apply cleanup more granularly

### Issue: False Positive for "Unused" Code
**Solution**:

- Check for dynamic imports (import())
- Verify reflection/string-based references
- Look for eval() or dynamic require()
- Keep code if uncertain

### Issue: Import Organization Breaks Code
**Solution**:

- Check for circular dependencies
- Verify import side effects
- Keep original organization if needed
- Document special requirements

### Issue: Modernization Changes Behavior
**Solution**:

- Review browser/Node.js compatibility
- Check for subtle semantic differences
- Test edge cases thoroughly
- Revert if behavior changes

### Issue: TypeScript Type Errors After Cleanup
**Solution**:

- Run `tsc --noEmit` to check types
- Fix type errors incrementally
- Consider type-only imports
- Update @types/* packages if needed

## Success Criteria

After using this skill, your codebase should have:

- [ ] All unused imports removed
- [ ] No console.log debugging statements
- [ ] No commented-out code (except strategic comments)
- [ ] Duplicate code consolidated where appropriate
- [ ] Modern ES6+ patterns applied (arrow functions, destructuring, async/await)
- [ ] Imports organized properly (Node.js → external → internal)
- [ ] Unused npm packages identified or removed
- [ ] All tests passing
- [ ] All linting checks passing
- [ ] TypeScript compilation successful (if using TypeScript)
- [ ] Cleanup documented in DEVLOG.md
- [ ] Changes committed to version control

## Related Skills

- `setup-javascript-system-prompt`: Establish standards before cleanup
- `code-review-quality`: Review code quality after cleanup
- `generate-test-cases`: Create tests for newly consolidated code
- `generate-docstrings`: Document cleaned-up code

## Tools and Libraries

### Static Analysis Tools
- **ESLint**: Linting and style checking
- **TypeScript**: Type checking
- **Prettier**: Code formatting
- **import-js**: Import management

### Duplication Detection
- **jscpd**: Copy-paste detection
- **jsinspect**: Structural duplication detection

### Unused Code Detection
- **depcheck**: Unused npm dependencies
- **ts-prune**: Unused TypeScript exports
- **unimported**: Unused files and dependencies

### Installation
```bash
npm install --save-dev eslint typescript prettier
npm install --save-dev jscpd depcheck ts-prune unimported
```

### Running Tools
```bash
# ESLint
npx eslint src/

# TypeScript
npx tsc --noEmit

# Prettier
npx prettier --check src/

# Dependency check
npx depcheck

# Unused exports (TypeScript)
npx ts-prune

# Duplication detection
npx jscpd src/
```

## Additional Resources

- [JavaScript Clean Code](https://github.com/ryanmcdermott/clean-code-javascript)
- [TypeScript Best Practices](https://www.typescriptlang.org/docs/handbook/declaration-files/do-s-and-don-ts.html)
- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- [ES6 Features](https://github.com/lukehoban/es6features)
- [You Don't Know JS](https://github.com/getify/You-Dont-Know-JS)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5 - code_cleanup/javascript_cleanup.md
