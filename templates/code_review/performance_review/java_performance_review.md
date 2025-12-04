---
template_id: java_performance_review
template_name: Performance Review - Java
version: 1.0.0
last_updated: 2025-12-03
language: Java
category: code_review
phase: performance_review
phase_number: 4
difficulty: advanced
estimated_time_hours: 2-3
prerequisites:
  - code_review/security_review/java_security_review.md
related_templates:
  - code_review/code_quality/java_code_quality.md
tools:
  - junit (5.11.3)
  - maven
  - gradle
tags:
  - code-review
  - performance
  - code-review
  - java
---
# Java Performance Review

## Objective
Systematically identify performance bottlenecks, inefficient algorithms, memory leaks, and resource usage issues. Provide data-driven optimization recommendations to improve application speed, scalability, and resource efficiency.

## Output Directory Structure

All outputs should be saved in organized directories:

```
review/performance_review/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `review/performance_review/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Review Checklist

### Performance Profiling

- [ ] CPU profiling completed (JProfiler, VisualVM, YourKit)

- [ ] Memory profiling performed (heap analysis, leak detection)

- [ ] Garbage collection analysis conducted

- [ ] Thread profiling and contention analysis done

- [ ] I/O operations analyzed

- [ ] Hot paths and bottlenecks identified

### Algorithm Efficiency

- [ ] Time complexity evaluated (O(n), O(n²), etc.)

- [ ] Space complexity assessed

- [ ] Inefficient loops identified (nested, redundant)

- [ ] Collection usage patterns reviewed

- [ ] Stream API performance evaluated

### Memory Management

- [ ] Memory leaks detected

- [ ] Heap usage patterns analyzed

- [ ] Object retention analysis completed

- [ ] GC overhead and pause times measured

- [ ] Memory pooling opportunities identified

### Database Performance

- [ ] Query execution times measured

- [ ] N+1 query problems identified

- [ ] Missing indexes detected

- [ ] JPA/Hibernate query optimization reviewed

- [ ] Connection pooling configuration evaluated

### Concurrency & Threading

- [ ] Thread pool configuration reviewed

- [ ] Synchronization overhead assessed

- [ ] Lock contention identified

- [ ] CompletableFuture and reactive patterns evaluated

- [ ] Parallel streams usage assessed

## Severity Classification

Use this framework to classify and prioritize all findings from the code review.

### CRITICAL (Fix Immediately)

**Definition:** Issues that create immediate risks to system stability, data integrity, or compliance.

**Examples:**
- Security vulnerabilities (SQL injection, XSS, authentication bypass)
- Resource leaks (unclosed connections, file handles, memory leaks)
- Data loss risks (destructive operations without validation)
- Thread safety violations (race conditions, deadlocks)
- Compliance violations (GDPR, HIPAA, PCI-DSS)

**Action Required:**
- Block deployment until fixed
- Require hotfix within 24 hours
- Add tests to prevent regression
- Document root cause and fix

---

### HIGH (Fix Before Next Release)

**Definition:** Issues that significantly impact maintainability, performance, or correctness but don't cause immediate failures.

**Examples:**
- Incorrect business logic (wrong calculations, flawed algorithms)
- Performance bottlenecks (O(n²) algorithms, missing indexes, inefficient queries)
- Memory inefficiency (loading large datasets into memory unnecessarily)
- Breaking API changes without deprecation
- Missing critical error handling (network errors, API failures not caught)

**Action Required:**
- Schedule fix in current sprint
- Cannot release without resolution
- Update documentation
- Performance test after fix

---

### MEDIUM (Fix in Next Cycle)

**Definition:** Code smells and technical debt that reduce maintainability but don't affect correctness.

**Examples:**
- High complexity (cyclomatic complexity >10, functions >100 lines)
- Code duplication (>10 lines duplicated across modules)
- Poor naming (unclear variable/function names, inconsistent conventions)
- Missing tests (<80% coverage on critical paths)
- Incomplete error messages (no context for debugging)

**Action Required:**
- Add to backlog
- Prioritize in next sprint planning
- Consider during refactoring opportunities
- Track technical debt metrics

---

### LOW (Nice to Have)

