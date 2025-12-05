---
template_id: python_comments
template_name: Comments - Python
version: 1.0.0
last_updated: 2025-12-03
language: Python
category: documentation
phase: comments
difficulty: beginner
estimated_time_hours: 1-2
prerequisites: []
tools:

  - pytest (8.3.4+)

  - black (24.12.0)

  - mypy (1.13.0)

  - ruff
tags:

  - documentation

  - documentation

  - python
---
# Python Strategic Comments

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

### When NOT to Comment

- [ ] Obvious code that's self-explanatory

- [ ] Information already in docstrings

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
# Python Strategic Comments Request

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

Please add strategic comments to this Python project following this protocol:

## Phase 1: Analysis & Comment Identification

1. **Analyze Codebase for Comment Opportunities**
   Review the code to identify sections that would benefit from comments:

   - Complex algorithms or business logic

   - Non-obvious implementation decisions

   - Workarounds for known issues

   - Performance-critical sections

   - Security-sensitive operations

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

```python
# Calculate optimal route using A* pathfinding algorithm.
# We use A* instead of Dijkstra because our graph has a reliable heuristic
# (Euclidean distance), which reduces search time by ~40% in testing.
# Trade-off: Uses more memory (O(n) vs O(log n)) but acceptable for our
# typical graph sizes (<1000 nodes).
def find_optimal_route(start, end, graph):
    open_set = {start}
    came_from = {}
    # ... implementation
```

**Good**: Explains algorithm choice, trade-offs, and why it's appropriate
**Bad**: `# Find route` (obvious from function name)

### 2. Business Logic Comments

Document domain rules and business decisions:

```python
# Business rule: Premium users get 30-day refund window, standard users get 14 days.
# This differs from the legal minimum (7 days) to improve customer satisfaction.
# See: Business Policy Document v3.2, Section 4.1
refund_window = 30 if user.is_premium else 14

# Calculate late fee: $5 per day, capped at 50% of original amount.
# Cap prevents fees from exceeding loan value (legal requirement in CA).
late_fee = min(days_late * 5, original_amount * 0.5)
```

