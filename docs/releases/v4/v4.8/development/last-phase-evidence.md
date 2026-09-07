# Last-Phase Evidence - v4.8.0

**Plan**: [v4.8.0-adoption-agentic-loops-and-coding-agent-practice](../plans/v4.8.0-adoption-agentic-loops-and-coding-agent-practice.md), Phase 5 of 5
**Date**: 2026-09-07
**Branch**: `feat/v4.8.0-agentic-loops`, cut from `develop` at `a243c178`
**Integration base**: `develop`
**Driver**: `/implement ... full`
**Model routing**: plan asked frontier / max; session ran `claude-opus-5` (strong). Surfaced at the boundary with the exact keystrokes and recorded as `WN-E`; not silently absorbed.

Every duty below is fail-closed. A duty is omitted only by a recorded `QG` or `DF` known gap.

---

## Architecture refactor

Run via [[project-refactor]] and [[docs-layout-refactor]] detectors. Nothing was moved, so no reference repair was required.

**Empty directories** under tracked trees:

```
docs/decisions/proposed/process
docs/decisions/proposed/tooling
extensions/nexus-code-search/benchmarks/.work/corpus/.nexus/code-index
extensions/nexus-code-search/benchmarks/.work/run-10k3cjf4/corpus/tests
extensions/nexus-code-search/benchmarks/.work/run-nleyqgk5/corpus/tests
```

Disposition: none is a finding. `git ls-files docs/decisions/proposed/` returns only `docs/decisions/proposed/.gitkeep`, so the two `proposed/` subdirectories exist on disk only and are untracked; the `.work/` paths are benchmark scratch under an ignored tree.

**Repository root**, tracked status of every non-obvious entry:

```
Microsoft            ignored
pytest-out.log       ignored
image.png            UNTRACKED-NOT-IGNORED
checksums.txt        TRACKED
MANIFEST.sha256      TRACKED
reports              ignored
```

One advisory, not acted on: `image.png` is untracked AND unignored, so it appears in every `git status` and could be committed by a broad `git add`. It predates this plan (present at session start) and is the maintainer's file, so it was left untouched and deliberately excluded from every commit in this plan. Suggested next step for the maintainer: delete it or add it to `.gitignore`.

**Docs retention** (advisory, never fails):

```
docs retention: nothing due for archival (current v4.7, threshold 2 minors)
```

Finding: clean. Nothing proposed, nothing applied.

---

## Known-gaps reconciliation

Reconciled via [[known-gaps-tracker]]. Glob over both canonical and legacy layouts found **36 reachable ledgers** (29 under `docs/releases/v*/v*/`, 7 under `docs/archives/v*/v*/`). None was unreachable.

**This version.** `docs/releases/v4/v4.8/known-gaps.md` opened this plan with 3 pre-existing items (`WN-A`, `WN-B` resolved, `WN-C`) and now carries the following, added by this plan:

| id | Class | Source phase | Summary |
|---|---|---|---|
| `WN-D` | Warning | Phase 1 | `make` absent on this host; every `validate` step run directly instead (33) |
| `WN-E` | Warning | Phase 4 | Ran strong where the plan asked frontier; surfaced with keystrokes, not absorbed |
| `WN-F` | Warning | Phase 4 | Nothing detects a framework tag whose supporting sentence is later deleted |
| `WN-G` | Warning | Phase 5 | Coverage builder mis-parses a trailing comment on any framework field (AF-6) |
| `WN-H` | Warning | Phase 5 | Coverage builder silently ignores a block-sequence framework field (AF-7) |
| `WN-I` | Warning | Phase 5 | `test_org_cli.py` disconnect test is flaky; OneDrive-redirection hypothesis recorded |
| `DF-1` | Deferred | Phase 5 | Goal clause 3's REVIEW half never wired the taxonomy into a review skill |

**The eight carried items the plan named explicitly**, each with whether this plan touched it:

| id | Where it lives | Touched by this plan? |
|---|---|---|
| `HT-4` | v4.4 - no human comprehension cohort for the rebuilt guide illustrations | **Not repaired, but advanced.** This plan touches no guide. Its Phase 5 human-testing duty asks for one reader OUTSIDE the operator loop, which is the cohort `HT-4` is missing; see `## Human/manual testing suggestions`. Stays open, owned by v4.4. |
| `GA-1` | v4.4 - a rule's selector is never proven to match anything (dead-selector sweep of the guide stylesheet) | **No.** This plan changes no CSS and no guide asset. Carried unchanged. |
| `CQ-1` | v4.4 - CodeQL `js/xss-through-dom` on the guide's media toggle | **No.** The flagged toggle was already removed in a v4.4 phase; the alert awaits re-evaluation on the next scan. Carried unchanged. |
| `HT-2` | v4.4 - installer postcondition on the real current host; a sandbox attempt mutated live platform config | **No, and deliberately not attempted.** See the `NOT COVERED` entry under `## Tier 3 deep pass`: running the installer on this host is the exact action `HT-2` records as harmful. Carried unchanged. |
| `QG-1` | v4.1 - an additional local full profile did not complete within the release-prep window | **No.** Already recorded as resolved during the v4.4.0 Phase 7 reconciliation. No action. |
| `RV-3` | v4.4 - the Models scene names `xAI Grok` rather than `Cursor Grok` | **No.** Guide content. Carried unchanged. |
| `RV-4` | v4.4 - a guide heading reads quieter than the tags below it | **No.** Guide typography. Carried unchanged. |
| `RV-5` | v4.4 - the Home label renders slightly larger than its title | **No.** Guide typography. Carried unchanged. |

No item was closed by fiat, and none of the eight was silently dropped.

---

## Living docs architecture

Self-gated check. This repository is the Nexus-Hub **catalog**, not an application with a user-facing product walkthrough, so an atlas walkthrough and per-component companion HTML are deliberately NOT invented here; `docs/handbooks/README.md` states that in the tree itself.

```
docs/handbooks/  EXISTS (3 files: README.md, html/.gitkeep, markdown/.gitkeep)
docs/decisions/  EXISTS (40 files)
docs/incidents/  EXISTS (5 files)
docs/README.md   (21 lines)
docs/DEVLOG.md   (120 lines)
docs/todos.md    (147 lines)
docs/testing     correctly absent
docs/validation  correctly absent
```

- `docs/handbooks/markdown/` holds no authored pages, so the regenerate-and-fail-on-stale check is a documented no-op rather than a skipped step. `html/` correctly holds no generated output, because markdown is the source of truth and there is no source.
- The self-gate held: `docs/testing/` and `docs/validation/` were NOT invented.
- `docs/decisions/` grew by one record this plan (38 records validated OK, up from 37).
- `docs/DEVLOG.md` is an index, one line per RELEASE. v4.8.0 is unreleased, so no row is added here; `/update release` owns that row. This is why steps 8.7 across all four phases correctly recorded a no-op rather than writing narrative into a living surface.

`python scripts/check_docs_conventions.py` and `python scripts/check_doc_colocation.py` both exit 0.

---

## Git-tree hygiene

`python scripts/check_release_preconditions.py --branches --repo-settings` (report only; nothing deleted):

```
Branch hygiene (merged into origin/develop)
  OK: no merged remote branches to clean up
  Reporting only -- nothing was deleted.
Repository settings
  OK: delete_branch_on_merge is enabled
  NOTE: the repository description disagrees with README.md:
    - commands: description says 18, README.md declares 19
    - hooks: description says 34, README.md declares 35
    - skills: description says 329, README.md declares 336
        The description is not a version-carrying surface, so
        check_version_sync.py cannot see it and it drifts silently
        across releases. Update it by hand.
```

Disposition: the description drift is pre-existing, is not a version-carrying surface, and is a GitHub repository setting rather than a file. Per [[cicd-architect]] Step 10, repository settings are documented and never mutated automatically. Left for the maintainer to update by hand at release time; no gap recorded because the tool already reports it every run.

---

## CI/CD coverage

Terminal reconciliation via [[cicd-architect]] Step 9, six steps in order. **This plan changed no pipeline file across any of its five phases**, which is the outcome the lifecycle requires; every phase's step 8.3 recorded its CI impact in prose instead.

**1. DETECT.** GitHub Actions. `.github/workflows/` present with 13 workflows; no `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/config.yml`, `azure-pipelines.yml`, `.buildkite/pipeline.yml`, `.woodpecker.yml`, or `.drone.yml`.

**2. COMPARE**, field by field, with observable evidence per field:

