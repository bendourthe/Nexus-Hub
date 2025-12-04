---
template_id: java_maintenance_cicd
template_name: Maintenance & CI/CD - Java
version: 1.0.0
last_updated: 2025-12-03
language: Java
category: test_development
phase: maintenance_cicd
phase_number: 7
difficulty: intermediate
estimated_time_hours: 3-5
prerequisites:
  - test_development/code_coverage/java_code_coverage.md
related_templates:
  - test_development/reward_hacking/java_reward_hacking.md
tools:
  - junit (5.11.3)
  - maven
  - gradle
tags:
  - test-development
  - java
---
# Java Test Maintenance & CI/CD Integration

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                            ► │ [COMPLETE]
│ Phase 3: Test Cases Development                ► │ [COMPLETE]
│ Phase 4: Mocks & Fixtures                      ► │ [COMPLETE]
│ Phase 5: Performance Testing                   ► │ [COMPLETE]
│ Phase 6: Code Coverage                         ► │ [COMPLETE]
│ Phase 7: Maintenance & CI/CD                    ► │ ● CURRENT
│ Phase 8: Reward Hacking Validation                 ► │ [NEXT]
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 6 (Code Coverage) should be completed first
**Next Step:** Phase 8 (Reward Hacking Validation)

---


## Objective
Establish comprehensive test automation infrastructure, integrate tests into CI/CD pipelines, implement quality gates, manage test maintenance, handle flaky tests, optimize test execution, and ensure sustainable testing practices for Java projects using Maven or Gradle.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/maintenance_cicd/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/maintenance_cicd/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### CI/CD Configuration

- [ ] GitHub Actions/GitLab CI pipeline configured

- [ ] Test stages defined (unit, integration, e2e)

- [ ] Parallel execution enabled

- [ ] Test result reporting set up

- [ ] Artifact storage configured

### Quality Gates

- [ ] Code coverage threshold enforced (80%+)

- [ ] Test pass rate requirement set (100%)

- [ ] Performance regression checks enabled

- [ ] Security scanning integrated

- [ ] Deployment gates configured

### Test Maintenance

- [ ] Flaky test detection implemented

- [ ] Test execution time monitoring enabled

- [ ] Obsolete test cleanup process established

- [ ] Test documentation maintained

- [ ] Test data management automated

### Pre-commit Hooks

- [ ] Code formatting checks (Google Java Format)

- [ ] Linting (Checkstyle)

- [ ] Static analysis (SpotBugs, PMD)

- [ ] Fast test subset execution

- [ ] Commit hooks configured

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Java Test Maintenance & CI/CD Implementation

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/maintenance_cicd"
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

Please implement comprehensive test automation and maintenance infrastructure for this Java project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: CI/CD Pipeline Configuration

### GitHub Actions Setup

**Create `.github/workflows/tests.yml`**:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  lint:
    name: Lint and Format Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up JDK 17
        uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: 'maven'

      - name: Check formatting
        run: mvn com.spotify.fmt:fmt-maven-plugin:check

      - name: Run Checkstyle
        run: mvn checkstyle:check

      - name: Run SpotBugs
        run: mvn spotbugs:check

      - name: Run PMD
        run: mvn pmd:check

  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        java-version: ['11', '17', '21']

    steps:
      - uses: actions/checkout@v3

      - name: Set up JDK ${{ matrix.java-version }}
        uses: actions/setup-java@v3
        with:
          java-version: ${{ matrix.java-version }}
          distribution: 'temurin'
          cache: 'maven'

      - name: Run unit tests
        run: mvn test -Dtest=**/*Test.java -DfailIfNoTests=false

      - name: Generate coverage report
        run: mvn jacoco:report

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./target/site/jacoco/jacoco.xml
          flags: unit-tests
          name: codecov-java-${{ matrix.java-version }}

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results-${{ matrix.java-version }}
          path: |
            target/surefire-reports/
            target/site/jacoco/

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up JDK 17
        uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: 'maven'

      - name: Run integration tests
        env:
          DATABASE_URL: jdbc:postgresql://localhost:5432/testdb
          DATABASE_USER: postgres
          DATABASE_PASSWORD: testpass
          REDIS_URL: redis://localhost:6379
        run: mvn verify -Dtest=**/*IT.java -DfailIfNoTests=false

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./target/site/jacoco/jacoco.xml
          flags: integration-tests

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up JDK 17
        uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: 'maven'

      - name: Run OWASP Dependency Check
        run: mvn org.owasp:dependency-check-maven:check

      - name: Run Snyk security scan
        uses: snyk/actions/maven@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            target/dependency-check-report.html

  quality-gate:
    name: Quality Gate
    runs-on: ubuntu-latest
    needs: [lint, unit-tests, integration-tests, security]
    steps:
      - name: Quality gate passed
        run: echo "All quality checks passed!"
