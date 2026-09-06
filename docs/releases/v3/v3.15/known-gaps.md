# Known Gaps - v3.15

**Project**: Nexus-Hub
**Status**: `v3.15.0` through `v3.15.9` are all released and tagged (10 releases). v3.15.10 Phases 1-4 are complete locally on `feat/v3.15.10-end-of-task-behavior`: two purposeful notification triggers with repo+branch labels and a run-time kill switch, the end-of-task summary rule in all 12 substantive instruction templates, per-platform notification-coverage verification with delivery to Cursor, and the terminal gate. Awaiting `/update release`.
**Last updated**: 2026-08-08 (v3.15.14 Phase 4 final reconciliation; release-ready, handed to `/update release`)

**Current v3.15.9 status**: Phases 1-7 run on `feat/v3.15.9-cross-provider-routing`, based on the released v3.15.8 `develop`. Claude/Codex/GitHub monitors install only into VS Code; Cursor Usage Monitor installs only into Cursor. Focused CI builds/packages the Cursor VSIX and degrades E2E when the hosted runner lacks the Cursor CLI, pointing at the live-smoke checklist. Phase 7 reconciled this ledger, confirmed CI coverage and optimization, and completed the README/CHANGELOG record; the remaining steps are the maintainer-approved branch push, the integration PR to protected `develop`, and `/update release` after green integration.

> **Correction notice (2026-07-30, applies file-wide)**: several advisory blocks below, in the v3.15.0 through v3.15.5 sections, attribute repo-wide Windows test failures to **WN-v36-1** ("bash cannot be fully exercised on the Windows dev host", covered on Linux in CI only). **That premise is disproven.** The cause was PATH shadowing: `C:\Windows\System32\bash.exe` (the WSL launcher stub) preceded Git Bash and could not resolve a Windows-style script path at all, so it exited 127 before executing a line. v3.15.6 Phase 4 fixed it structurally with a module-level PATH repair in `catalog/hooks/tests/conftest.py` and `tests/conftest.py`; both test trees now pass on Windows with no PATH assistance (658 and 516, zero failures). Those earlier blocks are left as written because they record what was believed at the time, which is what a gap ledger is for. Read them with this correction in mind, and do not cite WN-v36-1 as evidence that a Windows host cannot run bash. Canonical entry updated in [docs/releases/v3/v3.6/known-gaps.md](../v3.6/known-gaps.md); resolution detail in the v3.15.6 HO-1 and DF-2 entries below.

> **Prior-version ingest (platform-parity)**: v3.14.5's DF-4 (platform additive-surface drift) is the direct input to the v3.15.0 release and was actioned per phase; it does not carry forward as a separate open item. The v3.14.5 Advisory pre-existing failure `test_init_subcommand.py::test_default_wire_project_surfaces_returns_none` was re-confirmed and owned by Phase 5.2 (resolved; see the v3.15.0 Advisory below).

> **Prior-version ingest (codesight)**: checked `docs/v3/v3.14/known-gaps.md`. The open v3.14 items (usage-monitor DF/HO series) are unrelated to this feature set and do not carry in. The one relevant caveat is **HO-1** (flat/nested skill-name collision across skill layouts): the codesight plan shipped zero new catalog skills (all work is extension code), so HO-1 does not apply.

> **Scope note (version collision, RESOLVED)**: three plans under `docs/v3/v3.15/plans/` were all stamped `v3.15.0` (`platform-parity-all-gaps`, `adoption-codesight`, and `adoption-awesome-llm-apps`). This was the comparison-versioning artifact (plans stamped with the authoring-cycle version, not the real adoption target). Reconciled on 2026-07-22 by re-stamping: v3.15.0 = platform-parity-all-gaps, v3.15.1 = adoption-codesight, v3.15.2 = adoption-awesome-llm-apps. See the v3.15.1 QG-2 (Resolved) entry.

## v3.15.14 - spec artifact reconciliation and proportional spec depth

### v3.15.14 Phase 4 - FINAL RECONCILIATION (release-ready)

**Status**: Phase 4 (Architecture Refactor, Known-Gaps Reconciliation, and CI/CD) complete on `feat/adoption-spec-driven-development`. This is the plan's terminal phase, so the release-readiness workflow ran. The version bump, changelog stamp, tag, and push are handed to `/update release` and were NOT performed here.

**Final disposition of every v3.15.14 open item**: 2 closed this phase (QG-1, MT-1), 1 closed in Phase 2 (NI-1), 2 transferred to v3.16 (NI-2 as TR-1, the spec-kit S5/S6/S8 non-claim as TR-2), 1 closed on verification rather than transferred (the setup-node pin, recorded as TR-3), 3 recorded as decisions or enhancements needing no action (DF-1, EN-1, DC-1). **No open item remains and no release blocker exists.**

#### 4.1 Architecture refactor

Near-no-op as the plan predicted, with one deliberate departure from precedent.

Both of the plan's specific checks are clean. **No orphaned reference to the removed inline spec template survives** anywhere in `catalog/`, `guides/`, or `docs/`: a sweep for the distinctive "Objective / Commands / Project Structure / Code Style / Boundaries" cluster attributed to a spec returns nothing. The one `### Objective` heading remaining in `catalog/` is `competitive-generation`'s task-brief template (Objective plus Acceptance Criteria for a competitive-generation brief), which is unrelated and correctly left alone. **`catalog/templates/` gained no stray file**: it still holds exactly `constitution-template.md`, `spec-quality-checklist.md`, and `spec-template.md`, so no installer registration is required in either `scripts/installer.sh` or `scripts/installer.ps1`.

**The empty-directory posture changed, on an explicit maintainer decision.** Every prior audit in this version (v3.15.5, v3.15.7, and v3.15.14 Phases 1 to 3) reported the 8 untracked empty directories under `catalog/skills/` and left them in place as a parallel session's scaffolding. This phase surfaced them again along with a ninth (`docs/v3/v3.17/comparisons`), and the maintainer chose deletion over the precedent. All nine were removed after verifying each was genuinely empty AND carried zero tracked files; removing them exposed two parent shells (`catalog/skills/testing/visual-regression-testing`, `catalog/skills/tests-generation/performance-regression-gate`) that had held only a `scripts/` child and no `SKILL.md`, and those were removed on the same test. `git status` is unchanged by all eleven removals, confirming zero repository impact.

That decision turned out better than the precedent: `validate_skills.py --bundles-only` warnings dropped from **18 to 11**, because several of the removed `scripts/` directories were generating orphan-bundle warnings. The precedent was defensible but was quietly costing validator signal.

No committed file moved or was renamed, so no reference repair was needed. The docs tree stays canonical, no tracked build or coverage artifact exists (`git ls-files` matches nothing under `out/`, `coverage/`, or `*.vsix`), and no untracked file sits under `docs/`.

#### 4.2 Reverse-engineering matrix

`docs/policy/mcp-reverse-engineering-matrix.md` gains an "Adopted in the v3.15.14 spec-driven-development cycle" section: seven rows, one per candidate. D1, D2, and D7 are classified `re-full` (local artifact edits to owned templates and skills); D6, D5, D4, and D3 are `skill-native` under MCP Registry Policy tier 2. The Rationale column names all three external sources (the spec-driven-development article attributed to Gregor Ojstersek, the `obra/superpowers` example specification, and `github/spec-kit`) and states that per the Reverse-Engineering Attribution Rule none is named in any distributed artifact, which was verified.

Both policy declines are recorded with their actual grounds. The **Spec Kit CLI is declined as redundant, not as a trust concern**: all ten `speckit.*` commands have first-party equivalents, so tier 2's preference for an LLM-native skill over an external tool applies. **Architecture-in-the-spec is declined on layering grounds, not trust grounds**: it conflicts with the normative-versus-context split and would fail `spec-quality-checklist.md`'s implementation-detail checks, so a spec written to the source's shape would fail its own quality gate. The one genuine sub-gap (error handling) was adopted at the plan layer as D4 instead.

Cycle-wide confirmation recorded in the matrix: no adopted item introduces an MCP entry, an outbound call, an API key, a third-party data processor, or a runtime dependency. `catalog/mcp-configs/mcp-servers.json` is untouched and the registry size is unchanged.

#### 4.3 Known-gaps reconciliation and transfers

**Closed this phase:**

- **QG-1 - CLOSED.** The plan asserts a 269-skill catalog in its Overview and in sub-task 4.4; validation reports **270**. The plan's reasoning was sound (this plan creates no skill, so the count is unchanged BY THIS PLAN) but its literal figure had gone stale because a parallel workstream shipped a skill in between. The CHANGELOG entry states 270, re-derived from validator output rather than transcribed from the plan.
- **MT-1 - CLOSED.** `tests/skills/test_spec_artifact_agreement.py` now guards the three-artifact agreement: 21 cases asserting the template carries its mandatory headings and marks them mandatory, that the skill's Verification checklist names each one, that the skill declares exactly one canonical skeleton and no rival has returned, that the checklist's scope item is bound to `## Non-Goals` **on its own line**, that a reason-per-entry item exists, that the reviewer agrees with the template's heading, and that the template still mandates a reason per Non-Goal. CI already runs `tests/skills`, so it is covered without a workflow change; the step label was updated to name it.

  **The guard was mutation-tested, and the first draft failed that test.** Three mutations were applied and reverted: unbinding `## Non-Goals` from the checklist's scope item, deleting the reason-per-entry item, and repointing the skill's Verification at the rival template's six areas. The third failed correctly on the first draft, but **the first mutation passed**, because the assertion was `"Non-Goals" in checklist` and the heading is also named in the Content Quality section. The test asserted presence of a token rather than the binding. It was rewritten to check the scope line itself, and all three mutations now fail while the baseline passes 21. Recorded because a guard that passes on the defect it was written to catch would have closed MT-1 on a false guarantee.

**Transferred to v3.16** (see [docs/releases/v3/v3.16/known-gaps.md](../v3.16/known-gaps.md), `TR-#` namespace):

- **NI-2 becomes TR-1**: the `A1` example still phrases a Non-Goal as an Assumption. Left by plan instruction; the Non-Goals authoring note names it as the worked illustration. Fixing it while the note still points at it would remove the evidence, so the rewrite belongs to whichever cycle next touches the template.
- **The spec-kit non-claim becomes TR-2**: v3.11.0 items S5, S6, and S8 were not re-examined by this article-scoped pass and carry **no status claim** in either direction. A future repository-delta comparison must verify them rather than infer from this cycle.

**Closed on verification instead of transferred:**

- **TR-3**: the plan directed transferring "`actions/setup-node@v4` remains tag-pinned at `.github/workflows/claude-usage-monitor.yml`:31". Verification found it SHA-pinned at line 38, along with all three siblings (`codex`, `cursor`, `github` monitor workflows), all at `@49933ea5288caeca8642d1e84afbd3f7d6820020 # v4`, and `validate_workflow_security.py` passes. Transferring it would have carried a false open item into the v3.16 ledger. Recorded as closed rather than dropped silently, so a reader of the plan is not left expecting a transfer that never arrived.

**Phase 1.4 remainder**: none. The plan's fourth transfer was conditional ("if Phase 1.4 revealed that `idea-refine` or `scope-guardian-reviewer` needed more than a naming reconciliation"). Both needed only the minimum change, so there is no deferred remainder to record.

**Needing no action**: DF-1 (Phase 1, resolved in place), EN-1 (Phase 2, an enhancement beyond the plan), DC-1 (Phase 3, the `implementation-plan` skill choice).

**Marker sweep across every file this version changed**: zero `TODO` / `FIXME` / `XXX` / `HACK` / `# DEVIATION:` markers. The plan's deviations and decisions are recorded in this ledger and in the session histories, not left inline.

#### 4.4 CHANGELOG

`CHANGELOG.md` had **no `## [Unreleased]` section** (the file went straight from its header to `## [3.15.13]`), so the section was created rather than appended to. It carries Fixed entries for the template's missing scope boundary, the completion gate validating the wrong artifact, and `idea-refine`'s reasonless hand-off; and Added entries for Problem Statement and Invariants, the blast-radius depth tier (noting explicitly that the hard approval gate is unchanged and unconditional), plan-layer failure-mode coverage, the build-class convention, and the new guard test. ASCII-only. The catalog count is stated as **270**, not the plan's 269. No version-carrying surface was bumped; `/update release` owns that and the `check_version_sync.py` gate.

#### 4.5 CI/CD

**Covered without a structural change, and the reasoning is recorded so it is not re-derived.** Every surface this plan touched (`catalog/templates/**`, `catalog/skills/developer-experience/spec-driven-development/**`, `catalog/skills/workflow/implementation-plan/**`, `catalog/agents/scope-guardian-reviewer.md`) sits outside `docs/`, so `ci.yml`'s workflow-level `paths-ignore: docs/**` fires the full job set for all of them. Adding a positive `paths:` filter restricted to those directories, as sub-task 1.5 literally suggested, would have **narrowed** coverage rather than optimizing it.

The four optimizations the plan asks for are already present and were verified rather than assumed: `concurrency` with `cancel-in-progress` at workflow level, pip caching keyed on `.pre-commit-config.yaml`, expensive Windows and matrix legs gated behind `if: github.event_name != 'pull_request'`, and SHA-pinned action references with version comments. The new guard test needed no new job because the `Skills-script tests` step already runs `tests/skills` as a directory; only its descriptive label was updated to name the new coverage, which is the single CI edit in this phase.

#### 4.6 Definition of Done, re-verified end to end

Each item checked against the tree rather than assumed from the phase reports:

1. **A spec from the template has a section for non-goals, and the checklist's scope item is tickable from the template alone.** Verified in Phase 1 by authoring a throwaway spec and walking the checklist, and now permanently asserted by `test_spec_artifact_agreement.py`.
2. **`scope-guardian-reviewer`'s out-of-scope finding cannot fire on a template-conformant spec.** The reviewer names `## Non-Goals`, the template produces it, and a test asserts both.
3. **The skill names exactly one canonical template and its Verification lists that template's sections.** Asserted by three tests, including one that fails if a rival inline template returns.
4. **The depth rule exists and the hard gate's unconditional clauses survive verbatim.** Proven by diff shape: across Phase 2 the file has exactly two deleted lines, neither in the gate block.
5. **`make validate`, `make lint`, `make test` pass and the FR-### / SC-### contract is unchanged.** The ID contract was proven in Phase 1 by a 46-insertion, 0-deletion diff on the template.

#### Advisory (no action required)

- **Model-prompting-profile staleness check (9.0 step 4)**: `verify_model_prompting_profiles.py` (the structural gate) passes. The advisory freshness check is deliberately NOT a release blocker and is `/update release`'s governance step 5, where it belongs; it was not run here and was not re-stamped.
- **Two stale facts in one plan, same lesson.** QG-1 (the 269-skill count) and TR-3 (the setup-node pin) were both true when the plan was written and both went stale before Phase 4 ran. Neither was caught by transcription; both were caught by checking the assertion against the tree. A plan is a decision record, not a data source.

### v3.15.14 Phase 3 checkpoint

**Status**: Phase 3 (Plan-layer conventions, D4/D3) complete locally on `feat/adoption-spec-driven-development`. `implementation-plan` was chosen as the single plan-layer skill and now requires per-component failure-mode coverage across three named situations, carries a one-line scaffolding-versus-load-bearing build class per sub-task, and has two matching Verification items plus two rationalization rows. `plan-before-code` was NOT edited. `spec-template.md` was not touched, which is the declined merge this phase had to avoid. Phase 4 is not started.

**Summary**: 0 deviations, 0 new gaps, 1 recorded decision (DC-1, the skill choice), 0 blockers.

### v3.15.14 Phase 3 Open Items

#### Decisions recorded

##### DC-1 - `implementation-plan` chosen over `plan-before-code` as the plan layer for D4 and D3

- **Source phase**: v3.15.14 Phase 3.1
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.14-spec-driven-development.md` sub-task 3.1 ("or `plan-before-code` if that is the better fit for per-component design detail; pick ONE and state the choice")
- **Decision**: `implementation-plan`, confirmed with the maintainer before editing. Four grounds. It produces a durable artifact under `docs/**/plans/`, so the convention lands in a document a reviewer reads later, whereas `plan-before-code`'s plan lives in the conversation turn. It already has a per-sub-task template (`#### N.1` with `**Objective**` and `**Prompt**`), which is the native attachment point for D3's one-line-per-sub-task label; `plan-before-code`'s plan template has no per-sub-task slot. It is the spec's downstream consumer via `/spec` then `/plan`, which is what makes D4's compose-with-`### Edge Cases` story work at all. And the two skills' own cross-link settles the layering: `implementation-plan` describes `plan-before-code` as "lightweight planning for individual features within a phase", so per-component detail across a plan belongs to the outer skill.
- **Cost accepted**: `implementation-plan` was at 445 of the 500-line body target, against `plan-before-code`'s 353. The edits were budgeted to fit inline rather than pushed to a `references/` file, on the reasoning that both conventions are authoring-time rules that shape every sub-task written (Tier 2), not edge-case reference material (Tier 3). Final size 469 lines, 31 under the target.
- **Suggested next step**: None. Recorded so a future reader does not re-litigate the choice, and so the Phase 3 exit-checklist item "exactly one plan-layer skill chosen" has a stated answer.

#### Advisory (no action required)

- **The declined merge held.** This phase's whole risk was that closing the error-handling gap would pull architecture back into the spec, which the comparison declined because it conflicts with the normative-versus-context split and would fail `spec-quality-checklist.md`'s implementation-detail checks. Verified mechanically: `git diff --name-only` for Phase 3 lists exactly one file, `catalog/skills/workflow/implementation-plan/SKILL.md`. `spec-template.md` was not modified, its `Key Entities` prohibition ("Do not include database schemas, column types, or implementation details") is intact at line 107, and a grep of the template for retry / backoff / error-handling / schema / interface / module-boundary language returns only that prohibition line itself. The new Step 3.6 also states the boundary explicitly as an instruction to future authors: do NOT close this gap by pushing error handling, data models, interfaces, or schemas back into the spec template.
- **The build-class provenance note is recorded in the skill body without attribution**, per the plan and the AGENTS.md reverse-engineering attribution rule. The skill says the convention is adopted on its own merits, that it was proposed on the strength of an example specification said to demonstrate it, and that the document carried no code blocks and no such labeling, so the cited evidence does not support the claim. No external article, author, newsletter, or repository is named. Full provenance goes in the Phase 4.2 matrix row.
- **CI/CD unchanged, third phase running.** One file under `catalog/`, outside `docs/`, so `ci.yml`'s existing `paths-ignore: docs/**` trigger fires the full job set. The plan-contract suite (`tests/plans`) is the surface most at risk from a plan-template change and it passes; those tests assert the presence of required fields rather than the absence of others, so the two new template fields are additive.
- **QG-1, MT-1, and NI-2 carry forward to Phase 4 unchanged.**

### v3.15.14 Phase 2 checkpoint

**Status**: Phase 2 (Proportional spec depth, D6/D5) complete locally on `feat/adoption-spec-driven-development`. A blast-radius depth-tier rule now sits INSIDE the Hard Gate section, the opening motivation carries the guess-cost-scales-with-codebase-size argument, "When NOT to use" separates the needs-a-spec question from the how-deep question, and two rationalization rows defend the new rule against the misreadings it invites. The hard gate is provably unmodified. NI-1 was closed in passing with maintainer approval. Phases 3 and 4 are not started.

**Summary**: 0 new deviations, 1 gap closed (NI-1), 1 scope addition beyond the plan (a second rationalization row, recorded below as an enhancement rather than a deviation), 0 blockers. The full test surface is green for the first time this version: 3,250 passed, 0 failed.

### v3.15.14 Phase 2 Open Items

#### Resolved this phase

##### NI-1 - CLOSED: `overview_l1` no longer advertises project-level areas as spec capabilities

- **Source phase**: opened v3.15.14 Phase 1.3, closed v3.15.14 Phase 2
- **Reason it was open**: the frontmatter listed "project structure definition, boundaries (Always/Ask/Never)" among the skill's key capabilities, which Phase 1 had relocated out of the feature spec and into project-level context. The statement was not false, but it read as though those areas belong in a spec.
- **Resolution**: the clause now reads "scope bounding through explicit non-goals, spec depth chosen by blast radius", which describes what the skill actually does after Phases 1 and 2 and adds trigger vocabulary matching the new capability rather than removing vocabulary outright. Closed with maintainer approval to fold it into this phase rather than defer to Phase 4.
- **Verification**: `run_trigger_evals.py --gate` re-run after the edit, since `overview_l1` is Tier-1 always-loaded metadata and a reword moves routing vocabulary. Result: 0 un-allowlisted collisions, 0 routing failures across the 9 skills carrying cases. No routing regression.

#### Enhancements beyond the plan (recorded, not deviations)

##### EN-1 - A second rationalization row was added; the plan specified one

- **Source phase**: v3.15.14 Phase 2.1
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.14-spec-driven-development.md` sub-task 2.1 ("Add a Common Rationalizations row rebutting the misreading this rule invites")
- **Reason**: the plan named the skip-the-approval misreading, which is now row 4. A second misreading is at least as likely and the plan did not name it: reading "the change is small" as qualifying for "When NOT to use" (no spec) rather than for the depth rule's bottom tier (a short spec). That is the shallow-spec-becomes-no-spec slide, and it is a different error from treating a short spec as a licence to skip approval, so one row could not rebut both without blurring. Row 5 covers it. This adds material rather than departing from the plan, so it is recorded as an enhancement rather than as DF-2.
- **Suggested next step**: None. Recorded so the Phase 2 exit checklist item ("a third added rebutting the depth rule's misreading") reads correctly against a table that now has two additions, not one.

#### Advisory (no action required)

- **The full repository test surface is green.** Running `pytest tests catalog/hooks/tests` from PowerShell rather than Git Bash yielded **2580 passed, 56 skipped, 0 failed** (exit 0), plus 670 passed / 1 skipped across the five extension suites and a passing compression accuracy gate. This is a direct empirical confirmation of Phase 1's BG-16 classification: the identical tree that produced `1587 passed, 1 failed` under Git Bash produces `2580 passed, 0 failed` under PowerShell, with the difference being exactly `test_ps_standalone_extracts_and_hands_off`. BG-16's cause and suggested next step are unchanged; this entry only records that the shell-dependence was reproduced deliberately in both directions.
- **The hard gate's integrity was proven mechanically, not by reading.** Across all of Phase 2 the file has exactly two deleted lines: the `overview_l1` frontmatter line and the old one-line "When NOT to use" paragraph. The Hard Gate block therefore has zero deleted lines, which establishes that "The gate applies regardless of how simple the change looks" and "Silence is not approval" survive verbatim without needing a string comparison to say so. The four surfaces (behavior, public API, data schema, CLI) are byte-identical between the new tier table and the merge-gate section.
- **CI/CD unchanged, same reasoning as Phase 1.** This phase modified one file under `catalog/`, which sits outside `docs/` and therefore fires `ci.yml`'s full job set through the existing `paths-ignore: docs/**` trigger. No new surface, no new optimization opportunity.
- **QG-1 and MT-1 carry forward unchanged.** The catalog holds 270 skills, not the 269 the plan asserts, and nothing automated yet asserts the template / checklist / skill trio stays in agreement. Both remain Phase 4 work.

### v3.15.14 Phase 1 checkpoint

**Status**: Phase 1 (Reconcile the spec artifact, D1/D2/D7) complete locally on `feat/adoption-spec-driven-development`. `spec-template.md` gained `## Problem Statement`, `## Non-Goals`, and `## Invariants` as a pure-insertion diff (46 insertions, 0 deletions, so the FR-### / SC-### contract is mechanically unchanged); `spec-quality-checklist.md` binds its scope-bounding item to the new section; `spec-driven-development` SKILL.md now names exactly one canonical template and its Verification checklist enumerates that template's sections; `scope-guardian-reviewer` and `idea-refine` were reconciled to the template's heading names. Phases 2-4 are not started.

**Summary**: 1 deviation (DF-1, resolved in place), 2 deferred items (NI-1, NI-2), 1 quality-gate discrepancy for a later phase (QG-1), 1 missing-test gap (MT-1). No blocker.

### v3.15.14 Phase 1 Open Items

#### Deviations

##### DF-1 - RESOLVED IN PLACE: the rival inline template was removed in prose form as well as code-block form

- **Source phase**: v3.15.14 Phase 1.3
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.14-spec-driven-development.md` sub-task 1.3
- **Reason**: The plan named "the rival inline template block at lines 176-207" for removal. That code block was only half the rival artifact: the same structure existed immediately above it as prose, in the "Write a spec document covering six core areas" enumeration at former lines 134-173, and the Verification item the plan explicitly repoints ("all six core areas") referenced the PROSE list, not the code block. Removing only the code block would have left the skill still instructing the author to cover six areas the canonical template does not have, which fails the phase's own Stability Gate ("SKILL.md names exactly one canonical template"). Both forms were therefore removed and their project-onboarding content relocated together into the new "Project-level context (distinct from a feature spec)" section, which is what the plan's relocation instruction asked for.
- **Suggested next step**: None; the deviation is resolved and consistent with the plan's stated intent. Recorded because it exceeds the literal line range the plan named.

#### Non-implemented / deferred

##### NI-1 - CLOSED in Phase 2: `spec-driven-development`'s `overview_l1` still advertises project-level areas as spec capabilities

> **Status update**: closed by v3.15.14 Phase 2 with maintainer approval; see the NI-1 entry under the Phase 2 checkpoint above for the resolution and the trigger-gate verification. The entry below is retained as written, which is what it looked like when it was opened.

- **Source phase**: v3.15.14 Phase 1.3
- **Plan reference**: same plan, sub-task 1.3
- **Reason**: The frontmatter `overview_l1` lists "project structure definition, boundaries (Always/Ask/Never)" among the skill's key capabilities. After Phase 1 the body scopes those to project-level context rather than to a feature spec. The statement is not false (the skill still teaches them, in their correct home), but the phrasing predates the split and reads as though they belong in the spec. It was deliberately left alone: `overview_l1` is Tier-1 always-loaded metadata, edits to it change routing vocabulary, and the trigger-and-routing gate is the surface that would surface a regression. Changing it inside a phase whose gate is about template authority would conflate two risks.
- **Suggested next step**: Reword the two clauses during Phase 2 (which already edits this file's motivation prose) or in Phase 4's refactor, then re-run `python scripts/run_trigger_evals.py --gate` to confirm no routing regression.

##### NI-2 - OPEN: the `A1` example still phrases a Non-Goal as an Assumption

- **Source phase**: v3.15.14 Phase 1.1
- **Plan reference**: same plan, sub-task 1.1 (which instructed "leave `A1`'s text alone")
- **Reason**: `spec-template.md`'s `A1` example reads "Authentication uses the existing session-cookie middleware; JWT is out of scope for this feature". The second clause is a Non-Goal, not an Assumption, under the boundary the new `## Non-Goals` authoring note defines. The plan chose to document the boundary rather than rewrite the example, so the template now explains the distinction and names `A1` as the illustration of getting it wrong.
- **Suggested next step**: Already scheduled for the record in Phase 4.3. Rewriting `A1` into a clean Assumption (and moving its scope clause into the Non-Goals example) is a one-line follow-up.

#### Quality gates

##### QG-1 - OPEN: the plan asserts a catalog count of 269; the catalog holds 270

- **Source phase**: v3.15.14 Phase 1.5 (observed during validation)
- **Plan reference**: same plan, Overview ("the catalog count stays at 269") and sub-task 4.4 ("catalog count is unchanged at 269 skills")
- **Reason**: `make validate` reports `skills.json OK -- 270 skills`. The plan was authored when the catalog held 269 and a skill has landed since. The plan's underlying claim is still correct (this plan creates no new skill, so the count is unchanged BY THIS PLAN), but the literal number is stale, and Phase 4.4 would write the wrong figure into `CHANGELOG.md` if followed verbatim.
- **Suggested next step**: In Phase 4.4, write "unchanged at 270 skills" and re-derive the number from `make validate` output at the time rather than from the plan text.

#### Missing tests

##### MT-1 - OPEN: no automated check asserts the spec artifact trio stays in agreement

- **Source phase**: v3.15.14 Phase 1.5
- **Plan reference**: same plan, sub-task 1.5
- **Reason**: The whole defect this phase fixes was a silent disagreement between three prose artifacts: the template's sections, the checklist's items, and the skill's Verification list. Phase 1 repaired the disagreement but added nothing that would detect it recurring. The existing validators cover placeholder syntax, bundle orphans, and routing vocabulary; none of them knows that the skill's Verification list is supposed to enumerate the template's headings. A future edit to any one of the three can silently desynchronize them again, which is precisely how the original defect arose.
- **Suggested next step**: Add a small pytest under `tests/` asserting (a) `catalog/templates/spec-template.md` contains the mandatory headings `## Problem Statement`, `## User Scenarios & Testing`, `## Requirements`, `## Success Criteria`, `## Non-Goals`, (b) each of those headings is named somewhere in the `spec-driven-development` Verification section, and (c) `spec-quality-checklist.md` references `## Non-Goals`. Roughly 20 lines, no new dependency. Best placed in Phase 4 alongside the CI/CD pass so the new test is covered by the existing workflow.

#### Advisory (no action required)

- **BG-16 re-confirmed, not re-opened**: `tests/installer/test_bootstrap.py::test_ps_standalone_extracts_and_hands_off` failed once during Phase 1.5 validation and was traced to the already-documented v3.15.12 BG-16 cause: the suite was launched from Git Bash, so `install.ps1` inherited a `PATH` resolving GNU tar 1.35 ahead of Windows bsdtar 3.8.4. The same test passes from PowerShell on the identical tree, which was verified. Phase 1 changed five Markdown files under `catalog/` and touches nothing the test exercises. No new entry is warranted; BG-16 remains the canonical record and its suggested next step is unchanged.
- **CI/CD assessed, no change proposed**: sub-task 1.5 asked for a path-filtered pipeline covering `catalog/templates/**` and `catalog/skills/**`. `.github/workflows/ci.yml` already covers both, via a `paths-ignore: docs/**` trigger (the changed directories sit outside `docs/`, so every one of them fires the full job set), and it already carries the three optimizations named: `concurrency` with `cancel-in-progress`, pip caching keyed on `.pre-commit-config.yaml`, and the expensive Windows and matrix legs gated behind `if: github.event_name != 'pull_request'`. Adding a positive `paths:` filter restricted to those two directories would NARROW coverage rather than optimize it, so none was added. Phase 4.5 should re-confirm rather than re-derive this.

## v3.15.12 - cursor live transport and github billing monitor

### v3.15.12 Phase 1 checkpoint

**Status**: Phase 1 (Cursor consent-gated live transport) complete locally on `feat/v3.15.12-usage-monitor-transport-and-auth`. Consent gate, read-only allowlisted-key session adapter, `credential-api` transport with a declarative wire contract, provenance/staleness labelling, and a real capability check all landed with 233 extension tests green and coverage at 93.05 statements / 86.52 branches / 97.55 functions / 93.19 lines. Phases 2-5 are not started.

### v3.15.12 Phase 1 Open Items

#### Hand-offs

##### BG-16 - OPEN: `test_ps_standalone_extracts_and_hands_off` passes or fails depending on which shell launched pytest

- **Status**: Open. A test-harness defect, not a product defect. Recorded rather than fixed, because the fix touches a bootstrap test outside this version's scope.
- **Symptom**: `tests/installer/test_bootstrap.py::test_ps_standalone_extracts_and_hands_off` fails deterministically when the suite is launched from Git Bash (`/usr/bin/tar: unexpected end of file`, `Child returned status 128`) and passes deterministically when launched from PowerShell. Its four siblings in the same file pass either way. Verified by three consecutive failing runs from Git Bash and a clean `5 passed` from PowerShell on the same tree.
- **Cause**: The test constructs its subprocess environment as `{**os.environ, ...}`, so `install.ps1` inherits whatever `PATH` pytest itself was started with. From Git Bash, `/usr/bin` precedes `System32`, so the script resolves **GNU tar** (shipped with Git for Windows) instead of the **bsdtar** that Windows bundles as `tar.exe`. GNU tar rejects the archive that Python's `tarfile` module wrote for the fixture; bsdtar accepts it.
- **Why it matters beyond this repo**: a real user running `install.ps1` from PowerShell gets bsdtar and is unaffected, so the shipped bootstrap is sound. But the test's verdict depends on the shell that launched the suite, which is precisely the property a test must not have. It also means a CI runner whose `PATH` puts a GNU tar first would fail this test while the product works, and the reverse - it silently masked itself in the v3.15.12 final gate, which was run from PowerShell and therefore read green.
- **Suggested next step**: Have the test resolve the archiver explicitly rather than inherit it - either pin `PATH` to the Windows system directory for the subprocess, or assert against whichever `tar` is resolved and write the fixture archive in a format both accept (GNU tar is stricter about padding on small archives). Do **not** "fix" it by writing the tarball differently without also removing the `PATH` dependency, because that leaves the shell-sensitivity in place for the next fixture.

##### HO-7 - CLOSED: personal usage now reads automatically through the verified Connect RPC

- **Status**: Closed. The route was recovered, probed (HTTP 200), implemented, and verified end-to-end against a live account: the compiled transport returned real percentages, correct billing-cycle dates, and the shared pool correctly identified as pooled team context. This entry previously read "closed as a negative: no such surface exists". **That conclusion was wrong and is retracted.** It rested on `cursor.com/docs/api` documenting only Enterprise-admin APIs, and treated absence from the public docs as absence of a surface - the same reasoning error already corrected once in this version's GitHub auth work.
- **What the evidence actually shows**: Cursor's own client calls `GetCurrentPeriodUsage` on `aiserver.v1.DashboardService`, a unary Connect RPC. The request message is `GetCurrentPeriodUsageRequest { team_id: int32 optional }`, so a personal query is an empty body. The response carries exactly the figures this extension renders: `billing_cycle_start` / `billing_cycle_end` (int64), a `plan_usage` message with `auto_spend`, `auto_limit`, `auto_percent_used`, `api_spend`, `api_limit`, `api_percent_used`, `total_spend`, `included_spend`, `bonus_spend`, `remaining`, and `limit`, plus a `spend_limit_usage` message distinguishing `pooled_*` (the shared team pool) from `individual_*` and naming `limit_type`. Recovered by reading the locally installed client bundle, not by network probing.
- **Why the shipped transport fails**: `CURSOR_WIRE_CONTRACT` assumes `GET /api/usage-summary`, a REST path that does not exist. That is what produced the probe's `401`, then `405` with `allow: POST`, then `403`. The `405` was the real signal and was under-read at the time: a Connect endpoint is POST-only. The credential half of the design is unaffected - `cursorAuth/accessToken` read read-only from one allowlisted key is exactly what the client itself authenticates with, and is the direct analogue of how the Claude monitor reads `~/.claude/.credentials.json` and the Codex monitor reads `~/.codex/auth.json`.
- **What this invalidates**: the claim that automatic personal usage "is not buildable" (retracted), and the plan to reach it through an Enterprise adapter, which would not have served a Team-plan user anyway. The manual copy step is a stopgap and should not be presented as the intended design: a pasted snapshot is frozen at the moment it was entered, so it goes stale silently and reports a stale number as current - the precise failure mode the rest of this extension is built to prevent.
- **Resolution**: `CURSOR_WIRE_CONTRACT` is now `wire/v2-rpc-verified` with `verified: true`, POSTing an empty body to the RPC host behind the existing consent gate. Three probe findings are pinned by tests: field names are camelCase (Connect's proto3 JSON mapping, not the descriptor's snake_case), percentages are used as delivered and never derived (spend-over-limit gave 1078.70 against a reported 23.97), and money is minor units (limit 2000 for a 20-dollar allowance) with cycle bounds as epoch-millisecond strings. Two defects were caught during implementation: the production `FetchJsonClient` still hardcoded `method: "GET"` while every stub-based test passed, and the panel's command guard would have rendered the new button inert; both now have tests. HO-5 is superseded, since the route it was waiting to verify is not the route that exists.
- **Superseded next step** (retained for the record): Replace the REST contract with the Connect call (`POST https://api2.cursor.sh/aiserver.v1.DashboardService/GetCurrentPeriodUsage`, `content-type: application/json`, empty `{}` body, bearer token from the existing session adapter) behind the consent gate that already exists. Confirm the field units before rendering money: the spend fields are `int32`, which strongly suggests cents rather than dollars, and formatting cents as dollars would overstate spend by 100x. Keep `verified: false` until one bounded probe on a real account confirms both the field names and the units.

##### HO-5 - NARROWED, not closed: the wire contract is unverified against a live account

- **Source phase**: v3.15.12 Phase 1.3 - Session adapter and transport (T005 / T006)
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.12-cursor-live-transport-and-github-billing-monitor.md` (sub-tasks 1.3, 1.5)
- **Reason**: The plan's "Prior-version gaps ingested" table records HO-5 as "Closed by Phase 1". That is **not** what shipped, and the difference matters. The consent gate, the read-only one-key adapter, the transport, and the degradation path are all implemented and tested, and the authorization boundary is recorded in `cursor-usage-auth-probe.md`. What is NOT established is that the undocumented JSON route exists at the assumed path with the assumed field names and units. Cursor documents no personal-usage API, so that can only be settled by one bounded probe using the maintainer's own signed-in session, on the maintainer's host. Rather than invent a fixture and label it verified, `CURSOR_WIRE_CONTRACT.verified` is `false`, the fixtures carry `provenance: expected-shape-unverified`, and every field name is a dot-path in one table so correcting them is a string edit. A payload that does not match is rejected, so the failure mode is "degrades to cache with a staleness label", never "renders a wrong number as live".
- **Suggested next step**: Run the Bounded Probe Procedure in `cursor-usage-auth-probe.md` once, record the sanitized field names and units, and correct `tests/fixtures/cursor-usage/wire-contract.json` together with the `CURSOR_WIRE_CONTRACT` constant (a test asserts the two agree). HO-5 closes at that point. If the route turns out not to exist, the honest outcome is to keep the manual/cache posture and say so, not to reach for HTML scraping, which the non-goals exclude.

#### Warnings

##### WN-5 - Live transport requires Node 22.13+ in the extension host, and emits an experimental warning where present

- **Source phase**: v3.15.12 Phase 1.3 - Session adapter (T004)
- **Plan reference**: same plan, sub-task 1.3
- **Reason**: Reading `state.vscdb` needs SQLite. Adding `better-sqlite3` would break the plan's own "no new dependency" Constitution Check and require per-platform prebuilds in the VSIX, so the adapter uses Node's built-in `node:sqlite`, feature-detected via a guarded dynamic import. Two consequences. First, a Cursor build whose Electron ships Node 20 has no `node:sqlite`; the capability check reports `sqlite-unavailable` and the extension degrades to cache/manual, which means the plan's Definition of Done ("real numbers after exactly one consent click") is host-dependent and unproven on the maintainer's specific Cursor build. Second, `node:sqlite` is still flagged experimental upstream and emits `ExperimentalWarning: SQLite is an experimental feature` on import; in an extension host that lands in the log, not in front of the user.
- **Suggested next step**: When running the HO-5 probe, record the Cursor version and whether the capability check reports `available` on that host. If it reports `sqlite-unavailable`, the options are a hand-rolled read-only page parser or accepting the manual posture on that host; do not add a native dependency without revisiting the Constitution Check.

#### Quality gates

##### QG-6 - RESOLVED same phase: the Cursor CI workflow did not trigger on a fixture-only change

- **Source phase**: v3.15.12 Phase 1.5 - Tests and stabilization (post-phase CI/CD pass)
- **Plan reference**: same plan, sub-task 1.5; `.github/workflows/cursor-usage-monitor.yml`
- **Reason**: The workflow is path-filtered to `extensions/cursor-usage-monitor/**`, but the wire fixtures live at `tests/fixtures/cursor-usage/` because the repo-level pytest contract suite also asserts over them. `liveTransport.test.ts` asserts that the committed fixture and the `CURSOR_WIRE_CONTRACT` constant agree, which is precisely the check that must run when someone corrects the fixture after the HO-5 probe. Today a fixture-only edit runs the Python suite (via `ci.yml`, which lists `tests/plans`) but not the extension suite, so a fixture edited out of step with the constant could merge with the disagreement unasserted. The diff was proposed rather than applied, per the "never silently rewrite CI" rule.
- **Resolution**: approved and applied in the same phase. `tests/fixtures/cursor-usage/**` was added to both the `push` and `pull_request` path lists in `.github/workflows/cursor-usage-monitor.yml`, with a comment recording why the fixtures sit outside the extension directory. Two lines, no new job, no extra cold runner on unrelated changes. Recorded as resolved rather than deleted, because the reasoning is what stops a future reader "tidying" the path back out.

#### Maintainer-only, and NOT closable by an agent

- **Phase 1 exit checklist item "One consent click yields live numbers on a real host"** is unverified. It requires a human in Cursor, and it is gated on HO-5 above. Recorded rather than ticked.
- **QG-5** (v3.15.9 Cursor live visual smoke), **QG-4** (v3.15.8 light/dark/high-contrast smoke), and **MT-5** (v3.15.8 GitHub monitor Extension Development Host activation) are re-stated unchanged. All three need a human observing rendered UI.

#### Deviations from the plan's stated file list (no gap, recorded for accuracy)

- **`src/providers/liveAccess.ts` is new and was not named in the plan.** The credential source and the capability rule were first written inside `extension.ts`, where neither could be asserted without exporting activation internals. They carry the phase's two security invariants (a refusal never reaches the state database; consent is requested only when it could be acted on), so they were moved to a module and are now tested directly.
- **T007 named `usageStore.ts`, and the work landed in three files.** The provenance vocabulary (`snapshotProvenance`, `describeProvenance`) and `clearCache()` are in `usageStore.ts` as planned. The `liveTransportCapable` change is in `extension.ts` and `cursorUsageRuntime.ts`, because that is where the hardcoded `false` actually lived. The runtime dependency widened to `boolean | (() => boolean)` so all 16 existing call sites that pass a boolean still compile.
- **`tests/plans/test_v3_15_9_cursor_usage_contracts.py` was modified.** Its `test_fixture_inventory_is_exact_and_parseable` asserts an exact fixture set, so four new fixtures required adding them. Two assertions were added in the same file to hold the wire fixtures to `verified: false`.
- **`test/vscode-stub.ts` gained an `informationResponses` queue**, mirroring the existing `warningResponses`, so a modal consent choice can be scripted in tests.
- **One existing assertion changed.** `extension.test.ts` asserted the refresh notice contains `HO-5`. That message was deliberately replaced with provenance text, so the assertion now checks that the notice names what is on screen and explicitly does **not** cite an internal gap id.

No Phase 1 missing-test gap remains: every new source file has a dedicated test file, and coverage exceeds every configured threshold.

### v3.15.12 Phase 1 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 1 |
| Hand-offs (HO) | 1 | 0 |

HO-5 is carried forward **narrowed** rather than closed: the plan predicted Phase 1 would close it, and the implementation landed, but the one step that would make the claim true (a live probe of the undocumented route) is maintainer-only. WN-5 is new and open. QG-6 was raised and resolved inside the phase once the CI diff was approved.

### v3.15.12 Phase 2 checkpoint

**Status**: Phase 2 (Cursor usage UI) complete locally. The dashboard now renders three bars, the on-demand bar is currency-against-limit with a payload-derived shared-scope annotation, and percentage precision is unified across dashboard, status bar, and hover. 253 extension tests green; coverage 93.46 statements / 87.29 branches / 97.60 functions / 93.60 lines.

### v3.15.12 Phase 2 Open Items

#### Maintainer-only, and NOT closable by an agent

- **The Phase 2 Stability Gate's "theme-legible in light, dark, and high contrast" is unverified.** The automated surface asserts the structural half of it: the meter track and fill use VS Code theme tokens, `@media(forced-colors:active)` overrides the fill to `Highlight` with a `CanvasText` border, every bar pairs its fill with a numeric label so nothing depends on colour alone, and the new on-demand bar reuses that same CSS. What no agent can verify is the rendered result on a real host in three themes. This is the same class as **QG-4** and **QG-5**, which remain open; the new on-demand bar widens what those smokes need to cover rather than adding a separate item.

#### Contract interpretation, recorded because a reviewer should see it

- **Measuring personal spend against a shared team limit is permitted only with the sharing annotation.** `cursor-usage-data-contract.md` forbids deriving a personal hard cap and forbids `$limit / member_count`, and the v3.15.9 visual contract said Teams spend limits are "never a personal meter". Phase 2's plan nonetheless requires an on-demand bar against its limit. These reconcile: the prohibition is against presenting a shared limit *as if it were personal*, not against showing spend in the context of the pool it draws from. The resolution is that the bar is permitted **only** while it carries an explicit annotation naming the sharing scope, which is asserted by test. The visual contract was amended in this phase to record that rule rather than leaving the document contradicting the code.

#### Deviations from the plan's stated file list (no gap, recorded for accuracy)

- **`src/statusBarManager.ts` was changed and is not in the plan's Phase 2 file list.** T010's requirement that a 1.7% pool stay distinguishable from a 100% pool exposed that plain `Math.round` rendered 1.7% as "2%". Fixing that only in `dashboardPanel.ts` would have made the same pool read `1.7%` in the panel and `2%` in the status bar, so the new `formatPercent` in `formatters.ts` drives all three surfaces. The alternative, a deliberate inconsistency between surfaces, is worse than the out-of-list edit.
- **`docs/v3/v3.15/development/cursor-usage-visual-contract.md` was amended.** Its v3.15.9 text stated on-demand spend "is not a token meter" and is "currency text", which Phase 2 supersedes. The doc now records the third bar, the currency-only labelling rule, the drop-rather-than-approximate cases, the over-limit clamp, and the annotation requirement. `tests/plans` pins the brand pipeline, attribution, hashes, and ASCII in that file, all of which still hold.
- **T010's two included-usage bars already existed** from v3.15.9 with `role="meter"`, the `#4682B4` fill, and per-percent width classes. Phase 2's actual work on them was the precision fix; the new rendering work was T011's on-demand bar.
- **`README.md` gained a paragraph** describing the three bars and the drop/clamp rules, since it already documents the data contract the bars express.

No Phase 2 missing-test gap remains: every changed file is covered by the new `ui.test.ts` block, and coverage rose on every metric relative to Phase 1.

### v3.15.12 Phase 2 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

Phase 2 introduced no new numbered gap. Its one unverifiable item, three-theme visual legibility, folds into the already-open QG-4 / QG-5 smokes rather than becoming a new entry. HO-5 and WN-5 carry forward from Phase 1 unchanged.

### v3.15.12 Phase 3 checkpoint

**Status**: Phase 3 (rename to GitHub Billing Usage) complete locally. Display name, description, all nine command titles, category, configuration and view titles, panel and hover copy, both installers, and the README now read `GitHub Billing`. The extension id is deliberately unchanged. 103 GitHub extension tests green, 14 new installer/manifest tests green, 32 installer-smoke tests green.

### v3.15.12 Phase 3 Open Items

#### Bugs / regressions found and resolved inside the phase

##### BG-11 - RESOLVED: the rename would have failed CI through a suite the phase's own gate did not cover

- **Source phase**: v3.15.12 Phase 3.3 - Tests and stabilization (T020)
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.12-cursor-live-transport-and-github-billing-monitor.md` (sub-task 3.3)
- **Reason**: `catalog/hooks/tests/test_installer_smoke.py` pins both renamed strings: the `USAGE_MONITORS` table asserted the display name `GitHub Usage Monitor`, and `test_github_monitor_status_hint_promises_no_percentage` asserted the literal `GitHub Usage: --` status hint. Neither lives under `tests/`, which is the tree the phase gate runs, so the rename would have gone green locally and failed on the ubuntu runner. Found by grepping `catalog/hooks/tests` for the old strings rather than by the gate.
- **Resolution**: both assertions updated with a comment recording that the folder and id deliberately did not change, and the no-percentage assertion extended to also reject `GitHub Billing: --%` so the renamed prefix cannot smuggle back the false-quota claim it was written to prevent. Suite re-run: 32 passed.
- **Lesson carried forward**: a rename's blast radius is not bounded by the plan's file list. The gate must include `catalog/hooks/tests` whenever installer text changes, because `ci.yml` collects it separately from `tests/`.

#### Deviations from the plan's stated file list (no gap, recorded for accuracy)

- **T017 decided to KEEP the extension id**, which the plan offered as the recommended branch. An id is `publisher.name`, so renaming `name` mints a new extension instead of updating the installed one, leaving anyone who already installed the old id with two extensions both writing a status-bar item. Renaming display surfaces only is non-breaking: an existing install updates in place and keeps its stored token and cached snapshot. Consequence, recorded in the README: searching the Command Palette for "GitHub Usage" no longer matches.
- **T018 / T019 became display-string edits, not uninstall logic.** Because the id is unchanged, no teardown of a superseded id is needed, and the new tests assert that none was added (`uninstall-extension.*github` must not appear). This is the smaller and safer half of the branch the plan described.
- **Six files outside the plan's Phase 3 list were changed.** `catalog/hooks/tests/test_installer_smoke.py` (BG-11 above); the repo-root `README.md` usage-monitor roster; `development/github-usage-data-contract.md` and `development/github-usage-visual-contract.md`, both of which asserted the old title as current fact; and the GitHub extension's `test/ui.test.ts`, which pinned the old status-bar label and settings-panel title. Each was a stale-fact fix required by the rename, not opportunistic editing.
- **Historical records were deliberately NOT rewritten.** The v3.15.8 plan, its three phase histories, the `## What's New in v3.15.8` section of the root README, and the earlier CHANGELOG entries all keep "GitHub Usage Monitor", because they record what shipped under that name at that time. Rewriting them would falsify the record, the same rule applied to the v3.15.11 plan question (PR-1).

#### Carried forward unchanged

- **HO-5** (narrowed: the Cursor wire contract awaits one maintainer probe) and **WN-5** (Node 22.13+ host requirement) from Phase 1.
- **QG-4**, **QG-5**, **MT-5** remain maintainer-only. **MT-5** specifically covers GitHub monitor Extension Development Host activation, so the renamed surfaces are new copy for that smoke to read; the rename is asserted statically but has not been seen rendered in a real VS Code window.

### v3.15.12 Phase 3 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 1 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

One bug found and resolved in-phase (BG-11), and it is the useful result of Phase 3: the rename's blast radius reached a test tree the phase gate did not run, and only a deliberate grep for the old strings caught it before CI would have.

### v3.15.12 Phase 4 pre-work (T022a / T022b) - 2026-08-06

**Status**: the documentary half of T022 is done and the probe harness is committed. **T022c, the empirical half, is maintainer-gated and blocks the rest of Phase 4.** No Phase 4 implementation (T023 onward) has been written, deliberately.

#### Hand-offs

##### HO-6 - The VS Code session premise cannot be settled from documentation, and needs a live probe with a classic-PAT control

- **Source phase**: v3.15.12 Phase 4.1 - T022
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.12-cursor-live-transport-and-github-billing-monitor.md` (sub-task 4.1)
- **Reason**: The plan assumed first-party documentation would answer whether VS Code GitHub sessions are accepted by the billing endpoints. It does not. GitHub's REST endpoint reference says fine-grained PATs work for user and organization billing usage, while GitHub's own "Automating usage reporting" tutorial says the billing usage endpoints do **not** support fine-grained PATs and directs users to a classic PAT. Enterprise is the single documentary negative (fine-grained PATs and GitHub App tokens explicitly rejected). Because the reference's token section is titled "Fine-grained access tokens for...", OAuth's absence from it is **not** a rejection, so no documentary reading can rule the session path out either. That leaves a live probe as the only resolution, and a probe needs a **classic-PAT control** on an account that genuinely holds the role and has enhanced billing enabled, because insufficient role, organization OAuth-app restrictions, and SSO authorization all produce the same `403` / `404` shapes.
- **Suggested next step**: run the probe matrix in `development/github-billing-auth-probe.md` using `src/providers/authProbe.ts`, one `/settings/billing/usage` read per credential class per level, and paste the sanitized records into that document's results table. `toMarkdownRow` emits a paste-ready row. Then T023 implements against recorded evidence rather than an assumption.
- **This is the second maintainer gate in v3.15.12**, alongside HO-5. Both exist for the same reason: a premise that only a real host and a real account can settle.

#### Corrections to premises this plan inherited (recorded so they are not re-derived)

Three assumptions were wrong, and one of them was a wrong decision *rule* rather than a wrong fact. All three are recorded in full in `development/github-billing-auth-probe.md`:

1. **"The endpoint reference's token list settles OAuth support"** - it does not. That section enumerates fine-grained token support only. A rule of the form "session unsupported because the docs do not list OAuth" rejects OAuth on absence of evidence, and would have permanently foreclosed a viable auth path.
2. **"GitHub has no billing-specific OAuth scope"** - `manage_billing:enterprise` exists, subsumed by `admin:enterprise`.
3. **"VS Code's provider filters scopes against a fixed allowlist"** - the current provider forwards caller-supplied scopes into the GitHub login flow. It still cannot mint a fine-grained PAT or GitHub App token through `getSession()`.

Plus one trap that would have silently broken the plan's own "never fall back silently" requirement: **`AuthenticationSession.scopes` reports the scopes the extension REQUESTED, not what GitHub granted.** Granted scopes must be read from the `X-OAuth-Scopes` response header. A narrowed consent would otherwise have read as a full grant.

#### Plan revisions applied

- The Definition of Done's global "session default XOR PAT default" line is struck through and replaced with **per-target capability resolution**: a session is used for a given user / organization / enterprise only after that target and endpoint return `200`.
- T022 is split into T022a (documentary, done), T022b (harness, done), and T022c (maintainer-gated probe).
- T023 / T024 / T026 are reshaped from a single auth default to a three-state per-target capability (`supported` with evidence class, `blocked` with a diagnosed reason, or `unknown`), with explicit no-silent-broadening and no-silent-swap rules.
- The Phase 4 Stability Gate and exit checklist now require that every `supported` verdict trace to a recorded `200`, and that no verdict rest on the endpoint reference's silence about OAuth.

#### Shipped improvement made possible by the finding

- **The extension is now self-diagnosing on permission failures.** `withAuthorizationDiagnosis` attaches `X-Accepted-OAuth-Scopes`, `X-OAuth-Scopes`, `X-Accepted-GitHub-Permissions`, and `X-GitHub-Request-Id` to any failed billing response and appends GitHub's own answer to the message, so a `403` now names the scope the operation would accept instead of only what the extension guessed from the configured scope. This is useful independently of how T022c resolves.
- **The README and data contract no longer present the fine-grained token class as exhaustive.** Classic PAT is documented as a valid class, enterprise is documented as classic-only, and the doc conflict is stated rather than smoothed over.

### v3.15.12 Phase 4 pre-work Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 1 | 0 |

HO-6 is new and open. It is not a defect: it is the honest result of discovering that the question T022 asks cannot be answered from documentation. The alternative, picking whichever documentary reading suited the plan's preferred branch, is precisely the failure mode `auth.ts:99` was written to prevent.

### v3.15.12 VERSION-FINAL RECONCILIATION (Phase 5) - 2026-08-06

**Status**: all five phases complete locally. This is the authoritative open/closed set for v3.15.12.

#### Closed this version

| Item | Disposition |
|---|---|
| **HO-5** | **SUPERSEDED, and its stated conclusion RETRACTED.** This row previously read "CLOSED as a negative... there is no supported surface". That was wrong: it inferred the absence of a surface from its absence in the public documentation. Cursor's own client reads personal usage through `GetCurrentPeriodUsage` on `aiserver.v1.DashboardService`, verified against a live account and shipped in v3.15.13. `CURSOR_WIRE_CONTRACT.verified` is now `true`. See HO-7 |
| **WN-5** | **RESOLVED, favorably.** Cursor's extension host is Electron 40.10.3 / Node 24.15.0 with `node:sqlite` available, well above the 22.13 floor. Answered via `ELECTRON_RUN_AS_NODE`, not by a human reading a panel |
| **BG-11** | Resolved: the rename would have failed CI through `catalog/hooks/tests`, a tree the phase gate did not run |
| **BG-12** | Resolved: both probe runners aborted on exit via `process.exit()` racing `node:sqlite` teardown |
| **BG-13** | Resolved: scope escalation would have requested `admin:org` for a non-scope failure |
| **BG-14** | Resolved: `logIn` / `logOut` were registered with no test driving them, on a stub with no `authentication` surface |
| **QG-6** | Resolved: the Cursor workflow now triggers on `tests/fixtures/cursor-usage/**` |

#### Open at release

| Item | Why it is open |
|---|---|
| **HO-6** | Narrowed to **one command the maintainer runs**. `GitHub Billing: Diagnose Authorization` acquires a session, probes once, and records the verdict. It cannot be closed by an agent: a VS Code session exists only inside the editor, and reading its token from the OS keychain is an explicit non-goal. Until it runs, an unprobed target reports `unknown`, and `unknown` is never treated as `supported` |
| **QG-4 / QG-5 / MT-5** | Maintainer-only interactive smokes. **Scope widened this version**: QG-4/QG-5 now also cover the Cursor on-demand bar (currency labels, shared-scope note, over-limit clamp, dropped-bar fallback), and MT-5 now also covers the renamed GitHub surfaces and the new Authorization panel section |
| **WN-3** | Unchanged. `test_instruction_merge.py` depends on installer-suite import order (v3.15.7). Untouched by this release |
| **DF-14 / DF-16 / DF-17** | Out of scope; carried unchanged |

#### Re-checked

- **WN-4**: `npm audit` reports **0 vulnerabilities** in both usage-monitor extensions. The prior entry recorded transitive `@vscode/vsce` deprecation *notices* alongside a clean audit; the audit remains clean.
- **PR-1**: remains recorded, and **this release did not repeat it.** v3.15.12 had a plan before implementation, and every phase produced a session history. The plan was also corrected in place three times when evidence contradicted it (the breaking-id assumption, the HO-5 closure prediction, and the global auth default), rather than left describing work that did not happen.

#### Advisory, pre-existing, not introduced by this release

`docs/DEVLOG.md` contains 22 non-ASCII characters at lines 2422 and beyond, all in v2.0.0-era historical entries (em-dashes and one `<=` symbol). The repository's Markdown rule is ASCII-only for English. These were **not** introduced by v3.15.12 (its own entries are ASCII-clean, verified) and were left untouched, because they are historical records and fixing them traces to nothing this release asked for. Recorded so a future ASCII sweep has the line numbers.

#### BG-15 - RESOLVED: a guard test failed for anyone who had actually installed the product

- **Source phase**: v3.15.12 Phase 5.5 (final gate)
- **Reason**: `tests/integrations/test_copilot_hermes_native.py::test_global_install_never_touches_the_real_home` asserted the developer's real `~/.copilot/agents` contained **no** `*.agent.md` at all. That conflates "this test wrote here" with "these files exist here". A legitimate global install puts the catalog's 23 agents there, so the assertion failed permanently on a dogfooding maintainer's machine. Corroborated as an installer run rather than a test leak by the shared timestamp window across `~/.nexus-hub/VERSION`, `~/.codex/prompts`, and `~/.copilot/agents`. The test's real guard - that `install_global` routes through the patchable `_copilot_home` accessor - passed throughout, and nothing in v3.15.12 touches the Copilot integration.
- **Resolution**: snapshot `*.agent.md` before `install_global` and assert the set is unchanged after, naming any offending file in the failure message. Same intent, no longer environment-dependent; the 23-file defect it guards would still fail it.
- **Lesson**: a guard that asserts on ambient developer state, rather than on the delta a test causes, becomes a false alarm the moment the product is actually used.

#### Verification posture, stated plainly

Every automated gate is green. What is **not** verified is anything requiring a human at a rendered UI: the three Cursor bars in three themes, the renamed GitHub palette entries and Authorization panel, and the in-editor OAuth verdict. Those are QG-4, QG-5, MT-5, and HO-6. This release does not claim them.

### v3.15.12 Phase 4 checkpoint (T023-T027) - 2026-08-06

**Status**: Phase 4 implementation complete on the HO-6 evidence. Per-target capability resolution, account-identity and verdict display, and a log in / log out pair that structurally cannot end the shared GitHub session. 175 extension tests green.

#### What made this buildable

HO-6's affirmative resolution. The scope candidates are GitHub's own answers rather than guesses: `user` for user scope, and `repo` first for organizations because `repo` **alone** returned `200` on three organizations and VS Code's provider requests it routinely, with `admin:org` held back for an explicit escalation.

#### Design decisions worth carrying forward

- **The log-out isolation guarantee is structural, not documentary.** `sessionBinding.ts` is injected a `MonitorOwnedState` with exactly three members and **no** sign-out, revoke, or `removeSession` member, so `logOutOfMonitor` has no reachable path to the session Copilot shares. A test asserts the injected surface stays that narrow and that the function takes no session provider at all. A comment saying "do not sign out here" would not survive a refactor; a missing capability does.
- **An OAuth success is recorded as `probed-only`, never `documented-and-probed`.** GitHub's endpoint reference enumerates fine-grained support only, so a live `200` is real but undocumented. Promoting it would overstate the evidence in the direction this release has twice had to correct.
- **A `401` is always `credential-invalid`, never `token-type-unsupported`.** That misreading is exactly what the probe's interpretation table exists to prevent, and it is now enforced by the diagnosis function's ordering.
- **Escalation requires evidence.** `nextScopeEscalation` returns null when the credential already carries an accepted scope, because a failure in that state is role, SSO, or app-approval shaped and broader scope cannot fix it. Found by its own test; the first implementation would have requested `admin:org` for a non-scope problem.

#### Bugs found and resolved inside the phase

##### BG-13 - RESOLVED: scope escalation would have requested breadth it did not need

- **Source phase**: v3.15.12 Phase 4.2 (T023)
- **Reason**: `nextScopeEscalation` initially escalated whenever an accepted scope was ungranted. A credential already holding `repo` (which GitHub lists as accepted) that still failed would therefore have triggered a request for `admin:org` - silent broadening for a cause broader scope cannot address.
- **Resolution**: returns null when any accepted scope is already granted, consistent with `diagnoseBlockedReason`, which only reports `insufficient-scope` when none is. Caught by the test written alongside it.

##### BG-14 - RESOLVED: the new commands would have shipped unexercised

- **Source phase**: v3.15.12 Phase 4.3 (T026)
- **Reason**: `logIn` / `logOut` were registered but no test drove them, and the vscode stub had no `authentication` surface at all - so a test that tried would have failed on a missing API rather than on behavior. This is the same defect class as v3.15.11's BG-9/BG-10, where a hook shipped registered and permanently inert.
- **Resolution**: the stub gained `authentication.getSession` with a scripted session queue and a request log; three tests now drive the real handlers through `activate()`, including one asserting log out never calls `getSession` with `createIfNone` or `clearSessionPreference`.

#### Deviation, recorded for accuracy

`tests/installer/test_github_billing_rename.py` pinned the manifest command count at 9; the two new commands make 11. Updated deliberately with a note rather than relaxed to a range, because the exact count is what would catch a dropped command.

#### Still open after Phase 4

- **The `vscode-oauth` leg of T022c is unrun.** A session needs the editor, so per-app authorization and SSO for `GitHub for VS Code` specifically remain unverified; the `gh` result does not transfer. The in-editor diagnostic is the remaining piece, and the code is written so that target simply reports `unknown` until it is probed rather than assuming either answer.
- **Enterprise scope is unprobed** (no enterprise slug on the reference account).
- **MT-5** still applies: none of the new panel copy has been seen rendered in a real VS Code window.

### v3.15.12 Phase 4 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 2 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 1 | 0 |

HO-6 stays open, narrowed to the in-editor OAuth leg. Two bugs found and resolved in-phase, both by tests written alongside the code rather than after it.

### v3.15.12 probe runs - 2026-08-06 (authorized by the maintainer)

Both probes were run. One premise is resolved; the other advanced but is still open.

#### HO-6 - RESOLVED in the affirmative, narrowed to a per-app question

- **OAuth-app tokens ARE accepted by the enhanced billing usage endpoint.** Three organization `200`s (`Tidal-Medical`, `EMVI-AI`, `smesh-stanford`) using a GitHub CLI OAuth token (`gho_`) carrying `gist, read:org, repo, workflow`.
- **GitHub's own `X-Accepted-OAuth-Scopes` names the scopes**: `user` for user scope, `admin:org` or `repo` for organization scope. **`repo` alone sufficed**, and `repo` is a scope VS Code's provider requests routinely.
- **This empirically kills the "billing usage is fine-grained-PAT-only" reading**, and with it the inference that a VS Code session cannot work. An implementation built on that inference would have shipped the wrong default. It is worth stating plainly that the original decision rule proposed for T022 would have reached exactly that wrong conclusion, from the endpoint reference's silence about OAuth.
- **The user-scope `404` was a scope insufficiency, not a class rejection.** The token lacked `user`. GitHub returned `404` rather than `403` for insufficient access, and the accepted-scope header is what disambiguated it. No classic-PAT control was needed: the decision rule requires a control only for a negative verdict, and this is a positive-with-diagnosis.
- **Still open, and narrower than before**: OAuth-app authorization and SSO are per-app, so the `gh` result does not transfer to `GitHub for VS Code`. The remaining question is whether VS Code's provider can obtain `repo` / `user` and is authorized for the target organization. That needs an in-editor leg. Enterprise scope is unprobed (no enterprise slug on this account).
- **Consequence for T023**: the session path can now be designed as the *likely* default with a PAT fallback, per target, instead of being treated as unavailable. No per-organization variation was observed across three organizations, which does not falsify per-target resolution (OAuth-app restrictions are a per-org setting that can differ elsewhere) but does mean the risk was not exercised here.

#### HO-5 - PROBE COMPLETE: the authorized path does not work (supersedes the "advanced, still open" note below)

The full authorized sequence was run on 2026-08-06. Status ladder, all pre-recorded leads:

| Attempt | Result |
|---|---|
| `GET /api/usage-summary` | **401** (twice, before and after opening Cursor) |
| `GET /api/dashboard/get-current-period-usage` | **405** - route exists, wrong verb |
| `POST` same route, empty body (separately authorized) | **403** |

The boundary says stop on `401` / `403` / `429`, so the sequence is closed.

**What is confirmed**: `cursorAuth/accessToken` exists on a real host and holds a valid-shaped token; the read-only one-key adapter works end to end; route B exists and POST is its verb.

**Corrected 2026-08-06: the first version of this entry over-claimed.** `403` means only "understood and refused"; it does not identify the refusal as bearer-token audience rather than a missing CSRF token, absent origin headers, a malformed body, an account entitlement, or a WAF rule. Cursor's documented `401`/`403` semantics apply to `api.cursor.com`, not to a private dashboard endpoint behind possibly different middleware. The defensible record is:

```text
CURSOR_PRIVATE_DASHBOARD_CONTRACT = unsupported
The tested app access token did not produce usage data.
The token's precise audience remains UNPROVEN.
No further private-route, header, or cookie guessing will be performed.
```

**What actually closes HO-5 is the absence of any supported surface, not the 403.** Four checks, all first-party or local:

1. Cursor documents **no personal-account usage API**; its usage/spending APIs are Enterprise-team endpoints needing an explicitly created Admin API key.
2. The Cursor SDK requires an explicit key and **states it does not auto-discover credentials from a local Cursor installation**.
3. **No Cursor-owned authentication provider exists**: of 116 bundled extensions in Cursor 3.14.27, only `github-authentication` and `microsoft-authentication` declare `contributes.authentication`.
4. **No Cursor-owned usage or billing command exists**: zero matches for `usage|billing|spend|quota|credit|subscription|account|plan` across every bundled manifest; the 21 `cursor-*` extensions contribute 8 commands total, none usage-related.

Independently, Cursor's terms restrict reverse engineering, probing or scanning the service, and scraping or extracting data, which is its own reason to stop rather than keep guessing.

**One instrument gap, found and fixed.** The probe captured no response headers, so "POST is route B's verb" was only probable. Adding header capture and re-running returned **`allow: POST`** with `content-type: application/json`, a conforming `405` per RFC 9110. The fix paid for itself on the first re-run, and it is why the `403` is known to be a refusal on the *correct* verb.

`CURSOR_WIRE_CONTRACT` stays `verified: false` by conclusion, and the `CursorAccountApiProvider` seam is retained for a future supported API rather than deleted.

**This affects Definition-of-Done item 1** ("a fresh Cursor install shows real included-usage numbers after exactly one consent click"), which is now known to be unsatisfiable within the plan's own non-goals rather than merely unverified. Items 2, 3, and 4 are unaffected and met.

**What Phase 1 delivered remains sound and worth keeping**: the consent gate, the read-only allowlisted-key adapter with a now-confirmed key name, the fail-closed transport with a fixture-pinned contract, and the degradation path that turns exactly this outcome into an explicit staleness label instead of a wrong number. The phase's defensive design is what makes this a clean negative result rather than a silent misreport.

#### WN-5 - RESOLVED, favorably, and answerable without a human

Cursor's extension host is **Electron 40.10.3 / Node 24.15.0** with `node:sqlite` **available**, well above the 22.13 floor. So the capability check reports `available` and the consent prompt does appear on this host.

Recorded as maintainer-only initially, on the correct observation that the extension host is a different runtime from system Node but the wrong conclusion that only a human could inspect it. `ELECTRON_RUN_AS_NODE=1 Cursor.exe -e "..."` reports the host's Node version and module availability directly. The technique is written up in the probe doc and generalizes to any Electron-based editor.

#### HO-5 - Advanced, still open (SUPERSEDED by the probe-complete entry above)

- **The allowlisted key name is confirmed against a real host.** `cursorAuth/accessToken` exists in `%APPDATA%\Cursor\User\globalStorage\state.vscdb` and holds a value passing the shape rule. The v3.15.9 probe could only verify that the file existed; this verifies the key.
- **The read-only one-key adapter works end to end**: opened, read, released, reached the transport.
- **`GET https://cursor.com/api/usage-summary` returned 401**, so no wire shape was obtained and `CURSOR_WIRE_CONTRACT` remains `verified: false`.
- **The `401` is ambiguous** between a stale session, a wrong header form, and a wrong route. The probe boundary forbids guessing at header variations or neighbouring endpoints, so more attempts do not resolve it. Next step: sign in to Cursor and re-run; if still `401`, one re-run with `--route /api/dashboard/get-current-period-usage`, then stop and record.

#### WN-5 - NOT resolved, and it would be easy to think it was

The probe script reported `node:sqlite` available, but it ran on **system Node v24.13.0**. Cursor's extension host runs its own Electron Node, a different runtime. This run says nothing about the extension host, so WN-5 stays open and is answered only from inside Cursor by observing whether the panel reports the capability available.

#### BG-12 - RESOLVED same session: the probe script aborted instead of exiting

- **Source**: the HO-5 probe runner, first authorized run.
- **Reason**: the script called `process.exit(code)` in its promise chain. Forcing exit while `node:sqlite` and the fetch connection were still tearing down tripped a libuv assertion (`!(handle->flags & UV_HANDLE_CLOSING)`) and replaced the exit code with `0xC0000409`. The probe printed its full result first, so the finding was not lost, but the run *looked* like a crash rather than a clean `401`, and the exit code was unusable for scripting.
- **Resolution**: both probe runners now set `process.exitCode` and let Node drain handles naturally. Verified: the capability-unavailable path now exits `1` cleanly.

#### Instrument change made during the run

`CredentialKind` gained **`gh-oauth`**, tracked separately from `vscode-oauth`, because OAuth-app authorization and SSO grants are per-app and recording a `gh` result as though it came from VS Code's app would have corrupted the evidence. A test asserts the two classes stay distinct through the record, the sanitized form, and the markdown row.

## v3.15.11 - codex notification delivery and the inert-hook regression

### v3.15.11 process deviation (recorded 2026-08-05)

**PR-1 - v3.15.11 shipped without a plan document.** Every other v3.15 release has a plan under `plans/` and a session history under `development/history/`. v3.15.11 has neither at release time. The release itself was authorized (the maintainer said "proceed with `/update release`"), but that standing instruction was carried across a task boundary and treated as covering work that had not been planned: settling DF-15 turned into two bug fixes and a new platform capability, and the work went straight to a tag.

**Disposition.** A session history was backfilled on 2026-08-05 (`2026-08-05_v3.15.11-codex-notification-delivery-backfilled.md`), because a history is legitimately written after the fact. A plan was deliberately **NOT** backfilled: a plan records intent formed before the work, so writing one now and dating it earlier would fabricate a planning record. This is the same rule applied to the 144 un-ticked exit checkboxes in released v3.15 plans and to QG-5.

**Correction to an earlier claim.** The v3.15.10 Phase 4 audit concluded "all v3.15 plans complete". That was true when written and is now incomplete: there is a released version with no plan. The accurate statement is that v3.15.0 through v3.15.10 each have a plan and all are released, and v3.15.11 is released without one.

**Rule to carry forward.** A release authorization covers releasing *planned* work. It does not authorize planning-by-omission for new work discovered mid-task. When a follow-up task turns into feature work or bug fixes, stop and plan rather than continuing to a tag.


**Status**: complete locally. This is a follow-on patch to v3.15.10, cut because settling DF-15 exposed a regression v3.15.10 had already shipped.

### Resolved

- **DF-15 SETTLED, and it was worth settling.** `openai/codex` ships no `docs/hooks.md`, so the event set was verified against the **implementation**: `codex-rs/hooks/src/events/permission_request.rs` is a dedicated module, and the serde wire names in `codex-rs/hooks/src/lib.rs` enumerate the full set. `PermissionRequest` is real and is Codex's "blocked on the human" event, which makes **Codex the only platform besides Claude Code able to express the attention trigger**. Both triggers are now delivered to Codex.
- **BG-9 (NEW, resolved same release): v3.15.10 shipped Codex a permanently inert completion hook.** `notify-on-complete.sh` reached Codex and was registered on `Stop`, but `_notify_common.sh` was not copied. Shared modules are deliberately unregistered in `settings.json` (that is what makes them modules), so the settings-driven script collection never saw it, and the hook sourced nothing and exited silently on every run. `build_hook_entries` now resolves `_`-prefixed sibling modules from the delivered script bodies and copies both shell variants. Asserted by test.
- **BG-10 (NEW, resolved same release): the Notification chain was silently dropped for Codex** as "no Codex event of that name", because no alias mapped it onto `PermissionRequest`. Added `CODEX_EVENT_ALIASES`, applied before the membership test. Asserted by test, including that the alias target actually exists in the verified event set.

Both bugs are the same shape as the inert-hook failure the Phase 3 verification discipline exists to prevent, which is a useful result: the discipline caught them, but only when someone went looking at what a platform actually receives rather than what the catalog registers.

### Still open, unchanged

- **QG-5** (Cursor live visual smoke), **QG-4** (light/dark/high-contrast smoke), **MT-5** (Extension Development Host activation). All three require a human observing rendered UI and **cannot be closed by an agent**. What IS verified this release: the automated surface is green (Cursor extension 132 tests, GitHub extension 103 tests, both packaging in CI). What is NOT verified is the rendered result on a live host. These are recorded as open rather than quietly folded into a passing release.
- **HO-5** (live Cursor transport disabled by design), **WN-4** (upstream `@vscode/vsce` deprecations), **WN-3** (v3.15.7 test import order).
- **DF-14** trigger B still undelivered on Qwen (`Stop`, verified) and Gemini CLI (`AfterAgent`, verified); Kimi's event set still unenumerated. Codex is now removed from DF-14, having been delivered.
- **DF-16** Windows notification linger unmeasured. **DF-17** DF-1 commands residual.
- The 144 un-ticked exit-checklist boxes across six released v3.15 plans, and `session-summary.sh` carrying the same `basename "$(pwd)"` weakness the notification hooks shed.

### v3.15.11 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Deferred (DF) | 3 | 1 |
| Bugs / regressions (BG) | 0 | 2 |
| Warnings (WN) | 2 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 2 | 0 |
| Hand-offs (HO) | 1 | 0 |

---

## v3.15.10 - end-of-task-agent-behavior

**Status**: Phases 1-4 complete locally on `feat/v3.15.10-end-of-task-behavior`. Awaiting `/update release`.

### What this release closed

Three field defects in the notification path, all observed on 2026-08-04:

1. **Notification storms.** `Stop` fires at the end of every conversational turn, so a session driven by background monitors produced a burst of toasts. Closed by moving to two purposeful triggers and asserting `SubagentStop` is never wired.
2. **Meaningless labels.** `basename "$(pwd)"` named whatever directory the hook ran in; one observed toast read `Task complete in work`. Closed by resolving from the git root and including the branch.
3. **An opt-out that could not opt out.** Measured: a User-scope environment variable read back correctly while a freshly spawned child under the running editor read it as empty, because a child process inherits its parent's environment BLOCK rather than the registry. Closed by a switch file stat-ed on every invocation.

Plus **DF-1's skills half**, resolved in Nexus-Hub's favor by first-party documentation, and two PowerShell defects found by the full test tree (see below).

### Open items

#### Hand-offs and by-design (unchanged, carried from earlier versions)

- **HO-5**: live Cursor transport stays disabled until the maintainer authorizes the bounded probe. Intended shipped state, not a defect.
- **WN-4**: transitive `@vscode/vsce` deprecation notices; `npm audit` clean. Upstream-bounded.
- **WN-3**: `test_instruction_merge.py` depends on installer-suite import order (v3.15.7). Untouched by this release.

#### Maintainer-only, and NOT closable by an agent

These require a human at a real IDE and are the reason "all known gaps addressed" cannot be literally true at release time:

- **QG-5** (v3.15.9): the Cursor live visual smoke was not executed. Still open.
- **QG-4** (v3.15.8): interactive light/dark/high-contrast visual smoke.
- **MT-5** (v3.15.8): GitHub monitor Extension Development Host activation coverage.

#### Deferred, introduced by v3.15.10

- **DF-14 - trigger B deferred on four platforms.** Qwen (`Stop`, verified) and Gemini CLI (`AfterAgent`, verified) each need a writer for their own `settings.json` layout plus a test surface; Gemini CLI is additionally enterprise-only opt-in, making it the lowest-value target. Codex (`Stop` likely) and Kimi have event sets that reachable first-party docs never enumerate, so nothing was delivered for them. Deferring is the honest output of a verification-gated phase.
- **DF-15 - Codex `PermissionRequest` unsettled.** Secondary sources describe an event that would make Codex the only platform besides Claude Code able to express "blocked on the human". `openai/codex` has no `docs/hooks.md` and the reachable `docs/config.md` "Lifecycle hooks" section does not enumerate events. Highest-value open item from Phase 3, because the payoff is a genuinely new capability rather than a port.
- **DF-16 - Windows notification linger not shortened.** The 5.5-second post-`ShowBalloonTip` sleep keeps a `powershell.exe` alive per notification. Disposing a `NotifyIcon` early can cancel a queued toast on Windows 10/11, and the shortest safe value requires observing a rendered toast on a live desktop, which no test here can do. Exposed as `NEXUS_NOTIFY_LINGER_MS` to be measured rather than guessed.
- **DF-17 - DF-1 commands residual.** The global `~/.cursor/commands` write is now documented as redundant (Cursor no longer documents a commands directory, Cursor 2.4 migrates commands into skills, and Nexus-Hub already ships each command as a command-skill). Retained deliberately because the risk is asymmetric: writing a directory Cursor ignores is harmless, removing one it does read silently drops coverage. Remove deliberately in a later release.

#### Advisory (pre-existing or out of scope, recorded so they are not lost)

- **The parity guard covers five of twelve substantive templates.** `check_base_template_parity.py` is scoped to the lockstep five by design. `tests/validators/test_end_of_task_rule.py` closes the gap for the end-of-task rule specifically, but a future shared section added to all twelve would drift silently on the other seven. A general "all substantive templates agree" guard is a candidate for a later release.
- **`session-summary.sh` carries the same `basename "$(pwd)"` weakness** the notification hooks just shed, so its project label degrades in exactly the same way. NOT fixed here: it is a different hook with a different purpose, and changing it does not trace to this release's scope. Worth a targeted follow-on.
- **Exit checkboxes are un-ticked in six released plans.** `v3.15.0` through `v3.15.4` and `v3.15.6` carry unchecked exit-checklist items even though all ten of `v3.15.0`-`v3.15.9` are tagged and released. This is a documentation-hygiene artifact, not unfinished work: the release and its tag are the completion evidence. Deliberately NOT mass-ticked, because an exit checkbox is a verification record and ticking it retroactively without re-running the verification would fabricate one. Resolve by re-verifying, or by replacing the boxes with a dated "released" note.
- **Seven empty skill scaffolds remain** under `catalog/skills/` (maintainer work-in-progress). Since v3.15.9 the installers skip any skill directory with no `SKILL.md` and the validator warns about them, so they no longer break anything. Left in place.
- **Pre-existing Ruff findings** (`RUF022`, `ISC004`, `I001`, plus 7 in `test_installer_smoke.py`) untouched, per the v3.15.9 disposition.

### v3.15.10 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 4 | 1 |
| Bugs / regressions (BG) | 0 | 2 |
| Warnings (WN) | 2 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 2 | 0 |
| Hand-offs (HO) | 1 | 0 |

Resolved: DF-1's skills half (overturned in Nexus-Hub's favor by first-party docs) and two PowerShell defects (an intermittent `$LASTEXITCODE` race that degraded the notification label under load, and an assignment to the readonly `$home` automatic variable in the kill switch's default path). Both bugs were user-visible rather than test-only, and both were invisible to the new test file run in isolation.

New this release: DF-14 through DF-17. The three QG/MT items and HO-5 are maintainer or upstream actions, not agent-closable work.

---

## v3.15.9 - cross-provider-routing-and-cursor-usage-monitor

### v3.15.9 Phase 1 checkpoint

Phase 1 replaced the host-locked plan-routing document contract with generic `frontier` / `strong` / `standard` / `fast` tiers, separate `low` / `medium` / `high` / `max` effort, and a required dated Current model map spanning Anthropic, OpenAI, Google, and Cursor. The implementation-plan template, `/plan`, `/implement`, `/route`, the model-routing overview, and repository policy now agree on the split between cross-provider planning and host-native switching. Eight semantic tests enforce the schema, exact fallback markers, four-by-four map, legacy rejection fixture, and related-surface cross-links.

### v3.15.9 Phase 1 Open Items

No Phase 1 deviation, regression, missing-test gap, warning, or quality-gate gap remains. The model-map refresh helpers and bundled fallback snapshot are planned Phase 2 deliverables, not deferred Phase 1 work.

### v3.15.9 Phase 1 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

**Verification boundary.** The focused routing-contract suite passes 8 tests; the complete repository suite passes 1,466 tests with 20 declared skips; Ruff check and format verification pass; skill bundle and routing gates pass; all direct Windows equivalents of `make validate` pass. GNU Make is unavailable on this host, so the canonical wrapper could not execute, but every command in its validate recipe ran successfully. CI already collects `tests/plans` and has path triggering, concurrency cancellation, pip caching, and bounded jobs, so no workflow edit was required.

### v3.15.9 Phase 2 checkpoint

Phase 2 rewrote `model-routing` around separate planning, implementation, and direct-switching modes. The deterministic helper maps five rubric signals to generic tier/effort, validates dated four-by-four provider-map JSON, renders exact fresh/offline/unavailable Markdown grammar, and ships Bash plus PowerShell entry points. The bundled snapshot was refreshed from official Anthropic, OpenAI, Google, and Cursor sources on 2026-08-03. `/plan`, `/implement`, `/route`, and the retained implement-phase runbook now invoke the same scoring, refresh, fallback, reconfirmation, and no-downshift rules.

### v3.15.9 Phase 2 Open Items

No Phase 2 deviation, regression, warning, missing-test gap, or quality-gate bypass remains. The eight untracked empty skill scaffolds already recorded in the v3.15.5 terminal-phase section remain local parallel-session artifacts with zero tracked files; the Hermes layout assertion passed when those empty directories were temporarily isolated and restored.

### v3.15.9 Phase 2 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

**Verification boundary.** The Phase 2 routing tests pass 25 tests with 85% line coverage on `model-map.py`; Bash/PowerShell wrapper and existing switch tests pass 16; the complete hook suite passes 908 with 36 declared skips. The repository suite ran 1,482 passing tests with 20 declared skips plus the local empty-scaffold Hermes assertion described above, which passed isolated after environmental isolation. All five extension suites passed (670 tests and one declared skip); the skill-scanner process required termination only after pytest had printed its complete 89-pass result. Ruff, ShellCheck, PowerShell parsing, skill bundle/quality/routing gates, security scan, compression gate, and every direct Windows equivalent of `make validate` pass. CI already collects both new test files and has path filtering, concurrency cancellation, pip caching, and bounded jobs, so no workflow edit was justified.

### v3.15.9 Phase 3 checkpoint

Phase 3 defines the Cursor usage boundary before runtime code. The data contract separates personal Cursor Models and Other Models pools, preserves source units, keeps on-demand currency separate, and treats Teams spend limits as shared context rather than personal caps. The auth probe records documented CLI/configuration surfaces, bounded cross-OS state candidates, dashboard semantic anchors, and fail-soft source priority without reading a credential. Nine sanitized JSON/HTML fixtures cover healthy pools, on-demand on/off, empty periods, unknown denominators, authentication/visibility errors, and both dashboard routes. The visual contract locks `#4682B4`, preserves official Icons8 480px/48px source bytes with hashes and attribution requirements, and defines the Phase 5 vector/font/package pipeline.

### v3.15.9 Phase 3 Open Items

#### Hand-offs

##### HO-5 - Authorized Cursor session/dashboard probe required before automatic credential reuse

- **Source phase**: v3.15.9 Phase 3.2 - Auth and scrape paths
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.9-cross-provider-routing-and-cursor-usage-monitor.md` (sub-task 3.2 / T015)
- **Reason**: The Windows probe verified that `%APPDATA%\Cursor\User\globalStorage\state.vscdb` exists, but no credential value was opened and no authenticated dashboard request was made because that requires separate explicit authorization. Cursor documents no public personal-usage API, so endpoint/schema success cannot be inferred from path presence.
- **Suggested next step**: Phases 4-6 intentionally ship SecretStorage, injected adapters, UX, and dual-host install without a default live transport. Before a later release enables automatic session reuse, request authorization for the bounded one-key/one-request probe in `cursor-usage-auth-probe.md`; otherwise keep the adapter disabled and preserve the cache/manual UI posture.

No Phase 3 implementation, regression, warning, missing-test, or quality-gate gap remains. Phase 5's normalized SVG/font/package icon and Icons8 attribution notice are planned work, not Phase 3 deferrals.

### v3.15.9 Phase 3 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 1 | 0 |

**Verification boundary.** The Phase 3 contract suite passes 25 tests and the complete plan-contract surface passes 79. The clean-scaffold repository suite passes 1,508 tests with 20 declared skips. Ruff, IDE lint, secret/personal-path scanning, Unicode safety, skill bundle/quality/routing gates, supply-chain and workflow validators, security scan, version/template/profile/platform checks, and compression accuracy all pass. CI already collects `tests/plans` and the new extension/fixture paths make the workflow run on non-doc changes, so no Phase 3 workflow edit is required.

### v3.15.9 Phase 4 checkpoint

Phase 4 scaffolds an independently compilable Node 22 / VS Code 1.85 extension data layer. Strict TypeScript types separate quantities, money, personal pools, shared team context, source provenance, fresh/stale snapshots, provider errors, and store states. The auth broker exposes only callback-scoped SecretStorage credentials and pure path/auth planning; automatic state-database reuse remains disabled under HO-5. Fixture-driven JSON and semantic-HTML normalizers reject unit/schema drift, provider orchestration enforces one JSON attempt plus bounded HTML fallback, and the store validates persisted unknowns before normalized-only cache/manual fallback with reset-aware percentage suppression.

### v3.15.9 Phase 4 Open Items

HO-5 remains open by design and is honored in code: no live credential, state database, browser cookie, or dashboard endpoint is accessed; no default transport claims live compatibility. Phase 6's focused workflow/installer E2E is approved planned scope, not a Phase 4 quality-gate bypass.

#### Warnings

##### WN-4 - Latest VS Code packaging toolchain emits two transitive deprecation notices

- **Source phase**: v3.15.9 Phase 4.1 - Cursor extension scaffold
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.9-cross-provider-routing-and-cursor-usage-monitor.md` (sub-task 4.1 / T020)
- **Reason**: A clean `npm ci` installs the latest `@vscode/vsce` dependency tree and warns that transitive `whatwg-encoding@3.1.1` and `prebuild-install@7.1.3` are deprecated. Neither package is a direct dependency, `npm audit` reports zero vulnerabilities, and replacing them locally would require overriding the supported packaging toolchain.
- **Suggested next step**: Re-run `npm ci` when `@vscode/vsce` updates in Phase 5/6; accept the upstream warning while audit remains clean, and remove this item when the transitive packages disappear.

No new Phase 4 implementation, regression, missing-test, or quality-gate gap remains.

### v3.15.9 Phase 4 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 1 | 0 |

**Verification boundary.** A clean `npm ci` installs 346 packages with zero audit vulnerabilities; TypeScript compilation and all 58 Vitest cases pass. Coverage is 92.12% statements, 87.09% branches, 98.61% functions, and 92.39% lines. The complete plan suite passes 79 tests and the clean-scaffold repository suite passes 1,508 with 20 declared skips. Type-design review is GO at 8/10 encapsulation and 9/10 invariant expression/enforcement/strictness after persisted snapshots, freshness states, provenance, and transport errors were tightened. All direct validation/security gates pass.

### v3.15.9 Phase 5 checkpoint

Phase 5 wires the Cursor Usage Monitor UX shell on top of the Phase 4 data layer. Activation routes through `CursorUsageRuntime` with coalesced refresh, status-bar Cursor Models / Other Models labels (compact C/O mode), Markdown hover with `#4682B4` meter blocks and on-demand/team context, dashboard and standalone settings webviews, threshold evaluation via `alertMetric`, and an activity-bar warning webview that embeds the 48px mark plus Icons8 attribution. Generated assets include `icons/cursor.svg`, `fonts/cursor-icons.woff2` (`U+E103`), transparent `icon.png`, and `THIRD_PARTY_NOTICES.md`. Production still injects no live transport under HO-5.

### v3.15.9 Phase 5 Open Items

HO-5 remains open by design and is honored in the UX path: `liveTransportCapable: false` disables auto-fetch timers; refresh surfaces the boundary while cache/manual data stay visible. WN-4 remains open (transitive `@vscode/vsce` deprecations; audit clean). Interactive light/dark/high-contrast smoke and dual-host installer/CI E2E are Phase 6 scope, not Phase 5 quality-gate bypasses.

No new Phase 5 implementation, regression, missing-test, or quality-gate gap remains.

### v3.15.9 Phase 5 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 1 | 0 |

**Verification boundary.** Extension compile, 132 Vitest cases, and V8 coverage pass at 92.39% statements / 85.85% branches / 96.96% functions / 92.47% lines. `npm run package` and `npm run verify:package` succeed for `cursor-usage-monitor-0.1.0.vsix` (43 archived files; 15 runtime modules). Custom `colors.*` urgency config is intentionally omitted per the visual contract (semantic tokens + text/icon severity). Phase 6 owns installer host isolation and the path-filtered workflow; existing sibling usage-monitor workflows remain the CI pattern to copy.

### v3.15.9 Phase 6 checkpoint

Phase 6 splits usage-monitor installation by host. Both installers resolve the VS Code CLI (`code` / standard VS Code and VSCodium paths) and the Cursor CLI (`cursor` / app-bundle paths) independently, install Claude/Codex/GitHub monitors only through the VS Code CLI, and install `nexus-hub.cursor-usage-monitor` only through the Cursor CLI under an ANYSPHERE vendor header. Cursor is no longer a VS Code-family fallback. A path-filtered Cursor monitor workflow runs Node 22 coverage + package + verify, uploads the VSIX, and either installs into a throwaway Cursor profile or skips-with-note to the live-smoke checklist. Dependabot tracks the extension npm tree.

### v3.15.9 Phase 6 Open Items

HO-5 remains open by design (no live Cursor session/dashboard probe). WN-4 remains open (transitive `@vscode/vsce` deprecations; audit clean). Interactive theme/live smoke still requires a local Cursor host when CI lacks the Cursor CLI - that is the documented E2E degrade, not a quality-gate bypass. Phase 7 reconciles gaps and release readiness.

No new Phase 6 implementation, regression, missing-test, or quality-gate gap remains.

### v3.15.9 Phase 6 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 1 | 0 |

**Verification boundary.** Installer smoke + host-isolation assertions and Cursor workflow policy tests pass (123 combined with related workflow policy suites in the focused run). Extension suite remains 132 green. CI now includes `.github/workflows/cursor-usage-monitor.yml` with path filters, concurrency cancellation, npm caching, SHA-pinned actions, and an honest Cursor-CLI E2E degrade.

### v3.15.9 Phase 7 checkpoint

Phase 7 ran the terminal architecture/known-gaps/CI gate. The structural audit found no tracked empty directory, duplicate group, or orphaned asset introduced by this plan; the one untracked migration remnant (`catalog/skills/code-review/references/`, empty since the v3.15.8 Phase 8 checklist relocation) was removed, and the eight untracked parallel-session skill scaffolds recorded in the v3.15.5 terminal audit were left unmodified. All 11 remaining `Rec. model / effort` occurrences were inspected and are intentional: legacy-compatibility guidance (`model-routing`, `/implement`, the implement-phase runbook, AGENTS.md), the negative fixture in `tests/plans/test_v3_15_9_routing_contract.py`, and historical CHANGELOG/DEVLOG/plan records. No live surface still teaches the deprecated column. CI required no edit: `ci.yml` already collects `tests/plans`, `tests/workflows`, `tests/installer`, and the installer smoke suite, and the Cursor monitor workflow already carries path filters, concurrency cancellation, npm caching, SHA-pinned actions, least-privilege permissions, bounded timeouts, and the honest E2E degrade. README's usage-monitor roster gained the Cursor monitor and the host-isolation contract; CHANGELOG's Unreleased section gained the Phases 3-4 data-layer entry. Two branch-introduced Python files (`model-map.py`, `test_cursor_usage_monitor_workflow.py`) were normalized with `ruff format`; the change is behavior-neutral and their focused suites were re-run green (37 tests).

**Terminal test run correction (2026-08-04).** The claim above that CI required no edit still holds, but the claim that Phase 7 touched no source file does not. The full local suite surfaced one failure, `test_hermes_skills_are_exactly_one_level_deep` (`commit-sweep has no SKILL.md at depth 1`), traced to a genuine contract disagreement rather than to the scaffolds themselves: `flatten_skills` published every `<category>/<name>/` directory (277) while `validate_skills.py --bundles-only` silently skipped the 7 without a `SKILL.md`, so a malformed directory passed every gate and only failed an integration test. Because the scaffolds are untracked empty directories that git cannot represent, a clean CI checkout never reproduced it. Phase 7 fixed the shared adapter (`flatten_skills` and `catalog_skill_names` now require a `SKILL.md`, logging each skip) which corrects Hermes, Cursor, Codex, Antigravity, Qwen, Kimi, and OpenCode simultaneously, and added `find_malformed_skill_dirs` so the validator reports what it used to skip. The validator finding is a WARNING, not an error, so a work-in-progress scaffold still passes CI (the orphan-bundle precedent), and the maintainer's seven scaffolds were preserved rather than deleted. Five tests were added (2 adapter, 3 validator).

**Advisory carried forward (pre-existing, not introduced by v3.15.9).** `_catalog_adapters.py` (RUF022, unsorted `__all__`), `validate_skills.py` (ISC004), and `tests/integrations/test_catalog_adapters.py` (I001, unsorted import block) each carry one pre-existing Ruff finding, and all four files touched by the hardening were already non-`ruff format` conformant at `HEAD`. They were deliberately NOT reformatted: doing so would rewrite hundreds of pre-existing lines and violate scope traceability. Newly added lines were hand-formatted to the `ruff format` shape so the additions themselves are clean. Same disposition as the `test_installer_smoke.py` findings above: left for a hygiene pass outside this release.

### v3.15.9 Phase 7 Open Items (final reconciliation)

The three deliverable gaps this release exists to close are closed: host-locked, staleness-prone plan routing (Phases 1-2), the missing Cursor usage monitor (Phases 3-5), and the installer cross-host install defect (Phase 6). Scrape fragility never materialized as a shipped risk because HO-5 keeps live transport disabled entirely. Remaining items:

#### Hand-offs

HO-5 remains open by design and carries beyond v3.15.9: live Cursor transport stays disabled (cache/manual UI posture) until the maintainer authorizes the bounded one-key/one-request probe recorded in `cursor-usage-auth-probe.md`. This is the intended shipped state, not a defect.

#### Warnings

WN-4 remains open: a clean `npm ci` of the latest `@vscode/vsce` toolchain still emits the two transitive deprecation notices (`whatwg-encoding@3.1.1`, `prebuild-install@7.1.3`); `npm audit` remains at zero vulnerabilities. Re-check on the next `@vscode/vsce` update.

#### Deferred (added during the v3.15.9 release contract re-verification)

> **SUPERSEDED 2026-08-04 by v3.15.10 Phase 3.** The extension recorded below was based on secondary sources and is **withdrawn**. First-party [cursor.com/docs/skills](https://cursor.com/docs/skills) documents `~/.cursor/skills/` and `~/.agents/skills/` as user-level (global) read-paths, with recursive discovery, so the global skills write is correct and load-bearing. The commands half is separately resolved: Cursor no longer documents a commands directory, Cursor 2.4 migrates commands into skills, and Nexus-Hub already delivers each command as a command-skill, so the global commands write is redundant rather than dead-and-load-bearing. See the v3.15.10 Phase 3 entry for the full settlement. The text below is retained as the dated record of what was believed at the time.

**DF-1 is extended, not resolved.** The release-time platform read-contract re-verification found multiple current sources stating that Cursor exposes **no personal/global skills directory**, only the project `.cursor/skills/<name>/SKILL.md` path. DF-1 previously covered only the unverified global `~/.cursor/commands/` read-path; it now also covers the global `~/.cursor/skills/` path Nexus-Hub writes. The evidence is secondary (community and third-party documentation, not an official Cursor doc page), so the global Cursor surfaces are **retained unchanged** rather than removed: writing a directory Cursor may ignore is harmless, while removing one it does read would silently drop coverage. Settle it against first-party Cursor documentation in a v3.15.10 follow-on and then either keep or drop the global writes deliberately. Recorded in `docs/policy/platform-read-contracts.json` (`meta.verified_for_version_note`) and mirrored in the `.md` companion.

#### Advisory (pre-existing, not introduced by v3.15.9)

`catalog/hooks/tests/test_installer_smoke.py` carries 7 Ruff findings that exist identically on `develop`, including three F821 undefined names in its `if __name__ == "__main__"` manual-runner list (they reference tests deleted in an earlier release). Pytest collection and execution are unaffected, so this is dead-path-only. Left for a hygiene pass outside this release's scope rather than fixed here, per the scope-traceability rule.

#### Release-readiness residuals referenced from v3.15.8

MT-5 (GitHub monitor Extension Development Host activation coverage) and QG-4 (interactive light/dark/high-contrast visual smoke) remain open in the v3.15.8 section below; both are consolidated into the maintainer's local release-readiness pass together with this release's Cursor live-smoke checklist (`docs/v3/v3.15/development/cursor-usage-live-smoke.md`). None of them blocks the v3.15.9 integration push.

**QG-5 (NEW, open at release): the Cursor live smoke was NOT executed for v3.15.9.** The checklist at `docs/v3/v3.15/development/cursor-usage-live-smoke.md` requires a human driving a real Cursor instance to confirm the status bar, meters, dashboard, threshold warning, and theme rendering; it cannot be performed by an automated agent and no local Cursor host ran it before the tag. The maintainer authorized the release to proceed without it (2026-08-04). What IS proven for the Cursor monitor is the automated surface: 132 extension tests green with coverage thresholds held, packaging verified in CI, and installer host isolation asserted by test. What is NOT proven is the rendered visual result on a live Cursor host. Close QG-5 by running the checklist post-release and recording the outcome here; treat any finding as a v3.15.10 fix candidate. This entry exists so the release record does not imply a verification that never happened.

### v3.15.9 Phase 7 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 1 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 1 | 0 |
| Hand-offs (HO) | 1 | 0 |

The version-final open set is **HO-5**, **WN-4**, and **QG-5**. HO-5 and WN-4 are by-design or upstream-bounded. QG-5 (Cursor live smoke not executed) is a real, acknowledged verification gap the maintainer accepted to ship past; it is the one item where v3.15.9's evidence is weaker than the plan intended, and it is recorded rather than smoothed over.

One bug was found and resolved inside Phase 7 (BG resolved: the skill-directory contract disagreement between `flatten_skills` and `validate_skills.py --bundles-only`, surfaced by `test_hermes_skills_are_exactly_one_level_deep`). The earlier Phase 7 statement that "Phase 7 introduced no new gap" was written before the terminal test run and is superseded by this table.

## v3.15.0 - platform-parity-all-gaps

**Status**: ALL 7 PHASES COMPLETE / RELEASED (2026-07-23). Phase 1 (capability model + read-contract web re-verification), 2 (Cursor parity), 3 (OpenCode parity), 4 (Qwen + Kimi reclassification), 5 (Copilot skill broadening), 6 (installer checklist + runtime verify parity), and 7 (architecture refactor + known-gaps reconciliation + CI/CD) all COMPLETE.

**Phase 1**: `hooks_supported` is now the single load-bearing hook-capability signal - `SkillsIntegration._mirror_catalog` (base) and `Antigravity20Integration._mirror_surface` (bespoke hooks.json writer) both gate hook installation on it; the change is byte-identical for the live registry (every integration declaring `hooks_subdir` also sets `hooks_supported: True`). The dead `permissions_file` config key (declared on 7 subclasses, never read by any code) was removed; the permission JSON files themselves are installed by a separate mechanism and are untouched. The five parity-target platforms (Cursor, OpenCode, Qwen, Kimi, Copilot) were web re-verified against current official docs (2026-07-20); findings + source URLs + MATCH/DRIFT/UNVERIFIED classifications are recorded in `docs/policy/platform-read-contracts.md` (Re-verification log) and the sibling JSON's `parity_verification_v3_15_0` block. Plan: [plans/v3.15.0-platform-parity-all-gaps.md](plans/v3.15.0-platform-parity-all-gaps.md).

**Phase 2 (Cursor parity) COMPLETE.** The Cursor integration surfaces were already implemented in the branch-untangle commit `a56cdffa` (skills flattened to `.cursor/skills`, subagents to `.cursor/agents`, a `version:1` `hooks.json` with `git-guardrails` gated on `hooks_supported`, project `.cursor/commands/`), with a full 8-test `test_cursor.py`. Phase 2 closed the DF-1 verification gate that `a56cdffa` deferred and completed sub-task 2.3: (1) a 2026-07-21 direct re-read of Cursor's official docs RESOLVED DF-1(b) - the `hooks.json` schema is confirmed and the minimal writer is valid as-is (no code change); (2) DF-1(a) global `~/.cursor/commands/` remains UNVERIFIED (no official doc; community feature-request) - the write is retained per plan 2.3 and tracked as the DF-1 residual; (3) `wire_project_surfaces` now also seeds project `.cursor/commands/` so `nexus-hub init` gives a project the slash surface, not just the rules stub. Tests: `test_cursor.py` 9/9.

**Phase 3 (OpenCode parity) COMPLETE.** **3.1 (agents surface)**: added `agents_subdir: "agents"` to `OpenCodeIntegration.config` - a config-only change, since the base `_mirror_catalog` copies `catalog/agents/*.md` verbatim to `~/.config/opencode/agents/` (global) and `.opencode/agents/` (project). A 2026-07-21 direct re-read of `opencode.ai/docs/agents/` confirmed OpenCode reads `.md` + YAML frontmatter there with `mode` OPTIONAL (default `all`). **3.2 (plugins/hooks)**: OUT OF SCOPE, confirmed - plugins are JavaScript/TypeScript modules loaded by Bun, so Nexus-Hub's shell/py hooks do not translate without a JS/TS wrapper; `hooks_supported` stays `False` (DF-4 resolved as a documented non-gap). **3.3 (tests)**: `tests/integrations/test_opencode.py` (6 tests).

**Phase 4 (Qwen + Kimi reclassification) COMPLETE.** **4.1 (Qwen)**: reclassified `QwenIntegration` to `MarkdownIntegration + SkillsIntegration`; it now delivers flattened skills + agents + **Markdown** commands at `~/.qwen/{skills,agents,commands}` (global, detection-gated) and `.qwen/{skills,agents,commands}` (project), preserving `QWEN.md`. Commands are Markdown, NOT TOML (deprecated in Qwen). **DF-2 resolved**: skills delivered to both scopes (global is the reliable path). **4.2 (Kimi)**: reclassified and FULLY MIGRATED to the current Kimi Code CLI product (`~/.kimi-code/`), delivering AGENTS.md + flattened skills (command-skills reach Kimi as `/skill:<name>`) at `~/.kimi-code/` (global, detection-gated) and `.kimi-code/` (project). The old `~/.kimi/` writes and the `.kimi/agent.yaml` companion are DROPPED. **DF-3 resolved**. **4.3 (tests)**: 41 passed; `verify_platform_contracts` now covers 10 platforms.

**Phase 5 (Copilot skill broadening) COMPLETE.** Widened Copilot's opt-in `.github/skills` seeding from a bare on/off toggle to a SELECTOR (`scripts/lib/integrations/copilot.py`). `NEXUS_HUB_COPILOT_SKILLS` now accepts a bundle id (any of the 15 in `data/bundles.json`) or `all` (the full catalog), with bare-truthy still meaning the default `core-developer` bundle and an unknown id falling back to the default. Kept OFF by default and never-overwrite (a Nexus-Hub policy choice, not a Copilot requirement). Fixed the pre-existing `test_init_subcommand.py::test_default_wire_project_surfaces_returns_none` advisory by adding `copilot` to the test's `overrides` set. DF-5 resolved.

**Phase 6 (installer checklist + runtime verify parity) COMPLETE - confirmation, no production change.** The v3.14.5 summary-driven checklist and the JSON-driven `[verify]` pass are both generic, so the Cursor/OpenCode/Qwen/Kimi surfaces added in Phases 2-4 already flow through both automatically - no installer or runner edit was needed. Locked in with tests: 4 new `_verify_checks` tests in `tests/installer/test_verify_read_paths.py` and a parametrized newly-parity summary test in `tests/integrations/test_install_summary.py`.

**Phase 7 (architecture refactor + known-gaps reconciliation + CI/CD) COMPLETE.** The v3.15.0 cumulative diff introduced no empty dirs, duplicates, or orphans. The substantive work corrected the now-stale AGENTS.md platform-coverage prose (Cursor -> full-surface parity; OpenCode + Qwen Code + Kimi Code CLI moved into a new "Skills-bearing integrations" bullet; guardrails-only is now just Aider / Windsurf / OpenClaw). All deliverable gaps resolved (DF-2/3/4/5); residuals recorded below. CI already covers the release (new integration + verify tests run in the `tests` job; `verify_platform_contracts` + the freshness gate run in `validate`).

### v3.15.0 Release-readiness residuals (open, non-blocking)

- **DF-1(a)** - Cursor global `~/.cursor/commands/` UNVERIFIED (kept, tracked; the confirmed project `.cursor/commands/` is the load-bearing surface).
- **WN-1** - `test_bootstrap.py` fails in the Windows Git-Bash dev env (environmental `tar`); confirmed to be verified green in CI at `/update release`.
- **DF-5 residual** - Copilot's new native custom-agents (`.github/agents/*.agent.md`) + Preview hooks (`.github/hooks/*.json`) surfaces are not yet populated (future release).
- **OpenCode `rules_subdir`** - the contract records "no rules/ folder" yet the integration writes a `rules_subdir`; a pre-existing note flagged in Phase 3 for a future rules-surface review (not a v3.15.0 change).

### v3.15.0 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 4 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 1 | 0 |
| Hand-offs (HO) | 0 | 0 |

### v3.15.0 Advisory (pre-existing test failure) - RESOLVED in Phase 5.2

- `test_init_subcommand.py::test_default_wire_project_surfaces_returns_none` - the test's `overrides` set omitted `copilot`, which has overridden `wire_project_surfaces` since v3.11.0 (it returns a skip-note `WriteResult`, not `None`). It was confirmed PRE-EXISTING. **RESOLVED (Phase 5.2, 2026-07-21)**: added `copilot` to the test's `overrides` set (and removed a pre-existing unused `import pytest`). The test now passes (6/6).

### v3.15.0 Open Items

#### Deferred

##### DF-1 - Cursor global commands path UNVERIFIED (residual; hooks.json schema RESOLVED in Phase 2)

- **Source phase**: v3.15.0 Phase 1.2; actioned in Phase 2 (2026-07-21)
- **Plan reference**: Phase 2 (Cursor parity - skills, hooks.json, agents, project commands)
- **Status**: PARTIALLY RESOLVED. **DF-1(b) hooks.json schema - RESOLVED**: [cursor.com/docs/hooks](https://cursor.com/docs/hooks) confirms `{version:1, hooks:{<event>:[{...}]}}` with the optional fields defaulted, so the integration's minimal `beforeShellExecution -> {command}` writer is schema-valid as-is (no code change). **DF-1(a) global `~/.cursor/commands/` - RESIDUAL (still UNVERIFIED)**: project `.cursor/commands/<name>.md` is officially documented (Cursor 1.6+) and confirmed, but the user-global `~/.cursor/commands/` dir has no reachable official doc and [forum.cursor.com](https://forum.cursor.com/t/personal-custom-slash-commands/133386) reports it as an open feature-request.
- **Decision**: the global write is RETAINED per plan sub-task 2.3 and the contract's negative-only-evidence caution; it is harmless if unread.
- **Suggested next step**: a future cycle with a reachable Cursor commands doc (or an empirical test) should confirm or drop the global `~/.cursor/commands/` write. Not blocking - the confirmed project `.cursor/commands/` surface is the load-bearing path.

##### DF-2 - Qwen skills auto-load reliability (open issue #2343) - RESOLVED (mitigated in Phase 4)

- **Source phase**: v3.15.0 Phase 1.2; resolved Phase 4 (2026-07-21)
- **Status**: RESOLVED (mitigated). A live smoke test on a current Qwen build was not possible, so the mitigation the gap suggested was taken: skills are delivered to BOTH the global `~/.qwen/skills/` (the reliable path) and the project `.qwen/skills/`. The #2343 project-auto-load issue is an open upstream GitHub issue, not documented behavior; the global path covers it.
- **Residual**: none blocking.

##### DF-3 - Kimi current product is `~/.kimi-code/`, not the baseline's deprecated `~/.kimi/` - RESOLVED (Phase 4)

- **Source phase**: v3.15.0 Phase 1.2; resolved Phase 4 (2026-07-21)
- **Status**: RESOLVED. A 2026-07-21 re-read of kimi.com/code/docs confirmed the current product is Kimi Code CLI (`MoonshotAI/kimi-code`, data root `~/.kimi-code/`), separate from the older "Kimi CLI" (`~/.kimi/`).
- **Decision (maintainer)**: FULL migration to `~/.kimi-code/`. The integration writes AGENTS.md + native `~/.kimi-code/skills` at both scopes (global detection-gated on `~/.kimi-code`); the old `~/.kimi/` writes and the `.kimi/agent.yaml` companion are DROPPED.
- **Residual**: a user still on the OLD "Kimi CLI" (`~/.kimi/`) no longer receives a surface (accepted trade-off); pre-existing `~/.kimi/` files are left in place. Not blocking.

##### DF-4 - OpenCode plugins/hooks out of scope (RESOLVED as a documented non-gap in Phase 3.2)

- **Source phase**: v3.15.0 Phase 1.2; resolved Phase 3.2 (2026-07-21)
- **Status**: RESOLVED (decision: out of scope). A 2026-07-21 re-read of [opencode.ai/docs/plugins](https://opencode.ai/docs/plugins) confirmed plugins are JavaScript/TypeScript modules loaded by Bun; a `.sh`/`.py` script cannot be dropped into `plugins/` and run, so Nexus-Hub's shell/py hooks cannot be delivered without a JS/TS wrapper per hook.
- **Decision**: OpenCode hooks are OUT OF SCOPE. `hooks_supported` stays `False`.
- **Suggested next step**: none required. Revisit only if a maintainer wants OpenCode hook parity badly enough to own a JS/TS plugin wrapper.

##### DF-5 - Copilot skill broadening + stale opt-in framing - RESOLVED (Phase 5)

- **Source phase**: v3.15.0 Phase 1.2; resolved Phase 5 (2026-07-21)
- **Status**: RESOLVED. Phase 5 widened `.github/skills` seeding from a bare toggle to a SELECTOR (bundle id or `all`; bare-truthy = default `core-developer`), keeping OFF-by-default + never-overwrite as the commit-visibility policy, and corrected the framing in `copilot.py`'s docstring to state the opt-in is a Nexus-Hub policy, not a Copilot requirement.
- **Residual (out of scope, not blocking)**: Copilot's custom agents (`.github/agents/*.agent.md`) and Preview hooks (`.github/hooks/*.json`) are new native surfaces Nexus-Hub does not yet populate. A candidate for a future release.

#### Warnings

##### WN-1 - `test_bootstrap.py::test_ps_standalone_extracts_and_hands_off` fails in the Windows Git-Bash dev env (pre-existing, environmental)

- **Source phase**: surfaced during v3.15.0 Phase 6's `tests/installer` run (pre-existing, NOT caused by any v3.15.0 phase)
- **Reason**: the standalone-bootstrap test drives `install.ps1`, which shells out to extract the downloaded `main` tarball; on this Windows Git-Bash host `/usr/bin/tar` fails with `unexpected end of file` (a local `tar`-binary quirk, not a code defect). `tests/installer` is otherwise 120 passed / 15 skipped.
- **Suggested next step**: confirm the bootstrap test passes in CI (Linux/macOS `tar`), where this environmental quirk does not apply. Not a release blocker on its own (the core installers `scripts/installer.{sh,ps1}` are unaffected).

#### Quality-gate gaps

##### QG-1 - `make validate` compression-accuracy eval not run in Phase 1 (unrelated to Phase 1 scope)

- **Source phase**: v3.15.0 Phase 1.4
- **Reason**: `make` is unavailable in the dev environment, so the `make validate` steps were run individually. The context-compressor accuracy-regression eval was not run in Phase 1 because Phase 1 does not touch `extensions/nexus-context-compressor`. Every other `make validate` step passed.
- **Suggested next step**: the eval runs in CI and at `/update release`; no action needed unless a later phase touches the compressor.

## v3.15.1 - adoption-codesight

**Status**: ALL 7 PHASES BUILT on `feat/adoption-codesight`. Extension-only, no catalog registry / installer / `base-*.md` changes. Phase 1: a deterministic `.nexus/CONTEXT-MAP.md` + `.nexus/context/` article set compiled from the existing tree-sitter graph, exposed as the `generate_context_map` MCP tool and a `nexus-hub map` one-shot CLI (neutral-path, byte-identical tool/CLI, content-hash no-op). Phase 2: framework-aware route extraction, an env-var audit, and middleware detection/categorization. Phase 3: ORM schema extraction (SQLAlchemy / Django / Prisma), React component extraction, and background-event detection, feeding Data Models / Components / Events sections. Phases 4-6 added hot-file ranking + a git-scoped change map, the token-savings benchmark + map-health lint, and the knowledge-map extractor. Phase 7 completed the terminal refactor, known-gaps reconciliation, reverse-engineering-matrix update, and CI/CD (context-map Action recipe). **Both DoD axes hold** (measured token-reduction + verified extractor accuracy). `GENERATOR_VERSION` reached 4. Full extension suite green (294 passed, 1 pre-existing skip).

### v3.15.1 Open Items

#### Deferred

##### DF-3 - Additional frameworks / ORMs / component libs / event patterns deferred (explicit coverage, not silent)

- **Source phase**: v3.15.1 adoption-codesight Phase 2 (2.1) + Phase 3 (3.1, 3.2)
- **Plan reference**: Phase 2.1 / Phase 3.1 / Phase 3.2 ("verifying each with a fixture before adding the next ... Do NOT attempt every framework at once")
- **Reason**: per the plan's incremental posture, each detector lands with its own fixture rather than all at once. Currently covered:
    - **Routes**: FastAPI, Flask, Django, Express (via the existing resolvers). Deferred: Hono / Fastify / Next / NestJS (TS), Gin (Go), Rails (Ruby), Spring Boot (Java), Laravel (PHP) - each needs a new extraction-time resolver + fixture.
    - **ORM schema**: SQLAlchemy, Django ORM, Prisma. Deferred: TypeORM, Drizzle (TS), ActiveRecord (Ruby), GORM (Go) - decorator/call-based, each needs its own detector + fixture.
    - **Components**: React (props via destructuring or the resolved prop type). Deferred: Vue, Svelte. Design-system-primitive auto-filtering is also deferred.
    - **Events**: declaration-strong signals (Celery task decorators, BullMQ `new Queue/Worker`, Kafka, `new EventEmitter`). Deferred: invocation-only patterns (`.delay(`, `.emit(`, Redis `.publish(`/`.subscribe(`) - too common to detect without false positives.
- **Suggested next step**: add a detector + fixture per additional target in a follow-on pass. The map's section renderers and the accuracy harness already handle any new detector's output generically.

#### Warnings

##### WN-1 - Pre-existing unused `json` import in scripts/nexus_hub_cli.py

- **Source phase**: v3.15.1 adoption-codesight Phase 1 (1.2)
- **Reason**: ruff flags `F401 json imported but unused` in `scripts/nexus_hub_cli.py`. The import is PRE-EXISTING (present on `develop`), not introduced by this phase, and `scripts/` is not ruff-gated in this repo's CI. Left untouched per the no-out-of-scope-cleanup rule.
- **Suggested next step**: remove the unused import as part of a dedicated `scripts/` lint pass.

##### WN-2 - Pre-existing ruff findings in graph/affected.py

- **Source phase**: v3.15.1 adoption-codesight Phase 4 (4.1)
- **Reason**: ruff flags an unused `EdgeKind` import (F401) and an unused `frontier` local (F841) in `graph/affected.py`. Both are PRE-EXISTING; Phase 4 only ADDED `most_imported_files` (ruff-clean). The extension `src/` is not ruff-gated in this repo's CI. Left untouched per the no-out-of-scope-cleanup rule.
- **Suggested next step**: remove both in a dedicated extension lint pass.

#### Missing tests / coverage gaps

##### MT-2 - Benchmark `--update-baseline` write path not automated-tested

- **Source phase**: v3.15.1 adoption-codesight Phase 5 (5.1)
- **Reason**: `measured_baseline()` is unit-tested, but the `benchmark --update-baseline` CLI branch that OVERWRITES the committed `benchmark_baseline.json` is deliberately not exercised (a test that ran it would clobber the committed baseline). The gate path (`--check`), JSON/report output, and `--repo` mode are all tested.
- **Suggested next step**: if desired, test `--update-baseline` against a monkeypatched `BASELINE_PATH` pointing at a temp file. Low value.

##### MT-1 - Repo-level `nexus-hub map` dispatch has no automated test

- **Source phase**: v3.15.1 adoption-codesight Phase 1 (1.2)
- **Reason**: the extension test suite fully covers the map surface (generator, model, tokens, the `generate_context_map` MCP handler, and `nexus_code_search.contextmap.cli`; tool-vs-CLI byte-identity is asserted). The thin dispatch in `scripts/nexus_hub_cli.py` (a 3-line verbatim forward) is verified only by a manual smoke run, not an automated repo-level test.
- **Suggested next step**: add a small repo-level dispatch test asserting `nexus_hub_cli.main(["map", ...])` forwards and returns the extension CLI's exit code.

### v3.15.1 Resolved

##### DF-1 - Overview frameworks line + Most-Imported Files section (RESOLVED)

- Originally Phase 1's placeholder for the Overview `Frameworks:` line and the "Most-Imported Files" section. The frameworks half was resolved in Phase 2; the Most-Imported Files half was resolved in Phase 4 (`most_imported_files` fills the section from inbound import edges, labeled distinct from symbol-level `code_impact`). Both halves shipped and are fixture-tested.

##### DF-2 - nexus-code-search extension package version bump (RESOLVED, Phase 7)

- The extension carries its own package version, independent of the catalog release version. Phase 7 bumped `extensions/nexus-code-search/pyproject.toml` `2.0.0 -> 2.1.0` and refreshed the description to cover the context-map surface. This is NOT a `check_version_sync.py` surface (that guard covers the catalog release version, which `/update release` owns; the QG-2 release hold has since been reconciled by the v3.15.0/v3.15.1/v3.15.2 re-stamp).

##### QG-1 - Duplicate extension-test run across ci.yml and code-search.yml (RESOLVED by decision, Phase 7)

- Decision: RETAIN both. `code-search.yml` (path-filtered, cached, concurrency) is the fast scoped signal on extension changes; the always-on `tests` job in `ci.yml` is the cross-cutting safety gate. The small duplicate on extension-only changes is an intentional coverage-over-minutes trade-off. The benchmark + lint + knowledge tests run in that suite on every extension change; the context-map GitHub Action recipe is documented in the extension README.

##### QG-2 - Three plans stamped v3.15.0 (release-time version reconciliation) (RESOLVED, 2026-07-22)

- Three plans under `docs/v3/v3.15/plans/` were all stamped `v3.15.0` (`platform-parity-all-gaps`, `adoption-codesight`, `adoption-awesome-llm-apps`): the comparison-versioning artifact where plans carry the authoring-cycle version, not the real adoption target. Reconciled by re-stamping the deferred plans: v3.15.0 = platform-parity-all-gaps, v3.15.1 = adoption-codesight (this plan), v3.15.2 = adoption-awesome-llm-apps (and in the v3.16 line, v3.17.0 = model-prompting-research, v3.18.2 = rtk-and-meterless).

### v3.15.1 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 2 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 2 | 0 |
| Missing tests / coverage gaps (MT) | 2 | 0 |
| Quality-gate gaps (QG) | 0 | 2 |
| Hand-offs (HO) | 0 | 0 |

RESOLVED: DF-1 (frameworks line P2 + Most-Imported Files P4), DF-2 (extension version bump P7), QG-1 (CI duplicate-run decision P7), QG-2 (v3.15.0 version collision reconciled by re-stamping, 2026-07-22). OPEN and carried as documented, non-blocking deferrals: DF-3 (deferred detectors - explicit future coverage), WN-1 / WN-2 (pre-existing ruff findings in `scripts/nexus_hub_cli.py` and `graph/affected.py`, in files this plan edited but not introduced by it; a future dedicated lint pass), MT-1 (repo-level `nexus-hub map` dispatch not auto-tested), MT-2 (benchmark `--update-baseline` write path untested).

### v3.15.1 Advisory

- **Definition-of-done measured half VALIDATED (Phase 5)**: the token-savings benchmark measures the compiled map vs a simulated manual-exploration cost. On the committed sample corpus (3 realistic repos) the map saves ~44-55% of exploration tokens (regression-guarded by `benchmark_baseline.json`); on Nexus-Hub itself a ~22k-token map replaces ~1.9M tokens (~99% reduction, 443 files). Combined with the Phase 2-3 zero-FP + recall accuracy harness, both DoD axes hold. The tiny per-framework `contextmap` fixtures are NOT a benchmark corpus - a map is not worth its fixed overhead on a 2-file repo; savings scale with codebase size.
- **Map-health lint ships as extension code, not a new catalog skill (Phase 5.2 decision)**: the deterministic checks (orphan articles, missing backlinks, staleness) live in `contextmap/maphealth.py` (exposed as the `map_health` MCP tool + `nexus-hub map --lint`); the richer semantic checks stay in the LLM-native `documentation-consistency` skill. No `data/` registry files were touched.
- **Knowledge-map extractor ships as extension code, not a new catalog skill (Phase 6.1 decision)**: the mechanical classification + decision / open-question extraction lives in `contextmap/knowledge.py` (exposed as the `generate_knowledge_map` MCP tool + `nexus-hub map --knowledge`); narrative synthesis stays with the LLM-native `solution-knowledge-base` skill. Phases 1-6 remained entirely extension-only.
- **tiktoken is optional, not a dependency**: the token-count header prefers `tiktoken` (cl100k_base) when it is importable and loads without a network fetch, and otherwise falls back to a deterministic stdlib heuristic. The extension adds no dependency on tiktoken, preserving its zero-outbound posture. Token counts differ between an environment with tiktoken cached and one without; within any single environment they are deterministic, so the tool-vs-CLI byte-identity and the token-header self-consistency both hold.
- **`.nexus/` layout for consumers**: the generator writes `<root>/.nexus/CONTEXT-MAP.md` and `<root>/.nexus/context/*.md` (intended to be committed) alongside the pre-existing `<root>/.nexus/code-index/` graph database (gitignored). Consumer-repo `.gitignore` guidance (commit the map, ignore the index) is documented in the extension README.

## v3.15.2 - adoption-awesome-llm-apps

**Status**: IN PROGRESS. Phases 1-5 COMPLETE; Phase 6 pending. This section is appended per-phase and finalized at the v3.15.2 release (Phase 6). Plan: [plans/v3.15.2-adoption-awesome-llm-apps.md](plans/v3.15.2-adoption-awesome-llm-apps.md).

**Phase 1 (catalog-wide trigger-and-routing eval, A1) COMPLETE.** Shipped `scripts/run_trigger_evals.py` (Python stdlib only, model-free): it tokenizes every skill `description`, stems light inflections (ing/es/ed/s), and flags any pair whose trigger vocabulary overlaps at or above a configurable threshold (default 0.5, containment metric `|A n B| / min(|A|, |B|)`). First-run triage over all 267 skills surfaced 39 near-collisions. 38 are by-design category siblings (parallel `<lang>-cleanup` / `<lang>-expert` / `init-<lang>-project` / framework-expert / `*-generation` / mobile-platform / compliance-regulation pairs, plus two matched pairs that already carry mutual SKIP clauses) recorded in `scripts/run_trigger_evals.allowlist.json`; the one genuine collision (the broad `technical-documentation` skill lacked a SKIP clause carving out the single-artifact `architecture-decision-record` and `project-constitution` skills) was FIXED by sharpening `technical-documentation`'s description (and its `data/skills.json` mirror). Registered warning-first in `installer.sh`, `installer.ps1`, the `Makefile` (`make trigger-evals` plus a `make validate` step), and `.github/workflows/ci.yml`. Tests: `tests/validators/test_run_trigger_evals.py` (25 tests, 96% line coverage). Promotion from warning-only to a hard `--gate` is deferred to Phase 6 per the plan.

**Phase 2 (unfilled-placeholder lint, A3) COMPLETE.** Extended `scripts/validate_skills.py` with `validate_placeholders`: it flags unfilled multi-word angle-bracket template placeholders (two or more single-space-separated lowercase words, e.g. `<what this skill does>`) as a HARD ERROR in both the `description` frontmatter field and the SKILL.md body prose. Single-word CLI notation (`<path>`), uppercase template tokens (`<MAJOR>`), and HTML tags are excluded by the tight regex shape, and fenced code blocks + inline-code spans are skipped (CommonMark-aware fence tracking mirrored from the secret scanner). The check runs inside the `--bundles-only` mode that `make validate` and CI already invoke, so NO new CI job was added. First run over all 267 skills produced ZERO findings (no genuine scaffolds, no false positives), so no SKILL.md fix was needed. Tests: 14 cases added to `tests/validators/test_validate_skills.py` (description hit, body hit, CLI-notation / HTML / uppercase-token / comparison-operator negatives, fenced + inline-code + backticked-description exemptions, nested-fence guard, `_body_after_frontmatter`, and two `--bundles-only` CLI tests) - new-code line coverage 100% in-process. AGENTS.md documents the new lint alongside the orphan-bundle detection block.

**Phase 3 (per-skill trigger-cases + routing assertions, A2) COMPLETE.** Extended `scripts/run_trigger_evals.py` to consume optional `catalog/skills/<cat>/<name>/evals/trigger-cases.json` files and assert lexical routing: (a) each `should_trigger: true` prompt must rank its own skill first among all skills (else it names the mis-routed-to skill), and (b) within a skill's cases the weakest positive must clear the strongest near-miss negative by a configurable `--margin` (default 1.15x). `lexical: false` cases are skipped (left for behavioral evals); skills without a file emit a WARN (never a FAIL), so the catalog never blocks on incomplete coverage. The schema and `evals/` convention are documented in AGENTS.md; the orphan-bundle audit is reconciled (a code comment on `BUNDLED_SUBDIRS` records that `evals/` is intentionally excluded because it is runner-consumed, not SKILL.md-referenced). First tranche authored for 6 distinctive-noun skills (react-expert, vue-expert, gdpr-compliance, ccpa-compliance, kubernetes-expert, docx-generation), chosen from the Phase 1 near-collision pairs plus a high-value standalone; all 36 lexical cases pass (0 routing failures). One vue near-miss was retuned to lean on react-distinctive vocabulary after the margin check correctly flagged that generic component/state words did not separate vue from react - the eval working as intended. Tests: routing cases added to `tests/validators/test_run_trigger_evals.py` (rank-first pass, misroute, margin-fail, lexical-false skip, malformed file, no-cases WARN, JSON routing block, real-catalog tranche) - runner line coverage 95%. No CI edit needed (the extended eval is the same warning-only step; new tests run via the existing `pytest tests/validators` step).

**Phase 4 (behavioral-eval schema interop, A4) COMPLETE.** Decision: ship an ADAPTER, not a native re-alignment. The eval-loop's internal `evals.json` is a strict superset of the interoperable behavioral-eval schema `{skill_name, evals:[{id, prompt, expected_output, expectations[]}]}` - it carries `should_trigger` (trigger-rate metric), `turns`/`trigger_turn` (multi-turn), `model` (cheap-model fragility), and `tags`, none of which the interoperable schema can express - so adopting it natively would drop capabilities and force a rewrite of the grader/aggregator/optimizer/viewer. Instead shipped `scripts/skill_eval_convert.py`, a stdlib-only bidirectional converter (`--to-interop` / `--to-internal`) that maps `query`<->`prompt` and `assertions[].text`<->`expectations[]`, preserving `expected_output` verbatim and stashing every internal-only field under an `x_nexus` extension key so BOTH round-trips are lossless (`internal->interop->internal == internal`, `interop->internal->interop == interop`). Behavior preserved by construction: the grading path (internal format + grader/aggregator/optimizer/viewer) is unchanged; there was no committed sample `evals.json` to migrate. Registered in both installers (sibling of the other eval-loop scripts); documented in `references/schemas.md` (interop section + decision rationale) and referenced from the skill's SKILL.md. Tests: `tests/validators/test_skill_eval_convert.py` (18 cases: field mapping, both lossless round-trips, extension-namespace behavior, error handling, and CLI + in-process main surfaces) - converter line coverage 96%.

**Phase 5 (Hermes roster + shared `.agents/skills/`, A5) COMPLETE.** Added `scripts/lib/integrations/hermes.py` as a `SkillsIntegration` (skills-native: reads folder-per-skill `SKILL.md` directly, so NO instruction file and NO `base-hermes.md` - a `SkillsIntegration`, not a `MarkdownIntegration`), registered in `_register_builtins()`. It writes flattened skills to `~/.hermes/skills/` (global, detection-gated on `~/.hermes`) and `.hermes/skills/` (project), each catalog command also surfacing as a skill. Per the shared-path ownership rule Kimi follows, Hermes READS but does not WRITE the shared `~/.agents/skills/` (owned by `codex`) or the project `.agents/skills/` (seeded by `antigravity2`'s `wire_project_surfaces` on `nexus-hub init`), avoiding a teardown conflict. The shared-project `.agents/skills/` path is therefore CONFIRMED present (`cmd_init` walks every integration's `wire_project_surfaces`, and `antigravity2` seeds `.agents/skills/`), not newly added. Documented in `docs/policy/platform-read-contracts.md` (surface-table rows + a Hermes section) and the AGENTS.md platform-coverage section. Tests: `tests/integrations/test_hermes.py` (6 cases) + the parameterized `test_contract.py` (hermes: 4 passed, 1 skipped) + a runner dry-run confirming `.hermes/skills/` and zero disk writes. No `base-*.md`, catalog-registry, or hook change; `verify_platform_contracts` stays green (Hermes intentionally not in `contract_checks`, see DF-2).

**Phase 6 (architecture refactor + known-gaps reconciliation + CI/CD) COMPLETE (release HELD).** **6.1 refactor**: audited this plan's cumulative diff (2584 insertions across 33 files) - all additions are cohesive and correctly placed (repo scripts under `scripts/` referenced in both installers + Makefile + CI; the `hermes` integration under `scripts/lib/integrations/` registered in `_register_builtins()`; per-skill `evals/trigger-cases.json` consumed by the runner; tests under `tests/validators` + `tests/integrations`). No empty dirs, duplicates, orphans, or overcomplicated structure - a no-op cleanup. Docs-tree refactoring (`docs-layout-refactor`) was DEFERRED because a parallel task is actively re-stamping `docs/v3/v3.16` -> `docs/v3/v3.15` plans/comparisons; running it now would collide (see the release hold below). **6.2 known-gaps**: this reconciliation (DF-1 resolved by the CI-review decision; DF-2 / WN-1 / MT-1 carried as documented non-blocking deferrals; MT-1 - the trigger-cases WARN-path coverage - is the explicit item the next release picks up). **6.3 CI/CD**: promoted the trigger-and-routing eval from warning-only to a HARD `--gate` in both `.github/workflows/ci.yml` and the Makefile `validate` step (catalog is clean: 0 un-allowlisted collisions, 0 routing failures); confirmed CI covers every plan change (A1/A2 via the `--gate` step, A3 inside `validate_skills.py --bundles-only`, A4 via `pytest tests/validators`, A5 via `pytest tests/integrations`) with no new/redundant job and the existing concurrency + caching + gated-matrix optimizations intact. **6.4 verification**: validators + `tests/validators` (302) + `tests/integrations` (398) green; `--gate` passes; dry-run install lands `.hermes/skills/`. RELEASE HELD - the release-readiness sub-phases (9A/9B) ran, but 9C-9E (`/update release`: version bump / changelog / develop->main merge / tag / GitHub Release) is NOT run pending the active-parallel-re-stamp reconciliation, the unpushed branch, and the in-flux v3.15.x version numbering (see the release-hold note below).

### v3.15.2 Open Items

#### Deferred

##### DF-2 - Hermes not yet first-class installer-wired (registry-only)

- **Source phase**: v3.15.2 Phase 5.1 / 5.2.
- **Plan reference**: Phase 5.1 ("no installer copy-step edit is needed because the runner is invoked automatically").
- **Reason**: `hermes` is registered in `_register_builtins()` and installable on demand via `runner.py install --integrations hermes` (detection-gated), but the installers drive extended platforms through explicit `should_install <key>` / `invoke_registry_platform` blocks + a `known_platform_keys` list, and Hermes is intentionally NOT added to those yet (nor to the JSON `contract_checks`, which would then REQUIRE the installer reference and fail `verify_platform_contracts`). Editing the installers is an AGENTS.md "ask first" action and outside this phase's stated scope. Hermes therefore sits in the same tier as aider/windsurf/openclaw: registered + documented + runner-installable.
- **Suggested next step**: if Hermes adoption warrants it, promote it to a default-installed platform in a follow-on - add `should_install hermes` / `invoke_registry_platform` blocks to both installers, add `hermes` to `known_platform_keys`, and add a `contract_checks` entry (with the required installer reference).

#### Warnings

##### WN-1 - Windows-local dry-run install of the new copy block not executed

- **Source phase**: v3.15.2 Phase 1.4.
- **Plan reference**: Phase 1.4 ("do a dry-run install into a throwaway directory and confirm the script lands at `~/.nexus-hub/scripts/`").
- **Reason**: the bash installer cannot fully run on the Windows dev host (WN-v36-1). The new copy block mirrors the `generate_report.py` pattern exactly, is shellcheck-clean, and targets `$scripts_dest` (which resolves to `~/.nexus-hub/scripts`).
- **Suggested next step**: none required - CI's `bootstrap` and `install-smoke` jobs exercise the installer end-to-end on ubuntu / macOS / Windows.

#### Missing tests / coverage gaps

##### MT-1 - trigger-cases.json routing coverage is a first tranche (6/267 skills)

- **Source phase**: v3.15.2 Phase 3.3.
- **Plan reference**: Phase 3.3 ("leave the rest of the catalog on the WARN path for incremental authoring in later releases") and Phase 6.2 ("Explicitly record the deferred incremental work ... skills still on the WARN path").
- **Reason**: routing cases were authored for 6 distinctive-noun skills; the remaining 261 skills have no `evals/trigger-cases.json` and are on the WARN path (never fails the gate). This is by design - lexical routing cases are only meaningful for skills with distinctive description vocabulary, and command-dispatcher skills (`/plan`, `/implement`, `/review`, `/compare`, `/update`) lexically overlap their sub-skills, so they need `lexical: false` reasoning-routed cases (deferred).
- **Suggested next step**: author further tranches incrementally in later releases; for the command dispatchers, add `lexical: false` cases covered by behavioral evals (ties into Phase 4 schema interop).

### v3.15.2 Resolved

##### DF-1 - CI per-path-filter granularity for the trigger-eval step - RESOLVED (Phase 6.3 CI review, by decision)

- **Source phase**: v3.15.2 Phase 1.5; closed in Phase 6.3.
- **Resolution**: the Phase 6.3 CI review confirmed the design decision - the eval is a sub-second stdlib step that rides the existing single `validate` job (which already has `concurrency` cancel-in-progress, pip caching, and cost-gated macOS/Windows matrix legs). Splitting it into a separately-path-filtered job would ADD checkout + setup minutes, defeating the stated optimization goal, so no per-path-filter granularity is added. Closed as a non-gap by decision (mirrors the v3.15.1 QG-1 CI-dedup resolution pattern).

### v3.15.2 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 1 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

RESOLVED: DF-1 (CI per-path-filter granularity, closed by the Phase 6.3 CI-review decision). OPEN and carried as documented, non-blocking deferrals: DF-2 (Hermes registry-only, not yet default-installer-wired), WN-1 (Windows-local dry-run not run; CI is authoritative), MT-1 (trigger-cases WARN-path coverage - the explicit item the next release picks up).

### v3.15.2 Release hold (Phase 6, release-readiness 9C-9E)

The final phase's `/update release` hand-off (version bump / changelog / develop->main merge / tag / push / GitHub Release) is HELD. Active hold conditions at Phase 6 completion:

1. **Active parallel re-stamp in the working tree** - a concurrent task is renumbering `docs/v3/v3.16/{plans,comparisons}/*` into the `docs/v3/v3.15/` line (v3.15.3 / v3.15.4 / v3.15.5 / v3.15.6 plans + comparisons appearing, v3.16.x files deleted/renamed). These are uncommitted and NOT part of this plan; the Phase 1-6 commits deliberately excluded them via surgical staging. A release must not run over a half-reorganized docs tree.
2. **In-flux version numbering** - with v3.15.3-.6 being created from former v3.16.x plans, whether v3.15.2 is still the correct release stamp for this plan needs user confirmation (the comparison-versioning-flaw pattern).
3. **Unpushed branch** - `feat/adoption-awesome-llm-apps` (Phases 1-6) is local-only; nothing is pushed.

Resolution path (user-owned): reconcile the parallel re-stamp, confirm the version stamp, push the branch, then run `/update release` for whichever version this plan ships as (it re-verifies the platform contract, bumps every version surface via `check_version_sync`, finalizes the changelog, merges develop->main, tags, and publishes the GitHub Release under its own gates).

## v3.15.3 - adoption-no-ai-slop

**Status**: ALL 3 PHASES COMPLETE / RELEASED (2026-07-24). This section is finalized. Plan: [plans/v3.15.3-adoption-no-ai-slop.md](plans/v3.15.3-adoption-no-ai-slop.md).

**Phase 1 (author the anti-slop-editing skill and bundle) COMPLETE.** Authored a new `catalog/skills/developer-experience/anti-slop-editing/` bundle: `SKILL.md` (dual Edit/Detect mode, a 17-entry named-slop-pattern catalog each with a quoted smell + a concrete before/after fix, voice-preservation discipline, a wired self-check loop, Common Rationalizations, and a binary Verification section), `references/slop-wordlist.md` (banned words + often-empty adverbs + empty phrases, framed as judgment guidance not a hard lint), `references/self-check.md` (a pass/fail content-quality rubric the skill grades its own output against before returning), and `evals/trigger-cases.json` (4 positives + 4 near-miss negatives drawn from the SKIP clause). The single-line `description` was lexically co-engineered with the eval prompts so the routing gate ranks `anti-slop-editing` first on every positive and clears the 1.15x near-miss margin, and so it collides with no sibling description. Per the reverse-engineering attribution rule, no external repository, product, author, or course is named anywhere in the shipped bundle. Gates green: full `validate_skills.py` on the skill PASS (0 errors, 0 warnings); whole-tree `--bundles-only` PASS (this skill clean; see the Advisory below for the one pre-existing warning); `run_trigger_evals.py --gate` PASS (0 un-allowlisted collisions, 0 routing failures across 7 skills with cases). CI already covers the skill's validation with no edit (the new bundle flows through the existing `--bundles-only` + `--gate` + skill-security steps under the optimized `validate` job). Registration in the three `data/` files, the reverse-engineering-matrix row, and the CHANGELOG entry are Phase 2 work.

**Phase 2 (register and record provenance) COMPLETE.** Registered `anti-slop-editing` by hand in the three registry files (no full catalog rebuild): a row in `data/SKILL_INDEX.md`, a full entry in `data/skills.json` (matching the sibling schema, `summary_l0`/`overview_l1` wrapped in the literal-quote convention, `description` unwrapped), and the developer-experience `skill_count` bumped 31 -> 32 in `data/marketplace.json`. Catalog now consistently reports **268 skills** across `skills.json` (268 entries), the marketplace category-sum (268), and `SKILL_INDEX.md`. Added a `skill-native` row to `docs/policy/mcp-reverse-engineering-matrix.md` recording the MIT external source (named ONLY in the matrix, never in the shipped skill body, per the Reverse-Engineering Attribution Rule) and confirming zero outbound call / API key / dependency / data processor / new commercial relationship. Added a `## [Unreleased]` section to `CHANGELOG.md` (Added: the skill; note the 268-skill count; no version-surface bump). Gates green: JSON integrity (all 5 catalog files parse), `check_version_sync` still matches 3.15.2 (no version numbers touched; the `[Unreleased]` heading is correctly ignored by the extractor), `run_trigger_evals.py --gate` still PASS (the routing gate reads SKILL.md, not skills.json, so the mirror add is inert to it), and the skill validator still PASS. The README / AGENTS.md prose skill-count ("267 skills") is intentionally NOT bumped here; `/update release` owns the count-surface reconciliation at release time (Phase 3 hands off to it).

**Phase 3 (terminal refactor + known-gaps reconciliation + CI/CD) COMPLETE.** **3.1 refactor** ([[project-refactor]] + [[docs-layout-refactor]]): a verification pass, near-no-op as expected for a skill-only plan. The cumulative plan diff (`develop..HEAD`) is exactly 13 cohesive files - the 4-file skill bundle (standard `SKILL.md` + `references/` + `evals/` layout, no empty dirs, no orphans, no stray files), the 3 `data/` registry files, and the docs (CHANGELOG, matrix row, DEVLOG, known-gaps, 2 session-history files, all correctly placed under `docs/v3/v3.15/`). Nothing to move or delete. **3.2 known-gaps**: this reconciliation - NI-1 kept as a documented non-blocking deferral; DF-1 (below) records the one deferred follow-up; the three advisories carried for `/update release`. **3.3 CI/CD**: confirmed the existing `.github/workflows/ci.yml` already covers every change with no edit - skill validation (`validate_skills.py --bundles-only`), trigger + routing (`run_trigger_evals.py --gate`), and registry integrity (the `skills.json` / `bundles.json` / `workflows.json` JSON-parse steps) all run under the single `validate` job, which is already optimized (workflow-level `paths-ignore: docs/**` so `catalog/**` + `data/**` + `scripts/**` changes trigger it, `concurrency` cancel-in-progress, pip caching, and cost-gated macOS/Windows matrix legs on the bootstrap / install-smoke jobs). A separately-path-filtered job for this sub-second work would only add checkout + setup minutes (the same decision recorded at v3.15.1 QG-1 and v3.15.2 DF-1). **3.4 validation**: `validate_skills.py` (skill + whole-tree `--bundles-only`), `run_trigger_evals.py --gate`, `check_version_sync`, and the catalog JSON-integrity checks all green; no behavior changed (verification-only refactor). `make` is unavailable on this Windows host, so the steps ran individually; CI is the authoritative full-suite gate. **Release hand-off**: the version bump, changelog finalization, and the count-surface reconciliation (README / AGENTS.md / `plugin.description` to 268) are handed to `/update release`; no tag / merge / push performed by this phase.

### v3.15.3 Open Items

#### Deferred

##### DF-1 - promote the self-check eval-loop pattern into a reusable authoring convention

- **Source phase**: v3.15.3 Phase 3.2 (deferred follow-up).
- **Plan reference**: Phase 3.2 ("Record any deferred anti-slop follow-ups, for example promoting the self-check eval pattern into a reusable authoring convention").
- **Reason**: `anti-slop-editing` ships a runtime self-check loop (the skill grades its own output against `references/self-check.md`, fixes, and re-checks before returning). This is a genuinely reusable authoring pattern - a skill that produces content could ship a rubric and self-grade against it - but generalizing it (a shared convention documented in AGENTS.md, or a `references/self-check.md` template other skills adopt) is out of scope for this single-skill plan.
- **Suggested next step**: in a future cycle, evaluate promoting the self-check-loop pattern into an authoring convention (AGENTS.md guidance + an optional shared rubric template), so other content-producing skills can adopt it. Non-blocking; the pattern works today inside `anti-slop-editing`.

#### Not implemented

##### NI-1 - description carries 3 of the 5 plan-listed trigger phrases verbatim (250-char ceiling; mitigated)

- **Source phase**: v3.15.3 Phase 1.1.
- **Plan reference**: Phase 1.1 (description trigger phrases: "make this less AI-sounding", "does this read as AI", "de-slop this", "remove AI patterns", "audit this draft for slop").
- **Reason**: the single-line `description` is capped at 250 chars (the `validate_skills.py` I-03 rule). The three phrases that also carry the strongest lexical routing signal ("de-slop this", "make it less AI-sounding", "does this read as AI") are in the description verbatim; the other two ("remove AI patterns", "audit this draft for slop") are covered by `overview_l1` and the "When to Use This Skill" section, which the agent reads at trigger time. Routing is proven by the passing trigger-eval `--gate`, so discoverability is not degraded.
- **Suggested next step**: none required. If the 250-char budget frees up (for example via a shorter SKIP phrasing), fold one more phrase into the description. Non-blocking.

### v3.15.3 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 1 | 0 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

OPEN and carried as documented, non-blocking deferrals: NI-1 (description carries 3 of 5 plan-listed trigger phrases verbatim under the 250-char cap; routing proven by the `--gate`), DF-1 (promote the self-check eval-loop pattern into a reusable authoring convention in a future cycle). No release blocker.

### v3.15.3 Release readiness (Phase 3, release-readiness 9A/9B)

- **9A resolve known gaps**: re-read the Open Items above; grepped the plan's added files for `TODO`/`FIXME`/`XXX`/`HACK`/`# DEVIATION:` - none (the bundle is prose; the only "TODO"-like strings are absent). NI-1 and DF-1 are out-of-scope-to-fix-now, documented deferrals. No release blocker remains.
- **9B verify tests + CI**: no new code module ships (prose skill), so no unit test is owed; the validation surface (`evals/trigger-cases.json` + the validators) is green, and CI covers `catalog/skills/**` + `data/**` through the `validate` job. No missing tests.
- **9C-9E hand-off**: handed to `/update release` (version bump 3.15.2 -> 3.15.3 across every `check_version_sync` surface, changelog finalization, the 268-skill count reconciliation in README / AGENTS.md / `plugin.description`, then commit / merge develop -> main / tag / GitHub Release under its own gates). This phase performed no tag, merge, or push.

### v3.15.3 Advisory (pre-existing, not introduced by this plan)

- The whole-tree bundle audit reports one orphan: `catalog/skills/workflow/demo-capture/scripts/__pycache__/capture-demo.cpython-312.pyc` (a compiled-bytecode artifact). It is PRE-EXISTING (not created by this plan), lives in a different skill, and is a warning, never an error. Left untouched per the no-out-of-scope-cleanup rule; a future `demo-capture` touch or a `.gitignore` / clean pass should remove the stray `.pyc`.
- **`marketplace.json` `statistics.total_skills` does not exist** (Phase 2 reconciliation): the plan's sub-task 2.1 said to "increment ... `statistics.total_skills`", but the current `marketplace.json` schema has an empty `statistics: {}` block and derives the catalog total from the sum of `categories[].skill_count`. Registration therefore only bumped the developer-experience `skill_count` (31 -> 32), which keeps the derived total (268) consistent with `skills.json`. No `statistics.total_skills` field was invented (that would risk breaking schema consumers). Non-blocking; the derived total is correct.
- **`marketplace.json` `plugin.description` skill count is stale** ("265 curated skills"): PRE-EXISTING drift (it already read 265 while the catalog held 267), not introduced by this plan and not made worse by it. It is a marketing-prose count, not a `check_version_sync` surface. Left untouched per the no-out-of-scope-cleanup rule; `/update release` should reconcile it (along with the README / AGENTS.md "267 skills" prose) to 268 at release time.

## v3.15.4 - presentify-visual-fidelity

**Status**: ALL 7 PHASES COMPLETE (release-ready). This section is finalized; the version ships when the maintainer runs `/update release` (the branch `feat/presentify-visual-fidelity` is unpushed and not yet merged to `develop`). Plan: [plans/v3.15.4-presentify-visual-fidelity.md](plans/v3.15.4-presentify-visual-fidelity.md).

> **Prior-version ingest**: checked this file (docs/v3/v3.15/known-gaps.md). The open v3.15.0-.3 items are unrelated to presentify visual fidelity and do not carry in. The v3.15.2/.3 `__pycache__` `.pyc` advisory recurs (a transient, gitignored bytecode artifact); see the v3.15.4 Advisory.

**Phase 1 (full-width canvas contract) COMPLETE.** Made "full-width" a concrete, measurable edge-to-edge canvas across both the LLM-native authoring path and the deterministic baseline builder. **1.1**: replaced the prose "Full-width" bullet in `references/interactive-features.md` ("Output aspect (the canvas)") with an enforceable contract (page shell spans the viewport via named `--gutter` tokens not a centered `max-width` column; full-bleed top-level bands; the 45-85ch `--measure` scoped per prose element only; and a success metric - the widest top-level content band reaches at least ~95% of a 1920px viewport with no global zoom) plus a "failure to avoid" note. **1.2**: tightened SKILL.md Step 6 (the "Use the viewport width on purpose" and "Spacing, density, and aspect" bullets) to cite the contract by name and state the binary full-width rule, and added a distinct Common Rationalizations row rebutting the full-width centered-column retreat. **1.3**: added `--layout {full|standard|portrait}` (default standard) to `build_presentation.py`, which injects a `--page-max`/`--gutter` pair into a new `NEXUS_ASPECT` marker block and stamps `data-aspect` on the root `<html>`; the template (`assets/presentation-template.html`) now drives the canvas from those vars (`--slide-max` -> `--page-max`, `.slide` padding -> `--gutter`), keeps `--measure` scoped to prose only, widens a full-width chart to its band, and gates the projector-padding widening to non-full aspects. `standard` reproduces the historical centered column; `full` is edge-to-edge (page-max 100%, small gutters, ~96.7% band at 1920px); `portrait` is a 46rem reading column. **1.4**: `tests/skills/test_presentify_layout.py` (11 pass / 1 skip) asserts the injected vars + `data-aspect` per layout, offline-cleanliness, head integrity, and a browser-free CSS heuristic proving the >=95% full-width / <95% standard metric; it also ships a headless-optional `measure_widest_band` helper (the Phase 5 gate seed) whose true-render check skips-with-note without a browser. CI: `presentify-extractor.yml` path filter broadened to the whole bundle + the new test, `pytest` added, and the layout suite wired in (concurrency-cancel + pip cache already present). Gates green: ruff clean, `validate_skills.py --bundles-only` (0 errors), `validate_unicode_safety.py` (0 errors), `validate_workflow_security.py`, and the full `tests/skills` suite (33 pass / 1 skip).

**Phase 2 (image sizing and placement discipline) COMPLETE.** Gave every image a prominence-appropriate, bounded box with no meaningful-content crop and no dead space at 100% zoom. **2.1**: extended `references/interactive-features.md` "Prominence preservation" with four measurable image-box rules (a hero height cap of ~80vh; a secondary cap that forbids a low-`page_fraction` image from ballooning past a hero, the inverse of the contact-sheet defect; an object-fit / crop policy where `contain` plus a matched background serves meaningful content and `cover` is reserved for decorative backdrops; and a no-oversized-tile rule) plus a dead-space ceiling (~30%) in "Spacing and density", each with an observable metric the Phase 5 QA gate grades (rendered box vs viewport, aspect-distortion ratio, whitespace fraction). **2.2**: CONFIRMED (no extractor code change) that `scripts/extract_content.py` already emits `page_fraction` and native `width`/`height` for BOTH PPTX picture shapes (`shape-picture`, fraction from shape-vs-slide area) and PDF embedded rasters (`embedded-raster`, fraction from bbox-vs-page area), and that `references/content-model.md` already documents these v3 fields; the confirmation artifact is the new prominence test. **2.3**: applied the caps to `assets/presentation-template.html`: `figure img` now carries `max-height: 80vh` + `object-fit: contain` + a matched `background` (aspect preserved via `height: auto` + `max-width`), and a new token-driven `.gallery` grid caps each tile (a minimum width plus `max-height: 40vh` + `object-fit: contain`) so no secondary balloons. **2.4**: `tests/skills/test_presentify_extractor_prominence.py` (PPTX + PDF fixtures via python-pptx / reportlab, `importorskip`-guarded) asserts populated `page_fraction` + native dimensions; `tests/skills/test_presentify_layout.py` gained a browser-free image-cap assertion (max-height, object-fit, gallery) and a headless-optional rendered image-box check (skips without a browser). CI: `presentify-extractor.yml` path filter broadened to `tests/skills/**` and the step now runs the whole `tests/skills/` dir (that runner installs the heavy extractor libs, so the prominence tests execute there). Gates green: ruff clean, orphan audit 0 errors, unicode 0 errors, workflow-security pass, full `tests/skills` suite 36 pass / 2 skip.

**Phase 3 (annotated-figure overlay recreation) COMPLETE.** When a source figure is a base image carrying author-added annotations (map regions, colored zones, callout labels), those annotations are now recreated as a registered interactive overlay on the extracted base image instead of being dropped to a textual list beside a flat map. **3.1**: `references/figure-reconstruction.md` part 1 records an `annotated: true` signal alongside the base classification, and part 5 is rewritten from a binary (full SVG rebuild OR flat enhanced-original) into a THREE-way decision that adds the OVERLAY-RECREATION path (keep the base image; recreate each annotation in a registered overlay layer normalized to the base image with percentage coords; make it interactive with hover/focus highlight, a click-toggle legend, keyboard focus, and a lightbox that moves base + overlay together; carry the provenance badge + view-original toggle), with the side-text kept as an ACCESSIBLE COMPLEMENT, never the replacement. **3.2**: part 4 gates overlays on confidence (high/medium recreate; low degrades to enhanced-original + textual complement with no fabricated regions), part 6 adds the overlay round-trip, and the coverage-reconciliation format adds an `[overlay-reconstructed]` accounting line. **3.3**: `scripts/extract_content.py` now captures PPTX overlay shapes drawn over a picture as an `annotations` array on the image block (a non-picture shape whose center lies inside a picture and is smaller than it, with an image-relative bbox, text, solid fill/line colors, and the enclosing group name); `_iter_pptx_shapes` was extended to carry the group name, and a two-pass shape walk assigns overlays without emitting them as stray text. `content-model.md` and `extraction-runbook.md` document the new field and the flattened-PDF agent-vision path. The extractor change is regression-free (the committed and the new extractor both score 41 PASS / 4 environmental-OCR FAIL on `verify_phase1.py`, and all 8 PPTX checks pass). **3.4**: the baseline builder (`build_presentation.py` + `assets/presentation-template.html`) recreates the overlay from the `annotations` metadata as the deterministic realization of the pattern (a `.fig-annotated` figure: base image, a `.fig-overlay` layer of percentage-positioned `.fig-region` elements with labels, a `.fig-legend`, a provenance badge, and a CSS-only view-original toggle - a checkbox + label, no JS), so the end-to-end path (annotated PPTX -> extractor -> builder -> HTML) is testable. Tests in `tests/skills/test_presentify_annotations.py` (5 cases, 4 run locally + 1 headless-optional skip) cover the extractor annotations, the end-to-end overlay, the dependency-free builder overlay, and the no-annotations degrade. CI needs no edit: `presentify-extractor.yml` already runs the whole `tests/skills/` dir under a `tests/skills/**` path filter (Phase 2). Gates green: ruff clean, orphan audit 0 errors, unicode 0 errors, full `tests/skills` suite 40 pass / 3 skip. **Post-commit security hardening**: a background commit-review flagged that `annotations[].fill` (and the legend color) was interpolated RAW into an inline `style="..."` attribute (attribute-context injection). Fixed by adding `_safe_color` (strict `#hex` validation, drop otherwise) at the fill's point of use, so the content-model JSON (a general input contract, not only the trusted extractor output) cannot inject via a color; legitimate hex is unaffected, and `test_builder_rejects_malicious_fill_color` regression-guards it (suite now 41 pass / 3 skip).

**Phase 4 (reliable stock/mix imagery integration) COMPLETE.** Made a stock/mix imagery choice reliably put relevant, license-verified images into image-starved sections, so "mix" never silently produces zero images. **4.1**: folded the build-time-network / generation CONSENT into the up-front batched design round (`catalog/commands/presentify.md` + SKILL.md Step 2): when the resolved imagery tier is `stock`, `mix` / `auto`, or `ai`, consent is captured with the four design choices, not as a separate mid-run prompt, and a consented run is EXPECTED to attempt integration (silence is a bug). The load-bearing invariants are preserved: the default `procedural` tier and every non-interactive run stay offline; `fetch_stock_media.py` performs NO network without `--consent`; a recalled preference never pre-answers consent. **4.2**: defined an image-starved-section detection pass (SKILL.md Step 6 + `references/interactive-features.md` Tier 2): after the structure is drafted, identify each section that carries no source visual AND would be materially clearer with one, derive SHORT content-relevant keywords from the section topic (never the source document text, keeping the compiling-content trap closed), and fetch/license-verify/base64-embed ONE relevant asset per starved section (Openverse-first, then Wikimedia, Pexels when configured), placed per the Phase 2 sizing rules, with relevance-and-restraint (a loosely-related photo is worse than none). **4.3**: added the integration gate (SKILL.md Verification item + a Tier 2 rubric criterion feeding Phase 5): a consented `stock` / `mix` / `ai` run MUST integrate at least one relevant asset into each starved section OR record a per-section reason; a consented run that integrated ZERO assets with no reason FAILS. **4.4**: VERIFIED (no change) that `nexus-hub setup-media` already exists and stores the Pexels key at `~/.nexus-hub/config/media.env` at mode 0600 - it is wired in `scripts/nexus_hub_cli.py` (`cmd_setup_media` dispatches to `scripts/setup_media_keys.py`), listed in `--help`, present in both installers, and tested by `tests/skills/test_media_key_setup.py`; the first-time-video note in the command/skill already points at it. No installer edit and no "Ask first" trigger. **4.5**: `tests/skills/test_presentify_stock_fetch.py` (14 cases, network monkeypatched so no real request and no `requests` dependency) covers the consent gate (no `--consent` = no network + degrade code 3), a consented Openverse run integrating + crediting a base64 asset (offline), the free-for-commercial-use allow-list rejecting NC/ND (parametrized `is_commercial_cc` + `accept_candidate`), and degrade-always-carries-a-reason (so the integration gate never sees silent zero-integration). CI needs no edit: the fetcher is under the bundle path filter and the new test under `tests/skills/**` (Phase 2). Gates green: ruff clean, orphan audit 0 errors, unicode 0 errors, full `tests/skills` suite 55 pass / 3 skip. Extractor (`fetch_stock_media.py`) UNCHANGED (complete since v3.13/v3.14); this phase is pipeline wiring (command + skill + reference prose) plus tests.

**Phase 5 (iterative multi-agent visual-QA self-critique loop) COMPLETE.** Replaced the single-pass Step 9 with a genuine iterative loop that renders the output, grades each segment against its source and the measurable Phase 1-4 rubric, adversarially verifies, synthesizes fixes, and re-renders until the page-level bar passes or a cap is hit. **5.1**: authored `references/visual-qa-rubric.md` - the per-segment grading rubric assembling metrics from Phases 1-4 (full-width band, image sizing / crop / dead-space, annotation-overlay fidelity vs source, imagery integration into starved sections, readability / layout integrity), split into STRUCTURAL (deterministic, scorer-checkable) and AGENT-VISION (screenshot judgment) kinds, with a per-segment score schema and a binary page-level pass bar (no open high-severity finding). **5.2**: added the Dynamic-Workflow TEMPLATE `assets/visual-qa-workflow.js` (adapt, not run verbatim) that fans the per-segment grading out (pipeline: grade -> adversarially verify high-severity findings with an independent skeptic -> synthesize fixes -> rebuild -> re-grade), carrying the THREE mandatory workflow rules inline: graceful degradation (Dynamic Workflows -> isolated subagents -> single sequential agent, and headless render -> the structural scorer), scope-first token caution (5-15x multiplier, calibrate on one segment, confirm before scale), and skill-native (no outbound call / dependency / credential, LOCAL render); cross-links `[[agent-orchestration-primitives]]` + `[[ai-billing-safeguards]]`. **5.5a**: shipped `scripts/visual_qa_score.py` - the deterministic STRUCTURAL scorer (stdlib-only, no network, headless-optional) that scores a generated `.html` against the structural rubric subset (full-width band via the canvas vars, image caps, overlay well-formedness, imagery-integration count, offline / layout integrity) and returns per-criterion findings + the binary pass bar; it is the structural-review degradation path AND the reused Phase-1 `measure_widest_band` "gate seed" made concrete. **5.3**: rewrote SKILL.md Step 9 from a single render-and-look into the iterative render -> per-segment grade -> adversarially-verify -> synthesize -> re-render loop with the full degradation ladder and the scope-first / budget caution, and updated the Bundled Resources list with the rubric, the scorer, and the workflow template. **5.4**: refreshed the SKILL.md Verification checklist (binary items for the full-width band metric, image sizing, annotation-overlay fidelity, the imagery-integration gate, and the loop-ran-and-converged-or-degraded check) and added four Common Rationalizations rows (one-render-pass, whole-page-not-per-segment, skip-verification-because-expensive, skip-QA-without-a-browser), each tied to one of the four observed defects. **5.5b**: `tests/skills/test_presentify_visual_qa.py` (10 cases, dependency-free) asserts the scorer flags each seeded structural defect (narrow full-width, missing image caps, dropped overlay, zero imagery on a consented expectation, a non-offline page) and passes a clean fixture and n/a cases, drives the CLI exit codes, and asserts the workflow template carries the three mandatory rules + cross-links and the rubric lists all five criteria + the pass bar. CI needs no edit: the scorer is under the bundle path filter (and ruff-linted by the presentify-extractor "Lint the bundled scripts" step), and the new test under `tests/skills/**` (Phase 2). Gates green: ruff clean, orphan-bundle audit 0 errors (rubric + scorer + workflow template all referenced from SKILL.md), unicode 0 errors, SKILL.md 229 lines (within the 800 cap), full `tests/skills` suite 65 pass / 3 skip.

**Phase 6 (command, skill, and registry polish) COMPLETE.** Finalized the user-facing command and skill text and added the loop-depth knob; no new open items (a polish phase). **6.1**: added an optional `--qa-depth {light|standard|deep}` flag to `catalog/commands/presentify.md` (Usage + a flag bullet) that bounds the Step 9 iterative visual-QA loop (`light` = a single grading pass, `standard` = the capped loop, `deep` = the full per-segment fan-out, the default per the chosen ambition), with the scope-first / 5-15x-multiplier caution and the `[[ai-billing-safeguards]]` cross-link; updated the command's visual-QA delegation sentence from the old single-pass description to the iterative per-segment render -> grade vs source -> adversarially-verify -> synthesize -> re-render loop with the degradation ladder; and added a matching `--qa-depth` note to SKILL.md Step 9 (the command already referenced the knob in its Common Rationalizations since Phase 5, so this closed that coherence gap). The four up-front design choices and the no-memory-pre-answer rule are intact. **6.2**: coherence pass over SKILL.md - added the iterative visual-QA loop as a node in the pipeline diagram (it previously stopped at the authored `.html`), and confirmed the Instructions, Common Rationalizations, Verification, and Bundled Resources all reflect Phases 1-5 (they do, from the per-phase edits). SKILL.md is 236 lines, within the 800 soft cap. **Frontmatter / registry decision (deliberate NO-CHANGE)**: reviewed `description` / `summary_l0` / `overview_l1` and left them UNCHANGED, so the three `data/` registry files are untouched. The description's trigger surface already covers the creation intent comprehensively (it already names the output aspect full-width / standard / portrait and "dominant source visuals kept prominent (not flattened into thumbnails)"); the Phase 1-5 work refines that intent rather than adding a new entry intent, and the plan's suggested refine / defect trigger phrases ("fix the layout", "the images are too big / cropped") would risk over-triggering the creation skill on requests that are not "build a presentify site from these documents". `summary_l0` is at its ~15-word budget and still accurate; `overview_l1` remains accurate (the visual-QA loop is an internal quality mechanism, not a new user-facing output type). Per the plan's "ONLY IF changed", no registry sync was performed. **6.3**: `validate_skills.py --bundles-only` (0 errors), `run_trigger_evals.py --gate` (0 collisions, 0 routing failures; descriptions unchanged), and `validate_unicode_safety.py` (0 errors) all green; confirmed CI needs no edit - `ci.yml`'s `validate` job already runs catalog validation and triggers on `catalog/**` + `data/**` (via `paths-ignore: docs/**`) with concurrency + caching, so a separately-path-filtered job would only add minutes (the same decision recorded at v3.15.1 QG-1 / v3.15.2 DF-1). No code changed (Markdown-only), so ruff is not applicable; full `tests/skills` suite still 65 pass / 3 skip.

**Phase 7 (architecture refactor, known-gaps reconciliation, and CI/CD) COMPLETE - v3.15.4 release-ready.** The terminal gate. **7.1 refactor** ([[project-refactor]] + [[docs-layout-refactor]]): a verification pass, near-no-op as expected. The committed skill bundle is clean: all Phase 1-6 additions are correctly placed (`scripts/visual_qa_score.py`, `references/visual-qa-rubric.md`, `assets/visual-qa-workflow.js` in their standard subdirs; the five `tests/skills/test_presentify_*.py` files), no duplicates, no orphans (the orphan-bundle audit passes with every script / reference / asset referenced from SKILL.md), and no committed empty dirs. Removed two UNTRACKED local-only empty dirs (`docs/v3.9.0/.../worked-example/{inputs,models}`, leftover cruft not in git) for working-tree tidiness (zero repo impact). The docs tree (`docs/v3/v3.15/`) is well-organized (plans / comparisons / development-history / known-gaps). No committed file moved or renamed, so no reference repair was needed. **7.2 known-gaps**: this reconciliation. Grepped the plan's changed files for `TODO`/`FIXME`/`XXX`/`HACK`/`DEVIATION` (only the one resolved-and-documented `# DEVIATION` explaining the TITLE_RE constraint, which stays as code documentation). RESOLVED BG-1 inline as a small, tracked, in-scope gap under the 9A rule (`theme_to_css` now emits `--color-bg` / `--color-fg` matching the template's `var()` references, guarded by `test_builder_emits_matching_theme_color_vars`). Every remaining open item got a disposition: DF-1 / DF-2 / DF-3 and MT-1 / MT-2 / MT-3 are kept as documented, non-blocking deferrals, none a release blocker; the plan's named inherent-limitation deferrals are recorded in the Advisory below. **7.3 CI/CD**: confirmed CI covers every change with no edit. `presentify-extractor.yml` runs on the whole bundle (`document-to-interactive-html/**`) + `tests/skills/**`, lints the bundled scripts with ruff, runs the extractor fixture suites, and runs the full `tests/skills/` dir (layout, extractor-prominence, annotations, stock-fetch, visual-QA); `ci.yml`'s `validate` job runs catalog validation + the trigger gate on `catalog/**` + `data/**`; both are already optimized (path filters, `concurrency` cancel-in-progress, pip caching, cost-gated matrix legs). The headless-render checks skip-with-note in CI (no browser); a gated headless-render job is the recorded MT-1 / MT-3 follow-up, not added here. **7.4 stabilization**: `validate_skills.py --bundles-only` (0 errors), `run_trigger_evals.py --gate` (0 collisions, 0 routing failures), `validate_unicode_safety.py` (0 errors), and the full `tests/skills` suite (66 pass / 3 skip) all green; SKILL.md 236 lines (within the 800 cap); ruff clean on the BG-1 builder change + the new test. Finalized the `## [Unreleased]` CHANGELOG entry (the Phases 1-6 summary + the BG-1 Fixed line) so `/update release` needs only to stamp the version heading. The version bump (3.15.3 -> 3.15.4), changelog finalization, count reconciliation (unchanged at 268 skills), tag, and push are handed to `/update release`; this phase performed no version bump, tag, merge, or push.

### v3.15.4 Open Items

#### Deferred

##### DF-3 - overlay-annotation detection is a geometric heuristic (full-slide-background text is captured)

- **Source phase**: v3.15.4 Phase 3.3.
- **Plan reference**: Phase 3.3 (capture author-added overlay shapes over a picture).
- **Reason**: the extractor assigns a non-picture shape as an annotation when its CENTER lies inside a picture AND its area is smaller than the picture. This correctly captures region rectangles and callout labels over a figure, but a full-slide BACKGROUND picture with body text on top would capture that body text as annotations (the text is, arguably, overlaid on the image). The LLM-native path re-reads under the confidence gate and applies judgment; the deterministic builder renders whatever `annotations` carries. Documented in the `extraction-runbook.md` PPTX gotchas.
- **Suggested next step**: if this over-capture is observed in practice, tighten the heuristic (for example, skip pictures whose `page_fraction` is ~1.0 unless they are classified `map`/`diagram`/annotated, or require the annotation shape to carry a fill or a short label). Non-blocking; the primary consumer applies judgment.

##### DF-1 - baseline builder does not group images into a `.gallery` (styles are latent)

- **Source phase**: v3.15.4 Phase 2.3.
- **Plan reference**: Phase 2.3 (template image / gallery styles) and 2.1 (prominence rules; the primary target is the LLM-native authoring path).
- **Reason**: the Phase 2.3 template now carries a token-driven `.gallery` grid with a bounded per-tile cap, but the deterministic baseline builder (`build_presentation.py`) renders each image as its own stacked `<figure>` and does not emit a `.gallery` wrapper or classify hero-vs-secondary from `page_fraction`. So on the baseline path several small images stack (each bounded by `max-height: 80vh` + `max-width`, so none crops or distorts) rather than forming a grid. The prominence-aware hero/secondary sizing and the gallery grid are the LLM-native path's job per the reference; the baseline is the "plain draft to elevate".
- **Suggested next step**: if the baseline should render a true gallery, teach the builder to group a run of comparable-`page_fraction` images into a `.gallery` wrapper (and size a high-`page_fraction` image as a hero) in a later phase. Non-blocking.

##### DF-2 - PDF embedded-raster `page_fraction` is null when the pdfplumber image-bbox count does not match the extracted raster count

- **Source phase**: v3.15.4 Phase 2.2 (discovered while confirming the signals).
- **Plan reference**: Phase 2.2 ("If any is missing or frequently null, add it").
- **Reason**: the PDF path computes `page_fraction` for an embedded raster only when pdfplumber's per-page `images` bbox list length equals the extracted raster count (the extractor's intentional geometry-alignment guard, so a bbox is never mis-assigned to the wrong raster). When the counts differ the block still carries native `width`/`height` but `page_fraction` is absent. This is NOT "frequently null" for well-formed report PDFs (the confirmed embedded-raster test yields a populated fraction), so it is documented rather than fixed; PPTX pictures and PDF rasterized-regions always carry the fraction.
- **Suggested next step**: a later phase could add per-raster bbox matching (by size / order heuristics) to populate `page_fraction` even when the counts differ. Non-blocking; the native dimensions still provide a fallback ranking signal.

#### Missing tests / coverage gaps

##### MT-1 - rendered-width full-width check skips without a headless browser (browser-free heuristic covers the metric)

- **Source phase**: v3.15.4 Phase 1.4.
- **Plan reference**: Phase 1.4 ("when no headless browser is present, the helper falls back to a computed-CSS/markup heuristic and the test skips-with-note rather than failing") and the plan's Phase 7 deferral ("the headless-browser-optional degradation - structural review is weaker than a real render").
- **Reason**: `measure_widest_band` renders and measures the widest `.slide__body` when a headless browser (Playwright) is present, but no browser is installed on the dev host or in the `presentify-extractor` CI runner, so `test_rendered_band_width` SKIPS. The >=95% full-width / <95% standard metric IS asserted browser-free by `test_heuristic_band_fraction_meets_contract` (deterministic CSS/markup math), and the injected-var / offline / head-integrity assertions all run without a browser.
- **Suggested next step**: Phase 5 builds the iterative visual-QA loop and its gate; gate a headless-render job to merges/schedule there (per the plan) so the true rendered-width check runs in CI, and reuse `measure_widest_band` as its seed.
- **CLOSED 2026-08-11 by v3.16.5 Phase 3** (appended, not rewritten - the record above stands as it was written). The suggested next step was followed almost verbatim: `.github/workflows/presentify-extractor.yml` now carries a `render` job gated to merges (`push` to `main`/`develop`) plus a weekly cron, which installs Playwright chromium with a version-keyed download cache and runs the full `tests/skills/` suite with `NEXUS_REQUIRE_RENDER=1`. `measure_widest_band` is reused unchanged as its seed. Two things were added beyond the original suggestion, both because the gap's real shape was worse than "the check skips":
    - **The skip is now enforceable, not just possible.** A `render_gate` fixture in `tests/conftest.py` converts the runtime skip into a FAILURE when `NEXUS_REQUIRE_RENDER=1`. Without it, a job that installed a browser and then skipped the checks anyway would still look green - which is precisely how this gap survived four minor versions. Local behavior is unchanged (skip-with-note, never a hard fail on a missing browser).
    - **A new `scripts/ensure_render_env.py` makes a degraded environment explicit.** It probes for an importable Playwright with a *launchable* chromium (launching is the only honest test; a cache directory can exist while the build inside it is unusable), then a local Chrome/Edge, and exits with a distinct code per state while printing the exact one-time provisioning commands. The CI job runs it as a gate before the tests, so a broken browser install fails loudly instead of degrading quietly.
- **Observed while closing it**: on the maintainer's Windows host, Playwright and a cached chromium were ALREADY present, yet all three browser-dependent checks skipped across multiple Phase 1 and Phase 2 runs and then passed consistently after one warm-up launch. That is the strongest available argument for the explicit probe: the environment was capable the whole time, and the loop reported a clean structural pass without ever saying it had not rendered.

##### MT-2 - consented stock/mix per-section integration is agent behavior (fetcher enforcement is unit-tested; end-to-end graded by Phase 5)

- **Source phase**: v3.15.4 Phase 4.5.
- **Plan reference**: Phase 4.2 / 4.3 (image-starved-section detection + integration gate).
- **Reason**: the deterministic enforcement layer (`fetch_stock_media.py`'s consent gate, free-for-commercial-use allow-list, and degrade-with-a-reason) is unit-tested in `tests/skills/test_presentify_stock_fetch.py`. The agent-side behavior (detecting which sections are image-starved, deriving per-section keywords, and placing a fetched asset into each starved section) is LLM-native authoring, not deterministically unit-testable; it is graded by the Phase 5 visual-QA loop (imagery-integration criterion). This mirrors the prior phases' pattern (agent behavior graded by Phase 5).
- **Suggested next step**: Phase 5 adds the imagery-integration rubric criterion and gate; no additional unit test is owed for the agent-side placement. Non-blocking.
- **CLOSED 2026-08-11 by v3.16.5 Phase 5** (appended, not rewritten - the record above stands as written). The item deferred end-to-end grading of consented per-section integration to "the Phase 5 visual-QA loop", and that loop now exists (v3.16.5 Phase 3) with the placement pass running inside it. What closes the gap is not more agent instruction but a DETERMINISTIC record check: the placement pass must write an `IMAGERY PLACEMENTS` block to the design record with one decision per section, and `visual_qa_score.py` verifies that record against the page - failing a consented run that embedded assets but left no decision trail, a record claiming more embedded assets than the page contains, or a decline with no reason. That converts "the agent should integrate or explain" from an instruction into a checkable artifact, which is what the original item was missing. The agent-vision half (is THIS image relevant to THIS section?) remains a screenshot judgment by design and is graded by rubric criterion 4.
- **Status after v3.16.5 Phase 3** (appended, not rewritten): still OPEN, and deliberately so. Phase 3 built the render loop that HOSTS the end-to-end grading this item defers to, and the rubric's imagery-integration criterion is now graded from real screenshots rather than from markup. The remaining half - deciding WHERE imagery helps and verifying each candidate's contextual relevance - is v3.16.5 Phase 5's placement pass. Recorded here so a reader of this ledger is not left assuming Phase 3 closed it.

##### MT-3 - the visual-QA loop's agent-vision grading, fan-out, and end-to-end sample-deck smoke are behavioral (the structural scorer is the unit-tested backbone)

- **Source phase**: v3.15.4 Phase 5.5.
- **Plan reference**: Phase 5.5 ("a test that the workflow template degrades ... an end-to-end smoke test on the sample board deck fixture asserting the loop reaches the pass bar").
- **Reason**: the deterministic STRUCTURAL scorer (`scripts/visual_qa_score.py`) is fully unit-tested (per-criterion defect flagging, clean pass, CLI exit codes). The AGENT-VISION grading (crop, dead space, annotation placement vs source, imagery relevance, contrast), the Dynamic-Workflow fan-out, and the full render -> grade -> fix -> re-render loop are LLM-native + runtime + browser behavior, not deterministically unit-testable; the workflow template is an adapt-me artifact asserted structurally (it carries the three mandatory rules), not executed. There is no committed "sample board deck" fixture, and the loop is agent-driven, so the e2e smoke is a browser-gated / release-time verification (the Phase 7 exit checklist verifies the four observed defects on the sample deck), not a CI unit test.
- **Suggested next step**: when a headless-browser CI job is added (gated to merges/schedule, per the plan), wire an e2e smoke that runs the scorer against a built sample-deck fixture; the agent-vision grading stays a behavioral (non-unit) check. Non-blocking.

### v3.15.4 Resolved

##### BG (deviation) - TITLE_RE swallowed the document head (PRE-EXISTING, root-cause fixed in Phase 1.3)

- **Source phase**: discovered and fixed in v3.15.4 Phase 1.3 (logged as a `# DEVIATION:` in `build_presentation.py`).
- **Status**: RESOLVED. `TITLE_RE = <title>.*?</title>` (DOTALL) matched the template header comment's literal "<title>" mention and spanned to the real `</title>`, deleting the comment close (`-->`), the `<html>` tag, `<head>`, and the `<meta>` tags on every build - so the baseline builder had been emitting malformed HTML with no document head (unnoticed because no test checked builder output structure and `assert_no_external` strips comments before scanning). Constraining the pattern to `<title>[^<]*</title>` keeps the match to a single well-formed title element. Fixed here because Phase 1.3 requires the builder to emit a valid `<html data-aspect="...">` (the head must survive); guarded by `test_head_survives_title_substitution`.

##### BG-1 - baseline builder lost theme background/foreground colors in built output (PRE-EXISTING; RESOLVED in Phase 7)

- **Source phase**: discovered in v3.15.4 Phase 1.3; resolved in Phase 7.2 (a small, in-scope known-gap fix under the 9A rule).
- **Status**: RESOLVED. `theme_to_css()` emitted `--color-background` / `--color-foreground`, but the template CSS references `var(--color-bg)` / `var(--color-fg)`, so the BUILT output left those two vars undefined and the body lost its theme background / foreground colors (the raw template rendered fine standalone). Fixed by mapping the theme's `background` / `foreground` palette keys to the `--color-bg` / `--color-fg` CSS var names in `theme_to_css` (a name-alignment only; the palette values and every other `--color-*` name are unchanged, and the template carries no `var(--color-background)` / `var(--color-foreground)` reference, so nothing else breaks). Deferred out of Phases 1-6 as orthogonal to the four observed defects; fixed in the terminal phase as a tracked, small, in-scope gap. Guarded by `test_builder_emits_matching_theme_color_vars`.

### v3.15.4 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 3 | 0 |
| Bugs / regressions (BG) | 0 | 2 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 3 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

OPEN and carried as documented, non-blocking items (all reconciled in Phase 7 as deferred with a disposition): DF-1 (baseline builder does not group images into a `.gallery`; the gallery styles are latent for the LLM-native path), DF-2 (PDF embedded-raster `page_fraction` is null on a pdfplumber bbox-count mismatch; native dimensions still rank), DF-3 (overlay-annotation detection is a geometric heuristic that would capture full-slide-background body text; the primary consumer applies judgment), MT-1 (rendered-width, rendered image-box, and rendered overlay-toggle checks skip without a headless browser; the metrics are covered browser-free by the CSS heuristic + markup assertions), MT-2 (consented stock/mix per-section integration is agent behavior; the fetcher enforcement is unit-tested and the end-to-end placement is graded by the Phase 5 loop), MT-3 (the visual-QA loop's agent-vision grading, fan-out, and e2e sample-deck smoke are behavioral; the structural scorer is the unit-tested backbone, and the e2e is a browser-gated / release-time check). RESOLVED: the pre-existing TITLE_RE head-corruption bug (Phase 1.3) and BG-1 (the builder color-var mismatch, fixed in Phase 7.2). None of the open items is a release blocker.

### v3.15.4 Advisory (pre-existing, not introduced by this phase)

- The whole-tree bundle audit reports transient `__pycache__/*.pyc` orphan warnings (e.g. `catalog/skills/specialized-domains/document-to-interactive-html/scripts/__pycache__/build_presentation.cpython-312.pyc`) whenever the bundle's Python is executed locally. These are gitignored (`.gitignore` line 60, `__pycache__/`), never staged, and were cleaned after each phase's test runs. Warning, never error; no action needed.

**Inherent limitations (recorded per the Phase 7.2 reconciliation; accepted, non-blocking):**

- **Headless-browser-optional degradation is weaker than a real render.** Without a browser the visual-QA loop grades only the STRUCTURAL rubric subset (`scripts/visual_qa_score.py`) plus a markup / computed-CSS read; the AGENT-VISION criteria (crop of meaningful content, dead space, annotation placement vs source, imagery relevance, contrast) are not certified. This is by design (the loop never hard-fails on a missing browser); the true rendered / vision gate is the MT-1 / MT-3 browser-gated follow-up.
- **Local AI imagery (Tier 3) still requires a local runtime.** The `ai` tier degrades to Tier 1 when no local model runtime / weights are present (a pre-existing constraint, unchanged by v3.15.4; a hosted generation API is a policy hard-no). Not a regression; recorded for completeness.
- **The object-fit / crop heuristic cannot certify "meaningful content" structurally.** The Phase 2 caps (`object-fit: contain`, the height caps) prevent distortion and viewport-dominance deterministically, but whether a given crop removed MEANINGFUL content (a chart axis, a labeled region, a face) is an agent-vision judgment, not a structural one. Covered by the loop's agent-vision pass when a browser is present.
- **The visual-QA fan-out carries a token-multiplier cost.** A per-segment fan-out is a 5-15x multiplier; this is MITIGATED (scope-first calibration, the `--qa-depth` knob, and `[[ai-billing-safeguards]]`) and degrades to a single sequential pass / the structural scorer, but it is not eliminated. Accepted per the plan's Complexity Tracking (the user chose maximum fidelity over a capped single-agent loop).

## v3.15.5 - model-prompting-research

**Status**: ALL 6 PHASES COMPLETE; RELEASE-READY. This section is finalized; the version ships when the maintainer runs `/update release` (the branch `feat/model-prompting-research` is unpushed and not yet merged to `develop`). Phase 1 (profile-layer contract and validators), Phase 2 (research engine and skill scaffold), Phase 3 (edit-routing classifier and guard-gated auto-apply), Phase 4 (command, skill finalize, registration), Phase 5 (advisory release integration), and Phase 6 (terminal refactor + known-gaps + CI/CD gate) all COMPLETE. The catalog is now **269 skills** and **17 commands**. The release also carries one out-of-phase inclusion: the installed default reasoning effort dropped from `xhigh` to `medium`. Plan: [plans/v3.15.5-model-prompting-research.md](plans/v3.15.5-model-prompting-research.md). **Phase 3 disproved the plan's central safety claim about `check_base_template_parity.py` and re-implemented the hard rail where it can actually be enforced; read the Phase 3 paragraph and DF-2 before Phase 6 confirms the Definition of Done.**

> **Prior-version ingest**: checked this file (docs/v3/v3.15/known-gaps.md). The open v3.15.0-.4 items are unrelated to model-prompting research and do not carry in. One item is adjacent and worth naming: v3.15.0's **HO-1** (flat/nested skill-name collision across skill layouts) DOES apply from Phase 2 onward, because this release ships a new catalog skill (`model-prompting-research`); Phase 1 ships only the skill's bundle data with no `SKILL.md`, so the collision surface does not exist yet.

**Phase 1 (profile-layer contract and validators) COMPLETE.** Established the per-model prompting profile layer as a schema-validated, freshness-stamped contract, plus the two repo-level scripts that police it. **1.1**: created the layer under `catalog/skills/ai-development/model-prompting-research/` with the authoritative machine index `assets/profiles-index.json` (schema 1.0.0: `meta.roster` sorted and unique, a `meta.roster_hash` defined as `sha256` of the sorted roster joined by newlines, `meta.roster_source` provenance, and per-model claim objects carrying `claim` / `source_url` / `confidence` / `scope` and an optional `note`), the contract doc `references/schema.md`, and one seed mirror `references/models/claude-opus-5.md`. Live enumeration via the `model-routing` helpers returned the picker sentinel (no `ANTHROPIC_API_KEY` present), so the roster was read from the Claude Code model picker and is provenance-tagged `picker`; the single seed claim is deliberately tagged `confidence: unverified` and `scope: model-specific` (the ambiguous-defaults-to-model-specific rule) so it cannot reach a shared body before Phase 2 verifies it. **1.2**: added `scripts/verify_model_prompting_profiles.py`, a stdlib-only STRUCTURAL hard gate wired into `make validate` and the CI `validate` job; it validates the top-level keys, the `meta` block, roster sortedness / uniqueness / hash self-consistency, every claim's shape and allowed `confidence` / `scope`, rejects unknown keys at every level (so a `sources_url` typo fails loudly), and enforces a BOTH-directions match between index models and `references/models/*.md`. It deliberately does NOT check freshness or roster coverage. **1.3**: added `scripts/check_model_prompting_freshness.py`, the ADVISORY counterpart; it compares the recorded roster against a live roster passed on argv (the caller enumerates, the script never touches the network), reports IN SYNC / DRIFTED (added, removed, or hash-not-re-stamped) / UNKNOWN, and exits 0 on every path unless the explicit `--strict` flag is passed. It is deliberately absent from `make validate` and CI so a vendor shipping a model can never wedge a release. It imports `find_bundle` and `roster_hash` from the validator so the two can never disagree about the canonical hash. **1.4**: registered both scripts in BOTH installers (the `scripts/installer.sh` `safe_copy` block and the `scripts/installer.ps1` `Safe-Copy` block), verified by extracting and running the REAL `install_templates` / `Install-Templates` functions against throwaway HOMEs on both hosts: both scripts land byte-identically under `~/.nexus-hub/scripts/`, and the installed validator runs standalone. The repo's generalized guard `test_installers_copy_every_scripts_dir_py_file` passes. **1.5**: 62 new tests in `tests/validators/` (subprocess-invoked, matching the established validator-test pattern), all green; measured coverage 94% (validator) and 97% (freshness checker), 97% combined, against the 80% gate. All `make validate` gates exit 0, and ShellCheck exits 0.

**Phase 2 (research engine and skill scaffold) COMPLETE.** Built the web-research half and the skill that houses it. **2.1 skill scaffold**: authored `SKILL.md` (131 lines, well inside the 500-line norm) with a 243-character pushy `description`, a 13-word `summary_l0`, and a 148-word `overview_l1`, all inside budget. The body carries When to Use / When NOT (fencing off `model-routing`, `prompt-engineering`, `/usage`, and `platform-contract-verification`), a pipeline diagram, seven-step Instructions delegating detail to the runbook, the scope hard rail as a table, the degradation ladder, the budget section, a bundled-resources table, seven Common Rationalizations each citing a concrete failure mode, an eight-item binary Verification checklist, and Related Skills. Pushed the procedure detail to a new `references/research-runbook.md` per the three-tier norm. **2.2 fan-out template**: added `assets/research-workflow.js`, a Dynamic-Workflow TEMPLATE (adapt, not run verbatim) that pipelines per model: search and FETCH the vendor's own primary sources, extract discrete claims, then adversarially refute each claim with three independent skeptics weighing source authority, currency, and actionability. A claim survives only on a primary source plus a majority failing to refute, and confidence follows the margin. Scope can be tightened by a verifier but never loosened. The three mandatory rules are inline (graceful degradation with an explicit offline logged-no-op rung, scope-first token caution, skill-native), cross-linking `[[agent-orchestration-primitives]]`, `[[ai-billing-safeguards]]`, and `[[adversarial-verifier]]`. **2.3 budget cap and kill switch**: a 60k-output-token default per-model branch cap (`PER_MODEL_BUDGET`) plus a one-branch reserve checked BEFORE each branch starts, so the run stops starting branches at the ceiling rather than dying mid-verification; because writes happen per model, a capped run leaves a valid partial layer plus a logged shortfall. Documented in SKILL.md and the runbook, including how to raise it. **Deterministic planner and writer (in-spirit realization of 2.2/2.4)**: added the bundled `scripts/write_model_prompting_profile.py`, which owns the two ends of the pipeline that must not be agent work. `plan` computes the research work-list (unprofiled, claimless, or wholly-unverified models) so the fan-out is reproducible and the caller can scout it, which the workflow needs anyway since workflow scripts have no filesystem access. `write` validates and merges verified claims, re-stamps the roster and hash, and regenerates the Markdown mirrors, refusing the entire write on any malformed claim. **2.4 tests**: 51 tests in `tests/skills/test_model_prompting_research.py`, 91% branch coverage on the writer. The load-bearing one is a cross-check: whatever the writer produces must pass the repo-level structural gate, so the two cannot drift apart. Also covers the roster-to-fan-out mapping, the merge and roster re-stamp, the partial (budget-capped) write, the eleven malformed-input abort cases, Markdown pipe escaping, and static assertions that the template carries all three mandatory rules, its cross-links, the kill switch, and no runtime-forbidden clock or RNG call. **Routing evals**: shipped `evals/trigger-cases.json` (4 positives, 5 near-miss negatives drawn from the SKIP clause), matching the v3.15.3 standard for a new skill. It immediately caught a real defect: the original description's SKIP clause said "picking a model", and "picking" stems to the same token as the "pick the cheapest model" near-miss, so the weakest positive (0.57) failed to clear the strongest negative (0.50) by the 1.15x margin. Reworded to "choosing a model" and added "conventions", and the gate now passes across all 269 skills. **CI**: no edit needed; `ci.yml` already runs `pytest tests/skills -v` and the `validate` job already triggers on `catalog/**`.

**Phase 3 (edit-routing classifier and guard-gated auto-apply) COMPLETE.** The plan's highest-risk phase, and the one that can autonomously write to the shipping catalog. **A CORRECTION TO THE PLAN'S CENTRAL SAFETY CLAIM came out of it, and it is the most important thing in this section.** The plan's Overview and Definition of Done assert that `check_base_template_parity.py` makes the hard rail physical, so that "a model-named line in a shared `base-*.md` fails the build" and "model-specific content physically cannot land in a shared body". That is FALSE. It was tested empirically before any Phase 3 code was written, with three fixture cases: (A) the same model-named line added to ALL FIVE `base-*.md` files inside an invariant section PASSES the guard; (B) a model-named line added to ONE file in a non-invariant section PASSES; (C) the control, a genuinely divergent invariant section, is correctly CAUGHT. The guard compares the five templates TO EACH OTHER, so lockstep is exactly what it verifies, and an auto-apply engine dutifully applying the same model-named line five times satisfies it perfectly. Case A is not a corner case: it is precisely what a well-behaved, lockstep-respecting engine would do. **3.1 classifier**: implemented in the bundled `scripts/apply_prompting_edits.py` with four routes (`eligible`, `profile-only`, `rejected`). Scope must be exactly `model-agnostic-candidate` to be eligible; a missing, empty, unrecognized, or differently-cased value routes to `profile-only`, so ambiguity always resolves to model-specific. Only six shared-body surfaces are targetable (skill description, trigger phrase, rationalization, verification, command body, base-template line); anything else is rejected, so the feature cannot touch installers, hooks, `data/`, READMEs, or CI. **The hard rail was therefore implemented in the engine, where it can actually be enforced**: an edit may not INTRODUCE a model identifier into a shared body regardless of its declared scope, detected by comparing identifiers in the edit's new text against those already in its old text (so rewording or removing an existing mention stays allowed). Routing rules and the evidence are documented in `references/edit-routing.md`. **3.2 guard-gated apply loop**: creates or checks out `feat/tune-prompting-<stamp>` from the integration branch (the stamp is caller-supplied, never generated internally, since a workflow runtime has no clock), then asserts HEAD is that branch and is not `main`/`master`/`develop` BEFORE touching a file. Each eligible edit is snapshotted, applied, and guarded against the full suite (skill-bundle audit, base-template parity, profile schema, version sync, trigger-and-routing gate, plus ShellCheck on a shell edit); all-pass keeps it, any-fail restores the snapshot and quarantines the edit with the failing guard's name and output, and the run continues. Edits stay uncommitted unless `--commit` is passed, and every run ends by stating the branch is for human merge. **A second plan correction**: the plan specified `git checkout -- <file>` for the revert, which is wrong when two eligible edits target the same file, because it reverts to HEAD and would silently discard an earlier SURVIVING edit along with the failing one. An in-memory snapshot restore reverts exactly the failed edit; `test_a_failing_second_edit_does_not_destroy_a_surviving_first_edit` guards it. **3.3 gap report**: rendered deterministically from one run's results, with applied / quarantined / profile-only / rejected sections, a branch diff summary, and ready-to-paste known-gaps entries per quarantined edit and per unverified model. **3.4 tests**: 62 tests in `tests/skills/test_model_prompting_edit_routing.py`, 83% branch coverage on the engine. They include the corrected hard-rail proof as a PAIR: one test pins the parity guard's real (permissive) behavior so the false premise cannot quietly return, and its partner proves the engine blocks the exact edit the parity guard misses. Also covered: every routing rule, eight model-identifier shapes, the reword-is-allowed and remove-is-allowed cases, per-edit auto-revert, the same-file multi-edit case, unusable anchors, branch isolation end to end, uncommitted-vs-committed behavior, `develop` remaining untouched, and gap-report determinism and Markdown table integrity.

**Phase 4 (standalone command, skill finalize, and registration) COMPLETE.** The authoring-and-registry phase over machinery already built and tested. **4.1 command**: added `catalog/commands/tune-prompting.md`, a thin dispatcher with a pushy description and a SKIP clause fencing off `/route`, `prompt-engineering`, and `/usage`. It accepts a bare invocation, a single model id (the scope-first calibration path), `--dry-run` (research and profiles plus a report of what it WOULD change in shared bodies, applying nothing), and `--profiles-only` (never considers a shared-body edit at all). It documents the three load-bearing safety properties inline, including the corrected note that `check_base_template_parity.py` does NOT enforce the hard rail, and records the per-platform slash surfaces. **4.2 SKILL.md finalize**: the body was already complete after Phase 3, so this added the entry point (the command and its flags) and nothing else. 161 lines, well inside the 500-line norm; the full validator reports 0 errors and 0 warnings, so the orphan-bundle audit finds every one of the seven bundled resources referenced. **4.3 registration**: hand-edited the three registry files only, per AGENTS.md rule 2, and deliberately did NOT run the catalog rebuild (it rewrites the whole tree). The resulting diff is 3 lines in `SKILL_INDEX.md`, 4 in `marketplace.json`, and 60 in `skills.json`. **Registering the skill surfaced and corrected pre-existing registry drift that no gate was checking**: `skills.json.statistics.total_skills` read 260 against 268 actual entries, `SKILL_INDEX.md`'s total line read 267, and `skills.json.statistics.categories` was stale in five categories (code-review 13, developer-experience 30, orchestration 15, project-setup 4, workflow 41), summing to 261. All were set to true values, so the catalog now reads a consistent 269 skills across disk, `skills.json` entries, `statistics`, and `marketplace.json`, with matching per-category counts; `marketplace.json`'s `plugin.description` moved to 269 skills and 17 commands. The `statistics.categories` correction was in scope because Phase 4 edits that same `statistics` block, and leaving `total_skills: 269` beside a breakdown summing to 261 would have been self-inconsistent. **The root cause was closed rather than logged**: `tests/validators/test_registry_consistency.py` (9 tests) now asserts that every on-disk skill is registered, that no registry entry lacks a skill on disk, that `total_skills` and every per-category count agree across `skills.json` and `marketplace.json`, that the `SKILL_INDEX.md` total matches and carries a row per skill, and that every index summary is quoted (the MCP server parses those). Both drifts would have been caught by it. **4.4 stabilization**: a throwaway-profile registry install confirmed distribution end to end, landing all ten bundle files flattened at `.claude/skills/model-prompting-research/` (SKILL.md, both assets, the eval, all four references including `models/`, both scripts) plus the command at `.claude/commands/tune-prompting.md` and `.codex/prompts/tune-prompting.md`, and Codex additionally receiving it as a command-skill at `.codex/skills/tune-prompting/SKILL.md`. All 14 validate gates exit 0; `tests/skills` 185 passed / 3 skipped, `tests/integrations` 398 passed / 1 skipped, `tests/validators` 372 passed with only the pre-existing Windows-host failure. CI needs no edit: the `validate` job's catalog and JSON checks pick up the new skill and command automatically, `pytest tests/skills` and `pytest tests/validators` cover the new tests, and `install-smoke` verifies read-paths generically.

> **Count correction**: the Phase 3 devlog and session history record `tests/skills` at 179 passed. That figure was measured immediately before the final six default-guard tests were added to `test_model_prompting_edit_routing.py`; the accurate Phase 3 total is 185, which is what Phase 4 re-measured.

**Out-of-phase inclusion: installed default reasoning effort lowered from `xhigh` to `medium`.** An independent operator-facing change, authored in a parallel session and folded into this release at the maintainer's direction rather than carried as its own version. A fresh install now starts Claude Code (and the Claude desktop app, which reads the same `~/.claude/settings.json`) at `medium`, so the deeper tiers become a deliberate per-task escalation instead of a standing per-turn cost. Three declarations move in lockstep, because `env.CLAUDE_CODE_EFFORT_LEVEL` is the highest-precedence lever and a mismatch would silently win over the scalar: `effortLevel` and `env.CLAUDE_CODE_EFFORT_LEVEL` in the canonical template `catalog/hooks/settings.json` (which both installers read at runtime rather than hardcoding, so no installer edit was needed), and the same two keys in the `nexus-hub init` project stub (`scripts/lib/integrations/claude.py`). The `model: opus` pin is unchanged. Four documentation surfaces that stated the old value as fact were corrected (`guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md`, the Effort-Level Strategy section of `prompt-engineering`, the fan-out effort note in `multi-agent-coordinator`, and the effort-level section of the `claude-usage-monitor` README, whose usage-band roadmap now reads as modulation in both directions around the default), and both regression guards that pinned `xhigh` now pin `medium` AND assert the scalar/env match (`catalog/hooks/tests/test_installer_smoke.py`, `tests/installer/test_init_subcommand.py`). **Verified on review before commit**: a repo-wide `xhigh` sweep found no remaining surface that states it as the installed default (the other 20-odd hits are legitimate references to `xhigh` as a valid effort VALUE, in the effort scale, the `switch-model` helpers, and archived v0.9-era history); `catalog/hooks/tests/test_platform_parity.py::test_effort_level_language_consistency` needed no update because it bans a hardcoded `effortLevel` default in the `base-*.md` templates and already listed `medium` among the banned values; and the renamed guard was correctly re-registered in that file's `_run_all()` list. Tests: the two updated guards pass, `test_init_subcommand` 6/6, `test_platform_parity` 4/4.

**Phase 5 (release integration, advisory governance step) COMPLETE.** Made `/update release` aware of profile staleness without coupling the release clock to the model-release clock. **5.1**: added governance step 5 to `catalog/commands/update.md`, after step 4 (platform-contract-verification). It self-gates (real work only in a repo shipping the profile layer plus `model-routing`, silent no-op elsewhere), enumerates the live roster, runs `check_model_prompting_freshness.py --advisory`, and on DRIFTED prints a one-line note naming the added or removed models plus an offer to run `/tune-prompting`. The entry spells out the ADVISORY contract as four explicit bullets (never blocks, never re-stamps a freshness marker, never wired into `make validate` or CI, degrades to a logged no-op offline) and states the contrast with step 4 in the imperative, closing with a warning that a future editor who "fixes" this into a blocking gate reintroduces the exact coupling the design avoids. **5.2**: mirrored into the `implement-phase` final-phase gate as item 4 of the 9.0 mandatory gate, by REFERENCE rather than duplication per the plan (it invokes the skill and points at `/update release` governance step 5 as the canonical description). Edited the CATALOG copy (`catalog/skills/workflow/implement-phase/references/implement-phase-runbook.md`), not the installed one. **5.3**: 24 tests in `tests/skills/test_release_staleness_step.py`. The functional behavior (in-sync / added / removed / UNKNOWN / never-non-zero-in-advisory) was already covered exhaustively by the Phase 1 freshness-checker suite, so these tests guard what prose can silently lose: that both entry points declare the step, declare it advisory and self-gating, name the same script, order it after the platform-contract step, and that the mirroring sentence was updated. **The load-bearing test is `test_freshness_checker_is_not_wired_into_any_gate`**, which fails the moment the checker appears as an invocation in the Makefile or `ci.yml`; its sibling asserts the structural gate IS still wired, so the deliberate split cannot silently collapse in either direction. Two further tests assert the step did not leak into the `base-*.md` lockstep templates (it is command + skill behavior, not always-loaded instruction text) and that `update.md` stays a thin dispatcher rather than inlining the procedure. **A gap the new tests found and closed**: the check for "each gate file documents why the checker is absent" failed on the Makefile, which omitted the freshness checker with no explanation at all (only `ci.yml` carried a note). A five-line comment now records why, so the omission cannot be read as an oversight and re-added by a future editor. The comment sits at column 0 inside the recipe, which GNU make strips without terminating the recipe; verified structurally (38 recipe lines, 31 tab-prefixed commands, still ending in the compression gate). Gates: all 12 validate gates exit 0, `tests/skills` 209 passed / 3 skipped.

**Phase 6 (architecture refactor, known-gaps reconciliation, and CI/CD) COMPLETE - v3.15.5 release-ready.** The terminal gate. **6.1 refactor** (`project-refactor` + `docs-layout-refactor`): the v3.15.5 diff introduced no duplicates, no orphans (the bundle audit finds every one of the eight bundled resources referenced from SKILL.md), and no committed empty directories. The detectors did surface **8 UNTRACKED empty directories** elsewhere in `catalog/skills/` (`code-cleanup/lint-repair-loop`, `developer-experience/helper-script-authoring`, `developer-experience/code-optimizer/scripts`, `testing/visual-regression-testing/scripts`, `tests-generation/false-confidence-test-audit`, `tests-generation/performance-regression-gate/scripts`, `workflow/commit-sweep`, `workflow/end-of-shift-validation`); all carry zero tracked files, so they have zero repo impact, and several look like live skill scaffolding from the parallel session active in this worktree. They were REPORTED AND LEFT IN PLACE rather than removed, unlike the v3.15.4 Phase 7 precedent, because deleting another session's in-progress scaffolding is not a tidiness win. The docs tree stays canonical and no committed file moved, so no reference repair was needed. **NI-4 resolved**: corrected all five prose count surfaces to 269 skills / 17 commands (`AGENTS.md` Repository Overview and project-structure comment, `README.md` lines 9, 33, and 181). `docs/CATALOG-COVERAGE.md` carries no counts, and no platform-coverage table needed a change, because the new skill and command use existing distribution channels (the recursive skill-folder copy and the `catalog/commands/` copy) rather than adding a surface. The README "What's New in v3.15.5" section is deliberately left to `/update release`, matching the v3.15.4 precedent. **6.2 known-gaps**: this reconciliation, with a disposition on every open item (below). The TODO/FIXME/XXX/HACK/DEVIATION sweep over the release's files found only two hits, both benign: `references/schema.md` documenting `note` as a legitimate place for a TODO, and the seed claim's own note. That note read `TODO(phase-2)`, a reference to a phase that has now passed without a real research run, so it was re-pointed at `TODO(first-verified-run)` and expanded to say plainly that it is a hand-seeded contract example rather than research output. **6.3 CI/CD**: complete with no edit, verified surface by surface. `ci.yml` already runs every tree this release added tests to (`tests/validators` for the two repo scripts and the registry guard, `tests/skills` for the writer, the apply engine, and the release step, plus `tests/integrations`, `tests/installer`, and `catalog/hooks/tests`), and the `validate` job runs the profile schema gate alongside the JSON integrity checks and the trigger-routing gate. It is already optimized (workflow-level `paths-ignore`, `concurrency` cancel-in-progress, pip caching, cost-gated matrix legs). **The freshness checker is confirmed NOT a blocking gate**, and that is now machine-enforced rather than asserted: `test_freshness_checker_is_not_wired_into_any_gate` fails if it ever appears as an invocation in the Makefile or `ci.yml`. **6.4 release readiness**: the Definition of Done is confirmed item by item below, the `[Unreleased]` CHANGELOG section is finalized, and the version bump, changelog stamp, tag, push, and GitHub Release are HANDED to `/update release` and were NOT run. This phase performed no version bump, tag, merge, or push.

### v3.15.5 Definition of Done: confirmation

| DoD item | Status |
|---|---|
| `/tune-prompting` runs end to end on demand (enumerate, fan out, verify, write profiles, propose and guard-gate edits, land on a branch, emit the report) | MET as shipped machinery. The command sequences all ten steps and every deterministic stage is tested; the live web research itself is agent behavior, recorded as MT-3. |
| The profile layer exists, is schema-valid (hard-gated in `make validate`), auto-distributes via the installer, and carries a freshness marker | MET. Verified by a throwaway-profile install landing all bundle files, plus the structural gate in `make validate` and CI. |
| The model-specific vs model-agnostic classifier is tested, and a model-specific finding provably cannot reach a shared body | MET IN SUBSTANCE, with the mechanism corrected. The classifier is tested exhaustively and the engine's rail provably blocks any edit that would introduce a model identifier. The DoD's parenthetical "(parity guard proves it)" is FALSE and was disproved with evidence; the accurate claim is that this FEATURE cannot autonomously write model-specific content into a shared body. The hand-edit residual is accepted: see DF-2. |
| The auto-apply loop is branch-isolated, guard-gated, auto-reverts a guard-failing edit, and never commits to `develop` or `main` | MET. Each property has a dedicated test, including one asserting `develop` carries no commit from a run. |
| `/update release` carries an advisory, self-gating, offline-degrading staleness step that never blocks a release | MET, and machine-enforced by the not-wired-into-any-gate test. |
| `make validate`, `make test`, and ShellCheck green; both installers register the new repo-level scripts; the skill is registered in the three `data/` files | MET. All 14 validate gates exit 0; the two repo scripts are in both installers (verified by running the real `install_templates` functions); the skill is registered and the counts are consistent at 269. |

### v3.15.5 Open Items

#### Not implemented (deferred to a later phase by design)

##### ~~NI-4~~ (RESOLVED in Phase 6.1) - AGENTS.md and README still carry the pre-registration catalog counts

- **Source phase**: v3.15.5 Phase 4.3.
- **Plan reference**: Phase 6.1 ("Correct AGENTS.md + README: the new `ai-development` skill count, the new command, and the coverage/what-distributes tables").
- **Reason**: Phase 4 registered the skill in the three `data/` files, which is where the plan scopes registration. The prose count surfaces are Phase 6.1's job and still read the old values: `AGENTS.md` says "268 skills" in its Repository Overview and again in the project-structure comment, and says "16 commands"; `README.md` carries the count in three places. Nothing fails, because no gate cross-checks prose counts against the registry (the new `test_registry_consistency.py` deliberately covers the machine-readable files only, since prose phrasing varies too much to assert safely).
- **RESOLVED in Phase 6.1**: all five prose count surfaces now read 269 skills and 17 commands (`AGENTS.md` Repository Overview and project-structure comment; `README.md` lines 9, 33, 181). `docs/CATALOG-COVERAGE.md` carries no counts. No platform-coverage table needed a change, because the new skill and command reuse existing distribution channels rather than adding a surface. A prose-count guard was considered and NOT added: phrasing varies too much across these five sentences to assert safely, and the machine-readable counts are already guarded by `tests/validators/test_registry_consistency.py`. The README "What's New in v3.15.5" section is left to `/update release`, per the v3.15.4 precedent.

##### ~~NI-3~~ (RESOLVED in Phase 4.3) - the skill exists on disk but is not in the three `data/` registry files until Phase 4.3

- **Source phase**: v3.15.5 Phase 2.1.
- **Plan reference**: Phase 4.3 ("Register the skill": one row in `data/SKILL_INDEX.md`, one entry in `data/skills.json`, and the `ai-development` / total counts in `data/marketplace.json`).
- **Reason**: Phase 2 creates `SKILL.md`, so the catalog now carries 269 skills on disk while `data/skills.json` still lists 268. This is the plan's intended sequencing (register once the skill is complete, not while it is half-built), and no gate cross-checks the on-disk count against the registry, so nothing fails. The practical consequence in the interim is that discovery paths reading `data/` (the MCP skill server, `/skills list`, the `{{SKILL_INDEX}}` block in each platform's instruction file) will not surface the skill, while the file-tree install would copy it.
- **RESOLVED in Phase 4.3**: the skill is registered in all three files. The catalog now reads a consistent 269 skills across disk, `skills.json` entries, `skills.json.statistics`, and `marketplace.json`, and `data/`-driven discovery (the MCP skill server, `/skills list`, the `{{SKILL_INDEX}}` block) surfaces it. Registering it also exposed pre-existing count drift in `skills.json` and `SKILL_INDEX.md`, which was corrected and is now guarded by `tests/validators/test_registry_consistency.py`. The prose counts in AGENTS.md and README remain Phase 6.1's job: see NI-4.

##### ~~NI-1~~ (RESOLVED in Phase 2.1) - the profile layer is not yet distributed, because the skill has no SKILL.md until Phase 2

- **Source phase**: v3.15.5 Phase 1.1.
- **Plan reference**: Phase 1.1 ("both are referenced from the SKILL.md scaffold created in Phase 2 (leave a placeholder reference note for now)") and Phase 2.1 (scaffold the skill).
- **Reason**: Phase 1 intentionally ships the bundle data with no `SKILL.md`. `scripts/validate_skills.py::find_skill_dirs` discovers a skill only by the presence of `SKILL.md`, so the directory is currently invisible to the catalog validators (no orphan-bundle warning, no placeholder-lint error, no registry drift) and is not picked up by the installer's skill enumeration. This is the desired intermediate state: an unfinished skill must not surface in the catalog. `references/schema.md` carries the forward reference so Phase 2 wires `SKILL.md` to `schema.md`, `profiles-index.json`, and `claude-opus-5.md`.
- **RESOLVED in Phase 2.1**: `SKILL.md` now exists and references `references/schema.md`, `references/research-runbook.md`, `references/models/claude-opus-5.md`, `assets/profiles-index.json`, `assets/research-workflow.js`, and `scripts/write_model_prompting_profile.py`. The bundle is therefore discoverable by the installer's skill enumeration and is now under the orphan-bundle audit, which reports 0 unreferenced files for it. Registry visibility is a separate, still-open item: see NI-3.

##### NI-2 - three of four rostered models are UNVERIFIED (no profile), and the one seed claim is unverified

- **Source phase**: v3.15.5 Phase 1.1.
- **Plan reference**: Phase 1.1 ("Seed one real current model ... otherwise hand-seed one entry with a TODO") and Phase 2.2 (the research fan-out that writes real profiles).
- **Reason**: the recorded roster carries four model ids; only `claude-opus-5` has a profile, and its single claim is tagged `confidence: unverified` with a TODO note because no adversarial-verify pass has run. Writing claims tagged as verified without running the verification would be fabrication, so the seed is honest about its status instead. The validator deliberately treats a rostered-but-unprofiled model as a note, not a failure.
- **Suggested next step**: Phase 2.2's research fan-out profiles the remaining models and re-verifies the seed claim (re-fetch the primary source, confirm the URL resolves, refute-test, re-tag confidence). Phase 3.3 emits an UNVERIFIED-model known-gaps entry per run, which supersedes this item.

#### Deferred

##### DF-2 - model-specific content in a shared body is unguarded against HAND edits (the engine rail binds only the engine)

- **Source phase**: v3.15.5 Phase 3.1.
- **Plan reference**: the plan's Overview and Definition of Done ("a model-specific finding provably cannot reach a shared body (parity guard proves it)").
- **Reason**: the plan's premise is false (see the Phase 3 paragraph above for the three-case evidence). The rail was therefore implemented in the apply engine, which makes the accurate claim: **this feature cannot autonomously write model-specific content into a shared body**. It is NOT the stronger claim that model-specific content cannot exist in a shared body, because a human hand-editing a `SKILL.md`, a command, or a `base-*.md` bypasses the engine entirely. A catalog-wide model-name gate was considered and deliberately not added in this phase: the catalog already carries pre-existing model mentions (6 matches across the `base-*.md` set and 10 SKILL.md files), several of them legitimate (`model-routing` documents tiers by name, `claude-api` names model ids), so such a gate would fail on day one and triaging those mentions is a separate decision with its own scope.
- **Suggested next step**: decide in Phase 6 (or as its own cycle) whether to add a repo-internal `check_model_specific_leakage.py` gate. It would need an allowlist for legitimate mentions and a triage pass over the 16 existing ones. It would need NO installer edit (it belongs in the `DEV_ONLY_SCRIPTS` allowlist in `catalog/hooks/tests/test_installer_smoke.py`, alongside the three existing repo-internal guards). Until then, the residual is documented rather than closed.
- **DISPOSITION (Phase 6.2/6.4): ACCEPTED as a documented residual, and the DoD wording corrected in the confirmation table above.** The maintainer deferred this decision to Phase 6, and the call is to accept rather than build the catalog-wide gate in this release, for three reasons. First, the DoD's *intent* is met: the autonomous path (the only one this release creates) provably cannot write model-specific content into a shared body, proven by a paired test rather than asserted. Second, the gate's blocking cost lands on pre-existing content, not on this feature: 6 matches across the `base-*.md` set and 10 SKILL.md files would fail on day one, several legitimately (`model-routing` documents tiers by name, `claude-api` names model ids), so shipping it would mean either a triage pass over unrelated skills or an allowlist large enough to blunt the guard. Third, the residual is bounded and visible: it is a human hand-edit, which already goes through review, and the corrected mechanism is now documented in three places (`references/edit-routing.md` with the three-case evidence, the SKILL.md hard-rail section, and the `/tune-prompting` command's safety posture) so no future reader inherits the false premise. **Carried forward, not closed**: a repo-internal `check_model_specific_leakage.py` remains the right long-term fix. It needs no installer edit (the `DEV_ONLY_SCRIPTS` allowlist in `catalog/hooks/tests/test_installer_smoke.py` covers repo-internal guards, with three precedents) but does need the triage pass. Recorded here for the next `/plan` ingest rather than as a v3.15.5 blocker.

##### DF-1 - the new CI gate rides the existing validate job instead of a separately path-filtered job

- **Source phase**: v3.15.5 Phase 1.5.
- **Plan reference**: Phase 1.5 ("Create or update the CI workflow to run the new validator and pytests, with a path filter scoped to the skill bundle + the two scripts").
- **Reason**: DEVIATION from the literal wording, taken in service of the plan's own stated CI-optimization goal. `ci.yml` already triggers the `validate` job on any non-docs change (the workflow-level `paths-ignore: docs/**` covers `catalog/**` and `scripts/**`), and it already carries concurrency cancel-in-progress plus pip caching. A dedicated path-filtered job for two fast stdlib scripts would add a cold runner (checkout plus setup-python) rather than save action minutes, so the validator was added as a step in the existing `validate` job and the pytests ride the existing `tests/validators` step. Same decision and rationale as v3.15.1 QG-1, v3.15.2 DF-1, and v3.15.4 Phase 6.3.
- **Suggested next step**: revisit in Phase 6.3 (the CI optimization pass) only if the profile-layer checks grow expensive enough to justify their own runner. Non-blocking.

#### Missing tests / coverage gaps

##### ~~MT-1~~ (RESOLVED in Phase 5.3, as a side effect) - the `make validate` wiring and the new CI step are not asserted by any test

- **Source phase**: v3.15.5 Phase 1.2 and 1.5.
- **Plan reference**: Phase 1.2 ("Wire it into the `make validate` target so a malformed profile fails the build").
- **Reason**: the validator itself is covered by 62 tests, but nothing asserts that the `Makefile` `validate` target and the `ci.yml` `validate` job actually invoke it. A future edit could silently drop either line and every test would still pass. The repo has no existing precedent for asserting Makefile-target or CI-step contents (no other gate is guarded this way), so this is a pre-existing class of gap rather than a new one. `make` is also not installed on the dev host, so the target cannot be executed locally to prove the wiring.
- **RESOLVED in Phase 5.3**, without being the goal of that phase. `tests/skills/test_release_staleness_step.py::test_the_structural_sibling_IS_wired_into_every_gate` asserts that `verify_model_prompting_profiles.py` appears in BOTH the `Makefile` and `ci.yml`, which is exactly what this item asked for; its paired test asserts the advisory checker does NOT. So the wiring for this release's gate is now machine-checked in both directions. The broader generalization (a guard covering every `scripts/*.py` gate name, in the shape of `test_installers_copy_every_scripts_dir_py_file`) remains un-built and is a pre-existing catalog-wide gap rather than a v3.15.5 one; it is not carried forward as a v3.15.5 item.

##### MT-4 - the apply loop's DEFAULT guard suite is not exercised end to end; tests inject fake guards

- **Source phase**: v3.15.5 Phase 3.4.
- **Plan reference**: Phase 3.2 ("run the full guard suite") and 3.4 ("the per-edit guard loop with an injected guard failure").
- **Reason**: the loop's control flow (apply, guard, keep-or-revert, quarantine, continue) is fully tested with injected pass/fail guards, which is what keeps the tests fast and deterministic. Running the real five-gate suite once per edit takes minutes, so no test executes `DEFAULT_GUARDS` end to end. **The realistic half of this gap was closed in-phase**: `test_every_default_guard_points_at_a_script_that_exists` asserts each default guard names a `.py` script that is actually present, and `test_the_default_suite_covers_the_gates_the_plan_requires` pins the three gates the plan names. A renamed or moved gate now fails at test time instead of quarantining every edit on a live run.
- **Suggested next step**: what remains is a genuine end-to-end run of the real suite (one slow-marked test applying a trivial edit under `DEFAULT_GUARDS`). Phase 6.3 is the natural home. Non-blocking, and the failure direction is safe: a broken guard quarantines edits rather than letting them through.

##### MT-3 - the research fan-out itself is agent behavior over live web calls and is not unit-run

- **Source phase**: v3.15.5 Phase 2.2 and 2.4.
- **Plan reference**: Phase 2.4 ("Test the deterministic parts without live web calls ... use fixtures/mocks for search/fetch results").
- **Reason**: the middle of the pipeline (search, fetch, extract claims, refute) is irreducibly agent work against live vendor documentation, so it cannot be asserted deterministically. What IS covered: the two deterministic ends (the planner's work-list mapping and the writer's validate-and-merge, 91% branch coverage, cross-checked against the repo structural gate) and static assertions that the workflow template carries the three mandatory rules, its cross-links, the budget kill switch, every degradation rung, and no runtime-forbidden clock or RNG call. What is NOT covered: that a real fan-out actually retrieves primary sources, that the refuter panel rejects a bad claim in practice, and that the degradation ladder selects the right rung at runtime. This mirrors the v3.15.4 MT-3 precedent, where the structural scorer was the unit-tested backbone of an otherwise behavioral visual-QA loop.
- **Suggested next step**: the first real `/tune-prompting` run (Phase 4 onward) is the behavioral proof, and its output is reviewable because every claim carries a citation. If stronger coverage is wanted later, record a fixture of captured search/fetch responses and replay it through a single sequential-agent run. Non-blocking.

##### MT-2 - subprocess-invoked validator tests need explicit coverage plumbing, so coverage is not measured in CI

- **Source phase**: v3.15.5 Phase 1.5.
- **Plan reference**: Phase 1.5 (stabilization) and the implement-phase coverage gate.
- **Reason**: `tests/validators/conftest.py` runs each validator as a SUBPROCESS (deliberately, so the tests exercise the real CLI surface end users run), so a plain `pytest --cov` collects nothing from the scripts under test. Coverage for this phase was measured out-of-band with `COVERAGE_PROCESS_START` plus `coverage combine` (94% validator, 97% freshness checker, 97% combined, branch coverage on), but CI does not run coverage for `tests/validators` at all, so the number is enforced nowhere. This affects the entire pre-existing `tests/validators` suite, not only the two new scripts.
- **Suggested next step**: if coverage enforcement is wanted for this suite, add the `COVERAGE_PROCESS_START` plumbing to the CI `tests` job once, for the whole `tests/validators` tree. Non-blocking; behavioral coverage is strong, since every documented structural rule has a dedicated failing-case test.

### v3.15.5 reconciliation summary (Phase 6.2)

**RESOLVED (4)**: NI-1 (bundle undistributed until SKILL.md existed, closed in Phase 2.1), NI-3 (skill unregistered, closed in Phase 4.3 along with the pre-existing count drift), NI-4 (prose counts, closed in Phase 6.1), MT-1 (the `make validate` / CI wiring unasserted, closed as a side effect of Phase 5.3's paired gate tests).

**OPEN and carried as documented, non-blocking items (6)**: NI-2 (three of four rostered models UNVERIFIED and the seed claim unverified; resolves on the first real `/tune-prompting` run, which needs web access and is user-initiated), DF-1 (the CI gate rides the existing `validate` job rather than a dedicated path-filtered one; the same call recorded at v3.15.1 QG-1, v3.15.2 DF-1, and v3.15.4 Phase 6.3), DF-2 (model-specific content in a shared body is unguarded against HAND edits; ACCEPTED with the DoD wording corrected, and the catalog-wide leakage gate carried forward for a future `/plan` ingest), MT-2 (subprocess coverage plumbing is not run in CI for the whole `tests/validators` tree), MT-3 (the research fan-out is agent behavior over live web calls and is not unit-run; the deterministic ends are at 88-97% and the template's rules are statically asserted), MT-4 (the DEFAULT guard suite is not executed end to end, though its realistic half was closed in-phase by asserting each default guard names a script that exists).

**None of the open items is a release blocker.** The two that would matter most if left silent, DF-2's corrected mechanism and MT-4's guard-name check, were both handled in-phase: the first by documenting the real rail in three places and proving it with a paired test, the second by closing the half that catches the realistic failure.

### v3.15.5 Advisory (pre-existing, not introduced by this phase)

- **Repo-wide test failures on the Windows dev host are pre-existing and were baseline-verified.** A detached worktree at `develop` (`b613b251`) reproduces exactly the same failures as the feature branch: `catalog/hooks/tests` 99 failed / 361 passed / 36 skipped (identical counts), `tests/validators/test_session_query_extract.py::test_discover_obsidian_vault_marker` 1 failed, and `tests/installer/test_branch_flag.py` 3 failed. These trace to the documented WN-v36-1 constraint (bash cannot be fully exercised on the Windows dev host) and are covered on Linux in CI. Phase 1 introduced zero new failures.
- **The two pytest trees must be run as SEPARATE invocations.** Running `pytest catalog/hooks/tests tests` as one command makes pytest adopt a nested `pyproject.toml` as rootdir and breaks module discovery, producing a large and misleading failure count. `ci.yml` already runs them as separate steps and documents why; it is noted here because the combined form is an easy mistake to repeat locally.
- **The unicode-safety validator reports 1051 warnings across the repo (0 errors).** Pre-existing non-ASCII punctuation, mostly em dashes in `AGENTS.md` and other docs. Warning-only, exit 0, and untouched by this phase.

## v3.15.6 - adoption-sandbox-escapes

**Status**: ALL 4 PHASES COMPLETE on `feat/adoption-sandbox-escapes`; release-ready, pending the user-driven `/update release`. This subsection is finalized. Plan: [plans/v3.15.6-adoption-sandbox-escapes.md](plans/v3.15.6-adoption-sandbox-escapes.md). Comparison: [comparisons/v3.15.6-comparison-sandbox-escapes.md](comparisons/v3.15.6-comparison-sandbox-escapes.md).

**Phase 1 (skill-native foundation: AC1, AC7, AC6 guidance) COMPLETE.** Authored a new `catalog/skills/security-operations/agentic-endpoint-hardening/` bundle: `SKILL.md` (244 lines, under the 500-line norm) carrying the config-write-then-executed three-step model, a six-form escape taxonomy with a why-it-slips-through column, the normative execution-trigger surface list, nine control layers each marked enforced / advisory / guidance-only, a privileged-local-daemon enumeration section, a seven-question platform audit checklist, a Limits and Honest Boundaries section, nine Common Rationalizations, ten binary Verification items, and seven Related Skills cross-links; `references/standards.md` (source provenance plus the framework mapping); and `evals/trigger-cases.json` (6 positives + 4 near-miss negatives drawn from the SKIP clause). Declared the optional framework fields `mitre_attack: [T1546, T1059, T1611]`, `d3fend_techniques: [D3-FA, D3-FH, D3-PA]`, and `nist_csf: [PR.PS, DE.CM]`; every identifier was cross-checked against existing verified in-repo usage (with live source URLs) rather than asserted from memory, so no invented ID ships in a security artifact. Per the Reverse-Engineering Attribution Rule the vendor, its framework, and its commercial product are named ONLY in `references/standards.md` and the policy matrix, never in the skill body, which describes component classes rather than product versions so it stays accurate as vendors patch. Registered by hand in the three registry files (no catalog rebuild): a row in `data/SKILL_INDEX.md`, a full entry in `data/skills.json`, and the security-operations `skill_count` bumped 15 -> 16 in `data/marketplace.json`. Catalog now reports a consistent **270 skills** across all four surfaces (`skills.json` array length 270, `statistics.total_skills` 270, marketplace category-sum 270, `SKILL_INDEX.md` 270 rows), verified programmatically along with zero duplicate names and exact per-category and per-priority agreement. Added a seven-row `docs/policy/mcp-reverse-engineering-matrix.md` section covering all seven candidates (AC1 and AC7 `skill-native`, AC2 / AC4 / AC5 `re-full`, AC3 `re-partial`, AC6 mixed) plus the two drop-outright rows (the vendor's commercial endpoint product and its framework adopted verbatim), each recording that no outbound call, API key, third-party data processor, or runtime dependency is introduced.

**Gates green.** All 13 `make validate` validators PASS individually (`make` is unavailable on this Windows host, so each was invoked directly); bundle audit PASS (0 errors, 6 pre-existing warnings, none in this skill); `run_trigger_evals.py --gate` PASS (0 un-allowlisted collisions, 0 routing failures across 9 skills with cases); compression accuracy gate PASS; catalog skill-security scan PASS (0 HIGH/CRITICAL); shellcheck PASS; a mechanical markdown style self-check PASS on all four touched Markdown files. Discoverability was verified end-to-end rather than inferred from counts: the skill-server catalog loads 270 skills, `get_skill("agentic-endpoint-hardening")` returns the record with the correct category, and the frontmatter parses as real YAML with `summary_l0` at 12 words and `overview_l1` at 146 words (both inside their norms). CI needs no edit: the existing `validate` job already covers skill validation, the routing gate, and registry integrity, and is already optimized (workflow-level `paths-ignore: docs/**` so `catalog/**` + `data/**` + `scripts/**` trigger it, `concurrency` cancel-in-progress, pip caching, and cost-gated macOS / Windows matrix legs).

**Documented deviations from the plan text (all additive, none reducing scope).**

- **D1 (materially improves Phase 2's implementability).** The plan lists the canonical execution-trigger paths as one flat list including `core.hooksPath` and `core.fsmonitor`, and sub-task 2.1 asks `escalation-trigger.sh` to cover them. That hook only ever receives a file path (`CLAUDE_FILE_PATH`) and can never match a git config key, so a single flat list makes 2.1 unimplementable as literally written. The skill therefore defines the list in THREE groups keyed by matching input: group A file paths and group C interpreter paths (both matched against a write or edit target, so `escalation-trigger` owns them), and group B command-string patterns (matched against a shell command, so `git-guardrails` owns them). `.git/config` was added to group A as the mechanical consequence of `core.hooksPath` being agent-writable, since writing that key into the config file is a file write. Phase 2 should route the groups accordingly.
- **D2.** The plan says to state that "Phases 2 and 3 reuse this exact list". A distributed skill has no "Phase 2" for its reader, so the normative section instead names the concrete consumers (the `escalation-trigger` advisory, the `git-guardrails` command guardrail, and the opt-in strict permission stub) and states that a change must propagate to them. The intent (declare the list authoritative and name its consumers) is fully implemented and is more useful to both the end user and the Phase 2 implementer.
- **D3 (departure from precedent, deliberate).** The five prose skill-count surfaces (`AGENTS.md` lines 11 and 27, `README.md` lines 9, 33, and 185) were corrected 269 -> 270 in THIS phase, whereas v3.15.3 deferred count-surface reconciliation to `/update release` and v3.15.5 fixed it in its final phase as NI-4. Reasoning: this phase created the drift, the fix is five single-token edits, and leaving the repo advertising 269 while shipping 270 across three further phases is a worse state than a slightly early fix. `/update release` re-verifying them is idempotent. The hook count (28) was deliberately NOT touched, because Phase 3 adds the provenance-ledger hook and should own its own count bump. The README "What's New in v3.15.5" release-notes line was correctly left alone.

**Phase 2 (advisory enforcement: AC2, AC4) COMPLETE.** Extended `escalation-trigger.sh` with groups A and C of the canonical surface list, hardened `git-guardrails.sh` with group B, created both net-new PowerShell siblings, and added 154 passing tests. **The phase found and fixed two real defects that the plan text did not anticipate, and both mattered more than the feature work.** First, `escalation-trigger.sh` was **inert in production**: it read the path only from `$CLAUDE_FILE_PATH`, an environment variable Claude Code does not set, while all nine sibling Write/Edit hooks read the path from the stdin JSON payload. Proven empirically (a stdin payload produced no output; the env var produced a warning), so the hook had never warned on anything. Adding escape paths to it would have shipped exactly the "coverage that reads as coverage but matches nothing" failure the Phase 1 skill warns about, and Phase 1's own Verification item ("the signal was seen firing, not assumed") is unsatisfiable while the hook cannot read its input. The input contract now reads stdin JSON (`jq` with a `grep`/`sed` fallback, matching the sibling convention) and retains the env var as a documented fallback so an existing setup that exports it keeps working. Second, the `.sh`/`.ps1` parity test caught that the text fallback does not decode JSON escapes, so a Windows path arrived with doubled backslashes and the separator normalization turned each `\\` into `//`, defeating every glob; the `.ps1` was correct because `ConvertFrom-Json` decodes properly. Fixed by decoding the backslash escape in the fallback branch only (the `jq` branch needs no such step). Both defects are recorded as BG-1 and BG-2 below.

Beyond the two fixes: the init carve-out is implemented as a writer-identity signal (`NEXUS_HUB_INIT=1` suppresses the advisory for the five surfaces `nexus-hub init` actually owns, verified not to over-suppress `.git/hooks/*`), which is the control the Phase 1 skill prescribes because a legitimate installer write and a hostile one produce an identical file. The default action stays `warn`, tested explicitly, so the catalog can never self-block its own wiring. `git-guardrails` gained the two inline `git -c core.hooksPath= / core.fsmonitor=` patterns written to tolerate interleaved `-c` options (so `git -c protocol.version=2 -c core.hooksPath=x` is not an evasion) plus a separate persistent-`git config` check that deliberately excludes the read forms, because flagging `git config --get core.hooksPath` would be a false positive on a diagnostic command. The argv-decomposition limitation is documented in both hook headers and in the skill. No hook file needed a `settings.json` change: the `.ps1` files are siblings of already-registered hooks (matching the five pre-existing `.ps1` hooks, none of which is registered), so the logical hook count stays 28 and Phase 3's genuinely-new provenance hook owns the bump to 29.

**Gates green.** ShellCheck 0 warnings on both modified hooks (and across all 35 catalog `.sh` files); PowerShell AST parse clean on both new siblings; the full `catalog/hooks/tests` suite is **614 passed / 36 skipped / 0 failed**, up from a 460-passed baseline, so Phase 2 contributes exactly 154 passing tests. Every behavioral assertion runs against BOTH implementations through a parametrized `run` fixture, which is what makes the suite the parity check rather than a separate manual step (the plan asked for manual confirmation in 2.3; a skip-guarded parametrized test is strictly stronger and needs no human in the loop). All 10 validators pass, including `validate_no_personal_paths.py`, which caught a placeholder home-directory path in the new test file (changed to a neutral `/srv/project/...` form). CI needs no edit to cover the work (the `tests` job already runs the whole hook suite and the `shellcheck` job already lints every catalog `.sh`); two optional hardening diffs were proposed rather than applied silently, and are recorded as QG-1.

**Phase 2 documented deviations.**

- **D5 (necessary to deliver the stated intent).** Fixing `escalation-trigger.sh`'s input contract is beyond the literal text of sub-task 2.1, which asks only to extend the path list. It is not optional: the sub-task's objective is that writes to the escape surfaces "trigger the advisory", which is impossible while the hook cannot read its input. The env-var fallback is retained so the change is backward compatible.
- **D6 (test-infrastructure addition).** Added `catalog/hooks/tests/conftest.py` with `bash_bin` and `powershell_bin` session fixtures that probe for a working interpreter, and converted `test_git_guardrails.py` to use them. This is why Phase 2's tests pass on the Windows dev host without manual PATH help, and it resolves HO-1 for the two files that use it. The fixtures only DEFINE behavior (no pytest hooks, no collection changes), so they are inert for the tests that do not request them.

**Phase 3 (hard enforcement and monitoring: AC5, AC3) COMPLETE.** Shipped the opt-in hardened permission posture and the best-effort provenance ledger, plus both PowerShell siblings and 65 tests. **Two schema and correctness problems were resolved before writing anything, and the parity tests then caught two more real defects.**

**The plan's `defaultMode` instruction was wrong and is deliberately not implemented.** Sub-task 3.1 says to set `defaultMode` to "ask/deny", but that key takes permission MODES (`default`, `acceptEdits`, `plan`, `bypassPermissions`), not the sibling array names, and `defaultMode` appears nowhere in `guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md` while the in-flight v3.17.0 autonomy plan schedules confirming its value set as unstarted work. Writing an unverified enum into a user's `settings.json` is a schema bet with no upside, since `default` is already Claude Code's behavior. The overlay therefore ships `deny` and `ask` only (both confirmed with worked examples in that reference) and a test asserts `defaultMode` stays absent. Recorded as DF-3 so v3.17.0 Phase 2 can revisit it once the enum is verified.

**The overlay is an overlay, not a second copy.** The plan says the flag installs the strict stub "instead of" the default. Implemented as base-plus-overlay: `claude-permissions-strict.json` carries ONLY `deny` and `ask`, and the installer merges it on top of the existing allow list. The alternative (duplicating the 15KB read-only allow list into a second file) would give the catalog two sources of truth that silently drift. A test asserts the overlay carries no `allow` key. The posture is identical; the maintenance burden is not.

**The deny-versus-ask split is a real decision, not a dump.** `deny` holds the surfaces where an agent write is essentially never legitimate and the blast radius is a trusted executor running code at host privilege: version-control hooks and config, interpreter and virtual-environment paths, and the group B git commands. `ask` holds the surfaces an agent DOES legitimately touch (harness settings and hooks, editor task and launch config, editor rules), where a hard deny would break real workflows but silent approval is the exact escape being defended against. That mirrors control layer 3 of the skill (require approval for host-side automation), and a test asserts the two lists do not overlap. A separate finding that shaped this: the permission config governs the AGENT's tool calls, not the installer's own file I/O, so denying `.claude/settings.json` does NOT break `nexus-hub init`.

**Two defects the `.sh`/`.ps1` parity tests caught in the provenance ledger.** First, `Add-Content -Encoding utf8` writes a UTF-8 BOM on Windows PowerShell 5.1, which made the ledger's first field unparseable as an integer AND broke format parity, which matters because both implementations can append to the same ledger file; fixed with BOM-less `UTF8Encoding($false)` writes, matching the installer's own `Write-JsonFile`. Second, GNU coreutils `sha256sum` escapes a filename containing a backslash and prefixes the whole output line with `\`, so a Windows path produced a 65-character hash with a leading backslash; fixed by hashing via stdin, which removes the filename from the output entirely. Neither defect is reachable by a POSIX-only test, and both were found by running the same assertions against both implementations.

**The provenance ledger's boundary is documented, not glossed.** It records a timestamp, a content hash, and a path, one line per agent write, and NEVER file contents (tests assert a planted secret never reaches the ledger or the hook's output). Correlation is capped to the current session by construction (a test proves a second session sees nothing from the first), the ledger is line-capped, and hashing is size-capped so per-write overhead is bounded. The correlation heuristic is stated plainly in the hook and the skill: it matches a path or basename anywhere in the command string, so it over-reports (a path mentioned as an argument reads like one being executed) and under-reports (a path reached through a variable or wrapper is invisible). It is a tripwire, not a determination that execution occurred. The un-achievable half (instrumenting executors in other processes) is the explicitly dropped part of the `re-partial` classification.

**Gates green.** ShellCheck 0 warnings on the new hook and both installers; PowerShell AST parse clean on both new `.ps1` files; all 11 validators pass; catalog security scan clean; all 6 touched JSON files parse; 65 new tests pass (44 provenance-ledger across both implementations, 21 strict-permissions). The one ShellCheck warning encountered (an unused timestamp field) was resolved by USING the value rather than silencing it, so the advisory now reports how long ago the path was written, which materially changes how a reader judges it. An IDE diagnostic for an unused variable in the `.ps1` was likewise resolved by making `tool_name` the explicit branch discriminator instead of inferring the branch from which field happens to be present, which also removes a real ambiguity for a payload carrying both.

**Phase 3 documented deviations.**

- **D9 (plan schema error, not implemented as written).** `defaultMode` omitted; see the paragraph above and DF-3.
- **D10 (better than as written).** The strict stub is a deny/ask overlay merged on top of the base allow list, rather than a full replacement file, so the allow list keeps one source of truth.
- **D11 (call-site placement).** The strict merge is invoked from the call site rather than inside `install_permissions` / `Install-Permissions`, because those functions return early in their allow-merge path (jq missing, nothing new to add, merge failed) and would have silently skipped the overlay in the common "allow list already up to date" case.
- **D12 (HO-2 scoped honestly).** `NEXUS_HUB_INIT=1` is exported from `init` in both installers as asked, but the comment states plainly what it does not achieve: Claude Code's Write/Edit hooks observe the agent's tool calls, not the installer's process, so `init`'s own writes never reach that hook. See HO-2 below, now resolved with that caveat recorded.

**Phase 4 (terminal gate: architecture refactor, known-gaps reconciliation, CI/CD) COMPLETE.** The final phase, so the mandatory 9.0 gate ran and the release-readiness workflow follows; the version bump, changelog finalization, tag, and push are HANDED to `/update release` and were NOT performed here.

**4.1 refactor: a verification pass, clean.** The detectors found nothing to apply, which is the expected outcome for a purely additive plan. No empty directories under any path this plan touched, no duplicate content among the 15 added files (compared by SHA-256), the new skill bundle in the conventional `SKILL.md` + `references/` + `evals/` layout, the docs tree still canonical (`comparisons/`, `development/`, `plans/`, `known-gaps.md`), and every hook, sibling, test, and registration in its conventional location. No committed file moved, so no reference repair was needed. One survey result recorded rather than acted on: `catalog/hooks` now carries 8 `.ps1` siblings for 25 `.sh` hooks (this plan added 3); the other 17 are pre-existing and out of scope.

**4.2 known-gaps: every item has a disposition** (below). Two resolved in this phase (DF-2, QG-1), one transferred with a named owner (DF-3 to v3.17.0 Phase 2), one carried as a documented deferral (DF-1), and the two scope boundaries the plan required be tracked explicitly rather than left in prose are now NI-1 and NI-2. Co-resident coordination: the v3.15 minor tree holds eight plans (v3.15.0 through v3.15.7). None of v3.15.5's six carried deferrals interacts with this feature set (its DF-2 concerns model-specific content in shared skill bodies, a different mechanism entirely), and v3.15.7 is unstarted, so nothing needed transferring between sections. This subsection is final for v3.15.6; the file as a whole stays open while v3.15.4, v3.15.5, and v3.15.7 remain in flight.

**4.3 CI/CD: three changes, all evidence-driven.** Both QG-1 diffs applied, closing it: the `.ps1` AST-parse gate (new, unconditional, because the parametrized hook tests SKIP when no PowerShell interpreter is present and a skip emits no signal) and the removal of the `|| true` that made the catalog `shellcheck` step decorative rather than enforcing (safe now: all 36 catalog `.sh` files pass `--severity=warning` with zero warnings, so the gate starts green). Third and most consequential, a new push-only `tests-windows` job runs the hook suite plus the installer and validator suites on a real Windows host. **That job exists because of a demonstrated miss, not for symmetry**: the Phase 3 ledger BOM defect is specific to Windows PowerShell 5.1 and does NOT reproduce under the ubuntu leg's pwsh 7, so CI as previously configured would have passed a ledger that was unparseable on every Windows user's machine. The fixture otherwise prefers pwsh, so the job pins the edition with a new `NEXUS_TEST_POWERSHELL` variable, giving coverage of BOTH editions across the two legs (ubuntu: pwsh 7; windows: 5.1) instead of testing one twice. Cost is controlled the same way the existing Windows and macOS legs are: pushes only, never on pull requests.

**4.4 validation.** Full suites green with no PATH assistance: `catalog/hooks/tests` 658 passed / 36 skipped / 0 failed, and `tests/installer` + `tests/validators` green (see 4.4 evidence in the session history). All 11 validators pass, catalog security scan clean, ShellCheck 0 warnings across all 36 catalog `.sh` files plus both installers, PowerShell AST parse clean on all 8 catalog `.ps1` files, and `ci.yml` parses with its seven jobs intact. No behavior changed in this phase beyond the DF-2 test-infrastructure repair, which only makes previously-environmental failures pass.

**Phase 4 documented deviation.**

- **D13 (better than as written; the outcome the instruction wanted).** DF-2's remedy was approved as "convert the ~17 hook test files to the `bash_bin` fixture". Converting each file's module-level `shutil.which("bash")` and `skipif` into fixture plumbing is a wide diff across varied patterns with real risk to existing assertions. Implemented instead as a PATH repair at `conftest.py` module level: pytest imports `conftest.py` before any test module, so repairing `os.environ["PATH"]` there fixes every `shutil.which("bash")` and every `subprocess.run(["bash", ...])` in all 11 files with ZERO edits to them, and keeps working for files added later. Verified by running the full suite with no PATH help: 658 passed / 0 failed, against 91 failed before. The same repair was added at `tests/conftest.py`, which was NOT in DF-2's original scope but is the same root cause, the same remedy, and de-risks the new `tests-windows` job (which runs that tree and would otherwise depend on the runner image's PATH ordering).

### v3.15.6 Open Items

#### Not implemented (scope boundaries, tracked rather than silent)

##### NI-1 - full cross-executor trust-seam instrumentation is not locally achievable (the dropped half of AC3)

- **Source phase**: v3.15.6 Phase 3.2, recorded explicitly in Phase 4.2 per the plan's instruction.
- **Plan reference**: Phase 3.2 ("Document the honest boundary ... the un-achievable cross-executor instrumentation is explicitly out of scope") and the comparison's `re-partial` classification of AC3.
- **Reason**: a hook observes the tool calls of the harness it is installed in. It cannot instrument an editor extension, a language server, a version-control integration, or any other trusted executor running in a separate process, which is precisely where the execution half of most real escapes happens. What ships is same-session correlation between an agent write and a later command, which is a genuine local audit trail and tripwire. What does not ship, and cannot without a dedicated endpoint agent, is observing the executors themselves. This is the deliberately dropped part of the `re-partial` classification, not an incomplete implementation.
- **Where it is documented for users**: the "Limits and Honest Boundaries" section of `agentic-endpoint-hardening/SKILL.md`, the header of both `provenance-ledger` implementations, and the matrix row for AC3.
- **Suggested next step**: none. Reconsider only if Nexus-Hub ever ships a component that legitimately observes other processes, which would be a different product. Recording it here prevents a future reader from mistaking the local ledger for endpoint detection.

##### NI-2 - the git guardrail is a fixed-pattern denylist, not argv decomposition (the AC4 limitation)

- **Source phase**: v3.15.6 Phase 2.2, recorded explicitly in Phase 4.2 per the plan's instruction.
- **Plan reference**: Phase 2.2 ("document the limitation honestly: this is a fixed-pattern denylist over the raw command string, not an argv decomposition") and the comparison's Step 7 conflict note.
- **Reason**: `git-guardrails` regex-matches the raw command string. It catches the specific known-bad patterns (including the interleaved `-c` form and the persistent `git config` form, with reads correctly excluded), but quoting, unusual spacing, environment indirection, and equivalent alternate flags can evade it, and a flag nobody listed passes silently. The source's own thesis applies to this hook: a denylist cannot keep pace. Building a real argv decomposition for every shell form the agent might emit is a much larger piece of work than this plan scoped, and it would still be defense-in-depth rather than a boundary.
- **Where it is documented for users**: the header comments of both `git-guardrails` implementations, the "Limits and Honest Boundaries" section of the skill, and the strict permission overlay's `_group_b_note`.
- **Suggested next step**: keep the layered posture (advisory hook + opt-in permission deny + threat-model skill) rather than pursuing completeness in the denylist. If argv decomposition is ever wanted, scope it as its own effort with a parser, not as more regexes.

#### Deferred

##### DF-3 - `defaultMode` deliberately omitted from the strict overlay pending enum verification

- **Source phase**: v3.15.6 Phase 3.1.
- **Plan reference**: Phase 3.1 ("with `defaultMode` set to ask/deny rather than auto-approve").
- **Reason**: the instruction is not implementable as written (`ask` and `deny` are sibling array keys, not `defaultMode` values), and the key's valid value set is unverified in this repo: it appears nowhere in `guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md`, and `docs/v3/v3.16/plans/v3.17.0-agent-autonomy-toggle.md` Phase 2 schedules confirming it against official documentation. Writing an unverified enum into a user's `settings.json` risks breaking their config for no benefit, because the safest documented value (`default`) is already Claude Code's behavior. The overlay ships the verified `deny` and `ask` keys instead, and a test pins the omission so it cannot drift back in accidentally.
- **Suggested next step**: after v3.17.0 Phase 2 verifies the `defaultMode` enum against official docs, decide whether the strict overlay should also set it. If yes, add it plus a test; if no, keep the omission and record the reasoning there. Non-blocking: the deny/ask entries deliver the hardening on their own.

##### DF-1 - `ai-agent-governance` carries no SKIP clause (reciprocal carve-out not added)

- **Source phase**: v3.15.6 Phase 1.1 / 1.4.
- **Plan reference**: Phase 1.1 (the description's SKIP clause fencing off deployed-service agent governance).
- **Reason**: the new skill's SKIP clause names `ai-agent-governance`'s territory in order to defer to it, which imports that skill's vocabulary into the new description's token set and produced a 50% near-collision on the pairwise detector. The pair was ALLOWLISTED (with a reason) rather than fixed in place, because routing is empirically correct in both directions: the `neg-service-governance` case routes away from the new skill, and all six positives outrank every competitor including `ai-agent-governance` (the runner's `_top_competitor` scores against every other skill). Adding a reciprocal SKIP clause to `ai-agent-governance` would be the higher-quality fix and matches the `technical-documentation` precedent, but that skill's missing SKIP clause is a PRE-EXISTING description-quality gap that this phase did not create, and editing it would also require syncing its `description` mirror in `data/skills.json`. Out of scope per the no-out-of-scope-cleanup rule.
- **Suggested next step**: in a future cycle, sharpen `ai-agent-governance`'s description with a SKIP clause deferring local coding-agent endpoint hardening to `agentic-endpoint-hardening` (and sync `data/skills.json`), making the pair mutually fenced like `oncall-runbook` / `runbook-writer`. The allowlist entry can stay either way. Non-blocking; routing is proven correct today.


#### Resolved

##### DF-2 RESOLVED - the whole bare-`bash` class is gone, and the WN-v36-1 failure set with it

- **Source phase**: raised v3.15.6 Phase 2.3, resolved Phase 4.
- **Resolution**: fixed at the root rather than per file. `conftest.py` is imported by pytest BEFORE any test module, so repairing `os.environ["PATH"]` there lands ahead of every test module's own `shutil.which("bash")` and every `subprocess.run(["bash", ...])`. One module-level repair in `catalog/hooks/tests/conftest.py` therefore fixed all 11 affected files with ZERO edits to them, and keeps working for files added later. The same repair was added at `tests/conftest.py` (outside DF-2's original scope, but the same root cause and remedy) which also de-risks the new `tests-windows` CI job, since that job runs the `tests/` tree and would otherwise depend on the runner image's PATH ordering.
- **Evidence, measured with NO PATH assistance**: `catalog/hooks/tests` 658 passed / 36 skipped / **0 failed** (was 91 failed), and `tests/installer` + `tests/validators` 516 passed / 16 skipped / **0 failed** (was 4 failed). That is the complete 103-failure set carried across several releases as WN-v36-1, now structurally resolved rather than worked around.
- **Note on the approved remedy**: the maintainer approved "convert the ~17 files to the `bash_bin` fixture". The PATH repair reaches the same outcome with a fraction of the diff and no risk to existing assertions; see D13. The `bash_bin` / `powershell_bin` fixtures are retained for tests that want the interpreter explicitly.

##### BG-5 RESOLVED - `session-summary.ps1` never parsed, so the hook was dead on Windows since v3.11.0 (PRE-EXISTING, found by the new gate)

- **Source phase**: v3.15.6 Phase 4.3, found the moment the new `.ps1` AST gate was run for the first time.
- **Reason**: line 139 read `$lines.Add("- Branch: ``$branch``")` inside a DOUBLE-quoted string, which is broken twice over because the backtick is PowerShell's escape character. `` `$branch `` emitted the literal text `$branch` rather than the value, and the trailing backtick escaped the closing quote so the string never terminated. The parser then ran on through the following lines and reported "string is missing the terminator" 23 lines later, which is why the real cause is not where the error points.
- **Impact**: a parse error prevents a script from running at all, so `session-summary.ps1` has been completely non-functional for Windows users who run hooks through PowerShell since it shipped in v3.11.0. Silent, because nothing parsed catalog `.ps1` files until this phase added the gate.
- **Resolution**: rewritten as `$lines.Add('- Branch: ``' + $branch + '``')`, using single quotes plus concatenation so no escape rules apply, and verified to render byte-identically to the `.sh` sibling's `echo "- Branch: \`$BRANCH\`"`. All 8 catalog `.ps1` files now parse clean, so the new gate starts green.
- **Scope note**: this file was NOT touched by this plan and the fix is technically out-of-scope cleanup. It is included because the alternative was worse: the phase adds an AST gate the maintainer approved, and shipping it would have meant either a red gate or an allowlisted permanent hole that leaves a known-broken hook broken. One line, root-caused rather than worked around.
- **Value of the gate, demonstrated immediately**: it found a real, silent, multi-release defect on its very first run. That is the argument for keeping it unconditional rather than relying on the behavioral tests, which SKIP when no interpreter is present.

##### QG-1 RESOLVED - both CI hardening diffs applied, plus a Windows leg

- **Source phase**: raised v3.15.6 Phase 2.3, resolved Phase 4.3.
- **Resolution**: (1) added an unconditional PowerShell AST-parse step for `catalog/hooks/*.ps1`, which matters because the parametrized hook tests SKIP without an interpreter and a skip emits no signal; (2) removed the `|| true` that made the catalog `shellcheck` step decorative, safe because all 36 catalog `.sh` files pass `--severity=warning` with zero warnings today, so the gate starts green.
- **Third change, beyond QG-1's original scope and the reason it matters**: a new push-only `tests-windows` job runs the hook, installer, and validator suites on a real Windows host, pinned to Windows PowerShell 5.1 via the new `NEXUS_TEST_POWERSHELL` variable. This is evidence-driven: the Phase 3 ledger BOM defect is specific to 5.1 and does NOT reproduce under the ubuntu leg's pwsh 7, so CI as previously configured would have passed a ledger that was unparseable for every Windows user. The pin gives coverage of both editions across the two legs rather than testing pwsh twice. Cost-gated to pushes only, matching `bootstrap-windows` and `install-smoke`.

##### HO-2 RESOLVED - `NEXUS_HUB_INIT=1` exported by both installers, with its real scope recorded

- **Source phase**: raised v3.15.6 Phase 2.1, resolved Phase 3.1.
- **Resolution**: both installers now export the marker for the `init` subcommand (`export NEXUS_HUB_INIT=1` in `installer.sh`, `$env:NEXUS_HUB_INIT = "1"` in `installer.ps1`), in lockstep per the installer-aware rule, and a test asserts both.
- **Correction recorded with it**: the export does LESS than the plan implies, and the comment in both installers says so. Claude Code's `PreToolUse` Write/Edit hooks observe the AGENT's tool calls, not the installer's process, so `init`'s own file writes never reach `escalation-trigger` and were never going to warn. The marker is an explicit intent declaration for any hook chain that DOES wrap the installer, plus lockstep parity; the carve-out's practical consumer is an operator exporting the same variable for a deliberate setup pass in an agent session.
- **Security framing, stated so it is not mistaken later**: this is a SELF-ASSERTED signal. An agent can set the variable itself, so it is not verified identity and must never be promoted to a boundary. It is acceptable only because the hook is advisory: the carve-out suppresses a warning and never grants a capability. Both hooks and both installers carry that caveat inline.

##### HO-1 RESOLVED - hook-test verification route found; the WN-v36-1 characterization was wrong

- **Source phase**: raised v3.15.6 Phase 1.4, resolved Phase 2 pre-flight.
- **Resolution**: route (b) works and the root cause is much smaller than the long-standing note claimed. The suite never needed a POSIX host: on Windows, `C:\Windows\System32\bash.exe` (the WSL launcher stub) **shadows Git Bash on PATH**, receives a Windows-style script path it cannot resolve, and exits 127 before executing a line. Putting Git Bash ahead of it takes the full hook suite from 99 failed / 361 passed to **0 failed / 460 passed** on the same machine, with no other change. The two remaining failing files outside `catalog/hooks/tests` (`tests/validators/test_session_query_extract.py`, `tests/installer/test_branch_flag.py`) also pass under Git Bash, closing all 103 of the failures previously carried as unavoidable.
- **Correction to record**: the WN-v36-1 framing repeated across several releases ("bash cannot be fully exercised on the Windows dev host", covered on Linux in CI only) is **inaccurate**. It is PATH shadowing, not host incapability, and it was diagnosable at any time by asking WHICH bash answered rather than whether bash worked. A future cycle should reword that note wherever it is cited, rather than continuing to treat 103 failures as environmental.
- **Durability**: Phase 2 also made the fix structural for the files it owns via the `bash_bin` probe fixture (see D6), so those tests are correct on any host without PATH ceremony. Extending that to the remaining files is DF-2.

##### BG-1 RESOLVED - `escalation-trigger.sh` was inert in production (wrong input contract)

- **Source phase**: v3.15.6 Phase 2.1 (discovered while implementing AC2).
- **Reason**: the hook resolved its target path solely from `$CLAUDE_FILE_PATH`, which Claude Code does not set. All nine sibling Write/Edit hooks read `.tool_input.file_path` from the stdin JSON payload. Verified empirically: a real stdin payload produced no output at all, while the env var produced the expected warning. The hook had therefore never fired in normal operation, and it was the ONLY hook in the catalog using that contract.
- **Resolution**: reads the stdin JSON payload first (`jq` when present, a `grep`/`sed` fallback otherwise, matching the sibling convention), treats a JSON `null` as absent, and falls back to `$CLAUDE_FILE_PATH` so any setup exporting it keeps working. Covered by tests asserting the stdin contract, the `tool_input.path` alias, the env fallback, and that stdin wins over the env var.
- **Why it mattered here**: without this, AC2 would have added escape surfaces to a hook that cannot fire, producing a longer list that reports coverage it does not have. That is the precise failure mode the Phase 1 skill names, and it would have been invisible to a test suite that only asserted the pattern list's contents.

##### BG-2 RESOLVED - the no-jq fallback did not decode JSON escapes, so Windows paths never matched

- **Source phase**: v3.15.6 Phase 2.1 (caught by the `.sh`/`.ps1` parity test).
- **Reason**: the `grep`/`sed` fallback reads the RAW JSON string, so a Windows path arrives as `C:\\repo\\.git\\hooks\\x`. The separator normalization then rewrote each `\\` to `//`, yielding `C://repo//.git//hooks//x`, which matches no glob. The PowerShell sibling was already correct because `ConvertFrom-Json` decodes the escape, so the two implementations disagreed.
- **Resolution**: decode the backslash escape in the fallback branch only, before normalization (the `jq` branch needs no such step because `jq` already decodes). Covered by a backslash-path test that runs against both implementations.
- **Note on coverage**: locally `jq` is absent, so the tests exercise the fallback branch; on a runner with `jq` present the same tests exercise the `jq` branch. The assertion is behavioral, so it is correct either way, but neither environment alone covers both branches.

### v3.15.6 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 2 | 0 |
| Deferred (DF) | 2 | 1 |
| Bugs / regressions (BG) | 0 | 8 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 1 |
| Hand-offs (HO) | 0 | 2 |

**OPEN at plan completion, none blocking.** NI-1 (full cross-executor seam instrumentation is not locally achievable; the deliberately dropped half of AC3's `re-partial` classification), NI-2 (the git guardrail is a fixed-pattern denylist, not argv decomposition; AC4's documented limitation), DF-1 (`ai-agent-governance` reciprocal SKIP clause not added; the near-collision is allowlisted and routing is proven correct in both directions), and DF-3 (`defaultMode` omitted from the strict overlay, transferred to v3.17.0 Phase 2 which verifies its enum). The two NI items are scope boundaries recorded so a future reader cannot mistake the shipped controls for something stronger; both are documented in the skill, in the hooks themselves, and in the reverse-engineering matrix.

**RESOLVED across the plan and its follow-on (13 items).** HO-1 and DF-2 together eliminated the WN-v36-1 class: the 103 failures carried across several releases as "bash cannot be exercised on the Windows dev host" were PATH shadowing, and a `conftest.py` PATH repair now makes both test trees pass with no assistance (658 + 516, zero failures). HO-2 (`NEXUS_HUB_INIT=1` exported by both installers with its self-asserted, advisory-only scope recorded). QG-1 (both CI hardening diffs applied, plus a Windows PowerShell 5.1 leg). And four real defects: BG-1 (`escalation-trigger.sh` was inert in production, reading an environment variable Claude Code does not set), BG-2 (the no-jq fallback did not decode JSON backslash escapes, so Windows paths matched nothing), BG-3 (the PowerShell ledger wrote a UTF-8 BOM, breaking integer parsing and `.sh`/`.ps1` format parity on a shared ledger file), BG-4 (`sha256sum` escapes backslash-containing filenames, so a Windows path produced a 65-character hash), BG-5 (`session-summary.ps1` never parsed, so that hook was dead on Windows from v3.11.0; PRE-EXISTING, found by the new AST gate on its first run), and, in the post-plan follow-on, BG-6 (the two description gates silently failed to BLOCK on a host without `jq`, because a failing `grep` under `set -e` aborted them before they reached the refusal), BG-7 (`git-guardrails.sh` exited 1 on any payload carrying no command, same cause), and BG-8 (both languages' description gates blocked on a malformed payload instead of failing open).

**No MT entry is owed.** Phase 1 ships prose and JSON with no executable module; the Phase 2 and 3 shell logic carries 219 tests that each run against both implementations. Worth recording as a method note: four of the six defects found in this plan were caught specifically because assertions run against BOTH the bash and PowerShell implementations, and two of those four (the BOM and the `sha256sum` escaping) are unreachable from a POSIX-only test. A suite that asserted one implementation and eyeballed the other would have shipped all four.

### v3.15.6 follow-on (post-plan, maintainer-requested): full PowerShell hook parity

**Scope note.** The four phases above are the plan. This block records work requested AFTER Phase 4 completed and shipped in the same release, kept separate so the plan's scope is not retroactively rewritten. Two items: correcting the WN-v36-1 citations now that its premise is disproven, and giving every remaining `catalog/hooks/*.sh` a PowerShell sibling.

**WN-v36-1 corrected at the source, history preserved.** The canonical entry in [../v3.6/known-gaps.md](../v3.6/known-gaps.md) blamed the space-containing checkout path and concluded the failures were unavoidable; both are wrong. It now carries a dated RESOLVED correction naming PATH shadowing as the real cause, with the measurement that disproves the space theory (the same space-containing checkout passes with Git Bash ahead of the WSL stub), and its superseded remedy is explicitly marked as one that would have entrenched the misdiagnosis by permanently skipping tests that were always capable of passing. The live surfaces that stated the premise as fact were reworded: two `ci.yml` job comments, three `tests/installer` module docstrings and their two `skipif` reasons, and the Mac smoke-test doc. **The historical session-history narratives and the earlier v3.15.x advisory blocks were deliberately left as written**, because a gap ledger records what was believed at the time; a single file-wide correction notice at the top of this file points readers at the fix instead. Two Windows skips in `tests/installer` were RETAINED on a narrower and still-valid ground (those tests drive the full installer, a path this suite has never verified on Windows) rather than being unskipped on the strength of a diagnosis alone.

**Hook sibling coverage went from 8 of 25 to 25 of 25** (17 new `.ps1` files, about 1900 lines). The four `*-diff-review` variants were generated from the already-shipping `antigravity-cli-diff-review.ps1` because the family is one hook with a swapped CLI name (the `.sh` variants differ by 2 lines each), so they stay in lockstep by construction rather than by discipline. `AGENTS.md` now states the both-implementations invariant for hook authoring, names its machine enforcement, and records the PowerShell pitfalls that produced real defects.

**The parity harness is generic, not 17 bespoke files** (`catalog/hooks/tests/test_hook_sibling_parity.py`). It asserts the structural invariant in BOTH directions, a syntax floor per file, and exit-code agreement per pair across a set of quiet payloads, so it also protects hooks nobody has written yet. Side-effecting hooks are run with `HOME` redirected into a temp directory, so no test can reach real credentials, caches, or the developer's DEVLOG.

**Three pre-existing bash defects and one of my own, all found by the harness on its first runs.** This is the same lesson as Phases 2 and 3, now on a third code path: comparing two implementations finds what inspecting one does not.

##### BG-6 RESOLVED - `require-description.sh` and `require-powershell-description.sh` silently failed to block without `jq`

- **Source**: v3.15.6 follow-on, found by the parity harness.
- **Reason**: under `set -euo pipefail`, a `grep` that matches nothing returns non-zero, and a failing command substitution in an assignment ABORTS the script. So on a host without `jq`, a command carrying NO description made the description `grep` fail and the hook exited 1 **before reaching its block**. The gate allowed precisely what it exists to refuse, and exit 1 reads to the harness as a hook error rather than a refusal.
- **Severity framing**: this is a security defect, not a cosmetic one, and it is the same class as the Phase 2 finding that `escalation-trigger.sh` was inert. A control that reads its input incorrectly is not a control. Verified after the fix on this jq-less host: a description-less command now returns 2 (blocked) and a described one returns 0.
- **Resolution**: every extraction on both branches is now guarded with `|| true`, matching the pattern Phase 2 applied to `escalation-trigger.sh`.

##### BG-7 RESOLVED - `git-guardrails.sh` exited 1 on any payload carrying no command

- **Source**: v3.15.6 follow-on, found by the parity harness.
- **Reason**: the same `set -e` interaction. An empty payload, a malformed one, or a valid payload for a non-Bash tool made the command `grep` fail and aborted the script with exit 1 instead of reaching its documented allow path. Latent in normal operation, because a Bash tool call always carries a command, but wrong for every other case.
- **Resolution**: `|| true` on both extraction branches. A behavioural sweep of all 25 `.sh` hooks confirms the class is now empty.

##### BG-8 RESOLVED - the description gates blocked on a malformed payload (both languages)

- **Source**: v3.15.6 follow-on. The bash half surfaced when BG-6's fix let the hooks reach their block; the PowerShell half was MY defect, caught by the parity harness on the next run.
- **Reason**: a parse failure, or a valid payload for a different tool, is not evidence that a description is missing, so refusing there would wedge the agent on a harness quirk. `git-guardrails.sh` already documented the correct behaviour ("if we couldn't extract a command, allow"); the description gates lacked that guard. My `.ps1` versions had a narrower version of the same flaw: they failed open on a parse ERROR but still fell through to the block for a well-formed payload with no command, so a `Write` tool call was refused.
- **Resolution**: both languages now fail open when no command can be extracted. Confirmed by four spot-checks per implementation (no-command, empty object, command-without-description, command-with-description) and by the parity suite.

##### Advisory (documented asymmetry, not a defect)

- `secret-scan.sh` requires `jq` and exits 0 without it, so on a jq-less host it cannot scan at all, while `secret-scan.ps1` parses JSON natively and always scans. The difference is in the safe direction (the sibling blocks strictly more, never less) and is documented in the `.ps1` header. The parity suite therefore tests this pair's blocking behaviour CONDITIONALLY on `jq` for bash and unconditionally for PowerShell, rather than asserting a false symmetry. My first version of that test asserted symmetry and was wrong; the corrected test states the dependency explicitly.

### v3.15.6 Release readiness (Phase 4, release-readiness 9A/9B)

- **9A resolve known gaps**: re-read every open item above and gave each a disposition (2 resolved this phase, 1 transferred with a named owner, 2 carried as documented deferrals, 2 newly recorded as explicit scope boundaries). Swept the plan's added and modified files for `TODO` / `FIXME` / `XXX` / `HACK` / `# DEVIATION:` markers: none present (the 13 deviations are documented here and in the session histories, not left as inline markers). No release blocker remains.
- **9B verify tests and CI/CD**: every new module has coverage. The two advisory hooks, the two guardrail hooks, the provenance ledger, the permission overlay, and both installer merge helpers are covered by 219 tests, each exercised against both implementations where both exist, with the installer tests extracting and running the REAL shipped functions rather than a re-implementation. CI covers every change: skill validation and registry integrity (`validate` job), hook lint and the `.ps1` AST gate (`shellcheck` job), the full hook and repo suites on ubuntu (`tests`) and on Windows PowerShell 5.1 (`tests-windows`), and installer dry-runs (`bootstrap`, `bootstrap-windows`, `install-smoke`). No secret is introduced: the provenance ledger records paths and hashes only, asserted by a test that plants a secret and proves it reaches neither the ledger nor the hook's output.
- **9C-9E hand-off**: HANDED to `/update release` and NOT performed here. It owns the version bump (3.15.5 to 3.15.6 across every `check_version_sync` surface), the changelog stamp of the `[Unreleased]` section, the README "What's New" section, the platform read-contract freshness re-stamp, the `develop` merge, the tag, the push, and the GitHub Release, each behind its own confirmation gate. This phase performed no version bump, tag, merge, or push. One note for that step: the branch is 2 commits behind `develop` (unrelated v3.16 planning docs from a parallel session, no file overlap), so `/update release` should integrate `develop` first.

### v3.15.6 Advisory (pre-existing, not introduced by this phase)

- **The full repo-wide failure set is pre-existing and was baseline-verified in this phase.** A detached worktree at clean `develop` (`189c3df5`) reproduces the same failures as the feature branch. Totals measured this phase: `catalog/hooks/tests` 99 failed / 361 passed / 36 skipped (identical to baseline), `tests/validators` 1 failed (`test_session_query_extract.py::test_discover_obsidian_vault_marker`) / 372 passed, `tests/installer` 3 failed (all three `test_branch_flag.py::test_bash_*`) / 119 passed / 15 skipped, `tests/integrations` 398 passed / 1 skipped, `tests/skills` 209 passed / 3 skipped, and all five extension suites fully green (670 passed). Every failure is the same `bash.EXE` exit-127 path-resolution class described in HO-1, and the set matches the v3.15.5 Advisory exactly. Aggregate: 2129 passed, 103 pre-existing environmental failures, 0 introduced.
- **The bundle audit reports 6 orphan warnings, all pre-existing `__pycache__/*.pyc` artifacts** in `docs-layout-refactor` (1), `document-to-interactive-html` (4), and `demo-capture` (1). None is in the new skill. They are already covered by `.gitignore` (`__pycache__/` at line 60) so none is tracked, but the audit walks the filesystem rather than the index and still sees them. Left untouched per the no-out-of-scope-cleanup rule; the `demo-capture` one was already recorded as a v3.15.3 advisory.
- **A stale `.git/worktrees/nh-baseline-dev` metadata directory could not be pruned** (permission denied, most likely a OneDrive or scanner lock). It is not this phase's artifact and predates it, `git worktree list` already excludes it, and nothing inside `.git/` is committed, so it has zero repo impact. The worktree this phase created for baseline verification was removed and its metadata cleaned up successfully.
- **An unrelated working-tree modification was present and deliberately excluded from this phase's commit**: `docs/v3/v3.16/plans/v3.17.0-agent-autonomy-toggle.md` carries a coherent authored edit (refining that plan's Phase 1 around PowerShell-block coverage and workspace scope) written by a parallel session, not by this phase. It was left unstaged and untouched. Notably, that plan already cites "the v3.15.6 escape taxonomy" and its execution-trigger config paths as a dependency, so a downstream plan is already consuming the list this phase authored.
- **The unicode-safety validator still reports its pre-existing repo-wide warnings (0 errors).** All four Markdown files touched by this phase are strictly ASCII, verified explicitly.

## v3.15.7 - adoption-raptor-loop-hunt

### v3.15.7 Phase 1 checkpoint

Phase 1 added the shared finding-disposition doctrine to `pentest-reporting` and `exploitability-analyzer`: confirmed and potential severity remain separate under partial visibility, the higher axis drives triage, every surviving finding receives exactly one of four dispositions, and `needs-live-validation` carries a concrete safe validation receipt. The existing full-CVSS-vector requirement remains owned by `pentest-reporting`.

### v3.15.7 Phase 1 Open Items

#### Warnings

##### WN-3 - `test_instruction_merge.py` depends on installer-suite import order

- **Source phase**: v3.15.7 Phase 1 - Finding-disposition doctrine.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.7-adoption-raptor-loop-hunt.md` (sub-task 1.3).
- **Reason**: `python -m pytest tests/installer/test_instruction_merge.py -q` fails during collection with `ImportError: cannot import name 'merge_marker_section' from partially initialized module 'scripts.lib.installer.instruction_merge' (most likely due to a circular import)`. The authoritative full `tests/installer` run passes 143 tests and skips 16, so this is a pre-existing isolated-test order dependency rather than a Phase 1 product regression.
- **Suggested next step**: break the `instruction_merge` / integrations package import cycle or add an isolated-import regression test in a later maintenance phase.

The remaining v3.15.7 phases are scheduled plan work, not gaps in the completed Phase 1 scope.

### v3.15.7 Phase 1 Resolved

None. No pre-existing bug or deferred item was pulled into this phase.

### v3.15.7 Phase 1 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

**Verification boundary.** The two changed skill bodies passed the catalog bundle, placeholder, routing, security, and registry gates. The complete edited-content test matrix reports 1,793 passed, 21 skipped, and 0 failed. No executable module changed, so code coverage is not applicable to this prose-only phase.

### v3.15.7 Phase 2 checkpoint

Phase 2 added the refutation-validity taxonomy and rejection proof burden to `adversarial-verifier`. A finding can now be rejected only by observed contradictory evidence, including an actual input-source inventory, per-route accounting, and build or default-configuration evidence for reachability claims. Unseen server behavior and merely plausible framework protections are invalid refutations; when the relevant layer is unavailable, the finding moves to `needs-live-validation`. `security-review` now points to this doctrine through a thin rejection gate rather than duplicating it.

### v3.15.7 Phase 2 Open Items

No new items. WN-3 remains open and unchanged from Phase 1; the authoritative full installer suite remains green.

### v3.15.7 Phase 2 Resolved

None. Phase 2 did not take ownership of WN-3 or any older v3.15 gap.

### v3.15.7 Phase 2 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

**Verification boundary.** The complete edited-content test matrix reports 1,793 passed, 21 skipped, and 0 failed. The two mandatory dry checks passed: one candidate was rejected on observed evidence, and one candidate with an unobservable server layer was escalated to `needs-live-validation`. No executable module changed, so code coverage is not applicable to this prose-only phase.

### v3.15.7 Phase 3 checkpoint

Phase 3 added a target-wide component denominator, explicit COVERED / OMITTED / UNCOVERED accounting, and the `N + O + U = M` balance to `security-review`. It also added an orthogonal four-altitude ledger and the proven-dirty sink sweep, which scopes negative evidence to the tested trigger path and keeps unresolved paths UNKNOWN. The `/review` command exposes the exact `N of M` coverage promise while delegating its mechanics to the owner skill; `advanced-attack-patterns` and `business-logic-abuse` carry reciprocal ownership pointers without duplicating the rules.

### v3.15.7 Phase 3 Open Items

No new items. WN-3 remains open and unchanged from Phase 1; the authoritative complete repository suite remains green.

### v3.15.7 Phase 3 Resolved

None. Phase 3 did not take ownership of WN-3 or any older v3.15 gap.

### v3.15.7 Phase 3 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

**Verification boundary.** The complete matrix reports 1,793 passed, 21 skipped, and 0 failed. The required dry check enumerated seven real `extensions/` components, assigned only six, and forced `nexus-web-fetch` to remain visible as UNCOVERED; its report stated `5 of 7 components covered; 1 omitted; 1 UNCOVERED` and correctly prohibited a completeness claim. No executable module changed, so code coverage is not applicable to this prose-only phase.

### v3.15.7 Phase 4 checkpoint

Phase 4 added the anti-costume-rigor fraud-class table to `verification-before-completion`. Its ten rows cover fabricated and stale evidence, overstated outcomes, false tested-route claims, unsupported N/A entries, read-derived coverage, wrong-instrument sweeps, completeness-unknown enumeration, dropped pending work, and escalation avoidance. Every row states the exact artifacts or sets an auditor compares. `pentest-reporting` references the owner table through a thin pre-delivery gate and adds binary checks for confirmation evidence, rejection receipts, and component coverage actions.

### v3.15.7 Phase 4 Open Items

No new items. WN-3 remains open and unchanged from Phase 1; both complete test passes remain green.

### v3.15.7 Phase 4 Resolved

None. Phase 4 did not take ownership of WN-3 or any older v3.15 gap.

### v3.15.7 Phase 4 Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

**Verification boundary.** Both complete matrices report 1,793 passed, 21 skipped, and 0 failed. The mechanical table audit found exactly ten required rows and reduced each tell to an explicit Compare or Diff operation. No executable module changed, so code coverage is not applicable to this prose-only phase.

### v3.15.7 Phase 5 checkpoint

Phase 5 added a pure-standard-library typed capability-grant broker under `agent-access-policy`. Authorization is side-effect-free and produces only a least-privilege plan unless execution is explicitly requested. The broker rejects missing authorization sources, ungranted capabilities, out-of-scope writes, off-allowlist network destinations, malformed requests, and execution without a reachable sandbox. Its four capabilities are `network`, `write`, `use_secret`, and `destructive_test`; write paths are absolute and scoped, and network destinations are exact normalized strings. The owning skill documents the enforcement boundary and its composition with the v3.15.6 strict permission overlay and trust-seam provenance hook. The policy matrix records the local `re-full` adoption, with no outbound service, API key, third-party processor, runtime dependency, or installer edit.

### v3.15.7 Phase 5 Open Items

No new items. WN-3 remains open and unchanged from Phase 1. The monolithic Windows integration wrapper exceeded its command budget while repeatedly copying all platform surfaces, but file-level isolation found no failing test: the two heavy files passed separately, and all 80 contract nodes passed through a bounded exact-node scheduler. This is verification-environment throughput, not a product defect or deferred implementation.

### v3.15.7 Phase 5 Resolved

None. Phase 5 did not take ownership of WN-3 or any older v3.15 gap.

### v3.15.7 Phase 5 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

**Verification boundary.** The focused broker suite reports 24 passed with 87% branch coverage. Ruff check and format verification are clean. Catalog bundle, quality, routing, and security gates pass. The complete test matrix accounts for 1,818 passed, 20 skipped, and 0 failed: five extension suites supplied 670 passes and 1 skip; repository installer, integration, skill, and validator groups supplied 1,148 passes and 19 skips. The integration total includes all 399 collected cases, with the 80 heavy contract nodes run exactly and independently after the monolithic Windows wrapper exceeded its time budget.

### v3.15.7 Phase 6 checkpoint

Phase 6 added a pure-standard-library closure gate under `security-review`. It mechanically computes five claim-to-evidence differences over a local review record: components without a logged action or explicit caveat, findings without a terminal or explicitly pending disposition, confirmed findings without supporting evidence, rejected findings without a complete rejection record, and report claims without matching facts. Any non-empty difference exits non-zero. `skill-eval-loop` now requires separately scored adversarial axes, objective traps, deterministic and live-model tiers, judge-only ground truth, randomized fixtures, and artifact-based verdicts. `known-gaps-tracker` now states that cross-cycle memory may only raise scrutiny; prior work is a priority and recheck signal, never a coverage or exclusion signal. Building the durable store remains explicitly deferred to a future cycle.

### v3.15.7 Phase 6 Open Items

No new repository item. WN-3 remains open and unchanged from Phase 1. The durable cross-run store is plan-owned future work rather than an incomplete Phase 6 deliverable because this phase intentionally adopted doctrine only. The Windows integration wrapper again exceeded its command budget during repeated all-platform catalog copies, but all 399 integration cases were accounted for through non-contract grouping plus exact contract-node execution, with no failed test. The disposable mirror and coverage data remain outside the repository because the sandbox rejected their removal; they do not affect repository state or distribution.

### v3.15.7 Phase 6 Resolved

None. Phase 6 did not take ownership of WN-3 or any older v3.15 gap.

### v3.15.7 Phase 6 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

**Verification boundary.** The focused closure-gate suite reports 17 passed with 87% branch coverage. Ruff check and format verification are clean. Catalog bundle, quality, routing, security, version, platform-contract, freshness, and compression gates pass. The complete test matrix accounts for 1,834 passed, 21 skipped, and 0 failed: five extension suites supplied 670 passes and 1 skip; repository installer, integration, skill, and validator groups supplied 1,164 passes and 20 skips. The integration total includes all 399 collected cases; 79 contract nodes passed and the Hermes sibling-preservation node produced its expected environment skip.

### v3.15.7 Phase 7 checkpoint

Phase 7 audited the repository and active v3.15 documentation layout, reconciled the version ledger, reviewed every GitHub Actions workflow, resolved the isolated installer import cycle, and completed the local release-readiness matrix. The architecture audit proposed no moves or deletions: all 63 active v3.15 Markdown files are correctly classified, the six duplicate-content groups are intentional parity or placeholder artifacts, no tracked empty directory needs cleanup, and no receiving skill crossed the 500-line target because of this plan. The catalog remains at 270 skills, no skill frontmatter changed, and no generated catalog sync is required. The v3.15.6 composition seam remains accurate: endpoint permission and provenance controls constrain host reachability, while the v3.15.7 broker authorizes one typed model-emitted action above that layer; neither replaces the sandbox.

### v3.15.7 Phase 7 Open Items

#### Deferred

##### DF-6 - Durable monotonic-scrutiny store remains deferred

- **Source phase**: v3.15.7 Phase 7 - Known-gaps reconciliation.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.7-adoption-raptor-loop-hunt.md` (sub-task 7.2; comparison candidate B11).
- **Reason**: Phase 6 adopted the safety invariant that prior-cycle memory may only raise scrutiny, never establish coverage or exclude a candidate. A durable store is locally buildable but was intentionally deferred because its persistence, invalidation, and poisoning-resistance surface exceeds this patch's bounded scope.
- **Re-entry condition**: Re-propose only with a local storage schema, explicit invalidation rules, poisoning tests, and proof that every stored signal can only increase review priority.

##### DF-7 - External vulnerability-database reconnaissance remains declined

- **Source phase**: v3.15.7 Phase 7 - Known-gaps reconciliation.
- **Plan reference**: `docs/v3/v3.15/comparisons/v3.15.7-comparison-raptor-loop-hunt.md` (prior-art recon via OSV, NVD, or GitHub).
- **Reason**: Mandating this step would add third-party egress to a local skill surface and duplicate existing `dependency-security-audit` and `cve-reachability-analyzer` ownership. The MCP Registry Policy prefers those existing local skills over a new search-as-service dependency.
- **Re-entry condition**: Reconsider only if the capability cannot be expressed through the existing local skills and a future proposal passes the registry's reverse-engineer-first audit.

##### DF-8 - Provider-key cross-vendor judging remains declined

- **Source phase**: v3.15.7 Phase 7 - Known-gaps reconciliation.
- **Plan reference**: `docs/v3/v3.15/comparisons/v3.15.7-comparison-raptor-loop-hunt.md` (cross-vendor judge).
- **Reason**: A mandated provider-key path would transmit source and findings to another model vendor. Nexus-Hub already owns the local `cross-model-orchestrator` path and the comparison adopted the harness-as-second-evaluator fallback instead.
- **Re-entry condition**: Reconsider only for an explicit user-owned provider workflow with egress disclosure, hard spending controls, and no claim that a second vendor is required for correctness.

##### DF-9 - Additive platform capability drift is deferred to v3.15.8

- **Source phase**: v3.15.7 release-time platform read-contract re-verification on 2026-08-02.
- **Affected surfaces**: Codex custom agents and native hooks; Gemini CLI and Qwen native hooks; Kimi custom agents and TOML hook configuration; Copilot custom agents and hooks. Hermes documentation now also demonstrates category-nested skill layouts, while the current flattened child layout remains discoverable and functional.
- **Reason**: These are additive upstream capabilities, not dead delivery paths in v3.15.7. Implementing them safely requires adapter design, config-merge ownership, teardown semantics, and cross-platform tests beyond this release's approved scope.
- **Decision**: The maintainer approved release-with-documented-drift on 2026-08-02. The machine contract keeps enforcing the currently delivered paths; a non-consumed findings block records the new capabilities without making unsupported adapter promises.
- **Re-entry condition**: v3.15.8 must reconcile each surface against the cost-effective CI/CD foundation work, add exact contract checks only as the corresponding adapter behavior lands, and preserve shared-path ownership during install, repair, and teardown.
- **RESOLVED (v3.15.8 Phase 9.2, 2026-08-03)**: every surface named above now has a disposition, and all 18 ownership-matrix rows are enforceable. Codex agents and hooks shipped in Phase 5; Gemini CLI and Qwen hooks in Phase 6; Kimi agents and hooks in Phase 7 (global hooks only -- no project hook path exists, recorded as DF-13); Copilot global agents in Phase 8, with Copilot hooks at both scopes and Copilot project agents established as **inherited** through Copilot's own default Claude-format read paths rather than duplicated. Hermes resolved opposite to the drift-audit premise: discovery probes only direct subdirectories, so the flattened layout is required and the category-nested example would have broken it. Contract checks were added per adapter as its behavior landed (`contract_checks` config keys plus `install_verify` surfaces for Codex, Qwen, and Kimi), shared-path ownership held throughout (`~/.agents/skills` stayed Codex-owned, `.agents/skills` Antigravity-owned, and neither Kimi nor Hermes claimed the shared agent directories), and the machine contract and its Markdown mirror were updated together in every phase. The re-entry condition is met in full; DF-9 closes here.

### v3.15.7 Phase 7 Resolved

##### BG-1 - Usage-monitor clean-install workflows repaired

- **Resolution**: both usage-monitor workflows now pin `actions/setup-node` by commit and use Node 22, both package manifests declare `node >=22.0.0`, and both lockfiles were rebuilt from their exact manifests with npm 10.9.4. This resolves the Claude monitor's long-standing missing and inconsistent `@emnapi` graph and the equivalent Codex monitor failure discovered on the Extra Credits commit.
- **Evidence**: clean npm 10 installs and TypeScript compilation pass for both extensions. Claude reports 5 passing Vitest cases. Codex reports 75 passing cases and 80.55% statements, 80.29% branches, 77.19% functions, and 81% lines. The two focused GitHub workflows remain the remote release gate.

##### BG-2 - First release PR exposed three CI defects

- **Resolution**: normalized terminal newlines in the four files rejected by the end-of-file hook; made `secret-scan.sh` fail open when `jq` cannot parse the payload, matching `secret-scan.ps1`; restored the reactivated Presentify check by pinning Ruff 0.16.1, preserving intentional security suppressions, tracking all six shebang scripts as executable, and normalizing OCR spacing in the fixture enrichment protocol; and changed Linux CI to invoke `python -m pytest` so repository-package imports resolve during skills-test collection.
- **Evidence**: the exact malformed secret-scan parity node passes, Ruff 0.16.1 reports no findings, both OCR spacing regression cases pass within a 46-passed focused suite, all four artifacts end with LF, and the regenerated 1,194-entry manifest verifies. Release PR #28 is green at `c204162b`: validation, Presentify, full tests, bootstrap, install smoke, ShellCheck, and doc colocation all pass.

##### BG-3 - Windows push-only test gate exposed interpreter and hashing defects

- **Resolution**: `test_model_routing_switch.py` now invokes the exact Bash executable selected by the shared `bash_bin` probe instead of resolving the ambiguous `bash` alias again. `provenance-ledger.ps1` now computes SHA-256 through a direct .NET file stream and disposes both stream and algorithm in `finally`, avoiding the hosted Windows PowerShell 5.1 `Get-FileHash` failure while preserving the advisory hook's `NOHASH` fallback.
- **Evidence**: the focused Windows PowerShell 5.1 regression suite reports 54 passed, including all model-routing exit contracts and both provenance hash assertions, and the changed hook passes the Windows PowerShell AST parser. The follow-up pull request and post-merge push remain the remote authority.

##### WN-3 - `test_instruction_merge.py` isolated import cycle resolved

- **Resolution**: `scripts/lib/installer/instruction_merge.py` now defers the `FileAction` runtime import until a result is created, so importing the merge helper no longer initializes the integrations registry and loops back through `copilot.py`. `tests/installer/test_instruction_merge.py` includes a fresh-interpreter regression test that imports the helper without preloading the registry.
- **Evidence**: The exact former reproduction now reports 13 passed; the full installer suite reports 144 passed and 16 skipped; the changed module reports 87% branch coverage.

### v3.15.7 Phase 7 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 4 | 0 |
| Bugs / regressions (BG) | 0 | 3 |
| Warnings (WN) | 0 | 1 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 1 | 0 |

**Verification boundary.** The Phase 7 complete local matrix accounts for 1,835 passed, 21 skipped, and 0 failed across five extensions plus repository installer, integration, skill, and validator groups; the separately required hook suite reports 900 passed and 36 skipped. Release-time re-verification passes every hard validator, manifest integrity, 75 Codex monitor tests with coverage, and 54 focused broker, closure, and instruction-merge tests. A fresh monolithic rerun of the 559 integration and installer cases exceeded the Windows command budget without a failure; collection remained healthy. Release PR #28 and monitor repair PR #29 pass every triggered workflow; both monitor workflows also pass on the merged `develop` commit. The push-only Windows test gate then exposed BG-3, whose focused local Windows PowerShell 5.1 suite reports 54 passed after the repair. The follow-up pull request and post-merge push remain the next authority; model-profile roster drift remains advisory.

### v3.15.7 Release readiness (Phase 7, release-readiness 9A/9B)

- **9A resolve known gaps**: WN-3 is resolved with an isolated-import regression test. The durable store, both declined external candidates, and additive platform drift have explicit reasons, owners, and re-entry conditions. The monitor and Windows push-gate defects are owned by BG-1 and BG-3; no unowned v3.15.7 release blocker remains.
- **9B verify tests and CI/CD**: Every changed executable has focused branch coverage and belongs to an already-collected test surface. Existing CI covers skill validation, bundle and placeholder checks, broker and closure tests, version/platform gates, Linux integration, and gated Windows/macOS legs without adding a cold runner. The broad `ci.yml` trigger remains intentional because it also owns installers, integrations, and extensions; narrower focused workflows retain their path filters, concurrency controls, caches, or scheduled security semantics.
- **9C-9E handoff**: Release notes, the 3.15.6 to 3.15.7 version bump, README and CHANGELOG updates, release-branch push, green release PR #28, and green monitor repair PR #29 are complete. The maintainer authorized the sequence; the Windows follow-up PR, develop/main promotion, post-merge CI, tag, and GitHub Release remain pending in that order.

## v3.15.8

### v3.15.8 Phase 1 checkpoint

Phase 1 converted DF-9 and the GitHub monitor requirements into explicit ownership, billing-data, authentication, visual, fixture, and test contracts. The platform matrix keeps all newly observed Codex, Gemini CLI, Qwen, Kimi, and Copilot surfaces finding-only until their implementation phases add owned writes and lifecycle tests; the existing Hermes flattened layout remains the only enforceable Hermes claim. Eleven sanitized billing fixtures and 27 semantic tests now reject unsupported ownership, unsafe fixture content, false denominators, and invalid visual requirements.

### v3.15.8 Phase 1 Open Items

#### Deferred

##### DF-10 - Exact GitHub status SVG and redistribution evidence remain unavailable

- **Source phase**: v3.15.8 Phase 1.3 - Fix the Visual Contract.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 1.3).
- **Reason**: the declared 20x20 SVG was not present in the supplied assets or repository, and the observed 14x14 gradient PNG does not include confirmed redistribution or trademark-use evidence. Phase 1 therefore cannot record exact SVG geometry, copy either asset into the extension package, or derive a non-blurry 128x128 or 256x256 package icon without inventing source data.
- **Re-entry condition**: before Phase 3 packages visual assets, the maintainer supplies the exact SVG plus provenance and redistribution approval, and supplies or approves a high-resolution source suitable for a 256x256 icon.

#### Quality-gate gaps

##### QG-2 - Repository CI does not collect `tests/plans`

- **Source phase**: v3.15.8 Phase 1.5 - Testing and Stabilization.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 1.5 and Phase 9.3).
- **Reason**: `.github/workflows/ci.yml` collects integration, installer, validator, and skill suites but not the new semantic contract suite under `tests/plans`. The v3.15.8 plan explicitly defers unnecessary workflow restructuring until later design and final CI reconciliation, so Phase 1 did not silently broaden the workflow.
- **Re-entry condition**: add the Phase 1 contract suite to an appropriate existing CI job during Phase 4 design or Phase 9 reconciliation, preserving path filters, caching, concurrency cancellation, and gated expensive matrices.

### v3.15.8 Phase 1 Resolved

- The repository-wide personal-path validator initially found a pre-existing absolute portfolio path in `docs/v3/v3.16/plans/v3.20.0-interactive-guide-redesign.md`. With explicit maintainer authorization, the path was replaced by `../online-portfolio/nexus-hub/index.html`; `python scripts/validate_no_personal_paths.py` now exits 0.
- HO-3 was resolved in Phase 2 by retaining the documented fine-grained-token fallback in `ExtensionContext.secrets` and keeping VS Code GitHub session reuse disabled until billing-endpoint acceptance is proven by an authorized probe.

### v3.15.8 Phase 1 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 1 | 0 |
| Hand-offs (HO) | 0 | 1 |

**Verification boundary.** Phase 1 reports 27 contract tests with 100% statement coverage plus 103 affected platform, lifecycle, summary, verification, and Codex tests, for 130 focused passes and no failures. Ruff check and format verification are clean; all eleven JSON fixtures parse; the direct Windows equivalents of `make validate` pass every hard validator; the repository-wide personal-path gate and `git diff --check` pass. The full 399-case integration collection advanced without a failure but exceeded the bounded Windows command duration, so this checkpoint does not claim a fresh complete integration-suite pass.

### v3.15.8 Phase 2 checkpoint

Phase 2 adds the independent `extensions/github-usage-monitor/` TypeScript package with typed billing models, SecretStorage-backed token lifecycle commands, explicit user/organization/enterprise ownership, a versioned GitHub REST client, defensive Copilot and Actions normalization, verified-or-manual allowance resolution, and last-known-good cache behavior. The implementation keeps unknown limits percentage-free, keeps errors distinct from zero usage, and does not reuse a VS Code GitHub session without evidence that the billing endpoints accept it.

### v3.15.8 Phase 2 Open Items

#### Quality-gate gaps

##### QG-3 - GitHub Usage Monitor tests are not collected by CI

- **Source phase**: v3.15.8 Phase 2.5 - Testing and Stabilization.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 2.5 and Phase 4.3).
- **Reason**: `.github/workflows/ci.yml` runs Python suites, while the focused Claude and Codex workflows collect only their own extension paths. The new GitHub monitor therefore has no remote Node 22 compile-and-coverage gate yet. Phase 4 explicitly owns a path-filtered monitor workflow, so Phase 2 does not add a partial or duplicate CI definition.
- **Suggested next step**: implement T028 and T029 in Phase 4 with a path-filtered Node 22 workflow that uses the lockfile cache, concurrency cancellation, clean install, compile, coverage, and VSIX dry-package gates.

### v3.15.8 Phase 2 Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| HO-3 | Authorized GitHub billing probe required before authentication choice | Phase 2 | No authorized credential was available, so the contract's fine-grained-token fallback was selected; tokens are validated before storage in `ExtensionContext.secrets`, and VS Code session reuse remains disabled pending live proof. |

### v3.15.8 Phase 2 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 1 | 0 |
| Hand-offs (HO) | 0 | 1 |

**Carryovers.** DF-10 remains owned by Phase 3 visual packaging, and QG-2 remains owned by Phase 4 or Phase 9 repository-CI reconciliation. Phase 2 adds only QG-3; it introduces no skipped implementation, known bug, suppressed warning, or uncovered source file.

### v3.15.8 Phase 3 checkpoint

Phase 3 adds the GitHub Usage Monitor status item, detailed hover, theme-adaptive dashboard, secure settings surface, threshold recommendations, de-duplicated activity-bar warning view, normalized icon-font glyph, supplied gradient alert mark, vector-derived 256x256 package icon, third-party notice, and 16 focused UI and asset tests. The package preserves absolute-only display for unknown allowances, uses `#651DA8` for meters, escapes provider content, and packages without source, tests, coverage, dependencies, or source maps.

### v3.15.8 Phase 3 Open Items

#### Missing tests / coverage gaps

##### MT-5 - Extension activation and live VS Code lifecycle branches remain below 80 percent file coverage

- **Source phase**: v3.15.8 Phase 3.5 - Testing and Stabilization.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 3.5).
- **Reason**: global package coverage passes at 82.09% statements, 77.93% branches, 85.27% functions, and 87.32% lines, but `src/extension.ts` remains at 34.74% statements because authorized refresh, native settings dispatch, toast actions, and repeated activation timing require broader VS Code lifecycle integration than the current unit stub provides.
- **Suggested next step**: add Extension Development Host integration coverage for activation, authorized refresh, native settings dispatch, alert actions, and configuration changes during Phase 4 packaging or Phase 9 final reconciliation.

#### Quality-gate gaps

##### QG-4 - Interactive light, dark, and high-contrast visual smoke remains unobserved

- **Source phase**: v3.15.8 Phase 3.5 - Testing and Stabilization.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 3.5).
- **Reason**: VS Code CLI 1.131.0 is installed, but this non-interactive session cannot observe or capture the Extension Development Host GUI. Automated tests verify theme tokens, semantic meter and alert labels, focus-visible styling, responsive layout, reduced motion, CSP, escaping, and unknown-limit fallback, but they are not screenshots or a human visual inspection.
- **Suggested next step**: during Phase 4 packaging, install the locally built VSIX into an isolated Extension Development Host and capture status, hover, dashboard, settings, and warning surfaces in light, dark, high-contrast, keyboard-only, 200 percent zoom, and forced-colors modes.

### v3.15.8 Phase 3 Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| DF-10 | Exact GitHub status SVG and redistribution evidence unavailable | Phase 3 | The maintainer supplied both assets. SVG Repo identifies the exact SVG as CC0; Streamline's free-license and attribution terms cover the supplied warning mark. The normalized one-path SVG, byte-identical 14x14 PNG, WOFF2 glyph, vector-derived 256x256 icon, hashes, and attribution are recorded in the visual contract and package notice. |

### v3.15.8 Phase 3 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 1 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 1 | 0 |
| Hand-offs (HO) | 0 | 0 |

**Carryovers.** QG-2 and QG-3 remain owned by Phase 4 or Phase 9 CI reconciliation. Authorized live billing verification remains a release-readiness activity. Phase 3 adds MT-5 and QG-4; it introduces no skipped implementation, known production bug, suppressed warning, or bypassed hard gate.

### v3.15.8 Phase 4 checkpoint

Phase 4 makes the GitHub Usage Monitor a distributed utility rather than a local package. Both installers build and install it under a `GITHUB` vendor header after Anthropic and OpenAI, using an absolute-usage status hint that promises no percentage, and the installer smoke test now enforces presence, identity, and vendor order across both shells so a monitor cannot be wired into one and forgotten in the other. A path-filtered `github-usage-monitor.yml` adds the extension's remote gate (read-only token, SHA-pinned actions, Node 22, exact lockfile cache, concurrency cancellation, clean install, compile, coverage thresholds, VSIX packaging, packaged-content verification), and fourteen semantic workflow-policy tests assert those properties instead of snapshotting the file. A new `verify:package` gate asserts the VSIX carries every runtime asset and no coverage report, source tree, nested VSIX, or credential-shaped file. The extension README documents installer and VSIX setup, billing scopes, SecretStorage token lifecycle, permissions, manual allowances, alerts, cache and fallback behavior, and the four honesty limits (personal endpoints omit managed Copilot, summary APIs are preview, unknown quotas stay absolute, nothing is scraped).

Two decisions are worth recording. The focused workflow deliberately does not trigger on `scripts/installer.{sh,ps1}`, because `ci.yml` already runs on every non-docs change and owns the installer parity assertion; listing the installers would rebuild an unchanged VSIX on every installer edit. And on maintainer request during this phase, the usage-meter fill changed from `#651DA8` to teal `#008080` across the status hover and dashboard accent, the visual contract, both READMEs, and the contract test; the maintainer-supplied gradient artwork and the package icon derived from it keep their original purple stops.

### v3.15.8 Phase 4 Open Items

#### Deferred

##### DF-11 - Focused monitor workflow does not trigger on installer changes

- **Source phase**: v3.15.8 Phase 4.2 - Add Focused CI.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 4.2, T028).
- **Reason**: T028 lists "relevant installer lines" among the workflow's triggers, but GitHub path filters are file-scoped, so the narrowest expression of that intent is the whole of `scripts/installer.sh` and `scripts/installer.ps1`. Including them would start a Node runner and rebuild an unchanged VSIX on every installer edit. The compensating control is real rather than notional: `ci.yml` has no path filter beyond `paths-ignore: docs/**`, so any installer change runs `catalog/hooks/tests/test_installer_smoke.py`, which is what asserts both shells build every monitor in the same order.
- **Suggested next step**: during Phase 9 CI reconciliation, either accept this divergence explicitly in the workflow comparison or, if per-path job gating is adopted repository-wide, add an installer-parity job gated to installer changes.
- **ACCEPTED AS A RETAINED DIFFERENCE (Phase 9.3, 2026-08-03)**: the first option. The repo-wide audit confirmed that per-path job gating was NOT adopted -- every focused workflow keeps a whole-workflow `paths:` filter and `ci.yml` remains the unfiltered catch-all -- so adding installer paths to the monitor workflow would rebuild an unchanged VSIX on every installer edit with no gate that `ci.yml` does not already provide. The compensating control is now also test-asserted rather than merely described: `test_focused_workflows_filter_by_path` requires `ci.yml` to keep a `paths-ignore` filter (so it cannot quietly acquire a `paths` filter that would strand installer changes), and `test_installer_smoke.py` continues to assert both shells build every monitor in the same order. This is a deliberate, documented divergence from T028's literal wording, not an open gap.

### v3.15.8 Phase 4 Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| QG-2 | Repository CI does not collect `tests/plans` | Phase 4 | `ci.yml`'s `tests` job enumerates directories by name, so `tests/plans` was never collected. A `Plan-contract + workflow-policy tests` step now runs `tests/plans` and the new `tests/workflows` together, with a comment recording why a new directory is invisible until listed. |
| QG-3 | GitHub Usage Monitor tests are not collected by CI | Phase 4 | `.github/workflows/github-usage-monitor.yml` gives the extension a path-filtered Node 22 gate with clean install, compile, coverage thresholds, VSIX packaging, and packaged-content verification, mirroring the Claude and Codex monitor workflows and pinned to the same action SHAs (enforced by a cross-workflow policy test). |

### v3.15.8 Phase 4 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 2 |
| Hand-offs (HO) | 0 | 0 |

**Carryovers.** MT-5 (extension activation coverage) and QG-4 (interactive light/dark/high-contrast smoke) remain open and are now more pointed: the meter color changed after Phase 3's accessibility pass, so the first Extension Development Host session should confirm the teal fill in all three themes. `#008080` clears the 3:1 non-text contrast floor against both a white and a black backdrop by calculation, which the previous purple did only against white, but that is arithmetic rather than an observed render. Authorized live billing verification remains a release-readiness activity. Phase 4 adds DF-11 and resolves QG-2 and QG-3; it introduces no skipped implementation, known production bug, suppressed warning, or bypassed hard gate.

### v3.15.8 Phase 5 checkpoint

Phase 5 turns the two finding-only Codex rows from Phase 1's ownership matrix into owned writes. Custom agents are no longer a file copy: `_codex_native.py` transforms each `catalog/agents/*.md` into a Codex agent TOML at `~/.codex/agents/` and `.codex/agents/`, carrying `name`, `description`, and the Markdown body as `instructions`, and inferring `sandbox_mode = "read-only"` when every tool the agent declares is non-mutating. Native hooks copy their scripts under an owned directory and merge into `hooks.json` at both scopes, with each handler carrying a `commandWindows` that points at the `.ps1` sibling so a PowerShell host gets the same guardrail. Both writes are ownership-gated through the install manifest, so a user-authored `planner.toml` or a hand-written hook group survives an install, a reinstall is byte-identical, and teardown removes only Nexus-Hub entries before deleting `hooks.json` and the two directories if nothing else remains.

Two upstream constraints shaped the design and are surfaced rather than papered over. Codex ships its hook engine disabled behind `[features] hooks`, so the installer sets that flag idempotently in the same `config.toml` it already merges permissions into, and leaves it alone when the user has explicitly set it to `false`. And Codex requires the user to trust hooks interactively via `/hooks` before any of them fire, which no installer can do on the user's behalf; the install summary now says so in both scopes instead of implying the hooks are live.

### v3.15.8 Phase 5 Open Items

#### Hand-offs

##### HO-4 - Codex hooks stay inert until the user trusts them via `/hooks`

- **Source phase**: v3.15.8 Phase 5.2 - Codex Native Hooks.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 5.2).
- **Reason**: Codex gates hook execution behind an interactive trust prompt. Writing `hooks.json` and enabling `[features] hooks` is the whole of what an installer can do; the remaining step is a deliberate human confirmation, and simulating it would defeat the control it exists to provide.
- **Suggested next step**: none in code. The install summary carries the instruction at both scopes, and the read-contract prose records the trust model, so this is a documented user action rather than an implementation gap.

#### Missing tests / coverage gaps

##### MT-6 - Codex agent and hook delivery is not observed against a real Codex install

- **Source phase**: v3.15.8 Phase 5.3 - Testing and Stabilization.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 5.3).
- **Reason**: the suite proves the TOML schema, the merge algebra, ownership, idempotence, cross-shell parity, and teardown against a temporary filesystem, and the read contract asserts the surfaces exist after an install. What no test can prove from here is that a running Codex build loads the emitted TOML as an agent and fires the merged hooks, because that needs an authorized Codex session on a host that has the product installed.
- **Suggested next step**: fold a manual Codex load check into the same release-readiness pass that owns the other live verifications, then record the observed result in the read-contract verification block.

### v3.15.8 Phase 5 Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| - | Codex custom agents finding-only | Phase 5 | The four Codex agent and hook rows in `platform-capability-ownership.md` flip from finding-only to enforceable, backed by owned writes, `install_verify` checks in `platform-read-contracts.json`, and the new `tests/integrations/test_codex_native.py`. The Phase 1 guard that forbids premature enforcement was tightened rather than removed: `test_unimplemented_surfaces_are_finding_only` now reads an explicit `IMPLEMENTED_CAPABILITIES` map, so a listed capability must be marked enforceable and name its phase while every unbuilt row must still read finding-only. |

### v3.15.8 Phase 5 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 1 | 0 |

**Carryovers.** DF-11, MT-5, and QG-4 remain open and unchanged; Phase 9 still owns the CI reconciliation and the live visual smoke. Phase 5 adds HO-4 and MT-6, both of which are boundaries of what an installer and a filesystem-level suite can establish rather than work that was skipped. It introduces no skipped implementation, known production bug, suppressed warning, or bypassed hard gate.

### v3.15.8 Phase 6 checkpoint

Phase 6 turns the four Gemini CLI and Qwen hook rows enforceable. Both platforms read hooks from a `hooks` key inside their own `settings.json`, so both are served by one shared module (`_settings_hooks.py`) plus a mixin that owns the install and teardown choreography, with the per-platform differences isolated in a spec object. Those differences are real: Gemini CLI renamed every lifecycle event, so `PreToolUse` is `BeforeTool` and `Stop` is `AfterAgent`, while Qwen kept the Claude-style names Nexus-Hub already uses. Both match on their own tool ids as regexes rather than on Claude's tool names as literals, so `Bash` becomes `^(run_shell_command)$` and `Edit` becomes `^(replace)$`, and `Skill` is dropped for want of any equivalent. Only the tool events carry a matcher, because the lifecycle events match on a session source or compact trigger rather than a tool.

Two constraints shaped the design. Neither platform has Codex's `commandWindows` override, and both funnel every shell call through a single `run_shell_command` tool, which collapses Nexus-Hub's separate `Bash` and `PowerShell` matchers onto one id. A registration therefore has to commit to one command string, so the installing host picks it: a Windows install registers the `.ps1` sibling and the PowerShell-flavored guardrails, a POSIX install the `.sh` and the Bash-flavored ones, with both siblings copied either way. And because these hooks live in the file that also holds the user's model, theme, and MCP configuration, the merge is stricter than Codex's dedicated `hooks.json` -- every unrelated key survives, the previous content is backed up, and a malformed file is never rewritten. Ownership is the `nexus-hub:` handler `name`, which is also what Gemini CLI fingerprints project hooks on, so a stable name avoids re-triggering its untrusted-hook warning on every install.

### v3.15.8 Phase 6 Open Items

#### Deferred

##### DF-12 - Gemini CLI extension-packaged hooks are a cleaner write path left unused

- **Source phase**: v3.15.8 Phase 6.1 - Map Gemini CLI Hooks.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 6.1).
- **Reason**: the [extension reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/extensions/reference.md) documents extensions as a fourth hook-precedence layer, reading `~/.gemini/extensions/<name>/hooks/hooks.json` with `${extensionPath}` and `${/}` substitution. That would give Nexus-Hub a fully-owned directory instead of a merge into the user's main config, and would solve the absolute-path and path-separator problems outright. It is not used because the reference documents only `gemini extensions install` for populating that directory, so writing it directly would be an inferred write path of exactly the kind sub-task 6.1 says to record rather than ship; it also has no project scope, where half of this phase's delivery lives. The maintainer chose settings.json now with this recorded as a follow-on.
- **Suggested next step**: if a later release can verify that a directly-written extension directory is loaded (or can shell out to `gemini extensions install` against a local path), migrate global-scope hooks there and keep the settings.json merge for workspace scope.

#### Missing tests / coverage gaps

##### MT-7 - Windows shell dispatch for these two platforms is asserted, not observed

- **Source phase**: v3.15.8 Phase 6.3 - Testing and Stabilization.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 6.3).
- **Reason**: the host-aware branch is fully tested in both directions, and CI runs the suite on a Windows runner, so what gets *written* on Windows is proven. What is not proven is which shell each CLI actually launches the command with. The workspace-scope command references `$env:GEMINI_PROJECT_DIR` / `$env:QWEN_PROJECT_DIR` in PowerShell syntax; if a Windows build dispatches through `cmd.exe` instead, the variable stays literal and the hook fails to find its script. Neither platform's documentation states the Windows shell, and the failure mode is bounded: Gemini CLI's exit-code contract makes any non-zero exit other than 2 a warning that lets the interaction proceed, so a wrong guess degrades to a warning rather than a block.
- **Suggested next step**: during release readiness, run one project-scope hook on a Windows host with each CLI installed and record the observed shell in the read contract; if it is `cmd.exe`, switch the workspace reference to `%VAR%` form behind the same host check.

### v3.15.8 Phase 6 Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| - | Gemini CLI native hooks finding-only | Phase 6 | Row flipped to enforceable, backed by an ownership-scoped `settings.json` merge at both scopes, a `hooks_supported` contract-check entry, and the shared `tests/integrations/test_settings_hooks.py`. |
| - | Qwen native hooks finding-only | Phase 6 | Same, plus `install_verify` surfaces for `~/.qwen/settings.json` and `~/.qwen/hooks`, and the `shell` / `statusMessage` fields Qwen documents and Gemini CLI does not. |

### v3.15.8 Phase 6 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

**Carryovers.** HO-4, MT-6, DF-11, MT-5, and QG-4 remain open and unchanged. Phase 6 adds DF-12 (a documented alternative write path deliberately not inferred) and MT-7 (the Windows shell each CLI dispatches through is undocumented upstream). Both are limits of what verified documentation supports rather than work that was skipped, and both have bounded failure modes. Existing deny controls are unaffected: the `git-guardrails` and `secret-scan` guardrails are registered on both platforms wherever a matcher exists, and no hook was mapped onto an approximation. Phase 6 introduces no skipped implementation, known production bug, suppressed warning, or bypassed hard gate.

### v3.15.8 Phase 7 checkpoint

Phase 7 delivers three of the four Kimi rows and corrects the fourth rather than shipping it. Re-verification against the official agent, hook, tool, and configuration references changed both halves of the phase from what the matrix assumed.

Custom agents turned out to need no transform at all. Kimi discovers Markdown agent files with YAML frontmatter and explicitly accepts the Claude Code shape the catalog already ships -- `description` is the only required field, `name` falls back to the filename, the comma-separated `tools` form exists specifically to "keep Claude Code-style agent files loadable", and unknown fields are ignored. So the catalog agents are copied verbatim at both scopes, which means an agent behaves identically on Kimi and Claude, and only validation is applied (a file with no description, no body, or a non-kebab-case name is skipped rather than shipped for Kimi to reject).

Hooks went the other way and got harder. Kimi's `[[hooks]]` entries permit only `event`, `matcher`, `command`, and `timeout`, and the docs state that any extra field makes the config file fail to load -- so the handler-`name` ownership Phase 6 used for Gemini CLI and Qwen is not merely unavailable here, emitting it would break the user's entire configuration. Ownership is a marker-delimited managed block instead, spliced into `config.toml` without ever parsing and re-emitting the user's TOML, which preserves their comments and table order byte-for-byte and needs no non-stdlib round-tripper. The merged result is validated with `tomllib` and rolled back on failure, and a file that was already invalid is left untouched so the block cannot be mistaken for the cause. Event names need no translation and Kimi's tool names match Claude's for `Bash`, `Write`, `Edit`, and `Skill`, so the matcher mapping is near-identity.

Two incidental corrections came out of the work. `IntegrationBase._copy_file` is ownership-blind -- it keeps any existing destination unless the whole install runs with `--overwrite` -- so it cannot satisfy the matrix's manifest-driven repair requirement; the Phase 5 `write_owned_file` primitive was lifted into a shared `_owned` module and reused rather than duplicated. And both installers were still printing `Kimi (.kimi/agent.yaml + system.md)` as the workspace display name, advertising a path dropped in v3.15.0 Phase 4; that is now the real `.kimi-code/` surface.

### v3.15.8 Phase 7 Open Items

#### Deferred

##### DF-13 - Kimi has no project-scoped hook path, so workspace hooks are undeliverable

- **Source phase**: v3.15.8 Phase 7.2 - Merge Kimi TOML Hooks.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 7.2).
- **Reason**: the matrix assumed a project `.kimi-code/config.toml`. That file does not exist -- Kimi's project-local configuration is `.kimi-code/local.toml`, which the [configuration reference](https://www.kimi.com/code/docs/en/kimi-code-cli/configuration/config-files) documents as holding only a `[workspace]` table with `additional_dir`, and `[[hooks]]` is documented exclusively in the user-level `~/.kimi-code/config.toml`. Sub-task 7.2 says to reject undocumented paths, so the workspace hook row stays finding-only with the reason recorded in the row itself rather than shipping an invented destination. The practical impact is bounded: hooks installed at global scope apply to every project, so a user loses per-project hook scoping, not the guardrails.
- **Suggested next step**: if Kimi later documents project-scoped hooks (in `local.toml` or elsewhere), deliver them through the same marker-block merge, which is scope-agnostic already.

#### Missing tests / coverage gaps

##### MT-8 - Kimi agent and hook delivery is not observed against a real Kimi install

- **Source phase**: v3.15.8 Phase 7.3 - Testing and Stabilization.
- **Plan reference**: `docs/v3/v3.15/plans/v3.15.8-platform-parity-and-github-usage-monitor.md` (sub-task 7.3).
- **Reason**: the suite proves the verbatim copy, the four-field schema, comment and table preservation, rollback, duplicate suppression, host-selected commands, and teardown against a temporary filesystem, and CI runs it on Windows. What no test here can prove is that a running Kimi build lists the copied agents alongside its built-ins and fires the spliced hooks. This is the same boundary as MT-6 for Codex and MT-7 for the Gemini-CLI-class platforms.
- **Suggested next step**: fold a Kimi load check into the same release-readiness pass that owns MT-6 and MT-7, confirming `/hooks` lists the block's entries and the agents appear in Kimi's agent list.

### v3.15.8 Phase 7 Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| - | Kimi custom agents finding-only (both scopes) | Phase 7 | Rows flipped to enforceable. Verbatim validated copy to `~/.kimi-code/agents/` and `.kimi-code/agents/`, manifest-owned so a user-authored agent survives and a drifted owned one is repaired. The shared `~/.agents/agents/` and `.agents/agents/` paths are deliberately not claimed. |
| - | Kimi native hooks finding-only (global) | Phase 7 | Row flipped to enforceable via a marker-managed `[[hooks]]` block in `~/.kimi-code/config.toml`, with `contract_checks` and three `install_verify` surfaces. |
| - | Stale deprecated Kimi path in both installer summaries | Phase 7 | The workspace display name advertised `.kimi/agent.yaml`, dropped in v3.15.0 Phase 4. Both installers now name the real `.kimi-code/` surface. |
| - | `_copy_file` cannot repair a drifted owned file | Phase 7 | Found by a Phase 7 test. `write_owned_file` moved from `_codex_native` into a shared `_owned` module and reused by Kimi, so there is one manifest-aware write rather than two. |
| - | Teardown could raise `PermissionError` and abandon the rest of an uninstall | Phase 7 | Found by the pre-existing `test_contract.py`. On Windows a delete-pending file vanishes from a directory listing but still blocks `rmdir`, so the empty-directory cleanup shipped in Phase 5 (Codex) and Phase 6 (the settings-hooks mixin) could crash mid-teardown. Consolidated into `_owned.remove_dir_if_empty`, which logs and reports `kept` instead of raising; all three integrations now share it. |
| - | Kimi agents were written twice per install | Phase 7 | Found by `test_contract.py`'s dry-run histogram comparison. Declaring `agents_subdir` made the base `_mirror_catalog` copy `catalog/agents` in addition to the integration's own validated, ownership-aware writer. The key is now deliberately unset, with the read path still asserted via `doc_mentions` and `install_verify`. |

### v3.15.8 Phase 7 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 0 |
| Bugs / regressions (BG) | 0 | 3 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

**Carryovers.** DF-12, MT-7, HO-4, MT-6, DF-11, MT-5, and QG-4 remain open and unchanged. Phase 7 adds DF-13 (Kimi documents no project hook path, so that row is corrected rather than delivered) and MT-8 (delivery is not observed against a running Kimi build).

It also resolves four defects, three of them latent and none introduced by this phase's own feature work. Two came from the pre-existing `test_contract.py`, which is worth noting because it is the suite that runs every integration through the same lifecycle: its dry-run histogram caught the double agent write, and its uninstall case caught a teardown crash that had shipped in Phase 5 and Phase 6 and would have abandoned an uninstall partway through on Windows. The other two are the ownership-blind `_copy_file` that would have left a drifted agent unrepaired on any platform using it, and the stale `.kimi/agent.yaml` label both installers were still printing a full minor version after that path was dropped.

Existing deny controls are unaffected; `git-guardrails` and `secret-scan` are registered wherever Kimi has a matching tool name, and Kimi's fail-open hook semantics are stated in the install summary rather than left implied. Phase 7 introduces no skipped implementation, known production bug, suppressed warning, or bypassed hard gate.

### v3.15.8 Phase 8 checkpoint

Phase 8 closes the last four platform rows, and the headline finding is that most of the Copilot surface did not need building. Copilot in VS Code reads Claude-format customization files **by default**: its documented `chat.hookFilesLocations` default includes `~/.claude/settings.json` and `.claude/settings.json`, it "uses the same hook format as Claude Code and Copilot CLI for compatibility", and its default workspace agent locations include `.claude/agents`. Nexus-Hub already writes all three. So Copilot hooks at both scopes and Copilot project agents were already live, and the correct action was to record that rather than build a parallel surface -- a `.github/hooks/*.json` or `.github/agents/*.md` copy would be a redundant, commit-visible duplicate in the user's repository, which is the same policy concern that keeps `.github/skills/` opt-in, and agent files deduplicate across levels by filename anyway. Those rows are marked enforceable-as-inherited, with a new contract test asserting the dependency in the direction it actually runs: if the `claude` integration ever stopped writing those paths, Copilot's coverage would silently vanish.

The one genuine gap was global agents. `~/.copilot/agents` is Copilot's documented user-profile agent path and `~/.claude/agents` is not, so outside a repository Copilot saw no catalog agents at all. Those now ship verbatim as `<name>.agent.md`, since Copilot accepts the catalog's Claude-style frontmatter as-is and documents Claude's tool names as aliases -- the third platform in this plan (after Kimi and, for its body, Codex) where the right answer was a validated copy rather than a transform. Validation covers Copilot's required `description` and its 30,000-character prompt cap, detection accepts either a VS Code user dir or an existing `~/.copilot`, and absence produces a not-detected note rather than a false claim.

Hermes resolved in the opposite direction from the v3.15.2 expectation. The upstream rule is quoted plainly -- "Hermes discovers skills by listing every subdirectory of the tap path and probing each for `SKILL.md`" -- so discovery is one level, not recursive, and the flattened layout Nexus-Hub already writes is **required**. A category-nested migration, which the v3.15.2 note treated as a possible future alignment, would have hidden every skill at depth 2 and broken discovery outright. No migration was performed; a regression test now pins both halves of the invariant.

### v3.15.8 Phase 8 Open Items

None. Phase 8 introduces no deferred item, missing-test gap, or hand-off of its own.

### v3.15.8 Phase 8 Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| - | Copilot custom agents finding-only (both scopes) | Phase 8 | Global ships verbatim to `~/.copilot/agents/*.agent.md`, validated and manifest-owned. Workspace is enforceable-as-inherited from `.claude/agents`, a documented Copilot default, with no committed `.github/agents` duplicate. |
| - | Copilot native hooks finding-only (both scopes) | Phase 8 | Both scopes enforceable-as-inherited from `~/.claude/settings.json` and `.claude/settings.json`, both documented Copilot default hook locations carrying the same format. `hooks_supported` stays false so no summary claims a Copilot-owned hook surface. |
| - | Copilot global hooks recorded as "no supported destination proven" | Phase 8 | Disproven. The destination exists and is already populated; the row is now inherited rather than unavailable. |
| - | Hermes nesting claim unresolved since v3.15.2 | Phase 8 | Resolved against the upstream discovery rule. Discovery is depth-1, so the existing flattened delivery is required; the earlier "recursive discovery" premise in the drift audit is corrected. Rows flipped to fully enforceable with no migration. |
| BG | Category-level `catalog/skills/code-review/references/` shipped as a bogus skill on nine platforms | Phase 8 | Found by the new Hermes depth-1 test. Four checklists sat at the category level instead of inside a skill, so `flatten_skills` presented `references` as a skill with no `SKILL.md` on every flattened platform, and the three sibling skills citing `references/<file>.md` had relative paths that did not resolve. Relocated into each citing skill's own `references/` per the per-skill bundling convention; the bundle audit stays at 0 errors. |
| BG | A test run wrote 23 agent files into the developer's real `~/.copilot/agents` | Phase 8 | Introduced and fixed within this phase. Adding a second global detection signal meant `test_copilot_install_global_skips_without_vscode`, which patched only `_vscode_user_dir`, no longer short-circuited `install_global` on a host that really has `~/.copilot`. The leaked files were removed and the design corrected: `~/.copilot` is now reached only through a patchable `_copilot_home()` accessor mirroring `_vscode_user_dir()`, both affected tests isolate it, and a new test asserts `install_global` routes through the accessor so a future global surface cannot bypass it. |

### v3.15.8 Phase 8 Summary

| Category | Open | Resolved |
|---|---:|---:|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 3 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 0 | 0 |

*(The third BG is the GitHub monitor lockfile defect recorded in the Phase 9 reconciliation section below; it surfaced during the integration push, after the Phase 8 commit.)*

**Carryovers.** DF-13, MT-8, DF-12, MT-7, HO-4, MT-6, DF-11, MT-5, and QG-4 remain open and unchanged, and Phase 9 owns the reconciliation. Phase 8 adds nothing to that list: the two things it could not prove locally are the same live-observation boundary already tracked as MT-6, MT-7, and MT-8, and no new deferral was needed because the Copilot rows resolved to inheritance rather than to partial delivery.

Both resolved bugs were found by tests rather than by review, and one of them was this phase's own: adding a second global detection signal let an existing Copilot test escape its patch and write into the developer's real home directory. That is worth recording rather than quietly fixing, because the lesson generalizes -- a global surface must be reachable only through a patchable accessor, and adding a second one to an existing gate silently widens what an old test can touch.

### v3.15.8 Phase 9 reconciliation (9.2)

Every v3.15.8 gap now has a disposition, an owner, and a next step. This is the consolidated view; each item's own entry above carries the detail.

| ID | Disposition | Owner / next step |
|---|---|---|
| DF-9 | **Resolved** (Phase 9.2) | All 18 ownership-matrix rows are enforceable across Phases 5-8. Re-entry condition met in full; closed at its own entry above. |
| DF-10 | **Retained deferral** (maintainer-blocked) | The exact 20x20 SVG and its redistribution/trademark evidence were never supplied, so Phase 3 packaged a deterministic derived icon instead of the observed 14x14 gradient PNG. Nothing in the shipped package depends on the missing asset. Re-entry is unchanged: the maintainer supplies the SVG plus provenance, or the derived icon stands. |
| DF-11 | **Accepted retained difference** (Phase 9.3) | Per-path job gating was not adopted repo-wide, so the divergence from T028's literal wording stands with `ci.yml` as the compensating control, now test-asserted. |
| DF-12 | **Retained deferral** (upstream-blocked) | Gemini CLI extension-packaged hooks would be a cleaner write path, but only `gemini extensions install` is documented for populating that directory and it has no project scope. Re-entry: a later release that can verify a directly-written extension directory is loaded. |
| DF-13 | **Retained deferral** (upstream-blocked) | Kimi documents no project-scoped hook path (`local.toml` carries only `[workspace]`). Global hooks apply to every project, so the loss is per-project scoping, not the guardrails. Re-entry: upstream documenting a project hook path. |
| MT-5 | **Transferred to v3.15.9** | `src/extension.ts` sits at 34.74% statements because activation, authorized refresh, native settings dispatch, and toast actions need an Extension Development Host harness the package does not have. Package coverage passes its thresholds (82.09% statements, 87.32% lines), so this is a coverage-shape gap rather than a release blocker, and building an EDH harness is its own piece of work. |
| MT-6 / MT-7 / MT-8 | **Consolidated into one release-readiness live pass** | Codex agents/hooks, the Windows shell each of Gemini CLI and Qwen dispatches through, and Kimi's agents/hooks are all "written correctly, not observed running". They share one precondition -- a host with those products installed -- so they are one pass, not four. The Copilot agents-dropdown check from Phase 8 joins it. |
| HO-4 | **Retained hand-off** (by design) | Codex hooks stay inert until the user trusts them via `/hooks`. No installer can perform an interactive trust confirmation; the install summary says so at both scopes. Nothing further to do in code. |
| QG-2 / QG-3 | **Resolved** (Phase 4) | `ci.yml` now collects `tests/plans` and `tests/workflows`; the GitHub monitor has a path-filtered Node 22 gate. |
| QG-4 | **Retained deferral** (environment-blocked) | The interactive light/dark/high-contrast smoke needs a GUI session this non-interactive environment cannot observe. Automated tests cover theme tokens, semantic labels, focus styling, responsive layout, reduced motion, CSP, escaping, and the unknown-limit fallback; what is missing is a human render, including the teal meter fill. Joins the same release-readiness pass as MT-6/7/8. |

**Nothing was deleted.** Every historical gap from v3.15.0 through v3.15.7 remains as written, including the v3.15.6 correction notice about WN-v36-1.

#### Post-commit addition: the integration push found one more defect

##### BG - GitHub monitor lockfile was Linux-incomplete by construction - RESOLVED (2026-08-03)

- **Source**: the v3.15.8 integration push to `develop`, after the Phase 9 commit. The `github-usage-monitor` workflow failed on `npm ci` with `@emnapi/runtime@1.11.3` and `@emnapi/core@2.0.0-alpha.3` missing from the lock file, while the identical command passed on the Windows dev host.
- **Root cause**: the extension devDepended on `sharp` (plus `svg2ttf`, `svgpath`, `ttf2woff2`). On Linux npm resolves `@img/sharp-linux-*`, which requires those two `@emnapi` packages; on Windows it resolves `sharp-win32-*`, which does not. A lockfile generated on Windows is therefore Linux-incomplete **by construction**, and no Windows-side npm invocation repairs it -- `--package-lock-only`, a full delete-and-regenerate, and `--os=linux --cpu=x64 --libc=glibc` all reproduce the same Windows-shaped tree.
- **Why it recurred**: this is the same class v3.15.7 fixed for the Claude and Codex monitors (commit `598519c0`), which is why those two locks already carried hoisted `@emnapi` entries and the newer GitHub monitor did not. Fixing it the same way would have left the next dependency bump to reintroduce it.
- **Resolution (commit `17ed7317`)**: the four packages exist only to regenerate `icon.png` and `fonts/github-icons.woff2` via `npm run generate:icons`. Both assets are committed and no build, test, coverage, or packaging step reads them from source -- CI runs only compile, `test:coverage`, `package`, and `verify:package`. They were removed from `devDependencies` and documented as install-on-demand in a `//generate:icons` note beside the script. The lock drops from 494 to 378 packages with zero `@emnapi`, `sharp`, or `wasm32-wasi` entries, so the platform divergence is eliminated at the root rather than patched, and `npm audit` now reports 0 vulnerabilities. Verified by a clean `npm ci`, compile, 103 tests, unchanged coverage (82.09% statements / 87.32% lines), a 39-file VSIX, 37-file content verification, and a green `github-usage-monitor` run on `develop`.
- **Standing lesson**: a lockfile committed from a single platform is only valid for that platform's optional-dependency graph. Prefer removing a build-time-only native dependency over regenerating its lock, because the removal is permanent and the regeneration is per-bump. Two items are transferred rather than closed (MT-5 to v3.15.9) or consolidated (MT-6/7/8 plus QG-4 and the Copilot check into one live pass); the rest are resolved or are genuine upstream and environment limitations with dated reasons.

**Monitor-specific findings recorded explicitly**, per 9.2's requirement: GitHub's billing summary APIs remain public preview and may change shape without notice (the provider normalizes defensively and keeps unknown quotas percentage-free); personal-scope endpoints omit managed Copilot seats; no authorized billing credential was ever available in this plan, so every live billing path is unexercised (HO-3's original subject, resolved by choosing the fine-grained-token fallback); and the supplied brand asset limitation is DF-10 above. No monitor claims a percentage it cannot compute, and nothing is scraped.

The existing Copilot skills selector is unchanged and asserted non-regressed (off by default, bundle-id or `all`, never overwriting a committed file). Existing deny controls are unaffected -- and in Copilot's case they were already active through the Claude path, which is precisely what this phase established. Phase 8 introduces no skipped implementation, known production bug, suppressed warning, or bypassed hard gate.
