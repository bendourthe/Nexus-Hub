---
name: cleanup-java
description: Remove dead code, consolidate duplicates, and modernize Java codebases for improved maintainability
version: 1.0.0
author: Benjamin Dourthe
language: Java
category: Code Cleanup
priority: MEDIUM
tags: [java, cleanup, refactoring, modernization, dead-code, streams, lambdas]
template_source: code_cleanup/java_cleanup.md
---

# Java Code Cleanup

Systematically identify and remove dead code, consolidate duplicate logic, and modernize legacy Java patterns to maintain a lean, current, and maintainable codebase.

## When to Use This Skill

Use this skill when you need to:
- Remove unused imports, methods, classes, and fields
- Consolidate duplicate code and near-duplicate implementations
- Modernize legacy patterns (loops to streams, anonymous classes to lambdas, null checks to Optional)
- Clean up System.out.println statements and commented code
- Optimize import organization and code structure
- Prepare codebase for new features or refactoring
- Reduce technical debt before major releases
- Remove unused Maven/Gradle dependencies

## What This Skill Does

This skill performs comprehensive Java code cleanup:

### 1. Dead Code Detection
- **Unused Imports**: Identifies and removes unused import statements
- **Unused Methods**: Finds private methods never called
- **Unused Classes**: Detects classes without instantiation
- **Unused Fields**: Identifies fields assigned but never read
- **Unreachable Code**: Finds code after return/break/continue statements
- **Empty Blocks**: Detects empty methods, classes, or catch blocks
- **Unused Dependencies**: Identifies Maven/Gradle dependencies not used in code

### 2. Duplicate Code Consolidation
- **Exact Duplicates**: Finds identical code blocks for consolidation
- **Near Duplicates**: Detects similar code with minor variations
- **Duplicate Logic**: Identifies functionally equivalent implementations
- **Copy-Paste Detection**: Finds code copied across classes
- **Consolidation Strategy**: Recommends refactoring approach

### 3. Code Modernization (Java 8+)
- **Lambda Expressions**: Converts anonymous classes to lambdas
- **Method References**: Replaces lambdas with method references
- **Streams API**: Modernizes collection processing
- **Optional**: Uses Optional instead of null checks
- **Try-with-resources**: Converts try-finally patterns
- **Diamond Operator**: Uses `<>` for type inference

### 4. Code Modernization (Java 9+)
- **Collection Factories**: Uses List.of(), Set.of(), Map.of()
- **Private Interface Methods**: Extracts duplicate default method logic
- **Var Keyword**: Uses var for local variable type inference (Java 10+)
- **Switch Expressions**: Converts switch statements (Java 12+)
- **Text Blocks**: Uses text blocks for multi-line strings (Java 13+)
- **Records**: Replaces simple POJOs (Java 14+)
- **Pattern Matching**: Uses pattern matching for instanceof (Java 14+)
- **Sealed Classes**: Applies sealed classes for controlled inheritance (Java 15+)

### 5. Debug Statement Cleanup
- **Print Statements**: Removes debug System.out.println()
- **Commented Code**: Cleans up old commented-out code
- **TODO Comments**: Catalogs and prioritizes TODO items
- **printStackTrace**: Replaces with proper logging
- **Temporary Variables**: Identifies debug-only variables

### 6. Import Organization
- **Standard Library**: Groups Java standard library imports
- **Extensions**: Organizes javax.* imports
- **Third-Party**: Structures external dependencies
- **Internal Packages**: Organizes project imports
- **Unused Removal**: Eliminates unnecessary imports
- **Wildcard Imports**: Replaces `import java.util.*;` with specific imports

### 7. Code Simplification
- **Complex Conditionals**: Simplifies nested if/else statements
- **Excessive Nesting**: Reduces deeply nested code
- **Long Methods**: Identifies candidates for decomposition
- **Magic Numbers**: Converts literals to named constants
- **Redundant Code**: Removes unnecessary operations
- **Unnecessary Else**: Simplifies if-return patterns

## Prerequisites

