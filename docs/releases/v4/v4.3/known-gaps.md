# Known Gaps - v4.3

**Project**: Nexus-Hub
**Status**: finalized for the v4.3.0 release
**Finalized**: 2026-08-31, at `/update release`. The five deferred items and two warnings below remain OPEN and owned by this ledger; they are deferrals recorded with an owner and a next step, not unfinished release work. One warning was resolved during v4.4.0 Phase 7 reconciliation; the four resolved bugs and one resolved coverage gap were fixed within this release.
**Last updated**: 2026-08-31 (v4.4.0 Phase 7 reconciliation)

## v4.3.0 - agentic-verification-discipline

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 5 | 0 |
| Bugs / regressions (BG) | 0 | 4 |
| Warnings (WN) | 2 | 1 |
| Missing tests / coverage gaps (MT) | 0 | 1 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Deferred

##### DF-1 - Inline workflow validators remain outside repository-native profiles

- **Source phase**: Phase 5 CI/CD contract comparison
- **Plan reference**: `docs/releases/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T021 / T026
- **Evidence**: The 23-field comparison found large validation command lists embedded directly in workflow jobs even though `ci/run.py` exposes repository-native profiles.
- **Impact**: Local and remote gates can drift because some CI behavior is defined only inside workflow YAML instead of the shared profile contract.
- **Owner**: Next CI/CD lifecycle plan.
- **Next step**: Inventory each inline validator, migrate it incrementally into the smallest owning `ci/run.py` profile, and prove local and workflow parity before removing the YAML body.

##### DF-2 - Pip caches are not keyed by dependency manifests

- **Source phase**: Phase 5 CI/CD contract comparison
- **Plan reference**: `docs/releases/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T021 / T026
- **Evidence**: Several workflow setup and cache steps use workflow files as dependency keys because the corresponding test environments do not have dedicated dependency manifests.
- **Impact**: Dependency changes can reuse stale caches or require unrelated workflow edits to invalidate them, weakening cache determinism.
- **Owner**: Next CI/CD lifecycle plan.
- **Next step**: Add scoped dependency manifests for the affected environments, key caches to those manifests, and validate cold and warm cache behavior on every supported runner.

##### DF-3 - Report profile does not aggregate or publish structured evidence

- **Source phase**: Phase 5 CI/CD contract comparison
- **Plan reference**: `docs/releases/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T021 / T026
- **Evidence**: The repository-native `report` profile is empty, and CI does not aggregate coverage, security, or SARIF outputs into bounded-retention artifacts.
- **Impact**: A green gate lacks one durable report package for later review, trend analysis, and failure diagnosis.
- **Owner**: Next CI/CD lifecycle plan.
- **Next step**: Define the report schema, populate the `report` profile, publish unconditional success-or-failure evidence with explicit seven-day retention, and verify artifact contents on a pull request.

##### DF-4 - OpenClaw tool interception requires a typed plugin

- **Source phase**: Phase 5 platform-contract verification
- **Plan reference**: `docs/releases/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T021 / T023
- **Evidence**: Current official OpenClaw documentation exposes native skills and lifecycle hooks, but those managed hooks do not intercept or gate tool calls. Tool gating requires a typed plugin.
- **Impact**: Nexus-Hub can deliver verified OpenClaw skills and document lifecycle-hook discovery, but it cannot claim responsive-write guard parity through the native hook surface.
- **Owner**: Platform integration maintainer.
- **Next step**: Scope and review a typed OpenClaw tool-interception plugin in a future platform plan; until then, keep the guardrail surface explicitly `NOT COVERED` and do not synthesize a shell-hook port.

##### DF-5 - The ownership guard has no per-write managed root and refuses silently

- **Source phase**: Phase 5 stabilization (post-full-suite regression triage)
- **Plan reference**: `docs/releases/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T025
- **Evidence**: `_link_like_managed_ancestor` walks ancestors only between `ctx.target_root` and the destination. A global-scope write to `~/.copilot`, `~/.claude`, or the VS Code user directory is outside that root, so it received no ancestor policing at all; before the fix it was refused outright and reported as `kept` with nothing written and no error raised. `FileAction` carries only `path` and `action`, so a refusal cannot surface a reason to the caller.
- **Impact**: Out-of-root managed writes now proceed with leaf-level link protection only (symlink, junction, and hard-link destinations are still never written through, and replacement is an atomic directory-entry swap). Ancestor substitution on a global-scope path is not detected. A genuine in-tree refusal is still visible only in the manifest log, not in the returned result.
- **Owner**: Platform integration maintainer.
- **Next step**: Give `write_owned_file` an explicit managed root per call so global-scope destinations are policed against their own root (`~/.copilot`, `~/.claude`), and add a refusal reason to `FileAction` (or a companion result note) so a refusal is surfaced rather than reported as an ordinary `kept`.

#### Warnings

##### WN-2 - GitHub settings that require the web UI remain unverified

- **Source phase**: Phase 5 CI/CD contract comparison, approved bundle F
- **Plan reference**: `docs/releases/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T021 / T026
- **Evidence**: Read-only APIs proved Actions permissions, workflow-token permissions, branch protection, required contexts, cache usage, repository visibility, and branch cleanup behavior. They did not expose the repository's default artifact retention, merge-queue state, or per-runner-class billing minutes.
- **Impact**: The local pipeline and runbook are reconciled, but those three platform settings cannot be claimed as currently verified from this session.
- **Owner**: Authorized publication flow with GitHub Settings access.
- **Next step**: During publication, inspect Settings, Actions, General and Settings, Rules, Rulesets plus the billing page; record the three values in the release evidence and resolve this warning without changing a setting unless separately approved.

