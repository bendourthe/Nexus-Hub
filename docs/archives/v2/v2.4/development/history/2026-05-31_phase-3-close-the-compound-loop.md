# Session History - v2.4.0 (adoption-compound-engineering-plugin) Phase 3: Close the Compound Loop

**Date**: 2026-05-31
**Plan**: [docs/archives/v2/v2.4/plans/adoption-compound-engineering-plugin.md](../../plans/adoption-compound-engineering-plugin.md)
**Phase**: 3 of 8 - Close the compound loop (A5 strategy anchor + planning grounding, A7 cross-tool session query)
**Sub-tasks**: T013 (product-strategy skill), T014 (wire planning/learning skills to read docs/solutions), T015 (session-query skill + extraction scripts), T016 (testing + stabilization)
**Outcome**: Two new local-only workflow skills shipped and registered (`product-strategy`, `session-query`; total 242 -> 244, workflow 33 -> 35). The compound loop is now wired end-to-end: capture (`solution-knowledge-base`) -> plan (`implementation-plan` / `generate-plan` read `docs/solutions/` + `STRATEGY.md` as grounding) -> review (Phase-2 pipeline) -> capture (`known-gaps-tracker` + `continuous-learning` graduate findings into solution docs). The `session-query` skill ships four bundled scripts (discover + extract, `.sh`/`.ps1` + `.py`/`.ps1`) that read LOCAL session JSONL logs with zero outbound. All validators green; orphan-bundle 0/0 across 244 skills; MCP skill-server 43 passed; repo-level tests 344 passed (incl. 13 new). PowerShell extractor parity verified empirically; live skill-eval-loop deferred (DF-v24-4).

---

## Goal

Adopt the two compound-loop items that turn captured knowledge into grounding for future work: a durable product-strategy anchor read by ideation/planning (A5), planning/learning skills that read the `docs/solutions/` knowledge base before designing (A5), and a script-first cross-tool session-query skill that recovers prior investigation context from local Claude/Codex/Cursor session logs (A7). All content re-authored generically with no source-repo attribution and zero new outbound calls / credentials / dependencies.

## Steps taken

1. **Phase 0 - resolve plan / phase**: parsed the invocation (`3 of docs/archive/v2/v2.4/plans/adoption-compound-engineering-plugin.md`); legacy flat layout confirmed. Phase 3's prerequisite is Phase 1 (complete); Phases 1, 2, 4 already closed. Final-phase detection: false (3 of 8).

2. **Phase 1 - pre-implementation review**: read the full plan and the Phase-3 sub-tasks; the `solution-knowledge-base` / `solution-refresh` skills (the A1 store this phase grounds against); `project-constitution` (to confirm T013 should be a NEW skill, not a constitution extension - governance vs product framing); `continuous-learning`, `known-gaps-tracker`, `implementation-plan`, `session-history`, and the `generate-plan` command (the T014 edit targets); the three data registries; the `tests/validators` conftest runner and an exemplar bundled-script skill (`docs-layout-refactor`) for the script convention.

3. **T013 - product-strategy skill**: created `catalog/skills/workflow/product-strategy/SKILL.md` (125 lines) - authors/maintains a durable `STRATEGY.md` (or `docs/<version>/strategy.md`) with five required sections (Target Problem, Approach, Target Persona, Key Metrics, Tracks), an authoring flow and an amendment flow, framed as the product sibling of `project-constitution` (framing vs governance). Registered in all three data files (skills.json + statistics, marketplace workflow count, SKILL_INDEX).

4. **T014 - close the loop**: added a "Phase B.5: Knowledge-Base Grounding" step to `implementation-plan/SKILL.md` and a "Step 2.5: Knowledge-Base Grounding" to the `generate-plan` command (both: search `docs/solutions/` for prior solutions and read `STRATEGY.md` before designing phases); cross-linked `continuous-learning` -> `solution-knowledge-base` distinguishing runtime instincts (`.nexus/instincts/`) from durable solved-problem docs (`docs/solutions/`); noted in `known-gaps-tracker` how a resolved `BG` gap graduates into a solution doc (records *how*, not just *that*). Minimal edits, each traced to closing the loop.

