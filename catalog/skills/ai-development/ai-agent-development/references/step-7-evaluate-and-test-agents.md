### Step 7: Evaluate and Test Agents

**Evaluation Framework**:

```python
@dataclass
class EvalCase:
    """A single evaluation case for an agent."""
    name: str
    input: str
    expected_output: str | None = None       # For exact match
    expected_contains: list[str] | None = None  # For partial match
    max_tool_calls: int = 20
    max_seconds: float = 60.0
    tags: list[str] = field(default_factory=list)


@dataclass
class EvalResult:
    case_name: str
    passed: bool
    output: str
    tool_calls: int
    duration_seconds: float
    failure_reason: str = ""


def run_evaluation(agent_fn, cases: list[EvalCase]) -> list[EvalResult]:
    """Run an evaluation suite against an agent function."""
    import time
    results = []

    for case in cases:
        start = time.time()
        try:
            output = agent_fn(case.input)
            duration = time.time() - start

            passed = True
            reason = ""

            if case.expected_output and output.strip() != case.expected_output.strip():
                passed = False
                reason = f"Expected '{case.expected_output}', got '{output[:200]}'"

            if case.expected_contains:
                missing = [s for s in case.expected_contains if s not in output]
                if missing:
                    passed = False
                    reason = f"Output missing expected strings: {missing}"

            if duration > case.max_seconds:
                passed = False
                reason = f"Timeout: {duration:.1f}s > {case.max_seconds}s"

            results.append(EvalResult(
                case_name=case.name,
                passed=passed,
                output=output[:500],
                tool_calls=0,  # Instrumented via guardrails
                duration_seconds=duration,
                failure_reason=reason,
            ))

        except Exception as e:
            results.append(EvalResult(
                case_name=case.name,
                passed=False,
                output="",
                tool_calls=0,
                duration_seconds=time.time() - start,
                failure_reason=str(e),
            ))

    return results


def print_eval_report(results: list[EvalResult]):
    """Print a summary report of evaluation results."""
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\nAgent Evaluation: {passed}/{total} passed ({100*passed/total:.0f}%)\n")

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.case_name} ({r.duration_seconds:.1f}s)")
        if not r.passed:
            print(f"         Reason: {r.failure_reason}")
```
