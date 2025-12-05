---
template_id: java_code_coverage
template_name: Code Coverage - Java
version: 1.0.0
last_updated: 2025-12-03
language: Java
category: tests_generation
phase: code_coverage
phase_number: 6
difficulty: intermediate
estimated_time_hours: 2-3
prerequisites:

  - tests_generation/performance_testing/java_performance_testing.md
related_templates:

  - tests_generation/maintenance_cicd/java_maintenance_cicd.md
tools:

  - junit (5.11.3)

  - maven

  - gradle
tags:

  - test-development

  - java
---
# Java Code Coverage Analysis

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                            ► │ [COMPLETE]
│ Phase 3: Test Cases Development                ► │ [COMPLETE]
│ Phase 4: Mocks & Fixtures                      ► │ [COMPLETE]
│ Phase 5: Performance Testing                   ► │ [COMPLETE]
│ Phase 6: Code Coverage                          ► │ ● CURRENT
│ Phase 7: Maintenance & CI/CD                       ► │ [NEXT]
│ Phase 8: Reward Hacking Validation                       ► │ 
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 5 (Performance Testing) should be completed first
**Next Step:** Phase 7 (Maintenance & CI/CD)

---


## Objective
Implement comprehensive code coverage measurement using JaCoCo and Cobertura, analyze coverage gaps, establish coverage goals (80%+ target), create systematic improvement strategies, integrate coverage into CI/CD, and maintain high-quality test coverage for Java projects.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/code_coverage/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/code_coverage/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Coverage Setup

- [ ] JaCoCo or Cobertura installed and configured

- [ ] Maven/Gradle integration enabled

- [ ] Coverage configuration file created

- [ ] HTML report generation configured

- [ ] CI/CD coverage reporting set up

### Coverage Analysis

- [ ] Current coverage baseline measured

- [ ] Coverage gaps identified and prioritized

- [ ] Critical paths coverage verified

- [ ] Edge cases coverage assessed

- [ ] Untested code documented

### Coverage Goals

- [ ] Target coverage defined (80%+ recommended)

- [ ] Coverage thresholds set by module

- [ ] Critical path coverage requirements established

- [ ] Coverage improvement plan created

- [ ] Timeline for improvements defined

### Coverage Integration

- [ ] Coverage gates in CI/CD configured

- [ ] Coverage reports automated

- [ ] Coverage trends tracked

- [ ] Coverage regression prevention enabled

- [ ] Team coverage standards documented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Java Code Coverage Implementation

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/code_coverage"
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

Please implement comprehensive code coverage measurement and improvement for this Java project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: Coverage Setup and Configuration

### Install Coverage Tools

**Maven with JaCoCo**:

Add to `pom.xml`:
```xml
<project>
  <build>
    <plugins>
      <plugin>
        <groupId>org.jacoco</groupId>
        <artifactId>jacoco-maven-plugin</artifactId>
        <version>0.8.11</version>
        <executions>
          <!-- Prepare agent for test execution -->
          <execution>
            <id>prepare-agent</id>
            <goals>
              <goal>prepare-agent</goal>
            </goals>
          </execution>

          <!-- Generate report after tests -->
          <execution>
            <id>report</id>
            <phase>test</phase>
            <goals>
              <goal>report</goal>
            </goals>
          </execution>

          <!-- Check coverage thresholds -->
          <execution>
            <id>check</id>
            <goals>
              <goal>check</goal>
            </goals>
            <configuration>
              <rules>
                <rule>
                  <element>BUNDLE</element>
                  <limits>
                    <limit>
                      <counter>LINE</counter>
                      <value>COVEREDRATIO</value>
                      <minimum>0.80</minimum>
                    </limit>
                    <limit>
                      <counter>BRANCH</counter>
                      <value>COVEREDRATIO</value>
                      <minimum>0.80</minimum>
                    </limit>
                  </limits>
                </rule>
              </rules>
            </configuration>
          </execution>
        </executions>
        <configuration>
          <excludes>
            <exclude>**/config/**</exclude>
            <exclude>**/dto/**</exclude>
            <exclude>**/entity/**</exclude>
            <exclude>**/Application.class</exclude>
          </excludes>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
```

**Gradle with JaCoCo**:

