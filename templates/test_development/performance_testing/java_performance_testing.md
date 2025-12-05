---
template_id: java_performance_testing
template_name: Performance Testing - Java
version: 1.0.0
last_updated: 2025-12-03
language: Java
category: test_development
phase: performance_testing
phase_number: 5
difficulty: advanced
estimated_time_hours: 4-6
prerequisites:

  - test_development/mocks_fixtures/java_mocks_fixtures.md
related_templates:

  - test_development/code_coverage/java_code_coverage.md
tools:

  - junit (5.11.3)

  - maven

  - gradle
tags:

  - test-development

  - testing

  - performance

  - java
---
# Java Performance Testing

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                            ► │ [COMPLETE]
│ Phase 3: Test Cases Development                ► │ [COMPLETE]
│ Phase 4: Mocks & Fixtures                      ► │ [COMPLETE]
│ Phase 5: Performance Testing                    ► │ ● CURRENT
│ Phase 6: Code Coverage                             ► │ [NEXT]
│ Phase 7: Maintenance & CI/CD                             ► │ 
│ Phase 8: Reward Hacking Validation                       ► │ 
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 4 (Mocks & Fixtures) should be completed first
**Next Step:** Phase 6 (Code Coverage)

---


## Objective
Implement comprehensive performance testing to validate system behavior under load, identify bottlenecks, measure response times, profile resource usage, detect performance regressions, and ensure scalability requirements are met using Java tooling.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/performance_testing/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/performance_testing/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Performance Test Coverage

- [ ] Load tests implemented for critical endpoints

- [ ] Stress tests validate beyond-capacity behavior

- [ ] Baseline benchmarks established with JMH

- [ ] Performance regression tests configured

- [ ] Resource profiling set up

### Metrics and Monitoring

- [ ] Response time thresholds defined

- [ ] Throughput targets established

- [ ] Resource usage limits set (heap, GC pauses)

- [ ] Error rate thresholds configured

- [ ] Performance reports automated

### Test Infrastructure

- [ ] JMH benchmarking configured

- [ ] Gatling load testing set up

- [ ] Performance test data prepared

- [ ] CI/CD integration planned

- [ ] Results storage and trending implemented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Java Performance Testing Implementation

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/performance_testing"
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

Please implement comprehensive performance testing for this Java project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: Performance Requirements Definition

### Define Performance Targets

Document expected performance characteristics:

**Response Time Requirements**:
| Endpoint/Operation | P50 (median) | P95 | P99 | Timeout |
|-------------------|--------------|-----|-----|---------|
| GET /api/users | <100ms | <200ms | <500ms | 2s |
| POST /api/users | <200ms | <400ms | <1s | 5s |
| Database query | <50ms | <100ms | <200ms | 1s |
| Cache lookup | <5ms | <10ms | <20ms | 100ms |

**Throughput Requirements**:
| Operation | Target RPS | Peak RPS | Concurrent Threads |
|-----------|------------|----------|--------------------|
| REST API | 100 | 500 | 200 |
| Message processing | 50 | 100 | N/A |

**Resource Limits**:

- **Heap Memory**: <2GB

- **GC Pause**: <100ms P99

- **CPU**: <80% average, <95% peak

- **Thread count**: <500 active

- **Database connections**: <50 concurrent

## Phase 2: Benchmarking with JMH

### Setup JMH (Java Microbenchmark Harness)

```xml
<!-- pom.xml -->
<dependencies>
    <dependency>
        <groupId>org.openjdk.jmh</groupId>
        <artifactId>jmh-core</artifactId>
        <version>1.37</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>org.openjdk.jmh</groupId>
        <artifactId>jmh-generator-annprocess</artifactId>
        <version>1.37</version>
        <scope>test</scope>
    </dependency>
</dependencies>

<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-shade-plugin</artifactId>
            <version>3.5.0</version>
            <executions>
                <execution>
                    <phase>package</phase>
                    <goals>
                        <goal>shade</goal>
                    </goals>
                    <configuration>
                        <finalName>benchmarks</finalName>
                        <transformers>
                            <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                                <mainClass>org.openjdk.jmh.Main</mainClass>
                            </transformer>
                        </transformers>
                    </configuration>
                </execution>
            </executions>
        </plugin>
    </plugins>
</build>
```

