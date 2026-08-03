# Documentation Cleanup Report - v3.15.7

**Last updated**: 2026-08-02
**Scope**: `docs/v3/v3.15/`
**Mode**: Audit and report; no file moves

## Outcome

The active v3.15 documentation tree is already canonical. Phase 1 introduced no misplaced, duplicated, stale, or archive-ready documentation, so no move, rename, deletion, or reference repair was applied.

## Inventory

The bundled `docs-layout-refactor` audit helper inventoried 55 Markdown files under the active v3.15 tree:

| Location | Files | Decision |
|---|---:|---|
| Root | 1 | Keep `known-gaps.md` as the active minor-version ledger |
| `comparisons/` | 5 | Keep as active source and adoption analyses |
| `plans/` | 8 | Keep as active v3.15 implementation plans |
| `development/` | 41 | Keep as phase histories and development records |

The reference-graph helper found inbound-reference records for two active targets: `known-gaps.md` and the v3.15.6 adoption plan. No Phase 1 document move was proposed, so reference repair was not required.

## Gitignore and Generated Artifacts

No new repository-local cache, build output, audit scratch file, or generated binary was created. Existing ignore rules remain sufficient; zero `.gitignore` patterns were added. The detached checkout and both diagnostic logs were removed during Phase 1 closeout. Windows denied Git permission to prune the inert `.git/worktrees/v3157-phase1-tests` metadata directory after the checkout disappeared; it is absent from `git worktree list`, is not committed, and has no repository-content impact.

## Decision

Keep the v3.15 tree unchanged. Re-run the audit after a phase that adds or relocates documentation, and reserve archival moves for a later major-version cleanup rather than moving active v3.15 records during Phase 1.

## Phase 2 Audit - 2026-07-31

The bundled inventory helper found 58 Markdown files and no binaries under `docs/v3/v3.15/` after the required Phase 2 history was written: 2 at the version root, 5 under `comparisons/`, 8 under `plans/`, and 43 under `development/`. The reference graph found 73 inbound references across 3 active targets. Every file remains part of the active v3.15 release record, so the Phase 2 disposition is Cat 4 for all 58 files and zero files in Cat 1, Cat 2, or Cat 3.

Phase 2 added no repository-local cache, build output, generated binary, or audit scratch file. Temporary test logs were written outside the repository and removed during closeout. Existing ignore rules remain sufficient; zero `.gitignore` patterns were added.

No move, rename, deletion, archive operation, or reference repair was applied. The report remains self-classified as Cat 4 while v3.15.7 is active.

## Phase 3 Audit - 2026-07-31

After the required Phase 3 history was written, the bundled inventory helper found 59 Markdown files and no binaries under `docs/v3/v3.15/`: 2 at the version root, 5 under `comparisons/`, 8 under `plans/`, and 44 under `development/`. The reference graph found 73 inbound references across 3 active targets. Every file remains part of the active v3.15 release record, so the Phase 3 disposition is Cat 4 for all 59 files and zero files in Cat 1, Cat 2, or Cat 3.

Phase 3 created only already-ignored test caches and coverage files. It created no repository-local scratch log, generated binary, or new artifact class. Existing ignore rules remain sufficient; zero `.gitignore` patterns were added.

No move, rename, deletion, archive operation, or reference repair was applied. The report remains self-classified as Cat 4 while v3.15.7 is active.

## Phase 4 Audit - 2026-07-31

After the required Phase 4 history was written, the bundled inventory helper found 60 Markdown files and no binaries under `docs/v3/v3.15/`: 2 at the version root, 5 under `comparisons/`, 8 under `plans/`, and 45 under `development/`. The reference graph found 73 inbound references across 3 active targets. Every file remains part of the active v3.15 release record, so the Phase 4 disposition is Cat 4 for all 60 files and zero files in Cat 1, Cat 2, or Cat 3.

Phase 4 created only already-ignored test caches and coverage files. It created no repository-local scratch log, generated binary, or new artifact class. Existing ignore rules remain sufficient; zero `.gitignore` patterns were added.

No move, rename, deletion, archive operation, or reference repair was applied. The report remains self-classified as Cat 4 while v3.15.7 is active.

