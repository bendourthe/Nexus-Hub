## Common Patterns

### Pattern 1: Retry with Exponential Backoff

```python
import asyncio
import random

async def retry_with_backoff(
    coro_factory,
    retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
):
    """Retry an async operation with exponential backoff and optional jitter."""
    for attempt in range(retries):
        try:
            return await coro_factory()
        except Exception as e:
            if attempt == retries - 1:
                raise
            delay = min(base_delay * (2 ** attempt), max_delay)
            if jitter:
                delay *= (0.5 + random.random())
            await asyncio.sleep(delay)
```

### Pattern 2: Circuit Breaker

```python
import asyncio
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    async def call(self, coro):
        if self.state == CircuitState.OPEN:
            if time.monotonic() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise RuntimeError("Circuit breaker is OPEN")

        try:
            result = await coro
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

### Pattern 3: Fan-Out / Fan-In with Result Aggregation

```go
// Fan-out work to N goroutines; fan-in results into a single channel
func fanOutFanIn(ctx context.Context, input []int, workers int) (int, error) {
    jobs := make(chan int, len(input))
    results := make(chan int, len(input))
    errs := make(chan error, workers)

    // Fan-out
    var wg sync.WaitGroup
    for i := 0; i < workers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range jobs {
                select {
                case <-ctx.Done():
                    errs <- ctx.Err()
                    return
                default:
                    results <- job * job // Example: square the number
                }
            }
        }()
    }

    // Send jobs
    for _, v := range input {
        jobs <- v
    }
    close(jobs)

    // Wait for workers, then close results
    go func() {
        wg.Wait()
        close(results)
        close(errs)
    }()

    // Fan-in: aggregate
    total := 0
    for r := range results {
        total += r
    }

    if err := <-errs; err != nil {
        return 0, err
    }
    return total, nil
}
```

### Pattern 4: Actor Model (Simplified Python)

```python
import asyncio
from typing import Any

class Actor:
    """Lightweight actor: processes messages sequentially via a mailbox."""

    def __init__(self):
        self._mailbox: asyncio.Queue = asyncio.Queue()
        self._running = False

    async def start(self):
        self._running = True
        asyncio.create_task(self._run())

    async def _run(self):
        while self._running:
            message = await self._mailbox.get()
            if message is None:
                break
            await self.handle(message)

    async def handle(self, message: Any):
        raise NotImplementedError

    async def send(self, message: Any):
        await self._mailbox.put(message)

    async def stop(self):
        self._running = False
        await self._mailbox.put(None)

class CounterActor(Actor):
    def __init__(self):
        super().__init__()
        self.count = 0

    async def handle(self, message):
        if message["type"] == "increment":
            self.count += message.get("amount", 1)
        elif message["type"] == "get":
            message["reply"].set_result(self.count)
```
