# Known Gaps - v3.18

**Project**: Nexus-Hub
**Status**: v3.18.0 (`docs-lifecycle-retention`) released. v3.18.1 (`github-usage-monitor-accuracy`) Phases 1-6 implemented on `feat/v3.18.1-github-usage-monitor-accuracy`. **Zero release blockers across both.**
**Last updated**: 2026-08-22 (v3.18.1 section appended: BG-1 and QG-1 closed in implementation; NI-1 / NI-2 open by design; DF-1 and MT-1 out of scope)

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

### NI-1 - OPEN by design: price ratios and the legacy multipliers cannot be separated by any saturated month

- **Target files**: `extensions/github-usage-monitor/src/providers/drawdown.ts`, `docs/v3/v3.18/development/github-drawdown-ledger.md`
- **What is unresolved**: the shipped model weights by current price ratios (Windows 1.67x, macOS 10.33x). The legacy published multipliers (2x, 10x) fit the same data, differing by about 0.3% of the weighted total. Every month observed on the measured account is either **saturated** (so it reports only "at least the allowance" and cannot choose between two models that both predict above the cap) or **Linux-dominated** (so every candidate yields the same answer within tolerance). The data does not distinguish them.
- **Decision**: ship the derived ratios, because the mechanism tracks GitHub's price changes and a hardcoded snapshot demonstrably does not - this number was revised three times for exactly that reason. This is a bet on the mechanism's stability, not a claim that the evidence separates the candidates, and the decision record says so in its Consequences.
- **Disposition**: `docs/v3/v3.18/development/github-drawdown-ledger.md` states the falsifier - an unsaturated month whose non-Linux share exceeds 15% and whose displayed value matches unweighted raw minutes - and `src/providers/reconciliation.ts` refuses to classify a saturated or Linux-dominated month as support. A fourth revision has to produce a discriminating month rather than an argument.

### NI-2 - OPEN by design: the included allowance is still plan-table-derived

- **Target file**: `extensions/github-usage-monitor/src/providers/planEntitlements.ts`
- **What is unresolved**: no billing endpoint returns the included allowance. The legacy product-specific endpoints that served `included_minutes` closed down in September 2025 and return 404/410; `/settings/billing/usage` returns consumption only. The denominator therefore comes from a published plan table (2,000 minutes, 0.5 GB on Free) that nothing on the account confirms.
- **Decision**: keep the plan table with the existing manual override as the correction path, and label the denominator's provenance in the panel, which Phase 4 now does as a separate sentence from the numerator's.
- **Why not scraped**: `github.com/settings/billing` requires a browser session cookie, and the extension holds an OAuth Bearer token, so the page is unreachable with the credential it has. It is also undocumented with no stability contract. Recorded as a rejected alternative in the decision record rather than left as an open idea.

### DF-1 - DEFERRED: a repository whose visibility cannot be read is excluded, and the whole figure goes unknown

- **Target files**: `extensions/github-usage-monitor/src/providers/repositories.ts`, `src/providers/drawdown.ts`
- **What is deferred**: a token without the `repo` scope cannot see private repositories, which are exactly the ones that draw down. The existing behavior is to name the unresolved repositories and report the drawdown as unknown rather than returning a partial sum, and Phase 4 now renders that group in the panel with the explanation. What is **not** built is a prompt that offers to re-authorize with the missing scope at the moment the gap is detected.
- **Why deferred**: it is an authorization-flow change, not an accuracy change, and this plan's scope boundary is the drawdown model plus two documents. Adding a scope-escalation prompt on the refresh path is the kind of adjacent work the Boundaries rule declines.
- **Suggested next step**: surface it from the existing reconnect offer rather than adding a new prompt surface.

### MT-1 - OPEN, pre-existing and out of scope: v3.16 development history is due for archival

- **Target path**: `docs/v3/v3.16/development/history` (39 files)
- **What is open**: `scripts/check_docs_retention.py` reports this directory as due for archival under the v3.18.0 retention policy (current minor v3.18, two-minor threshold). The check is advisory and always exits 0.
- **Why not done here**: it is unrelated to this plan, and Phase 6.1 forbids refactoring outside plan scope. A 39-file move belongs in its own change with its own reference-repair pass, which is the lesson the v3.18.0 archive pass recorded when a comparable move turned up 227 inbound references including six that CI executes directly.
- **Suggested next step**: run the archive pass through `/update refactor` or the `docs-layout-refactor` skill as its own change.

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