##### WN-3 - Optional platform surfaces remain unverified

- **Source phase**: Phase 5 platform-contract verification
- **Plan reference**: `docs/releases/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T021 / T023
- **Evidence**: The current official audit did not prove Antigravity CLI loose workflow or hook destinations, Cursor legacy command directories, Gemini IDE surfaces beyond `GEMINI.md`, or Nexus AI read paths. The coupled bundle removes or avoids those claims instead of guessing.
- **Impact**: Verified platform destinations continue to install, while these optional surfaces are deliberately absent or marked `UNVERIFIED`; users do not receive a false discovery guarantee.
- **Owner**: Platform integration maintainer.
- **Next step**: Recheck each surface against dated official documentation or a live-host artifact before adding a destination, default, or verification gate.

### Resolved

#### Warnings

##### WN-1 - GitHub repository description advertises 328 skills

- **Source phase**: Phase 5 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
- **Plan reference**: `docs/releases/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T020 / T026
- **Evidence at deferral**: `python scripts/check_release_preconditions.py --branches --repo-settings` reported that the live GitHub description said 328 skills while README and the generated catalog said 329.
- **Resolution**: `python scripts/check_release_preconditions.py --repo-settings` returned `OK: repository description agrees with README.md`; `README.md` and the generated catalog declare 329 skills.
- **Resolved in**: v4.4.0 Phase 7 reconciliation on 2026-08-31

#### Bugs / Regressions

##### BG-1 - Responsive hook misses fixed text caps expressed through CSS custom properties

- **Source phase**: Phase 5 Tier 3 deep pass and independent Goal-vs-codebase review
- **Plan reference**: `docs/releases/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T007 / T022 / T023
- **Evidence at discovery**: Both hook siblings returned exit 0 for a text selector using `max-width: var(--measure)` with `--measure: 60ch`, while the canonical responsive-layout rule forbids the resulting fixed text cap and the detector reports it.
- **Impact**: The render-time detector and write-time guard enforced different forms of the same rule, allowing a prohibited declaration through the earliest gate.
- **Resolution**: The maintainer explicitly approved one bounded post-budget stabilization after the deep pass exhausted its unchanged global three-cycle allowance. Both siblings now resolve balanced custom-property chains with fallback, cascade, specificity, `!important`, CSS-wide value, source-order, cycle, nested-variable, and bounded-complexity handling; ambiguous or unreadable relevant edits fail closed. The full owned hook module passed 105 tests, sibling parity passed 302 tests, the 24-variable PowerShell case completed in 0.56 seconds, and an independent reviewer reproduced the more-specific fixed override as exit 2 on both hosts before returning APPROVE with no P0-P3 finding.
- **Resolved in**: v4.3.0 Phase 5 bounded stabilization on 2026-08-30

##### BG-2 - POSIX responsive hook silently exits when Python is unavailable

- **Source phase**: Phase 5 independent Goal-vs-codebase review
- **Plan reference**: `docs/releases/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T007 / T015 / T023
- **Evidence at discovery**: `catalog/hooks/html-responsive-guard.sh` exited 0 before reading the payload when neither `python3` nor `python` was available, while the selector-free install contract permitted a full install without Python.
- **Impact**: A supported installation could register an inert guard and report success for prohibited HTML or CSS writes.
- **Resolution**: The Bash sibling now classifies the bounded payload path without Python, keeps irrelevant paths at exit 0, and returns actionable cannot-run exit 3 for relevant HTML or CSS writes, including escaped and metadata-shadowed paths. Paired regressions, the 105-test owned module, and the 302-case sibling-parity suite passed; the independent no-Python matrix reproduced irrelevant Markdown exit 0 and all three relevant path forms at exit 3.
- **Resolved in**: v4.3.0 Phase 5 bounded stabilization on 2026-08-30

##### BG-3 - POSIX existing-settings upgrades skip managed-hook registration without jq

