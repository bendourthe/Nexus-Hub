---
name: vue-expert
description: Deep Vue 3 expertise for Composition API, component patterns, Pinia state management, Vue Router, performance optimization, and testing. Use when building Vue applications, designing composables, or reviewing Vue code.
summary_l0: "Build Vue 3 apps with Composition API, Pinia, Vue Router, and optimization"
overview_l1: "This skill provides specialized Vue 3 expertise covering Composition API fundamentals, component architecture with SFC and TypeScript, composable design for reusable logic, Pinia state management, Vue Router patterns, performance optimization, testing with Vitest and Vue Test Utils, and advanced TypeScript integration. Use it when designing Vue component architectures (SFC, slots, provide/inject), writing composables, managing state with Pinia, configuring Vue Router (guards, lazy loading, nested routes), optimizing rendering (shallowRef, v-memo, KeepAlive, async components), testing components and composables, or integrating TypeScript with typed props, emits, and generic components. The expected output is well-architected Vue 3 code with proper component boundaries, type-safe props and emits, optimized rendering, comprehensive tests, and idiomatic Composition API usage. Trigger phrases: vue component, vue composable, composition api, ref reactive, pinia store, vue router, vue performance, vue testing, vue typescript, defineProps, defineEmits, provide inject, v-model, shallowRef, keepalive, vue test utils."
---

# Vue Expert

Specialized expertise in Vue 3 development, providing deep guidance on Composition API fundamentals, Single File Component architecture, composable design, Pinia state management, Vue Router patterns, performance optimization, testing with Vitest and Vue Test Utils, and advanced TypeScript integration.

## When to Use This Skill

Use this skill for:

- Building Vue 3 applications with the Composition API (ref, reactive, computed, watch)
- Designing Single File Components with typed props, emits, slots, and v-model
- Extracting reusable logic into composables (useAsync, useFetch, useForm)
- Managing application state with Pinia (stores, getters, actions, plugins)
- Configuring Vue Router with guards, lazy loading, nested routes, and meta fields
- Optimizing rendering performance (shallowRef, v-once, v-memo, KeepAlive, async components)
- Testing components and composables with Vitest and Vue Test Utils
- Integrating TypeScript with generic components, typed slots, and module augmentation

**Trigger phrases**: "vue component", "vue composable", "composition api", "ref reactive", "pinia store", "vue router", "vue performance", "vue testing", "vue typescript", "defineProps", "defineEmits", "provide inject", "v-model", "shallowRef", "keepalive", "vue test utils"

## What This Skill Does

Provides Vue 3 expertise including:

- **Composition API**: ref, reactive, computed, watch, watchEffect, lifecycle hooks
- **Component Patterns**: SFC structure, props/emits with TypeScript, slots, provide/inject, v-model
- **Composables**: Custom composable design, async patterns, shared state, dependency injection
- **State Management**: Pinia stores, getters, actions, plugins, SSR hydration, devtools
- **Routing**: Vue Router guards, lazy loading, nested routes, navigation, typed meta fields
- **Performance**: shallowRef, v-once, v-memo, KeepAlive, async components, virtual scrolling
- **Testing**: Vitest, Vue Test Utils, component mounting, composable testing, router/store mocking
- **TypeScript**: Typed props, typed emits, generic components, typed slots, global property augmentation

## Instructions

### Step 1: Master Composition API Fundamentals

Full walkthrough: [step-1-master-composition-api-fundamentals.md](references/step-1-master-composition-api-fundamentals.md) (load this step when you reach it).

### Step 2: Design Component Patterns

Full walkthrough: [step-2-design-component-patterns.md](references/step-2-design-component-patterns.md) (load this step when you reach it).

### Step 3: Build Composables for Reusable Logic

Full walkthrough: [step-3-build-composables-for-reusable-logic.md](references/step-3-build-composables-for-reusable-logic.md) (load this step when you reach it).

### Step 4: Manage State with Pinia

Full walkthrough: [step-4-manage-state-with-pinia.md](references/step-4-manage-state-with-pinia.md) (load this step when you reach it).

### Step 5: Configure Vue Router Patterns

Full walkthrough: [step-5-configure-vue-router-patterns.md](references/step-5-configure-vue-router-patterns.md) (load this step when you reach it).

### Step 6: Optimize Performance

Full walkthrough: [step-6-optimize-performance.md](references/step-6-optimize-performance.md) (load this step when you reach it).

### Step 7: Test with Vitest and Vue Test Utils

Full walkthrough: [step-7-test-with-vitest-and-vue-test-utils.md](references/step-7-test-with-vitest-and-vue-test-utils.md) (load this step when you reach it).

### Step 8: Integrate TypeScript Deeply

Full walkthrough: [step-8-integrate-typescript-deeply.md](references/step-8-integrate-typescript-deeply.md) (load this step when you reach it).

## Best Practices

- **Use Composition API for all new components** (Options API is supported but Composition API is the standard for Vue 3)
- **Extract composables when logic is reused** across two or more components
- **Prefer ref over reactive** for top-level state (ref works with primitives and is easier to destructure)
- **Always type defineProps and defineEmits** using the type-only syntax for compile-time safety
- **Use shallowRef for large collections** that are replaced rather than mutated in place
- **Keep components under 200 lines** of script; extract composables or child components when complexity grows
- **Colocate tests with source files** (ComponentName.vue and ComponentName.test.ts in the same directory)
- **Use provide/inject with InjectionKey** for type-safe dependency injection across component trees

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will destructure the props or a reactive object to make the template cleaner." | Destructuring a reactive source severs Vue's reactivity tracking, so the value freezes at its initial state and the UI silently stops updating. Keep the ref/reactive intact or use `toRefs`; cleaner syntax is not worth a dead binding. |
| "Plain `ref` is fine for this large list; reactivity is reactivity." | Deep reactivity on a large array makes Vue track every nested property, and the render cost scales with list size. `shallowRef` plus `v-memo` (or virtual scrolling) is what keeps a big list responsive. |
| "I will type props with a loose object instead of an InjectionKey for provide/inject." | Untyped provide/inject defers a missing-provider mismatch to a runtime `undefined` deep in a child component. A typed `InjectionKey` turns that into a compile-time error at the injection site. |

## Verification

- [ ] All components use `<script setup lang="ts">` with typed props and emits
- [ ] Composables follow the `use` prefix convention and return reactive state
- [ ] Pinia stores use the Setup Store syntax with typed state, getters, and actions
- [ ] Route guards check authentication and authorization with typed meta fields
- [ ] Large lists use shallowRef, v-memo, or virtual scrolling for performance
- [ ] Components are tested with Vue Test Utils and Vitest
- [ ] Composables are tested in isolation without mounting components
- [ ] Global types are augmented for router meta, global properties, and components
- [ ] Side effects use watch/watchEffect with proper cleanup via onCleanup
- [ ] v-model bindings use defineModel for clean two-way data flow
- [ ] Provide/inject uses typed InjectionKey for compile-time safety
- [ ] Async components use defineAsyncComponent with loading and error fallbacks

## Related Skills

- [[nextjs-expert]] - SSR framework patterns applicable to Nuxt (Vue's SSR framework)
- [[javascript-cleanup]] - JavaScript code quality and cleanup
- [[typescript-expert]] - Advanced TypeScript patterns and strict configuration
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
