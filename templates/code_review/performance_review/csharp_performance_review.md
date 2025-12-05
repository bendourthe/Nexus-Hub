---
template_id: csharp_performance_review
template_name: Performance Review - C#
version: 1.0.0
last_updated: 2025-12-03
language: C#
category: code_review
phase: performance_review
phase_number: 4
difficulty: advanced
estimated_time_hours: 2-3
prerequisites:

  - code_review/security_review/csharp_security_review.md
related_templates:

  - code_review/code_quality/csharp_code_quality.md
tools:

  - NUnit (4.2.2)
  - xUnit
  - MSTest
tags:

  - code-review
  - performance
  - code-review
  - c#
---
# C# Performance Review

## Objective
Systematically identify performance bottlenecks, inefficient algorithms, and resource usage issues in .NET applications. Provide data-driven optimization recommendations to improve application speed, scalability, and resource efficiency.

## Output Directory Structure

All outputs should be saved in organized directories:

```
review/performance_review/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `review/performance_review/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Review Checklist

### Performance Profiling

- [ ] CPU profiling completed (dotTrace, PerfView, VS Profiler)

- [ ] Memory profiling performed (dotMemory, PerfView)

- [ ] GC (Garbage Collection) behavior analyzed

- [ ] Hot paths and bottlenecks identified

- [ ] Method-level timing measurements captured

### Algorithm Efficiency

- [ ] Time complexity evaluated (O(n), O(n²), etc.)

- [ ] Space complexity assessed

- [ ] Inefficient loops identified (nested, redundant)

- [ ] LINQ query efficiency reviewed

- [ ] Data structure choices evaluated

### Database Performance

- [ ] Query execution times measured (EF Core query logging)

- [ ] N+1 query problems identified

- [ ] Missing indexes detected

- [ ] Query optimization opportunities documented

- [ ] Connection pooling configured properly

### Memory Management

- [ ] Memory leaks detected

- [ ] Large object allocations identified (LOH)

- [ ] GC pressure assessed (Gen 0, Gen 1, Gen 2 collections)

- [ ] Caching strategies reviewed

- [ ] IDisposable implementation verified

### I/O & Network

- [ ] File I/O operations profiled

- [ ] Network call latency measured

- [ ] Synchronous vs asynchronous patterns evaluated

- [ ] HttpClient usage reviewed (reuse, pooling)

- [ ] Batching opportunities identified

### Concurrency & Parallelism

- [ ] async/await usage evaluated

- [ ] Parallel processing opportunities identified (Parallel.ForEach, PLINQ)

- [ ] Thread pool usage assessed

- [ ] Task management reviewed

- [ ] Deadlock and race condition risks checked

## Severity Classification

Use this framework to classify and prioritize all findings from the code review.

### CRITICAL (Fix Immediately)

**Definition:** Issues that create immediate risks to system stability, data integrity, or compliance.

**Examples:**
- Security vulnerabilities (SQL injection, XSS, authentication bypass)
- Resource leaks (unclosed connections, file handles, memory leaks)
- Data loss risks (destructive operations without validation)
- Thread safety violations (race conditions, deadlocks)
- Compliance violations (GDPR, HIPAA, PCI-DSS)

**Action Required:**
- Block deployment until fixed
- Require hotfix within 24 hours
- Add tests to prevent regression
- Document root cause and fix

---

### HIGH (Fix Before Next Release)

**Definition:** Issues that significantly impact maintainability, performance, or correctness but don't cause immediate failures.

**Examples:**
- Incorrect business logic (wrong calculations, flawed algorithms)
- Performance bottlenecks (O(n²) algorithms, missing indexes, inefficient queries)
- Memory inefficiency (loading large datasets into memory unnecessarily)
- Breaking API changes without deprecation
- Missing critical error handling (network errors, API failures not caught)

**Action Required:**
- Schedule fix in current sprint
- Cannot release without resolution
- Update documentation
- Performance test after fix

---

### MEDIUM (Fix in Next Cycle)

**Definition:** Code smells and technical debt that reduce maintainability but don't affect correctness.

**Examples:**
- High complexity (cyclomatic complexity >10, functions >100 lines)
- Code duplication (>10 lines duplicated across modules)
- Poor naming (unclear variable/function names, inconsistent conventions)
- Missing tests (<80% coverage on critical paths)
- Incomplete error messages (no context for debugging)

