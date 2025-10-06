# Phase 2: Code Comments & Inline Documentation

Add strategic code comments that explain reasoning, non-obvious logic, and important decisions.

---

## Overview

This phase focuses on adding high-value comments that explain the "why" behind code decisions, complex algorithms, performance optimizations, and non-obvious behavior. Following organizational standards, comments should be placed above code blocks (never inline) and focus on reasoning rather than describing what code does.

### Time Estimate
- **Analysis**: 30-60 minutes
- **Comment Writing**: 30-60 minutes
- **Review**: 15-30 minutes
- **Total**: 1-2 hours

---

## Copy-Paste Prompt

```
Please help me add strategic code comments to my Python project following organizational standards.

**Project Context:**
- Project name: [YOUR_PROJECT_NAME]
- Source code location: src/
- Current comment status: [None / Sparse / Needs improvement]

**Comment Standards:**

### Critical Rules
1. **No inline comments**: Comments must be on separate lines above code
2. **Explain "why" not "what"**: Focus on reasoning and decisions, not obvious operations
3. **No meta-commentary**: No editing history, revision notes, or TODO markers in production code
4. **Above code blocks**: Comments should precede the code they explain
5. **Descriptive focus**: Explain logic, algorithms, performance, security considerations

---

## Comment Categories

### 1. Algorithm and Logic Explanations

Add comments explaining complex algorithms, non-obvious logic, and implementation approaches:

**Pattern:**
```python
# [Why this algorithm/approach was chosen]
# [Key characteristics or complexity]
# [Important constraints or considerations]
[code implementation]
```

**Examples:**
```python
# Use binary search for O(log n) performance on sorted data
# This is critical for large datasets (>10k items)
result = binary_search(sorted_list, target)

# Implement breadth-first search to find shortest path
# Depth-first would be more memory efficient but wouldn't guarantee shortest path
path = bfs_shortest_path(graph, start, end)

# Use dynamic programming to avoid recalculating overlapping subproblems
# Naive recursive approach would be O(2^n), this reduces to O(n^2)
memo = {}
result = fibonacci_dp(n, memo)

# Apply Knuth-Morris-Pratt algorithm for O(n+m) string matching
# Simple substring search would be O(n*m) for large texts
matches = kmp_search(text, pattern)
```

**Apply to:**
- Complex algorithms
- Non-obvious logic flows
- Algorithm selection decisions
- Complexity considerations

---

### 2. Performance Optimizations

Explain performance-related decisions and optimizations:

**Pattern:**
```python
# [Performance consideration or optimization]
# [Expected impact or measurement]
# [Trade-offs if any]
[optimized code]
```

**Examples:**
```python
# Cache results to avoid expensive API calls during batch processing
# API rate limit is 100 calls/minute, caching prevents exceeding it
if key not in self.cache:
    self.cache[key] = expensive_api_call(key)

# Use thread pool for I/O-bound operations
# Testing showed 4x performance improvement with 8 threads
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(process_item, item) for item in items]

# Lazy evaluation to avoid loading entire dataset into memory
# Dataset can be 10GB+, streaming reduces memory to <100MB
for chunk in pd.read_csv(filename, chunksize=10000):
    process_chunk(chunk)

# Preallocate list for known size to avoid repeated reallocations
# Reduces memory operations from O(n) to O(1)
results = [None] * len(items)
for i, item in enumerate(items):
    results[i] = process(item)

# Use set for O(1) lookups instead of list O(n) scans
# Dataset contains 100k+ items where lookup performance is critical
valid_ids = set(valid_id_list)
if item_id in valid_ids:
    process_item(item_id)
```

**Apply to:**
- Caching strategies
- Data structure choices
- Algorithm optimization
- Memory management
- Concurrency decisions

---

### 3. Security Considerations

Document security-related implementations:

**Pattern:**
```python
# [Security concern being addressed]
# [Approach taken and why]
# [Relevant standards or best practices]
[security implementation]
```

**Examples:**
```python
# Sanitize user input to prevent SQL injection
# Use parameterized queries per OWASP guidelines
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# Hash passwords with bcrypt before storage
# NIST recommends bcrypt with work factor >= 10
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))

