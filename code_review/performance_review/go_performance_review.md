# Go Performance Review

## Objective
Systematically identify performance bottlenecks, inefficient algorithms, and resource usage issues. Provide data-driven optimization recommendations to improve application speed, scalability, and resource efficiency.

## Output Directory Structure

All review outputs should be saved in organized directories:

```
review/
└── performance_review/
    ├── performance_review_report.md
    ├── performance_review_findings.json
    ├── analysis_scripts/
    └── supporting_data/
```

**Directory Setup**:

- Create `review/performance_review/` directory in repository root if it doesn't exist

- All review outputs (reports, findings, scripts, data) go in the phase-specific directory

**Expected Outputs**:

- `performance_review_report.md` - Main findings and recommendations

- `performance_review_findings.json` - Structured data for tooling integration

- `analysis_scripts/` - Any scripts generated during analysis

- `supporting_data/` - Raw data, logs, profiling results, scan outputs

## Review Checklist

### Performance Profiling
- [ ] CPU profiling completed (pprof)
- [ ] Memory profiling performed (pprof)
- [ ] Goroutine profiling analyzed
- [ ] Block profiling reviewed
- [ ] Mutex contention profiling checked
- [ ] Hot paths and bottlenecks identified

### Algorithm Efficiency
- [ ] Time complexity evaluated (O(n), O(n²), etc.)
- [ ] Space complexity assessed
- [ ] Inefficient loops identified (nested, redundant)
- [ ] Algorithmic improvements documented
- [ ] Data structure choices reviewed

### Concurrency Performance
- [ ] Goroutine usage patterns evaluated
- [ ] Channel performance assessed
- [ ] Mutex contention measured
- [ ] Work distribution analyzed
- [ ] Race conditions checked

### Memory Management
- [ ] Memory leaks detected
- [ ] Large object allocations identified
- [ ] Memory growth patterns analyzed
- [ ] Caching strategies reviewed
- [ ] Garbage collection behavior assessed

### I/O & Network
- [ ] File I/O operations profiled
- [ ] Network call latency measured
- [ ] Connection pooling evaluated
- [ ] Buffering strategies reviewed
- [ ] Context cancellation properly used

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Go Performance Review

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Review Protocol

Please perform a comprehensive performance review of this Go application following this protocol:

## Phase 1: Performance Profiling Setup

1. **CPU Profiling**
   ```go
   // Add to main.go or test file
   import (
       "os"
       "runtime/pprof"
   )

   // Start CPU profiling
   f, _ := os.Create("cpu.prof")
   pprof.StartCPUProfile(f)
   defer pprof.StopCPUProfile()

   // Run with:
   go run main.go
   go tool pprof cpu.prof
   ```

   ```bash
   # Or use built-in HTTP profiling
   import _ "net/http/pprof"

   # Then access http://localhost:6060/debug/pprof/
   go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30
   ```

2. **Memory Profiling**
   ```go
   // Heap profiling
   import "runtime/pprof"

   f, _ := os.Create("mem.prof")
   pprof.WriteHeapProfile(f)
   f.Close()

   // Analyze with:
   go tool pprof -alloc_space mem.prof    # Total allocations
   go tool pprof -alloc_objects mem.prof  # Allocation count
   go tool pprof -inuse_space mem.prof    # Current memory usage
   ```

3. **Goroutine Profiling**
   ```bash
   # Access via pprof HTTP endpoint
   go tool pprof http://localhost:6060/debug/pprof/goroutine

   # Or programmatically
   pprof.Lookup("goroutine").WriteTo(f, 0)
   ```

4. **Block & Mutex Profiling**
   ```go
   import "runtime"

   // Enable block profiling
   runtime.SetBlockProfileRate(1)

   // Enable mutex profiling
   runtime.SetMutexProfileFraction(1)

   // Access via pprof
   go tool pprof http://localhost:6060/debug/pprof/block
   go tool pprof http://localhost:6060/debug/pprof/mutex
   ```

5. **Execution Tracing**
   ```go
   import "runtime/trace"

   f, _ := os.Create("trace.out")
   trace.Start(f)
   defer trace.Stop()

   // Visualize with:
   go tool trace trace.out
   ```

## Phase 2: Bottleneck Identification

1. **Analyze Profiling Results**
   ```bash
   # Top CPU consumers
   go tool pprof -top cpu.prof

   # Interactive analysis
   go tool pprof cpu.prof
   (pprof) top 20
   (pprof) list functionName
   (pprof) web  # Visual call graph

   # Flame graph
   go tool pprof -http=:8080 cpu.prof
   ```

   - Identify functions consuming >5% of total time
   - Find functions called excessive times
   - Locate memory-intensive operations
   - Identify blocking operations

