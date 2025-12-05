---
template_id: go_comments
template_name: Comments - Go
version: 1.0.0
last_updated: 2025-12-03
language: Go
category: documentation
phase: comments
difficulty: beginner
estimated_time_hours: 1-2
prerequisites: []
tools:

  - go test (1.23+)
  - testify
tags:

  - documentation
  - documentation
  - go
---
# Go Strategic Comments

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

- [ ] Concurrency patterns and goroutine management

- [ ] Channel usage and synchronization

- [ ] Interface design decisions

### When NOT to Comment

- [ ] Obvious code that's self-explanatory

- [ ] Information already in package documentation

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
# Go Strategic Comments Request

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

Please add strategic comments to this Go project following this protocol:

## Phase 1: Analysis & Comment Identification

1. **Analyze Codebase for Comment Opportunities**
   Review the code to identify sections that would benefit from comments:

   - Complex algorithms or business logic
   - Non-obvious implementation decisions
   - Workarounds for known issues
   - Performance-critical sections
   - Security-sensitive operations
   - Goroutine management and synchronization
   - Channel patterns and buffering decisions
   - Interface design rationale
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

```go
// FindOptimalRoute calculates optimal route using A* pathfinding algorithm.
// We use A* instead of Dijkstra because our graph has a reliable heuristic
// (Euclidean distance), which reduces search time by ~40% in testing.
// Trade-off: Uses more memory (O(n) vs O(log n)) but acceptable for our
// typical graph sizes (<1000 nodes).
func FindOptimalRoute(start, end Node, graph *Graph) Route {
    openSet := map[Node]bool{start: true}
    cameFrom := make(map[Node]Node)
    // ... implementation
}
```

**Good**: Explains algorithm choice, trade-offs, and why it's appropriate
**Bad**: `// Find route` (obvious from function name)

### 2. Business Logic Comments

Document domain rules and business decisions:

```go
// Business rule: Premium users get 30-day refund window, standard users get 14 days.
// This differs from the legal minimum (7 days) to improve customer satisfaction.
// See: Business Policy Document v3.2, Section 4.1
refundWindow := 30
if !user.IsPremium {
    refundWindow = 14
}

// Calculate late fee: $5 per day, capped at 50% of original amount.
// Cap prevents fees from exceeding loan value (legal requirement in CA).
lateFee := math.Min(float64(daysLate)*5.0, originalAmount*0.5)
```