5. **T015 - session-query skill + scripts**: created `catalog/skills/workflow/session-query/SKILL.md` (127 lines) plus four bundled scripts: `scripts/discover-sessions.{sh,ps1}` (enumerate `*.jsonl` under Claude `~/.claude/projects`, Codex `~/.codex`, Cursor `~/.cursor`, or a custom `--root`; print `tool<TAB>path`) and `scripts/extract-session.{py,ps1}` (read transcripts, apply topic / branch / time-window filters, emit a JSON digest). Script-first architecture; stdlib-only Python; strictly zero-outbound. Registered in all three data files. Added pytest at `tests/validators/test_session_query_extract.py` (13 cases: digest fields, time-window filtering, branch filter, malformed-line resilience, no-filter reporting, invalid-since error, and a zero-outbound static-analysis guard across all four scripts).

6. **T016 - stabilization**: ran the validators directly (make unavailable on host), the MCP skill-server suite, the full repo pytest, the static trigger-surface check for both new skills, and a PowerShell-parity smoke for the extractor; recorded the live-eval deferral (DF-v24-4); ran the post-phase documentation sequence.

## Troubleshooting

- **PowerShell variable-name collision (extract-session.ps1)**: the extractor crashed with `Could not compare "<datetime>" to ""`. Root cause: PowerShell variable names are case-insensitive, so a local `$since` aliased the `[string]$Since` parameter; assigning `$null` to a `[string]`-typed variable coerces it to `""`, which made `$hasWindow` ( `$null -ne $since` ) wrongly true and then `$ts -lt ""` failed. Fix: renamed the locals to `$sinceDt` / `$untilDt` / `$topicList` (no parameter collision) and hardened the window logic to test `$x -is [datetime]` instead of `$null -ne $x`. Verified empirically: topic / time-window / no-match runs now match the Python digest exactly.
- **`make` not on PATH (Windows host)**: invoked the `validate` target's commands directly with `python` (JSON-load + count reconciliation, `validate_skills.py --bundles-only` / `--quality`, the four CI validators, the solution-frontmatter validator). All exit 0.
- **CI did not cover `tests/skills/`**: the new extraction test was first placed at `tests/skills/`, but `.github/workflows/ci.yml` runs `pytest tests/integrations tests/installer` and `pytest tests/validators` - not `tests/skills`. Rather than edit CI config (approval-gated; Phase 7 T032 already plans CI broadening), relocated the test into `tests/validators/` (the established home for subprocess-based script-CLI tests like `test_validate_solution_frontmatter.py`), which CI already runs. `REPO_ROOT = parents[2]` is unchanged at the same depth.
- **Git Bash vs native-Python `/tmp` mismatch**: a discover->extract pipe smoke initially reported `files_matched=0` because Git Bash `/tmp` and native Python's `/tmp` resolve to different directories on Windows. Re-ran with a repo-relative path and confirmed `files_scanned=1 files_matched=1`. Environmental, not a script bug (pytest uses native `tmp_path`).
- **PSScriptAnalyzer unapproved-verb warning**: `Parse-Ts` / `Emit-Root` use unapproved PowerShell verbs; renamed to `ConvertTo-Utc` / `Write-RootMatches`.

## Assumptions

