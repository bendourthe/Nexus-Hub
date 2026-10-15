---
name: react-expert
description: Deep React expertise for component architecture, hooks, state management, performance optimization, and testing. Use when building React applications, optimizing rendering, or reviewing React code.
summary_l0: "Build React apps with component architecture, hooks, state management, and optimization"
overview_l1: "This skill provides specialized React expertise covering component architecture patterns, hooks design, state management strategies, performance optimization, testing, TypeScript integration, accessibility, and React 19 features. Use it when designing component architectures (composition, compound, render props), writing custom hooks, choosing state management (Context, Zustand, Redux Toolkit, Jotai), optimizing rendering (memoization, code splitting, Suspense), testing with React Testing Library and MSW, integrating TypeScript, building accessible UI with ARIA patterns, implementing error boundaries, or adopting React 19 features (Actions, use hook, Server Components). Key capabilities include component pattern selection, hook composition, state architecture design, render performance optimization, testing strategy implementation, TypeScript generics for components, and accessibility compliance. The expected output is well-architected React code with proper component boundaries, optimized rendering, comprehensive tests, and accessibility support. Trigger phrases: react component, react hooks, useEffect, useState, react performance, react testing, react typescript, react accessibility, zustand, redux toolkit, react memo, suspense, server components."
---

# React Expert

Specialized expertise in React development, providing deep guidance on component architecture patterns, hooks design, state management strategies, performance optimization, testing with React Testing Library, TypeScript integration, accessibility, and React 19 features.

## When to Use This Skill

Use this skill for:

- Designing component architectures (composition, compound, render props)
- Writing and composing custom hooks
- Choosing and implementing state management (Context, Zustand, Redux Toolkit, Jotai)
- Optimizing rendering performance (memoization, code splitting, Suspense)
- Testing components with React Testing Library and MSW
- Integrating TypeScript with React patterns
- Building accessible UI with ARIA patterns and keyboard navigation
- Implementing error boundaries and recovery strategies
- Adopting React 19 features (Actions, use hook, Server Components)

**Trigger phrases**: "react component", "react hooks", "useEffect", "useState", "react performance", "react testing", "react typescript", "react accessibility", "zustand", "redux toolkit", "react memo", "suspense", "server components"

## What This Skill Does

Provides React expertise including:

- **Component Patterns**: Composition, compound components, render props, HOCs
- **Hooks**: Built-in hooks, custom hook design, rules and pitfalls
- **State Management**: Context API, Zustand, Redux Toolkit, Jotai
- **Performance**: React.memo, useMemo, useCallback, lazy loading, Suspense, concurrent features
- **Testing**: React Testing Library, user-event, MSW for network mocking
- **TypeScript**: Typed props, generic components, discriminated unions
- **Accessibility**: ARIA roles, keyboard navigation, focus management
- **Error Handling**: Error boundaries, recovery patterns
- **React 19**: Actions, use hook, optimistic updates, document metadata

## Instructions

### Step 1: Design Component Architecture

Full walkthrough: [step-1-design-component-architecture.md](references/step-1-design-component-architecture.md) (load this step when you reach it).

### Step 2: Master Hooks Patterns

Full walkthrough: [step-2-master-hooks-patterns.md](references/step-2-master-hooks-patterns.md) (load this step when you reach it).

### Step 3: Implement State Management

Full walkthrough: [step-3-implement-state-management.md](references/step-3-implement-state-management.md) (load this step when you reach it).

### Step 4: Optimize Performance

Full walkthrough: [step-4-optimize-performance.md](references/step-4-optimize-performance.md) (load this step when you reach it).

### Step 5: Test with React Testing Library

Full walkthrough: [step-5-test-with-react-testing-library.md](references/step-5-test-with-react-testing-library.md) (load this step when you reach it).

### Step 6: Integrate TypeScript

Full walkthrough: [step-6-integrate-typescript.md](references/step-6-integrate-typescript.md) (load this step when you reach it).

### Step 7: Implement Accessibility

Full walkthrough: [step-7-implement-accessibility.md](references/step-7-implement-accessibility.md) (load this step when you reach it).

### Step 8: Error Boundaries

Full walkthrough: [step-8-error-boundaries.md](references/step-8-error-boundaries.md) (load this step when you reach it).

### Step 9: React 19 Features

Full walkthrough: [step-9-react-19-features.md](references/step-9-react-19-features.md) (load this step when you reach it).

## Best Practices

- **Lift state up only as far as necessary** (keep state close to where it is used)
- **Prefer composition over prop drilling** (use children or render props)
- **Memoize expensive computations, not everything** (profile before optimizing)
- **Always clean up side effects** in useEffect return functions
- **Use keys correctly**: stable, unique identifiers (never array indices for dynamic lists)
- **Test user behavior, not implementation**: query by role/label, not test-ids
- **Split contexts by update frequency** to avoid unnecessary re-renders
- **Co-locate related code**: keep component, styles, tests, and types together

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will memoize everything with `useMemo`/`React.memo` to be safe." | Memoizing without profiling adds comparison overhead and dependency-array bugs that cost more than the re-render they prevent. Memoize only where the profiler shows a measurable render cost; premature memoization is a documented anti-pattern. |
| "The list uses the array index as the key; it renders fine." | Index keys break the moment the list reorders, filters, or inserts: React reuses the wrong DOM node and component state attaches to the wrong item, producing stale inputs and lost focus. Use a stable unique id. |
| "I will omit a value from the useEffect dependency array to stop it re-running." | A deliberately incomplete dependency array means the effect closes over stale state and silently uses old values. The fix is to restructure the effect (or use a ref), not to lie to the linter. |

## Verification

- [ ] Components follow single-responsibility principle
- [ ] Custom hooks extract reusable stateful logic
- [ ] useEffect dependencies are complete and correct
- [ ] Side effects are cleaned up on unmount
- [ ] Lists use stable, unique keys (not array indices)
- [ ] Expensive renders are memoized with profiling evidence
- [ ] Tests query by accessible role/label, not test-id
- [ ] Error boundaries wrap critical UI sections
- [ ] Keyboard navigation and ARIA attributes are present
- [ ] TypeScript strict mode enabled, no `any` escape hatches
- [ ] Bundle size is audited; heavy dependencies are lazy loaded
- [ ] No prop drilling beyond two levels (use context or composition)

## References

- `references/performance-patterns.md` - quick-lookup guide for React rendering optimization patterns, including memoization decision matrices.
- `references/testing-recipes.md` - quick-lookup guide for common React testing patterns with React Testing Library, Vitest, and MSW.

## Related Skills

- [[nextjs-expert]] - React framework with SSR, routing, and server components
- [[javascript-cleanup]] - JavaScript code quality and cleanup
- [[unit-tests]] - General unit testing strategies
- [[performance-review]] - Broad performance review methodology
- [[test-cases]] - Test case design patterns

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
