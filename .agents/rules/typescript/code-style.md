---
title: TypeScript Code Style
category: typescript
priority: high
---

# TypeScript Code Style Rules

## Compiler Configuration

- Enable `strict: true` in `tsconfig.json`. Never disable individual strict flags without a comment justifying why.
- Enable `noUncheckedIndexedAccess: true` to prevent silent `undefined` from array/object indexing.
- Use `"moduleResolution": "bundler"` (or `"node16"`) for modern projects; avoid legacy `"node"` resolution.
- Set `"target"` to the minimum runtime version your deployment supports. Do not over-transpile.

## Types and Interfaces

- Prefer `type` aliases for data shapes and unions. Use `interface` only for extension points or when declaration merging is intentional.
- Never use `any`. Use `unknown` for truly unknown values and narrow with type guards.
- Prefer `readonly` on object properties and array types that should not be mutated.
- Use template literal types for string unions where values follow a pattern (e.g., `type EventName = \`on\${string}\``).
- Avoid type assertions (`as Type`) except at well-defined boundaries (e.g., API response parsing); document each one.

## Functions and Components

- Always declare return types explicitly on exported functions; infer on private helpers where obvious.
- Avoid `React.FC` -- use function declarations with explicit prop types: `function Foo({ bar }: FooProps)`.
- Extract complex conditional rendering into named helper functions or sub-components.
- Keep React components under 150 lines. Extract hooks for stateful logic.

## Naming Conventions

- Variables, functions, parameters: `camelCase`
- Types, interfaces, classes, components: `PascalCase`
- Constants (module-level, never reassigned): `UPPER_SNAKE_CASE`
- Private class members: `_name` prefix (TypeScript `private` alone is insufficient at runtime)
- Boolean variables: prefix with `is`, `has`, `can`, `should` (e.g., `isLoading`, `hasError`)

## Null Safety

- Prefer optional chaining `?.` and nullish coalescing `??` over manual `null`/`undefined` checks.
- Initialize all class properties in the constructor or with a definite assignment assertion (`!`) only when the initializer is genuinely deferred.
- Never return `null` from functions that could return `undefined` -- be consistent within a project.
