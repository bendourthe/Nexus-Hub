---
name: cpp-expert
description: Deep C++ expertise for systems and performance-critical development. Use when writing modern C++ code, implementing RAII and smart pointers, designing templates and concepts, optimizing memory layout, or building high-performance applications.
summary_l0: "Write modern C++ with RAII, smart pointers, templates, and performance optimization"
overview_l1: "This skill provides deep C++ expertise for systems and performance-critical development. Use it when writing modern C++ code, implementing RAII and smart pointers, designing templates and concepts (C++20), optimizing memory layout, or building high-performance applications. Key capabilities include RAII resource management, smart pointer design (unique_ptr, shared_ptr, weak_ptr), template metaprogramming and concepts, move semantics and perfect forwarding, memory layout optimization for cache performance, constexpr and compile-time computation, multi-threading with std::thread and atomics, and CMake build system design. The expected output is safe, performant C++ code with modern idioms, proper resource management, and optimized memory access patterns. Trigger phrases: C++ code, RAII, smart pointer, template, concepts, C++20, move semantics, C++ performance, memory layout, CMake."
---

# C++ Expert

Specialized expertise in modern C++ programming, providing deep guidance on RAII, smart pointers, templates, concepts, move semantics, concurrency primitives, memory optimization, and testing with GoogleTest. Covers C++17 through C++23 features with a focus on safety, performance, and idiomatic patterns.

## When to Use This Skill

Use this skill for:

- Writing modern C++ (C++17/20/23) code
- Implementing RAII and smart pointer ownership models
- Designing templates and constraining them with concepts
- Applying move semantics and perfect forwarding
- Building concurrent and parallel applications
- Optimizing memory layout and cache performance
- Testing with GoogleTest and GMock

**Trigger phrases**: "c++", "cpp", "modern c++", "RAII", "smart pointer", "template", "concepts", "move semantics", "constexpr", "std::thread"

## What This Skill Does

Provides C++ expertise including:

- **Modern Fundamentals**: auto, structured bindings, constexpr/consteval/constinit, modules, spaceship operator
- **Ownership**: RAII, unique_ptr, shared_ptr, weak_ptr, custom deleters
- **Generic Programming**: Templates, concepts, variadic templates, fold expressions
- **Value Semantics**: Move constructors, perfect forwarding, Rule of Five/Zero
- **Concurrency**: Threads, mutexes, atomics, latches, barriers, async tasks
- **Performance**: Custom allocators, cache-friendly layouts, SoA vs AoS, PMR
- **Testing**: GoogleTest, GMock, parameterized tests, death tests, sanitizers

## Instructions

### Step 1: Master Modern C++ Fundamentals

Full walkthrough: [step-1-master-modern-c-fundamentals.md](references/step-1-master-modern-c-fundamentals.md) (load this step when you reach it).

### Step 2: Apply RAII and Smart Pointers

Full walkthrough: [step-2-apply-raii-and-smart-pointers.md](references/step-2-apply-raii-and-smart-pointers.md) (load this step when you reach it).

### Step 3: Design Templates and Concepts

Full walkthrough: [step-3-design-templates-and-concepts.md](references/step-3-design-templates-and-concepts.md) (load this step when you reach it).

### Step 4: Apply Move Semantics and Perfect Forwarding

Full walkthrough: [step-4-apply-move-semantics-and-perfect-forwarding.md](references/step-4-apply-move-semantics-and-perfect-forwarding.md) (load this step when you reach it).

### Step 5: Build Concurrent Applications

Full walkthrough: [step-5-build-concurrent-applications.md](references/step-5-build-concurrent-applications.md) (load this step when you reach it).

### Step 6: Optimize Memory and Performance

Full walkthrough: [step-6-optimize-memory-and-performance.md](references/step-6-optimize-memory-and-performance.md) (load this step when you reach it).

### Step 7: Test with GoogleTest and GMock

Full walkthrough: [step-7-test-with-googletest-and-gmock.md](references/step-7-test-with-googletest-and-gmock.md) (load this step when you reach it).

## Best Practices

- **Prefer the Rule of Zero**: let compiler-generated special members handle copying and moving by using smart pointers and standard containers as members
- **Mark move constructors and move assignment noexcept**: standard containers (such as std::vector) only use move operations during reallocation when they are noexcept
- **Use concepts over SFINAE**: concepts produce clearer error messages and are easier to read and maintain
- **Favour make_unique and make_shared**: they are exception-safe and avoid repeating the type name
- **Prefer scoped_lock over manual lock/unlock**: it locks multiple mutexes atomically and unlocks on scope exit
- **Constrain templates early**: use static_assert or concepts at the point of declaration rather than letting errors propagate into instantiation
- **Enable sanitizers in CI**: AddressSanitizer, UndefinedBehaviorSanitizer, and ThreadSanitizer catch bugs that tests alone miss
- **Profile before optimizing**: use perf, VTune, or Tracy to identify bottlenecks rather than guessing

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Raw `new`/`delete` is fine for this small object" | One early `return` or thrown exception between the `new` and the `delete` leaks the allocation; `unique_ptr` releases on every exit path. |
| "I'll add `noexcept` to move operations later" | A move constructor that can throw silently disables move semantics in `std::vector` reallocation, so the container copies instead and your "optimized" type is slower than before. |
| "Sanitizers slow the build, I'll run them before release" | ASan/UBSan catch use-after-free and signed-overflow UB that pass silently in a normal build and corrupt memory only under production load. |
| "Templates are fine without concepts" | An unconstrained template emits a 200-line error from deep inside instantiation; a `concept` fails at the call site with one readable line. |

## Verification

- [ ] No raw new/delete (use smart pointers or containers)
- [ ] Move constructors and move assignment are noexcept
- [ ] Templates are constrained with concepts
- [ ] All resources are RAII-managed
- [ ] Concurrency uses scoped_lock or unique_lock (no manual lock/unlock)
- [ ] Sanitizers (ASan, UBSan, TSan) pass cleanly
- [ ] GoogleTest suite covers edge cases and error paths
- [ ] Benchmarks exist for performance-critical paths

## Related Skills

- [[performance-testing]] -- C++ benchmarking and profiling for performance-critical paths
- [[cicd-architect]] -- C++ CI/CD with CMake and sanitizers in the pipeline
- [[code-quality]] -- static analysis and code-standard scoring of the result
- [[kubernetes-expert]] -- deploying compiled C++ services in containers

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: C++ Core Guidelines, Effective Modern C++, awesome-claude-code-subagents patterns


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