Add to `build.gradle`:
```groovy
plugins {
    id 'java'
    id 'jacoco'
}

jacoco {
    toolVersion = "0.8.11"
}

test {
    finalizedBy jacocoTestReport
}

jacocoTestReport {
    dependsOn test
    reports {
        xml.required = true
        html.required = true
        csv.required = false
    }

    afterEvaluate {
        classDirectories.setFrom(files(classDirectories.files.collect {
            fileTree(dir: it, exclude: [
                '**/config/**',
                '**/dto/**',
                '**/entity/**',
                '**/Application.class'
            ])
        }))
    }
}

jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit {
                counter = 'LINE'
                value = 'COVEREDRATIO'
                minimum = 0.80
            }
        }
        rule {
            limit {
                counter = 'BRANCH'
                value = 'COVEREDRATIO'
                minimum = 0.80
            }
        }
    }
}

check.dependsOn jacocoTestCoverageVerification
```

**Gradle Kotlin DSL**:
```kotlin
plugins {
    java
    jacoco
}

jacoco {
    toolVersion = "0.8.11"
}

tasks.test {
    finalizedBy(tasks.jacocoTestReport)
}

tasks.jacocoTestReport {
    dependsOn(tasks.test)
    reports {
        xml.required.set(true)
        html.required.set(true)
        csv.required.set(false)
    }

    classDirectories.setFrom(
        files(classDirectories.files.map {
            fileTree(it) {
                exclude(
                    "**/config/**",
                    "**/dto/**",
                    "**/entity/**",
                    "**/Application.class"
                )
            }
        })
    )
}

tasks.jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit {
                counter = "LINE"
                value = "COVEREDRATIO"
                minimum = "0.80".toBigDecimal()
            }
        }
        rule {
            limit {
                counter = "BRANCH"
                value = "COVEREDRATIO"
                minimum = "0.80".toBigDecimal()
            }
        }
    }
}

tasks.check {
    dependsOn(tasks.jacocoTestCoverageVerification)
}
```

### Alternative: Cobertura Configuration

**Maven with Cobertura**:
```xml
<plugin>
  <groupId>org.codehaus.mojo</groupId>
  <artifactId>cobertura-maven-plugin</artifactId>
  <version>2.7</version>
  <configuration>
    <formats>
      <format>html</format>
      <format>xml</format>
    </formats>
    <check>
      <branchRate>80</branchRate>
      <lineRate>80</lineRate>
      <totalBranchRate>80</totalBranchRate>
      <totalLineRate>80</totalLineRate>
      <packageLineRate>75</packageLineRate>
      <packageBranchRate>75</packageBranchRate>
    </check>
    <instrumentation>
      <excludes>
        <exclude>**/*Test.class</exclude>
        <exclude>**/config/*.class</exclude>
        <exclude>**/dto/*.class</exclude>
      </excludes>
    </instrumentation>
  </configuration>
  <executions>
    <execution>
      <goals>
        <goal>clean</goal>
        <goal>check</goal>
      </goals>
    </execution>
  </executions>
</plugin>
```

### Advanced JaCoCo Configuration

**Per-package thresholds**:
```xml
<configuration>
  <rules>
    <rule>
      <element>PACKAGE</element>
      <limits>
        <limit>
          <counter>CLASS</counter>
          <value>MISSEDCOUNT</value>
          <maximum>0</maximum>
        </limit>
      </limits>
    </rule>

    <!-- Critical packages need higher coverage -->
    <rule>
      <element>PACKAGE</element>
      <includes>
        <include>com.myapp.core.*</include>
        <include>com.myapp.security.*</include>
      </includes>
      <limits>
        <limit>
          <counter>LINE</counter>
          <value>COVEREDRATIO</value>
          <minimum>0.90</minimum>
        </limit>
      </limits>
    </rule>
  </rules>
</configuration>
```

## Phase 2: Measure Current Coverage

### Run Coverage Analysis

**Maven**:
```bash
# Run tests with coverage
mvn clean test

# Generate coverage report
mvn jacoco:report

# View HTML report
open target/site/jacoco/index.html  # macOS
xdg-open target/site/jacoco/index.html  # Linux
start target/site/jacoco/index.html  # Windows

# Check coverage thresholds
mvn jacoco:check
```