## Phase 5 Audit - 2026-07-31

After the required Phase 5 history was written, the bundled inventory helper found 61 Markdown files and no binaries under `docs/v3/v3.15/`: 2 at the version root, 5 under `comparisons/`, 8 under `plans/`, and 46 under `development/`. The reference graph found 73 inbound references across 3 active targets. Every file remains part of the active v3.15 release record, so the Phase 5 disposition is Cat 4 for all 61 files and zero files in Cat 1, Cat 2, or Cat 3.

Phase 5 created only already-ignored Python bytecode and coverage data during testing. The broker bundle's generated bytecode and the repository coverage database were removed before closeout, and the disposable local-temp test mirror was deleted. Existing ignore rules remain sufficient; zero `.gitignore` patterns were added.

No move, rename, deletion, archive operation, or reference repair was applied. The report remains self-classified as Cat 4 while v3.15.7 is active.

## Phase 6 Audit - 2026-07-31

After the required Phase 6 history was written, the bundled inventory helper found 62 Markdown files and no binaries under `docs/v3/v3.15/`: 2 at the version root, 5 under `comparisons/`, 8 under `plans/`, and 47 under `development/`. The reference graph found 73 inbound references across 3 active targets. Every file remains part of the active v3.15 release record, so the Phase 6 disposition is Cat 4 for all 62 files and zero files in Cat 1, Cat 2, or Cat 3.

Phase 6 created only already-ignored Python bytecode and coverage data inside the repository during testing, and none remains in the Phase 6 bundle. A disposable contract-test mirror and coverage database remain under the local temporary directory because the sandbox rejected their removal after their exact paths were validated; both are outside the repository and contain only reproducible test inputs or coverage data. Existing repository ignore rules remain sufficient; zero `.gitignore` patterns were added.

No move, rename, deletion, archive operation, or reference repair was applied. The report remains self-classified as Cat 4 while v3.15.7 is active.

## Phase 7 Final Audit - 2026-08-02

After the required Phase 7 history was written, the bundled inventory and reference-graph approach found 63 Markdown files and no binaries under `docs/v3/v3.15/`: 2 at the version root, 5 under `comparisons/`, 8 under `plans/`, and 48 under `development/`. The reference graph retains 73 inbound-reference records across 3 active targets. All 63 files remain Cat 4 active release records; zero files qualify for deletion, archival, relocation, or consolidation.

The repository-wide structural audit found no tracked empty directory that requires removal, no accidental duplicate file group, no obsolete plan artifact, and no unjustified single-child chain. The duplicate hashes correspond to intentional empty package markers, parity templates, paired usage-monitor assets, licenses, warning icons, and equivalent test configuration. The only empty skill scaffolds visible in the shared worktree are untracked parallel-session artifacts and were not modified.

No receiving skill crossed the 500-line target because of this plan: the one edited skill above 500 lines was already grandfathered and grew by only 25 lines without crossing a threshold. Every new bundled script is referenced by its parent skill, the bundle audit reports zero errors, and the plan created no monolithic replacement security skill. No move, rename, deletion, archive operation, reference repair, `.gitignore` edit, or generated catalog sync was justified.

## v3.15.8 Phase 1 Audit - 2026-08-02

The bundled audit helper inventoried 366 active documentation files repository-wide and 68 files under `docs/v3/v3.15/` before the Phase 1 session history was added. The reference graph contained 48 referenced documentation targets. The three new contract documents, the v3.15.8 plan update, and this checkpoint all belong to the active v3.15 development record; the session history brings the expected active v3.15 total to 69.

All Phase 1 documentation remains Cat 4 active/current. No file qualifies as Cat 1 deletion, Cat 2 historical archive, or Cat 3 relocation. The plan, development contracts, fixtures, and semantic tests use their canonical directories, and the v3.16.7 portable-path correction changes content only, not document ownership or placement.

Phase 1 created only already-ignored Python coverage and cache outputs. Existing ignore rules cover `.coverage`, `.pytest_cache`, `.ruff_cache`, and `__pycache__`; zero `.gitignore` patterns were added. No move, rename, deletion, archive operation, or reference repair was applied.

