### Step 4: Build Concurrent Applications

**CompletableFuture Pipelines**:

```java
// Async computation with chaining
CompletableFuture<UserProfile> profileFuture = CompletableFuture
    .supplyAsync(() -> userService.findById(userId))
    .thenApply(user -> enrichWithPreferences(user))
    .thenApply(user -> buildProfile(user))
    .exceptionally(ex -> {
        logger.error("Failed to load profile for user {}", userId, ex);
        return UserProfile.defaultProfile();
    });

// Combining multiple futures
CompletableFuture<String> nameFuture = CompletableFuture.supplyAsync(() -> fetchName(id));
CompletableFuture<String> emailFuture = CompletableFuture.supplyAsync(() -> fetchEmail(id));
CompletableFuture<String> roleFuture = CompletableFuture.supplyAsync(() -> fetchRole(id));

CompletableFuture<UserSummary> combined = nameFuture
    .thenCombine(emailFuture, (name, email) -> new UserSummary(name, email, null))
    .thenCombine(roleFuture, (summary, role) -> new UserSummary(summary.name(), summary.email(), role));

// Wait for all futures
CompletableFuture<Void> allDone = CompletableFuture.allOf(nameFuture, emailFuture, roleFuture);
allDone.thenRun(() -> System.out.println("All lookups complete"));

// Wait for first to complete
CompletableFuture<Object> fastest = CompletableFuture.anyOf(
    fetchFromPrimary(id),
    fetchFromSecondary(id)
);
```

**Virtual Threads and Structured Concurrency**:

```java
// Virtual threads replace platform threads for I/O-bound work (Java 21+)
// Each virtual thread is lightweight (a few KB vs. ~1 MB for platform threads)
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<Response>> futures = requests.stream()
        .map(req -> executor.submit(() -> httpClient.send(req, BodyHandlers.ofString())))
        .toList();

    for (var future : futures) {
        Response response = future.get();
        process(response);
    }
}

// Structured concurrency (preview in Java 21+)
// Ensures child tasks are bounded by the parent scope
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Subtask<User> userTask = scope.fork(() -> userService.findById(userId));
    Subtask<List<Order>> ordersTask = scope.fork(() -> orderService.findByUser(userId));

    scope.join();            // Wait for both tasks
    scope.throwIfFailed();   // Propagate any exception

    return new UserDashboard(userTask.get(), ordersTask.get());
}

// Synchronized vs ReentrantLock
// Use synchronized for simple mutual exclusion
public class Counter {
    private int count = 0;

    public synchronized void increment() { count++; }
    public synchronized int getCount() { return count; }
}

// Use ReentrantLock for advanced features (tryLock, timed lock, fairness)
public class FairCounter {
    private final ReentrantLock lock = new ReentrantLock(true); // fair ordering
    private int count = 0;

    public void increment() {
        lock.lock();
        try {
            count++;
        } finally {
            lock.unlock(); // always unlock in finally
        }
    }

    public boolean tryIncrement(long timeout, TimeUnit unit) throws InterruptedException {
        if (lock.tryLock(timeout, unit)) {
            try {
                count++;
                return true;
            } finally {
                lock.unlock();
            }
        }
        return false;
    }
}
```

**Atomic Variables and ConcurrentHashMap**:

```java
// AtomicInteger, AtomicLong, AtomicReference for lock-free operations
private final AtomicLong requestCount = new AtomicLong(0);

public void handleRequest() {
    long count = requestCount.incrementAndGet();
    logger.info("Request #{}", count);
}

// ConcurrentHashMap for thread-safe map operations
private final ConcurrentHashMap<String, AtomicLong> metrics = new ConcurrentHashMap<>();

public void recordMetric(String name) {
    metrics.computeIfAbsent(name, k -> new AtomicLong(0)).incrementAndGet();
}

public Map<String, Long> getSnapshot() {
    return metrics.entrySet().stream()
        .collect(Collectors.toMap(Map.Entry::getKey, e -> e.getValue().get()));
}
```