```

### GitLab CI Configuration

**Create `.gitlab-ci.yml`**:

```yaml
stages:
  - lint
  - test
  - quality
  - deploy

variables:
  MAVEN_OPTS: "-Dmaven.repo.local=.m2/repository"
  MAVEN_CLI_OPTS: "--batch-mode --errors --fail-at-end --show-version"

cache:
  paths:
    - .m2/repository

before_script:
  - export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

lint:
  stage: lint
  image: maven:3.9-eclipse-temurin-17
  script:
    - mvn $MAVEN_CLI_OPTS com.spotify.fmt:fmt-maven-plugin:check
    - mvn $MAVEN_CLI_OPTS checkstyle:check
    - mvn $MAVEN_CLI_OPTS spotbugs:check
    - mvn $MAVEN_CLI_OPTS pmd:check

unit-tests:
  stage: test
  image: maven:3.9-eclipse-temurin-17
  script:
    - mvn $MAVEN_CLI_OPTS test -Dtest=**/*Test.java
    - mvn $MAVEN_CLI_OPTS jacoco:report
  coverage: '/Total.*?([0-9]{1,3})%/'
  artifacts:
    reports:
      junit:
        - target/surefire-reports/TEST-*.xml
      coverage_report:
        coverage_format: cobertura
        path: target/site/jacoco/jacoco.xml
    paths:
      - target/site/jacoco/

integration-tests:
  stage: test
  image: maven:3.9-eclipse-temurin-17
  services:
    - postgres:14
    - redis:7
  variables:
    POSTGRES_DB: testdb
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: testpass
    DATABASE_URL: jdbc:postgresql://postgres:5432/testdb
  script:
    - mvn $MAVEN_CLI_OPTS verify -Dtest=**/*IT.java
  artifacts:
    paths:
      - target/site/jacoco/

quality-gate:
  stage: quality
  image: maven:3.9-eclipse-temurin-17
  script:
    - mvn $MAVEN_CLI_OPTS jacoco:check
  needs:
    - unit-tests
    - integration-tests
```

## Phase 2: Quality Gates Configuration

### Maven Configuration

**Configure in `pom.xml`**:

```xml
<project>
    <build>
        <plugins>
            <!-- JaCoCo for code coverage -->
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>0.8.11</version>
                <executions>
                    <execution>
                        <goals>
                            <goal>prepare-agent</goal>
                        </goals>
                    </execution>
                    <execution>
                        <id>report</id>
                        <phase>test</phase>
                        <goals>
                            <goal>report</goal>
                        </goals>
                    </execution>
                    <execution>
                        <id>jacoco-check</id>
                        <goals>
                            <goal>check</goal>
                        </goals>
                        <configuration>
                            <rules>
                                <rule>
                                    <element>PACKAGE</element>
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
            </plugin>

            <!-- Surefire for unit tests -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.2.2</version>
                <configuration>
                    <includes>
                        <include>**/*Test.java</include>
                    </includes>
                    <parallel>classes</parallel>
                    <threadCount>4</threadCount>
                    <forkCount>2C</forkCount>
                    <reuseForks>true</reuseForks>
                </configuration>
            </plugin>

            <!-- Failsafe for integration tests -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-failsafe-plugin</artifactId>
                <version>3.2.2</version>
                <configuration>
                    <includes>
                        <include>**/*IT.java</include>
                    </includes>
                </configuration>
                <executions>
                    <execution>
                        <goals>
                            <goal>integration-test</goal>
                            <goal>verify</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>

            <!-- Checkstyle -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-checkstyle-plugin</artifactId>
                <version>3.3.1</version>
                <configuration>
                    <configLocation>google_checks.xml</configLocation>
                    <violationSeverity>warning</violationSeverity>
                    <failOnViolation>true</failOnViolation>
                </configuration>
            </plugin>

            <!-- SpotBugs -->
            <plugin>
                <groupId>com.github.spotbugs</groupId>
                <artifactId>spotbugs-maven-plugin</artifactId>
                <version>4.8.2.0</version>
                <configuration>
                    <effort>Max</effort>
                    <threshold>Medium</threshold>
                    <failOnError>true</failOnError>
                </configuration>
            </plugin>

            <!-- PMD -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-pmd-plugin</artifactId>
                <version>3.21.2</version>
                <configuration>
                    <rulesets>
                        <ruleset>/rulesets/java/quickstart.xml</ruleset>
                    </rulesets>
                    <failOnViolation>true</failOnViolation>
                </configuration>
            </plugin>

            <!-- Google Java Format -->
            <plugin>
                <groupId>com.spotify.fmt</groupId>
                <artifactId>fmt-maven-plugin</artifactId>
                <version>2.21.1</version>
                <executions>
                    <execution>
                        <goals>
                            <goal>check</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

