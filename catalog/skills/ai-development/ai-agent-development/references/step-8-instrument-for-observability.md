### Step 8: Instrument for Observability

**Structured Logging and Tracing**:

```python
import logging
import uuid
from contextvars import ContextVar
from functools import wraps

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")

logger = logging.getLogger("agent")


def new_trace() -> str:
    """Start a new trace and return its ID."""
    tid = uuid.uuid4().hex[:12]
    trace_id_var.set(tid)
    return tid


def traced(func):
    """Decorator that adds trace context to log messages."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        trace_id = trace_id_var.get()
        logger.info(
            "step_start",
            extra={
                "trace_id": trace_id,
                "step": func.__name__,
                "args_summary": str(args)[:200],
            },
        )
        try:
            result = func(*args, **kwargs)
            logger.info(
                "step_end",
                extra={
                    "trace_id": trace_id,
                    "step": func.__name__,
                    "result_summary": str(result)[:200],
                },
            )
            return result
        except Exception as e:
            logger.error(
                "step_error",
                extra={
                    "trace_id": trace_id,
                    "step": func.__name__,
                    "error": str(e),
                },
            )
            raise
    return wrapper


@traced
def agent_step(task: str) -> str:
    """Example instrumented agent step."""
    return run_react_agent(task)
```

**Cost Tracking**:

```python
@dataclass
class UsageTracker:
    """Track token usage and estimated cost across agent runs."""
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: int = 0

    # Approximate pricing per million tokens (adjust to current rates)
    INPUT_COST_PER_M = 3.0
    OUTPUT_COST_PER_M = 15.0

    def record(self, response):
        """Record usage from an API response."""
        self.input_tokens += response.usage.input_tokens
        self.output_tokens += response.usage.output_tokens
        self.tool_calls += sum(
            1 for b in response.content if getattr(b, "type", "") == "tool_use"
        )

    @property
    def estimated_cost(self) -> float:
        return (
            (self.input_tokens / 1_000_000) * self.INPUT_COST_PER_M
            + (self.output_tokens / 1_000_000) * self.OUTPUT_COST_PER_M
        )

    def summary(self) -> str:
        return (
            f"Tokens: {self.input_tokens:,} in / {self.output_tokens:,} out | "
            f"Tool calls: {self.tool_calls} | "
            f"Est. cost: ${self.estimated_cost:.4f}"
        )
```
