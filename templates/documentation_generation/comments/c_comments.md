---
template_id: c_comments
template_name: Comments - C
version: 1.0.0
last_updated: 2025-12-03
language: C
category: documentation
phase: comments
difficulty: beginner
estimated_time_hours: 1-2
prerequisites: []
tools:

  - unity
  - cmocka
  - check
tags:

  - documentation
  - documentation
  - c
---
# C Strategic Comments

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

- [ ] Memory management rationale

- [ ] Pointer arithmetic explanations

- [ ] Platform-specific code

### When NOT to Comment

- [ ] Obvious code that's self-explanatory

- [ ] Information already in header documentation

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
# C Strategic Comments Request

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

Please add strategic comments to this C project following this protocol:

## Phase 1: Analysis & Comment Identification

1. **Analyze Codebase for Comment Opportunities**
   Review the code to identify sections that would benefit from comments:

   - Complex algorithms or business logic
   - Non-obvious implementation decisions
   - Workarounds for known issues
   - Performance-critical sections
   - Security-sensitive operations
   - Memory management and ownership
   - Pointer usage and arithmetic
   - Platform-specific implementations
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

```c
/*

 * Calculate optimal route using A* pathfinding algorithm.
 * We use A* instead of Dijkstra because our graph has a reliable heuristic
 * (Euclidean distance), which reduces search time by ~40% in testing.
 * Trade-off: Uses more memory (O(n) vs O(log n)) but acceptable for our
 * typical graph sizes (<1000 nodes).
 */
route_t* find_optimal_route(node_t* start, node_t* end, graph_t* graph) {
    node_set_t* open_set = create_node_set();
    insert_node(open_set, start);
    /* ... implementation */
}
```

**Good**: Explains algorithm choice, trade-offs, and why it's appropriate
**Bad**: `/* Find route */` (obvious from function name)

### 2. Business Logic Comments

Document domain rules and business decisions:

```c
/* Business rule: Premium users get 30-day refund window, standard users get 14 days.

 * This differs from the legal minimum (7 days) to improve customer satisfaction.
 * See: Business Policy Document v3.2, Section 4.1
 */
int refund_window = user->is_premium ? 30 : 14;

/* Calculate late fee: $5 per day, capped at 50% of original amount.
 * Cap prevents fees from exceeding loan value (legal requirement in CA).
 */
double late_fee = fmin(days_late * 5.0, original_amount * 0.5);
```

