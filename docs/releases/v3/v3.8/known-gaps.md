# Known Gaps -- v3.8.0

**Status**: finalized; archived 2026-09-29; 0 open items (3 migrated to v4.13 as AR-26, AR-29, AR-37). Per-section status lines below are historical and were written before release.

**Open items**: 0

**Status at last pre-archive update**: v3.8.0 (loop-engineering enrichment from the Ralph for Claude Code comparison) is feature-complete on `develop`. The `adoption-ralph-claude-code` plan ([docs/releases/v3/v3.8/plans/adoption-ralph-claude-code.md](plans/adoption-ralph-claude-code.md)) landed all three phases: Phase 1 (exit-signal protocol, stall/fault detection, untrusted-task-source fence), Phase 2 (trace_log JSONL schema, task-readiness gate, recovery-point note), Phase 3 (sandboxing-an-unattended-loop subsection + three reverse-engineering-matrix declines). The skill body grew 157 -> 189 lines (under the 500-line norm); no frontmatter change, so no `data/` registry edit was required. As release prep, two carried-forward gaps were closed (WN-v37-3, WN-v33-2). The Ralph plan + comparison were relocated from `docs/v3/v3.7/` to `docs/v3/v3.8/` with full reference repair.

**Last updated**: 2026-06-18 (v3.8.0 release prep)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for v3.8.0. The next version's `/plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

## Summary

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 1 | 0 |
| BG | 0 | 0 |
| MT | 0 | 0 |
| WN | 5 | 2 |
| QG | 0 | 0 |
| **Total** | **6** | **2** |

## Open Items

| ID | Category | Source | Reason | Suggested next step | Severity |
|---|---|---|---|---|---|
| WN-v38-1 - MIGRATED to v4.13 (AR-29) | WN | release prep (carried from WN-v37-3) | The `README_zh.md` global-install count line was refreshed to the current catalog counts, but the rest of the Chinese README has not had a full re-translation pass against the current English README. | Do a full `README_zh.md` re-translation pass in a future docs sweep; the counts and install flow are now correct. | Low (secondary-language doc; counts + install flow correct; English README and all machine-read registries are authoritative). |
| WN-v38-2 - CLOSED 2026-09-29 | WN | release prep | `data/skills.json` `overview_l1` for `git-branching-workflow` and `session-query` was hand-synced to match the trimmed `SKILL.md` fields. The canonical regeneration path is `make build-catalog`. | Optionally run `make build-catalog` to canonically re-derive `data/` from `catalog/`; the two fields are already consistent. | Low (the two fields are consistent SKILL.md <-> skills.json; this is a provenance nicety). |
| WN-v33-1 - RESOLVED 2026-09-29 | WN | carried from v3.3.0 / v3.7.0 | Local Windows verification is partially emulated: `make` is not on PATH, so `make validate` / `make lint` / `make test` are run by invoking the underlying validators and pytest directly. For v3.8.0 the direct validate chain is green (JSON catalogs OK, per-skill orphan-bundle audit PASS, zero overview_l1 word-count warnings). | Confirm CI `validate` + `shellcheck` + `tests` are green on the release run. No code change expected. | Low (direct validator equivalents all green; only ShellCheck relies on CI). |
| WN-v36-1 - RESOLVED 2026-09-29 | WN | carried from v3.7.0 | bash cannot be fully run on the Windows dev host: the checkout path contains a space ("OneDrive - Supira") and `bash.EXE` mis-resolves it, so the bash-invoking installer test suites hang or return exit 127 on this checkout. v3.8.0 changed no installer or bash code (skill-doc + docs only), so this does not bite the v3.8.0 diff. | CI (ubuntu / macOS) remains the authoritative bash gate; optionally make the affected bash-invoking tests skip cleanly on a space-containing Windows path. No production-code change. | Low (environment-only; reproduces only under space-containing paths; green on CI and space-free checkouts). |
| WN-v37-1 - MIGRATED to v4.13 (AR-26) | WN | carried from v3.7.0 | The live `curl \| bash` one-liner against GitHub cannot be exercised in CI or on the Windows dev host. The v3.7.0 tag is now live on `main`, so the documented one-liner can finally be exercised verbatim on a real Mac. | Run the recorded macOS smoke-test checklist ([docs/releases/v3/v3.7/development/mac-smoke-test.md](../v3.7/development/mac-smoke-test.md)) on a real Mac and record the results. | Low (the macOS bash path is auto-verified in CI; only the live-network one-liner is manual). |
| DF-v36-2 - MIGRATED to v4.13 (AR-37) | DF | carried from v3.6.0 | A portable, agent-agnostic declarative YAML orchestration runtime (usable across all agents) remains deferred and policy-disfavored as a runtime. The MCP Registry Policy prefers LLM-native skills over bespoke runtimes, and the harness's own Dynamic Workflows already cover orchestration on Claude Code. The v3.8.0 loop-engineering enrichment reinforced this decision by declining a per-project loop runtime config + standalone loop runtime (recorded in the reverse-engineering matrix). | Revisit only if cross-agent declarative orchestration becomes a stated product goal; until then the adopted vocabulary + Dynamic Workflows are the answer. | Low (deferred + policy-disfavored; vocabulary already adopted). |

