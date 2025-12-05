---
template_id: cpp_comments
template_name: Comments - Cpp
version: 1.0.0
last_updated: 2025-12-03
language: Cpp
category: documentation
phase: comments
difficulty: beginner
estimated_time_hours: 1-2
prerequisites: []
tools:

  - google test
  - catch2
  - boost.test
tags:

  - documentation
  - documentation
  - cpp
---
# C++ Strategic Comments

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

- [ ] Template metaprogramming rationale

- [ ] RAII and resource management

- [ ] Move semantics and copy elision

### When NOT to Comment

- [ ] Obvious code that's self-explanatory

- [ ] Information already in Doxygen comments

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
# C++ Strategic Comments Request

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

Please add strategic comments to this C++ project following this protocol:

## Phase 1: Analysis & Comment Identification

1. **Analyze Codebase for Comment Opportunities**
   Review the code to identify sections that would benefit from comments:

   - Complex algorithms or business logic
   - Non-obvious implementation decisions
   - Workarounds for known issues
   - Performance-critical sections
   - Security-sensitive operations
   - Template usage and SFINAE patterns
   - RAII and resource management
   - Move semantics and perfect forwarding
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

```cpp
/**

 * Calculate optimal route using A* pathfinding algorithm.
 * We use A* instead of Dijkstra because our graph has a reliable heuristic
 * (Euclidean distance), which reduces search time by ~40% in testing.
 * Trade-off: Uses more memory (O(n) vs O(log n)) but acceptable for our
 * typical graph sizes (<1000 nodes).
 */
Route findOptimalRoute(const Node& start, const Node& end, const Graph& graph) {
    std::unordered_set<Node> openSet{start};
    std::unordered_map<Node, Node> cameFrom;
    // ... implementation
}
```

**Good**: Explains algorithm choice, trade-offs, and why it's appropriate
**Bad**: `// Find route` (obvious from function name)

### 2. Business Logic Comments

Document domain rules and business decisions:

```cpp
// Business rule: Premium users get 30-day refund window, standard users get 14 days.
// This differs from the legal minimum (7 days) to improve customer satisfaction.
// See: Business Policy Document v3.2, Section 4.1
int refundWindow = user.isPremium() ? 30 : 14;

// Calculate late fee: $5 per day, capped at 50% of original amount.
// Cap prevents fees from exceeding loan value (legal requirement in CA).
double lateFee = std::min(daysLate * 5.0, originalAmount * 0.5);
```

