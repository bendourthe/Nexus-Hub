# Code Cleanup & Refactoring Review

## Objective
Identify and eliminate dead code, duplication, and legacy patterns so the codebase remains lean, maintainable, and aligned with current architecture decisions.

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

### Duplication & Consolidation
- [ ] Near-duplicate functions or classes grouped with merge candidates
- [ ] Copy-pasted logic replaced with shared utilities or templates
- [ ] Repeated SQL queries or API calls centralized
- [ ] Configuration defaults unified across services
- [ ] DRY violations documented with recommended abstractions

### Refactoring Readiness
- [ ] Local complexity hotspots captured (cyclomatic, cognitive metrics)
- [ ] Large functions/modules broken into manageable units
- [ ] Legacy construction patterns replaced with modern equivalents
- [ ] Naming aligns with domain language and architecture boundaries
- [ ] Deprecation notices or migration guides drafted where needed

### Regression Safety
- [ ] Critical behaviours covered by unit/integration tests
- [ ] Cleanup changes gated by feature flags or staged rollout plans
- [ ] Observatory signals (logs, metrics, traces) updated
- [ ] Stakeholders notified of breaking removals
- [ ] Rollback strategy documented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Codebase Cleanup Request

Please perform a comprehensive, systematic cleanup of my codebase following this protocol:

## Phase 1: Analysis & Safety Check

Before making ANY changes, please:

1. **Analyze the complete codebase structure**
   - Identify all Python files in src/ and tests/
   - Map dependencies between modules
   - Identify public APIs that must be preserved

2. **Generate a detailed cleanup report** listing:
   - Unused imports, variables, and functions
   - Empty lines within function bodies
   - Inline and meta-commentary comments
   - Any additional cleanup opportunities (see below)
   - Estimated impact and risk level for each category

3. **Present findings and wait for my approval** before proceeding

## Phase 2: Cleanup Tasks

After I approve, systematically clean the following:

### Critical Removals
- **Unused imports**: Remove any imports not referenced in the code
- **Unused variables**: Remove variables that are assigned but never used
- **Unused functions**: Remove private functions (starting with `_`) that are never called
  - PRESERVE public functions even if seemingly unused (may be part of public API)
- **Empty lines within functions**: Remove blank lines inside function/method bodies
  - KEEP empty lines between functions, classes, and major code sections

### Comment Cleanup
- **Inline comments**: Remove same-line comments unless they explain complex logic
- **Meta-commentary**: Remove comments about code changes (e.g., "Changed from X to Y", "Added this because...")
- **Commented-out code**: Remove old code blocks that are commented out
- PRESERVE comments that explain:
  - Why a particular approach was chosen
  - Business logic or domain-specific rules
  - Complex algorithms or non-obvious implementations
  - Workarounds for known issues/bugs in dependencies

### Additional Cleanup Opportunities

#### Code Quality
- **Debug statements**: Remove leftover print(), console.log(), or debugging code
- **Redundant code**: Identify and consolidate duplicate functions or logic blocks
- **Unused parameters**: Remove function parameters that are defined but never used
- **Unnecessary pass statements**: Remove `pass` where not required
- **Trailing whitespace**: Remove whitespace at end of lines
- **Redundant return statements**: Simplify unnecessary `return None` at function ends

#### Import Organization
- **Consolidate imports**: Combine multiple imports from same module
- **Optimize import statements**: Use more efficient import patterns where applicable
- **Verify import grouping**: Ensure imports follow the standard structure:
  1. Standard library (alphabetically)
  2. Third-party libraries (grouped by function)
  3. Local application imports (alphabetically)

#### Code Simplification
- **Simplify boolean expressions**: `if x == True:` → `if x:`
- **Simplify conditional returns**: Multi-line if/else returns → single return with ternary
- **Remove redundant string concatenation**: Use f-strings consistently
- **Simplify list/dict comprehensions**: Where it improves readability

## Phase 3: Verification Protocol

After cleanup, you MUST:

1. **Provide summary** of all changes made, organized by category
2. **Highlight any edge cases** or decisions that required judgment
3. **Request that I run tests** to verify nothing broke:
Please run your test suite to verify the cleanup didn't break anything:
python tests/run_all_tests.py
4. **Document cleanup** in DEVLOG.md under a new section:
```markdown
   ### Code Cleanup - [Date]
   - Removed [X] unused imports
   - Removed [Y] unused functions
   - Removed [Z] empty lines
   - Additional improvements: [summary]

## Critical Safety Rules

**DO NOT:**
- Remove any public functions, classes, or methods (they may be imported elsewhere)
- Remove docstrings or type hints
- Remove empty lines between functions, classes, or major code sections
- Remove comments that explain business logic or complex algorithms
- Remove constants or configuration values even if seemingly unused
- Make multiple sweeping changes at once - work systematically by category

**ALWAYS:**
- Work on one file at a time or in small logical groups
- Explain any removal that might be ambiguous
- Preserve code functionality - cleanup should never change behavior
- Ask for confirmation if uncertain about removing something
- Track what was removed in case rollback is needed

## Output Format
Present cleanup in this structure:
- **Cleanup Report - [Category]**
- **File:** path/to/file.py
- **Removals:**
  - Line X: Unused import module_name
  - Lines X-Y: Unused function function_name()
  - Line Z: Inline comment removed
- **Rationale:** [Brief explanation of why these were removed]

## Summary Statistics

- **Total files processed:** X
- **Unused imports removed:** Y
- **Unused functions removed:** Z
- **Lines removed:** N
- **Code reduction:** X%

**Overall Impact:** [Low/Medium/High risk assessment]

## Optional Advanced Cleanup (Requires Extra Review)
If you'd like an even more thorough cleanup, also consider:
- **Type hint consistency**: Add missing type hints to match coding standards
- **Docstring completeness**: Flag functions missing docstrings
- **Naming convention audit**: Identify inconsistent naming patterns
- **Complexity analysis**: Flag overly complex functions (>50 lines) for potential refactoring
- **Dead code detection**: Identify code blocks that can never execute (unreachable code after return, etc.)
These require more careful review and may involve refactoring beyond simple cleanup.
~~~