### Basic JMH Benchmark

```java
package com.example.benchmarks;

import org.openjdk.jmh.annotations.*;
import org.openjdk.jmh.infra.Blackhole;
import org.openjdk.jmh.runner.Runner;
import org.openjdk.jmh.runner.options.Options;
import org.openjdk.jmh.runner.options.OptionsBuilder;

import java.util.concurrent.TimeUnit;

/**

 * Benchmark for data processing operations.
 *

 * Run with: java -jar target/benchmarks.jar
 */
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MILLISECONDS)
@State(Scope.Thread)
@Fork(value = 2, jvmArgs = {"-Xms2G", "-Xmx2G"})
@Warmup(iterations = 3, time = 5)
@Measurement(iterations = 5, time = 10)
public class DataProcessingBenchmark {

    private List<User> testUsers;
    private String searchQuery;

    @Setup
    public void setup() {
        // Setup runs before benchmark
        testUsers = generateTestUsers(1000);
        searchQuery = "test";
    }

    @Benchmark
    public void benchmarkLinearSearch(Blackhole blackhole) {
        // Blackhole prevents JVM from optimizing away unused results
        List<User> results = linearSearch(testUsers, searchQuery);
        blackhole.consume(results);
    }

    @Benchmark
    public void benchmarkBinarySearch(Blackhole blackhole) {
        List<User> results = binarySearch(testUsers, searchQuery);
        blackhole.consume(results);
    }

    @Benchmark
    public void benchmarkStreamProcessing(Blackhole blackhole) {
        List<User> results = testUsers.stream()
            .filter(u -> u.getName().contains(searchQuery))
            .collect(Collectors.toList());
        blackhole.consume(results);
    }

    @Benchmark
    public void benchmarkParallelStreamProcessing(Blackhole blackhole) {
        List<User> results = testUsers.parallelStream()
            .filter(u -> u.getName().contains(searchQuery))
            .collect(Collectors.toList());
        blackhole.consume(results);
    }

    public static void main(String[] args) throws Exception {
        Options opt = new OptionsBuilder()
            .include(DataProcessingBenchmark.class.getSimpleName())
            .build();

        new Runner(opt).run();
    }
}
```

### Advanced JMH Patterns

```java
package com.example.benchmarks;

import org.openjdk.jmh.annotations.*;
import org.openjdk.jmh.infra.Blackhole;

import java.util.concurrent.TimeUnit;

/**

 * Advanced JMH benchmark patterns.
 */
@BenchmarkMode({Mode.Throughput, Mode.AverageTime})
@OutputTimeUnit(TimeUnit.MILLISECONDS)
@State(Scope.Benchmark)
public class AdvancedBenchmarks {

    @Param({"100", "1000", "10000"})
    private int dataSize;

    private List<String> data;

    @Setup(Level.Trial)
    public void setupTrial() {
        // Runs once per trial (fork)
        System.out.println("Setting up trial with data size: " + dataSize);
    }

    @Setup(Level.Iteration)
    public void setupIteration() {
        // Runs before each iteration
        data = generateTestData(dataSize);
    }

    @TearDown(Level.Iteration)
    public void tearDownIteration() {
        // Cleanup after each iteration
        data = null;
        System.gc();
    }

    @Benchmark
    @Fork(value = 1, jvmArgs = {"-XX:+UseG1GC"})
    public void benchmarkWithG1GC(Blackhole blackhole) {
        blackhole.consume(processData(data));
    }

    @Benchmark
    @Fork(value = 1, jvmArgs = {"-XX:+UseParallelGC"})
    public void benchmarkWithParallelGC(Blackhole blackhole) {
        blackhole.consume(processData(data));
    }

    /**

     * Benchmark method with state for each thread.
     */
    @Benchmark
    @Threads(4)
    public void benchmarkMultiThreaded(ThreadState state, Blackhole blackhole) {
        state.counter++;
        blackhole.consume(processData(data));
    }

    @State(Scope.Thread)
    public static class ThreadState {
        long counter = 0;

        @TearDown(Level.Trial)
        public void tearDown() {
            System.out.println("Thread processed " + counter + " operations");
        }
    }

    /**

     * Benchmark with custom measurement.
     */
    @Benchmark
    @Measurement(iterations = 10, time = 5, timeUnit = TimeUnit.SECONDS)
    public void benchmarkCustomMeasurement(Blackhole blackhole) {
        blackhole.consume(expensiveOperation(data));
    }

    /**

     * Group multiple benchmarks together.
     */
    @Benchmark
    @Group("g")
    @GroupThreads(3)
    public void groupRead(Blackhole blackhole) {
        blackhole.consume(readOperation(data));
    }

    @Benchmark
    @Group("g")
    @GroupThreads(1)
    public void groupWrite(Blackhole blackhole) {
        blackhole.consume(writeOperation(data));
    }
}
```

