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

All Phase 1 documentation remains Cat 4 active/current. No file qualifies as Cat 1 deletion, Cat 2 historical archive, or Cat 3 relocation. The plan, development contracts, fixtures, and semantic tests use their canonical directories, and the v3.20.0 portable-path correction changes content only, not document ownership or placement.

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

## v3.15.9 Phase 1 Audit - 2026-08-03

After the Phase 1 history was written, the active v3.15 tree holds 80 Markdown files: 2 at the version root, 5 under `comparisons/`, 10 under `plans/`, and 63 under `development/`. The v3.15.9 plan moved from parallel untracked context into the active phase branch; the new routing contract and Phase 1 history occupy canonical `development/` locations.

Every Phase 1 document is Cat 4 active/current: the plan drives the remaining six phases, the routing contract is the normative v3.15.9 schema, and the history records the completed phase. No file is obsolete, duplicated, misplaced, archive-ready, or an orphan. No move, rename, deletion, archive operation, or reference repair is justified.

Generated output consisted only of repository Python caches already covered by root ignore rules. The new pytest module belongs under the existing `tests/plans/` surface already collected by CI. Zero `.gitignore` patterns were added.

Two untracked v3.17 scroll-world documents appeared concurrently outside this phase's v3.15 scope. They were not read as instructions, modified, moved, staged, or included in this audit decision.

## v3.15.9 Phase 2 Audit - 2026-08-03

Before the Phase 2 history is written, the bundled inventory helper finds 80 Markdown files and no non-Markdown files under `docs/v3/v3.15/`: 2 at the version root, 5 under `comparisons/`, 10 under `plans/`, and 63 under `development/` (including 59 prior history files). The new history will bring the active tree to 81 Markdown files. The reference graph identifies four active targets with inbound references: the cleanup report, shared known-gaps ledger, v3.15.6 sandbox-escapes plan, and the v3.15.9 cross-provider routing contract.

Every Phase 2 document remains Cat 4 active/current. The v3.15.9 plan tracks the next five phases, the known-gaps checkpoint records the clean gate, and the new history is the canonical phase handoff. No document is obsolete, duplicated, misplaced, archive-ready, or orphaned; no move, rename, deletion, archive operation, or reference repair is justified.

Phase 2 adds skill-bundled Python/Bash/PowerShell source, a dated JSON reference, and fixture/test source outside `docs/`. Generated output is limited to ignored Python caches and coverage data; the repository status contains no generated test artifact. Existing ignore rules are sufficient, so zero `.gitignore` patterns were added. The pre-existing untracked empty skill scaffolds documented in the v3.15.5 terminal audit were temporarily isolated only for the Hermes regression check and restored unchanged.

## v3.15.9 Phase 3 Audit - 2026-08-04

Before the Phase 3 history is written, the active v3.15 tree holds 84 Markdown files and no non-Markdown files: 2 at the version root, 5 under `comparisons/`, 10 under `plans/`, and 67 under `development/` (including 60 prior history files). The new history will bring the active tree to 85 Markdown files.

Every Phase 3 document is Cat 4 active/current. The data contract is the runtime schema for Phases 4-5, the auth probe defines the least-privilege source boundary, the visual contract governs supplied artwork and later derivatives, the plan drives four remaining phases, and the history is the canonical handoff. No document is obsolete, duplicated, misplaced, archive-ready, or orphaned; no move, rename, deletion, archive operation, or reference repair is justified.

The two committed PNGs and their adjacent `icons/README.md` belong under the new `extensions/cursor-usage-monitor/` package scaffold rather than under `docs/`. The fixture directory and plan test are source artifacts. Generated output is limited to ignored Python caches and coverage data, and the temporary clean-scaffold test directory was removed after restoring the pre-existing empty scaffolds. Existing ignore rules are sufficient, so zero `.gitignore` patterns were added.

## v3.15.9 Phase 4 Audit - 2026-08-04

