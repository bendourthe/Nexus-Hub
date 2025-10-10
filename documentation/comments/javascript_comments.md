# JavaScript Strategic Comments

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

- [ ] Browser compatibility issues

- [ ] Async/Promise chain reasoning

### When NOT to Comment

- [ ] Obvious code that's self-explanatory

- [ ] Information already in JSDoc

- [ ] Redundant type information (use TypeScript instead)

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
# JavaScript Strategic Comments Request

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

Please add strategic comments to this JavaScript project following this protocol:

## Phase 1: Analysis & Comment Identification

1. **Analyze Codebase for Comment Opportunities**
   Review the code to identify sections that would benefit from comments:
   - Complex algorithms or business logic
   - Non-obvious implementation decisions
   - Workarounds for known issues
   - Performance-critical sections
   - Security-sensitive operations
   - Browser compatibility workarounds
   - Async/await error handling patterns
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

```javascript
/**
 * Calculate optimal route using A* pathfinding algorithm.
 * We use A* instead of Dijkstra because our graph has a reliable heuristic
 * (Euclidean distance), which reduces search time by ~40% in testing.
 * Trade-off: Uses more memory (O(n) vs O(log n)) but acceptable for our
 * typical graph sizes (<1000 nodes).
 */
function findOptimalRoute(start, end, graph) {
    const openSet = new Set([start]);
    const cameFrom = new Map();
    // ... implementation
}
```

**Good**: Explains algorithm choice, trade-offs, and why it's appropriate
**Bad**: `// Find route` (obvious from function name)

### 2. Business Logic Comments

Document domain rules and business decisions:

```javascript
// Business rule: Premium users get 30-day refund window, standard users get 14 days.
// This differs from the legal minimum (7 days) to improve customer satisfaction.
// See: Business Policy Document v3.2, Section 4.1
const refundWindow = user.isPremium ? 30 : 14;

// Calculate late fee: $5 per day, capped at 50% of original amount.
// Cap prevents fees from exceeding loan value (legal requirement in CA).
const lateFee = Math.min(daysLate * 5, originalAmount * 0.5);
```