## Resolved

| ID | Category | Resolved in | Note |
|---|---|---|---|
| WN-v37-3 | WN | v3.8.0 release prep | The `README_zh.md` global-install bullet cited outdated counts (187 skills / 34 commands / 13 hooks / 10 agents). Refreshed to the current catalog counts (256 skills / 15 commands / 23 hooks / 23 agents). A full Chinese re-translation pass is carried forward as WN-v38-1. |
| WN-v33-2 | WN | v3.8.0 release prep | The `git-branching-workflow` (169 words) and `session-query` (175 words) `overview_l1` fields exceeded the 150-word soft limit. Both trimmed to 132 words by dropping the trailing trigger-phrase lists already present in each `description`; `data/skills.json` synced to match. The validator now reports zero `overview_l1` word-count warnings catalog-wide. (The benign `demo-capture` `.pyc` orphan is a local-only, gitignored artifact needing no repo action -- `make clean` removes it.) |

## Archive reconciliation - 2026-09-29

Before this minor moved to `docs/archives/`, every item that this file did not already record as resolved, closed, accepted, or declined was audited against the current tree. Each row below gives the one disposition applied, and the item's own line carries the same marker. Migrated items are tracked in `docs/releases/v4/v4.13/known-gaps.md`, section "Migrated from archived minors (v3.x, v4.0-v4.11) - 2026-09-29".

| Item | Disposition | Evidence, reason, or destination |
|---|---|---|
| WN-v38-1 (line 25) | Migrated | AR-29: `README_zh.md` is 271 lines against the English README's 792 and needs a full re-translation |
| WN-v38-2 (line 26) | Closed | Superseded: `scripts/check_registry_entries.py --check --strict` enforces SKILL.md-to-registry agreement, and hand-editing `data/skills.json` is the declared convention |
| WN-v33-1 (line 27) | Resolved | the release CI run on `main` for this version passed (`gh run list --branch main`, matched by run title because tag SHAs were later rewritten) |
| WN-v36-1 (line 28) | Resolved | `install.ps1` now resolves the Windows `tar.exe` via `Resolve-TarExe` (commit `43bae404`), and the test-PATH repair in `tests/conftest.py` (v3.15.6) fixed the Windows host failures; see v3.6 WN-v36-1 and `docs/archives/v3/v3.18/known-gaps.md` WN-1 after this move |
| WN-v37-1 (line 29) | Migrated | AR-26: live macOS installer smoke (`curl \| bash` and `--branch`) never recorded; `development/mac-smoke-test.md` steps are still pending; merged with v3.0 DF-v30-8, v3.7-v3.9 WN-v37-1 |
| DF-v36-2 (line 30) | Migrated | AR-37: conditional adoption candidates awaiting a maintainer build-or-decline decision; merged with v3.0 DF-v30-9, v3.6-v3.9 DF-v36-2, v3.9 DF-v39-nomistakes-1, v3.10 DF-v310-ruflo-A6 and A10-rest |