### Gradle Configuration

**Configure in `build.gradle`**:

```groovy
plugins {
    id 'java'
    id 'jacoco'
    id 'checkstyle'
    id 'pmd'
    id 'com.github.spotbugs' version '5.2.5'
    id 'com.diffplug.spotless' version '6.23.3'
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

test {
    useJUnitPlatform()

    // Parallel execution
    maxParallelForks = Runtime.runtime.availableProcessors().intdiv(2) ?: 1

    // Test filtering
    include '**/*Test.class'
    exclude '**/*IT.class'

    // Reporting
    reports {
        junitXml.required = true
        html.required = true
    }

    finalizedBy jacocoTestReport
}

task integrationTest(type: Test) {
    include '**/*IT.class'
    exclude '**/*Test.class'

    shouldRunAfter test
}

jacoco {
    toolVersion = "0.8.11"
}

jacocoTestReport {
    dependsOn test

    reports {
        xml.required = true
        html.required = true
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

checkstyle {
    toolVersion = '10.12.7'
    configFile = file("${project.rootDir}/config/checkstyle/checkstyle.xml")
    maxWarnings = 0
    maxErrors = 0
}

pmd {
    toolVersion = '6.55.0'
    consoleOutput = true
    ruleSetFiles = files("${project.rootDir}/config/pmd/ruleset.xml")
}

spotbugs {
    toolVersion = '4.8.3'
    effort = 'max'
    reportLevel = 'medium'
}

spotless {
    java {
        googleJavaFormat('1.18.1')
        removeUnusedImports()
        trimTrailingWhitespace()
        endWithNewline()
    }
}

check.dependsOn jacocoTestCoverageVerification
```

### Test Pass Rate Gate

```java
// src/test/java/com/example/QualityGateListener.java
package com.example;

import org.junit.platform.launcher.TestExecutionListener;
import org.junit.platform.launcher.TestPlan;
import org.junit.platform.engine.reporting.ReportEntry;

/**
 * Quality gate enforcement for test suite.
 */
public class QualityGateListener implements TestExecutionListener {
    private int totalTests = 0;
    private int passedTests = 0;
    private int failedTests = 0;

    @Override
    public void testPlanExecutionFinished(TestPlan testPlan) {
        double passRate = totalTests > 0
            ? (double) passedTests / totalTests * 100
            : 0;

        System.out.println("\n" + "=".repeat(60));
        System.out.println(String.format(
            "Test Pass Rate: %.1f%% (%d/%d)",
            passRate, passedTests, totalTests
        ));
        System.out.println("=".repeat(60));

        if (passRate < 100) {
            System.out.println("⚠️  WARNING: Not all tests passed");
            System.out.println("Failed tests: " + failedTests);
        } else {
            System.out.println("✅ Quality Gate Passed: All tests passed");
        }

        if (failedTests > 0) {
            System.out.println("\n❌ Quality Gate Failed: Some tests did not pass");
            System.out.println("All tests must pass before merge.");
            System.exit(1);
        }
    }

    @Override
    public void reportingEntryPublished(
        org.junit.platform.engine.TestExecutionResult result
    ) {
        totalTests++;
        if (result.getStatus() == org.junit.platform.engine.TestExecutionResult.Status.SUCCESSFUL) {
            passedTests++;
        } else {
            failedTests++;
        }
    }
}
```

