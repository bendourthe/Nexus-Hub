### Step 8: Instrument for Observability

Field names, span kinds, and the default privacy rules are owned by
[`agent-span-contract.md`](agent-span-contract.md). A runnable, metadata-only
demonstration ships at [`../scripts/trace-example.py`](../scripts/trace-example.py).
This step teaches the instrumentation; it does not restate the contract.

**Structured Logging and Tracing**:

The default is metadata only. Arguments, results, and raw exception text stay
out of the record unless a human has separately authorized capturing them.

```python
import logging
import secrets
from contextvars import ContextVar
from functools import wraps

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")

logger = logging.getLogger("agent")

# Bounded allowlist. An unrecognized failure becomes internal_error; it never
# becomes the exception text.
ERROR_CATEGORIES = frozenset({
    "timeout", "rate_limited", "invalid_input",
    "permission_denied", "unavailable", "internal_error",
})


def new_trace() -> str:
    """Start a new trace and return its ID (32 hex characters, not truncated)."""
    tid = secrets.token_hex(16)
    trace_id_var.set(tid)
    return tid


def categorize(exc: BaseException) -> str:
    """Map an exception to an allowlisted category, discarding its message."""
    match exc:
        case TimeoutError():
            return "timeout"
        case PermissionError():
            return "permission_denied"
        case ValueError():
            return "invalid_input"
        case _:
            return "internal_error"


def traced(func):
    """Decorator that adds trace context to log messages."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        trace_id = trace_id_var.get()
        span_id = secrets.token_hex(8)
        # Arity is metadata; the argument values are not recorded.
        logger.info(
            "step_start",
            extra={
                "trace_id": trace_id,
                "span_id": span_id,
                "step": func.__name__,
                "arg_count": len(args) + len(kwargs),
            },
        )
        try:
            result = func(*args, **kwargs)
            logger.info(
                "step_end",
                extra={
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "step": func.__name__,
                    "status": "OK",
                    "result_type": type(result).__name__,
                },
            )
            return result
        except Exception as e:
            logger.error(
                "step_error",
                extra={
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "step": func.__name__,
                    "status": "ERROR",
                    "error.type": categorize(e),
                },
            )
            raise
    return wrapper


@traced
def agent_step(task: str) -> str:
    """Example instrumented agent step."""
    return run_react_agent(task)
```

Three changes from the shape this example used to have, each fixing a real leak:

- **`str(args)[:200]` and `str(result)[:200]` are gone.** Truncation is not
  redaction. The first 200 characters of a prompt are still the prompt, and a
  truncated credential is still a credential prefix. Record the arity and the
  result type, which answer "what shape was this call" without reproducing it.
- **`str(e)` is replaced by an allowlisted category.** Exception messages carry
  file paths, connection strings, and row data that nobody reviewed before it
  reached the log.
- **The trace ID is no longer shortened to 12 hex characters.** A truncated
  identifier raises collision probability across a long-running system while
  saving nothing that matters.

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
