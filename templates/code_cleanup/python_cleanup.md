---
template_id: python_cleanup
template_name: Code Cleanup - Python
version: 1.0.0
last_updated: 2025-12-03
language: Python
category: ai-templates
phase: code_cleanup
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
tools:

  - pytest (8.3.4+)
  - black (24.12.0)
  - mypy (1.13.0)
  - ruff
tags:

  - ai-templates
  - refactoring
  - python
---
# Code Cleanup & Refactoring Review

## Objective
Identify and eliminate dead code, duplication, and legacy patterns so the codebase remains lean, maintainable, and aligned with current architecture decisions.

## Output Directory Structure

All outputs should be saved in organized directories:

```
cleanup/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `cleanup/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


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

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="cleanup"
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

### Multi-Pass Cleanup Protocol

**CRITICAL: Perform multiple passes through the entire codebase to ensure completeness**

1. **First Pass**: Apply all cleanup tasks systematically across the codebase
   - Work through all Python files in the project
   - Apply all requested cleanup operations
   - Track which files were modified

2. **Verification Pass**: Review the entire codebase again
   - Check for any files that were missed in the first pass
   - Verify all cleanup patterns were applied consistently
   - Identify any edge cases or exceptions that need attention

3. **Repeat Until Complete**: Continue additional passes if needed
   - If files were found that needed cleanup in the verification pass, perform another full pass
   - Repeat until a complete pass finds no additional cleanup opportunities
   - Track the number of passes required to achieve complete cleanup

4. **Pass Tracking**: Maintain detailed statistics for each pass
   - Number of files processed per pass
   - Number of files cleaned per pass
   - Percentage of codebase cleaned per pass
   - Types of issues found per pass

#### When to Stop Multi-Pass Cleanup

Stop when **ONE** of these conditions is met:

1. ✅ **Zero-change pass** (RECOMMENDED STOPPING POINT)
   - Entire verification pass finds nothing to clean
   - All files reviewed, no modifications made
   - This is the ideal completion state

2. ✅ **Diminishing returns threshold**
   - <5% additional files cleaned per pass
   - Calculate: `(files_cleaned_this_pass / total_files) < 0.05`
   - Example: If 150 total files and pass cleans <8 files, stop

3. ✅ **Pass limit reached**
   - Maximum 3 passes completed
   - Log incomplete work if stopping at this point
   - Document remaining issues for future cleanup

4. ✅ **Time limit reached**
   - 8 hours of cleanup time exceeded
   - Document progress and remaining work
   - Schedule follow-up cleanup session if needed

**NEVER stop without at least 2 passes (initial + verification).**

#### Progress Tracking

Create `${OUTPUT_DIR}/cleanup/progress.md` after each pass:

```markdown
# Cleanup Progress Log

## Pass 1 - Initial Cleanup
- **Date**: 2025-12-03
- **Start Time**: 10:00 AM
- **End Time**: 1:00 PM
- **Duration**: 3 hours
- **Files Analyzed**: 150
- **Files Cleaned**: 45 (30.0%)
- **Issues Found**: 234
  - Unused imports: 67
  - Unused variables: 89
  - Empty lines: 45
  - Inline comments: 33
- **Issues Resolved**: 234 (100%)

## Pass 2 - Verification
- **Date**: 2025-12-03
- **Start Time**: 2:00 PM
- **End Time**: 3:00 PM
- **Duration**: 1 hour
- **Files Analyzed**: 150
- **Files Cleaned**: 8 (5.3%)
- **Issues Found**: 12
  - Unused imports: 5
  - Empty lines: 7
- **Issues Resolved**: 12 (100%)

## Decision: STOP - Diminishing returns threshold met
- **Condition Met**: Files cleaned in Pass 2 (5.3%) < threshold (5%)
- **Total Passes**: 2
- **Total Time**: 4 hours
- **Total Files Cleaned**: 53/150 (35.3%)
- **Overall Status**: ✅ Cleanup complete
```

#### Multi-Pass Decision Matrix

Use this matrix to decide whether to continue or stop:

| Files Cleaned This Pass | Total Files | Percentage | Action |
|------------------------|-------------|------------|---------|
| 0 | Any | 0% | **STOP** - Zero-change pass (ideal completion) |
| 1-7 | 150 | <5% | **STOP** - Diminishing returns |
| 8-15 | 150 | 5-10% | **CONTINUE** - Still worthwhile |
| 16+ | 150 | >10% | **CONTINUE** - Significant cleanup remaining |

**Time-based stopping:**
- After 8 hours total cleanup time, **STOP** regardless of percentage
- Document remaining work for future cleanup session

**Pass-based stopping:**
- After 3 passes, **STOP** and document incomplete work
- Consider if issues are edge cases or systematic problems

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

#### Useless Variables and Properties

Identify and remove variables, properties, and configuration that serve no functional purpose:

- **Ignored Style Properties**: In custom-painted widgets (PyQt/PySide, tkinter)
  - Properties defined in stylesheets/setStyleSheet() that are completely ignored by custom paintEvent()
  - CSS properties that are overridden by manual QPainter drawing code
  - Style configurations that have no effect due to custom rendering

