---
name: frontend-ui-engineering
description: Implements production-quality frontend UIs with accessible components, responsive layout, and maintainable state management. Use when building new UI features, implementing designs, or reviewing frontend code for quality and accessibility. Covers all frontend stacks (React, Vue, Svelte, vanilla) — not framework-specific. Trigger phrases: build this UI, implement this design, frontend component, responsive layout, accessible UI, frontend implementation.
summary_l0: "Build accessible, responsive frontend UIs with clean component architecture and maintainable state"
overview_l1: "This skill guides production-quality frontend UI implementation across any framework. Use it when building new UI components, implementing designs, or establishing frontend quality standards. Key capabilities include component decomposition, accessibility-first implementation (WCAG 2.1 AA), responsive layout patterns, state management decisions, performance optimization (Core Web Vitals), and semantic HTML. The expected output is a UI that works for all users on all devices, with testable components and maintainable state. Without this guidance, frontends accumulate accessibility debt, inconsistent state management, and layout fragility that is expensive to fix later. Trigger phrases: build this UI, implement this design, create a component, frontend feature, responsive layout, accessible component, UI implementation."
---

# Frontend UI Engineering

Build UIs that work for every user on every device — accessible by default, responsive by design, and maintainable over time.

## When to Use This Skill

Use when:
- Implementing a new UI component or screen from a design
- Building a feature that involves user-facing interaction
- Reviewing frontend code for accessibility, performance, or maintainability
- Establishing component architecture patterns for a new frontend project

**When NOT to use:** For framework-specific deep dives, use `react-expert`, `nextjs-expert`, `vue-expert`, or `svelte-expert`. This skill covers cross-framework principles and decisions.

## Instructions

### Step 1: Decompose Before Building

Do not start with a single large component. Decompose the UI into a hierarchy before writing any code:

1. **Identify data boundaries**: Where does data come from? At which level of the tree?
2. **Identify interaction boundaries**: Which components own user events vs. which display data?
3. **Identify reuse candidates**: What might be reused in other contexts?

Component types to distinguish:
- **Container components**: fetch/transform data, hold state, pass props down
- **Presentational components**: receive props, render, emit events — no data fetching
- **Layout components**: manage spacing, grid, positioning — no business logic

### Step 2: Semantic HTML First

Write semantic HTML before adding interactivity or styling. Correct semantics give you accessibility and SEO for free:

| Use | Instead of |
|---|---|
| `<button>` for clickable actions | `<div onClick>` |
| `<nav>`, `<main>`, `<aside>` | `<div class="nav">` |
| `<ul>/<li>` for lists | Multiple `<div>` elements |
| `<label>` paired with inputs | Placeholder text only |
| `<h1>`-`<h6>` in logical order | Styled `<span>` elements |
| `<a href>` for navigation | `<div onClick=navigate>` |

### Step 3: Accessibility (WCAG 2.1 AA Minimum)

These are non-negotiable for production UIs:

- [ ] All images have meaningful `alt` text (or `alt=""` for decorative images)
- [ ] All interactive elements reachable and operable by keyboard alone (Tab, Enter, Space, Arrow keys)
- [ ] Color contrast ratio ≥ 4.5:1 for text; ≥ 3:1 for large text and UI components
- [ ] Focus indicator visible at all times — never `outline: none` without a custom replacement
- [ ] Form inputs have associated `<label>` elements (not just placeholder text)
- [ ] Error messages describe what went wrong and how to fix it — not just "invalid input"
- [ ] Dynamic content changes announced to screen readers via `aria-live` regions
- [ ] No information conveyed by color alone (use icon + color, not color alone)

### Step 4: Responsive Layout

Start from mobile, expand to larger screens. Never start from desktop and squeeze down.

```css
/* Mobile first — base styles apply to all sizes */
.card { padding: 1rem; }

/* Progressively enhance for larger screens */
@media (min-width: 768px) { .card { padding: 2rem; } }
@media (min-width: 1200px) { .card { max-width: 1200px; margin: 0 auto; } }
```

Layout hierarchy:
1. Use CSS Grid for two-dimensional layouts (rows AND columns)
2. Use Flexbox for one-dimensional layouts (row OR column)
3. Use logical properties (`margin-inline`, `padding-block`) for RTL/LTR support
4. Never use fixed pixel widths for containers that must adapt to screen size

### Step 5: State Management

Choose the right scope for each piece of state:

| State type | Scope | Tool |
|---|---|---|
| Local UI state (open/closed, hover) | Component | `useState` / reactive vars |
| Shared UI state (theme, modal) | Component tree | Context / Pinia / Svelte stores |
| Server state (API data) | App | TanStack Query / SWR / Apollo |
| URL state (filters, pagination) | URL | `useSearchParams` / router |
| Form state | Form component | `useForm` / Reactive forms |

Rules:
- Co-locate state as low in the tree as possible — lift only when siblings need it
- Server state is not the same as client state; use a dedicated server-state library
- Avoid storing derived data in state; compute it from the source

### Step 6: Core Web Vitals

Target before shipping:

| Metric | Target | How to fix |
|---|---|---|
| LCP (Largest Contentful Paint) | < 2.5s | Preload hero images, avoid render-blocking resources |
| CLS (Cumulative Layout Shift) | < 0.1 | Set explicit width/height on images and media |
| INP (Interaction to Next Paint) | < 200ms | Break up long tasks, defer non-critical JS |
| FID / TBT | < 50ms TBT | Minimize main thread work during load |

Quick wins: lazy load below-the-fold images, code-split at route level, preconnect to critical origins.

### Step 7: Component Testing

Testable components are built with testing in mind from the start:

- Test behavior, not implementation (what the user sees/does, not internal state)
- Query by accessible roles, labels, and text — not CSS selectors or `data-testid`
- Use `data-testid` only when no accessible query exists
- Test loading, error, and empty states — not just the happy path
- Test keyboard interactions for interactive components

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Accessibility can be added later" | Retrofitting accessibility into an inaccessible architecture costs 5-10x more than building it in. Screen reader users exist today. |
| "Our users are all on desktop, so mobile doesn't matter" | Your next hire, your investors, your customers on the train — they are on mobile. Build responsive from the start. |
| "This is just a `div` with `onClick`" | Screen reader users cannot discover or activate that element. Use a `<button>`. |
| "Color contrast is a design concern, not engineering" | Engineers ship code that can fail contrast checks. Verify before merge, not after a11y audit. |
| "We'll optimize performance later" | Core Web Vitals affect SEO and user retention immediately. Each 100ms of LCP improvement is measurable conversion impact. |

## Verification

- [ ] All images have descriptive `alt` attributes
- [ ] All interactive elements are keyboard-accessible (tab through the feature manually)
- [ ] Color contrast passes 4.5:1 minimum (verify with browser DevTools accessibility checker)
- [ ] Layout is tested at 320px, 768px, and 1200px widths
- [ ] Components have tests that cover loading, error, and empty states
- [ ] No `outline: none` without a visible focus replacement
- [ ] Core Web Vitals measured in staging (Lighthouse score ≥ 80 for Performance + Accessibility)

## Related Skills

- `react-expert` — React-specific patterns, hooks, and optimization
- `nextjs-expert` — Next.js App Router, Server Components, and data fetching
- `vue-expert` — Vue 3 Composition API and Pinia
- `svelte-expert` — Svelte runes and SvelteKit patterns
- `e2e-testing-automation` — End-to-end testing for user flows
- `performance-review` — Detect and fix frontend performance bottlenecks
