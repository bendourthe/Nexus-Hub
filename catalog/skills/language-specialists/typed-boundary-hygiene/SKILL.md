---
name: typed-boundary-hygiene
description: Audit and rewrite low-evidence TypeScript and JavaScript contracts. Use for "low-evidence TypeScript", "chained type assertion", "as unknown as", "Record<string, unknown>", "unknown parameter", "unknown return", "SAFETY comment for assertion", "vi.mock", or "conditional empty object spread", including unsafe dictionaries, object parameters, Reflect access, and widen-then-assert code. SKIP - prose or voice slop (anti-slop-editing), ESLint dead-code cleanup (javascript-cleanup), type-system design, generics, or Zod schemas (typescript-expert), and Effect service constructors.
summary_l0: "Replace low-evidence TypeScript contracts with named, checked types"
overview_l1: "Run a bounded audit over the TypeScript or JavaScript files being edited. Find chained assertions, unknown or object function contracts, unsafe dictionaries, widen-then-assert flows, assertion comments, conditional empty spreads, Reflect access, and module mocks. For each finding, establish the real invariant, replace the weak contract with a named type or testable seam, and require a SAFETY comment on any remaining non-const assertion. This skill owns contract hygiene and assertion evidence; typescript-expert owns generics, discriminated unions, and parsing unknown I/O with Zod. Trigger phrases: low-evidence TypeScript, as unknown as, Record<string unknown>, unknown parameter, unknown return, SAFETY comment, vi.mock, conditional empty object spread."
version: 1.0.0
author: Benjamin Dourthe
category: language-specialists
tags:
  - typescript
  - javascript
  - type-safety
  - contracts
  - assertions
---

# Typed Boundary Hygiene

Replace types that merely silence the compiler with contracts justified by runtime evidence or by a named internal invariant. Run this procedure on the TypeScript or JavaScript files in scope; it is a source-editing runbook, not a type-system tutorial.

## When to Use This Skill

Use when:

- A TypeScript change contains `as unknown as`, chained assertions, or widen-then-assert flows.
- A function or type alias publishes `unknown`, `object`, or `Record<string, unknown | any | object>` as its downstream contract rather than narrowing unknown input at a named runtime parser, type predicate, or assertion-function entrypoint.
- A non-const assertion lacks a `SAFETY:` comment naming the checked invariant.
- Tests use `vi.mock` or `jest.mock` where a real dependency seam can be injected.
- Code uses conditional empty object spreads, `Reflect.get`, `Reflect.apply`, or repeated ad hoc `typeof` checks.

**When NOT to use:**

- Prose, tone, or voice cleanup belongs to [[anti-slop-editing]].
- ESLint fixes, unused code, and ES6+ modernization belong to [[javascript-cleanup]].
- Generics, discriminated unions, branded types, Zod schema design, and parsing data that entered as unknown at I/O belong to [[typescript-expert]].
- Effect service constructors are outside this skill's contract.

## Rule Ownership

| Concern | Owning skill | Handoff |
|---|---|---|
| Function-contract `unknown` / `object` / unsafe dictionaries | `typed-boundary-hygiene` | Replace low-evidence downstream contracts with named types; hand runtime parser, type predicate, and assertion-function entrypoints to `typescript-expert`. |
| Chained assertions, widen-then-assert, and assertion comments | `typed-boundary-hygiene` | Establish the invariant and remove or justify the assertion. |
| Type-system design, generics, and discriminated unions | `typescript-expert` | Design the named types this runbook consumes. |
| Boundary parsing of unknown I/O with Zod or `safeParse` | `typescript-expert` | Parse external input into a named type before this runbook evaluates downstream contracts. |
| ESLint, dead code, and ES6+ modernization | `javascript-cleanup` | Clean syntax and unused code without restating this pattern catalog. |
| Prose and voice | `anti-slop-editing` | Edit human-facing language only. |

## Instructions

### 1. Bound the audit

List the TypeScript and JavaScript files changed by the current task. Search only that scope first:

```bash
rg -n "as unknown as|Record<string, *(unknown|any|object)>|:\s*(unknown|object)\b|vi\.mock|jest\.mock|Reflect\.(get|apply)" <changed-files>
```

Also inspect `as` assertions, conditional spreads, exported function signatures, and type aliases. Do not expand to a repository-wide cleanup unless the user placed the whole repository in scope.