| Field | Result | Observable evidence |
|---|---|---|
| Five repository-native profiles | PASS | `scripts/ci/run.py --profile {fast,full,platform,report,release}` all five accepted; `--profile fast --list` enumerates the step groups |
| No profile reimplements a validator | PASS | The `fast` listing names existing repository commands (`validate_unicode_safety`, `check_docs_conventions`, `check_version_sync`, ...), not inline reimplementations |
| Event separation | PASS | `ci.yml` fires on `pull_request: [main, develop]`, `merge_group`, `workflow_dispatch` only. Its own header comment records that the `push` trigger was deliberately removed in v4.0.0 because a push to `develop` IS the merge commit of the PR that just ran |
| No workflow double-fires PR-into-develop and push-to-develop | PASS | A crude grep flagged `post-merge.yml` as a candidate; inspection shows its `on:` block is `push: branches: [main, develop]` only, and the `pull_request` string never appears in the file. Recorded because the grep was the artifact, not the finding |
| Expensive host legs run pre-merge | PASS | Same `ci.yml` header records the Windows and macOS legs being moved from `push` to the pull request in v4.0.0, with the reason (minutes spent after merge cannot prevent a bad merge) |
| Triggers UNFILTERED at workflow level | PASS | `ci.yml` has no `paths:` filter; the header cites the v3.17.5 incident (seven administrator bypasses in one day) and points at the `changes` job that applies the identical scoping per job |
| Exactly one aggregate required context | PASS | `docs/policy/required-checks.json` lists `validate`, `shellcheck`, `ci-required`, `colocation`, `verify` for both protected branches; no `job (leg)` context appears |
| Required checks unconditionally produced | PASS | `python scripts/check_required_check_coverage.py` exits 0 |
| Permissions least-privilege | PASS | `ci.yml` declares read-only contents with an inline justification; `python scripts/validate_workflow_security.py` exits 0 |
| Immutable action references | PASS | Every `uses:` across all 13 workflows matches a 40-character SHA; a grep for non-SHA third-party references returned nothing |
| Caching, concurrency, path scoping | PASS | Covered by `validate_workflow_security.py` and `tests/workflows/test_workflow_policy_repo_wide.py`; both green |
| Artifact retention explicit | PASS | `retention-days` present where artifacts are uploaded (`cursor-usage-monitor.yml` 7, `supply-chain-watch.yml` 30) |
| Structured reports | PASS | `scripts/ci/reporting.py` exists and is the profiles' reporting surface |
| Deployment boundaries | PASS | Release work is isolated in `release.yml`; post-merge work in `post-merge.yml`; neither runs the complete suite |
| Failure recovery | PASS | `tests/workflows` suite green (see below) |
| Cross-installer parity (HARD gate; this repo ships more than one installer) | PASS | `python scripts/check_installer_parity.py` exits 0; `tests/installer` suite green |
| Platform read-contract freshness | PASS | `python scripts/verify_platform_contracts.py` and `python scripts/check_platform_contract_freshness.py` both exit 0 |

Suite evidence for the pipeline surface: `python -m pytest tests/workflows tests/installer tests/ci -q` produced `671 passed, 60 skipped` in 282.35s, exit 0. An earlier identical run reported `1 failed, 670 passed`; that single failure was not reproducible and is recorded as `WN-I`.

**3. PROPOSE.** No difference found, so nothing was proposed.

**4. APPROVE.** Not applicable: no change to approve. Silence was not treated as approval for anything.

**5. APPLY.** Nothing applied. No pipeline file was modified by this plan.

**6. RECORD.** One environment-only difference recorded, and it is not a pipeline difference: the repository-description drift under `## Git-tree hygiene`, which lives in a GitHub setting rather than a file.

**Conclusion: PASS**, on observable per-field evidence rather than on a green run. The specific thing this plan's changes could have broken is the `validate` job, because Phase 4 changed two of that job's own scripts (`validate_skills.py`, `build_framework_coverage.py`); both are in `DEV_ONLY_SCRIPTS`, both still run in the same job, and `check_required_check_coverage.py` still reports every required context as unconditionally produced.

**What the pipeline cannot enforce** ([[cicd-architect]] Step 10), documented and not mutated: protected `main` and `develop` rejecting direct pushes, pull request required before merge with `ci-required` required, administrator-bypass policy, merge-queue configuration, fork workflow restrictions, artifact retention period, and billing review. The statement "a `push`-filtered workflow means a merge happened" is true for this repository ONLY because those external protections exist.

---

## Tier 3 deep pass

Run via [[functional-verification]] and its `references/deep-pass.md`, followed in order.

**Revision under review**: `feat/v4.8.0-agentic-loops` at the Phase 5 working tree. **Integration base**: `develop` at `a243c178`.

### Blast-radius verdict

- **Verdict**: `run`
- **Positive triggers**: distributed catalog content changed (`catalog/skills/**`, `catalog/commands/research.md`); a validation boundary changed (`scripts/validate_skills.py` gained a new validated field); a generated document changed (`docs/framework-coverage.md`); a skill and command contract changed (five optional schema fields, a new frontmatter field, a new command section).
- **Diff paths**: 43 files in the Phase 4 commit alone; 54 markdown artifacts across the plan's four commits.
- **Ambiguity check**: none needed; four of the five triggers apply directly.

### Feature inventory

16 features inventoried, 16 exercised, 0 uncovered.

