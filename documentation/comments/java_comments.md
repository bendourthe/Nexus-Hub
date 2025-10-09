# Java Strategic Comments

## Objective
Add strategic, high-value comments that explain "why" rather than "what", focusing on business logic, design decisions, non-obvious implementations, and workarounds while avoiding redundant commentary.

## Output Directory Structure

All documentation outputs should be saved in organized directories:

```
documentation/
└── comments/
    ├── generated_docs/
    ├── templates/
    ├── assets/
    └── exports/
```

**Directory Setup**:
- Create `documentation/` directory in repository root if it doesn't exist
- Create `documentation/comments/` subdirectory for this documentation phase
- All documentation files, templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:
- `generated_docs/` - Generated documentation files (HTML, MD, PDF)
- `templates/` - Documentation templates and examples
- `assets/` - Images, diagrams, supplementary files
- `exports/` - Published documentation, release artifacts

## Implementation Checklist

### When to Comment
- [ ] Complex algorithms requiring explanation
- [ ] Business logic and domain rules
- [ ] Non-obvious code decisions
- [ ] Workarounds for bugs in dependencies
- [ ] Performance-critical sections
- [ ] Security-sensitive code
- [ ] Thread safety considerations
- [ ] Exception handling rationale

### When NOT to Comment
- [ ] Obvious code that's self-explanatory
- [ ] Information already in Javadoc
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
# Java Strategic Comments Request

Please add strategic comments to this Java project following this protocol:

## Phase 1: Analysis & Comment Identification

1. **Analyze Codebase for Comment Opportunities**
   Review the code to identify sections that would benefit from comments:
   - Complex algorithms or business logic
   - Non-obvious implementation decisions
   - Workarounds for known issues
   - Performance-critical sections
   - Security-sensitive operations
   - Thread safety and concurrency patterns
   - Exception handling strategies
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

```java
/**
 * Calculate optimal route using A* pathfinding algorithm.
 * We use A* instead of Dijkstra because our graph has a reliable heuristic
 * (Euclidean distance), which reduces search time by ~40% in testing.
 * Trade-off: Uses more memory (O(n) vs O(log n)) but acceptable for our
 * typical graph sizes (<1000 nodes).
 */
public Route findOptimalRoute(Node start, Node end, Graph graph) {
    Set<Node> openSet = new HashSet<>(Collections.singletonList(start));
    Map<Node, Node> cameFrom = new HashMap<>();
    // ... implementation
}
```

**Good**: Explains algorithm choice, trade-offs, and why it's appropriate
**Bad**: `// Find route` (obvious from method name)

### 2. Business Logic Comments

Document domain rules and business decisions:

```java
// Business rule: Premium users get 30-day refund window, standard users get 14 days.
// This differs from the legal minimum (7 days) to improve customer satisfaction.
// See: Business Policy Document v3.2, Section 4.1
int refundWindow = user.isPremium() ? 30 : 14;

// Calculate late fee: $5 per day, capped at 50% of original amount.
// Cap prevents fees from exceeding loan value (legal requirement in CA).
BigDecimal lateFee = BigDecimal.valueOf(daysLate)
    .multiply(BigDecimal.valueOf(5))
    .min(originalAmount.multiply(BigDecimal.valueOf(0.5)));
```