2. **Hot Path Analysis**
   - Map critical execution paths
   - Measure end-to-end latency
   - Identify slowest operations
   - Document user-facing performance impacts

3. **Resource Usage Patterns**
   - CPU utilization during typical operations
   - Memory growth patterns over time
   - Goroutine count and lifecycle
   - Network bandwidth usage

## Phase 3: Algorithm Efficiency Review

1. **Time Complexity Analysis**
   - Review loops and nested iterations
   - Identify O(n²) or worse algorithms
   - Check for redundant computations
   - Assess search and sort operations

2. **Common Performance Anti-Patterns**
   ```go
   // Inefficient patterns to search for:

   // 1. Repeated string concatenation (use strings.Builder)
   var result string
   for _, s := range items {
       result += s  // BAD: O(n²) due to string immutability
   }
   // Better:
   var builder strings.Builder
   for _, s := range items {
       builder.WriteString(s)  // O(n)
   }

   // 2. Growing slice without capacity
   var items []int
   for i := 0; i < n; i++ {
       items = append(items, i)  // BAD: may cause multiple reallocations
   }
   // Better:
   items := make([]int, 0, n)  // Pre-allocate capacity

   // 3. Map lookups in tight loops
   for i := 0; i < len(data); i++ {
       if val, ok := expensiveMap[key]; ok {  // BAD: if map is recalculated
           // process
       }
   }
   // Better: cache lookup result if possible

   // 4. Unnecessary conversions
   for _, b := range []byte(string(bytes)) {  // BAD: double conversion
   }
   // Better: use bytes directly

   // 5. defer in tight loops
   for i := 0; i < n; i++ {
       mu.Lock()
       defer mu.Unlock()  // BAD: defers accumulate
   }
   // Better: manual unlock or restructure

   // 6. Iterating with index instead of range
   for i := 0; i < len(slice); i++ {
       item := slice[i]  // Less efficient than range
   }
   // Better:
   for _, item := range slice {
   }
   ```

3. **Data Structure Optimization**
   - Evaluate slice vs array usage
   - Check for appropriate map usage
   - Review struct field ordering (memory alignment)
   - Assess sync.Pool usage for object reuse

## Phase 4: Concurrency Performance Analysis

1. **Goroutine Usage Patterns**
   ```go
   // Check for:
   // 1. Goroutine leaks
   go func() {
       // Never returns - leak!
   }()

   // 2. Excessive goroutines
   for i := 0; i < 1000000; i++ {
       go process(i)  // BAD: too many goroutines
   }
   // Better: worker pool pattern

   // 3. Missing synchronization
   var counter int  // BAD: race condition
   for i := 0; i < 10; i++ {
       go func() {
           counter++  // Not atomic
       }()
   }
   // Better: use sync/atomic or mutex
   ```

2. **Channel Performance**
   ```go
   // Inefficient patterns:
   // 1. Unbuffered channels causing blocking
   ch := make(chan int)  // Consider buffering

   // 2. Select with default causing busy-wait
   for {
       select {
       case v := <-ch:
           process(v)
       default:
           // BAD: busy loop
       }
   }

   // 3. Channels in hot paths (consider lock-free alternatives)
   ```

3. **Mutex Contention Analysis**
   ```bash
   # Identify mutex bottlenecks
   go tool pprof http://localhost:6060/debug/pprof/mutex

   # Consider:
   - Using sync.RWMutex for read-heavy workloads
   - Reducing critical section size
   - Lock-free alternatives (sync/atomic)
   - Sharding to reduce contention
   ```

4. **Worker Pool Patterns**
   ```go
   // Evaluate worker pool implementation
   // Good pattern:
   func worker(jobs <-chan Job, results chan<- Result, wg *sync.WaitGroup) {
       defer wg.Done()
       for job := range jobs {
           results <- process(job)
       }
   }

   // Setup
   numWorkers := runtime.NumCPU()
   jobs := make(chan Job, 100)
   results := make(chan Result, 100)
   var wg sync.WaitGroup

   for i := 0; i < numWorkers; i++ {
       wg.Add(1)
       go worker(jobs, results, &wg)
   }
   ```

## Phase 5: Memory Management Review

1. **Memory Leak Detection**
   ```bash
   # Monitor memory growth
   go tool pprof -base mem1.prof mem2.prof

   # Common leak sources:
   - Global caches without eviction
   - Goroutine leaks holding references
   - Unclosed HTTP response bodies
   - Event listeners not removed
   ```