## v3.15.8 Phase 2 Audit - 2026-08-02

The bundled audit helper inventoried 367 documentation files repository-wide and 69 files under `docs/v3/v3.15/` before the Phase 2 session history was added. The reference graph contained 48 referenced documentation targets and 240 inbound edges. The new history file brings the expected active v3.15 total to 70.

All Phase 2 documentation remains Cat 4 active/current. The v3.15.8 plan, shared known-gaps ledger, cleanup report, DEVLOG, progress tracker, and phase history are current implementation records in their canonical locations. No file qualifies as Cat 1 deletion, Cat 2 archive, or Cat 3 refresh or relocation.

Phase 2 produced package-local build, dependency, coverage, and VSIX outputs. Root rules already covered `node_modules/`, `out/`, and `*.vsix`, but not the monitor's `coverage/` directory, so `extensions/github-usage-monitor/.gitignore` now records the package-local `node_modules/`, `out/`, `coverage/`, and `*.vsix` convention. Four scoped patterns were added. No move, rename, deletion, archive operation, or reference repair was applied.

## v3.15.8 Phase 3 Audit - 2026-08-02

The active documents changed in Phase 3 are the existing v3.15.8 plan, shared known-gaps ledger, visual contract, cleanup report, DEVLOG, progress tracker, and one new session history. Each remains a Cat 4 active/current record in its canonical directory. No file qualifies for deletion, archival, consolidation, or relocation, and no comparison or adoption-plan co-location changed.

Phase 3 intentionally adds committed binary distribution assets under `extensions/github-usage-monitor/`: the byte-identical supplied warning PNG, deterministic WOFF2 glyph, and deterministic transparent 256x256 package PNG. They are product artifacts, not generated scratch output. Package-local `node_modules/`, `out/`, `coverage/`, and `*.vsix` remain covered by the Phase 2 `.gitignore`; zero additional ignore patterns are required.

No move, rename, deletion, archive operation, or reference repair was applied. The report remains Cat 4 while v3.15.8 is active.

## v3.15.8 Phase 4 Audit - 2026-08-02

After the Phase 4 session history was written, the tree holds 73 Markdown files and no non-Markdown files under `docs/v3/v3.15/`: 2 at the version root, 5 under `comparisons/`, 10 under `plans/`, and 56 under `development/`. The `plans/` count includes one untracked plan created by a parallel session (`v3.15.9-cross-provider-routing-and-cursor-usage-monitor.md`); it is not part of this phase's change set and was neither modified nor committed here.

The active documents changed in Phase 4 are the v3.15.8 plan, shared known-gaps ledger, visual contract, this cleanup report, DEVLOG, one new session history, and the new `extensions/github-usage-monitor/README.md`. Each remains a Cat 4 active/current record in its canonical directory. The extension README belongs beside its package rather than under `docs/`, matching the Claude and Codex monitors. No file qualifies for deletion, archival, consolidation, or relocation.

Phase 4 added one new tracked test directory (`tests/workflows/`) and one new tracked script (`extensions/github-usage-monitor/scripts/verify-package-contents.js`); both are source, not scratch. Generated output was limited to the package-local `out/`, `coverage/`, and `*.vsix` paths already covered by the Phase 2 `.gitignore`, plus repository Python caches already covered by root rules. Zero `.gitignore` patterns were added.

No move, rename, deletion, archive operation, or reference repair was applied. The report remains Cat 4 while v3.15.8 is active.

## v3.15.8 Phase 5 Audit - 2026-08-02

After the Phase 5 session history was written, the tree holds 74 Markdown files and no non-Markdown files under `docs/v3/v3.15/`: 2 at the version root, 5 under `comparisons/`, 10 under `plans/`, and 57 under `development/`. The single-file increase over Phase 4 is this phase's session history. The `plans/` count still includes the untracked `v3.15.9-cross-provider-routing-and-cursor-usage-monitor.md` created by a parallel session; it was neither modified nor committed here.