### Running JMH Benchmarks

```bash
# Build benchmarks JAR
mvn clean package

# Run all benchmarks
java -jar target/benchmarks.jar

# Run specific benchmark
java -jar target/benchmarks.jar DataProcessingBenchmark

# Run with profilers
java -jar target/benchmarks.jar -prof gc        # GC profiling
java -jar target/benchmarks.jar -prof stack     # Stack profiling
java -jar target/benchmarks.jar -prof perf      # Linux perf

# Generate JSON results
java -jar target/benchmarks.jar -rf json -rff results.json

# Quick run for testing
java -jar target/benchmarks.jar -f 1 -wi 1 -i 3
```

## Phase 3: Load Testing with Gatling

### Setup Gatling

```xml
<!-- pom.xml -->
<dependencies>
    <dependency>
        <groupId>io.gatling.highcharts</groupId>
        <artifactId>gatling-charts-highcharts</artifactId>
        <version>3.9.5</version>
        <scope>test</scope>
    </dependency>
</dependencies>

<build>
    <plugins>
        <plugin>
            <groupId>io.gatling</groupId>
            <artifactId>gatling-maven-plugin</artifactId>
            <version>4.5.0</version>
        </plugin>
    </plugins>
</build>
```

### Basic Gatling Load Test

```scala
package simulations

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

/**

 * Basic load test for REST API.
 *

 * Run with: mvn gatling:test -Dgatling.simulationClass=simulations.BasicApiSimulation
 */
class BasicApiSimulation extends Simulation {

  val httpProtocol = http
    .baseUrl("http://localhost:8080")
    .acceptHeader("application/json")
    .contentTypeHeader("application/json")

  val scn = scenario("API Load Test")
    .exec(
      http("Get Users")
        .get("/api/users")
        .check(status.is(200))
        .check(responseTimeInMillis.lte(200))
    )
    .pause(1)
    .exec(
      http("Create User")
        .post("/api/users")
        .body(StringBody("""{"username":"testuser","email":"test@example.com"}"""))
        .check(status.is(201))
        .check(responseTimeInMillis.lte(400))
    )
    .pause(1)
    .exec(
      http("Get User Detail")
        .get("/api/users/${userId}")
        .check(status.is(200))
    )

  setUp(
    scn.inject(
      nothingFor(4 seconds),
      atOnceUsers(10),
      rampUsers(50) during (30 seconds),
      constantUsersPerSec(20) during (1 minute),
      rampUsersPerSec(10) to 50 during (2 minutes)
    )
  ).protocols(httpProtocol)
   .assertions(
     global.responseTime.max.lt(1000),
     global.responseTime.percentile(95).lt(500),
     global.successfulRequests.percent.gt(99)
   )
}
```

### Advanced Gatling Scenarios