**Definition:** Style inconsistencies and minor optimizations that don't impact functionality.

**Examples:**
- Style violations (linting warnings, formatting issues)
- Minor performance optimizations (in non-critical code paths)
- Missing documentation on helper functions
- Verbose code that could be more concise
- Debug statements left in code

**Action Required:**
- Fix opportunistically during other work
- Batch with other low-priority changes
- Good for new contributors
- Can be deferred indefinitely

---

## Severity Assignment Guidelines

**When to Escalate Severity:**
- Issue affects **production environment** → escalate one level
- Issue affects **customer-facing features** → escalate one level
- Issue has **no workaround** → escalate one level
- Issue appears in **multiple locations** → escalate one level

**When to De-escalate Severity:**
- Issue only in **test/development code** → de-escalate one level
- Issue has **easy workaround** → de-escalate one level
- Issue is **isolated to single module** → de-escalate one level
- Issue **rarely executed** (edge case) → de-escalate one level

**Examples:**
- Memory leak in production API: **HIGH → CRITICAL** (production + customer-facing)
- Style violation in test file: **LOW → Ignore** (test code + style only)
- Duplicated logic across 15 modules: **MEDIUM → HIGH** (multiple locations)

---

## Reporting Format

For each finding, include:

**1. Severity Level:** [CRITICAL/HIGH/MEDIUM/LOW]

**2. Location:** File path and line numbers

**3. Issue Description:** What's wrong and why it matters

**4. Impact:** Specific consequences of not fixing

**5. Recommendation:** How to fix (with code example if applicable)

**6. Effort Estimate:** Time to fix (hours/days)

**Example Finding:**
```markdown
### HIGH: Performance Bottleneck in User Search

**Location:** `src/services/userService:145-167`

**Issue:** The user search function loads all users into memory and performs linear search on every request.

**Impact:**
- Response time degrades with user count (currently 500ms for 10k users)
- High memory usage (50MB+ per request)
- Poor scalability (can't handle >100k users)

**Recommendation:**
Move filtering to database with indexed query:
- Add database index on search fields
- Use database LIKE/ILIKE queries
- Implement pagination (limit results to 50)
- Add caching for common searches

**Effort:** 3 hours (2 hours implementation + 1 hour testing)

**Priority:** Must fix before next release (performance SLA violation)
```

---


## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Java Performance Review

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="review/performance_review"
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

Please perform a comprehensive performance review of this Java application following this protocol:

## Phase 1: Performance Profiling Setup

1. **JVM Profiling Tools**
   ```bash
   # VisualVM (free, bundled with JDK)
   jvisualvm

   # JProfiler (commercial)
   jprofiler

   # YourKit (commercial)
   java -agentpath:/path/to/yjp/bin/linux-x86-64/libyjpagent.so YourApp

   # Async-profiler (free, low overhead)
   ./profiler.sh -d 30 -f profile.html <pid>

   # Java Flight Recorder (JFR)
   java -XX:StartFlightRecording=duration=60s,filename=recording.jfr YourApp
   jfr print recording.jfr
   ```

2. **CPU Profiling**
   - Identify methods consuming >5% of CPU time
   - Measure method call frequencies
   - Detect hot loops and recursive calls
   - Profile both application and JVM time

3. **Memory Profiling**
   ```bash
   # Heap dump analysis
   jmap -dump:format=b,file=heap.bin <pid>
   jhat heap.bin  # Or use Eclipse MAT

   # Live object monitoring
   jcmd <pid> GC.class_histogram

   # Memory allocation profiling
   java -XX:+UseG1GC -XX:+PrintGC -XX:+PrintGCDetails YourApp
   ```

4. **Thread Analysis**
   ```bash
   # Thread dump
   jstack <pid> > ${OUTPUT_DIR}/exports/threads.txt

   # Continuous thread monitoring
   jcmd <pid> Thread.print
   ```

## Phase 2: Bottleneck Identification

1. **CPU Bottlenecks**
   - Methods with high CPU consumption
   - Synchronization bottlenecks
   - Excessive string operations
   - Reflection and dynamic proxy overhead
   - Serialization/deserialization costs