**Action Required:**
- Add to backlog
- Prioritize in next sprint planning
- Consider during refactoring opportunities
- Track technical debt metrics

---

### LOW (Nice to Have)

**Definition:** Style inconsistencies and minor optimizations that don't impact functionality.

**Examples:**
- Style violations (linting warnings, formatting issues)
- Minor performance optimizations (in non-critical code paths)
- Missing documentation on helper functions
- Verbose code that could be more concise
- Debug statements left in code

**Action Required:**
- Fix opportunistically during other work
- Batch with other low-priority changes
- Good for new contributors
- Can be deferred indefinitely

---

## Severity Assignment Guidelines

**When to Escalate Severity:**
- Issue affects **production environment** → escalate one level
- Issue affects **customer-facing features** → escalate one level
- Issue has **no workaround** → escalate one level
- Issue appears in **multiple locations** → escalate one level

**When to De-escalate Severity:**
- Issue only in **test/development code** → de-escalate one level
- Issue has **easy workaround** → de-escalate one level
- Issue is **isolated to single module** → de-escalate one level
- Issue **rarely executed** (edge case) → de-escalate one level

**Examples:**
- Memory leak in production API: **HIGH → CRITICAL** (production + customer-facing)
- Style violation in test file: **LOW → Ignore** (test code + style only)
- Duplicated logic across 15 modules: **MEDIUM → HIGH** (multiple locations)

---

## Reporting Format

For each finding, include:

**1. Severity Level:** [CRITICAL/HIGH/MEDIUM/LOW]

**2. Location:** File path and line numbers

**3. Issue Description:** What's wrong and why it matters

**4. Impact:** Specific consequences of not fixing

**5. Recommendation:** How to fix (with code example if applicable)

**6. Effort Estimate:** Time to fix (hours/days)

**Example Finding:**
```markdown
### HIGH: Performance Bottleneck in User Search

**Location:** `src/services/userService:145-167`

**Issue:** The user search function loads all users into memory and performs linear search on every request.

**Impact:**
- Response time degrades with user count (currently 500ms for 10k users)
- High memory usage (50MB+ per request)
- Poor scalability (can't handle >100k users)

**Recommendation:**
Move filtering to database with indexed query:

- Add database index on search fields
- Use database LIKE/ILIKE queries
- Implement pagination (limit results to 50)
- Add caching for common searches

**Effort:** 3 hours (2 hours implementation + 1 hour testing)

**Priority:** Must fix before next release (performance SLA violation)
```

---


## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C# Performance Review

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="review/performance_review"
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

## Review Protocol

Please perform a comprehensive performance review of this .NET application following this protocol:

## Phase 1: Performance Profiling Setup

1. **CPU Profiling**
   ```powershell
   # Using dotnet-trace (cross-platform)
   dotnet tool install --global dotnet-trace
   dotnet trace collect --process-id <pid> --profile cpu-sampling

   # Using PerfView (Windows)
   PerfView.exe collect -CircularMB:500 -ThreadTime -NoGui /AcceptEULA

   # Visual Studio Profiler
   # Debug > Performance Profiler > CPU Usage
   ```

2. **Memory Profiling**
   ```powershell
   # Using dotnet-counters
   dotnet tool install --global dotnet-counters
   dotnet counters monitor --process-id <pid> --counters System.Runtime

   # Using dotnet-gcdump
   dotnet tool install --global dotnet-gcdump
   dotnet gcdump collect -p <pid>

   # Analyze with PerfView or Visual Studio
   ```

3. **Application Insights / Telemetry**
   ```csharp
   // Ensure telemetry is configured
   services.AddApplicationInsightsTelemetry();

   // Custom performance tracking
   using var operation = telemetryClient.StartOperation<RequestTelemetry>("OperationName");
   // ... operation code ...
   operation.Telemetry.Success = true;
   ```

## Phase 2: Bottleneck Identification

1. **Analyze Profiling Results**
   - Identify methods consuming >5% of total time
   - Find methods called excessive times
   - Locate memory-intensive operations
   - Identify async over sync issues
   - Review GC statistics (Gen 0/1/2 collections, pause times)

2. **Hot Path Analysis**
   - Map critical execution paths
   - Measure end-to-end latency
   - Identify slowest endpoints/operations
   - Document user-facing performance impacts