The active documents changed in Phase 5 are the v3.15.8 plan, the platform capability ownership matrix, the shared known-gaps ledger, this cleanup report, DEVLOG, one new session history, and the two `docs/policy/platform-read-contracts.{json,md}` files. Each remains a Cat 4 active/current record in its canonical directory. The read-contract pair lives under `docs/policy/` rather than the version tree because it is the living cross-version contract, which is also why its freshness gate runs on every `make validate`.

Phase 5 added two tracked source files (`scripts/lib/integrations/_codex_native.py` and `tests/integrations/test_codex_native.py`) and no new directory, artifact class, or scratch output. Repository Python caches are the only generated output and are already covered by root ignore rules. Zero `.gitignore` patterns were added.

No move, rename, deletion, archive operation, or reference repair was applied. The report remains Cat 4 while v3.15.8 is active.

## v3.15.8 Phase 6 Audit - 2026-08-02

After the Phase 6 session history was written, the tree holds 75 Markdown files and no non-Markdown files under `docs/v3/v3.15/`: 2 at the version root, 5 under `comparisons/`, 10 under `plans/`, and 58 under `development/`. The single-file increase over Phase 5 is this phase's session history. The `plans/` count still includes the untracked `v3.15.9-cross-provider-routing-and-cursor-usage-monitor.md` created by a parallel session; it was neither modified nor committed here.

The active documents changed in Phase 6 are the v3.15.8 plan, the platform capability ownership matrix, the shared known-gaps ledger, this cleanup report, DEVLOG, one new session history, and the two `docs/policy/platform-read-contracts.{json,md}` files. Each remains a Cat 4 active/current record in its canonical directory. No file qualifies for deletion, archival, consolidation, or relocation.

Phase 6 added three tracked source files (`scripts/lib/integrations/_settings_hooks.py`, `scripts/lib/integrations/_settings_hooks_mixin.py`, and `tests/integrations/test_settings_hooks.py`) and no new directory, artifact class, or scratch output. The installer writes `settings.json.nexus-hub.bak` and a transient `.nexus-hub.tmp` beside a user's config at install time, but both land in the user's home or project tree rather than this repository, and the temp file is replaced atomically rather than left behind (asserted by a test). Repository Python caches are the only generated output and are already covered by root ignore rules. Zero `.gitignore` patterns were added.

No move, rename, deletion, archive operation, or reference repair was applied. The report remains Cat 4 while v3.15.8 is active.

## v3.15.8 Phase 7 Audit - 2026-08-02

After the Phase 7 session history was written, the tree holds 76 Markdown files and no non-Markdown files under `docs/v3/v3.15/`: 2 at the version root, 5 under `comparisons/`, 10 under `plans/`, and 59 under `development/`. The single-file increase over Phase 6 is this phase's session history. The `plans/` count still includes the untracked `v3.15.9-cross-provider-routing-and-cursor-usage-monitor.md` created by a parallel session; it was neither modified nor committed here.

The active documents changed in Phase 7 are the v3.15.8 plan, the platform capability ownership matrix, the shared known-gaps ledger, this cleanup report, DEVLOG, one new session history, and the two `docs/policy/platform-read-contracts.{json,md}` files. Each remains a Cat 4 active/current record in its canonical directory. No file qualifies for deletion, archival, consolidation, or relocation.

Phase 7 added three tracked source files (`scripts/lib/integrations/_kimi_native.py`, `scripts/lib/integrations/_owned.py`, and `tests/integrations/test_kimi_native.py`) and moved one function between modules without changing behavior; no new directory, artifact class, or scratch output was introduced. As in Phase 6, the installer writes a `.nexus-hub.bak` companion and a transient `.nexus-hub.tmp` beside the user's `config.toml`, both under the user's home rather than this repository, with the temp file replaced atomically (asserted by a test). Repository Python caches are the only generated output and are already covered by root ignore rules. Zero `.gitignore` patterns were added.

No move, rename, deletion, archive operation, or reference repair was applied to documentation. The report remains Cat 4 while v3.15.8 is active.

## v3.15.8 Phase 8 Audit - 2026-08-03

