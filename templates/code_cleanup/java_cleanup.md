---
template_id: java_cleanup
template_name: Code Cleanup - Java
version: 1.0.0
last_updated: 2025-12-03
language: Java
category: ai-templates
phase: code_cleanup
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
tools:
  - junit (5.11.3)
  - maven
  - gradle
tags:
  - ai-templates
  - refactoring
  - java
---
# Code Cleanup & Refactoring Review - Java

## Objective
Identify and eliminate dead code, duplication, and legacy patterns so the codebase remains lean, maintainable, and aligned with current architecture decisions. Focus on Java-specific issues including unused imports, code smells, and modern Java patterns.

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

- [ ] Unused classes, interfaces, and methods identified

- [ ] Dormant feature flags, experiments, or toggles catalogued

- [ ] Deprecated APIs and endpoints mapped to replacement timeline

- [ ] Obsolete configuration values or properties removed

- [ ] Unreachable code paths confirmed with coverage/profiling evidence

- [ ] Unused Maven/Gradle dependencies identified

### Duplication & Consolidation

- [ ] Near-duplicate classes or methods grouped with merge candidates

- [ ] Copy-pasted logic replaced with shared utilities or base classes

- [ ] Repeated database queries or API calls centralized

- [ ] Configuration defaults unified across modules

- [ ] DRY violations documented with recommended abstractions

- [ ] Duplicate POJO classes or DTOs consolidated

### Refactoring Readiness

- [ ] Local complexity hotspots captured (cyclomatic, cognitive metrics)

- [ ] Large classes/methods broken into manageable units

- [ ] Legacy construction patterns replaced with modern Java equivalents

- [ ] Naming aligns with domain language and architecture boundaries

- [ ] Deprecation notices or migration guides drafted where needed

- [ ] Anonymous classes replaced with lambdas where appropriate

### Regression Safety

- [ ] Critical behaviours covered by unit/integration tests

- [ ] Cleanup changes gated by feature flags or staged rollout plans

- [ ] Observatory signals (logs, metrics, traces) updated

- [ ] Stakeholders notified of breaking removals

- [ ] Rollback strategy documented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Java Codebase Cleanup Request

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

Please perform a comprehensive, systematic cleanup of my Java codebase following this protocol:

## Phase 1: Analysis & Safety Check

Before making ANY changes, please:

1. **Analyze the complete codebase structure**
   - Identify all .java files in src/main/java and src/test/java
   - Map dependencies between packages and classes
   - Identify public APIs that must be preserved
   - Check pom.xml or build.gradle for unused dependencies

2. **Generate a detailed cleanup report** listing:
   - Unused imports and static imports
   - Unused fields, methods, and classes
   - Debug System.out.println() statements
   - Empty lines within method bodies
   - Inline and meta-commentary comments
   - Dead code after returns or in unreachable branches
   - Legacy patterns (raw types, old-style loops, null checks)
   - Code smells (god classes, long methods, feature envy)
   - Estimated impact and risk level for each category

3. **Present findings and wait for my approval** before proceeding

## Phase 2: Cleanup Tasks

After I approve, systematically clean the following:

### Multi-Pass Cleanup Protocol

**CRITICAL: Perform multiple passes through the entire codebase to ensure completeness**

1. **First Pass**: Apply all cleanup tasks systematically across the codebase
   - Work through all .java files in src/main/java and src/test/java
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
  - Use IDE inspections or static analysis tools to detect
  - Remove wildcard imports (import java.util.*;) and replace with specific imports

- **Unused fields**: Remove private fields that are assigned but never read

- **Unused methods**: Remove private methods that are never called
  - PRESERVE public and protected methods (may be part of public API or used by subclasses)

- **Unused parameters**: Remove parameters that are defined but never used
  - Consider using @SuppressWarnings("unused") if parameter is required by interface

- **Unused local variables**: Remove variables that are assigned but never used

- **Empty methods**: Remove empty method bodies or replace with appropriate implementations

- **Empty lines within methods**: Remove excessive blank lines inside method bodies
  - KEEP empty lines between logical code sections and between methods

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
  - Javadoc documentation for public APIs

### Debugging & Development Artifacts

- **System.out/err statements**: Remove System.out.println() and System.err.println() used for debugging
  - PRESERVE intentional logging using proper logging frameworks (SLF4J, Log4j)

- **printStackTrace()**: Replace printStackTrace() with proper logging

- **Test-only code**: Remove code marked as temporary test scaffolding

### Additional Cleanup Opportunities

