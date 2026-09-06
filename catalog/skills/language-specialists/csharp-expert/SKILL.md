---
name: csharp-expert
description: Deep C# expertise for enterprise application development. Use when writing C# code, implementing async/await patterns, designing with LINQ, working with generics and delegates, building ASP.NET Core services, or applying SOLID design principles.
summary_l0: "Write enterprise C# with async/await, LINQ, generics, and ASP.NET Core patterns"
overview_l1: "This skill provides deep C# expertise for enterprise application development. Use it when writing C# code, implementing async/await patterns, designing with LINQ, working with generics and delegates, building ASP.NET Core services, or applying SOLID design principles. Key capabilities include async/await pattern design, LINQ query optimization, generic type and delegate design, ASP.NET Core middleware and DI configuration, Entity Framework Core usage, record and pattern matching (C# 10+), nullable reference type adoption, and SOLID principle application. The expected output is well-architected C# code with proper async patterns, LINQ usage, dependency injection, and enterprise design patterns. Trigger phrases: C# code, async await C#, LINQ, ASP.NET Core, Entity Framework, C# generics, C# delegates, SOLID C#, .NET, C# patterns."
---

# C# Expert

Specialized expertise in C# programming, providing deep guidance on async/await patterns, LINQ queries, generics and delegates, modern language features, dependency injection, error handling, and testing enterprise applications with xUnit.

## When to Use This Skill

Use this skill for:

- Implementing async/await and Task-based concurrency
- Writing efficient LINQ queries and custom extension methods
- Designing with generics, delegates, and event-driven patterns
- Leveraging modern C# features (pattern matching, records, file-scoped namespaces)
- Configuring dependency injection and applying SOLID principles
- Building robust error handling with structured logging
- Writing comprehensive tests with xUnit and mocking frameworks

**Trigger phrases**: "csharp", "c#", "dotnet", ".net", "asp.net", "async await", "linq", "entity framework", "xunit", "blazor"

## What This Skill Does

Provides C# expertise including:

- **Async/Await**: Task, ValueTask, async streams, cancellation, ConfigureAwait
- **LINQ**: Query and method syntax, deferred execution, Expression trees
- **Type System**: Generics, delegates, events, covariance/contravariance
- **Modern C#**: Pattern matching, records, switch expressions, list patterns
- **Architecture**: Dependency injection, SOLID principles, options pattern
- **Reliability**: Custom exceptions, Result pattern, structured logging
- **Testing**: xUnit, Moq/NSubstitute, FluentAssertions, integration tests

## Instructions

### Step 1: Master Async/Await and Task Patterns

Full walkthrough: [step-1-master-async-await-and-task-patterns.md](references/step-1-master-async-await-and-task-patterns.md) (load this step when you reach it).

### Step 2: Achieve LINQ Mastery

Full walkthrough: [step-2-achieve-linq-mastery.md](references/step-2-achieve-linq-mastery.md) (load this step when you reach it).

### Step 3: Leverage Generics, Delegates, and Events

Full walkthrough: [step-3-leverage-generics-delegates-and-events.md](references/step-3-leverage-generics-delegates-and-events.md) (load this step when you reach it).

### Step 4: Embrace Pattern Matching and Modern C#

Full walkthrough: [step-4-embrace-pattern-matching-and-modern-c.md](references/step-4-embrace-pattern-matching-and-modern-c.md) (load this step when you reach it).

### Step 5: Apply Dependency Injection and SOLID Principles

Full walkthrough: [step-5-apply-dependency-injection-and-solid-principles.md](references/step-5-apply-dependency-injection-and-solid-principles.md) (load this step when you reach it).

### Step 6: Build Robust Error Handling and Logging

Full walkthrough: [step-6-build-robust-error-handling-and-logging.md](references/step-6-build-robust-error-handling-and-logging.md) (load this step when you reach it).

### Step 7: Write Comprehensive Tests with xUnit

Full walkthrough: [step-7-write-comprehensive-tests-with-xunit.md](references/step-7-write-comprehensive-tests-with-xunit.md) (load this step when you reach it).

## Best Practices

- **Prefer async all the way** - Avoid mixing sync and async code; do not call `.Result` or `.Wait()` on tasks
- **Use CancellationToken everywhere** - Pass it through every async method signature and honor it
- **Small interfaces** - Follow Interface Segregation; clients should not depend on methods they do not use
- **Immutable data** - Use records and init-only setters for DTOs and value objects
- **Validate at boundaries** - Use FluentValidation or DataAnnotations at API entry points, not deep in domain logic
- **Log structurally** - Use semantic message templates with named parameters, never string interpolation in log calls
- **Fail fast** - Validate configuration at startup with `ValidateOnStart()`; do not let misconfiguration surface at runtime
- **Dispose properly** - Implement `IAsyncDisposable` for types that hold unmanaged or pooled resources

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "`.Result` is quicker than awaiting here" | Blocking on a Task from a request thread (ASP.NET, UI) deadlocks when the continuation needs the captured synchronization context; the symptom is a request that hangs forever, not an exception. |
| "I don't need to pass CancellationToken to this call" | A long EF Core query with no token keeps running after the client disconnects, holding a pooled connection until the pool is exhausted under load. |
| "Materializing the LINQ query early is harmless" | Calling `.ToList()` before a `.Where()` filter loads the whole table into memory instead of pushing the predicate to SQL, turning an indexed query into a full-table scan. |
| "Field injection with `[Autowired]`-style attributes reads cleaner" | Constructor injection makes missing dependencies a compile/startup failure; field injection defers it to a `NullReferenceException` at first use. |

## Verification

- [ ] All async methods accept and forward CancellationToken
- [ ] No `.Result` or `.Wait()` calls on tasks (async all the way)
- [ ] LINQ queries use deferred execution correctly (materialized only when needed)
- [ ] Generic constraints are as tight as necessary
- [ ] Dependency injection lifetimes are correct (no captive dependency problems)
- [ ] Structured logging uses message templates, not string interpolation
- [ ] Custom exceptions inherit from a common base
- [ ] Tests use Arrange-Act-Assert and meaningful assertion messages
- [ ] Integration tests replace external dependencies with test doubles

## Related Skills

- [[typescript-expert]] -- frontend/fullstack with Blazor WASM interop
- [[sql-expert]] -- Entity Framework Core and raw SQL optimization
- [[cicd-architect]] -- .NET CI/CD pipelines with GitHub Actions
- [[code-quality]] -- static analysis with Roslyn analyzers
- [[kubernetes-expert]] -- containerized .NET microservices on K8s

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: Microsoft C# documentation, .NET design guidelines, enterprise patterns


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
