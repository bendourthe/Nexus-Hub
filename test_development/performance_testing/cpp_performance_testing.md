# C++ Performance Testing

## Objective
Implement comprehensive performance testing to validate system behavior under load, identify bottlenecks, measure response times, profile resource usage, detect performance regressions, and ensure scalability requirements are met using C++ tooling.

## Output Directory Structure

All test outputs should be saved in organized directories:

```
tests/
└── performance_testing/
    ├── test_files/
    ├── test_data/
    ├── test_reports/
    └── test_configs/
```

**Directory Setup**:

- Create `tests/{phase}/` directory in repository root if it doesn't exist

- All test files, data, reports, and configurations go in the phase-specific directory

**Expected Outputs**:

- `test_files/` - Actual test implementation files

- `test_data/` - Test fixtures, mock data, sample inputs

- `test_reports/` - Test execution reports, coverage reports, performance results

- `test_configs/` - Framework configurations, test runner settings

## Implementation Checklist

### Performance Test Coverage
- [ ] Load tests implemented for critical functions
- [ ] Stress tests validate edge cases and limits
- [ ] Baseline benchmarks established with Google Benchmark
- [ ] Performance regression tests configured
- [ ] Resource profiling set up

### Metrics and Monitoring
- [ ] Execution time thresholds defined
- [ ] Throughput targets established
- [ ] Resource usage limits set (memory, CPU)
- [ ] Memory leak detection configured
- [ ] Performance reports automated

### Test Infrastructure
- [ ] Google Benchmark configured
- [ ] Memory profiling tools configured
- [ ] Performance test data prepared
- [ ] CI/CD integration planned
- [ ] Results storage and trending implemented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C++ Performance Testing Implementation

Please implement comprehensive performance testing for this C++ project following this protocol:

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

**Execution Time Requirements**:
| Operation | Target | P95 | P99 | Timeout |
|-----------|--------|-----|-----|---------|
| Data processing | <10ms | <20ms | <50ms | 100ms |
| Memory allocation | <1ms | <2ms | <5ms | 10ms |
| File I/O | <50ms | <100ms | <200ms | 1s |
| Network operation | <100ms | <200ms | <500ms | 2s |

**Throughput Requirements**:
| Operation | Target ops/sec | Peak ops/sec |
|-----------|----------------|--------------|
| Container operations | 100,000 | 500,000 |
| String processing | 50,000 | 250,000 |

**Resource Limits**:
- **Memory**: <512MB heap allocation
- **CPU**: <80% average, <95% peak
- **Thread count**: <100 threads
- **Cache efficiency**: >90% L1 hit rate

## Phase 2: Benchmarking with Google Benchmark

### Setup Google Benchmark

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.14)
project(PerformanceTests)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Download and configure Google Benchmark
include(FetchContent)
FetchContent_Declare(
    benchmark
    GIT_REPOSITORY https://github.com/google/benchmark.git
    GIT_TAG v1.8.3
)
FetchContent_MakeAvailable(benchmark)

# Add benchmark executable
add_executable(benchmarks
    benchmarks/string_benchmarks.cpp
    benchmarks/container_benchmarks.cpp
    benchmarks/algorithm_benchmarks.cpp
)

target_link_libraries(benchmarks
    PRIVATE benchmark::benchmark
)

# Enable optimizations for release builds
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    target_compile_options(benchmarks PRIVATE -O3 -march=native)
endif()
```

### Basic Benchmarks

```cpp
/**
 * string_benchmarks.cpp
 *
 * Performance benchmarks for string operations.
 */
#include <benchmark/benchmark.h>
#include <string>
#include <sstream>
#include <vector>

// Benchmark: String concatenation with operator+
static void BM_StringConcatenation(benchmark::State& state) {
    for (auto _ : state) {
        std::string result;
        for (int i = 0; i < state.range(0); ++i) {
            result = result + "test";
        }
        benchmark::DoNotOptimize(result);
    }
}
BENCHMARK(BM_StringConcatenation)->Range(8, 8<<10);

// Benchmark: String concatenation with stringstream
static void BM_StringStream(benchmark::State& state) {
    for (auto _ : state) {
        std::stringstream ss;
        for (int i = 0; i < state.range(0); ++i) {
            ss << "test";
        }
        std::string result = ss.str();
        benchmark::DoNotOptimize(result);
    }
}
BENCHMARK(BM_StringStream)->Range(8, 8<<10);