#### Code Quality

- **Redundant code**: Identify and consolidate duplicate methods or logic blocks

- **Dead code after returns**: Remove unreachable code after return statements

- **Unnecessary else**: Simplify if-return patterns that don't need else blocks

- **Trailing whitespace**: Remove whitespace at end of lines

- **Redundant modifiers**: Remove redundant public on interface methods, final on interface fields

- **Empty catch blocks**: Flag or properly handle empty catch blocks

- **Redundant initializations**: Remove explicit initialization to default values (null, 0, false)

#### Import Organization

- **Consolidate imports**: Organize imports in standard order:
  1. Java standard library (java.*)
  2. Java extensions (javax.*)
  3. Third-party libraries (org.*, com.*)
  4. Internal packages

- **Remove wildcard imports**: Replace `import java.util.*;` with specific imports

- **Static imports**: Organize static imports separately

#### Code Modernization (Java 8+)

- **Lambda expressions**: Replace anonymous inner classes with lambdas where appropriate

- **Method references**: Replace lambdas with method references where clearer

- **Streams API**: Replace traditional loops with streams where it improves readability

- **Optional**: Use Optional instead of null checks where appropriate

- **Diamond operator**: Use `<>` for generic type inference (Java 7+)

- **Try-with-resources**: Replace try-finally for AutoCloseable resources (Java 7+)

- **String operations**: Use String.isEmpty() instead of length() == 0

- **Collections**: Replace raw types with generic types

#### Code Modernization (Java 9+)

- **Private interface methods**: Extract duplicate default method logic

- **Collection factories**: Replace verbose collection initialization with List.of(), Set.of(), Map.of()

- **Var keyword**: Use `var` for local variable type inference where appropriate (Java 10+)

- **Switch expressions**: Replace switch statements with expressions (Java 12+)

- **Text blocks**: Replace multi-line string concatenation with text blocks (Java 13+)

- **Records**: Replace simple POJOs with records (Java 14+)

- **Pattern matching**: Use pattern matching for instanceof (Java 14+)

- **Sealed classes**: Apply sealed classes for controlled inheritance (Java 15+)

#### Code Smells

- **Long methods**: Flag methods exceeding 50 lines for potential extraction

- **Long parameter lists**: Suggest parameter objects for methods with >4 parameters

- **God classes**: Identify classes with too many responsibilities

- **Feature envy**: Identify methods that use more data from other classes

- **Data clumps**: Identify groups of parameters that appear together

- **Primitive obsession**: Suggest value objects for primitive types with behavior

- **Inappropriate intimacy**: Identify classes that access each other's internals too much

#### Useless Variables and Properties

Identify and remove variables, properties, and configuration that serve no functional purpose:

- **Ignored CSS/Style Properties**: In custom-painted Swing/JavaFX components
  - CSS properties defined but completely ignored by custom paintComponent() or render() methods
  - Style settings that are overridden by manual Graphics2D drawing
  - JavaFX CSS that has no effect due to custom rendering

- **Dead Configuration Values**: Settings that are defined but never used
  - Unused fields in configuration classes
  - Properties files with unused keys
  - Constants that are never referenced

- **Redundant Constants**: Values that duplicate other constants
  - Multiple constants with identical values
  - Constants that duplicate framework defaults

**Detection Example: Custom Swing Component**

```java
// BEFORE - Useless style properties
public class BadProgressBar extends JProgressBar {
    // ❌ All these properties are IGNORED by custom paintComponent
    private static final Color BORDER_COLOR = new Color(0xd0d0d0);  // Not used
    private static final int BORDER_RADIUS = 12;                     // Not used
    private static final Color BG_COLOR = new Color(0xe5e7eb);      // Not used

    public BadProgressBar() {
        super();
        // CSS-style properties that are ignored
        setBorder(BorderFactory.createLineBorder(BORDER_COLOR));     // IGNORED
        setBackground(BG_COLOR);                                      // IGNORED
    }

    @Override
    protected void paintComponent(Graphics g) {
        // Custom painting bypasses ALL the properties set above
        Graphics2D g2 = (Graphics2D) g;
        g2.setColor(new Color(0xf0f0f0));  // Hardcoded, ignores setBorder/setBackground
        g2.fillRoundedRect(...);
    }
}

// AFTER - Using clear constants
public class GoodProgressBar extends JProgressBar {
    // ✅ Visual properties as clear class constants
    private static final int BORDER_RADIUS = 12;
    private static final Color BORDER_COLOR = new Color(0xd0d0d0);
    private static final Color BACKGROUND_COLOR = new Color(0xe5e7eb);
    private static final Color TEXT_COLOR = new Color(0x2c3e50);

    public GoodProgressBar() {
        super();
        // Only non-visual properties
        setOpaque(false);
    }

    @Override
    protected void paintComponent(Graphics g) {
        Graphics2D g2 = (Graphics2D) g;
        // Use the constants in actual drawing code
        g2.setColor(BACKGROUND_COLOR);
        g2.fillRoundedRect(..., BORDER_RADIUS, BORDER_RADIUS);
        g2.setColor(BORDER_COLOR);
        g2.drawRoundedRect(..., BORDER_RADIUS, BORDER_RADIUS);
    }
}
```