**Good**: Explains business rule, reasoning, and references
**Bad**: `// Set refund window` (doesn't explain the logic)

### 3. Non-Obvious Implementation Comments

Clarify code that isn't self-explanatory:

```go
// Use sync.Map instead of map with mutex for concurrent access.
// sync.Map optimized for read-heavy workloads (90:10 read:write ratio).
// Trade-off: Slower writes but eliminates lock contention on reads.
var cache sync.Map

// Iterate backwards to avoid slice index shifting during removal.
// Forward iteration with removal would skip elements after each deletion.
for i := len(items) - 1; i >= 0; i-- {
    if shouldRemove(items[i]) {
        items = append(items[:i], items[i+1:]...)
    }
}

// Copy slice to prevent external modification affecting internal state.
// Direct assignment shares underlying array, violating encapsulation.
func (s *Service) GetItems() []Item {
    result := make([]Item, len(s.items))
    copy(result, s.items)
    return result
}
```

**Good**: Explains why approach was chosen and what problem it solves
**Bad**: `// Create copy` (obvious from code)

### 4. Workaround Comments

Document workarounds for bugs or limitations:

```go
// WORKAROUND: github.com/lib/pq has connection leak in v1.10.x
// Creating new connection for each query until fixed in v2.0.
// See: https://github.com/lib/pq/issues/1234
// TODO: Remove this workaround after upgrading to v2.0+
db, err := sql.Open("postgres", connStr)
if err != nil {
    return err
}
defer db.Close()

// HACK: Sleep 100ms to avoid race condition in third-party API.
// Their rate limiter returns 429 even when we're under the limit if
// requests arrive too close together. Reported to vendor 2024-01-15.
time.Sleep(100 * time.Millisecond)

// Go 1.18 doesn't support slices.Contains(), using manual loop as fallback.
// TODO: Replace with slices.Contains() when upgrading to Go 1.21+
func contains(items []string, target string) bool {
    for _, item := range items {
        if item == target {
            return true
        }
    }
    return false
}
```

**Good**: Explains issue, links to tracking, includes TODO for removal
**Bad**: `// Wait a bit` (doesn't explain why)

### 5. Performance-Critical Comments

Explain optimization decisions:

```go
// Cache results because recalculation is expensive (O(n²) complexity).
// Cache invalidated on data updates via channel notification.
// Memory impact: ~10MB for typical dataset of 10k items.
var (
    statisticsCache sync.Map
    cacheMutex      sync.RWMutex
)

func CalculateStatistics(data []Data) Statistics {
    key := generateCacheKey(data)
    if cached, ok := statisticsCache.Load(key); ok {
        return cached.(Statistics)
    }

    result := computeExpensiveStatistics(data)
    statisticsCache.Store(key, result)
    return result
}

// Use strings.Builder for concatenation in loop to avoid O(n²) complexity.
// String concatenation with + creates new string on each iteration.
// Builder reduces time from ~500ms to ~5ms for 10k iterations.
var builder strings.Builder
builder.Grow(len(items) * avgItemLen) // Pre-allocate to avoid reallocations
for _, item := range items {
    builder.WriteString(item)
    builder.WriteString(delimiter)
}

// Use sync.Pool to reuse buffer allocations across requests.
// Reduces GC pressure by ~70% under high load (1M requests/sec).
// Pool automatically scales with concurrency level.
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}
```

**Good**: Explains performance trade-offs and constraints
**Bad**: `// Use cache for speed` (obvious, lacks detail)

### 6. Security-Sensitive Comments

Document security considerations:

```go
// Security: Use parameterized queries to prevent SQL injection attacks.
// User input must NEVER be concatenated directly into SQL strings.
row := db.QueryRow("SELECT * FROM users WHERE id = $1", userID)

// Constant-time comparison prevents timing attacks that could
// leak information about the correct token value.
// bytes.Equal() returns early on mismatch, leaking length information.
if subtle.ConstantTimeCompare(
    []byte(providedToken),
    []byte(expectedToken)) == 1 {
    grantAccess()
}

// Clear sensitive data from memory immediately after use.
// Prevents sensitive data from lingering during garbage collection.
// Zero-fill array to overwrite password bytes.
password := getPasswordFromUser()
defer func() {
    for i := range password {
        password[i] = 0
    }
}()
```

**Good**: Explains security reasoning
**Bad**: `// Check credentials` (misses security implication)

### 7. Concurrency and Goroutine Comments

Explain goroutine management and synchronization:

```go
// Launch worker goroutines with WaitGroup for graceful shutdown.
// Number of workers tuned to match CPU cores for optimal throughput.
// Too many goroutines cause context switching overhead (measured 20% slowdown).
var wg sync.WaitGroup
workerCount := runtime.NumCPU()

for i := 0; i < workerCount; i++ {
    wg.Add(1)
    go func() {
        defer wg.Done()
        processJobs(jobQueue)
    }()
}

wg.Wait() // Block until all workers complete

// Use buffered channel to prevent goroutine blocking on send.
// Buffer size of 100 matches expected burst rate during peak load.
// Unbuffered channel would cause sender goroutines to block, reducing throughput by 60%.
jobQueue := make(chan Job, 100)

// Use context for cancellation propagation across goroutine tree.
// Allows clean shutdown of all child goroutines when parent context cancelled.
// Without context, child goroutines would leak on parent termination.
ctx, cancel := context.WithCancel(context.Background())
defer cancel() // Ensure cancel called to release resources

go func() {
    select {
    case <-ctx.Done():
        // Cleanup and exit
        return
    case job := <-jobQueue:
        processJob(job)
    }
}()

// Use mutex to protect shared state from concurrent access.
// RWMutex would be overkill here as write operations are frequent (50% of ops).
// Benchmark showed regular mutex 15% faster for our access pattern.
type SafeCounter struct {
    mu    sync.Mutex
    count int
}

func (c *SafeCounter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.count++
}
```

**Good**: Explains concurrency patterns and reasoning
**Bad**: `// Use goroutine` (obvious from go keyword)

### 8. Channel Pattern Comments

Explain channel usage and buffering decisions:

```go
// Fan-out pattern: Distribute work across multiple worker goroutines.
// Single producer feeds multiple consumers for parallel processing.
// Improves throughput from 100 to 800 items/sec on 8-core machine.
func fanOut(input <-chan Item, workerCount int) []<-chan Result {
    outputs := make([]<-chan Result, workerCount)

    for i := 0; i < workerCount; i++ {
        outputs[i] = worker(input)
    }

    return outputs
}

// Fan-in pattern: Merge results from multiple channels into one.
// Uses WaitGroup to close output channel after all inputs complete.
// Prevents goroutine leak and enables range loop on output channel.
func fanIn(inputs ...<-chan Result) <-chan Result {
    output := make(chan Result)
    var wg sync.WaitGroup

    for _, input := range inputs {
        wg.Add(1)
        go func(ch <-chan Result) {
            defer wg.Done()
            for result := range ch {
                output <- result
            }
        }(input)
    }

    // Close output channel when all inputs drained
    go func() {
        wg.Wait()
        close(output)
    }()

    return output
}

// Pipeline pattern: Chain operations through channels.
// Each stage processes data and passes to next stage.
// Enables concurrent processing of different pipeline stages.
func pipeline(input <-chan Data) <-chan Result {
    // Stage 1: Validation
    validated := make(chan Data)
    go func() {
        defer close(validated)
        for data := range input {
            if isValid(data) {
                validated <- data
            }
        }
    }()

    // Stage 2: Processing
    processed := make(chan Result)
    go func() {
        defer close(processed)
        for data := range validated {
            processed <- process(data)
        }
    }()

    return processed
}
```

**Good**: Explains channel patterns and their benefits
**Bad**: `// Create channel` (obvious from make())

### 9. Interface Design Comments

Explain interface design decisions:

```go
// Storage interface abstracts persistence layer for testability.
// Allows swapping implementations (in-memory, database, cloud storage)
// without changing business logic. Mocking interface enables unit tests.
type Storage interface {
    Save(key string, value []byte) error
    Load(key string) ([]byte, error)
    Delete(key string) error
}

// Accept interfaces, return structs principle.
// Function accepts interface for flexibility (any Reader implementation).
// Returns concrete type to avoid forcing abstraction on caller.
func ProcessData(r io.Reader) (*Result, error) {
    // ...
}

// Small interfaces are better than large ones (interface segregation).
// Separate concerns: Writer only for write operations, Reader for read.
// Prevents forcing implementers to provide unnecessary methods.
type Writer interface {
    Write(p []byte) (n int, err error)
}

type Reader interface {
    Read(p []byte) (n int, err error)
}
```

**Good**: Explains interface design rationale
**Bad**: `// Storage interface` (obvious from declaration)

### 10. TODO/FIXME/HACK Conventions

Use standardized tags for technical debt:

```go
// TODO: Refactor this into separate validation package (target: v2.1)
// Current implementation works but violates single responsibility principle.
// Estimate: 4 hours
func ProcessAndValidate(data Data) error {
    // ...
}

// FIXME: Race condition when multiple goroutines process same job.
// Occurs under high load (>1000 jobs/second). Need distributed lock.
// Priority: HIGH - Causes duplicate processing ~0.1% of time
// Assigned to: @username, Issue #456
func ProcessJob(jobID string) error {
    // ...
}

// HACK: Temporary workaround for memory leak in library v2.3
// Remove this when upgrading to v2.4+ which has the fix.
// See: https://github.com/project/issues/123
runtime.GC() // Force garbage collection as workaround

// NOTE: This function must be called before initialization.
// Order dependency: database connection must be established first.
func Configure() {
    // ...
}

// WARNING: Modifying this constant will break backward compatibility.
// Value is hardcoded in legacy clients (v1.x).
// Cannot change until all clients upgrade to v2.0+.
const ProtocolVersion = 1
```

**Format**: `TAG: Description (context)`

- **TODO**: Planned improvement or feature

- **FIXME**: Known bug or issue

- **HACK**: Temporary workaround

- **NOTE**: Important information

- **WARNING**: Critical caution

### 11. Inline Comments (Use Sparingly)

Reserve inline comments for truly non-obvious code:

```go
// Good inline comment - explains non-obvious detail
result := value & 0xFF // Mask to get only the last byte

// Bad inline comment - obvious from code
count++ // Increment count

// Good inline comment - explains magic number
const timeout = 86400 * time.Second // 24 hours

// Bad inline comment - should be named constant
timeout := 86400 * time.Second // Timeout value
// Better: Use named constant
const dayDuration = 24 * time.Hour
timeout := dayDuration

// Good inline comment - explains regex pattern
pattern := regexp.MustCompile(`^[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}$`) // RFC 5322 email format
```

### 12. Package Documentation vs. Inline Comments

**Package docs for API documentation, inline comments for implementation details:**

```go
// ProcessPayment processes user payment with fraud detection.
//
// This function validates the payment, performs fraud checks, and processes
// the transaction through the payment gateway. All amounts are in cents.
//
// Returns payment confirmation with transaction ID.
// Returns ValidationError if payment data is invalid.
// Returns FraudError if payment fails fraud checks.
// Returns PaymentError if payment processing fails.
func ProcessPayment(payment Payment) (*PaymentResult, error) {
    // Use Luhn algorithm to validate card number before API call.
    // Prevents unnecessary API charges for invalid cards (~15% of attempts).
    if !isValidCardNumber(payment.CardNumber) {
        return nil, ValidationError{Msg: "Invalid card number"}
    }

    // 3D Secure required for EU transactions over €30 (PSD2 compliance).
    // US transactions always skip 3DS for better conversion rates.
    requires3DS := payment.Currency == "EUR" && payment.Amount > 3000

    return paymentGateway.Charge(payment, requires3DS)
}
```

**Package docs**: What the function does, parameters, return values
**Inline comments**: Why implementation choices were made

### 13. What NOT to Comment

**Avoid these comment anti-patterns:**

```go
// BAD: Obvious comments
// Set x to 5
x := 5

// BAD: Redundant with function name
// Calculate total
func CalculateTotal() float64 {
    // ...
}

// BAD: Meta-commentary about code changes
// Changed this from += to = on 2024-01-15
// Fixed bug here
// Updated by John

// BAD: Commented-out code (use version control instead)
// oldFunction()
// return previousValue

// BAD: Duplicating package documentation
// CalculateTotal calculates total price.
func CalculateTotal(items []Item) float64 {
    // Calculate total price
    total := 0.0
    for _, item := range items {
        total += item.Price
    }
    return total
}

// BAD: Vague or unhelpful
// Do stuff
// Handle things
// Process data
```

## Phase 3: Comment Placement Guidelines

### Block Comments
```go
// Use block comments before code blocks they describe.
// Separate from previous code with blank line.
// Keep lines under 80 characters.

func MyFunction() {
    // Block comments inside functions go before the relevant section
    // with proper indentation.
    codeSection()
}
```

### Inline Comments
```go
// Place inline comments sparingly, separated by at least 2 spaces
result := complexCalculation() // Explanation when truly needed
```

### Section Dividers
```go
// ===== Data Processing Section =====
// Use sparingly for major logical sections in long files

// ----- Helper Functions -----
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
   - Good: "Reverse loop to avoid slice index shifting during removal" (why)

3. **Is Accurate and Current**
   - Does comment match current code behavior?
   - Is referenced information still valid?
   - Are linked issues/docs still relevant?

4. **Is Concise**
   - Can you say the same thing in fewer words?
   - Are you repeating information from package docs or type declarations?
   - Is every sentence necessary?

5. **Is Properly Formatted**
   - Correct grammar and spelling
   - Proper indentation
   - Follows Go conventions

## Phase 5: Refactoring vs. Commenting

Sometimes improving code readability is better than adding comments:

### When to Refactor Instead of Comment

```go
// BAD: Comment explaining complex logic
// Calculate discount: 10% for orders > $100, 5% for > $50, 0% otherwise
discount := 0.10
if total <= 100 {
    if total > 50 {
        discount = 0.05
    } else {
        discount = 0.0
    }
}

// GOOD: Extract to well-named function (self-documenting)
func calculateDiscount(total float64) float64 {
    if total > 100 {
        return 0.10
    } else if total > 50 {
        return 0.05
    }
    return 0.0
}

// BAD: Comment explaining magic number
result := value * 1.07 // Apply sales tax

// GOOD: Named constant (self-documenting)
const salesTaxRate = 1.07
result := value * salesTaxRate

// BAD: Comment explaining complex condition
if user.Age >= 18 && user.HasLicense && !user.HasViolations {
    // User is eligible to rent
}

// GOOD: Extract to well-named function
if isEligibleToRent(user) {
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
   grep -r "TODO" .

   # Find FIXME comments
   grep -r "FIXME" .

   # Track technical debt with tools:
   # - golangci-lint with godox linter
   # - Custom Go tools parsing comments
   # - CI/CD integration for tracking trends
   ```

## Output Format

Please provide comment additions in this format:

### File-by-File Report
```markdown
## File: internal/service/user.go

### Line 45: Complex Algorithm Comment
**Code Section**:
```go
[relevant code]
```

**Added Comment**:
```go
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

- Concurrency/goroutines: [count]

- Channel patterns: [count]

- Interface design: [count]

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
   - Extract complex logic to named functions
   - Only comment what can't be made obvious

3. **Keep Comments Current**
   - Update with code changes
   - Remove obsolete comments
   - Review during code reviews

4. **Be Concise**
   - Every word should add value
   - Avoid redundancy with package docs
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

  - golangci-lint:
      # godox linter for TODO/FIXME tracking
      # misspell for comment spelling

  - go-critic:
      # Comment style checking
      # Deprecated comment detection

  - staticcheck:
      # Unused code detection
      # Best practice enforcement

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
   ```go
   // BAD
   count := 0 // Initialize count to zero

   // GOOD (no comment needed - obvious from code)
   count := 0
   ```

2. **Don't Duplicate Package Documentation**
   ```go
   // BAD
   // CalculateTotal calculates total price of items.
   func CalculateTotal(items []Item) float64 {
       // Calculate total price of items
       total := 0.0
       for _, item := range items {
           total += item.Price
       }
       return total
   }

   // GOOD
   // CalculateTotal calculates total price of items.
   func CalculateTotal(items []Item) float64 {
       total := 0.0
       for _, item := range items {
           total += item.Price
       }
       return total
   }
   ```

3. **Don't Leave Commented-Out Code**
   ```go
   // BAD
   // oldImplementation()
   // previousApproach()
   newImplementation()

   // GOOD (use version control)
   newImplementation()
   ```

4. **Don't Write Vague Comments**
   ```go
   // BAD: "Handle edge case"
   // BAD: "Fix issue here"
   // BAD: "Do special processing"

   // GOOD: Specific and informative
   // Handle empty slice to prevent panic in min() operation
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

---

## Output Format Specifications

The strategic comments should:

- Explain "why" decisions were made, not "what" the code does

- Be concise yet informative (typically 1-3 lines)

- Include context, references, or trade-offs where relevant

- Use proper formatting and indentation

- Follow team conventions for TODO/FIXME/HACK tags

- Add genuine value that can't be conveyed through code structure

- Be maintained and updated as code evolves

~~~
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
