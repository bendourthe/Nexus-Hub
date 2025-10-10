# C# Strategic Comments

## Objective
Add strategic, high-value comments that explain "why" rather than "what", focusing on business logic, design decisions, non-obvious implementations, and workarounds while avoiding redundant commentary.

## Output Directory Structure

All outputs should be saved in organized directories:

```
documentation/comments/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `documentation/comments/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### When to Comment
- [ ] Complex algorithms requiring explanation
- [ ] Business logic and domain rules
- [ ] Non-obvious code decisions
- [ ] Workarounds for bugs in dependencies
- [ ] Performance-critical sections
- [ ] Security-sensitive code
- [ ] Thread safety and async patterns
- [ ] LINQ query complexity
- [ ] IDisposable implementation reasoning

### When NOT to Comment
- [ ] Obvious code that's self-explanatory
- [ ] Information already in XML documentation
- [ ] Redundant type information
- [ ] Meta-commentary about changes
- [ ] Commented-out code

### Comment Quality
- [ ] Explains "why" not "what"
- [ ] Adds genuine value
- [ ] Concise and clear
- [ ] Properly formatted
- [ ] Up-to-date with code

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C# Strategic Comments Request

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="documentation/comments"
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

Please add strategic comments to this C# project following this protocol:

## Phase 1: Analysis & Comment Identification

1. **Analyze Codebase for Comment Opportunities**
   Review the code to identify sections that would benefit from comments:
   - Complex algorithms or business logic
   - Non-obvious implementation decisions
   - Workarounds for known issues
   - Performance-critical sections
   - Security-sensitive operations
   - Thread safety and async/await patterns
   - Resource management (IDisposable) decisions
   - Sections likely to confuse future developers

2. **Identify Existing Comments**
   - Review current comments for quality and value
   - Flag redundant or obvious comments for removal
   - Identify outdated comments needing updates
   - Check for commented-out code to remove

3. **Generate Comment Plan**
   Create a prioritized list of where comments add value before adding them.

## Phase 2: Strategic Comment Patterns

### 1. Complex Algorithm Comments

Use **block comments** before complex algorithms:

```csharp
/// <summary>
/// Calculate optimal route using A* pathfinding algorithm.
/// We use A* instead of Dijkstra because our graph has a reliable heuristic
/// (Euclidean distance), which reduces search time by ~40% in testing.
/// Trade-off: Uses more memory (O(n) vs O(log n)) but acceptable for our
/// typical graph sizes (<1000 nodes).
/// </summary>
public Route FindOptimalRoute(Node start, Node end, Graph graph)
{
    var openSet = new HashSet<Node> { start };
    var cameFrom = new Dictionary<Node, Node>();
    // ... implementation
}
```

**Good**: Explains algorithm choice, trade-offs, and why it's appropriate
**Bad**: `// Find route` (obvious from method name)

### 2. Business Logic Comments

Document domain rules and business decisions:

```csharp
// Business rule: Premium users get 30-day refund window, standard users get 14 days.
// This differs from the legal minimum (7 days) to improve customer satisfaction.
// See: Business Policy Document v3.2, Section 4.1
int refundWindow = user.IsPremium ? 30 : 14;

// Calculate late fee: $5 per day, capped at 50% of original amount.
// Cap prevents fees from exceeding loan value (legal requirement in CA).
decimal lateFee = Math.Min(daysLate * 5m, originalAmount * 0.5m);
```

