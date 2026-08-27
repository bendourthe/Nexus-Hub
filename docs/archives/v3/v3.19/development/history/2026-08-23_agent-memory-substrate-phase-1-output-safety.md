# Session History - Agent-Memory Substrate Phase 1: Output-Safety Foundation

**Date**: 2026-08-23
**Branch**: `feat/v3.19.1-agent-memory-substrate`
**Plan**: [`docs/releases/v3/v3.19/plans/v3.19.1-agent-memory-substrate.md`](../../plans/v3.19.1-agent-memory-substrate.md)
**Phase**: 1 - Output-safety foundation
**Environment**: Windows 11, PowerShell, Python 3.12.10, pytest, coverage; GNU Make unavailable, so validation ran as its constituent commands
**Outcome**: A dated per-CLI truncation contract exists, a shared paging helper pages agent-consumed output under both a byte cap and a line cap, printed next-part commands resolve to a real file, and `check_docs_retention.py` is the first consumer. Every required gate for this phase passed.

## 1. Starting State and Routing

- **Starting commit**: `origin/develop` at the v3.19.0 back-merge
- **Branch base**: new `feat/v3.19.1-agent-memory-substrate` from `origin/develop` (the leftover `feat/v3.19.0-code-intelligence-hardening` branch was already merged)
- **Plan recommendation**: strong reasoning tier, medium effort
- **Implementation route**: the active Cursor session remained at or above the planned tier; no downshift

## 2. What Was Implemented

### 2.1 - Re-verify per-CLI output truncation limits

Wrote `docs/policy/output-truncation-limits.md` with a 2026-08-23 table covering Cursor, Claude Code, Gemini CLI / Antigravity CLI, Codex, and OpenCode. Classification is MATCH / DRIFT / UNVERIFIED per the platform-read-contracts convention. Figures were not copied from any third-party project comment.

The safe default is the minimum across MATCH rows: 20,000 bytes (Cursor's inline Shell cap, applied as UTF-8 bytes) and 256 lines (conservative historical line fuse). OpenCode's live tool path is UNVERIFIED and does not move the default.

### 2.2 - Shared output-paging helper

Added `scripts/lib/output_paging.py`. It pages by both caps, never splits a line, reports an oversized line instead of truncating it, adds no framing when the payload fits, and appends one `# next:` line with a resolved command when more parts remain. The module lives under `scripts/lib/`, which both installers already copy wholesale (v3.16.1), so no new named copy step was added. No PowerShell sibling: no `.sh` consumer exists yet.

### 2.3 - Self-naming command output

Added `scripts/lib/self_naming.py`. Printed commands resolve the interpreter and the script from their real paths and fold a home-directory prefix to `~/...`. An audit of repo-level scripts found no existing bare self-invocation of the `nexus-memory wake` shape (that package does not exist yet); the helper is used by the pager trailer and by the retention-script consumer.

### 2.4 - First consumer and tests

`check_docs_retention.py` now renders its report to a string and emits it through the pager, with `--part` for follow-up pages. The script still always exits 0: a paging error falls back to the unpaged report so the advisory validate gate cannot become a release blocker.

## 3. Tests and Troubleshooting

`tests/validators/test_output_paging.py` covers under-cap (no framing), over-byte, over-line, over-both, oversized-line reporting, next-part command resolution, self-naming home-fold, and the retention consumer. Existing `test_check_docs_retention.py` stayed green.

Two first-run failures were TEST, not IMPL:

- The resolver returned the interpreter (`python.exe`) before the script because both exist as files. It now skips the interpreter when a later token also resolves.
- A 120-byte test cap was smaller than the real Windows next-part trailer (home-folded Store Python path plus a quoted OneDrive script path). The test cap was raised to 400.

Coverage on the two new modules is 84% / 88% with `PYTHONPATH=scripts/lib`. `check_docs_retention.py` is exercised through subprocess (the pre-existing pattern), so line coverage of that file is not collected by `--cov`.

## 4. Verification

| Gate | Result |
|---|---|
| Paging + retention tests | 27 passed after the two TEST fixes (11 new paging tests plus 16 existing retention tests) |
| Existing retention suite | 16 passed unchanged |
| Modified-module coverage | `output_paging.py` 84%, `self_naming.py` 88% |
| Unicode safety on the new policy file | Pass (`--strict`) |
| Lint on the new Python files | No diagnostics |
| CI path | Covered by the existing `tests` job (`tests/validators`); no new required job (workflow-level `paths:` is forbidden on required checks after v3.17.6) |

## 5. CI/CD and Post-Phase Review

No CI rewrite. `.github/workflows/ci.yml` already runs `tests/validators` on every relevant change, uses concurrency cancel-in-progress, pip caching, and a job-level `changes` classifier instead of a workflow `paths:` filter. A dedicated paging job would add minutes without adding a required-check surface. Unverified CLI surfaces are recorded as DF-1 / DF-2 / WN-1 in `known-gaps.md` rather than guessed.

`docs/DEVLOG.md` is unchanged: it is a one-line-per-release index and v3.19.1 is not released yet.

## 6. Files Changed

| File | Change |
|---|---|
| `docs/policy/output-truncation-limits.md` | Dated per-surface truncation contract |
| `scripts/lib/output_paging.py` | Shared paging helper |
| `scripts/lib/self_naming.py` | PATH-independent self-command builder |
| `scripts/check_docs_retention.py` | First consumer; `--part`; still exit 0 |
| `tests/validators/test_output_paging.py` | Phase 1 unit and resolution tests |
| `docs/v3/v3.19/known-gaps.md` | v3.19.1 subsection; UNVERIFIED surfaces |
| `docs/v3/v3.19/plans/v3.19.1-agent-memory-substrate.md` | Phase 1 exit checklist marked complete |
| `CHANGELOG.md` | Unreleased paging and self-naming notes |

## 7. Next Steps

Phase 2: write the memory-substrate contract, the agent-performed compression protocol, the subagent write-exclusion clause, and the Tier-1 token-budget guard.
