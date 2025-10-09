# C Performance Testing

## Objective
Implement comprehensive performance testing to validate system behavior under load, identify bottlenecks, measure response times, profile resource usage, detect performance regressions, and ensure scalability requirements are met using C tooling.

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
- Create `tests/` directory in repository root if it doesn't exist
- Create `tests/performance_testing/` subdirectory for this testing phase
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
- [ ] Baseline benchmarks established
- [ ] Performance regression tests configured
- [ ] Resource profiling set up

### Metrics and Monitoring
- [ ] Execution time thresholds defined
- [ ] Throughput targets established
- [ ] Resource usage limits set (memory, CPU)
- [ ] Memory leak detection configured
- [ ] Performance reports automated

### Test Infrastructure
- [ ] Timing infrastructure implemented
- [ ] Memory profiling tools configured
- [ ] Performance test data prepared
- [ ] CI/CD integration planned
- [ ] Results storage and trending implemented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C Performance Testing Implementation

Please implement comprehensive performance testing for this C project following this protocol:

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
| Buffer processing | 10,000 | 50,000 |
| Hash calculations | 1,000 | 5,000 |

**Resource Limits**:
- **Memory**: <512MB heap allocation
- **CPU**: <80% average, <95% peak
- **File handles**: <100 open files
- **Thread count**: <50 threads

## Phase 2: Timing Infrastructure

### High-Resolution Timer Implementation

```c
/**
 * performance_timer.h
 *
 * High-resolution timing utilities for performance measurement.
 */
#ifndef PERFORMANCE_TIMER_H
#define PERFORMANCE_TIMER_H

#include <stdint.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <sys/time.h>
#endif

typedef struct {
    uint64_t start;
    uint64_t end;
    double elapsed_ms;
} perf_timer_t;

/**
 * Get current timestamp in nanoseconds.
 */
static inline uint64_t perf_get_time_ns(void) {
#ifdef _WIN32
    LARGE_INTEGER frequency;
    LARGE_INTEGER counter;
    QueryPerformanceFrequency(&frequency);
    QueryPerformanceCounter(&counter);
    return (uint64_t)(counter.QuadPart * 1000000000ULL / frequency.QuadPart);
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
#endif
}

/**
 * Start performance timer.
 */
static inline void perf_timer_start(perf_timer_t *timer) {
    timer->start = perf_get_time_ns();
}

/**
 * Stop performance timer and calculate elapsed time.
 */
static inline void perf_timer_stop(perf_timer_t *timer) {
    timer->end = perf_get_time_ns();
    timer->elapsed_ms = (double)(timer->end - timer->start) / 1000000.0;
}

/**
 * Get elapsed time in milliseconds.
 */
static inline double perf_timer_elapsed_ms(const perf_timer_t *timer) {
    return timer->elapsed_ms;
}

/**
 * Get elapsed time in microseconds.
 */
static inline double perf_timer_elapsed_us(const perf_timer_t *timer) {
    return timer->elapsed_ms * 1000.0;
}

#endif /* PERFORMANCE_TIMER_H */
```

### Benchmark Framework

