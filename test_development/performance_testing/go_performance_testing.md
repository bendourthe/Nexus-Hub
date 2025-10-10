# Go Performance Testing

## Objective
Implement comprehensive performance testing to validate system behavior under load, identify bottlenecks, measure response times, profile resource usage, detect performance regressions, and ensure scalability requirements are met using Go tooling.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/performance_testing/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/performance_testing/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Performance Test Coverage

- [ ] Load tests implemented for critical endpoints

- [ ] Stress tests validate beyond-capacity behavior

- [ ] Baseline benchmarks established with testing.B

- [ ] Performance regression tests configured

- [ ] Resource profiling set up (pprof)

### Metrics and Monitoring

- [ ] Response time thresholds defined

- [ ] Throughput targets established

- [ ] Resource usage limits set (memory, goroutines)

- [ ] Error rate thresholds configured

- [ ] Performance reports automated

### Test Infrastructure

- [ ] Go benchmarking configured

- [ ] Load testing tools set up

- [ ] Performance test data prepared

- [ ] CI/CD integration planned

- [ ] Results storage and trending implemented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Go Performance Testing Implementation

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/performance_testing"
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

Please implement comprehensive performance testing for this Go project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: Performance Requirements Definition

### Define Performance Targets

Document expected performance characteristics:

**Response Time Requirements**:
| Endpoint/Operation | P50 (median) | P95 | P99 | Timeout |
|-------------------|--------------|-----|-----|---------|
| GET /api/users | <100ms | <200ms | <500ms | 2s |
| POST /api/users | <200ms | <400ms | <1s | 5s |
| Database query | <50ms | <100ms | <200ms | 1s |
| Cache lookup | <5ms | <10ms | <20ms | 100ms |

**Throughput Requirements**:
| Operation | Target RPS | Peak RPS | Concurrent Goroutines |
|-----------|------------|----------|----------------------|
| REST API | 100 | 500 | 1000 |
| Message processing | 50 | 100 | N/A |

**Resource Limits**:

- **Memory**: <512MB heap

- **Goroutines**: <10,000 active

- **GC Pause**: <10ms P99

- **CPU**: <80% average, <95% peak

- **Database connections**: <50 concurrent

## Phase 2: Benchmarking with testing.B

### Basic Benchmark

```go
package benchmarks

import (
    "testing"
)

// BenchmarkLinearSearch benchmarks linear search through users.
//
// Run with: go test -bench=. -benchmem
func BenchmarkLinearSearch(b *testing.B) {
    users := generateTestUsers(1000)
    query := "test"

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _ = linearSearch(users, query)
    }
}

// BenchmarkBinarySearch benchmarks binary search through users.
func BenchmarkBinarySearch(b *testing.B) {
    users := generateTestUsers(1000)
    query := "test"

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _ = binarySearch(users, query)
    }
}

// BenchmarkMapLookup benchmarks map-based lookup.
func BenchmarkMapLookup(b *testing.B) {
    userMap := generateTestUserMap(1000)
    query := "test"

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _ = userMap[query]
    }
}

// BenchmarkConcurrentSearch benchmarks concurrent search operations.
func BenchmarkConcurrentSearch(b *testing.B) {
    users := generateTestUsers(1000)
    query := "test"

    b.ResetTimer()
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            _ = linearSearch(users, query)
        }
    })
}

func generateTestUsers(count int) []User {
    users := make([]User, count)
    for i := 0; i < count; i++ {
        users[i] = User{ID: i, Name: "User" + string(rune(i))}
    }
    return users
}

func generateTestUserMap(count int) map[string]User {
    userMap := make(map[string]User, count)
    for i := 0; i < count; i++ {
        key := "User" + string(rune(i))
        userMap[key] = User{ID: i, Name: key}
    }
    return userMap
}

type User struct {
    ID   int
    Name string
}

func linearSearch(users []User, query string) []User {
    results := make([]User, 0)
    for _, user := range users {
        if user.Name == query {
            results = append(results, user)
        }
    }
    return results
}

func binarySearch(users []User, query string) []User {
    // Implementation
    return []User{}
}
```

### Advanced Benchmark Patterns

