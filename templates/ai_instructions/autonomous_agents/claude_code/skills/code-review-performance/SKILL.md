---
name: code-review-performance
description: Systematically identify performance bottlenecks, inefficient algorithms, and resource usage issues - analyze complexity, database queries, memory usage, and I/O operations
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language
category: Code Review
tags: [code-review, performance, optimization, workflow, phase-4]
priority: HIGH
based_on: AI Templates Code Review Workflow, Anthropic Claude Code Best Practices 2025
---

# Code Review Performance Analysis

Systematically identify performance bottlenecks, inefficient algorithms, and resource usage issues that impact application speed, scalability, and user experience. This skill is **Phase 4** of the complete code review workflow, examining computational complexity, I/O operations, memory usage, and providing data-driven optimization recommendations.

## When to Use This Skill

Use this skill as **Phase 4** after completing context, quality, and security reviews:

- ✅ After [Phase 1: Context](../code-review-context-analysis/SKILL.md), [Phase 2: Quality](../code-review-quality/SKILL.md), and [Phase 3: Security](../code-review-security/SKILL.md) complete
- ✅ Application experiencing slow response times
- ✅ High resource consumption (CPU, memory, disk)
- ✅ Scalability issues as user load increases
- ✅ Database query performance problems
- ✅ Pre-production performance validation
- ✅ Capacity planning and optimization
- ✅ Cost reduction initiatives (cloud resources)

**This skill is essential when**:
- You need to identify performance bottlenecks
- You're planning optimization initiatives
- You want to improve application scalability
- You're reducing infrastructure costs
- You need to meet performance SLAs

## What This Skill Does

This skill implements **Phase 4: Performance Review** of the six-phase code review workflow:

### Complete Workflow
- Phase 1: [Context Analysis](../code-review-context-analysis/SKILL.md) - Project understanding
- Phase 2: [Quality Review](../code-review-quality/SKILL.md) - Code maintainability
- Phase 3: [Security Review](../code-review-security/SKILL.md) - Vulnerability identification
- **Phase 4: Performance Review (This Skill)** - Bottleneck analysis
- Phase 5: [Testing Review](../code-review-testing/SKILL.md) - Test coverage evaluation
- Phase 6: [Final Report](../code-review-final-report/SKILL.md) - Consolidated findings

## Why Performance Review Matters

**Without Performance Review**:
```
Application: *runs without profiling*
Users: *experience slow response times*
Infrastructure: *over-provisioned to compensate*
Result:
- ❌ Poor user experience and satisfaction
- ❌ High infrastructure costs
- ❌ Cannot scale to handle growth
- ❌ Inefficient resource utilization
- ❌ Competitive disadvantage
- ❌ Lost revenue from slow performance
```

**With Performance Review**:
```
Application: *optimized based on profiling data*
Users: *experience fast, responsive application*
Infrastructure: *right-sized for actual needs*
Result:
- ✅ Excellent user experience
- ✅ Reduced infrastructure costs
- ✅ Scales efficiently with growth
- ✅ Optimal resource utilization
- ✅ Competitive advantage
- ✅ Increased revenue from better performance
```

## Benefits of Performance Review

### User Experience
- **Fast Response**: Users get results quickly
- **Smooth Interactions**: No lag or delays
- **Reliability**: Consistent performance under load
- **Scalability**: Maintains performance as users grow

### Cost Optimization
- **Resource Efficiency**: Reduce CPU, memory, storage usage
- **Infrastructure Savings**: Right-size cloud resources
- **Bandwidth Reduction**: Optimize network usage
- **Database Costs**: Reduce query execution time

### Business Impact
- **User Retention**: Fast apps keep users engaged
- **Conversion Rates**: Performance impacts revenue
- **Competitive Edge**: Faster than competitors
- **Capacity Planning**: Understand growth limits

## Prerequisites

### Required
- Completion of [Phase 1: Context](../code-review-context-analysis/SKILL.md), [Phase 2: Quality](../code-review-quality/SKILL.md), and [Phase 3: Security](../code-review-security/SKILL.md)
- Source code access
- Profiling tools installed
- Representative test data
- Performance testing environment