// Benchmark: String concatenation with append
static void BM_StringAppend(benchmark::State& state) {
    for (auto _ : state) {
        std::string result;
        result.reserve(state.range(0) * 4); // Reserve space
        for (int i = 0; i < state.range(0); ++i) {
            result.append("test");
        }
        benchmark::DoNotOptimize(result);
    }
}
BENCHMARK(BM_StringAppend)->Range(8, 8<<10);

// Benchmark: String find operations
static void BM_StringFind(benchmark::State& state) {
    std::string haystack(state.range(0), 'a');
    haystack += "needle";

    for (auto _ : state) {
        auto pos = haystack.find("needle");
        benchmark::DoNotOptimize(pos);
    }
}
BENCHMARK(BM_StringFind)->Range(8, 8<<20);

BENCHMARK_MAIN();
```

### Advanced Benchmark Patterns

```cpp
/**
 * container_benchmarks.cpp
 *
 * Performance benchmarks for STL containers.
 */
#include <benchmark/benchmark.h>
#include <vector>
#include <list>
#include <deque>
#include <set>
#include <unordered_set>
#include <map>
#include <unordered_map>
#include <algorithm>

// Fixture for container benchmarks
class ContainerFixture : public benchmark::Fixture {
public:
    void SetUp(const ::benchmark::State& state) {
        size_ = state.range(0);
        data_.resize(size_);
        for (int i = 0; i < size_; ++i) {
            data_[i] = i;
        }
    }

    void TearDown(const ::benchmark::State&) {
        data_.clear();
    }

protected:
    int size_;
    std::vector<int> data_;
};

// Vector operations
BENCHMARK_DEFINE_F(ContainerFixture, VectorPushBack)(benchmark::State& st) {
    for (auto _ : st) {
        std::vector<int> vec;
        for (int i = 0; i < size_; ++i) {
            vec.push_back(i);
        }
        benchmark::DoNotOptimize(vec);
    }
}
BENCHMARK_REGISTER_F(ContainerFixture, VectorPushBack)->Range(8, 8<<10);

BENCHMARK_DEFINE_F(ContainerFixture, VectorPushBackReserve)(benchmark::State& st) {
    for (auto _ : st) {
        std::vector<int> vec;
        vec.reserve(size_);
        for (int i = 0; i < size_; ++i) {
            vec.push_back(i);
        }
        benchmark::DoNotOptimize(vec);
    }
}
BENCHMARK_REGISTER_F(ContainerFixture, VectorPushBackReserve)->Range(8, 8<<10);

// Map vs unordered_map
BENCHMARK_DEFINE_F(ContainerFixture, MapInsert)(benchmark::State& st) {
    for (auto _ : st) {
        std::map<int, int> m;
        for (int i = 0; i < size_; ++i) {
            m[i] = i;
        }
        benchmark::DoNotOptimize(m);
    }
}
BENCHMARK_REGISTER_F(ContainerFixture, MapInsert)->Range(8, 8<<10);

BENCHMARK_DEFINE_F(ContainerFixture, UnorderedMapInsert)(benchmark::State& st) {
    for (auto _ : st) {
        std::unordered_map<int, int> m;
        m.reserve(size_);
        for (int i = 0; i < size_; ++i) {
            m[i] = i;
        }
        benchmark::DoNotOptimize(m);
    }
}
BENCHMARK_REGISTER_F(ContainerFixture, UnorderedMapInsert)->Range(8, 8<<10);

// Algorithm benchmarks
static void BM_Sort(benchmark::State& state) {
    std::vector<int> data(state.range(0));
    for (auto _ : state) {
        state.PauseTiming();
        std::generate(data.begin(), data.end(), std::rand);
        state.ResumeTiming();

        std::sort(data.begin(), data.end());
        benchmark::DoNotOptimize(data);
    }
}
BENCHMARK(BM_Sort)->Range(8, 8<<15);

// Multithreaded benchmark
static void BM_ParallelSort(benchmark::State& state) {
    std::vector<int> data(state.range(0));
    for (auto _ : state) {
        state.PauseTiming();
        std::generate(data.begin(), data.end(), std::rand);
        state.ResumeTiming();

        // Use parallel execution (C++17)
        std::sort(std::execution::par, data.begin(), data.end());
        benchmark::DoNotOptimize(data);
    }
}
BENCHMARK(BM_ParallelSort)->Range(8, 8<<15)->ThreadRange(1, 8);