```go
package benchmarks

import (
    "bytes"
    "encoding/json"
    "strings"
    "testing"
)

// BenchmarkStringOperations benchmarks different string operations.
func BenchmarkStringOperations(b *testing.B) {
    testCases := []struct {
        name string
        fn   func() string
    }{
        {
            name: "Concatenation",
            fn: func() string {
                s := ""
                for i := 0; i < 100; i++ {
                    s += "test"
                }
                return s
            },
        },
        {
            name: "Builder",
            fn: func() string {
                var sb strings.Builder
                for i := 0; i < 100; i++ {
                    sb.WriteString("test")
                }
                return sb.String()
            },
        },
        {
            name: "Buffer",
            fn: func() string {
                var buf bytes.Buffer
                for i := 0; i < 100; i++ {
                    buf.WriteString("test")
                }
                return buf.String()
            },
        },
    }

    for _, tc := range testCases {
        b.Run(tc.name, func(b *testing.B) {
            for i := 0; i < b.N; i++ {
                _ = tc.fn()
            }
        })
    }
}

// BenchmarkJSONEncoding benchmarks JSON encoding operations.
func BenchmarkJSONEncoding(b *testing.B) {
    data := generateLargeStruct()

    b.Run("Marshal", func(b *testing.B) {
        b.ResetTimer()
        for i := 0; i < b.N; i++ {
            _, err := json.Marshal(data)
            if err != nil {
                b.Fatal(err)
            }
        }
    })

    b.Run("Encoder", func(b *testing.B) {
        b.ResetTimer()
        for i := 0; i < b.N; i++ {
            var buf bytes.Buffer
            enc := json.NewEncoder(&buf)
            if err := enc.Encode(data); err != nil {
                b.Fatal(err)
            }
        }
    })
}

// BenchmarkMemoryAllocation benchmarks memory allocation patterns.
func BenchmarkMemoryAllocation(b *testing.B) {
    b.Run("SliceWithoutCapacity", func(b *testing.B) {
        b.ReportAllocs()
        for i := 0; i < b.N; i++ {
            s := []int{}
            for j := 0; j < 1000; j++ {
                s = append(s, j)
            }
        }
    })

    b.Run("SliceWithCapacity", func(b *testing.B) {
        b.ReportAllocs()
        for i := 0; i < b.N; i++ {
            s := make([]int, 0, 1000)
            for j := 0; j < 1000; j++ {
                s = append(s, j)
            }
        }
    })
}

// BenchmarkConcurrency benchmarks different concurrency patterns.
func BenchmarkConcurrency(b *testing.B) {
    data := generateTestData(1000)

    b.Run("Sequential", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            for _, item := range data {
                _ = processItem(item)
            }
        }
    })

    b.Run("Goroutines", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            ch := make(chan result, len(data))
            for _, item := range data {
                go func(item string) {
                    ch <- processItem(item)
                }(item)
            }
            for range data {
                <-ch
            }
        }
    })

    b.Run("WorkerPool", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            processWithWorkerPool(data, 10)
        }
    })
}

type result struct {
    value string
}

func generateLargeStruct() interface{} {
    return struct {
        ID    int
        Name  string
        Items []string
    }{
        ID:    1,
        Name:  "Test",
        Items: []string{"a", "b", "c"},
    }
}

func generateTestData(count int) []string {
    data := make([]string, count)
    for i := 0; i < count; i++ {
        data[i] = "item"
    }
    return data
}

func processItem(item string) result {
    return result{value: item}
}

func processWithWorkerPool(data []string, workers int) {
    jobs := make(chan string, len(data))
    results := make(chan result, len(data))

    for w := 0; w < workers; w++ {
        go func() {
            for item := range jobs {
                results <- processItem(item)
            }
        }()
    }

    for _, item := range data {
        jobs <- item
    }
    close(jobs)

    for range data {
        <-results
    }
}
```

### Running Benchmarks