For each match, write down the invariant the code assumes. If no runtime check, construction path, or trusted library contract proves it, treat the type as low evidence.

### 2. Remove chained assertions

**Smell:** a value crosses two unrelated types through `unknown`.

Rejected:

```ts
const user = payload as unknown as User;
```

Preferred at I/O: hand the boundary to [[typescript-expert]] and parse into `User`. Preferred after a trusted construction path: keep one assertion only when the code checks the invariant, and document that check:

```ts
assertUserShape(payload);
// SAFETY: assertUserShape verifies every required User field before this cast.
const user = payload as User;
```

Delete the assertion entirely when control flow already narrows the value.

### 3. Replace conditional empty object spreads

**Smell:** an empty object exists only to make a conditional spread type-check.

Rejected:

```ts
const options = { ...base, ...(enabled ? { cache: true } : {}) };
```

Preferred: construct the named contract with explicit control flow so the optional field's presence is visible.

```ts
const options: RequestOptions = { ...base };
if (enabled) {
  options.cache = true;
}
```

Keep a conditional spread only when its output type is already exact and it is clearer than the branch; the empty object must not be the thing persuading the compiler.

### 4. Preserve known-value narrowness

**Smell:** a known literal is widened and later asserted back to a union.

Rejected:

```ts
const state: string = "ready";
start(state as JobState);
```

Preferred:

```ts
const state = "ready" satisfies JobState;
start(state);
```

Use `as const` for immutable literal objects and tuples. Use `satisfies` when the value must be checked against a broader contract without losing its narrow inferred type.

### 5. Replace module mocks with real seams

**Smell:** `vi.mock` or `jest.mock` replaces an entire module to reach one dependency.

Rejected:

```ts
vi.mock("./clock", () => ({ now: () => 0 }));
```

Preferred: inject the capability the unit actually needs.

```ts
export type Clock = { now(): number };

export function createSession(clock: Clock) {
  return { createdAt: clock.now() };
}
```

Keep a module mock only when the module boundary itself is the behavior under test. State that reason in the test.

### 6. Replace `object` parameters with named shapes

**Smell:** a function accepts `object`, which proves only that the value is non-primitive.

Rejected:

```ts
function render(config: object): string;
```

Preferred:

```ts
type RenderConfig = {
  theme: "light" | "dark";
  compact?: boolean;
};

function render(config: RenderConfig): string;
```

If the input arrived from I/O, parse it first. Do not move `unknown` from the boundary into the function contract.

### 7. Remove reflective access when the key is knowable

**Smell:** `Reflect.get` or `Reflect.apply` avoids expressing a property or callable contract.

Rejected:

```ts
const id = Reflect.get(value, "id") as string;
```

Preferred:

```ts
type Identified = { id: string };
const id = value.id;
```

Use reflection only for genuinely dynamic metaprogramming. Wrap that operation behind a typed helper, validate the dynamic key or callable, and apply the assertion-comment rule.

### 8. Centralize repeated ad hoc narrowing

**Smell:** several call sites repeat `typeof` checks and then assert the same shape.

Rejected:

```ts
if (typeof value === "object" && value !== null) {
  consume(value as Settings);
}
```

Preferred: put the checks in a named type predicate or assertion function.

```ts
function isSettings(value: unknown): value is Settings {
  return typeof value === "object" && value !== null && "mode" in value;
}

if (isSettings(value)) {
  consume(value);
}
```

An ad hoc `typeof` check is allowed inside the predicate. A named runtime parser, type predicate, or assertion-function entrypoint may accept `unknown` because its job is to narrow that value before returning it downstream. Add property checks sufficient for the named type; `typeof value === "object"` alone is not proof.

### 9. Replace `unknown` contracts and unsafe dictionaries

**Smell:** a parameter, return type, or alias exposes uncertainty that the caller or callee must rediscover.

Rejected:

```ts
type Metadata = Record<string, unknown>;
function normalize(input: unknown): unknown;
```

Preferred:

```ts
type Metadata = {
  requestId: string;
  retryCount?: number;
};

function normalize(input: RawRecord): NormalizedRecord;
```

Use a named interface, discriminated union, `Map<K, V>`, or generic constraint that states the keys and values actually supported. Explicit exceptions are `cause?: unknown` on an error, because JavaScript permits any thrown value, and named runtime parser, type predicate, or assertion-function entrypoints that narrow unknown input before returning a named type.