### Recommended
- Production performance baselines
- Load testing tools
- Application Performance Monitoring (APM) access
- Database query logs
- Historical performance data

### Knowledge
- Algorithm complexity (Big O notation)
- Profiling and benchmarking techniques
- Database optimization
- Caching strategies
- Concurrency patterns

## Instructions

### Step 1: Performance Profiling Setup

**Install and configure profiling tools for your language:**

1. **Python CPU Profiling**

   ```bash
   # Install profiling tools
   pip install cProfile py-spy pyinstrument memory_profiler

   # Profile with cProfile (standard library)
   python -m cProfile -o profile.stats main.py

   # Analyze results
   python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"

   # Or use py-spy for production profiling (no code changes needed)
   py-spy record -o profile.svg -- python main.py

   # Interactive profiling with pyinstrument
   pyinstrument main.py
   ```

2. **JavaScript/Node.js Profiling**

   ```bash
   # Built-in Node.js profiler
   node --prof app.js

   # Process profiling output
   node --prof-process isolate-0xnnnnnnnnnnnn-v8.log > processed.txt

   # Chrome DevTools profiling
   node --inspect app.js
   # Open chrome://inspect

   # Clinic.js suite
   npm install -g clinic
   clinic doctor -- node app.js
   clinic flame -- node app.js
   clinic bubbleprof -- node app.js
   ```

3. **Java Profiling**

   ```bash
   # JProfiler or YourKit (commercial)
   # Or use built-in tools

   # VisualVM (free)
   jvisualvm

   # Java Flight Recorder
   java -XX:StartFlightRecording=duration=60s,filename=recording.jfr -jar app.jar

   # Async-profiler
   ./profiler.sh -d 60 -f profile.html <PID>
   ```

4. **Go Profiling**

   ```go
   // Add profiling to code
   import _ "net/http/pprof"

   go func() {
       log.Println(http.ListenAndServe("localhost:6060", nil))
   }()

   // Then profile remotely
   go tool pprof http://localhost:6060/debug/pprof/profile
   go tool pprof http://localhost:6060/debug/pprof/heap
   ```

   ```bash
   # Command-line profiling
   go test -cpuprofile=cpu.prof -memprofile=mem.prof -bench=.
   go tool pprof cpu.prof
   ```

5. **C/C++ Profiling**

   ```bash
   # Valgrind for memory profiling
   valgrind --tool=callgrind ./program
   kcachegrind callgrind.out.*

   # gprof for CPU profiling
   gcc -pg program.c -o program
   ./program
   gprof program gmon.out > analysis.txt

   # perf (Linux)
   perf record -g ./program
   perf report
   ```

6. **C# Profiling**

   ```bash
   # dotTrace or PerfView
   # BenchmarkDotNet for micro-benchmarking

   dotnet add package BenchmarkDotNet
   # Add benchmarks and run
   dotnet run -c Release
   ```

### Step 2: Identify Performance Bottlenecks

**Analyze profiling results to find hot paths:**

1. **CPU Hotspots**

   Look for:
   - Functions consuming >5% of total CPU time
   - Functions called excessively (thousands of times)
   - Nested loops with high iteration counts
   - Recursive functions with poor base cases
   - Inefficient algorithms (O(n²) or worse)

2. **Memory Analysis**

   **Python Example**:
   ```python
   from memory_profiler import profile

   @profile
   def analyze_data(data):
       # This decorator will show line-by-line memory usage
       results = []
       for item in data:
           processed = expensive_operation(item)
           results.append(processed)
       return results

   # Run with: python -m memory_profiler script.py
   ```

   Look for:
   - Large object allocations
   - Memory growth over time (potential leaks)
   - Unnecessary data copies
   - Large collections kept in memory

3. **I/O Bottlenecks**

   Monitor:
   - File read/write operations
   - Network calls and latency
   - Database queries and execution time
   - API calls to external services

### Step 3: Algorithm Efficiency Review

**Evaluate time and space complexity:**