2. **Memory Bottlenecks**
   - Objects with large retained size
   - Memory leaks (growing heap usage)
   - Excessive object creation
   - Large collections in memory
   - ClassLoader leaks

3. **I/O Bottlenecks**
   - Blocking I/O operations
   - Database query performance
   - Network call latency
   - File system operations
   - Logging overhead

## Phase 3: Algorithm Efficiency Review

1. **Collection Performance**
   ```java
   // Inefficient patterns to search for:

   // 1. Using wrong collection type
   // BAD: ArrayList for frequent searches (O(n))
   List<String> list = new ArrayList<>();
   if (list.contains(item)) { }  // O(n) lookup

   // GOOD: HashSet for membership checks (O(1))
   Set<String> set = new HashSet<>();
   if (set.contains(item)) { }  // O(1) lookup

   // 2. Iterating entire collection unnecessarily
   // BAD
   for (User user : allUsers) {
       if (user.getId().equals(targetId)) {
           return user;
       }
   }
   // GOOD: Use Map for O(1) lookup
   userMap.get(targetId);

   // 3. Growing ArrayList without initial capacity
   // BAD
   List<String> list = new ArrayList<>();  // Default capacity 10
   for (int i = 0; i < 10000; i++) {
       list.add(string);  // Multiple resizes
   }
   // GOOD
   List<String> list = new ArrayList<>(10000);

   // 4. Inefficient Map iteration
   // BAD
   for (String key : map.keySet()) {
       Value value = map.get(key);  // Double lookup
   }
   // GOOD
   for (Map.Entry<String, Value> entry : map.entrySet()) {
       String key = entry.getKey();
       Value value = entry.getValue();
   }
   ```

2. **String Operations**
   ```java
   // Performance issues:

   // 1. String concatenation in loops
   // BAD: O(n²) complexity
   String result = "";
   for (String s : strings) {
       result += s;  // Creates new string each iteration
   }
   // GOOD: O(n) complexity
   StringBuilder sb = new StringBuilder();
   for (String s : strings) {
       sb.append(s);
   }
   String result = sb.toString();

   // 2. String.split() for simple cases
   // BAD: Regex overhead
   String[] parts = line.split(",");
   // GOOD: For simple delimiter
   StringTokenizer st = new StringTokenizer(line, ",");

   // 3. String comparison
   // BAD: Multiple string comparisons
   if (status.equals("active") || status.equals("pending")) { }
   // GOOD: Use enum
   if (status == Status.ACTIVE || status == Status.PENDING) { }
   ```

3. **Stream API Performance**
   ```java
   // Check for Stream API misuse:

   // 1. Unnecessary boxing/unboxing
   // BAD
   list.stream()
       .map(i -> i * 2)  // Boxing Integer to int
       .collect(Collectors.toList());
   // GOOD: Use primitive streams
   IntStream.range(0, list.size())
       .map(i -> list.get(i) * 2)
       .boxed()
       .collect(Collectors.toList());

   // 2. Multiple passes when one suffices
   // BAD
   long count = list.stream().filter(predicate).count();
   List<T> filtered = list.stream().filter(predicate).collect(toList());
   // GOOD: Single pass
   List<T> filtered = list.stream().filter(predicate).collect(toList());
   long count = filtered.size();

   // 3. Parallel streams for small collections
   // BAD: Overhead > benefit for small lists
   smallList.parallelStream().map(function).collect(toList());
   // GOOD: Use sequential for small collections
   smallList.stream().map(function).collect(toList());
   ```

## Phase 4: Database Performance Analysis

1. **JPA/Hibernate Performance**
   ```java
   // Enable SQL logging
   spring.jpa.show-sql=true
   spring.jpa.properties.hibernate.format_sql=true
   logging.level.org.hibernate.SQL=DEBUG
   logging.level.org.hibernate.type.descriptor.sql.BasicBinder=TRACE
   ```

2. **N+1 Query Detection**
   ```java
   // BAD: N+1 queries
   @Entity
   public class Post {
       @ManyToOne
       private User author;  // Lazy loaded by default
   }

   List<Post> posts = postRepository.findAll();  // 1 query
   for (Post post : posts) {
       String name = post.getAuthor().getName();  // N queries
   }

   // GOOD: Eager fetching
   @Query("SELECT p FROM Post p JOIN FETCH p.author")
   List<Post> findAllWithAuthors();

   // GOOD: Entity graph
   @EntityGraph(attributePaths = {"author"})
   List<Post> findAll();
   ```

