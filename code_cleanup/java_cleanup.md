# Code Cleanup & Refactoring Review - Java

## Objective
Identify and eliminate dead code, duplication, and legacy patterns so the codebase remains lean, maintainable, and aligned with current architecture decisions. Focus on Java-specific issues including unused imports, code smells, and modern Java patterns.

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

- **Total files processed:** X
- **Unused imports removed:** Y
- **Unused methods removed:** Z
- **Debug statements removed:** N
- **Lines removed:** M
- **Code reduction:** X%
- **Modernization changes:** P
- **Code smells addressed:** Q

**Overall Impact:** [Low/Medium/High risk assessment]

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
