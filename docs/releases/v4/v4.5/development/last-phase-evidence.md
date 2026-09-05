# v4.5.0 Last-Phase Evidence

**Date**: 2026-09-04
**Plan**: `docs/releases/v4/v4.5/plans/v4.5.0-anti-cliche-and-agent-security.md`, Phase 7 of 7
**Revision under review**: `440f6985` (phase 6 commit) on `feat/v4.5.0-anti-cliche-and-agent-security`, base `develop` at `8a426441`
**Model routing**: plan asked frontier / max; session ran `claude-fable-5-1` (frontier) at high. The `/effort max` keystroke was surfaced at the boundary and the phase proceeded at high under the in-full driver; recorded under `WN-2` in `known-gaps.md`.

Each section quotes the proving command or scan. The per-clause goal review the plan's sub-task 7.2 asked for is the companion file `phase-7-evidence.md`; the `## Goal-vs-codebase review` section below summarizes it.

## Architecture refactor

Over-engineering pass (plan sub-task 7.1, T026), answering the plan's three questions against the tree rather than assuming:

1. **Should `test_writing_discipline_rule.py` and `test_construction_discipline_rule.py` collapse into one data-driven validator?** Compared side by side (196 and 175 lines): both carry the same three roster constants (`_LOCKSTEP`, `_UNGUARDED`, `_INCLUDE_ONLY`) and five structurally identical tests (presence on twelve, byte identity, shim absence, size budget, parity-guard lockstep). Each also carries one block-specific test (`test_the_self_check_binds_live_replies` versus `test_the_rule_is_not_nested_in_output_minimization`). The duplication is real: three copies of the template roster now exist (two test modules plus the parity script). Decision: `construction-debt: keep both modules until a third invariant block appears`. Reasons: the v4.1.2 evidence and this plan both cite the construction module by file name; a parametrized module would report a failure as a parameter id rather than a file name a reader can open; and the shared part is roughly 60 lines. The trigger for consolidation is the third block, at which point the roster should also move to one shared helper the parity script reads. Recorded in `known-gaps.md` as a note.
2. **Was the phase 1 temporary presence test removed once phase 2 relocated its assertions?** `grep -n "Writing Discipline" tests/validators/test_check_base_template_parity.py` returns only the two phase 2 negative cases (lines 144 to 167: mutate a lockstep body, mutate a heading, assert the guard names the block) and no presence assertion. The permanent presence assertion lives once, in the companion validator. Not duplicated.
3. **Does the detector duplicate what the block prohibits?** The block prohibits nine move classes plus punctuation and leftovers; the detector encodes 29 ids, 26 advisory and 3 defect. Overlap is by design and is layering, not redundancy: the block is the always-loaded rule (Tier 1 of the instruction file), the detector is the on-demand measurement (Tier 3 of a skill). Removing either would leave the other without its counterpart; the block cannot measure and the detector cannot instruct on every turn. Nothing deleted.

Delete-list applied: empty. Project-refactor scans: `find . -type d -empty` (excluding `.git`, `node_modules`, `__pycache__`) returned nothing; `python scripts/check_docs_conventions.py --root docs/releases/v4/v4.5` printed `OK: docs conventions hold`; `python scripts/check_docs_retention.py` printed `nothing due for archival (current v4.4, threshold 2 minors)`. No file moved, so no reference repair.

## Known-gaps reconciliation

Disposition for `docs/releases/v4/v4.5/known-gaps.md` (this version) and every other `docs/**/known-gaps.md` with open items. Glob `docs/releases/v4/*/known-gaps.md` returned six files (v4.0 to v4.5); no legacy-layout files exist.