| # | Feature | Source | Boundary | Observed result | Status |
|---|---|---|---|---|---|
| 1 | Loop readiness scorecard | T001 | Agent applies it to a library loop | Total 12; every justification traced to a real field after one fix | exercised |
| 2 | Run-contract schema fields | T003 | Loop definition author | 5 fields documented Optional; all 6 library loops still valid, none changed | exercised |
| 3 | `trace_log.score` + aggregation rule | T003 | Trace consumer | Field and rule both present and asserted | exercised |
| 4 | Failure-mode ownership table | T004 | Multi-skill review | 10 rows, each owner resolved against the real catalog listing | exercised |
| 5 | Five owner-skill rule sentences | Phase 1 | Owner skill reader | All five present, pinned by phrase | exercised |
| 6 | Step 0 autonomy ladder | T007 | Operator choosing a structure | Competitive-landscape example landed on single goal loop; graph unreachable until the measured-limitation item is answered | exercised |
| 7 | Graph readiness checklist | T008 | Escalation gate | 6 signals, 8 items, item 1 requires measured-not-predicted | exercised |
| 8 | Verifier taxonomy | T011 | Evaluation author | 4 classes each with a weakness, 7 deliverables, 3 rules, all cross-links resolve | exercised |
| 9 | Completion evidence, `/research` | T013 | Research run closing summary | 4 of 5 metrics computed from a real 240-line deliverable; local-corpus zero fixed | exercised |
| 10 | Completion evidence, compile | T014 | Compile run closing summary | Same block asserted on both surfaces through one parametrized fixture | exercised |
| 11 | Capability-to-regression graduation | T015 | Eval-set maintainer | Rule present with default N=3 and the never-edited clause; holdout note reciprocal | exercised |
| 12 | `obviated_by_model` column + fixture | T016 | Stocktake consumer | Fixture yields exactly 1 populated / 1 review / 1 empty; live catalog yields 0 | exercised |
| 13 | `owasp_agentic` validator | T019 | `validate_skills.py --bundles-only` CLI | 9 input shapes plus a scratch skill: `ASI99` fails with exit 1, naming file and field | exercised |
| 14 | OWASP column in the matrix | T020, T026 | Compliance reader | All ten identifiers present; `prompt-injection-defense` ASI01, `agent-memory` ASI06, `agent-execution-isolation` ASI02 and ASI05, as the plan expected | exercised |
| 15 | Navigator-layer isolation | T020 | ATT&CK Navigator | Regeneration produced a **byte-identical** layer; 0 `ASI` strings; 64 techniques, none prefixed `ASI` | exercised |
| 16 | Cross-bundle relative links (cross-phase surface, owned by no single phase) | Phases 1-4 | Agent following a link | 81 relative links across 54 markdown artifacts, 0 broken | exercised |

Feature 16 is the genuinely Tier-3-only row: Phase 2 links into Phase 1's bundle and Phase 3 links into Phase 1's schema, so no single phase could have exercised the whole cross-bundle graph.

### Rendered-surface delegates

**NOT APPLICABLE**, with the reason. Every artifact this plan produced is Markdown, JSON, or Python. No browser UI, local HTML, generated HTML, PDF, DOCX, or PPTX was created or changed, so:

- [[browser-testing-with-devtools]]: NOT APPLICABLE - no browser surface in the diff.
- `scripts/detect_visual_defects.py`: NOT APPLICABLE - it accepts local HTML and this plan produced none.
- [[accessibility-engineering]], [[hallmark-design]], [[interface-review]]: NOT APPLICABLE - no visual surface.

This is a reasoned not-applicable tied to the diff, not a skipped step.

### Adversarial pass

Run via [[adversarial-verifier]]. Attack surface: the one new parser this plan added, reading frontmatter from `SKILL.md` files, which are a supply-chain artifact (the reason `skill-security-scan` exists). Four findings, three of them real.

| id | Severity | Finding | Disposition |
|---|---|---|---|
| AF-1 | P1 | A NESTED (indented) `owasp_agentic` key was skipped by the validator but READ by the coverage builder, which matches with `line.strip()`. `ASI99` reached `docs/framework-coverage.md` while the validator reported PASS | **FIXED** in cycle 1 |
| AF-1b | P1 | The second route: a nested BARE SCALAR escaped both the shape check (which skips indented lines) and membership | **FIXED** in cycle 1 |
| AF-2 | P1 | With a DUPLICATE key, the validator read the first and the builder rendered the last, so `[ASI01]` then `[ASI99]` passed and published `ASI99` | **FIXED** in cycle 1 |
| AF-6 | P2 | A trailing comment breaks the BUILDER's parser: `owasp_agentic: [ASI01] # fine` yields the literal identifier `'[ASI01] # fine'`. Pre-existing, affects all seven framework fields | Recorded as `WN-G` |
| AF-7 | P2 | The builder silently IGNORES a block-sequence framework field, so a tag can validate cleanly and never appear in the matrix. Pre-existing, affects all seven fields | Recorded as `WN-H` |