- **Dead Configuration Values**: Settings that are defined but never used
  - Class constants assigned but never referenced
  - Configuration dictionaries with unused keys
  - Theme/style values that are shadowed by code-level constants

- **Redundant Constants**: Values that duplicate other constants
  - Multiple constants with identical values serving the same purpose
  - Constants that duplicate framework defaults unnecessarily

**Detection Example: PyQt Custom-Painted Widgets**

```python
# BEFORE - Useless stylesheet properties
class BadProgressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        # ❌ All these CSS properties are IGNORED by custom paintEvent
        self.setStyleSheet("""
            QProgressBar {
                border: 1px solid #d0d0d0;      /* IGNORED */
                border-radius: 12px;             /* IGNORED */
                background-color: #e5e7eb;       /* IGNORED */
                color: #2c3e50;                  /* IGNORED */
            }
        """)

    def paintEvent(self, event):
        # Custom painting bypasses ALL stylesheet properties above
        painter = QPainter(self)
        painter.drawRoundedRect(...)  # Draws its own border, background, etc.

# AFTER - Using constants (clear and discoverable)
class GoodProgressBar(QProgressBar):
    # ✅ Visual properties as clear, discoverable class constants
    BORDER_RADIUS = 12
    BORDER_COLOR = QColor("#d0d0d0")
    BACKGROUND_COLOR = QColor("#e5e7eb")
    TEXT_COLOR = QColor("#2c3e50")

    def __init__(self):
        super().__init__()
        # Only stylesheet properties that actually work
        self.setStyleSheet("QProgressBar { background: transparent; }")

    def paintEvent(self, event):
        painter = QPainter(self)
        # Use the constants in actual drawing code
        painter.setPen(self.BORDER_COLOR)
        painter.setBrush(self.BACKGROUND_COLOR)
        painter.drawRoundedRect(..., self.BORDER_RADIUS, self.BORDER_RADIUS)
```

**Why This Matters:**
1. **Clarity**: Configuration is where you expect it (class constants at top)
2. **Maintainability**: Easy to find and modify visual properties
3. **No Confusion**: No wondering why changing CSS doesn't work
4. **Better IDE Support**: Constants have autocomplete, CSS strings don't

**Detection Strategy:**
1. Find classes that override `paintEvent()` or similar custom rendering methods
2. Check if they have `setStyleSheet()` calls with visual properties
3. Verify those visual properties are actually used in the paint code
4. If not used, extract values to class constants and remove useless CSS
5. Add comment explaining why stylesheet is minimal

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

### Multi-Pass Cleanup Metrics

**Pass-by-Pass Breakdown:**

- **Pass 1** (Initial cleanup):
  - Files processed: X
  - Files cleaned: Y
  - Percentage of codebase: Z%

- **Pass 2** (Verification):
  - Files processed: X
  - Files cleaned: W (files missed in Pass 1)
  - Percentage of codebase: V%

- **Pass N** (if needed):
  - Files processed: X
  - Files cleaned: 0 (verification complete)

**Multi-Pass Summary:**
- **Total passes required**: N
- **Files cleaned in first pass**: Y (Z% of codebase)
- **Files cleaned in subsequent passes**: W (V% of codebase)
- **Final verification**: ✅ All files processed, no additional cleanup needed

### Standard Cleanup Metrics

- **Total files processed:** X

- **Unused imports removed:** Y

- **Unused functions removed:** Z

- **Unused variables removed:** A

- **Lines removed:** N

- **Code reduction:** X%

### Useless Code Detection Metrics

- **Useless style properties removed:** M
  - Converted to code constants: P
  - Simply deleted: Q

- **Dead configuration removed:** R

- **Redundant constants consolidated:** S

**Impact Analysis:**
- Code clarity improvement: [High/Medium/Low]
- Maintenance burden reduction: [High/Medium/Low]
- Configuration discoverability: [High/Medium/Low]

**Overall Impact:** [Low/Medium/High risk assessment]

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/backup
mkdir -p ${OUTPUT_DIR}/scripts
mkdir -p ${OUTPUT_DIR}/analysis
```

**Save files as follows**:

- Cleanup report → `cleanup/cleanup_report.md`

- Cleanup history → `cleanup/cleanup_history.md`

- Backups → `cleanup/backup/`

- Scripts → `cleanup/scripts/`

- Analysis → `cleanup/analysis/`

## Optional Advanced Cleanup (Requires Extra Review)
If you'd like an even more thorough cleanup, also consider:

- **Type hint consistency**: Add missing type hints to match coding standards

- **Docstring completeness**: Flag functions missing docstrings

- **Naming convention audit**: Identify inconsistent naming patterns

- **Complexity analysis**: Flag overly complex functions (>50 lines) for potential refactoring

- **Dead code detection**: Identify code blocks that can never execute (unreachable code after return, etc.)
These require more careful review and may involve refactoring beyond simple cleanup.
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
