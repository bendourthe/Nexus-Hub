### Step 5: Build Concurrent Applications

**Threads and Joining**:

```cpp
#include <thread>
#include <mutex>
#include <shared_mutex>
#include <atomic>
#include <future>
#include <latch>
#include <barrier>

// std::jthread (C++20) joins automatically on destruction
void parallel_compute(std::span<const double> input, std::span<double> output) {
    auto worker = [&](std::size_t begin, std::size_t end) {
        for (auto i = begin; i < end; ++i) {
            output[i] = expensive_transform(input[i]);
        }
    };

    auto mid = input.size() / 2;
    std::jthread t1(worker, 0, mid);
    std::jthread t2(worker, mid, input.size());
    // Both threads join when t1 and t2 go out of scope
}
```

**Mutexes and Lock Guards**:

```cpp
class ThreadSafeCache {
    mutable std::shared_mutex mutex_;
    std::unordered_map<std::string, std::string> data_;

public:
    // Multiple readers allowed simultaneously
    auto get(const std::string& key) const -> std::optional<std::string> {
        std::shared_lock lock(mutex_);  // Shared (read) lock
        auto it = data_.find(key);
        return (it != data_.end()) ? std::optional{it->second} : std::nullopt;
    }

    // Exclusive access for writes
    void put(const std::string& key, const std::string& value) {
        std::unique_lock lock(mutex_);  // Exclusive (write) lock
        data_[key] = value;
    }

    // Lock multiple mutexes without deadlock
    void merge_from(ThreadSafeCache& other) {
        std::scoped_lock lock(mutex_, other.mutex_);  // Locks both, deadlock-free
        data_.merge(other.data_);
    }
};
```

**Atomics and Async Tasks**:

```cpp
// Atomic for lock-free counters and flags
std::atomic<int> request_count{0};
std::atomic<bool> shutdown_requested{false};

void handle_request() {
    request_count.fetch_add(1, std::memory_order_relaxed);
    // Process request...
}

// std::async for fire-and-forget tasks with futures
auto future_result = std::async(std::launch::async, [] {
    return compute_heavy_result();
});
// Do other work...
auto result = future_result.get();  // Blocks until ready

// std::latch (C++20): single-use countdown barrier
void parallel_init(std::span<Subsystem*> systems) {
    std::latch ready(systems.size());

    for (auto* sys : systems) {
        std::jthread([sys, &ready] {
            sys->initialize();
            ready.count_down();  // Signal completion
        });
    }

    ready.wait();  // Block until all subsystems initialized
}

// std::barrier (C++20): reusable synchronization point
void iterative_solver(int iterations, int num_threads) {
    std::barrier sync_point(num_threads, [] noexcept {
        // Completion function runs once per phase
    });

    auto worker = [&](int id) {
        for (int i = 0; i < iterations; ++i) {
            compute_local(id);
            sync_point.arrive_and_wait();  // All threads synchronize
            exchange_boundaries(id);
            sync_point.arrive_and_wait();  // Synchronize again
        }
    };

    std::vector<std::jthread> threads;
    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back(worker, i);
    }
}
```

**Condition Variables**:

```cpp
template <typename T>
class BoundedQueue {
    std::queue<T> queue_;
    std::mutex mutex_;
    std::condition_variable not_empty_;
    std::condition_variable not_full_;
    std::size_t max_size_;

public:
    explicit BoundedQueue(std::size_t max_size) : max_size_(max_size) {}

    void push(T item) {
        std::unique_lock lock(mutex_);
        not_full_.wait(lock, [&] { return queue_.size() < max_size_; });
        queue_.push(std::move(item));
        not_empty_.notify_one();
    }

    T pop() {
        std::unique_lock lock(mutex_);
        not_empty_.wait(lock, [&] { return !queue_.empty(); });
        T item = std::move(queue_.front());
        queue_.pop();
        not_full_.notify_one();
        return item;
    }
};
```