Before the Phase 4 history is written, the active v3.15 tree holds 85 Markdown files and no non-Markdown files: 2 at the version root, 5 under `comparisons/`, 10 under `plans/`, and 68 under `development/` (including 61 prior history files). The new history will bring the active tree to 86 Markdown files.

The Phase 4 plan update, known-gaps checkpoint, DEVLOG entry, cleanup report, and history are Cat 4 active/current. The Cursor extension's README belongs with its package and documents the data-layer boundary for Phase 5. No document is obsolete, duplicated, misplaced, archive-ready, or orphaned; no move, rename, deletion, archive operation, or reference repair is justified.

The new extension-local `.gitignore` adds four standard generated-output patterns (`node_modules/`, `out/`, `coverage/`, and `*.vsix`). Clean install, compile, and coverage created only those ignored paths. The temporary clean-scaffold repository-test directory was removed after restoring the pre-existing empty scaffolds. No root ignore change or generated artifact is included in the phase diff.

## v3.15.9 Phase 5 Audit - 2026-08-04

Before the Phase 5 history is written, the active v3.15 tree holds 86 Markdown files and no non-Markdown files: 2 at the version root, 5 under `comparisons/`, 10 under `plans/`, and 69 under `development/` (including the Phase 4 history). The new history will bring the active tree to 87 Markdown files.

Every Phase 5 document is Cat 4 active/current. The visual-contract acceptance update, known-gaps checkpoint, DEVLOG entry, CHANGELOG Unreleased note, plan checkbox closeout, and history are the canonical handoff. The extension README and `THIRD_PARTY_NOTICES.md` belong with the package. No document is obsolete, duplicated, misplaced, archive-ready, or orphaned; no move, rename, deletion, archive operation, or reference repair is justified.

Generated outputs remain covered by the existing extension-local ignore rules (`node_modules/`, `out/`, `coverage/`, `*.vsix`). Source artwork (`icons/cursor-ai-480.png`) stays packaging-excluded via `.vscodeignore` while the derived SVG, WOFF2, 48px warning mark, and package icon ship in the VSIX. Zero new `.gitignore` patterns were required.

## v3.15.9 Phase 6 Audit - 2026-08-04

Before the Phase 6 history is written, the active v3.15 tree holds 88 Markdown files after the live-smoke checklist was added (2 at the version root, 5 under `comparisons/`, 10 under `plans/`, and 71 under `development/` including Phase 5 history). The new Phase 6 history will bring the active tree to 89 Markdown files.

Every Phase 6 document is Cat 4 active/current: the live-smoke checklist is the mandatory CI-degrade companion, the plan checkbox closeout and known-gaps checkpoint record the dual-host gate, and the history is the canonical handoff. Workflow YAML and Dependabot entries are CI config, not docs. No document is obsolete, duplicated, misplaced, archive-ready, or orphaned; no move, rename, deletion, archive operation, or reference repair is justified. Zero new `.gitignore` patterns were required.

## v3.15.9 Phase 7 Final Audit - 2026-08-04

Before the Phase 7 history is written, the active v3.15 tree holds 89 Markdown files and no non-Markdown files: 2 at the version root, 5 under `comparisons/`, 10 under `plans/`, and 72 under `development/` (including the Phase 6 history). The new Phase 7 history will bring the active tree to 90 Markdown files. Every document remains Cat 4 active/current while v3.15.9 is being cut; no file qualifies for deletion, archival, consolidation, or relocation, and no reference repair is justified.

The repository-wide structural audit for the terminal phase found no tracked empty directory, no accidental duplicate group introduced by this plan, and no orphaned asset: every `extensions/cursor-usage-monitor/` icon, font, and script is referenced by the package manifest, README, or generator pipeline, and every `model-routing` bundled script, reference, and snapshot is cited from its SKILL.md. The 11 remaining `Rec. model / effort` occurrences were each inspected: all are intentional (legacy-compatibility guidance in `model-routing`, `/implement`, the implement-phase runbook, and AGENTS.md; the negative fixture in `tests/plans/test_v3_15_9_routing_contract.py`; and historical CHANGELOG/DEVLOG/v3.8-v3.9 plan records). One untracked empty directory left over from the v3.15.8 Phase 8 checklist relocation (`catalog/skills/code-review/references/`) was removed; the eight untracked empty skill scaffolds recorded in the v3.15.5 terminal audit remain parallel-session artifacts and were not modified, and the local `.antigravitycli/` tool directory was left untouched.