```c
/**
 * benchmark.h
 *
 * Simple benchmarking framework for C.
 */
#ifndef BENCHMARK_H
#define BENCHMARK_H

#include "performance_timer.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BENCHMARK_ITERATIONS 10000
#define BENCHMARK_WARMUP 100

typedef void (*benchmark_fn)(void *context);

typedef struct {
    const char *name;
    benchmark_fn fn;
    void *context;
    double min_ms;
    double max_ms;
    double avg_ms;
    double total_ms;
    int iterations;
} benchmark_result_t;

/**
 * Run a benchmark function.
 */
static inline benchmark_result_t benchmark_run(
    const char *name,
    benchmark_fn fn,
    void *context,
    int iterations
) {
    benchmark_result_t result = {0};
    result.name = name;
    result.fn = fn;
    result.context = context;
    result.iterations = iterations;
    result.min_ms = 1e9;
    result.max_ms = 0.0;

    perf_timer_t timer;

    // Warmup
    for (int i = 0; i < BENCHMARK_WARMUP; i++) {
        fn(context);
    }

    // Actual benchmark
    for (int i = 0; i < iterations; i++) {
        perf_timer_start(&timer);
        fn(context);
        perf_timer_stop(&timer);

        double elapsed = perf_timer_elapsed_ms(&timer);
        result.total_ms += elapsed;

        if (elapsed < result.min_ms) result.min_ms = elapsed;
        if (elapsed > result.max_ms) result.max_ms = elapsed;
    }

    result.avg_ms = result.total_ms / iterations;

    return result;
}

/**
 * Print benchmark results.
 */
static inline void benchmark_print_result(const benchmark_result_t *result) {
    printf("Benchmark: %s\n", result->name);
    printf("  Iterations: %d\n", result->iterations);
    printf("  Total:      %.3f ms\n", result->total_ms);
    printf("  Average:    %.6f ms\n", result->avg_ms);
    printf("  Min:        %.6f ms\n", result->min_ms);
    printf("  Max:        %.6f ms\n", result->max_ms);
    printf("  Ops/sec:    %.2f\n", 1000.0 / result->avg_ms);
    printf("\n");
}

/**
 * Macro to define and run a benchmark.
 */
#define BENCHMARK(name, iterations) \
    void benchmark_##name(void *context); \
    void run_benchmark_##name(void) { \
        benchmark_result_t result = benchmark_run( \
            #name, \
            benchmark_##name, \
            NULL, \
            iterations \
        ); \
        benchmark_print_result(&result); \
    } \
    void benchmark_##name(void *context)

#endif /* BENCHMARK_H */
```

### Example Benchmarks

```c
/**
 * example_benchmarks.c
 *
 * Example performance benchmarks.
 */
#include "benchmark.h"
#include <string.h>
#include <stdlib.h>

/* Benchmark: String copying with strcpy */
BENCHMARK(string_copy_strcpy, 10000) {
    char src[1000] = "This is a test string for benchmarking";
    char dst[1000];
    strcpy(dst, src);
}

/* Benchmark: String copying with memcpy */
BENCHMARK(string_copy_memcpy, 10000) {
    char src[1000] = "This is a test string for benchmarking";
    char dst[1000];
    memcpy(dst, src, strlen(src) + 1);
}

/* Benchmark: Memory allocation */
BENCHMARK(memory_allocation, 10000) {
    void *ptr = malloc(1024);
    if (ptr) {
        free(ptr);
    }
}

/* Benchmark: Array iteration */
BENCHMARK(array_iteration, 10000) {
    int arr[1000];
    for (int i = 0; i < 1000; i++) {
        arr[i] = i * 2;
    }
}

/* Benchmark: Pointer arithmetic */
BENCHMARK(pointer_arithmetic, 10000) {
    int arr[1000];
    int *ptr = arr;
    for (int i = 0; i < 1000; i++) {
        *ptr++ = i * 2;
    }
}

int main(void) {
    printf("=== Performance Benchmarks ===\n\n");

    run_benchmark_string_copy_strcpy();
    run_benchmark_string_copy_memcpy();
    run_benchmark_memory_allocation();
    run_benchmark_array_iteration();
    run_benchmark_pointer_arithmetic();

    return 0;
}
```

## Phase 3: Memory Profiling

### Memory Tracking Implementation