```bash
# Run all benchmarks
go test -bench=. -benchmem

# Run specific benchmark
go test -bench=BenchmarkLinearSearch -benchmem

# Run benchmarks with CPU profiling
go test -bench=. -cpuprofile=cpu.prof

# Run benchmarks with memory profiling
go test -bench=. -memprofile=mem.prof

# Run benchmarks multiple times for statistical significance
go test -bench=. -benchtime=10s -count=5

# Compare benchmark results
go test -bench=. -benchmem > ${OUTPUT_DIR}/exports/new.txt
benchstat old.txt new.txt
```

## Phase 3: Profiling with pprof

### CPU Profiling

```go
package main

import (
    "log"
    "os"
    "runtime/pprof"
)

// ProfileCPU profiles CPU usage during function execution.
func ProfileCPU() {
    f, err := os.Create("cpu.prof")
    if err != nil {
        log.Fatal(err)
    }
    defer f.Close()

    if err := pprof.StartCPUProfile(f); err != nil {
        log.Fatal(err)
    }
    defer pprof.StopCPUProfile()

    // Run code to profile
    performExpensiveOperation()
}

func performExpensiveOperation() {
    // Your code here
}
```

### Memory Profiling

```go
package main

import (
    "log"
    "os"
    "runtime"
    "runtime/pprof"
)

// ProfileMemory profiles memory allocation.
func ProfileMemory() {
    // Run code to profile
    performMemoryIntensiveOperation()

    f, err := os.Create("mem.prof")
    if err != nil {
        log.Fatal(err)
    }
    defer f.Close()

    runtime.GC() // Force garbage collection before profiling
    if err := pprof.WriteHeapProfile(f); err != nil {
        log.Fatal(err)
    }
}

func performMemoryIntensiveOperation() {
    // Your code here
}
```

### Goroutine Profiling

```go
package main

import (
    "log"
    "os"
    "runtime/pprof"
)

// ProfileGoroutines profiles active goroutines.
func ProfileGoroutines() {
    f, err := os.Create("goroutine.prof")
    if err != nil {
        log.Fatal(err)
    }
    defer f.Close()

    if err := pprof.Lookup("goroutine").WriteTo(f, 0); err != nil {
        log.Fatal(err)
    }
}
```

### HTTP Handler for Runtime Profiling

```go
package main

import (
    "log"
    "net/http"
    _ "net/http/pprof"
)

func main() {
    // Start pprof server
    go func() {
        log.Println("Starting pprof server on :6060")
        log.Println(http.ListenAndServe("localhost:6060", nil))
    }()

    // Your application code
    startApplication()
}

func startApplication() {
    // Application logic
}

// Access profiles at:
// http://localhost:6060/debug/pprof/
// http://localhost:6060/debug/pprof/heap
// http://localhost:6060/debug/pprof/goroutine
// http://localhost:6060/debug/pprof/profile?seconds=30
```

### Analyzing Profiles

```bash
# Analyze CPU profile
go tool pprof cpu.prof
# Commands: top, list, web

# Analyze memory profile
go tool pprof mem.prof

# Interactive web interface
go tool pprof -http=:8080 cpu.prof

# Compare profiles
go tool pprof -base=old.prof new.prof

# Generate flame graph
go tool pprof -http=:8080 http://localhost:6060/debug/pprof/profile?seconds=30
```

## Phase 4: Load Testing

### HTTP Load Test

