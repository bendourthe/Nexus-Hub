# Session History - v3.14.0 Phase 1: Codex Usage Monitor

**Date**: 2026-07-16
**Branch**: `feat/codex-lb-adoption` (off `develop`)
**Plan**: [docs/releases/v3/v3.14/plans/v3.14.0-codex-lb-adoption.md](../../plans/v3.14.0-codex-lb-adoption.md), Phase 1 of 6 (not the final phase)
**Scope**: `extensions/claude-usage-monitor/**` and `CHANGELOG.md` only (no catalog metadata, installer, or base-template)

## Goal

Ship the directly-requested build first: generalize the `claude-usage-monitor` extension behind a provider interface and add a Codex provider that reads the local Codex-app OAuth token and renders live ChatGPT account usage in the existing status-bar / tooltip / dashboard / warning UI, failing soft on the undocumented endpoint, with the Claude path unchanged.

## Key decision (mid-phase correction)

The plan and its seed comparison both assumed the Codex **CLI** credential store (`~/.codex/auth.json`). The user clarified this targets the ChatGPT Codex **app**. Since the app's on-disk credential location could not be verified from this environment, the Codex provider reads a **configurable** path (`usageMonitor.codex.authPath` -> `CODEX_HOME/auth.json` -> `~/.codex/auth.json`) and parses **shape-tolerantly**, failing soft. Exact-location confirmation is logged as DF-1.

## Sub-tasks completed

1. **1.1 - Provider interface + Claude extraction.** `src/providers/{types,errors,claude,index}.ts`; `ClaudeUsageProvider` is the old `UsageFetcher` with private methods preserved; self-describing `ProviderFetchError` + single `describeProviderError`; Claude-API types moved out of `types.ts`; `usageFetcher.ts` deleted; `usageMonitor.provider` setting added (default `claude`). No behavior change.
2. **1.2 - Codex credential reader.** `src/providers/codex.ts`: pure `parseCodexCredential` / `resolveCodexAuthPath` / `readCodexCredential` helpers; secret-safe `readCredential()`; never logs the token.
3. **1.3 - wham/usage fetcher + mapping.** Single authenticated GET with a 30s timeout; `mapCodexUsageResponse` is tolerant of shape variation and returns null (-> fail-soft) when no primary window is present; plan type, credits, and additional limits surfaced.
4. **1.4 - UI reuse + toggle + recommendations.** Additive optional model fields (`providerId`, `planLabel`, `additionalLimits`, `creditsSummary`); status bar / tooltip / dashboard / warning view branch on `providerId` (Claude strings unchanged); Codex recommendations (throttle / wait / rotate); `usageMonitor.provider` setting, "Usage: Switch Provider" command, settings-panel selector, config-change watcher; provider-aware usage URL.
5. **1.5 - Tests, docs, version, package.** Vitest harness with a `vscode` alias stub; README multi-provider docs; `package.json` 0.6.2 -> 0.7.0 + displayName/description; `.vscodeignore` excludes the test harness; clean 0.7.0 VSIX.

## Test results

- `npm run compile` (tsc): clean, exit 0.
- `npm test` (Vitest): **35 passed** across 4 files - `codex-credential` (18), `codex-usage-mapping` (8), `provider-errors` (5), `codex-recommendations` (4).
- `npm run package`: clean VSIX `claude-usage-monitor-0.7.0.vsix` (39 files), `providers/` included, `test/` excluded.

## CI/CD

No CI edit this phase. The extension is not yet exercised in CI (Python extensions only); logged as QG-1 and deferred to Phase 6.3, which owns the path-filtered npm compile + Vitest job. Editing CI is an ask-first gate.

## Deviations

- The plan's `fetchUsage(): Promise<UsageModel>` signature was widened to a `ProviderFetchResult` success/error union, because the shipping UI depends on the fetcher's error contract (banners, `describeProviderError`, rate-limit backoff). Faithful-to-consumers; logged here rather than as a known gap.
- Codex credential source is configurable rather than a fixed CLI path (see the mid-phase correction above). Logged as DF-1.

## Known gaps added

- DF-1 (exact Codex-app credential path/shape unverified), DF-2 (undocumented `wham/usage` durability), MT-1 (UI modules untested without a VS Code host), QG-1 (extension not in CI). See [docs/releases/v3/v3.14/known-gaps.md](../../known-gaps.md).

## Next steps

- Phase 2: skill-native review/verification cluster (C4 + C3 + C6).
- Before `/update release` (Phase 6): resolve the v3.14.0 version-number collision with the held `feat/agentic-setup-adoption` plan.
- Phase 6 dry-run install must engage the HO-1 flat/nested skill-collision check once Phases 2+ add catalog skills.
