# Phase 6 Effort Evidence

**Date**: 2026-10-16. **Scope**: Claude Code effort delivery only. Other platform settings are not requalified by this pass.

## Sources

- [Model configuration](https://code.claude.com/docs/en/model-config#adjust-effort-level): fetched through the web tool. Short excerpt: "a top-level `effortLevel` in your user settings file doesn't count for Opus 5.5". Explicit session sources precede saved settings, then the model default. The environment source has its stronger precedence specified in the environment reference.
- [Settings reference](https://code.claude.com/docs/en/settings-reference#modelsettings): direct Accept: text/markdown fetch returned HTTP 200 at the exact canonical URL, 425177 bytes, after the web tool response-size limit. Short excerpt: "Claude Code writes each entry under the model's canonical name". Saved model effort wins over a top-level fallback in the same file; normal scope precedence applies across files. Recognized alias/provider forms map to the canonical entry. Per-model effort requires Claude Code 2.1.251 or later.
- [Environment variables](https://code.claude.com/docs/en/env-vars): fetched through the web tool. Short excerpt: "Takes precedence over `--effort`, `/effort`, and the `modelSettings` and `effortLevel` settings". This is why an installer-created override defeats later saved choices.
- [Models overview](https://platform.claude.com/docs/en/models/overview): fetched after its documented redirect from the older about-claude URL. The canonical API IDs are `claude-fable-5-1`, `claude-opus-5-5`, `claude-sonnet-5-5`, and `claude-haiku-5-5`. No authenticated request or availability probe was made.

## Delivery Decision

Follow the maintainer's later Q3 amendment: seed per-model High and stop seeding the effort environment variable. The top-level High fallback remains for older models. Settings accept low, medium, high, and xhigh; max cannot be a default in these keys. The concrete-ID list needs refreshing when models change.

A matching recorded legacy env seed can be retired in favor of the per-model default. An unrecorded value is not assumed to be an old seed, even if its value looks familiar; retain it and provide the doctor note. A later user choice identical to the last seed is indistinguishable and may be upgraded. These are ownership limits, not measured model-quality or savings claims.

The older Phase 6 example asking the env value itself to become High predates the explicit amendment. Its effective-effort intent is preserved by retiring only an owned env seed and setting the current model's High default. Reintroducing an env High would contradict the newer decision and keep saved choices overridden.

## Settings Upgrade

**Revision**: Phase 6 working tree on `bda65451031fa8cab921e274226163284b5bb1fe`; the phase history identifies the local commit. The native `install_core_settings` and `Install-CoreSettings` functions load scratch profile settings and the real shipped template. The writer-sequence fixture also runs the real guardrail, usage-display, and description settings writers; hook file copying, command conversion, and managed-hook merge internals remain separate existing contracts.

| Input | Expected and observed result on both backends |
|---|---|
| Recorded legacy env Medium and per-model Medium | Env override absent afterward; current Opus per-model effort High; other user fields and subagent `inherit` retained |
| Changed value or unrecorded legacy Medium | Existing settings bytes retained; doctor names the override and its exact-key removal option |
| Fresh template copy | Seven actual core values recorded; hooks and attribution are not claimed as owned |
| Removed saved model effort | Remains absent across upgrades and a fresh template copy; existing values under removed keys stay user-owned |
| Invalid or different-target record | Existing settings and record retained; no ownership inferred |
| Non-object parent, Unicode text, bracketed profile path, empty hook arrays | User-owned malformed parent retained with a warning; independent defaults still seed; user text and literal paths survive; valid empty arrays receive the intended hooks |

The ownership and writer regressions executed under Git Bash with jq 1.8.2 and Windows PowerShell 5.1. New failing cases were observed before the ownership, UTF-8/path, and empty-array fixes. Eighteen malformed-root/record cases, including wrapped objects, already pass without another runtime change; the array-unwrapping suspicion was rejected. Settings-schema loading is observed; no authenticated Claude request, model-quality evaluation, or session-header claim is made.

## Doctor

The actual `scripts/nexus-hub.cmd doctor --target <scratch-home> --integrations claude` launcher reports an unowned Medium override in text and JSON while a missing manifest retains its existing exit 1. The public Python command route also delegates to the real runner for a recorded healthy installation: text and JSON report one healthy integration, exit 0, and the exact-key fix; all settings and manifest bytes remain unchanged. Selecting Codex omits the unrelated Claude note. Missing source returns exit 2 with remediation. Arbitrary unsupported values are not echoed.

A separate original-source CLI exercise against a healthy scratch install returned exit 0 in both output modes, reported `CLAUDE_CODE_EFFORT_LEVEL=medium` and `Remove only env.CLAUDE_CODE_EFFORT_LEVEL`, and left every file byte-identical. Raw controlled evidence is retained as `nexus-v4140-phase6-live-doctor.json` under the session Temp directory.

## Concurrent Record Replacement

Two native core invocations ran concurrently per backend against one scratch profile. Both returned 0; the final legacy env seed was retired, Opus effort was High, and unknown metadata survived. Sampled record reads were valid JSON: 82 observations for Bash and 61 for PowerShell. PowerShell had three transient read-sharing failures during replacement; no partial record was observed and neither writer warned. This verifies the sampled replacement behavior, not continuous read availability or serializable concurrent ownership. Raw controlled evidence is `nexus-v4140-phase6-concurrent.json` under Temp.

## Local Qualification

The initial broader selection passed 400 tests with six existing POSIX-only Windows skips. The final post-phase selection passed 411 tests with the same six skips in 439.85 seconds. The separate hook-root installer smoke passed 38 cases with no skips. The fast profile passed all 17 checks in 105.9 seconds; defaults sync reports all 14 platforms synchronized. ShellCheck, Bash syntax, PowerShell 5.1 AST parsing, and Python compilation pass. Ruff 0.17.1 adds no diagnostic relative to HEAD; one old doctor-test warning was removed. Other platforms' declared settings and the parsed hook chain are unchanged.

The full native profile, the project coverage threshold, cross-phase integration, remote required checks, and release remain final-phase work. No remote publication or paid model call occurred in this phase.

## Tested Source Hashes

| Source | SHA-256 of exercised working-copy bytes |
|---|---|
| `configs/platform-defaults.json` | `169d21bee705cc6b0b32c1afaea02c25d5fff78d234b5cce290a28f38e6a18a5` |
| `catalog/hooks/settings.json` | `342cecc3f0af6356641593a7b8fb901ed740cabe1291c5a4990c563235272b6e` |
| `scripts/installer.sh` | `5346e4283ae0f9556275469ef8e217d4b9cd9d7b883aea4d52506a1df9d62548` |
| `scripts/installer.ps1` | `711e70f5f337e10b549ad928f5ed4c1b0f21576cc14fa4b02c5c3bd0dc0c1981` |
| `scripts/lib/integrations/claude.py` | `e222462645b683412dc917379c28ee215dde425f89fc35199922484cfe30d2ff` |
| `scripts/lib/integrations/runner.py` | `03f2c090a6401552d215e0fb1c1556f9137d07e6db6a3e1f63c0bc316beddbbe` |
| `scripts/nexus_hub_cli.py` | `e6ca024340904ac96c29d0dd527f6931c0e3c4e1cd0ac05a3da4b94133168c94` |
