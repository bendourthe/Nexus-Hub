### Step 4: Apply Test Minimization

Reduce an existing complex reproduction to its minimal form.

**Python: Test minimizer**

```python
def minimize_reproduction(
    original_test_fn,
    setup_elements: list,
    verify_failure_fn,
) -> list:
    """Reduce the setup of a reproduction test to its minimal elements.

    Args:
        original_test_fn: The original test function (callable).
        setup_elements: List of setup steps that can be individually toggled.
        verify_failure_fn: Returns True if the bug still reproduces
                           with the given subset of setup elements.
    """
    # Start with all elements
    current = list(setup_elements)

    # Try removing each element one at a time
    changed = True
    while changed:
        changed = False
        for i in range(len(current) - 1, -1, -1):
            candidate = current[:i] + current[i + 1:]
            if verify_failure_fn(candidate):
                current = candidate
                changed = True
                break

    return current


def minimize_input_data(
    original_data: dict,
    test_fn,
) -> dict:
    """Reduce a complex input dictionary to the minimal keys needed to trigger the bug."""
    minimal = {}

    # First pass: find which top-level keys are required
    for key in original_data:
        subset = {k: v for k, v in original_data.items() if k != key}
        try:
            test_fn(subset)
            # If the test passes without this key, the key is needed
            # (we want the test to fail, meaning the bug reproduces)
        except Exception:
            # Bug still reproduces without this key; it is not needed
            continue
        minimal[key] = original_data[key]

    # If no keys were identified as required, all are needed
    if not minimal:
        return original_data

    # Verify that the minimal set still triggers the bug
    try:
        test_fn(minimal)
        return original_data  # Minimal set does not trigger; return original
    except Exception:
        return minimal
```