**Good**: Explains business rule, reasoning, and references
**Bad**: `// Set refund window` (doesn't explain the logic)

### 3. Non-Obvious Implementation Comments

Clarify code that isn't self-explanatory:

```javascript
// Use btoa() instead of Buffer for browser compatibility.
// Node.js would use Buffer.from(data).toString('base64')
// but btoa() works in all modern browsers without polyfills.
const encodedData = btoa(binaryData);

// Reverse iteration prevents index shifting during removal.
// Forward iteration would skip elements after each deletion.
for (let i = items.length - 1; i >= 0; i--) {
    if (shouldRemove(items[i])) {
        items.splice(i, 1);
    }
}

// Use double negation to coerce to boolean while preserving falsy values.
// Direct boolean conversion would treat 0 and "" as false.
const hasValue = !!value && value !== 0 && value !== '';
```

**Good**: Explains why approach was chosen and what problem it solves
**Bad**: `// Encode data to base64` (obvious from code)

### 4. Workaround Comments

Document workarounds for bugs or limitations:

```javascript
// WORKAROUND: axios has memory leak with long-lived connections in v0.27.
// Creating new instance for each request until fixed in v1.0.
// See: https://github.com/axios/axios/issues/4937
// TODO: Remove this workaround after upgrading to axios>=1.0
const axiosInstance = axios.create();
const response = await axiosInstance.get(url);

// HACK: Delay 100ms to avoid race condition in third-party API.
// Their rate limiter returns 429 even when we're under the limit if
// requests arrive too close together. Reported to vendor 2024-01-15.
await new Promise(resolve => setTimeout(resolve, 100));

// IE11 doesn't support Array.prototype.includes()
// Using indexOf as fallback for older browser support.
// TODO: Remove when IE11 support is dropped (Q3 2024)
const hasItem = Array.prototype.includes
    ? items.includes(searchItem)
    : items.indexOf(searchItem) !== -1;
```

**Good**: Explains issue, links to tracking, includes TODO for removal
**Bad**: `// Wait a bit` (doesn't explain why)

### 5. Performance-Critical Comments

Explain optimization decisions:

```javascript
// Cache results because recalculation is expensive (O(n²) complexity).
// Cache invalidated on data updates via event listener.
// Memory impact: ~10MB for typical dataset of 10k items.
const cache = new Map();
function calculateStatistics(data) {
    const key = JSON.stringify(data);
    if (cache.has(key)) return cache.get(key);

    const result = expensiveCalculation(data);
    cache.set(key, result);
    return result;
}

// Use requestAnimationFrame to batch DOM updates and prevent layout thrashing.
// Direct manipulation would trigger reflow on every change (~60ms total).
// RAF batches all changes into single reflow (~5ms).
const updates = [];
requestAnimationFrame(() => {
    updates.forEach(update => update());
    updates.length = 0;
});

// Lazy load heavy dependency only when needed to reduce initial bundle size.
// Saves ~150KB in main bundle, loaded on-demand in ~200ms.
async function processAdvanced(data) {
    const { heavyProcessor } = await import('./heavy-processor.js');
    return heavyProcessor(data);
}
```

**Good**: Explains performance trade-offs and constraints
**Bad**: `// Use cache for speed` (obvious, lacks detail)

### 6. Security-Sensitive Comments

Document security considerations:

```javascript
// Security: Sanitize user input to prevent XSS attacks.
// textContent doesn't parse HTML, preventing script injection.
// NEVER use innerHTML with user input.
element.textContent = userInput;

// Use cryptographically secure random for tokens.
// Math.random() is NOT secure and predictable.
// crypto.getRandomValues() provides CSPRNG for security-critical operations.
const token = crypto.getRandomValues(new Uint8Array(32));

// Validate origin to prevent CSRF attacks in postMessage handler.
// Accepting messages from any origin would allow malicious sites
// to send commands to our application.
window.addEventListener('message', (event) => {
    if (event.origin !== 'https://trusted-domain.com') {
        return; // Reject untrusted origins
    }
    handleMessage(event.data);
});
```

**Good**: Explains security reasoning
**Bad**: `// Check input` (misses security implication)

### 7. Async/Promise Comments

Explain async patterns and error handling:

```javascript
// Use Promise.all for parallel execution instead of sequential awaits.
// Sequential: 300ms + 200ms + 150ms = 650ms total
// Parallel: max(300ms, 200ms, 150ms) = 300ms total
const [users, posts, comments] = await Promise.all([
    fetchUsers(),
    fetchPosts(),
    fetchComments()
]);

// Wrap in try-catch to prevent unhandled promise rejection.
// fetch() doesn't reject on HTTP errors (404, 500, etc), only network failures.
// Must manually check response.ok to handle HTTP errors.
try {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
} catch (error) {
    logger.error('API request failed', { url, error });
    throw error;
}

// Race condition prevention: Use AbortController to cancel previous request.
// Without cancellation, fast typing could cause responses to arrive out of order,
// displaying stale results over newer ones.
let abortController = null;
async function search(query) {
    if (abortController) {
        abortController.abort(); // Cancel previous request
    }
    abortController = new AbortController();

    return fetch(`/api/search?q=${query}`, {
        signal: abortController.signal
    });
}
```

**Good**: Explains async patterns and why they're necessary
**Bad**: `// Async function` (obvious from syntax)

### 8. TODO/FIXME/HACK Conventions

Use standardized tags for technical debt:

```javascript
// TODO: Refactor this into separate validation module (target: v2.1)
// Current implementation works but violates single responsibility.
// Estimate: 4 hours
function processAndValidate(data) {
    // ...
}

// FIXME: Race condition when multiple workers process same job.
// Occurs under high load (>1000 jobs/second). Need distributed lock.
// Priority: HIGH - Causes duplicate processing ~0.1% of time
// Assigned to: @username, Issue #456
function processJob(jobId) {
    // ...
}

// HACK: Temporary workaround for memory leak in library v2.3
// Remove this when upgrading to v2.4+ which has the fix.
// See: https://github.com/project/issues/123
// Force garbage collection workaround
if (global.gc) global.gc();

// NOTE: This function must be called before DOM ready.
// Event listeners need to be registered before user interactions.
function initializeEventHandlers() {
    // ...
}

// WARNING: Modifying this constant will break authentication.
// Value is hardcoded in legacy mobile apps (iOS 1.2, Android 1.3).
// Cannot change until all users upgrade to v2.0+.
const AUTH_TOKEN_LENGTH = 32;
```

**Format**: `TAG: Description (context)`

- **TODO**: Planned improvement or feature

- **FIXME**: Known bug or issue

- **HACK**: Temporary workaround

- **NOTE**: Important information

- **WARNING**: Critical caution

### 9. Inline Comments (Use Sparingly)

Reserve inline comments for truly non-obvious code:

```javascript
// Good inline comment - explains non-obvious detail
const result = value & 0xFF;  // Mask to get only the last byte

// Bad inline comment - obvious from code
count++;  // Increment count

// Good inline comment - explains magic number
const timeout = 86400000;  // 24 hours in milliseconds

// Bad inline comment - should be constant
const timeout = 86400000;  // Timeout value
// Better: Define constant
const MILLISECONDS_PER_DAY = 86400000;
const timeout = MILLISECONDS_PER_DAY;

// Good inline comment - explains regex pattern
const pattern = /^[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}$/;  // RFC 5322 email format
```

### 10. JSDoc vs. Inline Comments

**JSDoc for API documentation, inline comments for implementation details:**

```javascript
/**
 * Process user payment with fraud detection.
 *
 * @param {Object} payment - Payment details
 * @param {number} payment.amount - Amount in cents
 * @param {string} payment.currency - ISO 4217 currency code
 * @returns {Promise<PaymentResult>} Payment confirmation
 * @throws {FraudError} If payment fails fraud checks
 */
async function processPayment(payment) {
    // Use Luhn algorithm to validate card number before API call.
    // Prevents unnecessary API charges for invalid cards (~15% of attempts).
    if (!validateCardNumber(payment.cardNumber)) {
        throw new ValidationError('Invalid card number');
    }

    // 3D Secure required for EU transactions over €30 (PSD2 compliance).
    // US transactions always skip 3DS for better conversion rates.
    const requires3DS = payment.currency === 'EUR' && payment.amount > 3000;

    return await paymentGateway.charge(payment, { requires3DS });
}
```

**JSDoc**: What the function does, parameters, return values
**Inline comments**: Why implementation choices were made

### 11. What NOT to Comment

**Avoid these comment anti-patterns:**

```javascript
// BAD: Obvious comments
// Set x to 5
const x = 5;

// BAD: Redundant with function name
// Calculate total
function calculateTotal() {
    // ...
}

// BAD: Meta-commentary about code changes
// Changed this from += to = on 2024-01-15
// Fixed bug here
// Updated by John

// BAD: Commented-out code (use version control instead)
// oldFunction();
// return previousValue;

// BAD: Duplicating JSDoc
/**
 * Calculate total price.
 */
function calculateTotal(items) {
    // Calculate total price
    return items.reduce((sum, item) => sum + item.price, 0);
}

// BAD: Vague or unhelpful
// Do stuff
// Handle things
// Process data
```

## Phase 3: Comment Placement Guidelines

### Block Comments
```javascript
// Use block comments before code blocks they describe.
// Separate from previous code with blank line.
// Keep lines under 80 characters.

function myFunction() {
    // Block comments inside functions go before the relevant section
    // with proper indentation.
    codeSection();
}
```

### Inline Comments
```javascript
// Place inline comments sparingly, separated by at least 2 spaces
const result = complexCalculation();  // Explanation when truly needed
```

### Section Dividers
```javascript
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
   - Good: "Reverse loop to avoid index shifting during removal" (why)

3. **Is Accurate and Current**
   - Does comment match current code behavior?
   - Is referenced information still valid?
   - Are linked issues/docs still relevant?

4. **Is Concise**
   - Can you say the same thing in fewer words?
   - Are you repeating information from JSDoc or type annotations?
   - Is every sentence necessary?

5. **Is Properly Formatted**
   - Correct grammar and spelling
   - Proper indentation
   - Follows project conventions

## Phase 5: Refactoring vs. Commenting

Sometimes improving code readability is better than adding comments:

### When to Refactor Instead of Comment

```javascript
// BAD: Comment explaining complex logic
// Calculate discount: 10% for orders > $100, 5% for > $50, 0% otherwise
const discount = total > 100 ? 0.10 : (total > 50 ? 0.05 : 0.0);

// GOOD: Extract to well-named function (self-documenting)
function calculateDiscount(total) {
    if (total > 100) return 0.10;
    if (total > 50) return 0.05;
    return 0.0;
}

// BAD: Comment explaining magic number
const result = value * 1.07;  // Apply sales tax

// GOOD: Named constant (self-documenting)
const SALES_TAX_RATE = 1.07;
const result = value * SALES_TAX_RATE;

// BAD: Comment explaining complex condition
if (user.age >= 18 && user.hasLicense && !user.hasViolations) {
    // User is eligible to rent
}

// GOOD: Extract to well-named function
if (isEligibleToRent(user)) {
    // ...
}

// BAD: Comment explaining callback purpose
items.filter(item => {
    // Check if item is valid and in stock
    return item.isValid && item.inStock;
});

// GOOD: Named function for clarity
const isAvailable = item => item.isValid && item.inStock;
items.filter(isAvailable);
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
   # - fixme (npm package)
   # - ESLint custom rules for comment tracking
   # - GitHub Actions to track TODO/FIXME trends
   ```

## Output Format

Please provide comment additions in this format:

### File-by-File Report
```markdown
## File: src/components/UserProfile.js

### Line 45: Complex Algorithm Comment
**Code Section**:
```javascript
[relevant code]
```

**Added Comment**:
```javascript
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

- Async/Promise patterns: [count]

- Browser compatibility: [count]

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
   - Avoid redundancy with JSDoc
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
  - eslint:
      # Configure comment rules
      rules:
        - no-warning-comments  # Track TODO/FIXME
        - spaced-comment  # Enforce spacing
        - capitalized-comments  # Enforce style

  - jsdoc:
      # Enforce JSDoc standards
      # Separate from inline comments

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
   ```javascript
   // BAD
   let count = 0;  // Initialize count to zero

   // GOOD (no comment needed - obvious from code)
   let count = 0;
   ```

2. **Don't Duplicate JSDoc**
   ```javascript
   // BAD
   /**
    * Calculate total price of items.
    */
   function calculateTotal(items) {
       // Calculate total price of items
       return items.reduce((sum, item) => sum + item.price, 0);
   }

   // GOOD
   /**
    * Calculate total price of items.
    */
   function calculateTotal(items) {
       return items.reduce((sum, item) => sum + item.price, 0);
   }
   ```

3. **Don't Leave Commented-Out Code**
   ```javascript
   // BAD
   // oldImplementation();
   // previousApproach();
   newImplementation();

   // GOOD (use version control)
   newImplementation();
   ```

4. **Don't Write Vague Comments**
   ```javascript
   // BAD: "Handle edge case"
   // BAD: "Fix issue here"
   // BAD: "Do special processing"

   // GOOD: Specific and informative
   // Handle empty array to prevent reduce() error with no initial value
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