- Java codebase to clean up
- Version control (git) for safe cleanup with rollback capability
- Test suite for regression verification (recommended)
- Backup of codebase or committed state
- Maven or Gradle build system

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
   # Maven
   mvn test

   # Gradle
   ./gradlew test
   ```

4. **Create Output Directory**:
   ```bash
   mkdir -p cleanup_report/{templates,assets,exports}
   ```

### Step 2: Invoke the Cleanup Skill

Tell Claude Code to use this skill:

```
"Use the cleanup-java skill to analyze and clean up this Java codebase.
Focus on:
1. Removing all unused imports, methods, and fields
2. Consolidating duplicate code
3. Modernizing to Java 8+ patterns (streams, lambdas, Optional)
4. Removing System.out.println statements
5. Organizing imports properly
6. Identifying unused Maven/Gradle dependencies

Save all reports to cleanup_report/ directory."
```

### Step 3: Review Cleanup Plan

Claude Code will generate a comprehensive cleanup plan including:

1. **Dead Code Candidates** - List of unused code with usage analysis
2. **Duplication Report** - Duplicate code locations with consolidation strategy
3. **Modernization Opportunities** - Legacy patterns to update
4. **Code Smells** - God classes, long methods, feature envy
5. **Risk Assessment** - Impact analysis for each cleanup operation
6. **Implementation Plan** - Ordered steps with dependencies

**Review the plan before proceeding with changes!**

### Step 4: Execute Cleanup in Phases

The skill will execute cleanup in safe phases:

**Phase 1: Low-Risk Cleanup**
- Remove unused imports
- Clean System.out.println statements
- Remove commented code
- Organize imports

**Phase 2: Code Modernization**
- Convert to lambda expressions
- Apply method references
- Use streams API
- Apply Optional for null handling
- Use try-with-resources

**Phase 3: Structural Changes**
- Consolidate duplicates
- Remove dead methods
- Simplify complex code
- Extract constants

**Phase 4: Verification**
- Run tests after each phase
- Run static analysis tools
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
   # Maven
   mvn clean test
   mvn verify

   # Gradle
   ./gradlew clean test
   ```

2. **Static Analysis**:
   ```bash
   # Maven with SpotBugs
   mvn spotbugs:check

   # Maven with Checkstyle
   mvn checkstyle:check

   # Gradle
   ./gradlew check
   ```

3. **Build Verification**:
   ```bash
   # Maven
   mvn clean package

   # Gradle
   ./gradlew build
   ```

4. **Manual Testing** (if no automated tests):
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
   git commit -m "Remove unused imports and methods"

   git add src/
   git commit -m "Modernize to Java 8 streams and lambdas"

   git add src/
   git commit -m "Consolidate duplicate validation logic"
   ```

3. **Update Dependencies** (if needed):
   ```bash
   # Maven - manually edit pom.xml
   git add pom.xml
   git commit -m "Remove unused Maven dependencies"

   # Gradle - manually edit build.gradle
   git add build.gradle
   git commit -m "Remove unused Gradle dependencies"
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
```java
import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import com.fasterxml.jackson.databind.ObjectMapper;

public class DataProcessor {
    public String processData(String data) {
        return data.toUpperCase();
    }
}
```

**After:**
```java
public class DataProcessor {
    public String processData(String data) {
        return data.toUpperCase();
    }
}
```

### Category 2: Debug Statements
**Before:**
```java
public double calculateTotal(List<Item> items) {
    System.out.println("DEBUG: items = " + items);
    double total = items.stream()
        .mapToDouble(Item::getPrice)
        .sum();
    System.out.println("DEBUG: total = " + total);
    return total;
}
```

**After:**
```java
public double calculateTotal(List<Item> items) {
    return items.stream()
        .mapToDouble(Item::getPrice)
        .sum();
}
```

### Category 3: Lambda Expressions and Streams
**Before:**
```java
List<String> names = new ArrayList<>();
for (User user : users) {
    if (user.isActive()) {
        names.add(user.getName());
    }
}
Collections.sort(names);

button.addActionListener(new ActionListener() {
    @Override
    public void actionPerformed(ActionEvent e) {
        handleClick(e);
    }
});
```

**After:**
```java
List<String> names = users.stream()
    .filter(User::isActive)
    .map(User::getName)
    .sorted()
    .collect(Collectors.toList());

button.addActionListener(e -> handleClick(e));
// or even better with method reference:
button.addActionListener(this::handleClick);
```

### Category 4: Optional Instead of Null Checks
**Before:**
```java
public String getUserName(Long userId) {
    User user = userRepository.findById(userId);
    if (user != null) {
        return user.getName();
    }
    return "Anonymous";
}
```