Register in `src/test/resources/junit-platform.properties`:
```properties
junit.platform.execution.listeners.deactivate=com.example.QualityGateListener
```

### Performance Regression Gate

```java
// src/test/java/com/example/benchmark/PerformanceGate.java
package com.example.benchmark;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

/**
 * Performance regression detection.
 */
public class PerformanceGate {
    private static final String BASELINE_FILE = "src/test/resources/baseline.json";
    private static final double REGRESSION_THRESHOLD = 0.10; // 10%

    private Map<String, Long> benchmarks = new HashMap<>();
    private Map<String, Long> baseline = new HashMap<>();
    private ObjectMapper mapper = new ObjectMapper();

    public PerformanceGate() {
        loadBaseline();
    }

    private void loadBaseline() {
        File file = new File(BASELINE_FILE);
        if (file.exists()) {
            try {
                baseline = mapper.readValue(
                    file,
                    mapper.getTypeFactory().constructMapType(
                        HashMap.class, String.class, Long.class
                    )
                );
            } catch (IOException e) {
                System.err.println("Failed to load baseline: " + e.getMessage());
            }
        }
    }

    public void recordBenchmark(String name, long durationMs) {
        benchmarks.put(name, durationMs);
    }

    public void checkRegressions() throws Exception {
        if (baseline.isEmpty()) {
            saveBaseline();
            System.out.println("📊 Baseline performance metrics saved");
            return;
        }

        StringBuilder regressions = new StringBuilder();
        boolean hasRegressions = false;

        for (Map.Entry<String, Long> entry : benchmarks.entrySet()) {
            String name = entry.getKey();
            long current = entry.getValue();

            if (baseline.containsKey(name)) {
                long baselineValue = baseline.get(name);
                double regression = (double) (current - baselineValue) / baselineValue;

                if (regression > REGRESSION_THRESHOLD) {
                    hasRegressions = true;
                    regressions.append(String.format(
                        "  %s: %.1f%% slower\n    Baseline: %dms, Current: %dms\n",
                        name, regression * 100, baselineValue, current
                    ));
                }
            }
        }

        if (hasRegressions) {
            System.out.println("\n❌ Performance Regression Detected:");
            System.out.println(regressions.toString());
            throw new AssertionError("Performance regression gate failed");
        }

        System.out.println("✅ Performance Gate Passed: No regressions detected");
    }

    private void saveBaseline() throws IOException {
        mapper.writerWithDefaultPrettyPrinter()
            .writeValue(new File(BASELINE_FILE), benchmarks);
    }
}
```

## Phase 3: Pre-commit Hooks

### Install Pre-commit Framework

```bash
pip install pre-commit

# Create .pre-commit-config.yaml
```

**Create `.pre-commit-config.yaml`**:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: local
    hooks:
      - id: maven-format
        name: Format Java code
        entry: mvn com.spotify.fmt:fmt-maven-plugin:format
        language: system
        files: \.java$
        pass_filenames: false

      - id: maven-checkstyle
        name: Run Checkstyle
        entry: mvn checkstyle:check
        language: system
        files: \.java$
        pass_filenames: false

      - id: maven-spotbugs
        name: Run SpotBugs
        entry: mvn spotbugs:check
        language: system
        files: \.java$
        pass_filenames: false

      - id: maven-test-fast
        name: Run fast tests
        entry: mvn test -Dtest=**/*Test.java -Dgroups=fast
        language: system
        pass_filenames: false
        always_run: true
```

### Install Hooks

```bash
# Install the git hook scripts
pre-commit install

# Run against all files (optional)
pre-commit run --all-files

# Update hooks to latest versions
pre-commit autoupdate
```

### Maven Wrapper for Hooks

```bash
# Create Maven wrapper
mvn wrapper:wrapper

# Use in pre-commit hooks
./mvnw clean test
```

## Phase 4: Test Parallelization

### Maven Parallel Execution

```xml
<!-- pom.xml -->
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-surefire-plugin</artifactId>
    <version>3.2.2</version>
    <configuration>
        <!-- Parallel execution by classes -->
        <parallel>classes</parallel>
        <threadCount>4</threadCount>

        <!-- Or use CPU-based calculation -->
        <forkCount>2C</forkCount>
        <reuseForks>true</reuseForks>

        <!-- Timeout per test -->
        <forkedProcessTimeoutInSeconds>300</forkedProcessTimeoutInSeconds>
    </configuration>
</plugin>
```

### Gradle Parallel Execution

```groovy
test {
    // Use multiple processes
    maxParallelForks = Runtime.runtime.availableProcessors().intdiv(2) ?: 1

    // Or specific number
    // maxParallelForks = 4

    // Fork options
    forkEvery = 100

    // JVM arguments for each fork
    jvmArgs '-Xmx1024m'
}
```

### Handle Non-Thread-Safe Tests

```java
package com.example;

import org.junit.jupiter.api.parallel.Execution;
import org.junit.jupiter.api.parallel.ExecutionMode;
import org.junit.jupiter.api.parallel.ResourceLock;

/**
 * Tests that must run serially.
 */