Phase 7 changed documentation, one README section, and two source files (README usage-monitor roster, CHANGELOG Unreleased completeness, this report, the known-gaps reconciliation, DEVLOG, and the session history, plus the skill-directory hardening in `scripts/lib/integrations/_catalog_adapters.py` and `scripts/validate_skills.py` with tests in `tests/integrations/test_catalog_adapters.py` and `tests/validators/test_validate_skills.py`). It added no new directory, artifact class, or scratch output. Generated output was limited to already-ignored Python caches and package-local extension outputs. Zero `.gitignore` patterns were added.

**Correction to the structural-audit paragraph above (same date, after the terminal test run).** The audit's statement that the seven empty skill scaffolds were "left unmodified" with no consequence was incomplete: `tests/integrations/test_copilot_hermes_native.py::test_hermes_skills_are_exactly_one_level_deep` failed on `commit-sweep has no SKILL.md at depth 1`. The scaffolds are untracked and empty, so git cannot see them and a clean CI checkout never reproduces the failure. Root cause was a disagreement between two gates: `flatten_skills` copied all 277 `<category>/<name>/` directories while `validate_skills.py --bundles-only` silently skipped the 7 lacking a `SKILL.md`. Phase 7 resolved it in the shared adapter (so every skills-bearing integration is corrected at once) rather than by deleting the scaffolds, which are preserved.

## v3.15.10 Phase 4 Final Audit - 2026-08-04

Before the Phase 4 history is written, the active v3.15 tree holds 96 Markdown files and no non-Markdown files: 2 at the version root, 5 under `comparisons/`, 11 under `plans/`, and 78 under `development/`. v3.15.10 added five documents (the notification contract, the summary-rule rationale, and three phase histories) plus the plan itself. The Phase 4 history brings the active tree to 97. Every document is Cat 4 active/current while v3.15.10 is being cut; none qualifies for deletion, archival, consolidation, or relocation, and no reference repair is justified.

The repository-wide structural audit found no orphan among the files this release added: every new hook (`_notify_common.{sh,ps1}`, `notify-attention-required.{sh,ps1}`) is referenced from `settings.json`, a sibling hook, a test, or the contract doc, and `_notify_common` is deliberately a module rather than a registered hook (leading underscore, matching the `_skill_rules.py` precedent), which is itself asserted by test. Seven empty skill scaffolds remain under `catalog/skills/` as maintainer work-in-progress; since v3.15.9 the installers skip any skill directory without a `SKILL.md` and the validator warns about them, so they are inert rather than harmful and were left untouched. One empty bundled subdirectory (`catalog/skills/developer-experience/code-optimizer/scripts`) exists inside a shipped skill and is recorded as a minor hygiene item rather than removed, because it is untracked local state rather than repository content.

Two dead-reference candidates were inspected and both are intentional. The `basename "$(pwd)"` strings remaining in `catalog/hooks/notify-on-complete.sh` and `catalog/hooks/tests/test_notify_triggers.py` are prose explaining the defect that was fixed, not live code. The same expression in `catalog/hooks/session-summary.sh` IS live and carries the identical mislabeling weakness, but that is a different hook with a different purpose and changing it does not trace to this release's scope, so it is recorded as a follow-on in the known-gaps advisory section instead.

Phase 4 changed documentation only (CHANGELOG, DEVLOG, known-gaps, this report, and the session history). It added no source file, directory, artifact class, or scratch output, and required zero new `.gitignore` patterns.