```go
package loadtest

import (
    "fmt"
    "net/http"
    "sync"
    "sync/atomic"
    "testing"
    "time"
)

// TestAPILoad performs load testing on HTTP endpoints.
func TestAPILoad(t *testing.T) {
    const (
        concurrency = 100
        duration    = 30 * time.Second
        url         = "http://localhost:8080/api/users"
    )

    var (
        successCount int64
        failureCount int64
        totalLatency int64
    )

    startTime := time.Now()
    endTime := startTime.Add(duration)

    var wg sync.WaitGroup
    for i := 0; i < concurrency; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            client := &http.Client{Timeout: 5 * time.Second}

            for time.Now().Before(endTime) {
                reqStart := time.Now()
                resp, err := client.Get(url)
                latency := time.Since(reqStart)

                if err != nil {
                    atomic.AddInt64(&failureCount, 1)
                    continue
                }
                resp.Body.Close()

                if resp.StatusCode == http.StatusOK {
                    atomic.AddInt64(&successCount, 1)
                    atomic.AddInt64(&totalLatency, int64(latency))
                } else {
                    atomic.AddInt64(&failureCount, 1)
                }
            }
        }()
    }

    wg.Wait()
    elapsed := time.Since(startTime)

    totalRequests := successCount + failureCount
    avgLatency := time.Duration(totalLatency / successCount)
    rps := float64(totalRequests) / elapsed.Seconds()

    fmt.Printf("\nLoad Test Results:\n")
    fmt.Printf("  Duration: %v\n", elapsed)
    fmt.Printf("  Total Requests: %d\n", totalRequests)
    fmt.Printf("  Success: %d\n", successCount)
    fmt.Printf("  Failures: %d\n", failureCount)
    fmt.Printf("  Success Rate: %.2f%%\n", 100.0*float64(successCount)/float64(totalRequests))
    fmt.Printf("  RPS: %.2f\n", rps)
    fmt.Printf("  Avg Latency: %v\n", avgLatency)

    if successCount < totalRequests*95/100 {
        t.Errorf("Success rate too low: %d/%d", successCount, totalRequests)
    }
}
```

### Advanced Load Testing

```go
package loadtest

import (
    "context"
    "fmt"
    "net/http"
    "sort"
    "sync"
    "sync/atomic"
    "testing"
    "time"
)

// LoadTestConfig configures load test parameters.
type LoadTestConfig struct {
    URL         string
    Concurrency int
    Duration    time.Duration
    RampUpTime  time.Duration
}

// LoadTestResult stores load test metrics.
type LoadTestResult struct {
    TotalRequests int64
    SuccessCount  int64
    FailureCount  int64
    Latencies     []time.Duration
    StartTime     time.Time
    Duration      time.Duration
}

// RunLoadTest executes a load test with given configuration.
func RunLoadTest(t *testing.T, config LoadTestConfig) *LoadTestResult {
    result := &LoadTestResult{
        StartTime: time.Now(),
        Latencies: make([]time.Duration, 0, 10000),
    }

    var (
        latenciesMux sync.Mutex
        wg           sync.WaitGroup
    )

    ctx, cancel := context.WithTimeout(context.Background(), config.Duration)
    defer cancel()

    // Ramp up goroutines gradually
    rampUpInterval := config.RampUpTime / time.Duration(config.Concurrency)

    for i := 0; i < config.Concurrency; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            client := &http.Client{Timeout: 10 * time.Second}

            for {
                select {
                case <-ctx.Done():
                    return
                default:
                    reqStart := time.Now()
                    resp, err := client.Get(config.URL)
                    latency := time.Since(reqStart)

                    atomic.AddInt64(&result.TotalRequests, 1)

                    if err != nil {
                        atomic.AddInt64(&result.FailureCount, 1)
                        continue
                    }
                    resp.Body.Close()

                    if resp.StatusCode == http.StatusOK {
                        atomic.AddInt64(&result.SuccessCount, 1)
                        latenciesMux.Lock()
                        result.Latencies = append(result.Latencies, latency)
                        latenciesMux.Unlock()
                    } else {
                        atomic.AddInt64(&result.FailureCount, 1)
                    }
                }
            }
        }()

        time.Sleep(rampUpInterval)
    }

    wg.Wait()
    result.Duration = time.Since(result.StartTime)

    return result
}

// PrintResults displays load test results.
func (r *LoadTestResult) PrintResults() {
    sort.Slice(r.Latencies, func(i, j int) bool {
        return r.Latencies[i] < r.Latencies[j]
    })

    var (
        p50 time.Duration
        p95 time.Duration
        p99 time.Duration
        avg time.Duration
    )

    if len(r.Latencies) > 0 {
        total := time.Duration(0)
        for _, l := range r.Latencies {
            total += l
        }
        avg = total / time.Duration(len(r.Latencies))

        p50 = r.Latencies[len(r.Latencies)*50/100]
        p95 = r.Latencies[len(r.Latencies)*95/100]
        p99 = r.Latencies[len(r.Latencies)*99/100]
    }

    rps := float64(r.TotalRequests) / r.Duration.Seconds()
    successRate := 100.0 * float64(r.SuccessCount) / float64(r.TotalRequests)

    fmt.Printf("\n=== Load Test Results ===\n")
    fmt.Printf("Duration:        %v\n", r.Duration)
    fmt.Printf("Total Requests:  %d\n", r.TotalRequests)
    fmt.Printf("Success:         %d\n", r.SuccessCount)
    fmt.Printf("Failures:        %d\n", r.FailureCount)
    fmt.Printf("Success Rate:    %.2f%%\n", successRate)
    fmt.Printf("RPS:             %.2f\n", rps)
    fmt.Printf("\nLatency:\n")
    fmt.Printf("  Average:       %v\n", avg)
    fmt.Printf("  P50:           %v\n", p50)
    fmt.Printf("  P95:           %v\n", p95)
    fmt.Printf("  P99:           %v\n", p99)
}

// TestAPIWithLoadTest is an example test using the load testing framework.
func TestAPIWithLoadTest(t *testing.T) {
    config := LoadTestConfig{
        URL:         "http://localhost:8080/api/users",
        Concurrency: 50,
        Duration:    30 * time.Second,
        RampUpTime:  5 * time.Second,
    }

    result := RunLoadTest(t, config)
    result.PrintResults()

    // Assert requirements
    successRate := float64(result.SuccessCount) / float64(result.TotalRequests)
    if successRate < 0.99 {
        t.Errorf("Success rate too low: %.2f%%", successRate*100)
    }

    rps := float64(result.TotalRequests) / result.Duration.Seconds()
    if rps < 100 {
        t.Errorf("RPS too low: %.2f", rps)
    }
}
```

