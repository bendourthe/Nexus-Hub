# Known Gaps - v3.16

**Project**: Nexus-Hub
**Status**: v3.16.0 `platform-defaults-config` is in flight on `feat/platform-defaults-config` (all 5 phases complete; reconciled and release-ready, unreleased). The v3.16 line holds seven committed plans: v3.17.0 agent-autonomy-toggle, v3.18.2 adoption-rtk-and-meterless, v3.18.1 adoption-optmem, v3.18.0 adoption-jcodemunch, v3.16.0 platform-defaults-config, v3.19.1 adoption-interface-craft-skills, and v3.15.14 adoption-spec-driven-development.
**Last updated**: 2026-08-09 (v3.16.1 Phase 8 reconciliation; every open item dispositioned; v3.16.0 Phase 5 reconciliation preserved above)

> **File-lifecycle note**: this ledger was created ahead of any v3.16 implementation, by a comparison that deliberately claimed no release slot, so it began with only the `## Comparison-Sourced Deferrals` section. Each v3.16 version-implementation phase **appends** its own `## v3.16.N - <slug>` section rather than replacing this file, keeping its own `DF-#` / `NI-#` / `BG-#` / `WN-#` / `QG-#` numbering, which is namespaced separately from the `CD-#` and `TR-#` ids used above.

---

## Transferred in from v3.15.14 (spec-driven-development cycle)

Items the v3.15.14 plan deliberately excluded from its own scope, transferred here at its Phase 4.3 reconciliation. Each traces to that cycle's comparison rather than being invented at transfer time. These use the `TR-#` (Transferred) namespace, distinct from both `CD-#` above and the per-version `DF-#` / `NI-#` / `QG-#` ids.

**Source**: [docs/v3/v3.15/plans/v3.15.14-spec-driven-development.md](../v3.15/plans/v3.15.14-spec-driven-development.md) sub-task 4.3, reconciled 2026-08-08. The full v3.15.14 open/closed set stays in [docs/v3/v3.15/known-gaps.md](../v3.15/known-gaps.md); only the deliberately out-of-scope remainder lands here.

### TR-1 - OPEN: the `A1` example in `spec-template.md` phrases a Non-Goal as an Assumption

- **Target file**: `catalog/templates/spec-template.md` (the `A1` bullet under `## Assumptions`)
- **Reason it is open**: `A1` reads "Authentication uses the existing session-cookie middleware; JWT is out of scope for this feature". The second clause is a Non-Goal under the boundary the new `## Non-Goals` authoring note defines, not an Assumption. The v3.15.14 plan instructed Phase 1.1 to leave `A1`'s text alone and instead document the boundary, which is what shipped: the Non-Goals note now names `A1` explicitly as the illustration of getting it wrong.
- **Suggested next step**: rewrite `A1` into a clean Assumption (keep the session-cookie default, drop the scope clause) and move the scope clause into the Non-Goals example, which already carries a reason. Roughly a two-line edit. Whichever cycle next touches the spec template should absorb it.
- **Why it was not done in v3.15.14**: teaching the distinction and then silently fixing the example would have removed the worked illustration the note points at. Fixing it is correct once the note has been read by real authors; doing both in one release removes the evidence.

### TR-2 - OPEN: v3.11.0 spec-kit items S5, S6, and S8 carry no status claim

- **Target**: the v3.11.0 spec-kit adoption ledger
- **Reason it is open**: the v3.15.14 comparison was article-scoped, not a repository-delta pass against `github/spec-kit`, so S5, S6, and S8 were never re-examined. The honest position is that they carry **no status claim** from this cycle rather than an implied "still open" or "now closed".
- **Suggested next step**: a future repository-delta comparison against `github/spec-kit` should re-verify all three explicitly and record a verdict per item. Do not infer their state from the v3.15.14 cycle, which did not look.

### TR-3 - CLOSED on transfer: `actions/setup-node` SHA-pinning

- **Status**: **Closed, not transferred as open.** The v3.15.14 plan recorded this as an incidental finding to transfer: "`actions/setup-node@v4` remains tag-pinned at `.github/workflows/claude-usage-monitor.yml`:31, a residual of the v3.11.0 S2 SHA-pinning item."
- **What verification found**: the reference is now SHA-pinned, and so are its three siblings. All four monitor workflows carry `actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020 # v4` (`claude-usage-monitor.yml`:38, `codex-usage-monitor.yml`:38, `cursor-usage-monitor.yml`:51, `github-usage-monitor.yml`:44). The gap was closed by a cycle between the v3.15.14 comparison being written and its Phase 4 running, and `validate_workflow_security.py` passes.
- **Why it is recorded rather than dropped silently**: transferring a resolved gap would have carried a false item into the v3.16 ledger, and dropping it without a note would have left a reader of the v3.15.14 plan expecting a transfer that never arrived. This is the second stale-fact in that plan (the first being its 269-skill catalog count, which is 270), and both are the same lesson: verify a plan's factual assertions at execution time rather than transcribing them.

---

## Comparison-Sourced Deferrals

Items that a `/compare` pass classified as genuine but too small to justify a release slot. Each names its target file and is ready for whichever cycle next touches that skill to absorb, without re-running the comparison.

**Numbering**: these use the `CD-#` (Comparison-Deferred) namespace, deliberately distinct from the per-version `DF-#` / `NI-#` / `QG-#` ids, so a version-implementation phase appending to this file cannot collide with them.

### Source: no-mistakes delta comparison (2026-07-29)

**Comparison**: [comparisons/v3.16-comparison-no-mistakes-delta.md](comparisons/v3.16-comparison-no-mistakes-delta.md). Second pass against `github.com/kunchenguid/no-mistakes`, covering releases `v1.38.0` through `v1.41.2`. The v3.9.0 N1-N6 ledger was verified closed; both v3.9.0 declines (the Go gate runtime, the default-on telemetry) were re-verified and held. The delta was almost entirely host-side runtime plumbing, leaving the three prose folds below. Maintainer decision on 2026-07-29: record as known gaps, open no release slot.

#### Deferred

##### CD-1 - nested-invocation (re-entrancy) guard for loop-engineering