AF-1, AF-1b, and AF-2 mattered because they defeated the exact guarantee this feature's decision record claims as its justification: that a shape-only check would accept `ASI99` and a plausible identifier in a compliance-facing matrix reads as verified coverage. Membership validation that can be bypassed by indenting a line is not membership validation.

**Fix**: `_owasp_agentic_values` now validates the UNION of every occurrence of the key, indented ones included, and validates a nested bare scalar. This is deliberately broader than YAML's own semantics, because the builder is broader too, and the validator must be the wider of the two to fail closed. Five regression tests pin all four routes plus a guard that a block sequence still stops at the next key at the same indent.

**Post-fix re-exercise**: 10 cases (4 attack, 6 regression) reported 0 remaining bypasses; live catalog `RESULT: PASS (0 errors)`; `build_framework_coverage.py --check` in sync; `test_owasp_agentic_mapping.py` 63 passed; `test_framework_field_shape.py` 20 passed.

AF-6 and AF-7 were NOT fixed here on purpose: both are one-line changes to a parser shared by all seven framework fields, and changing shared parsing behavior should land with a test matrix over all seven rather than riding along in a mapping phase. Both are recorded with that reasoning and a specific next step. No shipped skill triggers either.

### Implementation convergence

Run via [[implementation-convergence]]. **Result: `converged`.** 0 missing, 0 partial, 0 contradicting-with-work-remaining, 1 accepted `unrequested`. Per that skill's no-op guarantee, NO `## Phase N: Convergence` section was appended to the plan; a converged tree leaves the ledger byte-for-byte unchanged.

| id | Gap type | Severity | Source-ref | Evidence | Remaining work |
|---|---|---|---|---|---|
| CV-1 | contradicts | LOW | T021 | The plan named `test_validate_skills_framework_fields.py`; the ten cases landed in the existing `test_framework_field_shape.py`, which already owns the validator subprocess harness | None. Intent satisfied; the path divergence is recorded in the Phase 4 Plan delta with the `AGENTS.md` test-retention reason |
| CV-2 | unrequested | MEDIUM | no task line | The AF-1/AF-2 validator hardening and its five regression tests | Surfaced for review, not hidden. Produced by the mandated Tier 3 deep pass and closes a confirmed bypass of the release's stated guarantee |

Task-line completion was marked separately from this pass (36 of 37 task lines, 43 exit-checklist lines); the convergence pass itself wrote nothing.

### Goal-vs-plan sufficiency audit

| Question | Answer | Evidence | Change needed now | Owner |
|---|---|---|---|---|
| 1. What did implementing this teach that the plan did not know? | That the membership guarantee was bypassable by indenting one line, because the validator's parser was narrower than the coverage builder's. The plan reasoned carefully about WHICH values to accept and not at all about which LINES each tool reads | AF-1/AF-1b/AF-2 under the adversarial pass | Fixed in cycle 1 | this phase |
| 2. What did the plan assume that turned out false? | Two official OWASP titles (ASI03, ASI06 use ampersands), that its single source URL enumerates the ten entries (it does not), and that all ten named owners already stated the rule assigned to them (five did not) | Phase 4 and Phase 1 Plan deltas | All three corrected inside their phases | phases 1 and 4 |
| 3. What would a reader of the Goal expect that no phase delivered? | Goal clause 3 says "every REVIEW and research deliverable names the verifier class that grades it". The research half landed on both surfaces; the review half did not. No task line wired the taxonomy into any review skill | Goal line 10 of the plan; T011-T017 task lines | Not fixed here: choosing which review surfaces carry it is a design decision outside every phase's declared scope | `DF-1` |
| 4. What did the maintainer ask for that no task line captured? | One thing, and it was answered before implementation began: the plan's Phase 5 opens an integration pull request against `develop` while the session started ON `develop`, which is impossible. Raised as a blocking pre-flight question and resolved by the maintainer choosing to branch (`feat/v4.8.0-agentic-loops`) | The Phase 0 pre-flight exchange | None; resolved before any code changed | resolved |

`fix_rerun_cycles_used`: **1** of 3.

### Deep-pass NOT COVERED