1. **Common Performance Anti-Patterns**

   **Python**:
   ```python
   # BAD: O(n²) - repeated string concatenation
   result = ""
   for word in words:
       result += word  # Creates new string each time
   # GOOD: O(n)
   result = "".join(words)

   # BAD: O(n²) - list concatenation in loop
   result = []
   for item in items:
       result = result + [item]  # Creates new list each time
   # GOOD: O(n)
   result = []
   for item in items:
       result.append(item)

   # BAD: O(n²) - linear search in loop
   for item in list1:
       if item in list2:  # O(n) search for each item
           process(item)
   # GOOD: O(n)
   set2 = set(list2)  # O(n) to create set
   for item in list1:
       if item in set2:  # O(1) lookup
           process(item)

   # BAD: O(n) - unnecessary recalculation
   for i in range(len(data)):
       result = expensive_calculation(constant_param)  # Same result every time!
       process(data[i], result)
   # GOOD: O(1) for calculation
   result = expensive_calculation(constant_param)
   for i in range(len(data)):
       process(data[i], result)
   ```

   **JavaScript**:
   ```javascript
   // BAD: O(n²) - nested loops without optimization
   for (let i = 0; i < arr1.length; i++) {
       for (let j = 0; j < arr2.length; j++) {
           if (arr1[i] === arr2[j]) {
               matches.push(arr1[i]);
           }
       }
   }
   // GOOD: O(n) using Set
   const set2 = new Set(arr2);
   const matches = arr1.filter(item => set2.has(item));

   // BAD: Inefficient array operations
   let result = [];
   for (let i = 0; i < 1000000; i++) {
       result.push(i);
       result = result.filter(x => x > -1);  // Filters entire array each iteration!
   }
   // GOOD: Single operation
   let result = [];
   for (let i = 0; i < 1000000; i++) {
       result.push(i);
   }
   ```

   **Java**:
   ```java
   // BAD: O(n²) - String concatenation in loop
   String result = "";
   for (String word : words) {
       result += word;  // String immutable, creates new object each time
   }
   // GOOD: O(n) - StringBuilder
   StringBuilder result = new StringBuilder();
   for (String word : words) {
       result.append(word);
   }

   // BAD: Wrong collection type for use case
   List<Integer> numbers = new ArrayList<>();
   for (int i = 0; i < 10000; i++) {
       if (numbers.contains(i)) {  // O(n) search in ArrayList
           process(i);
       }
   }
   // GOOD: Use HashSet for O(1) lookups
   Set<Integer> numbers = new HashSet<>();
   for (int i = 0; i < 10000; i++) {
       if (numbers.contains(i)) {  // O(1) search in HashSet
           process(i);
       }
   }
   ```

   **Go**:
   ```go
   // BAD: Unnecessary allocations in loop
   for i := 0; i < len(data); i++ {
       slice := make([]int, 100)  // Allocates new slice each iteration
       // use slice
   }
   // GOOD: Reuse slice
   slice := make([]int, 100)
   for i := 0; i < len(data); i++ {
       // reuse slice
   }

   // BAD: String concatenation in loop
   var result string
   for _, word := range words {
       result += word  // Strings immutable in Go
   }
   // GOOD: strings.Builder
   var builder strings.Builder
   for _, word := range words {
       builder.WriteString(word)
   }
   ```

   **C/C++**:
   ```cpp
   // BAD: Inefficient memory allocation
   for (int i = 0; i < 1000000; i++) {
       int* data = new int[100];  // Allocate every iteration
       // use data
       delete[] data;
   }
   // GOOD: Allocate once
   int* data = new int[100];
   for (int i = 0; i < 1000000; i++) {
       // reuse data
   }
   delete[] data;

   // BAD: Unnecessary copies
   std::vector<LargeObject> process(std::vector<LargeObject> input) {  // Copy
       // process
       return result;  // Another copy
   }
   // GOOD: Move semantics
   std::vector<LargeObject> process(std::vector<LargeObject>&& input) {  // Move
       // process
       return result;  // Move
   }
   ```

   **C#**:
   ```csharp
   // BAD: LINQ in tight loop
   for (int i = 0; i < 1000000; i++) {
       var result = list.Where(x => x > threshold).ToList();  // Creates new list each time
   }
   // GOOD: Filter once before loop if possible
   var filtered = list.Where(x => x > threshold).ToList();
   for (int i = 0; i < 1000000; i++) {
       // use filtered
   }

   // BAD: Boxing in loop
   ArrayList list = new ArrayList();
   for (int i = 0; i < 100000; i++) {
       list.Add(i);  // Boxing int to object each time
   }
   // GOOD: Generic collection
   List<int> list = new List<int>();
   for (int i = 0; i < 100000; i++) {
       list.Add(i);  // No boxing
   }
   ```

