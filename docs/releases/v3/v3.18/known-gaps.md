# Known Gaps - v3.18

**Project**: Nexus-Hub
**Status**: v3.18.0 (`docs-lifecycle-retention`) released. v3.18.1 (`github-usage-monitor-accuracy`) Phases 1-6 implemented on `feat/v3.18.1-github-usage-monitor-accuracy`. **Zero release blockers across both.**
**Last updated**: 2026-08-22 (post-v3.18.2 housekeeping: v3.18.2 MT-1 closed by the v3.16 history archive pass; BG-2 recorded as an environment-only local-run flake)

> **File-lifecycle note**: this ledger is opened by the v3.18.0 Phase 5 reconciliation. Each subsequent v3.18.N implementation appends its own `## v3.18.N - <slug>` section rather than replacing this file, keeping its own `DF-#` / `NI-#` / `BG-#` / `WN-#` / `MT-#` / `QG-#` numbering.

> **Prior-version ingest**: checked `docs/v3/v3.17/known-gaps.md`. **MT-1** (AGENTS.md is 74% of the always-loaded budget) is **RESOLVED here** in Phase 3 and is marked so in the v3.17 ledger with its delta. No other v3.17 item is in this plan's scope: the open v3.17 items concern platform read-contracts, org-knowledge precedence, and usage-monitor coverage, none of which this documentation-lifecycle plan touches. They stay in the v3.17 ledger with their existing owners.

---

## v3.18.0 - docs-lifecycle-retention

**Status**: Phases 1-5 implemented and every gap closed. DEVLOG is a 99-line index, every writer produces that format, AGENTS.md is down 2,578 relocated words with MT-1 closed, the retention policy and its advisory checker are in place, and the first archive pass moved 216 files. Release is handed to `/update release`.

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

### DF-1 - CLOSED as accepted 2026-08-21: the DEVLOG index format is enforced by a CI-gating test, not a writer-side hook

- **Target files**: `catalog/skills/workflow/devlog-generation/SKILL.md`, `tests/validators/test_devlog_index_format.py`
- **What it was**: Phase 2 aligned every writer's *instructions*; nothing stops an agent writing a paragraph into a table cell at the moment it writes it.
- **Why the acceptance holds, now verified rather than asserted**: `tests/validators/test_devlog_index_format.py` is run by `python -m pytest tests/validators` in **both** the `tests` and `tests-windows` CI jobs, and `tests` feeds the `ci-required` aggregate. Its 150-line ceiling is a hard assertion, so a regression fails the build rather than warning. The check is one run late, not absent.
- **Why not a writer-side gate**: a `PreToolUse` hook on writes to `docs/DEVLOG.md` would have to parse partially-written Markdown and decide whether a half-finished table is a violation. That is more machinery, and more false-positive surface, than a one-run-late hard gate justifies.

### DF-2 - RESOLVED 2026-08-21: SKIP clauses no longer feed the routing scorer positive vocabulary

- **Target files**: `scripts/run_trigger_evals.py`, `scripts/run_trigger_evals.allowlist.json`, `tests/validators/test_run_trigger_evals.py`
- **What it was**: the scorer tokenized a skill's whole `description`, so a `SKIP:` clause naming what it fences off imported that vocabulary as **positive** trigger evidence. Two real cases: "generate the changelog entry for this release" scored a perfect **1.00** against `devlog-generation`, and so did "what work is still open or deferred for this version", both purely on SKIP-clause text. `AGENTS.md` tells every author to write a SKIP clause, so the gate was penalising authors for following the rule.
- **Resolution**: `strip_skip_clause()` drops everything from the first SKIP marker (`SKIP:`, `SKIP -`, `Do NOT use for`) onward before tokenizing, applied at both description-tokenization sites and deliberately **not** to prompts. Six regression tests added.
- **Measured blast radius**: allowlisted collisions went 40 to 37, un-allowlisted stayed at 0, routing failures stayed at 0. Four previously-colliding pairs fell below threshold, and **one new collision appeared** -- counterintuitive until you notice the overlap ratio divides by the smaller token set, so removing tokens shrinks the denominator too and a ratio can rise. `multi-agent-code-review` vs `pr-description-writer` landed at exactly 50%; both key on the same object (a pull request) with different verbs, so it is allowlisted with that reasoning rather than papered over by editing a description.
- **Four now-unused allowlist entries were left in place.** They name pairs that are still *intentional* neighbours even though their measured overlap now sits below threshold, and there is no unused-entry enforcement. Pruning them would only re-open them the next time a description changes.
- **Authoring hazard found on the way**: see BG-3.