**Good**: Explains business rule, reasoning, and references
**Bad**: `// Set refund window` (doesn't explain the logic)

### 3. Non-Obvious Implementation Comments

Clarify code that isn't self-explanatory:

```cpp
// Use std::unordered_map for O(1) lookup instead of std::map's O(log n).
// Our access pattern is random with no need for ordering.
// Memory overhead (~30% more) is acceptable given performance gain (~10x faster).
std::unordered_map<std::string, Value> cache;

// Iterate in reverse to avoid iterator invalidation during erase.
// Forward iteration with erase invalidates iterators after erase point.
// Reverse iteration processes each element once without invalidation issues.
for (auto it = items.rbegin(); it != items.rend(); ) {
    if (shouldRemove(*it)) {
        // std::vector::erase needs forward iterator
        items.erase(std::next(it).base());
    } else {
        ++it;
    }
}

// Return by value to enable copy elision (NRVO).
// Modern compilers eliminate copy, making this as efficient as returning pointer.
// Avoids manual memory management and ownership transfer complexity.
std::vector<Item> getItems() const {
    return items_;  // Copy elided in C++17
}
```

**Good**: Explains why approach was chosen and what problem it solves
**Bad**: `// Create map` (obvious from code)

### 4. Workaround Comments

Document workarounds for bugs or limitations:

```cpp
// WORKAROUND: libstdc++ 8.x has bug in std::filesystem::canonical with symlinks.
// Using manual path resolution until we upgrade to libstdc++ 9+
// See: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=12345
// TODO: Remove this workaround after upgrading to GCC 9+
std::string canonicalPath = resolvePathManually(path);

// HACK: Sleep 100ms to avoid race condition in third-party API.
// Their rate limiter returns 429 even when we're under the limit if
// requests arrive too close together. Reported to vendor 2024-01-15.
std::this_thread::sleep_for(std::chrono::milliseconds(100));

// C++14 doesn't have std::optional, using boost::optional as fallback.
// TODO: Replace with std::optional when upgrading to C++17
#if __cplusplus >= 201703L
using std::optional;
#else
using boost::optional;
#endif
```

**Good**: Explains issue, links to tracking, includes TODO for removal
**Bad**: `// Wait a bit` (doesn't explain why)

### 5. Performance-Critical Comments

Explain optimization decisions:

```cpp
// Cache results because recalculation is expensive (O(n²) complexity).
// Cache invalidated on data updates via observer pattern.
// Memory impact: ~10MB for typical dataset of 10k items.
// Thread-safety: Protected by shared_mutex for concurrent reads.
mutable std::shared_mutex cacheMutex_;
mutable std::unordered_map<std::string, Statistics> statisticsCache_;

Statistics calculateStatistics(const std::vector<Data>& data) const {
    std::string key = generateCacheKey(data);

    // Read lock for cache lookup (allows concurrent reads)
    {
        std::shared_lock lock(cacheMutex_);
        auto it = statisticsCache_.find(key);
        if (it != statisticsCache_.end()) {
            return it->second;
        }
    }

    Statistics result = computeExpensiveStatistics(data);

    // Write lock for cache insert
    {
        std::unique_lock lock(cacheMutex_);
        statisticsCache_[key] = result;
    }

    return result;
}

// Reserve capacity to avoid reallocation during growth.
// Vector reallocation causes O(n) copy and memory fragmentation.
// Pre-allocation reduces time from ~500ms to ~5ms for 10k insertions.
std::vector<Item> items;
items.reserve(expectedCount);

// Use move semantics to avoid unnecessary copies.
// std::move transfers ownership without copying data.
// Essential for large objects (strings, vectors, unique_ptr).
largeVector = std::move(tempVector);  // Transfer, don't copy
```

**Good**: Explains performance trade-offs and constraints
**Bad**: `// Use cache for speed` (obvious, lacks detail)

### 6. Security-Sensitive Comments

Document security considerations:

```cpp
// Security: Use prepared statements to prevent SQL injection attacks.
// User input must NEVER be concatenated directly into SQL strings.
// Parameterized queries safely escape user input.
auto stmt = conn.prepare("SELECT * FROM users WHERE id = ?");
stmt.bind(1, userId);

// Constant-time comparison prevents timing attacks that could
// leak information about the correct token value.
// std::string::operator== returns early on mismatch, leaking length.
// Use crypto library's constant-time compare for security-critical data.
if (constantTimeCompare(providedToken, expectedToken)) {
    grantAccess();
}

// Clear sensitive data from memory immediately after use.
// Prevents sensitive data from lingering in memory after destruction.
// std::string::clear() doesn't guarantee overwrite; manually zero memory.
std::fill(password.begin(), password.end(), '\0');
password.clear();
```

**Good**: Explains security reasoning
**Bad**: `// Check credentials` (misses security implication)

### 7. RAII and Resource Management Comments

Explain RAII patterns and ownership:

```cpp
// RAII: Lock guard ensures mutex release even on exception.
// Manual lock/unlock error-prone and unsafe in exception paths.
// Destructor automatically unlocks when guard goes out of scope.
{
    std::lock_guard<std::mutex> lock(mutex_);
    // ... critical section
}  // Mutex automatically unlocked here

// unique_ptr for exclusive ownership with automatic cleanup.
// Prevents memory leaks by deleting on destruction.
// Transfer ownership with std::move; copying disabled by design.
std::unique_ptr<Resource> resource = std::make_unique<Resource>();

// shared_ptr for shared ownership with reference counting.
// Last owner's destructor deletes the object.
// Thread-safe reference count enables concurrent access.
std::shared_ptr<Data> sharedData = std::make_shared<Data>();

// Custom deleter for non-standard cleanup.
// FILE* requires fclose(), not delete operator.
// unique_ptr with custom deleter provides RAII for C APIs.
auto fileDeleter = [](FILE* f) { if (f) fclose(f); };
std::unique_ptr<FILE, decltype(fileDeleter)> file(fopen("data.txt", "r"), fileDeleter);
```

**Good**: Explains RAII reasoning and ownership
**Bad**: `// Lock mutex` (obvious from code)

### 8. Template and Generic Programming Comments

Explain template design decisions:

```cpp
// Template specialization for performance-critical types.
// Generic implementation uses virtual calls (~10ns overhead per call).
// Specialized version uses direct calls, improving throughput by 40%.
template<typename T>
class Processor {
    // Generic implementation
};

template<>
class Processor<int> {
    // Optimized for int - no virtual calls
};

// SFINAE to enable function only for numeric types.
// std::enable_if removes function from overload resolution for non-numeric types.
// Provides better error messages than template instantiation failure.
template<typename T>
std::enable_if_t<std::is_arithmetic_v<T>, T>
clamp(T value, T min, T max) {
    return std::max(min, std::min(value, max));
}

// Perfect forwarding preserves value category (lvalue/rvalue).
// std::forward<T> casts to T&&, maintaining original lvalue/rvalue status.
// Enables efficient forwarding without unnecessary copies.
template<typename T, typename... Args>
std::unique_ptr<T> makeUnique(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}

// Variadic template for type-safe printf-style formatting.
// Parameter pack expansion processes each argument individually.
// Type safety enforced at compile time, unlike C printf.
template<typename... Args>
std::string format(const std::string& fmt, Args&&... args) {
    return formatImpl(fmt, std::forward<Args>(args)...);
}
```

**Good**: Explains template reasoning and techniques
**Bad**: `// Template function` (obvious from syntax)

### 9. Move Semantics Comments

Explain move operations and copy elision:

```cpp
// Move constructor transfers ownership without copying data.
// Source object left in valid but unspecified state.
// Essential for efficient transfer of expensive-to-copy objects.
Buffer(Buffer&& other) noexcept
    : data_(std::exchange(other.data_, nullptr))
    , size_(std::exchange(other.size_, 0)) {
    // std::exchange transfers value and resets source atomically
}

// Move assignment with copy-and-swap idiom for exception safety.
// Strong exception guarantee: either succeeds or leaves object unchanged.
// Swap is noexcept, preventing partial assignment state.
Buffer& operator=(Buffer other) noexcept {
    swap(*this, other);  // Copy-and-swap idiom
    return *this;
}

// Return value optimization (RVO) eliminates copy.
// Compiler constructs return value directly in caller's storage.
// Named return value optimization (NRVO) works even for named variables.
// Guaranteed in C++17 for prvalues.
std::vector<int> createLargeVector() {
    std::vector<int> result;
    result.reserve(1000000);
    // ... populate vector
    return result;  // No copy - NRVO eliminates it
}

// std::move enables move semantics for named objects.
// Without std::move, named objects are copied (lvalues).
// Move appropriate when source no longer needed.
std::vector<int> temp = createData();
processData(std::move(temp));  // Transfer ownership, don't copy
// temp now in moved-from state - don't use it
```

**Good**: Explains move semantics and optimization
**Bad**: `// Move data` (obvious from std::move)

### 10. Concurrency Comments

Explain thread safety and synchronization:

```cpp
// Thread-safe singleton using Meyers' singleton pattern.
// C++11 guarantees static local initialization is thread-safe.
// No explicit locking needed; compiler handles synchronization.
static Singleton& getInstance() {
    static Singleton instance;
    return instance;
}

// Reader-writer lock for read-heavy workloads.
// shared_lock allows concurrent reads without contention.
// unique_lock for exclusive write access.
// ~90% reads justify shared_mutex overhead (~2x slower than mutex for writes).
std::shared_mutex dataMutex_;

void read() const {
    std::shared_lock lock(dataMutex_);  // Shared read access
    // ... read data
}

void write() {
    std::unique_lock lock(dataMutex_);  // Exclusive write access
    // ... modify data
}

// atomic for lock-free operations.
// Atomic operations provide sequential consistency without locks.
// Suitable for simple operations (increment, compare-exchange).
// Complex operations still need mutex.
std::atomic<int> counter_{0};

// Use std::scoped_lock for multiple mutex acquisition.
// Prevents deadlock via consistent lock ordering.
// RAII ensures all mutexes released on scope exit.
std::scoped_lock lock(mutex1_, mutex2_);  // Deadlock-free
```

**Good**: Explains concurrency patterns and trade-offs
**Bad**: `// Lock mutex` (obvious from code)

### 11. TODO/FIXME/HACK Conventions

Use standardized tags for technical debt:

```cpp
// TODO: Refactor this into separate validation class (target: v2.1)
// Current implementation works but violates single responsibility principle.
// Estimate: 4 hours
void processAndValidate(const Data& data) {
    // ...
}

// FIXME: Race condition when multiple threads process same job.
// Occurs under high load (>1000 jobs/second). Need std::mutex protection.
// Priority: HIGH - Causes duplicate processing ~0.1% of time
// Assigned to: @username, Issue #456
void processJob(const std::string& jobId) {
    // ...
}

// HACK: Temporary workaround for memory leak in library v2.3
// Remove this when upgrading to v2.4+ which has the fix.
// See: https://github.com/project/issues/123
// Force cleanup as workaround
manualCleanup();

// NOTE: This function must be called after initialization.
// Order dependency: database connection must be established first.
void configure() {
    // ...
}

// WARNING: Modifying this constant will break ABI compatibility.
// Value is part of binary interface with existing shared libraries.
// Cannot change without major version bump.
constexpr int ProtocolVersion = 1;
```

**Format**: `TAG: Description (context)`

- **TODO**: Planned improvement or feature

- **FIXME**: Known bug or issue

- **HACK**: Temporary workaround

- **NOTE**: Important information

- **WARNING**: Critical caution

### 12. Inline Comments (Use Sparingly)

Reserve inline comments for truly non-obvious code:

```cpp
// Good inline comment - explains non-obvious detail
int result = value & 0xFF;  // Mask to get only the last byte

// Bad inline comment - obvious from code
count++;  // Increment count

// Good inline comment - explains magic number
constexpr auto timeout = std::chrono::hours(24);  // 24 hours

// Bad inline comment - should be named constant
auto timeout = 86400s;  // Timeout value
// Better: Use named constant
constexpr auto dayDuration = std::chrono::hours(24);
auto timeout = dayDuration;

// Good inline comment - explains regex pattern
std::regex pattern(R"(^[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}$)");  // RFC 5322 email format
```

### 13. Doxygen vs. Inline Comments

**Doxygen for API documentation, inline comments for implementation details:**

```cpp
/**

 * @brief Process user payment with fraud detection.
 *

 * This function validates the payment, performs fraud checks, and processes
 * the transaction through the payment gateway. All amounts are in cents.
 *

 * @param payment Payment details including amount, currency, and card info
 * @return Payment confirmation with transaction ID
 * @throws ValidationException if payment data is invalid
 * @throws FraudException if payment fails fraud checks
 */
PaymentResult processPayment(const Payment& payment) {
    // Use Luhn algorithm to validate card number before API call.
    // Prevents unnecessary API charges for invalid cards (~15% of attempts).
    if (!isValidCardNumber(payment.cardNumber)) {
        throw ValidationException("Invalid card number");
    }

    // 3D Secure required for EU transactions over €30 (PSD2 compliance).
    // US transactions always skip 3DS for better conversion rates.
    bool requires3DS = payment.currency == "EUR" && payment.amount > 3000;

    return paymentGateway.charge(payment, requires3DS);
}
```

**Doxygen**: What the function does, parameters, return values, exceptions
**Inline comments**: Why implementation choices were made

### 14. What NOT to Comment

**Avoid these comment anti-patterns:**

```cpp
// BAD: Obvious comments
// Set x to 5
int x = 5;

// BAD: Redundant with function name
// Calculate total
double calculateTotal() {
    // ...
}

// BAD: Meta-commentary about code changes
// Changed this from += to = on 2024-01-15
// Fixed bug here
// Updated by John

// BAD: Commented-out code (use version control instead)
// oldFunction();
// return previousValue;

// BAD: Duplicating Doxygen
/**

 * Calculate total price.
 */
double calculateTotal(const std::vector<Item>& items) {
    // Calculate total price
    return std::accumulate(items.begin(), items.end(), 0.0,
        [](double sum, const Item& item) { return sum + item.price; });
}

// BAD: Vague or unhelpful
// Do stuff
// Handle things
// Process data
```

## Phase 3: Comment Placement Guidelines

### Block Comments
```cpp
// Use block comments before code blocks they describe.
// Separate from previous code with blank line.
// Keep lines under 80 characters.

void myFunction() {
    // Block comments inside functions go before the relevant section
    // with proper indentation.
    codeSection();
}
```

### Inline Comments
```cpp
// Place inline comments sparingly, separated by at least 2 spaces
auto result = complexCalculation();  // Explanation when truly needed
```

### Section Dividers
```cpp
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
   - Good: "Reverse iteration to avoid iterator invalidation" (why)

3. **Is Accurate and Current**
   - Does comment match current code behavior?
   - Is referenced information still valid?
   - Are linked issues/docs still relevant?

4. **Is Concise**
   - Can you say the same thing in fewer words?
   - Are you repeating information from Doxygen or type declarations?
   - Is every sentence necessary?

5. **Is Properly Formatted**
   - Correct grammar and spelling
   - Proper indentation
   - Follows project conventions

## Phase 5: Refactoring vs. Commenting

Sometimes improving code readability is better than adding comments:

### When to Refactor Instead of Comment

```cpp
// BAD: Comment explaining complex logic
// Calculate discount: 10% for orders > $100, 5% for > $50, 0% otherwise
double discount = total > 100.0 ? 0.10 : (total > 50.0 ? 0.05 : 0.0);

// GOOD: Extract to well-named function (self-documenting)
double calculateDiscount(double total) {
    if (total > 100.0) return 0.10;
    if (total > 50.0) return 0.05;
    return 0.0;
}

// BAD: Comment explaining magic number
double result = value * 1.07;  // Apply sales tax

// GOOD: Named constant (self-documenting)
constexpr double SalesTaxRate = 1.07;
double result = value * SalesTaxRate;

// BAD: Comment explaining complex condition
if (user.age >= 18 && user.hasLicense && !user.hasViolations) {
    // User is eligible to rent
}

// GOOD: Extract to well-named function
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
   # - Clang-Tidy for code quality
   # - Doxygen for documentation
   # - Custom scripts for comment tracking
   ```

## Output Format

Please provide comment additions in this format:

### File-by-File Report
```markdown
## File: src/UserService.cpp

### Line 45: Complex Algorithm Comment
**Code Section**:
```cpp
[relevant code]
```

**Added Comment**:
```cpp
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

- RAII/resource management: [count]

- Template/generic programming: [count]

- Move semantics: [count]

- Concurrency: [count]

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
   - Avoid redundancy with Doxygen
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

  - clang-tidy:
      # Code quality and style
      # Comment format checking

  - doxygen:
      # Documentation generation
      # Comment validation

  - cppcheck:
      # Static analysis
      # Code quality metrics

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
   ```cpp
   // BAD
   int count = 0;  // Initialize count to zero

   // GOOD (no comment needed - obvious from code)
   int count = 0;
   ```

2. **Don't Duplicate Doxygen**
   ```cpp
   // BAD
   /**

    * Calculate total price of items.
    */
   double calculateTotal(const std::vector<Item>& items) {
       // Calculate total price of items
       return std::accumulate(items.begin(), items.end(), 0.0,
           [](double sum, const Item& item) { return sum + item.price; });
   }

   // GOOD
   /**

    * Calculate total price of items.
    */
   double calculateTotal(const std::vector<Item>& items) {
       return std::accumulate(items.begin(), items.end(), 0.0,
           [](double sum, const Item& item) { return sum + item.price; });
   }
   ```

3. **Don't Leave Commented-Out Code**
   ```cpp
   // BAD
   // oldImplementation();
   // previousApproach();
   newImplementation();

   // GOOD (use version control)
   newImplementation();
   ```

4. **Don't Write Vague Comments**
   ```cpp
   // BAD: "Handle edge case"
   // BAD: "Fix issue here"
   // BAD: "Do special processing"

   // GOOD: Specific and informative
   // Handle empty vector to prevent undefined behavior in std::min_element
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