**Gradle**:
```bash
# Run tests with coverage
./gradlew clean test jacocoTestReport

# View HTML report
open build/reports/jacoco/test/html/index.html

# Check coverage thresholds
./gradlew jacocoTestCoverageVerification
```

### Analyze Coverage Report

**Console output example**:
```
[INFO] --- jacoco:0.8.11:check (check) @ myapp ---
[INFO] Loading execution data file target/jacoco.exec
[INFO] Analyzed bundle 'myapp' with 45 classes

Rule violated for bundle myapp:
  lines covered ratio is 0.76, but expected minimum is 0.80
  branches covered ratio is 0.68, but expected minimum is 0.80
```

**HTML report structure**:
```
Package                        Class Coverage    Method Coverage    Line Coverage    Branch Coverage
com.myapp.service             78% (18/23)       81% (43/53)        76% (231/304)    68% (45/66)
com.myapp.controller          92% (11/12)       88% (22/25)        89% (178/200)    84% (21/25)
com.myapp.repository          85% (17/20)       90% (36/40)        87% (156/179)    79% (19/24)
com.myapp.util                95% (19/20)       94% (47/50)        93% (245/263)    90% (36/40)
```

### Identify Coverage Gaps

**Create Java coverage analysis tool**:

```java
package com.myapp.analysis;

import org.jacoco.core.analysis.*;
import org.jacoco.core.tools.ExecFileLoader;

import java.io.*;
import java.util.*;

/**

 * Analyze coverage gaps and prioritize improvements.
 */
public class CoverageGapAnalyzer {

    public static void analyzeCoverageGaps(File execFile, File classesDir)
            throws IOException {

        ExecFileLoader execFileLoader = new ExecFileLoader();
        execFileLoader.load(execFile);

        final CoverageBuilder coverageBuilder = new CoverageBuilder();
        final Analyzer analyzer = new Analyzer(
            execFileLoader.getExecutionDataStore(),
            coverageBuilder
        );

        analyzer.analyzeAll(classesDir);

        List<CoverageGap> gaps = new ArrayList<>();

        for (IClassCoverage cc : coverageBuilder.getClasses()) {
            double lineCoverage = getCounter(cc.getLineCounter());
            double branchCoverage = getCounter(cc.getBranchCounter());
            double avgCoverage = (lineCoverage + branchCoverage) / 2.0;

            if (avgCoverage < 80.0) {
                gaps.add(new CoverageGap(
                    cc.getName(),
                    avgCoverage,
                    lineCoverage,
                    branchCoverage,
                    avgCoverage < 50.0 ? "HIGH" : "MEDIUM"
                ));
            }
        }

        gaps.sort(Comparator.comparing(CoverageGap::getAvgCoverage));

        System.out.println("=".repeat(80));
        System.out.println("Coverage Gap Analysis");
        System.out.println("=".repeat(80));
        System.out.printf("%-50s %8s %8s %8s %10s%n",
            "Class", "Avg", "Lines", "Branch", "Priority");
        System.out.println("-".repeat(80));

        for (CoverageGap gap : gaps) {
            System.out.printf("%-50s %7.1f%% %7.1f%% %7.1f%% %10s%n",
                gap.getClassName(),
                gap.getAvgCoverage(),
                gap.getLineCoverage(),
                gap.getBranchCoverage(),
                gap.getPriority()
            );
        }

        System.out.printf("%nTotal classes needing improvement: %d%n", gaps.size());
    }

    private static double getCounter(ICounter counter) {
        int total = counter.getTotalCount();
        if (total == 0) return 100.0;
        return 100.0 * counter.getCoveredCount() / total;
    }

    static class CoverageGap {
        private final String className;
        private final double avgCoverage;
        private final double lineCoverage;
        private final double branchCoverage;
        private final String priority;

        // Constructor and getters...
    }

    public static void main(String[] args) throws IOException {
        File execFile = new File("target/jacoco.exec");
        File classesDir = new File("target/classes");
        analyzeCoverageGaps(execFile, classesDir);
    }
}
```

## Phase 3: Prioritize Coverage Improvements

### Coverage Improvement Matrix