```c
/**
 * memory_profiler.h
 *
 * Memory allocation tracking and leak detection.
 */
#ifndef MEMORY_PROFILER_H
#define MEMORY_PROFILER_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef ENABLE_MEMORY_PROFILING

typedef struct {
    size_t total_allocated;
    size_t total_freed;
    size_t current_usage;
    size_t peak_usage;
    size_t allocation_count;
    size_t free_count;
} memory_stats_t;

static memory_stats_t g_memory_stats = {0};

/**
 * Tracked malloc wrapper.
 */
static inline void* tracked_malloc(size_t size, const char *file, int line) {
    void *ptr = malloc(size);
    if (ptr) {
        g_memory_stats.total_allocated += size;
        g_memory_stats.current_usage += size;
        g_memory_stats.allocation_count++;

        if (g_memory_stats.current_usage > g_memory_stats.peak_usage) {
            g_memory_stats.peak_usage = g_memory_stats.current_usage;
        }

        #ifdef VERBOSE_MEMORY_TRACKING
        printf("[ALLOC] %p: %zu bytes at %s:%d\n", ptr, size, file, line);
        #endif
    }
    return ptr;
}

/**
 * Tracked free wrapper.
 */
static inline void tracked_free(void *ptr, size_t size, const char *file, int line) {
    if (ptr) {
        g_memory_stats.total_freed += size;
        g_memory_stats.current_usage -= size;
        g_memory_stats.free_count++;

        #ifdef VERBOSE_MEMORY_TRACKING
        printf("[FREE]  %p: %zu bytes at %s:%d\n", ptr, size, file, line);
        #endif

        free(ptr);
    }
}

/**
 * Print memory statistics.
 */
static inline void print_memory_stats(void) {
    printf("\n=== Memory Statistics ===\n");
    printf("Total Allocated:   %zu bytes (%.2f MB)\n",
           g_memory_stats.total_allocated,
           g_memory_stats.total_allocated / (1024.0 * 1024.0));
    printf("Total Freed:       %zu bytes (%.2f MB)\n",
           g_memory_stats.total_freed,
           g_memory_stats.total_freed / (1024.0 * 1024.0));
    printf("Current Usage:     %zu bytes (%.2f MB)\n",
           g_memory_stats.current_usage,
           g_memory_stats.current_usage / (1024.0 * 1024.0));
    printf("Peak Usage:        %zu bytes (%.2f MB)\n",
           g_memory_stats.peak_usage,
           g_memory_stats.peak_usage / (1024.0 * 1024.0));
    printf("Allocations:       %zu\n", g_memory_stats.allocation_count);
    printf("Frees:             %zu\n", g_memory_stats.free_count);
    printf("Potential Leaks:   %zu\n",
           g_memory_stats.allocation_count - g_memory_stats.free_count);
    printf("\n");
}

/**
 * Reset memory statistics.
 */
static inline void reset_memory_stats(void) {
    memset(&g_memory_stats, 0, sizeof(memory_stats_t));
}

#define malloc(size) tracked_malloc(size, __FILE__, __LINE__)
#define free(ptr) tracked_free(ptr, 0, __FILE__, __LINE__)

#else

static inline void print_memory_stats(void) {}
static inline void reset_memory_stats(void) {}

#endif /* ENABLE_MEMORY_PROFILING */

#endif /* MEMORY_PROFILER_H */
```

### Using Valgrind for Memory Profiling

```bash
# Install Valgrind (Linux)
sudo apt-get install valgrind

# Memory leak detection
valgrind --leak-check=full \
         --show-leak-kinds=all \
         --track-origins=yes \
         --verbose \
         --log-file=valgrind-memory.txt \
         ./your_program

# Memory profiling with massif
valgrind --tool=massif \
         --massif-out-file=massif.out \
         ./your_program

# Visualize massif output
ms_print massif.out

# Cache profiling
valgrind --tool=cachegrind \
         --cachegrind-out-file=cachegrind.out \
         ./your_program

# Analyze cachegrind output
cg_annotate cachegrind.out
```

## Phase 4: CPU Profiling

### Using gprof

