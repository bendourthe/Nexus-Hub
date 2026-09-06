# Session History - v3.16.0 Phase 1: Defaults contract, generator, and guard

**Date**: 2026-08-08
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.0-platform-defaults-config.md](../../plans/v3.16.0-platform-defaults-config.md)
**Phase**: 1 of 5 (not the final phase; no release-readiness workflow ran)
**Branch**: `feat/platform-defaults-config`, cut from `develop`
**Outcome**: Complete. All four quality gates passed.

## Goal

Make `configs/platform-defaults.json` the single place Claude's install defaults are declared, with every derived artifact generated or read from it, and a guard that fails the build on drift.

## Sub-tasks completed

### 1.1 - Schema and Claude seed

Created `configs/platform-defaults.json` (schema_version 1) with a `meta` block carrying the purpose, authority, scope boundary against the read-contract, the do-not-invent rule, the generator commands, and an env-precedence warning; and a `platforms` object keyed by integration-registry ids. Seeded `claude` only, with the three values taken from the shipped template rather than retyped. Per-platform entries carry `source_url`, `verified`, `doc_statement`, `settings`, `rationale`, and `derived_artifacts`.

The source URL was **fetched and verified**, not assumed. The obvious candidate (`https://docs.claude.com/en/docs/claude-code/settings`) returns a 301 to a different host; the canonical location is `https://code.claude.com/docs/en/settings`, which names all four keys and states that `CLAUDE_CODE_EFFORT_LEVEL` overrides `effortLevel` for a session. Recording the redirecting URL would have baked provenance rot into the file on day one.

Documented the schema, the five rules, the generator usage, and the add-a-platform procedure in a new `configs/README.md`.

### 1.2 - Surgical generator and drift check

Added `scripts/sync_platform_defaults.py` (stdlib only). Two strategies, both declared in the source rather than hardcoded in the script, so Phase 3 widens coverage with a data edit:

- `merge-keys` for JSON artifacts: loads, sets only the declared dotted keys, re-dumps preserving key order, indentation, and newline convention.
- `runtime-read` for the Python module that reads the source itself: nothing to generate, but the module's offline fallback literal is verified (and repaired by `--apply`) via `ast.literal_eval`, with no import and no side effects.

### 1.3 - Stub reads the source

Removed `_PROJECT_SETTINGS_STUB` entirely from `scripts/lib/integrations/claude.py`. The stub is now composed at call time by `build_project_settings_stub()` from the declared source, with the static `_comment` and `permissions` parts held separately. Candidate paths are tried in priority order (repo checkout, then the bootstrap-materialized `~/.nexus-hub/src/configs/`).

### 1.4 - Validation and CI wiring

Added `python scripts/sync_platform_defaults.py --check` to the `Makefile` `validate` target and to the CI `validate` job, next to the other repo-internal structural guards. Added `sync_platform_defaults.py` to `DEV_ONLY_SCRIPTS` in `catalog/hooks/tests/test_installer_smoke.py` with a justification following the three existing precedents.

### 1.5 - Tests and stabilization

Added `tests/validators/test_sync_platform_defaults.py` (69 cases). Retargeted `tests/installer/test_init_subcommand.py` and the effort-level assertion in `catalog/hooks/tests/test_installer_smoke.py` from hardcoded literals to the declared source.

## Test results

| Suite | Result |
|-------|--------|
| `tests/validators` | 461 passed |
| `tests/installer` + `tests/integrations` + `catalog/hooks/tests` | 1750 passed, 53 skipped, 1 failed (pre-existing, see below) |
| `tests/validators/test_sync_platform_defaults.py` | 69 passed |
| Coverage, both changed modules | **99%** (`sync_platform_defaults.py` 99%, `claude.py` 98%) |
| ShellCheck | Clean (no shell file changed) |
| `validate` guards (8, run individually) | All pass |

End-to-end verification: a real `nexus-hub init` into a throwaway project wrote a stub whose `effortLevel`, `model`, and `env.CLAUDE_CODE_EFFORT_LEVEL` match the declared source, with key order `_comment, effortLevel, model, env, permissions` preserved.

## Troubleshooting trail

1. **`Path.read_text(newline=...)` is Python 3.13+.** Failed on this 3.12 host; CI pins 3.11. Resolved with a `read_text_raw` helper passing `newline=""` through `open()`.
2. **The round-trip was not byte-identical, and the reason mattered.** `json.dumps(indent=2)` reproduced git's stored 5950 bytes exactly, but the on-disk file is 6211 bytes because `core.autocrlf=true` materializes CRLF. Resolved by detecting and preserving each artifact's dominant newline, then covering both conventions with parametrized tests.
3. **One failure in the 1750-test run.** `test_ps_standalone_extracts_and_hands_off` fails on `/usr/bin/tar: unexpected end of file`. Classified ENV and confirmed pre-existing by re-running it in a detached `git worktree` at the base `develop` commit, where it failed identically in 3.6s. Recorded as BG-1.
4. **Coverage read artificially low.** The script's `main()` is exercised only through subprocess CLI tests, which coverage cannot instrument. Added in-process `main()` tests and error-branch tests, raising the module from 78% to 99%.

## Deviations from the plan

- **No CI path filter** (recorded as DF-1). The workflow has no per-job path filters; a positive `paths:` filter would narrow coverage rather than save minutes. Matches the v3.15.14 Phase 4.5 precedent.
- **Silent fallback on a missing source** (recorded as DF-2, closed). The plan called for an unconditional one-line note; absence is the normal installed-tree case, so the note would print on every `nexus-hub init`. Confirmed with the maintainer before implementing.
- **One extra file retargeted beyond the plan's list.** The plan named `tests/installer/test_init_subcommand.py` as the test to retarget; `catalog/hooks/tests/test_installer_smoke.py` held the same duplicated literal and was retargeted for the same reason.

## Known gaps appended

DF-1 (no CI path filter), DF-2 (closed, silent fallback), NI-1 (`configs/` not distributed), BG-1 (pre-existing bootstrap tar failure), WN-1 (stale worktree admin entries). Recorded in [docs/releases/v3/v3.16/known-gaps.md](../../known-gaps.md) under `## v3.16.0 - platform-defaults-config`.

## Next steps

**Phase 2 - Per-platform lever research and verification.** Web-verify each of the sixteen registered integrations for a documented default-setting lever and classify VERIFIED (with URL and date) or UNVERIFIED, recorded in `docs/policy/platform-defaults-levers.md`. The hard rule is that a lever is recorded only when a fetched official vendor page names it; "no lever documented" is a valid and expected result. Phase 1's Claude entry is the shape every later entry follows, and its fetched-and-corrected source URL is the worked example of why the URL is verified rather than assumed.
