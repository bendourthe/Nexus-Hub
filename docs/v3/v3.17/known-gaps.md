# Known Gaps - v3.17

**Project**: Nexus-Hub
**Status**: v3.17.5 is released. v3.17.6 (CI gate hygiene and branch hygiene) is in progress on `feat/ci-gate-and-branch-hygiene`, Phase 1 of 6 complete: the required-check coverage guard is in place and intentionally fails this tree until Phase 2 migrates the two path-filtered workflows. Prior v3.17.0 through v3.17.5 records remain below.
**Last updated**: 2026-08-19 (v3.17.6 Phase 1 append)

> **File-lifecycle note**: this ledger was opened by the v3.17.0 Phase 1 append. Each subsequent v3.17.N implementation appends its own `## v3.17.N - <slug>` section rather than replacing this file, keeping its own `DF-#` / `NI-#` / `BG-#` / `WN-#` / `MT-#` / `QG-#` numbering.

> **Prior-version ingest**: checked `docs/v3/v3.15/known-gaps.md`. v3.15.2 DF-2 (Hermes registered but not installer-wired) carries forward as DF-4 because it remains a delivery limitation. v3.15.0 WN-1 (the Windows Git-Bash bootstrap `tar` failure) recurred and carries forward as WN-1. The v3.15.1 lint warnings involved files outside this plan and do not carry in. The v3.18.2 RTK and Meterless artifacts keep their established stamp under `docs/v3/v3.18/`; their stale pre-move references were corrected during Phase 6 rather than transferred as gaps.

---

## v3.17.6 - ci-gate-and-branch-hygiene

**Status**: Phase 1 of 6 complete (2026-08-19). The required-check coverage validator, its declared manifest, and its 30-test suite are in place and wired into `make validate` and CI's existing `validate` job. The guard intentionally exits 1 on this tree; clearing it is Phase 2's job. Work is isolated on `feat/ci-gate-and-branch-hygiene` so `develop` never carries a red required check. This section is appended to by each subsequent phase.

### QG-1 - OPEN by design: the guard fails this repository until Phase 2 lands

- **Target files**: `scripts/check_required_check_coverage.py`, `Makefile`, `.github/workflows/ci.yml`
- **What it is**: the validator reports 18 `CONDITIONAL` contexts (9 per protected branch), spanning 7 distinct jobs: `validate`, `shellcheck`, `bootstrap`, `tests`, `install-smoke`, `installer-smoke` (in `ci.yml`), and `colocation` (in `doc-colocation.yml`). Because the guard runs inside the `validate` job, and `validate` is itself a required context, `make validate` and CI both fail on this branch.
- **Why it is not a Phase 1 failure**: sub-task 1.1 specifies exactly this outcome ("exits 1 today (pre-migration) naming the seven offending checks, which is the evidence Phase 2 then clears"). A guard that passed here would be asserting nothing.
- **Why the work is branch-isolated**: landing Phase 1 alone on `develop` would leave a required check red, so every unrelated merge in the gap would need an administrator bypass. That is precisely the habit this plan exists to end, so Phase 1 and Phase 2 must reach `develop` together.
- **Suggested next step**: Phase 2 migrates both workflows to job-level `if:`, after which the guard must exit 0. Do not merge this branch before it does.

### MT-1 - OPEN limitation: matrix legs are resolved by job id, not verified against real legs

- **Target files**: `scripts/check_required_check_coverage.py`, `docs/policy/required-checks.json`
- **What it is**: a context of the form `job (leg)` resolves to its job id, and the parenthesised leg is informational only. Every matrix in `ci.yml` defines its `os` list as a `${{ ... fromJSON(...) }}` expression evaluated per event, so the legs cannot be enumerated statically without an expression evaluator.
- **What it means in practice**: a manifest entry naming a leg that no longer exists (say `installer-smoke (fedora-latest)`) resolves to the real `installer-smoke` job and PASSES. The guard catches a filtered workflow and a missing job; it does not catch a stale matrix leg.
- **Why it was not fixed here**: evaluating GitHub expression syntax is a materially larger build than this phase, and the failure mode it would catch is narrower than the one being fixed. Recorded so the limit is a known boundary rather than an assumed capability.
- **Suggested next step**: none required for v3.17.6. If leg drift ever bites, the cheap partial fix is to compare the leg set in `--sync` output against the manifest and warn on a difference, rather than to evaluate expressions.

### MT-2 - OPEN observation: the repository has no coverage instrumentation, so the 80% gate is unmeasurable in-suite

- **Target files**: `tests/validators/conftest.py`, `tests/validators/test_check_required_check_coverage.py`
- **What it is**: every validator test invokes its script as a **subprocess**, deliberately, so the test exercises the CLI surface a maintainer actually runs (stated in the `conftest.py` docstring). `coverage` therefore records nothing for those runs without `--parallel-mode` plus a `COVERAGE_PROCESS_START` shim, and the repository defines no coverage threshold, `[tool.coverage]` section, or `--cov` flag anywhere.
- **How the gate was satisfied**: line coverage of the new validator was measured at **90%** with a one-off out-of-tree in-process probe that replays the suite's own fixtures through `main()`. The probe is scratch tooling and is deliberately NOT committed, because committing it would create a second, divergent way to exercise the same code.
- **Why it is not a Phase 1 failure**: adding subprocess-coverage plumbing to a suite of 1819 tests is a repository-wide change with no bearing on this plan's goal.
- **Suggested next step**: if a future version wants an enforced coverage number, the change belongs in `conftest.py` and CI once, for all validators, not per phase.

### WN-1 - OPEN environmental: `make` is unavailable on the development host

- **Target files**: `Makefile`
- **What it is**: the host running this phase has no `make`, so the `validate` target's new recipe line was verified by direct script invocation plus a tab-indentation check (`cat -A`) rather than by executing the target. Its first real execution will be in CI.
- **Why it is low risk**: the recipe is a single `@python scripts/...` line adjacent to sixteen identical ones, and the CI `validate` job invokes the script directly rather than through `make`, so CI coverage of the guard does not depend on the Makefile edit being correct.
- **Suggested next step**: confirm the target runs end-to-end on a host that has `make`, or in Phase 2's proof PRs.

### BG-1 - CLOSED in implementation: a stripped-environment test wrote into the repository working tree

- **Target files**: `tests/validators/test_check_required_check_coverage.py`
- **What was wrong**: the first draft of the PyYAML-absence test ran its subprocess with `PATH=""` and no `APPDATA` / `LOCALAPPDATA`, and an earlier draft of the `--sync` test put a `gh.bat` stub on `PATH`. On Windows, Python resolves a bare `gh` to `gh.exe` only, so the stub was skipped and the **real** `gh` ran with no state directory. Between them the two tests created `.local/state/gh/` and a literal `%SystemDrive%/ProgramData/` directory inside the repository.
- **How it surfaced**: `git status` during the post-phase sequence, not by any test failing. Both tests passed while polluting the tree.
- **Resolution**: the `--sync` tests now monkeypatch `subprocess.run` in-process (portable, and a tighter assertion: they also verify only `gh api` is ever called, never a protection write). The PyYAML test inherits the real environment and runs with `cwd` set to its tmpdir. Both stray directories were removed and confirmed not to regenerate.
- **Lesson worth keeping**: a test that strips the environment to simulate a missing dependency will make every tool it touches fall back to relative paths. Set `cwd` to a tmpdir whenever you do that.
---

## v3.17.5 - adoption-deepseek-harness