## Phase 5: Stress Testing

### Stress Test Implementation

```go
package stresstest

import (
    "fmt"
    "runtime"
    "testing"
    "time"
)

// TestMemoryStress tests memory allocation and garbage collection.
func TestMemoryStress(t *testing.T) {
    var m runtime.MemStats
    runtime.ReadMemStats(&m)
    initialAlloc := m.Alloc

    // Perform memory-intensive operations
    data := make([][]byte, 0)
    for i := 0; i < 10000; i++ {
        buffer := make([]byte, 1024*10) // 10KB
        data = append(data, buffer)
    }

    // Process data
    for _, buf := range data {
        processBuffer(buf)
    }

    // Clear data and force GC
    data = nil
    runtime.GC()
    time.Sleep(100 * time.Millisecond)

    runtime.ReadMemStats(&m)
    finalAlloc := m.Alloc
    increase := finalAlloc - initialAlloc

    fmt.Printf("Memory Stress Test:\n")
    fmt.Printf("  Initial Alloc: %d MB\n", initialAlloc/1024/1024)
    fmt.Printf("  Final Alloc: %d MB\n", finalAlloc/1024/1024)
    fmt.Printf("  Increase: %d MB\n", increase/1024/1024)
    fmt.Printf("  GC Runs: %d\n", m.NumGC)

    if increase > 50*1024*1024 {
        t.Errorf("Potential memory leak: %d MB increase", increase/1024/1024)
    }
}

// TestGoroutineStress tests goroutine management.
func TestGoroutineStress(t *testing.T) {
    initialGoroutines := runtime.NumGoroutine()

    // Spawn many goroutines
    done := make(chan bool)
    for i := 0; i < 10000; i++ {
        go func() {
            time.Sleep(100 * time.Millisecond)
            done <- true
        }()
    }

    // Wait for completion
    for i := 0; i < 10000; i++ {
        <-done
    }

    time.Sleep(500 * time.Millisecond)
    finalGoroutines := runtime.NumGoroutine()

    fmt.Printf("Goroutine Stress Test:\n")
    fmt.Printf("  Initial: %d\n", initialGoroutines)
    fmt.Printf("  Final: %d\n", finalGoroutines)
    fmt.Printf("  Leak: %d\n", finalGoroutines-initialGoroutines)

    if finalGoroutines-initialGoroutines > 10 {
        t.Errorf("Goroutine leak detected: %d extra goroutines",
            finalGoroutines-initialGoroutines)
    }
}

func processBuffer(buf []byte) {
    // Simulate processing
    for i := range buf {
        buf[i] = byte(i % 256)
    }
}
```