// Template benchmark
template<typename Container>
static void BM_ContainerIteration(benchmark::State& state) {
    Container container(state.range(0), 42);
    for (auto _ : state) {
        int sum = 0;
        for (const auto& elem : container) {
            sum += elem;
        }
        benchmark::DoNotOptimize(sum);
    }
}
BENCHMARK_TEMPLATE(BM_ContainerIteration, std::vector<int>)->Range(8, 8<<10);
BENCHMARK_TEMPLATE(BM_ContainerIteration, std::list<int>)->Range(8, 8<<10);
BENCHMARK_TEMPLATE(BM_ContainerIteration, std::deque<int>)->Range(8, 8<<10);
```

### Custom Counters and Statistics

```cpp
/**
 * advanced_benchmarks.cpp
 *
 * Benchmarks with custom metrics and statistics.
 */
#include <benchmark/benchmark.h>
#include <vector>
#include <numeric>

// Benchmark with custom counters
static void BM_VectorProcessing(benchmark::State& state) {
    std::vector<int> vec(state.range(0), 42);
    size_t bytes_processed = 0;

    for (auto _ : state) {
        int sum = std::accumulate(vec.begin(), vec.end(), 0);
        benchmark::DoNotOptimize(sum);
        bytes_processed += vec.size() * sizeof(int);
    }

    state.SetBytesProcessed(bytes_processed);
    state.SetItemsProcessed(state.iterations() * vec.size());

    // Custom counter
    state.counters["elements"] = benchmark::Counter(
        vec.size(),
        benchmark::Counter::kIsRate
    );
}
BENCHMARK(BM_VectorProcessing)->Range(8, 8<<15);

// Benchmark with complexity analysis
static void BM_LinearComplexity(benchmark::State& state) {
    std::vector<int> vec(state.range(0), 42);

    for (auto _ : state) {
        for (const auto& elem : vec) {
            benchmark::DoNotOptimize(elem);
        }
    }

    state.SetComplexityN(state.range(0));
}
BENCHMARK(BM_LinearComplexity)
    ->Range(8, 8<<15)
    ->Complexity(benchmark::oN);

// Benchmark with custom statistics
static void BM_CustomStatistics(benchmark::State& state) {
    for (auto _ : state) {
        std::vector<int> vec(1000);
        std::generate(vec.begin(), vec.end(), std::rand);
        benchmark::DoNotOptimize(vec);
    }
}
BENCHMARK(BM_CustomStatistics)
    ->Repetitions(10)
    ->ReportAggregatesOnly(true)
    ->ComputeStatistics("max", [](const std::vector<double>& v) -> double {
        return *std::max_element(v.begin(), v.end());
    });
```

### Running Benchmarks

```bash
# Build benchmarks
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
make

# Run all benchmarks
./benchmarks

# Run specific benchmark
./benchmarks --benchmark_filter=BM_StringAppend

# Run with time unit
./benchmarks --benchmark_time_unit=ms

# Run with repetitions
./benchmarks --benchmark_repetitions=5

# Generate JSON output
./benchmarks --benchmark_format=json --benchmark_out=results.json

# Generate CSV output
./benchmarks --benchmark_format=csv --benchmark_out=results.csv

# Compare results
./benchmarks --benchmark_out=new.json
compare.py benchstat old.json new.json
```

## Phase 3: Memory Profiling

### Smart Pointer Benchmarks

```cpp
/**
 * memory_benchmarks.cpp
 *
 * Benchmarks for memory allocation and smart pointers.
 */
#include <benchmark/benchmark.h>
#include <memory>
#include <vector>

struct LargeObject {
    std::array<int, 1000> data;
};

// Raw pointer allocation
static void BM_RawPointer(benchmark::State& state) {
    for (auto _ : state) {
        auto* obj = new LargeObject();
        benchmark::DoNotOptimize(obj);
        delete obj;
    }
}
BENCHMARK(BM_RawPointer);

// unique_ptr allocation
static void BM_UniquePtr(benchmark::State& state) {
    for (auto _ : state) {
        auto obj = std::make_unique<LargeObject>();
        benchmark::DoNotOptimize(obj);
    }
}
BENCHMARK(BM_UniquePtr);

// shared_ptr allocation
static void BM_SharedPtr(benchmark::State& state) {
    for (auto _ : state) {
        auto obj = std::make_shared<LargeObject>();
        benchmark::DoNotOptimize(obj);
    }
}
BENCHMARK(BM_SharedPtr);

// Object pool pattern
template<typename T>
class ObjectPool {
public:
    ObjectPool(size_t size) {
        pool_.reserve(size);
        for (size_t i = 0; i < size; ++i) {
            pool_.push_back(std::make_unique<T>());
        }
    }