- **NOT COVERED: real installer execution on this host** - scope: proving that the new bundled reference files and the changed command file actually land in a user's platform directories. Owner: the maintainer. Reason: this repository's own `HT-2` gap records that a prior attempt to sandbox an installer run by redirecting `HOME` did NOT isolate it and mutated live platform config, and this session's operating memory carries the same instruction. The delivery MECHANISM is evidenced instead (`check_installer_parity.py` exits 0; every new file sits under `catalog/skills/**` or `catalog/commands/`, which both installers copy recursively per the `AGENTS.md` distribution table, so no installer edit is required). Next step: the maintainer runs a real install on a disposable machine, which also advances `HT-2`.

### Gate disposition

Supplied per [[quality-gate-definitions]]: **PASS with recorded gaps.** No unresolved deep-pass finding is without a disposition. Three P1 findings fixed and re-exercised; two P2 findings recorded with owners and next steps; one Goal miss recorded as `DF-1`; one uncovered scope recorded with its owner and its reason.

Record handed to [[verification-before-completion]] for evidence freshness: every command quoted here was run in this session against the revision under review.

---

## Goal-vs-codebase review

Independent review of the resulting tree against the plan header Goal, read as if this agent had not implemented the phases.

**Goal restated** (four clauses, verbatim from the plan): a loop is admitted only after a scored readiness test and declared through a run contract naming scope, permissions, budgets, persisted state, and audit evidence; the orchestration skill states which autonomy level a task earns and gates every graph on a written readiness checklist; every review and research deliverable names the verifier class that grades it, with `/research` emitting machine-checkable completion evidence instead of the producer's confidence; the agent-security skills are mapped to the OWASP Top 10 for Agentic Applications through a validated seventh framework field rendered into the coverage matrix.

| Clause | Artifacts that satisfy it | Verdict |
|---|---|---|
| 1. Scored admission + run contract | `loop-engineering/references/loop-readiness-scorecard.md` cited from "When to Use This Skill" (before assembly) and Step 2 (recorded into instance state); `loop-schema.md` gains `scope`, `permissions`, `budgets`, `state_contract`, `audit_evidence` | **Satisfied**, with one honest qualification below |
| 2. Autonomy level + graph gate | `agent-orchestration-primitives` Step 0 (six rungs, three selection inputs, minimum-sufficient-autonomy rule) and `references/graph-readiness-checklist.md` cited from the Step 4 gate | **Satisfied** |
| 3. Verifier class named + research completion evidence | `ai-output-evaluation/references/verifier-taxonomy.md` cited from Step 1; "Completion evidence" sections in `catalog/commands/research.md` and `deep-research-compilation/SKILL.md` | **PARTIAL** |
| 4. Validated seventh framework field, rendered | `owasp_agentic` in `validate_skills.py` (shape + closed-set membership) and `build_framework_coverage.py`; the OWASP Agentic column in `docs/framework-coverage.md` with all ten identifiers; 15 skills tagged; the decision record; the mapping skill documenting seven frameworks | **Satisfied** |

**The two gaps, stated rather than glossed:**

1. **Clause 3 is partial, in two distinct ways.** The REVIEW half is not delivered at all: the taxonomy exists but no review skill cites it, so a review deliverable still does not name its verifier class. Recorded as `DF-1` with a specific one-line next step. Separately, `/research` emits the completion evidence but the block is ADVISORY in this release, so it reports rather than replacing the producer's confidence; the Goal's "instead of" is therefore delivered as "alongside". That was the plan's own deliberate decision, taken with a stated reason (no measured baseline exists to set a threshold from) and asserted by test, so it is a documented scope decision rather than a miss.
2. **Clause 1's "only after" is doctrine, not enforcement.** Nothing mechanically prevents assembling a loop without scoring it, because Nexus-Hub ships no loop runtime; the standing decision that the driver is a host command covers this. The scorecard is gated at the two points where a reader makes the decision, which is the strongest form available to a catalog. Not recorded as a gap, because implementing enforcement would require the runtime this project has explicitly declined; stated here so the clause is not read as stronger than it is.

**Completing every prior-phase checkbox was not treated as evidence.** Each verdict above was reached by locating the artifact and reading it, and clause 3's shortfall was found this way rather than from any phase's own report.

---

## Human/manual testing suggestions

Last phase only. These cover what automated tests cannot, and the first advances the carried `HT-4` gap.