3. **Query Optimization**
   ```java
   // BAD: Fetching unnecessary data
   @Query("SELECT p FROM Post p")
   List<Post> findAll();  // Loads all fields

   // GOOD: Project only needed fields
   @Query("SELECT new com.example.PostSummary(p.id, p.title) FROM Post p")
   List<PostSummary> findAllSummaries();

   // BAD: Missing pagination
   List<Post> findAll();  // Could load thousands of records

   // GOOD: Use pagination
   Page<Post> findAll(Pageable pageable);

   // BAD: Inappropriate fetch type
   @OneToMany(fetch = FetchType.EAGER)  // Always loads
   private List<Comment> comments;

   // GOOD: Lazy loading with explicit fetching when needed
   @OneToMany(fetch = FetchType.LAZY)
   private List<Comment> comments;
   ```

4. **Connection Pool Configuration**
   ```properties
   # HikariCP configuration (Spring Boot default)
   spring.datasource.hikari.maximum-pool-size=10
   spring.datasource.hikari.minimum-idle=5
   spring.datasource.hikari.connection-timeout=30000
   spring.datasource.hikari.idle-timeout=600000
   spring.datasource.hikari.max-lifetime=1800000

   # Monitor connection pool usage
   spring.datasource.hikari.leak-detection-threshold=60000
   ```

## Phase 5: Memory Management Review

1. **Memory Leak Detection**
   ```bash
   # Take heap dumps before and after operations
   jmap -dump:format=b,file=heap1.bin <pid>
   # ... run application ...
   jmap -dump:format=b,file=heap2.bin <pid>

   # Compare heaps with Eclipse MAT
   # Look for:
   # - Growing collections
   # - ThreadLocal leaks
   # - Event listener leaks
   # - Cache without eviction
   # - Static field references
   ```

2. **Common Memory Leaks**
   ```java
   // 1. Static collections
   public class Cache {
       private static Map<String, Object> cache = new HashMap<>();  // Never cleared!

       public static void put(String key, Object value) {
           cache.put(key, value);
       }
   }
   // FIX: Use WeakHashMap or implement eviction

   // 2. ThreadLocal not removed
   private static ThreadLocal<Connection> threadLocal = new ThreadLocal<>();

   public void doWork() {
       Connection conn = getConnection();
       threadLocal.set(conn);
       // ... work ...
       // Missing: threadLocal.remove();
   }

   // 3. Listeners not unregistered
   eventBus.register(listener);
   // Missing: eventBus.unregister(listener);

   // 4. Unclosed resources
   InputStream is = new FileInputStream(file);
   // ... use stream ...
   // Missing: is.close();
   // FIX: Use try-with-resources
   ```

3. **Garbage Collection Analysis**
   ```bash
   # GC logging
   java -Xlog:gc*:file=gc.log:time,level,tags YourApp

   # Analyze GC with GCViewer or GCEasy.io

   # Key metrics to review:
   # - GC frequency
   # - GC pause times (target: <200ms)
   # - Heap usage after GC
   # - Old generation growth rate
   # - Memory leak indicators
   ```

4. **Object Pooling**
   ```java
   // Consider pooling for expensive objects:

   // 1. Thread pools (ExecutorService)
   ExecutorService executor = Executors.newFixedThreadPool(10);

   // 2. Database connection pools (HikariCP, Tomcat pool)

   // 3. Object pools for expensive creation
   GenericObjectPool<ExpensiveObject> pool = new GenericObjectPool<>(factory);
   ExpensiveObject obj = pool.borrowObject();
   try {
       // use object
   } finally {
       pool.returnObject(obj);
   }
   ```

## Phase 6: Concurrency Optimization

