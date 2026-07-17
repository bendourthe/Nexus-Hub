---
name: web-artifacts-builder
description: "Scaffold multi-component HTML artifacts (Vite + React + TypeScript + Tailwind v4 + shadcn/ui) for any in-browser deployable target - product demos, internal tools, prototypes, embedded widgets, single-page apps, dashboards, configurators. Use whenever the user asks to \"build a web app / web artifact / single-page app / interactive demo / prototype\", needs state management or routing, requires shadcn/ui components, or wants to scaffold a Vite-React-Tailwind project from zero. Bundles cross-platform init scripts (init-artifact.sh + init-artifact.ps1) so Windows / macOS / Linux all reach the same scaffold. SKIP: simple single-file HTML / JSX (just write the file inline), static landing pages without state, generative-art p5.js sketches (use generative-art), or any artifact that does not need a build step."
summary_l0: "Scaffold Vite + React + TypeScript + Tailwind v4 + shadcn/ui multi-component web artifacts"
overview_l1: "This skill scaffolds multi-component HTML artifacts for any in-browser deployable target - product demos, internal tools, interactive prototypes, embedded widgets, single-page apps, dashboards, configurators. The scaffold pairs Vite + React + TypeScript + Tailwind v4 + shadcn/ui, the stack that minimizes version-mismatch debugging while supporting state management, routing, and accessible component primitives out of the box. The skill ships a cross-platform pair of init scripts (init-artifact.sh for macOS / Linux, init-artifact.ps1 for Windows) so the same scaffold lands on every supported OS. Trigger phrases: web artifact, web app, SPA, single-page app, interactive demo, prototype, internal tool, dashboard, Vite React, Tailwind shadcn, scaffold a frontend, build a web app, multi-component HTML."
---

# Web Artifacts Builder

Scaffolds multi-component HTML artifacts using a vetted stack: Vite + React + TypeScript + Tailwind v4 + shadcn/ui. The skill's value is not the stack choice itself - it is that the scaffold is one command, succeeds the same way on every OS, and erases the version-mismatch debugging that eats an hour on a from-scratch setup.

## When to Use This Skill

Use this skill when:

- The user asks to build a web app, SPA, single-page app, or interactive demo
- The artifact has multiple components, state, routing, or shadcn/ui primitives
- The artifact will be deployed in a browser (Vercel, Netlify, GitHub Pages, internal share, embedded preview)
- A Vite + React + TS + Tailwind + shadcn scaffold is the right starting point and the user wants it scaffolded once, correctly
- The user wants a prototype that pairs production-grade tooling with prototype-grade speed

**Trigger phrases**: "web artifact", "web app", "SPA", "single-page app", "interactive demo", "prototype", "internal tool", "dashboard", "Vite React", "Tailwind shadcn", "scaffold a frontend", "build a web app", "multi-component HTML", "spin up a UI", "set up a React project".

**When NOT to use**:

