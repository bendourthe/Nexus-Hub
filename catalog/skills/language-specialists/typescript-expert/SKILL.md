---
name: typescript-expert
description: Deep TypeScript expertise for type-safe application development. Use when writing TypeScript code, designing type systems, implementing generics, handling discriminated unions, configuring tsconfig, or building type-safe APIs and React components.
summary_l0: "Write type-safe TypeScript with generics, discriminated unions, and strict configuration"
overview_l1: "This skill provides deep TypeScript expertise for type-safe application development. Use it when writing TypeScript code, designing type systems, implementing generics, handling discriminated unions, configuring tsconfig, or building type-safe APIs and React components. Key capabilities include advanced type system design (mapped types, conditional types, template literal types), generic function and class implementation, discriminated union pattern usage, strict tsconfig configuration, type guard and assertion function writing, Zod schema integration for runtime validation, and type-safe API client design. The expected output is strictly-typed TypeScript code with proper generics, type narrowing, and compilation configuration. Trigger phrases: TypeScript code, generics, discriminated union, type guard, tsconfig, TypeScript strict, type-safe API, TypeScript React, mapped types, conditional types."
---

# TypeScript Expert

Specialized expertise in TypeScript programming, providing deep guidance on the type system, generics, discriminated unions, advanced type patterns, runtime validation, React component typing, and tooling configuration for building robust, type-safe applications.

## When to Use This Skill

Use this skill for:

- Designing type-safe data models and APIs
- Implementing generics and utility types
- Building discriminated unions with exhaustive checks
- Writing advanced type-level logic (recursive types, variadic tuples, conditional types)
- Integrating runtime validation with Zod
- Typing React components, hooks, and context
- Configuring tsconfig, path aliases, and project references

**Trigger phrases**: "typescript", "ts types", "generics", "discriminated union", "zod schema", "tsconfig", "react typescript", "type guard", "utility type"

## What This Skill Does

Provides TypeScript expertise including:

- **Type System**: Strict mode, literal types, template literals, branded types, const assertions
- **Generics**: Constraints, conditional types, mapped types, infer keyword, utility types
- **Discriminated Unions**: Tagged unions, exhaustive checks, type narrowing, type guards
- **Advanced Patterns**: Recursive types, variadic tuples, declaration merging, module augmentation
- **Runtime Validation**: Zod schemas, safeParse, transforms, refinements, inferred types
- **React Typing**: Component props, hooks, context, event handlers, polymorphic components
- **Tooling**: tsconfig strict flags, path aliases, declaration files, project references

## Instructions

### Step 1: Master Type System Fundamentals

Full walkthrough: [step-1-master-type-system-fundamentals.md](references/step-1-master-type-system-fundamentals.md) (load this step when you reach it).

### Step 2: Generics and Utility Types

Full walkthrough: [step-2-generics-and-utility-types.md](references/step-2-generics-and-utility-types.md) (load this step when you reach it).

### Step 3: Discriminated Unions and Pattern Matching

Full walkthrough: [step-3-discriminated-unions-and-pattern-matching.md](references/step-3-discriminated-unions-and-pattern-matching.md) (load this step when you reach it).

### Step 4: Advanced Type Patterns

Full walkthrough: [step-4-advanced-type-patterns.md](references/step-4-advanced-type-patterns.md) (load this step when you reach it).

### Step 5: Runtime Validation with Zod

Full walkthrough: [step-5-runtime-validation-with-zod.md](references/step-5-runtime-validation-with-zod.md) (load this step when you reach it).

### Step 6: React with TypeScript

Full walkthrough: [step-6-react-with-typescript.md](references/step-6-react-with-typescript.md) (load this step when you reach it).

### Step 7: Configuration and Tooling

Full walkthrough: [step-7-configuration-and-tooling.md](references/step-7-configuration-and-tooling.md) (load this step when you reach it).

## Best Practices

- **Enable strict mode** - Never ship a project with `strict: false`; fix the underlying type issues instead
- **Forbid any and parse I/O** - A named runtime parser, type predicate, or assertion function may accept `unknown` so it can prove a named type; do not publish `unknown`, `object`, or `Record<string, unknown>` in downstream function or alias contracts, and hand contract cleanup to [[typed-boundary-hygiene]]
- **Infer where obvious, annotate where not** - Let TypeScript infer local variables; always annotate exported function signatures
- **Prefer type aliases over interfaces for data** - Use interfaces only when you need declaration merging or extension points
- **Validate at the boundary** - Use Zod (or a similar library) where data enters your system (API routes, form submissions, storage reads)
- **Use discriminated unions over type flags** - A `kind` or `type` discriminant is safer and more ergonomic than `if (obj.isError)`
- **Branded types for domain IDs** - Prevent accidental mixing of `UserId` and `OrderId` even though both are strings
- **Keep generics simple** - If a type requires more than three generic parameters, consider restructuring

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "`any` here is faster than fighting the types" | `any` silently disables every check downstream of that value, so a renamed field or wrong shape compiles cleanly and fails at runtime in the browser. |
| "TypeScript types validate the API response" | Types are erased at compile time and provide zero runtime guarantees; an API that returns an unexpected shape needs a Zod `safeParse` at the boundary or it corrupts state. |
| "`strict` mode is too noisy, I'll enable it later" | Retrofitting `strict` onto a large untyped codebase is far more work than starting strict; without `noUncheckedIndexedAccess`, `arr[i]` is typed non-undefined and the missing-element bug ships. |
| "The exported function's return type is obvious" | An inferred return type changes silently when the implementation changes, so a refactor can widen the public contract without any diff on the signature; an explicit return type fails the build instead. |

## Verification

- [ ] `strict: true` enabled in tsconfig with `noUncheckedIndexedAccess`
- [ ] No uses of `any`; I/O boundaries use named runtime parsers, type predicates, or assertion functions to narrow `unknown`, and downstream function or alias contracts do not publish `unknown`, `object`, or `Record<string, unknown>` (audit with [[typed-boundary-hygiene]])
- [ ] All exported functions have explicit return types
- [ ] Discriminated unions use exhaustive checks (`assertNever`)
- [ ] API boundaries validated with Zod (or equivalent runtime validator)
- [ ] React components typed without `React.FC`
- [ ] Custom hooks return explicitly typed tuples or objects
- [ ] Path aliases configured in both tsconfig and bundler
- [ ] Declaration files provided for untyped dependencies

## Related Skills

- [[react-expert]] -- React architecture and patterns
- [[code-quality]] -- TypeScript code-standard scoring
- [[cicd-architect]] -- TypeScript CI/CD pipelines
- [[api-design]] -- type-safe API design
- [[typed-boundary-hygiene]] -- owns low-evidence function contracts, unsafe dictionaries, chained assertions, widen-then-assert flows, and assertion comments; this skill retains generics, discriminated unions, and Zod boundary parsing
- [[performance-testing]] -- TypeScript build optimization

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: TypeScript Handbook, Effective TypeScript, awesome-claude-code-subagents patterns


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