    T* acquire() {
        if (pool_.empty()) {
            return nullptr;
        }
        T* obj = pool_.back().release();
        pool_.pop_back();
        return obj;
    }

    void release(T* obj) {
        pool_.push_back(std::unique_ptr<T>(obj));
    }

private:
    std::vector<std::unique_ptr<T>> pool_;
};

static void BM_ObjectPool(benchmark::State& state) {
    ObjectPool<LargeObject> pool(100);

    for (auto _ : state) {
        auto* obj = pool.acquire();
        benchmark::DoNotOptimize(obj);
        pool.release(obj);
    }
}
BENCHMARK(BM_ObjectPool);
```

### Using Valgrind

```bash
# Memory leak detection
valgrind --leak-check=full \
         --show-leak-kinds=all \
         --track-origins=yes \
         --verbose \
         --log-file=valgrind-memory.txt \
         ./benchmarks --benchmark_filter=BM_RawPointer

# Memory profiling with massif
valgrind --tool=massif \
         --massif-out-file=massif.out \
         ./benchmarks

# Visualize massif output
ms_print massif.out

# Cache profiling
valgrind --tool=cachegrind \
         --cachegrind-out-file=cachegrind.out \
         ./benchmarks

# Analyze cachegrind output
cg_annotate cachegrind.out
```

### Using Sanitizers

```cmake
# CMakeLists.txt - Enable sanitizers

# Address Sanitizer (detects memory errors)
option(ENABLE_ASAN "Enable Address Sanitizer" OFF)
if(ENABLE_ASAN)
    target_compile_options(benchmarks PRIVATE -fsanitize=address -fno-omit-frame-pointer)
    target_link_options(benchmarks PRIVATE -fsanitize=address)
endif()

# Memory Sanitizer (detects uninitialized reads)
option(ENABLE_MSAN "Enable Memory Sanitizer" OFF)
if(ENABLE_MSAN)
    target_compile_options(benchmarks PRIVATE -fsanitize=memory -fno-omit-frame-pointer)
    target_link_options(benchmarks PRIVATE -fsanitize=memory)
endif()

# Thread Sanitizer (detects data races)
option(ENABLE_TSAN "Enable Thread Sanitizer" OFF)
if(ENABLE_TSAN)
    target_compile_options(benchmarks PRIVATE -fsanitize=thread)
    target_link_options(benchmarks PRIVATE -fsanitize=thread)
endif()

# Undefined Behavior Sanitizer
option(ENABLE_UBSAN "Enable Undefined Behavior Sanitizer" OFF)
if(ENABLE_UBSAN)
    target_compile_options(benchmarks PRIVATE -fsanitize=undefined)
    target_link_options(benchmarks PRIVATE -fsanitize=undefined)
endif()
```

## Phase 4: CPU Profiling

### Using perf (Linux)

```bash
# Compile with debug symbols
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo ..
make

# Record performance data
perf record -g ./benchmarks

# View performance report
perf report

# Generate flamegraph
perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg

# CPU cache analysis
perf stat -e cache-references,cache-misses,cycles,instructions,branches,branch-misses ./benchmarks

# Record call graph
perf record -g --call-graph dwarf ./benchmarks

# Analyze specific function
perf record -e cpu-cycles -g ./benchmarks
perf report --sort comm,dso,symbol
```

### Using Intel VTune

```bash
# Hotspot analysis
vtune -collect hotspots -result-dir=vtune_results -- ./benchmarks

# Memory access analysis
vtune -collect memory-access -result-dir=vtune_results -- ./benchmarks

# Threading analysis
vtune -collect threading -result-dir=vtune_results -- ./benchmarks

# Generate HTML report
vtune -report summary -result-dir=vtune_results -format html -report-output=vtune_report.html
```

### Custom Profiling

```cpp
/**
 * profiler.hpp
 *
 * Simple RAII-based profiler for hot path analysis.
 */
#ifndef PROFILER_HPP
#define PROFILER_HPP

#include <chrono>
#include <string>
#include <unordered_map>
#include <iostream>
#include <iomanip>

class Profiler {
public:
    struct Stats {
        uint64_t call_count = 0;
        double total_ms = 0.0;
        double min_ms = std::numeric_limits<double>::max();
        double max_ms = 0.0;
    };

    class ScopedTimer {
    public:
        ScopedTimer(Profiler& profiler, const std::string& name)
            : profiler_(profiler), name_(name) {
            start_ = std::chrono::high_resolution_clock::now();
        }

