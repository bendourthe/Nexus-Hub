---
name: performance-review
description: Profile performance, detect bottlenecks, analyze resource usage, caching strategies, and boundary conditions. Use when addressing performance issues, optimizing hot paths, reducing resource consumption, or as Phase 4 of comprehensive code review.
summary_l0: "Detect performance bottlenecks, resource issues, and caching optimization opportunities"
overview_l1: "This skill identifies performance bottlenecks, caching issues, and optimization opportunities, serving as Phase 4 of the 6-phase code review methodology. Use it when identifying performance bottlenecks, optimizing critical code paths, reducing resource consumption, improving response times, addressing scalability concerns, profiling memory and CPU usage, or evaluating caching strategies. Key capabilities include hot path identification, algorithmic complexity analysis, memory allocation profiling, database query optimization, caching strategy evaluation, I/O bottleneck detection, resource leak identification, and scalability assessment. The expected output is a performance findings report with identified bottlenecks, profiling data, optimization recommendations with expected impact, and prioritized remediation steps. Trigger phrases: performance review, bottleneck, slow code, optimize, profiling, latency, throughput, memory usage, caching."
---

# Code Review - Performance Review

Identify performance bottlenecks, caching issues, and optimization opportunities. This skill is **Phase 4** of the 6-phase code review methodology.

## When to Use This Skill

Use this skill when you need to:

- Identify performance bottlenecks
- Optimize critical code paths
- Reduce resource consumption
- Improve response times
- Address scalability concerns
- Profile memory and CPU usage
- Evaluate caching strategies

**Trigger phrases**: "performance review", "bottleneck", "slow code", "optimize", "profiling", "latency", "throughput", "memory usage", "caching"

## What This Skill Does

### Performance Dimensions

| Dimension | Metrics |
|-----------|---------|
| **Time** | Response time, latency, throughput |
| **Memory** | Heap usage, allocations, leaks |
| **CPU** | Utilization, hot paths |
| **I/O** | Database queries, network calls |
| **Concurrency** | Threading, async efficiency |
| **Caching** | Hit rate, TTL, invalidation |

### Severity Classification

| Level | Alias | Description |
|-------|-------|-------------|
| **P0** | CRITICAL | Production outages, severe degradation |
| **P1** | HIGH | Significant performance impact |
| **P2** | MEDIUM | Notable inefficiency |
| **P3** | LOW | Minor optimization opportunity |

## Instructions

### Step 1: Profile Application

```bash
# Python
python -m cProfile -s cumtime script.py
py-spy record -o profile.svg -- python script.py

# JavaScript/Node.js
node --prof app.js
clinic doctor -- node app.js

# Java
java -XX:+FlightRecorder -XX:StartFlightRecording=duration=60s,filename=app.jfr App
```

### Step 2: Identify Hot Paths

1. **CPU Profiling**
   - Functions with highest cumulative time
   - Frequent function calls
   - Complex algorithms

2. **Memory Analysis**
   - Large object allocations
   - Memory leaks
   - Garbage collection pressure
   - Event listener leaks (registered but never removed)

3. **I/O Analysis**
   - N+1 query patterns
   - Unoptimized database queries
   - Unnecessary network calls

### Step 3: Common Anti-Patterns

Reference: `references/code-quality-checklist.md` (Performance & Caching section)

| Anti-Pattern | Issue | Solution |
|--------------|-------|----------|
| N+1 Queries | Loop database calls | Batch queries, joins |
| Large Payloads | Excessive data transfer | Pagination, field selection |
| No Caching | Repeated computations | Add caching layer |
| Sync I/O | Blocking operations | Async/await |
| String Concatenation | Memory allocation in loops | StringBuilder/join |
| Missing Memoization | Same pure function called repeatedly | Add memoization |
| Over-fetching | `SELECT *` when only 2 columns needed | Select specific columns |
| No Pagination | Loading entire tables | LIMIT/OFFSET or cursor pagination |

### Step 4: Caching Strategy Analysis

| Issue | Risk | Diagnostic |
|-------|------|-----------|
| **Missing cache** | Repeated expensive computations | "Is this expensive operation called more than once with the same inputs?" |
| **Cache without TTL** | Stale data served indefinitely | "How long is cached data valid?" |
| **No invalidation strategy** | Cache and database drift | "When the source data changes, how is the cache updated?" |
| **Key collisions** | Different data overwriting each other | "Could two different inputs produce the same cache key?" |
| **User data cached globally** | Data leaks between users | "Does the cache key include user/tenant identity?" |
| **Cache stampede** | All caches expire simultaneously | "What happens when the cache expires under load?" |

