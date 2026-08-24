---
name: svelte-expert
description: Deep Svelte 5 and SvelteKit expertise for runes reactivity, component patterns, server-side rendering, form actions, and deployment. Use when building Svelte applications, migrating to Svelte 5 runes, or optimizing SvelteKit projects.
summary_l0: "Build Svelte apps with runes, SvelteKit routing, server-side rendering, and form actions"
overview_l1: "This skill provides specialized Svelte 5 and SvelteKit expertise covering runes reactivity ($state, $derived, $effect, $props, $bindable), component composition with snippets, file-based routing, data loading with load functions, form actions with progressive enhancement, shared-rune and context state, hooks, performance tuning, transitions, prerendering, adapter selection, and testing with Vitest and Playwright. Use it when scaffolding SvelteKit apps, migrating from Svelte 4 stores to Svelte 5 runes, designing snippet-based components, implementing server-side data loading and form mutations, building shared rune state, configuring auth hooks, optimizing rendering, or writing component and end-to-end tests. The expected output is a well-structured SvelteKit application with fine-grained reactivity, progressive enhancement, and production-ready deployment. Trigger phrases: svelte, sveltekit, svelte 5, runes, $state, $derived, $effect, $props, svelte component, svelte routing, svelte form actions, svelte load function, svelte store, svelte hooks, svelte transition, svelte animation."
---

# Svelte Expert

Specialized expertise in Svelte 5 and SvelteKit development, providing deep guidance on the runes reactivity system, component composition with snippets, SvelteKit file-based routing, server-side data loading, form actions with progressive enhancement, state management, hooks and middleware, performance optimization, and testing with Vitest and Playwright.

## When to Use This Skill

Use this skill for:

- Building new SvelteKit applications with Svelte 5 runes
- Migrating from Svelte 4 stores to Svelte 5 runes reactivity
- Designing component architectures with snippets, two-way binding, and composition
- Implementing server-side data loading with load functions
- Building form mutations with form actions and progressive enhancement
- Managing shared state with rune-based stores and context API
- Configuring SvelteKit hooks for authentication, error handling, and request modification
- Optimizing performance with fine-grained reactivity, prerendering, and adapter selection
- Writing component tests with @testing-library/svelte and E2E tests with Playwright

**Trigger phrases**: "svelte", "sveltekit", "svelte 5", "runes", "$state", "$derived", "$effect", "$props", "svelte component", "svelte routing", "svelte form actions", "svelte load function", "svelte store", "svelte hooks", "svelte transition", "svelte animation"

## What This Skill Does

Provides Svelte 5 and SvelteKit expertise including:

- **Runes Reactivity**: $state, $derived, $effect, $props, $bindable, $inspect for fine-grained reactivity
- **Component Patterns**: Snippets, event handling, two-way binding, component composition
- **SvelteKit Routing**: File-based routing, layouts, route params, groups, error pages
- **Data Loading**: Load functions, form actions, progressive enhancement, streaming
- **State Management**: Shared rune stores, context API with getContext/setContext, derived state
- **Hooks and Middleware**: handle, handleFetch, handleError, environment variables, service workers
- **Performance**: Fine-grained reactivity, transitions, animations, lazy loading, prerendering, adapters
- **Testing**: Component testing with Vitest and @testing-library/svelte, E2E with Playwright

## Instructions

### Step 1: Master Svelte 5 Runes Fundamentals

Full walkthrough: [step-1-master-svelte-5-runes-fundamentals.md](references/step-1-master-svelte-5-runes-fundamentals.md) (load this step when you reach it).

### Step 2: Build Component Patterns

Full walkthrough: [step-2-build-component-patterns.md](references/step-2-build-component-patterns.md) (load this step when you reach it).

### Step 3: Structure SvelteKit Routing

Full walkthrough: [step-3-structure-sveltekit-routing.md](references/step-3-structure-sveltekit-routing.md) (load this step when you reach it).