```scala
package simulations

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

class AdvancedApiSimulation extends Simulation {

  val httpProtocol = http
    .baseUrl("http://localhost:8080")
    .acceptHeader("application/json")
    .contentTypeHeader("application/json")
    .userAgentHeader("Gatling Load Test")

  // Feeders for test data
  val userFeeder = csv("users.csv").random
  val searchFeeder = Iterator.continually(Map(
    "query" -> scala.util.Random.alphanumeric.take(10).mkString
  ))

  // Reusable request chains
  val login = exec(
    http("Login")
      .post("/api/login")
      .body(StringBody("""{"username":"${username}","password":"${password}"}"""))
      .check(status.is(200))
      .check(jsonPath("$.token").saveAs("authToken"))
  )

  val getProfile = exec(
    http("Get Profile")
      .get("/api/profile")
      .header("Authorization", "Bearer ${authToken}")
      .check(status.is(200))
      .check(jsonPath("$.id").saveAs("userId"))
  )

  val updateProfile = exec(
    http("Update Profile")
      .put("/api/profile")
      .header("Authorization", "Bearer ${authToken}")
      .body(StringBody("""{"bio":"Updated bio text"}"""))
      .check(status.is(200))
  )

  // Scenario: Normal user workflow
  val normalUser = scenario("Normal User")
    .feed(userFeeder)
    .exec(login)
    .pause(2)
    .exec(getProfile)
    .pause(5, 10)
    .repeat(3) {
      exec(
        http("Browse Users")
          .get("/api/users")
          .queryParam("page", "${page}")
          .header("Authorization", "Bearer ${authToken}")
          .check(status.is(200))
      )
      .pause(2, 5)
    }
    .exec(updateProfile)
    .pause(1)

  // Scenario: Heavy user
  val heavyUser = scenario("Heavy User")
    .feed(userFeeder)
    .exec(login)
    .pause(1)
    .during(2 minutes) {
      feed(searchFeeder)
      .exec(
        http("Search")
          .get("/api/search")
          .queryParam("q", "${query}")
          .header("Authorization", "Bearer ${authToken}")
          .check(status.is(200))
      )
      .pause(500 milliseconds, 2 seconds)
    }

  // Scenario: Admin operations
  val adminUser = scenario("Admin")
    .feed(userFeeder)
    .exec(login)
    .pause(1)
    .exec(
      http("Get Admin Dashboard")
        .get("/api/admin/dashboard")
        .header("Authorization", "Bearer ${authToken}")
        .check(status.is(200))
    )
    .pause(5)
    .repeat(10) {
      exec(
        http("Get User Reports")
          .get("/api/admin/reports/users")
          .header("Authorization", "Bearer ${authToken}")
          .check(status.is(200))
      )
      .pause(3)
    }

  setUp(
    normalUser.inject(
      rampUsers(100) during (2 minutes),
      constantUsersPerSec(50) during (5 minutes)
    ),
    heavyUser.inject(
      rampUsers(20) during (1 minute),
      constantUsersPerSec(10) during (5 minutes)
    ),
    adminUser.inject(
      rampUsers(5) during (30 seconds),
      constantUsersPerSec(2) during (5 minutes)
    )
  ).protocols(httpProtocol)
   .maxDuration(10 minutes)
   .assertions(
     global.responseTime.percentile(95).lt(500),
     global.responseTime.percentile(99).lt(1000),
     global.successfulRequests.percent.gt(99),
     forAll.failedRequests.count.lt(100)
   )
}
```

### Gatling with Java DSL

```java
package simulations;

import io.gatling.javaapi.core.*;
import io.gatling.javaapi.http.*;
import static io.gatling.javaapi.core.CoreDsl.*;
import static io.gatling.javaapi.http.HttpDsl.*;
import java.time.Duration;

/**

 * Gatling load test using Java DSL.
 */
public class JavaApiSimulation extends Simulation {

    HttpProtocolBuilder httpProtocol = http
        .baseUrl("http://localhost:8080")
        .acceptHeader("application/json")
        .contentTypeHeader("application/json");

    ScenarioBuilder scn = scenario("API Load Test")
        .exec(
            http("Get Users")
                .get("/api/users")
                .check(status().is(200))
                .check(responseTimeInMillis().lte(200))
        )
        .pause(Duration.ofSeconds(1))
        .exec(
            http("Create User")
                .post("/api/users")
                .body(StringBody("{\"username\":\"test\",\"email\":\"test@example.com\"}"))
                .check(status().is(201))
                .check(jsonPath("$.id").saveAs("userId"))
        )
        .pause(Duration.ofSeconds(1))
        .exec(
            http("Get User Detail")
                .get("/api/users/#{userId}")
                .check(status().is(200))
        );

    {
        setUp(
            scn.injectOpen(
                nothingFor(Duration.ofSeconds(4)),
                atOnceUsers(10),
                rampUsers(50).during(Duration.ofSeconds(30)),
                constantUsersPerSec(20).during(Duration.ofMinutes(1))
            )
        ).protocols(httpProtocol)
         .assertions(
             global().responseTime().max().lt(1000),
             global().responseTime().percentile(95.0).lt(500),
             global().successfulRequests().percent().gt(99.0)
         );
    }
}
```