- **Source phase**: Phase 5 independent Goal-vs-codebase review
- **Plan reference**: `docs/releases/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T015 / T021 / T023
- **Evidence at discovery**: `scripts/installer.sh` copied the hook files but only reconciled an existing `settings.json` inside `command -v jq`; without jq it warned and left the settings unchanged. Fresh settings and the Windows native JSON path did not expose this branch.
- **Impact**: A POSIX upgrade could contain the new hook on disk without registering it, so the consuming project did not inherit the discipline through its active settings.
- **Resolution**: The POSIX installer now uses jq first and a Python JSON fallback, fails before write when neither safe parser is available, writes and converts a same-directory candidate before atomic replacement, preserves symlinked settings targets through a bounded resolver, and reads PowerShell 5.1 BOM input through `utf-8-sig`. Direct WSL exercises proved no-jq upgrade, no-parser no-write, conversion rollback for existing and fresh settings, symlink preservation, and BOM fallback. The consolidated current-tree installer/platform gate passed 188 tests with 6 expected host skips, the declarative parity check passed, and independent review returned APPROVE with no P0-P3 finding.
- **Resolved in**: v4.3.0 Phase 5 bounded stabilization on 2026-08-30
##### BG-4 - A WSL-stub `bash` silently denied every guarded tool call

- **Source phase**: Phase 5 publication and integration (second red required-check round)
- **Plan reference**: `docs/releases/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T026
- **Evidence at discovery**: `tests-windows` failed with the Copilot bridge returning `deny` where `allow` was expected. Comparing the observed output against the branches that can produce it settled the cause: a `deny` with the default reason is emitted ONLY when the child returns non-zero, whereas an authority rejection emits `modifiedArgs` with no `permissionDecision`. The child had exited non-zero with an EMPTY stderr, and a missing interpreter would instead have raised `OSError` and surfaced a `hook-compat:` reason. That is the signature of the Windows WSL launcher stub answering to `bash`, which prints its no-distribution notice to stdout.
- **Impact**: User-facing, not merely a CI artifact. On any Windows host whose PATH `bash` is that stub, every guarded tool call was denied with no actionable diagnostic, which reads as a broken agent rather than a missing interpreter. The guard failed closed, which is correct, but for a reason no user could act on.
- **Resolution**: `_resolve_bash_command` rewrites a BARE `bash` to a verified absolute Git Bash on Windows. A caller-chosen absolute interpreter is never second-guessed, a host with no Git Bash keeps the original command so PATH resolution still applies, POSIX is untouched, and the rewrite happens at the execution site only so `_copilot_permission_authoritative` still inspects the original command and its binding is unchanged. An earlier fix in this same round attributed the failure to the `st_nlink == 1` predicate; that hypothesis was disproven and BOTH the predicate change and its regression test were reverted rather than kept for tidiness, because a security predicate must not be loosened on disproven evidence. `tests-windows` passed on the following integration round.
- **Resolved in**: v4.3.0 Phase 5 integration stabilization on 2026-08-30

##### MT-1 - The local gate could not observe host interpreter resolution

- **Source phase**: Phase 5 publication and integration (raised after two red rounds)
- **Plan reference**: `docs/releases/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md` T025 / T026
- **Evidence at discovery**: Three of the four causes across two red integration rounds were invisible to a fully green local suite because each depended on how the HOST resolves or provides something rather than on the code under test. No gate group could observe that class at all: every group runs Python directly rather than through the interpreter the hooks are actually launched with.
- **Impact**: Broader than the bridge that exposed it. Nexus-Hub registers hooks as `bash <script>` and the assistant host performs that launch, so a host with an unusable `bash` leaves every Nexus-Hub bash hook silently inert, and Nexus-Hub cannot rewrite how the host invokes them. A green local gate therefore certified a configuration in which the shipped discipline does not run.
- **Resolution**: Closed in this release at the maintainer's direction rather than deferred, in three parts. (1) `test_guard_survives_a_wsl_stub_first_on_path` places a stub `bash` first on PATH and asserts the guard still allows; its failure mode was verified by disabling the resolver, so the test is proven capable of failing. (2) `scripts/lib/integrations/_interpreters.py` probes whether each interpreter can execute a script, requiring an exact marker on stdout AND exit 0 so a shim that swallows the script and returns 0 cannot pass; `runner.py verify` reports an unusable interpreter as a NEEDS-ACTION line naming Git Bash and the PATH remedy, fail-soft so it never fails an install that delivered every file correctly. (3) A new `interpreters` group runs `scripts/check_interpreter_resolution.py --gate` in the fast, full, and platform profiles, registered repo-internal in `DEV_ONLY_SCRIPTS`. It is a GROUP inside existing profiles, not a new workflow job, so it adds no required status context and cannot reproduce the v3.17.5 pending-check trap. Six focused tests cover the probe and the advisory-versus-gate exit contract. Final local gate: 43 passed, 0 failed, 0 skipped, 0 advisory, profile exit 0.
- **Resolved in**: v4.3.0 Phase 5 integration stabilization on 2026-08-30
