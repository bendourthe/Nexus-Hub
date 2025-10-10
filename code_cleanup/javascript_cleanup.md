# Code Cleanup & Refactoring Review - JavaScript/TypeScript

## Objective
Identify and eliminate dead code, duplication, and legacy patterns so the codebase remains lean, maintainable, and aligned with current architecture decisions. Focus on JavaScript/TypeScript specific issues including unused imports, console logs, and modern ES6+ patterns.

## Output Directory Structure

All cleanup outputs should be saved in organized directories:

```
cleanup/
├── cleanup_report.md
├── cleanup_history.md
├── backup/
├── scripts/
└── analysis/
```

**Directory Setup**:

- Create `cleanup/` directory in repository root if it doesn't exist

- All cleanup reports, history, backups, scripts, and analysis go in this directory

**Expected Outputs**:

- `cleanup_report.md` - Detailed report of all cleanup actions performed

- `cleanup_history.md` - Historical log of cleanup sessions with timestamps

- `backup/` - Backup copies of files before cleanup modifications

- `scripts/` - Automated cleanup scripts generated or used

- `analysis/` - Analysis data, metrics, and diagnostic outputs

## Review Checklist

### Dead Code & Drift
- [ ] Unused modules, packages, and entry points identified
- [ ] Dormant feature flags, experiments, or toggles catalogued
- [ ] Deprecated APIs and endpoints mapped to replacement timeline
- [ ] Obsolete configuration values or environment variables removed
- [ ] Unreachable code paths confirmed with coverage/profiling evidence
- [ ] Unused npm dependencies identified in package.json

### Duplication & Consolidation
- [ ] Near-duplicate functions or classes grouped with merge candidates
- [ ] Copy-pasted logic replaced with shared utilities or templates
- [ ] Repeated API calls or database queries centralized
- [ ] Configuration defaults unified across services
- [ ] DRY violations documented with recommended abstractions
- [ ] Duplicate type definitions or interfaces consolidated

### Refactoring Readiness
- [ ] Local complexity hotspots captured (cyclomatic, cognitive metrics)
- [ ] Large functions/modules broken into manageable units
- [ ] Legacy construction patterns replaced with modern ES6+ equivalents
- [ ] Naming aligns with domain language and architecture boundaries
- [ ] Deprecation notices or migration guides drafted where needed
- [ ] Callback patterns replaced with promises/async-await where appropriate

### Regression Safety
- [ ] Critical behaviours covered by unit/integration tests
- [ ] Cleanup changes gated by feature flags or staged rollout plans
- [ ] Observatory signals (logs, metrics, traces) updated
- [ ] Stakeholders notified of breaking removals
- [ ] Rollback strategy documented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# JavaScript/TypeScript Codebase Cleanup Request

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

Please perform a comprehensive, systematic cleanup of my JavaScript/TypeScript codebase following this protocol:

## Phase 1: Analysis & Safety Check

Before making ANY changes, please:

1. **Analyze the complete codebase structure**
   - Identify all .js, .jsx, .ts, .tsx files in src/ and test/
   - Map dependencies between modules
   - Identify public APIs that must be preserved
   - Check package.json for unused dependencies

2. **Generate a detailed cleanup report** listing:
   - Unused imports and exports
   - Unused variables, functions, and classes
   - Console.log() and debugging statements
   - Empty lines within function bodies
   - Inline and meta-commentary comments
   - Dead code after returns or in unreachable branches
   - Legacy patterns (var, function expressions, callbacks)
   - Estimated impact and risk level for each category

3. **Present findings and wait for my approval** before proceeding

## Phase 2: Cleanup Tasks

After I approve, systematically clean the following:

### Critical Removals
- **Unused imports**: Remove any imports not referenced in the code
  - Use ESLint's no-unused-vars or TypeScript's compiler to detect
  - Remove entire import statements when no specifiers are used
- **Unused variables**: Remove variables that are assigned but never used
- **Unused functions**: Remove private functions (not exported) that are never called
  - PRESERVE exported functions even if seemingly unused (may be part of public API)
- **Unused parameters**: Remove parameters that are defined but never used in function bodies
  - Keep parameters that are part of function signature contracts (callbacks, event handlers)
- **Empty lines within functions**: Remove excessive blank lines inside function/method bodies
  - KEEP empty lines between logical code sections and between functions

### Comment Cleanup
- **Inline comments**: Remove same-line comments unless they explain complex logic
- **Meta-commentary**: Remove comments about code changes (e.g., "Changed from X to Y", "Added this because...")
- **Commented-out code**: Remove old code blocks that are commented out
- **TODO comments**: Flag or remove stale TODO comments
- PRESERVE comments that explain:
  - Why a particular approach was chosen
  - Business logic or domain-specific rules
  - Complex algorithms or non-obvious implementations
  - Workarounds for known issues/bugs in dependencies
  - JSDoc/TSDoc documentation

### Debugging & Development Artifacts
- **Console statements**: Remove console.log(), console.debug(), console.warn() used for debugging
  - PRESERVE intentional logging for production (error handling, monitoring)
- **Debugger statements**: Remove `debugger;` breakpoints
- **Test-only code**: Remove code marked as temporary test scaffolding

### Additional Cleanup Opportunities