## Phase 4: Stress Testing

### Stress Test Implementation

```java
package com.example.tests.stress;

import org.junit.jupiter.api.Test;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

/**

 * Stress tests to find breaking points.
 */
public class StressTests {

    @Test
    public void testMaxConcurrentRequests() throws Exception {
        int maxThreads = 1000;
        ExecutorService executor = Executors.newFixedThreadPool(maxThreads);
        AtomicInteger successCount = new AtomicInteger(0);
        AtomicInteger failureCount = new AtomicInteger(0);
        CountDownLatch latch = new CountDownLatch(maxThreads);

        long startTime = System.currentTimeMillis();

        for (int i = 0; i < maxThreads; i++) {
            executor.submit(() -> {
                try {
                    Response response = apiClient.get("/api/users");
                    if (response.isSuccessful()) {
                        successCount.incrementAndGet();
                    } else {
                        failureCount.incrementAndGet();
                    }
                } catch (Exception e) {
                    failureCount.incrementAndGet();
                } finally {
                    latch.countDown();
                }
            });
        }

        latch.await(5, TimeUnit.MINUTES);
        executor.shutdown();

        long duration = System.currentTimeMillis() - startTime;

        System.out.println("Stress Test Results:");
        System.out.println("  Threads: " + maxThreads);
        System.out.println("  Success: " + successCount.get());
        System.out.println("  Failures: " + failureCount.get());
        System.out.println("  Duration: " + duration + "ms");
        System.out.println("  Success Rate: " +
            (100.0 * successCount.get() / maxThreads) + "%");

        // Assert acceptable failure rate
        assertTrue(successCount.get() > maxThreads * 0.95,
            "Too many failures under stress");
    }

    @Test
    public void testMemoryStress() {
        Runtime runtime = Runtime.getRuntime();
        long initialMemory = runtime.totalMemory() - runtime.freeMemory();

        // Perform memory-intensive operations
        for (int i = 0; i < 10000; i++) {
            List<User> users = userService.findAll();
            processUsers(users);
        }

        System.gc();
        long finalMemory = runtime.totalMemory() - runtime.freeMemory();
        long memoryIncrease = finalMemory - initialMemory;

        System.out.println("Memory Usage:");
        System.out.println("  Initial: " + (initialMemory / 1024 / 1024) + "MB");
        System.out.println("  Final: " + (finalMemory / 1024 / 1024) + "MB");
        System.out.println("  Increase: " + (memoryIncrease / 1024 / 1024) + "MB");

        // Assert no significant memory leak
        assertTrue(memoryIncrease < 100 * 1024 * 1024,
            "Potential memory leak detected");
    }
}
```

## Phase 5: Response Time Testing

### Response Time Benchmarks