2. **Data Structure Optimization**

   Choose appropriate data structures:
   - **Lists**: Sequential access, ordered
   - **Sets**: Fast membership testing (O(1))
   - **Dictionaries/Maps**: Fast key-value lookup (O(1))
   - **Queues**: FIFO processing
   - **Priority Queues**: Ordered processing
   - **Trees**: Hierarchical data, range queries

### Step 4: Database Performance Analysis

**Identify and optimize slow database operations:**

1. **Query Profiling**

   **Python (SQLAlchemy)**:
   ```python
   # Enable SQL logging
   import logging
   logging.basicConfig()
   logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

   # Or use flask-sqlalchemy debugging
   app.config['SQLALCHEMY_ECHO'] = True

   # Measure query time
   import time
   start = time.time()
   results = User.query.filter_by(status='active').all()
   print(f"Query took {time.time() - start:.3f}s")
   ```

   **JavaScript (Node.js)**:
   ```javascript
   // Log queries with timing
   const { performance } = require('perf_hooks');

   const start = performance.now();
   const results = await User.find({ status: 'active' });
   const duration = performance.now() - start;
   console.log(`Query took ${duration.toFixed(3)}ms`);
   ```

2. **N+1 Query Detection**

   **Python Example**:
   ```python
   # BAD: N+1 queries
   users = User.query.all()  # 1 query
   for user in users:
       orders = user.orders.all()  # N queries (one per user)
       process(orders)

   # GOOD: Eager loading
   users = User.query.options(joinedload(User.orders)).all()  # 1 query with JOIN
   for user in users:
       orders = user.orders  # No additional query
       process(orders)
   ```

   **JavaScript (Sequelize)**:
   ```javascript
   // BAD: N+1 queries
   const users = await User.findAll();  // 1 query
   for (const user of users) {
       const orders = await user.getOrders();  // N queries
   }

   // GOOD: Eager loading
   const users = await User.findAll({
       include: [{ model: Order }]  // 1 query with JOIN
   });
   ```

   **Java (JPA)**:
   ```java
   // BAD: N+1 queries
   List<User> users = entityManager
       .createQuery("SELECT u FROM User u", User.class)
       .getResultList();  // 1 query
   for (User user : users) {
       List<Order> orders = user.getOrders();  // N queries (lazy loading)
   }

   // GOOD: Eager loading with JOIN FETCH
   List<User> users = entityManager
       .createQuery("SELECT u FROM User u JOIN FETCH u.orders", User.class)
       .getResultList();  // 1 query
   ```

3. **Missing Index Detection**

   **Identify slow queries**:
   ```sql
   -- PostgreSQL: Find slow queries
   SELECT query, mean_exec_time, calls
   FROM pg_stat_statements
   ORDER BY mean_exec_time DESC
   LIMIT 10;

   -- MySQL: Enable slow query log
   SET GLOBAL slow_query_log = 'ON';
   SET GLOBAL long_query_time = 1;  -- Log queries > 1 second

   -- Check for missing indexes
   EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
   ```

   **Add appropriate indexes**:
   ```sql
   -- Create index on frequently queried column
   CREATE INDEX idx_users_email ON users(email);

   -- Composite index for multiple columns
   CREATE INDEX idx_users_status_created ON users(status, created_at);

   -- Partial index for common filter
   CREATE INDEX idx_users_active ON users(email) WHERE status = 'active';
   ```

4. **Query Optimization**

   **Python (SQLAlchemy)**:
   ```python
   # BAD: Loading all columns when only need few
   users = User.query.all()  # SELECT * FROM users
   names = [u.name for u in users]

   # GOOD: Select only needed columns
   users = db.session.query(User.name).all()  # SELECT name FROM users

   # BAD: Loading full objects for count
   count = len(User.query.all())  # SELECT * then count in Python

   # GOOD: Database-level count
   count = User.query.count()  # SELECT COUNT(*) FROM users
   ```