#### Code Quality
- **Redundant code**: Identify and consolidate duplicate functions or logic blocks
- **Dead code after returns**: Remove unreachable code after return statements
- **Unnecessary else**: Simplify if-return patterns that don't need else blocks
- **Trailing whitespace**: Remove whitespace at end of lines
- **Redundant return statements**: Simplify unnecessary `return undefined;` at function ends
- **Empty constructors**: Remove constructors that do nothing

#### Import Organization
- **Consolidate imports**: Combine multiple imports from same module
- **Sort imports**: Organize imports in standard order:
  1. Node.js built-ins (fs, path, etc.)
  2. External dependencies (react, lodash, etc.)
  3. Internal modules (grouped by feature)
  4. Type imports (TypeScript)
  5. Styles and assets
- **Use named imports**: Replace `import *` with specific named imports where possible
- **Remove unused type imports**: Clean up TypeScript type-only imports

#### Code Modernization
- **Replace var with const/let**: Convert legacy `var` declarations
- **Arrow functions**: Replace function expressions with arrow functions where appropriate
- **Template literals**: Replace string concatenation with template literals
- **Destructuring**: Use destructuring for objects and arrays where it improves readability
- **Spread operators**: Replace Object.assign and array concatenation with spread syntax
- **Async/await**: Replace promise chains with async/await where it improves readability
- **Optional chaining**: Use `?.` operator instead of manual null checks
- **Nullish coalescing**: Use `??` operator instead of `||` for default values

#### TypeScript-Specific
- **Remove explicit types**: Remove redundant type annotations that TypeScript can infer
- **Any types**: Flag or replace `any` with proper types
- **Unused type definitions**: Remove unused interfaces, types, and enums
- **Type assertions**: Review and potentially remove unnecessary type assertions

#### Build & Configuration
- **Unused npm packages**: Identify dependencies in package.json not imported anywhere
- **DevDependencies**: Verify dev dependencies are correctly categorized
- **Babel/webpack config**: Remove unused plugins or loaders

## Phase 3: Verification Protocol

After cleanup, you MUST:

1. **Provide summary** of all changes made, organized by category
2. **Highlight any edge cases** or decisions that required judgment
3. **Request that I run tests and linting** to verify nothing broke:
   ```bash
   npm run lint
   npm run type-check  # For TypeScript
   npm test
   npm run build
   ```
4. **Document cleanup** in CHANGELOG.md or development log:
   ```markdown
   ### Code Cleanup - [Date]
   - Removed [X] unused imports
   - Removed [Y] unused functions
   - Removed [Z] console.log statements
   - Modernized [N] legacy patterns
   - Additional improvements: [summary]
   ```

## Critical Safety Rules

**DO NOT:**
- Remove any exported functions, classes, or variables (they may be imported elsewhere)
- Remove JSDoc/TSDoc comments or type definitions
- Remove empty lines between functions, classes, or major code sections
- Remove comments that explain business logic or complex algorithms
- Remove constants or configuration values even if seemingly unused
- Remove intentional console.error() or production logging
- Change function signatures or public APIs
- Make multiple sweeping changes at once - work systematically by category

**ALWAYS:**
- Work on one file at a time or in small logical groups
- Explain any removal that might be ambiguous
- Preserve code functionality - cleanup should never change behavior
- Ask for confirmation if uncertain about removing something
- Track what was removed in case rollback is needed
- Run ESLint/TSLint after changes to verify correctness
- Preserve backward compatibility for public APIs

## Output Format
Present cleanup in this structure:
- **Cleanup Report - [Category]**
- **File:** path/to/file.js
- **Removals:**
  - Line X: Unused import { module }
  - Lines X-Y: Unused function functionName()
  - Line Z: console.log() debugging statement
  - Line N: Inline comment removed
- **Rationale:** [Brief explanation of why these were removed]

## Summary Statistics

- **Total files processed:** X
- **Unused imports removed:** Y
- **Unused functions removed:** Z
- **Console statements removed:** N
- **Lines removed:** M
- **Code reduction:** X%
- **Modernization changes:** P

**Overall Impact:** [Low/Medium/High risk assessment]

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p cleanup/backup
mkdir -p cleanup/scripts
mkdir -p cleanup/analysis
```

**Save files as follows**:

- Cleanup report → `cleanup/cleanup_report.md`

- Cleanup history → `cleanup/cleanup_history.md`

- Backups → `cleanup/backup/`

- Scripts → `cleanup/scripts/`

- Analysis → `cleanup/analysis/`

## Optional Advanced Cleanup (Requires Extra Review)
If you'd like an even more thorough cleanup, also consider:
- **Type coverage**: Add missing TypeScript types to match coding standards
- **JSDoc completeness**: Flag functions missing documentation
- **Naming convention audit**: Identify inconsistent naming patterns (camelCase, PascalCase)
- **Complexity analysis**: Flag overly complex functions (>50 lines, high cyclomatic complexity)
- **Performance patterns**: Identify inefficient patterns (unnecessary re-renders, memory leaks)
- **Accessibility**: Flag missing ARIA attributes or accessibility issues
- **Security**: Identify potential XSS vulnerabilities or unsafe patterns
- **Bundle size**: Analyze import costs and suggest lighter alternatives

These require more careful review and may involve refactoring beyond simple cleanup.
~~~
