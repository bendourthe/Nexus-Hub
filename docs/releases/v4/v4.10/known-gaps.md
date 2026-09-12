# Known gaps - v4.10.0

Unfinished work, deferrals, and defects found during v4.10.0 that did not reach a clean state. Open items carry forward into the next plan's ingest.

**Last updated**: 2026-09-12

## Open Items - found 2026-09-10 during v4.10.0 implementation

**Summary**: 6 open (1 DF, 3 WN, 2 MT). WN-3 resolved 2026-09-12.

### WN-3 - `tests/skills/test_target_manifest.py` is red on `develop`

**Status**: RESOLVED 2026-09-12 by PR #199; see "Resolved during this version" below. Retained here because its diagnosis was wrong in an instructive way: it read an environmental property as a defect on `develop`.

- **Source phase**: Phase 6 (T025).
- **Plan reference**: v4.10.0 Phase 6, full local suite.
- **What was observed**: the full profile reported 16 failing tests. Five trace to this plan and are fixed. The remaining **11 are all in `tests/skills/test_target_manifest.py`** and are **pre-existing**: checking out `origin/develop` over the working tree and re-running reproduces the same 11 failures with none of this plan's changes applied.
- **Reason it is open**: it is not this plan's defect and diagnosing a git-metadata test module is outside its scope. Fixing it here would mix an unrelated repair into a content plan.
- **Suggested next step**: triage separately. Note that the integration pull request for this plan will run the same suite and is expected to show these 11 failures, so a red `tests` check on that pull request must be read against this baseline rather than attributed to the plan. Confirm the baseline on `develop` before reproducing locally.

### DF-1 - Skill registration is documented as three files, but five carry catalog state

- **Source phase**: Phase 2 (T006), surfaced in Phase 5 (T016).
- **Plan reference**: v4.10.0 Phase 2, "Register the skill".
- **What was observed**: `AGENTS.md` instructs a new skill to update `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json`. Doing exactly that left the catalog inconsistent with itself **four separate times**, each caught by a different gate and none by the per-phase `fast` profile:
    1. `data/skills.json` also carries a `statistics` block (`total_skills` plus a per-category map). Three `test_registry_consistency.py` assertions failed.
    2. Its `path` field requires a trailing slash; `check_registry_entries.py` rejected the entry without one.
    3. Its `size` field must be a dict of `lines`/`characters`/`tokens_estimate`, not an int.
    4. **`data/bundles.json` is a fifth registry file** the instruction never mentions. A skill in no module is unreachable by any install profile except `full`, which `test_selective_install.py::test_every_catalog_skill_is_reachable_through_some_module` enforces.
  Separately, four prose surfaces state the catalog size (`.claude-plugin/plugin.json`, `data/marketplace.json`, `README.md`, `AGENTS.md`) plus the generated interactive guide, which `stamp_guide_counts.py` stamps.
- **Reason it is open**: the fix is to widen the registration instructions in `AGENTS.md`, which is a documentation change outside this plan's stated scope. This plan corrected the data; it did not rewrite the instruction that produced the error.
- **Suggested next step**: update the "Register the skill" section of `AGENTS.md` to name all five files and both derived-count surfaces, and to point at `python scripts/check_registry_entries.py --emit <skill>`, which prints a paste-ready entry with the correct field shapes and would have prevented three of the four errors above. Prefer deriving counts from the entry list over incrementing by hand.

### WN-1 - The residual-reference check scans Markdown only

- **Source phase**: Phase 5 (T015, T016).
- **Plan reference**: v4.10.0 D6, "residual-reference check that fails on a single survivor".
- **What was observed**: `--check-residual` walks `*.md`. The one surviving reference found while replaying the three renumbers was in `docs/releases/v4/v4.9/development/qualification/v4.9-layout-public.json`, which the check would not have reached.
- **Reason it is open**: widening the scan to all file types would sweep in generated inventories, lockfiles, and frozen evidence snapshots whose purpose is to record a past state, producing failures that must all be exempted. Every reference class in the Phase 1 acceptance surface is Markdown, so the current scope is sufficient for the documented procedure and insufficient as a repository-wide guarantee. That distinction is stated in the Phase 5 evidence.
- **Suggested next step**: if a future renumber touches a non-Markdown reference, extend the scan with an explicit include-list of file types rather than a blanket walk, and keep the frozen-evidence exemption.

### WN-2 - The fast profile does not reach `tests/validators/`