### DF-3 - RESOLVED 2026-08-21 by decision: the anchor hazard is documented, and a general validator was rejected on evidence

- **Target files**: `docs/policy/docs-retention.md`, `catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md`
- **What it was**: an in-document anchor link is a same-page reference until its content moves to another file, at which point it dangles and no link checker sees it, because a fragment-only target reads as same-page by definition. Phase 3 moved a block with three such anchors; the link check passed and they were found by reading the file.
- **A general anchor validator was built as a measurement and then rejected.** Across the repo it found 19 "dangling" anchors out of 101, and every one was legitimate on inspection: illustrative anchors inside a skill that teaches document structure, README **template** placeholders whose target sections are created when the template is filled, and one outright false positive of its own making. That last one is decisive. The checker flagged a correct table of contents because the forge replaces each space with a hyphen while the implementation collapsed whitespace runs, so `Compliance & Governance` slugs to `compliance--governance` and not `compliance-governance`. A gate whose first real sample is a false positive on valid documentation gets ignored, and an ignored gate is worse than no gate.
- **Resolution**: the rule is stated where relocation is governed (`docs-retention.md`) and where it is executed (`docs-layout-refactor`), both naming the Phase 3 incident and prescribing a manual grep for fragment links over any moved block. The three concrete instances were repaired in Phase 3.

### WN-1 - RESOLVED 2026-08-21: `install.ps1` resolves `tar` explicitly instead of trusting PATH

- **Target files**: `install.ps1`
- **Root cause, proven by reproduction rather than inferred**: GNU tar (the one Git Bash / MSYS put on PATH) parses a drive-letter path as a remote `host:path` specification, so extracting from a `C:` path makes it try to connect to a host named `C`:

  ```text
  tar (child): Cannot connect to C: resolve failed
  gzip: stdin: unexpected end of file
  /usr/bin/tar: Child returned status 128
  ```

  The gzip line is downstream noise from a child that never received data, which is why this has read as a corrupt archive rather than a path-parsing bug.
- **Resolution**: `Resolve-TarExe` prefers the Windows system tar under `System32` (bsdtar, shipped on Windows 10 1803+, which handles drive letters correctly) and falls back to PATH `tar` only when it is absent. Applied at all three sites: the dependency precheck, the extractor-availability decision, and the extraction call.
- **Verification**: `tests/installer/test_bootstrap.py` goes from 4 passed / 1 failed to **5 passed**, with no test changes. The fix is in the product, not the assertion.
- **The pattern this closes for the third time**: a bare tool name on Windows resolving through PATH to the wrong binary. The first two were `bash` finding the System32 WSL stub (v3.15.6 Phase 4, misdiagnosed for four minor versions; v3.17.6 Phase 6, rediscovered from scratch). `tests/validators/bash_helper.py` already solved it for `bash` by probing empirically; this solves it for `tar` by resolving the known-good binary explicitly.

### WN-2 - CLOSED as accepted by design 2026-08-21: the retention rule is advisory

- **Target files**: `docs/policy/docs-retention.md`, `scripts/check_docs_retention.py`
- **What it is**: the checker always exits 0, so the policy's effect depends on someone reading its output. It runs in `make validate` and in the CI `validate` job as an informational step.
- **Why the acceptance holds**: a hard gate would block an unrelated release the moment a minor version aged out, which is a real cost preventing no harm, and archiving is a reference-repair operation that needs a confirmation gate rather than a validator. The Phase 5 pass is the existence proof that the advisory report does get acted on.
- **If it is ever ignored in practice**, the fix is a step in the release flow that forces an explicit decision, not a hard validator gate.

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

### MT-2 - CLOSED by decision 2026-08-21: the DEVLOG line ceiling stays in the test constant

- **Target files**: `tests/validators/test_devlog_index_format.py`, `docs/policy/doc-budgets.json`
- **The question**: the 150-line ceiling for `docs/DEVLOG.md` is a module constant in the conformance test, while every other document ceiling lives in `docs/policy/doc-budgets.json` with a documented ratchet rule.
- **Decision: leave it where it is.** `doc-budgets.json` maps a path to a **word** ceiling for **always-loaded** instruction documents, and `validate_doc_budgets.py` computes headroom as a fraction of that number. `docs/DEVLOG.md` is neither always-loaded nor word-bounded: its constraint is one line per release. Putting it there would require the schema to carry a unit per entry and the validator to branch on it, to express a single ceiling.
- **Revisit when** a second line-bounded document appears. Two would justify a shared home; one does not justify a schema change.

