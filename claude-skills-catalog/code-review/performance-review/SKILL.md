---
name: performance-review
description: Profile performance, detect bottlenecks, analyze resource usage, and recommend optimizations. Use when addressing performance issues, optimizing hot paths, reducing resource consumption, or as Phase 4 of comprehensive code review.
---

# Code Review - Performance Review

Identify performance bottlenecks and optimization opportunities. This skill is **Phase 4** of the 6-phase code review methodology.

## When to Use This Skill

Use this skill when you need to:

- Identify performance bottlenecks
- Optimize critical code paths
- Reduce resource consumption
- Improve response times
- Address scalability concerns
- Profile memory and CPU usage

**Trigger phrases**: "performance review", "bottleneck", "slow code", "optimize", "profiling", "latency", "throughput", "memory usage"

## What This Skill Does

### Performance Dimensions

| Dimension | Metrics |
|-----------|---------|
| **Time** | Response time, latency, throughput |
| **Memory** | Heap usage, allocations, leaks |
| **CPU** | Utilization, hot paths |
| **I/O** | Database queries, network calls |
| **Concurrency** | Threading, async efficiency |

### Severity Classification

- **CRITICAL**: Production outages, severe degradation
- **HIGH**: Significant performance impact
- **MEDIUM**: Notable inefficiency
- **LOW**: Minor optimization opportunity

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

3. **I/O Analysis**
   - N+1 query patterns
   - Unoptimized database queries
   - Unnecessary network calls

### Step 3: Common Anti-Patterns

| Anti-Pattern | Issue | Solution |
|--------------|-------|----------|
| N+1 Queries | Loop database calls | Batch queries, joins |
| Large Payloads | Excessive data transfer | Pagination, field selection |
| No Caching | Repeated computations | Add caching layer |
| Sync I/O | Blocking operations | Async/await |
| String Concatenation | Memory allocation | StringBuilder/join |

### Step 4: Document Findings

```markdown
## Performance Finding

**File**: [path/to/file.py:42]
**Severity**: HIGH
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
- Latency: 500ms → 50ms
- Database queries: N+1 → 1
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

## Quality Checklist

- [ ] Application profiled
- [ ] Hot paths identified
- [ ] Database queries analyzed
- [ ] Memory usage reviewed
- [ ] Caching opportunities found
- [ ] Findings documented with metrics

## Related Skills

- `context-analysis` - Context understanding (Phase 1)
- `performance-testing` - Load testing
- `final-report` - Consolidated report (Phase 6)

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Based on**: AI Templates code_review/performance_review/