- **Source**: no-mistakes delta comparison, candidate M1 (upstream `v1.41.2` #567 "prevent recursive validation runs", plus the `NO_MISTAKES_GATE` environment marker and `nested_gate_context` error observed in the upstream agent skill).
- **Target**: `catalog/skills/workflow/loop-engineering/SKILL.md`, alongside the existing `iteration_cap`, exit-signal protocol, and stall/fault-detection material.
- **Reason**: `loop-engineering` bounds a loop's iterations but says nothing about a loop running *inside itself*. Iteration caps apply per level, so they do not bound the recursion: an agent operating inside a bounded loop or verification gate that triggers the same loop again can multiply its own budget without tripping any cap. A catalog-wide search found no re-entrancy or nested-invocation language in any skill body.
- **Suggested next step**: add a re-entrancy rule stating that an agent must detect it is already inside an instance of this loop or gate (via an environment marker set by the outer invocation) and refuse the inner instance rather than proceeding, reporting the nesting instead. State the cap-does-not-bound-recursion failure mode explicitly. Cross-link `[[ai-billing-safeguards]]` (nesting is a budget-multiplication path) and `[[using-git-worktrees]]` (isolation does not imply non-re-entrancy). **Phrase it as a guard against unintended re-entrancy into the same instance, NOT as a prohibition on depth**: deliberate nesting (a workflow spawning subagents that themselves loop) is legitimate, so cross-link `[[agent-orchestration-primitives]]` so fan-out is not discouraged. Per the reverse-engineering attribution rule, do not name the external project in the skill body; add the provenance row to `docs/policy/mcp-reverse-engineering-matrix.md` if the fold lands. Non-blocking; nothing is broken today.

##### CD-2 - extend egress-redaction beyond the egress boundary

- **Source**: no-mistakes delta comparison, candidate M2 (upstream `v1.40.3` #469 "redact embedded credentials from stored upstream URLs and error surfaces").
- **Target**: `catalog/skills/security/egress-redaction/SKILL.md`, whose scope is currently stated as detecting credentials "in a prompt, file, or generated output before it leaves the host" (line 17).
- **Reason**: the skill is framed on a single boundary, egress. A credential embedded in a persisted remote URL (the `scheme://user:token@host/path` form, routinely written by clone and remote-add flows) or leaked into an error message, stack trace, or log line never crosses an egress boundary, yet still lands in plaintext on local disk. The data class and verdict already exist (Credentials are classified BLOCK at lines 57 and 89); only the boundary list is too narrow.
- **Suggested next step**: add two boundaries to the same existing policy. First, **local persistence**: redact before writing a credential into stored configuration or state, naming the embedded-credential URL form as the canonical example. Second, **error surfaces**: redact before a credential reaches an error message, stack trace, or log. State why this is a distinct gap (neither is an egress boundary, so an egress-framed skill does not cover them). **Do not add a parallel policy table** duplicating the data classes or the BLOCK verdict, which would create two sources of truth for one classification. Attribution and matrix handling as in CD-1. Non-blocking.

##### CD-3 - repair-loop prompt-size cross-link (optional, lowest priority)

- **Source**: no-mistakes delta comparison, candidate M3 (upstream `v1.40.2` #526 "handle oversized Claude repair prompts").
- **Target**: `catalog/skills/workflow/loop-engineering/SKILL.md`, cross-linking `[[context-compression]]` and `[[prompt-token-optimization]]`.
- **Reason**: a bounded repair loop can fail on accumulated prompt size before it reaches its iteration cap, as findings and fix history pile up across rounds. All three relevant skills exist; nothing connects them at this failure mode.
- **Suggested next step**: a one-line cross-link noting the failure mode and that inter-round compaction is the mitigation. Marked optional: drop this entry if the ledger is being trimmed. Non-blocking.

#### QG-3 - CLOSED: Phase 2's CI trigger change violated an encoded workflow policy

- **Source phase**: found in Phase 5, sub-task 5.4, caused in Phase 2.
- **What happened**: `tests/workflows/test_workflow_policy_repo_wide.py::test_focused_workflows_filter_by_path[ci.yml]` asserts that the catch-all gate, exempt from the `paths` requirement, declares `paths-ignore`. Phase 2's QG-1 fix replaced `paths-ignore` with `paths: ['**', '!docs/**', 'docs/policy/**']`, so the assertion failed.
- **Why the workflow was right and the test was wrong**: the test asserted the KEY (`paths-ignore`) as a proxy for the PROPERTY it cares about (the repo-wide gate must run by default and subtract exclusions, never opt in to an allowlist). Phase 2's change preserves that property -- a `paths` list beginning with `**` is behaviourally a denylist -- and the change was *forced*, because re-including `docs/policy/` is impossible in `paths-ignore`: GitHub Actions supports the `!` negation character in `paths` only, and the two filters cannot both be set for one event. So the test failed a change that WIDENED coverage.
- **Fix**: the assertion now accepts either shape (a `paths-ignore` denylist, or a `paths` list whose first entry is `**`) and rejects anything narrower, with the reasoning recorded inline. Verified against all three shapes: the current form accepts, the old form still accepts, and a narrowing allowlist is still rejected.
- **Lesson worth keeping**: this was caught only by the FULL suite. `tests/workflows` was never in the partial runs used during Phases 2 through 4, all of which were green. It is the third defect this cycle found by running everything rather than by review (after BG-2 and BG-3), and the second where a test encoded a proxy rather than the invariant it meant.

### Observations (no action)

- **v3.11.0 S2 residual**: `actions/setup-node@v4` remains tag-pinned at `.github/workflows/claude-usage-monitor.yml`:31, while the `actions/checkout` and `actions/setup-python` references are SHA-pinned per the v3.11.0 S2 adoption. Surfaced by the spec-driven-development comparison (2026-07-29) and out of scope for both comparisons, neither of which traced to it. Fold into any cycle that next touches CI workflows.
- **v3.11.0 S5, S6, S8 unverified**: not re-verified in the article-scoped spec-driven-development pass; no status claim exists for them. A future repository-delta comparison against Spec Kit should re-verify.
- **no-mistakes N7 unverified**: the optional diff-to-session intent-matching candidate from v3.9.0 was not verified in the delta pass and is recorded as neither closed nor open. Re-check if `session-query` is next revisited.
- **`tasks-to-issues` is GitHub-only**: upstream `no-mistakes` added Azure DevOps PR handling (`v1.40.1` #510), a reminder that Nexus-Hub's issue fan-out runs through the `gh` CLI only. This is a pre-existing scope decision, not a gap, and no demand signal accompanies it.
- **Methodological note for future delta passes**: verifying the v3.9.0 ledger by searching for the source's own vocabulary (`auto-fix`, `ask-user`, `no-op`) returned zero catalog hits and read as "never adopted", when in fact the doctrine had landed under Nexus-Hub-native names (escalate bucket, mechanical-fix bucket) exactly as the reverse-engineering attribution rule requires. Verify a ledger against the concept's target file, never against the external source's strings.

---

## v3.16.0 - platform-defaults-config

Gaps recorded during implementation of [plans/v3.16.0-platform-defaults-config.md](plans/v3.16.0-platform-defaults-config.md). Appended at Phase 1 (post-phase step 8.4); later phases append to this same section. Ids use the per-version `DF-#` / `NI-#` / `BG-#` / `WN-#` / `QG-#` namespace, distinct from the `CD-#` and `TR-#` ids above.

### DF-1 - OPEN: no per-job CI path filter for the drift check

- **Source phase**: Phase 1, sub-task 1.5.
- **Plan reference**: 1.5 asks to "create or update the CI workflow to cover the new script and tests with a path filter scoped to `configs/` plus the script plus its tests".
- **Reason**: `.github/workflows/ci.yml` has no per-job path filters. It uses a single workflow-level `paths-ignore: ['docs/**']`, so `configs/`, `scripts/`, and `tests/` already trigger the `validate` job. Adding a narrowing filter for one step would have *reduced* coverage (the check would stop running on changes that can cause drift) without a meaningful action-minute saving, since the check runs in about a second inside a job that already runs.
- **Precedent**: v3.15.14 Phase 4.5 reached the same conclusion independently for `catalog/templates/**` and `catalog/skills/**` (recorded in [docs/DEVLOG.md](../../DEVLOG.md) under its 2026-08-08 entry): those paths sit outside `docs/`, so the existing `paths-ignore` already fires the full job set, and a positive `paths:` filter would have narrowed coverage rather than optimized it. The reasoning transfers unchanged to `configs/`.
- **Suggested next step**: none required. If Phase 5's CI/CD optimization pass introduces per-job path filtering as a general pattern, include this step's inputs (`configs/**`, `scripts/sync_platform_defaults.py`, `tests/validators/test_sync_platform_defaults.py`) in that design rather than bolting one filter onto an otherwise unfiltered job.

### DF-2 - CLOSED: the stub's missing-source fallback is silent rather than noted

- **Source phase**: Phase 1, sub-task 1.3.
- **Plan reference**: 1.3 says to "fall back to the values currently hardcoded and log a one-line note rather than raising".
- **What shipped instead**: absence of the source degrades **silently**; only a source that exists but cannot be parsed prints a one-line note to stderr. The plan's wording treated absence as exceptional, but it is the normal case: the installers read `configs/permissions/` from a checkout and never copy `configs/` into `~/.nexus-hub`, so an unconditional note would print on every `nexus-hub init` for installed users. A second candidate path (`~/.nexus-hub/src/configs/`, which the one-line bootstrap materializes) was added so an installed tree still picks up the live value where one exists.
- **Status**: confirmed with the maintainer at implementation time and closed as a deliberate, documented deviation. Covered by `test_stub_falls_back_silently_when_the_source_is_absent` and `test_stub_notes_once_when_the_source_is_malformed`.

### NI-1 - OPEN: `configs/` is not distributed, so some installed trees use the fallback

- **Source phase**: Phase 1, sub-task 1.3.
- **Reason it is open**: `configs/platform-defaults.json` is a repo-internal source. An installed tree with no bootstrap-materialized checkout under `~/.nexus-hub/src/` finds no candidate and uses the module's hardcoded fallback. The fallback cannot silently rot (the `--check` guard compares it to the declared values), so the values are always correct at ship time; what such a tree loses is the ability to change the default by editing one file locally.
- **Why it was not done in Phase 1**: the fix is an installer copy step, and modifying the installers is ask-first under AGENTS.md. The plan explicitly scopes the installers as untouched so this release adds no `jq` dependency and stays independent of the v3.17.0 `jq` removal.
- **Suggested next step**: decide deliberately in a later cycle whether `configs/platform-defaults.json` should become a distributed artifact. If yes, it needs a copy step in BOTH `scripts/installer.sh` and `scripts/installer.ps1` and a row in the AGENTS.md distribution table. If no, record that end users configure via their own `settings.json` and the source is a maintainer surface only.

### BG-1 - OPEN (pre-existing, not introduced here): PowerShell bootstrap tarball test fails locally

- **Source phase**: Phase 1, sub-task 1.5 (observed, not caused).
- **Symptom**: `tests/installer/test_bootstrap.py::test_ps_standalone_extracts_and_hands_off` fails with `/usr/bin/tar: unexpected end of file` / `Child returned status 128`. `install.ps1` shells out to `tar`, which on a Windows host with Git Bash ahead of the system `tar` on PATH resolves to the MSYS binary and rejects the fixture archive.
- **Evidence it is pre-existing**: reproduced identically (3.6s) in a detached `git worktree` at the base `develop` commit with none of this phase's changes present. The full run was 1750 passed / 1 failed / 53 skipped, and this is the one.
- **Suggested next step**: pin the extraction binary in `install.ps1` (prefer `$env:SystemRoot\System32\tar.exe` on Windows) or skip the test when `tar` resolves to an MSYS path. CI is unaffected because its runners have a consistent `tar`. Fold into whichever cycle next touches the bootstrap.

### WN-1 - OPEN (environmental): stale git worktree admin entries cannot be pruned

- **Source phase**: Phase 1, sub-task 1.5 (observed while classifying BG-1).
- **Symptom**: `git worktree prune` reports `failed to delete '.git/worktrees/<name>': Permission denied` for `v3.15.8-platform-parity` and `v3157-phase1-tests`, left over from earlier cycles on this OneDrive-backed checkout.
- **Impact**: none on the catalog or on any distributed artifact; `git worktree list` is already clean, so only the admin directories linger.
- **Suggested next step**: remove `.git/worktrees/*` for the stale names outside a OneDrive sync window. Not a code gap; recorded so a future reader does not mistake it for repository corruption.

### QG-1 - CLOSED: a docs-only push skipped every CI guard, including the one Phase 2 added

- **Source phase**: Phase 2, post-phase step 8.3.
- **What was wrong**: `.github/workflows/ci.yml` carried `paths-ignore: ['docs/**']` on both the `push` and `pull_request` triggers, on the stated premise that "docs-only pushes never affect validators, tests, or the installer". That premise was true when written and is no longer true: `docs/policy/` is validator INPUT. `platform-read-contracts.json` feeds `verify_platform_contracts.py` and `check_platform_contract_freshness.py`, and Phase 2 added `platform-defaults-levers.md`, which feeds the lever-contract completeness tests. A push editing only one of those files skipped CI entirely, so the exact edit each guard exists to catch was the edit that never ran it.
- **Fix applied**: both triggers now use a `paths` filter (`'**'`, `'!docs/**'`, `'docs/policy/**'`) so `docs/policy/` re-triggers the full job set while the rest of `docs/` still skips it. The stale comment is corrected so it does not mislead a future reader.
- **Why `paths` rather than a negation inside `paths-ignore`**: GitHub Actions supports the `!` negation character in `paths` **only**, never in `paths-ignore`, and the two filters cannot both be set for one event. This was verified against GitHub's own workflow-syntax documentation rather than assumed; the first-drafted fix (adding `- '!docs/policy/**'` to the existing `paths-ignore`) would have been silently invalid.
- **Scope note**: the hole was pre-existing and affected the read-contract guards too, so the fix benefits more than this plan. Applied here rather than deferred to Phase 5 at the maintainer's direction.

### NI-2 - OPEN: `copilot` has a VERIFIED lever on a surface Nexus-Hub does not integrate

- **Source phase**: Phase 2, sub-task 2.1.
- **Finding**: GitHub documents `~/.copilot/settings.json` with a `model` key plus `permissions.disableBypassPermissionsMode`, `sandbox.enabled`, and `sandbox.allowBypass`. That is a genuine, first-party-documented lever, so the row is VERIFIED.
- **Why it is open**: the lever belongs to the **Copilot CLI**, while Nexus-Hub's `copilot` integration targets Copilot's instruction surface (`.github/copilot-instructions.md` plus VS Code user-profile prompt files). The integration has no `global_dir` and installs nothing into `~/.copilot`. It is recorded with Surface alignment **Mismatch** for exactly this reason.
- **Suggested next step**: Phase 3 must decide deliberately: either extend the `copilot` integration to write `~/.copilot/settings.json` (a new product surface, which is a scope decision rather than a mechanical one), or record Copilot as declared-but-not-writable with the reason. It must NOT write the file merely because a lever was found.

### NI-3 - OPEN: `gemini` and `gemini-cli` share one home, so `~/.gemini/settings.json` needs a single owner

- **Source phase**: Phase 2, sub-task 2.1.
- **Finding**: the registry keeps `gemini` and `gemini-cli` as two integrations, but both resolve to the `~/.gemini` home. Google's configuration reference documents `~/.gemini/settings.json` (`model.name`, `general.defaultApprovalMode`) for the Gemini CLI. `gemini` is classified UNVERIFIED because no official document names a behavioral-default lever for that specific surface, and transferring the CLI's lever by analogy is what the do-not-invent rule forbids.
- **Why it is open**: a default written to `~/.gemini/settings.json` on behalf of `gemini-cli` is also visible to anything else using that home. If Phase 3 ever declares a lever for `gemini` as well, two integrations would race to own one file.
- **Suggested next step**: Phase 3 must assign the `~/.gemini/settings.json` write to exactly one platform id and state which. Note that `gemini-cli` is enterprise-only post-2026-06-18 and installs only under `--enterprise`, so the owning id determines whether the default reaches a default install at all.

### NI-4 - OPEN: four platforms are deliberate non-implementations awaiting a Phase 5 disposition

- **Source phase**: Phase 2, sub-tasks 2.1 and 2.2.
- **The four**: `antigravity` (Antigravity 1.0 documents in-app settings-panel controls only, naming no config file), `gemini` (see NI-3), `nexus-ai` (the repository is private, so no publicly-citable first-party document exists; an authenticated inspection found no user-facing behavioral-default configuration surface), and `windsurf` (mode, model, and approval behavior are in-app or admin-dashboard controls, with no documented disk file).
- **Why it is open**: each is a correct, evidence-backed "no lever documented" result rather than an oversight, and each is deliberately absent from `configs/platform-defaults.json`. The plan's sub-task 5.2 requires an explicit disposition for every one so a future reader cannot mistake a deliberate omission for a forgotten platform.
- **Suggested next step**: Phase 5.2 records a disposition per platform. No action is needed before then; the classifications are already machine-checked by `tests/validators/test_platform_defaults_levers.py`.

### BG-2 - CLOSED: seeding escaped the test sandbox and wrote into the real home

- **Source phase**: Phase 3, sub-task 3.2 (found by the integration suite, fixed in-phase).
- **What went wrong**: `platform_defaults._expand()` resolved `~` with `os.path.expanduser`, which reads `USERPROFILE` / `HOME` from the process environment. The integration test suite isolates installs by patching `Path.home()`, which `expanduser` does not honour, so a test run created real config files in the developer's actual home directory (`~/.hermes/config.yaml`, `~/.aider.conf.yml`, `~/.qwen/settings.json`, `~/.kimi-code/config.toml`). All four were removed; each contained only the Nexus-Hub banner and the declared keys, so nothing user-authored was lost. `~/.codex/config.toml` is a genuine pre-existing user file and was left untouched.
- **Fix**: `_expand()` resolves `~` through `Path.home()`, matching how `base.py` resolves every other global target. Covered by `test_home_is_resolved_through_path_home_not_expanduser` and `test_seeding_writes_under_a_patched_home`.
- **Lesson worth keeping**: `expanduser` versus `Path.home()` is not a style choice in this repository. The test suite's isolation strategy decides which one is correct, and the wrong one fails silently by writing to the right-looking place on the wrong machine.

### BG-3 - CLOSED: undetected platforms were seeded

- **Source phase**: Phase 3, sub-task 3.2 (found by the integration suite, fixed in-phase).
- **What went wrong**: the seeding hook ran in `IntegrationBase.install()` unconditionally, so a detection-gated integration that had already marked itself not-detected still received a seeded config file. Installing Nexus-Hub would have created, for example, `~/.hermes/config.yaml` on a machine with no Hermes installed.
- **Fix**: gated on `result.detected is not False`. The `is not False` form is deliberate and load-bearing: `WriteResult.detected` is `Optional[bool]` where `None` means "this platform is not detection-gated at all", so a plain truthiness check would have wrongly suppressed seeding for codex, cursor, and claude. Covered by `test_undetected_platforms_are_not_seeded` plus the four integration tests that originally caught it.

### DF-3 - CLOSED: aider was reclassified from writable to not-writable

- **Source phase**: Phase 3, sub-tasks 3.1 and 3.2.
- **What changed**: aider was initially declared with `install_target.mode = "write"` targeting `~/.aider.conf.yml`. The integration suite caught the contradiction: `AiderIntegration.install_global` is a documented no-op whose own docstring states that `~/.aider.conf.yml` is a surface Nexus-Hub does not touch, and the integration performs no Aider detection at all.
- **Resolution**: reclassified to `not-writable` with the reason recorded in the defaults file, following the plan's own sub-task 3.2 instruction that a platform whose only Nexus-Hub surface is its instruction file must not have a config file synthesized for it. The lever remains VERIFIED in the lever contract with Surface alignment **Partial**; what is missing is a surface to write it through, not evidence.

### NI-2 - RESOLVED: copilot's surface mismatch was resolved by deliberate expansion

- **Source phase**: raised in Phase 2, dispositioned in Phase 3.
- **Decision**: the maintainer chose to extend the `copilot` integration to write `~/.copilot/settings.json`, adopting the Copilot CLI as a new product surface rather than recording Copilot as declared-but-not-writable. The defaults entry carries a `notes` field stating plainly that this is a surface expansion, so a future reader does not mistake it for a pre-existing capability.
- **What is seeded**: `model: "auto"` (the one vendor-documented self-selecting model value in this release), `permissions.disableBypassPermissionsMode: true`, and `sandbox.enabled: true`.

### NI-5 - OPEN: four verified platforms are declared but not writable

- **Source phase**: Phase 3, sub-task 3.2.
- **The four, each with a distinct reason**: `antigravity2` (the vendor names `toolPermission` and `artifactReviewPolicy` but does NOT enumerate their allowed values, so any seeded value would be invented), `opencode` (model keys are provider-scoped with no documented safe default, and the `permission` key's full schema is not enumerated), `openclaw` (its only documented lever is a provider-scoped model pin), and `aider` (see DF-3).
- **Why it is open**: each is a declared-for-the-record entry with an empty `settings` object, asserted by `test_not_writable_platforms_declare_no_settings_and_state_a_reason`. These are correct outcomes, not omissions.
- **Suggested next step**: re-verify at the next lever-contract pass. `antigravity2` in particular becomes seedable the moment Google enumerates the allowed values for its two documented keys.

### NI-6 - OPEN: hermes is seedable but not installed by default

- **Source phase**: Phase 3, sub-task 3.2.
- **Finding**: `hermes` is VERIFIED, has Exact surface alignment, and is declared writable, but it appears in neither installer's platform list (`invoke_registry_platform` / `Invoke-RegistryPlatform`). Its seeded default therefore reaches only an explicit `runner.py install --integrations hermes` run.
- **Why it is open**: promoting Hermes to a first-class default-installed platform is a tracked follow-on already recorded in AGENTS.md, and doing it here would have expanded this plan into platform onboarding.
- **Suggested next step**: fold into whichever cycle promotes Hermes. The seeding side needs no further work; it starts reaching users the moment the platform is installed by default.

### QG-2 - CLOSED: the TOML and YAML seeding tests would have silently skipped in CI

- **Source phase**: Phase 3, post-phase step 8.3.
- **What was wrong**: the seeding tests use `pytest.importorskip` for `tomlkit` and `yaml`, so on a CI runner without those libraries the entire TOML and YAML coverage would SKIP rather than fail. Two of the four writable formats would have reported green while proving nothing.
- **Fix**: the CI test job installs them explicitly (`pip install pytest tomlkit PyYAML`), with a comment recording why. Both installers also gained an optional-dependency check for the same two libraries, mirroring the existing `python-docx` / `python-pptx` pattern (approved as an ask-first installer edit).

### DF-4 - CLOSED: AGENTS.md described an installer/registry split that no longer exists

- **Source phase**: Phase 4, sub-task 4.2 (discovered in Phase 3, corrected here).
- **What was wrong**: the "Platform coverage caveats" section described the Original 4 (Claude, Gemini/Antigravity 1.0, Codex, Copilot) as installing via "legacy installer copy blocks" *instead of* the integration registry, with the registry subclasses "standing by" for a future migration. Verified against both installers, that is no longer accurate: `invoke_registry_platform` (bash) and `Invoke-RegistryPlatform` (PowerShell) each call `runner.py install --integrations <key>` for all fourteen default-installed keys, at global and workspace scope.
- **What is still true**: several platforms are invoked with `instruction_only`, so the registry renders only the marker-merged instruction file while the installer's own `safe_folder_copy` blocks handle the catalog tree (the DF-001 replacement path). The split is about how much each registry call does, not about whether the registry is used at all.
- **Why it mattered beyond bookkeeping**: the stale description implied that a change reaching every platform would need installer edits. Because the registry path is universal, a hook added to `IntegrationBase` reaches all of them with no installer change, which is exactly what let Phase 3 add install-time seeding without touching either installer. The correction is recorded inline in AGENTS.md as a dated note rather than a silent rewrite, so a reader who remembers the old claim sees why it changed.

### Observations (no action)

- **Local Python lint was not run**: `ruff` is not installed on this host. The repository's own `make lint` target runs ShellCheck only (which passed, on unchanged shell files), so no declared gate was bypassed. Python style was kept to the surrounding conventions by hand, and the generator emits ruff-shaped literals (magic trailing comma) so `--apply` does not fight the formatter.
- **`make` is unavailable on this host**: the `validate` steps were run individually as the equivalent, and all eight passed.
- **Only Claude is seeded, by design**: Phase 2 web-verifies the remaining fifteen registered integrations before any of them appears in the defaults file. A single-platform defaults file at the end of Phase 1 is the intended state, not an omission.
- **`gemini-cli`'s thinking budget is not a clean lever**: Google documents a thinking budget only nested per model alias, at `modelConfigs.aliases[*].modelConfig.generateContentConfig.thinkingConfig.thinkingBudget`, rather than as a top-level setting. It is recorded in the lever contract for completeness but is NOT recommended for seeding; the clean levers for that platform are `model.name` and `general.defaultApprovalMode`.
- **Two platforms document a lever but no model or effort key**: `antigravity2` documents an autonomy/approval policy (`toolPermission`, `artifactReviewPolicy`) with no default-model or reasoning-effort key, and `cursor` documents `approvalMode` and `sandbox.*` but explicitly no config-file default-model mechanism (model selection is the runtime `/model` command). Both are VERIFIED for what they document and silent on the rest; Phase 3 must not extrapolate the missing halves from sibling platforms.
- **`aider`'s alignment is Partial, not Exact**: its lever file `.aider.conf.yml` is searched in the home directory, the git repo root, then the current directory, while Nexus-Hub installs Aider at workspace scope only (project-root `CONVENTIONS.md`, no global surface). Writing a project-root `.aider.conf.yml` would place a new file type in a user's repository, which Phase 3 should weigh deliberately rather than treat as routine.
- **Doc-host churn is now a tracked signal**: this pass followed three redirects to first-party successors (Claude 301 to `code.claude.com`, OpenAI Codex 308 chain to `learn.chatgpt.com`, and `docs.windsurf.com` 307 to `docs.devin.ai`). The last is first-hand confirmation of the Cognition rebrand that AGENTS.md currently flags as third-party reporting. The lever contract's re-verification instructions now treat a redirect as an early signal of vendor reorganization rather than a cosmetic detail.

---

## v3.16.0 Phase 5 - Final reconciliation

Every open item above receives an explicit disposition here, and every platform that this release deliberately did NOT act on is named individually. The plan's sub-task 5.2 requires this so a future reader can tell a deliberate non-implementation from an oversight.

### Per-platform disposition (the 16 registered integrations)

| Platform | Class | Seeded? | Disposition |
|---|---|---|---|
| `claude` | VERIFIED | Already delivered | **Done.** The installer copies the derived `catalog/hooks/settings.json`; a second writer would race it. |
| `codex` | VERIFIED | Yes (TOML) | **Done.** effort + approval + sandbox seeded; model omitted (no vendor-documented safe default). |
| `copilot` | VERIFIED | Yes (JSON) | **Done, surface deliberately expanded.** Nexus-Hub now writes `~/.copilot/settings.json`, a Copilot CLI surface it did not previously touch. Maintainer decision, recorded in NI-2. |
| `cursor` | VERIFIED | Yes (JSON) | **Done.** `approvalMode` seeded; no model key exists to seed (the vendor documents none in the config file). |
| `gemini-cli` | VERIFIED | Yes (JSON) | **Done, sole owner of `~/.gemini/settings.json`** (NI-3). Enterprise-only, so it reaches users only under `--enterprise`. |
| `kimi` | VERIFIED | Yes (TOML) | **Done.** thinking effort + permission mode seeded; `default_model` omitted (must reference a predefined alias). |
| `qwen` | VERIFIED | Yes (JSON) | **Done.** reasoning effort + approval mode seeded. |
| `hermes` | VERIFIED | Declared, reaches nobody yet | **Deferred (NI-6).** Seedable and correct, but Hermes is absent from both installers' default platform lists. Transfers to whichever cycle promotes it; the seeding side needs no further work. |
| `aider` | VERIFIED | No - not writable | **Deliberate non-implementation (DF-3).** Its `install_global` is a documented no-op stating `~/.aider.conf.yml` is a surface Nexus-Hub does not touch, and the integration performs no Aider detection. Seeding would create config for possibly-absent software. |
| `antigravity2` | VERIFIED | No - not writable | **Deliberate non-implementation (NI-5).** The vendor names `toolPermission` and `artifactReviewPolicy` but does not enumerate their allowed values; any seeded value would be invented. Becomes seedable the moment Google publishes the values. |
| `opencode` | VERIFIED | No - not writable | **Deliberate non-implementation (NI-5).** Model keys are provider-scoped with no documented safe default, and the `permission` key's full schema is not enumerated. |
| `openclaw` | VERIFIED | No - not writable | **Deliberate non-implementation (NI-5).** Its only documented lever is a provider-scoped model pin, which this release does not seed anywhere without a vendor-documented self-selecting value. |
| `antigravity` | UNVERIFIED | No - absent from the defaults file | **Deliberate non-implementation (NI-4).** Antigravity 1.0 documents its controls as in-app settings-panel toggles and names no config file. Not a gap in research; a genuine absence of a lever. |
| `gemini` | UNVERIFIED | No - absent | **Deliberate non-implementation (NI-4).** Distinct from `gemini-cli` in the registry; no official document names a behavioral lever for that surface, and transferring the CLI's lever by analogy is what the do-not-invent rule forbids. |
| `nexus-ai` | UNVERIFIED | No - absent | **Deliberate non-implementation (NI-4).** The repository is private, so no publicly-citable document exists; an authenticated inspection found no user-facing behavioral-default surface. Re-check if that changes. |
| `windsurf` | UNVERIFIED | No - absent | **Deliberate non-implementation (NI-4).** Mode, model, and approval are in-app or admin-dashboard controls with no documented disk file. The platform is already deprecated-but-served and detection-gated. |

**Totals**: 7 platforms seeded, 1 already delivered, 4 declared-but-not-writable, 4 UNVERIFIED and absent. Every one of the 16 is accounted for, and `tests/validators/test_platform_defaults_levers.py` fails if a newly registered platform is ever added without a classification.

### Disposition of the remaining open items

| Item | Disposition |
|---|---|
| **DF-1** (no per-job CI path filter) | **Closed as deliberate.** The workflow has no per-job path filters at all; a positive filter would narrow coverage rather than save minutes. Phase 2's QG-1 fix additionally ensures `docs/policy/` re-triggers the job, so the check runs on every push that can cause drift. |
| **NI-1** (`configs/` is not distributed) | **Carried forward, open.** An installed tree with no bootstrap checkout falls back to the module literals, which `--check` keeps honest, so nothing is wrong; what such a tree lacks is local editability. Fixing it means an installer copy step (ask-first) and belongs to a cycle that is already touching the installers. |
| **NI-3** (`~/.gemini` shared home) | **Closed.** Phase 3 assigned `~/.gemini/settings.json` solely to `gemini-cli`, asserted by `test_gemini_never_declares_a_write_target`. |
| **NI-4**, **NI-5**, **NI-6** | **Dispositioned individually in the per-platform table above.** NI-4 and NI-5 are closed as deliberate non-implementations with reasons; NI-6 is carried forward to the Hermes-promotion cycle. |
| **BG-1** (PowerShell bootstrap tar failure) | **Carried forward, open, and explicitly NOT a release blocker.** Pre-existing and reproduced on a clean `develop` worktree with none of this plan's changes present. It affects a Windows host whose PATH resolves `tar` to the Git Bash MSYS binary; CI runners are unaffected. Fold into whichever cycle next touches the bootstrap. |
| **WN-1** (stale git worktree admin dirs) | **Closed as environmental.** Local `.git/worktrees/*` residue on a OneDrive-backed checkout. Touches no catalog content and no distributed artifact. |

### Phase 5 cleanliness pass

- **Four v3.15.5 documentation surfaces retargeted**: `guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md`, `extensions/claude-usage-monitor/README.md`, `catalog/skills/ai-development/prompt-engineering/SKILL.md`, and `catalog/skills/orchestration/multi-agent-coordinator/SKILL.md` now name `configs/platform-defaults.json` as the source and label `catalog/hooks/settings.json` as generated. This closes the remaining half of the drift problem: those four files previously pointed readers at what is now a derived artifact.
- **Bundle-audit blind spot fixed**: `validate_skills.py` excluded generated artifacts (`__pycache__`, `*.pyc`, and similar) from the orphan audit. Warnings went from 11 to 0 without weakening the check, verified by injecting a real orphan and confirming it is still reported. All 11 were gitignored build artifacts that existed only on a developer machine, so the audit's signal now means the same thing locally and in CI.
- **Layout**: `github-ci-cd-cost-effective-alternatives.md` moved from the v3.16 version root into a new `research/` subdirectory. The live inbound reference in `docs/v3/v3.19/plans/v3.19.0-cost-effective-ci-cd.md` was repaired; the reference inside a v3.15 session history was **deliberately left unchanged**, because a session history is a frozen record of what was true at the time and rewriting it would falsify the record.
- **`.antigravitycli/`** added to `.gitignore` (stray local runtime directory).

## v3.16.1 - evals-and-selective-installation

Appended by Phase 1 (Evaluation Contract and RAG Metrics) on 2026-08-08. Own `DF-#` / `NI-#` / `BG-#` / `WN-#` / `QG-#` namespace, separate from v3.16.0's.

### QG-1 - CLOSED: CI path filters excluded the document the new test guards

- **Target files**: `.github/workflows/ci.yml` (the `push` and `pull_request` `paths` filters), `tests/skills/test_evaluation_methodology.py`
- **What is wrong**: the workflow triggers on `['**', '!docs/**', 'docs/policy/**']`. The new test asserts against `docs/v3/v3.16/development/evaluation-artifact-contract.md`, which sits under `docs/**` and is not re-included. A push that edits only the contract - deleting an artifact definition or the local-first rule - therefore skips CI entirely, so the guard does not run on exactly the edit it exists to catch.
- **Why it was not fixed in Phase 1**: this plan's Lifecycle Contract reserves pipeline edits for Phase 8 unless a phase's explicit deliverable requires them. Phase 1's deliverables were two documents and a test.
- **Resolution (Phase 8.3)**: added `- 'docs/v*/*/development/*.md'` to the `paths` filter on BOTH the `push` and `pull_request` events (GitHub Actions configures them independently). The glob is scoped deliberately: a `*` never crosses a `/`, so it matches the contract docs directly under a `development/` directory and NOT `development/history/*.md` one level deeper. Session histories are frozen records no test reads, and re-including them would run the full matrix on every phase write-up for no signal. Verified on both events; `validate_workflow_security.py` still passes. Full reasoning in [v3.16.1-ci-cd-comparison.md](development/v3.16.1-ci-cd-comparison.md).

### WN-1 - OPEN (environmental): no Python linter or ShellCheck on the implementation host

- **What happened**: `ruff` is not installed on the implementation host, so the Phase 3 lint/format step could not run against the new test module. `make` and `shellcheck` are likewise absent, so `make lint` could not be invoked either.
- **Impact assessed as low**: `make lint` covers shell scripts only (`scripts/installer.sh`, `install.sh`), and this phase changed no shell file. The one new Python file was hand-checked for style against the neighboring `tests/skills/` modules and is exercised by 74 passing assertions. CI runs the suite on Linux and Windows, so the module is not unlinted in the pipeline sense - only on this machine.
- **Suggested next step**: none required for correctness. If the repo wants a Python lint gate it does not currently have one in the `Makefile`, which is a separate decision, not a v3.16.1 gap.

### BG-1 - OPEN (pre-existing, inherited): PowerShell bootstrap tarball test fails on this host

- **Failing test**: `tests/installer/test_bootstrap.py::test_ps_standalone_extracts_and_hands_off`, the only failure in a full-suite run of 1818 passed / 20 skipped.
- **Why it is not this phase's**: the signature is `/usr/bin/tar: Child returned status 128 ... Error is not recoverable`, the MSYS `tar` behavior already recorded as v3.16.0's BG-1 and reproduced there on a clean `develop` worktree with none of that plan's changes present. Phase 1 changed three Markdown documents, one skill body, and one Python test module; it touched no installer, no shell script, and no PowerShell file.
- **Suggested next step**: none for v3.16.1. It is the same inherited item, carried forward with v3.16.0's disposition: fold into whichever cycle next touches the bootstrap. CI runners are unaffected because their PATH does not resolve `tar` to the Git Bash binary.

### DF-1 - CLOSED: the plan's declared filename did not match the file on disk

- **What was wrong**: the plan header declared `**Slug**: adoption-evals-and-selective-installation` and `**Filename**: v3.16.1-adoption-evals-and-selective-installation.md`, and the Phase 1.1 prompt referenced that path, but the file on disk is `v3.16.1-evals-and-selective-installation.md`. Two further references pointed at the same non-existent path: `docs/todos.md` line 120 and the seeding comparison report's handoff line.
- **Resolution**: the user chose to correct the plan header rather than rename the file. The header's Slug and Filename fields and the Phase 1.1 prompt path were updated to the on-disk name, and the two stale external references were repaired in the same pass so no surface still names a path that does not exist.
- **Why this is recorded**: it is a deviation from the plan-as-written, resolved by explicit user decision, and the record is what makes the header edit traceable to an approval rather than to drift.

### NI-1 - CLOSED: four role bundles named skills that do not exist in the catalog

- **Target file**: `data/bundles.json`
- **What was wrong**: four `bundles` entries referenced skill ids with no catalog directory. Found by the Phase 2 test `test_every_selection_skill_resolves_to_a_real_catalog_dir`, which was written to verify the two AI selections and swept the rest for free.

| Bundle | Broken reference | Resolution | Basis |
|---|---|---|---|
| `core-developer` | `add-strategic-comments` | `strategic-comments` | Same capability, verb prefix dropped in a past rename |
| `frontend-engineer` | `cleanup-javascript` | `javascript-cleanup` | Same capability, `<lang>-cleanup` is the catalog's naming convention |
| `devops-engineer` | `release-management` | `shipping-and-launch` | See below |
| `tech-lead` | `release-management` | `shipping-and-launch` | See below |

- **Why `shipping-and-launch`**: `release-management` never existed as a skill at any point in git history, so this is not a rename to reverse. It was introduced into `bundles.json` by `927e5af5` (the root-layout refactor) as a forward reference that was never created. The naive repairs are all wrong: `devops-engineer` already lists `release-notes-writer` and `rollback-strategy-advisor`, and `tech-lead` already lists `version-upgrade`, so it duplicates none of them. `shipping-and-launch` ("execute safe production deployments with pre-flight checks, go/no-go decisions, and post-launch verification") is the capability the id names, and it was absent from both bundles, so the mapping adds the intended coverage without duplication.
- **Impact if left**: today the ids are inert metadata. Once Phase 6 makes selection operational, a `--bundles core-developer` install would resolve against a skill that does not exist, which the Phase 5 contract requires to fail closed before any write. It was therefore a v3.16.1 blocker for Phase 6.
- **Resolution**: fixed in Phase 2 at the user's direction. `test_every_selection_skill_resolves_to_a_real_catalog_dir` now runs with no allowlist, so any future broken reference fails immediately, and a companion `test_no_selection_lists_a_duplicate_skill` guards the adjacent defect. Phase 7.1 still owns adding the equivalent validation to the resolver itself; this closes the data defect, not the missing guard.

### NI-2 - CLOSED: 121 of 139 OpenAI agent descriptors were truncated mid-word

- **Target files**: `catalog/skills/*/*/agents/openai.yaml`
- **What is wrong**: `short_description` was produced by a hard 200-character slice of the skill description, so most descriptors end mid-word (for example `... designing tool interfaces, or implementin`). Measured this phase: 121 of 139 do not end at a sentence boundary.
- **What was fixed**: the three in `ai-development` adjacent to this phase's work (`ai-agent-development`, `prompt-engineering`, `rag-implementation`), plus the new `eval-pipeline-audit` descriptor, now end at a sentence boundary. Fix approved by the user as an explicit scope extension when the defect was believed to affect three files.
- **Why the rest were not fixed in Phase 2**: the true scope was 118 more files across every category, a catalog-wide cleanup rather than a Phase 2 deliverable. A test in `test_eval_pipeline_audit.py` asserted the new descriptor was not truncated, so the defect could not spread through that phase's work.
- **Resolution (Phase 8.2)**: mechanical pass over the remaining 118. Each `short_description` was rebuilt from its skill's own `description` frontmatter, taking whole sentences so the text ends where a thought does instead of at an arbitrary character count. Result: **140 descriptors, 0 truncated, 0 non-ASCII**, every `display_name` preserved, lengths min/median/max 123/233/348. No generator produces these files (they are hand-maintained), so there is nothing that would re-apply the 200-character slice.

### DF-2 - CLOSED: registered by hand instead of `make build-catalog`

- **What the plan said**: T012 instructs "Run `make build-catalog` so `data/SKILL_INDEX.md`, `data/skills.json`, templates, and other generator-owned outputs are rebuilt by their authoritative tooling."
- **What was done and why**: `make` is unavailable on this host (WN-1), and the repository's own precedent (DEVLOG, v3.15.3 Phase 2.1) records the standing rule that `build_skills_catalog.py` rewrites the whole tree. That was measured rather than assumed this phase: running the builder produced a 6695-line diff in `skills.json` and 174 lines in `SKILL_INDEX.md`, which would have made the phase commit unreviewable. Reverted, and the three registry files were hand-edited instead, for a 56-line diff. Decision confirmed by the user.
- **Residual risk, and how it was closed**: hand-editing missed the derived `statistics` block, which `tests/validators/test_registry_consistency.py` caught (3 failures). See DF-3.

### DF-3 - CLOSED: `skills.json` aggregate statistics were stale and were recomputed

- **What happened**: registering the skill by hand required updating `statistics.total_skills` and `statistics.categories`, which three registry-consistency tests assert. Recomputing those fields from the entries revealed that the aggregate fields had drifted well beyond this phase's contribution: `total_lines` 127877 -> 130166 and `total_tokens_estimate` 630224 -> 672031, against a new skill contributing only 151 lines and 2089 tokens.
- **Decision**: recompute all derived fields from the entries rather than incrementing by the new skill's delta. Once the block had to be touched, recomputation is the only method that yields a value matching the field's own contract (the sum of the entry sizes); incrementing would have written a differently-wrong number and called it correct.
- **Root cause, and the residual gap**: aggregates are only correct immediately after a builder run, and the standing rule is not to run the builder. Every subsequent hand-edit leaves them a little more stale. Nothing currently tests `total_lines`, `total_tokens_estimate`, or `average_lines_per_skill`, which is why the drift went unnoticed. Phase 7.1 already owns generated-catalog verification and is the right place to decide whether these fields should be tested, derived on read, or dropped.

### QG-2 - CLOSED: Phase 6's cited regression evidence predated its final edit

- **What happened**: Phase 6's `-Profile` alias fix (BG-5) was made *after* the `tests/installer` + `tests/integrations` regression run had already been started in the background. That run reported 873 passed and was cited in the Phase 6 commit message, but it had tested the tree as it stood before the rename. Two assertions in `test_selection_parity.py` still matched the old `[string]$Profile` / `$argsList += @("--profile", $Profile)` spellings and were therefore stale at commit time.
- **How it surfaced**: the Phase 7 full-suite run, which failed on exactly those two assertions.
- **Resolution**: both tests updated to assert the alias arrangement that is now correct, and one of them strengthened into a named guard (`test_powershell_profile_is_an_alias_not_a_parameter_name`) that also asserts a literal `[string]$Profile,` parameter is absent - so the shadowing bug cannot come back. Verified by re-running the module (26 passed) and by a live `-Profile minimal` install resolving 10 skills.
- **The actual lesson, which is about process rather than code**: a long-running background gate is only evidence for the tree it started against. Any edit made while it runs invalidates it. Either re-run after the last edit, or do not cite that run as the phase's evidence. Phase 6's other results (the 811-file byte-equivalence check, the three-way hash agreement, the live installs) were all produced after the final edit and remain valid.

### NI-4 - CLOSED: 166 of 271 skills were unreachable through any module or bundle

- **What the 7.1 audit found**: only **105 of 271** skills were reachable via any module or role bundle; the other **166 existed solely under `full`**. Six catalog categories were covered by nothing at all (`business-product`, `language-specialists`, `project-setup`, `research`, `security-operations`, `specialized-domains`). Selective installation could therefore never reach 61 percent of the catalog, and every one of the six command-delegate skills was in the unreachable set - which is why the first run of the new `surface_requirements` dropped `/implement`, `/describe`, `/route`, `/constitution`, `/presentify`, and `/tune-prompting` from *every* focused install.
- **Why it was a real defect rather than a curation preference**: a module system that cannot express most of the catalog makes `--modules` a decoration. The gap was invisible before this phase because nothing resolved selections, so no one could observe that two thirds of the catalog had no selector that reached it.
- **Resolution (user-directed)**: modules are now **category-complete**. The six existing curated modules were extended to cover their whole capability area (for example `testing` 8 -> 21 skills across `testing` + `tests-generation`), and 14 new modules were added for the categories no module mapped to. 20 modules, **271/271 skills reachable, 0 unreachable**. `data/bundles.json` schema bumped 1.4.0 -> 1.5.0 with the guarantee stated in its metadata. The 15 curated **role bundles were left untouched** - they are opinionated cross-category sets and expanding them was neither needed nor asked for.
- **Side effect, deliberate and recorded**: `core` grew from 31 to 45 skills, because it composes from `testing` and `code-review`, both of which became category-complete. That is the intended consequence of a module meaning "this whole capability area" rather than "a curated slice of it".
- **Guarded by**: `test_every_catalog_skill_is_reachable_through_some_module` in `tests/integrations/test_selective_install.py`, so a newly added skill that lands in no module fails the suite.

### NI-5 - CLOSED: no command or agent declared its required skills

- **What was missing**: the Phase 5 contract defines `surface_requirements`, but `data/bundles.json` declared none, so every selection installed all 20 commands and 23 agents regardless of whether the skills behind them were present. A focused install was smaller but not coherent.
- **Resolution**: six commands are declared, each naming exactly one delegate skill. The criterion is evidence-based rather than inferred: only commands whose own file states they are a thin pointer over one named skill (`/implement` "thin dispatcher over the retained `implement-phase` skill", `/presentify` "thin entry point over the `document-to-interactive-html` skill", and so on). Multi-mode commands (`/plan` "planning **skills**", `/update`, `/review`, `/spec`, `/skills`, `/setup`) are deliberately NOT declared, because requiring every mode's delegate would make them vanish unless all modes' skills were selected.
- **Agents declare nothing, and that is a finding rather than an omission**: 22 of 23 agents reference no skill at all and none shares a name with a skill, so they are self-contained.
- **Effect**: a `workflow` module selection now keeps 16 of 20 commands; `workflow` + `ai-engineering` keeps 18. Before the module expansion the same declarations dropped all six from every selection.

### DF-5 - CLOSED: both installers delegate selector resolution instead of implementing it natively

- **What the plan said**: Phases 6.1 and 6.2 instruct each legacy installer to implement the selection contract **natively**, with "a native fallback that does not make Python mandatory".
- **What was done and why**: a jq implementation was written first (`selection.jq`, ~150 lines covering composition, closure, cycle detection, eligibility, and canonical-JSON hashing). It was then discovered that **jq is not installed on the development host**, and nothing in `.github/workflows/ci.yml` installs or asserts it either. Shipping an unverifiable second implementation of a hashed contract is worse than one shared implementation: any divergence would surface as a silent hash mismatch on a user's machine. The jq file was deleted unshipped, and both installers now call `scripts/lib/installer/selection.py --emit lines`. Decision confirmed by the user.
- **What the original constraint protected is preserved**: a **no-selector full install still requires neither Python nor jq**, because both installers return from the selection path before touching Python when no selector was supplied (`selection_requested || return 0`, `if (-not (Test-SelectionRequested)) { return }`). A Python-less host already skipped every registry-backed platform before this change, so requiring Python for selectors specifically imposes nothing new on it. Both installers state this in their error text.
- **Guarded by**: `test_both_installers_require_python_only_for_selectors` in `tests/installer/test_selection_parity.py`.

### BG-2 - CLOSED: `set -e` swallowed the Bash selector error message

- **What was wrong**: `resolve_selection` captured the resolver with a bare `out=$(...)` and checked `$?` afterwards. `installer.sh` runs under `set -e`, so a non-zero resolver exit aborted the script **at the assignment**, and the handler that prints which selector was wrong never ran. Observed behavior: exit 2 with completely empty stderr.
- **Resolution**: `out=$("$py" "${args[@]}" 2>&1) || rc=$?`, which keeps the failure ours to report. Guarded by `test_bash_error_path_captures_status_under_set_e`.

### BG-3 - CLOSED: Windows CRLF made the Bash staging loop silently select nothing

- **What was wrong**: the resolver's records are read with `while IFS=$'\t' read -r kind value`. A **Windows Python invoked from Git Bash writes CRLF**, so every `value` carried a trailing `\r`, `find -name "$value"` matched nothing, and the stage was built empty. The install then completed successfully having copied **zero skills** - a green run that shipped nothing, which is the worst failure shape available.
- **Resolution**: strip the CR from both fields before the `case`. Guarded by `test_bash_strips_carriage_returns_from_resolver_output`.

### BG-4 - CLOSED: PowerShell `2>&1` on the resolver produced NativeCommandError noise

- **What was wrong**: `$output = & $py @resolverArgs 2>&1`. In Windows PowerShell 5.1, redirecting a native command's stderr wraps each line in an ErrorRecord (`NativeCommandError`) and sets `$?` false even on a clean exit, so a good selector run surfaced as a visible error.
- **Resolution**: drop the redirect. The resolver's stderr already reaches the console, so the user still sees which selector was wrong; only the exit code is needed. Guarded by `test_powershell_does_not_redirect_native_stderr`.

### BG-5 - CLOSED: the PowerShell `-Profile` parameter shadowed an automatic variable

- **What was wrong**: `[string]$Profile` shadows PowerShell's built-in `$PROFILE` automatic variable, flagged by PSScriptAnalyzer as `PSAvoidAssignmentToAutomaticVariable`.
- **Resolution**: the parameter is now `$InstallProfile` with `[Alias("Profile")]`, so the user-facing spelling stays identical to the Bash `--profile` while nothing is shadowed. Verified by a live `-Profile minimal` install resolving 10 skills.

### DF-4 - CLOSED: the contract and fixtures assumed profiles carry a flat skill list

- **What was wrong**: the Phase 5.2 contract, the fixture catalog, and the first cut of the resolver all read a profile's skills from a `skills` array. Real profiles in `data/bundles.json` have no `skills` array at all: they **compose**, from `bundles`, `modules`, and `extra_skills`, and the `full` profile is marked `"all": true` rather than listing the catalog.
- **How it surfaced**: `test_every_real_bundle_resolves`, which runs the resolver against the actual `data/bundles.json` rather than only against fixtures. Both real profiles resolved to zero skills and were reported as "empty selection" user errors -- a message that blames the user's selector for what was a modeling error in the resolver.
- **Resolution**: `_expand_entry` now unions `skills`, `extra_skills`, referenced `modules`, and referenced `bundles`, with cycle protection on the references. The fixture catalog was rewritten to mirror the composed shape (its `core` profile now exercises all three composition keys at once), the affected case expectations were recomputed, and the contract gained section 2.1a stating that selection entries are not uniform.
- **Why this is recorded rather than quietly fixed**: it is the concrete argument for keeping a real-catalog test alongside fixture tests. Every one of the 89 fixture assertions passed while the resolver could not resolve a single real profile, because the fixtures encoded the same wrong assumption as the code. Verified real numbers after the fix: minimal 10 skills, core 31, ai-engineering 6, ai-engineer 13, full 271.

### NI-3 - CLOSED: `scripts/lib/installer/` was not distributed by either installer

- **Target files**: `scripts/installer.sh` (the `integrations_src` copy block, around line 2295), `scripts/installer.ps1` (its equivalent)
- **What is wrong**: both installers recursively copy `scripts/lib/integrations/` into `~/.nexus-hub/scripts/lib/integrations/` and write an empty `lib/__init__.py`, but neither copies the sibling `scripts/lib/installer/`. Six integration modules import from it (`base.py`, `copilot.py`, `cursor.py`, `windsurf.py`, `antigravity.py` -- three of them at module top level), so the installed copy of the registry is not importable on its own.
- **Actual impact today: none.** Verified rather than assumed: the registry is always invoked as `$repo_root/scripts/lib/integrations/runner.py`, i.e. from the checkout (or the bootstrap-materialized `~/.nexus-hub/src/`), never from the installed copy. The installed tree is a reference copy that nothing executes.
- **Why it still matters**: the copy exists, which means someone intended the installed tree to be importable, and it silently is not. `scripts/lib/installer/selection.py` (added this phase) lands in the same undistributed directory, so Phase 6 inherits the question the moment `runner.py` imports the resolver.
- **Why it is not fixed here**: AGENTS.md classifies modifying the installer scripts as ask-first, and Phase 5's deliverables are a contract, fixtures, and a pure resolver with no installer edit. Phase 6.1 and 6.2 are already opening both installers.
- **Resolution (Phase 6.1 / 6.2)**: both installers now **copy `scripts/lib/` wholesale** in Phase 6, replacing the `integrations`-only copy in both installers. This makes the installed tree genuinely importable rather than importable-looking, and covers `selection.py` without a second registration. The alternative considered and rejected was documenting the copy as reference-only, which is a zero-behavior-change option but leaves a tree that looks importable and is not. Phase 6.1 and 6.2 own the edit; the empty `lib/__init__.py` write already present stays.

### Phase 4 - no new gaps; skill-native track (A1-A7) complete

Phase 4 (synthetic data, human review, and skill quality) added two Tier-3 references, a directive-density review in `skill-stocktake`, and 63 test assertions. No deviation, no skipped test, no suppressed warning, no bypassed gate, so no new entry.

The A1-A7 completion check the plan requires was run against the comparison's own declared target column, not asserted: all seven items have their implemented artifact present, and exactly one new skill was created across the whole track (`eval-pipeline-audit`) rather than the seven-skill verbatim import the Out of Scope section forbids. A8 (selective installation) remains, and is Phases 5-7.

NI-2 is unchanged: Phase 4 touched no `agents/` descriptor.

### Phase 3 - no new gaps

Phase 3 (error analysis and evaluator calibration) added two Tier-3 references under `ai-output-evaluation`, routing from the parent skill, and 40 test assertions. It introduced no deviation, no skipped test, no suppressed warning, and no bypassed gate, so it contributes no new entry. Recorded explicitly because a phase with no gaps and a phase whose gaps were never written down look identical in this file otherwise.

Two notes on existing entries:

- **QG-1 does not extend to Phase 3.** Its scope is the CI `paths` filter excluding `docs/**`, which affects only the assertions targeting `evaluation-artifact-contract.md`. Both Phase 3 references live under `catalog/skills/`, so an edit to either does trigger CI.
- **NI-2 is unchanged.** Phase 3 added no `agents/` descriptor, so the 118 remaining truncated files are neither reduced nor extended.

### WN-2 - OPEN (cosmetic, Windows-only): subprocess output decoding noise in test harnesses

- **What happens**: when a Python test harness captures the installer's stdout on Windows, the reader thread decodes it as cp1252 and raises `UnicodeDecodeError: 'charmap' codec can't decode byte 0x90` on the installer's UTF-8 check-mark glyphs. Observed in the `slow` parity tests and in the Phase 8 manual install comparison.
- **Impact: none on correctness.** The exception is raised inside `subprocess`'s reader thread, not the test; the process still exits 0, the install completes, and every assertion reads the filesystem rather than the captured text. Both affected tests pass.
- **Why it is recorded anyway**: the traceback is alarming in a log and could lead a future reader to believe an install failed when it did not. That is a real cost even though nothing is broken.
- **Suggested next step**: pass `encoding="utf-8", errors="replace"` to the `subprocess.run` calls in the affected tests, or set `PYTHONIOENCODING`. A few lines, no production-code change. Left for whichever cycle next touches those harnesses; fixing it in a terminal phase would edit tests for a cosmetic reason after the suite is already green.

### v3.16.1 final disposition (Phase 8.2)

Every item raised across the eight phases has been dispositioned. **16 closed, 3 carried forward, 0 release blockers.**

The three carried forward are environmental or cosmetic, and none is a release blocker:

| Item | Why it is carried rather than fixed |
|---|---|
| **WN-1** - no `make`, `ruff`, or `shellcheck` on the implementation host | A property of the development machine, not the codebase. Its practical impact was verified as narrow: `make lint` covers shell scripts only, and every `make validate` guard was run individually by invoking its underlying command directly. CI runs the authoritative gate on both Linux and Windows. Adding a Python lint gate is a repo-wide decision recorded in the CI/CD comparison as a retained difference, not something to introduce in a terminal phase. |
| **BG-1** - `test_ps_standalone_extracts_and_hands_off` fails with an MSYS `tar` error | Inherited from v3.16.0, where it was reproduced on a clean `develop` worktree with none of that plan's changes present. It affects a Windows host whose PATH resolves `tar` to the Git Bash binary; CI runners are unaffected. v3.16.1 touched no bootstrap file, and the failure signature is byte-identical across every run this cycle. |
| **WN-2** - `UnicodeDecodeError` noise when a test harness captures installer output on Windows | Cosmetic. The exception is raised in `subprocess`'s reader thread, not the test; both affected tests pass and every assertion reads the filesystem. Fixing it means adding `encoding="utf-8"` to a few `subprocess.run` calls, which is a test-only edit not worth making in a terminal phase after the suite is green. |

Five findings this cycle were **bugs in work this plan produced**, all caught by running the code rather than reading it, and all now carry a named regression test: BG-2 (`set -e` swallowing the selector error), BG-3 (Windows CRLF making Bash stage nothing while reporting success), BG-4 (PowerShell 5.1 `NativeCommandError`), BG-5 (`-Profile` shadowing an automatic variable), and QG-2 (a cited regression run that predated its own final edit).

Two were **pre-existing defects the work exposed**: NI-1 (four bundle references to skills that do not exist) and NI-4 (166 of 271 skills unreachable through any module). Neither was visible before this cycle, because nothing resolved selections until Phase 5.

## v3.16 Summary

| Category | Open | Resolved |
|---|---|---|
| Comparison-sourced deferrals (`CD-#`) | 3 (CD-1, CD-2, CD-3) | 0 |
| Transferred in from v3.15.14 (`TR-#`) | 2 (TR-1, TR-2) | 1 (TR-3) |
| v3.16.0 version-implementation gaps | 3 carried forward (NI-1, NI-6, BG-1) | 13 closed (DF-1, DF-2, DF-3, DF-4, NI-2, NI-3, NI-4, NI-5, QG-1, QG-2, QG-3, BG-2, BG-3, WN-1) |
| v3.16.1 version-implementation gaps (all 8 phases) | 3 carried forward (WN-1, WN-2, BG-1; all environmental or cosmetic) | 15 closed (DF-1..DF-5, NI-1..NI-5, BG-2..BG-5, QG-1, QG-2) |

The three comparison-sourced items remain non-blocking prose folds with named target files. Of the v3.16.0 items, BG-1 is pre-existing and reproduces without this plan's changes, WN-1 is environmental, DF-1 is a reasoned non-implementation, NI-1 is a deliberate scope boundary the plan requires, and NI-2 / NI-3 / NI-4 are Phase 2 findings that Phase 3 and Phase 5 are already scheduled to dispose of. Phase 5 dispositioned every open item: 13 closed, 3 carried forward. **None gates the v3.16.0 release.** NI-1 and NI-6 are scope decisions for cycles already touching the relevant surfaces, and BG-1 is pre-existing, reproduced on a clean `develop` worktree, and confined to a Windows host whose PATH resolves `tar` to the Git Bash binary. Of the 13 closed, three (BG-2, BG-3, and QG-3) were caught by the test suite rather than by review, which is this cycle's strongest argument for running the full suite before declaring a phase done.