@Execution(ExecutionMode.SAME_THREAD)
public class DatabaseMigrationTest {

    @ResourceLock("database")
    @Test
    void testMigration001() {
        // Test implementation
    }

    @ResourceLock("database")
    @Test
    void testMigration002() {
        // Test implementation
    }
}
```

Configure in `junit-platform.properties`:
```properties
junit.jupiter.execution.parallel.enabled=true
junit.jupiter.execution.parallel.mode.default=concurrent
junit.jupiter.execution.parallel.mode.classes.default=concurrent
```

## Phase 5: Flaky Test Management

### Detect Flaky Tests

```xml
<!-- Add to pom.xml -->
<dependency>
    <groupId>org.junit.jupiter</groupId>
    <artifactId>junit-jupiter-api</artifactId>
    <version>5.10.1</version>
    <scope>test</scope>
</dependency>
```

### Retry Flaky Tests

```java
package com.example.util;

import org.junit.jupiter.api.extension.*;

/**
 * Retry extension for flaky tests.
 */
public class RetryExtension implements TestExecutionExceptionHandler {
    private static final int MAX_RETRIES = 3;

    @Override
    public void handleTestExecutionException(
        ExtensionContext context,
        Throwable throwable
    ) throws Throwable {
        int retriesKey = context.getUniqueId().hashCode();
        ExtensionContext.Store store = context.getStore(
            ExtensionContext.Namespace.create(getClass(), context.getRequiredTestMethod())
        );

        Integer retries = store.get(retriesKey, Integer.class);
        if (retries == null) {
            retries = 0;
        }

        if (retries < MAX_RETRIES) {
            store.put(retriesKey, retries + 1);
            System.out.println(String.format(
                "Test failed (attempt %d/%d), retrying...",
                retries + 1, MAX_RETRIES
            ));
            Thread.sleep(1000);
            // Retry will happen automatically
            return;
        }

        throw throwable;
    }
}

// Usage
@ExtendWith(RetryExtension.class)
@Test
void flakyExternalApiCall() {
    // Test implementation
}
```

### Track Flaky Tests

```java
package com.example.listener;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.platform.launcher.TestExecutionListener;
import org.junit.platform.launcher.TestIdentifier;

import java.io.File;
import java.io.IOException;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * Track flaky test occurrences.
 */
public class FlakyTestTracker implements TestExecutionListener {
    private static final String FLAKY_LOG = "target/flaky-tests.json";
    private Map<String, FlakyTestInfo> flakyTests = new HashMap<>();
    private ObjectMapper mapper = new ObjectMapper();

    public FlakyTestTracker() {
        loadLog();
    }

    private void loadLog() {
        File file = new File(FLAKY_LOG);
        if (file.exists()) {
            try {
                flakyTests = mapper.readValue(
                    file,
                    mapper.getTypeFactory().constructMapType(
                        HashMap.class, String.class, FlakyTestInfo.class
                    )
                );
            } catch (IOException e) {
                System.err.println("Failed to load flaky test log: " + e.getMessage());
            }
        }
    }

    @Override
    public void executionFinished(
        TestIdentifier testIdentifier,
        org.junit.platform.engine.TestExecutionResult result
    ) {
        if (result.getStatus() ==
            org.junit.platform.engine.TestExecutionResult.Status.FAILED) {
            String testName = testIdentifier.getDisplayName();
            FlakyTestInfo info = flakyTests.computeIfAbsent(
                testName, k -> new FlakyTestInfo()
            );
            info.count++;
            info.lastSeen = LocalDateTime.now().toString();
        }
    }