## Phase 6: Performance Regression Detection

### Baseline Management

```go
package regression

import (
    "encoding/json"
    "fmt"
    "os"
    "testing"
    "time"
)

// BenchmarkResult stores benchmark metrics.
type BenchmarkResult struct {
    Name           string        `json:"name"`
    NsPerOp        int64         `json:"ns_per_op"`
    AllocsPerOp    int64         `json:"allocs_per_op"`
    BytesPerOp     int64         `json:"bytes_per_op"`
    Timestamp      time.Time     `json:"timestamp"`
}

// Baseline manages performance baselines.
type Baseline struct {
    Results map[string]BenchmarkResult `json:"results"`
}

// LoadBaseline loads baseline from file.
func LoadBaseline(filename string) (*Baseline, error) {
    file, err := os.Open(filename)
    if err != nil {
        return &Baseline{Results: make(map[string]BenchmarkResult)}, nil
    }
    defer file.Close()

    var baseline Baseline
    if err := json.NewDecoder(file).Decode(&baseline); err != nil {
        return nil, err
    }

    return &baseline, nil
}

// Save saves baseline to file.
func (b *Baseline) Save(filename string) error {
    file, err := os.Create(filename)
    if err != nil {
        return err
    }
    defer file.Close()

    enc := json.NewEncoder(file)
    enc.SetIndent("", "  ")
    return enc.Encode(b)
}

// Compare compares current result with baseline.
func (b *Baseline) Compare(name string, current BenchmarkResult) (bool, float64) {
    baseline, exists := b.Results[name]
    if !exists {
        b.Results[name] = current
        return false, 0
    }

    percentChange := float64(current.NsPerOp-baseline.NsPerOp) / float64(baseline.NsPerOp) * 100
    isRegression := percentChange > 10.0 // 10% threshold

    return isRegression, percentChange
}

// TestBenchmarkRegression checks for performance regressions.
func TestBenchmarkRegression(t *testing.T) {
    baseline, err := LoadBaseline("benchmark_baseline.json")
    if err != nil {
        t.Fatal(err)
    }

    // Run benchmark
    result := testing.Benchmark(func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            expensiveOperation()
        }
    })

    current := BenchmarkResult{
        Name:        "expensiveOperation",
        NsPerOp:     result.NsPerOp(),
        AllocsPerOp: int64(result.AllocsPerOp()),
        BytesPerOp:  int64(result.AllocedBytesPerOp()),
        Timestamp:   time.Now(),
    }

    isRegression, percentChange := baseline.Compare("expensiveOperation", current)

    fmt.Printf("Benchmark Regression Check:\n")
    fmt.Printf("  Name: %s\n", current.Name)
    fmt.Printf("  Current: %d ns/op\n", current.NsPerOp)
    if prev, exists := baseline.Results["expensiveOperation"]; exists {
        fmt.Printf("  Baseline: %d ns/op\n", prev.NsPerOp)
        fmt.Printf("  Change: %.2f%%\n", percentChange)
    }

    if isRegression {
        t.Errorf("Performance regression detected: %.2f%% slower", percentChange)
    }

    if err := baseline.Save("benchmark_baseline.json"); err != nil {
        t.Fatal(err)
    }
}

func expensiveOperation() {
    // Implementation
}
```

## Phase 7: CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on:
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'

jobs:
  performance:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Go
      uses: actions/setup-go@v4
      with:
        go-version: '1.21'

    - name: Install dependencies
      run: go mod download

    - name: Run benchmarks
      run: |
        go test -bench=. -benchmem -benchtime=10s ./... > ${OUTPUT_DIR}/exports/benchmark-results.txt
        cat benchmark-results.txt

    - name: Check for regressions
      run: go test -v ./tests/regression/...

    - name: Run load tests
      run: go test -v -timeout=5m ./tests/load/...

    - name: Profile CPU
      run: |
        go test -bench=. -cpuprofile=cpu.prof
        go tool pprof -text cpu.prof > ${OUTPUT_DIR}/exports/cpu-profile.txt

    - name: Profile Memory
      run: |
        go test -bench=. -memprofile=mem.prof
        go tool pprof -text mem.prof > ${OUTPUT_DIR}/exports/mem-profile.txt

    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: |
          benchmark-results.txt
          cpu-profile.txt
          mem-profile.txt
          *.prof

    - name: Comment PR
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const results = fs.readFileSync('benchmark-results.txt', 'utf8');
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: '## Performance Test Results\n\n```\n' + results + '\n```'
          });