### BG-3 - RESOLVED 2026-08-21: escaped word boundaries reached a regex as literal control characters

- **Target files**: `scripts/run_trigger_evals.py`, `tests/validators/test_run_trigger_evals.py`
- **What happened**: the first cut of the DF-2 SKIP-marker pattern was authored with escaped word boundaries that arrived in the file as literal **backspace bytes** (`0x08`), six of them. The compiled regex therefore matched nothing, `strip_skip_clause()` was a silent no-op, and the fix appeared to be in place while changing nothing.
- **Why it took a second look**: `grep` renders `0x08` as nothing, so the pattern line looked correct on inspection. It was caught only by printing `_SKIP_MARKER.pattern` with `repr()` after the behavioural check came back unchanged.
- **Resolution**: control characters stripped, pattern rewritten, and `test_skip_marker_pattern_contains_no_control_characters` added so the same accident fails loudly instead of silently.
- **Transferable lesson**: when a regex-based fix appears to do nothing, print the compiled pattern with `repr()` before re-reading the logic. A behavioural assertion that a helper actually transforms its input would also have caught it, which is why one now exists.

---

## Reconciliation summary (2026-08-21, Phase 5)

| Category | Closed | Open |
|---|---|---|
| Bugs (`BG-#`) | 3 (BG-1, BG-2, BG-3) | 0 |
| Deferred / design (`DF-#`) | 4 (DF-1 accepted, DF-2 fixed, DF-3 decided, DF-4 policy corrected) | 0 |
| Warnings (`WN-#`) | 2 (WN-1 fixed, WN-2 accepted by design) | 0 |
| Maintenance (`MT-#`) | 2 (MT-1 archive pass executed, MT-2 decided) | 0 |
| Ingested from v3.17 | 1 (MT-1 AGENTS.md budget share, resolved in Phase 3) | 0 |

Every item raised during v3.18.0 is closed: five fixed in code, three closed by an explicit recorded decision, and one policy corrected by attempting to execute it. Two of the fixes (`WN-1`, `BG-3`) are defects the plan never anticipated, and both were found by verifying a result rather than by reading code.

**Release blockers: 0.** Every open item is either accepted by design with its reasoning recorded, pre-existing and out of this plan's scope, or a carried follow-on that breaks nothing while it waits.

---

## v3.18.1 - github-usage-monitor-accuracy

**Status**: Phases 1-6 implemented on `feat/v3.18.1-github-usage-monitor-accuracy`. Extension at 0.4.0. Three reported defects fixed, the weight table removed as a behavioral input, and the residual uncertainty converted from an argument into a falsifier with a ledger behind it.

**Prior-version ingest**: checked `docs/v3/v3.16/known-gaps.md` and `docs/v3/v3.17/known-gaps.md`. **v3.16 NI-2** (the drawdown weights cannot be verified) is **superseded here** and marked so in that ledger: the constants it described no longer exist, though the underlying uncertainty carries forward as NI-1 below. **v3.16 NI-4** (self-hosted and larger-runner exclusion rules are tested against invented SKU strings only) remains open and unchanged - this release did not acquire a real inventory for either, and it now matters slightly more, because an excluded runner that should have been included is a hole in a weighted figure rather than an unweighted one. No other prior item is in this plan's scope.

### NI-1 - CLOSED as MOOT 2026-08-22: price ratios and the legacy multipliers cannot be separated by any saturated month

- **Target files**: `extensions/github-usage-monitor/src/providers/drawdown.ts`, `docs/v3/v3.18/development/github-drawdown-ledger.md`
- **What is unresolved**: the shipped model weights by current price ratios (Windows 1.67x, macOS 10.33x). The legacy published multipliers (2x, 10x) fit the same data, differing by about 0.3% of the weighted total. Every month observed on the measured account is either **saturated** (so it reports only "at least the allowance" and cannot choose between two models that both predict above the cap) or **Linux-dominated** (so every candidate yields the same answer within tolerance). The data does not distinguish them.
- **Decision**: ship the derived ratios, because the mechanism tracks GitHub's price changes and a hardcoded snapshot demonstrably does not - this number was revised three times for exactly that reason. This is a bet on the mechanism's stability, not a claim that the evidence separates the candidates, and the decision record says so in its Consequences.
- **Disposition**: `docs/v3/v3.18/development/github-drawdown-ledger.md` states the falsifier - an unsaturated month whose non-Linux share exceeds 15% and whose displayed value matches unweighted raw minutes - and `src/providers/reconciliation.ts` refuses to classify a saturated or Linux-dominated month as support. A fourth revision has to produce a discriminating month rather than an argument.
- **Reconciled 2026-08-22 (v3.18.3 Phase 5): CLOSED as MOOT.** Every target file above lives under `extensions/github-usage-monitor/`, which **v3.18.2 withdrew and deleted**. The limitation is real and the analysis stands, but there is no longer any shipped code it constrains. Verified by absence: the directory does not exist and the extension roster is three usage monitors, not four. Re-open only if the monitor is ever rebuilt, and read the withdrawal decision record first - the reason it was withdrawn is that GitHub serves no included-usage figure at all.

