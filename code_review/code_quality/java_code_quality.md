# Java Code Quality Review

## Objective
Systematically evaluate code maintainability, readability, and adherence to Java best practices. Identify technical debt, complexity hotspots, and areas requiring refactoring to improve long-term codebase health.

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
- [ ] Java naming conventions verified (camelCase, PascalCase, UPPER_CASE)
- [ ] Import organization follows standard order
- [ ] JavaDoc format consistent for public APIs
- [ ] Code formatting consistent (Google Style, Oracle conventions)
- [ ] Package structure follows domain organization

### Code Complexity
- [ ] Methods under 30 lines (flagged if exceeded)
- [ ] Cyclomatic complexity under 10 per method
- [ ] Nesting depth under 4 levels
- [ ] Class size reasonable (<300 lines)
- [ ] Package cohesion evaluated

### Design & Architecture
- [ ] SOLID principles followed
- [ ] DRY principle applied (no significant duplication)
- [ ] Separation of concerns maintained
- [ ] Appropriate use of design patterns
- [ ] Dependency injection properly used

### Code Smells
- [ ] Long parameter lists identified (>5 parameters)
- [ ] Feature envy detected
- [ ] God classes or services identified
- [ ] Primitive obsession checked
- [ ] Dead code marked for removal

### Error Handling
- [ ] Exceptions used appropriately (checked vs unchecked)
- [ ] Custom exceptions defined when needed
- [ ] Try-with-resources used for AutoCloseable
- [ ] Exception messages informative
- [ ] Logging appropriate for debugging

### Java-Specific Practices
- [ ] Effective use of Java 8+ features (streams, lambdas, Optional)
- [ ] Proper use of generics
- [ ] Equals/hashCode consistency
- [ ] Thread safety considered
- [ ] Resource management (try-with-resources)

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Java Code Quality Review

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

Please perform a comprehensive code quality review of this Java project following this protocol:

## Phase 1: Coding Standards Assessment

1. **Checkstyle Analysis**
   ```bash
   # Run Checkstyle (Maven)
   mvn checkstyle:check

   # Generate Checkstyle report
   mvn checkstyle:checkstyle

   # For Gradle
   ./gradlew checkstyleMain checkstyleTest
   ```

2. **Style Violations Analysis**
   - Document most common violations
   - Identify patterns of non-compliance
   - Assess consistency across packages
   - Flag formatting inconsistencies
   - Review against Google Java Style or Oracle conventions

3. **Naming Convention Review**
   - Verify method names are descriptive and camelCase
   - Check class names use PascalCase
   - Confirm constants use UPPER_SNAKE_CASE
   - Review package naming (lowercase, domain-based)
   - Identify unclear or abbreviated names

## Phase 2: Static Analysis

1. **PMD Analysis**
   ```bash
   # Run PMD (Maven)
   mvn pmd:check

   # Generate PMD report
   mvn pmd:pmd

   # For Gradle
   ./gradlew pmdMain pmdTest
   ```

2. **SpotBugs/FindBugs Analysis**
   ```bash
   # Run SpotBugs (Maven)
   mvn spotbugs:check

   # Generate SpotBugs report
   mvn spotbugs:spotbugs

   # For Gradle
   ./gradlew spotbugsMain spotbugsTest
   ```

3. **SonarQube Analysis** (if available)
   ```bash
   # Run SonarQube analysis
   mvn sonar:sonar -Dsonar.host.url=http://localhost:9000

   # Or for Gradle
   ./gradlew sonarqube
   ```

## Phase 3: Complexity Analysis

1. **Method-Level Complexity**
   ```bash
   # Calculate cyclomatic complexity with PMD
   mvn pmd:check -Dpmd.analysisCache=false

   # Or use JaCoCo for complexity metrics
   mvn jacoco:prepare-agent test jacoco:report
   ```

2. **Identify Complexity Hotspots**
   - List methods with complexity >10
   - Flag methods longer than 30 lines
   - Identify deeply nested code (>4 levels)
   - Document complex conditional logic
   - Review switch statements with many cases

3. **Class-Level Analysis**
   - Assess class size and cohesion
   - Identify classes with too many responsibilities
   - Check coupling between classes
   - Evaluate package organization
   - Review class hierarchies depth

## Phase 4: Design Quality Review

1. **SOLID Principles**
   - **Single Responsibility**: Check if classes have one clear purpose
   - **Open/Closed**: Evaluate extensibility without modification
   - **Liskov Substitution**: Review inheritance hierarchies
   - **Interface Segregation**: Check for lean interfaces
   - **Dependency Inversion**: Assess dependency on abstractions

2. **DRY Violations**
   ```bash
   # Check for code duplication using PMD CPD
   mvn pmd:cpd-check

   # Or use SonarQube duplication detection
   ```
   - Identify duplicated logic
   - Find near-duplicate methods
   - Document consolidation opportunities
   - Check for copy-paste programming

3. **Design Patterns**
   - Identify patterns in use (factory, builder, strategy, observer)
   - Assess pattern appropriateness
   - Flag pattern misuse or over-engineering
   - Suggest beneficial pattern applications
   - Review Spring stereotypes usage (@Service, @Repository, @Component)

