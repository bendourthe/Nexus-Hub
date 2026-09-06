---
name: astro-expert
description: Deep Astro expertise for island architecture, content collections, multi-framework integration, and hybrid rendering. Use when building Astro sites, optimizing content-driven pages, or integrating React/Vue/Svelte components with partial hydration.
summary_l0: "Build Astro sites with content collections, island architecture, and multi-framework integration"
overview_l1: "This skill provides specialized Astro expertise covering project structure, component syntax, content collections with Zod schemas, file-based routing with static and server-side rendering, island architecture with client directives, multi-framework component integration, data fetching, API endpoints, middleware, image optimization, View Transitions, and deployment across adapters. Use it when scaffolding Astro projects, building content-driven sites with collections, designing island-based hydration, integrating React/Vue/Svelte/Solid components, configuring static/SSR/hybrid rendering, optimizing images with astro:assets, or deploying to Vercel/Netlify/Cloudflare/Node.js. Key capabilities include content collection schema design, selective hydration with client directives, multi-framework composition, hybrid rendering configuration, and adapter-based deployment. The expected output is a well-structured Astro site with proper content modeling, optimized hydration, and production-ready deployment. Trigger phrases: astro, astro.build, content collections, island architecture, partial hydration, client:load, client:idle, client:visible, astro components, astro routing, astro deployment, astro adapter, view transitions, astro:assets, MDX astro."
---

# Astro Expert

Specialized expertise in Astro development, providing deep guidance on the island architecture, content collections with type-safe schemas, file-based routing with static/SSR/hybrid rendering, multi-framework component integration (React, Vue, Svelte, Solid), client hydration directives, data fetching patterns, API endpoints, middleware, image optimization with `astro:assets`, View Transitions, and production deployment across multiple adapters.

## When to Use This Skill

Use this skill for:

- Scaffolding new Astro projects with proper directory structure
- Building content-driven sites with type-safe content collections
- Designing island architecture strategies with selective hydration
- Integrating React, Vue, Svelte, or Solid components in Astro pages
- Implementing file-based routing with dynamic segments and pagination
- Configuring static, SSR, or hybrid rendering modes
- Creating API endpoints and server-side middleware
- Optimizing images, fonts, and Core Web Vitals
- Adding View Transitions for SPA-like navigation
- Generating sitemaps, RSS feeds, and structured data
- Deploying to Vercel, Netlify, Cloudflare Workers, or Node.js

**Trigger phrases**: "astro", "astro.build", "content collections", "island architecture", "partial hydration", "client:load", "client:idle", "client:visible", "astro components", "astro routing", "astro deployment", "astro adapter", "view transitions", "astro:assets", "MDX astro"

## What This Skill Does

Provides Astro expertise including:

- **Project Structure**: Directory conventions, `.astro` component syntax, frontmatter scripts, expressions, and slots
- **Content Collections**: Zod schema definitions, querying and rendering collections, MDX integration, reference relations
- **Routing**: File-based routing, dynamic routes, rest parameters, pagination, i18n routing
- **Island Architecture**: `client:load`, `client:idle`, `client:visible`, `client:media`, `client:only` directives and hydration strategies
- **Multi-Framework**: React, Vue, Svelte, Solid components coexisting in a single Astro project with shared state
- **Data Fetching**: Frontmatter fetch, API endpoints, SSR middleware, authentication patterns
- **Performance**: Image optimization with `astro:assets`, View Transitions, prefetching, fonts, Core Web Vitals
- **Deployment**: Node.js, Vercel, Netlify, Cloudflare adapters, static output, environment variable configuration

## Instructions

### Step 1: Astro Fundamentals

Full walkthrough: [step-1-astro-fundamentals.md](references/step-1-astro-fundamentals.md) (load this step when you reach it).

### Step 2: Content Collections

Full walkthrough: [step-2-content-collections.md](references/step-2-content-collections.md) (load this step when you reach it).

### Step 3: Routing and Pages

Full walkthrough: [step-3-routing-and-pages.md](references/step-3-routing-and-pages.md) (load this step when you reach it).

### Step 4: Island Architecture

Full walkthrough: [step-4-island-architecture.md](references/step-4-island-architecture.md) (load this step when you reach it).

### Step 5: Multi-Framework Integration

Full walkthrough: [step-5-multi-framework-integration.md](references/step-5-multi-framework-integration.md) (load this step when you reach it).

### Step 6: Data Fetching and API Routes

Full walkthrough: [step-6-data-fetching-and-api-routes.md](references/step-6-data-fetching-and-api-routes.md) (load this step when you reach it).

### Step 7: Performance and SEO

Full walkthrough: [step-7-performance-and-seo.md](references/step-7-performance-and-seo.md) (load this step when you reach it).

### Step 8: Deployment and Adapters

Full walkthrough: [step-8-deployment-and-adapters.md](references/step-8-deployment-and-adapters.md) (load this step when you reach it).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will add `client:load` to every interactive component to be safe." | Hydrating everything on load defeats the entire point of island architecture and ships the JavaScript bundle Astro exists to avoid. Use the narrowest directive that works (`client:visible` or `client:idle`), and leave purely static content unhydrated. |
| "Content collections are overkill; I will just read Markdown files directly." | Reading files raw drops the Zod schema validation, so a missing frontmatter field surfaces as a runtime crash on a published page instead of a build-time error. Collections catch the bad content before deploy. |
| "I can fetch data in the component template like a client-side framework." | Astro `.astro` frontmatter runs at build or request time, not in the browser; treating it like a client component leads to fetches that never run where you expect. Match the fetch location to the rendering mode (static, SSR, or island). |

## Verification

- [ ] Each interactive component uses the narrowest viable client directive (static content stays unhydrated)
- [ ] Content collections define a Zod schema and the build passes `astro check` with no schema errors
- [ ] The configured output mode (static / server / hybrid) matches an installed adapter
- [ ] Images use `astro:assets` (`<Image />` or `getImage`) rather than raw `<img>` tags
- [ ] The production build succeeds: `astro build`

## Related Skills

- [[react-expert]] -- React components rendered as Astro islands with partial hydration
- [[vue-expert]] -- Vue components rendered as Astro islands with partial hydration
- [[svelte-expert]] -- Svelte components rendered as Astro islands with partial hydration
- [[frontend-ui-engineering]] -- accessible, responsive UI patterns for the pages Astro renders
