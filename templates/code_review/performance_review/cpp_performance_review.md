---
template_id: cpp_performance_review
template_name: Performance Review - Cpp
version: 1.0.0
last_updated: 2025-12-03
language: Cpp
category: code_review
phase: performance_review
phase_number: 4
difficulty: advanced
estimated_time_hours: 2-3
prerequisites:

  - code_review/security_review/cpp_security_review.md
related_templates:

  - code_review/code_quality/cpp_code_quality.md
tools:

  - google test
  - catch2
  - boost.test
tags:

  - code-review
  - performance
  - code-review
  - cpp
---
# C++ Performance Review

## Objective
Systematically identify performance bottlenecks, inefficient algorithms, and resource usage issues. Provide data-driven optimization recommendations to improve application speed, memory efficiency, and scalability with focus on C++-specific optimizations.

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

- [ ] CPU profiling completed (perf, Valgrind, VTune)

- [ ] Memory profiling performed (Valgrind, Heaptrack)

- [ ] Cache analysis conducted (perf, Cachegrind)

- [ ] Hot paths and bottlenecks identified

- [ ] Function-level timing measurements captured

### Algorithm Efficiency

- [ ] Time complexity evaluated (O(n), O(n²), etc.)

- [ ] Space complexity assessed

- [ ] Inefficient loops identified (nested, redundant)

- [ ] Algorithmic improvements documented

- [ ] Data structure choices reviewed

### Memory Performance

- [ ] Memory allocation patterns analyzed

- [ ] Cache locality issues identified

- [ ] Memory fragmentation assessed

- [ ] Object size optimization reviewed

- [ ] Memory alignment checked

### C++ Specific Optimizations

- [ ] Move semantics usage evaluated

- [ ] Copy elision opportunities identified

- [ ] RVO/NRVO application assessed

- [ ] Template instantiation overhead reviewed

- [ ] Compile-time computation opportunities (constexpr)

### I/O Performance

- [ ] File I/O operations profiled

- [ ] Buffering strategies reviewed

- [ ] Serialization performance assessed

- [ ] Memory-mapped I/O opportunities identified

### Concurrency & Parallelism

- [ ] Threading/async opportunities identified

- [ ] Lock contention measured

- [ ] Thread pool usage evaluated

- [ ] SIMD opportunities assessed

- [ ] Parallel algorithm usage reviewed

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
# C++ Performance Review

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

Please perform a comprehensive performance review of this C++ application following this protocol:

## Phase 1: Performance Profiling Setup

1. **CPU Profiling with perf (Linux)**
   ```bash
   # Build with debug symbols
   cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo ..
   make

   # Profile with perf
   perf record -g ./application
   perf report

   # Generate flamegraph
   perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg

   # Profile specific function
   perf record -g -e cycles:u ./application
   ```

2. **Profiling with Valgrind/Callgrind**
   ```bash
   # CPU profiling with Callgrind
   valgrind --tool=callgrind --callgrind-out-file=callgrind.out ./application

   # Visualize with kcachegrind
   kcachegrind callgrind.out

   # Cache profiling with Cachegrind
   valgrind --tool=cachegrind --cachegrind-out-file=cachegrind.out ./application
   cg_annotate cachegrind.out
   ```

3. **Memory Profiling**
   ```bash
   # Valgrind Massif for heap profiling
   valgrind --tool=massif --massif-out-file=massif.out ./application
   ms_print massif.out

   # Heaptrack for heap profiling
   heaptrack ./application
   heaptrack_gui heaptrack.application.pid.gz

   # Memory bandwidth profiling
   perf stat -e cache-misses,cache-references ./application
   ```

4. **Intel VTune Profiler (if available)**
   ```bash
   # Hotspot analysis
   vtune -collect hotspots ./application

   # Memory access analysis
   vtune -collect memory-access ./application

   # Microarchitecture analysis
   vtune -collect uarch-exploration ./application
   ```

5. **Tracy Profiler (Real-time profiling)**
   ```cpp
   // Add Tracy instrumentation
   #include <Tracy.hpp>

   void myFunction() {
       ZoneScoped;  // Automatic function profiling
       // ... function body ...
   }
   ```

## Phase 2: Bottleneck Identification

1. **Analyze Profiling Results**
   - Identify functions consuming >5% of total time
   - Find functions called excessive times
   - Locate memory-intensive operations
   - Identify cache-inefficient code
   - Find branch mispredictions