**After:**
```java
public String getUserName(Long userId) {
    return userRepository.findById(userId)
        .map(User::getName)
        .orElse("Anonymous");
}
```

### Category 5: Try-with-Resources
**Before:**
```java
BufferedReader reader = null;
try {
    reader = new BufferedReader(new FileReader("data.txt"));
    String line = reader.readLine();
    return line;
} catch (IOException e) {
    throw new RuntimeException(e);
} finally {
    if (reader != null) {
        try {
            reader.close();
        } catch (IOException e) {
            // ignore
        }
    }
}
```

**After:**
```java
try (BufferedReader reader = new BufferedReader(new FileReader("data.txt"))) {
    return reader.readLine();
} catch (IOException e) {
    throw new RuntimeException(e);
}
```

### Category 6: Duplicate Code Consolidation
**Before:**
```java
public boolean validateUser(User user) {
    if (user.getName() == null || user.getName().isEmpty()) {
        return false;
    }
    if (user.getEmail() == null || user.getEmail().isEmpty()) {
        return false;
    }
    if (!user.getEmail().contains("@")) {
        return false;
    }
    return true;
}

public boolean validateAdmin(Admin admin) {
    if (admin.getName() == null || admin.getName().isEmpty()) {
        return false;
    }
    if (admin.getEmail() == null || admin.getEmail().isEmpty()) {
        return false;
    }
    if (!admin.getEmail().contains("@")) {
        return false;
    }
    return true;
}
```

**After:**
```java
public interface Account {
    String getName();
    String getEmail();
}

public boolean validateAccount(Account account) {
    if (account.getName() == null || account.getName().isEmpty()) {
        return false;
    }
    if (account.getEmail() == null || account.getEmail().isEmpty()) {
        return false;
    }
    if (!account.getEmail().contains("@")) {
        return false;
    }
    return true;
}

// User and Admin implement Account interface
```

### Category 7: Modern Java Features (Java 14+)
**Before:**
```java
// Old instanceof check
if (obj instanceof String) {
    String str = (String) obj;
    System.out.println(str.length());
}

// Old POJO
public class Point {
    private final int x;
    private final int y;

    public Point(int x, int y) {
        this.x = x;
        this.y = y;
    }

    public int getX() { return x; }
    public int getY() { return y; }

    @Override
    public boolean equals(Object o) { /* ... */ }
    @Override
    public int hashCode() { /* ... */ }
}
```

**After:**
```java
// Pattern matching for instanceof (Java 14+)
if (obj instanceof String str) {
    System.out.println(str.length());
}

// Record (Java 14+)
public record Point(int x, int y) {}
```

### Category 8: Useless Variables and Properties
**Before:**
```java
// Swing component with ignored properties
public class BadProgressBar extends JProgressBar {
    // All these are IGNORED by custom paintComponent
    private static final Color BORDER_COLOR = new Color(0xd0d0d0);
    private static final int BORDER_RADIUS = 12;

    public BadProgressBar() {
        super();
        setBorder(BorderFactory.createLineBorder(BORDER_COLOR)); // IGNORED
        setBackground(new Color(0xe5e7eb)); // IGNORED
    }

    @Override
    protected void paintComponent(Graphics g) {
        Graphics2D g2 = (Graphics2D) g;
        g2.setColor(new Color(0xf0f0f0)); // Hardcoded
        g2.fillRoundedRect(0, 0, getWidth(), getHeight(), 12, 12);
    }
}
```

**After:**
```java
// Clear constants at class top
public class GoodProgressBar extends JProgressBar {
    private static final int BORDER_RADIUS = 12;
    private static final Color BORDER_COLOR = new Color(0xd0d0d0);
    private static final Color BACKGROUND_COLOR = new Color(0xe5e7eb);

    public GoodProgressBar() {
        super();
        setOpaque(false); // Only non-visual properties
    }

    @Override
    protected void paintComponent(Graphics g) {
        Graphics2D g2 = (Graphics2D) g;
        g2.setColor(BACKGROUND_COLOR); // Use constants
        g2.fillRoundedRect(0, 0, getWidth(), getHeight(), BORDER_RADIUS, BORDER_RADIUS);
        g2.setColor(BORDER_COLOR);
        g2.drawRoundedRect(0, 0, getWidth(), getHeight(), BORDER_RADIUS, BORDER_RADIUS);
    }
}
```