3. **Resource Usage Patterns**
   - CPU utilization during typical operations
   - Memory growth patterns over time
   - GC pressure and frequency
   - Thread pool starvation indicators
   - Network bandwidth usage

## Phase 3: Algorithm Efficiency Review

1. **Time Complexity Analysis**
   - Review loops and nested iterations
   - Identify O(n²) or worse algorithms
   - Check for redundant computations
   - Assess search and sort operations

2. **Common Performance Anti-Patterns**
   ```csharp
   // Inefficient patterns to search for:

   // 1. LINQ queries causing multiple enumerations
   var data = GetExpensiveData();
   if (data.Any()) // First enumeration
   {
       var first = data.First(); // Second enumeration - BAD
   }
   // Better: materialize once
   var data = GetExpensiveData().ToList();

   // 2. String concatenation in loops
   string result = "";
   foreach (var item in items)
   {
       result += item; // BAD: creates new string each time
   }
   // Better: use StringBuilder
   var sb = new StringBuilder();
   foreach (var item in items)
       sb.Append(item);

   // 3. Unnecessary boxing/unboxing
   ArrayList list = new ArrayList(); // BAD: causes boxing
   list.Add(1); // int boxed to object
   // Better: use generic collections
   List<int> list = new List<int>();

   // 4. Exceptions for control flow
   try
   {
       var value = dictionary[key]; // BAD: throws if key missing
   }
   catch (KeyNotFoundException)
   {
       // Handle missing key
   }
   // Better: use TryGetValue
   if (dictionary.TryGetValue(key, out var value))
   {
       // Use value
   }

   // 5. Synchronous I/O blocking async methods
   public async Task<string> GetDataAsync()
   {
       var data = File.ReadAllText(path); // BAD: blocking sync I/O
       return await ProcessAsync(data);
   }
   // Better: use async I/O
   public async Task<string> GetDataAsync()
   {
       var data = await File.ReadAllTextAsync(path);
       return await ProcessAsync(data);
   }

   // 6. Closure allocations in hot paths
   for (int i = 0; i < 1000000; i++)
   {
       DoWork(() => Console.WriteLine(i)); // BAD: allocates closure each iteration
   }
   // Better: avoid closure or use static local function

   // 7. Not disposing IDisposable objects
   var stream = new MemoryStream(); // BAD: not disposed
   // Use data...
   // Better: use using statement
   using var stream = new MemoryStream();
   ```

3. **LINQ Performance Issues**
   ```csharp
   // Bad: Multiple enumeration
   var query = items.Where(x => x.IsActive);
   var count = query.Count(); // First enumeration
   var first = query.First(); // Second enumeration

   // Better: Materialize once
   var activeItems = items.Where(x => x.IsActive).ToList();
   var count = activeItems.Count;
   var first = activeItems[0];

   // Bad: Inefficient query
   var result = items.Where(x => x.Age > 18)
                     .OrderBy(x => x.Name)
                     .Take(10)
                     .ToList();
   // Better: Order less data
   var result = items.Where(x => x.Age > 18)
                     .Take(10)
                     .OrderBy(x => x.Name)
                     .ToList();

   // Bad: Using Any() then First()
   if (items.Any(x => x.IsActive))
   {
       var item = items.First(x => x.IsActive); // Re-searches
   }
   // Better: Use FirstOrDefault once
   var item = items.FirstOrDefault(x => x.IsActive);
   if (item != null)
   {
       // Use item
   }
   ```

## Phase 4: Entity Framework Core Performance

1. **Query Performance Testing**
   ```csharp
   // Enable query logging
   optionsBuilder.LogTo(Console.WriteLine, LogLevel.Information)
                 .EnableSensitiveDataLogging()
                 .EnableDetailedErrors();

   // Or use logging in Startup
   services.AddDbContext<MyContext>(options =>
       options.UseSqlServer(connectionString)
              .LogTo(Console.WriteLine, LogLevel.Information));
   ```

2. **N+1 Query Detection**
   ```csharp
   // Bad: N+1 queries
   var posts = context.Posts.ToList(); // 1 query
   foreach (var post in posts)
   {
       var author = post.Author.Name; // N queries (lazy loading)
   }

   // Good: Eager loading
   var posts = context.Posts
                      .Include(p => p.Author)
                      .ToList(); // 1 or 2 queries

   // Good: Explicit loading
   var posts = context.Posts.ToList();
   context.Authors.Load();

   // Good: Split query for large includes
   var posts = context.Posts
                      .Include(p => p.Author)
                      .AsSplitQuery() // Separate queries to avoid cartesian explosion
                      .ToList();
   ```