2. **Allocation Analysis**
   ```bash
   # Find allocation hotspots
   go tool pprof -alloc_space mem.prof
   go tool pprof -alloc_objects mem.prof

   # Reduce allocations by:
   - Using sync.Pool for frequently allocated objects
   - Pre-allocating slices with capacity
   - Avoiding unnecessary conversions
   - Using pointers appropriately
   ```

3. **Garbage Collection Tuning**
   ```go
   import "runtime/debug"

   // Monitor GC stats
   var stats debug.GCStats
   debug.ReadGCStats(&stats)

   // Tune GOGC if needed
   debug.SetGCPercent(200)  // Default is 100

   // Consider SetMemoryLimit for Go 1.19+
   debug.SetMemoryLimit(1024 * 1024 * 1024) // 1GB
   ```

4. **Struct Memory Layout**
   ```go
   // Bad: Inefficient field ordering (24 bytes on 64-bit)
   type Inefficient struct {
       flag   bool    // 1 byte + 7 padding
       number int64   // 8 bytes
       small  int8    // 1 byte + 7 padding
   }

   // Good: Optimized field ordering (16 bytes on 64-bit)
   type Efficient struct {
       number int64   // 8 bytes
       flag   bool    // 1 byte
       small  int8    // 1 byte + 6 padding
   }

   // Use: fieldalignment tool
   fieldalignment -fix ./...
   ```

## Phase 6: I/O Performance Optimization

1. **File I/O Analysis**
   ```go
   // Inefficient:
   file, _ := os.Open("large.txt")
   scanner := bufio.NewScanner(file)
   for scanner.Scan() {
       process(scanner.Text())
   }

   // Consider:
   - Buffer size tuning
   - Batch processing
   - Memory-mapped I/O for large files
   ```

2. **HTTP Client Performance**
   ```go
   // Good: Configure HTTP client
   client := &http.Client{
       Timeout: 10 * time.Second,
       Transport: &http.Transport{
           MaxIdleConns:        100,
           MaxIdleConnsPerHost: 100,
           IdleConnTimeout:     90 * time.Second,
           DisableCompression:  false,
           // Enable HTTP/2
       },
   }

   // Always close response bodies
   defer resp.Body.Close()
   ```

3. **Database Performance**
   ```go
   // Use connection pooling
   db.SetMaxOpenConns(25)
   db.SetMaxIdleConns(5)
   db.SetConnMaxLifetime(5 * time.Minute)

   // Use prepared statements
   stmt, _ := db.Prepare("SELECT * FROM users WHERE id = ?")
   defer stmt.Close()

   // Batch operations
   tx, _ := db.Begin()
   for _, item := range items {
       tx.Exec("INSERT INTO ...", item)
   }
   tx.Commit()
   ```

## Phase 7: Benchmarking

1. **Write Benchmarks**
   ```go
   func BenchmarkFunction(b *testing.B) {
       // Setup
       data := generateTestData()

       b.ResetTimer()
       for i := 0; i < b.N; i++ {
           function(data)
       }
   }

   // Run benchmarks
   go test -bench=. -benchmem
   go test -bench=. -cpuprofile=cpu.prof -memprofile=mem.prof
   ```

2. **Comparative Benchmarks**
   ```bash
   # Benchmark before optimization
   go test -bench=. -count=5 > old.txt

   # Make changes

   # Benchmark after optimization
   go test -bench=. -count=5 > new.txt

   # Compare results
   benchstat old.txt new.txt
   ```