- Simple single-file HTML / JSX with no state and no build step (just write the file directly; the scaffold is overhead)
- Static landing pages where the artifact is HTML + CSS only (Astro is a better fit; route via `framework-specialists/astro-expert`)
- Generative-art sketches (use `specialized-domains/generative-art` - that skill ships its own p5.js + HTML viewer convention without a build step)
- Server-side rendered apps (use `framework-specialists/nextjs-expert`)
- Mobile-only artifacts (use `specialized-domains/ios-development` or `specialized-domains/android-development`)
- "I just need to add a button to an existing app" (work in the existing app, don't scaffold)

If the artifact does not need a build step, this skill is the wrong shape. The scaffold's value is in the build pipeline.

## The Stack

| Layer | Choice | Why |
|---|---|---|
| Build tool | Vite | Fast HMR, ESM-native, no webpack config, sane defaults. |
| Framework | React 18+ | Largest component-primitive ecosystem; pairs with shadcn. |
| Language | TypeScript (strict) | Catches version-skew and prop-shape errors at compile time, not runtime. |
| Styling | Tailwind CSS v4 | Utility-first; v4's `@theme` block is the integration point for `theme-tokens`. |
| Components | shadcn/ui | Copy-in components (not a dependency); fully accessible primitives via Radix. |
| State (if needed) | useState / useReducer / zustand | No global state until a real cross-component need; then pick zustand for its smallness. |
| Router (if needed) | react-router | Default for SPAs; skip entirely for single-page artifacts. |

The stack is opinionated on purpose. Each substitution costs roughly 30 minutes of debugging the next time something breaks. If the user has a different stack preference, route through `framework-specialists/<other>-expert`.

## Instructions

1. **Confirm fit first**. Read the "When NOT to use" list above. If the artifact is single-file or static, do not scaffold. Push back: "This is one HTML file; we don't need Vite for it."
2. **Run the bundled init script**. The script lives at `~/.nexus-hub/skills/developer-experience/web-artifacts-builder/scripts/init-artifact.{sh,ps1}` after the installer runs (or `catalog/skills/developer-experience/web-artifacts-builder/scripts/` in this repo). Pick the script for the host OS:

    ```bash
    # macOS / Linux
    bash ~/.nexus-hub/skills/developer-experience/web-artifacts-builder/scripts/init-artifact.sh <project-name>
    ```

    ```powershell
    # Windows
    & "$HOME\.nexus-hub\skills\developer-experience\web-artifacts-builder\scripts\init-artifact.ps1" -ProjectName <project-name>
    ```

    The script: (a) verifies Node + npm exist; (b) runs `npm create vite@latest <name> -- --template react-ts`; (c) installs and configures Tailwind v4 (`@tailwindcss/vite` plugin + `@theme` in `src/app.css`); (d) initializes `shadcn` with sensible defaults; (e) prints the next-step instructions (`cd <name> && npm run dev`).

3. **Tailwind v4 integration**. The script wires Tailwind via the v4 Vite plugin (not the legacy v3 PostCSS plugin). The single `@import "tailwindcss";` line in `src/app.css` is the entry point. Theme tokens go in a `@theme { --color-primary: ...; }` block in the same file; if `theme-tokens` is in use, emit the theme JSON values into that block.
4. **shadcn first-run**. The script runs `npx shadcn@latest init` with the New York style + Slate base color as default. Add components on demand: `npx shadcn@latest add button card dialog input`.
5. **Tree-shake the scaffold**. After scaffolding, delete `src/App.css` (Tailwind replaces it), the default Vite logo files, and the placeholder counter. The artifact's first commit should be the scaffold minus the demo content.
6. **Wire `theme-tokens` if used**. If the user names a theme from the `theme-tokens` skill, load the theme JSON, emit its palette, fonts, spacing, radius, and shadow into the `@theme` block in `src/app.css`. Map: `palette.primary` -> `--color-primary`, `fonts.heading` -> `--font-heading`, etc.
7. **Verify before claiming success**. Run `npm run dev` after scaffolding; open the localhost URL; confirm the page renders without console errors. The harness's `tools` doesn't browse for you - tell the user explicitly to verify in their browser before counting the artifact as "scaffolded".

## Cross-Platform Behavior

Both init scripts produce the same scaffold. Differences:

- **Bash script**: requires `bash` 4+ (default on macOS / Linux). Uses `set -euo pipefail` per the project's bash safety rules. Falls back gracefully if `node` or `npm` is missing - prints `Node.js not detected; install via https://nodejs.org or your platform package manager` and exits non-zero.
- **PowerShell script**: requires Windows PowerShell 5.1+ or PowerShell 7+. Uses `$ErrorActionPreference = 'Stop'`. Same fallback message if `node`/`npm` is missing.

The PowerShell script is mandatory under the `v1.1.3 four-hook` cross-platform precedent: every `.sh` bundled under a skill's `scripts/` MUST have a `.ps1` sibling, and the two MUST land at parallel paths after the installer's recursive copy.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We don't need a scaffolder - I'll just create the files manually" | Manual scaffolding takes 20-30 minutes and produces a setup that breaks the next time `vite`, `tailwind`, or `shadcn` ships a major version. The scaffold script costs 30 seconds and erases an entire class of version-mismatch bugs. |
| "Tailwind v4 is too new - let's use v3 to be safe" | v4 has been stable since 2025. The migration cost from v3 to v4 is real (the `@tailwind` directives change to `@import "tailwindcss";`), so starting on v4 is cheaper than starting on v3 and migrating later. |
| "shadcn adds complexity - let's just use raw HTML elements" | shadcn is copy-in, not a dependency. The complexity is exactly the lines you see in your `src/components/ui/`. The accessibility wins (Radix primitives, keyboard nav, focus management) are not free to rewrite from scratch. |
| "The artifact is small - I'll skip TypeScript" | TypeScript catches the prop-shape errors that "small" artifacts ship with. The cost of `tsc` is one config file. Skipping TS to "save time" usually trades 5 minutes of setup for 30 minutes of `Cannot read property of undefined`. |
| "I'll add Redux / Apollo / a global state library to be safe" | No. Start with `useState` and `useReducer`. Add `zustand` only when there is a concrete cross-component need. Redux on a 200-line prototype is a self-imposed tax. |
| "I'll edit the bundled init script directly to customize my flow" | Don't. The bundled scripts are the contract; if you need a custom flow, fork `init-artifact.{sh,ps1}` into your project's `scripts/` and edit there. Changes to the bundled script affect every future scaffold. |

## Verification

Binary checklist - each item must describe an observable artifact or state.

- [ ] `npm create vite` step completed; `<project-name>/` exists with `package.json`, `vite.config.ts`, `src/`, `index.html`.
- [ ] Tailwind v4 wired: `@tailwindcss/vite` listed in `package.json` deps; `vite.config.ts` includes the `tailwindcss()` plugin; `src/app.css` has `@import "tailwindcss";` at the top.
- [ ] `npx shadcn@latest init` completed; `components.json` exists at the project root; `src/components/ui/` directory created (may be empty until first component is added).
- [ ] `npm run dev` starts a dev server without errors; the page renders at `localhost:5173` (or the printed port).
- [ ] Default Vite demo content (logo, counter) has been removed from `src/App.tsx`.
- [ ] If `theme-tokens` was used, the chosen theme's palette / fonts / spacing values appear in `src/app.css` inside a `@theme { ... }` block.
- [ ] Both init scripts ran successfully on the host OS, OR the script aborted with a clear error before producing a half-scaffolded project.

"The scaffold looks fine" is not a valid verification criterion. The verification is: does `npm run dev` actually start, and does the page render in the browser without console errors?

## Bundled Resources

Two scaffolding scripts ship under `scripts/`. They are functionally identical and produce the same project layout; only the host shell differs.

- `scripts/init-artifact.sh` - bash script for macOS / Linux. Set executable on installer copy.
- `scripts/init-artifact.ps1` - PowerShell script for Windows. Run via `pwsh` or Windows PowerShell 5.1+.

The two scripts are kept parallel per the v1.1.3 four-hook precedent: every bundled `.sh` has a `.ps1` sibling, both produce the same output, neither one references the other. Cross-platform parity is enforced by the recursive-copy logic in `scripts/installer.{sh,ps1}` (Phase 3 of the v1.1.5 plan).

## Related Skills

- [[react-expert]] -- deep React component patterns, hooks, state management; consumed after the scaffold for the actual app logic.
- [[nextjs-expert]] -- server-side rendered alternative; route here when SSR / SEO is a requirement.
- [[astro-expert]] -- static-first alternative; route here when the artifact is mostly content with islands of interactivity.
- [[frontend-ui-engineering]] -- accessibility, responsive layout, component architecture; complements this skill once the scaffold exists.
- [[ui-component-generation]] -- generates individual components inline with the agent; pairs with this scaffold to produce the components consumed by `src/components/`.
- [[theme-tokens]] -- 10 curated themes; emit a theme into `src/app.css` `@theme` block during scaffold customization.
- [[brand-styling]] -- apply user-supplied brand tokens; route through this skill for the scaffold, then through brand-styling to override the theme.