After the Phase 8 session history was written, the tree holds 77 Markdown files and no non-Markdown files under `docs/v3/v3.15/`: 2 at the version root, 5 under `comparisons/`, 10 under `plans/`, and 60 under `development/`. The single-file increase over Phase 7 is this phase's session history. The `plans/` count still includes the untracked `v3.15.9-cross-provider-routing-and-cursor-usage-monitor.md` created by a parallel session; it was neither modified nor committed here.

The active documents changed in Phase 8 are the v3.15.8 plan, the platform capability ownership matrix, the shared known-gaps ledger, this cleanup report, DEVLOG, one new session history, and the two `docs/policy/platform-read-contracts.{json,md}` files. Each remains a Cat 4 active/current record in its canonical directory. No file qualifies for deletion, archival, consolidation, or relocation.

**This phase did perform a catalog relocation**, the first in v3.15.8 and the only one so far. Four checklist files moved out of `catalog/skills/code-review/references/` (a category-level directory that violated the per-skill bundling convention) into the `references/` directory of each skill that cites them: `code-quality/references/` gained `solid-checklist.md`, `code-quality-checklist.md`, and `removal-plan.md`; `performance-review/references/` was created for `code-quality-checklist.md`; `security-review/references/` gained `security-checklist.md`. The category-level directory was then deleted. `code-quality-checklist.md` deliberately exists in two skills, because per-skill bundling makes each skill self-contained rather than sharing across siblings. This is a reference *repair*, not a documentation cleanup: the three skills already cited these relative paths and could not resolve them. The bundle audit reports 0 errors and no new orphan afterward.

Phase 8 added one tracked test file (`tests/integrations/test_copilot_hermes_native.py`) and no new directory or artifact class. Repository Python caches are the only generated output and are already covered by root ignore rules; the 10 bundle-audit warnings are `scripts/__pycache__/*.pyc` artifacts inside skill bundles, pre-existing and untracked. Zero `.gitignore` patterns were added.

## v3.15.8 Phase 9 Audit - 2026-08-03

After the Phase 9 session history was written, the tree holds 78 Markdown files and no non-Markdown files under `docs/v3/v3.15/`: 2 at the version root, 5 under `comparisons/`, 10 under `plans/`, and 61 under `development/`. The single-file increase over Phase 8 is this phase's session history. The `plans/` count still includes the untracked `v3.15.9-cross-provider-routing-and-cursor-usage-monitor.md` created by a parallel session; it was neither modified nor committed here, and MT-5's transfer names v3.15.9 as its destination without editing that plan.

The active documents changed in Phase 9 are the v3.15.8 plan, the shared known-gaps ledger, this cleanup report, DEVLOG, and one new session history. Each remains a Cat 4 active/current record in its canonical directory. No file qualifies for deletion, archival, consolidation, or relocation.

**Code-layout findings, which are this phase's substance.** The refactor removed duplication rather than files: `scripts/lib/integrations/_hooks_common.py` was added (126 lines) and 152 lines came out of the four adapters, for a net reduction with one more module. No file became obsolete, no directory was emptied, and no deprecated file was found -- the v3.15.8 adapters are all four phases old at most. One dead reference was repaired: `kimi.py` and `_kimi_native.py` imported host helpers from `_settings_hooks`, a module named for a different platform's file, which now resolve to `_hooks_common`. One trivial wrapper (`SettingsHooksMixin._remove_dir_if_empty`) was removed in favor of the shared helper it delegated to, with both callers updated.

The independent Claude, Codex, and GitHub monitor boundaries were explicitly preserved: no monitor abstraction was shared or extracted, each extension keeps its own package, tests, and workflow, and the release worktree discipline is untouched. The installer dispatch duplication the sub-task mentions was inspected and left alone -- both installers delegate every v3.15.8 platform through the Python registry already, so the per-platform blocks that remain are the shell-side provider headers and detection notes, which are not duplication to remove.

Phase 9 added two tracked source files (`_hooks_common.py`, `tests/workflows/test_workflow_policy_repo_wide.py`) and no new directory or artifact class. Generated output was limited to the package-local `out/`, `coverage/`, and the `*.vsix` produced by the release-readiness packaging check (removed after verification), all already covered by the Phase 2 `.gitignore`, plus repository Python caches covered by root rules. Zero `.gitignore` patterns were added.
