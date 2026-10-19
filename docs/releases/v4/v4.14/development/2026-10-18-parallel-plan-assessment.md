# v4.14 Parallel Plan Assessment

This release-scoped assessment answers whether the seven approved v4.14 plans can be implemented concurrently. It records current dependencies, overlapping source files, prospective worker lanes, shared metadata ownership, and the native run-contract change required before automatic scheduling. It does not admit a member or change the signed run.

## Observed Constraints

The queue enumerator exits 0. It reports v4.14.1 through v4.14.6 queued. Its v4.14.0 Status parser reports unknown; the explicit approved minor run and actual 32/34 task state establish that member as in progress. No plan was unreadable. Membership is the frozen seven-member run, not a count of open checkboxes.

The current completion contract requires the previous member to be PLAN COMPLETE, its release back-merged into the integration tip, and member-start recorded at that tip. Therefore the present approved run admits members sequentially. Starting extra agents alone does not change that constraint. No member-start, frozen plan prose, approval, HMAC, version order or queue membership was changed for this assessment.

The existing plan/implement commands identify parallel candidates and suggest separate sessions. They do not currently provide an automatic multi-plan dispatcher. Their isolated-worktree support supplies one useful prerequisite, not the scheduling or native admission mechanism.

## Candidate Schedule

| Plan | Current assessment and evidence | Prospective lane |
|---|---|---|
| v4.14.0 | In progress; owns installer core settings, platform defaults and model-routing. Its merge is an explicit prerequisite for v4.14.5 and v4.14.6. | Finish current integration first. |
| v4.14.1 | Ordering impact with v4.14.2 and v4.14.3 through model-routing/SKILL.md; with v4.14.2 and v4.14.4 through implement-phase-runbook.md. | Lane A after v4.14.0. |
| v4.14.2 | Ordering impact with v4.14.1; its predecessor table explicitly says DoD3 builds on the effort/cache note. It supplies test_rule_ownership.py and decision-policy-harness.md required by v4.14.4. | Lane A after v4.14.1. |
| v4.14.3 | Ordering/content impact with v4.14.1 and v4.14.2 through routing and the read contract. v4.14.4 explicitly declares no impact from v4.14.3. | One worker after v4.14.2. |
| v4.14.4 | Hard prerequisite: v4.14.2 Phase2 landed. It reads v4.14.1 verification behavior before extending the gate. Its functional paths are disjoint from v4.14.3, but both still update the shared release ledger. | Another worker beside v4.14.3, after shared metadata is coordinated. |
| v4.14.5 | Ordering impact with v4.14.0 through configs/platform-defaults.json and platform-defaults-levers.md. Its table explicitly declares no impact from v4.14.1 through v4.14.4; declared implementation files are disjoint from them. | Lane B after v4.14.0, beside v4.14.1 and then v4.14.2. |
| v4.14.6 | Installer overlap with v4.14.0; Claude-id parity consumes the v4.14.3 model map; guardrails and omitted-key controls consume v4.14.4 and v4.14.5. Its plan allows Not-Settable when those are absent, but finishing the preceding features first avoids that reduction. | Follow v4.14.3, v4.14.4 and v4.14.5 for complete controls. |

With coordinator-owned shared metadata, the prospective waves are v4.14.1 plus v4.14.5; then v4.14.2 while any independent v4.14.5 work continues; then v4.14.3 plus v4.14.4; then v4.14.6. Releases remain in semantic-version order. This is a dependency-based recommendation, not a measured speedup or a claim that the current contract already permits it. None of these is a documentation-only plan to move ahead of capability work.

## Shared Surfaces

The release known-gaps file is shared by several task lists and is also updated by mandatory final duties that some task lists omit. Global progress, generated catalog state, version files, changelogs and release bookkeeping likewise need explicit ownership. A dispatcher must not treat the task-path inventory as complete or silently ignore these collisions.

One concrete stale assessment is v4.14.2 declaring no owner overlap with v4.14.0 even though both task inventories name catalog/skills/ai-development/model-routing/SKILL.md. v4.14.1 also names catalog/commands/implement.md in its DoD although that path is missing from its task-derived touched list. The v4.14.6 workflow task spells github/workflows/nexus-hub-settings.yml without the leading dot. These are reasons for fresh content review and verified write claims before automatic admission, not permission to rewrite the frozen plans.

## Required Changes

1. Have /plan record implementation prerequisites, claimed read/write surfaces and coordinator-owned metadata. Use the current queue assessment as evidence; missing or uncertain independence defaults to sequential execution.
2. Give /implement one coordinator and a bounded worker pool, initially at most three workers. Automatically create one branch and isolated worktree per eligible plan, assign exclusive source ownership, and apply the same approved aggregate spend limits. Each worker retains focused phase checks and one local commit per phase.
3. Separate native implementation admission from integration/release admission. Record each worker baseline and owned commits; retain release order, fresh integration-base checks, exact approval binding and all final completion predicates. Old approved records must retain their existing meaning unless an explicit supported transition is authorized.
4. Coordinate shared ledgers and generated state. Before publication, refresh each candidate against the current integration tree, reconcile any drift, and rerun affected checks. Queue complete-plan validation, hosted CI, merges and releases through the coordinator. Do not push incomplete worker phases.
5. Keep the coordinator separate from worker worktrees that must be deleted. Extend native cleanup and interruption handling so a failed, paused or edited worker cannot lose another worker's files or invalidate the approval record.

## Verification Limits

The evidence is the current enumerator output, task-path intersections and the six plans' explicit predecessor and prerequisite sections, inspected on commit 33d11b6991ae4f29fc5fcffbf9466ca12d34ce07. The inventory is a lower bound on actual writes. No automatic scheduling implementation, contract migration, additional plan start or elapsed-time benchmark has been performed. The immediate v4.14 work remains the current CodeQL correction and green integration of PR485.
