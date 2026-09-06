# Session History - v3.16.1 Phase 5: Selection contract and resolver

**Date**: 2026-08-08
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.1-evals-and-selective-installation.md](../../plans/v3.16.1-evals-and-selective-installation.md)
**Phase**: 5 of 8 (not the final phase; no release-readiness workflow ran)
**Branch**: `feat/v3.16.1-evals-and-selective-installation`
**Outcome**: Complete. Architecture frozen before Phase 6 touches two 3000-line installers.

## Goal

Define and implement one deterministic selection model, proven by a shared fixture matrix, before changing any platform installer. This is the first phase of the plan to ship runtime code.

## Sub-tasks completed

### 5.1 - Install-ownership audit (T025)

Created `selective-install-baseline.md`. Every row was read from source rather than inferred: three independent implementations (Bash 3234 lines, PowerShell 3382, Python registry), a surface-by-surface ownership table naming which of them copies what, the registry class hierarchy, the state objects that must carry selection, the nine lifecycle operations that must agree on scope, existing flag surfaces, and the no-Python constraint.

Two findings shaped the design. `SkillsIntegration._mirror_catalog` is the single chokepoint for file-tree surfaces in the registry path, so selection has exactly one place to be consulted there. And `InstallManifest.from_dict` already reads every key with a default, so backward compatibility for an old manifest is structurally true rather than something to build.

### 5.2 - Normative selection contract (T026)

Created `install-selection-contract.md`: selector grammar, the no-selector-equals-full guarantee, `full` exclusivity, union semantics, sorting and deduplication, transitive closure with reasons, traversal-scoped cycle detection, surface eligibility, always-present policy surfaces, the skill-index content rule, a failure table with exit codes, the selection manifest shape and hash definition, lifecycle behavior, and five compatibility requirements.

### 5.3 - Shared fixture matrix (T027)

Created `tests/fixtures/install-selection/` with three small catalogs (valid, missing-skill, cycle) and `cases.json`: 22 resolver-scope cases and 5 install-scope cases reserved for Phase 6. Every case carries a `why` field stating what it protects.

### 5.4 / 5.5 - Resolver, state, tests (T028, T029, T030)

Added `scripts/lib/installer/selection.py` (pure stdlib, ~430 lines). Extended `InstallContext` with an optional `selection` field defaulting to `None`, and `InstallManifest` with `set_selection` / `selection` / `selection_hash` plus additive serialization. Added `tests/installer/test_install_selection.py`, 90 assertions.

## Decisions made

- **The hash covers the resolved outcome, not the request.** Two ways of asking for the same install (`--modules a,b` versus repeated flags, or a different selector order) must produce the same hash, because they produce the same install. `warnings` is excluded too, so advisory wording changes cannot move it. This is the join key Phase 6 uses to prove Bash, PowerShell, and Python agree; if it depended on the request, that check would degrade into comparing each implementation against itself.
- **Fixture cases declare `same_hash_as` instead of a literal digest.** The property worth asserting is that two requests agree, not what the canonicalization format happens to produce. A hardcoded digest would pin the format and break on any harmless serialization change.
- **Cycle detection and missing-skill validation are traversal-scoped, not global.** A data defect in a corner of the catalog nobody selected must not block an unrelated install. `unreachable-cycle-does-not-fail` pins this: the cycle catalog resolves fine for a module that does not reach the cycle, and fails for one that does.
- **Undeclared commands and agents always install.** Excluding them would silently shrink every install the moment selection shipped, before a single declaration existed. Including them preserves current behavior exactly and lets Phase 7.1 add declarations incrementally, each narrowing by a known amount. Verified against the real catalog: with no `surface_requirements` present, every selection currently yields all 20 commands and 23 agents, which is the documented behavior rather than a bug.
- **Empty selection is an error; full selection is a warning.** An empty install is never what anyone wanted. A full one is the default and therefore always a legitimate end state, so refusing it would be obstructive, but an unintended full install is real enough to surface.
- **Resolution is pure, which makes fail-before-write structural.** `test_resolution_never_writes` runs every failing case from an empty temp cwd and asserts nothing appeared. A caller physically cannot have written anything by the time resolution raises.
- **The manifest gains a key only when a selection exists.** A full install writes byte-identical manifest bytes to what it wrote before v3.16.1, so an existing diff-based check does not start reporting a change on every default install.

## Troubleshooting trail