## Output Structure

The skill generates organized output in `cleanup_report/`:

```
cleanup_report/
├── templates/
│   ├── cleanup_checklist.md       # Reusable cleanup checklist
│   ├── modernization_guide.md     # Java modernization patterns
│   └── checkstyle_config.xml      # Recommended Checkstyle config
├── assets/
│   ├── duplication_graph.png      # Visual duplication analysis
│   ├── complexity_heatmap.png     # Code complexity visualization
│   └── dependency_graph.png       # Dependency analysis
└── exports/
    ├── cleanup_report.md           # Comprehensive cleanup report
    ├── dead_code_list.md           # Dead code candidates
    ├── duplication_analysis.md     # Duplicate code analysis
    ├── modernization_plan.md       # Modernization strategy
    ├── code_smells.md              # Code smell analysis
    ├── unused_dependencies.md      # Unused Maven/Gradle deps
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
- Check for reflection usage
- Verify serialization requirements
- Look for Spring/DI framework usage
- Keep code if uncertain

### Issue: Import Organization Breaks Code
**Solution**:
- Check for static imports conflicts
- Verify class name conflicts
- Keep original organization if needed
- Document special requirements

### Issue: Modernization Changes Behavior
**Solution**:
- Review Java version compatibility
- Check for subtle semantic differences (e.g., exception handling in streams)
- Test edge cases thoroughly
- Revert if behavior changes

### Issue: Compilation Errors After Changes
**Solution**:
- Run `mvn clean compile` or `./gradlew clean build`
- Fix errors incrementally
- Consider Java version compatibility
- Check for missing dependencies

## Success Criteria

After using this skill, your codebase should have:

- [ ] All unused imports removed
- [ ] No System.out.println debugging statements
- [ ] No commented-out code (except strategic comments)
- [ ] Duplicate code consolidated where appropriate
- [ ] Modern Java patterns applied (streams, lambdas, Optional)
- [ ] Imports organized properly (java → javax → third-party → internal)
- [ ] Unused dependencies identified or removed
- [ ] All tests passing
- [ ] All static analysis checks passing
- [ ] Code builds successfully
- [ ] Cleanup documented in DEVLOG.md
- [ ] Changes committed to version control

## Related Skills

- `setup-java-system-prompt`: Establish standards before cleanup
- `code-review-quality`: Review code quality after cleanup
- `generate-test-cases`: Create tests for newly consolidated code
- `generate-javadoc`: Document cleaned-up code

## Tools and Libraries

### Static Analysis Tools
- **Checkstyle**: Style checking
- **PMD**: Code analysis
- **SpotBugs**: Bug detection
- **SonarQube**: Comprehensive analysis

### Duplication Detection
- **CPD** (Copy/Paste Detector): Part of PMD
- **Simian**: Similarity analysis

### Unused Code Detection
- **Maven Dependency Plugin**: Dependency analysis
- **Gradle unused-dependencies**: Unused dependency detection

### Installation and Usage

**Maven (pom.xml)**:
```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-checkstyle-plugin</artifactId>
    <version>3.2.0</version>
</plugin>
<plugin>
    <groupId>com.github.spotbugs</groupId>
    <artifactId>spotbugs-maven-plugin</artifactId>
    <version>4.7.3.0</version>
</plugin>
```

**Gradle (build.gradle)**:
```groovy
plugins {
    id 'checkstyle'
    id 'pmd'
    id 'com.github.spotbugs' version '5.0.13'
}
```

**Running Tools**:
```bash
# Maven
mvn checkstyle:check
mvn pmd:check
mvn spotbugs:check
mvn dependency:analyze

# Gradle
./gradlew checkstyleMain
./gradlew pmdMain
./gradlew spotbugsMain
```

## Additional Resources

- [Effective Java (3rd Edition) by Joshua Bloch](https://www.oreilly.com/library/view/effective-java-3rd/9780134686097/)
- [Refactoring to Streams and Lambdas](https://www.oracle.com/technical-resources/articles/java/ma14-java-se-8-streams.html)
- [Java Code Conventions](https://www.oracle.com/java/technologies/javase/codeconventions-contents.html)
- [Modern Java in Action](https://www.manning.com/books/modern-java-in-action)
- [Java Design Patterns](https://java-design-patterns.com/)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5 - code_cleanup/java_cleanup.md
