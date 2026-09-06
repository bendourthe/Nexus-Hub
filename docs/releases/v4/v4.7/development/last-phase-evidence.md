# v4.7.0 Last-Phase Evidence

**Date**: 2026-09-05
**Plans**: `docs/releases/v4/v4.7/plans/v4.7.0-adoption-model-behavior-and-distribution-integrity.md` (main, Phase 7 of 7) and `v4.7.0-adoption-gpt-6-astra-prompting.md` (amendment, Phase 4 discharged here with one shared evidence file, as that plan's note on Phase 4 states)
**Revision under review**: `eef2b0de` (Phase 6 commit) on `feat/v4.7.0-model-behavior-and-distribution-integrity`, base `develop` at `76bcf614`
**Model routing**: plan asked frontier / max; session ran `claude-fable-5-1` (frontier) at high. The `/effort max` keystroke was surfaced at the boundary and the phase proceeded at high under the in-full driver; recorded under `WN-1`.

Each section quotes the proving command or scan.

## Architecture refactor

Over-engineering and cleanliness pass (`project-refactor`, `docs-layout-refactor`) across everything the plan touched:

- `find . -type d -empty` (excluding `.git`, `node_modules`, `__pycache__`): nothing.
- `python scripts/check_docs_conventions.py --root docs/releases/v4/v4.7`: `OK: docs conventions hold`. `python scripts/check_docs_retention.py`: `nothing due for archival (current v4.5, threshold 2 minors)`.
- Duplication reviewed by hand where the plan grew parallel structures: the three template validators (`test_construction_discipline_rule.py`, `test_writing_discipline_rule.py`, `test_autonomy_block_rule.py`) now differ in roster strategy (the two older ones hardcode twelve paths, the new one derives them from the directory) and `test_communication_contract_rule.py` copies the derived roster. That is two copies of one helper, which is the third-block trigger v4.5.0's `construction-debt:` note named. Delete-list: none applied this release, because consolidating four modules means renaming files the v4.1.2, v4.5.0, and v4.7.0 evidence cite by name; recorded below as `DF-3` with the concrete next step (one shared roster helper the parity script also reads). `construction-debt: four template validators share one roster; consolidate on the next template block.`
- Helper scripts for the phases lived in the operator's home directory outside the repository; nothing was left in the tree. No file moved, so no reference repair.

## Known-gaps reconciliation

Glob `docs/releases/v4/*/known-gaps.md` returns seven files (v4.0 to v4.7); no legacy-layout file exists.

- **v4.7** (this file, finalized with derived counts): open `DF-1` (v4.4.6 plan-map note deferred to the guide branch), `DF-2` (Codex CLI does not yet list `gpt-6-astra`; codex entry reads DRIFTED), `DF-3` (four template validators share one roster; consolidate on the next block), `DF-4` (report item E5, reusable `workflow_call` CI factoring, deliberately excluded), `DF-5` (report item E6, per-skill presentation metadata, deliberately excluded), `WN-1` (phases 2, 6, 7 at high against max), `MT-1` (the scheduled watch and the attestation job unobserved until publication and a tag); resolved: none this cycle.
- **v4.5** (finalized at its release; open `DF-1`, `DF-2`, `DF-3`, `WN-2`, `WN-3`, `MT-1`): `WN-3` (profile layer lists `claude-fable-5`, live roster `claude-fable-5-1`) was re-checked this cycle with `python scripts/check_model_prompting_freshness.py --advisory claude-fable-5-1 claude-opus-5 claude-sonnet-5 claude-haiku-4-5-20251001` and still reports DRIFTED; this plan added the first OpenAI profile under a multi-platform schema but did not refresh the Claude roster, so the item stays open with `/tune-prompting` as the next step. The other five items are unrelated to this scope and stay owned by v4.5.
- **v4.4** (published in the v4.4.5 tag; open `DF-1`, `WN-1`, `WN-2` on `develop`; the v4.4.6 work is still on a concurrent branch): `DF-1` (platform marks) carried forward unchanged, guide-specific and out of scope, as the plan directs. `WN-1` recorded that a phase ran one tier below its recommendation because the map resolved the frontier tier to `claude-fable-5`, a legacy model; this plan's Phase 1 re-verified the map (frontier is `claude-fable-5-1`), so the condition that produced `WN-1` no longer exists and the item is closable as superseded. `WN-2` was scoped to v4.4 guide phases now complete and is closable. Neither v4.4 edit was made from this branch: the file is modified in the concurrent v4.4.6 session's checkout and would conflict; the dispositions live in the v4.7 ledger's carry-forward table for that session or the release step to apply.
- **v4.1** (finalized; `DF-1` prompting profile layer vs live Codex roster): narrowed by this plan. The layer now holds `gpt-6-astra` for `codex` under schema 1.1.0 with a live-enumerated roster; the six live Codex CLI models remain unprofiled and `plan --platform codex` lists them. Recorded as the narrowing in the v4.7 ledger; the v4.1 file is a finalized record and is not edited.
- **v4.0**, **v4.2**, **v4.3**: no item touched by this plan; each stays owned by its ledger. v4.0 `DF-1` (the seven non-lockstep templates are not byte-locked by the release gate) is narrowed further for the Autonomous Operation block, which its validator byte-compares across all twelve, as v4.5.0 did for Writing Discipline.
- Markers introduced this version: `git diff origin/develop..HEAD | grep -E "^\+.*(TODO|FIXME|XXX|HACK|# DEVIATION:)"` returns only the history sentences reading `None marked # DEVIATION:`. No unrecorded work.

## Living docs architecture

- `docs/handbooks/`: markdown and html trees are scaffolds (`.gitkeep` only), so there is no generated documentation to regenerate and no snapshot to take; `grep -rn "Autonomous Operation\|Writing Discipline" docs/handbooks/markdown/*.md` returns nothing, so nothing is stale.
- `docs/decisions/`: two records this plan authored, `implemented/policy/2026-09-05-autonomous-operation-block-on-every-platform.md` (the always-loaded block, five alternatives) and `implemented/policy/2026-09-05-verifiable-pinnable-installs.md` (the install verification gate and pinning, five alternatives), as the plan's 7.3 requires. `python scripts/validate_decision_records.py`: `33 decision record(s) OK`.
- `docs/README.md`, `docs/DEVLOG.md`: the DEVLOG is a one-line-per-release index and gains its v4.7.0 line at `/update release`. `docs/todos.md` is modified in the concurrent session's checkout and was not refreshed from this branch (same reason as the v4.4 ledger); recorded for the release step.
- Self-gate: no `docs/testing/` or `docs/validation/` was invented.

## Git-tree hygiene

`python scripts/check_release_preconditions.py --branches --repo-settings` (report only, nothing deleted), run at the Phase 7 tree:

```text
Branch hygiene (merged into origin/develop)
  merged branch(es) are cleanup candidates: origin/backmerge/v4.4.5, origin/backmerge/v4.5.0,
    origin/docs/v4.5-v4.7-plans-and-comparisons, origin/docs/v4.5.0-publication-evidence,
    origin/docs/v4.7-v4.9-plans-migration, origin/feat/v4.4.3-guide-illustration-rebuild,
    origin/feat/v4.5.0-anti-cliche-and-agent-security, origin/fix/v4.4.5-codeql-fixtures,
    origin/release/v4.4.5, origin/release/v4.5.0
  (11 branch(es) with an open PR were excluded)
  1 branch(es) survive a CLOSED, unmerged PR: origin/backmerge/v3.20.0
  delete_branch_on_merge does NOT cover these. Review and delete by hand.
Repository settings
  OK: delete_branch_on_merge is enabled
  OK: repository description agrees with README.md
```

The plan asked whether `docs/releases/v4/v4.5/` and `docs/releases/v4/v4.6/` are committed, since the comparison target-resolution rule keys on committed plans: both are on `develop` (v4.5 shipped in the v4.5.0 release; v4.6 was committed with its plan and comparison before this branch was cut). The worktree was clean at `eef2b0de` before this phase's writes.

## CI/CD coverage

Terminal pipeline reconciliation via `cicd-architect`, existing-pipeline comparison mode. **DETECT**: GitHub Actions, twelve workflows (eleven before this plan plus `supply-chain-watch.yml`). Phase 6 is the one phase that changed pipeline files, and the per-phase CI impact records agree: phases 1 to 5 and the amendment's phase 3 changed none.

| Field | Evidence | Result |
|---|---|---|
| Profiles / event separation | `ci.yml` (pull request), `post-merge.yml` (protected-branch push), `release.yml` (tag), `supply-chain-watch.yml` (schedule and dispatch only); the new workflow is event-scoped and the policy test's `LIFECYCLE_EVENT_WORKFLOWS` names it with the reason | PASS |
| Always-resolving aggregate required check | `python scripts/check_required_check_coverage.py`: `Required-check coverage: OK -- 10 declared context(s) across 2 branch(es), every one produced unconditionally`; `tests/workflows/test_supply_chain_watch.py::test_watch_produces_no_required_check` proves the new workflow's job is outside the set | PASS |
| New tests inside existing jobs | Every new test module sits under `tests/validators`, `tests/skills`, `tests/installer`, or `tests/workflows`, trees the `tests` job runs whole (`ci.yml` line 253; `test_ci_runs_every_repo_test.py` guards it); no new job | PASS |
| Permissions | Both changed workflows keep the top-level `permissions: contents: read`; `publish-artifact` scopes `contents: write`, `id-token: write`, `attestations: write` to itself (`test_release_artifact_job_is_scoped_and_pinned`) | PASS |
| Immutable action references | Every `uses:` in both changed workflows is a 40-character SHA with a version comment (`attest-build-provenance@e8998f94...`, `upload-artifact@ea165f8d...`, the existing checkout and setup-python pins) | PASS |
| Caching | `actions/cache` in `guide-render` unchanged; pip caches not keyed by manifests remains v4.3 `DF-2` | PASS with recorded gap (v4.3) |
| Concurrency | `supply-chain-watch.yml` uses a per-ref group with `cancel-in-progress: false` (a scheduled audit is never superseded by a manual one), named in the policy test's `NO_CANCEL`; `release.yml` unchanged in this respect | PASS |
| Path scoping | No workflow-level `paths:` on a required-check producer; the new workflow has no pull-request trigger to scope | PASS |
| Artifact retention / structured reports | The watch uploads `pip-audit.json` with `retention-days: 30`; the release job attaches `SHA256SUMS` and the tarball to the Release; v4.3 `DF-3` (report profile) unchanged | PASS with recorded gap (v4.3) |
| Deployment boundaries / failure recovery | `publish-artifact` fails visibly when no Release exists after ten minutes and names the backfill command; `--clobber` makes re-runs idempotent; a red required check reopens this phase per the runbook | PASS |
| Secrets | `grep -E "secrets\." .github/workflows/release.yml .github/workflows/supply-chain-watch.yml` names only `GITHUB_TOKEN`; `python scripts/validate_workflow_security.py`: PASS inside the validate target | PASS |

**PROPOSE / APPROVE / APPLY**: no difference attributable to this plan beyond the two deliverables Phase 6 already applied with the maintainer's plan approval; nothing further proposed. **RECORD**: `MT-1` (remote observation of the two new jobs) is the one item that cannot be evidenced locally. **Cross-installer parity** (two installers ship): `python scripts/check_installer_parity.py`: `installer parity: PASS`; `verify_platform_contracts.py` and `check_platform_contract_freshness.py` pass inside the validate target. Conclusion: PASS on observable evidence; no field rests on a green run.

## Tier 3 deep pass

### Tier 3 blast-radius verdict

- **Verdict**: run
- **Diff evidence**: 87 files, 3,227 insertions, 109 deletions against `origin/develop`: twelve distributed templates, twenty-one catalog skill files, two commands, one distributed bootstrap pair (`install.sh`, `install.ps1`), the CLI (`scripts/nexus_hub_cli.py`), two repo-level validators, two workflow files, the routing data and the profile index (data files), and the docs.
- **Reason**: distributed catalog content, templates, installers, workflows, a validation boundary, and a data contract (schema 1.1.0) all changed; four of the five triggers apply.
- **Ambiguity check**: none.

### Inventory and exercise

| Feature | Source | Real boundary exercised | Observed | Status |
|---|---|---|---|---|
| Routing data and effort contract | Phase 1 | `model-map.py validate` and `fallback`; `sync_platform_defaults.py --check` | `{"valid": true, "verified_as_of": "2026-09-05", "tiers": 4, "providers": 4}`; frontier row `claude-fable-5-1 / gpt-6-astra / gemini-3.8-flash / cursor-grok-4.6`; defaults in sync, 13 platforms | verified |
| Autonomous Operation block and guard | Phase 2 | Block deleted from `base-qwen.md`, validator run, restored, run again (repeated this phase) | `4 failed, 20 passed` with the block gone (first failure names `base-qwen.md`), `24 passed` restored; parity guard exit 0 | verified |
| Long-output and base64 rules | Phase 3 | Extractor plus deterministic builder on a multi-section fixture | 39,400-byte artifact, 13 sections, ends with `</html>`, zero external references; guidance surfaces asserted by 6 tests | verified |
| Quoting examples and contract half | Phase 4 | Agent-authored compilation of two fixture sources against the example; 17 tests on the twelve templates | one marked quotation, agreement-and-difference structure; 122 template-validator tests pass | verified |
| Reliability metrics and rules | Phase 5 | Three independent runs of the trigger eval as the `pass@3` exercise; ownership test | `pass@3 = 1.0`, `pass^3 = 1.0`, three individual results recorded; 8 tests | verified |
| Multi-platform profile index and Astra profile | Amendment 3 | `verify_model_prompting_profiles.py`; `plan --platform codex`; freshness `--platform codex` | OK on schema 1.1.0; six live Codex models remain targets, `gpt-6-astra` profiled; DRIFTED with the honest reason (`DF-2`) | verified |
| Closing-summary markers | Amendment 3 | Detector on a two-line fixture | two `closing-summary-marker` advisories at `1:1` and `3:1` | verified |
| Fail-closed pinned install (both bootstraps) | Phase 6 | PowerShell leg through the parametrized suite (7 cases); bash leg by hand under Git Bash (genuine, corrupted, missing checksum, unresolvable ref, branch) | every case matched its expected exit and message; `PINNED_REF` written for a tag and cleared for a branch | verified (bash leg by hand; CI ubuntu is the suite proof) |
| Pinned-aware `nexus-hub upgrade` | Phase 6 | CLI dry-run seam | refusal exit 3 with three options; `--latest` sets `NEXUS_HUB_REF=v<latest>`; `--ref` sets the named tag; unpinned prints `main` | verified |
| Supply-chain watch and attested artifact | Phase 6 | YAML parse, policy tests, required-check coverage | parse OK; 4 workflow tests pass; required set unchanged | verified statically; remote run recorded as `MT-1` |

### Adversarial pass

Hostile inputs against the two executables this plan changed. Bootstraps: a corrupted tarball (digest mismatch) aborts before extraction on both implementations; a `SHA256SUMS` that is missing, or present without an entry for the asset, aborts naming the file; a tag whose asset does not exist aborts naming the ref and the releases page; `--ref` with no value aborts with `needs a value`; a release directory path containing a space (and a backslash on POSIX) verifies; the pre-existing CWE-22 traversal guard still refuses `../evil` (existing tests, still green). CLI: a pinned install with no target refuses and runs nothing (`dry-run` absent from the output). Detector: the v4.5.0 hostile cases (empty, binary, missing, 200 KB line) were re-run in that release and the pattern table changed by one advisory regex anchored to line start, so a false positive on `bottom line` mid-sentence is excluded by construction. No finding.

### Code-vs-plan convergence and Goal-vs-plan sufficiency

`implementation-convergence` ran as the per-clause review below: ten clauses across the two plans, ten converged, no unimplemented, partial, divergent, or unrequested work. Sufficiency, four questions: (1) Did the plans cover every Goal clause? Yes; each maps to a phase whose artifact was exercised above. (2) Did any phase rest on its own checkboxes? No; the break test, the bootstrap runs, and the fetched vendor pages are the evidence. (3) What did the plans leave to a person? The remote observation of the two new jobs (`MT-1`) and the human suggestions below. (4) Did the plans omit anything the maintainer asked for? The maintainer's request was the full main plan with the amendments folded in and the three recorded decisions; all three were honored ((a), (a), (a)) and the ceilings rose once, by the measured delta, as approved.

**Terminal disposition**: no unresolved finding. The deep pass is complete.

## Goal-vs-codebase review

**Main plan Goal, restated**: routing data names the models that actually exist; the vendor-documented behavioral rules for autonomous long-horizon work reach every substantive template with a mechanical guard; the skills that summarize sources and emit large deliverables carry their specific guidance; agent reliability is a measured metric; a user installing Nexus-Hub can verify that what they downloaded is what the project published.

| Clause | Artifacts inspected (as if unimplemented) | Verdict |
|---|---|---|
| Routing data names models that exist | `last-known-model-map.json` cells against the four vendor pages fetched 2026-09-05; `configs/platform-defaults.json` against the Claude model-config page | Converged (the Claude statement was corrected in the direction the page states, not the direction the plan expected) |
| Behavioral rules on all twelve templates with a working guard | `grep -c "^## Autonomous Operation" templates/ai-instructions/*.md`: 1 in twelve substantive files, 0 in four shims; break test above | Converged |
| Emitting skills carry their specific guidance | `document-to-interactive-html/SKILL.md` step 6 and step 3, `presentify.md` notes, `security-review` and `security-patch-advisor` subsections, the two research skills' worked examples, `agent-communication` step 8 | Converged |
| Reliability is a measured metric with one owner | `ai-output-evaluation` step 6 defines `pass@k` and `pass^k` once; `skill-eval-loop` and `quality-gate-definitions` reference without restating (test enforced) | Converged |
| A user can verify a downloaded artifact | `release.yml` `publish-artifact`; `install.sh` `verify_release_archive`; `install.ps1` `Assert-ReleaseArchiveChecksum`; README pinning section | Converged, with the boundary stated: verifiable for tags from v4.7.0 on, not for branch installs |

**Amendment plan Goal, restated**: `gpt-6-astra`'s place in the routing data decided from quoted evidence and the two same-day maps reconciled; every substantive template states user-over-skill precedence and the silent-lookup versus disclosed-deviation line; the autonomous-operation and test-scope rules carry two vendor sources; the wordlist covers the two closing-summary markers; the prompting layer holds its first OpenAI profile through the runbook with every claim traced to a fetched primary source.

| Clause | Artifacts inspected | Verdict |
|---|---|---|
| Astra decided from quoted evidence; maps reconciled | `astra-routing-decision.md` quotes both pages; snapshot note `refresh_2026_09_05_v470`; v4.8.0 plan note added; v4.4.6 plan already agrees and its citation is `DF-1` | Converged (one citation deferred to the guide branch, recorded) |
| Precedence and disclosure in all twelve | Second paragraph of the block; `## Skill Discovery` cross-reference with the original sentence pinned | Converged |
| Two vendor sources on the two rules | Main plan 2.2 and 5.3 prompts cite the Astra guide; the block's decision record and `minimal-construction` reference both | Converged |
| Two closing-summary markers | `slop-wordlist.md` family line; detector id `closing-summary-marker`; seeded count 2 | Converged |
| First OpenAI profile through the runbook | `profiles-index.json` schema 1.1.0 with the codex entry; `references/models/gpt-6-astra.md`, twelve claims, all `developers.openai.com` sources, refutation fetch confirmed twelve of twelve | Converged (Codex CLI roster lag recorded as `DF-2`) |

Gaps: none against either Goal. Deferred items name what only publication or a person can supply.

## Human/manual testing suggestions

Last phase only; none has been run:

1. Perform a real first-time install from the bootstrap on a clean machine of each supported operating system with `--ref v4.7.0` (after the v4.7.0 Release exists) and confirm the `checksum OK` line, the pinned marker, and that `nexus-hub upgrade` refuses to move until told where.
2. Install an older pinned version that carries an artifact set (v4.7.0 itself is the first), then `nexus-hub upgrade --latest`, and confirm the rollback path with `--ref` back to it.
3. Read the `## Autonomous Operation` block on a non-Claude platform (Codex, Cursor, Qwen, Kimi) beside that platform's existing sections and judge whether it reads as native or as a transplant; the wording was authored once for twelve files.
4. A Codex user with a real `gpt-6-astra` entitlement confirms the id resolves on their account, since the routing decision rests on the vendor's documentation as a proxy for reachability.
5. On any platform, give an instruction that a shipped skill would narrow and confirm the reply names and quotes the skill instead of silently complying.
6. Dispatch `supply-chain-watch.yml` once after the merge and confirm it completes, uploads its report, and appears in no required context (`MT-1`).

Advisory model-prompting freshness (runbook duty 9), roster enumerated first: Claude roster `claude-fable-5-1 claude-opus-5 claude-sonnet-5 claude-haiku-4-5-20251001` reports DRIFTED (added `claude-fable-5-1`, removed `claude-fable-5`; v4.5 `WN-3`, `/tune-prompting`); Codex roster via `codex debug models` with `--platform codex` reports DRIFTED (removed `gpt-6-astra`; `DF-2`). Both advisory, neither blocks. The model map itself is fresh (`verified_as_of` 2026-09-05, validated above).

## Full-suite testing and stabilization

Local gate at the Phase 7 tree, in the `nh-v45` worktree:

- `validate` target (35 commands via the local runner): 0 failed.
- `shellcheck --severity=warning install.sh scripts/installer.sh`: clean. `install.ps1` parses.
- `python scripts/check_required_check_coverage.py`: OK, 10 contexts. `python scripts/check_installer_parity.py`: PASS.
- Full suite per directory (pytest tiers run separately in this repository because of basename clashes), plus the six extension suites:

```text
catalog/hooks/tests: 1280 passed, 33 skipped (9m24s)
tests/validators: 1225 passed, 2 skipped (3m28s)
tests/verification: 83 passed (34s)
tests/workflows: 107 passed, 15 skipped (2s)
tests/plans: 91 passed (3s)
tests/guides: 340 passed, 1 skipped (5m48s)
tests/ci: 88 passed (4s)
tests/installer: 469 passed, 43 skipped (4m17s); the org-CLI git-source test that failed once by ordering during Phase 6 passed in this run
tests/skills: 1006 passed (1m05s)
tests/integrations: 740 passed, 4 skipped (32m42s)
extensions/nexus-skill-server: 43 passed; nexus-skill-scanner: 89 passed; nexus-memory: 53 passed, 1 skipped
extensions/nexus-code-search: collection error; nexus-web-fetch: 3 collection errors; nexus-context-compressor: 3 failed (AST path resolved to regex), 234 passed
The three extension results are ENV, identical to the v4.5.0 record: git diff origin/develop..HEAD -- extensions/ is empty, and ci.yml pip-installs those packages in editable mode with [dev] extras, which this shell does not have.
```

- Capability-usage gate: `python scripts/check_release_capability_docs.py <Unreleased section> --strict --surface "Pinned install" --surface "nexus-hub upgrade --latest"`: `OK ... all five elements present` for both surfaces. The always-loaded template blocks are not opt-in and are described in their own entries.
- `CHANGELOG.md` `## [Unreleased]` carries eight `### Added` entries, the capability-usage block, and two `### Changed` entries covering every phase and the amendment.
- Decision records: `python scripts/validate_decision_records.py`: 33 OK.

## Publication and integration

Push performed 2026-09-05 after explicit approval (eight commits, one push); pull request https://github.com/bendourthe/Nexus-Hub/pull/167 into `develop`.

**First remote validation: one red required check, phase reopened.** `tests` (ubuntu) failed on exactly one case, `tests/installer/test_bootstrap_verification.py::test_release_dir_path_with_space_and_backslash[ps]`; every other job was green (`validate`, `shellcheck`, `colocation`, `verify`, CodeQL, `tests-windows`, `guide-render`, the three-OS bootstrap and smoke matrices), and `ci-required` was red only because it aggregates `tests`. Classification: TEST (a fixture defect). The fixture created a directory literally named `back\slash`; PowerShell 7 on Linux normalizes the backslash to a path separator and looked for `back/slash`, so the bootstrap correctly reported the release as unresolvable. The bash leg with the same literal name passed on the same runner, and both legs pass on Windows, where the fixture already avoided the literal backslash. It cannot be reproduced on this Windows host for that reason, which the runbook treats as the finding itself (an environment difference). Fix: the literal-backslash case now applies only to the bash leg on POSIX, with the reason in the test; one narrowly scoped stabilization commit, re-pushed with approval. The product code did not change.

**Re-push and merge.** After explicit approval the one stabilization commit was pushed; every required check went green against the merge result (`validate`, `shellcheck`, `colocation`, `verify`, `ci-required`; CodeQL passed with no new alert; `tests` and `tests-windows`, `guide-render`, and the three-OS bootstrap and smoke matrices also green; `render` skipped by its path filter). Merged with approval as `ca8e663ef135c314cb478945e3aa7b288a9e56d2` into `develop` at 2026-09-05T22:55:48Z; branch retained for the record. Post-merge behavior verified: the `Post-merge` run for that commit (https://github.com/bendourthe/Nexus-Hub/actions/runs/33997278041) executed exactly `provenance` and `smoke`, both successful, and did not rerun the suite. `T036` and `T060` are ticked. This section itself lands as the lifecycle's minimal post-merge documentation commit.

Handoff: `/update release` may start, subject to the maintainer's decision on release ordering (v4.6.0 is not yet built). The record of the intended remote event, kept for the reader:

- Branching model: `develop` + `main` (AGENTS.md); feature branch integrates through `develop`.
- Remote: `origin` (`bendourthe/Nexus-Hub`). Branch: `feat/v4.7.0-model-behavior-and-distribution-integrity` (seven phase commits plus this final commit). Pull-request target: `develop`.
- Expected required checks (`docs/policy/required-checks.json`): `validate`, `shellcheck`, `colocation`, `verify`, `ci-required`, plus the CodeQL code-scanning merge protection. This branch changes two Python scripts and adds one workflow, so CodeQL and `validate_workflow_security.py` both run against the merge result.
- Post-approval sequence: push once; open the pull request; wait for every required check against the merge result; on red, reopen this phase and reproduce locally before any re-push; merge on green with approval; confirm the post-merge workflow did only its scoped work; record the check results and merge SHA here; hand off to `/update release`, whose round-trip step should also verify the published `SHA256SUMS` against the downloaded tarball for the first time.