1. **One reader OUTSIDE the operator loop opens the v4.4.6 loop and graph lessons cold** (once they ship) and says, without prompting, whether they point at the readiness scorecard and the graph checklist this plan added. This is the outside-reader cohort `HT-4` records as missing; two rounds of operator review are not a substitute, because the operator already knows what the pictures are meant to show. If the lessons do not point at the new artifacts, that is a finding against the v4.4.6 plan, not against this one.
2. **A researcher runs `/research` on a topic of their own choosing** and judges whether the advisory completion-evidence block is USEFUL or NOISE at the end of a real deliverable. This is the half of Phase 3's verification expectation that this agent cannot produce: the arithmetic was exercised against a real report in the repository, but whether five metrics help or clutter a closing summary is a judgment about someone's working habits. Ask specifically whether the citation-coverage fraction changed what they did next.
3. **A security reviewer reads the OWASP Agentic column of `docs/framework-coverage.md` and challenges one tag.** Pick a tag and ask them to find the sentence in that skill's body that justifies it, using only `references/standards.md` as the pointer. This tests the claim the whole mapping rests on. `agent-execution-isolation`'s four tags are the highest-value target, since three of them were added beyond the plan's hypotheses; `loop-engineering`'s deliberate ABSENCE of `ASI08` is the second, because a reviewer who thinks it is a missing tag should find the ownership-table reason recorded in that skill's own `standards.md`.
4. **A maintainer runs a real install on a disposable machine** and confirms the two new loop reference files, the graph checklist, the verifier taxonomy, the stocktake fixture, and the changed `/research` command all land in the expected per-platform directories. This is the deep pass's one `NOT COVERED` item, and it also advances `HT-2`. Do NOT attempt it on a working machine: `HT-2` exists because a sandbox attempt mutated live platform config.

No fake walkthrough is offered, and none of these asks a human to exercise an incomplete feature.

---

## Full-suite testing and stabilization

The refactor changed no behavior because nothing was refactored: the architecture duty proposed no moves.

**Definitive full local suite**, run after every code and documentation edit was final so the evidence matches the reviewed revision:

```
python -m pytest tests/ -q
4403 passed, 68 skipped, 2 warnings in 2999.93s (0:49:59)
[exited with code 0]
```

The two warnings are a pre-existing `UnicodeDecodeError` in a pytest subprocess reader thread (`'utf-8' codec can't decode byte 0x97`), unrelated to this plan and present in the same form on the base revision.

Growth attributable to this plan: **+157 tests** (4246 at `a243c178`, 4403 now), across five files: `test_loop_engineering_bundle.py` (41), `test_orchestration_primitives_bundle.py` (22), `test_verifier_taxonomy_and_lifecycle.py` (51), `test_owasp_agentic_mapping.py` (63), and 15 cases appended to `test_framework_field_shape.py` (5 pre-existing, 20 now). Zero failures, and the `WN-I` flake passed in this run.

**Complete `validate` target**, every step executed directly because `make` is unavailable on this host (`WN-D`), each exit 0:

- 28 `python scripts/<name>.py` guards, including the two this plan changed (`validate_skills.py --bundles-only`, `build_framework_coverage.py --check`).
- The 4 inline JSON parse checks: `skills.json OK -- 336 skills`, `bundles.json OK -- 15 bundles`, `workflows.json OK -- 18 workflows`, `templates.json OK`.
- The compressor accuracy-regression gate: `Compression accuracy gate PASSED (CCR 100.0%, signatures 100.0%, reduction 45.8%)`.

33 steps in total. An earlier claim in this file said 28 and was corrected: the first pass had run only the `scripts/` guards, and the four JSON checks plus the compressor gate had not been executed when the claim was written.

**This local gate was insufficient, and the integration pull request proved it.** See `## Publication and integration` below. The steps above were each run and each passed, but they were run at DIFFERENT revisions across five phases, and never all at once against the final tree. `validate_no_personal_paths` was last executed during Phase 4, before Phase 5's documentation existed, and Phase 5 then wrote a personal filesystem path into a gap entry. Every individual claim above was true; the composite claim a reader would draw from them was not.

**Corrected gate, run as one command at the final revision**, which is the entry point CI's `validate` job actually invokes:

```
python scripts/ci/run.py --profile fast
PASS: 13 passed, 0 failed, 0 skipped, 0 advisory in 7.3s

python scripts/ci/run.py --profile full
FAIL: 43 passed, 1 failed, 0 skipped, 0 advisory in 4500.8s
```

The single `full` failure is its `repo-tests` step reporting `6 failed, 4397 passed`, all six in `tests/installer/test_core_settings_seeding.py` on the `powershell` parametrization. They do not reproduce (`470 passed, 43 skipped` for `tests/installer` entire; `12 passed, 10 skipped` for the file alone) and both CI test jobs passed them on the same commit. Recorded as a second instance under `WN-I` with the load hypothesis; not a defect this plan introduced, and not present in the file this plan touched.

**The durable lesson**: run `scripts/ci/run.py --profile full` as the local gate, not a hand-transcribed `Makefile` target. The profile IS the definitive list, which is the whole point of the repository-native-profiles design; transcribing the target reintroduced by hand exactly the two-list drift the profiles exist to prevent.

