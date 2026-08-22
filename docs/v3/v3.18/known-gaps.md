# Known Gaps - v3.18

**Project**: Nexus-Hub
**Status**: v3.18.0 (`docs-lifecycle-retention`) Phases 1-5 implemented on `feat/docs-lifecycle-retention`, not yet released. Reconciled 2026-08-21 at the end of Phase 5.
**Last updated**: 2026-08-21 (Phase 5 reconciliation)

> **File-lifecycle note**: this ledger is opened by the v3.18.0 Phase 5 reconciliation. Each subsequent v3.18.N implementation appends its own `## v3.18.N - <slug>` section rather than replacing this file, keeping its own `DF-#` / `NI-#` / `BG-#` / `WN-#` / `MT-#` / `QG-#` numbering.

> **Prior-version ingest**: checked `docs/v3/v3.17/known-gaps.md`. **MT-1** (AGENTS.md is 74% of the always-loaded budget) is **RESOLVED here** in Phase 3 and is marked so in the v3.17 ledger with its delta. No other v3.17 item is in this plan's scope: the open v3.17 items concern platform read-contracts, org-knowledge precedence, and usage-monitor coverage, none of which this documentation-lifecycle plan touches. They stay in the v3.17 ledger with their existing owners.

---

## v3.18.0 - docs-lifecycle-retention

**Status**: Phases 1-5 implemented. DEVLOG is a 99-line index, every writer produces that format, AGENTS.md is down 2,578 relocated words with MT-1 closed, and the retention policy plus its advisory checker are in place. Release is handed to `/update release`.

### BG-1 - RESOLVED in Phase 2: `auto-devlog.ps1` shipped with no opt-in gate

- **Target files**: `catalog/hooks/auto-devlog.ps1`, `catalog/hooks/tests/test_auto_devlog_index_guard.py`
- **What it was**: `auto-devlog.sh` has gated on `AUTO_DEVLOG=1` since it shipped. The PowerShell sibling checked only `NEXUS_DISABLED_HOOKS` and `NEXUS_HOOK_PROFILE`, so on PowerShell the hook was effectively **opt-out** and appended to `docs/DEVLOG.md` at every session end for users who never asked for it.
- **Why it matters beyond the divergence**: it is the most plausible explanation for the growth anomaly this plan recorded without a cause. The plan measured `docs/DEVLOG.md` at 3,149 lines on 2026-08-18; Phase 1 found 5,615 on 2026-08-21. No release accounts for 2,466 lines in three days.
- **How it surfaced**: the new parity test, not review. A POSIX-only test could not reach it, which is the case AGENTS.md makes for parametrizing every behavioral assertion over both implementations.
- **Resolution**: the gate is present in both, with a comment recording the divergence so the fix is not mistaken for a stylistic addition.

### BG-2 - RESOLVED in Phase 2: neither `auto-devlog` implementation could tell an index from a log

- **Target files**: `catalog/hooks/auto-devlog.sh`, `catalog/hooks/auto-devlog.ps1`
- **What it was**: both prepend a narrative entry above the first `## [` heading. The index format contains no such heading, so the entry would have landed inside the table, corrupting it silently.
- **Resolution**: both detect the index table header, print where narrative belongs, and exit 0. The guard is deliberately narrow and the tests assert both directions, because a guard that fired on every DEVLOG would silently disable the hook for consuming projects that kept the narrative format, and that failure is indistinguishable from the hook working.

### DF-1 - OPEN (accepted): the DEVLOG index format is held by prose plus one test, not by a writer-side gate

- **Target files**: `catalog/skills/workflow/devlog-generation/SKILL.md`, `tests/validators/test_devlog_index_format.py`
- **What it is**: Phase 2 aligned every writer's *instructions*, and `test_devlog_index_format.py` asserts the artifact's properties after the fact. Nothing stops an agent writing a paragraph into a table cell at the moment it writes it; the test catches it on the next run.
- **Why it is accepted**: the conformance suite is the enforcement, and it is a hard gate (the 150-line ceiling fails the build). A writer-side gate would mean a pre-commit hook parsing partially-written Markdown, which is more machinery than the risk justifies.
- **Owner**: none required. Revisit only if the conformance test starts catching real regressions rather than guarding against them.