2. **Hot Path Analysis**
   - Map critical execution paths
   - Measure end-to-end latency
   - Identify slowest operations
   - Document user-facing performance impacts

3. **Cache Performance**
   ```bash
   # Analyze cache misses with perf
   perf stat -e L1-dcache-load-misses,L1-dcache-loads,\
   LLC-load-misses,LLC-loads ./application

   # Typical metrics:
   - L1 cache miss rate
   - L2 cache miss rate
   - L3 (LLC) cache miss rate
   - TLB miss rate
   ```

## Phase 3: Algorithm & Data Structure Review

1. **Time Complexity Analysis**
   - Review loops and nested iterations
   - Identify O(n²) or worse algorithms
   - Check for redundant computations
   - Assess search and sort operations

2. **Common Performance Anti-Patterns**
   ```cpp
   // Inefficient patterns to search for:

   // 1. Unnecessary copies
   void processVector(std::vector<int> vec) {  // BAD: copies entire vector
       // ...
   }
   // Better:
   void processVector(const std::vector<int>& vec) {  // Good: pass by const ref
       // ...
   }

   // 2. String concatenation in loop
   std::string result;
   for (const auto& str : strings) {
       result += str;  // BAD: reallocations on each iteration
   }
   // Better:
   std::string result;
   result.reserve(total_size);  // Pre-allocate
   for (const auto& str : strings) {
       result += str;
   }

   // 3. Repeated lookup in map
   for (const auto& key : keys) {
       if (map.find(key) != map.end()) {
           auto value = map[key];  // BAD: double lookup
       }
   }
   // Better:
   for (const auto& key : keys) {
       auto it = map.find(key);
       if (it != map.end()) {
           auto value = it->second;  // Single lookup
       }
   }

   // 4. Creating temporary objects
   std::string getFullName(const std::string& first, const std::string& last) {
       return first + " " + last;  // Creates multiple temporary strings
   }
   // Better:
   std::string getFullName(const std::string& first, const std::string& last) {
       std::string result;
       result.reserve(first.size() + 1 + last.size());
       result = first;
       result += ' ';
       result += last;
       return result;  // RVO applies
   }

   // 5. Virtual function calls in hot loops
   for (size_t i = 0; i < huge_count; ++i) {
       obj->virtualMethod();  // BAD: indirect call overhead in hot loop
   }

   // 6. Unnecessary std::endl
   for (const auto& item : items) {
       std::cout << item << std::endl;  // BAD: flushes buffer each time
   }
   // Better:
   for (const auto& item : items) {
       std::cout << item << '\n';  // Good: no flush
   }
   // Flush once at end if needed
   std::cout << std::flush;
   ```

3. **Data Structure Optimization**
   ```cpp
   // Evaluate container choices
   // BAD: Wrong container for access pattern
   std::vector<int> data;
   for (int i = 0; i < 1000000; ++i) {
       data.insert(data.begin(), i);  // O(n) insertion at front
   }

   // GOOD: Use appropriate container
   std::deque<int> data;  // O(1) insertion at front
   // or std::list if frequent insertions in middle

   // BAD: std::map when order not needed
   std::map<std::string, int> lookup;  // O(log n) lookup

   // GOOD: std::unordered_map for faster lookup
   std::unordered_map<std::string, int> lookup;  // O(1) average lookup

   // Consider:
   - std::vector: contiguous memory, cache-friendly
   - std::deque: fast front/back insertion
   - std::list: fast arbitrary insertion (poor cache locality)
   - std::unordered_map: fast lookup (higher memory)
   - Small vector optimization (SVO)
   - Flat maps (sorted vector) for small datasets
   ```

## Phase 4: Memory Performance Analysis

1. **Memory Allocation Profiling**
   ```cpp
   // Identify allocation hotspots
   // BAD: Frequent allocations in loop
   for (int i = 0; i < iterations; ++i) {
       std::vector<int> temp(size);  // Allocates on each iteration
       process(temp);
   }

   // GOOD: Reuse allocation
   std::vector<int> temp;
   temp.reserve(size);
   for (int i = 0; i < iterations; ++i) {
       temp.clear();
       fillVector(temp);
       process(temp);
   }

   // Consider:
   - Object pooling for frequently allocated objects
   - Arena allocators for temporary allocations
   - Stack allocation for small objects
   - Custom allocators for specific patterns
   ```