### NI-2 - CLOSED as MOOT 2026-08-22: the included allowance is still plan-table-derived

- **Target file**: `extensions/github-usage-monitor/src/providers/planEntitlements.ts`
- **What is unresolved**: no billing endpoint returns the included allowance. The legacy product-specific endpoints that served `included_minutes` closed down in September 2025 and return 404/410; `/settings/billing/usage` returns consumption only. The denominator therefore comes from a published plan table (2,000 minutes, 0.5 GB on Free) that nothing on the account confirms.
- **Decision**: keep the plan table with the existing manual override as the correction path, and label the denominator's provenance in the panel, which Phase 4 now does as a separate sentence from the numerator's.
- **Why not scraped**: `github.com/settings/billing` requires a browser session cookie, and the extension holds an OAuth Bearer token, so the page is unreachable with the credential it has. It is also undocumented with no stability contract. Recorded as a rejected alternative in the decision record rather than left as an open idea.
- **Reconciled 2026-08-22 (v3.18.3 Phase 5): CLOSED as MOOT.** Every target file above lives under `extensions/github-usage-monitor/`, which **v3.18.2 withdrew and deleted**. The limitation is real and the analysis stands, but there is no longer any shipped code it constrains. Verified by absence: the directory does not exist and the extension roster is three usage monitors, not four. Re-open only if the monitor is ever rebuilt, and read the withdrawal decision record first - the reason it was withdrawn is that GitHub serves no included-usage figure at all.

### DF-1 - CLOSED as MOOT 2026-08-22: a repository whose visibility cannot be read is excluded, and the whole figure goes unknown

- **Target files**: `extensions/github-usage-monitor/src/providers/repositories.ts`, `src/providers/drawdown.ts`
- **What is deferred**: a token without the `repo` scope cannot see private repositories, which are exactly the ones that draw down. The existing behavior is to name the unresolved repositories and report the drawdown as unknown rather than returning a partial sum, and Phase 4 now renders that group in the panel with the explanation. What is **not** built is a prompt that offers to re-authorize with the missing scope at the moment the gap is detected.
- **Why deferred**: it is an authorization-flow change, not an accuracy change, and this plan's scope boundary is the drawdown model plus two documents. Adding a scope-escalation prompt on the refresh path is the kind of adjacent work the Boundaries rule declines.
- **Suggested next step**: surface it from the existing reconnect offer rather than adding a new prompt surface.
- **Reconciled 2026-08-22 (v3.18.3 Phase 5): CLOSED as MOOT.** Every target file above lives under `extensions/github-usage-monitor/`, which **v3.18.2 withdrew and deleted**. The limitation is real and the analysis stands, but there is no longer any shipped code it constrains. Verified by absence: the directory does not exist and the extension roster is three usage monitors, not four. Re-open only if the monitor is ever rebuilt, and read the withdrawal decision record first - the reason it was withdrawn is that GitHub serves no included-usage figure at all.

### MT-1 - RESOLVED 2026-08-22: v3.16 development history is archived

- **Target path**: `docs/archive/v3/v3.16/development/history` (39 files)
- **What is open**: `scripts/check_docs_retention.py` reports this directory as due for archival under the v3.18.0 retention policy (current minor v3.18, two-minor threshold). The check is advisory and always exits 0.
- **Why not done here**: it is unrelated to this plan, and Phase 6.1 forbids refactoring outside plan scope. A 39-file move belongs in its own change with its own reference-repair pass, which is the lesson the v3.18.0 archive pass recorded when a comparable move turned up 227 inbound references including six that CI executes directly.
- **Suggested next step**: run the archive pass through `/update refactor` or the `docs-layout-refactor` skill as its own change.
- **Resolved 2026-08-22 (confirmed in v3.18.3 Phase 5)**: the pass ran as its own change after the v3.18.2 release. `docs/archive/v3/v3.16/development/history/` now holds the 39 files, `scripts/check_docs_retention.py` reports *nothing due for archival*, and the five files left in `docs/v3/v3.16/development/` are the live CI inputs and shipped-code citations that the v3.18.0 DF-4 policy correction says must stay in the live tree. The v3.18.2 ledger records the same closure as its own MT-1; both now agree.