| Priority | Criteria | Action |
|----------|----------|--------|
| **Critical** | Core business logic <50% coverage | Immediate test creation |
| **High** | Public APIs <70% coverage | Test in current sprint |
| **Medium** | Utilities <80% coverage | Test in next sprint |
| **Low** | DTOs/Entities <80% coverage | Test when modified |

### Identify Critical Paths

```java
package com.myapp.analysis;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.stmt.TryStmt;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

/**

 * Identify critical code paths requiring coverage.
 */
public class CriticalPathAnalyzer {

    public static void analyzeCriticalPaths(Path sourceDir) throws IOException {
        JavaParser parser = new JavaParser();

        Files.walk(sourceDir)
            .filter(path -> path.toString().endsWith(".java"))
            .forEach(path -> {
                try {
                    CompilationUnit cu = parser.parse(path).getResult().orElse(null);
                    if (cu != null) {
                        List<CriticalPath> paths = new ArrayList<>();

                        cu.accept(new VoidVisitorAdapter<List<CriticalPath>>() {
                            @Override
                            public void visit(MethodDeclaration md, List<CriticalPath> arg) {
                                super.visit(md, arg);

                                // Public methods are critical
                                if (md.isPublic()) {
                                    arg.add(new CriticalPath(
                                        md.getNameAsString(),
                                        md.getBegin().get().line,
                                        "Public API"
                                    ));
                                }

                                // Methods with try-catch are critical
                                if (!md.findAll(TryStmt.class).isEmpty()) {
                                    arg.add(new CriticalPath(
                                        md.getNameAsString(),
                                        md.getBegin().get().line,
                                        "Error handling"
                                    ));
                                }
                            }
                        }, paths);

                        if (!paths.isEmpty()) {
                            System.out.println("\n" + path + ":");
                            paths.forEach(p -> System.out.printf(
                                "  Line %d: %s (%s)%n",
                                p.line, p.name, p.reason
                            ));
                        }
                    }
                } catch (IOException e) {
                    e.printStackTrace();
                }
            });
    }

    static class CriticalPath {
        final String name;
        final int line;
        final String reason;

        CriticalPath(String name, int line, String reason) {
            this.name = name;
            this.line = line;
            this.reason = reason;
        }
    }
}
```

## Phase 4: Systematic Coverage Improvement

### Strategy 1: Fill Happy Path Coverage

```java
/**

 * Add tests for basic functionality of uncovered code.
 *

 * Focus on main execution paths first.
 */

// Uncovered class
public class DiscountCalculator {
    public double calculateDiscount(double price, CustomerType customerType) {
        switch (customerType) {
            case PREMIUM:
                return price * 0.20;
            case REGULAR:
                return price * 0.10;
            default:
                return 0.0;
        }
    }
}

// Add basic coverage tests
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class DiscountCalculatorTest {

    private final DiscountCalculator calculator = new DiscountCalculator();

    @Test
    void shouldCalculatePremiumDiscount() {
        double discount = calculator.calculateDiscount(100.0, CustomerType.PREMIUM);
        assertEquals(20.0, discount, 0.01);
    }

    @Test
    void shouldCalculateRegularDiscount() {
        double discount = calculator.calculateDiscount(100.0, CustomerType.REGULAR);
        assertEquals(10.0, discount, 0.01);
    }

    @Test
    void shouldReturnZeroForGuestCustomer() {
        double discount = calculator.calculateDiscount(100.0, CustomerType.GUEST);
        assertEquals(0.0, discount, 0.01);
    }
}
```

### Strategy 2: Cover Edge Cases

```java
/**

 * Add tests for boundary conditions and edge cases.
 */

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

class DiscountCalculatorEdgeCasesTest {

    private final DiscountCalculator calculator = new DiscountCalculator();

    @Test
    void shouldHandleZeroPrice() {
        double discount = calculator.calculateDiscount(0.0, CustomerType.PREMIUM);
        assertEquals(0.0, discount, 0.01);
    }

    @Test
    void shouldHandleNegativePrice() {
        double discount = calculator.calculateDiscount(-100.0, CustomerType.PREMIUM);
        assertEquals(-20.0, discount, 0.01); // Or should throw?
    }

    @Test
    void shouldHandleVeryLargePrice() {
        double discount = calculator.calculateDiscount(1_000_000.0, CustomerType.PREMIUM);
        assertEquals(200_000.0, discount, 0.01);
    }

    @ParameterizedTest
    @ValueSource(doubles = {0.01, 10.0, 99.99, 1000.0, Double.MAX_VALUE})
    void shouldHandleVariousPrices(double price) {
        double discount = calculator.calculateDiscount(price, CustomerType.PREMIUM);
        assertTrue(discount >= 0);
    }

    @Test
    void shouldHandleNullCustomerType() {
        assertThrows(NullPointerException.class, () -> {
            calculator.calculateDiscount(100.0, null);
        });
    }
}
```