```java
package com.example.tests.performance;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;

/**

 * Response time performance tests.
 */
public class ResponseTimeTests {

    @Test
    public void testResponseTimePercentiles() {
        List<Long> responseTimes = new ArrayList<>();

        // Collect response times
        for (int i = 0; i < 100; i++) {
            long start = System.nanoTime();
            apiClient.get("/api/users");
            long elapsed = TimeUnit.NANOSECONDS.toMillis(
                System.nanoTime() - start
            );
            responseTimes.add(elapsed);
        }

        Collections.sort(responseTimes);

        long p50 = responseTimes.get(49);
        long p95 = responseTimes.get(94);
        long p99 = responseTimes.get(98);

        System.out.println("Response Time Percentiles:");
        System.out.println("  P50: " + p50 + "ms");
        System.out.println("  P95: " + p95 + "ms");
        System.out.println("  P99: " + p99 + "ms");

        // Assert against requirements
        assertTrue(p50 < 100, "P50 exceeds threshold: " + p50 + "ms");
        assertTrue(p95 < 200, "P95 exceeds threshold: " + p95 + "ms");
        assertTrue(p99 < 500, "P99 exceeds threshold: " + p99 + "ms");
    }

    @ParameterizedTest
    @ValueSource(ints = {1, 10, 50, 100})
    public void testResponseTimeUnderConcurrency(int concurrency)
            throws Exception {
        ExecutorService executor = Executors.newFixedThreadPool(concurrency);
        List<Future<Long>> futures = new ArrayList<>();

        long start = System.currentTimeMillis();

        for (int i = 0; i < concurrency; i++) {
            futures.add(executor.submit(() -> {
                long requestStart = System.nanoTime();
                apiClient.get("/api/users");
                return TimeUnit.NANOSECONDS.toMillis(
                    System.nanoTime() - requestStart
                );
            }));
        }

        List<Long> responseTimes = new ArrayList<>();
        for (Future<Long> future : futures) {
            responseTimes.add(future.get());
        }

        executor.shutdown();

        long totalDuration = System.currentTimeMillis() - start;
        double avgResponseTime = responseTimes.stream()
            .mapToLong(Long::longValue)
            .average()
            .orElse(0);

        System.out.println("Concurrency " + concurrency + ":");
        System.out.println("  Avg Response: " + avgResponseTime + "ms");
        System.out.println("  Total Duration: " + totalDuration + "ms");

        // Response time shouldn't degrade significantly
        assertTrue(avgResponseTime < 200,
            "Response time degraded: " + avgResponseTime + "ms");
    }
}
```

## Phase 6: Profiling and Optimization

### JVM Profiling

```java
package com.example.tests.profiling;

import java.lang.management.*;

/**

 * JVM performance monitoring utilities.
 */
public class JvmProfiler {

    public static void printMemoryUsage() {
        MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
        MemoryUsage heapUsage = memoryBean.getHeapMemoryUsage();
        MemoryUsage nonHeapUsage = memoryBean.getNonHeapMemoryUsage();

        System.out.println("Memory Usage:");
        System.out.println("  Heap Used: " +
            (heapUsage.getUsed() / 1024 / 1024) + "MB");
        System.out.println("  Heap Max: " +
            (heapUsage.getMax() / 1024 / 1024) + "MB");
        System.out.println("  Non-Heap Used: " +
            (nonHeapUsage.getUsed() / 1024 / 1024) + "MB");
    }

    public static void printGCStats() {
        List<GarbageCollectorMXBean> gcBeans =
            ManagementFactory.getGarbageCollectorMXBeans();

        System.out.println("Garbage Collection Stats:");
        for (GarbageCollectorMXBean gcBean : gcBeans) {
            System.out.println("  " + gcBean.getName() + ":");
            System.out.println("    Collections: " + gcBean.getCollectionCount());
            System.out.println("    Time: " + gcBean.getCollectionTime() + "ms");
        }
    }

    public static void printThreadStats() {
        ThreadMXBean threadBean = ManagementFactory.getThreadMXBean();

        System.out.println("Thread Stats:");
        System.out.println("  Total Started: " +
            threadBean.getTotalStartedThreadCount());
        System.out.println("  Current: " + threadBean.getThreadCount());
        System.out.println("  Peak: " + threadBean.getPeakThreadCount());
        System.out.println("  Daemon: " + threadBean.getDaemonThreadCount());
    }

    public static void monitorHotMethods() {
        ThreadMXBean threadBean = ManagementFactory.getThreadMXBean();
        threadBean.setThreadCpuTimeEnabled(true);

        long[] threadIds = threadBean.getAllThreadIds();
        for (long threadId : threadIds) {
            ThreadInfo info = threadBean.getThreadInfo(threadId, Integer.MAX_VALUE);
            long cpuTime = threadBean.getThreadCpuTime(threadId);

            if (cpuTime > 1000000000) { // 1 second threshold
                System.out.println("Hot Thread: " + info.getThreadName());
                System.out.println("  CPU Time: " + (cpuTime / 1000000) + "ms");
                StackTraceElement[] stack = info.getStackTrace();
                for (int i = 0; i < Math.min(5, stack.length); i++) {
                    System.out.println("    " + stack[i]);
                }
            }
        }
    }
}
```