## v3.15.12 Phase 1 audit (2026-08-05, mode: audit - no files moved)

v3.15.12 Phase 1 added exactly one document to the active v3.15 tree: the phase session history under `development/history/`. It modified two existing documents in place (`development/cursor-usage-auth-probe.md` gained a "Phase 4 Authorization" section; `known-gaps.md` gained the v3.15.12 subsection) plus the repo-root `CHANGELOG.md`, `docs/DEVLOG.md`, this report, and the extension's own `README.md`. Every one of those is its canonical location, so nothing qualifies for deletion, archival, consolidation, or relocation, and no reference repair is justified. **The phase created no scratch document**, so there is nothing to propose cleaning up.

The orphan audit covers the four new source files and four new fixtures. All four sources (`consent.ts`, `session.ts`, `liveTransport.ts`, `liveAccess.ts`) are re-exported from `src/providers/index.ts`, imported by `src/extension.ts`, and each has a dedicated test file. All four fixtures (`wire-contract.json`, `wire-usage-summary.json`, `wire-field-drift.json`, `wire-unit-drift.json`) are read by `test/liveTransport.test.ts` and enumerated in `tests/plans/test_v3_15_9_cursor_usage_contracts.py`, whose `test_fixture_inventory_is_exact_and_parseable` asserts the inventory is exact, so an unreferenced fixture in that directory is a hard failure rather than a warning. No orphan exists.

One structural note, recorded rather than acted on: the wire fixtures sit at repo-root `tests/fixtures/cursor-usage/` while the code that pins them lives under `extensions/cursor-usage-monitor/`, which is why the extension's CI workflow does not trigger on a fixture-only edit (QG-6). Relocating the fixtures into the extension directory would fix the trigger but break the repo-level Python contract suite that also asserts over them, and colocating a copy would create the duplication this report exists to prevent. Adding the path to the workflow's filter is the smaller change and is what QG-6 proposes.

Phase 1 required zero new `.gitignore` patterns: vitest coverage output is already ignored by `extensions/cursor-usage-monitor/.gitignore:3` (`coverage/`), and `*.vsix` plus `extensions/**/out/` are already covered repo-wide.

## v3.15.12 Phase 2 audit (2026-08-05, mode: audit - no files moved)

v3.15.12 Phase 2 added **no** document to the active v3.15 tree beyond its required phase history. It modified two existing documents in place: `development/cursor-usage-visual-contract.md` (the on-demand meter rule, superseded by this phase) and `known-gaps.md`, plus the repo-root `docs/DEVLOG.md`, this report, and the extension's `README.md`. Every one is its canonical location, so nothing qualifies for deletion, archival, consolidation, or relocation, and no reference repair is justified. The phase created no scratch document.

One classification worth stating explicitly, because it is the kind of thing that later reads as a contradiction: the visual contract is dated `v3.15.9` in its own header while now carrying a v3.15.12 rule. It was amended rather than superseded by a new file on purpose. A second `cursor-usage-visual-contract-v3.15.12.md` would split one contract across two documents and leave a reader unsure which governs, which is exactly the duplication this report exists to prevent. The amended bullets name the version that changed them, so the provenance survives inside the single document.

Phase 2 added no source file, directory, artifact class, or scratch output. It changed three existing TypeScript sources and one existing test file, all inside the extension tree, and required zero new `.gitignore` patterns.

## v3.15.12 Phase 3 audit (2026-08-06, mode: audit - no files moved)

Phase 3 added one document to the active v3.15 tree (its phase history) and one test file outside it (`tests/installer/test_github_billing_rename.py`, which belongs beside the installer suites it extends). It modified two existing v3.15 development documents in place, `github-usage-data-contract.md` and `github-usage-visual-contract.md`, both of which asserted the old extension title as present fact. Nothing qualifies for deletion, archival, consolidation, or relocation, and no reference repair is justified. The phase created no scratch document.

Two naming classifications are worth stating, because both will otherwise read as oversights later.