**Status**: All seven phases complete (2026-08-18). The nine adoption items land as: B1 doc word budgets, A1 deepseek-harness skill, A2+A3+A4 skill extensions, B2 decision-record lifecycle, B4 registry drift-check, B3 invocation-policy frontmatter, and Phase 7 reconciliation. B5 is deferred by design with a reference shape recorded below. Ready for the `/update release` handoff; no release blockers. This section is appended to by each subsequent phase, and Phase 7 owns the final reconciliation.

### MT-1 - OPEN observation: AGENTS.md is 74% of the entire always-loaded budget

- **Target files**: `AGENTS.md`, `docs/policy/doc-budgets.json`
- **What it is**: the Phase 1 seeding measurement found `AGENTS.md` at 9138 words against 6633 words for the other seven budgeted docs combined. It is inlined into `CLAUDE.md` by an `@` import and mirrored into every platform instruction surface, so it is the single largest recurring token cost in the catalog.
- **Why it is not a Phase 1 failure**: the plan specifies seeding every ceiling at current size plus 10% headroom, which this does. The gate now measures the cost; it does not by itself reduce it.
- **Suggested disposition**: a ratchet-down pass on `AGENTS.md` (relocating per-topic sections to `docs/policy/` and `guides/reference/` files the agent reads on demand) is a candidate for Phase 7 or a follow-on version. Tracked here so the measurement is not silently accepted as the permanent baseline.

### QG-1 - CLOSED in implementation: the skill-registration surface is six places, not three

- **Target files**: `data/skills.json`, `data/SKILL_INDEX.md`, `data/bundles.json`, `AGENTS.md`, `docs/v3/v3.17/plans/v3.17.5-adoption-deepseek-harness.md`
- **What was wrong**: the Phase 2 prompt and the standing `AGENTS.md` rule both name three registry files. Registering a skill actually touches six places: the `SKILL_INDEX.md` row AND its `**Total: N skills**` line; the `skills.json` entry AND its `statistics.total_skills` / `statistics.categories` map; the `marketplace.json` category count AND plugin description; and `data/bundles.json`'s capability `modules`, which have been CATEGORY-COMPLETE since schema 1.5.0 so that every skill is reachable by a focused install.
- **How it surfaced**: `test_registry_consistency.py` caught the four `statistics` / total-line omissions immediately. The sixth surface was caught only by `tests/integrations/test_selective_install.py::test_every_catalog_skill_is_reachable_through_some_module`, which failed with "1 catalog skills are reachable only via `full`". That suite takes about 30 minutes locally, so the gap is invisible to a fast validator loop.
- **Resolution**: all six updated; `deepseek-harness` added to the `ai-engineering` module. Folding the full list into the `AGENTS.md` "Register the skill" instructions is recommended follow-on work so the next author is not relying on a 30-minute suite to discover surface six.

### MT-2 - OPEN observation: plan-time catalog counts go stale

- **Target files**: `docs/v3/v3.17/plans/v3.17.5-adoption-deepseek-harness.md`
- **What it is**: the plan was authored 2026-08-14 against a 271-skill catalog and specified landing at 272. The catalog had reached 272 by implementation time, so Phase 2 landed at 273.
- **Why it matters**: a plan that hardcodes an absolute target count invites a wrong edit whenever implementation lags authoring. Counts were verified against four independent sources before editing, per the v3.16.1 lesson.
- **Suggested disposition**: plans should express catalog counts as a delta ("+1 skill") rather than an absolute target.

### MT-3 - CLOSED by design decision: A4 executive-summary block adapted rather than added

- **Target files**: `catalog/skills/infrastructure/incident-postmortem/SKILL.md`
- **What the plan asked for**: a new mandatory 30-second Executive Summary block at the top of the postmortem template, before the timeline.
- **Why it was adapted**: the skill already required a `Summary` section as required-section 1, positioned above the timeline. Adding a second summary beside it would have produced two competing top-of-document summaries and made the template worse.
- **What was done instead**: the existing `Summary` spec was rewritten in place to BE the 30-second executive summary and to require all four elements the plan named, including the two that were missing (why the process let the failure escape, and the durable lesson). The intent is fully delivered without duplicating structure. This is the one non-additive line in the Phase 3 diff.

### MT-4 - CLOSED by user decision: Phase 4 migration step rested on a false premise

- **Target files**: `docs/v3/v3.17/plans/v3.17.5-adoption-deepseek-harness.md`, `catalog/memory/decisions.md`
- **What the plan asked for**: migrate `.claude/memory/decisions.md` into dated records and replace its body with a pointer.
- **Why it could not be done**: that file does not exist in this repository. The only `decisions.md` is `catalog/memory/decisions.md`, a blank ADR template the installer distributes to every end user's `~/.claude/memory/`. It holds no Nexus-Hub decisions. Editing it would change what users receive on their next install, which is a distribution change, not a memory consolidation.
- **Resolution**: the user was asked and chose to skip the migration. The template is untouched. `scripts/validate_decision_records.py` guards the confusion in both directions (a memory file containing `# Decision:` fails with a relocation hint; one holding only the ADR template passes), and both directions are tested.
- **Carry-forward**: a comparison-seeded plan can inherit a path from the source project that does not exist in the target. Plans should verify that a named migration source exists before listing it as an acceptance criterion.

### MT-5 - RESOLVED in Phase 7: registry text drift repaired and the gate hardened