### Profiling with JFR (Java Flight Recorder)

```bash
# Start application with JFR
java -XX:StartFlightRecording=duration=60s,filename=recording.jfr \
     -XX:FlightRecorderOptions=stackdepth=256 \
     -jar application.jar

# Convert JFR to readable format
jfr print recording.jfr > ${OUTPUT_DIR}/exports/recording.txt

# Analyze with JMC (Java Mission Control)
jmc recording.jfr
```

## Phase 7: Performance Regression Detection

### Baseline Management

```java
package com.example.tests.regression;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.File;
import java.util.HashMap;
import java.util.Map;

/**

 * Performance baseline management for regression detection.
 */
public class PerformanceBaseline {

    private static final String BASELINE_FILE = "performance-baseline.json";
    private static final ObjectMapper mapper = new ObjectMapper();

    private Map<String, BenchmarkResult> baselines;

    public PerformanceBaseline() {
        this.baselines = load();
    }

    public void save(String name, BenchmarkResult result) {
        baselines.put(name, result);
        writeToFile();
    }

    public BenchmarkResult get(String name) {
        return baselines.get(name);
    }

    public RegressionResult compare(String name, BenchmarkResult current) {
        BenchmarkResult baseline = get(name);

        if (baseline == null) {
            save(name, current);
            return new RegressionResult(false, true, null);
        }

        double percentChange = ((current.getScore() - baseline.getScore()) /
                               baseline.getScore()) * 100;

        boolean isRegression = percentChange > 10.0; // 10% threshold

        return new RegressionResult(isRegression, false, percentChange);
    }

    private Map<String, BenchmarkResult> load() {
        File file = new File(BASELINE_FILE);
        if (file.exists()) {
            try {
                return mapper.readValue(file,
                    mapper.getTypeFactory().constructMapType(
                        HashMap.class, String.class, BenchmarkResult.class
                    )
                );
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        return new HashMap<>();
    }

    private void writeToFile() {
        try {
            mapper.writerWithDefaultPrettyPrinter()
                  .writeValue(new File(BASELINE_FILE), baselines);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static class BenchmarkResult {
        private double score;
        private String unit;
        private long timestamp;

        // Getters and setters
        public double getScore() { return score; }
        public void setScore(double score) { this.score = score; }
        public String getUnit() { return unit; }
        public void setUnit(String unit) { this.unit = unit; }
        public long getTimestamp() { return timestamp; }
        public void setTimestamp(long timestamp) { this.timestamp = timestamp; }
    }

    public static class RegressionResult {
        private boolean isRegression;
        private boolean isNewBaseline;
        private Double percentChange;

        public RegressionResult(boolean isRegression, boolean isNewBaseline,
                               Double percentChange) {
            this.isRegression = isRegression;
            this.isNewBaseline = isNewBaseline;
            this.percentChange = percentChange;
        }

        // Getters
        public boolean isRegression() { return isRegression; }
        public boolean isNewBaseline() { return isNewBaseline; }
        public Double getPercentChange() { return percentChange; }
    }
}
```

## Phase 8: CI/CD Integration

### Maven Configuration

```xml
<!-- pom.xml -->
<build>
    <plugins>
        <!-- JMH Benchmarks -->
        <plugin>
            <groupId>org.codehaus.mojo</groupId>
            <artifactId>exec-maven-plugin</artifactId>
            <version>3.1.0</version>
            <executions>
                <execution>
                    <id>run-benchmarks</id>
                    <phase>verify</phase>
                    <goals>
                        <goal>java</goal>
                    </goals>
                    <configuration>
                        <mainClass>org.openjdk.jmh.Main</mainClass>
                        <arguments>
                            <argument>-rf</argument>
                            <argument>json</argument>
                            <argument>-rff</argument>
                            <argument>benchmark-results.json</argument>
                        </arguments>
                    </configuration>
                </execution>
            </executions>
        </plugin>

        <!-- Gatling Load Tests -->
        <plugin>
            <groupId>io.gatling</groupId>
            <artifactId>gatling-maven-plugin</artifactId>
            <version>4.5.0</version>
            <configuration>
                <runMultipleSimulations>true</runMultipleSimulations>
            </configuration>
        </plugin>
    </plugins>
</build>
```