- **The contract, fixtures, and resolver all assumed profiles carry a flat `skills` list. They do not.** Real profiles compose from `bundles`, `modules`, and `extra_skills`, and `full` is marked `"all": true`. The first full run had 89 of 90 assertions passing while the resolver could not resolve a single real profile: both real profiles returned zero skills and were reported as "empty selection" user errors, blaming the user's selector for a modeling error in the code.

  What caught it was `test_every_real_bundle_resolves`, which runs against the actual `data/bundles.json` rather than only against fixtures. Every fixture assertion passed throughout, because the fixtures encoded the same wrong assumption as the resolver. That is the argument for keeping a real-data test beside a fixture suite, and it is recorded as DF-4.

  Fixed in three places, not one: `_expand_entry` now unions all four keys with cycle protection on references; the fixture catalog was rewritten to mirror the composed shape (its `core` profile exercises all three composition keys at once); and the contract gained section 2.1a. Verified afterwards against real data: minimal 10 skills, core 31, ai-engineering 6, ai-engineer 13, full 271.

- **`scripts/lib/installer/` is not distributed by either installer.** Found while checking whether the new module needed an installer registration entry. Both installers copy `scripts/lib/integrations/` recursively but not the sibling `installer/` package, which six integration modules import from -- three at module top level. Verified the practical impact is currently nil: the registry always runs as `$repo_root/scripts/lib/integrations/runner.py`, from the checkout, never from the installed copy. Recorded as NI-3 for Phase 6, which is already opening both installers. Not fixed here because AGENTS.md classifies installer edits as ask-first and this phase's deliverables contain none.

- **The new module needs no installer copy entry.** `test_installers_copy_every_scripts_dir_py_file` globs `scripts/*.py` non-recursively, so `scripts/lib/installer/selection.py` is outside its scope, consistent with the existing `scripts/lib/integrations/*.py` modules. No `DEV_ONLY_SCRIPTS` entry is required either. Checked rather than assumed, because the AGENTS.md installer rule is the repo's most-cited trap.

## Verification

- `python -m pytest -q tests/installer/test_install_selection.py` - 90 passed
- `python -m pytest -q tests/installer` - 250 passed, 16 skipped, 1 failed (BG-1, the inherited MSYS `tar` bootstrap failure; unrelated, and this phase touched no bootstrap file)
- Real-catalog resolution verified by inspection, not just by exit code: full 271 skills / 20 commands / 23 agents with no warnings; minimal 10; core 31; ai-engineering 6 including `eval-pipeline-audit`; ai-engineer 13
- Every profile, module, and bundle in the real `data/bundles.json` resolves
- `python scripts/validate_skills.py --bundles-only` - PASS, 0 errors, 0 warnings
- `python scripts/run_trigger_evals.py --gate` - PASS
- `validate_unicode_safety` (no findings in new files), `validate_no_personal_paths`, `scan_supply_chain_iocs`, `check_version_sync` - all PASS
- `git diff --check` - clean

## CI impact

None required. `tests/installer` already runs as its own CI step on both the Linux and Windows legs, so the 90 new assertions are covered with no workflow edit. The new fixtures live under `tests/fixtures/`, inside the workflow's `paths` filter. NI-3 is an installer-distribution question for Phase 6, not a CI one.

## Files changed

| File | Change |
|---|---|
| `docs/v3/v3.16/development/selective-install-baseline.md` | new |
| `docs/v3/v3.16/development/install-selection-contract.md` | new |
| `tests/fixtures/install-selection/catalog-valid.json` | new |
| `tests/fixtures/install-selection/catalog-missing-skill.json` | new |
| `tests/fixtures/install-selection/catalog-cycle.json` | new |
| `tests/fixtures/install-selection/cases.json` | new, 27 cases |
| `scripts/lib/installer/selection.py` | new |
| `scripts/lib/integrations/base.py` | `InstallContext.selection`, defaulting to None |
| `scripts/lib/integrations/manifest.py` | selection get/set/hash, additive serialization |
| `tests/installer/test_install_selection.py` | new, 90 assertions |
| `docs/v3/v3.16/known-gaps.md` | DF-4 closed, NI-3 open |
| `docs/DEVLOG.md`, `docs/todos.md` | Phase 5 entry and tracker |

## Next steps

Phase 6 implements this contract three times: Bash selector flags and copy filtering, PowerShell in lockstep, and the registry runner plus `SkillsIntegration` and `_catalog_adapters`. It is the highest-risk phase in the plan because it changes user-facing installers. Two Phase 5 outputs are what make it checkable: the fixture matrix gives all three implementations the same expectations, and the plan hash gives them a single value to compare. NI-3 needs a decision early in that phase, since 6.1 and 6.2 are already opening both installers.