1. **Thread Pool Configuration**
   ```java
   // Spring async configuration
   @Configuration
   @EnableAsync
   public class AsyncConfig {
       @Bean(name = "taskExecutor")
       public Executor taskExecutor() {
           ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
           executor.setCorePoolSize(10);  // Base threads
           executor.setMaxPoolSize(20);   // Max threads
           executor.setQueueCapacity(100); // Queue size
           executor.setThreadNamePrefix("async-");
           executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
           executor.initialize();
           return executor;
       }
   }

   // Monitor thread pool metrics
   @Bean
   public ThreadPoolTaskExecutor monitoredExecutor() {
       ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
       // ... configuration ...
       executor.setTaskDecorator(runnable -> {
           // Add monitoring/logging
           return runnable;
       });
       return executor;
   }
   ```

2. **Synchronization Optimization**
   ```java
   // BAD: Excessive synchronization
   public synchronized void processItem(Item item) {
       // Long-running operation
       expensiveComputation();
       list.add(item);
   }

   // GOOD: Minimize synchronized block
   public void processItem(Item item) {
       expensiveComputation();  // Outside synchronized
       synchronized(this) {
           list.add(item);  // Only critical section
       }
   }

   // BETTER: Use concurrent collections
   private final ConcurrentMap<String, Value> map = new ConcurrentHashMap<>();
   // No explicit synchronization needed

   // BAD: Synchronized collection wrappers
   Map<String, Value> map = Collections.synchronizedMap(new HashMap<>());
   // GOOD: Use ConcurrentHashMap
   Map<String, Value> map = new ConcurrentHashMap<>();
   ```

3. **Lock Contention Analysis**
   - Identify methods with high lock contention
   - Review synchronized block scope
   - Consider read-write locks (ReentrantReadWriteLock)
   - Evaluate lock-free alternatives (Atomic classes)
   - Check for deadlock conditions

4. **CompletableFuture Optimization**
   ```java
   // BAD: Blocking on CompletableFuture
   CompletableFuture<Result> future = async Operation();
   Result result = future.get();  // Blocks thread!

   // GOOD: Chain async operations
   asyncOperation1()
       .thenComposeAsync(result1 -> asyncOperation2(result1))
       .thenAcceptAsync(result2 -> processResult(result2));

   // Parallel execution
   CompletableFuture<Result1> future1 = asyncOp1();
   CompletableFuture<Result2> future2 = asyncOp2();
   CompletableFuture<Result3> future3 = asyncOp3();

   CompletableFuture.allOf(future1, future2, future3)
       .thenApply(v -> combineResults(
           future1.join(), future2.join(), future3.join()
       ));
   ```

## Phase 7: Spring Boot Performance (if applicable)

1. **Application Startup Optimization**
   ```java
   // 1. Lazy initialization (Spring Boot 2.2+)
   spring.main.lazy-initialization=true

   // 2. Component scanning optimization
   @SpringBootApplication(scanBasePackages = "com.example.specific")

   // 3. Exclude auto-configurations not needed
   @SpringBootApplication(exclude = {
       DataSourceAutoConfiguration.class,
       RedisAutoConfiguration.class
   })

   // 4. Use @Lazy for expensive beans
   @Bean
   @Lazy
   public ExpensiveService expensiveService() {
       return new ExpensiveService();
   }
   ```

2. **Caching Strategy**
   ```java
   // Enable caching
   @EnableCaching
   @Configuration
   public class CacheConfig {
       @Bean
       public CacheManager cacheManager() {
           CaffeineCacheManager cacheManager = new CaffeineCacheManager();
           cacheManager.setCaffeine(Caffeine.newBuilder()
               .maximumSize(1000)
               .expireAfterWrite(10, TimeUnit.MINUTES)
               .recordStats());
           return cacheManager;
       }
   }

   // Use caching appropriately
   @Cacheable(value = "users", key = "#id")
   public User getUserById(Long id) {
       return userRepository.findById(id).orElse(null);
   }

   @CacheEvict(value = "users", key = "#user.id")
   public void updateUser(User user) {
       userRepository.save(user);
   }
   ```