### GitHub Actions Workflow

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on:
  pull_request:
    branches: [ main ]
  schedule:

    - cron: '0 2 * * *'

jobs:
  performance:
    runs-on: ubuntu-latest

    steps:

    - uses: actions/checkout@v3

    - name: Set up JDK 17
      uses: actions/setup-java@v3
      with:
        java-version: '17'
        distribution: 'temurin'
        cache: maven

    - name: Build project
      run: mvn clean package -DskipTests

    - name: Run JMH benchmarks
      run: java -jar target/benchmarks.jar -rf json -rff benchmark-results.json

    - name: Check for regressions
      run: mvn test -Dtest=RegressionTests

    - name: Run Gatling load tests
      run: mvn gatling:test

    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: |
          benchmark-results.json
          target/gatling/**

    - name: Comment PR
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const results = JSON.parse(fs.readFileSync('benchmark-results.json'));
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: '## Performance Test Results\n\n' + results.summary
          });
```

## Output Format

Please provide a comprehensive performance testing implementation with the following structure:

### Performance Test Summary

- **Benchmarks Implemented**: [count]

- **Load Tests Created**: [count]

- **Performance Baselines Established**: [yes/no]

- **Regression Detection Configured**: [yes/no]

- **Profiling Tools Set Up**: [list]

### Performance Requirements
| Metric | Target | Measured | Status |
|--------|--------|----------|--------|
| API response P95 | <200ms | [value] | ✅/❌ |
| Throughput | 100 RPS | [value] | ✅/❌ |
| Heap usage | <2GB | [value] | ✅/❌ |
| GC pause P99 | <100ms | [value] | ✅/❌ |

### Benchmark Results
```
Benchmark: DataProcessingBenchmark.benchmarkStreamProcessing
Mode: Average Time
Score: 45.23 ms/op
Error: ±3.12 ms/op
Samples: 100
```

### Load Test Results
```
Simulation: BasicApiSimulation
Users: 100
RPS: 87.3
Response Time P50: 124ms
Response Time P95: 287ms
Response Time P99: 445ms
Success Rate: 99.8%
```

### Bottlenecks Identified
1. **Database Query in UserService.findAll()**

   - **Issue**: N+1 query problem

   - **Impact**: 200ms average response time

   - **Recommendation**: Use JOIN FETCH or batch loading

2. **JSON Serialization**

   - **Issue**: Jackson serialization overhead

   - **Impact**: 150ms for large responses

   - **Recommendation**: Use @JsonView or DTOs to reduce payload

### Performance Improvement Recommendations

- [ ] Add database query optimization (indexes, batch loading)

- [ ] Implement Redis caching for frequent queries

- [ ] Add pagination for large result sets

- [ ] Enable GZIP compression for REST responses

- [ ] Optimize Jackson serialization with custom serializers

### Test Execution
```bash
# Run JMH benchmarks
mvn clean package
java -jar target/benchmarks.jar

# Run Gatling load tests
mvn gatling:test

# Profile with JFR
java -XX:StartFlightRecording=duration=60s,filename=recording.jfr -jar app.jar
```

### Next Steps

- [ ] Establish performance baselines for all critical operations

- [ ] Integrate performance tests into CI/CD pipeline

- [ ] Set up APM (Application Performance Monitoring)

- [ ] Create performance dashboard with Grafana

- [ ] Schedule regular performance review meetings

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

1. **Performance test suite** with JMH benchmarks and Gatling load tests

2. **Performance baselines** documented

3. **Load test scenarios** for critical endpoints

4. **Profiling results** with bottleneck identification

5. **Regression detection** configuration

6. **CI/CD integration** for automated performance gates

7. **Performance report** with metrics and recommendations
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