```c
/**
 * Compile with profiling enabled:
 * gcc -pg -o program program.c
 *
 * Run program to generate gmon.out
 * ./program
 *
 * Analyze profile:
 * gprof program gmon.out > analysis.txt
 */

#include <stdio.h>
#include <stdlib.h>

void expensive_function(int iterations) {
    volatile int sum = 0;
    for (int i = 0; i < iterations; i++) {
        sum += i * i;
    }
}

void another_function(void) {
    for (int i = 0; i < 1000; i++) {
        expensive_function(10000);
    }
}

int main(void) {
    printf("Starting profiling test...\n");

    for (int i = 0; i < 100; i++) {
        another_function();
    }

    printf("Profiling complete. Run 'gprof program gmon.out' to see results.\n");
    return 0;
}
```

### Using perf (Linux)

```bash
# Compile with debug symbols
gcc -g -O2 -o program program.c

# Record performance data
perf record -g ./program

# View performance report
perf report

# Record with call graphs
perf record -g --call-graph dwarf ./program

# Generate flamegraph
perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg

# CPU cache analysis
perf stat -e cache-references,cache-misses,cycles,instructions ./program

# Record specific events
perf record -e cpu-cycles,cache-misses ./program
```

## Phase 5: Load Testing

### Load Test Implementation

```c
/**
 * load_test.c
 *
 * Load testing framework for C functions.
 */
#include "performance_timer.h"
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <stdatomic.h>

#define MAX_THREADS 100

typedef void* (*load_test_fn)(void *arg);

typedef struct {
    int thread_id;
    int iterations;
    load_test_fn fn;
    void *context;
} thread_context_t;

typedef struct {
    atomic_int success_count;
    atomic_int failure_count;
    double *latencies;
    int latency_count;
    int total_threads;
} load_test_result_t;

static load_test_result_t g_result = {0};
static pthread_mutex_t latency_mutex = PTHREAD_MUTEX_INITIALIZER;

void* load_test_thread(void *arg) {
    thread_context_t *ctx = (thread_context_t*)arg;
    perf_timer_t timer;

    for (int i = 0; i < ctx->iterations; i++) {
        perf_timer_start(&timer);

        // Call test function
        void *result = ctx->fn(ctx->context);

        perf_timer_stop(&timer);

        if (result != NULL) {
            atomic_fetch_add(&g_result.success_count, 1);

            // Store latency
            pthread_mutex_lock(&latency_mutex);
            if (g_result.latency_count < 100000) {
                g_result.latencies[g_result.latency_count++] = perf_timer_elapsed_ms(&timer);
            }
            pthread_mutex_unlock(&latency_mutex);
        } else {
            atomic_fetch_add(&g_result.failure_count, 1);
        }
    }

    return NULL;
}

int compare_double(const void *a, const void *b) {
    double da = *(const double*)a;
    double db = *(const double*)b;
    return (da > db) - (da < db);
}

void run_load_test(load_test_fn fn, void *context, int num_threads, int iterations_per_thread) {
    pthread_t threads[MAX_THREADS];
    thread_context_t contexts[MAX_THREADS];

    // Initialize result
    atomic_init(&g_result.success_count, 0);
    atomic_init(&g_result.failure_count, 0);
    g_result.latencies = malloc(100000 * sizeof(double));
    g_result.latency_count = 0;
    g_result.total_threads = num_threads;

    printf("Starting load test with %d threads, %d iterations each...\n",
           num_threads, iterations_per_thread);

    perf_timer_t total_timer;
    perf_timer_start(&total_timer);

    // Create threads
    for (int i = 0; i < num_threads; i++) {
        contexts[i].thread_id = i;
        contexts[i].iterations = iterations_per_thread;
        contexts[i].fn = fn;
        contexts[i].context = context;

        pthread_create(&threads[i], NULL, load_test_thread, &contexts[i]);
    }

    // Wait for completion
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }

    perf_timer_stop(&total_timer);

    // Calculate statistics
    int total_ops = atomic_load(&g_result.success_count) +
                    atomic_load(&g_result.failure_count);

    qsort(g_result.latencies, g_result.latency_count,
          sizeof(double), compare_double);

    double p50 = g_result.latencies[g_result.latency_count * 50 / 100];
    double p95 = g_result.latencies[g_result.latency_count * 95 / 100];
    double p99 = g_result.latencies[g_result.latency_count * 99 / 100];

    double total_latency = 0;
    for (int i = 0; i < g_result.latency_count; i++) {
        total_latency += g_result.latencies[i];
    }
    double avg_latency = total_latency / g_result.latency_count;

    double throughput = total_ops / (perf_timer_elapsed_ms(&total_timer) / 1000.0);

    // Print results
    printf("\n=== Load Test Results ===\n");
    printf("Total Operations:  %d\n", total_ops);
    printf("Success:           %d\n", atomic_load(&g_result.success_count));
    printf("Failures:          %d\n", atomic_load(&g_result.failure_count));
    printf("Success Rate:      %.2f%%\n",
           100.0 * atomic_load(&g_result.success_count) / total_ops);
    printf("Duration:          %.2f seconds\n",
           perf_timer_elapsed_ms(&total_timer) / 1000.0);
    printf("Throughput:        %.2f ops/sec\n", throughput);
    printf("\nLatency:\n");
    printf("  Average:         %.3f ms\n", avg_latency);
    printf("  P50:             %.3f ms\n", p50);
    printf("  P95:             %.3f ms\n", p95);
    printf("  P99:             %.3f ms\n", p99);
    printf("\n");

    free(g_result.latencies);
}

/* Example test function */
void* example_operation(void *context) {
    // Simulate work
    volatile int sum = 0;
    for (int i = 0; i < 10000; i++) {
        sum += i;
    }
    return (void*)1; // Success
}

int main(void) {
    run_load_test(example_operation, NULL, 10, 1000);
    return 0;
}
```