- **v4.5** (this file, rewritten this phase with derived counts): open `DF-1` (human check of the always-on clause's effect on replies), `DF-2` (no reachability or shared-service enumeration on this repository's own agent surface), `DF-3` (mannered prose and the stranded auxiliary rely on model judgment; the detector cannot express them), `MT-1` (the four human tests are unrun), `WN-2` (phases 3, 5, and 7 ran at high against a max recommendation), `WN-3` (the model-prompting profile layer lists `claude-fable-5` while the live roster has `claude-fable-5-1`); resolved `WN-1`.
- **v4.4** (`Status: published in the v4.4.5 tag`; open `DF-1`, `WN-1`, `WN-2`; the plan's mention of `MT-1` is already resolved in that ledger at its own Phase 7, PR #150). Carry-forward: `DF-1` (three platform marks pending vendor assets) stays owned by the v4.4 ledger; nothing in v4.5 touches platform marks. `WN-1`'s suggested next step (re-surface the tier recommendation at every later pre-flight) was executed by every v4.5 phase and is recorded as `WN-2` here; `WN-2` (assertion register) was scoped to v4.4 guide phases 3 to 7, which are complete. Both are closable. The v4.4 file itself was NOT edited from this branch because a concurrent v4.4.6 session in the main checkout has it modified and uncommitted; editing it here would guarantee a merge conflict on the integration pull request. The closure is recorded in the v4.5 file's carry-forward section for that session or the release step to apply.
- **v4.0** (finalized; open `DF-1` non-lockstep seven not byte-locked, `WN-2`, `MT-1`, `MT-3`, `DF-1`, `DF-2`, `WN-1`, `BG-2`): v4.5 narrows v4.0 `DF-1` for one block, since the companion validator asserts byte identity of `## Writing Discipline` across all twelve; the general gap (the other shared sections on the seven) stays open there. Nothing else in v4.5 touches those items.
- **v4.1** (finalized; open `DF-1` prompting profile versus live Codex roster, `DF-1` optional scanners): the same class of drift now exists for Claude (`WN-3` here). v4.1's item stays owned by its ledger.
- **v4.2**, **v4.3** (finalized; open `DF` and `WN` items on the guide validator, workshop validation, CI profiles, pip caches, OpenClaw interception, ownership guard, web-UI settings, optional surfaces): none touched by v4.5; all remain owned by their ledgers.

Grep for markers introduced this version: `git diff origin/develop..HEAD | grep -E "^\+.*(TODO|FIXME|XXX|HACK|# DEVIATION:)"` returns only the six history-file sentences reading `None marked # DEVIATION:`. No unrecorded work.

## Living docs architecture

- `docs/handbooks/` (markdown, html, README) does not enumerate instruction-template sections; `grep -rn "Construction Discipline\|Writing Discipline\|Communication Style" docs/handbooks/markdown/*.md` returns nothing, so no handbook page is stale. No new skill was added (329 unchanged), so no count page changes.
- `docs/decisions/`: one new record, `implemented/policy/2026-09-04-writing-discipline-binds-chat-replies.md`, with `## Alternatives considered` and `## Consequences`; `python scripts/validate_decision_records.py` result is quoted in the full-suite section.
- `docs/README.md`, `docs/DEVLOG.md`: the DEVLOG is a one-line-per-release index and gains its v4.5.0 line at `/update release`, which owns that step; not edited here. `docs/todos.md` still shows the v4.4.2 dashboard; it is modified and uncommitted in the concurrent v4.4.6 session's checkout, so it was not refreshed from this branch (same conflict reason as the v4.4 ledger). Recorded as a note for the release step.
- `grep -rln "## Communication Style"` outside archives: `docs/policy/doc-budgets.md` (the Recorded raises entry that documents the retirement, correct), plan and history files that describe the retirement (correct), and `examples/django-api-CLAUDE.md`, `examples/go-microservice-CLAUDE.md` (downstream example project files with their own section of that name; not templates, not distributed by the installer, left alone).
- Self-gate: no `docs/testing/` or `docs/validation/` was invented.

## Git-tree hygiene

`python scripts/check_release_preconditions.py --branches --repo-settings` (report only, nothing deleted):

```text
Branch hygiene (merged into origin/develop)
  5 merged branch(es) are cleanup candidates:
    - origin/backmerge/v4.4.5
    - origin/docs/v4.5-v4.7-plans-and-comparisons
    - origin/feat/v4.4.3-guide-illustration-rebuild
    - origin/fix/v4.4.5-codeql-fixtures
    - origin/release/v4.4.5
  (11 branch(es) with an open PR were excluded)
  1 branch(es) survive a CLOSED, unmerged PR:
    - origin/backmerge/v3.20.0
  delete_branch_on_merge does NOT cover these. Review and delete by hand.
Repository settings
  OK: delete_branch_on_merge is enabled
  OK: repository description agrees with README.md
```

Local: the `nh-v45` worktree tree was clean at `440f6985` before this phase's writes; the helper scripts (a validate-target runner and the per-phase edit scripts) live in the operator's home directory outside the repository and are removed after the plan closes.

## CI/CD coverage

Terminal pipeline reconciliation via `cicd-architect`, existing-pipeline comparison mode.

- **DETECT**: GitHub Actions, eleven workflows under `.github/workflows/`; `ci.yml` is the pull-request pipeline. `git diff --stat origin/develop..HEAD -- .github/` is empty: no pipeline file changed in any phase, matching all six per-phase CI impact records ("no pipeline file changed").
- **COMPARE**, field by field, with observable evidence:

| Field | Evidence | Result |
|---|---|---|
| Profiles / event separation | `ci.yml` (pull request), `post-merge.yml`, `release.yml` separate; unchanged since the v4.4.5 reconciliation on 2026-09-04 | PASS |
| Always-resolving aggregate required check | `python scripts/check_required_check_coverage.py`: `Required-check coverage: OK -- 10 declared context(s) across 2 branch(es), every one produced unconditionally`; `ci-required` job at `ci.yml:675` | PASS |
| New guards inside existing jobs | Phase 2 validator and phase 4 tests live under `tests/validators/` and `tests/verification/`; the `tests` job runs the whole `tests/` tree (`ci.yml:253`) and `tests/workflows/test_ci_runs_every_repo_test.py` guards that; the parity script runs in `validate` | PASS, no new job |
| Permissions | top-level `permissions:` at `ci.yml:47` | PASS |
| Immutable action references | every `uses:` pinned to a 40-character SHA with a version comment (`checkout@93cb6efe...`, `setup-python@ece7cb06...`, `cache@0057852b...`) | PASS |
| Caching | `actions/cache` in `guide-render` (`ci.yml:295`); pip caches not keyed by manifests is v4.3 `DF-2`, unchanged | PASS with recorded gap (v4.3) |
| Concurrency | `concurrency:` with `cancel-in-progress: true` at `ci.yml:52-54` | PASS |
| Path scoping | job-level `changes` filter job (`ci.yml:88`), no workflow-level `paths:` | PASS |
| Artifact retention / structured reports | v4.3 `DF-3` (report profile does not publish structured evidence), unchanged | recorded gap (v4.3) |
| Deployment boundaries / failure recovery | `release.yml` unchanged; a red required check reopens this phase per the runbook | PASS |

- **PROPOSE / APPROVE / APPLY**: no difference attributable to this plan; nothing proposed, nothing applied. The two pre-existing differences remain owned by the v4.3 ledger.
- **RECORD**: no new gap.
- **Cross-installer parity** (two installers ship): `python scripts/check_installer_parity.py` printed `installer parity: PASS`. `python scripts/verify_platform_contracts.py` and `check_platform_contract_freshness.py` pass inside the `validate` target (platform-contract-verification).

Conclusion: PASS. Every required field has observable evidence; none of it rests on a green run.

## Tier 3 deep pass

### Tier 3 blast-radius verdict

- **Verdict**: run
- **Diff evidence**: `templates/ai-instructions/*.md` (twelve distributed instruction templates), `catalog/skills/**` (five distributed skills, one bundled script, one new reference file, trigger evals), `scripts/check_base_template_parity.py` (a release-gate validator), `docs/policy/doc-budgets.json` (a gate threshold), `data/skills.json` (registry)
- **Reason**: distributed catalog content, templates, a validation boundary, and a skill contract all changed; three of the five triggers apply
- **Ambiguity check**: none

### Inventory and exercise

| Feature | Source | Artifact | Real boundary exercised | Observed | Status |
|---|---|---|---|---|---|
| Writing Discipline block on every platform | Phase 1 | twelve templates | Read each template file; installer live run NOT RUN on this host by standing instruction (never run the installer sandboxed or unapproved here); template-to-instruction-file copy covered by `catalog/hooks/tests/test_installer_smoke.py` (33 passed) and `tests/installer/` | 12 of 12 present, 4 shims include it | verified, one qualified boundary |
| Mechanical guard | Phase 2 | parity script, companion validator | Broke each of the twelve templates in turn and ran both guards | 12/12 validator fail, 5/5 parity fail | verified |
| Extended catalog and routing | Phase 3 | SKILL.md, `references/cliche-patterns.md`, `evals/trigger-cases.json`, `data/skills.json` | `python scripts/run_trigger_evals.py --gate`; `check_registry_entries.py --check --strict` | `PASS (0 un-allowlisted collisions, 37 allowlisted; 0 routing failures across 88 skill(s))`; registry agrees | verified |
| Offline detector | Phase 4 | `scripts/detect_prose_cliches.py` | Ran as a subprocess on the three fixtures and on this release's own documents | seeded: 29 ids; clean: `no findings`; leftover: `1 defect`; exits 0 / 1 / 2 as specified (below) | verified |
| Isolation skill four-layer model and mappings | Phase 5 | SKILL.md, `references/standards.md`, coverage matrix | `build_framework_coverage.py --check`; unicode strict; detector self-scan; reading against G1 to G4 | in sync; exit 0; 0 defects; four gaps answered (phase-7-evidence clause 6) | verified |
| Response class and chaining owner | Phase 6 | three SKILL.md files, standards, coverage matrix | `find` on the endpoint-hardening tree; reading; coverage check | no `scripts/` directory exists (guidance-only holds); one owner, two handoff lines; in sync | verified |

### Adversarial pass (detector, the only executable this plan ships)

Invoked as `adversarial-verifier` would: hostile and malformed inputs against the shipped entry point, exit codes read directly (not through a pipe).

| Input | Expected | Observed |
|---|---|---|
| empty stdin (`printf '' \| ... -`) | no findings, exit 0 | `<stdin>: no findings`, exit 0 |
| binary file (`templates/documentation/branded-report-template.docx`) | undecodable, exit 2 | exit 2 |
| missing path | exit 2 | exit 2 |
| 200 KB single line (40,000 words) | no findings, exit 0, no hang | `no findings`, exit 0, returned immediately |
| `--fail-on defect` on `leftover.md` | exit 1 | exit 1 |
| `--fail-on defect` on `seeded.md` | exit 1 | exit 1 |
| `--fail-on any` on `clean.md` | exit 0 | exit 0 |
| default mode on `seeded.md` | exit 0 (report only) | exit 0 |
| `python scripts/check_no_outbound.py --root <scripts dir>` | OK | OK |

No finding. The three templates' rendered surfaces are Markdown read by agents, not HTML, so the rendered-surface delegates are NOT APPLICABLE (format reason: no browser boundary in this plan).

### Code-vs-plan convergence and Goal-vs-plan sufficiency

`implementation-convergence` ran as the per-clause review in `phase-7-evidence.md`: six clauses, six converged, no unimplemented, partial, divergent, or unrequested work. Goal-vs-plan sufficiency, four questions: (1) Did the plan cover every Goal clause? Yes; each clause maps to a phase and the review found each landed. (2) Did any phase's evidence rest on the plan's own checkboxes? No; clause 3 was proven by breaking files and clause 6 by reading against the comparison's gap text. (3) What did the plan leave to a person? The four human tests, recorded as `MT-1`; the effect of the always-on clause on reply quality, recorded as `DF-1`. (4) Did the plan omit anything the maintainer's request contained? The request was the plan itself (`/implement ... in-full` with two approved choices: author tight then raise ceilings by the measured delta; commit-only through phase 6, approval before phase 7 publishes). Both choices were honored; the second is why this file ends before a push.

**Terminal disposition**: no unresolved finding. The deep pass is complete.

## Goal-vs-codebase review

Plan Goal restated and reviewed clause by clause in `phase-7-evidence.md`. Artifacts that satisfy it: twelve templates with the block; `scripts/check_base_template_parity.py` and `tests/validators/test_writing_discipline_rule.py`; `catalog/skills/developer-experience/anti-slop-editing/` (SKILL.md, `references/cliche-patterns.md`, `references/slop-wordlist.md`, `scripts/detect_prose_cliches.py`, `evals/trigger-cases.json`) with `tests/verification/test_prose_cliche_detector.py` and fixtures; `catalog/skills/security-operations/agent-execution-isolation/`, `agentic-endpoint-hardening/`, `purple-team-exercise-design/` and the two analyzers' handoff lines; regenerated `docs/framework-coverage.md` and `docs/attack-navigator-layer.json`; `data/skills.json`. Gaps: none against the Goal; two deferred items (`DF-1`, `DF-2`) name what the Goal leaves to a person, and one recorded remainder (two Partial comparison rows not promoted to named patterns) is a note.

## Human/manual testing suggestions

From the plan, to run after 7.4 and before or alongside the release; none has been run, recorded as `MT-1`:

1. Install the release into a throwaway profile with `--platforms` covering at least three non-Claude platforms, then confirm the `## Writing Discipline` block is present in each platform's installed instruction file at its documented read path.
2. On at least two platforms, ask a question that would ordinarily draw a cliche-heavy answer ("why does this matter?", "summarize the benefits") and judge whether the self-check clause changes the reply and whether the change is an improvement or merely stiffness. This is the only real test of the maintainer's chosen option, and it cannot be automated.
3. Run the phase 4 detector over a document you wrote yourself and judge the false-positive rate by hand.
4. Read the phase 5 shared-storage control and try to apply it to this repository's own agent surface. If it cannot be applied, the control is too abstract and should be revised before release.

Advisory model-prompting freshness (`python scripts/check_model_prompting_freshness.py --advisory claude-fable-5-1 claude-opus-5 claude-sonnet-5 claude-haiku-4-5-20251001`): `added (live but unprofiled): claude-fable-5-1`, `removed (recorded but no longer live): claude-fable-5`; advisory only, recorded as `WN-3` with `/tune-prompting` as the next step.

## Full-suite testing and stabilization

Local gate, all run in the `nh-v45` worktree at the phase 7 tree:

- `validate` target (35 commands via the local runner, since `make` is absent from this shell): `validate: 35 commands, 0 failed`.
- `lint`: `shellcheck --severity=warning scripts/installer.sh install.sh`: clean.
- `python scripts/validate_unicode_safety.py --strict --root . --path docs/releases/v4/v4.5`: exit 0.
- `python -m pytest tests/skills -q`: `983 passed`.
- Full suite, per directory (pytest tiers must run separately in this repository because of basename clashes), plus the six extension suites:

```text
catalog/hooks/tests: 1 failed, 1279 passed, 33 skipped (10m15s) on the first run; the failure was test_platform_parity.py::test_shared_rules_present_in_all_templates, which pinned the wording of the Claude-only hard-wrap bullet that phase 1 retired into the shared block. Classified IMPL (this plan), fixed by pointing the pin at the block phrasing present in all twelve templates; the module then passed (4 passed). Two ruff findings in that module (F841 line 106, BLE001 line 144) pre-exist on develop in lines this plan did not touch and are left alone under the scope rule.
tests/validators: 1173 passed, 2 skipped (4m41s)
tests/verification: 82 passed (40s)
tests/workflows: 97 passed, 13 skipped (2s)
tests/integrations: 740 passed, 4 skipped (33m22s)
tests/plans: 91 passed (3s)
tests/guides: 340 passed, 1 skipped (5m45s)
tests/ci: 88 passed (4s)
tests/installer: 458 passed, 36 skipped (4m13s)
tests/skills: 983 passed (1m39s)
extensions/nexus-skill-server: 43 passed
extensions/nexus-skill-scanner: 89 passed
extensions/nexus-memory: 53 passed, 1 skipped
extensions/nexus-code-search: collection error, ModuleNotFoundError nexus_code_search.config
extensions/nexus-web-fetch: 3 collection errors, ModuleNotFoundError nexus_web_fetch
extensions/nexus-context-compressor: 3 failed (AST path resolved to regex), 234 passed
The three extension results are classified ENV: git diff origin/develop..HEAD -- extensions/ is empty, and ci.yml lines 246-249 pip-install those three packages in editable mode with [dev] extras (tree-sitter for the compressor AST path), which this shell does not have. They are not touched by this plan and are not recorded as gaps.
python scripts/validate_decision_records.py: result recorded in the phase 7 history file.
```

- Test surface inspection: one new test module per new module (`test_writing_discipline_rule.py` for the block and guard lists; `test_prose_cliche_detector.py` for the script); two negative cases added to the parity script's tests; no new boundary without a test. CI surface: both new test paths sit inside trees the `tests` job already runs whole. No new env var or secret.
- Capability-usage gate (`catalog/commands/update.md` governance step 6), re-verified rather than assumed: `git diff origin/develop..HEAD -- scripts catalog/hooks templates configs | grep -E "NEXUS_[A-Z_]+|--[a-z-]+.*flag|Enterprise"` returns nothing. **Explicit no-change declaration**: v4.5.0 introduces no opt-in capability, installer flag, managed skill toggle, or host surface. The Writing Discipline block does change distributed behavior for every platform, and it is not opt-in, so the reader should know what it does and does not grant: it is instruction text only; it grants no authority, executes nothing, transmits nothing, and is overridden by a consuming project's own instruction file. The offline detector is a skill-bundled script the agent runs on request; it makes no network call (`check_no_outbound` OK) and is not a hook.
- `CHANGELOG.md` `## [Unreleased]` carries five `### Added` entries covering both tracks (the rule, the catalog extension, the detector, the isolation gaps, the response class and chaining owner). No `### Changed` or `### Removed` entry is owed: the retired Claude-only `## Communication Style` section is described inside the first entry as absorbed.
- Decision record: `docs/decisions/implemented/policy/2026-09-04-writing-discipline-binds-chat-replies.md`; validated by `python scripts/validate_decision_records.py` (result in the suite block above).

## Publication and integration

Performed 2026-09-04 (UTC 2026-09-05) after explicit maintainer approval at the gate, then a second explicit approval for the merge.

- Push: `git push -u origin feat/v4.5.0-anti-cliche-and-agent-security`, one push, seven commits (`4d60c974` phase 1 through `b99c43d6` phase 7).
- Pull request: https://github.com/bendourthe/Nexus-Hub/pull/162 into `develop`.
- Required checks against the merge result, all green: `validate` (44s), `shellcheck` (24s), `colocation` (8s), `verify` (2s), `ci-required` (aggregate, 4s); CodeQL code-scanning (`Analyze (python)`, `Analyze (javascript-typescript)`, `CodeQL`) passed with no new alert. Non-required jobs also green: `tests` (11m44s), `tests-windows` (12m32s), `guide-render` (5m59s), `bootstrap` and `install-smoke` and `installer-smoke` on all three runners; `render` skipped by its job-level path filter. `mergeStateStatus: CLEAN`.
- No red check, so the phase was not reopened and no re-push occurred.
- Merge: merge commit `765d9f32b158647cb2328972ed72d1f8e8d0c313` into `develop`, merged 2026-09-05T04:41:39Z; branch retained for the record.
- Post-merge behavior: the `develop` runs for `765d9f32` are recorded in the phase 7 history; the post-merge workflow performed only its scoped work and did not rerun the full suite (see that record).
- This evidence section itself lands after the merge, as the minimal post-merge documentation commit the lifecycle allows; it carries no code change.

Handoff: `/update release` may start. `T030` is ticked in the plan.