### Step 5: Memory Usage Optimization

**Identify and fix memory issues:**

1. **Memory Leak Detection**

   **Python**:
   ```python
   import tracemalloc

   tracemalloc.start()

   # Code to profile
   process_large_dataset()

   snapshot = tracemalloc.take_snapshot()
   top_stats = snapshot.statistics('lineno')

   print("Top 10 memory allocations:")
   for stat in top_stats[:10]:
       print(stat)
   ```

   **JavaScript**:
   ```javascript
   // Use Chrome DevTools heap snapshots
   // Or node --inspect and chrome://inspect

   // Monitor memory usage
   const used = process.memoryUsage();
   console.log(`Heap used: ${(used.heapUsed / 1024 / 1024).toFixed(2)} MB`);
   ```

2. **Memory-Efficient Patterns**

   **Python**:
   ```python
   # BAD: Load entire file into memory
   with open('large_file.txt') as f:
       data = f.read()  # Could be gigabytes
       process(data)

   # GOOD: Process line by line
   with open('large_file.txt') as f:
       for line in f:  # Generator, one line at a time
           process(line)

   # BAD: List comprehension for large data
   results = [expensive_operation(x) for x in huge_list]  # All in memory

   # GOOD: Generator expression
   results = (expensive_operation(x) for x in huge_list)  # One at a time
   for result in results:
       use(result)
   ```

   **JavaScript**:
   ```javascript
   // BAD: Loading entire dataset
   const allRecords = await Record.find({});  // Could be millions
   const processed = allRecords.map(process);

   // GOOD: Stream processing
   const cursor = Record.find({}).cursor();
   for await (const record of cursor) {
       process(record);
   }
   ```

3. **Caching Strategy**

   **Python**:
   ```python
   from functools import lru_cache

   # Cache expensive calculations
   @lru_cache(maxsize=128)
   def expensive_calculation(param):
       # Complex computation
       return result

   # Redis for distributed caching
   import redis
   cache = redis.Redis()

   def get_user(user_id):
       cached = cache.get(f'user:{user_id}')
       if cached:
           return json.loads(cached)

       user = User.query.get(user_id)
       cache.setex(f'user:{user_id}', 3600, json.dumps(user.to_dict()))
       return user
   ```

### Step 6: I/O and Network Optimization

**Optimize file and network operations:**

1. **Asynchronous I/O**

   **Python (asyncio)**:
   ```python
   import asyncio
   import aiohttp

   # BAD: Sequential API calls
   def fetch_all_urls(urls):
       results = []
       for url in urls:
           response = requests.get(url)  # Wait for each
           results.append(response.json())
       return results

   # GOOD: Concurrent API calls
   async def fetch_all_urls(urls):
       async with aiohttp.ClientSession() as session:
           tasks = [fetch_url(session, url) for url in urls]
           return await asyncio.gather(*tasks)

   async def fetch_url(session, url):
       async with session.get(url) as response:
           return await response.json()
   ```

   **JavaScript (async/await)**:
   ```javascript
   // BAD: Sequential requests
   async function fetchAll(urls) {
       const results = [];
       for (const url of urls) {
           const response = await fetch(url);  // Wait for each
           results.push(await response.json());
       }
       return results;
   }

   // GOOD: Concurrent requests
   async function fetchAll(urls) {
       const promises = urls.map(url =>
           fetch(url).then(r => r.json())
       );
       return Promise.all(promises);
   }
   ```

2. **Connection Pooling**

   **Python**:
   ```python
   # Database connection pooling
   from sqlalchemy import create_engine
   engine = create_engine(
       'postgresql://user:pass@localhost/db',
       pool_size=20,
       max_overflow=0,
       pool_pre_ping=True
   )

   # HTTP connection pooling
   import requests
   session = requests.Session()
   adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20)
   session.mount('http://', adapter)
   session.mount('https://', adapter)
   ```

3. **Batching Operations**

   **Python**:
   ```python
   # BAD: Individual inserts
   for record in records:
       db.session.add(User(**record))
       db.session.commit()  # Commit each record

   # GOOD: Batch insert
   db.session.bulk_insert_mappings(User, records)
   db.session.commit()  # Single commit
   ```