## Phase 6: Stress Testing

### Stress Test Implementation

```c
/**
 * stress_test.c
 *
 * Stress testing to find breaking points.
 */
#include "memory_profiler.h"
#include "performance_timer.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/**
 * Test memory allocation stress.
 */
void test_memory_stress(void) {
    printf("=== Memory Stress Test ===\n");

    reset_memory_stats();

    void **ptrs = malloc(10000 * sizeof(void*));
    if (!ptrs) {
        printf("Failed to allocate pointer array\n");
        return;
    }

    // Allocate many blocks
    for (int i = 0; i < 10000; i++) {
        ptrs[i] = malloc(1024 * 10); // 10KB each
        if (ptrs[i]) {
            memset(ptrs[i], i % 256, 1024 * 10);
        }
    }

    print_memory_stats();

    // Free all blocks
    for (int i = 0; i < 10000; i++) {
        free(ptrs[i]);
    }

    free(ptrs);

    print_memory_stats();
}

/**
 * Test sustained operation stress.
 */
void test_sustained_operations(void) {
    printf("=== Sustained Operations Test ===\n");

    const int duration_seconds = 60;
    const int operations_per_second = 1000;

    perf_timer_t total_timer, op_timer;
    perf_timer_start(&total_timer);

    int total_operations = 0;
    int failed_operations = 0;

    while (perf_timer_elapsed_ms(&total_timer) / 1000.0 < duration_seconds) {
        for (int i = 0; i < operations_per_second; i++) {
            perf_timer_start(&op_timer);

            // Perform operation
            void *ptr = malloc(1024);
            if (ptr) {
                memset(ptr, 0, 1024);
                free(ptr);
                total_operations++;
            } else {
                failed_operations++;
            }

            perf_timer_stop(&op_timer);

            // Maintain target rate
            double target_delay_ms = 1000.0 / operations_per_second;
            double actual_time_ms = perf_timer_elapsed_ms(&op_timer);
            if (actual_time_ms < target_delay_ms) {
                // Sleep for remaining time (simplified)
            }
        }
    }

    perf_timer_stop(&total_timer);

    printf("Duration:          %.2f seconds\n",
           perf_timer_elapsed_ms(&total_timer) / 1000.0);
    printf("Total Operations:  %d\n", total_operations);
    printf("Failed Operations: %d\n", failed_operations);
    printf("Success Rate:      %.2f%%\n",
           100.0 * total_operations / (total_operations + failed_operations));
    printf("\n");
}

int main(void) {
    test_memory_stress();
    test_sustained_operations();

    return 0;
}
```