### Step 4: Implement Data Loading and Form Actions

Full walkthrough: [step-4-implement-data-loading-and-form-actions.md](references/step-4-implement-data-loading-and-form-actions.md) (load this step when you reach it).

### Step 5: Manage State

Full walkthrough: [step-5-manage-state.md](references/step-5-manage-state.md) (load this step when you reach it).

### Step 6: Configure SvelteKit Hooks and Middleware

Full walkthrough: [step-6-configure-sveltekit-hooks-and-middleware.md](references/step-6-configure-sveltekit-hooks-and-middleware.md) (load this step when you reach it).

### Step 7: Optimize Performance

Full walkthrough: [step-7-optimize-performance.md](references/step-7-optimize-performance.md) (load this step when you reach it).

### Step 8: Test with Vitest and Playwright

Full walkthrough: [step-8-test-with-vitest-and-playwright.md](references/step-8-test-with-vitest-and-playwright.md) (load this step when you reach it).

## Best Practices

- **Use runes, not stores**: Svelte 5 runes ($state, $derived, $effect) replace writable/readable/derived stores with simpler, more performant primitives
- **Prefer $derived over $effect for computed values**: $effect is for side effects (fetches, DOM manipulation, logging); $derived is for transformations
- **Use progressive enhancement**: SvelteKit forms work without JavaScript by default; add `use:enhance` for a smoother UX, not as a requirement
- **Colocate data loading with routes**: each +page.server.ts loads only the data its +page.svelte needs
- **Stream slow data**: return promises from load functions and use `{#await}` blocks so the page renders immediately
- **Choose the right adapter**: adapter-auto for most deployments; adapter-node for self-hosted; adapter-static for fully prerendered sites
- **Keep components small**: extract logic into .svelte.ts modules and rendering into child components
- **Type your props with interfaces**: use the Props interface pattern with $props() for full TypeScript safety

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will compute the derived value inside an $effect that assigns to $state." | Using $effect to derive state creates an extra render pass and an easy infinite-loop trap when the effect's write feeds its own dependency. $derived computes synchronously without re-running the component; that is what it is for. |
| "Svelte 4 stores still work, so I will keep using them in this Svelte 5 project." | Mixing store reactivity with runes fragments the reactivity model and forfeits the fine-grained updates Svelte 5 provides. Worse, the two paradigms interact subtly and produce updates that fire in the wrong order. Migrate to $state and shared runes. |
| "The form posts to a server action, so I do not need to re-validate the input there." | Form actions are public endpoints reachable without `use:enhance`; a direct POST bypasses any client-side checks entirely. Validate with Zod and return `fail()` in the action, or unvalidated data hits your mutation. |

## Verification

- [ ] All reactive state uses $state (not Svelte 4 stores or let-assignment reactivity)
- [ ] Computed values use $derived, not $effect with assignment
- [ ] $effect cleanup functions handle abort controllers and timers
- [ ] Components use $props() with typed interfaces
- [ ] Snippets replace all slot usage (Svelte 5 pattern)
- [ ] Load functions validate params and return typed data
- [ ] Form actions validate input with Zod and return fail() on error
- [ ] Forms use use:enhance for progressive enhancement
- [ ] hooks.server.ts applies auth checks and security headers
- [ ] Private env variables are never imported in client code
- [ ] Transitions use easing functions for smooth motion
- [ ] Prerender is configured for static pages
- [ ] Component tests use @testing-library/svelte with accessible queries
- [ ] E2E tests cover critical user flows (auth, form submission, navigation)
- [ ] Vitest coverage meets 80% line threshold

## Related Skills

- [[react-expert]] - React component architecture and hooks (for comparison)
- [[nextjs-expert]] - Next.js App Router patterns (SvelteKit equivalent concepts)
- [[typescript-expert]] - Advanced TypeScript for typed components and stores
- [[unit-tests]] - General unit testing strategies
- [[e2e-testing-automation]] - End-to-end testing patterns with Playwright

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
