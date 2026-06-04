---
name: java-cleanup
description: Remove dead code, update deprecated APIs, apply modern Java patterns, and clean up Java codebases. Use when cleaning up Java projects, removing unused imports, modernizing legacy Java code, or improving code maintainability.
summary_l0: "Clean up Java codebases with modern patterns, deprecated API updates, and dead code removal"
overview_l1: "This skill systematically identifies and removes dead code, updates deprecated APIs, and applies modern Java patterns to maintain a clean, maintainable codebase. Use it when removing unused imports and dead code, updating deprecated API usage, applying modern Java features (Java 8+), fixing Checkstyle/PMD issues, or preparing Java code for review. Key capabilities include dead code detection and removal, deprecated API migration, modern Java feature adoption (streams, Optional, records, sealed classes, pattern matching), Checkstyle and PMD integration, import optimization, and code duplication elimination. The expected output is a modernized Java codebase with updated APIs, modern language features, and resolved static analysis warnings. Trigger phrases: cleanup Java, remove dead code Java, modernize Java, fix Checkstyle, Java refactor."
---

# Java Code Cleanup

Systematically identify and remove dead code, update deprecated APIs, and apply modern Java patterns to maintain a clean, maintainable codebase.

## When to Use This Skill

Use this skill when you need to:

- Remove unused imports and dead code
- Update deprecated API usage
- Apply modern Java features (8+)
- Fix Checkstyle/PMD issues
- Clean up before code review

**Trigger phrases**: "cleanup Java", "remove dead code Java", "modernize Java", "fix Checkstyle", "Java refactor"

## What This Skill Does

### Cleanup Areas

1. **Dead Code Removal**
   - Unused imports
   - Unused private methods
   - Unreachable code
   - Redundant code

2. **Style Compliance**
   - Checkstyle rules
   - PMD/SpotBugs
   - Naming conventions

3. **Modernization**
   - Streams API
   - Optional
   - var keyword
   - Records (Java 14+)

## Instructions

### Step 1: Run Analysis Tools

```bash
# Run Checkstyle
mvn checkstyle:check

# Run PMD
mvn pmd:check

# Run SpotBugs
mvn spotbugs:check
```

### Step 2: Modernize Patterns

```java
// Traditional loop → Stream
// Before
List<String> names = new ArrayList<>();
for (User user : users) {
    if (user.isActive()) {
        names.add(user.getName());
    }
}
// After
List<String> names = users.stream()
    .filter(User::isActive)
    .map(User::getName)
    .collect(Collectors.toList());

// Null checks → Optional
// Before
String name = user != null ? user.getName() : "Unknown";
// After
String name = Optional.ofNullable(user)
    .map(User::getName)
    .orElse("Unknown");

// Anonymous class → Lambda
// Before
button.addActionListener(new ActionListener() {
    @Override
    public void actionPerformed(ActionEvent e) {
        handleClick(e);
    }
});
// After
button.addActionListener(e -> handleClick(e));

// Data class → Record (Java 14+)
// Before
public class User {
    private final String name;
    private final String email;
    // constructor, getters, equals, hashCode, toString
}
// After
public record User(String name, String email) {}
```

## Tools

- **Checkstyle**: Style checking
- **PMD**: Static analysis
- **SpotBugs**: Bug detection
- **IntelliJ Inspections**: IDE analysis

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "A for-loop is clearer than a stream here" | A manual loop that accumulates into a mutable list hides the null-handling and filtering logic a stream makes explicit; Optional and stream pipelines remove the NullPointerException paths the loop quietly carried. |
| "The deprecated method still works, leave it" | A @Deprecated API is flagged for removal in a future JDK; the upgrade that drops it will then break the build at the worst possible moment. Migrate while the deprecation warning still points at the call. |
| "Checkstyle failures are just formatting, I'll skip them" | Checkstyle and PMD catch real defects (empty catch blocks, unused assignments, missing equals/hashCode), not only style. A green build with PMD warnings is shipping known latent bugs. |
| "I'll catch Exception broadly to be safe" | A broad catch swallows the InterruptedException and the programming error you needed to see, turning a crash into silent data corruption. Catch the specific exception and rethrow or log the rest. |

## Verification

- [ ] Checkstyle passes: `mvn checkstyle:check` succeeds
- [ ] PMD passes: `mvn pmd:check` reports no violations
- [ ] SpotBugs passes: `mvn spotbugs:check` reports no bugs
- [ ] All deprecated API call sites flagged by the compiler have been migrated
- [ ] No empty or overly broad catch blocks remain; exceptions are handled or rethrown specifically
- [ ] All existing tests pass: `mvn test`

## Related Skills

- [[code-quality]] -- score the cleaned codebase against SOLID and complexity metrics
- [[security-review]] -- security analysis for deserialization and input-handling paths
- [[java-expert]] -- idiomatic modern Java (streams, Optional, records) this cleanup applies
- [[deprecated-api-updater]] -- systematic migration of the deprecated Java API calls this skill flags

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Based on**: AI Templates code_cleanup/java_cleanup.md


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
