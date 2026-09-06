---
name: java-expert
description: Deep Java expertise for enterprise application development. Use when writing Java code, implementing concurrency patterns, designing with streams and generics, building Spring Boot services, or applying clean architecture principles.
summary_l0: "Write enterprise Java with streams, concurrency, Spring Boot, and clean architecture"
overview_l1: "This skill provides deep Java expertise for enterprise application development. Use it when writing Java code, implementing concurrency patterns (virtual threads, CompletableFuture), designing with streams and generics, building Spring Boot services, or applying clean architecture principles. Key capabilities include modern Java feature usage (records, sealed classes, pattern matching), Stream API design, concurrent programming with virtual threads, Spring Boot service architecture, JPA/Hibernate integration, generic type design, testing with JUnit 5 and Mockito, and clean architecture layering. The expected output is well-structured Java code with modern language features, proper concurrency handling, and enterprise architecture patterns. Trigger phrases: Java code, Spring Boot, Java streams, Java concurrency, virtual threads, JPA, Hibernate, Java generics, Java testing, clean architecture Java."
---

# Java Expert

Specialized expertise in Java programming, providing deep guidance on modern language features, streams and functional programming, generics, concurrency with virtual threads, Spring Boot patterns, resilience strategies, and testing with JUnit 5.

## When to Use This Skill

Use this skill for:

- Writing modern Java (17+) with records, sealed classes, and pattern matching
- Designing stream pipelines and functional transformations
- Implementing type-safe generic APIs
- Building concurrent applications with virtual threads and CompletableFuture
- Developing Spring Boot microservices
- Designing resilient error handling and retry strategies
- Writing comprehensive JUnit 5 test suites

**Trigger phrases**: "java", "spring boot", "jvm", "java concurrency", "java streams", "java generics", "junit", "java records", "virtual threads"

## What This Skill Does

Provides Java expertise including:

- **Modern Java**: Records, sealed classes, pattern matching, text blocks, virtual threads
- **Streams**: Stream API, collectors, Optional, parallel streams
- **Generics**: Bounded types, wildcards, type erasure workarounds
- **Concurrency**: CompletableFuture, virtual threads, structured concurrency, locks
- **Spring Boot**: DI, REST controllers, security, configuration, profiles
- **Resilience**: Custom exceptions, circuit breakers, retry patterns
- **Testing**: JUnit 5, Mockito, AssertJ, TestContainers, MockMvc

## Instructions

### Step 1: Leverage Modern Java Features

Full walkthrough: [step-1-leverage-modern-java-features.md](references/step-1-leverage-modern-java-features.md) (load this step when you reach it).

### Step 2: Master Streams and Functional Programming

Full walkthrough: [step-2-master-streams-and-functional-programming.md](references/step-2-master-streams-and-functional-programming.md) (load this step when you reach it).

### Step 3: Design Type-Safe Generics

Full walkthrough: [step-3-design-type-safe-generics.md](references/step-3-design-type-safe-generics.md) (load this step when you reach it).

### Step 4: Build Concurrent Applications

Full walkthrough: [step-4-build-concurrent-applications.md](references/step-4-build-concurrent-applications.md) (load this step when you reach it).

### Step 5: Apply Spring Boot Patterns

Full walkthrough: [step-5-apply-spring-boot-patterns.md](references/step-5-apply-spring-boot-patterns.md) (load this step when you reach it).

### Step 6: Implement Error Handling and Resilience

Full walkthrough: [step-6-implement-error-handling-and-resilience.md](references/step-6-implement-error-handling-and-resilience.md) (load this step when you reach it).

### Step 7: Test Effectively with JUnit 5

Full walkthrough: [step-7-test-effectively-with-junit-5.md](references/step-7-test-effectively-with-junit-5.md) (load this step when you reach it).

## Best Practices

- **Prefer records for data transfer** - Use records for DTOs, value objects, and event payloads
- **Use sealed types for domain modeling** - Sealed interfaces with records make invalid states unrepresentable
- **Choose virtual threads for I/O** - Virtual threads excel for I/O-bound workloads; platform threads remain better for CPU-bound computation
- **Favor Optional over null returns** - Return Optional from lookup methods; never use Optional as a field or parameter type
- **Inject dependencies through constructors** - Constructor injection makes dependencies explicit and supports immutability
- **Keep controllers thin** - Controllers should delegate to services; business logic never belongs in a controller
- **Handle exceptions globally** - Use @ControllerAdvice for consistent error responses across all endpoints
- **Test at the right level** - Use MockMvc for web layer, Mockito for unit tests, TestContainers for integration tests

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Returning `null` from a lookup is the Java way" | Callers forget the null check and a `NullPointerException` surfaces three layers up with no clue which lookup returned null; `Optional` forces the absence to be handled at the call site. |
| "Field injection with `@Autowired` is less verbose" | Field-injected beans cannot be constructed in a unit test without a Spring context and hide missing dependencies until runtime; constructor injection fails fast at startup. |
| "An imperative loop is clearer than a stream here" | Hand-rolled accumulation loops reintroduce off-by-one and mutable-state bugs that a `Collectors.toMap`/`groupingBy` pipeline cannot have. |
| "I'll catch `Exception` and log it" | A blanket catch swallows `InterruptedException` without re-interrupting the thread, breaking cancellation; catch the specific checked exceptions and route them through `@ControllerAdvice`. |

## Verification

- [ ] Records used for value types and DTOs
- [ ] Sealed interfaces used for closed type hierarchies
- [ ] Streams used instead of imperative loops for collection transformations
- [ ] Optional returned from lookup methods (never null)
- [ ] CompletableFuture or virtual threads for async I/O
- [ ] Custom exception hierarchy with @ControllerAdvice
- [ ] Constructor injection throughout (no @Autowired on fields)
- [ ] Tests cover unit, integration, and web layers
- [ ] Parameterized tests for functions with multiple input/output combinations

## Related Skills

- [[fastapi-expert]] -- contrast with Spring Boot when choosing a service framework
- [[performance-testing]] -- JMH benchmarks and load testing
- [[cicd-architect]] -- Maven/Gradle CI/CD pipelines
- [[kubernetes-expert]] -- Java microservices on K8s
- [[code-quality]] -- SonarQube, Checkstyle, and SpotBugs scoring

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: Effective Java (Bloch), Spring Boot Reference, JDK 21+ documentation


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