**Good**: Explains business rule, reasoning, and references
**Bad**: `/* Set refund window */` (doesn't explain the logic)

### 3. Non-Obvious Implementation Comments

Clarify code that isn't self-explanatory:

```c
/* Use calloc instead of malloc to zero-initialize memory.

 * Zero initialization prevents uninitialized read vulnerabilities.
 * Performance impact negligible (<1%) for typical allocations.
 */
buffer_t* buffer = calloc(1, sizeof(buffer_t));

/* Iterate backwards to avoid array index shifting during removal.
 * Forward iteration with memmove would cause quadratic time complexity.
 * Reverse iteration maintains O(n) by processing each element once.
 */
for (int i = count - 1; i >= 0; i--) {
    if (should_remove(items[i])) {
        memmove(&items[i], &items[i+1], (count - i - 1) * sizeof(item_t));
        count--;
    }
}

/* Copy string to prevent external modification of internal buffer.
 * Returning direct pointer violates encapsulation and enables buffer overflow.
 * Caller responsible for freeing returned memory.
 */
char* get_name(const user_t* user) {
    return strdup(user->name);
}
```

**Good**: Explains why approach was chosen and what problem it solves
**Bad**: `/* Allocate memory */` (obvious from code)

### 4. Workaround Comments

Document workarounds for bugs or limitations:

```c
/* WORKAROUND: glibc 2.24 has buffer overflow in strftime() with %Z specifier.

 * Using manual timezone formatting until system upgraded to glibc 2.28+
 * See: https://sourceware.org/bugzilla/show_bug.cgi?id=12345
 * TODO: Remove this workaround after upgrading to glibc 2.28+
 */
format_timezone_manual(buffer, sizeof(buffer), &tm);

/* HACK: Sleep 100ms to avoid race condition in third-party driver.
 * Their interrupt handler has race condition that causes missed events
 * if requests arrive too close together. Reported to vendor 2024-01-15.
 */
usleep(100000); /* 100ms */

/* GCC 4.8 doesn't support C11 _Generic, using macro dispatch as fallback.
 * TODO: Replace with _Generic when minimum compiler version is GCC 4.9+
 */
#if __GNUC__ > 4 || (__GNUC__ == 4 && __GNUC_MINOR__ >= 9)
#define print_value(x) _Generic((x), \
    int: print_int, \
    double: print_double)(x)
#else
#define print_value(x) print_generic(x)
#endif
```

**Good**: Explains issue, links to tracking, includes TODO for removal
**Bad**: `/* Wait */` (doesn't explain why)

### 5. Performance-Critical Comments

Explain optimization decisions:

```c
/* Cache results because recalculation is expensive (O(n²) complexity).

 * Cache invalidated on data updates via callback mechanism.
 * Memory impact: ~10MB for typical dataset of 10k items.
 * Thread-safety: Protected by reader-writer lock.
 */
static cache_t* statistics_cache = NULL;
static pthread_rwlock_t cache_lock = PTHREAD_RWLOCK_INITIALIZER;

statistics_t calculate_statistics(const data_t* data, size_t count) {
    char* key = generate_cache_key(data, count);

    pthread_rwlock_rdlock(&cache_lock);
    statistics_t* cached = cache_lookup(statistics_cache, key);
    if (cached) {
        pthread_rwlock_unlock(&cache_lock);
        free(key);
        return *cached;
    }
    pthread_rwlock_unlock(&cache_lock);

    statistics_t result = compute_expensive_statistics(data, count);

    pthread_rwlock_wrlock(&cache_lock);
    cache_insert(statistics_cache, key, &result);
    pthread_rwlock_unlock(&cache_lock);

    free(key);
    return result;
}

/* Use fixed-size buffer on stack instead of heap allocation.
 * Stack allocation avoids malloc overhead (~50ns per call).
 * Buffer size adequate for all valid inputs (max 256 chars).
 * Reduces allocation calls from 1M to 0, saving ~50ms per million operations.
 */
char buffer[256];
format_string(buffer, sizeof(buffer), input);

/* Pre-allocate exact capacity to avoid reallocation during growth.
 * Reallocation causes O(n) copies and memory fragmentation.
 * Known size enables single allocation, reducing time from 500ms to 5ms.
 */
array_t* array = array_create_with_capacity(known_count);
```

**Good**: Explains performance trade-offs and constraints
**Bad**: `/* Use cache for speed */` (obvious, lacks detail)

### 6. Security-Sensitive Comments

Document security considerations:

```c
/* Security: Use snprintf to prevent buffer overflow.

 * sprintf has no bounds checking and enables arbitrary code execution.
 * Always specify buffer size with snprintf to prevent overflow attacks.
 */
snprintf(buffer, sizeof(buffer), "User: %s", username);

/* Constant-time comparison prevents timing attacks that could
 * leak information about the correct token value.
 * strcmp returns early on mismatch, leaking token length and content.
 * Use memcmp_const_time or similar for security-critical comparisons.
 */
if (memcmp_const_time(provided_token, expected_token, TOKEN_LENGTH) == 0) {
    grant_access();
}

/* Clear sensitive data from memory immediately after use.
 * Prevents sensitive data from lingering in memory after free.
 * explicit_bzero() prevents compiler from optimizing away the clear.
 * Standard memset() may be optimized out as "dead store".
 */
explicit_bzero(password, password_length);
free(password);

/* Validate array index before access to prevent out-of-bounds read.
 * Out-of-bounds access causes undefined behavior and potential exploits.
 * Always check bounds before dereferencing arrays or pointers.
 */
if (index >= 0 && index < array_size) {
    return array[index];
}
return NULL; /* Invalid index */
```

**Good**: Explains security reasoning
**Bad**: `/* Check bounds */` (misses security implication)

### 7. Memory Management Comments

Explain allocation, ownership, and lifetime:

```c
/* Allocate buffer on heap because size exceeds stack limit (8KB).

 * Stack overflow causes segfault, heap allocation is safer for large buffers.
 * Caller responsible for freeing returned memory with free().
 */
uint8_t* create_large_buffer(size_t size) {
    return malloc(size);
}

/* Transfer ownership of buffer to caller.
 * This function allocates memory that caller must free.
 * Prevents double-free by setting internal pointer to NULL.
 */
char* take_buffer(buffer_t* buf) {
    char* result = buf->data;
    buf->data = NULL; /* Clear to prevent double-free */
    return result;
}

/* Shallow copy: Only copies pointers, not pointed-to data.
 * Both source and destination point to same underlying memory.
 * Caller must ensure source outlives destination to prevent use-after-free.
 * Deep copy requires duplicating all pointed-to memory.
 */
void shallow_copy_user(user_t* dest, const user_t* src) {
    dest->name = src->name; /* Shared pointer, not copied */
    dest->id = src->id;
}

/* Reference counting for shared ownership.
 * Increment refcount when creating new reference.
 * Decrement on release; free when refcount reaches zero.
 * Thread-safe refcount requires atomic operations.
 */
void user_retain(user_t* user) {
    atomic_fetch_add(&user->refcount, 1);
}

void user_release(user_t* user) {
    if (atomic_fetch_sub(&user->refcount, 1) == 1) {
        /* Last reference released, safe to free */
        free(user->name);
        free(user);
    }
}
```

**Good**: Explains ownership and lifetime
**Bad**: `/* Allocate memory */` (obvious from malloc)

### 8. Pointer and Address Arithmetic Comments

Explain pointer manipulations:

```c
/* Align pointer to 16-byte boundary for SIMD operations.

 * Unaligned access causes performance penalty or crash on some architectures.
 * Alignment formula: (ptr + align - 1) & ~(align - 1)
 */
void* aligned_ptr = (void*)(((uintptr_t)ptr + 15) & ~15);

/* Calculate structure offset using pointer arithmetic.
 * offsetof() not available for dynamically-sized members.
 * Cast to char* for byte-level arithmetic, then cast back.
 */
size_t offset = (char*)&s->member - (char*)s;

/* Use void pointer for type-agnostic memory operations.
 * Cast to char* for byte-level manipulation.
 * void pointer arithmetic is undefined; char* arithmetic is well-defined.
 */
void* memcpy_custom(void* dest, const void* src, size_t n) {
    char* d = (char*)dest;
    const char* s = (const char*)src;
    for (size_t i = 0; i < n; i++) {
        d[i] = s[i];
    }
    return dest;
}

/* Iterate through linked list using pointer-to-pointer.
 * Eliminates special case for head node, simplifying deletion logic.
 * *pp = (*pp)->next updates previous pointer to skip deleted node.
 */
void list_remove(list_t** head, int value) {
    for (list_t** pp = head; *pp != NULL; pp = &(*pp)->next) {
        if ((*pp)->value == value) {
            list_t* temp = *pp;
            *pp = (*pp)->next;
            free(temp);
            return;
        }
    }
}
```

**Good**: Explains pointer arithmetic reasoning
**Bad**: `/* Pointer math */` (obvious from code)

### 9. Platform-Specific Comments

Explain platform differences and portability:

```c
/* Platform-specific endianness conversion.

 * Network byte order is big-endian (most significant byte first).
 * x86/x86_64 use little-endian (least significant byte first).
 * ARM can be either (bi-endian); check platform macros.
 */
uint32_t network_to_host(uint32_t net_value) {
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
    return __builtin_bswap32(net_value);
#else
    return net_value; /* Already big-endian */
#endif
}

/* Windows uses backslash for paths, Unix uses forward slash.
 * Path separator defined in platform-specific headers.
 * Use PATH_SEPARATOR constant for cross-platform compatibility.
 */
#ifdef _WIN32
#define PATH_SEPARATOR '\\'
#else
#define PATH_SEPARATOR '/'
#endif

/* POSIX mmap() not available on Windows.
 * Use CreateFileMapping/MapViewOfFile on Windows.
 * Abstract behind portable interface for cross-platform code.
 */
#ifdef _WIN32
void* mmap_portable(int fd, size_t length) {
    HANDLE hFile = (HANDLE)_get_osfhandle(fd);
    HANDLE hMap = CreateFileMapping(hFile, NULL, PAGE_READONLY, 0, 0, NULL);
    return MapViewOfFile(hMap, FILE_MAP_READ, 0, 0, length);
}
#else
void* mmap_portable(int fd, size_t length) {
    return mmap(NULL, length, PROT_READ, MAP_PRIVATE, fd, 0);
}
#endif
```

**Good**: Explains platform differences
**Bad**: `/* Platform code */` (obvious from ifdef)

### 10. TODO/FIXME/HACK Conventions

Use standardized tags for technical debt:

```c
/* TODO: Refactor this into separate validation module (target: v2.1)

 * Current implementation works but violates single responsibility principle.
 * Estimate: 4 hours
 */
int process_and_validate(const data_t* data) {
    /* ... */
}

/* FIXME: Race condition when multiple threads process same job.
 * Occurs under high load (>1000 jobs/second). Need mutex protection.
 * Priority: HIGH - Causes duplicate processing ~0.1% of time
 * Assigned to: @username, Issue #456
 */
void process_job(const char* job_id) {
    /* ... */
}

/* HACK: Temporary workaround for memory leak in libfoo v2.3
 * Remove this when upgrading to v2.4+ which has the fix.
 * See: https://github.com/project/issues/123
 */
free_workaround(resource); /* Force cleanup */

/* NOTE: This function must be called before initialization.
 * Order dependency: network must be initialized first.
 */
void configure_network(void) {
    /* ... */
}

/* WARNING: Modifying this constant will break binary compatibility.
 * Value is part of ABI contract with existing shared libraries.
 * Cannot change without major version bump.
 */
#define PROTOCOL_VERSION 1
```

**Format**: `TAG: Description (context)`

- **TODO**: Planned improvement or feature

- **FIXME**: Known bug or issue

- **HACK**: Temporary workaround

- **NOTE**: Important information

- **WARNING**: Critical caution

### 11. Inline Comments (Use Sparingly)

Reserve inline comments for truly non-obvious code:

```c
/* Good inline comment - explains non-obvious detail */
int result = value & 0xFF; /* Mask to get only the last byte */

/* Bad inline comment - obvious from code */
count++; /* Increment count */

/* Good inline comment - explains magic number */
#define TIMEOUT 86400 /* 24 hours in seconds */

/* Bad inline comment - should be named constant */
int timeout = 86400; /* Timeout value */
/* Better: Use named constant */
#define SECONDS_PER_DAY 86400
int timeout = SECONDS_PER_DAY;

/* Good inline comment - explains bit manipulation */
flags |= (1 << 3); /* Set bit 3 (enable verbose mode) */
```

### 12. Header Documentation vs. Implementation Comments

**Header docs for API documentation, implementation comments for details:**

```c
/* Header file (user.h) */
/*

 * Process user payment with fraud detection.
 *

 * This function validates the payment, performs fraud checks, and processes
 * the transaction through the payment gateway. All amounts are in cents.
 *

 * @param payment Payment details including amount, currency, and card info
 * @return Payment confirmation with transaction ID, or NULL on error
 * @note Sets errno to EINVAL if payment data is invalid
 * @note Sets errno to EACCES if payment fails fraud checks
 */
payment_result_t* process_payment(const payment_t* payment);

/* Implementation file (user.c) */
payment_result_t* process_payment(const payment_t* payment) {
    /* Use Luhn algorithm to validate card number before API call.

     * Prevents unnecessary API charges for invalid cards (~15% of attempts).
     */
    if (!is_valid_card_number(payment->card_number)) {
        errno = EINVAL;
        return NULL;
    }

    /* 3D Secure required for EU transactions over €30 (PSD2 compliance).
     * US transactions always skip 3DS for better conversion rates.
     */
    bool requires_3ds = strcmp(payment->currency, "EUR") == 0
        && payment->amount > 3000;

    return payment_gateway_charge(payment, requires_3ds);
}
```

**Header docs**: What the function does, parameters, return values
**Implementation comments**: Why implementation choices were made

### 13. What NOT to Comment

**Avoid these comment anti-patterns:**

```c
/* BAD: Obvious comments */
/* Set x to 5 */
int x = 5;

/* BAD: Redundant with function name */
/* Calculate total */
double calculate_total(void) {
    /* ... */
}

/* BAD: Meta-commentary about code changes */
/* Changed this from += to = on 2024-01-15 */
/* Fixed bug here */
/* Updated by John */

/* BAD: Commented-out code (use version control instead) */
/* old_function(); */
/* return previous_value; */

/* BAD: Duplicating header documentation */
/*

 * Calculate total price.
 */
double calculate_total(const item_t* items, size_t count) {
    /* Calculate total price */
    double total = 0.0;
    for (size_t i = 0; i < count; i++) {
        total += items[i].price;
    }
    return total;
}

/* BAD: Vague or unhelpful */
/* Do stuff */
/* Handle things */
/* Process data */
```

## Phase 3: Comment Placement Guidelines

### Block Comments
```c
/*

 * Use block comments before code blocks they describe.
 * Separate from previous code with blank line.
 * Keep lines under 80 characters.
 */

void my_function(void) {
    /* Block comments inside functions go before the relevant section

     * with proper indentation.
     */
    code_section();
}
```

### Inline Comments
```c
/* Place inline comments sparingly, separated by at least 2 spaces */
int result = complex_calculation(); /* Explanation when truly needed */
```

### Section Dividers
```c
/* ===== Data Processing Section ===== */
/* Use sparingly for major logical sections in long files */

/* ----- Helper Functions ----- */
/* Or use simpler dividers for subsections */
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
   - Good: "Reverse loop to avoid memmove on every removal" (why)

3. **Is Accurate and Current**
   - Does comment match current code behavior?
   - Is referenced information still valid?
   - Are linked issues/docs still relevant?

4. **Is Concise**
   - Can you say the same thing in fewer words?
   - Are you repeating information from headers or declarations?
   - Is every sentence necessary?

5. **Is Properly Formatted**
   - Correct grammar and spelling
   - Proper indentation
   - Follows project conventions

## Phase 5: Refactoring vs. Commenting

Sometimes improving code readability is better than adding comments:

### When to Refactor Instead of Comment

```c
/* BAD: Comment explaining complex logic */
/* Calculate discount: 10% for orders > $100, 5% for > $50, 0% otherwise */
double discount = total > 100.0 ? 0.10 : (total > 50.0 ? 0.05 : 0.0);

/* GOOD: Extract to well-named function (self-documenting) */
double calculate_discount(double total) {
    if (total > 100.0) return 0.10;
    if (total > 50.0) return 0.05;
    return 0.0;
}

/* BAD: Comment explaining magic number */
double result = value * 1.07; /* Apply sales tax */

/* GOOD: Named constant (self-documenting) */
#define SALES_TAX_RATE 1.07
double result = value * SALES_TAX_RATE;

/* BAD: Comment explaining complex condition */
if (user->age >= 18 && user->has_license && !user->has_violations) {
    /* User is eligible to rent */
}

/* GOOD: Extract to well-named function */
if (is_eligible_to_rent(user)) {
    /* ... */
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
   # - cppcheck for code analysis
   # - Custom scripts for comment tracking
   # - CI/CD integration for trend analysis
   ```

## Output Format

Please provide comment additions in this format:

### File-by-File Report
```markdown
## File: src/user.c

### Line 45: Complex Algorithm Comment
**Code Section**:
```c
[relevant code]
```

**Added Comment**:
```c
/* [strategic comment explaining why/how] */
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

- Memory management: [count]

- Pointer arithmetic: [count]

- Platform-specific: [count]

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
   - Avoid redundancy with headers
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

  - cppcheck:
      # Static analysis
      # Comment style checking

  - splint:
      # Annotation checking
      # Code quality analysis

  - doxygen:
      # Documentation generation
      # Comment format validation

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
   ```c
   /* BAD */
   int count = 0; /* Initialize count to zero */

   /* GOOD (no comment needed - obvious from code) */
   int count = 0;
   ```

2. **Don't Duplicate Header Documentation**
   ```c
   /* BAD */
   /* Calculate total price of items. */
   double calculate_total(const item_t* items, size_t count) {
       /* Calculate total price of items */
       double total = 0.0;
       for (size_t i = 0; i < count; i++) {
           total += items[i].price;
       }
       return total;
   }

   /* GOOD */
   /* Calculate total price of items. */
   double calculate_total(const item_t* items, size_t count) {
       double total = 0.0;
       for (size_t i = 0; i < count; i++) {
           total += items[i].price;
       }
       return total;
   }
   ```

3. **Don't Leave Commented-Out Code**
   ```c
   /* BAD */
   /* old_implementation(); */
   /* previous_approach(); */
   new_implementation();

   /* GOOD (use version control) */
   new_implementation();
   ```

4. **Don't Write Vague Comments**
   ```c
   /* BAD: "Handle edge case" */
   /* BAD: "Fix issue here" */
   /* BAD: "Do special processing" */

   /* GOOD: Specific and informative */
   /* Handle empty array to prevent NULL dereference in loop */
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