- **Source phase**: Phase 5 (T016).
- **Plan reference**: v4.10.0 execution contract, which nominates `--profile fast` as the per-phase local gate.
- **What was observed**: DF-1 was introduced in Phase 2 and survived three subsequent phase gates. Every one of those gates ran `--profile fast` and the bundle audit, and both passed while the catalog disagreed with itself. Only a full `tests/validators/` run (1520 tests, about 3m24s) caught it.
- **Reason it is open**: this is a property of the profile design, not a defect introduced here. Moving registry-consistency tests into `fast` would slow the per-phase gate; leaving them out means catalog drift is invisible until the full profile runs.
- **Suggested next step**: consider a narrow `registry-consistency` step in the `fast` profile that runs only `tests/validators/test_registry_consistency.py` (0.31s), rather than the whole validators tree. Decide it as a CI/CD change with its own approval, not as a side effect of a content plan.

### MT-1 - The repository description still states the old catalog size

- **Source phase**: Phase 6 (T020).
- **Plan reference**: v4.10.0 Phase 6, git-tree hygiene.
- **What was observed**: `check_release_preconditions.py --repo-settings` reports the GitHub repository description says 336 skills while `README.md` now declares 337. The description is not a version-carrying surface, so `check_version_sync.py` cannot see it and it drifts silently.
- **Reason it is open**: it is a GitHub repository setting, changed through the web UI or `gh`, not a file in this branch. Changing it is outside a code branch's authority and should not be done silently on the maintainer's behalf.
- **Suggested next step**: the maintainer updates the repository description to 337 when this plan merges, or at the next release. The precondition checker already reports it, so it will not be missed.

### WN-4 - The scoped weekly bar is display-only and will not warn the user

- **Source phase**: the Claude Usage Monitor scoped weekly bar, folded into v4.10.0 from the unreleased v4.9.1 slot.
- **What was observed**: urgency thresholds, status-bar highlighting, and threshold notifications continue to evaluate the session and all-models weekly metrics only. The model-scoped weekly bar is rendered in the dashboard and the status-bar hover but feeds none of them.
- **Reason it is open**: this is the deliberate outcome, not an omission. The requirement was explicit that the second bar stay out of the status-bar text, and feeding it into the `highest` threshold metric would have coloured the status bar and raised a toast from a bar the user asked to keep off that surface. The consequence is real and is stated in the changelog: a scoped limit approaching capacity is visible on hover and in the dashboard but will not interrupt the user.
- **Suggested next step**: if a scoped limit ever becomes the binding constraint in practice, the cheapest change is a fourth `claudeUsage.thresholdMetric` value rather than folding it into `highest`, so an existing user's alerting does not change under them. That is a settings-schema change and needs its own decision record.

### MT-2 - The two weekly bars were not exercised in a running extension host

- **Source phase**: the same change.
- **What was observed**: the type check passed, 12 unit tests passed including 6 new mapping cases, and the real account payload was fed through `mapClaudeUsageResponse` and resolved a `Fable`-labelled scoped metric. None of that loads the extension. The tooltip SVG and the dashboard section were not rendered.
- **Reason it is open**: the verified boundary is the normalized data model, not the pixels. A mistake in the tooltip markup or the dashboard template would pass every check that was run. The status-bar hover in particular builds an inline SVG into a percent-encoded data URI, which no unit test in this extension covers today.
- **Suggested next step**: build the extension, load it in VS Code, hover the status-bar item, and open the dashboard, confirming two weekly bars with the second labelled from the account. Do this before publishing the tag, since the changelog asserts the bar appears.

## Resolved during this version

- **WN-3, `tests/skills/test_target_manifest.py` red on `develop`** - RESOLVED 2026-09-12 by PR #199. The 11 failures were not a defect in the module or on `develop`: they are a property of a host whose only git is hard-linked, which `resolve_trusted_git` correctly refuses. The fixture asserted that git EXISTS rather than that it QUALIFIES. The marker now skips with the measured reason. This gap's predicted consequence did NOT occur: it expected the integration pull request to show the same 11 failures, but PR #198 was green twice, because GitHub runners ship a single-link git. Coverage is unaffected - putting the conforming `bin/git.exe` first on PATH restores `53 passed, 2 skipped` locally.
- **Touched-path extraction returned zero for three of five live plans** (Phase 2, T007). The extractor read only backtick-quoted paths while three plans use bare trailing paths, which would have produced a false "no impact" for every pair involving them. Fixed and pinned by three tests.
- **`data/skills.json` statistics block disagreed with its own entry list** (Phase 5). Fixed by deriving both counts from the entries. The instruction that produced the error remains open as DF-1.
- **The Phase 1 evidence stated 99 plan files as 101** (Phase 6). An unverified figure, corrected against the script's own count in the evidence and the session history.