## Phase 7: Performance Regression Detection

### Baseline Management

```c
/**
 * regression_test.h
 *
 * Performance regression detection.
 */
#ifndef REGRESSION_TEST_H
#define REGRESSION_TEST_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_BASELINES 100
#define REGRESSION_THRESHOLD 10.0 // 10% threshold

typedef struct {
    char name[256];
    double avg_ms;
    time_t timestamp;
} baseline_entry_t;

typedef struct {
    baseline_entry_t entries[MAX_BASELINES];
    int count;
} baseline_db_t;

/**
 * Load baseline database from file.
 */
int load_baseline(const char *filename, baseline_db_t *db) {
    FILE *f = fopen(filename, "r");
    if (!f) {
        db->count = 0;
        return 0;
    }

    db->count = 0;
    while (db->count < MAX_BASELINES &&
           fscanf(f, "%255s %lf %ld\n",
                  db->entries[db->count].name,
                  &db->entries[db->count].avg_ms,
                  &db->entries[db->count].timestamp) == 3) {
        db->count++;
    }

    fclose(f);
    return db->count;
}

/**
 * Save baseline database to file.
 */
int save_baseline(const char *filename, const baseline_db_t *db) {
    FILE *f = fopen(filename, "w");
    if (!f) {
        return -1;
    }

    for (int i = 0; i < db->count; i++) {
        fprintf(f, "%s %.6f %ld\n",
                db->entries[i].name,
                db->entries[i].avg_ms,
                db->entries[i].timestamp);
    }

    fclose(f);
    return 0;
}

/**
 * Compare current result with baseline.
 */
int check_regression(baseline_db_t *db, const char *name, double current_ms) {
    // Find existing baseline
    int idx = -1;
    for (int i = 0; i < db->count; i++) {
        if (strcmp(db->entries[i].name, name) == 0) {
            idx = i;
            break;
        }
    }

    if (idx == -1) {
        // No baseline exists, create new one
        if (db->count < MAX_BASELINES) {
            strncpy(db->entries[db->count].name, name, 255);
            db->entries[db->count].avg_ms = current_ms;
            db->entries[db->count].timestamp = time(NULL);
            db->count++;

            printf("Created baseline for %s: %.6f ms\n", name, current_ms);
            return 0;
        }
        return -1;
    }

    // Compare with baseline
    double baseline_ms = db->entries[idx].avg_ms;
    double percent_change = ((current_ms - baseline_ms) / baseline_ms) * 100.0;

    printf("\nRegression Check: %s\n", name);
    printf("  Baseline:  %.6f ms\n", baseline_ms);
    printf("  Current:   %.6f ms\n", current_ms);
    printf("  Change:    %+.2f%%\n", percent_change);

    if (percent_change > REGRESSION_THRESHOLD) {
        printf("  ❌ REGRESSION DETECTED!\n\n");
        return 1;
    } else if (percent_change < -REGRESSION_THRESHOLD) {
        printf("  ✅ IMPROVEMENT!\n\n");
        // Update baseline
        db->entries[idx].avg_ms = current_ms;
        db->entries[idx].timestamp = time(NULL);
        return 0;
    } else {
        printf("  ✅ No significant change\n\n");
        return 0;
    }
}

#endif /* REGRESSION_TEST_H */
```

## Phase 8: CI/CD Integration

### Makefile for Performance Tests