3. **Query Optimization**
   ```csharp
   // Bad: Loading unnecessary data
   var users = context.Users.ToList(); // Loads all columns

   // Good: Select only needed columns
   var users = context.Users
                      .Select(u => new { u.Id, u.Name })
                      .ToList();

   // Bad: Client-side evaluation
   var users = context.Users
                      .Where(u => IsValidUser(u)) // Evaluates in-memory
                      .ToList();

   // Good: Database-side evaluation
   var users = context.Users
                      .Where(u => u.IsActive && u.Age >= 18)
                      .ToList();

   // Use AsNoTracking for read-only queries
   var users = context.Users
                      .AsNoTracking() // No change tracking overhead
                      .ToList();
   ```

4. **Bulk Operations**
   ```csharp
   // Bad: Individual inserts
   foreach (var user in users)
   {
       context.Users.Add(user);
       context.SaveChanges(); // N database round-trips
   }

   // Good: Batch insert
   context.Users.AddRange(users);
   context.SaveChanges(); // Single batch

   // For large batches, consider EFCore.BulkExtensions
   context.BulkInsert(users);
   ```

## Phase 5: Memory Management Review

1. **Garbage Collection Analysis**
   ```powershell
   # Monitor GC metrics
   dotnet counters monitor --process-id <pid> \
       --counters System.Runtime[gen-0-gc-count,gen-1-gc-count,gen-2-gc-count,gen-0-size,gen-1-size,gen-2-size,loh-size,alloc-rate]

   # Check GC settings
   # For server workloads, use Server GC
   # In .csproj:
   # <ServerGarbageCollection>true</ServerGarbageCollection>
   ```

2. **Large Object Heap (LOH) Issues**
   ```csharp
   // Objects >= 85,000 bytes go to LOH
   // LOH is not compacted by default (causes fragmentation)

   // Bad: Large temporary allocations
   public void ProcessData()
   {
       byte[] buffer = new byte[100000]; // LOH allocation
       // Use buffer...
   } // Buffer eligible for GC but LOH fragmentation

   // Better: Use ArrayPool for large temporary buffers
   public void ProcessData()
   {
       var buffer = ArrayPool<byte>.Shared.Rent(100000);
       try
       {
           // Use buffer...
       }
       finally
       {
           ArrayPool<byte>.Shared.Return(buffer);
       }
   }
   ```

3. **Memory Leak Detection**
   ```csharp
   // Common leak patterns:

   // 1. Event handlers not unsubscribed
   public class Subscriber
   {
       public Subscriber(Publisher publisher)
       {
           publisher.SomeEvent += HandleEvent; // BAD: creates strong reference
       }
       // Subscriber kept alive by publisher

       private void HandleEvent() { }
   }

   // 2. Static collections growing unbounded
   private static List<Item> _cache = new(); // BAD: never cleaned
   public void AddToCache(Item item)
   {
       _cache.Add(item); // Memory leak
   }

   // 3. Async operations not cancelled
   private CancellationTokenSource _cts = new();
   public async Task LongRunningTask()
   {
       await Task.Delay(TimeSpan.FromHours(1), _cts.Token);
   } // If not cancelled, keeps references alive
   ```

4. **Caching Strategy Review**
   ```csharp
   // Use MemoryCache with proper eviction
   services.AddMemoryCache();

   // Configure cache entry
   _cache.Set(key, value, new MemoryCacheEntryOptions
   {
       AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(5),
       SlidingExpiration = TimeSpan.FromMinutes(1),
       Size = 1, // For size-based eviction
       Priority = CacheItemPriority.Normal
   });
   ```

## Phase 6: Async/Await Performance

1. **Async Best Practices**
   ```csharp
   // Bad: Sync over async
   public string GetData()
   {
       return GetDataAsync().Result; // Blocks thread, can cause deadlock
   }

   // Bad: Async over sync
   public async Task<int> GetCountAsync()
   {
       return await Task.Run(() => _items.Count); // Unnecessary thread pool usage
   }

   // Good: Async all the way
   public async Task<string> GetDataAsync()
   {
       return await _httpClient.GetStringAsync(url);
   }

   // Good: ValueTask for hot paths that may complete synchronously
   public ValueTask<int> GetCachedValueAsync(string key)
   {
       if (_cache.TryGetValue(key, out int value))
           return new ValueTask<int>(value); // No allocation

       return new ValueTask<int>(LoadFromDatabaseAsync(key));
   }
   ```