    public void saveLog() {
        try {
            mapper.writerWithDefaultPrettyPrinter()
                .writeValue(new File(FLAKY_LOG), flakyTests);
        } catch (IOException e) {
            System.err.println("Failed to save flaky test log: " + e.getMessage());
        }
    }

    static class FlakyTestInfo {
        public int count = 0;
        public String lastSeen;
    }
}
```

## Phase 6: Test Maintenance Practices

### Monitor Test Execution Time

```java
package com.example.listener;

import org.junit.platform.launcher.TestExecutionListener;
import org.junit.platform.launcher.TestIdentifier;
import org.junit.platform.engine.TestExecutionResult;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Monitor slow tests.
 */
public class SlowTestListener implements TestExecutionListener {
    private static final long SLOW_TEST_THRESHOLD_MS = 1000;
    private List<SlowTest> slowTests = new ArrayList<>();
    private long startTime;

    @Override
    public void executionStarted(TestIdentifier testIdentifier) {
        if (testIdentifier.isTest()) {
            startTime = System.currentTimeMillis();
        }
    }

    @Override
    public void executionFinished(
        TestIdentifier testIdentifier,
        TestExecutionResult result
    ) {
        if (testIdentifier.isTest()) {
            long duration = System.currentTimeMillis() - startTime;

            if (duration > SLOW_TEST_THRESHOLD_MS) {
                slowTests.add(new SlowTest(
                    testIdentifier.getDisplayName(),
                    duration
                ));
                System.out.println(String.format(
                    "\n⚠️  Slow test: %s (%.2fs)",
                    testIdentifier.getDisplayName(),
                    duration / 1000.0
                ));
            }
        }
    }

    public void printReport() {
        if (!slowTests.isEmpty()) {
            System.out.println("\n" + "=".repeat(60));
            System.out.println("Slow Tests Detected:");

            slowTests.stream()
                .sorted((a, b) -> Long.compare(b.duration, a.duration))
                .limit(10)
                .forEach(test -> System.out.println(String.format(
                    "  %.2fs: %s",
                    test.duration / 1000.0,
                    test.name
                )));

            System.out.println("=".repeat(60));
        }
    }

    static class SlowTest {
        String name;
        long duration;

        SlowTest(String name, long duration) {
            this.name = name;
            this.duration = duration;
        }
    }
}
```

### Document Test Purpose

```java
package com.example.auth;

import org.junit.jupiter.api.*;

/**
 * User Authentication Test Suite
 *
 * <p>Purpose:
 * Validate user login, logout, and session management functionality.
 *
 * <p>Coverage:
 * <ul>
 *   <li>Valid credential login</li>
 *   <li>Invalid credential handling</li>
 *   <li>Session token generation and validation</li>
 *   <li>Multi-factor authentication flow</li>
 *   <li>Password reset process</li>
 * </ul>
 *
 * <p>Maintenance Notes:
 * <ul>
 *   <li>Update testValidLogin() if authentication logic changes</li>
 *   <li>mockEmailService fixture required for password reset tests</li>
 *   <li>Tests use in-memory H2 database for speed</li>
 *   <li>External API calls are mocked</li>
 * </ul>
 *
 * <p>Dependencies:
 * <ul>
 *   <li>AuthService</li>
 *   <li>UserRepository</li>
 *   <li>JwtTokenProvider</li>
 * </ul>
 *
 * <p>Last Review: 2024-01-15
 * <p>Reviewed By: alice@example.com
 */
@DisplayName("User Authentication Tests")
public class AuthenticationTest {
    // Test implementation
}
```

## Phase 7: Test Result Reporting

### Maven Surefire Reports

```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-surefire-plugin</artifactId>
    <version>3.2.2</version>
    <configuration>
        <reportFormat>brief</reportFormat>
        <useFile>false</useFile>
    </configuration>
</plugin>

<!-- Generate HTML reports -->
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-surefire-report-plugin</artifactId>
    <version>3.2.2</version>
    <executions>
        <execution>
            <phase>test</phase>
            <goals>
                <goal>report</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```

### Custom Test Reporter

```java
package com.example.reporter;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.platform.launcher.TestExecutionListener;
import org.junit.platform.launcher.TestPlan;

import java.io.File;
import java.io.IOException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Generate custom JSON test report.
 */