        ~ScopedTimer() {
            auto end = std::chrono::high_resolution_clock::now();
            auto duration = std::chrono::duration<double, std::milli>(end - start_);
            profiler_.record(name_, duration.count());
        }

    private:
        Profiler& profiler_;
        std::string name_;
        std::chrono::high_resolution_clock::time_point start_;
    };

    void record(const std::string& name, double duration_ms) {
        auto& stats = stats_[name];
        stats.call_count++;
        stats.total_ms += duration_ms;
        stats.min_ms = std::min(stats.min_ms, duration_ms);
        stats.max_ms = std::max(stats.max_ms, duration_ms);
    }

    void print_report() const {
        std::cout << "\n=== Profiling Report ===\n\n";
        std::cout << std::left << std::setw(30) << "Function"
                  << std::right << std::setw(12) << "Calls"
                  << std::setw(15) << "Total (ms)"
                  << std::setw(15) << "Avg (ms)"
                  << std::setw(15) << "Min (ms)"
                  << std::setw(15) << "Max (ms)" << "\n";
        std::cout << std::string(102, '-') << "\n";

        for (const auto& [name, stats] : stats_) {
            double avg_ms = stats.total_ms / stats.call_count;
            std::cout << std::left << std::setw(30) << name
                      << std::right << std::setw(12) << stats.call_count
                      << std::setw(15) << std::fixed << std::setprecision(3) << stats.total_ms
                      << std::setw(15) << std::fixed << std::setprecision(6) << avg_ms
                      << std::setw(15) << std::fixed << std::setprecision(6) << stats.min_ms
                      << std::setw(15) << std::fixed << std::setprecision(6) << stats.max_ms << "\n";
        }
        std::cout << "\n";
    }

    void reset() {
        stats_.clear();
    }

private:
    std::unordered_map<std::string, Stats> stats_;
};

// Global profiler instance
inline Profiler& get_profiler() {
    static Profiler profiler;
    return profiler;
}

// Macro for easy profiling
#define PROFILE_SCOPE(name) \
    Profiler::ScopedTimer timer##__LINE__(get_profiler(), name)

#define PROFILE_FUNCTION() \
    PROFILE_SCOPE(__FUNCTION__)

#endif /* PROFILER_HPP */
```

## Phase 5: Load Testing

### Load Test Implementation

```cpp
/**
 * load_test.cpp
 *
 * Multithreaded load testing framework.
 */
#include <iostream>
#include <vector>
#include <thread>
#include <atomic>
#include <chrono>
#include <algorithm>
#include <numeric>
#include <functional>

class LoadTest {
public:
    using TestFunction = std::function<bool()>;

    struct Result {
        std::atomic<uint64_t> success_count{0};
        std::atomic<uint64_t> failure_count{0};
        std::vector<double> latencies;
        std::chrono::duration<double> duration;
    };

    LoadTest(TestFunction fn, int num_threads, int iterations_per_thread)
        : fn_(fn), num_threads_(num_threads),
          iterations_per_thread_(iterations_per_thread) {}

    Result run() {
        Result result;
        std::vector<std::thread> threads;
        std::vector<std::vector<double>> thread_latencies(num_threads_);

        auto start = std::chrono::high_resolution_clock::now();

        // Launch threads
        for (int i = 0; i < num_threads_; ++i) {
            threads.emplace_back([this, &result, &thread_latencies, i]() {
                for (int j = 0; j < iterations_per_thread_; ++j) {
                    auto op_start = std::chrono::high_resolution_clock::now();

                    bool success = fn_();

                    auto op_end = std::chrono::high_resolution_clock::now();
                    auto duration = std::chrono::duration<double, std::milli>(op_end - op_start);

                    if (success) {
                        result.success_count.fetch_add(1, std::memory_order_relaxed);
                        thread_latencies[i].push_back(duration.count());
                    } else {
                        result.failure_count.fetch_add(1, std::memory_order_relaxed);
                    }
                }
            });
        }

        // Wait for completion
        for (auto& thread : threads) {
            thread.join();
        }

        auto end = std::chrono::high_resolution_clock::now();
        result.duration = end - start;

        // Merge latencies
        for (const auto& tl : thread_latencies) {
            result.latencies.insert(result.latencies.end(), tl.begin(), tl.end());
        }

        return result;
    }

