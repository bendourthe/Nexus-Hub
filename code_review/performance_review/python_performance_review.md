# Python Performance Review

## Objective
Systematically identify performance bottlenecks, inefficient algorithms, and resource usage issues. Provide data-driven optimization recommendations to improve application speed, scalability, and resource efficiency.

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
- [ ] CPU profiling completed (cProfile, py-spy)
- [ ] Memory profiling performed (memory_profiler, tracemalloc)
- [ ] I/O operations analyzed
- [ ] Hot paths and bottlenecks identified
- [ ] Function-level timing measurements captured

### Algorithm Efficiency
- [ ] Time complexity evaluated (O(n), O(n²), etc.)
- [ ] Space complexity assessed
- [ ] Inefficient loops identified (nested, redundant)
- [ ] Algorithmic improvements documented
- [ ] Data structure choices reviewed

### Database Performance
- [ ] Query execution times measured
- [ ] N+1 query problems identified
- [ ] Missing indexes detected
- [ ] Query optimization opportunities documented
- [ ] Connection pooling evaluated

### Memory Management
- [ ] Memory leaks detected
- [ ] Large object allocations identified
- [ ] Memory growth patterns analyzed
- [ ] Caching strategies reviewed
- [ ] Garbage collection behavior assessed

### I/O & Network
- [ ] File I/O operations profiled
- [ ] Network call latency measured
- [ ] Synchronous vs asynchronous patterns evaluated
- [ ] Batching opportunities identified
- [ ] Connection reuse assessed

### Concurrency & Parallelism
- [ ] Threading/multiprocessing opportunities identified
- [ ] Async/await usage evaluated
- [ ] GIL (Global Interpreter Lock) impact assessed
- [ ] Race conditions checked
- [ ] Resource contention identified

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Python Performance Review

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

Please perform a comprehensive performance review of this Python application following this protocol:

## Phase 1: Performance Profiling Setup

1. **CPU Profiling**
   ```python
   # Profile with cProfile
   python -m cProfile -o profile.stats main.py

   # Analyze results
   python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"

   # Or use py-spy for production profiling (no code changes)
   py-spy record -o profile.svg -- python main.py
   ```

2. **Memory Profiling**
   ```python
   # Line-by-line memory usage
   # Add @profile decorator to functions of interest
   from memory_profiler import profile

   @profile
   def my_function():
       # function code
       pass

   # Run with:
   python -m memory_profiler main.py

   # Or use tracemalloc (built-in, Python 3.4+)
   import tracemalloc
   tracemalloc.start()
   # ... code to profile ...
   snapshot = tracemalloc.take_snapshot()
   top_stats = snapshot.statistics('lineno')
   for stat in top_stats[:10]:
       print(stat)
   ```

3. **I/O Profiling**
   ```python
   # Monitor I/O operations
   # Use pyinstrument for async/I/O heavy code
   from pyinstrument import Profiler
   profiler = Profiler()
   profiler.start()
   # ... code to profile ...
   profiler.stop()
   profiler.print()
   ```

## Phase 2: Bottleneck Identification

1. **Analyze Profiling Results**
   - Identify functions consuming >5% of total time
   - Find functions called excessive times
   - Locate memory-intensive operations
   - Identify I/O bound operations

2. **Hot Path Analysis**
   - Map critical execution paths
   - Measure end-to-end latency
   - Identify slowest endpoints/operations
   - Document user-facing performance impacts

3. **Resource Usage Patterns**
   - CPU utilization during typical operations
   - Memory growth patterns over time
   - Network bandwidth usage
   - Disk I/O patterns

## Phase 3: Algorithm Efficiency Review

1. **Time Complexity Analysis**
   - Review loops and nested iterations
   - Identify O(n²) or worse algorithms
   - Check for redundant computations
   - Assess search and sort operations

2. **Common Performance Anti-Patterns**
   ```python
   # Inefficient patterns to search for:

   # 1. Growing list in loop (O(n) per append can be O(n²) total)
   result = []
   for item in large_list:
       result = result + [item]  # BAD: creates new list each time
   # Better: result.append(item)

   # 2. Repeated string concatenation (O(n²))
   text = ""
   for word in words:
       text += word  # BAD: strings are immutable
   # Better: "".join(words)

   # 3. Linear search in loop (O(n²))
   for item in list1:
       if item in list2:  # BAD: O(n) search
           # do something
   # Better: convert list2 to set for O(1) lookup

   # 4. Recalculating same value repeatedly
   for i in range(len(data)):
       result = expensive_calculation(param)  # BAD: if param doesn't change
       process(data[i], result)
   # Better: calculate once before loop

   # 5. Reading file multiple times
   for item in items:
       with open('config.txt') as f:  # BAD: reopening file
           config = f.read()
   # Better: read file once before loop

   # 6. Database queries in loop (N+1 problem)
   for user_id in user_ids:
       user = User.query.get(user_id)  # BAD: N queries
   # Better: User.query.filter(User.id.in_(user_ids)).all()
   ```

