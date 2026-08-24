### Step 6: Optimize Performance

**Profiling Before Optimizing**:

```python
import cProfile
import pstats

def profile_function(func, *args, **kwargs):
    """Profile a function and print the top 20 calls by cumulative time."""
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()

    stats = pstats.Stats(profiler)
    stats.sort_stats("cumulative")
    stats.print_stats(20)
    return result

# Or use the decorator approach
# python -m cProfile -s cumulative myapp/main.py
```

**Generators for Memory Efficiency**:

```python
# Bad: loads everything into memory
def read_all_lines(path: str) -> list[str]:
    with open(path) as f:
        return f.readlines()  # Entire file in memory

# Good: yields one line at a time
def read_lines(path: str) -> Iterator[str]:
    with open(path) as f:
        for line in f:
            yield line.strip()

# Generator expression (lazy evaluation)
total = sum(len(line) for line in read_lines("large_file.txt"))

# itertools for composable lazy pipelines
import itertools

def process_large_dataset(path: str) -> Iterator[dict[str, str]]:
    lines = read_lines(path)
    non_empty = (line for line in lines if line)
    batches = itertools.batched(non_empty, 1000)  # Python 3.12+
    for batch in batches:
        yield from process_batch(batch)
```

**Slots for Memory-Efficient Classes**:

```python
class HeavyObject:
    """Default: uses __dict__ for attribute storage."""
    def __init__(self, x: int, y: int, z: int) -> None:
        self.x = x
        self.y = y
        self.z = z

class LightObject:
    """Slots: fixed attribute set, ~40% less memory per instance."""
    __slots__ = ("x", "y", "z")

    def __init__(self, x: int, y: int, z: int) -> None:
        self.x = x
        self.y = y
        self.z = z

# Memory comparison (approximate):
# HeavyObject: ~152 bytes per instance
# LightObject: ~88 bytes per instance
```

**Caching with lru_cache and cache**:

```python
from functools import lru_cache, cache

@lru_cache(maxsize=256)
def fibonacci(n: int) -> int:
    """Memoized Fibonacci: O(n) instead of O(2^n)."""
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# Unbounded cache (Python 3.9+)
@cache
def expensive_lookup(key: str) -> dict[str, object]:
    return database.query(key)

# Cache with TTL using third-party library
from cachetools import TTLCache

api_cache: TTLCache[str, dict[str, object]] = TTLCache(maxsize=1000, ttl=300)
```

**Comprehensions Over Loops**:

```python
# List comprehension (faster than append loop)
squares = [x * x for x in range(1000)]

# Dict comprehension
index = {user.id: user for user in users}

# Set comprehension for deduplication
unique_domains = {email.split("@")[1] for email in emails}

# Conditional comprehension
active_users = [u for u in users if u.is_active and u.last_login is not None]

# Avoid nested comprehensions beyond 2 levels; use a function instead
# Bad:
matrix = [[row[i] for row in data] for i in range(cols)]
# Better:
def transpose(data: list[list[int]]) -> list[list[int]]:
    return [list(col) for col in zip(*data)]
```