2. **ConfigureAwait Usage**
   ```csharp
   // In library code, use ConfigureAwait(false) to avoid context capture
   public async Task<string> GetDataAsync()
   {
       var response = await _httpClient.GetAsync(url).ConfigureAwait(false);
       return await response.Content.ReadAsStringAsync().ConfigureAwait(false);
   }

   // In UI code, omit ConfigureAwait to stay on UI thread
   private async void Button_Click(object sender, EventArgs e)
   {
       var data = await GetDataAsync(); // Resumes on UI thread
       textBox.Text = data; // Can update UI
   }
   ```

3. **Parallel Processing**
   ```csharp
   // CPU-bound: Use Parallel.ForEach
   Parallel.ForEach(items, item =>
   {
       ProcessCpuBound(item);
   });

   // I/O-bound: Use Task.WhenAll
   var tasks = items.Select(item => ProcessIoBoundAsync(item));
   await Task.WhenAll(tasks);

   // With degree of parallelism limit
   var options = new ParallelOptions { MaxDegreeOfParallelism = 4 };
   Parallel.ForEach(items, options, item =>
   {
       ProcessItem(item);
   });
   ```

## Phase 7: ASP.NET Core Specific Optimizations

1. **Response Caching**
   ```csharp
   // Enable response caching
   services.AddResponseCaching();
   app.UseResponseCaching();

   // Use on endpoints
   [ResponseCache(Duration = 60)]
   public IActionResult Get()
   {
       return Ok(data);
   }

   // Or output caching (.NET 7+)
   app.MapGet("/api/data", () => GetData())
      .CacheOutput(policy => policy.Expire(TimeSpan.FromMinutes(5)));
   ```

2. **JSON Serialization**
   ```csharp
   // Use System.Text.Json (faster than Newtonsoft.Json)
   services.AddControllers()
           .AddJsonOptions(options =>
           {
               options.JsonSerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
               options.JsonSerializerOptions.DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull;
           });

   // For source generation (AOT-friendly, faster)
   [JsonSerializable(typeof(MyDto))]
   internal partial class AppJsonContext : JsonSerializerContext { }
   ```

3. **Minimal APIs vs Controllers**
   ```csharp
   // Minimal APIs have less overhead
   app.MapGet("/api/users/{id}", async (int id, UserService service) =>
   {
       var user = await service.GetUserAsync(id);
       return user is not null ? Results.Ok(user) : Results.NotFound();
   });
   ```

4. **HttpClient Best Practices**
   ```csharp
   // Bad: Creating HttpClient per request
   public async Task<string> GetDataAsync()
   {
       using var client = new HttpClient(); // BAD: socket exhaustion
       return await client.GetStringAsync(url);
   }

   // Good: Use IHttpClientFactory
   services.AddHttpClient<MyService>();

   public class MyService
   {
       private readonly HttpClient _httpClient;

       public MyService(HttpClient httpClient)
       {
           _httpClient = httpClient;
       }

       public async Task<string> GetDataAsync()
       {
           return await _httpClient.GetStringAsync(url);
       }
   }
   ```

## Output Format

Please provide a comprehensive performance report with the following structure:

### Executive Summary

- **Overall Performance**: [Excellent/Good/Fair/Poor]

- **Critical Bottlenecks**: [count and brief description]

- **Performance Impact**: [High/Medium/Low user-facing impact]

- **Optimization Potential**: [percentage improvement possible]

- **Recommended Investment**: [estimated hours for major improvements]

### Performance Profile Overview
**Top 10 Time-Consuming Methods**:
| Method | Type | Time | % Total | Calls | Time/Call | Category |
|--------|------|------|---------|-------|-----------|----------|
| [name] | [path] | [ms] | [%] | [count] | [ms] | [CPU/I/O/DB] |

**Top 10 Memory Allocations**:
| Operation | Type:Method | Allocations | Size (MB) | % Total |
|-----------|-------------|-------------|-----------|---------|
| [desc] | [location] | [count] | [MB] | [%] |

### GC Statistics

- **Gen 0 Collections**: [count] ([collections/sec])