3. **Data Structure Optimization**
   - Evaluate list vs set vs dict usage
   - Check for appropriate container choices
   - Review sorting strategies
   - Assess caching data structures

## Phase 4: Database Performance Analysis

1. **Query Performance Testing**
   ```python
   # Enable SQL query logging
   import logging
   logging.basicConfig()
   logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

   # Or use flask-sqlalchemy query debugging
   app.config['SQLALCHEMY_ECHO'] = True
   ```

2. **N+1 Query Detection**
   ```python
   # Bad: N+1 queries
   posts = Post.query.all()  # 1 query
   for post in posts:
       author = post.author  # N queries (one per post)

   # Good: Eager loading
   posts = Post.query.options(joinedload(Post.author)).all()  # 1 or 2 queries
   ```

3. **Index Analysis**
   - Review query execution plans
   - Identify missing indexes on filtered/joined columns
   - Check for unused indexes
   - Assess index selectivity

4. **Query Optimization**
   - Simplify complex queries
   - Reduce data fetched (select specific columns)
   - Optimize JOIN operations
   - Evaluate pagination strategies

## Phase 5: Memory Management Review

1. **Memory Leak Detection**
   ```python
   # Check for common leak patterns:
   # - Growing global caches without eviction
   # - Event handlers not removed
   # - Circular references (usually handled by GC)
   # - Large objects in closures

   # Monitor memory growth
   import tracemalloc
   tracemalloc.start()

   # ... run application ...

   snapshot = tracemalloc.take_snapshot()
   top_stats = snapshot.statistics('lineno')
   print("[ Top 10 memory consuming lines ]")
   for stat in top_stats[:10]:
       print(stat)
   ```

2. **Large Object Analysis**
   - Identify large data structures in memory
   - Review object lifecycle and cleanup
   - Assess when objects can be released
   - Check for unnecessary data retention

3. **Caching Strategy Review**
   - Evaluate cache hit rates
   - Check for cache invalidation logic
   - Assess memory limits for caches
   - Review cache eviction policies

## Phase 6: I/O & Concurrency Optimization

1. **I/O Operation Analysis**
   ```python
   # Identify synchronous I/O bottlenecks
   # Look for patterns like:
   - Multiple sequential file reads
   - Synchronous API calls in loops
   - Blocking database calls
   - Lack of connection pooling
   ```

2. **Async Opportunities**
   ```python
   # Evaluate async/await usage
   # Good candidates for async:
   - Multiple independent API calls
   - I/O bound operations
   - Database queries (with async driver)
   - File operations

   # Example: Sequential vs Concurrent
   # Bad: Sequential (slow)
   result1 = fetch_api_1()
   result2 = fetch_api_2()
   result3 = fetch_api_3()

   # Good: Concurrent (fast)
   import asyncio
   results = await asyncio.gather(
       fetch_api_1(),
       fetch_api_2(),
       fetch_api_3()
   )
   ```

3. **Concurrency Review**
   - Assess threading vs multiprocessing suitability
   - Evaluate async/await implementation
   - Check for race conditions and locks
   - Review connection pool configurations

## Phase 7: Python-Specific Optimizations

1. **Built-in Performance Features**
   ```python
   # Check usage of:
   - List comprehensions vs loops
   - Generator expressions for large datasets
   - Built-in functions (sum, max, min vs manual loops)
   - collections module (deque, Counter, defaultdict)
   - functools.lru_cache for memoization
   ```

2. **Common Python Optimizations**
   ```python
   # Prefer:
   # 1. List comprehension
   squares = [x**2 for x in range(100)]
   # over:
   squares = []
   for x in range(100):
       squares.append(x**2)

   # 2. Generator for large data
   def process_large_file(filename):
       for line in open(filename):  # Generator
           yield process(line)
   # vs loading entire file into memory

   # 3. Using built-ins
   total = sum(values)
   # vs:
   total = 0
   for v in values:
       total += v

   # 4. Dictionary lookup
   value = lookup_dict.get(key, default)
   # vs:
   if key in lookup_dict:
       value = lookup_dict[key]
   else:
       value = default
   ```

## Output Format

Please provide a comprehensive performance report with the following structure:

### Executive Summary
- **Overall Performance**: [Excellent/Good/Fair/Poor]
- **Critical Bottlenecks**: [count and brief description]
- **Performance Impact**: [High/Medium/Low user-facing impact]
- **Optimization Potential**: [percentage improvement possible]
- **Recommended Investment**: [estimated hours for major improvements]

### Performance Profile Overview
**Top 10 Time-Consuming Functions**:
| Function | File | Time | % Total | Calls | Time/Call | Category |
|----------|------|------|---------|-------|-----------|----------|
| [name] | [path] | [seconds] | [%] | [count] | [ms] | [CPU/I/O/DB] |

**Top 10 Memory-Consuming Operations**:
| Operation | File:Line | Memory | % Total | Description |
|-----------|-----------|--------|---------|-------------|
| [desc] | [location] | [MB] | [%] | [details] |

### Critical Performance Issues (Priority 1)
| Issue | Location | Impact | Current | Target | Optimization |
|-------|----------|--------|---------|--------|--------------|
| [description] | [file:line] | [High] | [metric] | [goal] | [strategy] |

### High-Impact Optimizations (Priority 2)
[List of optimizations with significant performance gains]

### Algorithm Inefficiencies
**O(n²) or Worse Algorithms Detected**:
| Function | Location | Complexity | Current Performance | Optimized Approach |
|----------|----------|------------|---------------------|-------------------|
| [name] | [file:line] | [O(n²)] | [metric] | [suggested algorithm] |

### Database Performance
**Slow Queries** (>100ms):
| Query | Execution Time | Frequency | Issue | Optimization |
|-------|----------------|-----------|-------|--------------|
| [query] | [ms] | [calls/sec] | [N+1/missing index/etc] | [solution] |

**Missing Indexes**:
| Table | Column(s) | Query Pattern | Impact |
|-------|-----------|---------------|--------|
| [table] | [cols] | [WHERE/JOIN] | [High/Med/Low] |

### Memory Analysis
- **Peak Memory Usage**: [MB]
- **Memory Leaks Detected**: [Yes/No - locations if yes]
- **Large Objects**: [list of large allocations]
- **Cache Efficiency**: [hit rate %]

### I/O & Network Performance
- **File I/O Operations**: [count and total time]
- **Network Calls**: [count, total time, average latency]
- **Blocking Operations**: [count and locations]
- **Async Opportunities**: [list of candidates]

### Concurrency Assessment
- **Current Concurrency Model**: [threading/multiprocessing/async/none]
- **CPU Utilization**: [percentage during load]
- **GIL Impact**: [High/Medium/Low]
- **Parallelization Opportunities**: [specific candidates]

### Python-Specific Findings
- **Sub-optimal Patterns**: [list with alternatives]
- **Built-in Replacements**: [manual code that could use built-ins]
- **Generator Opportunities**: [large list operations]
- **Caching Candidates**: [expensive repeated computations]

### Optimization Recommendations

**Quick Wins** (< 1 day effort, high impact):
1. **[Optimization]**
   - **Location**: [file:line]
   - **Current**: [metric]
   - **Expected Improvement**: [metric/percentage]
   - **Implementation**: [specific steps]

**Medium-term** (1-3 days effort):
[List of optimizations requiring moderate refactoring]

**Strategic** (> 3 days, architectural changes):
[List of major performance initiatives]

### Load Testing Recommendations
```python
# Suggested load testing scenarios
1. Normal load: X requests/sec for Y minutes
2. Peak load: X*3 requests/sec for Y minutes
3. Stress test: Gradually increase to failure point
4. Soak test: Normal load for 24 hours

# Tools: locust, pytest-benchmark, ab (Apache Bench)
```

### Monitoring Recommendations
```python
# Implement performance monitoring
- Response time tracking (p50, p95, p99)
- Database query performance monitoring
- Memory usage alerts
- Error rate tracking
- Custom business metric tracking

# Tools: Prometheus, DataDog, New Relic, Sentry
```

### Benchmark Results
**Before Optimization**:
- [Operation]: [time/throughput]

**After Optimization** (projected):
- [Operation]: [time/throughput]

**Improvement**: [percentage] faster / [X]x throughput

### Next Steps
- [ ] Implement quick win optimizations
- [ ] Set up performance benchmarking suite
- [ ] Configure production performance monitoring
- [ ] Plan load testing before deployment
- [ ] Schedule performance review sprint
- [ ] Document performance SLAs/targets

## Notes
- Optimize based on profiling data, not assumptions
- Focus on user-facing performance improvements first
- Measure before and after optimization
- Consider scalability alongside raw performance
- Balance performance with code maintainability

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