3. **REST API Performance**
   ```java
   // 1. Use DTOs instead of entities
   // BAD: Exposing entities
   @GetMapping("/users/{id}")
   public User getUser(@PathVariable Long id) {
       return userService.findById(id);  // May trigger lazy loading
   }

   // GOOD: Use DTOs
   @GetMapping("/users/{id}")
   public UserDto getUser(@PathVariable Long id) {
       return userService.findByIdAsDto(id);
   }

   // 2. Pagination for collections
   @GetMapping("/users")
   public Page<UserDto> getUsers(Pageable pageable) {
       return userService.findAll(pageable);
   }

   // 3. Compression
   server.compression.enabled=true
   server.compression.mime-types=application/json,application/xml,text/html,text/xml,text/plain

   // 4. HTTP/2 support
   server.http2.enabled=true
   ```

## Phase 8: Java-Specific Optimizations

1. **JVM Tuning**
   ```bash
   # Heap size configuration
   java -Xms2g -Xmx4g  # Initial and maximum heap

   # GC selection
   java -XX:+UseG1GC  # G1 GC (good default)
   java -XX:+UseZGC   # ZGC (low latency, Java 11+)

   # GC tuning (G1GC example)
   java -XX:MaxGCPauseMillis=200 \
        -XX:InitiatingHeapOccupancyPercent=45 \
        -XX:G1ReservePercent=10

   # JIT compiler tuning
   java -XX:+TieredCompilation \
        -XX:TieredStopAtLevel=1  # For startup-sensitive apps

   # Enable class data sharing (faster startup)
   java -Xshare:on
   ```

2. **Primitive vs Objects**
   ```java
   // BAD: Unnecessary boxing
   List<Integer> numbers = new ArrayList<>();  // Each int boxed
   for (int i = 0; i < 1000; i++) {
       numbers.add(i);  // Boxing overhead
   }

   // GOOD: Use primitive arrays for performance
   int[] numbers = new int[1000];
   for (int i = 0; i < 1000; i++) {
       numbers[i] = i;
   }

   // GOOD: Use primitive collections (Eclipse Collections, Trove)
   IntArrayList numbers = new IntArrayList();
   ```

3. **Method Inlining and JIT**
   - Keep hot methods small (<35 bytecode instructions)
   - Avoid megamorphic call sites
   - Use final for classes/methods when appropriate
   - Minimize exception creation in hot paths

## Output Format

Please provide a comprehensive performance report with the following structure:

### Executive Summary

- **Overall Performance**: [Excellent/Good/Fair/Poor]

- **Critical Bottlenecks**: [count and brief description]

- **Performance Impact**: [High/Medium/Low user-facing impact]

- **Optimization Potential**: [percentage improvement possible]

- **Recommended Investment**: [estimated hours for major improvements]

### Performance Profile Overview
**Top 10 CPU-Consuming Methods**:
| Method | Class | CPU Time | % Total | Calls | Time/Call | Category |
|--------|-------|----------|---------|-------|-----------|----------|
| [method] | [class] | [ms] | [%] | [count] | [ms] | [CPU/I/O/DB] |

**Top 10 Memory-Consuming Operations**:
| Operation | Class | Retained Size | % Heap | Description |
|-----------|-------|---------------|--------|-------------|
| [operation] | [class] | [MB] | [%] | [details] |

### Critical Performance Issues (Priority 1)
| Issue | Location | Impact | Current | Target | Optimization |
|-------|----------|--------|---------|--------|--------------|
| [description] | [class:method] | [High] | [metric] | [goal] | [strategy] |

### Memory Analysis

- **Heap Usage**: [current/max MB]

- **Memory Leaks Detected**: [Yes/No - locations if yes]

- **Old Generation Growth**: [MB/hour]

- **GC Overhead**: [% of execution time]

- **Average GC Pause**: [ms]

- **Longest GC Pause**: [ms]

**GC Analysis**:
| GC Type | Frequency | Avg Pause | Max Pause | Throughput |
|---------|-----------|-----------|-----------|------------|
| Young | [/min] | [ms] | [ms] | [%] |
| Old | [/hour] | [ms] | [ms] | [%] |

### Algorithm Inefficiencies
**Inefficient Loops and Collections**:
| Method | Issue | Current Complexity | Optimized Approach |
|--------|-------|-------------------|-------------------|
| [method] | [description] | [O(n²)] | [suggested improvement] |