# Implement rate limiting to prevent brute force attacks
# Allow max 5 failed attempts per IP per minute
if failed_attempts_count(ip_address) > 5:
    raise RateLimitExceeded("Too many failed attempts")

# Validate and sanitize file uploads to prevent path traversal
# Ensure filename contains no directory separators or special characters
safe_filename = secure_filename(uploaded_file.filename)

# Use constant-time comparison to prevent timing attacks
# Standard == operator leaks information through execution time
if hmac.compare_digest(provided_token, expected_token):
    authenticate_user()
```

**Apply to:**
- Input validation and sanitization
- Authentication and authorization
- Cryptographic operations
- Rate limiting
- Data protection

---

### 4. Error Handling and Edge Cases

Explain error handling strategies and edge case handling:

**Pattern:**
```python
# [Edge case or error condition being handled]
# [Why this handling approach]
# [Implications if not handled]
[handling code]
```

**Examples:**
```python
# Handle empty dataset gracefully without crashing
# Downstream consumers expect consistent return type
if not data:
    return []

# Retry with exponential backoff for transient network failures
# API occasionally returns 503 under load, usually recovers in seconds
for attempt in range(max_retries):
    try:
        return api_call()
    except TransientError:
        wait_time = min(2 ** attempt, 32)
        time.sleep(wait_time)

# Guard against division by zero in calculation
# Zero values are valid input but would crash without check
if denominator == 0:
    return default_value

# Handle timezone-naive datetime by assuming UTC
# Legacy data may lack timezone info, UTC is safest assumption
if dt.tzinfo is None:
    dt = dt.replace(tzinfo=timezone.utc)

# Validate file exists before attempting to read
# File may be deleted between check and use, but reduces common errors
if not os.path.exists(filepath):
    raise FileNotFoundError(f"File not found: {filepath}")
```

**Apply to:**
- Error handling strategies
- Edge case handling
- Graceful degradation
- Defensive programming

---

### 5. Business Logic and Domain Knowledge

Document business rules and domain-specific logic:

**Pattern:**
```python
# [Business rule or domain constraint]
# [Source of requirement if applicable]
# [Special cases or exceptions]
[business logic]
```

**Examples:**
```python
# Business rule: Orders over $100 receive free shipping
# Per marketing policy dated 2024-01-15
if order_total > 100:
    shipping_cost = 0

# Apply FIFO inventory accounting per GAAP standards
# Must track each lot's purchase price separately
oldest_lot = get_oldest_inventory_lot()
cost_basis = oldest_lot.unit_price

# Calculate overtime as 1.5x rate after 40 hours per week
# Complies with Fair Labor Standards Act requirements
regular_hours = min(hours_worked, 40)
overtime_hours = max(hours_worked - 40, 0)
total_pay = (regular_hours * rate) + (overtime_hours * rate * 1.5)

# Apply discount tiers based on customer loyalty level
# Tier structure defined in customer_benefits.md
if customer.loyalty_level == 'gold':
    discount = 0.15
elif customer.loyalty_level == 'silver':
    discount = 0.10
else:
    discount = 0.05
```

**Apply to:**
- Business rule implementations
- Domain-specific calculations
- Regulatory compliance
- Policy implementations

---

### 6. Integration and External Dependencies

Explain external integrations and API interactions:

**Pattern:**
```python
# [External system or API being integrated]
# [Key behaviors or limitations]
# [Error handling considerations]
[integration code]
```

**Examples:**
```python
# Stripe API requires amount in cents, not dollars
# Failing to convert causes 100x charge errors
amount_cents = int(amount_dollars * 100)
stripe.Charge.create(amount=amount_cents)

# AWS S3 limits object keys to 1024 bytes
# Truncate and hash long filenames to stay within limit
if len(key) > 1000:
    key = f"{key[:950]}_{hashlib.md5(key.encode()).hexdigest()}"

# Google Maps API has daily quota of 25,000 requests
# Cache results for 24 hours to stay within limits
cached_result = cache.get(address_key)
if cached_result:
    return cached_result

