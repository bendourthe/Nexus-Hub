# Phase 4: Performance & Scalability Review

## Objective
Evaluate code efficiency, identify performance bottlenecks, and assess scalability considerations.

## Review Checklist

### Algorithm Efficiency
- [ ] Appropriate data structures chosen
- [ ] Time complexity considered and documented
- [ ] Space complexity optimized
- [ ] No unnecessary nested loops
- [ ] Efficient searching and sorting algorithms
- [ ] Caching implemented where beneficial

### Memory Management
- [ ] No memory leaks
- [ ] Large data processed in chunks/streaming
- [ ] Unnecessary object creation avoided
- [ ] Generator expressions used where appropriate
- [ ] Memory-intensive operations optimized

### Database Operations
- [ ] Queries optimized (proper indexing considered)
- [ ] N+1 query problems avoided
- [ ] Batch operations used for multiple records
- [ ] Connection pooling implemented
- [ ] Query results limited appropriately
- [ ] Unnecessary queries eliminated

### I/O Operations
- [ ] File I/O performed efficiently
- [ ] Unnecessary file reads/writes avoided
- [ ] Buffering used appropriately
- [ ] Async I/O considered for concurrent operations
- [ ] Network calls minimized and batched

### Concurrency & Parallelism
- [ ] Thread safety considered where needed
- [ ] Appropriate use of threading vs multiprocessing
- [ ] Race conditions prevented
- [ ] Deadlocks prevented
- [ ] Concurrent operations properly synchronized

### Scalability Considerations
- [ ] Code handles growing data volumes
- [ ] No hardcoded limits that don't scale
- [ ] Resource usage bounded
- [ ] Horizontal scaling possible
- [ ] Performance degradation documented

### Profiling & Monitoring
- [ ] Performance-critical sections identified
- [ ] Logging doesn't impact performance
- [ ] Metrics collection implemented
- [ ] Performance benchmarks defined

## Detailed Review Prompt

```
Please perform a comprehensive performance and scalability review:

**Algorithm Efficiency Analysis:**
1. Review data structure choices:
   - Lists vs Sets vs Dicts for lookups
   - Appropriate use of collections (deque, defaultdict, Counter)
   - Efficient algorithms for searching and sorting

2. Analyze time complexity:
   ```python
   # Good: O(1) lookup with set
   valid_ids = set([1, 2, 3, 4, 5])
   if user_id in valid_ids:
       process(user_id)
   
   # Bad: O(n) lookup with list
   valid_ids = [1, 2, 3, 4, 5]
   if user_id in valid_ids:
       process(user_id)
   
   # Good: O(n) with dict comprehension
   result = {k: v for k, v in items.items() if condition(v)}
   
   # Bad: O(n²) with nested loops when unnecessary
   result = {}
   for k, v in items.items():
       for other_k in items.keys():
           if k == other_k and condition(v):
               result[k] = v
   ```

3. Identify caching opportunities:
   - Expensive computations repeated
   - API calls that could be cached
   - Database queries that could be cached
   - Consider @functools.lru_cache or custom caching

**Memory Management Assessment:**
1. Check for memory leaks:
   - Circular references
   - Unclosed file handles or connections
   - Growing caches without eviction
   - Large objects kept in memory unnecessarily

2. Review memory-intensive operations:
   ```python
   # Good: Generator for large datasets
   def process_large_file(file_path):
       with open(file_path) as f:
           for line in f:
               yield process_line(line)
   
   # Bad: Loading entire file into memory
   def process_large_file(file_path):
       with open(file_path) as f:
           lines = f.readlines()
           return [process_line(line) for line in lines]
   
   # Good: Generator expression
   total = sum(x**2 for x in range(10000000))
   
   # Bad: List comprehension for large dataset
   total = sum([x**2 for x in range(10000000)])
   ```

3. Check for unnecessary object creation:
   - String concatenation in loops (use join)
   - Repeated instantiation of same objects
   - Deep copying when shallow copy suffices

**Database Operations Review:**
1. Query optimization:
   - Check for N+1 query problems
   - Verify proper use of SELECT fields (avoid SELECT *)
   - Look for missing indexes
   - Check for unnecessary JOINs
   - Verify LIMIT clauses on large result sets

2. Batch operations:
   ```python
   # Good: Bulk insert
   db.bulk_insert(records)
   
   # Bad: Individual inserts in loop
   for record in records:
       db.insert(record)
   ```

3. Connection management:
   - Connection pooling used
   - Connections properly closed
   - Transaction management appropriate

**I/O Operations Assessment:**
1. File operations:
   - Large files processed in chunks
   - Buffering used appropriately
   - Unnecessary file operations eliminated
   - Temporary files cleaned up

2. Network operations:
   - Requests batched where possible
   - Timeouts configured
   - Retry logic with exponential backoff
   - Connection reuse implemented

3. Async opportunities:
   ```python
   # Consider async for I/O-bound operations
   import asyncio
   
   async def fetch_multiple_urls(urls):
       async with aiohttp.ClientSession() as session:
           tasks = [fetch_url(session, url) for url in urls]
           return await asyncio.gather(*tasks)
   ```

**Concurrency Review:**
1. Thread safety assessment:
   - Shared state properly protected
   - Race conditions identified
   - Deadlock potential evaluated
   - Lock contention minimized

2. Parallelism evaluation:
   ```python
   # Threading for I/O-bound
   from concurrent.futures import ThreadPoolExecutor
   
   with ThreadPoolExecutor(max_workers=8) as executor:
       results = executor.map(io_bound_task, items)
   
   # Multiprocessing for CPU-bound
   from concurrent.futures import ProcessPoolExecutor
   
   with ProcessPoolExecutor(max_workers=4) as executor:
       results = executor.map(cpu_bound_task, items)
   ```

**Scalability Assessment:**
1. Data volume handling:
   - Code handles 10x, 100x, 1000x current data
   - No hardcoded array sizes or limits
   - Memory usage bounded or streaming

2. Load handling:
   - Concurrent user support evaluated
   - Resource exhaustion prevented
   - Graceful degradation under load

3. Horizontal scaling:
   - Stateless design where appropriate
   - Distributed caching considered
   - Database sharding potential

**Performance Hotspots:**
Identify and document:
- Most frequently called functions
- Functions with highest execution time
- Memory-intensive operations
- Database query bottlenecks
- Network I/O bottlenecks

**Deliverables:**
Provide a performance assessment report with:
- Critical performance issues (requires immediate optimization)
- High-impact optimization opportunities
- Algorithm efficiency improvements
- Memory optimization suggestions
- Database query optimizations
- Scalability concerns and recommendations
- Specific code locations with metrics (if available)
- Recommended profiling areas
- Overall performance rating (Excellent/Good/Needs Optimization/Poor)
```