First, the **filenames keep `github-usage`** while their content now says `GitHub Billing Usage`: the contracts stay at `github-usage-data-contract.md` and `github-usage-visual-contract.md`, and the extension stays at `extensions/github-usage-monitor/`. That is deliberate and consistent with the phase's central decision. The extension id is `publisher.name`, so the directory name is load-bearing for the id; renaming the directory would either break the id or require a second rename to keep it. The docs follow the code's naming so a reader grepping either finds both. Renaming the doc files would also invalidate every inbound reference from the v3.15.8 plan and its three histories, which are historical records that must not be rewritten.

Second, **history was deliberately not rewritten**. The v3.15.8 plan, its three phase histories, the root README's `## What's New in v3.15.8` section, and earlier CHANGELOG entries all still say "GitHub Usage Monitor". They record what shipped under that name at that time, and editing them would falsify the record. Only documents asserting the old name as *current fact* were changed.

Phase 3 added no directory, artifact class, or scratch output, and required zero new `.gitignore` patterns.

## v3.15.12 Phase 4 pre-work audit (2026-08-06, mode: audit - no files moved)

The Phase 4 pre-work added two documents to the active v3.15 tree, `development/github-billing-auth-probe.md` and its session history, and modified `development/github-usage-data-contract.md`, `known-gaps.md`, the plan, this report, `docs/DEVLOG.md`, `CHANGELOG.md`, and the extension `README.md`. Every one is its canonical location; nothing qualifies for deletion, archival, consolidation, or relocation. No scratch document was created.

One placement decision worth stating: the new probe doc sits beside `cursor-usage-auth-probe.md` under `development/`, matching the existing convention that a probe record lives with the contracts it constrains rather than in `plans/`. The two are deliberately parallel documents for the same reason - each records a premise that only a real host can settle - and a reader who finds one should find the other adjacent.

The orphan audit covers two new source files. `src/providers/authProbe.ts` is imported by `test/auth-probe.test.ts` and referenced by name from the probe doc, and it is deliberately **not** yet wired into `extension.ts`: it is a T022c instrument, and wiring it into activation before the probe has been run would imply a capability the extension does not yet have. That makes it referenced-but-unwired by design, not an orphan. `test/auth-probe.test.ts` is collected by the extension's Vitest glob.

Phase 4 pre-work added no directory, artifact class, or scratch output, and required zero new `.gitignore` patterns.

## v3.15.12 Phase 4 and Phase 5 final audit (2026-08-06, mode: audit - no files moved)

Phase 4 added two session histories and no other document; Phase 5 added its own history and amended `known-gaps.md`, `CHANGELOG.md`, `docs/DEVLOG.md`, this report, and the plan. All canonical locations. Nothing qualifies for deletion, archival, consolidation, or relocation, and no reference repair is justified because nothing moved.

The repository-wide structural audit found: 8 empty directories under `catalog/skills/`, all untracked and all the same set prior reports dispositioned as maintainer work-in-progress or parallel-session artifacts, left untouched; no tracked build or coverage artifact (`git ls-files` matches nothing under `out/`, `coverage/`, or `*.vsix`); and no `TODO` / `FIXME` / `XXX` / `HACK` / `# DEVIATION` marker in any of the 40-plus files this version changed.

One untracked file belongs to a parallel session (`docs/v3/v3.17/comparisons/v3.19.2-comparison-mattpocock-...`, which that session renumbered out of v3.15.13 during this work). It was never staged. Every commit in this version staged by explicit path rather than `git add -A`, after the first Phase 1 commit nearly swept an earlier file of theirs in; that is recorded in the v3.15.12 Phase 2 history as the reason.

New source files this version, all referenced and none orphaned: the Cursor extension gained `providers/{consent,session,liveTransport,liveAccess,wireShape}.ts` plus `scripts/probe-wire-shape.js`, and the GitHub extension gained `providers/{authProbe,capability,sessionBinding,diagnose}.ts` plus `scripts/probe-billing-auth.js`. Each is imported by source or driven by a test; the two `scripts/` runners are referenced from their probe docs and excluded from both VSIXs by `.vscodeignore`.

