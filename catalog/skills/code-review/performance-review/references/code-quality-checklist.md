# Code Quality Checklist: Error Handling, Performance & Boundary Conditions

Reference checklist for deep code quality analysis. Used by the `code-quality` and `performance-review` skills during Phases 2 and 4 of code review.

---

## 1. Error Handling

### Anti-Patterns

| Anti-Pattern | Example | Risk |
|-------------|---------|------|
| **Silent failures** | Empty `catch` / `except: pass` | Bugs go undetected, data corruption |
| **Overly broad catch** | `catch (Exception e)` without re-throw | Hides specific, actionable errors |
| **Error info leakage** | Stack traces in API responses | Reveals internals to attackers |
| **Missing error handling** | No try/catch around I/O operations | Unhandled crashes |
| **Unhandled promise rejections** | `.then()` without `.catch()`, missing `await` in try | Silent async failures |
| **Swallowed return values** | Ignoring error return codes from function calls | Proceeding on failed preconditions |

### Best Practices Checklist

- [ ] Errors are caught at appropriate boundaries (not too early, not too late)
- [ ] User-facing error messages are friendly and do not leak internals
- [ ] Sufficient logging context accompanies each error (request ID, user context, operation)
- [ ] Async errors are properly propagated (rejected promises, async/await with try-catch)
- [ ] Fallback behavior is defined for recoverable errors
- [ ] Monitoring/alerting is configured for critical error paths

### Diagnostic Questions

1. "If this operation fails, will anyone know? Is it logged? Is it alerted?"
2. "Does the error message give the caller enough information to understand what went wrong and how to fix it?"
3. "Are there any code paths where an error is caught but not handled, logged, or re-thrown?"

---

## 2. Performance & Caching

### CPU Hotspots

| Issue | Indicator | Mitigation |
|-------|-----------|------------|
| Expensive ops in hot paths | Sorting, serialization, regex in request handlers | Move to background, cache result |
| Blocking main thread | Sync file I/O, CPU-bound work on event loop | Use worker threads, async I/O |
| Unnecessary recomputation | Same calculation repeated in loops | Memoize, compute once |
| Missing memoization | Pure function called repeatedly with same inputs | Add `@lru_cache`, `useMemo`, or manual cache |

### Database & I/O

| Issue | Example | Fix |
|-------|---------|-----|
| **N+1 Queries** | `for user in users: orders = query(user.id)` | Use JOIN, eager loading, or batch query |
| **Missing indexes** | Queries filtering on non-indexed columns | Add database index |
| **Over-fetching** | `SELECT *` when only 2 columns needed | Select specific columns |
| **No pagination** | Loading entire table into memory | Add LIMIT/OFFSET or cursor pagination |
| **Redundant queries** | Same query executed multiple times per request | Cache or query once, pass result |

### Caching Issues

| Issue | Risk |
|-------|------|
| **Missing cache** | Repeated expensive computations or external calls |
| **Cache without TTL** | Stale data served indefinitely |
| **No invalidation strategy** | Cache and database drift apart |
| **Key collisions** | Different data overwriting each other |
| **Caching user-specific data globally** | Data leaks between users |
| **Cache stampede** | All caches expire simultaneously, overwhelming backend |

### Memory

| Issue | Indicator |
|-------|-----------|
| **Unbounded collections** | Lists/maps that grow without limit |
| **Large object retention** | References preventing garbage collection |
| **String concatenation in loops** | `O(n^2)` memory allocation pattern |
| **Loading entire files** | Reading large files into memory instead of streaming |
| **Event listener leaks** | Listeners registered but never removed |

### Diagnostic Questions

1. "What is the most expensive operation in the critical path? Can it be cached, batched, or deferred?"
2. "Are there any N+1 query patterns? (Loop that issues a query per iteration)"
3. "Is there any unbounded data structure that grows with input size?"
4. "For cached data, what is the TTL and invalidation strategy?"

---

## 3. Boundary Conditions

### Null / Undefined

| Pattern | Risk |
|---------|------|
| Missing null checks before property access | `TypeError: Cannot read property of null` |
| Truthy/falsy confusion | `0`, `""`, `false` treated as missing when they are valid values |
| Optional chaining overuse | `a?.b?.c?.d` masking bugs by silently returning `undefined` |
| Null vs undefined inconsistency | Different representations of "no value" causing comparison bugs |

### Empty Collections

| Pattern | Risk |
|---------|------|
| Empty array not handled | `.map()` on empty array produces empty result silently |
| First/last element access without length check | `array[0]` or `array[array.length - 1]` on empty array |
| `.reduce()` without initial value on potentially empty array | `TypeError` at runtime |
| Iteration assumptions | Code assumes collection always has at least 1 element |

### Numeric Boundaries

| Pattern | Risk |
|---------|------|
| Division by zero | Unguarded division where divisor could be 0 |
| Integer overflow | Arithmetic exceeding `MAX_SAFE_INTEGER` or type bounds |
| Floating point comparison | `0.1 + 0.2 !== 0.3` causing incorrect equality checks |
| Negative values | Negative amounts, indices, or quantities not validated |
| Off-by-one | Loop bounds using `<` vs `<=`, index calculations |

### String Boundaries

| Pattern | Risk |
|---------|------|
| Empty string | Not distinguished from null/undefined in validation |
| Whitespace-only strings | Passes `if (str)` check but has no meaningful content |
| Very long strings | No max length validation causing buffer/performance issues |
| Unicode edge cases | Multi-byte characters, emoji, RTL text breaking assumptions |
| Case sensitivity | Inconsistent use of case-sensitive vs case-insensitive comparison |

### Diagnostic Questions

1. "What happens if this value is null, undefined, empty, zero, negative, or very large?"
2. "What happens if this collection is empty?"
3. "Are numeric operations guarded against division by zero, overflow, and off-by-one errors?"
4. "Does string handling account for empty, whitespace-only, and very long inputs?"

---

## Usage

For each section, the reviewer should:
1. Scan the relevant code areas using the tables as a checklist
2. Apply the diagnostic questions to each function/module
3. Flag concrete instances with file path and line number
4. Classify severity: P0 (production crash risk) through P3 (minor improvement)