2. **Cache Locality Optimization**
   ```cpp
   // BAD: Poor cache locality
   struct Object {
       int id;
       char padding[60];  // Forces objects far apart
       int value;
   };
   std::vector<Object> objects(1000000);
   for (auto& obj : objects) {
       process(obj.value);  // Poor cache utilization
   }

   // GOOD: Structure of Arrays (SoA)
   struct Objects {
       std::vector<int> ids;
       std::vector<int> values;
   };
   Objects objects;
   objects.values.resize(1000000);
   for (auto value : objects.values) {
       process(value);  // Better cache utilization
   }

   // Consider:
   - Data-oriented design
   - Structure of Arrays vs Array of Structures
   - Memory alignment
   - Padding to cache line boundaries
   ```

3. **Object Size Optimization**
   ```cpp
   // Check object sizes
   std::cout << "sizeof(MyClass): " << sizeof(MyClass) << std::endl;

   // Optimize member order to minimize padding
   // BAD:
   struct BadLayout {
       char a;     // 1 byte + 7 padding
       int64_t b;  // 8 bytes
       char c;     // 1 byte + 7 padding
       int64_t d;  // 8 bytes
   };  // Total: 32 bytes

   // GOOD:
   struct GoodLayout {
       int64_t b;  // 8 bytes
       int64_t d;  // 8 bytes
       char a;     // 1 byte
       char c;     // 1 byte + 6 padding
   };  // Total: 24 bytes

   // Use [[no_unique_address]] for empty members (C++20)
   ```

## Phase 5: C++ Specific Optimizations

1. **Move Semantics**
   ```cpp
   // Verify move semantics usage
   // BAD: Returning by const value prevents move
   const std::vector<int> getData() {
       std::vector<int> result(1000);
       return result;  // Copy instead of move
   }

   // GOOD: Return by value, enable RVO/move
   std::vector<int> getData() {
       std::vector<int> result(1000);
       return result;  // RVO or move
   }

   // BAD: Unnecessary copy
   void process(std::vector<int> data) {  // Copy
       // ...
   }

   // GOOD: Move or reference
   void process(std::vector<int>&& data) {  // Move
       // ...
   }
   // Or:
   void process(const std::vector<int>& data) {  // Reference
       // ...
   }
   ```

2. **RVO/NRVO Optimization**
   ```cpp
   // Named Return Value Optimization (NRVO)
   // Compilers can elide copies when returning local objects

   // Enable NRVO:
   std::vector<int> createVector() {
       std::vector<int> result;
       result.push_back(1);
       result.push_back(2);
       return result;  // NRVO: no copy or move
   }

   // Prevent NRVO (return different objects):
   std::vector<int> createVector(bool flag) {
       std::vector<int> result1;
       std::vector<int> result2;
       return flag ? result1 : result2;  // NRVO not possible
   }
   ```

3. **constexpr and Compile-Time Computation**
   ```cpp
   // Move computation to compile-time
   // Runtime:
   int factorial(int n) {
       return n <= 1 ? 1 : n * factorial(n - 1);
   }
   int result = factorial(10);  // Computed at runtime

   // Compile-time:
   constexpr int factorial(int n) {
       return n <= 1 ? 1 : n * factorial(n - 1);
   }
   constexpr int result = factorial(10);  // Computed at compile time

   // Use constexpr for:
   - Mathematical constants
   - Configuration values
   - Lookup tables
   - Type traits
   ```

4. **Template Optimization**
   ```cpp
   // Reduce template instantiation bloat
   // BAD: Separate instantiation for each type
   template<typename T>
   void processImpl(T* data, size_t size) {
       // Complex implementation
   }

   // GOOD: Factor out type-independent code
   void processImplInternal(void* data, size_t size, size_t element_size) {
       // Type-independent implementation
   }

   template<typename T>
   void processImpl(T* data, size_t size) {
       processImplInternal(data, size, sizeof(T));
   }

   // Use extern template to prevent instantiation:
   extern template class std::vector<int>;
   ```

5. **Small String Optimization (SSO)**
   ```cpp
   // Be aware of SSO - strings under ~15 chars often don't allocate
   std::string small = "short";  // No heap allocation (SSO)
   std::string large = "this is a very long string";  // Heap allocation

   // Optimize for SSO when possible
   ```

## Phase 6: I/O Performance