One deliberate non-orphan worth naming: `providers/authProbe.ts` is now reached from shipped code (the diagnostic) rather than tests alone, which it was during Phase 4 pre-work. At that point it was referenced-but-unwired **by design**, because wiring a probe into activation before the probe had been run would have implied a capability the extension did not have.

An advisory, pre-existing and not introduced here: `docs/DEVLOG.md` carries 22 non-ASCII characters from line 2422 onward, all in v2.0.0-era entries. This version's own entries are ASCII-clean, verified. Left untouched as historical record; line numbers recorded in `known-gaps.md` for a future sweep.

Phases 4 and 5 added no artifact class or scratch output, and required zero new `.gitignore` patterns.

## v3.15.14 Phase 1 audit (2026-08-07)

**Mode**: Audit and report; no file moves, no deletions.

Phase 1 is prose-only. It modified five committed Markdown files (`catalog/templates/spec-template.md`, `catalog/templates/spec-quality-checklist.md`, `catalog/skills/developer-experience/spec-driven-development/SKILL.md`, `catalog/skills/developer-experience/idea-refine/SKILL.md`, `catalog/agents/scope-guardian-reviewer.md`) plus this version's `known-gaps.md`. It added no file anywhere, so `catalog/templates/` gained nothing that would need installer registration, and no reference repair was required because nothing moved or was renamed.

One scratch artifact was created and discarded within the phase: a throwaway spec authored from the updated template to confirm every `spec-quality-checklist.md` item can be ticked from the template alone. It was written to the session scratchpad, never to the repository, and deleted after the walkthrough. No `.gitignore` pattern was needed.

Marker sweep over the five changed files: zero `TODO` / `FIXME` / `XXX` / `HACK` / `# DEVIATION:` hits. The phase's one deviation from the plan's literal instruction is recorded as DF-1 in `known-gaps.md` rather than left inline, matching the convention this version has used throughout.

The 8 untracked empty directories under `catalog/skills/` reported in the v3.15.5 and v3.15.7 audits are unchanged and were again left in place, for the same reason: they carry zero tracked files, so they have zero repository impact, and they appear to be a parallel session's in-progress scaffolding.

## v3.15.14 Phase 2 audit (2026-08-07)

**Mode**: Audit and report; no file moves, no deletions.

Phase 2 modified exactly one committed file, `catalog/skills/developer-experience/spec-driven-development/SKILL.md`, plus this version's `known-gaps.md`, `docs-cleanup-report.md`, and `DEVLOG.md`, and added one session-history file. No file was created under `catalog/`, so no installer registration applies and no reference repair was needed.

Marker sweep over the changed file: zero `TODO` / `FIXME` / `XXX` / `HACK` / `# DEVIATION:` hits. The phase produced no scratch artifact of any kind, so no `.gitignore` pattern was needed.

The skill body is 332 lines after this phase, comfortably inside the 500-line size norm, so no `references/` extraction is warranted yet. Phase 1 removed 73 lines from this file and Phase 2 added 31 net, leaving it 42 lines shorter than when this plan started despite carrying two new rules.

The 8 untracked empty directories under `catalog/skills/` are unchanged and were again left in place, for the reason recorded in the v3.15.5, v3.15.7, and v3.15.14 Phase 1 audits: they carry zero tracked files and appear to be a parallel session's scaffolding.

## v3.15.14 Phase 3 audit (2026-08-07)

**Mode**: Audit and report; no file moves, no deletions.

Phase 3 modified exactly one committed file under `catalog/`, `catalog/skills/workflow/implementation-plan/SKILL.md`, plus this version's `known-gaps.md`, `docs-cleanup-report.md`, and `DEVLOG.md`, and added one session-history file. No file was created under `catalog/`, so no installer registration applies and no reference repair was needed.

