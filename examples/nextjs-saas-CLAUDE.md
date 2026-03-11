# Next.js SaaS Application

A full-stack SaaS application built with Next.js 14+ (App Router), TypeScript, Tailwind CSS, and Prisma. Authentication via NextAuth.js. Payments via Stripe. Deployed on Vercel.

## Tech Stack
- **Language**: TypeScript 5.x
- **Package Manager**: pnpm
- **Build**: `next build`
- **Test**: Vitest (unit/integration), Playwright (E2E)
- **Lint/Format**: ESLint (Next.js config), Prettier

## Project Layout
```
app/
  (auth)/             # Auth route group (login, signup, callback)
  (dashboard)/        # Protected route group
  api/                # Route handlers (API endpoints)
  layout.tsx
  page.tsx
components/
  ui/                 # Primitive UI components (shadcn/ui)
  <feature>/          # Feature-specific components
lib/
  auth.ts             # NextAuth.js config
  db.ts               # Prisma client singleton
  stripe.ts           # Stripe client
  utils.ts
prisma/
  schema.prisma
  migrations/
tests/
  unit/
  e2e/                # Playwright tests
public/
next.config.ts
tailwind.config.ts
```

## Key Commands
```bash
# Dev server
pnpm dev

# Build
pnpm build

# Run all tests
pnpm test

# E2E tests
pnpm test:e2e

# Lint
pnpm lint

# Format
pnpm format

# Database migrations
pnpm prisma migrate dev

# Generate Prisma client
pnpm prisma generate
```

## Non-Obvious Tooling
- Server Components fetch data directly; Client Components receive data as props — do not mix
- Use `next/server` middleware for auth guard on protected routes (not component-level checks)
- Stripe webhooks must verify the `stripe-signature` header before processing any event
- Use `@vercel/analytics` and `@vercel/speed-insights` for production observability
- `pnpm prisma studio` opens a visual DB browser — useful for debugging
- Feature flags via `@vercel/edge-config` (not environment variables) for runtime toggling without redeploy

## TypeScript Conventions
- Enable `strict: true` in `tsconfig.json` — no exceptions
- Use Zod for all runtime validation (API route inputs, form data, env vars via `@t3-oss/env-nextjs`)
- Prefer `type` over `interface` for data shapes; use `interface` only for extension points
- Never use `any` — use `unknown` and narrow explicitly
- Server Actions must be in files with `"use server"` directive and must validate inputs with Zod
- API route handlers must return typed `NextResponse` with explicit status codes
- Avoid `React.FC` — declare props types directly: `function Foo({ bar }: FooProps)`
- Co-locate component styles, tests, and types in the same directory as the component

## Communication Style
- Place punctuation outside quotation marks (logical punctuation)
- No em-dashes; use parentheses, commas, or separate sentences
- Professional teaching tone
- Never hard-wrap paragraph text at a fixed column width; write each paragraph or bullet point as a single continuous line and let the editor or terminal handle visual wrapping

## Critical Rules
- Verify work before marking complete
- Find root causes; no temporary fixes
- Destructive git commands require user confirmation
- Never add `Co-Authored-By` lines, AI attribution footers, or AI-generated signatures to commit messages
- **MANDATORY: Every Bash/shell command approval MUST be preceded by a one-sentence plain-language explanation** of what the command does and what its impact will be. This applies to ALL commands regardless of complexity. No exceptions.
- Ask clarifying questions before coding if requirements are ambiguous
- Never commit `.env.local` or any Stripe/database secrets

## Output Minimization
- Prefer `pnpm test --reporter=verbose` only on failure; default to `dot` reporter
- Suppress Next.js build info logs; report only error counts and bundle size deltas

## Context References
- Skills: `.claude/skills/` (auto-activated by task context)
- Architecture: `.claude/context/architecture.md`
- Decisions: `.claude/memory/decisions.md`
- Rules: `.claude/rules/typescript/` (TypeScript-specific coding standards)
- Agents: `.claude/agents/` (specialized subagents for code review, TDD, security)