public class CustomTestReporter implements TestExecutionListener {
    private List<TestResult> results = new ArrayList<>();
    private long startTime;
    private int totalTests = 0;
    private int passedTests = 0;
    private int failedTests = 0;

    @Override
    public void testPlanExecutionStarted(TestPlan testPlan) {
        startTime = System.currentTimeMillis();
    }

    @Override
    public void testPlanExecutionFinished(TestPlan testPlan) {
        long duration = System.currentTimeMillis() - startTime;

        Map<String, Object> report = new HashMap<>();
        report.put("timestamp", LocalDateTime.now().toString());
        report.put("summary", Map.of(
            "total", totalTests,
            "passed", passedTests,
            "failed", failedTests,
            "duration", duration
        ));
        report.put("results", results);

        try {
            ObjectMapper mapper = new ObjectMapper();
            mapper.writerWithDefaultPrettyPrinter()
                .writeValue(new File("target/test-report.json"), report);
            System.out.println("\n📊 Custom test report saved to: target/test-report.json");
        } catch (IOException e) {
            System.err.println("Failed to save test report: " + e.getMessage());
        }
    }

    static class TestResult {
        public String name;
        public String status;
        public long duration;
        public String failureMessage;
    }
}
```

## Output Format

Please provide a comprehensive CI/CD and maintenance implementation with the following structure:

### CI/CD Configuration Summary

- **Platform**: [GitHub Actions/GitLab CI/Jenkins]

- **Pipeline Stages**: [list stages]

- **Parallel Execution**: [enabled/disabled, worker count]

- **Test Types Automated**: [unit, integration, e2e]

- **Quality Gates**: [list gates]

### Quality Gate Configuration
| Gate | Threshold | Current | Status |
|------|-----------|---------|--------|
| Code Coverage | 80% | [value] | ✅/❌ |
| Test Pass Rate | 100% | [value] | ✅/❌ |
| Performance | <10% regression | [value] | ✅/❌ |

### Pre-commit Hooks Configured

- [ ] Code formatting (Google Java Format)

- [ ] Linting (Checkstyle)

- [ ] Static analysis (SpotBugs, PMD)

- [ ] Fast test execution

- [ ] Coverage check

### Test Maintenance Status
**Slow Tests Identified**:
| Test | Duration | Recommendation |
|------|----------|----------------|
| [test_name] | [time] | [optimization] |

**Flaky Tests**:
| Test | Failure Rate | Action |
|------|--------------|--------|
| [test_name] | [rate] | [fix planned] |

### Test Execution Metrics

- **Total Tests**: [count]

- **Average Execution Time**: [duration]

- **Parallel Workers**: [count]

- **Tests per Second**: [rate]

- **Coverage**: [percentage]

### CI/CD Pipeline Visualization
```
┌─────────┐     ┌──────────┐     ┌────────────┐     ┌────────┐
│  Lint   │────▶│   Unit   │────▶│Integration │────▶│ Deploy │
└─────────┘     │  Tests   │     │   Tests    │     └────────┘
                └──────────┘     └────────────┘
                     │                 │
                     ▼                 ▼
                ┌─────────┐       ┌─────────┐
                │Coverage │       │Security │
                │  Gate   │       │  Scan   │
                └─────────┘       └─────────┘
```

### Best Practices Implemented

- [ ] All tests automated in CI/CD

- [ ] Quality gates prevent regressions

- [ ] Pre-commit hooks catch issues early

- [ ] Parallel execution for speed

- [ ] Flaky tests tracked and fixed

- [ ] Test maintenance schedule established

### Next Steps

- [ ] Monitor and optimize slow tests

- [ ] Fix identified flaky tests

- [ ] Review and update obsolete tests

- [ ] Enhance test documentation

- [ ] Set up test result dashboard

- [ ] Schedule regular test maintenance reviews

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

1. **Complete CI/CD pipeline configuration** (GitHub Actions or GitLab CI)
2. **Quality gate implementation** with thresholds (Maven/Gradle)
3. **Pre-commit hook configuration** with all checks
4. **Test parallelization setup** for faster execution
5. **Flaky test detection and tracking** system
6. **Test maintenance procedures** and documentation
7. **Test reporting infrastructure** with dashboards
8. **Execution metrics and monitoring** setup
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