### Strategy 3: Cover Error Paths

```java
/**

 * Add tests for error handling and exceptional conditions.
 */

// Class with error handling
public class UserService {

    private final UserRepository repository;
    private final Logger logger;

    public Optional<User> loadUserData(Long userId) {
        try {
            User user = repository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("User not found: " + userId));

            return Optional.of(user);

        } catch (DatabaseException e) {
            logger.error("Database error loading user: {}", userId, e);
            throw e;
        } catch (UserNotFoundException e) {
            logger.warn("User not found: {}", userId);
            return Optional.empty();
        }
    }
}

// Tests covering error paths
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
class UserServiceErrorHandlingTest {

    @Mock
    private UserRepository repository;

    @Mock
    private Logger logger;

    @InjectMocks
    private UserService userService;

    @Test
    void shouldHandleDatabaseError() {
        when(repository.findById(123L))
            .thenThrow(new DatabaseException("Connection failed"));

        assertThrows(DatabaseException.class, () -> {
            userService.loadUserData(123L);
        });

        verify(logger).error(
            eq("Database error loading user: {}"),
            eq(123L),
            any(DatabaseException.class)
        );
    }

    @Test
    void shouldHandleUserNotFound() {
        when(repository.findById(999L))
            .thenReturn(Optional.empty());

        Optional<User> result = userService.loadUserData(999L);

        assertTrue(result.isEmpty());
        verify(logger).warn("User not found: {}", 999L);
    }

    @Test
    void shouldPropagateUnexpectedExceptions() {
        when(repository.findById(123L))
            .thenThrow(new RuntimeException("Unexpected error"));

        assertThrows(RuntimeException.class, () -> {
            userService.loadUserData(123L);
        });
    }
}
```

### Strategy 4: Cover Branch Conditions

```java
/**

 * Ensure all branches of conditional logic are tested.
 */

public class ShippingCalculator {

    public double calculateShippingCost(
            double weight,
            Destination destination,
            boolean express) {

        double baseCost = weight * 2.5;

        if (destination == Destination.INTERNATIONAL) {
            baseCost *= 3;
        } else if (destination == Destination.REMOTE) {
            baseCost *= 1.5;
        }

        if (express) {
            baseCost *= 2;
        }

        return baseCost;
    }
}

// Tests covering all branches
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

class ShippingCalculatorBranchTest {

    private final ShippingCalculator calculator = new ShippingCalculator();

    @ParameterizedTest(name = "{0} {1} shipping should cost {2}")
    @CsvSource({
        "DOMESTIC,     false,  25.0",
        "DOMESTIC,     true,   50.0",
        "INTERNATIONAL, false,  75.0",
        "INTERNATIONAL, true,  150.0",
        "REMOTE,       false,  37.5",
        "REMOTE,       true,   75.0"
    })
    void shouldCalculateCorrectShippingCost(
            Destination destination,
            boolean express,
            double expected) {

        double cost = calculator.calculateShippingCost(10.0, destination, express);
        assertEquals(expected, cost, 0.01);
    }
}
```

## Phase 5: Coverage Reporting and Tracking

### Generate Comprehensive Reports

```bash
# Maven: Generate all report types
mvn clean test jacoco:report

# Gradle: Generate all report types
./gradlew clean test jacocoTestReport

# Reports generated:
# - target/site/jacoco/index.html (HTML)
# - target/site/jacoco/jacoco.xml (XML for CI/CD)
# - target/site/jacoco/jacoco.csv (CSV for analysis)
```

### Coverage Badge