    void print_result(const Result& result) const {
        uint64_t total_ops = result.success_count + result.failure_count;
        double duration_sec = result.duration.count();

        // Calculate percentiles
        auto latencies = result.latencies;
        std::sort(latencies.begin(), latencies.end());

        auto percentile = [&](int p) -> double {
            if (latencies.empty()) return 0.0;
            size_t idx = (latencies.size() * p) / 100;
            return latencies[std::min(idx, latencies.size() - 1)];
        };

        double avg = std::accumulate(latencies.begin(), latencies.end(), 0.0) / latencies.size();

        std::cout << "\n=== Load Test Results ===\n";
        std::cout << "Threads:           " << num_threads_ << "\n";
        std::cout << "Iterations/thread: " << iterations_per_thread_ << "\n";
        std::cout << "Total Operations:  " << total_ops << "\n";
        std::cout << "Success:           " << result.success_count << "\n";
        std::cout << "Failures:          " << result.failure_count << "\n";
        std::cout << "Success Rate:      " << (100.0 * result.success_count / total_ops) << "%\n";
        std::cout << "Duration:          " << duration_sec << " seconds\n";
        std::cout << "Throughput:        " << (total_ops / duration_sec) << " ops/sec\n";
        std::cout << "\nLatency:\n";
        std::cout << "  Average:         " << avg << " ms\n";
        std::cout << "  P50:             " << percentile(50) << " ms\n";
        std::cout << "  P95:             " << percentile(95) << " ms\n";
        std::cout << "  P99:             " << percentile(99) << " ms\n";
        std::cout << "\n";
    }

private:
    TestFunction fn_;
    int num_threads_;
    int iterations_per_thread_;
};

// Example usage
bool example_operation() {
    // Simulate work
    volatile int sum = 0;
    for (int i = 0; i < 10000; ++i) {
        sum += i;
    }
    return true; // Success
}

int main() {
    LoadTest test(example_operation, 10, 1000);
    auto result = test.run();
    test.print_result(result);

    return 0;
}
```

## Phase 6: Stress Testing

### Stress Test Implementation

```cpp
/**
 * stress_test.cpp
 *
 * Stress testing to find breaking points.
 */
#include <iostream>
#include <vector>
#include <thread>
#include <atomic>
#include <chrono>