## Expected Outcomes

### Pass Criteria
- No critical performance bottlenecks
- Appropriate algorithms and data structures used
- Efficient database queries
- Reasonable memory usage
- Code scales to expected data volumes
- Concurrency properly handled

### Critical Issues to Flag
- O(n²) or worse algorithms where better exists
- Memory leaks
- N+1 query problems
- Unbounded resource consumption
- Thread safety violations in concurrent code
- Complete file loading for large files

### High-Priority Optimizations
- Inefficient loops and iterations
- Missing caching for expensive operations
- Suboptimal data structures
- Inefficient database queries
- Missing batch operations
- Synchronous I/O that could be async

## Performance Patterns Reference

### Efficient Caching
```python
from functools import lru_cache
import time

@lru_cache(maxsize=128)
def expensive_computation(n: int) -> int:
    """Cache results of expensive computation."""
    time.sleep(1)  # Simulate expensive operation
    return n * n

# Use binary search for O(log n) performance on sorted data
# This is critical for large datasets (>10k items)
result = binary_search(sorted_list, target)
```

### Memory-Efficient Processing
```python
def process_large_dataset(file_path: str):
    """Process large dataset without loading into memory."""
    with open(file_path) as f:
        for line in f:
            # Process one line at a time
            yield process_line(line)

# Generator expression for memory efficiency
total = sum(x**2 for x in range(10_000_000))
```

### Efficient Database Operations
```python
# Batch operations
def bulk_insert_users(users: List[Dict]):
    """Insert multiple users efficiently."""
    db.bulk_insert('users', users)

# Select only needed fields
def get_user_names():
    """Retrieve only necessary fields."""
    return db.query("SELECT id, name FROM users")

# Use pagination for large result sets
def get_paginated_results(page: int = 1, size: int = 100):
    """Retrieve results in pages."""
    offset = (page - 1) * size
    return db.query(f"SELECT * FROM items LIMIT {size} OFFSET {offset}")
```

### Parallel Processing
```python
from concurrent.futures import ThreadPoolExecutor
import time

# Use thread pool for I/O-bound operations
# Testing showed 4x performance improvement with 8 threads
def process_urls_parallel(urls: List[str]):
    """Process multiple URLs concurrently."""
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(fetch_url, urls))
    return results
```

### Efficient String Operations
```python
# Good: Join for string concatenation
result = ''.join(items)

# Bad: String concatenation in loop
result = ''
for item in items:
    result += item

# Good: Use f-strings for formatting
message = f"User {user_id} processed in {elapsed:.2f}s"

# Avoid: Old-style formatting
message = "User %s processed in %.2f s" % (user_id, elapsed)
```

## Next Steps
After completing this phase, proceed to Phase 5: Testing & Quality Assurance Review.
