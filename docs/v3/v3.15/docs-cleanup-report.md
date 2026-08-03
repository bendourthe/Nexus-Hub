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