**Good**: Explains business rule, reasoning, and references
**Bad**: `// Set refund window` (doesn't explain the logic)

### 3. Non-Obvious Implementation Comments

Clarify code that isn't self-explanatory:

```csharp
// Use OrderedDictionary to maintain insertion order for cache eviction policy.
// Dictionary<K,V> would be faster but wouldn't preserve order for LRU implementation.
private readonly OrderedDictionary _cache = new OrderedDictionary();

// Reverse iteration prevents InvalidOperationException during removal.
// Forward iteration with removal would modify collection during enumeration.
for (int i = items.Count - 1; i >= 0; i--)
{
    if (ShouldRemove(items[i]))
    {
        items.RemoveAt(i);
    }
}

// ToList() creates defensive copy to prevent external modification.
// Returning direct reference would violate encapsulation.
public IEnumerable<Item> GetItems() => _items.ToList();
```

**Good**: Explains why approach was chosen and what problem it solves
**Bad**: `// Create new list` (obvious from code)

### 4. Workaround Comments

Document workarounds for bugs or limitations:

```csharp
// WORKAROUND: HttpClient has connection leak in .NET Framework 4.7
// Creating new client per request until we migrate to .NET 6+
// See: https://github.com/dotnet/runtime/issues/12345
// TODO: Remove this workaround after migrating to .NET 6+
using var client = new HttpClient();
var response = await client.GetAsync(url);

// HACK: Delay 100ms to avoid race condition in third-party API.
// Their rate limiter returns 429 even when we're under the limit if
// requests arrive too close together. Reported to vendor 2024-01-15.
await Task.Delay(100);

// EF Core 3.1 doesn't support GroupBy with multiple keys in memory.
// Using ToList() to force client-side evaluation as workaround.
// TODO: Remove when upgrading to EF Core 5.0+ with improved GroupBy support
var grouped = items.ToList()
    .GroupBy(x => new { x.Category, x.Type });
```

**Good**: Explains issue, links to tracking, includes TODO for removal
**Bad**: `// Wait a bit` (doesn't explain why)

### 5. Performance-Critical Comments

Explain optimization decisions:

```csharp
// Cache results because recalculation is expensive (O(n²) complexity).
// Cache invalidated on data updates via event handler.
// Memory impact: ~10MB for typical dataset of 10k items.
private readonly ConcurrentDictionary<string, Statistics> _statisticsCache = new();

public Statistics CalculateStatistics(List<Data> data)
{
    string key = GenerateCacheKey(data);
    return _statisticsCache.GetOrAdd(key, _ => ComputeExpensiveStatistics(data));
}

// Use StringBuilder for string concatenation in loop to avoid O(n²) complexity.
// String concatenation with + creates new string object on each iteration.
// StringBuilder reduces time from ~500ms to ~5ms for 10k iterations.
var result = new StringBuilder(initialCapacity);
foreach (var item in items)
{
    result.Append(item).Append(delimiter);
}

// Lazy<T> ensures thread-safe initialization with single instantiation.
// Avoids explicit locking overhead while guaranteeing singleton semantics.
// LazyThreadSafetyMode.ExecutionAndPublication prevents race conditions.
private readonly Lazy<ExpensiveService> _service = new(
    () => new ExpensiveService(),
    LazyThreadSafetyMode.ExecutionAndPublication);
```

**Good**: Explains performance trade-offs and constraints
**Bad**: `// Use cache for speed` (obvious, lacks detail)

### 6. Security-Sensitive Comments

Document security considerations:

```csharp
// Security: Use parameterized queries to prevent SQL injection attacks.
// User input must NEVER be concatenated directly into SQL strings.
using var command = new SqlCommand("SELECT * FROM Users WHERE Id = @id", connection);
command.Parameters.AddWithValue("@id", userId);

// Constant-time comparison prevents timing attacks that could
// leak information about the correct token value.
// String equality returns early on mismatch, leaking length information.
if (CryptographicOperations.FixedTimeEquals(
    Encoding.UTF8.GetBytes(providedToken),
    Encoding.UTF8.GetBytes(expectedToken)))
{
    GrantAccess();
}

// Clear sensitive data from memory immediately after use.
// Prevents sensitive data from lingering in managed heap.
// Use SecureString or zero-fill arrays for passwords.
var password = GetPasswordFromUser();
try
{
    Authenticate(password);
}
finally
{
    Array.Clear(password, 0, password.Length);
}
```

**Good**: Explains security reasoning
**Bad**: `// Check credentials` (misses security implication)

### 7. Thread Safety and Async Comments

Explain concurrency and async patterns:

```csharp
// Thread-safe using lock on dedicated object.
// Lock granularity is per-account to allow concurrent access to different accounts.
// Fine-grained locking improves throughput by ~300% compared to global lock.
private readonly object _lockObject = new();

public void UpdateBalance(Account account, decimal amount)
{
    lock (account.Lock)
    {
        account.Balance += amount;
    }
}

// ConcurrentDictionary ensures thread-safe dictionary operations without explicit locking.
// Lock-free for reads, optimistic locking for writes provides better performance.
// Throughput improves from 10k to 100k ops/sec under high contention.
private readonly ConcurrentDictionary<string, Value> _cache = new();

// ConfigureAwait(false) prevents deadlock in UI applications.
// By default, await resumes on captured SynchronizationContext (UI thread).
// Library code should always use ConfigureAwait(false) to avoid blocking UI.
var result = await FetchDataAsync().ConfigureAwait(false);

// SemaphoreSlim limits concurrent API requests to prevent rate limiting.
// Third-party API allows max 10 concurrent connections per account.
// Exceeding limit results in 429 errors and exponential backoff.
private static readonly SemaphoreSlim _rateLimiter = new(10, 10);

public async Task<Response> CallApiAsync()
{
    await _rateLimiter.WaitAsync();
    try
    {
        return await _httpClient.GetAsync(url);
    }
    finally
    {
        _rateLimiter.Release();
    }
}

// Task.Run offloads CPU-intensive work to thread pool.
// Prevents blocking async pipeline with synchronous computation.
// For I/O operations, use native async methods instead (don't use Task.Run).
var result = await Task.Run(() => ExpensiveCpuBoundOperation(data));
```

**Good**: Explains async/threading patterns and reasoning
**Bad**: `// Use lock` (obvious from keyword)

### 8. LINQ and Query Comments

Explain complex queries and performance considerations:

```csharp
// Use AsNoTracking for read-only queries to improve performance.
// EF Core change tracking has ~40% overhead for large result sets.
// Only use tracking when entities will be modified and saved.
var users = await context.Users
    .AsNoTracking()
    .Where(u => u.IsActive)
    .ToListAsync();

// Split into multiple queries to avoid cartesian explosion.
// Single query with multiple includes creates O(n×m×k) result set.
// Separate queries reduce from 100k rows to 1k+1k+1k = 3k rows.
var orders = await context.Orders.Where(o => o.UserId == userId).ToListAsync();
var items = await context.OrderItems.Where(i => orderIds.Contains(i.OrderId)).ToListAsync();

// Use Any() instead of Count() > 0 for existence checks.
// Any() short-circuits on first match (O(1) best case).
// Count() always scans entire collection (O(n)).
if (items.Any(x => x.IsExpired))
{
    // ...
}

// Materialize with ToList() before complex in-memory operations.
// EF Core can't translate complex expressions to SQL.
// Client evaluation warning indicates query should be split.
var results = await context.Products
    .Where(p => p.Category == category)
    .ToListAsync();  // Materialize before complex operation

var processed = results
    .Select(p => ComplexTransformation(p))  // Client-side only
    .ToList();
```

**Good**: Explains query optimization and performance implications
**Bad**: `// Query database` (obvious from code)

### 9. IDisposable and Resource Management Comments

Explain resource management decisions:

```csharp
// Implement IDisposable to release unmanaged resources (file handle).
// Without proper disposal, file remains locked until GC finalizes object.
// Follow dispose pattern to support both deterministic and non-deterministic cleanup.
public class FileProcessor : IDisposable
{
    private FileStream _fileStream;
    private bool _disposed;

    public void Dispose()
    {
        Dispose(true);
        GC.SuppressFinalize(this);  // Prevent finalizer from running
    }

    protected virtual void Dispose(bool disposing)
    {
        if (_disposed) return;

        if (disposing)
        {
            // Dispose managed resources
            _fileStream?.Dispose();
        }

        // Free unmanaged resources
        // ...

        _disposed = true;
    }
}

// Using statement ensures deterministic disposal even on exception.
// Resource guaranteed to be released when leaving scope.
// Equivalent to try-finally but more concise and less error-prone.
using (var connection = new SqlConnection(connectionString))
{
    await connection.OpenAsync();
    // ... use connection
}  // Dispose() called here automatically
```

**Good**: Explains resource management reasoning
**Bad**: `// Dispose resources` (obvious from IDisposable)

### 10. TODO/FIXME/HACK Conventions

Use standardized tags for technical debt:

```csharp
// TODO: Refactor this into separate validation service (target: v2.1)
// Current implementation works but violates single responsibility principle.
// Estimate: 4 hours
public void ProcessAndValidate(Data data)
{
    // ...
}

// FIXME: Race condition when multiple threads process same job.
// Occurs under high load (>1000 jobs/second). Need distributed lock.
// Priority: HIGH - Causes duplicate processing ~0.1% of time
// Assigned to: @username, Issue #456
public void ProcessJob(string jobId)
{
    // ...
}

// HACK: Temporary workaround for memory leak in library v2.3
// Remove this when upgrading to v2.4+ which has the fix.
// See: https://github.com/project/issues/123
GC.Collect();  // Force garbage collection as workaround

// NOTE: This method must be called after context initialization.
// Order dependency: database connection must be established first.
public void Configure()
{
    // ...
}

// WARNING: Modifying this constant will break backward compatibility.
// Value is hardcoded in legacy clients (v1.x).
// Cannot change until all clients upgrade to v2.0+.
private const int ProtocolVersion = 1;
```

**Format**: `TAG: Description (context)`
- **TODO**: Planned improvement or feature
- **FIXME**: Known bug or issue
- **HACK**: Temporary workaround
- **NOTE**: Important information
- **WARNING**: Critical caution

### 11. Inline Comments (Use Sparingly)

Reserve inline comments for truly non-obvious code:

```csharp
// Good inline comment - explains non-obvious detail
int result = value & 0xFF;  // Mask to get only the last byte

// Bad inline comment - obvious from code
count++;  // Increment count

// Good inline comment - explains magic number
const long timeout = 86400000L;  // 24 hours in milliseconds

// Bad inline comment - should be named constant
long timeout = 86400000L;  // Timeout value
// Better: Use named constant
private const long MillisecondsPerDay = 86400000L;
long timeout = MillisecondsPerDay;

// Good inline comment - explains regex pattern
var pattern = new Regex(@"^[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}$");  // RFC 5322 email format
```

### 12. XML Documentation vs. Inline Comments

**XML docs for API documentation, inline comments for implementation details:**

```csharp
/// <summary>
/// Process user payment with fraud detection.
/// </summary>
/// <param name="payment">Payment details including amount, currency, and card info</param>
/// <returns>Payment confirmation with transaction ID</returns>
/// <exception cref="ValidationException">Payment data is invalid</exception>
/// <exception cref="FraudException">Payment fails fraud checks</exception>
/// <remarks>
/// All amounts are in cents. This method validates the payment, performs fraud checks,
/// and processes the transaction through the payment gateway.
/// </remarks>
public async Task<PaymentResult> ProcessPaymentAsync(Payment payment)
{
    // Use Luhn algorithm to validate card number before API call.
    // Prevents unnecessary API charges for invalid cards (~15% of attempts).
    if (!IsValidCardNumber(payment.CardNumber))
    {
        throw new ValidationException("Invalid card number");
    }

    // 3D Secure required for EU transactions over €30 (PSD2 compliance).
    // US transactions always skip 3DS for better conversion rates.
    bool requires3DS = payment.Currency == "EUR" && payment.Amount > 3000;

    return await _paymentGateway.ChargeAsync(payment, requires3DS);
}
```

**XML docs**: What the method does, parameters, return values, exceptions
**Inline comments**: Why implementation choices were made

### 13. What NOT to Comment

**Avoid these comment anti-patterns:**

```csharp
// BAD: Obvious comments
// Set x to 5
int x = 5;

// BAD: Redundant with method name
// Calculate total
public decimal CalculateTotal()
{
    // ...
}

// BAD: Meta-commentary about code changes
// Changed this from += to = on 2024-01-15
// Fixed bug here
// Updated by John

// BAD: Commented-out code (use version control instead)
// OldMethod();
// return previousValue;

// BAD: Duplicating XML documentation
/// <summary>
/// Calculate total price.
/// </summary>
public decimal CalculateTotal(List<Item> items)
{
    // Calculate total price
    return items.Sum(item => item.Price);
}

// BAD: Vague or unhelpful
// Do stuff
// Handle things
// Process data
```

## Phase 3: Comment Placement Guidelines

### Block Comments
```csharp
// Use block comments before code blocks they describe.
// Separate from previous code with blank line.
// Keep lines under 80 characters.

public void MyMethod()
{
    // Block comments inside methods go before the relevant section
    // with proper indentation.
    CodeSection();
}
```

### Inline Comments
```csharp
// Place inline comments sparingly, separated by at least 2 spaces
var result = ComplexCalculation();  // Explanation when truly needed
```

### Section Dividers
```csharp
// ===== Data Processing Section =====
// Use sparingly for major logical sections in long classes

// ----- Helper Methods -----
// Or use simpler dividers for subsections
```

## Phase 4: Comment Quality Review

### Self-Review Checklist
For each comment, verify:

1. **Adds Value**
   - Would a competent developer understand the code without it?
   - If yes, consider removing the comment
   - If no, is the comment clear enough to help?

2. **Explains "Why" Not "What"**
   - Bad: "Loop through items" (what)
   - Good: "Reverse loop to avoid InvalidOperationException" (why)

3. **Is Accurate and Current**
   - Does comment match current code behavior?
   - Is referenced information still valid?
   - Are linked issues/docs still relevant?

4. **Is Concise**
   - Can you say the same thing in fewer words?
   - Are you repeating information from XML docs or type declarations?
   - Is every sentence necessary?

5. **Is Properly Formatted**
   - Correct grammar and spelling
   - Proper indentation
   - Follows project conventions

## Phase 5: Refactoring vs. Commenting

Sometimes improving code readability is better than adding comments:

### When to Refactor Instead of Comment

```csharp
// BAD: Comment explaining complex logic
// Calculate discount: 10% for orders > $100, 5% for > $50, 0% otherwise
decimal discount = total > 100m ? 0.10m : (total > 50m ? 0.05m : 0m);

// GOOD: Extract to well-named method (self-documenting)
public decimal CalculateDiscount(decimal total)
{
    if (total > 100m) return 0.10m;
    if (total > 50m) return 0.05m;
    return 0m;
}

// BAD: Comment explaining magic number
decimal result = value * 1.07m;  // Apply sales tax

// GOOD: Named constant (self-documenting)
private const decimal SalesTaxRate = 1.07m;
decimal result = value * SalesTaxRate;

// BAD: Comment explaining complex condition
if (user.Age >= 18 && user.HasLicense && !user.HasViolations)
{
    // User is eligible to rent
}

// GOOD: Extract to well-named method
if (IsEligibleToRent(user))
{
    // ...
}
```

## Phase 6: Comment Maintenance

### Keeping Comments Current

1. **Update Comments with Code Changes**
   - When refactoring, review and update affected comments
   - Remove outdated TODO/FIXME when resolved
   - Update references to issues, docs, or external resources

2. **Regular Comment Audits**
   - Review comments during code reviews
   - Flag outdated or incorrect comments
   - Remove or update as needed

3. **Version Control Integration**
   ```bash
   # Find TODO comments
   grep -r "TODO" src/

   # Find FIXME comments
   grep -r "FIXME" src/

   # Track technical debt with tools:
   # - StyleCop analyzers
   # - SonarQube/SonarLint
   # - Custom Roslyn analyzers
   ```

## Output Format

Please provide comment additions in this format:

### File-by-File Report
```markdown
## File: src/Services/UserService.cs

### Line 45: Complex Algorithm Comment
**Code Section**:
```csharp
[relevant code]
```

**Added Comment**:
```csharp
// [strategic comment explaining why/how]
[code]
```

**Rationale**: Explains [specific aspect] that isn't obvious from code alone.

---

### Line 78: Business Logic Comment
[Similar format]

---
```

### Summary Report
```markdown
## Comment Addition Summary

**Files Processed**: [count]
**Comments Added**: [count]
**Comment Types**:
- Complex algorithm: [count]
- Business logic: [count]
- Non-obvious implementation: [count]
- Workarounds: [count]
- Performance notes: [count]
- Security considerations: [count]
- Thread safety/async: [count]
- LINQ/query optimization: [count]
- Resource management: [count]
- TODO/FIXME/HACK: [count]

**Comments Removed** (redundant/outdated): [count]
**Comments Updated**: [count]

**Code Improvements** (refactored instead of commented): [count]

**Quality Metrics**:
- Average comment value rating: [High/Medium/Low]
- Comments explaining "why": [X%]
- Comments with context/references: [X%]
```

## Best Practices Summary

1. **Comment the Why, Not the What**
   - Code shows what happens
   - Comments explain why this approach

2. **Self-Documenting Code First**
   - Use clear names
   - Extract complex logic to named methods
   - Only comment what can't be made obvious

3. **Keep Comments Current**
   - Update with code changes
   - Remove obsolete comments
   - Review during code reviews

4. **Be Concise**
   - Every word should add value
   - Avoid redundancy with XML docs
   - Get to the point quickly

5. **Provide Context**
   - Link to issues, docs, or decisions
   - Explain trade-offs and constraints
   - Note related code sections

6. **Use Standard Tags**
   - TODO: Planned improvements
   - FIXME: Known bugs
   - HACK: Temporary workarounds
   - NOTE: Important information
   - WARNING: Critical cautions

## Tools for Comment Quality

```yaml
# Recommended tools
tools:
  - stylecop:
      # Enforce comment standards
      # Check XML documentation

  - sonarqube:
      # Technical debt tracking
      # Comment quality metrics

  - roslyn-analyzers:
      # Custom comment rules
      # Track TODO/FIXME patterns

  - grep/ripgrep:
      # Find technical debt tags
      patterns:
        - "TODO"
        - "FIXME"
        - "HACK"
        - "NOTE"
        - "WARNING"
```

## Common Mistakes to Avoid

1. **Don't Explain Obvious Code**
   ```csharp
   // BAD
   int count = 0;  // Initialize count to zero

   // GOOD (no comment needed - obvious from code)
   int count = 0;
   ```

2. **Don't Duplicate XML Documentation**
   ```csharp
   // BAD
   /// <summary>
   /// Calculate total price of items.
   /// </summary>
   public decimal CalculateTotal(List<Item> items)
   {
       // Calculate total price of items
       return items.Sum(item => item.Price);
   }

   // GOOD
   /// <summary>
   /// Calculate total price of items.
   /// </summary>
   public decimal CalculateTotal(List<Item> items)
   {
       return items.Sum(item => item.Price);
   }
   ```

3. **Don't Leave Commented-Out Code**
   ```csharp
   // BAD
   // OldImplementation();
   // PreviousApproach();
   NewImplementation();

   // GOOD (use version control)
   NewImplementation();
   ```

4. **Don't Write Vague Comments**
   ```csharp
   // BAD: "Handle edge case"
   // BAD: "Fix issue here"
   // BAD: "Do special processing"

   // GOOD: Specific and informative
   // Handle empty list to prevent InvalidOperationException in Min() operation
   ```

5. **Don't Forget to Update Comments**
   - Comments that contradict code are worse than no comments
   - Review comments during every code change
   - Remove comments that no longer apply

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/comments/generated_docs
mkdir -p ${OUTPUT_DIR}/comments/templates
mkdir -p ${OUTPUT_DIR}/comments/assets
mkdir -p ${OUTPUT_DIR}/comments/exports
```

**Save files as follows**:


- Templates → `documentation/comments/templates/`

- Assets → `documentation/comments/assets/`

- Exports → `documentation/comments/exports/`

Replace `{phase_name}` with the specific phase (docstrings, comments, user_docs, technical_docs, api_docs, or sbom).

~~~

## Output Format Specifications

The strategic comments should:
- Explain "why" decisions were made, not "what" the code does
- Be concise yet informative (typically 1-3 lines)
- Include context, references, or trade-offs where relevant
- Use proper formatting and indentation
- Follow team conventions for TODO/FIXME/HACK tags
- Add genuine value that can't be conveyed through code structure
- Be maintained and updated as code evolves
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