### QG-1 - CLOSED in implementation: the cross-extension parity test was verified to fail, not just to pass

- **Target file**: `extensions/github-usage-monitor/test/warning-parity.test.ts`
- **What could have shipped**: a source-text parity test is trivially fail-open. If the pattern locating the alert path stops matching after a rename, the test passes while asserting nothing - which is the same class of defect as the fail-open validator shipped and patched in v3.17.5.
- **Resolution**: the test asserts the alert-path call was **found** (`index > -1`) with a failure message naming what moved, and the defect was re-introduced and the suite re-run to confirm it fails on the intended assertion before being reverted. Both directions checked.

### BG-1 - RESOLVED in implementation: a 0.3.x cached snapshot would have rendered a confident 0%

- **Target files**: `extensions/github-usage-monitor/src/providers/enrich.ts`, `src/types.ts`
- **What would have happened**: breakdowns persisted before 0.4.0 carry no `pricePerUnit`. Had `undefined` been allowed to reach the weight calculation as `0`, every item would have derived a zero weight and the meter would have read a confident **0%** against a 2,000-minute allowance - the exact failure mode v3.16.4 already shipped once from a different cause.
- **Resolution**: `pricePerUnit` is documented as unknown-never-zero, `lineItemsOf` uses `?? null`, an item with a null or non-positive price joins the unresolved set rather than contributing, and `enrich.test.ts` pins the legacy-snapshot case: `drawdown: null`, `percentage: null`, `allowanceState: "unknown"`, self-healing on the next refresh.
- **Transferable lesson**: this is the third time in this extension that cached state outliving the version that wrote it has produced a wrong number rather than an error. Every field added after 0.1.0 must tolerate absence, and the test for it belongs in the same commit as the field.

---

## Reconciliation summary (2026-08-22, v3.18.1 Phase 6)

| Category | Closed | Open |
|---|---|---|
| Bugs (`BG-#`) | 1 (BG-1 resolved in implementation) | 0 |
| Quality gates (`QG-#`) | 1 (QG-1 verified in both directions) | 0 |
| Not-investigated (`NI-#`) | 0 | 2 (NI-1, NI-2 - both open **by design** with recorded decisions) |
| Deferred (`DF-#`) | 0 | 1 (DF-1, out of scope by the Boundaries rule) |
| Maintenance (`MT-#`) | 0 | 1 (MT-1, pre-existing and unrelated) |
| Ingested from v3.16 | 1 (NI-2 superseded) | 1 (NI-4 unchanged, invented SKU fixtures) |

**Release blockers: 0.** Both open `NI-#` items are open by design with their reasoning in a decision record and a falsifier in the ledger. `DF-1` is an authorization-flow change outside this plan's scope. `MT-1` is a pre-existing advisory that predates this plan and belongs in its own change.

---

## v3.18.2 - github-usage-monitor-withdrawal

**Status**: Implemented on `chore/remove-github-usage-monitor`. The extension is deleted and actively uninstalled from both hosts. This section CLOSES the v3.18.1 section above rather than extending it: every gap that section tracked concerned a reconstruction that no longer ships.

**Prior-version ingest**: **v3.18.1 NI-1** (price ratios versus legacy multipliers cannot be separated) is **CLOSED as moot** - the code that weighted anything is deleted, and the ledger that held the falsifier is deleted with it. **v3.16 NI-4** (self-hosted and larger-runner exclusion rules tested against invented SKU strings only) is **CLOSED as moot** for the same reason, and is additionally recorded below as having been *wrong*, not merely untested. **v3.16 NI-2** was already superseded in v3.18.1.

### DF-1 - CLOSED: the monitor reported 0% against an exhausted allowance

- **Reported**: 2026-08-22, against the v3.18.1 release, with the billing page screenshot showing `2,000 min used / 2,000 min included`.
- **Root cause**: repository visibility is point-in-time. `GET /repos/{owner}/{repo}` answers for *now*; billing line items are historical. A repository that was private while its minutes ran and public at read time has its whole month reclassified as free, yielding a drawdown of exactly zero that is marked *complete* and renders as a confident 0%. Reproduced against the pipeline: correct inputs yield 2,595 minutes / 129.8%, all-public inputs yield 0 / 0%, and unresolved inputs correctly yield *unavailable*.
- **Disposition**: closed by withdrawing the extension. Not fixable in place - see the decision record.

### WN-1 - CLOSED as shipped-wrong: self-hosted runners were excluded after GitHub began counting them