### DF-2 - OPEN (deferred to a follow-on): SKIP clauses fight the trigger-routing scorer

- **Target files**: `scripts/run_trigger_evals.py`, `scripts/validate_skills.allowlist.json`, `AGENTS.md`
- **What it is**: `run_trigger_evals.py` tokenizes a skill's whole `description` with no notion of negation, so a `SKIP:` clause that names what it fences off imports that vocabulary as **positive** trigger words. Authoring `devlog-generation`'s routing cases hit this twice: "generate the changelog entry for this release" scored a perfect **1.00** against `devlog-generation` purely on SKIP-clause text, and after that was worded around, "what work is still open or deferred for this version" scored 1.00 for the same reason.
- **Why it matters repo-wide**: `AGENTS.md` instructs every skill author to add a SKIP clause, and the routing gate penalises doing so. The 40 currently-allowlisted near-collisions were allowlisted without this lens and are worth re-examining under it.
- **Local workaround applied**: every SKIP clause in `devlog-generation` now names its target skill without reusing the target's own vocabulary ("unfinished or carried-over items (use known-gaps-tracker)" rather than "open or deferred work").
- **Suggested disposition**: either strip `SKIP:` / `Do NOT use for:` clauses from the text the scorer tokenizes, or score them negatively. Needs its own plan; changing scoring semantics affects all 273 skills and all 40 allowlist entries.

### DF-3 - OPEN (deferred): a link checker treating `#` as same-page cannot see an anchor orphaned by relocation

- **Target files**: any documentation link check, including `[[documentation-consistency]]`
- **What it is**: Phase 3 relocated a block containing three anchor-only links (`#three-tier-loading-model` and siblings). They were same-page anchors in `AGENTS.md` and became dangling cross-file links the instant the content moved. The link check **skipped them**, because it treats `#`-prefixed targets as same-page by definition, which they had stopped being. They were found by reading the file.
- **Why it matters**: this is a general property of relocation, not a one-off. Any future ratchet-down pass will hit it.
- **Suggested disposition**: when a documentation link gate is built, resolve `#anchor` targets against the containing file's own headings rather than assuming validity.

### WN-1 - OPEN (pre-existing, not caused here): `test_ps_standalone_extracts_and_hands_off` fails on a bare `tar`

- **Target files**: `install.ps1`, `tests/installer/test_bootstrap.py`
- **What it is**: `install.ps1` in standalone mode shells out to `tar`, which on a host that invokes PowerShell from a Git Bash session resolves to `/usr/bin/tar` and fails to decompress the test's stub tarball with "unexpected end of file / Child returned status 128".
- **Why it is recorded here**: found during Phase 1 verification, and it is the **third** instance in this repository of a bare tool name on Windows resolving through PATH to the wrong binary. The other two are `bash` finding the System32 WSL stub, documented in v3.15.6 Phase 4 and re-diagnosed from scratch in v3.17.6 Phase 6.
- **Not caused by this plan**: the failing path reads `install.ps1`, `scripts/installer.ps1`, and a temp-directory stub tarball. This plan's diff is documentation, hooks, and repo-internal tooling.
- **Suggested disposition**: resolve `tar` empirically the way `tests/validators/bash_helper.py` resolves `bash`, rather than trusting PATH order. That helper already exists and is the obvious template.

### WN-2 - OPEN (accepted): the retention rule is advisory and can be ignored indefinitely

- **Target files**: `docs/policy/docs-retention.md`, `scripts/check_docs_retention.py`
- **What it is**: the checker always exits 0, so the policy's effect depends on someone reading its output. It is wired into `make validate` and the CI `validate` job as an informational step for that reason.
- **Why it is accepted**: a hard gate would block an unrelated release the moment a minor version aged out, which is a real cost preventing no harm, and archiving is a reference-repair operation that needs a confirmation gate. Recorded in the decision record's Consequences.
- **Suggested disposition**: if the report turns out to be ignored in practice, the honest fix is a step in the release flow that requires an explicit decision, not a hard validator gate.

### MT-1 - RESOLVED in Phase 5: the first retention archive pass is executed

