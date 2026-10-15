### Step 5: Invariant Violation Detection

Verify that preconditions, postconditions, and loop invariants hold throughout the code.

**Python: Invariant checker**

```python
from functools import wraps
from typing import Callable

def precondition(*conditions: Callable):
    """Decorator that checks preconditions before function execution."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for condition in conditions:
                result = condition(*args, **kwargs)
                if not result:
                    raise AssertionError(
                        f"Precondition violated for {func.__name__}: "
                        f"{condition.__doc__ or condition.__name__}"
                    )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def postcondition(*conditions: Callable):
    """Decorator that checks postconditions after function execution."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            for condition in conditions:
                check = condition(result, *args, **kwargs)
                if not check:
                    raise AssertionError(
                        f"Postcondition violated for {func.__name__}: "
                        f"{condition.__doc__ or condition.__name__}"
                    )
            return result
        return wrapper
    return decorator


# Example usage
def non_negative_amount(amount, **kwargs):
    """Amount must be non-negative"""
    return amount >= 0

def balance_non_negative(result, amount, **kwargs):
    """Balance must remain non-negative after withdrawal"""
    return result >= 0

@precondition(non_negative_amount)
@postcondition(balance_non_negative)
def withdraw(amount, balance=0):
    return balance - amount


class InvariantChecker:
    """Runtime invariant checking for detecting semantic bugs."""

    def __init__(self):
        self.violations: list[dict] = []

    def check_loop_invariant(
        self,
        invariant_fn: Callable,
        description: str,
        context: dict,
    ) -> bool:
        """Check a loop invariant and record violations."""
        result = invariant_fn(context)
        if not result:
            self.violations.append({
                "type": "loop_invariant",
                "description": description,
                "context": context,
            })
        return result

    def check_data_invariant(
        self,
        data: any,
        invariant_fn: Callable,
        description: str,
    ) -> bool:
        """Check a data structure invariant."""
        result = invariant_fn(data)
        if not result:
            self.violations.append({
                "type": "data_invariant",
                "description": description,
                "data_snapshot": repr(data)[:200],
            })
        return result


# Example: checking a sorted list invariant
def is_sorted(lst):
    return all(lst[i] <= lst[i + 1] for i in range(len(lst) - 1))

checker = InvariantChecker()

def insert_sorted(lst, value):
    """Insert a value while maintaining sorted order."""
    # Precondition: list must be sorted
    checker.check_data_invariant(lst, is_sorted, "Input list must be sorted")

    # Find insertion point
    i = 0
    while i < len(lst) and lst[i] < value:
        i += 1
    lst.insert(i, value)

    # Postcondition: list must still be sorted
    checker.check_data_invariant(lst, is_sorted, "Output list must remain sorted")
    return lst
```

**JavaScript: Invariant checker**

```javascript
function precondition(conditionFn, description) {
  return function (target, propertyKey, descriptor) {
    const originalMethod = descriptor.value;
    descriptor.value = function (...args) {
      if (!conditionFn.apply(this, args)) {
        throw new Error(
          `Precondition violated for ${propertyKey}: ${description}`
        );
      }
      return originalMethod.apply(this, args);
    };
    return descriptor;
  };
}

function postcondition(conditionFn, description) {
  return function (target, propertyKey, descriptor) {
    const originalMethod = descriptor.value;
    descriptor.value = function (...args) {
      const result = originalMethod.apply(this, args);
      if (!conditionFn.call(this, result, ...args)) {
        throw new Error(
          `Postcondition violated for ${propertyKey}: ${description}`
        );
      }
      return result;
    };
    return descriptor;
  };
}

// Without decorators (plain function wrapper approach)
function withInvariant(fn, { pre, post, preDesc, postDesc }) {
  return function (...args) {
    if (pre && !pre(...args)) {
      throw new Error(`Precondition violated for ${fn.name}: ${preDesc}`);
    }
    const result = fn.apply(this, args);
    if (post && !post(result, ...args)) {
      throw new Error(`Postcondition violated for ${fn.name}: ${postDesc}`);
    }
    return result;
  };
}

// Example usage
const safeDivide = withInvariant(
  function divide(a, b) {
    return a / b;
  },
  {
    pre: (a, b) => b !== 0,
    preDesc: "Divisor must not be zero",
    post: (result) => Number.isFinite(result),
    postDesc: "Result must be a finite number",
  }
);
```
