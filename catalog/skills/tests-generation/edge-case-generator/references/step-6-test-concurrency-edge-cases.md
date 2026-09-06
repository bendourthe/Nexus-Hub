### Step 6: Test Concurrency Edge Cases

**Python:**
```python
import threading
import time


class TestConcurrencyEdgeCases:
    """Concurrency edge cases for shared-state operations."""

    def test_concurrent_counter_increments(self):
        counter = ThreadSafeCounter()
        threads = []
        for _ in range(100):
            t = threading.Thread(target=counter.increment)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        assert counter.value == 100

    def test_concurrent_reads_during_write(self):
        cache = SharedCache()
        cache.put("key", "initial")
        errors = []

        def reader():
            for _ in range(1000):
                val = cache.get("key")
                if val is None:
                    errors.append("Got None during concurrent read")

        def writer():
            for i in range(1000):
                cache.put("key", f"value_{i}")

        reader_thread = threading.Thread(target=reader)
        writer_thread = threading.Thread(target=writer)
        reader_thread.start()
        writer_thread.start()
        reader_thread.join()
        writer_thread.join()
        assert len(errors) == 0, f"Concurrent read failures: {errors[:5]}"

    def test_double_close_resource(self):
        resource = ManagedResource()
        resource.close()
        # Second close should not raise
        resource.close()
        assert resource.is_closed
```

**JavaScript:**
```javascript
describe("concurrency edge cases", () => {
  test("concurrent promise resolution order", async () => {
    const results = [];
    const fast = new Promise((resolve) =>
      setTimeout(() => { results.push("fast"); resolve(); }, 10)
    );
    const slow = new Promise((resolve) =>
      setTimeout(() => { results.push("slow"); resolve(); }, 50)
    );
    await Promise.all([slow, fast]);
    expect(results[0]).toBe("fast");
  });

  test("double-submit prevention", async () => {
    const handler = new SubmitHandler();
    const [result1, result2] = await Promise.all([
      handler.submit({ id: 1 }),
      handler.submit({ id: 1 }),
    ]);
    // One should succeed, one should be rejected as duplicate
    const successes = [result1, result2].filter((r) => r.status === "ok");
    expect(successes).toHaveLength(1);
  });

  test("race condition in check-then-act", async () => {
    const inventory = new Inventory({ widget: 1 });
    const purchase1 = inventory.purchase("widget");
    const purchase2 = inventory.purchase("widget");
    const results = await Promise.allSettled([purchase1, purchase2]);
    const fulfilled = results.filter((r) => r.status === "fulfilled");
    expect(fulfilled.length).toBeLessThanOrEqual(1);
  });
});
```

**Java:**
```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.RepeatedTest;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.jupiter.api.Assertions.*;

class ConcurrencyEdgeCasesTest {

    @RepeatedTest(10)
    void concurrentIncrementsAreAtomic() throws Exception {
        var counter = new ThreadSafeCounter();
        int threadCount = 100;
        var latch = new CountDownLatch(threadCount);
        var executor = Executors.newFixedThreadPool(threadCount);

        for (int i = 0; i < threadCount; i++) {
            executor.submit(() -> {
                counter.increment();
                latch.countDown();
            });
        }
        latch.await(5, TimeUnit.SECONDS);
        executor.shutdown();
        assertEquals(threadCount, counter.getValue());
    }

    @Test
    void doubleCloseDoesNotThrow() {
        var resource = new ManagedResource();
        resource.close();
        assertDoesNotThrow(resource::close);
    }

    @Test
    void concurrentMapAccessDoesNotLoseEntries() throws Exception {
        var map = new ConcurrentHashMap<String, Integer>();
        int threadCount = 50;
        var latch = new CountDownLatch(threadCount);
        var executor = Executors.newFixedThreadPool(threadCount);

        for (int i = 0; i < threadCount; i++) {
            final int idx = i;
            executor.submit(() -> {
                map.put("key-" + idx, idx);
                latch.countDown();
            });
        }
        latch.await(5, TimeUnit.SECONDS);
        executor.shutdown();
        assertEquals(threadCount, map.size());
    }
}
```
