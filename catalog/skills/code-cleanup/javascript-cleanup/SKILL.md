---
name: javascript-cleanup
description: Remove unused exports, fix ESLint issues, modernize to ES6+, and clean up JavaScript/TypeScript codebases. Use when cleaning up JS/TS projects, removing dead code, modernizing legacy JavaScript, or improving code maintainability.
summary_l0: "Clean up JavaScript/TypeScript with ES6+ modernization, ESLint fixes, and dead code removal"
overview_l1: "This skill systematically identifies and removes dead code, fixes ESLint issues, and modernizes legacy JavaScript patterns to maintain a clean, modern codebase. Use it when removing unused exports and dead code, fixing ESLint/TSLint issues, modernizing to ES6+ syntax, converting JavaScript to TypeScript, or preparing JS/TS code for review. Key capabilities include dead code and unused export detection, ESLint and TSLint warning resolution, ES6+ syntax migration (arrow functions, destructuring, template literals, async/await), TypeScript conversion, module system modernization (CommonJS to ESM), and import optimization. The expected output is a modernized JavaScript/TypeScript codebase with ES6+ syntax, resolved linter warnings, and removed dead code. Trigger phrases: cleanup JavaScript, cleanup TypeScript, remove dead code JS, fix ESLint, modernize JS, ES6 migration."
---

# JavaScript/TypeScript Code Cleanup

Systematically identify and remove dead code, fix ESLint issues, and modernize legacy JavaScript patterns to maintain a clean, modern codebase.

## When to Use This Skill

Use this skill when you need to:

- Remove unused exports and dead code
- Fix ESLint/TSLint issues
- Modernize to ES6+ syntax
- Convert to TypeScript
- Clean up before code review

**Trigger phrases**: "cleanup JavaScript", "cleanup TypeScript", "remove dead code JS", "fix ESLint", "modernize JS", "ES6 migration"

## What This Skill Does

### Cleanup Areas

1. **Dead Code Removal**
   - Unused exports
   - Unreachable code
   - Unused variables/functions
   - Dead imports

2. **Style Compliance**
   - ESLint rules
   - Prettier formatting
   - Naming conventions

3. **TypeScript Migration**
   - Type annotations
   - Interface definitions
   - Strict mode compliance

4. **ES6+ Modernization**
   - Arrow functions
   - Template literals
   - Destructuring
   - async/await

## Instructions

### Step 1: Run Analysis Tools

```bash
# Install tools
npm install --save-dev eslint prettier typescript

# Find issues
npx eslint . --ext .js,.ts,.tsx
npx tsc --noEmit

# Check formatting
npx prettier --check "src/**/*.{js,ts,tsx}"
```

### Step 2: Fix Issues Automatically

```bash
# Fix ESLint issues
npx eslint . --fix

# Format code
npx prettier --write "src/**/*.{js,ts,tsx}"

# Remove unused dependencies
npx depcheck
```

### Step 3: Modernize Patterns

```javascript
// var → const/let
// Before
var name = 'John';
// After
const name = 'John';

// Function → Arrow function
// Before
function add(a, b) { return a + b; }
// After
const add = (a, b) => a + b;

// String concatenation → Template literals
// Before
const msg = 'Hello, ' + name + '!';
// After
const msg = `Hello, ${name}!`;

// Promise.then → async/await
// Before
getData().then(data => process(data)).catch(err => handle(err));
// After
try {
  const data = await getData();
  process(data);
} catch (err) {
  handle(err);
}

// Object property shorthand
// Before
const obj = { name: name, age: age };
// After
const obj = { name, age };

// Destructuring
// Before
const name = user.name;
const age = user.age;
// After
const { name, age } = user;
```

### Step 4: Add TypeScript Types

```typescript
// Before (JavaScript)
function processUser(user) {
  return user.name.toUpperCase();
}

// After (TypeScript)
interface User {
  name: string;
  email: string;
  age: number;
}

function processUser(user: User): string {
  return user.name.toUpperCase();
}
```

## Common Cleanup Targets

| Pattern | Before | After |
|---------|--------|-------|
| Variable declaration | `var x = 1` | `const x = 1` |
| Function | `function f() {}` | `const f = () => {}` |
| String concat | `'a' + b` | `` `a${b}` `` |
| Object method | `{ f: function() {} }` | `{ f() {} }` |
| Null check | `x !== null && x !== undefined` | `x != null` |

## Tools

- **ESLint**: Linting and auto-fix
- **Prettier**: Code formatting
- **TypeScript**: Type checking
- **depcheck**: Find unused dependencies

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "var works the same as let, no need to change it" | var is function-scoped and hoisted, so the loop variable captured in a closure leaks the last value, not the per-iteration one. Converting to let/const fixes a class of closure bugs the old syntax invited. |
| "I'll silence this ESLint rule with eslint-disable" | A blanket disable hides the no-unused-vars and no-floating-promises rules that catch real defects; the unhandled promise rejection it suppresses crashes the process later. Fix the cause, do not disable the rule. |
| "Callbacks are fine, async/await is just sugar" | Nested callbacks drop errors silently when a handler forgets to check the err argument; async/await with try/catch routes every rejection through one path the linter can verify. |
| "tsc reports type errors but it still runs" | A type error is a runtime bug the compiler already found for you; shipping with `tsc --noEmit` failures means trusting that the wrong type never reaches that line, which it eventually does. |

## Verification

- [ ] ESLint is clean: `npx eslint . --ext .js,.ts,.tsx` reports no errors
- [ ] Type-check passes: `npx tsc --noEmit` reports no errors
- [ ] Formatting is consistent: `npx prettier --check "src/**/*.{js,ts,tsx}"` succeeds
- [ ] No `var` declarations remain; all are `let` or `const`
- [ ] No remaining `eslint-disable` comments without a justifying inline reason
- [ ] All existing tests pass: `npm test`

## Related Skills

- [[code-quality]] -- score the cleaned codebase against SOLID and complexity metrics
- [[docstrings]] -- add JSDoc documentation to the modernized functions
- [[javascript-expert]] -- idiomatic modern JavaScript patterns this cleanup applies
- [[typescript-expert]] -- type-safe patterns for the JavaScript-to-TypeScript conversion path
- [[typed-boundary-hygiene]] -- owns low-evidence TypeScript/JavaScript contracts and assertion evidence; this skill retains ESLint, dead-code, and ES6+ modernization

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Based on**: AI Templates code_cleanup/javascript_cleanup.md


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