- **Gen 1 Collections**: [count]

- **Gen 2 Collections**: [count]

- **LOH Size**: [MB]

- **Total Heap Size**: [MB]

- **GC Pause Time**: [ms average, max]

### Critical Performance Issues (Priority 1)
| Issue | Location | Impact | Current | Target | Optimization |
|-------|----------|--------|---------|--------|--------------|
| [description] | [type:method] | [High] | [metric] | [goal] | [strategy] |

### Algorithm Inefficiencies
**O(n²) or Worse Algorithms Detected**:
| Method | Location | Complexity | Current Performance | Optimized Approach |
|--------|----------|------------|---------------------|-------------------|
| [name] | [type:method] | [O(n²)] | [metric] | [suggested algorithm] |

### Entity Framework Performance
**Slow Queries** (>100ms):
| Query | Execution Time | Frequency | Issue | Optimization |
|-------|----------------|-----------|-------|--------------|
| [query] | [ms] | [calls/sec] | [N+1/missing index/etc] | [solution] |

**N+1 Query Patterns**:
| Location | Queries Generated | Recommendation |
|----------|-------------------|----------------|
| [type:method] | [N+1 count] | [Include/explicit loading] |

### Memory Analysis

- **Peak Working Set**: [MB]

- **Private Bytes**: [MB]

- **Gen 2 Heap Size**: [MB]

- **LOH Size**: [MB]

- **Memory Leaks Detected**: [Yes/No - locations if yes]

- **Large Object Allocations**: [count and locations]

### Async/Await Assessment

- **Sync-over-async Calls**: [count and locations]

- **Missing ConfigureAwait**: [count]

- **Thread Pool Starvation Risk**: [High/Medium/Low]

- **ValueTask Opportunities**: [locations]

### ASP.NET Core Performance

- **Average Request Time**: [ms]

- **P95 Request Time**: [ms]

- **P99 Request Time**: [ms]

- **Throughput**: [requests/sec]

- **Response Caching**: [implemented/not used]

- **HttpClient Usage**: [proper/issues found]

### Optimization Recommendations

**Quick Wins** (< 1 day effort, high impact):
1. **[Optimization]**
   - **Location**: [type:method]
   - **Current**: [metric]
   - **Expected Improvement**: [metric/percentage]
   - **Implementation**: [specific steps]

**Medium-term** (1-3 days effort):
[List of optimizations requiring moderate refactoring]

**Strategic** (> 3 days, architectural changes):
[List of major performance initiatives]

### Load Testing Recommendations
```csharp
// Suggested load testing scenarios

1. Normal load: X requests/sec for Y minutes
2. Peak load: X*3 requests/sec for Y minutes
3. Stress test: Gradually increase to failure point
4. Soak test: Normal load for 24 hours

// Tools: k6, JMeter, NBomber, BenchmarkDotNet
```

### Monitoring Recommendations
```csharp
// Implement performance monitoring

- Response time tracking (p50, p95, p99)

- GC metrics (collection counts, pause time)

- Memory usage and LOH size

- Thread pool metrics

- Database query performance

- Custom business metrics

// Tools: Application Insights, Prometheus, Datadog, New Relic
```

### Benchmark Results
**Before Optimization**:

- [Operation]: [time/throughput]

**After Optimization** (projected):

- [Operation]: [time/throughput]

**Improvement**: [percentage] faster / [X]x throughput

### Next Steps

- [ ] Implement quick win optimizations

- [ ] Set up performance benchmarking suite (BenchmarkDotNet)

- [ ] Configure production performance monitoring

- [ ] Plan load testing before deployment

- [ ] Schedule performance review sprint

- [ ] Document performance SLAs/targets

- [ ] Enable GC telemetry in production

## Notes

- Optimize based on profiling data, not assumptions

- Focus on user-facing performance improvements first

- Measure before and after optimization

- Consider scalability alongside raw performance

- Balance performance with code maintainability

- Use BenchmarkDotNet for micro-benchmarks

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/performance_review/analysis_scripts
mkdir -p ${OUTPUT_DIR}/performance_review/supporting_data
```

**Save files as follows**:

- Main report → `review/performance_review/performance_review_report.md`

- Findings data → `review/performance_review/performance_review_findings.json`

- Analysis scripts → `review/performance_review/analysis_scripts/`

- Supporting data → `review/performance_review/supporting_data/`
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