### Step 7: Concurrency and Parallelism

**Leverage multiple cores and threads:**

1. **Python Multiprocessing**

   ```python
   from multiprocessing import Pool

   # CPU-bound task
   def process_item(item):
       # Expensive computation
       return result

   # BAD: Sequential processing
   results = [process_item(item) for item in items]

   # GOOD: Parallel processing
   with Pool(processes=8) as pool:
       results = pool.map(process_item, items)
   ```

2. **Go Concurrency**

   ```go
   // Goroutines for concurrent processing
   func processItems(items []Item) []Result {
       results := make([]Result, len(items))
       var wg sync.WaitGroup

       for i, item := range items {
           wg.Add(1)
           go func(i int, item Item) {
               defer wg.Done()
               results[i] = process(item)
           }(i, item)
       }

       wg.Wait()
       return results
   }
   ```

3. **Java Parallel Streams**

   ```java
   // Parallel processing with streams
   List<Result> results = items.parallelStream()
       .map(item -> processItem(item))
       .collect(Collectors.toList());
   ```

### Step 8: Generate Performance Report

**Compile findings into structured report:**

```markdown
# Performance Review Report

**Project**: [Name]
**Date**: [Date]
**Reviewer**: [Name]

## Executive Summary

- **Overall Performance Grade**: [A-F]
- **Critical Bottlenecks**: [Count]
- **Optimization Potential**: [%]
- **Estimated Improvement**: [X]x faster, [Y]% less memory

## Performance Metrics Baseline

### Response Time
- **Average**: [ms]
- **95th Percentile**: [ms]
- **99th Percentile**: [ms]
- **Maximum**: [ms]

### Resource Usage
- **CPU**: [%] average, [%] peak
- **Memory**: [MB] average, [MB] peak
- **Disk I/O**: [MB/s] read, [MB/s] write
- **Network**: [MB/s] in, [MB/s] out

### Throughput
- **Requests/second**: [count]
- **Transactions/second**: [count]
- **Concurrent Users**: [count]

## Critical Bottlenecks

### Bottleneck 1: [Description]
- **Location**: [file:line]
- **Impact**: [% of total time]
- **Current Performance**: [metrics]
- **Root Cause**: [explanation]
- **Recommended Fix**: [solution]
- **Expected Improvement**: [estimate]
- **Effort**: [hours/days]

### Bottleneck 2: [Description]
[Same structure]

## Algorithm Complexity Issues

### O(n²) Algorithms
| Function | Location | Current | Recommended | Improvement |
|----------|----------|---------|-------------|-------------|
| search_duplicates | utils.py:45 | O(n²) | O(n) with Set | 100x faster |

### Inefficient Data Structures
| Location | Current | Issue | Recommended | Benefit |
|----------|---------|-------|-------------|---------|
| cache.py:20 | List | O(n) search | Dict/Set | O(1) lookup |

## Database Performance

### Slow Queries (>100ms)
| Query | Time | Calls | Location | Issue | Fix |
|-------|------|-------|----------|-------|-----|
| get_user_orders | 450ms | 1000 | api.py:67 | N+1 | Eager load |

### Missing Indexes
| Table | Column(s) | Query Pattern | Priority |
|-------|-----------|---------------|----------|
| users | email | WHERE email = ? | High |

### Query Optimization Opportunities
- [List specific queries to optimize]

## Memory Analysis

### Memory Hotspots
| Function | Memory | % Total | Issue | Fix |
|----------|--------|---------|-------|-----|
| load_dataset | 2.5 GB | 45% | Loading all at once | Stream processing |

### Memory Leaks
- **Leak 1**: [Description and fix]
- **Leak 2**: [Description and fix]

### Caching Recommendations
- [Areas where caching would improve performance]

## I/O Performance

### File I/O Issues
- [Inefficient file operations]

### Network Performance
- **Sequential API Calls**: [Count] - Parallelize
- **Missing Connection Pooling**: [Location]
- **Large Payload Sizes**: [Location] - Compress

### Database Connection Issues
- [Connection pooling configuration]

## Concurrency Opportunities

### CPU-Bound Operations
- [Tasks that could benefit from parallelization]

### I/O-Bound Operations
- [Tasks that could benefit from async/await]

### Thread Safety Issues
- [Potential race conditions]

## Optimization Roadmap

### Quick Wins (Hours)
1. **Add Database Index on users.email**
   - **Impact**: 10x faster user lookups
   - **Effort**: 1 hour
   - **Risk**: Low

2. **Cache Expensive Calculation**
   - **Impact**: 50% reduction in response time
   - **Effort**: 2 hours
   - **Risk**: Low

### Short-term (Days)
1. **Fix N+1 Queries**
   - **Impact**: 5x faster API endpoints
   - **Effort**: 3 days
   - **Risk**: Medium

2. **Implement Connection Pooling**
   - **Impact**: 30% better throughput
   - **Effort**: 2 days
   - **Risk**: Low

### Medium-term (Weeks)
1. **Optimize Algorithm Complexity**
   - **Impact**: 100x improvement on large datasets
   - **Effort**: 2 weeks
   - **Risk**: Medium

2. **Implement Async Processing**
   - **Impact**: 3x better concurrent request handling
   - **Effort**: 2 weeks
   - **Risk**: High

### Long-term (Months)
1. **Architectural Refactoring**
   - **Impact**: Horizontal scalability
   - **Effort**: 2 months
   - **Risk**: High

## Performance Testing Recommendations

### Load Testing Scenarios
- [Scenarios to test under load]

### Benchmarking Targets
- [Performance goals to measure]

### Monitoring Requirements
- [Metrics to track in production]

## Cost Impact Analysis

### Current Costs
- **Infrastructure**: $[amount]/month
- **Database**: $[amount]/month
- **Bandwidth**: $[amount]/month

### Projected Savings (After Optimization)
- **Infrastructure**: $[amount]/month ([%] reduction)
- **Database**: $[amount]/month ([%] reduction)
- **Bandwidth**: $[amount]/month ([%] reduction)
- **Total Annual Savings**: $[amount]

## Next Steps

- [ ] Implement quick wins (high impact, low effort)
- [ ] Set up performance monitoring
- [ ] Create performance test suite
- [ ] Schedule short-term optimizations
- [ ] Plan medium-term architectural improvements
- [ ] Proceed to [Phase 5: Testing Review](../code-review-testing/SKILL.md)
```