**Why This Matters:**
1. **Clarity**: Visual config is discoverable at class top
2. **Maintainability**: Easy to find and modify appearance constants
3. **No Confusion**: Clear why setBorder/setBackground don't work
4. **IDE Support**: Constants have better autocomplete than method chains

**Detection Strategy:**
1. Find classes that override paintComponent(), paint(), or similar
2. Check for setBorder(), setBackground(), setForeground() calls
3. Verify those properties are used in the paint method
4. Extract hardcoded values to constants, remove useless setter calls
5. Add Javadoc explaining why standard setters aren't used

#### Build & Configuration

- **Unused Maven/Gradle dependencies**: Identify dependencies not used in code

- **Dependency conflicts**: Check for version conflicts or duplicate dependencies

- **Test scope**: Verify test dependencies are correctly scoped

## Phase 3: Verification Protocol

After cleanup, you MUST:

1. **Provide summary** of all changes made, organized by category
2. **Highlight any edge cases** or decisions that required judgment
3. **Request that I run tests and build** to verify nothing broke:
   ```bash
   # Maven
   mvn clean compile
   mvn test
   mvn verify

   # Gradle
   ./gradlew clean build
   ./gradlew test
   ```
4. **Document cleanup** in CHANGELOG.md or development log:
   ```markdown
   ### Code Cleanup - [Date]
   - Removed [X] unused imports
   - Removed [Y] unused methods
   - Removed [Z] System.out.println statements
   - Modernized [N] legacy patterns
   - Additional improvements: [summary]
   ```

## Critical Safety Rules

**DO NOT:**

- Remove any public or protected methods, classes, or fields (they may be used by subclasses or external code)

- Remove Javadoc comments or annotations

- Remove empty lines between methods, classes, or major code sections

- Remove comments that explain business logic or complex algorithms

- Remove constants or configuration values even if seemingly unused

- Remove intentional logging statements using proper frameworks

- Change method signatures or public APIs

- Remove serialVersionUID from Serializable classes

- Make multiple sweeping changes at once - work systematically by category

**ALWAYS:**

- Work on one class at a time or in small logical groups

- Explain any removal that might be ambiguous

- Preserve code functionality - cleanup should never change behavior

- Ask for confirmation if uncertain about removing something

- Track what was removed in case rollback is needed

- Run static analysis tools after changes to verify correctness

- Preserve backward compatibility for public APIs

- Consider reflection usage that might reference seemingly unused methods

## Output Format
Present cleanup in this structure:

- **Cleanup Report - [Category]**

- **File:** path/to/File.java

- **Removals:**
  - Line X: Unused import java.util.List
  - Lines X-Y: Unused private method methodName()
  - Line Z: System.out.println() debugging statement
  - Line N: Inline comment removed

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

- **Unused methods removed:** Z

- **Debug statements removed:** N

- **Lines removed:** M

- **Code reduction:** X%

- **Modernization changes:** P

- **Code smells addressed:** Q

### Useless Code Detection Metrics

- **Useless style properties removed:** R
  - Converted to code constants: S
  - Simply deleted: T

- **Dead configuration removed:** U

- **Redundant constants consolidated:** V

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

- **Javadoc completeness**: Flag public methods/classes missing Javadoc

- **Naming convention audit**: Identify inconsistent naming patterns

- **Complexity analysis**: Flag overly complex methods (cyclomatic complexity > 10)

- **Performance patterns**: Identify inefficient patterns (unnecessary object creation, string concatenation)

- **Immutability**: Suggest making classes/fields immutable where appropriate

- **Thread safety**: Review and flag potential concurrency issues

- **Exception handling**: Review exception handling patterns and suggest improvements

- **Design patterns**: Identify opportunities to apply standard design patterns

- **SOLID principles**: Review adherence to SOLID principles

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