**Good**: Explains business rule, reasoning, and references
**Bad**: `# Set refund window` (doesn't explain the logic)

### 3. Non-Obvious Implementation Comments

Clarify code that isn't self-explanatory:

```python
# Use base64 encoding instead of direct binary storage because our database
# connection doesn't handle binary data reliably (issue #342).
# TODO: Switch to binary when we upgrade to PostgreSQL 14+
encoded_data = base64.b64encode(binary_data).decode('utf-8')

# Reverse iteration prevents index shifting during removal.
# Forward iteration would skip elements after each deletion.
for i in range(len(items) - 1, -1, -1):
    if should_remove(items[i]):
        del items[i]
```

**Good**: Explains why approach was chosen and what problem it solves
**Bad**: `# Encode data to base64` (obvious from code)

### 4. Workaround Comments

Document workarounds for bugs or limitations:

```python
# WORKAROUND: requests library has a memory leak in sessions with keep-alive.
# Creating new session for each request until fixed in requests 3.0.
# See: https://github.com/psf/requests/issues/4937
# TODO: Remove this workaround after upgrading to requests>=3.0
session = requests.Session()
response = session.get(url)
session.close()

# HACK: Sleep 100ms to avoid race condition in third-party API.
# Their rate limiter returns 429 even when we're under the limit if
# requests arrive too close together. Reported to vendor 2024-01-15.
time.sleep(0.1)
```

**Good**: Explains issue, links to tracking, includes TODO for removal
**Bad**: `# Wait a bit` (doesn't explain why)

### 5. Performance-Critical Comments

Explain optimization decisions:

```python
# Cache results because recalculation is expensive (O(n²) complexity).
# Cache invalidated on data updates via observer pattern.
# Memory impact: ~10MB for typical dataset of 10k items.
@lru_cache(maxsize=1000)
def calculate_statistics(data):
    # ... expensive calculation

# Use generator instead of list comprehension to avoid loading
# entire dataset into memory. Processes 1M+ records with <100MB RAM.
return (process_item(item) for item in large_dataset)
```

**Good**: Explains performance trade-offs and constraints
**Bad**: `# Use cache for speed` (obvious, lacks detail)

### 6. Security-Sensitive Comments

Document security considerations:

```python
# Security: Always use parameterized queries to prevent SQL injection.
# User input must NEVER be concatenated directly into SQL strings.
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# Constant-time comparison prevents timing attacks that could
# leak information about the correct token value.
if secrets.compare_digest(provided_token, expected_token):
    grant_access()
```

**Good**: Explains security reasoning
**Bad**: `# Check token` (misses security implication)

### 7. TODO/FIXME/HACK Conventions

Use standardized tags for technical debt:

```python
# TODO: Refactor this into separate validation module (target: v2.1)
# Current implementation works but violates single responsibility.
# Estimate: 4 hours
def process_and_validate(data):
    pass

# FIXME: Race condition when multiple workers process same job.
# Occurs under high load (>1000 jobs/second). Need distributed lock.
# Priority: HIGH - Causes duplicate processing ~0.1% of time
# Assigned to: @username, Issue #456
def process_job(job_id):
    pass

# HACK: Temporary workaround for memory leak in library v2.3
# Remove this when upgrading to v2.4+ which has the fix.
# See: https://github.com/project/issues/123
gc.collect()
```

**Format**: `TAG: Description (context)`

- **TODO**: Planned improvement or feature

- **FIXME**: Known bug or issue

- **HACK**: Temporary workaround

- **NOTE**: Important information

- **WARNING**: Critical caution

### 8. Inline Comments (Use Sparingly)

Reserve inline comments for truly non-obvious code:

```python
# Good inline comment - explains non-obvious detail
result = value & 0xFF  # Mask to get only the last byte

# Bad inline comment - obvious from code
count += 1  # Increment count

# Good inline comment - explains magic number
timeout = 86400  # 24 hours in seconds

# Bad inline comment - should be constant
timeout = 86400  # Timeout value
# Better: Define constant
SECONDS_PER_DAY = 86400
timeout = SECONDS_PER_DAY
```

### 9. What NOT to Comment

**Avoid these comment anti-patterns:**

```python
# BAD: Obvious comments
# Set x to 5
x = 5

# BAD: Redundant with function name
# Calculate total
def calculate_total():
    pass

# BAD: Meta-commentary about code changes
# Changed this from += to = on 2024-01-15
# Fixed bug here
# Updated by John

# BAD: Commented-out code (use version control instead)
# old_function()
# return previous_value

# BAD: Duplicating type information
# param1 (str): param1 is a string
def function(param1: str):
    pass

# BAD: Vague or unhelpful
# Do stuff
# Handle things
# Process data
```

## Phase 3: Comment Placement Guidelines

### Block Comments
```python
# Use block comments before code blocks they describe.
# Separate from previous code with blank line.
# Keep lines under 80 characters.

def function():
    # Block comments inside functions go before the relevant section
    # with proper indentation.
    code_section()
```

### Inline Comments
```python
# Place inline comments sparingly, separated by at least 2 spaces
result = complex_calculation()  # Explanation when truly needed
```

### Section Dividers
```python
# ===== Data Processing Section =====
# Use sparingly for major logical sections in long files

# ----- Helper Functions -----
# Or use simpler dividers for subsections
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

   - Are you repeating information from docstrings or type hints?

   - Is every sentence necessary?

5. **Is Properly Formatted**

   - Correct grammar and spelling

   - Proper indentation

   - Follows project conventions

## Phase 5: Refactoring vs. Commenting

Sometimes improving code readability is better than adding comments:

### When to Refactor Instead of Comment

```python
# BAD: Comment explaining complex logic
# Calculate discount: 10% for orders > $100, 5% for > $50, 0% otherwise
discount = 0.10 if total > 100 else (0.05 if total > 50 else 0.0)

# GOOD: Extract to well-named function (self-documenting)
def calculate_discount(total):
    if total > 100:
        return 0.10
    elif total > 50:
        return 0.05
    return 0.0

# BAD: Comment explaining magic number
result = value * 1.07  # Apply sales tax

# GOOD: Named constant (self-documenting)
SALES_TAX_RATE = 1.07
result = value * SALES_TAX_RATE

# BAD: Comment explaining complex condition
if (user.age >= 18 and user.has_license and not user.has_violations):
    # User is eligible to rent

# GOOD: Extract to well-named function
if is_eligible_to_rent(user):
    pass
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

   # Track technical debt
   # Consider tools like:
   # - fixme (npm package)
   # - pylint --notes=TODO,FIXME
   ```

## Output Format

Please provide comment additions in this format:

### File-by-File Report
```markdown
## File: src/package/module.py

### Line 45: Complex Algorithm Comment
**Code Section**:
```python
[relevant code]
```

**Added Comment**:
```python
# [strategic comment explaining why/how]
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

   - Avoid redundancy with docstrings/type hints

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

## Tools for Comment Quality

```yaml
# Recommended tools
tools:

  - pylint:
      # Check for missing docstrings, not inline comments
      # Configure to allow strategic commenting
      notes: ["TODO", "FIXME", "HACK", "NOTE", "WARNING"]

  - grep/ripgrep:
      # Find technical debt tags
      patterns:

        - "TODO"

        - "FIXME"

        - "HACK"

  - custom-scripts:
      # Track comment metrics
      # - Comment-to-code ratio
      # - TODO/FIXME count over time
      # - Outdated comment detection
```

## Common Mistakes to Avoid

1. **Don't Explain Obvious Code**
   ```python
   # BAD
   count = 0  # Initialize count to zero

   # GOOD (no comment needed - obvious from code)
   count = 0
   ```

2. **Don't Duplicate Docstrings**
   ```python
   # BAD
   def calculate_total(items):
       """Calculate total price of items."""
       # Calculate total price of items
       return sum(item.price for item in items)

   # GOOD
   def calculate_total(items):
       """Calculate total price of items."""
       return sum(item.price for item in items)
   ```

3. **Don't Leave Commented-Out Code**
   ```python
   # BAD
   # old_implementation()
   # previous_approach()
   new_implementation()

   # GOOD (use version control)
   new_implementation()
   ```

4. **Don't Write Vague Comments**
   ```python
   # BAD: "Handle edge case"
   # BAD: "Fix issue here"
   # BAD: "Do special processing"

   # GOOD: Specific and informative
   # Handle empty list case to prevent IndexError in downstream code
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