- **What was wrong**: `classifySku` excluded self-hosted runners from the drawdown, and `docs/policy/github-actions-minute-consumption.md` asserted in writing that they never draw down. GitHub's 2026 pricing page states that **from 2026-03-01 self-hosted runners consume the free quota "based on list price"**. Both statements were authored on 2026-08-22, five months after the behavior changed.
- **Why it was missed**: the claim was carried forward from earlier releases and re-asserted during a documentation phase without re-verification against live vendor documentation. The plan's do-not-invent rule covers inventing a claim; it did not catch *inheriting* a claim that had since expired.
- **Disposition**: closed as moot (both artifacts deleted). Recorded because the *class* of error is not moot: any surviving document that asserts third-party billing behavior carries the same expiry risk. The general lesson belongs to whatever next re-asserts a vendor behavior.

### MT-1 - CLOSED 2026-08-22 (post-release): v3.16 development history archived

- **Was**: 39 files under `docs/v3/v3.16/development/history`, two minors behind current, due under the retention policy and carried forward unchanged from v3.18.1 MT-1.
- **Closed by**: the post-v3.18.2 archive pass on `chore/v3.16-history-archive-and-plan-reslot`. Moved to `docs/archive/v3/v3.16/development/history/` as 39 git renames, matching the existing `docs/archive/v3/v3.15/development/history/` precedent.
- **Reference repair**: the inbound surface was **8 files / 21 references**, all documentation, with **no CI step, script, or hook** among them - unlike the v3.18.0 pass, which surfaced 227 references including six that CI executes directly. Repaired and verified to zero dangling references. Nine of the twenty-one were DEVLOG index rows, one per v3.16 patch release.
- **Scope note**: only `development/history` moved. The four `development/` contract documents (`evaluation-artifact-contract.md`, `github-entitlement-probe.md`, `install-selection-contract.md`, `selective-install-baseline.md`), plus `plans/`, `comparisons/`, and `known-gaps.md`, stay in the active tree - the retention policy ages out session histories, not contracts.
- **Also corrected**: `docs/archive/README.md` documented only whole-major archival, so the `docs/archive/v3/` subtree created by the v3.18.0 retention pass was undocumented. It now states both rules and carries a v3 index row.

### BG-2 - OPEN, environment-only: two installer tests fail non-deterministically in long local runs on OneDrive

- **Observed**: 2026-08-22, post-release, on this Windows working tree (an OneDrive-synced folder). Two separate long local runs each failed **one** test, and **a different one each time**: `tests/installer/test_org_cli.py::test_disconnect_requires_confirmation_and_yes_removes_state_and_cache` (1 failed / 3888 passed, full suite, 60 min) and `tests/installer/test_selection_parity.py::test_powershell_filtered_install_matches_bash` (1 failed / 417 passed, `tests/installer` only, 5 min).
- **Both pass in isolation** (5.1s and 7.1s respectively) and **both pass in CI**: `tests (ubuntu-latest)`, `installer-smoke` on ubuntu / macos / **windows**, and `install-smoke` were all green on the v3.18.2 PRs.
- **Assessment: environment, not product.** The failing assertion in the first is `org connect <git-uri>` returning exit 2 instead of 0 - a shell-out to `git` against a bare-repo fixture. This session independently hit `fatal: unable to write new index file` from `git checkout -b` in this same tree, which is the documented OneDrive file-locking hazard. A different test failing on each run is the signature of contention, not of a deterministic defect.
- **Explicitly NOT evidence of a regression in the v3.18.2 withdrawal.** `test_selection_parity` compares the PowerShell and bash installers, which the withdrawal edited on both sides, so it was the first candidate checked. It passes in isolation and `installer-smoke (windows-latest)` passed in CI, which is the job that exercises the retirement guard on the affected platform.
- **Disposition**: not a release blocker and not tracked as product flakiness. Recorded so the next person who sees a lone installer failure on a OneDrive tree does not spend the investigation again. **A local full-suite run on this tree is not a trustworthy signal**; CI on a clean checkout is. If either test ever fails **in CI**, treat it as a real defect and delete this entry.
- **Related process failure**: the first of these was reported to the user as a passing suite, because the run was piped (`pytest ... | tail`) and the pipeline's exit code is `tail`'s, not `pytest`'s. Never read `$?` through a pipe to judge a test run; capture the exit code directly or use `PIPESTATUS`.
- **New data point 2026-08-22 (v3.18.3 Phase 5), which does NOT close this item**: a full `tests/installer` run on this same OneDrive tree was clean (418 passed, 17 skipped, 0 failed), as was `tests/integrations` (661 passed, 1 skipped). A non-deterministic flake cannot be disproved by one green run, so the entry stays open on its stated terms. Recorded because the absence of a failure is still evidence about frequency, and because the next person needs to know a clean local run has happened rather than assuming the tests always fail here.