```

## Output Format

Please provide a comprehensive performance testing implementation with the following structure:

### Performance Test Summary

- **Benchmarks Implemented**: [count]

- **Load Tests Created**: [count]

- **Performance Baselines Established**: [yes/no]

- **Regression Detection Configured**: [yes/no]

- **Profiling Tools Set Up**: [list]

### Performance Requirements
| Metric | Target | Measured | Status |
|--------|--------|----------|--------|
| API response P95 | <200ms | [value] | ✅/❌ |
| Throughput | 100 RPS | [value] | ✅/❌ |
| Memory usage | <512MB | [value] | ✅/❌ |
| Goroutines | <10,000 | [value] | ✅/❌ |

### Benchmark Results
```
BenchmarkLinearSearch-8    10000    123456 ns/op    12345 B/op    123 allocs/op
BenchmarkBinarySearch-8    50000     23456 ns/op     2345 B/op     23 allocs/op
```

### Load Test Results
```
Duration:        30s
Total Requests:  2500
Success:         2475
Failures:        25
Success Rate:    99.00%
RPS:             83.3
Latency:
  Average:       120ms
  P50:           115ms
  P95:           180ms
  P99:           250ms
```

### Bottlenecks Identified
1. **Slice Reallocation in processUsers()**
   - **Issue**: Slice grows without pre-allocated capacity
   - **Impact**: Excessive allocations, 150ms overhead
   - **Recommendation**: Pre-allocate slice with make([]User, 0, expectedSize)

2. **String Concatenation in Loop**
   - **Issue**: Using + operator for string building
   - **Impact**: O(n²) complexity, 200ms for large strings
   - **Recommendation**: Use strings.Builder for efficient concatenation

### Performance Improvement Recommendations

- [ ] Pre-allocate slices with known capacity

- [ ] Use sync.Pool for frequently allocated objects

- [ ] Implement worker pools for concurrent operations

- [ ] Add response caching with ttlcache or groupcache

- [ ] Use context for timeout and cancellation

### Test Execution
```bash
# Run benchmarks
go test -bench=. -benchmem

# Profile CPU
go test -bench=. -cpuprofile=cpu.prof
go tool pprof -http=:8080 cpu.prof

# Run load tests
go test -v -timeout=5m ./tests/load/...
```

### Next Steps

- [ ] Establish performance baselines for all critical operations

- [ ] Integrate performance tests into CI/CD pipeline

- [ ] Set up continuous profiling with pprof in production

- [ ] Create performance dashboard with Prometheus/Grafana

- [ ] Schedule regular performance review meetings

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p tests/{phase_name}/test_files
mkdir -p tests/{phase_name}/test_data
mkdir -p tests/{phase_name}/test_reports
mkdir -p tests/{phase_name}/test_configs
```

**Save files as follows**:

- Test files → `tests/{phase_name}/test_files/`

- Test data → `tests/{phase_name}/test_data/`

- Test reports → `tests/{phase_name}/test_reports/`

- Test configs → `tests/{phase_name}/test_configs/`

Replace `{phase_name}` with the specific phase (test_cases, mocks_fixtures, performance_testing, maintenance_cicd, or code_coverage).

~~~

## Output Format

The AI assistant should deliver:

1. **Performance test suite** with testing.B benchmarks and load tests
2. **Performance baselines** documented
3. **Load test scenarios** for critical endpoints
4. **Profiling results** with pprof analysis
5. **Regression detection** configuration
6. **CI/CD integration** for automated performance gates
7. **Performance report** with metrics and recommendations
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