- **Target files**: `data/skills.json`, `data/SKILL_INDEX.md`
- **What it is**: the Phase 5 drift-check found that 107 of 273 skills have at least one registry text field disagreeing with their SKILL.md frontmatter: 74 `description`, 51 `overview_l1`, 16 `summary_l0` in `skills.json`, and 15 `summary_l0` in `SKILL_INDEX.md`.
- **Causes are mixed**: genuine staleness (a SKILL.md edited without its entry, e.g. `google-antigravity-sdk`'s `summary_l0`), plus at least six cases of real **encoding corruption** where `skills.json` holds `U+00E2 U+20AC U+201D`, the cp1252 rendering of the UTF-8 bytes for an em-dash, against a clean `U+2014` in SKILL.md. The corrupted file ships to users and feeds the MCP search server.
- **Why it is not fixed in Phase 5**: repairing it rewrites `description` for 74 skills. Descriptions are the routing surface that `run_trigger_evals.py` scores, and Phase 2 demonstrated that a single description edit moves neighbouring skills' scores. A routing-affecting rewrite of a distributed registry belongs in its own change, not inside a phase whose subject is building the checker.
- **Current containment**: `check_registry_entries.py` reports the drift on every run and fails it under `--strict`; structural drift is already a hard gate. `tests/validators/test_check_registry_entries.py::test_the_real_tree_reports_its_text_drift_rather_than_hiding_it` asserts the reporting stays visible, so the backlog cannot silently vanish.
- **Resolution (Phase 7, maintainer chose the full repair)**: all 156 fields synced from SKILL.md, which is the source of truth because it is the file agents actually load. 141 fields in `skills.json` and 15 summaries in `SKILL_INDEX.md`. The six encoding-corrupted entries now carry the same `U+2014` their source does. `check_registry_entries.py --check --strict` is now the gate in both `make validate` and CI, so any reappearance is a fresh regression rather than inherited debt.
- **Correction to the Phase 5 risk assessment**: Phase 5 recorded that repairing this would rewrite 74 routing descriptions and therefore needed a full eval re-run. That caution was overstated for this direction. `run_trigger_evals.py` scores descriptions read from `catalog/skills/`, not from `skills.json`, so syncing the registry FROM SKILL.md cannot move a routing score by construction. The eval gate was re-run anyway and passed with 0 failures. The caution remains correct for the opposite direction, editing SKILL.md itself.

### DF-1 - OPEN (deferred): five platforms not yet surveyed for invocation-policy levers

- **Target files**: `docs/policy/skill-invocation-policy-levers.md`
- **What it is**: the Phase 6 survey covered `claude`, `copilot`, `cursor`, `codex`, and `antigravity2` against fetched vendor documentation. The v3.17.5 release-pass contract re-verification added `qwen`, which turned out to document BOTH fields with matching semantics and is now recorded VERIFIED. `opencode`, `kimi`, `hermes`, and `nexus-ai` remain unsurveyed.
- **Why it matters**: the table records them as NOT SURVEYED, deliberately distinct from "none documented". The first means nobody looked; the second means someone read the vendor page. Collapsing the two is how an unchecked assumption becomes a recorded fact, which is the failure mode the do-not-invent rule exists to prevent.
- **Impact if left**: none functionally. Those platforms receive `SKILL.md` verbatim, so a declared field reaches them and is ignored if unrecognised. The gap is in the record, not the behavior.
- **Suggested disposition**: complete the survey in the next release pass that already re-verifies platform contracts, since `[[platform-contract-verification]]` visits the same vendor documentation. That is exactly how `qwen` was closed here: the contract re-verification was reading the same vendor page, so checking the invocation fields cost nothing extra. Fold the remaining four into the same pass.

### MT-6 - OPEN observation: the Codex invocation mapping is built but unexercised

- **Target files**: `scripts/lib/integrations/_catalog_adapters.py`
- **What it is**: no catalog skill declares `disable-model-invocation`, so `codex_invocation_policy` currently emits nothing on every install.
- **Why it exists anyway**: the maintainer chose to build it while the survey evidence was fresh, accepting the scope-fit trade-off explicitly. The inverted polarity is exactly the detail that is expensive and error-prone to re-derive later.
- **Containment**: `tests/integrations/test_codex_invocation_policy.py::test_the_shipped_catalog_declares_no_manual_only_skill` asserts today's state and fails when the first skill declares the field, which is the moment to re-check installer smoke expectations.

### DF-2 - DEFERRED by design: B5 gate-DAG runner for `make validate`

- **What it is**: the comparison's B5 item, a dependency-aware scheduler (needs-graph, cycle detection, `allowFailure`, bounded concurrency) replacing the sequential `make validate` chain.
- **Why deferred, not dropped**: the `Boundaries` scope-fit rule in `AGENTS.md` says not to add the structure before the pain. This plan added three validators, taking the chain to roughly thirty sequential steps that still complete in seconds. A DAG scheduler would be real machinery with no measured problem to solve.
- **Reference shape for whoever picks it up**: the source project's `scripts/run-gates.ts` (890 lines, 14 aggregates), described in `docs/v3/v3.17/comparisons/v3.17.5-comparison-deepseek-harness.md` under B5. Reach for it when validator wall-clock, not validator count, becomes the complaint.

### MT-7 - OPEN observation: nine skill descriptions contain non-ASCII punctuation

- **Target files**: nine `SKILL.md` files, listed in the Phase 7 session history.
- **What it is**: surfaced while repairing MT-5. Nine skills carry an em-dash (`U+2014`) in their `description` frontmatter, against the project's ASCII-only prose rule and the `anti-slop-editing` em-dash discipline.
- **Why it was not fixed here**: `description` is the routing surface that `run_trigger_evals.py` scores. Editing nine of them is the direction where the Phase 5 caution genuinely applies, and it is unrelated to this plan's scope. `validate_unicode_safety.py` passes, so nothing is broken today.
- **Suggested disposition**: fold into a prose pass that re-runs the trigger-eval gate, rather than a release-eve edit.

### NI-1 - NOT IMPLEMENTED by design: `docs/solutions/` remains absent

- The three-surface split written in `docs/decisions/README.md` names `docs/solutions/` as the home for solved problems with reproduction context. The directory does not exist yet, and the `solution-knowledge-base` skill creates it on first use.
- Recorded here so the split's third surface is a known future consolidation rather than an apparent inconsistency in the README. Nothing is broken by its absence: the split defines boundaries, and an empty boundary is still a boundary.

### BG-1 - CLOSED in Phase 7: a hardcoded catalog total broke an unrelated test

- **Target files**: `tests/skills/test_org_authoring_surface.py`, `catalog/skills/workflow/verification-before-completion/SKILL.md`
- **What was wrong**: `test_org_authoring_surface.py` is about ONE skill's registration, but it also froze the whole-catalog total in three places (`total_skills == 272`, the index total line, and the marketplace plugin description). Phase 2 took the catalog to 273 and broke it. The failure survived until the Phase 7 full-suite run because every scoped evidence set in Phases 2 through 6 covered `tests/validators`, `tests/integrations`, and `catalog/hooks/tests`, and this test lives in `tests/skills`.
- **Resolution**: the totals are now DERIVED from `len(skills["skills"])` inside that test, so it asserts consistency without freezing a number that changes every time a skill is added. The count invariant itself is owned by `test_registry_consistency.py`, which derives it from disk in both directions. A grep confirmed no other test hardcodes the old total.
- **Root-cause fix beyond the immediate break**: the change-surface table added to `verification-before-completion` in Phase 3 had no row for this case. It does now: a catalog-wide count is a global invariant, so a change to it requires grepping the old value across the whole test tree rather than reasoning about which suite "should" own it. The discipline this plan shipped is what failed here, so the discipline was the thing to repair.

### WN-1 - OPEN (carried, environmental): re-confirmed during v3.17.5 Phase 2

- `tests/installer/test_bootstrap.py::test_ps_standalone_extracts_and_hands_off` failed again in the Windows Git-Bash development environment on the same `/usr/bin/tar: unexpected end of file` quirk. Phase 2 touched no installer or bootstrap file, so this is the carried v3.15.0 item, not a regression. CI remains authoritative and passes.

### Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented by design / unverified (`NI-#`) | 1 (NI-1, `docs/solutions/` absent by design) | 0 |
| Deferred (`DF-#`) | 2 (DF-1 five platforms unsurveyed; DF-2 B5 gate-DAG runner) | 0 |
| Bugs (`BG-#`) | 0 | 3 (BG-1 hardcoded catalog total; plus the `size` schema violation and the `loop-engineering` index category, both found by the Phase 5 drift-check) |
| Warnings (`WN-#`) | 1 (WN-1, environmental, carried from v3.15.0) | 0 |
| Maintenance / tech debt (`MT-#`) | 4 (MT-1 AGENTS.md budget share; MT-2 plan-time counts; MT-6 mapping unexercised; MT-7 non-ASCII descriptions) | 3 (MT-3, MT-4, MT-5) |
| Quality gates (`QG-#`) | 0 | 1 (QG-1, six registration surfaces) |

**Release blockers: none.** Every open item is an observation, a deliberate deferral, or a carried environmental failure that CI does not reproduce.

---

## v3.17.3 - cursor-hook-portability-and-usage-monitor-reliability

**Status**: Released on 2026-08-16. The scope was limited to Cursor hook portability, Codex Extra Credits live-payload mapping, shared warning-color stability, release metadata, and the renumbering of unreleased plans.

### BG-1 - CLOSED in implementation: Windows Cursor inherited Bash hook commands

- **Target files**: both installers, `scripts/lib/integrations/cursor.py`, `catalog/hooks/cursor-hook-compat.py`, and Cursor installer/integration tests
- **What was wrong**: Cursor imported Claude Code hooks whose commands invoked `bash C:/...` even on Windows. A missing or mismatched Bash runtime produced empty or non-JSON stdout, and Cursor failed closed before write-producing commands such as `/implement` could run.
- **Resolution**: Windows now installs and registers the existing PowerShell hook siblings, macOS and Linux retain Bash, and a shared compatibility launcher emits one Cursor allow-or-deny JSON response while keeping diagnostics on stderr and preserving deny decisions.

### BG-2 - CLOSED in implementation: usage-monitor refreshes raced over one shared warning color

- **Target files**: both usage monitors' `src/types.ts` files and their regression tests
- **What was wrong**: low and critical refresh ticks reset `statusBarItem.warningBackground` to the Moderate color even though those urgency levels do not use that token, overwriting another monitor's active High color.
- **Resolution**: only Moderate and High urgency updates may write the shared warning token; low and critical ticks leave it untouched.

### BG-3 - CLOSED in implementation: Codex Extra Credits ignored the live spend-control shape

- **Target files**: `extensions/codex-usage-monitor/src/providers/codex.ts` and `test/codex-usage-mapping.test.ts`
- **What was wrong**: the live response exposes detailed Extra Credits usage under `spend_control.individual_limit`, which the mapper did not inspect.
- **Resolution**: the mapper accepts snake-case and camel-case spend-control aliases and exposes the detailed used amount, monthly limit, percentage, and reset date.

### Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented by design / unverified (`NI-#`) | 0 | 0 |
| Deferred (`DF-#`) | 0 | 0 |
| Bugs (`BG-#`) | 0 | 3 |
| Warnings (`WN-#`) | 0 | 0 |
| Missing tests (`MT-#`) | 0 | 0 |
| Quality-gate bypasses (`QG-#`) | 0 | 0 |

**Release blockers**: 0 identified before final verification. The v3.17.2 DF-6 migration remains installed through this expedited release and is retargeted to v3.17.4 so delayed v3.17.0 and v3.17.1 upgrades retain their recovery path.

## v3.17.2 - remove-autonomy-controller

**Status**: Controller removal was implemented in `cced5285`, integrated into `develop` by merge commit `3004fb19`, and pushed to `origin/develop` on 2026-08-15. Release preparation adds a fail-safe legacy-state migration on `release/v3.17.2`; final gates, promotion, tag, and GitHub Release remain pending.

### BG-1 - CLOSED in implementation: the controller could not guarantee universal approval

- **Target files**: `scripts/lib/autonomy.py`, `scripts/lib/autonomy_cli.py`, `scripts/nexus_hub_cli.py`, both usage-monitor extensions, the autonomy hooks, and feature-specific CI
- **What was wrong**: VS Code exposes no supported public API that lets one extension override another provider extension's approval decisions. The controller could write documented provider settings, but that only duplicated the providers' existing mode selectors and could not force actions that Claude Code, Codex, or another provider still classified as requiring confirmation.
- **Why removal is the fix**: the intended product was a provider-independent approval bypass. Keeping a wrapper around provider-native modes would preserve the implementation cost and security surface while failing that acceptance criterion.
- **Resolution**: remove the shared engine and CLI, integration descriptors, usage-monitor indicators and toggles, expiry and guard hooks, feature-specific tests and CI, and active product documentation. Provider-native approval controls remain owned by each provider.
- **Retained v3.17.0 work**: read-only permission-baseline hardening, shared permission merging, generic installer parity, real-install smoke coverage, and consequential-decision guidance remain independent and supported.

### Retired feature-specific v3.17.0 gaps

- **NI-3** (descriptor coverage) is no longer actionable because descriptors are removed from the product contract.
- **WN-4** (hook independence under provider no-prompt modes) remains historical evidence only; Nexus-Hub no longer claims or tests that product boundary.
- **MT-1** remains only as general Claude Usage Monitor coverage debt. The feature-specific `coverage.include` boundary and its deleted module are removed.

### BG-9 - CLOSED in release preparation: controller removal could leave elevated provider state behind

- **Target files**: `catalog/hooks/retire-provider-override.py`, `catalog/hooks/settings.json`, both installers, and their migration tests
- **What was wrong**: deleting the engine, CLI, and expiry hook stopped future controller use but did not restore a provider config already changed by v3.17.0 or v3.17.1. A stale `autonomy-expiry` or `autonomy-guard` registration could also remain in Claude settings after its script was removed.
- **Resolution**: both installers now deploy and invoke one idempotent retirement helper. It restores only version-1 state entries whose config and backup paths remain inside the repository, preserves unresolved entries on every unsafe or missing-backup path, removes stale controller hook registrations while retaining unrelated user hooks, and installs a temporary SessionStart retry for projects that were not open during upgrade.
- **Verification**: focused migration, installer, removed-surface, and Codex integration suites pass 58 tests; syntax and PowerShell AST checks pass.

### DF-6 - RESOLVED in v3.17.4: temporary retirement migration removed after one compatibility release

- **Target files**: `catalog/hooks/retire-provider-override.py`, `catalog/hooks/settings.json`, both installers, and their migration tests
- **Compatibility window**: the helper remained available through v3.17.3 so delayed upgrades from v3.17.0 and v3.17.1 retained their recovery path.
- **Resolution**: v3.17.4 removes the helper, SessionStart registration, installer wiring, and migration-specific tests. The hook count returns from 32 to 31, while the v3.17.2 record remains the historical description of the completed migration.

### WN-5 - OPEN advisory: per-model prompting profiles lag the current model roster

- **Target files**: `catalog/skills/ai-development/model-prompting-research/` and its recorded profile roster
- **Source phase**: v3.17.2 release preparation model-prompting freshness advisory
- **Reason it is open**: the required release advisory returned `DRIFTED`. The routing map itself is valid and was re-verified on 2026-08-15, but the separate prompting-profile layer still records its 2026-07-27 roster and lacks profiles for the newly mapped Anthropic, OpenAI, Google, and Cursor model IDs. This is intentionally advisory and is unrelated to the provider-state restoration defect fixed by v3.17.2.
- **Suggested next step**: run `/tune-prompting` in a dedicated model-prompting refresh cycle, update the recorded roster and affected profiles from current first-party guidance, then rerun `python scripts/check_model_prompting_freshness.py --advisory <live-model-ids>` until it reports `IN SYNC`.
- **Phase 6 recheck**: The live Codex roster contains `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.3-codex`, `gpt-5.2`, and `codex-auto-review`, while the profile layer still records the 2026-07-27 Anthropic roster. The advisory returned `DRIFTED` without blocking Phase 6; the dedicated `/tune-prompting` follow-up remains unchanged.

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented by design / unverified (`NI-#`) | 0 | 0 |
| Deferred (`DF-#`) | 0 | 1 (DF-6) |
| Bugs (`BG-#`) | 0 | 2 (BG-1, BG-9) |
| Warnings (`WN-#`) | 1 (WN-5) | 0 |
| Missing tests (`MT-#`) | 0 | 0 |
| Quality-gate bypasses (`QG-#`) | 0 | 0 |

**Release blockers**: 0. DF-6 remained a deliberate one-release compatibility window for v3.17.2 and is resolved by its scheduled v3.17.4 removal.

## v3.17.0 - agent-autonomy-toggle

**Status**: Phase 6 finalized (2026-08-15). 12 open (NI-1, NI-2, NI-3, DF-1, DF-2, DF-3, DF-4, DF-5, WN-1, WN-2, WN-4, MT-1) and 8 closed (BG-1, BG-2, BG-3, BG-4, BG-5, BG-6, BG-7, WN-3), 0 release blockers. The full local repository suite exceeded the bounded 15-minute Windows run; focused suites and hard validators are green, and protected-branch remote CI passed on the integrated `develop` tree. Plan: [plans/v3.17.0-agent-autonomy-toggle.md](plans/v3.17.0-agent-autonomy-toggle.md).

### NI-1 - OPEN: output redirection under an explicit allow rule is UNVERIFIED

- **Target file**: [development/permission-matcher-findings.md](development/permission-matcher-findings.md) (Finding 2), `scripts/validate_permission_baseline.py` (the `redirect` rule)
- **Source phase**: v3.17.0 Phase 1, sub-task 1.1
- **Plan reference**: 1.1 required determining empirically "whether Claude Code's matcher treats a redirected command as matching the bare pattern"
- **Reason it is open**: the official permissions documentation demonstrably models redirects, but states it only for the BUILT-IN read-only command set, never for explicit `allow` rules. Redirection operators are also absent from the enumerated command-separator list, so a redirected command is one subcommand rather than two, and a wildcard "matches any sequence of characters including spaces". Per this plan's evidence discipline, absence of a statement is recorded as UNVERIFIED rather than as absence of the behavior.
- **Why it is load-bearing**: `> file` truncates its target regardless of what the command emits (`Write-Host x > f` writes nothing to the file and still truncates it). If the native matcher admits redirects under allow rules, then EVERY baseline pattern carrying a trailing wildcard is a file-destruction primitive, and no per-entry rescoping repairs that. This is a global property of the matcher, not a defect of any individual entry, which is why Phase 1.1 did not attempt to fix it per-entry.
- **Suggested next step**: run the empirical probe named in Finding 2 against a throwaway project and a current Claude Code build: add one `Bash(echo *)` allow rule and observe whether `echo x > /tmp/probe` prompts. Phase 4 verified hook independence but did not execute this separate native-matcher probe, so the evidence remains UNVERIFIED.

### NI-2 - OPEN: whether Gemini's matcher splits compound commands at all

- **Target file**: `configs/permissions/gemini-permissions.json`, [development/permission-matcher-findings.md](development/permission-matcher-findings.md) (Finding 1)
- **Source phase**: v3.17.0 Phase 1, sub-task 1.1
- **Reason it is open**: Finding 1 VERIFIED compound-command splitting for Claude Code, quoted from its documentation, for both the Bash and the PowerShell matcher. No equivalent statement was located for Gemini's `run_shell_command`, and the file's own shipped comment records the opposite direction ("piped commands bypass allowlists (upstream issue)"). Gemini entries are therefore treated as PREFIX matches with no separator awareness, which is the conservative reading and is what `validate_permission_baseline.py` implements via its `prefix` match mode.
- **Why it matters**: under prefix semantics with no splitting, `run_shell_command(git status)` would admit `git status; rm -rf .`. The validator's conservative mode does not make that safe; it only stops Nexus-Hub from shipping patterns that depend on splitting.
- **Suggested next step**: run a dedicated Gemini CLI matcher probe and record a MATCH, DRIFT, or UNVERIFIED verdict beside the permission findings. Phase 2 verified autonomy levers, not compound-command matcher semantics. If splitting is absent, harden the Gemini baseline under prefix-without-splitting assumptions before expanding its Windows-shell coverage.

### NI-3 - OPEN by design: eight integrations have no autonomy descriptor

- **Target files**: `docs/policy/platform-read-contracts.json`, `docs/policy/platform-read-contracts.md`, `scripts/lib/integrations/`
- **Source phase**: v3.17.0 Phase 2, sub-tasks 2.2 and 2.4
- **Disposition**: deliberate non-delivery. Aider, Gemini Code Assist, Gemini CLI, and OpenClaw are DRIFT because their real controls cannot be represented safely by the one-file, project-scoped descriptor contract. Antigravity 1.0, Hermes, Nexus-AI, and Windsurf are UNVERIFIED because current first-party evidence does not establish a seedable general autonomy mode.
- **Why it remains open**: absence is the safe behavior. The descriptor accessor returns none and the UI or CLI reports the unsupported platform rather than approximating a broader or incomplete authority state.
- **Suggested next step**: re-run `platform-contract-verification` when a vendor publishes a new persistent autonomy contract. Add a descriptor only after its verdict becomes MATCH and its scope fits the workspace-bound product rule.

### DF-1 - OPEN: `gemini-permissions.json` ships no PowerShell or `cmd.exe` read-only set

- **Target file**: `configs/permissions/gemini-permissions.json`, `docs/permissions-research.md`
- **Source phase**: v3.17.0 Phase 1, sub-task 1.1 (observation only, by instruction)
- **Plan reference**: 1.1 explicitly forbids adding one ("this sub-task rescopes existing entries and deliberately does not expand coverage") and hands the observation to sub-task 5.3
- **Reason it is open**: a Windows Gemini user receives a POSIX-shaped allowlist plus a bare `run_shell_command(dir)`, so their real shell is effectively uncovered. Expanding coverage is a different risk decision from rescoping and belongs with the platform-coverage work.
- **Suggested next step**: `docs/permissions-research.md` now documents the gap. Resolve NI-2 before designing a PowerShell or general `cmd.exe` baseline, because the safe pattern shape depends on whether the matcher splits compound commands.

### DF-2 - OPEN: three of four platforms have no project-scoped permission target

- **Target file**: `scripts/installer.sh` and `scripts/installer.ps1` (`install_permissions` / `Install-Permissions`, workspace branch)
- **Source phase**: v3.17.0 Phase 1, sub-task 1.2
- **Reason it is open**: workspace scope is now wired and load-bearing, but only Claude Code has a confirmed target (`.claude/settings.local.json`). The other three skip WITH A NOTE, each for a stated reason: **Gemini** and **Codex** have no project-scoped permission path documented well enough to write, and a guessed path is worse than none because it reads as configured; **Copilot**'s only surface is `.vscode/settings.json`, which is commit-visible and therefore forbidden here without an explicit maintainer decision (the same reasoning that made the v3.11.0 Copilot `.github/skills/` surface opt-in).
- **Suggested next step**: run a permission-path-specific contract sweep for Gemini and Codex; the Phase 2 autonomy sweep answered a different question. The Copilot half needs a maintainer decision about writing to a commit-visible file, not more research.

### DF-3 - OPEN: `Install-Nexus-Hub-Permissions.ps1` still has no cross-platform equivalent

- **Target file**: `scripts/Install-Nexus-Hub-Permissions.ps1`, `scripts/nexus_hub_cli.py`
- **Source phase**: v3.17.0 Phase 1, sub-task 1.2 (deferred by that sub-task's own instruction)
- **Reason it is open**: that helper provides install, uninstall, and backup-repair paths for all four platforms and has no bash sibling, so POSIX users have no equivalent repair route. Sub-task 1.2 forbids porting it to bash, and correctly: a second shell script would recreate exactly the dual-implementation drift this phase removed.
- **Suggested next step**: expose install / uninstall / repair through the cross-platform `nexus-hub` CLI, whose `scripts/nexus_hub_cli.py` now includes the Phase 5 `autonomy` subcommand. One implementation, three operating systems. Phase 5 shipped autonomy only, so this separate lifecycle gap carries forward.

### DF-4 - OPEN (carried from v3.15.2): Hermes is registered but not installer-wired

- **Target files**: `scripts/lib/integrations/hermes.py`, `scripts/installer.sh`, `scripts/installer.ps1`
- **Source phase**: v3.15.2 DF-2, rechecked in v3.17.0 Phases 2 and 6
- **Reason it is open**: Hermes exists in the 16-platform integration registry but is absent from both installers' 14-platform delivery roster. Hermes is currently UNVERIFIED for autonomy, so the omission does not suppress a descriptor in this release; it would become user-visible immediately if its contract later verifies.
- **Suggested next step**: add Hermes to both installer manifests and real-installer smoke coverage in the same change that makes any Hermes integration artifact user-facing. Do not add one installer arm without the other.

### DF-5 - OPEN by design: the read-only baseline covers only four of 16 integrations

- **Target files**: `configs/permissions/`, `scripts/installer.sh`, `scripts/installer.ps1`, `docs/permissions-research.md`
- **Source phase**: v3.17.0 Phase 6 reconciliation of the Phase 1 and Phase 2 coverage boundaries
- **Disposition**: deliberate non-delivery. Claude Code, Codex, Gemini, and Copilot receive the existing baseline. Aider, Antigravity 1.0, Antigravity 2.0, Cursor, Gemini CLI, Hermes, Kimi, Nexus-AI, OpenClaw, OpenCode, Qwen, and Windsurf receive no Nexus-Hub read-only baseline.
- **Why it remains open**: autonomy coverage and read-only allowlist coverage are independent. This release widened the former and deliberately did not invent permission matchers for platforms whose safe read-only contracts were not researched.
- **Suggested next step**: handle one platform at a time through a permission-contract research and validator cycle. Do not infer baseline safety from the existence of an autonomy descriptor.

### WN-1 - OPEN (carried, environmental): `test_bootstrap.py` PowerShell hand-off failure

- **Target file**: `tests/installer/test_bootstrap.py::test_ps_standalone_extracts_and_hands_off`
- **Source phase**: v3.17.0 Phase 1, sub-task 1.4 (confirmed pre-existing, not caused here)
- **Reason it is open**: this fails in the Windows Git-Bash development environment on an environmental `tar` quirk. It is the v3.15.0 WN-1 item, which the v3.17.0 plan's dependency section predicted would recur during installer work. CI is authoritative for this test and passes.
- **Suggested next step**: none in this cycle. Do not treat a local failure of this one test as a regression from Phase 1; the phase touched neither the bootstrap scripts nor the tarball path.

### WN-2 - OPEN (pre-existing tooling debt): integration framework has no clean repository-wide Ruff baseline

- **Target file**: `scripts/lib/integrations/`
- **Source phase**: v3.17.0 Phase 2, sub-task 2.4 (lint verification)
- **Reason it is open**: an exploratory `python -m ruff check scripts/lib/integrations tests/integrations/test_autonomy_descriptors.py` reported 180 existing modernization, import-order, mutable-class-config, and unused-code findings across the integration framework. The Phase 2 test file passes focused Ruff validation, and Phase 2 did not suppress or introduce a new lint rule; cleaning the framework would be an unrelated broad refactor.
- **Suggested next step**: establish a deliberate Ruff baseline or scoped rule set in a dedicated lint-maintenance cycle, then reduce the existing findings in reviewable batches rather than mixing them into a release architecture phase.

### WN-3 - CLOSED in Phase 6: usage-monitor Vitest configs warned about the future native loader

- **Target files**: `extensions/claude-usage-monitor/vitest.config.mts`, `extensions/codex-usage-monitor/vitest.config.mts`
- **Source phase**: v3.17.0 Phase 5, sub-task 5.4 (test verification)
- **Plan reference**: 5.4 requires both extension suites and coverage gates to run cleanly.
- **Resolution**: both configs were renamed from `.ts` to `.mts`, matching the warning-free convention already used by the GitHub and Cursor monitors. Claude passed 11 tests and Codex passed 81 tests under Vitest 4.1.10 with no native-loader warning.

### WN-4 - OPEN (bounded verification): hook independence is verified only for Claude Code 2.1.156

- **Target files**: `docs/policy/platform-read-contracts.md`, `docs/v3/v3.17/development/history/2026-08-14_agent-autonomy-toggle-phase-4-deny-layer-and-hook-independence.md`
- **Source phase**: v3.17.0 Phase 4, sub-task 4.1
- **Evidence**: all six combinations of `acceptEdits`, `bypassPermissions`, and `--dangerously-skip-permissions` with Bash and Write reached the blocking project `PreToolUse` hook and created no marker file on Claude Code 2.1.156.
- **Why it remains open**: the result is a versioned empirical contract, not a vendor guarantee that all future permission or hook architectures preserve the same ordering.
- **Suggested next step**: repeat the six-case probe during `platform-contract-verification` after a material Claude permission or hook architecture change. Do not generalize this evidence to other platforms.

### MT-1 - OPEN (pre-existing coverage debt): Claude Usage Monitor lacks an extension-wide coverage baseline

- **Target file**: `extensions/claude-usage-monitor/src/`, `extensions/claude-usage-monitor/vitest.config.ts`
- **Source phase**: v3.17.0 Phase 5, sub-tasks 5.2 and 5.4
- **Plan reference**: 5.4 requires extension coverage of at least 80 percent.
- **Reason it is open**: the new autonomy state machine reaches 91.66 percent line coverage and is enforced at that explicit feature boundary, but enabling coverage over every imported Claude monitor module measured only 14.07 percent lines because the pre-existing provider, store, recommendation, type, and status-bar modules have little or no test coverage. Expanding those legacy tests is unrelated to the autonomy surface and would materially widen Phase 5.
- **Suggested next step**: add tests for the legacy Claude monitor modules in risk order, then remove the `coverage.include` feature boundary once the whole extension clears the same 80 percent line and statement floor that the Codex monitor already meets.

### BG-1 - CLOSED in Phase 1: `installer.ps1` kept mutation-capable entries on upgrade

- **Target file**: `scripts/installer.ps1` (`Install-Permissions`), `scripts/merge_permissions.py`
- **Source phase**: v3.17.0 Phase 1, sub-task 1.2 / amendment A3 bug 2
- **What was wrong**: the checkpoint commit converted `installer.sh` to the shared `merge_permissions.py` helper and left `installer.ps1` on its own native union merge. A union cannot retire an entry, so removal propagation -- the fix that strips retired mutation-capable entries from an existing user's config -- worked on macOS and Linux and silently did nothing on Windows. Every entry the Phase 1.1 hardening removed would have stayed auto-approved forever on every already-installed Windows host.
- **Why it is recorded rather than dropped**: this is amendment A2's thesis demonstrated inside the phase that motivated it. The drift was introduced WHILE fixing the original instance of the same class, by a maintainer who cannot routinely exercise the other two operating systems. That is the argument for parity being a standing gate rather than a per-cycle rediscovery.
- **Resolution**: `installer.ps1` ported to `merge_permissions.py`, which is now the only merge implementation in the repository. Both installers are asserted byte-identical for the same input by `tests/installer/test_permission_scope_parity.py::test_both_installers_produce_an_identical_merged_config`, which also asserts the retired entry is gone, the user-added entry survives, and template metadata does not leak. The Copilot scalar key was routed through the same helper, which additionally removed the `jq` dependency that made the new Git-Bash arm reachable.

### BG-2 - CLOSED in Phase 1: the validator passed its own motivating example

- **Target file**: `scripts/validate_permission_baseline.py` (rule 3b, `UNSAFE_SUBCOMMANDS` / `DUAL_MODE_SUBCOMMANDS`)
- **Source phase**: v3.17.0 Phase 1, sub-task 1.4 (found by the tests written for 1.3)
- **What was wrong**: `Bash(gh api *)` -- the entry the validator's docstring cites as its motivating example, and the exact fixture sub-task 1.3's acceptance criterion names -- **passed**. Rule 3 asks only that a dual-mode tool's first argument be pinned to a literal subcommand, and `api` is one; but `gh api` remains dual-mode at the flag level, so no depth of pinning excludes `--method DELETE`. `Bash(gh repo *)` (admits `gh repo delete`) and `Bash(git branch *)` (admits `-D`) had the same hole.
- **Resolution**: data-driven rule 3b, in the module's established one-line-to-extend style. `UNSAFE_SUBCOMMANDS` holds pairs no pinning rescues because the mutating switch is a flag rather than a verb; `DUAL_MODE_SUBCOMMANDS` holds pairs needing one more level of pinning. The shipped baselines pass unchanged, because every shipped entry already pins at depth two (`gh pr view *`, `git branch --list *`, `docker compose config *`).
- **Lesson worth keeping**: an acceptance criterion is not satisfied by a validator that merely exists. This one was verified during 1.3 against an injected fixture that happened to use a different shape, and the named fixture was never actually run until 1.4.

### BG-3 - CLOSED in Phase 1: the hardening broke 14 tests of the bash description hook

- **Target file**: `catalog/hooks/tests/test_format_bash_description.py`
- **Source phase**: v3.17.0 Phase 1.1 (introduced by checkpoint commit `9023e6c9`), found in 1.4's full-suite run
- **What was wrong**: that suite builds its pattern list by parsing the LIVE `configs/permissions/claude-permissions.json`, so the Phase 1.1 removals (`awk`, `find`, `cat`, `echo`) broke 14 of its tests. The breakage was already on `develop`, which means it would have turned CI red for any release cut from `develop` - including a v3.16.7 release that has nothing to do with permissions.
- **Resolution**: split by what each test is actually about. Seven exercise the PARSER's structural handling (if / elif / else, `select`, for-loop bodies, prefix variable assignments) and merely used `echo` as filler; they now measure against a module-level `STRUCTURAL_PATTERNS` list, so catalog policy and parser behavior can no longer break each other. The other seven were genuine policy assertions and are inverted, each with the I6 reasoning recorded inline and a note that little real capability is lost because Claude Code's built-in read-only set already covers `find` / `cat` / `echo` with real redirect analysis (matcher findings 3 and 5). One test was added asserting the rest of the pipeline vocabulary survived, so a future over-broad removal is caught.
- **Lesson worth keeping**: a config change is a code change when a test suite reads that config. The coupling was invisible from the diff of the permission file, and only a full-suite run surfaced it - which is the argument for running the whole suite at the phase gate rather than only the suites a phase's own files live in.

### BG-4 - CLOSED in Phase 6 integration: the revert-then-merge hazard was reconciled explicitly

- **Target**: the eventual `feat/v3.17.0-agent-autonomy-toggle` -> `develop` merge (Phase 6)
- **Source phase**: v3.17.0 Phase 1, closing decision (maintainer directive, 2026-08-13)
- **What happened**: Phase 1 began directly on `develop` and its checkpoint `9023e6c9` was pushed there, so the pending v3.16.7 presentify release inherited a permission-posture change it does not document, and inherited the 14-test hook regression BG-3 records. All v3.17.0 work was therefore separated onto this branch, and `develop` reverted the checkpoint in `9d9e9a07`. `develop` and the v3.16.7 branch are both green as a result.
- **Why it is a latent defect and not just bookkeeping**: this is the classic revert-then-merge trap. This branch still CONTAINS `9023e6c9`, while `develop` now contains a commit that deliberately removed those changes. A plain `git merge` can therefore resolve in favour of the removal and silently drop the hardening, the validator, both installers' merge wiring, the Makefile and CI steps, and the matcher-findings document - with no conflict to warn anyone.
- **Suggested next step (do this at the Phase 6 merge, not before)**: either revert `9d9e9a07` on this branch first, restoring the content, and then merge; or merge `develop` into this branch and resolve every conflicting path in favour of THIS branch. Either way, verify explicitly afterwards rather than trusting the merge: `configs/permissions/claude-permissions.json` still carries its `_hardening` block, `scripts/validate_permission_baseline.py` and `scripts/merge_permissions.py` exist, `make validate` still runs the baseline validator, and `tests/validators/test_validate_permission_baseline.py` plus `tests/installer/test_permission_scope_parity.py` still pass. A green suite is the check that matters, because the failure mode here is silent deletion rather than a broken build.
- **Resolution**: merged current `origin/develop` into the feature branch with `--no-ff --no-commit`, retained v3.16.8 release work, and restored the feature side for every path owned by revert `9d9e9a07`. The first focused run proved why this was necessary: Git had silently reintroduced the stale Bash Gemini sentinel and `jq` path and removed the PowerShell helper-distribution block outside visible conflict markers. Both installers were reconstructed from the feature tip with only the audited `3.16.8` version bumps reapplied.
- **Verification**: both `_hardening` blocks remain, both helper scripts and the matcher-findings document exist, Makefile and CI retain the permission and installer-parity hard gates, the 80-test baseline/scope-parity suite passes, installer parity passes, all 10 platform contracts match, and every underlying `make validate` command passes on Windows.

### BG-5 - CLOSED after integration: the PowerShell autonomy guard discarded hosted-runner stdin

- **Target files**: `catalog/hooks/autonomy-guard.ps1`, `catalog/hooks/tests/test_autonomy_guard.py`
- **Source phase**: v3.17.0 Phase 6 protected-branch CI
- **What was wrong**: the PowerShell adapter first gated the hook payload on `[Console]::IsInputRedirected`, which the Windows service runner reported false for the JSON pipe. Hosted diagnostics then proved that PowerShell had the correct payload, project root, state, engine, and Python executable, but piping the payload string into the native Python child produced empty stdin and a false allow.
- **Resolution**: consume PowerShell's automatic `$input` enumerator first with a raw-handle fallback, parse the JSON in the adapter, and pass the extracted file path through the engine's existing `--path` option. This removes the failing native-command pipeline without duplicating the engine's path policy.
- **Verification**: the explicit-path bridge passes 54 focused guard/engine tests, the Windows PowerShell 5.1 parse gate, workflow security validation, and the full local hook matrix with 1,057 passing tests and 39 expected skips. Protected-branch CI run `31904566621`, including Windows job `95060274953`, passed the hook suite and every downstream installer and validator step. Temporary CI tracing was removed after it isolated the failing boundary.

### BG-6 - CLOSED after integration: platform-default provenance URLs drifted from the verified contract

- **Target file**: `configs/platform-defaults.json`
- **Source phase**: v3.17.0 Phase 6 protected-branch CI
- **What was wrong**: Hermes differed only by a trailing slash, while Gemini CLI and Gemini Code Assist cited older official documentation locations than the contract table. The lever data remained unchanged, but provenance could not be traced consistently from both artifacts.
- **Resolution**: align all three JSON source URLs to the official sources already recorded in `docs/policy/platform-defaults-levers.md`.
- **Verification**: all 23 platform-default lever contract tests pass, the 13-platform derived-artifact sync check passes, and the complete validator suite passes 695 tests with two expected skips.

### BG-7 - CLOSED after integration: the Claude Usage Monitor lockfile omitted optional WASI dependencies

- **Target file**: `extensions/claude-usage-monitor/package-lock.json`
- **Source phase**: v3.17.0 Phase 6 protected-branch CI
- **What was wrong**: npm 11 tolerated references from `@rolldown/binding-wasm32-wasi` to `@emnapi/core` and `@emnapi/runtime` without package records, while the Node 22 runner's npm 10 clean install rejected the incomplete lock graph.
- **Resolution**: regenerate the lockfile with npm 10.9.4, adding the two exact optional package records and their integrity metadata.
- **Verification**: npm 10.9.4 completes a clean install, TypeScript compilation, 11 tests with 92 percent statement coverage, and VSIX packaging.

## v3.17.1 - Windows tag installer-smoke repair

**Status**: Finalized on 2026-08-15 with 0 open items, 1 closed item (BG-8), and 0 release blockers.

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented by design / unverified (`NI-#`) | 0 | 0 |
| Deferred (`DF-#`) | 0 | 0 |
| Bugs (`BG-#`) | 0 | 1 (BG-8) |
| Warnings (`WN-#`) | 0 | 0 |
| Missing tests (`MT-#`) | 0 | 0 |
| Quality-gate bypasses (`QG-#`) | 0 | 0 |

> Finalized on 2026-08-15 at the v3.17.1 bump. This patch leaves no open item for the next-plan ingest.

### BG-8 - CLOSED in v3.17.1: the tag-only Windows installer smoke assigned reserved `$HOME`

- **Target files**: `.github/workflows/ci.yml`, `tests/skills/test_installer_parity_lifecycle.py`
- **Source phase**: v3.17.0 release publication, tag CI run `31910449264`
- **What was wrong**: the release-only Windows PowerShell 5.1 step assigned `$home`. PowerShell variable names are case-insensitive, so this attempted to overwrite the read-only `$HOME` variable and exited before invoking `installer.ps1`. The regular Windows bootstrap and install-smoke jobs passed, isolating the defect to the tag-expanded harness rather than the installer.
- **Resolution**: rename the local variable and all of its uses to `$smokeHome`; add a lifecycle regression that rejects a case-insensitive `$home` assignment anywhere in the CI workflow.
- **Verification**: the regression test failed against the v3.17.0 workflow on the exact assignment, then passed after the rename. The v3.17.1 tag workflow is the release-level proof that the repaired all-OS installer-smoke matrix runs end to end.

## v3.17.4 - org-knowledge-layer

**Status**: All six phases completed on 2026-08-17 with 3 open non-blocking items, 2 resolved items, and 0 release blockers. Protected CI passed on the integrated feature result before release preparation. Plan: [plans/v3.17.4-org-knowledge-layer.md](plans/v3.17.4-org-knowledge-layer.md).

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented by design / unverified (`NI-#`) | 1 (NI-4) | 0 |
| Deferred (`DF-#`) | 2 (DF-7, DF-8) | 0 |
| Bugs (`BG-#`) | 0 | 0 |
| Warnings (`WN-#`) | 0 | 1 (WN-6) |
| Missing tests (`MT-#`) | 0 | 1 (MT-2) |
| Quality-gate bypasses (`QG-#`) | 0 | 0 |

### Open Items

### NI-4 - Copilot organization precedence remains advisory

- **Source phase**: v3.17.4 Phase 6, sub-task 6.2
- **Plan reference**: `docs/v3/v3.17/plans/v3.17.4-org-knowledge-layer.md` (sub-task 6.2)
- **Reason**: GitHub documents personal and repository custom instructions as higher-priority context than organization instructions. Nexus-Hub can project portable guidance into Copilot's local instruction surface, but it cannot make that local block non-overridable or describe it as vendor-enforced policy.
- **Suggested next step**: Keep `nexus-hub org status` advisory for Copilot. Organizations needing stronger control should configure GitHub's documented Business or Enterprise administrative surface and reinforce blocking requirements through permissions, hooks, or CI.

### DF-7 - Catalog-content suppression is outside the organization-layer contract

- **Source phase**: v3.17.4 Phase 6, sub-task 6.2
- **Plan reference**: `docs/v3/v3.17/plans/v3.17.4-org-knowledge-layer.md` (sub-task 6.2)
- **Reason**: The confirmed design makes organization guidance additive and higher-priority; it does not let a bundle remove or suppress generic Nexus-Hub catalog content. Adding negative-selection semantics would change bundle validation, materialization, conflict handling, and cross-platform guarantees beyond this release's approved scope.
- **Suggested next step**: If a real organization requires suppression, define a separate opt-in filtering contract with explicit ownership, conflict, audit, and uninstall semantics before adding it to a future plan.

### DF-8 - Platform-native enforcement generation remains administrator-owned

- **Source phase**: v3.17.4 Phase 6, sub-task 6.2
- **Plan reference**: `docs/v3/v3.17/plans/v3.17.4-org-knowledge-layer.md` (sub-task 6.2)
- **Reason**: Nexus-Hub intentionally generates portable local instructions and rules, not Claude managed policy, Cursor Team Rules, GitHub organization instructions, or other administrator-controlled vendor settings. Phase 4 documents verified escalation paths without inventing credentials or authority.
- **Suggested next step**: Keep enforcement configuration outside the installer. Re-evaluate only through a separately approved, vendor-specific administrative integration with explicit authentication, authorization, and rollback requirements.

### Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| MT-2 | Real installer entry points lacked organization seeding postconditions | Phase 6 | The existing POSIX and Windows installer-smoke steps now connect the same example bundle and invoke one shared checker for marker ordering and rule projection; 106 focused policy and parity tests plus the isolated Windows installer smoke passed. |
| WN-6 | Local Windows integrations suite exceeded the bounded phase runtime | Protected feature integration | The protected PR and post-merge `develop` workflows passed their full integration and Windows jobs on merge `9cfbf36d8c5efa8fd37d4c7c66070a3bb18c3d7a`, providing the authoritative hosted evidence the local warning awaited. |

## v3.17 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented by design / unverified (`NI-#`) | 4 (NI-1, NI-2, NI-3, NI-4) | 0 |
| Deferred (`DF-#`) | 7 (DF-1, DF-2, DF-3, DF-4, DF-5, DF-7, DF-8) | 1 (DF-6) |
| Bugs (`BG-#`) | 0 | 9 (BG-1, BG-2, BG-3, BG-4, BG-5, BG-6, BG-7, BG-8, BG-9) |
| Warnings (`WN-#`) | 4 (WN-1, environmental, carried from v3.15.0; WN-2, pre-existing Ruff baseline; WN-4, version-specific hook proof; WN-5, prompting-profile roster drift) | 2 (WN-3, Vitest config loader; WN-6, hosted integration evidence) |
| Missing tests (`MT-#`) | 1 (MT-1, Claude monitor extension-wide coverage) | 1 (MT-2, real installer organization postconditions) |
| Quality-gate bypasses (`QG-#`) | 0 | 0 |

**Release blockers**: 0. NI-1 and NI-2 require live matcher probes before their respective permission baselines can be broadened, but the shipped validators and hook guards conservatively avoid relying on either unverified behavior. BG-4 through BG-9 are closed; BG-8 is the v3.17.1 tag-only Windows harness repair and BG-9 is the v3.17.2 fail-safe state-restoration migration. DF-6 is resolved by the scheduled v3.17.4 removal, WN-6 is resolved by protected CI, and WN-5 remains the release workflow's non-blocking prompting-profile freshness advisory.
