### Step 6: Optimize Memory and Performance

**Cache-Friendly Data Structures (SoA vs AoS)**:

```cpp
// Array of Structures (AoS): poor cache utilization when accessing one field
struct ParticleAoS {
    float x, y, z;       // position
    float vx, vy, vz;    // velocity
    float mass;
    int   type;
};
std::vector<ParticleAoS> particles_aos(10'000);

// Structure of Arrays (SoA): cache-friendly when iterating one field
struct ParticlesSoA {
    std::vector<float> x, y, z;
    std::vector<float> vx, vy, vz;
    std::vector<float> mass;
    std::vector<int>   type;

    explicit ParticlesSoA(std::size_t n)
        : x(n), y(n), z(n), vx(n), vy(n), vz(n), mass(n), type(n) {}
};

// Updating positions touches only x, y, z and vx, vy, vz (contiguous in memory)
void update_positions(ParticlesSoA& p, float dt) {
    for (std::size_t i = 0; i < p.x.size(); ++i) {
        p.x[i] += p.vx[i] * dt;
        p.y[i] += p.vy[i] * dt;
        p.z[i] += p.vz[i] * dt;
    }
}
```

**Custom Allocators and PMR**:

```cpp
#include <memory_resource>
#include <vector>

// Polymorphic Memory Resource (std::pmr) lets you swap allocators at runtime
void process_batch(std::span<const Record> records) {
    // Stack-based buffer for small allocations (no heap, no fragmentation)
    std::array<std::byte, 16'384> buffer;
    std::pmr::monotonic_buffer_resource pool(buffer.data(), buffer.size());

    // Vector uses the stack buffer; falls back to default if exhausted
    std::pmr::vector<Result> results(&pool);
    results.reserve(records.size());

    for (const auto& rec : records) {
        results.push_back(transform(rec));
    }
}

// Placement new: construct an object in pre-allocated memory
alignas(Widget) std::byte storage[sizeof(Widget)];
Widget* w = new (storage) Widget(args...);
// Must call destructor manually
w->~Widget();
```

**Benchmarking with Google Benchmark**:

```cpp
#include <benchmark/benchmark.h>

// Basic benchmark
static void BM_VectorPushBack(benchmark::State& state) {
    for (auto _ : state) {
        std::vector<int> v;
        for (int i = 0; i < state.range(0); ++i) {
            v.push_back(i);
        }
        benchmark::DoNotOptimize(v.data());  // Prevent dead-code elimination
    }
}
BENCHMARK(BM_VectorPushBack)->Range(8, 1 << 20);

// Compare reserved vs unreserved
static void BM_VectorReserved(benchmark::State& state) {
    for (auto _ : state) {
        std::vector<int> v;
        v.reserve(state.range(0));
        for (int i = 0; i < state.range(0); ++i) {
            v.push_back(i);
        }
        benchmark::DoNotOptimize(v.data());
    }
}
BENCHMARK(BM_VectorReserved)->Range(8, 1 << 20);

// Benchmark with custom counters
static void BM_StringConcat(benchmark::State& state) {
    std::string base(state.range(0), 'x');
    for (auto _ : state) {
        std::string result = base + base;
        benchmark::DoNotOptimize(result);
    }
    state.SetBytesProcessed(state.iterations() * state.range(0) * 2);
}
BENCHMARK(BM_StringConcat)->RangeMultiplier(4)->Range(64, 1 << 16);

BENCHMARK_MAIN();
```