### Step 5: Boundary Conditions Affecting Performance

Reference: `references/code-quality-checklist.md` (Boundary Conditions section)

| Condition | Performance Impact |
|-----------|-------------------|
| Unbounded collections | Lists/maps growing without limit, OOM risk |
| Large file loading | Reading entire files into memory instead of streaming |
| String concatenation in loops | O(n^2) memory allocation |
| Empty collection edge cases | `.reduce()` without initial value, `.sort()` on empty arrays |

### Step 6: Diagnostic Questions

Apply these questions to each module under review:

1. "What is the most expensive operation in the critical path? Can it be cached, batched, or deferred?"
2. "Are there any N+1 query patterns? (Loop that issues a query per iteration)"
3. "Is there any unbounded data structure that grows with input size?"
4. "For cached data, what is the TTL and invalidation strategy?"

### Step 7: Document Findings

```markdown
## Performance Finding

**File**: [path/to/file.py:42]
**Severity**: P1 (HIGH)
**Impact**: 500ms added latency per request
**Category**: Database Query

### Issue
N+1 query pattern in user loading

### Current Code
```python
users = User.query.all()
for user in users:
    orders = Order.query.filter_by(user_id=user.id).all()
```

### Optimized Code
```python
users = User.query.options(
    joinedload(User.orders)
).all()
```

### Expected Improvement
- Latency: 500ms -> 50ms
- Database queries: N+1 -> 1
```

## Language-Specific Tools

### Python
- cProfile, py-spy, memory_profiler
- line_profiler, tracemalloc

### JavaScript
- Chrome DevTools, Node.js profiler
- clinic.js, 0x

### Java
- JFR, VisualVM, async-profiler
- JMH for benchmarks

### Go
- pprof, trace
- benchmarks

### C# / .NET
- dotTrace, dotMemory
- BenchmarkDotNet

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's fast enough on my machine" | A query that returns in 5ms against 100 local rows runs an N+1 pattern that becomes 2000 round-trips and seconds of latency against a production table; local timing hides the bottleneck this review exists to catch. |
| "We'll optimize when it becomes a problem" | An unbounded collection or missing-TTL cache does not degrade gradually; it works until a traffic spike causes an OOM crash or serves stale data, at which point the fix is an incident, not a review comment. |
| "Caching will fix the slow path, just add a cache" | A cache without an invalidation strategy or a tenant-scoped key creates a correctness bug (stale or cross-user data) that is far worse than the latency it removed; the caching-strategy table in this skill exists to prevent exactly that. |
| "The profiler shows this function is hot, so rewrite it" | Hot in cumulative time often means it calls a slow dependency (an N+1 query or sync I/O), not that its own logic is slow; optimizing the wrong layer wastes effort and leaves the real bottleneck in place. |

## Verification

- [ ] Application profiled and profile output saved (cProfile / clinic / JFR / pprof)
- [ ] Hot paths identified from cumulative time, not assumed
- [ ] Database queries analyzed for N+1, missing indexes, and over-fetching
- [ ] Memory usage reviewed for leaks and unbounded collections
- [ ] Caching strategy evaluated (TTL, invalidation, key scoping, stampede)
- [ ] Boundary conditions checked (empty collections, large files, unbounded growth)
- [ ] Diagnostic questions applied to each module under review
- [ ] Findings documented with measured metrics (before/after estimate) and severity (P0-P3)

## Related Skills

- [[context-analysis]] -- Context understanding (Phase 1)
- [[code-quality]] -- Code quality + SOLID review (Phase 2)
- [[security-review]] -- Security analysis (Phase 3)
- [[performance-testing]] -- load and stress testing to confirm the bottlenecks this review identifies
- [[testing-review]] -- Test assessment (Phase 5)
- [[final-report]] -- Consolidated report (Phase 6)
- [[code-optimizer]] -- apply the algorithmic and caching optimizations this review recommends

---

**Version**: 2.0.0
**Last Updated**: February 2026
**Based on**: Nexus-Hub code review methodology + code-review-expert


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