**Good**: Explains business rule, reasoning, and references
**Bad**: `// Set refund window` (doesn't explain the logic)

### 3. Non-Obvious Implementation Comments

Clarify code that isn't self-explanatory:

```java
// Use LinkedHashMap to maintain insertion order for cache eviction policy.
// HashMap would be faster but wouldn't preserve order for LRU implementation.
private Map<String, CachedValue> cache = new LinkedHashMap<>(16, 0.75f, true);

// Reverse iteration prevents ConcurrentModificationException.
// Forward iteration with removal would modify list during iteration.
for (int i = items.size() - 1; i >= 0; i--) {
    if (shouldRemove(items.get(i))) {
        items.remove(i);
    }
}

// Clone list to prevent external modification affecting internal state.
// Direct assignment would share reference, violating encapsulation.
this.items = new ArrayList<>(items);
```

**Good**: Explains why approach was chosen and what problem it solves
**Bad**: `// Create new list` (obvious from code)

### 4. Workaround Comments

Document workarounds for bugs or limitations:

```java
// WORKAROUND: Apache HttpClient has connection leak in version 4.5.x
// Creating new client instance for each request until fixed in 5.0.
// See: https://issues.apache.org/jira/browse/HTTPCLIENT-2089
// TODO: Remove this workaround after upgrading to HttpClient 5.0+
CloseableHttpClient client = HttpClients.createDefault();
try {
    HttpResponse response = client.execute(request);
    // ... process response
} finally {
    client.close();
}

// HACK: Sleep 100ms to avoid race condition in third-party API.
// Their rate limiter returns 429 even when we're under the limit if
// requests arrive too close together. Reported to vendor 2024-01-15.
Thread.sleep(100);

// JDK 8 doesn't have List.of(), using Arrays.asList() as fallback.
// TODO: Replace with List.of() when upgrading to JDK 11+
List<String> items = Arrays.asList("item1", "item2", "item3");
```

**Good**: Explains issue, links to tracking, includes TODO for removal
**Bad**: `// Wait a bit` (doesn't explain why)

### 5. Performance-Critical Comments

Explain optimization decisions:

```java
// Cache results because recalculation is expensive (O(n²) complexity).
// Cache invalidated on data updates via event listener.
// Memory impact: ~10MB for typical dataset of 10k items.
private final Map<String, Statistics> statisticsCache = new ConcurrentHashMap<>();

public Statistics calculateStatistics(List<Data> data) {
    String key = generateCacheKey(data);
    return statisticsCache.computeIfAbsent(key, k -> computeExpensiveStatistics(data));
}

// Use StringBuilder for string concatenation in loop to avoid O(n²) complexity.
// String concatenation with + creates new String object on each iteration.
// StringBuilder reduces time from ~500ms to ~5ms for 10k iterations.
StringBuilder result = new StringBuilder(initialCapacity);
for (String item : items) {
    result.append(item).append(delimiter);
}

// Lazy initialization using double-checked locking pattern.
// Volatile ensures visibility of singleton instance across threads.
// Reduces lock contention by only synchronizing on first access.
private volatile ExpensiveObject instance;

public ExpensiveObject getInstance() {
    if (instance == null) {
        synchronized (this) {
            if (instance == null) {
                instance = new ExpensiveObject();
            }
        }
    }
    return instance;
}
```

**Good**: Explains performance trade-offs and constraints
**Bad**: `// Use cache for speed` (obvious, lacks detail)

### 6. Security-Sensitive Comments

Document security considerations:

```java
// Security: Use PreparedStatement to prevent SQL injection attacks.
// User input must NEVER be concatenated directly into SQL strings.
String sql = "SELECT * FROM users WHERE id = ?";
try (PreparedStatement stmt = connection.prepareStatement(sql)) {
    stmt.setLong(1, userId);
    ResultSet rs = stmt.executeQuery();
    // ... process results
}

// Constant-time comparison prevents timing attacks that could
// leak information about the correct token value.
// String.equals() returns early on mismatch, leaking length information.
if (MessageDigest.isEqual(
        providedToken.getBytes(StandardCharsets.UTF_8),
        expectedToken.getBytes(StandardCharsets.UTF_8))) {
    grantAccess();
}

// Clear sensitive data from memory immediately after use.
// Prevents sensitive data from lingering in heap during garbage collection.
// Use char[] instead of String because String is immutable and can't be cleared.
char[] password = getPasswordFromUser();
try {
    authenticate(password);
} finally {
    Arrays.fill(password, '\0');  // Overwrite with zeros
}
```

**Good**: Explains security reasoning
**Bad**: `// Check credentials` (misses security implication)

### 7. Thread Safety Comments

Explain concurrency considerations:

```java
// Thread-safe using synchronization on shared state.
// Lock granularity is per-account to allow concurrent access to different accounts.
// Fine-grained locking improves throughput by ~300% compared to global lock.
public synchronized void updateBalance(Account account, BigDecimal amount) {
    synchronized (account) {
        account.setBalance(account.getBalance().add(amount));
    }
}

// AtomicInteger ensures thread-safe counter without explicit locking.
// Lock-free algorithm provides better performance under high contention.
// CAS operations avoid blocking, improving throughput from 10k to 100k ops/sec.
private final AtomicInteger counter = new AtomicInteger(0);

// CopyOnWriteArrayList used because reads vastly outnumber writes (99:1 ratio).
// Trade-off: Writes are expensive (O(n) copy) but reads are lock-free.
// Regular ArrayList with synchronization would cause contention on frequent reads.
private final List<Observer> observers = new CopyOnWriteArrayList<>();

// volatile ensures visibility of flag changes across threads.
// Without volatile, thread may never see updated value due to CPU caching.
// Note: volatile alone doesn't guarantee atomicity for compound operations.
private volatile boolean shutdownRequested = false;
```

**Good**: Explains thread safety approach and trade-offs
**Bad**: `// Synchronized method` (obvious from keyword)

### 8. Exception Handling Comments

Explain error handling strategies:

```java
// Catch broad Exception here because plugin can throw any exception type.
// Log and continue to prevent one bad plugin from crashing entire system.
// Each plugin runs in isolation for fault tolerance.
for (Plugin plugin : plugins) {
    try {
        plugin.execute();
    } catch (Exception e) {
        logger.error("Plugin {} failed: {}", plugin.getName(), e.getMessage(), e);
        // Continue processing other plugins
    }
}

// Rethrowing as RuntimeException because checked exceptions break interface contract.
// IOException is implementation detail that shouldn't leak to callers.
// Original cause preserved for debugging via exception chaining.
try {
    return processFile(file);
} catch (IOException e) {
    throw new ProcessingException("Failed to process file: " + file, e);
}

// Suppress exception because cleanup failure shouldn't mask original error.
// Original exception propagated; cleanup exception logged separately.
try {
    processResource(resource);
} finally {
    try {
        resource.close();
    } catch (IOException e) {
        logger.warn("Failed to close resource: {}", e.getMessage());
        // Don't throw - original exception takes precedence
    }
}
```

**Good**: Explains exception handling strategy and reasoning
**Bad**: `// Catch exception` (obvious from code)

### 9. TODO/FIXME/HACK Conventions

Use standardized tags for technical debt:

```java
// TODO: Refactor this into separate validation service (target: v2.1)
// Current implementation works but violates single responsibility principle.
// Estimate: 4 hours
public void processAndValidate(Data data) {
    // ...
}

// FIXME: Race condition when multiple threads process same job.
// Occurs under high load (>1000 jobs/second). Need distributed lock.
// Priority: HIGH - Causes duplicate processing ~0.1% of time
// Assigned to: @username, Issue JIRA-456
public void processJob(String jobId) {
    // ...
}

// HACK: Temporary workaround for memory leak in library v2.3
// Remove this when upgrading to v2.4+ which has the fix.
// See: https://github.com/project/issues/123
System.gc();  // Force garbage collection as workaround

// NOTE: This method must be called before initialization.
// Order dependency: database connection must be established first.
public void configure() {
    // ...
}

// WARNING: Modifying this constant will break backward compatibility.
// Value is hardcoded in legacy clients (v1.x).
// Cannot change until all clients upgrade to v2.0+.
private static final int PROTOCOL_VERSION = 1;
```

**Format**: `TAG: Description (context)`
- **TODO**: Planned improvement or feature
- **FIXME**: Known bug or issue
- **HACK**: Temporary workaround
- **NOTE**: Important information
- **WARNING**: Critical caution

### 10. Inline Comments (Use Sparingly)

Reserve inline comments for truly non-obvious code:

```java
// Good inline comment - explains non-obvious detail
int result = value & 0xFF;  // Mask to get only the last byte

// Bad inline comment - obvious from code
count++;  // Increment count

// Good inline comment - explains magic number
long timeout = 86400000L;  // 24 hours in milliseconds

// Bad inline comment - should be constant
long timeout = 86400000L;  // Timeout value
// Better: Define constant
private static final long MILLISECONDS_PER_DAY = 86400000L;
long timeout = MILLISECONDS_PER_DAY;

// Good inline comment - explains regex pattern
Pattern pattern = Pattern.compile("^[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,6}$",
    Pattern.CASE_INSENSITIVE);  // RFC 5322 email format
```

### 11. Javadoc vs. Inline Comments

**Javadoc for API documentation, inline comments for implementation details:**

```java
/**
 * Process user payment with fraud detection.
 * <p>
 * This method validates the payment, performs fraud checks, and processes
 * the transaction through the payment gateway. All amounts are in cents.
 *
 * @param payment Payment details including amount, currency, and card info
 * @return Payment confirmation with transaction ID
 * @throws ValidationException if payment data is invalid
 * @throws FraudException if payment fails fraud checks
 * @throws PaymentException if payment processing fails
 */
public PaymentResult processPayment(Payment payment)
        throws ValidationException, FraudException, PaymentException {

    // Use Luhn algorithm to validate card number before API call.
    // Prevents unnecessary API charges for invalid cards (~15% of attempts).
    if (!isValidCardNumber(payment.getCardNumber())) {
        throw new ValidationException("Invalid card number");
    }

    // 3D Secure required for EU transactions over €30 (PSD2 compliance).
    // US transactions always skip 3DS for better conversion rates.
    boolean requires3DS = "EUR".equals(payment.getCurrency())
        && payment.getAmount() > 3000;

    return paymentGateway.charge(payment, requires3DS);
}
```

**Javadoc**: What the method does, parameters, return values, exceptions
**Inline comments**: Why implementation choices were made

### 12. What NOT to Comment

**Avoid these comment anti-patterns:**

```java
// BAD: Obvious comments
// Set x to 5
int x = 5;

// BAD: Redundant with method name
// Calculate total
public BigDecimal calculateTotal() {
    // ...
}

// BAD: Meta-commentary about code changes
// Changed this from += to = on 2024-01-15
// Fixed bug here
// Updated by John

// BAD: Commented-out code (use version control instead)
// oldMethod();
// return previousValue;

// BAD: Duplicating Javadoc
/**
 * Calculate total price.
 */
public BigDecimal calculateTotal(List<Item> items) {
    // Calculate total price
    return items.stream()
        .map(Item::getPrice)
        .reduce(BigDecimal.ZERO, BigDecimal::add);
}

// BAD: Vague or unhelpful
// Do stuff
// Handle things
// Process data
```

## Phase 3: Comment Placement Guidelines

### Block Comments
```java
// Use block comments before code blocks they describe.
// Separate from previous code with blank line.
// Keep lines under 80 characters.

public void myMethod() {
    // Block comments inside methods go before the relevant section
    // with proper indentation.
    codeSection();
}
```

### Inline Comments
```java
// Place inline comments sparingly, separated by at least 2 spaces
int result = complexCalculation();  // Explanation when truly needed
```

### Section Dividers
```java
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
   - Good: "Reverse loop to avoid ConcurrentModificationException" (why)

3. **Is Accurate and Current**
   - Does comment match current code behavior?
   - Is referenced information still valid?
   - Are linked issues/docs still relevant?

4. **Is Concise**
   - Can you say the same thing in fewer words?
   - Are you repeating information from Javadoc or type declarations?
   - Is every sentence necessary?

5. **Is Properly Formatted**
   - Correct grammar and spelling
   - Proper indentation
   - Follows project conventions

## Phase 5: Refactoring vs. Commenting

Sometimes improving code readability is better than adding comments:

### When to Refactor Instead of Comment

```java
// BAD: Comment explaining complex logic
// Calculate discount: 10% for orders > $100, 5% for > $50, 0% otherwise
BigDecimal discount = total.compareTo(new BigDecimal("100")) > 0
    ? new BigDecimal("0.10")
    : (total.compareTo(new BigDecimal("50")) > 0
        ? new BigDecimal("0.05")
        : BigDecimal.ZERO);

// GOOD: Extract to well-named method (self-documenting)
public BigDecimal calculateDiscount(BigDecimal total) {
    if (total.compareTo(new BigDecimal("100")) > 0) {
        return new BigDecimal("0.10");
    } else if (total.compareTo(new BigDecimal("50")) > 0) {
        return new BigDecimal("0.05");
    }
    return BigDecimal.ZERO;
}

// BAD: Comment explaining magic number
BigDecimal result = value.multiply(new BigDecimal("1.07"));  // Apply sales tax

// GOOD: Named constant (self-documenting)
private static final BigDecimal SALES_TAX_RATE = new BigDecimal("1.07");
BigDecimal result = value.multiply(SALES_TAX_RATE);

// BAD: Comment explaining complex condition
if (user.getAge() >= 18 && user.hasLicense() && !user.hasViolations()) {
    // User is eligible to rent
}

// GOOD: Extract to well-named method
if (isEligibleToRent(user)) {
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
   # - Checkstyle custom checks
   # - SonarQube technical debt tracking
   # - Custom Maven/Gradle plugins
   ```

## Output Format

Please provide comment additions in this format:

### File-by-File Report
```markdown
## File: src/main/java/com/example/UserService.java

### Line 45: Complex Algorithm Comment
**Code Section**:
```java
[relevant code]
```

**Added Comment**:
```java
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
- Thread safety: [count]
- Exception handling: [count]
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
   - Avoid redundancy with Javadoc
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
  - checkstyle:
      # Enforce comment standards
      # Track TODO/FIXME/HACK tags

  - pmd:
      # Detect commented-out code
      # Check comment placement

  - sonarqube:
      # Technical debt tracking
      # Comment quality metrics

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
   ```java
   // BAD
   int count = 0;  // Initialize count to zero

   // GOOD (no comment needed - obvious from code)
   int count = 0;
   ```

2. **Don't Duplicate Javadoc**
   ```java
   // BAD
   /**
    * Calculate total price of items.
    */
   public BigDecimal calculateTotal(List<Item> items) {
       // Calculate total price of items
       return items.stream()
           .map(Item::getPrice)
           .reduce(BigDecimal.ZERO, BigDecimal::add);
   }

   // GOOD
   /**
    * Calculate total price of items.
    */
   public BigDecimal calculateTotal(List<Item> items) {
       return items.stream()
           .map(Item::getPrice)
           .reduce(BigDecimal.ZERO, BigDecimal::add);
   }
   ```

3. **Don't Leave Commented-Out Code**
   ```java
   // BAD
   // oldImplementation();
   // previousApproach();
   newImplementation();

   // GOOD (use version control)
   newImplementation();
   ```

4. **Don't Write Vague Comments**
   ```java
   // BAD: "Handle edge case"
   // BAD: "Fix issue here"
   // BAD: "Do special processing"

   // GOOD: Specific and informative
   // Handle empty list to prevent NoSuchElementException in min() operation
   ```

5. **Don't Forget to Update Comments**
   - Comments that contradict code are worse than no comments
   - Review comments during every code change
   - Remove comments that no longer apply
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