- **Target files**: `docs/v3/v3.0` through `docs/v3/v3.15` (`development/history/` only), `docs/archive/v3/`, 75 files of reference repair
- **What it was**: `scripts/check_docs_retention.py` reported 16 versions due for archival, the one-time backlog of having had no retention rule.
- **Resolution**: executed. 216 files moved from `docs/v3/v3.<MINOR>/development/history/` to `docs/archive/v3/v3.<MINOR>/development/history/`, one version at a time with a per-version file-count check. 75 files of inbound references repaired, including **54 rows of the DEVLOG index built in Phase 1** (its history links now point at the archive). Nine `development/` directories became empty and were removed. The checker now reports nothing due.
- **What executing it changed about the policy**: see DF-4 below. The scope narrowed from `development/` to `development/history/`, and that narrowing is the most valuable thing the pass produced.

### DF-4 - RESOLVED in Phase 5 (policy corrected): `development/` also holds live CI inputs and shipped-code citations

- **Target files**: `docs/policy/docs-retention.md`, `scripts/check_docs_retention.py`, `tests/validators/test_check_docs_retention.py`, the decision record
- **What was wrong**: the policy as authored in Phase 4 archived a version's whole `development/` subtree. Attempting that in Phase 5 found `development/` is not only working notes:
  - `.github/workflows/presentify-extractor.yml` **executes** six Python scripts under `docs/v3/v3.12/development/fixtures/` and `docs/v3/v3.13/development/fixtures/`. Archiving them breaks CI outright.
  - v3.15 holds eleven contract documents that shipped hooks (`_notify_common.sh` / `.ps1`, `notify-on-complete.*`, `notify-attention-required.*`) and tests cite by path in comments and skip messages.
  - v3.9, v3.12, and v3.13 hold `worked-example/` trees with 68 non-Markdown files between them.
- **How it surfaced**: building the inbound-reference index **before** moving anything, which the plan's propose-then-apply instruction requires. A grep for the moved paths returned 227 occurrences across 128 files, and reading them rather than counting them showed that some were CI `run:` steps and code comments rather than documentation links.
- **Resolution**: the unit that ages out is now `development/history/`. The reason is stated in the policy (with a table naming each category and why it stays), in the checker's `AGING_SUBDIR` comment, in the decision record's Consequences, and in a dedicated test (`test_non_history_development_content_is_never_reported`), so it cannot be widened back by accident.
- **Follow-on worth considering**: CI fixtures arguably do not belong in a version's docs directory at all. Relocating them to `tests/fixtures/` and the contract docs to `docs/policy/` is defensible, but it is a separate refactor with its own reference repair and its own risk of breaking CI, and a retention rule should not do it as a silent side effect.

### MT-2 - OPEN (suggestion): the DEVLOG line ceiling lives in a test constant, not in the budget policy

- **Target files**: `tests/validators/test_devlog_index_format.py`, `docs/policy/doc-budgets.json`
- **What it is**: the 150-line ceiling for `docs/DEVLOG.md` is a module constant in the conformance test. Every other always-loaded-document ceiling lives in `docs/policy/doc-budgets.json` with a documented ratchet rule.
- **Why it is a suggestion, not a defect**: the budget file measures **words** in always-loaded docs, and DEVLOG is neither always-loaded nor word-bounded (its constraint is one line per release). Moving it would require the budget file to carry two units.
- **Suggested disposition**: leave as-is unless a second line-bounded document appears, at which point the two justify a shared home.

---

## Reconciliation summary (2026-08-21, Phase 5)

| Category | Closed | Open |
|---|---|---|
| Bugs (`BG-#`) | 2 (BG-1, BG-2) | 0 |
| Deferred / design (`DF-#`) | 1 (DF-4, policy corrected in Phase 5) | 3 (DF-1 accepted, DF-2 and DF-3 deferred with dispositions) |
| Warnings (`WN-#`) | 0 | 2 (WN-1 pre-existing, WN-2 accepted by design) |
| Maintenance (`MT-#`) | 1 (MT-1, archive pass executed) | 1 (MT-2 suggestion) |
| Ingested from v3.17 | 1 (MT-1 AGENTS.md budget share, resolved in Phase 3) | 0 |

**Release blockers: 0.** Every open item is either accepted by design with its reasoning recorded, pre-existing and out of this plan's scope, or a carried follow-on that breaks nothing while it waits.