1. **File I/O Optimization**
   ```cpp
   // BAD: Character-by-character reading
   std::ifstream file("data.txt");
   char c;
   while (file.get(c)) {
       process(c);
   }

   // GOOD: Buffered reading
   std::ifstream file("data.txt");
   std::string line;
   while (std::getline(file, line)) {
       process(line);
   }

   // BETTER: Read entire file
   std::ifstream file("data.txt");
   std::string content((std::istreambuf_iterator<char>(file)),
                       std::istreambuf_iterator<char>());

   // BEST for large files: Memory-mapped I/O
   #include <sys/mman.h>
   // Use mmap() for large file access
   ```

2. **Serialization Performance**
   - Evaluate binary vs text serialization
   - Consider zero-copy serialization (flatbuffers, cap'n proto)
   - Review custom serialization overhead
   - Assess compression impact

## Phase 7: Concurrency & Parallelism

1. **Threading Opportunities**
   ```cpp
   // Identify parallelizable operations
   // Sequential:
   for (auto& item : items) {
       expensiveOperation(item);
   }

   // Parallel with std::for_each (C++17):
   #include <execution>
   std::for_each(std::execution::par, items.begin(), items.end(),
                 [](auto& item) { expensiveOperation(item); });

   // Thread pool:
   ThreadPool pool(std::thread::hardware_concurrency());
   for (auto& item : items) {
       pool.enqueue([&item]() { expensiveOperation(item); });
   }
   ```

2. **Lock Contention Analysis**
   ```bash
   # Profile lock contention with perf
   perf record -e 'syscalls:sys_enter_futex' ./application
   perf report

   # Or use ThreadSanitizer
   cmake -DCMAKE_CXX_FLAGS="-fsanitize=thread" ..
   ```

   ```cpp
   // Reduce lock contention
   // BAD: Coarse-grained locking
   std::mutex global_mutex;
   void process(int id) {
       std::lock_guard<std::mutex> lock(global_mutex);
       // Long operation
   }

   // GOOD: Fine-grained locking
   std::array<std::mutex, 16> shard_mutexes;
   void process(int id) {
       std::lock_guard<std::mutex> lock(shard_mutexes[id % 16]);
       // Long operation
   }

   // BETTER: Lock-free data structures
   std::atomic<int> counter;
   counter.fetch_add(1, std::memory_order_relaxed);
   ```

3. **SIMD Opportunities**
   ```cpp
   // Identify SIMD-friendly operations
   // Sequential:
   void addArrays(float* a, float* b, float* result, size_t n) {
       for (size_t i = 0; i < n; ++i) {
           result[i] = a[i] + b[i];
       }
   }

   // SIMD (compiler auto-vectorization):
   void addArrays(float* __restrict__ a, float* __restrict__ b,
                  float* __restrict__ result, size_t n) {
       #pragma omp simd
       for (size_t i = 0; i < n; ++i) {
           result[i] = a[i] + b[i];
       }
   }

   // Explicit SIMD with intrinsics (AVX):
   #include <immintrin.h>
   void addArraysAVX(float* a, float* b, float* result, size_t n) {
       for (size_t i = 0; i < n; i += 8) {
           __m256 va = _mm256_load_ps(&a[i]);
           __m256 vb = _mm256_load_ps(&b[i]);
           __m256 vr = _mm256_add_ps(va, vb);
           _mm256_store_ps(&result[i], vr);
       }
   }
   ```

## Phase 8: Compiler Optimization Analysis

1. **Optimization Flags**
   ```cmake
   # Verify optimization flags
   # Release build should have:
   set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG -march=native")

   # Profile-guided optimization (PGO)
   # Step 1: Build with profiling
   set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-generate")
   # Step 2: Run representative workload
   # Step 3: Rebuild with profile data
   set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-use")

   # Link-time optimization (LTO)
   set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)
   ```

2. **Branch Prediction**
   ```cpp
   // Help branch predictor with likely/unlikely (C++20)
   if (x > 0) [[likely]] {
       // Common case
   } else {
       // Rare case
   }

   // Or use compiler builtins
   if (__builtin_expect(x > 0, 1)) {
       // Common case
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
**Top 10 Time-Consuming Functions**:
| Function | File | Time | % Total | Calls | Time/Call | Category |
|----------|------|------|---------|-------|-----------|----------|
| [name] | [path] | [ms] | [%] | [count] | [μs] | [CPU/Memory/I/O] |

**Cache Performance**:
| Metric | Value | Status |
|--------|-------|--------|
| L1 Cache Miss Rate | [%] | [Good/Poor] |
| L2 Cache Miss Rate | [%] | [Good/Poor] |
| L3 Cache Miss Rate | [%] | [Good/Poor] |
| TLB Miss Rate | [%] | [Good/Poor] |

**Memory Profile**:
| Metric | Value |
|--------|-------|
| Peak Heap Usage | [MB] |
| Total Allocations | [count] |
| Allocation Hotspots | [top 5 locations] |

### Critical Performance Issues (Priority 1)
| Issue | Location | Impact | Current | Target | Optimization |
|-------|----------|--------|---------|--------|--------------|
| [description] | [file:line] | [High] | [metric] | [goal] | [strategy] |

### Algorithm Inefficiencies
**O(n²) or Worse Algorithms Detected**:
| Function | Location | Complexity | Current Performance | Optimized Approach |
|----------|----------|------------|---------------------|-------------------|
| [name] | [file:line] | [O(n²)] | [metric] | [suggested algorithm] |

### Memory Performance Issues
**Allocation Hotspots**:
| Location | Allocations/sec | Avg Size | Impact | Optimization |
|----------|----------------|----------|--------|--------------|
| [file:line] | [count] | [bytes] | [High] | [pooling/reuse] |

**Cache Inefficiency**:
| Issue | Location | Miss Rate | Optimization |
|-------|----------|-----------|--------------|
| [poor locality] | [file:line] | [%] | [SoA/alignment] |

### C++ Optimization Opportunities
**Move Semantics**:
| Location | Issue | Fix | Expected Gain |
|----------|-------|-----|---------------|
| [file:line] | [unnecessary copy] | [use move] | [%] |

**constexpr Opportunities**:
| Location | Computation | Benefit |
|----------|-------------|---------|
| [file:line] | [runtime calc] | [compile-time] |

**Template Optimization**:
| Issue | Location | Bloat Size | Fix |
|-------|----------|------------|-----|
| [excessive instantiation] | [file:line] | [KB] | [factor common code] |

### I/O Performance

- **File I/O Operations**: [count and total time]

- **Buffering Issues**: [locations]

- **Memory-Mapped I/O Opportunities**: [candidates]

### Concurrency Assessment

- **Current Concurrency Model**: [threading/async/none]

- **Lock Contention**: [hotspots]

- **Parallelization Opportunities**: [specific candidates]

- **SIMD Opportunities**: [vectorizable loops]

### Compiler Optimization Analysis

- **Current Optimization Level**: [-O2/-O3]

- **LTO Enabled**: [yes/no]

- **PGO Used**: [yes/no]

- **Recommendations**: [specific flags to add]

### Optimization Recommendations

**Quick Wins** (< 1 day effort, high impact):
1. **[Optimization]**
   - **Location**: [file:line]
   - **Current**: [metric]
   - **Expected Improvement**: [metric/percentage]
   - **Implementation**: [specific steps]

**Medium-term** (1-3 days effort):
[List of optimizations requiring moderate refactoring]

**Strategic** (> 3 days, architectural changes):
[List of major performance initiatives]

### Benchmark Results
**Before Optimization**:

- Operation X: [time/throughput]

- Memory usage: [MB]

**After Optimization** (projected):

- Operation X: [time/throughput]

- Memory usage: [MB]

**Improvement**: [X]x faster / [Y]% less memory

### Performance Testing Recommendations
```bash
# Benchmarking with Google Benchmark
#include <benchmark/benchmark.h>

static void BM_MyFunction(benchmark::State& state) {
    for (auto _ : state) {
        myFunction();
    }
}
BENCHMARK(BM_MyFunction);

# Run benchmarks
./my_benchmarks --benchmark_out=results.json
```

### Monitoring Recommendations

- Response time tracking (p50, p95, p99)

- Memory usage alerts

- CPU utilization monitoring

- Cache miss rate tracking

### Next Steps

- [ ] Implement quick win optimizations

- [ ] Set up performance benchmarking suite

- [ ] Configure production performance monitoring

- [ ] Plan load testing

- [ ] Schedule performance review sprint

- [ ] Document performance SLAs/targets

## Notes

- Profile in release builds with debug symbols (-O3 -g)

- Optimize based on profiling data, not assumptions

- Focus on hot paths (95% of time in 5% of code)

- Consider scalability alongside raw performance

- Balance performance with code maintainability

- Test performance improvements with realistic data

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
