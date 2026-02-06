# SOLID Principles & Architecture Smell Checklist

Reference checklist for SOLID principle violations, architecture smells, and refactoring guidance. Used by the `code-quality` skill during Phase 2 of code review.

---

## SOLID Diagnostic Questions

### Single Responsibility Principle (SRP)

**Diagnostic**: "What is the single reason this module would change?"

| Smell | Indicator |
|-------|-----------|
| God object/module | Class or module handles 3+ unrelated concerns |
| Low cohesion | Methods within a class rarely use the same fields |
| Unrelated imports | File imports from vastly different domains |
| Mixed abstraction levels | Business logic interleaved with I/O or presentation |

**When proposing a split**: Explain *why* it improves cohesion. Outline a minimal, safe split rather than a large rewrite.

### Open/Closed Principle (OCP)

**Diagnostic**: "Can I add a new variant without touching existing code?"

| Smell | Indicator |
|-------|-----------|
| Switch/if chains | Frequent edits to add new behavior via conditionals |
| No extension points | Every new feature requires modifying core logic |
| Hard-coded strategies | Algorithm selection baked into business logic |

### Liskov Substitution Principle (LSP)

**Diagnostic**: "Can I substitute any subclass without the caller knowing?"

| Smell | Indicator |
|-------|-----------|
| Type checks on subtypes | `instanceof` or `typeof` checks for concrete classes |
| Weakened preconditions | Subclass accepts wider input than parent contract |
| No-op overrides | Subclass methods that do nothing or throw "not supported" |
| Strengthened postconditions | Subclass returns narrower output unexpectedly |

### Interface Segregation Principle (ISP)

**Diagnostic**: "Do all implementers use all methods?"

| Smell | Indicator |
|-------|-----------|
| Fat interfaces | Interface with 5+ methods where most implementers stub half |
| Unused method implementations | `pass`, `throw NotImplemented`, or empty bodies |
| Forced dependencies | Implementers pulling in packages they don't need |

### Dependency Inversion Principle (DIP)

**Diagnostic**: "Can I swap the implementation without changing business logic?"

| Smell | Indicator |
|-------|-----------|
| Hard-coded implementations | Business logic directly instantiates infrastructure classes |
| Import chains | High-level modules importing from low-level modules |
| No abstraction boundary | Database, HTTP, or filesystem calls scattered through business logic |

---

## Common Code Smells (Beyond SOLID)

| Smell | Threshold | Impact |
|-------|-----------|--------|
| **Long Method** | >30 lines | Hard to understand, test, and maintain |
| **Large Class** | >500 lines | Low cohesion, multiple responsibilities |
| **Feature Envy** | Method uses another class's data more than its own | Misplaced responsibility |
| **Data Clumps** | Same group of fields/parameters appear together repeatedly | Missing abstraction |
| **Primitive Obsession** | Using primitives instead of small domain objects | Weak type safety, scattered validation |
| **Shotgun Surgery** | One change requires edits in many unrelated files | High coupling |
| **Divergent Change** | One module changes for multiple unrelated reasons | Multiple responsibilities |
| **Dead Code** | Unreachable functions, unused variables/imports | Maintenance burden, confusion |
| **Speculative Generality** | Abstractions/hooks for features that don't exist | Unnecessary complexity |
| **Magic Numbers/Strings** | Unexplained literal values in logic | Readability, error-prone |
| **Duplicate Code** | Copy-paste patterns across files | Inconsistent fixes, maintenance debt |
| **Deep Nesting** | >3 levels of indentation | Cognitive complexity, hard to follow |

---

## 7 Refactor Heuristics

1. **Split by responsibility, not by size**: A 100-line class with one clear purpose is better than three 30-line classes with tangled dependencies.
2. **Introduce abstraction only when needed**: Wait for the second use case before extracting a generic interface.
3. **Keep refactors incremental**: Prefer small, safe steps over large rewrites. Each step should leave the code in a working state.
4. **Preserve behavior first**: Add tests before restructuring. Verify the refactored code produces identical outputs.
5. **Name things by intent**: Rename to communicate purpose, not implementation. `calculateMonthlyRevenue()` not `doCalc()`.
6. **Prefer composition over inheritance**: Favor delegating behavior via composition. Reserve inheritance for true "is-a" relationships.
7. **Make illegal states unrepresentable**: Use types, enums, and structures that prevent invalid combinations at compile time rather than validating at runtime.

---

## Usage

When reviewing code quality, work through each SOLID principle using its diagnostic question. For each violation found:

1. State the principle violated
2. Quote the specific code location
3. Explain the concrete impact (not theoretical)
4. Propose an incremental fix with a rationale for *why* it improves cohesion/coupling
5. Classify severity: P0 (blocking) through P3 (optional)