### QG-1 - Verification performed for this release

- `python scripts/check_version_sync.py` - all six surfaces at 3.18.2.
- `catalog/hooks/tests/test_installer_smoke.py` - 33 passed, including the new both-hosts retirement guard, which was verified to FAIL when the retirement entry is removed.
- `tests/workflows/` - 73 passed, 8 skipped, after dropping the deleted workflow from the sibling roster and the Dependabot monitor count from four to three.
- `bash -n scripts/installer.sh` and a PowerShell AST parse of `scripts/installer.ps1` - both clean after the block removal.

### Release blockers

**None.** The withdrawal is self-contained: no catalog artifact, platform contract, installer copy step, or registry file changes shape, and no surviving extension is touched.

`BG-2` is open but is not a blocker and was recorded after the release: it is an environment-only local-run artifact that passes in CI on every platform, including the Windows leg that exercises the affected installer guard.

---

## v3.18.3 - presentify-slide-navigation

**Status**: Phases 1-4 of 5 implemented on `feat/presentify-slide-navigation`. Every gate is green (full validate, trigger evals, the repo pytest suites, Phase 2's 42-check keyboard walkthrough, Phase 3's 24-check grammar and step-driver harness, and Phase 4's 28 new scorer tests). **No release blockers from these phases.**

### DF-1 - RESOLVED in Phase 2: the Step 6 slide-navigation pointer

- **Target files**: `catalog/skills/specialized-domains/document-to-interactive-html/SKILL.md` (Step 6), `catalog/skills/specialized-domains/document-to-interactive-html/references/slide-navigation.md` (Phase 2 creates it)
- **What is deferred**: sub-task 1.2 item 4 asks Step 6 to point at `references/slide-navigation.md`. Phase 1 shipped alone, so the pointer was not written, per the plan's own instruction not to ship a dangling reference.
- **Why it matters**: `make validate` runs an orphan-bundle audit over per-skill bundled resources. A pointer to a file that does not exist yet is the failure mode the deferral avoids, and the repo has already paid for one post-release dangling-reference sweep.
- **Closes when**: Phase 2 creates the reference file and adds the pointer in the same commit.
- **Resolution (2026-08-22)**: Phase 2 shipped `references/slide-navigation.md` (132 lines, all eight rule areas binary) and the Step 6 Navigation-mode bullet pointing at it in the same commit. The orphan-bundle audit passes (0 errors over 273 skills) and the prose mention in the command is now accurate.
- **Note**: `catalog/commands/presentify.md` does carry a forward-looking PROSE mention ("following its own slide-navigation reference"), which sub-task 1.1 item 4 explicitly asked for. It names no path, so no audit or link checker can trip on it. It becomes accurate when Phase 2 lands.

### WN-1 - Registry text must be derived, not retyped

- **Target files**: `data/skills.json`, and any future hand-edit of a registry entry
- **What happened**: `check_registry_entries.py --check --strict` compares `SKILL.md` frontmatter against the `data/skills.json` mirror character for character. Writing the same sentence twice by hand produced a one-word divergence ("scrolling" versus "scroll") that failed the gate.
- **Why it is recorded rather than dismissed**: the same hand-sync is required in Phase 3 and Phase 4 if either touches a description, and the failure is silent until the gate runs. The fix is to copy the frontmatter value programmatically rather than retype the sentence.
- **Disposition**: not a defect and not a blocker. A process note for the remaining phases of this plan.
- **CLOSED 2026-08-22 (Phase 5)**: the remaining phases are done and no further registry hand-edit was needed (Phases 2-4 changed no frontmatter). The guidance is retained here because the next description edit will face the same strict comparison, and `check_registry_entries.py --check --strict` is what will catch it.

### Phase 2 notes (2026-08-22)

- The contract was proven implementable before shipping: a hand-authored five-slide sample passed a 42-check headless walkthrough (keyboard map, fragment order and idempotence, deep links with clamp/fallback branches, browser-back history, focus and live-region behavior, reduced-motion cuts, and the no-JS stacked fallback).
- One capture-protocol fact for Phase 4: a screenshot taken mid-transition shows two slides painted together while the state is correct. The Phase 4 capture protocol must wait for transition settle (or force reduced motion) before grading, or every slide-mode run will file a phantom double-slide defect.

### Phase 3 notes (2026-08-22)

- **BG-1 - RESOLVED in Phase 3, found and fixed in the same session**: the new engine step driver's initial `goTo` at mount never painted layer 0 (`_shown.index` starts at 0 so `crossing` was false while `active` was still -1). Caught by the render harness, not by `node --check`, which stayed green throughout - the case for the plan's render-verification step. Fixed by also gating the layer toggle on `this.active !== index`, with a comment naming the mount case.
- Two more settle-then-assert facts for Phase 4's capture protocol, joining the Phase 2 note: a fixed sleep racing a timed animation reads mid-count values (poll for the settled state instead), and CSSOM re-serializes transform values (`scale(1.0000)` reads back as `scale(1)`), so assertions against style strings must use the serialized form.

### Phase 4 notes (2026-08-22)

- **The three settle-then-capture facts recorded in Phases 2-3 are now DISCHARGED**: the rubric's degradation contract and SKILL.md Step 9 both carry the settle-before-capture rule for slide transitions and timed builds, so the phantom double-slide and mid-count defects cannot be filed on a slide-mode run.
- **The `data-nav` gate is deliberately not the only source of truth.** Six of the seven scorer checks are gated on the attribute, which makes the attribute a single point of failure: lose it and every check skips and the page scores a confident green (fail-OPEN, worse than no check). `slide-record` runs ungated and fails when the design record and the markup disagree, so the gate can only be wrong in the direction that gets caught. Any future slide-mode check must either be gated AND covered by this agreement check, or be ungated itself.
- **An existing guard test fired correctly and was updated, not loosened.** `test_no_stale_criteria_count_survives` hardcodes the rubric's criteria count so no surface can claim a stale one; growing the rubric to twelve broke it by design. The denylist now loops over eight / nine / ten / eleven and additionally asserts criterion 12 by name. Loosening it to a regex was rejected: it would pass forever and catch nothing.

### Release blockers

**None from Phases 1-4.**

---

## Reconciliation summary (2026-08-22, v3.18.3 Phase 5)

Every open item across the whole v3.18 ledger was walked, not only this plan's own section.

| Item | Was | Now | Basis |
|---|---|---|---|
| v3.18.1 NI-1 | OPEN by design | **CLOSED as moot** | Target extension withdrawn and deleted in v3.18.2; verified by absence |
| v3.18.1 NI-2 | OPEN by design | **CLOSED as moot** | Same |
| v3.18.1 DF-1 | DEFERRED | **CLOSED as moot** | Same |
| v3.18.1 MT-1 | OPEN, out of scope | **RESOLVED** | Archive pass executed post-v3.18.2; retention checker reports nothing due |
| v3.18.2 BG-2 | OPEN, environment-only | **OPEN** (unchanged) | A clean local run cannot disprove a non-deterministic flake; new data point recorded |
| v3.18.3 DF-1 | DEFERRED to Phase 2 | **RESOLVED** | `references/slide-navigation.md` and the Step 6 pointer shipped together in Phase 2 |
| v3.18.3 WN-1 | Process note | **CLOSED** | No further registry hand-edit was needed; the guidance is retained for the next one |

**The material finding is the moot cluster.** Three items sat marked OPEN or DEFERRED against `extensions/github-usage-monitor/`, an extension the very next patch release deleted. Nothing was wrong with the analysis; the ledger simply had no mechanism to notice that a later release removed the code an earlier release's gaps pointed at. Worth a habit rather than a tool: when a release withdraws a component, sweep the ledger for items whose **Target files** live under it, in the same change.

**Prior-version ingest.** `docs/v3/v3.17/known-gaps.md` was checked and carries ten open or deferred items. None is in this plan's scope - they concern platform invocation-policy levers, coverage instrumentation, per-model prompting-profile freshness, Gemini matcher semantics, and output-redirection verification. They stay in the v3.17 ledger with their existing owners; a presentify navigation feature is not the change that should close them.

**Stale carried-items list corrected.** `docs/todos.md` carried seven items forward from the v3.18.0 reconciliation, six of them unchecked. Cross-checking each against this ledger showed **five were already resolved** and only one is genuinely open (whether the MCP decision tree should leave AGENTS.md). The dashboard was overstating open work by 5x. Corrected in the same pass, each with the ledger item that closed it.

### Release blockers

**None.** The one item still open across all of v3.18 is BG-2, which is environment-only, passes in CI on every platform, and passed locally in this session too.
 The phase changes only documentation surfaces the installers already copy recursively, adds no catalog artifact, and leaves `data/marketplace.json` counts and the 273-skill total unchanged.
