---
name: add-strategic-comments
description: Add strategic, high-value comments that explain complex logic, business rules, and design decisions without cluttering code with obvious statements
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language (Python, JavaScript, Java, C#, Go, C, C++)
category: Documentation
priority: MEDIUM
tags: [documentation, comments, code-clarity, maintainability, refactoring, best-practices]
template_sources:

  - documentation/comments/python_comments.md
  - documentation/comments/javascript_comments.md
  - documentation/comments/java_comments.md
  - documentation/comments/csharp_comments.md
  - documentation/comments/go_comments.md
  - documentation/comments/c_comments.md
  - documentation/comments/cpp_comments.md
---

# Add Strategic Comments

Add meaningful, high-value comments that explain "why" not "what", focusing on complex algorithms, business logic, design decisions, and non-obvious implementations while maintaining clean, self-documenting code.

## When to Use This Skill

Use this skill when you need to:
- Explain complex business logic and rules
- Document non-obvious algorithm implementations
- Clarify design decisions and trade-offs
- Mark temporary workarounds and technical debt
- Explain performance optimizations
- Document security considerations
- Clarify edge case handling
- Add context for future maintainers
- Improve code comprehension without cluttering
- Balance self-documenting code with necessary explanations

## What This Skill Does

This skill identifies where strategic comments add value and generates appropriate comments:

### For All Languages
1. **Strategic Comment Identification**
   - Complex algorithms requiring explanation
   - Non-obvious business rules
   - Design decision rationale
   - Performance optimization reasoning
   - Security-critical sections
   - Workarounds and temporary fixes
   - Edge case handling

2. **Comment Quality Standards**
   - Explain "why" not "what"
   - Add value beyond code itself
   - Stay concise and focused
   - Remain maintainable over time
   - Avoid redundancy with code
   - Use proper formatting conventions

3. **Technical Debt Tracking**
   - TODO: Future improvements
   - FIXME: Known issues to address
   - HACK: Temporary workarounds
   - NOTE: Important considerations
   - WARNING: Critical information

4. **Refactoring Suggestions**
   - Identify code needing simplification
   - Suggest when comments indicate poor design
   - Balance commenting vs. code improvement
   - Recommend self-documenting alternatives

### Language-Specific Features

#### Python
- **Block Comments**: `#` for explanations above code blocks
- **Inline Comments**: Sparingly, only when necessary
- **PEP 8**: Comment style guidelines
- **Examples**:
  ```python
  # Use binary search for O(log n) performance on sorted data
  # Standard library bisect module provides this functionality
  index = bisect.bisect_left(sorted_items, target)

  # Cache expensive API calls to avoid rate limiting (100 calls/min)
  # Cache expires after 5 minutes to balance freshness vs performance
  if key not in self.cache or time.time() - self.cache_time > 300:
      self.cache[key] = expensive_api_call(key)
      self.cache_time = time.time()

  # HACK: Workaround for library bug in version 2.3.x
  # Remove this when upgrading to 2.4+ which fixes the issue
  # See: https://github.com/library/issues/1234
  if library_version < (2, 4):
      apply_workaround()

  # WARNING: This regex is intentionally permissive to handle legacy data
  # Tightening validation would reject 15% of existing records
  # Business decision from 2024-10-15 stakeholder meeting
  pattern = r'[\w\-\.]+'
  ```

#### JavaScript/TypeScript
- **Block Comments**: `//` or `/* */` for multi-line
- **JSDoc vs Comments**: JSDoc for API, comments for logic
- **Examples**:
  ```javascript
  // Debounce API calls to prevent overwhelming the server
  // 300ms delay balances responsiveness with load reduction
  const debouncedSearch = debounce(searchAPI, 300);

  // Use WeakMap to avoid memory leaks with DOM references
  // Standard Map would prevent garbage collection of removed elements
  const elementCache = new WeakMap();

  // TODO: Refactor this into smaller functions when requirements stabilize
  // Currently in flux due to ongoing product discussions
  function complexBusinessLogic(data) {
      // ...
  }

  // PERF: Batch database writes to reduce transaction overhead
  // Testing showed 10x improvement vs individual writes
  // Trade-off: Slight delay in data consistency (acceptable per product)
  if (pendingWrites.length >= BATCH_SIZE) {
      await flushWrites();
  }

  // TypeScript type narrowing requires explicit check here
  // Despite earlier validation, TS cannot infer type safety across functions
  if (value === null) {
      throw new Error('Unexpected null value');
  }
  ```

#### Java
- **Block Comments**: `//` for single-line, `/* */` for multi-line
- **JavaDoc**: Separate from strategic comments
- **Examples**:
  ```java
  // Use ConcurrentHashMap instead of synchronized HashMap
  // Lock-striping provides better scalability under high concurrency
  // See "Java Concurrency in Practice" §11.4
  private final ConcurrentHashMap<String, Value> cache = new ConcurrentHashMap<>();

  // Defensive copy to prevent external modification of internal state
  // Required by Effective Java Item 50: Make defensive copies
  public List<Item> getItems() {
      return new ArrayList<>(this.items);
  }

  // FIXME: Race condition when processing concurrent updates
  // Temporary lock prevents data corruption but impacts throughput
  // Need to implement optimistic locking in next sprint
  synchronized (this.processingLock) {
      processUpdate(data);
  }

  // Business rule: Minimum order value varies by region
  // North America: $25, Europe: €20, Asia: ¥2000
  // Configured in database but hardcoded fallback for system startup
  private static final double DEFAULT_MIN_ORDER = 25.0;

  // Reflection used here for plugin system extensibility
  // Direct instantiation would require compile-time dependencies
  // Performance impact acceptable: only during initialization
  Class<?> pluginClass = Class.forName(pluginClassName);
  ```

#### C#
- **Block Comments**: `//` for single-line, `/* */` for multi-line
- **XML Docs**: Separate from strategic comments
- **Examples**:
  ```csharp
  // Use Lazy<T> for thread-safe singleton initialization
  // Double-check locking pattern is error-prone in C#
  // See: https://csharpindepth.com/articles/singleton
  private static readonly Lazy<DatabaseConnection> _instance =
      new Lazy<DatabaseConnection>(() => new DatabaseConnection());

  // LINQ deferred execution: query built here, executed on iteration
  // Avoid multiple enumerations which would re-execute query
  var results = data.Where(x => x.IsActive)
                    .OrderBy(x => x.Priority)
                    .ToList();  // Force immediate execution

  // WARNING: IDisposable not implemented - deliberate design choice
  // Resource cleanup handled by DI container lifetime management
  // Implementing IDisposable would conflict with scoped service pattern
  public class ServiceClient {
      // ...
  }

  // Async/await used here to prevent thread pool starvation
  // ConfigureAwait(false) avoids deadlock in legacy sync contexts
  var result = await ProcessAsync().ConfigureAwait(false);

  // TODO: Migrate to System.Text.Json when .NET 6 upgrade completes
  // Newtonsoft.Json retained for compatibility with existing serialized data
  var json = JsonConvert.SerializeObject(data);
  ```

#### Go
- **Block Comments**: `//` standard, `/* */` for multi-line
- **Exported vs Unexported**: Different comment needs
- **Examples**:
  ```go
  // Use buffered channel to prevent goroutine leaks
  // Buffer size matches expected concurrent operations (10)
  // Unbuffered channel would block senders if receiver is slow
  results := make(chan Result, 10)

  // Mutex protects shared state from concurrent access
  // RWMutex not used: write operations far exceed reads (90%)
  // Profiling showed standard Mutex performs better for this pattern
  mu.Lock()
  defer mu.Unlock()

  // FIXME: Context cancellation not propagated to downstream services
  // Temporary issue until v2 API supports context passing
  // Tracked in issue #567
  go worker.Process(data)

  // Business rule: Retry with exponential backoff up to 5 attempts
  // Base delay: 100ms, max delay: 3.2s (100ms * 2^5)
  // Requirements from SLA agreement section 4.2
  for attempt := 0; attempt < maxRetries; attempt++ {
      time.Sleep(baseDelay * (1 << uint(attempt)))
      // ...
  }

  // Interface satisfied by multiple implementations
  // Loose coupling enables testing with mocks and future extensibility
  // See: https://go.dev/blog/using-go-interfaces
  var processor Processor = &DefaultProcessor{}
  ```

#### C
- **Block Comments**: `//` (C99+) or `/* */` (traditional)
- **Header Comments**: Function declarations in headers
- **Examples**:
  ```c
  /* Use static inline for small frequently-called functions

   * Compiler likely to inline, reducing function call overhead
   * Benchmark showed 15% performance improvement in hot path */
  static inline int min(int a, int b) {
      return (a < b) ? a : b;
  }

  /* Manual memory management required for legacy API compatibility
   * Modern code should use RAII-style wrappers in C++
   * Caller must free() returned pointer */
  char* allocate_buffer(size_t size) {
      // ...
  }

  /* HACK: Workaround for undefined behavior in pre-C99 compilers
   * Flexible array member not supported, using size 1 + allocation
   * Remove when minimum compiler version raised to C99 */
  struct packet {
      size_t length;
      char data[1];  /* Variable-length data follows */
  };

  /* Thread-local storage for errno-style error reporting
   * Alternative to global variable prevents race conditions
   * Requires compiler TLS support (-pthread flag) */
  __thread int last_error = 0;

  /* WARNING: Buffer overflow risk if input not validated
   * Caller MUST ensure src_len <= dest_size - 1
   * Consider using strncpy_s on platforms supporting it */
  void unsafe_copy(char* dest, const char* src, size_t dest_size);
  ```

#### C++
- **Block Comments**: `//` standard, `/* */` for multi-line
- **Modern C++**: Comment trade-offs and design choices
- **Examples**:
  ```cpp
  // Use unique_ptr for automatic memory management
  // No manual delete needed, exception-safe, zero overhead
  // Prefer over raw pointers unless performance-critical hot path
  auto resource = std::make_unique<Resource>();

  // Move semantics avoid expensive copy of large vector
  // std::move transfers ownership, leaving source in valid state
  // Essential for performance with large data structures
  data_ = std::move(source_data);

  // SFINAE used for conditional template instantiation
  // std::enable_if restricts template to arithmetic types only
  // Prevents compilation errors with invalid types
  template<typename T>
  typename std::enable_if<std::is_arithmetic<T>::value, T>::type
  calculate(T value) {
      // ...
  }

  // Lock-free algorithm using atomic operations
  // Compare-exchange prevents ABA problem in concurrent stack
  // See "C++ Concurrency in Action" §7.2 for detailed explanation
  T* old_head = head_.load(std::memory_order_acquire);
  while (!head_.compare_exchange_weak(
      old_head, new_node,
      std::memory_order_release,
      std::memory_order_acquire)) {
      // Retry until successful
  }

  // TODO: Replace with std::span when migrating to C++20
  // Current gsl::span is temporary bridge for C++17 compatibility
  // Minimal code changes required for migration
  void process(gsl::span<const int> data);

  // Virtual destructor required for polymorphic class
  // Without virtual, deleting via base pointer causes undefined behavior
  // See C++ Core Guidelines C.35
  virtual ~BaseClass() = default;
  ```

## Prerequisites

- Codebase with complex logic or non-obvious implementations
- Understanding of code purpose and design decisions
- Knowledge of project history and context
- Identification of technical debt and workarounds
- Team coding standards for comments

## Instructions

### Step 1: Analyze Code for Comment Opportunities

1. **Identify Complex Logic**:
   - Algorithms with non-obvious implementations
   - Business rules with specific requirements
   - Performance optimizations
   - Security-critical sections
   - Edge case handling

2. **Find Design Decisions**:
   - Architecture choices
   - Technology selections
   - Trade-off considerations
   - Workarounds for limitations
   - Compatibility concerns

3. **Locate Technical Debt**:
   - Temporary solutions
   - Known issues
   - Future improvements
   - Refactoring candidates
   - Deprecated patterns

4. **Review Existing Comments**:
   - Remove redundant comments
   - Update outdated information
   - Clarify ambiguous comments
   - Remove commented-out code

### Step 2: Invoke the Add Strategic Comments Skill

For **Python** code:
```
"Use the add-strategic-comments skill to add meaningful comments to Python code.

Language: Python
Scope: Module 'business_logic.py' / Directory 'src/core/'
Focus Areas:

- Complex algorithms in data processing
- Business rules validation logic
- Performance optimizations (caching, etc.)
- Workarounds for library limitations
- Security considerations
Guidelines:

- Explain 'why' not 'what'
- Avoid redundant comments
- Use TODO/FIXME/HACK appropriately
- Keep comments concise
- Follow PEP 8 style"
```

For **JavaScript/TypeScript** code:
```
"Use the add-strategic-comments skill for JavaScript/TypeScript comments.

Language: JavaScript / TypeScript
Scope: Module 'services/api.js' / Directory 'src/utils/'
Focus Areas:

- Asynchronous operation patterns
- Type narrowing explanations (TypeScript)
- Performance optimizations
- Browser compatibility workarounds
- State management logic
Guidelines:

- Explain design decisions
- Document performance trade-offs
- Clarify type inference limitations
- Mark technical debt with TODO/FIXME
- Balance JSDoc with inline comments"
```

For **Java** code:
```
"Use the add-strategic-comments skill for Java code commentary.

Language: Java
Scope: Class 'BusinessService.java' / Package 'com.example.core'
Focus Areas:

- Thread safety considerations
- Design pattern implementations
- Exception handling strategies
- Resource management
- Business rule enforcement
Guidelines:

- Explain concurrency design choices
- Document defensive programming
- Reference Effective Java items
- Use FIXME for known issues
- Keep comments maintainable"
```

For **C#** code:
```
"Use the add-strategic-comments skill for C# code documentation.

Language: C#
Scope: Class 'DataProcessor.cs' / Namespace 'MyApp.Core'
Focus Areas:

- Async/await patterns
- LINQ query explanations
- Dependency injection decisions
- IDisposable implementations
- Performance optimizations
Guidelines:

- Explain asynchronous design
- Document LINQ deferred execution
- Clarify DI lifetime choices
- Mark technical debt
- Reference Microsoft documentation"
```

For **Go** code:
```
"Use the add-strategic-comments skill for Go code commentary.

Language: Go
Scope: Package 'processor' / File 'worker.go'
Focus Areas:

- Goroutine and channel patterns
- Error handling strategies
- Interface design decisions
- Memory management
- Concurrency patterns
Guidelines:

- Explain goroutine coordination
- Document channel buffer sizing
- Clarify interface contracts
- Reference Go blog posts
- Keep comments idiomatic"
```

For **C/C++** code:
```
"Use the add-strategic-comments skill for C/C++ code documentation.

Language: C / C++
Scope: Header 'processor.h' / Directory 'src/core/'
Focus Areas:

- Memory management strategies
- Thread safety guarantees
- Undefined behavior prevention
- Performance optimizations
- Modern C++ feature usage
Guidelines:

- Explain ownership semantics
- Document thread safety
- Warn about unsafe operations
- Reference C++ Core Guidelines
- Clarify template metaprogramming"
```

### Step 3: Review and Refine Comments

1. **Validate Comment Quality**:
   - Does it explain "why" not "what"?
   - Does it add value beyond code?
   - Is it clear and concise?
   - Will it remain accurate?
   - Could the code be improved instead?

2. **Check for Anti-Patterns**:
   - Redundant comments explaining obvious code
   - Commented-out code (remove or explain why kept)
   - Outdated information contradicting code
   - Apologies or complaints in comments
   - Excessive commentary cluttering code

3. **Consider Refactoring**:
   - If comment is complex, simplify code
   - Extract functions with descriptive names
   - Use constants instead of magic numbers
   - Improve variable naming
   - Apply design patterns

4. **Maintain Comment Quality**:
   - Update comments with code changes
   - Remove obsolete comments
   - Keep TODO/FIXME list manageable
   - Link to external documentation
   - Review comments in code reviews

### Step 4: Apply Comment Best Practices

#### When TO Comment

**Complex Algorithms**:
```python
# Floyd-Warshall algorithm for all-pairs shortest paths
# O(n³) complexity, suitable for dense graphs with n < 500
# Alternative: Dijkstra from each vertex for sparse graphs
```

**Business Rules**:
```javascript
// Discount calculation rules from pricing policy v2.3:
// - Orders > $100: 10% discount
// - Premium members: Additional 5%
// - Promotions stack (max 25% total)
```

**Design Decisions**:
```java
// Use lazy initialization instead of eager loading
// Trades startup time for memory efficiency
// Profiling showed 80% of instances never used
```

**Workarounds**:
```csharp
// HACK: Manually dispose DbContext due to DI container leak
// Remove when upgrading to .NET 8 which fixes the issue
// Tracked in internal ticket #4521
```

**Performance Optimizations**:
```go
// Pre-allocate slice capacity to avoid repeated reallocation
// Benchmarks showed 40% improvement for typical input size (1000)
// See: https://go.dev/blog/slices
```

**Security Considerations**:
```c
// Use constant-time comparison to prevent timing attacks
// Standard memcmp leaks information through execution time
// Critical for password and token validation
```

#### When NOT to Comment

**Obvious Code**:
```python
# BAD: Redundant comment
# Increment counter by 1
counter += 1

# GOOD: No comment needed (self-evident)
counter += 1
```

**Self-Documenting Code**:
```javascript
// BAD: Comment explains what good naming would convey
// Get user's first name
const fn = user.n;

// GOOD: Clear naming eliminates need for comment
const firstName = user.firstName;
```

**Commented-Out Code**:
```java
// BAD: Keeping old code "just in case"
// public void oldMethod() {
//     // old implementation
// }

// GOOD: Remove and rely on version control
// If needed, reference in commit message or CHANGELOG
```

**Changelog Comments**:
```csharp
// BAD: Change history belongs in version control
// Changed to use async/await - 2024-10-15 - John Doe
// Fixed bug with null values - 2024-10-20 - Jane Smith
public async Task ProcessAsync()

// GOOD: No change history in code
public async Task ProcessAsync()
```

### Step 5: Track Technical Debt

Use consistent markers for different comment types:

**TODO**: Future improvements
```python
# TODO: Refactor into separate service class when requirements stabilize
# TODO: Add input validation once schema is finalized
# TODO: Optimize query performance (currently O(n²))
```

**FIXME**: Known bugs or issues
```javascript
// FIXME: Race condition when multiple users access simultaneously
// FIXME: Memory leak in event listener cleanup
// FIXME: Incorrect calculation for leap years
```

**HACK**: Temporary workarounds
```java
// HACK: Workaround for library bug in version 3.2.x
// HACK: Disable SSL verification in development (DO NOT COMMIT)
// HACK: Manual JSON parsing due to serialization issue
```

**NOTE**: Important information
```csharp
// NOTE: This method is called by reflection in plugin system
// NOTE: Changing method signature will break API compatibility
// NOTE: Performance-critical section - profile before modifying
```

**WARNING**: Critical considerations
```go
// WARNING: Not thread-safe - caller must synchronize
// WARNING: Modifying this affects billing calculations
// WARNING: Security-sensitive code - review changes carefully
```

### Step 6: Integrate with Development Workflow

1. **Code Review Focus**:
   - Review comment quality with code changes
   - Ensure comments explain "why"
   - Verify no commented-out code
   - Check TODO/FIXME items are tracked

2. **Automated Checks**:
   ```bash
   # Find commented-out code (Python)
   grep -r "^[ ]*#.*def \|^[ ]*#.*class " --include="*.py"

   # Find TODO/FIXME/HACK items
   grep -r "TODO\|FIXME\|HACK" --include="*.py" --include="*.js"
   ```

3. **Linter Integration**:
   - Configure linters to check comment style
   - Set maximum comment line length
   - Enforce spacing around comment markers
   - Flag redundant comments (if tool supports)

4. **Documentation Generation**:
   - Strategic comments complement docstrings
   - Extract TODO/FIXME for issue tracking
   - Include design decision comments in architecture docs
   - Reference comments in technical documentation

## Quality Checklist

Before finalizing strategic comments, verify:

- [ ] Comments explain "why" not "what"
- [ ] Complex algorithms have clear explanations
- [ ] Business rules are documented with context
- [ ] Design decisions include rationale
- [ ] Workarounds are marked and tracked
- [ ] Performance optimizations are explained
- [ ] Security considerations are noted
- [ ] No redundant or obvious comments
- [ ] No commented-out code without explanation
- [ ] TODO/FIXME items are actionable
- [ ] Comments are concise and clear
- [ ] Language-specific conventions followed
- [ ] Comments will age well with code
- [ ] Refactoring considered before commenting
- [ ] External references included where helpful

## Common Issues and Solutions

### Issue: Too Many Comments
**Solution**:

- Review each comment: does it add value?
- Refactor code to be more self-documenting
- Use better variable/function names
- Extract complex logic into well-named functions
- Remove redundant comments

### Issue: Outdated Comments
**Solution**:

- Update comments when changing code
- Review comments during code review
- Remove comments that no longer apply
- Use linters to detect code-comment mismatches (if available)
- Keep comments focused on "why" which ages better

### Issue: Comment Overload on Simple Code
**Solution**:

- Trust developers to understand basic patterns
- Comment the non-obvious, not the obvious
- Use comments to explain intent, not mechanics
- Let code speak for itself when possible
- Focus comments on business logic and edge cases

### Issue: Inconsistent TODO/FIXME Usage
**Solution**:

- Define team standards for technical debt markers
- Create issue tracker tickets for important items
- Regular cleanup of completed TODO items
- Use consistent format: `TODO(author): description`
- Review and prioritize during planning meetings

## Success Criteria

After using this skill, you should have:

- [ ] Complex logic explained with clear comments
- [ ] Business rules documented with context
- [ ] Design decisions include rationale
- [ ] Workarounds marked and tracked
- [ ] Technical debt visible and managed
- [ ] No redundant or obvious comments
- [ ] No commented-out code clutter
- [ ] Consistent comment style across codebase
- [ ] Comments complement self-documenting code
- [ ] Development team understands when to comment

## Related Skills

- `generate-docstrings`: Create API documentation
- `generate-api-docs`: Build comprehensive API reference
- `create-technical-docs`: Document architecture decisions
- `code-review-quality`: Review code including comments
- `cleanup-*`: Clean up code and comments

## Tools by Language

### Python
- **pylint**: Comment style checking
- **pydocstyle**: Docstring conventions
- **flake8**: Code quality including comments
- **black**: Code formatting (comment spacing)

### JavaScript/TypeScript
- **ESLint**: Comment validation rules
- **prettier**: Comment formatting
- **tslint**: TypeScript-specific comment rules
- **jsdoc**: API documentation validation

### Java
- **Checkstyle**: Comment style enforcement
- **PMD**: Code quality including comments
- **SpotBugs**: Detect commented-out code
- **SonarQube**: Comment quality metrics

### C#
- **StyleCop**: Comment style rules
- **ReSharper**: Comment suggestions
- **SonarQube**: Code quality metrics
- **FxCop**: Code analysis including comments

### Go
- **golint**: Comment conventions
- **staticcheck**: Code quality analysis
- **gofmt**: Code formatting
- **revive**: Flexible linter with comment rules

### C/C++
- **cppcheck**: Static analysis
- **clang-tidy**: Comment style checking
- **cpplint**: Google style guide enforcement
- **doxygen**: Documentation generation

## Additional Resources

- [Code Complete 2 - Chapter 32: Self-Documenting Code](https://www.oreilly.com/library/view/code-complete-2nd/0735619670/)
- [Clean Code - Chapter 4: Comments](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
- [The Art of Readable Code - Chapter 5: Knowing What to Comment](https://www.oreilly.com/library/view/the-art-of/9781449318482/)
- [Google Code Review Guidelines - Comments](https://google.github.io/eng-practices/review/reviewer/looking-for.html#comments)
- [Linux Kernel Coding Style - Commenting](https://www.kernel.org/doc/html/latest/process/coding-style.html#commenting)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5 - documentation/comments/