- T013 is a NEW `product-strategy` skill, not a `project-constitution` extension: the plan's prompt prefers this since the constitution is governance (MUST/SHOULD) while strategy is product framing (problem/approach/persona/metrics/tracks). The two are documented as siblings.
- The `.ps1` siblings for the per-skill scripts are mandatory (cross-platform parity rule applies to `.sh`/`.py` shipped under a skill's `scripts/`); the Python `extract-session.py` is the canonical, pytest-covered implementation and the `.ps1` mirrors it (parity verified empirically).
- Live `skill-eval-loop` runs stay deferred (no model CLI on PATH) consistent with DF-v24-1 / DF-v24-2 / DF-v24-3; a static trigger-surface check substitutes.
- Catalog count-prose in README.md ("208 skills") and AGENTS.md ("230 skills across 23 categories") stays deferred to the version bump per WN-v24-1; per-phase doc sync does not touch it.
- Coverage gate is not applicable to the doc skills (T013/T014 add Markdown); the session-query extractor (T015) is covered by 13 pytest cases.

## Testing results

- Registry reconciliation: skills.json array 244 == statistics.total_skills 244; workflow = 35 in skills.json / statistics / marketplace; marketplace category sum 244; SKILL_INDEX rows 244 and footer "244 skills across 21 categories"; both new frontmatter blocks parse as YAML; `summary_l0` 14 / 12 words; `overview_l1` 142 / 143 words (<=150).
- `make validate` equivalent (direct): JSON catalogs OK, orphan-bundle audit PASS 0/0 across 244 skills (all four session-query scripts referenced from SKILL.md), quality pass 0 errors / 576 warnings (pre-existing Phase-7 debt; neither new skill flagged), no-personal-paths / unicode-safety / supply-chain-iocs / workflow-security / solution-frontmatter all exit 0. All Phase-3 added lines are ASCII-clean (27/27).
- MCP skill-server (`extensions/nexus-skill-server`): 43 passed - confirms both new frontmatter blocks are consumed by the `search_skills` index.
- `tests/` (repo-level): 344 passed in ~5m47s, including the 13 new `test_session_query_extract.py` cases. No regression.
- `make lint`: shellcheck not installed on host (the Makefile lint target covers only `installer.sh` / `install.sh`); `bash -n` syntax OK on `discover-sessions.sh`; PowerShell `PSParser` parse OK on both `.ps1`; `set -euo pipefail` present.
- **PowerShell parity (PASS, empirical)**: `extract-session.ps1` topic run (files_matched=1, total=3, matched=2, branches=feature/login, snippets=2), window run (matched=2), and no-match run (files_matched=0) all match the Python digest.
- **Trigger-surface (PASS, static)** for both skills: `product-strategy` and `session-query` carry verbatim positive trigger phrases and an explicit `SKIP` clause; `summary_l0` <=15 words; `overview_l1` <=150 words.

## Deviations

- **DF-v24-4**: the live `skill-eval-loop` trigger run (1.0 positive / 0.0 fenced-negative) for `product-strategy` and `session-query` was deferred - no model CLI on PATH. Substituted with the static trigger-surface check above; foldable into Phase-8 T037 alongside DF-v24-1 / DF-v24-2 / DF-v24-3.
- **WN-v24-1 extended**: updated the count-prose deferral to the 244-skill truth (Phase 3 added `product-strategy` + `session-query`). No README / AGENTS.md prose edited this phase (deferred to bump).
- **CI test path**: relocated the new extraction test from `tests/skills/` into the CI-covered `tests/validators/` rather than editing CI config (see Troubleshooting). The per-skill `discover-sessions.sh` is not yet covered by CI shellcheck (CI lints only `catalog/hooks/*.sh`) - this is the existing QG-v23-1 gap that Phase 7 T032 broadens to `catalog/**/*.sh`; no new gap class introduced.
- No `# DEVIATION:` markers were left in any artifact; the plan was followed as written.

## Next steps

- Phase 5 (internal RE builds - re-full) follows: per-platform capability specs under `docs/specs/<platform>.md` (A6) and an installer `--branch` / `-Branch` testing flag (A9).
- Phase 8 T037 should fold in the deferred live `skill-eval-loop` runs for the Phase-1/2/3/4 skills (DF-v24-1 / DF-v24-2 / DF-v24-3 / DF-v24-4) when a model CLI is available.
- At the version bump, update the AGENTS.md / README.md count prose and regenerate the embedded SKILL INDEX (WN-v24-1).