## Phase 5: Java-Specific Best Practices

1. **Modern Java Features (Java 8+)**
   ```java
   // Check for opportunities to use:

   // 1. Stream API instead of loops
   // Bad
   List<String> result = new ArrayList<>();
   for (User user : users) {
       if (user.isActive()) {
           result.add(user.getName());
       }
   }
   // Good
   List<String> result = users.stream()
       .filter(User::isActive)
       .map(User::getName)
       .collect(Collectors.toList());

   // 2. Optional instead of null checks
   // Bad
   public String getUserEmail(Long id) {
       User user = findUser(id);
       if (user != null) {
           return user.getEmail();
       }
       return "unknown@example.com";
   }
   // Good
   public String getUserEmail(Long id) {
       return findUser(id)
           .map(User::getEmail)
           .orElse("unknown@example.com");
   }

   // 3. Lambdas instead of anonymous classes
   // Bad
   button.addActionListener(new ActionListener() {
       @Override
       public void actionPerformed(ActionEvent e) {
           handleClick();
       }
   });
   // Good
   button.addActionListener(e -> handleClick());

   // 4. Method references where applicable
   list.forEach(item -> System.out.println(item));  // Can use method reference
   list.forEach(System.out::println);  // Better
   ```

2. **Object-Oriented Principles**
   ```java
   // Check for:

   // 1. Proper equals/hashCode implementation
   @Override
   public boolean equals(Object o) {
       if (this == o) return true;
       if (o == null || getClass() != o.getClass()) return false;
       User user = (User) o;
       return Objects.equals(id, user.id);
   }

   @Override
   public int hashCode() {
       return Objects.hash(id);
   }

   // 2. Proper toString implementation
   @Override
   public String toString() {
       return "User{id=" + id + ", name='" + name + "'}";
   }

   // 3. Immutability where beneficial
   public final class ImmutableUser {
       private final Long id;
       private final String name;
       // Constructor, getters, no setters
   }
   ```

3. **Generics Usage**
   - Check for raw types (should use generics)
   - Verify proper use of wildcards (? extends, ? super)
   - Assess type safety
   - Review collections with proper type parameters

## Phase 6: Code Smell Detection

1. **Common Java Code Smells**
   - **Long Method**: Methods exceeding 30 lines
   - **Large Class**: Classes with >300 lines or >20 methods
   - **Long Parameter List**: Methods with >5 parameters
   - **Data Clumps**: Same groups of parameters appearing together
   - **Primitive Obsession**: Using primitives instead of objects
   - **Switch Statements**: Can often be replaced with polymorphism
   - **Temporary Field**: Fields only used in certain circumstances

2. **Anti-Patterns**
   - God objects/classes
   - Circular dependencies
   - Lava flow (dead/obsolete code)
   - Copy-paste programming
   - Magic numbers and strings
   - Anemic domain model
   - Service layer overuse

3. **Java-Specific Issues**
   ```java
   // Issues to search for:

   // 1. String concatenation in loops (use StringBuilder)
   String result = "";
   for (String s : strings) {
       result += s;  // BAD: Creates new string each iteration
   }

   // 2. Catching generic exceptions
   try {
       // code
   } catch (Exception e) {  // BAD: Too broad
       // handle
   }

   // 3. Empty catch blocks
   try {
       // code
   } catch (IOException e) {
       // BAD: Silent failure
   }

   // 4. Not using try-with-resources
   BufferedReader br = new BufferedReader(new FileReader(file));
   try {
       // use br
   } finally {
       br.close();  // BAD: Should use try-with-resources
   }

   // 5. Unnecessary boxing/unboxing
   Integer count = new Integer(5);  // BAD: Use Integer.valueOf(5) or just 5
   ```

## Phase 7: Spring Boot Specific (if applicable)

1. **Spring Stereotypes**
   - Verify proper use of @Service, @Repository, @Component
   - Check @Controller vs @RestController usage
   - Review @Configuration classes
   - Assess @Bean definitions

2. **Dependency Injection**
   - Prefer constructor injection over field injection
   - Avoid circular dependencies
   - Use @Qualifier when needed
   - Review @Autowired usage

3. **Spring Best Practices**
   ```java
   // Good practices:

   // 1. Constructor injection (recommended)
   @Service
   public class UserService {
       private final UserRepository repository;

       public UserService(UserRepository repository) {
           this.repository = repository;
       }
   }

   // 2. Proper REST controller design
   @RestController
   @RequestMapping("/api/users")
   public class UserController {
       private final UserService userService;

       public UserController(UserService userService) {
           this.userService = userService;
       }

       @GetMapping("/{id}")
       public ResponseEntity<UserDto> getUser(@PathVariable Long id) {
           return userService.findById(id)
               .map(ResponseEntity::ok)
               .orElse(ResponseEntity.notFound().build());
       }
   }

   // 3. Proper exception handling
   @ControllerAdvice
   public class GlobalExceptionHandler {
       @ExceptionHandler(ResourceNotFoundException.class)
       public ResponseEntity<ErrorResponse> handleNotFound(ResourceNotFoundException ex) {
           return ResponseEntity.status(HttpStatus.NOT_FOUND)
               .body(new ErrorResponse(ex.getMessage()));
       }
   }
   ```

