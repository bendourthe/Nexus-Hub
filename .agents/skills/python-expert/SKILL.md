---
name: python-expert
description: Deep Python expertise for production systems. Use when writing Python code, implementing async patterns, designing class hierarchies, handling exceptions idiomatically, optimizing performance, or working with Python packaging and typing.
summary_l0: "Write production Python with async patterns, type hints, and packaging best practices"
overview_l1: "This skill provides deep Python expertise for production systems. Use it when writing Python code, implementing async patterns with asyncio, designing class hierarchies, handling exceptions idiomatically, optimizing performance, or working with Python packaging and typing. Key capabilities include asyncio and async/await patterns, type hint design with mypy/pyright compliance, class and protocol design, exception handling hierarchies, performance optimization with profiling, packaging with pyproject.toml and uv/pip, dataclass and Pydantic model design, and testing with pytest. The expected output is production-grade Python code with proper type annotations, async patterns, exception handling, and packaging configuration. Trigger phrases: Python code, asyncio, type hints, Python packaging, Python performance, Python testing, pytest, Pydantic, Python async."
---

# Python Expert

Specialized expertise in Python programming, providing deep guidance on type annotations and static analysis, exception handling idioms, async/await concurrency, data modeling with dataclasses and Pydantic, testing with pytest, performance optimization, and modern packaging with pyproject.toml.

## When to Use This Skill

Use this skill for:

- Adding type annotations and configuring mypy strict mode
- Designing custom exception hierarchies and error chains
- Implementing async/await patterns with asyncio
- Modeling data with dataclasses and Pydantic
- Writing pytest test suites with fixtures and parametrize
- Profiling and optimizing Python performance
- Setting up Python project structure and packaging

**Trigger phrases**: "python", "asyncio", "pydantic", "pytest", "mypy", "type hints", "dataclass", "python packaging", "python performance"

## What This Skill Does

Provides Python expertise including:

- **Type System**: Annotations, generics, protocols, mypy strict
- **Error Handling**: Custom exceptions, error chains, context managers
- **Async/Await**: asyncio event loop, task groups, async generators
- **Data Modeling**: dataclasses, Pydantic BaseModel, validation
- **Testing**: pytest fixtures, parametrize, monkeypatch, coverage
- **Performance**: Profiling, generators, slots, caching, comprehensions
- **Packaging**: pyproject.toml, src layout, virtual environments

## Instructions

### Step 1: Master Type Annotations and mypy-Strict Patterns

Full walkthrough: [step-1-master-type-annotations-and-mypy-strict-patterns.md](references/step-1-master-type-annotations-and-mypy-strict-patterns.md) (load this step when you reach it).

### Step 2: Handle Exceptions Idiomatically

Full walkthrough: [step-2-handle-exceptions-idiomatically.md](references/step-2-handle-exceptions-idiomatically.md) (load this step when you reach it).

### Step 3: Implement Async/Await Patterns

Full walkthrough: [step-3-implement-async-await-patterns.md](references/step-3-implement-async-await-patterns.md) (load this step when you reach it).

### Step 4: Model Data with Dataclasses and Pydantic

Full walkthrough: [step-4-model-data-with-dataclasses-and-pydantic.md](references/step-4-model-data-with-dataclasses-and-pydantic.md) (load this step when you reach it).

### Step 5: Write Thorough Tests with pytest

Full walkthrough: [step-5-write-thorough-tests-with-pytest.md](references/step-5-write-thorough-tests-with-pytest.md) (load this step when you reach it).

### Step 6: Optimize Performance

Full walkthrough: [step-6-optimize-performance.md](references/step-6-optimize-performance.md) (load this step when you reach it).

### Step 7: Structure Projects and Packaging

Full walkthrough: [step-7-structure-projects-and-packaging.md](references/step-7-structure-projects-and-packaging.md) (load this step when you reach it).

## Best Practices

- **Type everything** - Run mypy strict in CI; zero type errors is the target
- **Raise specific exceptions** - Never raise bare Exception; define a project hierarchy
- **Use context managers** - For any resource that needs cleanup (files, connections, locks)
- **Prefer composition** - Inherit only from abstract base classes or Protocol
- **Immutable by default** - Use frozen dataclasses and tuples unless mutation is required
- **Profile first** - Measure before optimizing; use cProfile or py-spy
- **Test at boundaries** - Mock external services, not internal functions
- **Pin dependencies** - Exact versions in production; ranges only in library pyproject.toml

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Type hints are optional, the code runs without them" | Without annotations `mypy --strict` cannot catch a `None` passed where a `str` is expected, so the `AttributeError` surfaces at runtime in a code path the tests did not cover. |
| "A mutable default like `def f(x=[])` is convenient" | The default list is created once and shared across calls, so the second caller sees the first caller's mutations; this is a classic silent state-leak bug. |
| "A bare `except:` keeps the script robust" | Bare except swallows `KeyboardInterrupt` and `SystemExit`, so the process becomes unkillable and masks the real error instead of logging it. |
| "Pydantic validation is overkill for this input" | Skipping validation at the boundary lets a malformed payload propagate as a wrong-typed value deep into business logic, where the traceback no longer points at the source. |

## Verification

- [ ] All functions have type annotations (parameters and return)
- [ ] mypy strict passes with zero errors
- [ ] Custom exceptions inherit from a project base class
- [ ] Context managers used for resource cleanup
- [ ] Async code uses TaskGroup or gather for concurrency
- [ ] Pydantic models validate all external input
- [ ] pytest coverage at or above 80%
- [ ] No mutable default arguments in function signatures
- [ ] ruff check and ruff format pass
- [ ] pyproject.toml defines all project metadata

## Related Skills

- [[performance-testing]] -- Python profiling and benchmarks
- [[cicd-architect]] -- Python CI/CD pipelines
- [[code-quality]] -- Python code-standard scoring
- [[fastapi-expert]] -- FastAPI and async web services

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: awesome-codex-subagents python-pro patterns

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets are not met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