class StressTest {
public:
    static void test_memory_allocation() {
        std::cout << "=== Memory Allocation Stress Test ===\n";

        const size_t allocation_size = 1024 * 10; // 10KB
        const size_t num_allocations = 10000;

        std::vector<std::vector<uint8_t>> allocations;
        allocations.reserve(num_allocations);

        auto start = std::chrono::high_resolution_clock::now();

        try {
            for (size_t i = 0; i < num_allocations; ++i) {
                allocations.emplace_back(allocation_size, static_cast<uint8_t>(i % 256));
            }
        } catch (const std::bad_alloc& e) {
            std::cerr << "Memory allocation failed: " << e.what() << "\n";
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration<double>(end - start);

        size_t total_mb = (allocations.size() * allocation_size) / (1024 * 1024);

        std::cout << "Allocated:         " << allocations.size() << " blocks\n";
        std::cout << "Total Memory:      " << total_mb << " MB\n";
        std::cout << "Duration:          " << duration.count() << " seconds\n";
        std::cout << "\n";
    }

    static void test_thread_creation() {
        std::cout << "=== Thread Creation Stress Test ===\n";

        const int max_threads = 1000;
        std::atomic<int> completed{0};

        auto start = std::chrono::high_resolution_clock::now();

        std::vector<std::thread> threads;
        threads.reserve(max_threads);

        try {
            for (int i = 0; i < max_threads; ++i) {
                threads.emplace_back([&completed]() {
                    std::this_thread::sleep_for(std::chrono::milliseconds(10));
                    completed.fetch_add(1, std::memory_order_relaxed);
                });
            }

            for (auto& thread : threads) {
                thread.join();
            }
        } catch (const std::exception& e) {
            std::cerr << "Thread creation failed: " << e.what() << "\n";
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration<double>(end - start);

        std::cout << "Threads Created:   " << threads.size() << "\n";
        std::cout << "Threads Completed: " << completed.load() << "\n";
        std::cout << "Duration:          " << duration.count() << " seconds\n";
        std::cout << "\n";
    }

    static void test_sustained_load() {
        std::cout << "=== Sustained Load Test ===\n";

        const int duration_seconds = 60;
        const int operations_per_second = 1000;

        std::atomic<uint64_t> total_ops{0};
        std::atomic<bool> running{true};

        auto start = std::chrono::high_resolution_clock::now();

        std::thread worker([&]() {
            while (running.load(std::memory_order_relaxed)) {
                for (int i = 0; i < operations_per_second; ++i) {
                    // Perform operation
                    volatile int sum = 0;
                    for (int j = 0; j < 1000; ++j) {
                        sum += j;
                    }
                    total_ops.fetch_add(1, std::memory_order_relaxed);
                }
                std::this_thread::sleep_for(std::chrono::seconds(1));
            }
        });

        std::this_thread::sleep_for(std::chrono::seconds(duration_seconds));
        running.store(false, std::memory_order_relaxed);
        worker.join();

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration<double>(end - start);

        std::cout << "Duration:          " << duration.count() << " seconds\n";
        std::cout << "Total Operations:  " << total_ops.load() << "\n";
        std::cout << "Ops/sec:           " << (total_ops.load() / duration.count()) << "\n";
        std::cout << "\n";
    }
};

int main() {
    StressTest::test_memory_allocation();
    StressTest::test_thread_creation();
    StressTest::test_sustained_load();

    return 0;
}
```

## Phase 7: Performance Regression Detection

### Baseline Management

```cpp
/**
 * regression_test.hpp
 *
 * Performance regression detection system.
 */
#ifndef REGRESSION_TEST_HPP
#define REGRESSION_TEST_HPP

#include <string>
#include <unordered_map>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <ctime>
#include "json.hpp" // nlohmann/json

using json = nlohmann::json;

class RegressionDetector {
public:
    struct BenchmarkResult {
        std::string name;
        double avg_ms;
        time_t timestamp;

        json to_json() const {
            return json{
                {"name", name},
                {"avg_ms", avg_ms},
                {"timestamp", timestamp}
            };
        }

        static BenchmarkResult from_json(const json& j) {
            return BenchmarkResult{
                j["name"].get<std::string>(),
                j["avg_ms"].get<double>(),
                j["timestamp"].get<time_t>()
            };
        }
    };

    bool load(const std::string& filename) {
        std::ifstream file(filename);
        if (!file.is_open()) {
            return false;
        }

        json j;
        file >> j;

        baselines_.clear();
        for (const auto& item : j["baselines"]) {
            auto result = BenchmarkResult::from_json(item);
            baselines_[result.name] = result;
        }

        return true;
    }

    bool save(const std::string& filename) const {
        json j;
        j["baselines"] = json::array();

        for (const auto& [name, result] : baselines_) {
            j["baselines"].push_back(result.to_json());
        }

        std::ofstream file(filename);
        if (!file.is_open()) {
            return false;
        }

        file << std::setw(2) << j;
        return true;
    }

    bool check_regression(const std::string& name, double current_ms,
                         double threshold_percent = 10.0) {
        auto it = baselines_.find(name);

        if (it == baselines_.end()) {
            // No baseline exists, create new one
            BenchmarkResult result{name, current_ms, std::time(nullptr)};
            baselines_[name] = result;
            std::cout << "Created baseline for " << name << ": "
                      << current_ms << " ms\n";
            return false;
        }

        double baseline_ms = it->second.avg_ms;
        double percent_change = ((current_ms - baseline_ms) / baseline_ms) * 100.0;

        std::cout << "\nRegression Check: " << name << "\n";
        std::cout << "  Baseline:  " << std::fixed << std::setprecision(6)
                  << baseline_ms << " ms\n";
        std::cout << "  Current:   " << current_ms << " ms\n";
        std::cout << "  Change:    " << std::showpos << percent_change
                  << std::noshowpos << "%\n";

        if (percent_change > threshold_percent) {
            std::cout << "  ❌ REGRESSION DETECTED!\n\n";
            return true;
        } else if (percent_change < -threshold_percent) {
            std::cout << "  ✅ IMPROVEMENT!\n\n";
            // Update baseline with improvement
            it->second.avg_ms = current_ms;
            it->second.timestamp = std::time(nullptr);
            return false;
        } else {
            std::cout << "  ✅ No significant change\n\n";
            return false;
        }
    }

private:
    std::unordered_map<std::string, BenchmarkResult> baselines_;
};

#endif /* REGRESSION_TEST_HPP */
```

## Phase 8: CI/CD Integration

### CMake Configuration

```cmake
# CMakeLists.txt

# Performance testing option
option(BUILD_PERFORMANCE_TESTS "Build performance tests" ON)

if(BUILD_PERFORMANCE_TESTS)
    # Google Benchmark
    FetchContent_Declare(
        benchmark
        GIT_REPOSITORY https://github.com/google/benchmark.git
        GIT_TAG v1.8.3
    )
    FetchContent_MakeAvailable(benchmark)

    # JSON library for regression detection
    FetchContent_Declare(
        json
        GIT_REPOSITORY https://github.com/nlohmann/json.git
        GIT_TAG v3.11.2
    )
    FetchContent_MakeAvailable(json)

    # Performance test executables
    add_executable(benchmarks
        benchmarks/string_benchmarks.cpp
        benchmarks/container_benchmarks.cpp
    )
    target_link_libraries(benchmarks PRIVATE benchmark::benchmark)

    add_executable(load_test load_test.cpp)
    target_link_libraries(load_test PRIVATE pthread)

    add_executable(stress_test stress_test.cpp)
    target_link_libraries(stress_test PRIVATE pthread)

    add_executable(regression_test regression_test.cpp)
    target_link_libraries(regression_test PRIVATE nlohmann_json::nlohmann_json)

    # Enable optimizations
    if(CMAKE_BUILD_TYPE STREQUAL "Release")
        target_compile_options(benchmarks PRIVATE -O3 -march=native)
    endif()
endif()
```

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

    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y cmake build-essential valgrind linux-tools-common linux-tools-generic

    - name: Configure CMake
      run: |
        mkdir build
        cd build
        cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_PERFORMANCE_TESTS=ON ..

    - name: Build
      run: cmake --build build --config Release

    - name: Run benchmarks
      run: |
        cd build
        ./benchmarks --benchmark_format=json --benchmark_out=benchmark_results.json
        ./benchmarks --benchmark_format=console > benchmark_results.txt

    - name: Run load tests
      run: ./build/load_test > load_test_results.txt

    - name: Run stress tests
      run: ./build/stress_test > stress_test_results.txt

    - name: Check for regressions
      run: ./build/regression_test

    - name: Run Valgrind
      run: |
        valgrind --leak-check=full --show-leak-kinds=all --log-file=valgrind.txt ./build/benchmarks --benchmark_filter=BM_StringAppend
        cat valgrind.txt

    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: |
          build/benchmark_results.json
          build/benchmark_results.txt
          load_test_results.txt
          stress_test_results.txt
          valgrind.txt

    - name: Comment PR
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const results = fs.readFileSync('build/benchmark_results.txt', 'utf8');
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
| String operations | <1ms | [value] | ✅/❌ |
| Container ops | 100K/sec | [value] | ✅/❌ |
| Memory usage | <512MB | [value] | ✅/❌ |
| Memory leaks | 0 | [value] | ✅/❌ |

### Benchmark Results
```
Benchmark                    Time          CPU    Iterations
--------------------------------------------------------------
BM_StringAppend/8         0.345 us     0.345 us    2000000
BM_StringAppend/64        2.123 us     2.123 us     330000
BM_VectorPushBack/1024   45.234 us    45.234 us      15000
```

### Load Test Results
```
Threads:           10
Iterations/thread: 1000
Total Operations:  10000
Success:           9950
Failures:          50
Success Rate:      99.50%
Duration:          12.34 seconds
Throughput:        810.37 ops/sec
Latency:
  Average:         1.234 ms
  P50:             1.150 ms
  P95:             2.340 ms
  P99:             3.456 ms
```

### Bottlenecks Identified
1. **String Concatenation with operator+**
   - **Issue**: Repeated reallocation and copying
   - **Impact**: O(n²) complexity for n concatenations
   - **Recommendation**: Use std::string::reserve() or std::string::append()

2. **Vector Insertions Without Reserve**
   - **Issue**: Multiple reallocations as vector grows
   - **Impact**: 40% slower than pre-reserved vector
   - **Recommendation**: Call reserve() when final size is known

### Performance Improvement Recommendations
- [ ] Replace operator+ with std::string::append() for string building
- [ ] Use std::vector::reserve() when final size is predictable
- [ ] Consider std::move() for large object transfers
- [ ] Use const& for function parameters to avoid copies
- [ ] Enable link-time optimization (-flto) in Release builds

### Test Execution
```bash
# Build and run
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
make
./benchmarks

# Run with profiling
perf record -g ./benchmarks
perf report

# Memory check
valgrind --leak-check=full ./benchmarks
```

### Next Steps
- [ ] Establish performance baselines for all critical operations
- [ ] Integrate performance tests into CI/CD pipeline
- [ ] Set up continuous profiling with perf or VTune
- [ ] Create performance dashboard with historical trends
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

1. **Performance test suite** with Google Benchmark tests
2. **Performance baselines** documented
3. **Load test scenarios** for critical operations
4. **Profiling results** with bottleneck identification
5. **Regression detection** configuration
6. **CI/CD integration** for automated performance gates
7. **Performance report** with metrics and recommendations