Two structural notes specific to this phase.

The skill body grew from 445 to 469 lines, which is 31 under the 500-line target and well inside the 800-line hard cap, so no `references/` extraction is warranted. The extraction question was considered rather than assumed: both new conventions are authoring-time rules that shape every sub-task an author writes, which is Tier 2 material, whereas a worked catalogue of failure-mode examples would be Tier 3. If this file grows further, that catalogue is the first thing to move out.

`catalog/skills/workflow/plan-before-code/SKILL.md` was deliberately NOT edited. Sub-task 3.1 required choosing exactly one plan-layer skill, and the exit checklist asks for confirmation that the other was left alone. Its last commit is `39577bbe` (v3.0.0 Phase 9), unchanged by this plan.

Marker sweep over the changed file: zero `TODO` / `FIXME` / `XXX` / `HACK` / `# DEVIATION:` hits. No scratch artifact was produced and no `.gitignore` pattern was needed.

The 8 untracked empty directories under `catalog/skills/` are unchanged and were again left in place, for the reason recorded in every prior audit in this version.

## v3.15.14 Phase 4 audit (2026-08-08) - terminal-phase refactor gate

**Mode**: Audit, then apply with maintainer confirmation. This is the plan's final phase, so the mandatory refactor gate ran rather than an audit-only pass.

**The plan's two specific checks are clean.** No orphaned reference to the removed inline spec template survives anywhere in `catalog/`, `guides/`, or `docs/`: a sweep for the distinctive "Objective / Commands / Project Structure / Code Style / Boundaries" cluster attributed to a spec returns nothing. The single `### Objective` heading remaining under `catalog/` belongs to `competitive-generation`'s task-brief template (Objective plus Acceptance Criteria for a competitive-generation brief), which is unrelated and correctly untouched. `catalog/templates/` gained no stray file across the whole plan; it still holds exactly `constitution-template.md`, `spec-quality-checklist.md`, and `spec-template.md`, so no installer registration is required in either installer.

**Eleven empty directories were removed, reversing this version's standing posture on an explicit maintainer decision.** Every prior audit (v3.15.5, v3.15.7, and v3.15.14 Phases 1 to 3) reported the 8 untracked empty directories under `catalog/skills/` and left them as a parallel session's scaffolding. This phase surfaced them again plus a ninth, `docs/v3/v3.17/comparisons`, and the maintainer chose deletion. Each was removed only after verifying it was genuinely empty AND carried zero tracked files. Removing the `scripts/` children exposed two parent shells that held no `SKILL.md` (`catalog/skills/testing/visual-regression-testing` and `catalog/skills/tests-generation/performance-regression-gate`); both passed the same two-part test and were removed. `git status` is unchanged by all eleven removals, which is the proof of zero repository impact.

The decision was better than the precedent it reversed: `validate_skills.py --bundles-only` warnings fell from **18 to 11**, because several of the removed `scripts/` directories were producing orphan-bundle warnings. The standing "report and leave" posture was defensible on the grounds given (do not delete another session's work-in-progress) but was quietly costing validator signal, and nothing tracked was ever at risk.

**Layout otherwise unchanged.** No committed file moved or was renamed across the whole plan, so no reference repair was needed at any phase. The `docs/v3/v3.15/` tree stays canonical (comparisons / development / plans / known-gaps / this report). No tracked build or coverage artifact exists: `git ls-files` matches nothing under `out/`, `coverage/`, or `*.vsix`. No untracked file sits under `docs/`.

**One file was added outside `catalog/` this phase**: `tests/skills/test_spec_artifact_agreement.py`, the MT-1 guard. It lands in the existing `tests/skills/` tree that CI already runs as a directory, so it needs no new job and no installer registration (repo-internal tests are not a distributed surface).

**Marker sweep across every file this version changed**: zero `TODO` / `FIXME` / `XXX` / `HACK` / `# DEVIATION:` markers. Deviations and decisions live in `known-gaps.md` and the session histories, not inline.