**String Operation Issues**:
| Location | Issue | Impact | Fix |
|----------|-------|--------|-----|
| [class:method] | [concatenation in loop] | [High] | [use StringBuilder] |

### Database Performance
**Slow Queries** (>100ms):
| Query | Execution Time | Frequency | Issue | Optimization |
|-------|----------------|-----------|-------|--------------|
| [query] | [ms] | [calls/sec] | [N+1/missing fetch/etc] | [solution] |

**N+1 Query Problems**:
| Entity | Location | Queries Generated | Fix |
|--------|----------|-------------------|-----|
| [entity] | [class:method] | [N+1 queries] | [JOIN FETCH / Entity Graph] |

**Connection Pool**:

- Pool Size: [current]

- Active Connections: [average]

- Wait Time: [average ms]

- Recommendation: [adjustment if needed]

### Concurrency Analysis

- **Thread Pool Configuration**: [cores/max/queue]

- **Thread Utilization**: [average %]

- **Lock Contention**: [hot spots identified]

- **Deadlock Potential**: [Yes/No - details]

**Synchronization Issues**:
| Method | Lock Time | Contention | Recommendation |
|--------|-----------|------------|----------------|
| [method] | [ms] | [High/Med/Low] | [reduce scope/use concurrent collections] |

### Spring Boot Performance** (if applicable)

- **Startup Time**: [seconds]

- **Auto-configuration**: [count of configurations]

- **Bean Creation Time**: [slowest beans]

- **Cache Hit Rate**: [percentage]

### JVM Tuning Recommendations

- **Current Heap**: [Xms/Xmx]

- **Recommended Heap**: [Xms/Xmx]

- **GC Algorithm**: [current/recommended]

- **GC Tuning**: [specific parameters]

### Optimization Recommendations

**Quick Wins** (< 1 day effort, high impact):
1. **[Optimization]**
   - **Location**: [class:method]
   - **Current**: [metric]
   - **Expected Improvement**: [metric/percentage]
   - **Implementation**: [specific steps with code]

**Medium-term** (1-3 days effort):
[List of optimizations requiring moderate refactoring]

**Strategic** (> 3 days, architectural changes):
[List of major performance initiatives]

### Load Testing Recommendations
```bash
# JMeter test plan
# - Normal load: X requests/sec for Y minutes
# - Peak load: X*3 requests/sec for Y minutes
# - Stress test: Gradually increase to failure point
# - Soak test: Normal load for 24 hours

# Gatling test (Scala-based)
# Apache Bench for simple REST API testing
ab -n 10000 -c 100 http://localhost:8080/api/endpoint
```

### Monitoring Recommendations
```properties
# Enable Spring Boot Actuator
management.endpoints.web.exposure.include=health,metrics,prometheus
management.metrics.export.prometheus.enabled=true

# Micrometer metrics
management.metrics.enable.jvm=true
management.metrics.enable.process=true
management.metrics.enable.system=true

# Custom application metrics
@Timed(value = "api.users.get", description = "Time to get user")
public User getUser(Long id) { }
```

### Next Steps

- [ ] Implement quick win optimizations

- [ ] Fix identified memory leaks

- [ ] Optimize database queries (N+1 problems)

- [ ] Configure appropriate GC for workload

- [ ] Set up performance monitoring (Prometheus, Grafana)

- [ ] Establish performance benchmarking suite (JMH)

- [ ] Configure load testing in CI/CD

- [ ] Plan performance review sprint

- [ ] Document performance SLAs/targets

## Notes

- Profile in production-like environment

- Focus on user-facing performance first

- Measure before and after optimization

- Use JMH (Java Microbenchmark Harness) for micro-benchmarks

- Monitor GC behavior - it's critical for Java performance

- Consider reactive programming (Spring WebFlux) for I/O-bound apps

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/performance_review/analysis_scripts
mkdir -p ${OUTPUT_DIR}/performance_review/supporting_data
```

**Save files as follows**:

- Main report → `review/performance_review/performance_review_report.md`

- Findings data → `review/performance_review/performance_review_findings.json`

- Analysis scripts → `review/performance_review/analysis_scripts/`

- Supporting data → `review/performance_review/supporting_data/`
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