## Success Criteria

- [ ] Performance profiling completed
- [ ] Bottlenecks identified and prioritized
- [ ] Algorithm complexity analyzed
- [ ] Database queries optimized
- [ ] Memory usage profiled
- [ ] I/O operations assessed
- [ ] Concurrency opportunities identified
- [ ] Optimization roadmap created
- [ ] Cost impact calculated
- [ ] Team ready for testing review

## Related Skills

### Code Review Workflow
1. [Phase 1: Context Analysis](../code-review-context-analysis/SKILL.md)
2. [Phase 2: Quality Review](../code-review-quality/SKILL.md)
3. [Phase 3: Security Review](../code-review-security/SKILL.md)
4. **Phase 4: Performance Review (This Skill)**
5. [Phase 5: Testing Review](../code-review-testing/SKILL.md)
6. [Phase 6: Final Report](../code-review-final-report/SKILL.md)

## Additional Resources

### Profiling Tools
- **Python**: cProfile, py-spy, pyinstrument, memory_profiler, line_profiler
- **JavaScript**: Node.js profiler, clinic.js, Chrome DevTools
- **Java**: JProfiler, YourKit, VisualVM, Java Flight Recorder
- **Go**: pprof, trace, benchstat
- **C/C++**: Valgrind, gprof, perf, Intel VTune
- **C#**: dotTrace, PerfView, BenchmarkDotNet

### Performance Best Practices
- [Google Web Vitals](https://web.dev/vitals/)
- [Database Performance Tuning](https://use-the-index-luke.com/)
- [High Performance Browser Networking](https://hpbn.co/)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: AI Templates Code Review Workflow, Anthropic Claude Code Best Practices 2025
**Template Source**: `code_review/performance_review/*.md`