### 10. Eliminate widen-then-assert flows

**Smell:** a value is widened for storage or composition, then asserted back at the call site.

Rejected:

```ts
const handlers: Record<string, unknown> = buildHandlers();
register(handlers as HandlerMap);
```

Preferred:

```ts
const handlers = buildHandlers() satisfies HandlerMap;
register(handlers);
```

If heterogeneous storage is required, model the variants with a discriminated union owned by [[typescript-expert]] rather than erasing them into a dictionary.

### 11. Justify every remaining assertion

Every non-`as const` assertion that remains after the prior steps must have an adjacent `SAFETY:` comment naming the checked invariant and where it was checked.

Rejected:

```ts
return node as ElementNode;
```

Preferred:

```ts
// SAFETY: isElementNode checked the discriminant and required attributes above.
return node as ElementNode;
```

Comments such as `SAFETY: TypeScript cannot infer this` are not evidence. If the invariant cannot be named, remove the assertion or add the missing check.

### 12. Re-run the type and test gates

Run the repository's TypeScript compiler, lint command, and focused tests for the changed files. Re-run the search from Step 1 and inspect every remaining match. Record each retained match with its owning invariant; do not suppress a finding with a lint-disable comment.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "`unknown` is the safe replacement for `any` everywhere" | `unknown` is appropriate at an unparsed I/O boundary, but publishing it as a function or alias contract transfers missing knowledge to every consumer and recreates assertions downstream. |
| "The double assertion is safe because both types are structural" | `as unknown as` deliberately bypasses structural compatibility, so the compiler has proved nothing. A renamed or missing field reaches runtime unchecked. |
| "A `SAFETY:` comment is just ceremony" | The comment forces the checked invariant to be named. If the author cannot name it, the assertion is concealing a missing check rather than documenting a compiler limitation. |
| "Module mocking is faster than adding a seam" | Whole-module mocks couple tests to import mechanics and can pass while the real dependency contract drifts. A small injected capability keeps the unit and its test on the same contract. |
| "`Record<string, unknown>` keeps the API flexible" | It promises every string key and no usable value type, so callers must guess supported keys and cast values. A named shape or typed map preserves actual flexibility without erasing the contract. |
| "Reflection handles private or dynamic properties cleanly" | Reflection moves the property contract from the type checker into a string and an assertion. Keep it only for real metaprogramming behind one validated helper. |
| "The assertion is obvious from nearby code" | Refactors separate assumptions from the checks that justified them. An adjacent `SAFETY:` comment names the invariant and its proof location so drift is reviewable. |

## Verification

- [ ] The audit is bounded to the TypeScript or JavaScript files in the task's scope.
- [ ] No unexplained `as unknown as` or other chained assertion remains in the changed files.
- [ ] No changed downstream function or type alias publishes `unknown`, `object`, or `Record<string, unknown | any | object>` except the documented error-`cause` convention; named runtime parsers, type predicates, and assertion functions may accept `unknown` only when they prove a named type before return.
- [ ] Every remaining non-`as const` assertion has an adjacent `SAFETY:` comment naming the checked invariant.
- [ ] Known literals stay narrow through `satisfies` or `as const` rather than widen-then-assert.
- [ ] Each retained module mock tests the module boundary itself or has been replaced with an injected seam.
- [ ] Reflective access is isolated behind a validated typed helper when it cannot be removed.
- [ ] The repository TypeScript compiler, linter, and focused tests pass.
- [ ] `rg -n "as unknown as|Record<string, *(unknown|any|object)>|:\s*(unknown|object)\b|vi\.mock|jest\.mock|Reflect\.(get|apply)" <changed-files>` has no unexplained match.

## Related Skills

- [[typescript-expert]] -- owns type-system design, generics, discriminated unions, branded types, and parsing unknown I/O into named types.
- [[javascript-cleanup]] -- owns ESLint fixes, dead code, and ES6+ modernization; it hands low-evidence contracts to this skill.
- [[anti-slop-editing]] -- owns prose and voice cleanup; it does not handle TypeScript contract quality.
- [[code-quality]] -- evaluates broader maintainability after the typed-boundary findings are resolved.

---

**Version**: 1.0.0
**Last Updated**: August 2026