Add to `pom.xml`:
```xml
<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <executions>
    <execution>
      <id>jacoco-badge</id>
      <phase>verify</phase>
      <goals>
        <goal>report</goal>
      </goals>
    </execution>
  </executions>
</plugin>
```

Use shields.io in README:
```markdown
![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)
```

### Track Coverage Over Time

```java
package com.myapp.analysis;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.w3c.dom.Document;
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.*;
import java.time.LocalDateTime;
import java.util.*;

/**

 * Track coverage metrics over time.
 */
public class CoverageTracker {

    public static void recordCoverage() throws Exception {
        File xmlReport = new File("target/site/jacoco/jacoco.xml");
        File historyFile = new File("coverage-history.json");

        if (!xmlReport.exists()) {
            System.err.println("No jacoco.xml found. Run: mvn jacoco:report");
            return;
        }

        // Parse XML report
        Document doc = DocumentBuilderFactory.newInstance()
            .newDocumentBuilder()
            .parse(xmlReport);

        Map<String, Object> record = new HashMap<>();
        record.put("date", LocalDateTime.now().toString());
        record.put("lineCoverage", extractCoverage(doc, "LINE"));
        record.put("branchCoverage", extractCoverage(doc, "BRANCH"));
        record.put("instructionCoverage", extractCoverage(doc, "INSTRUCTION"));

        // Load history
        ObjectMapper mapper = new ObjectMapper();
        List<Map<String, Object>> history = new ArrayList<>();

        if (historyFile.exists()) {
            history = mapper.readValue(historyFile, List.class);
        }

        history.add(record);

        // Save history
        mapper.writerWithDefaultPrettyPrinter()
            .writeValue(historyFile, history);

        System.out.printf("Coverage recorded: %.1f%% lines%n",
            (Double) record.get("lineCoverage"));
    }

    private static double extractCoverage(Document doc, String type) {
        // Parse JaCoCo XML and extract coverage percentage
        // Implementation details...
        return 0.0;
    }
}
```

### Coverage Diff for PRs

```java
package com.myapp.analysis;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.File;
import java.util.Map;

/**

 * Show coverage changes in pull request.
 */
public class CoverageDiff {

    public static void compareCoverage(File baseReport, File currentReport)
            throws Exception {

        ObjectMapper mapper = new ObjectMapper();
        Map<String, Object> base = mapper.readValue(baseReport, Map.class);
        Map<String, Object> current = mapper.readValue(currentReport, Map.class);

        double baseLine = (Double) base.get("lineCoverage");
        double currentLine = (Double) current.get("lineCoverage");
        double diff = currentLine - baseLine;

        System.out.println("=".repeat(80));
        System.out.println("Coverage Diff");
        System.out.println("=".repeat(80));
        System.out.printf("Base coverage:    %.2f%%%n", baseLine);
        System.out.printf("Current coverage: %.2f%%%n", currentLine);
        System.out.printf("Difference:       %+.2f%%%n", diff);

        if (diff < -0.5) {
            System.out.printf("%n❌ Coverage decreased by %.2f%%%n", Math.abs(diff));
            System.exit(1);
        } else if (diff < 0) {
            System.out.printf("%n⚠️ Coverage decreased slightly by %.2f%%%n", Math.abs(diff));
        } else {
            System.out.println("\n✅ Coverage maintained or improved");
        }
    }
}
```

## Phase 6: Coverage in CI/CD

### GitHub Actions Coverage Integration

```yaml
# .github/workflows/coverage.yml
name: Coverage

on: [push, pull_request]

jobs:
  coverage:
    runs-on: ubuntu-latest

    steps:

      - uses: actions/checkout@v3

      - name: Set up JDK 17
        uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: 'maven'

      - name: Run tests with coverage
        run: mvn clean test jacoco:report

      - name: Check coverage threshold
        run: mvn jacoco:check

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./target/site/jacoco/jacoco.xml
          fail_ci_if_error: true

      - name: Generate coverage badge
        if: github.ref == 'refs/heads/main'
        run: |
          COVERAGE=$(grep -oP '(?<=<counter type="LINE".*covered=")[^"]*' target/site/jacoco/jacoco.xml | head -1)
          echo "COVERAGE=${COVERAGE}" >> $GITHUB_ENV

      - name: Archive coverage report
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: target/site/jacoco/
```