**Lint**: `shellcheck` is not installed on this host and the `lint` target skips with a note. No shell script was touched by any phase of this plan, so the gate is not applicable rather than bypassed.

This gate is LOCAL by construction and passed before the branch was published, so nothing in it depends on a remote result.

---

## Publication and integration

**Status: BLOCKED, awaiting explicit maintainer approval.**

Nothing has left this machine. Across all five phases there has been no `git push`, no pull request, and no remote CI run. The plan's four completed phases are four local commits on `feat/v4.8.0-agentic-loops`:

```
2d0de9f8 feat(security): map the catalog to the OWASP Agentic Top 10 as a seventh framework
2aada8ad feat(evaluation): name the verifier per deliverable and give research a finish line
76b6ba3c feat(orchestration): choose an autonomy level before a structure, and gate graphs
cc111f76 feat(loop-engineering): admit loops by a scored intake test and a run contract
```

The resolved publication parameters, for approval:

- **Branching model**: `develop` + `main` (per `AGENTS.md`). `main` is the installable branch and receives merges only at release time.
- **Remote**: `origin`.
- **Branch to publish**: `feat/v4.8.0-agentic-loops`.
- **Pull-request target**: `develop`, the integration branch. NOT `main`.
- **Required checks expected** (from `docs/policy/required-checks.json`): `validate`, `shellcheck`, `ci-required`, `colocation`, `verify`. Listed so a MISSING check is distinguishable from a FAILING one.
- **First remote validation**: this pull request, run against the synthetic merge result.

### Publication (approved 2026-09-07)

Approval was obtained explicitly at the gate. The branch was pushed ONCE:

```
git push -u origin feat/v4.8.0-agentic-loops
 * [new branch]  feat/v4.8.0-agentic-loops -> feat/v4.8.0-agentic-loops
```

Integration pull request opened against `develop`: **https://github.com/bendourthe/Nexus-Hub/pull/183**.

### First remote validation: RED, phase reopened

Run `34154935270`. Every check reached a terminal state. 21 of 23 contexts passed; `render` skipped legitimately.

```
validate:      fail
ci-required:   fail
shellcheck:    pass      colocation:    pass      verify:        pass
tests:         pass      tests-windows: pass      guide-render:  pass
changes:       pass      detect:        pass      CodeQL:        pass
Analyze (javascript-typescript): pass    Analyze (python): pass
bootstrap (macos-latest / ubuntu-latest): pass     bootstrap-windows: pass
install-smoke (macos / ubuntu / windows-latest): pass
installer-smoke (macos / ubuntu / windows-latest): pass
render:        skipping
```

`ci-required` failed CORRECTLY and for the right reason: it is an allowlist aggregate over its dependencies, and its log shows `R_validate: failure` producing `FAIL: a needed job did not succeed or skip -- validate=failure`. That is the fail-closed behavior the required-check contract specifies, observed working rather than assumed.

**Root cause**, from the job log:

```
validate  Repository-native validation profile  [FAIL] validate_no_personal_paths (0.9s)
validate  Repository-native validation profile  FAIL: 33 passed, 1 failed, 0 skipped, 0 advisory in 7.6s
```

**Reproduced locally before any fix**, per the never-re-run-a-red-check-without-a-local-reproduction rule:

```
python scripts/validate_no_personal_paths.py
docs\releases\v4\v4.8\known-gaps.md:98:98:  personal path leak: 'C:\\Users\\<user>' (username='<user>')
docs\releases\v4\v4.8\known-gaps.md:98:190: personal path leak: 'C:\\Users\\<user>' (username='<user>')
validate_no_personal_paths: 2 finding(s) in 2438 scanned file(s).
```

The leak was in `WN-I`, the flaky-test gap written during this phase, which quoted two absolute profile paths as evidence for its OneDrive-redirection hypothesis. The hypothesis is worth keeping; the absolute paths are not. Both were generalized to `<user-profile>/OneDrive - <tenant>/Documents/...` and `<user-profile>/Documents/...`, which preserves the finding and removes the leak.

**Why the local gate missed it**: `validate_no_personal_paths` last ran in Phase 4, before the Phase 5 text that broke it existed. See the correction under `## Full-suite testing and stabilization`.

**Verification after the fix**, at the final revision:

```
python scripts/validate_no_personal_paths.py   ->  0 findings
python scripts/ci/run.py --profile fast        ->  PASS: 13 passed, 0 failed
```

**Stabilization**: ONE narrowly scoped commit, not an amend. The final commit was already published and the pull request open, so amending would rewrite shared history; `[[code-commit-workflow]]` selects the added commit in that situation. Not a series.

### Merge

Pending. `/update release` remains held until every required check is green AND the merge to `develop` has landed.