3. **Continuous Benchmarking**
   ```yaml
   # GitHub Actions example
   - name: Run benchmarks
     run: |
       go test -bench=. -benchmem | tee benchmark.txt

   - name: Store benchmark
     uses: benchmark-action/github-action-benchmark@v1
     with:
       tool: 'go'
       output-file-path: benchmark.txt
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
**Top 10 CPU-Consuming Functions**:
| Function | Package | Time | % Total | Calls | Time/Call | Category |
|----------|---------|------|---------|-------|-----------|----------|
| [name] | [pkg] | [ms] | [%] | [count] | [µs] | [CPU/I/O/Lock] |

**Top 10 Memory Allocations**:
| Function | Package | Allocations | Bytes | % Total | Description |
|----------|---------|-------------|-------|---------|-------------|
| [name] | [pkg] | [count] | [MB] | [%] | [details] |

**Goroutine Statistics**:
- Peak goroutines: [count]
- Average goroutines: [count]
- Goroutine leaks detected: [count]

### Critical Performance Issues (Priority 1)
| Issue | Location | Impact | Current | Target | Optimization |
|-------|----------|--------|---------|--------|--------------|
| [description] | [file:line] | [High] | [metric] | [goal] | [strategy] |

### High-Impact Optimizations (Priority 2)
[List of optimizations with significant performance gains]

### Algorithm Inefficiencies
**O(n²) or Worse Algorithms Detected**:
| Function | Location | Complexity | Current Performance | Optimized Approach |
|----------|----------|------------|---------------------|-------------------|
| [name] | [file:line] | [O(n²)] | [metric] | [suggested algorithm] |

### Concurrency Issues
**Mutex Contention Hotspots**:
| Location | Contention Time | % Total | Recommendation |
|----------|-----------------|---------|----------------|
| [file:line] | [ms] | [%] | [optimization] |

**Goroutine Leaks**:
| Location | Leaked Goroutines | Cause | Fix |
|----------|-------------------|-------|-----|
| [file:line] | [count] | [reason] | [solution] |

### Memory Analysis
- **Peak Memory Usage**: [MB]
- **Memory Leaks Detected**: [Yes/No - locations if yes]
- **Allocation Rate**: [allocs/sec]
- **GC Pressure**: [High/Medium/Low]
- **GC Pause Time**: [p50/p95/p99 ms]

### I/O & Network Performance
- **File I/O Operations**: [count and total time]
- **Network Calls**: [count, total time, average latency]
- **Connection Pool Efficiency**: [utilization %]
- **Blocking Operations**: [count and locations]

### Go-Specific Findings
- **Escape Analysis Issues**: [allocations that could be stack]
- **Interface Boxing**: [unnecessary allocations]
- **Reflection Usage**: [performance impact]
- **CGO Calls**: [frequency and cost]

### Benchmark Results
**Key Operations**:
| Operation | ns/op | B/op | allocs/op | Comparison |
|-----------|-------|------|-----------|------------|
| [name] | [time] | [bytes] | [count] | [vs baseline] |

### Optimization Recommendations

**Quick Wins** (< 1 day effort, high impact):
1. **[Optimization]**
   - **Location**: [file:line]
   - **Current**: [metric]
   - **Expected Improvement**: [metric/percentage]
   - **Implementation**:
     ```go
     // Before
     [code]

     // After
     [optimized code]
     ```

**Medium-term** (1-3 days effort):
[List of optimizations requiring moderate refactoring]

**Strategic** (> 3 days, architectural changes):
[List of major performance initiatives]

### Load Testing Recommendations
```bash
# Suggested load testing tools
- vegeta: HTTP load testing
- hey: HTTP benchmarking
- ghz: gRPC load testing

# Example vegeta test
echo "GET http://localhost:8080/api/endpoint" | \
  vegeta attack -duration=30s -rate=100 | \
  vegeta report
```

### Monitoring Recommendations
```go
// Instrument code with metrics
import "github.com/prometheus/client_golang/prometheus"

// Define metrics
var (
    requestDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "http_request_duration_seconds",
            Help: "HTTP request latencies",
        },
        []string{"path", "method"},
    )
)

// Implement performance monitoring
- Response time tracking (p50, p95, p99)
- Goroutine count monitoring
- Memory usage alerts
- GC pause time tracking
- Custom business metric tracking

// Recommended tools:
- Prometheus + Grafana
- DataDog
- New Relic
- pprof integration
```

### Profiling Integration
```go
// Add to production code (with caution)
import _ "net/http/pprof"

http.ListenAndServe(":6060", nil)

// Access profiles:
// http://localhost:6060/debug/pprof/
// http://localhost:6060/debug/pprof/heap
// http://localhost:6060/debug/pprof/goroutine
// http://localhost:6060/debug/pprof/profile?seconds=30
```

### Next Steps
- [ ] Implement quick win optimizations
- [ ] Set up continuous benchmarking
- [ ] Configure production performance monitoring
- [ ] Plan load testing before deployment
- [ ] Schedule performance review sprint
- [ ] Document performance SLAs/targets

## Notes
- Optimize based on profiling data, not assumptions
- Focus on user-facing performance improvements first
- Always benchmark before and after optimization
- Consider scalability alongside raw performance
- Balance performance with code maintainability
- Use pprof religiously - it's your best friend

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p review/performance_review/analysis_scripts
mkdir -p review/performance_review/supporting_data
```

**Save files as follows**:

- Main report → `review/performance_review/performance_review_report.md`

- Findings data → `review/performance_review/performance_review_findings.json`

- Analysis scripts → `review/performance_review/analysis_scripts/`

- Supporting data → `review/performance_review/supporting_data/`
~~~