### Coverage Regression Prevention

```yaml
# Add to existing workflow

- name: Check for coverage regression
  run: |
    # Download base coverage from main branch
    git fetch origin main
    git show origin/main:target/site/jacoco/jacoco.xml > ${OUTPUT_DIR}/exports/base-jacoco.xml

    # Compare with current
    java -cp target/classes com.myapp.analysis.CoverageDiff \
      base-jacoco.xml \
      target/site/jacoco/jacoco.xml
```

## Output Format

Please provide a comprehensive coverage analysis with the following structure:

### Coverage Summary

- **Overall Coverage**: [percentage]

- **Line Coverage**: [percentage]

- **Branch Coverage**: [percentage]

- **Instruction Coverage**: [percentage]

- **Method Coverage**: [percentage]

- **Class Coverage**: [percentage]

### Coverage by Package
| Package | Line | Branch | Method | Class | Priority |
|---------|------|--------|--------|-------|----------|
| com.myapp.service | 76% | 68% | 81% | 78% | High |
| com.myapp.controller | 89% | 84% | 88% | 92% | Low |
| com.myapp.repository | 87% | 79% | 90% | 85% | Medium |

### Critical Coverage Gaps
1. **com.myapp.service.UserService** (67% line coverage)

   - **Missing**: Error handling branches

   - **Priority**: Critical - core business logic

   - **Action**: Add exception handling tests

2. **com.myapp.security.AuthService** (78% line coverage)

   - **Missing**: Edge cases in authentication

   - **Priority**: High - security-critical

   - **Action**: Add boundary condition tests

### Coverage Improvement Plan
**Sprint 1** (Target: 75% → 80%):

- [ ] Add error handling tests for service layer

- [ ] Cover authentication edge cases

- [ ] Test repository exception handling

**Sprint 2** (Target: 80% → 85%):

- [ ] Add branch coverage for conditionals

- [ ] Test validation logic thoroughly

- [ ] Cover integration scenarios

**Sprint 3** (Target: 85% → 90%):

- [ ] Add concurrency tests

- [ ] Cover all exception types

- [ ] Test transaction boundaries

### Coverage Reports Generated

- **HTML Report**: `target/site/jacoco/index.html`

- **XML Report**: `target/site/jacoco/jacoco.xml` (for CI/CD)

- **CSV Report**: `target/site/jacoco/jacoco.csv` (for analysis)

### Coverage Thresholds

- **Minimum Overall**: 80%

- **Critical Packages**: 90%

- **New Code**: 100%

- **CI/CD Gate**: Fail if <80%

### Best Practices Implemented

- [ ] Coverage measured on every test run

- [ ] HTML reports for detailed analysis

- [ ] Coverage tracked over time

- [ ] Regression prevention in CI/CD

- [ ] Critical paths prioritized

- [ ] Team coverage goals established

### Next Steps

- [ ] Fix identified coverage gaps

- [ ] Set up coverage dashboard

- [ ] Schedule coverage review meetings

- [ ] Document coverage standards

- [ ] Integrate coverage diff in PRs

- [ ] Track coverage trends monthly

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p tests/{phase_name}/test_files
mkdir -p tests/{phase_name}/test_data
mkdir -p tests/{phase_name}/test_reports
mkdir -p tests/{phase_name}/test_configs
```

**Save files as follows**:

- Test files → `tests/{phase_name}/test_files/`

- Test data → `tests/{phase_name}/test_data/`

- Test reports → `tests/{phase_name}/test_reports/`

- Test configs → `tests/{phase_name}/test_configs/`

Replace `{phase_name}` with the specific phase (test_cases, mocks_fixtures, performance_testing, maintenance_cicd, or code_coverage).

~~~

## Output Format

The AI assistant should deliver:

1. **Complete coverage configuration** (Maven pom.xml or Gradle build files)

2. **Current coverage analysis** with gaps identified

3. **Prioritized improvement plan** with specific actions

4. **Test implementations** to fill critical gaps (JUnit 5)

5. **Coverage reporting infrastructure** (HTML, XML, CSV)

6. **CI/CD integration** with coverage gates

7. **Coverage tracking utilities** for trends

8. **Coverage diff tools** for PR reviews

9. **Team documentation** on coverage standards
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
