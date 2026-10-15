### Step 6: Apply Delta Debugging

Delta debugging narrows a failing input or change set to its minimal failing subset.

**Python: Delta debugging algorithm**

```python
def delta_debug(changes: list, test_fn) -> list:
    """Find the minimal subset of changes that still triggers the failure.

    Args:
        changes: List of individual changes (lines, commits, etc.).
        test_fn: Callable that returns True if the bug is still present
                 with the given subset of changes.

    Returns:
        Minimal failing subset.
    """
    n = 2
    while len(changes) >= 2:
        chunk_size = max(len(changes) // n, 1)
        chunks = [
            changes[i:i + chunk_size]
            for i in range(0, len(changes), chunk_size)
        ]

        found_smaller = False
        for chunk in chunks:
            if test_fn(chunk):
                changes = chunk
                n = 2
                found_smaller = True
                break

        if not found_smaller:
            complement_found = False
            for chunk in chunks:
                complement = [c for c in changes if c not in chunk]
                if test_fn(complement):
                    changes = complement
                    n = 2
                    complement_found = True
                    break

            if not complement_found:
                if n >= len(changes):
                    break
                n = min(n * 2, len(changes))

    return changes
```