## Phase 8: Documentation Quality

1. **JavaDoc Coverage**
   ```bash
   # Generate JavaDoc
   mvn javadoc:javadoc

   # Check for missing JavaDoc
   mvn javadoc:javadoc -Xdoclint:all
   ```
   - Measure public API JavaDoc presence
   - Assess JavaDoc completeness
   - Verify parameter documentation
   - Check return value documentation
   - Review exception documentation

2. **Comment Quality**
   - Evaluate comment necessity and clarity
   - Flag commented-out code for removal
   - Check for TODO/FIXME/XXX comments
   - Verify comments explain "why" not "what"

## Output Format

Please provide a comprehensive quality report with the following structure:

### Executive Summary
- **Overall Quality Score**: [A-F grade]
- **Maintainability Index**: [score]
- **Average Complexity**: [cyclomatic complexity]
- **Critical Issues**: [count]
- **Technical Debt**: [estimated hours to address]

### Coding Standards Compliance
- **Checkstyle Violations**: [count and severity]
- **Most Common Issues**:
  1. [Issue type] - [count] occurrences
  2. [Issue type] - [count] occurrences
- **Consistency Score**: [percentage]

### Static Analysis Results
**PMD Findings**:
| Priority | Count | Top Issues |
|----------|-------|------------|
| High | [count] | [issue types] |
| Medium | [count] | [issue types] |
| Low | [count] | [issue types] |

**SpotBugs Findings**:
| Category | Count | Examples |
|----------|-------|----------|
| Correctness | [count] | [specific bugs] |
| Bad Practice | [count] | [specific issues] |
| Performance | [count] | [specific issues] |

### Complexity Analysis
**High Complexity Methods** (Cyclomatic Complexity >10):
| Method | Class | Complexity | Lines | Recommendation |
|--------|-------|------------|-------|----------------|
| [name] | [class] | [score] | [count] | [refactor suggestion] |

**Large Classes** (>300 lines):
| Class | Lines | Methods | Fields | Recommendation |
|-------|-------|---------|--------|----------------|
| [name] | [count] | [count] | [count] | [split suggestion] |

### Design Quality Issues
1. **SOLID Violations**:
   - [Principle]: [specific examples and impact]

2. **DRY Violations**:
   - [Location]: [description of duplication]
   - **Consolidation Opportunity**: [suggestion]

3. **Missing or Misused Patterns**:
   - [Location]: [pattern suggestion or misuse]

### Code Smells Identified
| Smell Type | Location | Severity | Description | Remediation |
|------------|----------|----------|-------------|-------------|
| [type] | [class:method] | [High/Med/Low] | [details] | [suggestion] |

### Java Best Practices Assessment
- **Modern Java Features Usage**: [Excellent/Good/Poor]
- **Stream API Adoption**: [percentage of opportunities used]
- **Optional Usage**: [appropriate/overused/underused]
- **Lambda Expressions**: [appropriate/could improve]
- **Generics**: [properly used/needs improvement]

### Spring Boot Best Practices** (if applicable)
- **Dependency Injection**: [constructor/field - recommendation]
- **Stereotype Annotations**: [appropriate/inconsistent]
- **Exception Handling**: [centralized/scattered]
- **REST API Design**: [RESTful/needs improvement]

### Documentation Score
- **JavaDoc Coverage**: [percentage]
- **Public API Documentation**: [comprehensive/partial/missing]
- **Comment Quality**: [Good/Fair/Poor]
- **Areas Needing Documentation**: [list]

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
- [ ] Implement automated quality gates (Checkstyle, PMD, SpotBugs)
- [ ] Plan refactoring sprints for high-priority technical debt
- [ ] Establish team coding standards documentation
- [ ] Set up pre-commit hooks for style enforcement
- [ ] Configure SonarQube for continuous monitoring

## Automation Recommendations
Suggest tools and configuration for continuous quality monitoring:

```xml
<!-- Maven pom.xml plugins -->
<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-checkstyle-plugin</artifactId>
            <version>3.3.0</version>
            <configuration>
                <configLocation>google_checks.xml</configLocation>
                <failOnViolation>true</failOnViolation>
            </configuration>
        </plugin>

        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-pmd-plugin</artifactId>
            <version>3.21.0</version>
        </plugin>

        <plugin>
            <groupId>com.github.spotbugs</groupId>
            <artifactId>spotbugs-maven-plugin</artifactId>
            <version>4.7.3.6</version>
        </plugin>
    </plugins>
</build>
```

```groovy
// Gradle build.gradle
plugins {
    id 'checkstyle'
    id 'pmd'
    id 'com.github.spotbugs' version '5.0.14'
}

checkstyle {
    toolVersion = '10.12.0'
    configFile = file("${rootDir}/config/checkstyle/checkstyle.xml")
}

pmd {
    ruleSets = []
    ruleSetFiles = files("${rootDir}/config/pmd/ruleset.xml")
}

spotbugs {
    effort = 'max'
    reportLevel = 'low'
}
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
