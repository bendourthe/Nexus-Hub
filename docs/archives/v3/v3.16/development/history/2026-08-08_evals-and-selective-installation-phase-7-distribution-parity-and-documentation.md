# Session History - v3.16.1 Phase 7: Distribution, parity, and documentation

**Date**: 2026-08-08
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.1-evals-and-selective-installation.md](../../plans/v3.16.1-evals-and-selective-installation.md)
**Phase**: 7 of 8 (not the final phase; no release-readiness workflow ran)
**Branch**: `feat/v3.16.1-evals-and-selective-installation`
**Outcome**: Complete. Selective installation is now coherent as well as smaller. The audit found and closed a defect that made the module system largely decorative.

## Goal

Prove every supported platform receives a coherent focused install, finalize the bundle and dependency metadata, and document the user workflow.

## The finding that shaped the phase

7.1 asks for an audit of every profile, module, and role bundle against the current catalog. The audit found that **only 105 of 271 skills were reachable through any module or bundle**; the other 166 existed solely under `full`. Six catalog categories were covered by nothing at all.

This was invisible before this cycle because nothing resolved selections, so no one could observe that two thirds of the catalog had no selector that reached it. It surfaced immediately once `surface_requirements` landed: all six command-delegate skills were in the unreachable set, so the first run dropped `/implement`, `/describe`, `/route`, `/constitution`, `/presentify`, and `/tune-prompting` from *every* focused install.

Curation is a product decision, so it went to the user rather than being decided here. The user chose to expand modules to cover the catalog.

## Sub-tasks completed

### 7.1 - Metadata (T041, T042)

**`surface_requirements`**: six commands declared, each naming exactly one delegate skill. The criterion is evidence-based, not inferred - only commands whose own file states they are a thin pointer over one named skill. Multi-mode commands are deliberately undeclared, because requiring every mode's delegate would make them vanish unless all modes' skills were selected. Agents declare nothing, which is a finding rather than an omission: 22 of 23 reference no skill and none shares a skill name.

**Category-complete modules**: the six curated modules were extended to cover their whole capability area, and 14 new modules added for the categories nothing mapped to. 20 modules, 271/271 reachable, 0 unreachable. Schema bumped 1.4.0 -> 1.5.0. The 15 role bundles were left untouched.

Generated catalogs verified unchanged (271 in all four places); no skill was added or removed.

### 7.2 - Distribution parity (T043, T044)

`tests/integrations/test_selective_install.py`, 44 assertions across 5 skill-bearing platforms x 3 representative selections.

### 7.3 - Documentation (T045, T046)

A README section covering both shells, and `guides/reference/SELECTIVE_INSTALLATION.md` with selector semantics, the six declared commands, inspection commands, lifecycle behavior, and a troubleshooting table keyed by the exact error text.

### 7.4 - Selection-aware verification (T047, T048)

Investigation found both checks already safe **by construction**, so the deliverable became pinning that property rather than fabricating a change. `runner.py verify` now reports the recorded scope first so a PASS on a focused install is interpretable.

## Decisions made

- **The "excluded skills are absent" assertion is the load-bearing one.** Asserting that resolved skills are present is weak: a filter that did nothing would pass it. The exclusion check is what proves filtering happened on each platform's own copy path, which differ (flattened, nested, command-as-skill) and could each bypass the filter independently.
- **Modules became category-complete rather than individually curated.** It is predictable ("this whole capability area"), explainable in one sentence, and mechanically verifiable by a test. The cost is recorded rather than hidden: `core` grew 31 -> 45 skills because it composes from two modules that expanded.
- **Only thin-pointer commands are declared.** Over-declaring would make focused installs lose commands wholesale, which is the opposite of coherent. A command is dropped only when the skill that does its work is absent, because then it is a pointer to nothing.
- **7.4 pinned an existing property instead of changing code.** `verify` asserts read paths are populated and `harness_audit` scores surfaces present over surfaces declared; neither compares against the catalog. The tempting future "fix" in both places is to compare against the catalog, and that edit would look like an improvement while reporting every focused install as broken. The tests name that specific edit so it fails loudly.

## Troubleshooting trail

- **The full suite surfaced two stale assertions from Phase 6 (QG-2).** Phase 6's `-Profile` alias fix was made *after* its regression run had already started in the background, so the 873-passed result cited in that commit had tested the pre-rename tree. Two `test_selection_parity.py` assertions still matched `[string]$Profile` and `$argsList += @("--profile", $Profile)`. Both were updated here, and the profile one was strengthened into a named guard that also asserts a literal `[string]$Profile,` parameter is absent, so the shadowing bug cannot return. The lesson is about process, not code: a long-running background gate is only evidence for the tree it started against, and any edit made while it runs invalidates it.
- **Phase 7's own tests had no failures.** 44 distribution assertions, 10 verification assertions, and the existing 99 selection and registry-consistency tests all passed on first run.
- **A near-miss worth noting**: the first `surface_requirements` draft was going to be derived from every skill a command *mentions*. `/presentify` mentions 7 and `/update` mentions 8; declaring those as requirements would have made both commands disappear from nearly every focused install. Checking what each command file actually says about delegation (rather than counting references) is what produced a defensible six.

## Verification

- `python -m pytest -q tests/integrations/test_selective_install.py` - 44 passed
- `python -m pytest -q tests/validators/test_selection_aware_verification.py` - 10 passed
- `python -m pytest -q tests/validators/test_registry_consistency.py tests/installer/test_install_selection.py` - 99 passed
- Resolution verified by inspection across the expanded modules: full 271 skills / 20 commands, minimal 10 / 14, core 45 / 14, workflow 43 / 16, workflow+ai 56 / 18, security-operations 16 / 14
- Every profile, module, and bundle resolves; 271/271 skills reachable
- Catalog counts agree at 271 across `skills.json`, `SKILL_INDEX` rows, the total line, `marketplace` sum, and `statistics`
- All 11 validators PASS (bundle audit, trigger gate, version sync, personal paths, supply chain, workflow security, platform contracts, contract freshness, base-template parity, platform-defaults drift)
- README addition is 31 lines, all ASCII; the guide is fully ASCII
- `bash -n` clean; `git diff --check` clean

## CI impact

None required. `tests/integrations` and `tests/validators` already run as their own CI steps, so both new modules are picked up automatically. No workflow file changed.

## Files changed

| File | Change |
|---|---|
| `data/bundles.json` | `surface_requirements` (6 commands); modules 6 -> 20, category-complete; schema 1.5.0 |
| `tests/integrations/test_selective_install.py` | new, 44 assertions |
| `tests/validators/test_selection_aware_verification.py` | new, 10 assertions |
| `scripts/lib/integrations/runner.py` | `verify` reports the recorded scope |
| `README.md` | selective-installation section for both shells |
| `guides/reference/SELECTIVE_INSTALLATION.md` | new user-facing reference |
| `docs/v3/v3.16/known-gaps.md` | NI-4, NI-5 closed |

## Next steps

Phase 8 is the terminal phase: architecture refactor, known-gaps reconciliation, the CI/CD comparison, the full local validation matrix, and the release handoff. Four gaps remain open across the cycle (QG-1 the CI path filter, NI-2 the 118 truncated agent descriptors, WN-1 the missing local toolchain, BG-1 the inherited MSYS `tar` failure); QG-1 in particular is a one-line fix that Phase 8.3 is already scoped to make.