# SendGrid requires RFC 5322 compliant email addresses
# Validate before sending to avoid API rejection
if not validate_email_rfc5322(email):
    raise InvalidEmailError(f"Invalid email format: {email}")
```

**Apply to:**
- Third-party API integrations
- External service limitations
- Protocol requirements
- Integration constraints

---

### 7. Data Structure and State Management

Explain data structure choices and state management:

**Pattern:**
```python
# [Data structure choice and reasoning]
# [Access patterns and performance]
# [Thread safety or concurrency considerations]
[data structure usage]
```

**Examples:**
```python
# Use OrderedDict to maintain insertion order for display
# Standard dict maintains order in Python 3.7+ but OrderedDict is explicit
display_items = OrderedDict()

# Thread-safe queue for producer-consumer pattern
# Multiple workers may access simultaneously
work_queue = queue.Queue(maxsize=1000)

# Use weak references to avoid circular reference memory leaks
# Parent-child relationships could prevent garbage collection
self.children = weakref.WeakSet()

# Store as tuple instead of list for immutability
# Coordinates should never change after creation
position = (x, y, z)

# Use defaultdict to simplify grouping logic
# Eliminates need for explicit key existence checks
groups = defaultdict(list)
for item in items:
    groups[item.category].append(item)
```

**Apply to:**
- Data structure selection
- State management
- Thread safety
- Memory management

---

## Anti-Patterns to Avoid

### ❌ Inline Comments
```python
# Bad: Inline comment
result = process(data)  # Process the data
x = x + 1  # Increment x
```

### ❌ Obvious Comments
```python
# Bad: States the obvious
# Loop through items
for item in items:
    # Print the item
    print(item)
```

### ❌ Meta-Commentary
```python
# Bad: Editing history
# Updated 2024-10-05: Changed algorithm
# TODO: Fix this later
# HACK: Temporary workaround
```

### ❌ Commented-Out Code
```python
# Bad: Keeping old code
# old_function(data)
new_function(data)
```

### ✅ Good Examples
```python
# Use binary search for O(log n) performance on sorted data
result = binary_search(sorted_list, target)

# Cache to avoid expensive API calls (100 calls/min limit)
if key not in cache:
    cache[key] = api_call(key)

# Apply exponential backoff for rate-limited APIs
for attempt in range(retries):
    wait_time = min(2 ** attempt, 32)
    time.sleep(wait_time)
```

---

## Deliverables

Please add strategic comments to:

1. **Complex algorithms**: Explain approach and complexity
2. **Performance optimizations**: Document reasoning and impact
3. **Security implementations**: Note standards and protections
4. **Error handling**: Explain edge cases and strategies
5. **Business logic**: Document rules and requirements
6. **External integrations**: Note limitations and behaviors
7. **Data structures**: Explain choices and access patterns

**Output Format:**
- Provide code files with comments added
- Comments above relevant code blocks
- No inline comments
- Focus on non-obvious aspects

**Quality Checks:**
- [ ] No inline comments
- [ ] Explains "why" not "what"
- [ ] No meta-commentary
- [ ] Complex logic explained
- [ ] Performance reasoning documented
- [ ] Security considerations noted
- [ ] Business rules documented

Complete and pause. Confirm comments add value and follow standards before proceeding to Phase 3.
```

---

## Success Criteria

- ✅ All complex algorithms explained
- ✅ Performance optimizations documented
- ✅ Security considerations noted
- ✅ No inline comments
- ✅ Comments focus on "why"
- ✅ Business logic documented
- ✅ Integration constraints explained

---

## Common Issues

### Issue: Too many obvious comments
**Solution**: Remove comments that just restate code. Focus on non-obvious reasoning.

### Issue: Inline comments present
**Solution**: Move all comments to separate lines above code.

### Issue: Meta-commentary in code
**Solution**: Move TODOs to issue tracker, remove revision history.

### Issue: Insufficient detail
**Solution**: Explain full context including performance impact, security implications, business requirements.

---

## Next Steps

After completing Phase 2, proceed to:
- **Phase 3**: Create user-facing documentation (README, guides, how-tos)
- **Phase 4**: Generate technical documentation for developers
