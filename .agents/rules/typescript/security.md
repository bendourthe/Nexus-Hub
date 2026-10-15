---
title: TypeScript Security Rules
category: typescript
priority: critical
---

# TypeScript Security Rules

## Input Validation

- Validate all external data at runtime using Zod (preferred) or class-validator. TypeScript types are erased at runtime and provide no runtime safety.
- Define Zod schemas at module boundaries (API routes, form submissions, storage reads) and parse with `.safeParse()` to handle errors explicitly.
- Never trust `req.body`, `req.query`, or `req.params` without validation, even if typed.

## XSS Prevention

- Never use `dangerouslySetInnerHTML` without first sanitizing content with DOMPurify.
- Do not use `innerHTML`, `outerHTML`, or `document.write` with user-supplied data.
- Use template literals or DOM API methods (`createElement`, `textContent`) for dynamic content.

## Authentication and Authorization

- Store JWTs in `httpOnly`, `Secure`, `SameSite=Strict` cookies. Never in `localStorage` or `sessionStorage`.
- Verify JWT signatures server-side on every protected request; do not trust decoded payloads without verification.
- Check authorization at the data layer, not just the route level, to prevent IDOR.

## Secrets and Environment

- Load secrets from environment variables via `@t3-oss/env-nextjs` or `zod` schema validation. This prevents missing secrets from surfacing as silent `undefined`.
- Never log `process.env` contents -- they may contain secrets.
- Ensure secrets are not included in client bundles. Next.js: only variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

## Dependencies

- Run `npm audit` (or `pnpm audit`) in CI and fail on critical/high CVEs.
- Pin exact dependency versions in production. Use `--save-exact` when adding packages.
- Avoid packages with no recent activity, no tests, and a single maintainer for security-sensitive functionality.

## API Responses

- Return a consistent error response shape. Never expose stack traces, file paths, or database errors to clients.
- Set `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, and `Strict-Transport-Security` headers on all responses (use `helmet` for Express/Fastify, or `next/headers` for Next.js).