```makefile
# Makefile for performance tests

CC = gcc
CFLAGS = -O2 -Wall -Wextra -std=c11 -pthread
PROF_CFLAGS = -pg -g
PERF_CFLAGS = -g -O2

# Targets
all: benchmark load_test stress_test

# Benchmarks
benchmark: benchmark.c
	$(CC) $(CFLAGS) -o benchmark benchmark.c

# Load tests
load_test: load_test.c
	$(CC) $(CFLAGS) -o load_test load_test.c

# Stress tests
stress_test: stress_test.c
	$(CC) $(CFLAGS) -DENABLE_MEMORY_PROFILING -o stress_test stress_test.c

# Profiling build
profile: benchmark.c
	$(CC) $(PROF_CFLAGS) -o benchmark_prof benchmark.c

# Run all performance tests
test: all
	./benchmark
	./load_test
	./stress_test

# Run with Valgrind
valgrind: all
	valgrind --leak-check=full --show-leak-kinds=all ./benchmark
	valgrind --leak-check=full --show-leak-kinds=all ./stress_test

# Profile with gprof
gprof: profile
	./benchmark_prof
	gprof benchmark_prof gmon.out > gprof_analysis.txt

# Clean
clean:
	rm -f benchmark load_test stress_test benchmark_prof
	rm -f gmon.out *.prof *.txt

.PHONY: all test valgrind gprof clean
```

### CI Configuration Example

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
        sudo apt-get install -y valgrind build-essential

    - name: Build performance tests
      run: make all

    - name: Run benchmarks
      run: ./benchmark > benchmark-results.txt

    - name: Run load tests
      run: ./load_test > load-test-results.txt

    - name: Run stress tests
      run: ./stress_test > stress-test-results.txt

    - name: Run Valgrind memory check
      run: |
        valgrind --leak-check=full --show-leak-kinds=all --log-file=valgrind.txt ./benchmark
        cat valgrind.txt

    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: |
          *-results.txt
          valgrind.txt
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
| Processing time | <10ms | [value] | ✅/❌ |
| Throughput | 10K ops/sec | [value] | ✅/❌ |
| Memory usage | <512MB | [value] | ✅/❌ |
| Memory leaks | 0 | [value] | ✅/❌ |

### Benchmark Results
```
Benchmark: string_copy_memcpy
  Iterations: 10000
  Average:    0.000123 ms
  Min:        0.000098 ms
  Max:        0.000456 ms
  Ops/sec:    8130081.30
```

### Load Test Results
```
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
1. **String Concatenation in process_data()**
   - **Issue**: Repeated reallocation using strcat()
   - **Impact**: O(n²) complexity, 200ms for 10K operations
   - **Recommendation**: Use single allocation with snprintf() or memcpy()

2. **Memory Fragmentation**
   - **Issue**: Many small allocations without pooling
   - **Impact**: 40% overhead in allocation time
   - **Recommendation**: Implement memory pool for fixed-size objects

### Performance Improvement Recommendations
- [ ] Implement memory pooling for frequent allocations
- [ ] Use const pointers where data isn't modified
- [ ] Replace malloc/free with arena allocator for temporary data
- [ ] Add __restrict keywords for non-aliasing pointers
- [ ] Enable compiler optimizations (-O3, -march=native)

### Test Execution
```bash
# Build and run all tests
make test

# Run with Valgrind
make valgrind

# Profile with gprof
make gprof

# Profile with perf
make
perf record -g ./benchmark
perf report
```

### Next Steps
- [ ] Establish performance baselines for all critical functions
- [ ] Integrate performance tests into CI/CD pipeline
- [ ] Set up continuous monitoring with system profilers
- [ ] Create performance dashboard with historical trends
- [ ] Schedule regular performance review meetings
~~~

## Output Format

The AI assistant should deliver:

1. **Performance test suite** with timing infrastructure and benchmarks
2. **Performance baselines** documented
3. **Load test scenarios** for critical operations
4. **Profiling results** with bottleneck identification
5. **Regression detection** configuration
6. **CI/CD integration** for automated performance gates
7. **Performance report** with metrics and recommendations
