# Known Gaps - v3.16

**Project**: Nexus-Hub
**Status**: v3.16.3 `github-usage-monitor-ux` is RELEASED (all six phases; 8 closed, 8 carried, 0 release blockers). v3.16.0 `platform-defaults-config` is in flight on `feat/platform-defaults-config` (all 5 phases complete; reconciled and release-ready, unreleased). The v3.16 line holds seven committed plans: v3.17.0 agent-autonomy-toggle, v3.18.2 adoption-rtk-and-meterless, v3.18.1 adoption-optmem, v3.18.0 adoption-jcodemunch, v3.16.0 platform-defaults-config, v3.19.1 adoption-interface-craft-skills, and v3.15.14 adoption-spec-driven-development.
**Last updated**: 2026-08-14 (v3.16.8 `adoption-watermark-hygiene` reconciled at its terminal Phase 3: 4 closed, 2 carried, 0 release blockers. The carried pair are WN-1, an accepted CJK ideographic-variation limitation with a named revisit trigger, and BG-1, pre-existing and environmental.) Previously 2026-08-13 (v3.16.7 section opened: Phase 1 shipped in `0dbc170f`, plan reverse-engineered and held OPEN at Phase 3 for incoming live-session lessons; BG-1 the frontmatter-breaking BOM, DF-1 the missing plan artifact and DF-2 the cross-session changelog contamination all closed.)

> **File-lifecycle note**: this ledger was created ahead of any v3.16 implementation, by a comparison that deliberately claimed no release slot, so it began with only the `## Comparison-Sourced Deferrals` section. Each v3.16 version-implementation phase **appends** its own `## v3.16.N - <slug>` section rather than replacing this file, keeping its own `DF-#` / `NI-#` / `BG-#` / `WN-#` / `QG-#` numbering, which is namespaced separately from the `CD-#` and `TR-#` ids used above.

---

## Transferred in from v3.15.14 (spec-driven-development cycle)

Items the v3.15.14 plan deliberately excluded from its own scope, transferred here at its Phase 4.3 reconciliation. Each traces to that cycle's comparison rather than being invented at transfer time. These use the `TR-#` (Transferred) namespace, distinct from both `CD-#` above and the per-version `DF-#` / `NI-#` / `QG-#` ids.

**Source**: [docs/releases/v3/v3.15/plans/v3.15.14-spec-driven-development.md](../v3.15/plans/v3.15.14-spec-driven-development.md) sub-task 4.3, reconciled 2026-08-08. The full v3.15.14 open/closed set stays in [docs/releases/v3/v3.15/known-gaps.md](../v3.15/known-gaps.md); only the deliberately out-of-scope remainder lands here.

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
- **Precedent**: v3.15.14 Phase 4.5 reached the same conclusion independently for `catalog/templates/**` and `catalog/skills/**` (recorded in [docs/DEVLOG.md](../../../DEVLOG.md) under its 2026-08-08 entry): those paths sit outside `docs/`, so the existing `paths-ignore` already fires the full job set, and a positive `paths:` filter would have narrowed coverage rather than optimized it. The reasoning transfers unchanged to `configs/`.
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

### WN-2 - CLOSED (was mischaracterized as cosmetic): subprocess decoding killed a test's error reporting

- **What was originally recorded**: a `UnicodeDecodeError` traceback when a Python test harness captured installer output on Windows, assessed as cosmetic because the affected tests still passed locally.
- **That assessment was wrong, and remote CI proved it.** On the Windows CI leg the same decoding failure left `proc.stdout` as `None`, so the test failed while BUILDING its own assertion message: `TypeError: 'NoneType' object is not subscriptable`. The real outcome was replaced by a confusing type error that pointed nowhere near the cause. A defect that destroys a failure message is not cosmetic - it is the specific thing that makes the next failure expensive to diagnose.
- **Resolution**: every `subprocess.run` in `tests/installer/test_selection_parity.py` now passes `encoding="utf-8", errors="replace"` through a shared `_CAPTURE` constant, with the reason documented at its definition.
- **The lesson**: "the test still passes" is not sufficient evidence that a warning is harmless. It passed on the host where the decode happened to succeed. Local green plus an unexplained traceback is a reason to look closer, not to file it as noise.

### BG-6 - CLOSED: the PowerShell end-to-end test ran on Linux CI

- **What was wrong**: `test_powershell_filtered_install_matches_bash` gated on `shutil.which("powershell") or shutil.which("pwsh")`. GitHub's `ubuntu-latest` image **ships `pwsh`**, so the guard did not skip - it found pwsh, ran the Windows installer against a POSIX host, and failed with a bare `rc=1`.
- **Why local testing missed it**: the development host is Windows, where the test runs legitimately and passes. The failure mode only exists on a Linux runner with pwsh installed, which is exactly the environment no local run reproduces.
- **Resolution**: the helper now returns `None` unless `sys.platform == "win32"`. `installer.ps1` is a Windows installer (Windows PowerShell 5.1 idioms, `%TEMP%`, Windows path handling); running it on Linux is not a supported scenario, so skipping is correct and reporting a failure was not.

### PX-1 - CLOSED (pre-existing, unrelated to v3.16.1): `end-of-file-fixer` failing on a cursor-usage-monitor source file

- **What was wrong**: `extensions/cursor-usage-monitor/src/statusBarManager.ts` ended with two newlines, so pre-commit's `end-of-file-fixer` rewrote it and failed the `validate` job. This had been failing the CI `validate` job on **every `develop` push for at least three releases**, including the v3.16.0 merge and the v3.15.14 merge.
- **Why it is fixed here despite being out of scope**: it is a one-byte normalization that the hook itself performs, it touches no logic, and it was the ONLY thing failing `validate`. A release cannot be called green while a long-standing red check is waved through, and leaving it would have meant either shipping red or claiming a pass the pipeline did not give.
- **Resolution**: trailing newline normalized to exactly one. Verified on the staged blob: single `
`, no CRLF, one-line diff.


### BG-7 - CLOSED: `Get-FileHash` broke the PowerShell installer on Windows CI

- **What was wrong**: `Safe-Copy` called `Get-FileHash`, which raised `CommandNotFoundException` inside `installer.ps1` under Windows PowerShell 5.1 on GitHub's `windows-latest` image, while the rest of `Microsoft.PowerShell.Utility` worked in the same session and pwsh 7 on the same image was fine.
- **Why it hid for four releases**: `Safe-Copy` hashes ONLY when the destination already exists, so on a fresh install every call short-circuits and the line is never reached. `install-smoke` installs into a clean HOME, so it passed release after release over unreachable code. Reaching it needs a job that installs twice into one HOME, which the v3.16.1 parity suite is the first to do.
- **Two hypotheses were tested and both DISPROVEN**: a stripped `PSModulePath`, and a pwsh-7 `PSModulePath` shadowing 5.1's Utility module. Windows PowerShell 5.1 resolves the cmdlet correctly under both.
- **Resolution**: the dependency was removed rather than tuned around. Hashing goes through .NET `SHA256`, which needs no module resolution and behaves identically on 5.1 and 7. This is the **second** sighting of the class in this repo (v3.15.6 hit it in `catalog/hooks/provenance-ledger.ps1` and reached for the same .NET stream), and `tests/installer/test_powershell_cmdlet_portability.py` now pins both.
- **Why the guard is static rather than behavioral**: re-running the install would not catch a reintroduction on any developer machine where the cmdlet works, which is all of them. The defect is only observable on an image we do not control, so a source assertion is the only check that fails in the right place.

### BG-8 - CLOSED: the PowerShell selection stage leaked on every focused install

- **What was wrong**: `Remove-SelectionStage` was written in Phase 6.2 and **never called**. The Bash side cleans its staging tree with `trap cleanup_selection_stage EXIT`; the PowerShell equivalent had no caller, so every focused install left a full copy of the selected skills in `%TEMP%`. Eight leaked stages were found on the development host.
- **Resolution**: called on the normal completion path. Verified by stage count across a successful focused install (8 -> 8, rc=0, 13 skills).

### NI-6 - OPEN (documented, bounded): one PowerShell early-exit path still leaks a stage

- **What remains**: an exit taken after `Resolve-Selection` but before completion (observed via the "Workspace path not found" validation) leaves its staging directory behind.
- **Why it is not fixed**: a `Register-EngineEvent PowerShell.Exiting` handler was written and then deliberately removed. Engine-event actions run in a separate scope where the `$script:`-scoped stage path is not reliably visible, so the cleanup could not be verified to run. An unverifiable cleanup is worse than a documented gap: it reads as covered while doing nothing.
- **Bound**: the residual is one directory under `%TEMP%` on an aborted install, not on the normal path. An earlier draft of the in-file comment claimed no such path existed; that claim was wrong and is corrected to describe the measured path.

### v3.16.1 final disposition (Phase 8.2)

Every item raised across the eight phases and the release itself has been dispositioned. **21 closed, 3 carried forward, 0 release blockers.** Five of the closures (WN-2, BG-6, PX-1, BG-7, BG-8) came from remote CI or from post-merge verification after the local suite was green -- which is this cycle's clearest evidence that a green local run is a weaker signal than it feels like.

The two carried forward are environmental, and neither is a release blocker:

| Item | Why it is carried rather than fixed |
|---|---|
| **WN-1** - no `make`, `ruff`, or `shellcheck` on the implementation host | A property of the development machine, not the codebase. Its practical impact was verified as narrow: `make lint` covers shell scripts only, and every `make validate` guard was run individually by invoking its underlying command directly. CI runs the authoritative gate on both Linux and Windows. Adding a Python lint gate is a repo-wide decision recorded in the CI/CD comparison as a retained difference, not something to introduce in a terminal phase. |
| **BG-1** - `test_ps_standalone_extracts_and_hands_off` fails with an MSYS `tar` error | Inherited from v3.16.0, where it was reproduced on a clean `develop` worktree with none of that plan's changes present. It affects a Windows host whose PATH resolves `tar` to the Git Bash binary; CI runners are unaffected. v3.16.1 touched no bootstrap file, and the failure signature is byte-identical across every run this cycle. |

Five findings this cycle were **bugs in work this plan produced**, all caught by running the code rather than reading it, and all now carry a named regression test: BG-2 (`set -e` swallowing the selector error), BG-3 (Windows CRLF making Bash stage nothing while reporting success), BG-4 (PowerShell 5.1 `NativeCommandError`), BG-5 (`-Profile` shadowing an automatic variable), and QG-2 (a cited regression run that predated its own final edit).

Two were **pre-existing defects the work exposed**: NI-1 (four bundle references to skills that do not exist) and NI-4 (166 of 271 skills unreachable through any module). Neither was visible before this cycle, because nothing resolved selections until Phase 5.

## v3.16.2 - loop-longevity-and-doctor-preflight

Appended by Phase 1 (Loop schema: gates, evidence freshness, instance state) on 2026-08-09. Own `DF-#` / `NI-#` / `BG-#` / `WN-#` / `QG-#` / `MT-#` namespace, separate from v3.16.0's and v3.16.1's.

### MT-1 - OPEN: the three new schema concepts carry no mechanical assertion

- **Target files**: `catalog/skills/workflow/loop-engineering/references/loop-schema.md`, `catalog/skills/workflow/loop-engineering/references/loop-library.md`
- **What is missing**: `gates`, `evidence_freshness`, and the Instance State section are prose in a Tier-3 reference file. `validate_skills.py` audits bundle references and orphans, not reference-file content, and `run_trigger_evals.py` scores routing rather than schema shape. Nothing fails today if a later edit deletes a Fields-table row, renames a gate type, or lets the worked example drift out of step with the library entry. The drift risk is now concrete rather than hypothetical: the identical `gates` block for `ship-pr-until-green` exists in **two** files, because the schema's worked example and the library entry are the same loop.
- **Why it was not done in Phase 1**: the phase's Stability Gate is documentation-scoped, and the plan routes all test construction to Phase 5, which is where this cycle's pytest surface is created. Building a one-off test module here would have put a test directory in front of the phase that must name it in `ci.yml` (v3.15.8 QG-2).
- **Suggested next step**: when Phase 5 adds its test module, add two cheap assertions alongside it - that the four gate types in the Fields table match those in the Human-Judgment Gates table, and that the `ship-pr-until-green` `gates` block is byte-identical in `loop-schema.md` and `loop-library.md`.

### WN-1 - OPEN (environmental, inherited): no `make` on the implementation host

- **What happened**: `make` is absent on this machine, so neither `make validate` nor `make test` could be invoked as targets. Same condition recorded as v3.16.1 WN-1 and carried forward there.
- **How it was handled rather than skipped**: every command inside both targets was read out of the `Makefile` and run individually. Seven `validate` guards (`validate_skills.py --bundles-only`, `validate_skills.py --quality`, `run_trigger_evals.py --gate`, `validate_no_personal_paths.py`, `validate_unicode_safety.py`, `check_version_sync.py`, `check_base_template_parity.py`) all pass, and all five extension suites plus `tests/` and `catalog/hooks/tests` were run to completion.
- **Suggested next step**: none for correctness. CI runs the authoritative gate on Linux and Windows.

### BG-1 - OPEN (pre-existing, inherited): PowerShell bootstrap tarball test fails on this host

- **What happened**: `tests/installer/test_bootstrap.py::test_ps_standalone_extracts_and_hands_off` fails with an MSYS `tar` error. It is the single failure in a 2178-test `tests/` run (2157 passed, 20 skipped).
- **Why it is not this phase's**: Phase 1 changed three Markdown files inside one skill bundle and touched no bootstrap, installer, or shell file. The failure signature is byte-identical to the one recorded under v3.16.0 BG-1 and v3.16.1 BG-1, where it was reproduced on a clean `develop` worktree carrying none of that cycle's changes.
- **Bound**: affects a Windows host whose PATH resolves `tar` to the Git Bash binary. CI runners are unaffected.

### NI-1 - OPEN (pre-existing, found in Phase 2): `catalog/commands/update.md` references a `nexus-hub doctor` that does not exist

- **Target file**: `catalog/commands/update.md`, the `config` delegation line and the `config scope` section
- **What is wrong**: both name `nexus-hub doctor` as an existing delegate ("`config-consistency-checker` / `nexus-hub doctor`"). No `doctor` subcommand exists in either installer today. The command file promises a surface a user cannot invoke.
- **How it was found**: while adding the Phase 2 capability gate to the same file. It is pre-existing and unrelated to this plan's edits, but it is the identical defect class the gate itself guards against - documentation asserting a capability the user cannot actually operate.
- **Suggested next step**: Phase 5.1 and 5.2 build exactly this subcommand, which closes the gap by making the reference true. Re-verify at Phase 5 rather than editing the prose now; deleting a reference that Phase 5 is about to make correct would be churn.

### DF-1 - DEFERRED by design: the capability usage gate has no mechanical checker

- **Target**: governance step 6 in `catalog/commands/update.md`
- **What is deferred**: the gate is currently a human read of the release notes. `scripts/check_release_capability_docs.py`, which asserts the five elements per named surface, is Phase 5.3's deliverable.
- **Why it was not built in Phase 2**: the plan sequences it that way, and Phase 5 declares Phase 2 as its prerequisite. Phase 2 deliberately does NOT name the script in `update.md` yet, because a forward reference to an unbuilt script is the same defect as NI-1 directly above it. The text says a checker is planned and describes its advisory posture without naming a path that does not resolve.
- **Suggested next step**: Phase 5.3 builds the script and replaces the "planned" sentence with the real invocation.

### Phase 2 dry-run evidence (recorded, not acted on)

The plan asked whether the gate would have caught anything real. Applied retroactively to the two most recent releases:

| Release | Verdict | Detail |
|---|---|---|
| **v3.15.10** (notification work) | **Would have FAILED** | It introduced `NEXUS_NOTIFY_DRY_RUN`, `NEXUS_NOTIFY_DISABLED_FILE`, and the `~/.nexus-hub/notifications-disabled` switch file. Element 1 is partial (the env vars are named but their accepted values are not), element 3 is effectively present (the switch file IS the disable path), and elements 2, 4, and 5 are absent outright - no readback command, no statement of what enabling the notification hooks does not grant, and no canonical documentation link. |
| **v3.15.11** (Codex notification delivery) | **Out of scope** | Its changes are internal hook-delivery fixes (`build_hook_entries` module resolution, `CODEX_EVENT_ALIASES`) to hooks that are on by default. It introduces and materially changes no opt-in surface, so it satisfies the gate with the single no-change declaration. |

One fail and one out-of-scope is the outcome that makes the gate worth having: it discriminates rather than firing on every release. Per the plan, neither release's notes were retroactively edited.

### BG-2 - OPEN (pre-existing, found in Phase 3): `secret-scan.sh` fails OPEN on a host without `jq`

- **Target file**: `catalog/hooks/secret-scan.sh`
- **What is wrong**: the hook extracts `file_path` and `content` with `jq`, and when `jq` is absent it takes an explicit `exit 0` path commented "Without jq we cannot reliably extract content; allow the write". It therefore scans nothing and blocks nothing. This was found by verifying the hook rather than reading its matcher: on this host (no `jq`), a payload carrying a well-formed AWS access key ID returned exit 0 with no output.
- **Why it matters**: this is a security guard that fails OPEN. A registered, executable, permanently silent hook is exactly shape S-1 in `docs/incidents/shapes.md`, which the two notes backfilled in this same phase are about. A user on a POSIX host without `jq` believes they have secret scanning and does not.
- **Bounds, and why it is not a release blocker**: `secret-scan.ps1` is unaffected and was verified working in both directions on this host (exit 2 on a seeded key, exit 0 on a clean note), so Windows users are covered. `AGENTS.md` already documents the asymmetry as acceptable ("a sibling that works where the bash version silently no-ops, for example on a host with no `jq`, is an acceptable and documented improvement"), so the behavior is known rather than newly discovered - what is new is the evidence that the bash side is genuinely inert, not merely degraded.
- **Suggested next step**: replace the `jq` dependency with a stdlib fallback (a short Python or `sed` extraction) so the bash hook degrades to scanning rather than to allowing, or fail CLOSED with an explicit "cannot scan, install jq" message. Failing open is the wrong default for a guard whose entire job is to block. Out of scope for this plan, which touches no hook logic.

### QG-1 - RESOLVED in Phase 3: `docs/incidents/**` was outside the CI path filters

- **What it was**: `ci.yml` excludes `docs/**` except for `docs/policy/**` and the per-version development contract docs. A new `docs/incidents/` tree would have been invisible to CI, so a note whose Durable fix was a paragraph rather than a link could be pushed without the guard ever running - the identical defect already fixed twice before (v3.16.0 for `docs/policy/**`, v3.16.1 QG-1 for the development contract docs).
- **Resolution**: added `- 'docs/incidents/**'` to the `paths` filter on BOTH the `push` and `pull_request` events, with a comment stating the rule the re-inclusion follows: a docs path earns a CI trigger only when a guard actually reads it. The guard that earns it (`scripts/check_incident_notes.py`) was built in the same phase and wired into the `validate` job and `make validate`.
- **Note on the plan's instruction**: sub-task 3.4 asked for the path filter unconditionally. Adding it without a guard would have run the full matrix on every incident note for zero signal, contradicting the reasoning already written into `ci.yml` for session histories. Building the guard first is what makes the instruction correct rather than costly.

### NI-2 - OPEN (pre-existing, surfaced in Phase 4): two edited skills are over the 500-line body target

- **Target files**: `catalog/skills/infrastructure/observability-setup/SKILL.md` (763 lines), `catalog/skills/orchestration/multi-agent-coordinator/SKILL.md` (703 lines)
- **What is wrong, and what is not**: both were already over the 500-line target before this phase (742 and 685), so they are grandfathered under the AGENTS.md rule that the norm is forward-looking. Both remain under the 800-line hard cap. Phase 4.5's instruction to "confirm both edited skills stayed within the 500-line body target" therefore describes a check that could not pass, and the honest report is that the target was already exceeded rather than that the check passed.
- **Why the additions were made in the body anyway**: each of the two doctrine items is a short rule that belongs where the reader already is. Pushing a 25-line rule into a `references/` file to protect a line count would trade discoverability for a number, which is the opposite of what the norm exists to achieve.
- **Watch item**: `observability-setup` at 763 lines is within 37 lines of the hard cap. The next cycle that adds to it should split it into `references/` first rather than discovering the cap mid-edit.
- **Suggested next step**: Phase 6.1's refactor pass should decide whether to split `observability-setup`, which is the natural place for that call.

### BG-3 - RESOLVED in Phase 5: the Bash doctor read every `file_contains` surface as MISSING

- **What it was**: the Bash `doctor` flattens the contract to tab-separated records. On a Windows host the Python fallback's `print()` emits CRLF, so the LAST field arrived carrying a trailing `\r`. Only `file_contains` surfaces use that final `needle` column, so only they broke: Bash reported 5 complete / 5 incomplete where PowerShell reported 9 / 1, on the same machine, with matching exit codes hiding the disagreement.
- **How it was found**: by running both implementations against the real machine and diffing the verdict lines. Neither implementation is wrong in isolation, and no single-platform test could have seen it. This is shape S-1 failure mode 2 (runs but disagrees) reproduced within hours of the notes describing it being written.
- **Resolution**: strip a trailing CR from the final field in the read loop, with the reasoning recorded inline. Verdict lines are now byte-identical across implementations, asserted by `tests/installer/test_doctor_parity.py`.
- **Why it is recorded rather than fixed silently**: it is the clearest available evidence that the parity requirement earns its cost. The durable fixes from both backfilled incidents caught a real defect on their first application.

### QG-2 - RESOLVED in Phase 5: `scripts/installer.ps1` was never AST-parsed in CI

- **What it was**: CI's unconditional PowerShell AST-parse step globbed `catalog/hooks` only, and the `bootstrap` job parses only the root `install.ps1`. `scripts/installer.ps1` - the largest PowerShell file in the repo, and the one this phase adds a subcommand to - was covered by neither. A parse error in it would have shipped exactly as `session-summary.ps1` did in v3.11.0.
- **How it was found**: while deciding where to add the AST assertion the plan required for the new `.ps1` code. The gate that the v3.11.0 incident produced turned out not to cover the file most exposed to the failure it guards.
- **Resolution**: the AST-parse step now covers `catalog/hooks/*.ps1`, `scripts/*.ps1`, and the root `install.ps1`. Verified locally on Windows PowerShell 5.1.

### NI-1 - RESOLVED in Phase 5

The `nexus-hub doctor` reference in `catalog/commands/update.md` (raised in Phase 2 as a documented-but-absent capability) now resolves: the subcommand exists in both installers. Closed by construction rather than by editing the prose, which is what Phase 2 predicted.

### DF-1 - RESOLVED in Phase 5

`scripts/check_release_capability_docs.py` exists, is wired into `DEV_ONLY_SCRIPTS`, and is now named in `update.md`'s governance step 6 with its real invocation. It ships ADVISORY (exits 0 while reporting) per the comparison's sequencing recommendation; `--strict` is the flip a future promotion turns on.

### NI-3 - OPEN (deliberate bound): `doctor --repair` prints remediation and never executes it

- **What it does**: `--repair` prints the exact remediation command for each failing platform and states plainly that nothing was changed.
- **Why it does not execute**: the remediation for most failures is re-running the installer, which writes across every platform surface. A diagnostic that mutates an install is how a preflight becomes the thing that breaks you, and the plan's own constraint is that doctor is read-only by default with any repair stating what it will change first. Printing the command satisfies the intent; executing it would put a write path inside a command users will reach for precisely when their install is already in an unknown state.
- **Suggested next step**: leave as-is unless a real user asks for it. If it is ever implemented, it must confirm interactively and name every path it will touch before touching one.

### WN-2 - CLOSED on inspection: `shellcheck` IS available on this host

Phase 1 recorded WN-1 (no `make`) as environmental and the v3.16.1 ledger carried a broader "no ruff or shellcheck" note. Phase 5 needed ShellCheck for the new Bash code and found it present and working: it flagged SC2088 on the first draft of `doctor_resolve_path`, which was then restructured rather than suppressed. `make` remains absent; `shellcheck` does not. Recording the correction so the next cycle does not skip a lint pass on a stale assumption.

### NI-4 - OPEN (opportunity, found at release governance step 4): GitHub Copilot now documents a user-global skills path

- **What changed on the vendor side**: Copilot's agent-skills documentation now lists **personal** skills at `~/.copilot/skills` or `~/.agents/skills`, and project skills at `.github/skills`, `.claude/skills`, **or** `.agents/skills`. Source: [docs.github.com](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills), fetched 2026-08-09.
- **Where Nexus-Hub stands**: Copilot is a behavioral-guardrails-only integration plus an OPT-IN `.github/skills/` project wrapper behind `NEXUS_HUB_COPILOT_SKILLS` (off by default because that directory is commit-visible). No user-global Copilot skills surface is written.
- **Why it is an opportunity, not a defect**: nothing is broken and no install regressed. A documented read-path simply became available that Nexus-Hub could populate, which would upgrade Copilot from guardrails-only to a full skills-bearing platform at global scope. Note that `nexus-hub init` already seeds project `.agents/skills` for Antigravity, which Copilot also reads, so some coverage may already exist incidentally and should be measured before new code is written.
- **Why it was not done in this release**: adding a new per-platform delivery surface is a feature with installer, adapter, contract, and test consequences across both installers. Implementing it inside a release commit is exactly the scope creep the Phase 4 scope-fit gate rejects.
- **Suggested next step**: a dedicated cycle. Measure what `.agents/skills` already surfaces to Copilot first, then decide whether `~/.copilot/skills` needs a separate write or whether the shared path suffices.

### NI-5 - OPEN (low): `~/.codex/skills` is no longer a documented Codex read-path

- **What changed**: Codex documents user-scope skill discovery at `$HOME/.agents/skills` only, plus `.agents/skills` scanned from the working directory up to the repo root. `~/.codex/skills` is absent from the current discovery list. Source: [learn.chatgpt.com](https://learn.chatgpt.com/docs/build-skills.md), fetched 2026-08-09.
- **Impact: none on coverage.** Nexus-Hub writes BOTH paths, and the one Codex reads is populated. The `~/.codex/skills` write is redundant rather than load-bearing, and its `install_verify` surface now asserts a path the vendor does not promise.
- **Why it is retained rather than removed**: this follows the precedent set for Cursor's commands directory in v3.15.10. Writing a directory the platform ignores is harmless; removing one that is still read would silently drop coverage, and vendor docs omitting a path is weaker evidence than vendor docs contradicting it.
- **Suggested next step**: re-verify next cycle. If `~/.codex/skills` is still undocumented, drop the write and its `install_verify` surface together.

### v3.16.2 Phase 6 final reconciliation

Every item raised across the six phases is dispositioned below. **8 closed, 5 carried forward, 0 release blockers.**

| Item | Disposition | Why |
|---|---|---|
| QG-1 | **Closed** (Phase 3) | `docs/incidents/**` added to both CI events' path filters, after the guard that justifies the trigger was built |
| QG-2 | **Closed** (Phase 5) | `scripts/installer.ps1` now covered by the unconditional AST-parse gate, alongside all `scripts/*.ps1` and the root bootstrap |
| BG-3 | **Closed** (Phase 5) | Trailing-CR divergence between the two doctors fixed and asserted by parity test |
| NI-1 | **Closed** (Phase 5) | `nexus-hub doctor` now exists, so `update.md`'s reference resolves |
| DF-1 | **Closed** (Phase 5) | `check_release_capability_docs.py` built, wired, and named in governance step 6 |
| WN-2 | **Closed** (Phase 5) | Stale assumption corrected: `shellcheck` IS present on this host and was used |
| MT-1 | **Carried** | The loop-schema concepts still have no mechanical assertion. Real, bounded, and now the cycle's only substantive open item. The duplicated `gates` block across `loop-schema.md` and `loop-library.md` is the concrete drift risk |
| NI-2 | **Carried** | `observability-setup` (763 lines) and `multi-agent-coordinator` (703) exceed the 500-line target. Both were already over before this cycle and remain under the 800 hard cap. Splitting `observability-setup` into `references/` is the next-touch action, deliberately not done here: a terminal phase is the wrong place to restructure a skill nothing in this plan required changing |
| NI-3 | **Carried** | `doctor --repair` prints rather than executes. A deliberate bound, not an omission |
| BG-2 | **Carried** | `secret-scan.sh` fails OPEN without `jq`. Pre-existing, bounded by a verified-working `.ps1` sibling, and out of this plan's scope (it touches no hook logic). **Worth a dedicated fix in a near-term cycle**: a security guard that fails open is the wrong default |
| WN-1 / BG-1 | **Carried** (environmental) | No `make` on this host; the inherited PowerShell bootstrap `tar` failure. Both re-verified rather than re-asserted: every `make validate` and `make test` command was run individually, and BG-1's signature is byte-identical to v3.16.0 and v3.16.1 |

Three of the eight closures (BG-3, QG-2, and BG-2's discovery) came from **exercising code rather than reading it** - running both doctors and diffing, checking where the AST gate actually globbed, and piping a payload through the secret-scan hook. That is this cycle's clearest methodological finding.

### Declined candidates (recorded so a future comparison does not re-propose them)

The LoopX comparison surfaced these and each was declined for a stated reason. Recording them here is what stops a later pass re-litigating settled ground.

| Candidate | Why declined |
|---|---|
| The LoopX control-plane runtime | Reverses the standing decision, restated three times since v3.1.0, that the loop **driver** is a host command to reference and never a catalog artifact to ship |
| Benchmark adapters | Out of scope, and they carry a Docker dependency |
| The dashboard SPA | Duplicates the v3.16.7 interactive-guide track already committed |
| The Lark extension | Fails the MCP Registry Policy tier-4 test: the vendor is not the intrinsic data destination |
| Per-skill agent sidecars and `.loopx-skill-scope` | Conflicts with the separate `catalog/agents/` surface and with the committed v3.16.9 selective-installation plan |
| Single-sentence skill descriptions | Conflicts with the mandated pushy-description style, which exists specifically to combat under-triggering |

One further candidate was **verified and dropped rather than declined on principle**: LoopX's CI hardening (path filters, concurrency groups, `timeout-minutes`, least-privilege `permissions`) is already complete across all nine Nexus-Hub workflows.

### Residual risk: does the incident archive become a directory nobody reads?

The comparison named this as the plan's main residual risk. The control is the Durable-fix requirement from Phase 3.1, and it **held, mechanically rather than aspirationally**:

- `scripts/check_incident_notes.py` fails any note whose Durable fix section carries no link, is wired into `make validate` and CI, and is covered by 12 tests asserting failure in each direction.
- `docs/incidents/**` triggers CI, so the guard runs on the push that adds a note.
- Both backfilled notes name AND link real, verified fixes, and each states what its fix would still miss.

The stronger evidence is behavioral rather than structural: within the same cycle, the shape those two notes describe (S-1, an unverified cross-platform sibling) **caught two live defects** - BG-3's Bash/PowerShell verdict divergence and QG-2's unparsed installer. An archive whose shapes are actively catching defects days after being written is not a graveyard. Re-assess after a cycle in which no one adds a note.

### Phase 1 disposition

Three items, **zero release blockers, zero caused by this phase**. MT-1 is a real coverage gap with a named owner (Phase 5); WN-1 and BG-1 are both environmental properties of the implementation host, already carried at v3.16.0 and v3.16.1 and re-verified rather than re-asserted.

### Phase 2 disposition

Two further items, **zero release blockers**. NI-1 is pre-existing and closes automatically when Phase 5 builds the subcommand it names. DF-1 is a deliberate plan-ordered deferral, not an omission. Neither was caused by Phase 2's edits, and the dry-run above is evidence rather than a gap.

### Phase 4 disposition

One new open item, **zero release blockers, zero caused by this phase**. NI-2 records a pre-existing condition that a plan instruction assumed away; the four doctrine additions themselves landed without collision, created no new skill, changed no frontmatter, and left `data/skills.json` untouched. `check_base_template_parity.py` was run explicitly and passes: `AGENTS.md` is not one of the five lockstep `base-*.md` templates, so these edits required no template change, which is exactly what sub-task 4.5 asked to verify.

### Phase 3 disposition

One new open item and one resolved. **Zero release blockers.** BG-2 is a pre-existing fail-open in a security hook, found by exercising the hook instead of reading its registration, bounded by the verified-working PowerShell sibling and already documented as a known asymmetry in `AGENTS.md`. QG-1 was raised and closed inside the phase.

The phase's own residual risk (named in the comparison) is that the incident archive becomes a directory nobody reads. The control is the Durable-fix requirement, and it is now mechanical rather than aspirational: `scripts/check_incident_notes.py` fails a note whose fix section carries no link, is wired into `make validate` and CI, and is covered by 12 tests asserting failure in each direction. Phase 6.2 should record whether it held.

## v3.16.3 - github-usage-monitor-ux

Appended by Phase 1 (Rename to GitHub Usage Monitor, with settings migration) on 2026-08-09. Own `DF-#` / `NI-#` / `BG-#` / `WN-#` / `QG-#` / `MT-#` namespace, separate from v3.16.0's, v3.16.1's, and v3.16.2's.

### DF-1 - DEFERRED by design: the old `githubUsage.*` configuration keys are not deleted

- **Target file**: `extensions/github-usage-monitor/src/migration.ts`
- **What is deferred**: v3.16.3 copies every user-set `githubUsage.*` value to `githubUsageMonitor.*` and then leaves the old key exactly where it is. The user's `settings.json` therefore carries both namespaces for one release.
- **Why it is deliberate, not an oversight**: the plan's sub-task 1.2 requires it, for two reasons that both hold. A user who downgrades to 0.1.0 must still find their settings, and a deletion that races a failed write loses the data outright rather than leaving a recoverable duplicate. The migration is written write-then-keep for the same reason the token path is written store-then-delete.
- **Suggested next step**: delete the old keys in v3.17.0, after one release has shipped with the migration. The key list is already an exported constant (`MIGRATED_CONFIG_KEYS`), and a test pins it against `package.json`, so the deletion pass has an authoritative list to iterate.

### NI-1 - CLOSED in phase: the plan's scope note omitted two files the rename necessarily breaks

- **What the plan said**: "this plan touches `extensions/github-usage-monitor/` plus four files outside it (`.github/workflows/github-usage-monitor.yml`, `.github/dependabot.yml`, `catalog/hooks/tests/test_installer_smoke.py`, and the two v3.15 contract documents)".
- **What implementation found**: two more surfaces hard-code the superseded display name and fail the moment it changes. `scripts/installer.sh` and `scripts/installer.ps1` each pass `"GitHub Billing Usage"` and the `"GitHub Billing: --"` status hint into `build_and_install_one_extension`, and `tests/installer/test_github_billing_rename.py` (57 assertions across 15 tests) existed solely to pin the v3.15.12 rename this phase reverses. Ten of its tests failed on the first full run. Neither of the two named workflow files needed any edit, because both key on the folder name, which did not move.
- **How it was closed**: the installers were updated with explicit maintainer approval (AGENTS.md lists installer edits under "Ask first"). The test file was rewritten and renamed to `tests/installer/test_github_monitor_naming.py`, keeping every durable invariant (the extension id never moves, both installers agree, exactly one install invocation, no teardown step) and re-deriving every naming assertion from a single `DISPLAY_NAME` constant, so the next rename is a one-line change rather than a ten-test rewrite. One assertion was added: the installer's status hint must match the label `statusBarManager.ts` actually renders, which is the drift this class of test was closest to missing.
- **Why it is recorded rather than dropped**: the plan's scope note is used by Phase 6 to bound the refactor sweep. A reader who trusts it would miss both surfaces.

### MT-1 - OPEN (pre-existing): `extension.ts` is the least-covered module, and the migration call site is only covered indirectly

- **Target file**: `extensions/github-usage-monitor/src/extension.ts` (36.81% statements, 40.38% lines)
- **What is missing**: `migration.ts` itself is well covered (89.65% statements, 100% functions) by 12 direct unit tests. Its *call site* inside `activate()` is exercised only as a side effect of the three test files that call `activate()`, none of which assert that the migration actually ran before the first configuration read. The ordering is the load-bearing property, and nothing pins it.
- **Why it was not done in Phase 1**: `extension.ts` was already the module's coverage floor before this phase, and the phase's Stability Gate is scoped to the rename and the migration's own behavior, both of which are covered. The repository thresholds pass with room (81.78% statements against 80, 85.67% lines against 80).
- **Suggested next step**: Phase 3 adds a first-run connection sequence to `activate()` and will need an activation-ordering test harness anyway. Add one assertion there that a configuration read observed the migrated value, not the default.

### WN-1 - OPEN (environmental, inherited): no `make` on the implementation host

- **What happened**: `make` is absent on this machine, so neither `make validate` nor `make test` could be invoked as targets. Same condition recorded as v3.16.1 WN-1 and v3.16.2 WN-1.
- **How it was handled rather than skipped**: every command inside both targets was read out of the `Makefile` and run individually. Fifteen `validate` guards pass; ShellCheck is clean on both installers once the Windows working copy is LF-normalized (see BG-2); all five MCP extension suites, `catalog/hooks/tests` (993 passed, 36 skipped), the extension's own Vitest suite (219 passed), and `tests/` were run to completion.
- **Suggested next step**: none for correctness. CI runs the authoritative gate on Linux and Windows.

### BG-1 - OPEN (pre-existing, inherited): PowerShell bootstrap tarball test fails on this host

- **What happened**: `tests/installer/test_bootstrap.py::test_ps_standalone_extracts_and_hands_off` fails with `/usr/bin/tar: Child returned status 128`. It is the single failure in the `tests/` run.
- **Why it is not this phase's**: the failure signature is byte-identical to the one recorded under v3.16.0 BG-1, v3.16.1 BG-1, and v3.16.2 BG-1, where it was reproduced on a clean `develop` worktree. This phase's only installer edit is two display strings inside the extension-install block, which the standalone bootstrap path does not reach.
- **Bound**: affects a Windows host whose PATH resolves `tar` to the Git Bash binary. CI runners are unaffected.

### BG-2 - OPEN (environmental, newly characterized): ShellCheck reports SC1017 on every line of both shell installers on this host

- **What happened**: `shellcheck --severity=warning scripts/installer.sh install.sh` emits SC1017 ("Literal carriage return") on essentially every line, producing 41 KB of output that reads as a total lint failure.
- **What it actually is**: git normalizes these files to LF on commit (`git diff` prints "CRLF will be replaced by LF the next time Git touches it"), so the CRLF exists only in the Windows working copy. Running ShellCheck against `git show HEAD:scripts/installer.sh` produces zero findings, and piping the working copy through `tr -d '\r'` first is clean for both files.
- **Why it is recorded rather than silently worked around**: the raw output is indistinguishable from a real regression, and a future phase that hits it on this host will otherwise spend the same time re-deriving that it is noise.
- **Suggested next step**: none required. If it recurs often enough to be a nuisance, the `lint` target could pipe through `tr -d '\r'` on Windows; that is a convenience change, not a correctness one.

### Phase 1 disposition

Four open items, **zero release blockers, one caused by this phase** (DF-1, which the plan mandates). NI-1 was raised and closed inside the phase. MT-1 is a pre-existing coverage floor with a named next-touch owner in Phase 3. WN-1, BG-1, and BG-2 are all environmental conditions of the Windows implementation host, two of them inherited unchanged from three prior cycles.

The phase's own residual risk is that the settings migration is untestable in the one situation that matters most: a real 0.1.0 install upgrading in place. Every migration assertion here runs against a fake `WorkspaceConfiguration`. The controls are that the migration refuses to record completion on any write failure (so a bad first pass retries rather than silently finishing), that it never deletes an old key, and that the token path writes before it deletes. Phase 6 should record whether an actual upgrade was exercised.

### NI-2 - SUPERSEDED 2026-08-22 by v3.18.1: the weights are no longer constants to verify

> **Superseded by v3.18.1 (`github-usage-monitor-accuracy`).** `OS_DRAWDOWN_WEIGHTS` no longer exists as a behavioral input. Each item's weight is derived from its own `pricePerUnit` relative to the standard Linux rate observed in the same payload, so there is no constant left to re-verify at each release and the "re-check the multiplier path" next step below is retired. The **underlying** uncertainty is not closed - price ratios and the legacy published values still cannot be separated by any saturated month - and is carried forward as `NI-1` in `docs/v3/v3.18/known-gaps.md` with a stated falsifier and a ledger to accumulate evidence. The decision that replaced this entry is `docs/decisions/implemented/architecture/2026-08-22-derive-actions-drawdown-weights-from-price.md`.
>
> Note also that the "ship the historical published values" decision recorded below was **reverted in v3.16.4** back to all-1 before v3.18.1 replaced the mechanism entirely; this entry describes the v3.16.3 state.

- **Target file**: `extensions/github-usage-monitor/src/providers/drawdown.ts` (`OS_DRAWDOWN_WEIGHTS`)
- **What is unresolved**: GitHub withdrew its minute-multiplier reference page; that path now serves runner pricing on every documentation variant checked. Measurement established that weighting **exists** (July's saturated bar falsified 1:1 outright), but not what the constants are. Two candidates fit every month available - the historical published values (Windows 2x, macOS 10x) and the current list-price ratios (1.67x, 10.33x). They predict 2,104 and 2,051 for July, both above a saturated 2,000, so that month cannot separate them; April, the only month low enough to try, predicts 1,473 versus 1,469.
- **Decision**: ship the historical published values, chosen with the maintainer, because GitHub once stated them outright where a price ratio never was. The card labels the figure a reconstruction rather than presenting it as GitHub's own.
- **Suggested next step**: re-check the multiplier path at each release (it is on the probe document's re-verification checklist). If GitHub republishes the basis, replace the constants and delete the caveat. An account with private macOS usage below the cap would also settle it.

### NI-3 - OPEN: the two billing endpoints use different SKU vocabularies

- **Target file**: `extensions/github-usage-monitor/src/providers/drawdown.ts` (`classifySku`)
- **What is wrong**: `/settings/billing/usage` returns `Actions Linux`; `/usage/summary` returns `actions_linux`. The classifier handles both only because its patterns are substring-based - a rule written against either vocabulary alone would silently misclassify the other endpoint's items, and a misclassified runner is excluded from the drawdown without a trace.
- **Suggested next step**: pin both vocabularies in the fixtures (the `Actions *` forms already are; add the `actions_*` forms) and state the hazard in a header comment on the pattern constants.

### MT-2 - OPEN: the self-hosted and larger-runner rules are unvalidated against real strings

- **Target file**: `extensions/github-usage-monitor/src/providers/drawdown.ts`
- **What is missing**: the measured account emitted only `Actions Linux`, `Actions Windows`, `Actions macOS 3-core`, `Actions storage`, and `Git LFS storage`. No self-hosted or larger-runner SKU appeared, so those exclusion rules are tested against **invented** strings only. Both are load-bearing: a larger-runner SKU wrongly counted inflates the drawdown, and a self-hosted one inflates it further.
- **Why it was not done in Phase 2**: no account was available that uses either runner class, and inventing a plausible string then asserting against it tests the rule against itself.
- **Suggested next step**: capture a real SKU inventory from an account using larger or self-hosted runners via `scripts/reconcile-drawdown.js`, which prints the inventory and flags anything unrecognized. Treat both rules as provisional until then.

### NI-4 - OPEN (policy, raised by the maintainer): this extension is held to a stricter rule than its three siblings

- **What surfaced**: the Claude, Codex, and Cursor monitors each read a usage endpoint returning used and limit together (`api.anthropic.com/api/oauth/usage`, `chatgpt.com/backend-api/wham/usage`, `api2.cursor.sh`). Two of those three are **not public APIs**. GitHub has an equivalent internal endpoint - it renders the very bars this phase spent its entire budget reconstructing - and the GitHub monitor is barred from it by its own data contract ("never scrapes GitHub.com, reads browser cookies").
- **Why it matters**: the honest answer to "why can't the GitHub monitor do what the others do" is not that it cannot, but that a rule written for this one extension forbids it. Phase 2's whole difficulty follows from that asymmetry.
- **Why it was not resolved here**: it is a policy question about what the monitors may read, affecting four extensions rather than one. Settling it inside a phase scoped to allowance derivation would be the wrong venue.
- **Suggested next step**: decide the standard deliberately in its own cycle - either relax the GitHub monitor's contract to match its siblings, or tighten the siblings to match it. Do not let it be settled by accretion.

### QG-2 - CLOSED in phase: three defects in the measurement tooling itself

- **What happened**: the reconciliation probe was wrong three times before producing a usable result. The first run used a `user`-only token, so private repositories 404'd and every private candidate summed zero. The second misclassified `Actions macOS 3-core` as a larger runner, dropping 111 minutes. The third compared August API data against displayed figures from an earlier month.
- **How each was closed**: the runner now withholds its verdict when any visibility lookup fails; the core-count rule became a per-OS ceiling with a regression test pinned to the real strings; and the queried period is printed directly above the verdict.
- **Why it is recorded rather than dropped**: each defect produced a *plausible wrong answer* rather than an error, and two of them briefly left a falsified model looking correct. What actually caught it was checking a candidate against an arithmetic bound rather than a tolerance. **A numeric match near a true value is not evidence.**

### Phase 2 disposition

Four open items, **zero release blockers**, one closed inside the phase. NI-2 is a deliberate, maintainer-approved decision with a named re-check trigger. NI-3 and MT-2 are honest limits of what a single account could validate. NI-4 is a policy question deliberately routed out of this phase.

The phase's own residual risk is that the shipped percentage is a **reconstruction presented inside a product that otherwise reports measured facts**. Three controls: the card states it is reconstructed rather than GitHub's own figure; an unresolved repository or unrecognized SKU excludes usage rather than guessing, so error runs toward understating; and `AllowanceInputs.api` stays unpopulated with a test asserting `allowanceSource` is never `"api"`, so nothing here can later be mistaken for a served entitlement.

### MT-1 - RESOLVED in Phase 3: the activation-ordering assertion now exists

- **Raised**: v3.16.3 Phase 1, noting that `migration.ts` was well covered while its call site inside `activate()` was exercised only incidentally, with nothing pinning the ordering that makes it correct.
- **How it was closed**: Phase 3 needed an activation harness for the first-run sequence, which is exactly what MT-1's suggested next step anticipated. The vscode stub gained an ordered configuration-access log, and `first-run.test.ts` asserts that the migration WRITE precedes the first READ of the same key, then that the read observed the migrated value rather than the default. Asserting the final value alone would have passed even if the read won the race.
- **Residual**: `extension.ts` remains the module's coverage floor. That is a breadth gap, not the specific ordering gap MT-1 named, and it is not carried forward as MT-1.

### NI-5 - OPEN (small): the first-run sequence resolves an owner before the session exists

- **Target file**: `extensions/github-usage-monitor/src/extension.ts` (the activation tail)
- **What is imperfect**: on a truly fresh install there is no session, so `resolveOwnerForFetch` returns null and the sequence falls back to `{ scope: <configured>, name: "pending" }` purely to pick scope candidates. The placeholder name is never used for a billing request - the refresh that follows re-resolves the owner from the now-established session - but a reader could reasonably mistake it for a real owner.
- **Why it is shaped that way**: the same deadlock the `logIn` command documents. With nothing configured there is no session, so the owner cannot be detected, so demanding one before connecting would prevent the very first connection.
- **Suggested next step**: give `firstRun` a scope rather than a full owner, since scope is all it needs. A small signature change best done when Phase 4 or 5 is already touching this file.

### Phase 3 disposition

One resolved, one new open item, **zero release blockers**. MT-1 closed exactly where Phase 1 predicted it would be cheapest. NI-5 is cosmetic and has a named next-touch owner.

The phase's own residual risk is the failure mode it exists to prevent: a modal on every VS Code start. Three controls, all mechanical. The decline flag lives in `globalState` rather than in memory, so it survives a restart; `runFirstRunConnection` returns an `interactiveAttempts` count and a test asserts it is exactly 1 on the prompting path and 0 on every other, which is the single number that separates correct behaviour from the defect; and a further test loops three additional activations after a decline, which a per-session flag would pass on one re-run and fail here.

### NI-5 - RESOLVED in Phase 4: the first-run sequence takes a scope, not a placeholder owner

- **Raised**: v3.16.3 Phase 3, noting that a fresh install passed `{ scope: <configured>, name: "pending" }` purely to select auth scopes, and that the placeholder read as a real account name.
- **How it was closed**: `FirstRunDependencies` now takes `scope: BillingScope`. The sequence constructs the throwaway owner internally with a comment stating that `peekBinding` and `logInToMonitor` read the name from it never - they take an owner only to derive scope candidates. Folded into Phase 4 because that phase was already in `extension.ts`, exactly as the gap's suggested next step proposed.
- **Caught by the change**: the test fixture kept passing `owner`, and because Vitest transpiles without type-checking, the missing `scope` surfaced as five runtime failures rather than a compile error. Worth remembering: a signature change in this codebase is only type-checked by `npm run compile`, not by the test run.

### NI-6 - OPEN (small): the settings section is read-only

- **Target file**: `extensions/github-usage-monitor/src/settingsPanel.ts` (`settingsSectionHtml`)
- **What is incomplete**: the section renders every value and every relocated command, but the fields themselves are static text. Changing a threshold still means opening VS Code settings via the "Edit in VS Code settings" button.
- **Why it is deliberate**: Phase 5 owns exactly this ("The current settings panel is entirely read-only... Making it editable is the real work here, not the layout"). Phase 4's remit was the shell.
- **Suggested next step**: Phase 5, as planned. `validateThresholds` already exists and is exported for it.

### Phase 4 disposition

One resolved, one new open item, **zero release blockers**. NI-5 closed where Phase 3 predicted. NI-6 is the deliberate Phase 4/5 boundary, recorded so a reader does not mistake a read-only section for an oversight.

The phase's own residual risk is that the settings section now shares one webview document with the dashboard, so a rendering error in either takes both down - where previously a broken settings panel left the dashboard usable. Three controls: the section renders on every state including unconnected and no-data, so the gear is never a control that does nothing; a test asserts exactly one `<script>` element and exactly one `acquireVsCodeApi()` call, since a second would throw and blank the whole panel; and `retainContextWhenHidden` was already set, so the merge did not change the panel's lifecycle.

### NI-6 - RESOLVED in Phase 5: the settings section is editable in place

- **Raised**: v3.16.3 Phase 4, recording the deliberate Phase 4/5 boundary - the section rendered every value but the fields were static text.
- **How it was closed**: thresholds, colors, the alert metric, the new status-bar metric, the compact toggle, the notification timeout, and the refresh interval all write back through `postMessage`. Threshold ordering is validated in the webview so the message lands beside the offending field, and `extension.ts` re-validates every message before touching configuration. The "Edit in VS Code settings" escape hatch was kept as a secondary control.

### BG-3 - RESOLVED in Phase 5: a snapshot missing a metric crashed the hover

- **Target file**: `extensions/github-usage-monitor/src/statusBarManager.ts`
- **What was wrong**: `selectStatusMetric` and `metricSection` both assumed all three metrics are always present. A snapshot cached by v0.1.0 can be missing one, and `undefined` reaching `formatAmount` threw, taking the entire tooltip down rather than degrading.
- **How it was found**: a Phase 5 test fixture that deliberately omitted a metric to exercise the unavailable-selection path. It surfaced two crashes neither the fixture nor the phase was aiming at.
- **Class**: the same one Phase 2 hit with a `NaN` drawdown. **Cached state outlives the version that wrote it**, so every access to a field added after 0.1.0 must tolerate absence. Worth checking the remaining surfaces in Phase 6.

### NI-7 - OPEN (small): the webview write-back has no dirty/save affordance

- **Target file**: `extensions/github-usage-monitor/src/settingsPanel.ts`
- **What is different from the sibling**: the Claude monitor's inline settings collect a draft and expose Save / Reset buttons; this one writes each field on `change`. Immediate write is simpler and matches the plan's wording ("each writing back through `postMessage`"), but it means there is no undo and no visible confirmation that a change landed.
- **Mitigation already in place**: both surfaces re-render immediately after a successful write, so the effect is visible at once. A setting that appears to do nothing for ten minutes is the failure this avoids.
- **Suggested next step**: only if a user reports wanting it. Adding Save / Reset would also mean adding a dirty-state model, which is real complexity for a form of eleven fields.

### Phase 5 disposition

Two resolved, one new open item, **zero release blockers**. NI-6 closed as planned. BG-3 was a genuine pre-existing crash found by a fixture aimed elsewhere. NI-7 is a deliberate divergence from the sibling pattern, recorded so it is not mistaken for an omission.

The phase's own residual risk is that a webview can now write configuration. Three controls: `EDITABLE_SETTINGS` gates both the key AND the value type, so a crafted message cannot reach an arbitrary VS Code setting; threshold ordering is re-validated in `extension.ts` because the panel's inline check is a convenience for the user and never a guarantee for the extension; and a test asserts that keys outside the set - including `billingOwner`, the allowance keys, and an unrelated `http.proxy` - are all rejected.

### NI-3 - RESOLVED in Phase 6: both SKU vocabularies are pinned

- **Raised**: Phase 2, on discovering that `/settings/billing/usage` returns `Actions Linux` while `/usage/summary` returns `actions_linux`, and that the classifier survived both only because its patterns happened to be substring-based.
- **How it was closed**: a header comment on the pattern block names the hazard and requires a fixture in BOTH spellings for any new rule, and a test asserts the two vocabularies classify identically across Linux, Windows, macOS, storage, and self-hosted - the last in three separator forms. What was luck is now a contract.

### BG-4 - RESOLVED in Phase 6: `repositoryNamesIn` would throw on a legacy snapshot

- **Target file**: `extensions/github-usage-monitor/src/providers/repositories.ts`
- **What was wrong**: the filter tested `name !== null`, which `undefined` passes, and then read `.length` on it. A breakdown written by extension 0.1.0 carries no `repositoryName` at all, so a cached snapshot reaching that path would throw.
- **How it was found**: the BG-3 absence-tolerance sweep this phase was asked to run. `enrich.ts` had the same shape one line away, where `undefined` slipped past a `=== null` guard and landed in the unresolved list as a literal `undefined`.
- **Now pinned**: `enrich.test.ts` carries a `legacySnapshot()` fixture shaped exactly like a 0.1.0 snapshot - no `drawdown`, no `drawdownBasis`, no `allowanceState`, and breakdowns with no `repositoryName` - and asserts the whole pipeline enriches it without throwing, withholds every percentage, and still converts storage.

### Phase 6 disposition, and the v3.16.3 reconciliation

Every v3.16.3 item was verified against its target file rather than transcribed from a prior phase's assertion, per the v3.16 ledger's own methodological note.

| Item | Verdict | Basis |
|---|---|---|
| NI-1 (plan scope note incomplete) | **Closed** in Phase 1 | Installers and the naming test updated; 48 tests pass |
| QG-2 (three probe-tooling defects) | **Closed** in Phase 2 | Verdict withheld on lookup failure; per-OS core ceiling; queried period printed |
| MT-1 (activation ordering unasserted) | **Closed** in Phase 3 | `first-run.test.ts` asserts the migration write precedes the first read |
| NI-5 (placeholder owner) | **Closed** in Phase 4 | `FirstRunDependencies` takes `scope: BillingScope` |
| NI-6 (read-only settings section) | **Closed** in Phase 5 | Eleven fields editable in place, write-back gated by `EDITABLE_SETTINGS` |
| BG-3 (missing metric crashed the hover) | **Closed** in Phase 5 | `selectStatusMetric` and `metricSection` both guarded |
| NI-3 (two SKU vocabularies) | **Closed** in Phase 6 | Header contract plus a both-spellings test |
| BG-4 (legacy snapshot threw) | **Closed** in Phase 6 | Guard plus the `legacySnapshot()` regression fixture |
| DF-1 (old `githubUsage.*` keys retained) | **Carried**, deliberate | Plan sub-task 1.2 requires one release of overlap; deletion targeted at v3.17.0 |
| NI-2 (drawdown weights unverifiable) | **Carried**, deliberate | GitHub publishes no basis; shipped by maintainer decision with the probe's re-verification checklist as the trigger |
| MT-2 (self-hosted / larger-runner rules) | **Carried** | No account available that uses either runner class; rules remain provisional |
| NI-4 (cross-monitor endpoint policy) | **Carried, routed out** | Affects four extensions and is a policy question, not an engineering one |
| NI-7 (no dirty/save affordance) | **Carried**, deliberate | Divergence from the Claude monitor; both surfaces re-render immediately instead |
| WN-1 / BG-1 / BG-2 | **Carried**, environmental | `make` absent on this host; the pre-existing PowerShell bootstrap tar failure; ShellCheck CRLF noise on a Windows working copy |

**Six closed, eight carried, zero release blockers.**

### The one item that should not be closed here: NI-4

Every other carried item is a scoped engineering decision with a named next step. NI-4 is different in kind and is called out separately so it is not lost in a table.

The Claude, Codex, and Cursor monitors each read a vendor endpoint that returns used and limit together, and **two of those three are not public APIs**. GitHub has an equivalent internal endpoint - it renders the very bars this plan spent two phases reconstructing - and the GitHub monitor alone is barred from it by its own data contract.

That asymmetry is the direct cause of this plan's hardest work: the entire drawdown reconstruction, its unverifiable weights (NI-2), its provisional SKU rules (MT-2), and the "reconstructed" caveat on every bar exist because of a rule written for one extension. Resolving it either way would retire three carried items at once.

It is deliberately **not** decided here. It affects four extensions, it is a question about what the monitors may read rather than about how they compute, and settling it inside a phase scoped to allowance derivation would be the wrong venue. It belongs in its own cycle, with the four monitors considered together.

## v3.16.5 - presentify-visual-overhaul

**Source plan**: [docs/releases/v3/v3.16/plans/v3.16.5-presentify-visual-overhaul.md](plans/v3.16.5-presentify-visual-overhaul.md). Appended at Phase 1 (fluid layout + readability contract). Ids are namespaced to this version, per the file-lifecycle note at the top.

### MT-1 - CLOSED in Phase 7: the calibration fixture is homed and guarded

- **Target file**: `tests/fixtures/presentify/nexus-hub-unit-test-workflow.html` (moved there in Phase 7 with `git mv`; tracked at the repo root from Phase 1 until then)
- **Source phase**: v3.16.5 Phase 1, sub-task 1.3
- **Plan reference**: sub-task 1.3 explicitly defers the fixture's final location ("coordinate with the maintainer on its final location - Phase 7 may move it under a fixtures dir")
- **Reason it is open**: Phase 1 brought the fixture to a clean scorer pass (0 high-severity findings across all nine criteria) and committed it at the repo root, so the fixes are no longer at risk of being lost. Two halves of the gap remain: the root is a holding position rather than its final location, and no test asserts that it still passes the scorer, so a future regression in either the fixture or the checker would go unnoticed.
- **Suggested next step**: Phase 7 sub-task 7.1 homes the fixture with reference repair (a `tests/fixtures/presentify/` dir is the natural target, and `tests/skills/**` is already a CI path filter); at that point add a one-line regression test asserting `score_html(fixture)["page_pass"] is True`, which converts the calibration fixture from a manual artifact into a standing gate.
- **One migration hazard to expect**: the fixture also exists as an untracked working-tree file at the ROOT of the primary checkout, where it was authored. When this branch merges to `develop`, git will place the tracked copy at `tests/fixtures/presentify/` and the stray root copy will simply remain untracked - delete it after the merge. It is not a conflict, and nothing reads it any more.
- **CLOSED 2026-08-11 by v3.16.5 Phase 7** (sub-task 7.1, home decided with the maintainer). The fixture now lives at `tests/fixtures/presentify/nexus-hub-unit-test-workflow.html`, moved with `git mv` so history follows it, and both halves of the gap are shut:
    - **Location**: inside a tree CI already path-filters, rather than an 84 KB HTML file at the repository root that read like stray build output. The two live references were repaired (the CI scoring step) or simplified (the dual-candidate lookup in the test, which existed only to survive this move and would otherwise have left a second accepted location nobody maintains).
    - **Guarding**: three standing tests plus a CI step. `test_calibration_fixture_passes_every_structural_criterion` fails on any high-severity regression, `test_calibration_fixture_has_no_stale_palette_literals` pins the superseded pre-v3.16.5 palette out of live markup, `test_calibration_fixture_holds_the_e5_rules` covers the render-surfaced defect classes, and the seven-case mutation suite proves the checks still detect what they claim. The `render` job also scores it directly.
    - **One gap the move itself introduced, and closed**: the workflow path-filtered `tests/skills/**` but not `tests/fixtures/**`, so a fixture-only edit would no longer have triggered the job that scores it - the standing gate would have silently stopped gating the exact file it guards. `tests/fixtures/presentify/**` was added to both filter lists.

### NI-2 - OPEN by design: contract rules 2 and 3 have no deterministic check

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/scripts/visual_qa_score.py`
- **Source phase**: v3.16.5 Phase 1, sub-tasks 1.1 and 1.2
- **Reason it is open**: rule 2 ("wrapping serves the viewport") is a rendered-geometry judgment - whether a paragraph sits beside dead space depends on the resolved track width, the actual `ch` width of the chosen font, and the reflow breakpoint, none of which are knowable from the markup. It is specified as an AGENT-VISION criterion in `references/visual-qa-rubric.md` criterion 6 and graded from a screenshot. Rule 3 ("scale declared once as custom properties") is partially enforced: the scorer now resolves `var()` against declared properties, so a malformed step token IS caught, but nothing asserts that the scale is declared once on `:root` rather than scattered.
- **Suggested next step**: Phase 3's real render loop closes the rule-2 half by measuring band and text-block boxes from an actual screenshot (this is the same measurement `measure_widest_band` already performs for full-width). The rule-3 half needs no code: a page whose tokens are wrong now fails `font-floor`, so the remaining gap is stylistic rather than a readability defect. Do not add a "declared once" parser check without a defect to point at.

### WN-1 - OPEN: semantic status colors are excluded from the automated contrast set

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/scripts/visual_qa_score.py` (`_STATUS_NAME_RE`)
- **Source phase**: v3.16.5 Phase 1, sub-task 1.2
- **Reason it is open**: a badge color's applicable WCAG floor is 3:1 when it renders as large or bordered text and 4.5:1 when it renders as body copy, and the scorer cannot know which. Grading every status color against 4.5:1 would produce false failures that teach authors to bypass the gate. The calibration fixture's `--stop: #c25050` measures 3.72:1 against `--base`, which passes the large-text floor and fails the body floor, and is therefore left ungraded rather than force-resolved.
- **Suggested next step**: Phase 3 grades status-badge contrast from a real screenshot, where the rendered size is observable and the correct floor is therefore decidable. `references/visual-qa-rubric.md` criterion 7 already assigns this to the AGENT-VISION half.

### DF-1 - CLOSED as accepted: the CSS rule parser treats media-scoped rules as unconditional

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/scripts/visual_qa_score.py` (`css_rules`)
- **Source phase**: v3.16.5 Phase 1, sub-task 1.2
- **Status**: accepted and documented in the function's own docstring rather than carried as a defect. The leaf-rule regex skips an at-rule prelude and returns the rules nested inside it, so a `font-size` declared only under a narrow breakpoint is graded as if it always applied. This errs toward REPORTING, which is the safe direction: a small font declared at a breakpoint is still a small font at that breakpoint. Resolving cascade plus breakpoints statically is the job of the real render (Phase 3), not of a markup heuristic.

### BG-1 - CLOSED in Phase 2: five of six per-section accent colors were sub-AA, injected at runtime

- **Target file**: `nexus-hub-unit-test-workflow.html` (the `data-accent` attributes and the canvas `fillStyle` / series literals)
- **Source phase**: v3.16.5 Phase 2, found while retargeting the diagrams' hardcoded hexes
- **What was wrong**: the page morphs its accent per section by reading `data-accent` off the active `<section>` and assigning it to `--accent` at runtime. All six declared values measured **3.20:1 to 4.36:1** against `--base`, so Phase 1's AA correction of the `--accent` token was reverted on every section as soon as the script ran. The canvas chart's axis-label and series colors carried the same superseded literals.
- **Why Phase 1 could not have caught it**: the values live in HTML attributes and JavaScript string literals, not in CSS declarations, so the `contrast` check never saw them. Phase 1's gate passed truthfully on what it could observe.
- **Resolution**: all six accents were replaced with hue-preserving values clearing AA (rose 4.36 -> 6.22, steel 3.20 -> 6.25, green 3.79 -> 6.17, olive 4.03 -> 5.65, terracotta 4.33 -> 5.67), and the canvas label color moved to the corrected `--ink-faint` value. The residual CHECKER gap is tracked separately as WN-2.

### WN-2 - OPEN: the scorer cannot see runtime-injected palette values

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/scripts/visual_qa_score.py` (`check_contrast`)
- **Source phase**: v3.16.5 Phase 2 (the checker gap behind BG-1)
- **Reason it is open**: `check_contrast` grades declared CSS custom properties. A page that assigns `--accent` from a `data-*` attribute in script, or paints canvas text with a literal, can pass the check and still render sub-AA text - which is exactly what BG-1 was. Statically resolving what a script assigns at runtime is not a job for a markup heuristic.
- **Suggested next step**: Phase 3 closes this by construction rather than by more parsing. A real screenshot shows the rendered color, so the AGENT-VISION half of rubric criterion 7 grades what the page actually paints. Do NOT attempt to interpret the script statically. A cheap partial guard is possible if it proves useful: collect hex literals from `data-accent`-style attributes and grade them alongside the declared tokens.

### NI-3 - OPEN by design: SVG contract rules 2 and 3 have no deterministic check

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/references/svg-diagram-quality.md` (rules 2 and 3)
- **Source phase**: v3.16.5 Phase 2, sub-tasks 2.1 and 2.2
- **Reason it is open**: rule 2 (no dashed path passes within a label's bounding box) needs a text-metrics engine to know a label's real box - glyph advance widths, letter-spacing, and the rotation transform all matter, and none is available to a markup parser. Rule 3 (connectors terminate on node edges) is checkable in principle but only against a declared intent about which shapes a connector joins, which the markup does not state. Both were verified NUMERICALLY by hand for this phase's two diagrams instead: the cubic midpoints are (269, 27.25) and (291, 245), giving 15.25 and 23.0 user units of label clearance, and every coordinate lies inside its viewBox.
- **Suggested next step**: Phase 3's render loop closes rule 2's practical half, since a screenshot shows a label sitting on a line immediately. Rule 3 stays an authoring discipline enforced by the rule-5 self-check; adding a parser for it would need an annotation convention that does not exist yet, so do not build one without a defect to point at.

### BG-2 - CLOSED in Phase 3: three rendered font-floor violations the static check passed

- **Target file**: `nexus-hub-unit-test-workflow.html`, plus two heuristics in `scripts/visual_qa_score.py`
- **Source phase**: v3.16.5 Phase 3, sub-task 3.4 (the first time in this plan that anything rendered the page)
- **What was wrong**: rendering at 1920 / 1366 / 390 measured three non-interactive text elements below the 13px secondary floor while `font-floor` reported all sizes clean. Two were CHECKER bugs and one was a Phase 1 mapping error:
    1. `.brand` at **12.48px**. `_font_role` matched `nav` anywhere in the selector, so `#nav .brand` - a static brand label inside a nav - was graded against the 12px interactive floor. Fixed by reading only the LAST compound of a selector and splitting the interactive pattern into an ELEMENT form and a CLASS form; `.label` and bare `nav` no longer imply interactivity.
    2. `code` at **12.22-12.81px**. `font-size:.92em` is relative to the inherited size, which the checker explicitly skips because it cannot resolve it. Fixed in the fixture with `max(.92em, 0.8125rem)`, which floors the optical em-matching at 13px, and in the checker by teaching `_len_px` to resolve `min()` / `max()` so the flooring construction the contract now recommends is itself verifiable.
    3. `.cmd-bar .label` at **12.07px**. Phase 1 mapped this static caption onto `--step--3`, the INTERACTIVE step, because its class is named `label`. Re-mapped to `--step--2`.
- **Also fixed in the same pass**: an inline `style="font-size:.72rem"` rendering at 11.52px on every viewport, invisible to a CSS-rule parser. The checker now grades `style="..."` attributes as pseudo-rules with the secondary floor, taking the checked-size count from 40 to 41.
- **And a horizontal-overflow regression introduced by Phase 2**: at 390px the document scrolled to 512px. Root cause was not the pinned graphic itself but the mobile media queries overriding `grid-template-columns` to `1fr`, dropping the `minmax(0, ...)` the desktop rules use - and `1fr` means `minmax(auto, 1fr)`, whose `auto` minimum is the content's min-content, so a wide `<pre>` stretched the track past the viewport. All five single-column overrides now keep `minmax(0, 1fr)`.
- **Why this matters more than the individual fixes**: every one of these passed a green structural gate. This is the concrete evidence for the phase's premise, and it is now pinned by a parametrized mutation test that seeds each defect class back into the fixture and asserts detection.

### WN-3 - OPEN: `em`-relative font sizes are render-verified only

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/scripts/visual_qa_score.py` (`check_font_floor`)
- **Source phase**: v3.16.5 Phase 3, sub-task 3.4
- **Reason it is open**: a fractional `em` resolves against the inherited size, which depends on the cascade and cannot be computed from declarations alone. The check skips such values rather than guessing, so `code{font-size:.92em}` was ungraded until a render measured it at 12.2px. Resolving the cascade statically is a browser's job.
- **Suggested next step**: none in the scorer. This is correctly closed by the render loop the same phase shipped, and the contract now recommends `max(<relative>, <floor>)` for meaning-carrying inline tokens - a construction the checker CAN verify since `min()`/`max()` resolution was added. If a cheap partial guard is ever wanted, resolving `em` against the nearest ancestor rule that declares an absolute size would cover the common case.

### BG-E1 - CLOSED: the render-session errata (E1-E10)

- **Source**: the `## Errata: render-session lessons (2026-08-11)` section of the plan, added by the maintainer after four real render-grade-fix rounds at 2560x1300 and 1920x1080. Binding on the remaining phases; E1-E5 correct already-committed Phase 1-2 artifacts and were executed in an errata pass immediately after Phase 3.
- **Canonical fixture**: the repo-root `nexus-hub-unit-test-workflow.html` was adopted wholesale as the reference implementation (E10). The Phase 1-3 worktree lineage had diverged by ~3291 lines and was discarded; where the scorer and the fixture disagreed, the fixture won.

**What each item required, and what it cost:**

- **E1 (root scaling)** - `references/responsive-typography.md` rule 3 was rewritten from "a per-element clamp scale declared as custom properties" to "scale the ROOT in one declaration". Both failure modes it replaces are recorded: a `clamp()` on `body` never reaches a `rem`-sized child, and per-element clamps cap out independently so a large display renders laptop-sized text no matter how many sizes are bumped.
- **E1's missing corollary, found while executing it** - root scaling does NOTHING below the root clamp's minimum. With `clamp(1rem, 0.5vw + 0.55rem, 1.6rem)` the root pins at 16px for every viewport at or below 1366px, so the canonical fixture carried **14 distinct sub-floor element classes at 1366px** while passing cleanly at the two widths the render session verified. All 14 were fixed (secondary to `.8125rem`, interactive to `.75rem`), and the contract now states the corollary explicitly.
- **E2 (fractional columns)** - rule 2's example became `minmax(0, 2fr) minmax(16rem, 1fr)` with notes adjacent to prose, and the precedence is stated: on wide screens filling the window beats line-length caps, and the 45-85ch measure is for single-column prose only.
- **E3 (the scorer's root assumption)** - `root_font_px()` parses the `html` font-size and every rem/ch value resolves against it. This retired **16 false font-floor positives** on the reference fixture and turned the full-width band math honest: the real gutter at 1920px is 50.6px, not 44px, so the band is 0.947 and not the 0.954 the old math reported. The scorer's numbers were then verified against a live render at 2560 / 1920 / 1366 and agree to four decimal places. A consequence handled at the same time: `rem` macro spacing IS fluid under a fluid root, so flagging it would penalise the technique E1 prescribes.
- **E4 (no rotated labels)** - rotation is now stated as a readability defect with the horizontal + `tspan` replacement, plus a Verification item and a rationalization row. Phase 2 had taught rotation as the fix for a label/path collision.
- **E5 (three render-only defects)** - documented as rule 7 and given a deterministic check (`render-only-defects`): at most one sticky layer per offset, `scroll-margin-top` on anchor targets under a sticky layer, and command blocks that wrap or scroll. Each direction is tested, including the near-misses (an offset second layer is accepted; a scrolling `pre` is accepted; the anchor rule is quiet with nothing pinned).
- **E6-E8 (capture protocol)** - instant scroll with a settle wait (a mid-animation frame nearly shipped a wrong diagnosis), a REQUIRED 2560x1300 capture, and computed-metric probes per iteration. The rubric now explains why BOTH ends of the viewport range are mandatory: the widest is where root scaling is fully engaged, the 1366 leg is where the root clamp pins and the floors bite.
- **E9 (two authoring rules)** - key-value cells as bullet lists with concrete example values, and neutral interactive-control colors distinct from chart data series.
- **E10** - noted: Playwright and chromium were already present, so the fixture work became verification rather than fixing.

**Fixed in the canonical fixture during this pass** (per maintainer note 3 - fix the page, never relax the check): the 14 sub-floor classes; the `code` element's `.9em` floored with `max(.9em, 0.8125rem)`, which a render caught at 12.53px and no parser can resolve (WN-3); the gutter cap tightened `2.75rem -> 2.6rem` so the full-width contract holds at the scaled root (0.947 -> 0.950); and `#mOn`, a marker defined for the highlighted flow state but never referenced, wired via `.flow.on{marker-end:url(#mOn)}` - without it the accent-stroked connector kept the dim arrowhead, which is the same non-inheritance trap Phase 2 documented.

**Fixed in the CHECK, because the fixture was right** (maintainer note 1): `svg-viewport-fit` demanded a literal `max-height`, but the fixture uses `height: calc(100vh - 7.5rem); width: auto; max-width: 100%` - which pins the graphic to its slot AND prevents the horizontal overflow that deriving width from a capped height can cause. It is the better construction, so the check now accepts either form and rule 4 documents the preferred one.

**Nothing deferred.** The E7 2560x1300 capture surfaced no new defects on the canonical fixture: no horizontal overflow, two sticky layers at distinct offsets, every anchor target carrying `scroll-margin-top`, and 0 of 5 `pre` blocks clipping.

### NI-4 - OPEN by design: the intake questions themselves are agent behavior

- **Target files**: `catalog/skills/specialized-domains/document-to-interactive-html/SKILL.md` (Steps 2 and 5), `catalog/commands/presentify.md`
- **Source phase**: v3.16.5 Phase 4, sub-tasks 4.1 and 4.2
- **Reason it is open**: asking a four-option question, and proposing three color schemes that are genuinely derived from the extracted content with a citable signal for each, are LLM-native behaviors. No unit test can assert that a proposed scheme is relevant to a document, only that the instruction to make it relevant exists. What IS deterministic is now tested: both surfaces agree on the four option values, the legacy aliases are documented on both, the `none` semantic change is disclosed, Round 2 sits between figure classification and authoring in pipeline order, the skips are documented, the diagram shows both rounds, and `design_seed.py --scheme-hint` provably pins the palette while the sampler keeps rolling.
- **Suggested next step**: none in the scorer. The visual half is already graded by the Phase 3 render loop (a scheme that clashes shows up in a screenshot), and the design record captures the offered schemes, the cited signals, and the choice, so a reviewer can audit the reasoning after the fact. Do not build a relevance parser; there is no defect to point at.

### DF-2 - ACCEPTED: `--images none` changed meaning, deliberately and visibly

- **Target files**: both intake surfaces
- **Source phase**: v3.16.5 Phase 4, sub-task 4.1
- **What changed**: pre-v3.16.5, `--images none` meant "typography / layout / color only, no visuals at all". Procedural visuals are now the always-on baseline, so that mode no longer exists and `none` means "nothing ADDED on top of the procedural layer". A user who passes `none` expecting a bare page now gets the procedural visual layer.
- **Why it is accepted rather than avoided**: the alternative is a fifth option (`bare`) that exists only to preserve a mode the plan deliberately removed - R8 makes procedural the baseline precisely because a page with no visuals at all is not an outcome worth offering. The change is disclosed in both surfaces with the words "no longer exists", and a test asserts that disclosure so it cannot be quietly dropped later.
- **Residual risk**: a saved command line still runs and still produces a good page; it just produces a slightly richer one than before. No error, no silent data loss.

### NI-5 - OPEN by design: placement RELEVANCE is a screenshot judgment

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/references/visual-qa-rubric.md` (criterion 4, the AGENT-VISION half)
- **Source phase**: v3.16.5 Phase 5, sub-tasks 5.1 and 5.2
- **Reason it is open**: whether an image actually depicts a section's subject is not decidable from markup. A `data:` URI is opaque bytes; the check can confirm an asset exists, that the record accounts for it, and that the record does not contradict the page, but not that the picture is of the right thing. That judgment stays with the agent looking at the rendered page, which is where the plan put it.
- **What IS deterministic, and why it is enough to close v3.15 MT-2**: the placement RECORD. A consented run must write an `IMAGERY PLACEMENTS` block with one decision per section, and the checker fails a run that embedded assets but left no decision trail, a record claiming more embedded assets than the page contains, or a decline with no reason. That converts "the agent should integrate or explain" from an instruction into a checkable artifact - the thing MT-2 was actually missing. A skip is now distinguishable from a miss.
- **Suggested next step**: none. Do not attempt image-content analysis; it would need a vision model inside a stdlib-only offline scorer, and the render loop already has vision available at exactly the moment the judgment is needed.

### WN-4 - OPEN: a background scrim below ~75% opacity defeats the static contrast check

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/references/interactive-features.md` (the background overlay recipe)
- **Source phase**: v3.16.5 Phase 5, sub-task 5.1
- **Reason it is open**: the `contrast` check certifies text against a DECLARED background color. A background-role image with a scrim over it composites to a per-pixel background, so the check's premise only holds while the scrim is opaque enough to dominate. The recipe mandates ~82%, at which the composited result is within a couple of percent of `--base` and the existing check stays valid. Below roughly 75% it no longer is, and no static check can certify the text.
- **Why it is a warning rather than a check**: the scorer cannot tell which `--base`-ish color a given band composites to without rendering, and the threshold is a judgment about how much image show-through is acceptable rather than a boundary with a right answer. The contract states the number and the reason, the rubric assigns the composited-contrast judgment to the AGENT-VISION half, and a rationalization row rebuts "it looks readable to me".
- **Suggested next step**: if a future page needs a lighter scrim, the contract's answer is to move the text off the image rather than to lower the threshold. A rendered check is possible in principle (sample the composited pixels behind the text box) and would belong in the Phase 3 loop, not the static scorer - only worth building if a real page pushes on it.

### DF-3 - DEFERRED with a reason: the local knockout helper is NOT adopted

- **Decision required by**: v3.16.5 Phase 6 sub-task 6.3, which explicitly says to decide the optional local knockout helper and, if out of scope, "record an explicit DEFER - no half-wired orphan".
- **What it would have been**: `scripts/knockout_background.py`, a local PIL flood-fill that makes a still's border-connected background transparent, for diorama-style floating subjects in a cinematic scene. The upstream pack ships an equivalent; it is genuinely local, needs no network, and Pillow is already a lazy-imported dependency elsewhere in this bundle, so the dependency is not the obstacle.
- **Why DEFERRED**: there is no call site. The cinematic path this phase built consumes clips and stills the user supplies or that the existing Tier 1 / 2 / 3 imagery paths produce; nothing in the engine, the protocol, or the intake asks for a background-knocked-out still. Adding the script now would ship a module that no shipped behavior invokes, which is exactly what the AGENTS.md scope-fit gate declines: "if the only justification is an uncommitted future runner, a design note, or a hypothetical extension with no validation contract, keep the design in docs or todo state until the real call site appears." A diorama look is a design possibility, not a committed feature.
- **Suggested next step**: adopt it the same cycle a cinematic scene composition genuinely needs floating subjects - that is when the call site exists and a test can assert something real about it. Roughly 40 lines plus a lazy Pillow import and a fixture. Until then the absence is the correct state, and this entry is the record so a later reader does not mistake it for an oversight.

### DF-4 - CORRECTED: the plan contradicted itself about naming the upstream project

- **Source phase**: v3.16.5 Phase 6, sub-tasks 6.3 and 6.4
- **The contradiction**: 6.3 instructs "State explicitly there is no separate `/scroll-world` command", while 6.4 requires a grep of `catalog/` for `Monid|Higgsfield|Seedance|scroll-world` to return ZERO. Following 6.3 literally makes 6.4 fail, in a distributed artifact, by naming the upstream repository.
- **How it was resolved**: the AGENTS.md Reverse-Engineering Attribution Rule is the binding authority - the upstream repo, product, or author must not appear in a user-facing artifact - so 6.4's gate wins and 6.3's INTENT was satisfied without the name. `references/scroll-scrub.md` now reads "There is no separate cinematic command and no separate cinematic skill - no rival slash command exists or should be created for this." The point 6.3 wanted made (no competing command, cinematic is a level of `/presentify`) is made in full; only the vendor name is gone.
- **Why it is recorded**: the first draft DID name it, and only the mechanical grep caught it. A parametrized test (`test_no_vendor_name_reaches_a_distributed_artifact`) now checks the engine, the protocol, `interactive-features.md`, `SKILL.md`, and the command file, so the next helpful sentence cannot reintroduce it. Attribution lives in `docs/policy/mcp-reverse-engineering-matrix.md` only.

### BG-3 - CLOSED in Phase 6: `image-sizing` fired on a data URI anywhere in the file

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/scripts/visual_qa_score.py`
- **Source phase**: v3.16.5 Phase 6, sub-task 6.4 (found by running one cinematic build through the loop, which is what that sub-task exists for)
- **What was wrong**: the check treated `"data:image" in html` as evidence of a figure, so it demanded the Phase 2 caps (`max-height: 80vh`, `object-fit: contain`) on any page containing an embedded image anywhere - including inside an inline `<script>` config. A cinematic page keeps its stills in that config and builds its layers at runtime, so the static file has no `<img>` at all and there is no figure box to cap. Every cinematic build failed for a missing cap on a figure it did not have.
- **Resolution**: the caps now require a real figure box - a `<figure>`, or an `<img>` with a `data:` URI that is not a cinematic stage layer. A page with embedded image data but no figure box is graded n/a with that reason stated. A stage layer is separately exempt on its merits: it is a decorative `aria-hidden` full-bleed backdrop, and `object-fit: cover` is CORRECT for it, since `contain` would letterbox the stage and defeat the level.

### v3.16.5 Phase 7 - TERMINAL reconciliation (2026-08-11)

Every v3.16.5 item, with a verdict. Nothing is left implicit, and nothing gates the release.

**Closed this phase (1)**

- **MT-1** - the calibration fixture is homed at `tests/fixtures/presentify/` and guarded by three standing tests plus a CI scoring step. See above.

**Closed in earlier phases (7)** - recorded here so a reader does not have to reconstruct the set: DF-1 (parser media-scope, accepted and documented), BG-1 (five sub-AA runtime accents), BG-2 (three rendered font-floor violations plus the mobile overflow regression), BG-E1 (the ten render-session errata, nothing deferred), BG-3 (`image-sizing` firing on any embedded data URI, which would have failed every cinematic build), DF-4 (the plan's own naming contradiction, resolved in favour of the Attribution Rule), and - in `docs/v3/v3.15/known-gaps.md` - **v3.15 MT-1** (the headless render now runs in CI) and **v3.15 MT-2** (the placement record makes a skip distinguishable from a miss). Both v3.15 closure notes were verified present and appended rather than rewritten.

**Carried, by design, with a stated reason and next step (7)**

| Item | Why it stays open | Where it is actually answered |
|---|---|---|
| **NI-2** | Typography rule 2 (prose stranded beside dead space) is a rendered-geometry judgment: it depends on resolved track widths and the real `ch` width of the chosen font. Rule 3's half was superseded by errata E1 and is now partially enforced (a malformed step token IS caught, since the scorer resolves `var()`). | The Phase 3 render loop grades rule 2 from screenshots. Do not build a geometry parser. |
| **NI-3** | SVG rules 2 (dash/label collision) and 3 (connectors on node edges) need glyph metrics and a declared join intent the markup does not carry. Verified numerically per-diagram instead. | Phase 3's screenshots catch a label sitting on a line immediately; rule 3 stays an authoring discipline enforced by the rule-5 self-check. |
| **NI-4** | The intake questions are agent behavior. No test can assert a proposed colour scheme is *relevant* to a document, only that the instruction to make it relevant exists. | The deterministic half IS tested (option agreement across both surfaces, aliases, pipeline order, skips, the diagram, and `--scheme-hint` behavior); the visual half is graded by the render loop. |
| **NI-5** | Placement relevance is a screenshot judgment - a `data:` URI is opaque bytes. | The render loop has vision at exactly the moment the judgment is needed. Do NOT build image analysis into a stdlib-only offline scorer. |
| **WN-1** | A semantic status colour's applicable WCAG floor depends on its rendered size (3:1 for large or bordered badge text, 4.5:1 for body), which a parser cannot know. Grading them all at 4.5:1 would produce false failures that teach authors to bypass the gate. | Rubric criterion 7's agent-vision half, where rendered size is observable. |
| **WN-3** | A fractional `em` resolves against the inherited size and cannot be computed from declarations alone. | Closed in practice by the contract's `max(<relative>, <floor>)` recommendation - a construction the checker CAN verify now that `min()`/`max()` resolution exists - plus the render loop. |
| **WN-4** | The `contrast` check certifies text against a DECLARED background; a background-role image with a scrim composites per-pixel, so the check's premise holds only while the scrim dominates (~82%). The threshold is a judgment about acceptable show-through, not a boundary with a right answer. | Rubric criterion 4's agent-vision half. If a page ever needs a lighter scrim, the contract's answer is to move the text off the image, not to lower the threshold. |

**Accepted or deferred with a decision (2)**

- **DF-2** - `--images none` changed meaning (it used to mean "no visuals at all"). Accepted: the alternative was a fifth `bare` option preserving a mode R8 deliberately removed. Disclosed in both surfaces with the words "no longer exists", and a test asserts that disclosure so a later edit cannot quietly drop it.
- **DF-3** - the local knockout helper is NOT adopted, because no call site exists. The AGENTS.md scope-fit gate declines a module justified only by a hypothetical extension; Pillow already being available was never the obstacle. Adopt it the cycle a cinematic scene genuinely needs floating subjects, which is when a test can assert something real.

**Pattern worth carrying forward.** Six of the seven carried items are the same shape: a static parser reaching the edge of what markup can tell it, with the answer sitting in the render loop rather than in more parsing. That is not a backlog - it is the correct division of labour, and the phase that made it correct was Phase 3. The one lesson to keep is the asymmetry BG-2 exposed: a false PASS is far more expensive than a false FAIL. Sixteen false failures were loud and fixed within the hour; one false pass (a band fraction inflated across its own threshold) sat inside a green run for two phases and would have shipped.

**Release-blocker check: NONE.** No open item blocks v3.16.5.

### v3.16.5 Phase 1-7 summary

| Category | Open | Resolved |
|---|---|---|
| v3.16.5 Phase 1 gaps | 3 (MT-1 fixture unhomed and unguarded; NI-2 typography rules 2-3 by design; WN-1 status-color exclusion) | 1 accepted-and-documented (DF-1 parser scope) |
| v3.16.5 Phase 2 gaps | 2 (WN-2 runtime-injected palette invisible to the scorer; NI-3 SVG rules 2-3 by design) | 1 closed (BG-1 sub-AA runtime accents) |
| v3.16.5 errata pass (E1-E10) | 0 | 1 closed (BG-E1: all ten items executed; 14 sub-floor classes, the gutter, the `code` em-size and an unwired marker fixed in the fixture; the viewport-fit check widened where the fixture was right; nothing deferred) |
| v3.16.5 Phase 7 gaps (TERMINAL reconciliation) | 0 new; 7 carried by design with a stated reason and next step (NI-2, NI-3, NI-4, NI-5, WN-1, WN-3, WN-4) and 2 accepted-or-deferred with a decision (DF-2, DF-3) | 1 closed (MT-1: fixture homed at `tests/fixtures/presentify/` and guarded by 3 tests + a CI step) |
| v3.16.5 Phase 6 gaps | 2 (DF-3 knockout helper deferred, no call site; DF-4 the plan's own naming contradiction, corrected) | 1 closed (BG-3 `image-sizing` fired on any embedded data URI, breaking every cinematic build) |
| v3.16.5 Phase 5 gaps | 2 (NI-5 placement relevance is a screenshot judgment, by design; WN-4 the scrim-opacity floor below which no static contrast check holds) | 1 closed (**v3.15 MT-2**: the placement record makes a skip distinguishable from a miss) |
| v3.16.5 Phase 4 gaps | 2 (NI-4 intake questions are agent behavior, by design; DF-2 the `none` semantic change, accepted and disclosed) | 0 |
| v3.16.5 Phase 3 gaps | 1 (WN-3 `em`-relative sizes render-verified only) | 3 closed (BG-2 three rendered floor violations + the mobile overflow regression; **v3.15 MT-1** headless render in CI; **v3.15 MT-2** superseded by the placement pass Phase 5 owns) |

None is a release blocker, and two of the three (NI-2, WN-1) are deliberately routed to Phase 3, which is the phase that acquires the rendered screenshots those judgments require. MT-1 is routed to Phase 7, which already owns the fixture's final location; Phase 1 committed the fixture at the repo root so its fixes are not at risk while that decision waits. Phase 3 settles the argument the first two phases kept making. Every one of Phase 1's and Phase 2's routed items was the same shape - a static parser at the limit of what markup can tell it - and a single render pass closed or superseded four of them while finding four defects that had passed a green structural gate: a 12.48px brand label misclassified as interactive, 12.2px emphasis tokens the checker explicitly declined to judge, an 11.52px inline style it could not see, and a 390px horizontal overflow that Phase 2's own viewport-fit fix had introduced. Two of those four were bugs in the checker rather than in the page. The lesson is not that the scorer is bad - it is that a parser and a renderer answer different questions, and shipping only the parser means shipping the difference.

Phase 2 repeats the pattern and sharpens it. Its most valuable finding was again invisible to the phase that should have owned it: BG-1's five sub-AA accents are injected by script, so Phase 1's contrast check could not observe them and passed truthfully on an incomplete view. Two of Phase 2's three new items (WN-2, NI-3) are the same shape - a static parser reaching the edge of what markup can tell it - and both route to Phase 3, where a rendered screenshot answers directly what no amount of extra parsing would. That is an argument for building Phase 3 rather than for deepening the scorer.

Worth noting from Phase 1: the most valuable defect that phase found was not in the fixture but in the checker - the `font-floor` check initially skipped every `var()` value, so tokenizing the fixture DROPPED its checked font count from 40 to 17. A linter that verifies the non-compliant form more thoroughly than the compliant one rewards the wrong behavior, and nothing in the plan would have surfaced it; only running the checker before and after the fix did.

## v3.16.6 - presentify-verbosity-intake

**Status**: COMPLETE and reconciled (Phase 2 TERMINAL 2026-08-12, plus one release-flow finding). Both phases done and merged to `develop`; 2 carried (NI-1 by design; WN-1 the manifest-generator environment dependence, routed onward), 3 closed (DF-1, QG-1, BG-1), 0 release blockers. Plan: [plans/v3.16.6-presentify-verbosity-intake.md](plans/v3.16.6-presentify-verbosity-intake.md).

### NI-1 - OPEN by design: the verbosity contract is agent behavior with no deterministic check

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/SKILL.md` (Step 5 round-2 question, Step 6 depth rules) and `references/visual-qa-rubric.md` (criterion 10)
- **Source phase**: v3.16.6 Phase 1, sub-tasks 1.1-1.3
- **Plan reference**: sub-task 1.3 forbids deterministic scorer checks outright ("maintainer decision 2026-08-11: word / section-count bands are crude and false-positive; enforcement is record + rubric only")
- **Reason it is open**: whether a page's depth matches its declared level is a structure-vs-content judgment (which topics count as "major", whether a section is appendix-grade), not a countable property. Criterion 10 is AGENT-VISION only and page-level, graded against the design record's recorded level and section-count target. This mirrors v3.16.5's NI-4 (intake questions are agent behavior) and is the same shape as its NI-2/NI-3 family: a judgment the render loop answers and a parser cannot.
- **Suggested next step**: none scheduled - by design. Revisit ONLY if a shipped page plainly contradicts its recorded level AND the rubric criterion missed it; that concrete defect would justify the cheap partial guard (comparing the rendered top-level section count against the recorded target band), which was considered and rejected absent a defect to point at.

### DF-1 - CLOSED in Phase 2: the v3.16.5 deferral was never recorded in this file

- **Target file**: this file (the v3.16.5 subsection above)
- **Source phase**: v3.16.6 Phase 1 (discovered during the Phase 8 known-gaps append)
- **Reason**: the v3.16.6 plan's Origin note says the verbosity axis was "deferred from v3.16.5 by maintainer decision 2026-08-11" and its sub-task 2.2 expects to close "the v3.16.5-deferred entry" - but the v3.16.5 Phase 7 reconciliation (same date) never wrote that entry, so there is no entry to close. The deferral decision is real (it is recorded in the v3.16.6 plan header and in the maintainer conversation); only its known-gaps bookkeeping was skipped.
- **Suggested next step**: Phase 2 sub-task 2.2 closes the deferral by reference to THIS note instead of a v3.16.5 entry; no retroactive edit to the finalized v3.16.5 subsection.
- **CLOSED 2026-08-12 by v3.16.6 Phase 2** (the reconciliation this entry asked for): the deferred work itself shipped in Phase 1 (the coverage-depth axis is live on all three surfaces), so the deferral is fulfilled, and this note IS its bookkeeping record - the missing v3.16.5 entry is documented here rather than written retroactively into a finalized section. Nothing remains to transfer.

### BG-1 - CLOSED at release (checker gap OPEN as WN-1): the shipped v3.16.5 manifest hashed CRLF bytes

- **Target file**: `MANIFEST.sha256` (fixed), `scripts/generate_manifest.py` (the open checker half)
- **Source phase**: v3.16.6 release flow (found when the routine manifest regeneration diffed 520 entries instead of the ~5 the release touched)
- **What was wrong**: the v3.16.5 release was cut in a Windows worktree where ~520 catalog files materialized with CRLF endings, and `generate_manifest.py` hashes working-tree bytes - so the SHIPPED v3.16.5 manifest recorded CRLF hashes that do not match the LF bytes a GitHub-tarball install materializes. `nexus-hub verify` against a clean v3.16.5 install would have reported ~520 spurious mismatches. Verified precisely: for a spot-checked file the old manifest entry equals the sha256 of the blob's CRLF conversion, and the new entry equals the blob's own sha256.
- **Resolution (the data half)**: the v3.16.6 manifest is regenerated over LF bytes matching the committed blobs, so `verify` works against tarball installs again.
- **WN-1 - OPEN (the checker half)**: `generate_manifest.py` remains generation-environment-dependent; cutting a release from a CRLF-materialized tree would reintroduce the defect silently. Suggested next step: newline-normalize text files (or hash committed blob bytes via `git cat-file`) in the generator, plus a one-entry self-check comparing a known file's manifest hash against its blob hash. Route to the next cycle that touches `scripts/`.

### QG-1 - CLOSED in Phase 1: the CI path filter missed the command file the tests assert against

- **Target file**: `.github/workflows/presentify-extractor.yml` (both `paths:` lists)
- **Source phase**: v3.16.6 Phase 1, Phase 8 CI readiness check (pre-existing since v3.16.5 Phase 4)
- **What was wrong**: `tests/skills/test_presentify_intake.py` has asserted on `catalog/commands/presentify.md` since v3.16.5 Phase 4, and this phase added more such assertions - but the workflow's path filters did not include the command file, so a command-only edit would merge without running the suite that guards it (the same silent-ungating shape as v3.16.5 MT-1's fixture-move hazard).
- **Resolution**: `catalog/commands/presentify.md` added to both the `push` and `pull_request` path filters (2 lines).

## v3.16.7 - presentify-first-shot-hardening

**Status**: RELEASED 2026-08-13 (tag `v3.16.7`, `main` at `254d124e`, GitHub Release published). Three post-release findings, all from checks that should have run during the release, ALL NOW FIXED in v3.16.8 (branch `feat/v3.16.8-adoption-watermark-hygiene`): `BG-2`, an `eol=crlf` residual in the WN-1 manifest fix found by verifying the published tarball (both halves ingested into the v3.16.8 plan as sub-tasks 1.3 and 2.3); `NI-4`, the process gap that let the model map go 11 days stale because the advisory freshness step was allowed to answer UNKNOWN; and `QG-1` (closed), a capability-gate declaration that read correctly to a human and matched none of the checker's patterns. A full governance audit of all six release steps is recorded at the end of this section. 3 open (NI-2 and NI-3 by design, WN-3 accepted style consistency), 10 closed (BG-1, DF-1, DF-2, NI-1, WN-1, WN-2, QG-1, plus BG-2, NI-4 and the --strict promotion fixed in v3.16.8).

**Prior status line**: RECONCILED, awaiting `/update release`. All four phases shipped (`0dbc170f`, `1b97cdf9`, the Phase 3 commit, and the Phase 4 commit). The Phase 3 intake CLOSED on 2026-08-13 when the VectorCAST-session lessons arrived, and Phase 4 closed the long-carried manifest defect at its root. 3 open (NI-2 and NI-3 by design, WN-3 accepted style consistency), 6 closed (BG-1, DF-1, DF-2, NI-1, WN-1, WN-2). No release blocker remains. Plan: [plans/v3.16.7-presentify-first-shot-hardening.md](plans/v3.16.7-presentify-first-shot-hardening.md).

### BG-1 - CLOSED: `0dbc170f` shipped a UTF-8 BOM that broke the skill's YAML frontmatter

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/SKILL.md`, `tests/skills/test_presentify_intake.py`
- **Source phase**: v3.16.7 Phase 1 (introduced), found by the Phase 2 reverse-engineering audit
- **What was wrong**: both files gained a leading `EF BB BF`. Verified empirically rather than inferred: read with `encoding="utf-8"` (what `validate_skills.py` line 258 uses, NOT `utf-8-sig`), `content.startswith("---")` is False and the frontmatter regex does not match, so the validator's own `parse_frontmatter()` returned `None` and reported "no valid YAML frontmatter (must start with ---)". `scripts/validate_unicode_safety.py` also failed with exit 1, its SINGLE error being that BOM - and that validator runs in `make validate` and in the CI `validate` job, so **CI was red on this branch**. `AGENTS.md` records that the MCP skill server depends on parseable frontmatter, so discovery for the catalog's largest skill was at risk too.
- **Resolution**: both BOMs stripped, files rewritten as UTF-8 without a BOM. `validate_unicode_safety.py` now exits 0 and the frontmatter error is gone. (`validate_skills.py` in FULL mode still reports a 1769-character description for this skill, but that is a pre-existing condition shared by 168 skills and is not run by `make validate`, which invokes `--bundles-only`; it is not this release's regression.)
- **Why it is recorded rather than quietly fixed**: this is the THIRD time the repository has met this trap. `AGENTS.md` documents it twice (the v3.11.0 `session-summary.ps1` parse failure and the v3.15.6 provenance-ledger BOM), and the fix each time was prose. The durable guard already exists - `validate_unicode_safety.py` catches a BOM in any non-`.ps1` text file - so what failed here was running it, not having it. That points at the pre-commit / phase-gate habit rather than at another rule.

### DF-1 - CLOSED: the v3.16.7 slot had no plan artifact

- **Target file**: `docs/v3/v3.16/plans/v3.16.7-presentify-first-shot-hardening.md`
- **Source phase**: v3.16.7 Phase 1 (the work landed before any plan existed)
- **Reason**: Phase 1 was built and committed straight from live-session lessons, so the version had no plan document while every other v3.16.x version has one, and there was no artifact against which "is this version complete" could be answered.
- **Resolution**: the plan was reverse-engineered from `0dbc170f` on 2026-08-13 and carries an explicit provenance note saying so, rather than presenting itself as having preceded the work. It is deliberately left OPEN at Phase 3 so further live-session lessons land inside this release.

### DF-2 - CLOSED: v3.17.0 changelog text landed in this branch's `[Unreleased]`

- **Target file**: `CHANGELOG.md`
- **Source phase**: v3.16.7 Phase 1
- **What was wrong**: `0dbc170f` staged `CHANGELOG.md` while a concurrent session had uncommitted v3.17.0 permission-hardening changelog text in the shared working tree. `[Unreleased]` therefore described permission work whose code is NOT on this branch, and carried a duplicated `### Added` heading. Releasing as-is would have announced unshipped work.
- **Resolution**: the v3.17.0 entries were removed here and preserved on `feat/v3.17.0-agent-autonomy-toggle`, where that code lives; the duplicate heading was merged. Two `v3.17.0` mentions remain in already-released sections as legitimate historical cross-references and were left alone.
- **Lesson**: two agents sharing one working tree is the hazard, not the changelog. A `git add <file>` picks up whatever is in the tree, including another session's work in progress.

### NI-1 - CLOSED: the Phase 3 intake received its lessons and is built

- **Target**: the plan's Phase 3
- **Source phase**: maintainer directive, 2026-08-13
- **Why it was open**: the maintainer was running `/presentify` on another project and expected further first-shot lessons. The plan held Phase 3 open so the whole batch shipped in v3.16.7 rather than half of it, and the intake protocol required each lesson to name an OBSERVED defect, since a guard with no observed defect behind it is declined by the `AGENTS.md` scope-fit rule.
- **Resolution**: the VectorCAST decision-brief session supplied 26 backlog items (`PRES-01` through `PRES-26`) plus five proposed gates on 2026-08-13. The intake closed, six sub-tasks were specified, and all six were built the same day. Every one traces to a defect observed in that session, so the scope-fit bar held without exception.

### NI-2 - OPEN: Gates A, B, and E are agent behavior with no deterministic checker

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/references/visual-qa-rubric.md`, `references/content-intent.md`
- **Source phase**: v3.16.7 Phase 3 (sub-tasks 3.1, 3.3, 3.6)
- **Reason it is open**: `scripts/visual_qa_score.py` can check a `content_intent` block's PRESENCE and shape, but not whether a `scope_class` is the right one, whether an assumption was genuinely accepted, or whether a visual explains its section. Those are judgments, and the same reasoning the maintainer applied to rubric criterion 10 in v3.16.5 applies here: a crude deterministic proxy produces false positives and trains the agent to satisfy the proxy. Enforcement is therefore record plus rubric, exactly as criterion 10 is.
- **Suggested next step**: consider a NARROW structural check for the mechanically-decidable half only, namely the `content_intent` block's presence and field completeness, and the `standalone` banned-phrase scan (a literal string search over visible text, which is decidable). Leave the judgments to the rubric. Do not attempt to score decision coverage.

### NI-3 - OPEN: the composition probes are specified but not implemented in a helper

- **Target file**: `catalog/skills/specialized-domains/document-to-interactive-html/SKILL.md` Step 9
- **Source phase**: v3.16.7 Phase 3 (sub-task 3.5)
- **Reason it is open**: line count, width utilization, one-word orphan detection, rectangle intersection, and per-section density deltas are specified as `page.evaluate()` probes the grading agent writes inline, matching how the existing probes (root size, per-role smallest size, band fraction, `scrollWidth`, painted-canvas) are already specified. No bundled script computes them. That is consistent rather than a shortfall, and the `AGENTS.md` scope-fit gate declines a helper with no call site, but it does mean the probes are as reliable as the agent that writes them each run.
- **Suggested next step**: if a future session finds the probes being skipped or written inconsistently, extract all of them (existing and new) into one bundled `scripts/render_probes.js` the loop injects verbatim. Do that as ONE extraction covering the whole probe set, not a second partial layer.

### WN-2 - CLOSED: two ruff findings in the Phase 1 test module

- **Target file**: `tests/skills/test_presentify_first_shot_hardening.py`
- **Source phase**: v3.16.7 Phase 1 (introduced), observed at the Phase 3 gate, fixed in Phase 4.1
- **What was wrong**: `ruff check` reported two `PLW1510` findings (`subprocess.run` without an explicit `check=`) on the two `fit_map_projection.py` invocation tests. Verified pre-existing at the Phase 3 gate by stashing and re-running against the Phase 1 baseline, then deliberately left alone: the `AGENTS.md` scope rule declines adjacent cleanup inside a feature phase.
- **Resolution**: `check=False` added to both calls in Phase 4, where a cleanliness pass is in scope by definition. The module now reports 0 ruff findings, down from 2.

### WN-3 - OPEN (accepted, style-consistency): `generate_manifest.py` uses legacy `typing` generics

- **Target file**: `scripts/generate_manifest.py`, `tests/validators/test_verify_install.py`
- **Source phase**: v3.16.7 Phase 4.2
- **Reason it is open**: the WN-1 fix added code using `Dict` / `List` / `Tuple` from `typing`, matching the module's existing convention (it already imports and uses them throughout, which is where the 10 baseline findings came from). `ruff` default rules flag these as `UP006` / `UP035` in favor of PEP 585 lowercase generics. Ruff is NOT a CI gate in this repo and no `[tool.ruff]` config exists, so these are advisory findings from an ad-hoc invocation, not a failing check.
- **Why it was not fixed here**: modernizing only the new functions would leave one module written two ways, and modernizing the whole module is an out-of-scope style refactor of release-critical tooling during a release phase. The project rule to write code that reads like the surrounding code points the same way.
- **Suggested next step**: if the repo ever adopts a `[tool.ruff]` config with `UP` enabled, modernize this module in ONE pass rather than incrementally.

### BG-2 - CLOSED in v3.16.8: `eol=crlf` files now hash their distributed form

- **Resolution (2026-08-14)**: `_git_eol_attrs()` batches one `git check-attr --stdin -z eol` over the same path list the `ls-files` pass already built, and `_apply_eol()` converts only paths resolving to `crlf`. Proven end to end: an archive of the index verifies `OK 1231 file(s) match`, `verify: PASS`, up from `1230 OK / 1 MODIFIED / FAIL`. The entry for `scripts/nexus-hub.cmd` now equals `e314f2c6...`, which is the hash measured from the DOWNLOADED v3.16.7 tarball, so the generator models the real artifact rather than the object store.
- **Four regression tests** in `tests/validators/test_verify_install.py`: an `eol=crlf` path hashes the CRLF form while a `text=auto` sibling in the same repo still hashes LF (the mirror guard against a blanket conversion), an explicit `eol=lf` path is untouched, `_apply_eol` is idempotent so converting twice cannot double a CR, and an unspecified path is OMITTED from the attribute map rather than defaulted.
- **A subtlety found while building the proof, now encoded in the release flow**: a LOCAL `git archive` is not a valid stand-in for the published tarball unless it pins `-c core.autocrlf=false -c core.eol=lf`. Without those a Windows host applies CRLF to every `text=auto` file and the check reports ~1180 of 1231 as modified, which looks catastrophic and means nothing. GitHub builds its tarballs on Linux. A path with an EXPLICIT `eol` attribute is host-independent, which is exactly why the generator models the attribute and not the host.
- **Original diagnosis, retained**: see below.

### BG-2 original diagnosis, found POST-RELEASE by verifying the published v3.16.7 tarball

- **Target file**: `scripts/generate_manifest.py`
- **Source phase**: v3.16.7 Phase 4.2 (the WN-1 fix), discovered immediately after publishing by downloading the real release artifact and running `verify_install.py` against it
- **What is wrong**: the WN-1 fix hashes a tracked file's GIT BLOB bytes, which is right for every file whose distributed form is the blob. It is WRONG for a file carrying an explicit `eol=crlf` attribute, because `git archive` (and therefore the GitHub tarball) applies that conversion, so the distributed bytes are CRLF while the blob is LF. `.gitattributes` declares `scripts/nexus-hub.cmd text eol=crlf` (deliberately, so the Windows launcher ships with CRLF), and it is the ONLY such file in the covered roots (`git check-attr eol` over `catalog templates scripts data` returns exactly one `eol: crlf`).
- **Measured impact**: verifying the published `Nexus-Hub-3.16.7.tar.gz` reports `OK 1230 file(s) match` and `MODIFIED scripts/nexus-hub.cmd`, verdict `FAIL (1 modified, 0 missing, 0 extra)`. Confirmed by hash: the blob has 0 CRLF and hashes `ae471239...`, the tarball copy hashes `e314f2c6...`.
- **Honest framing**: this is a large net improvement, not a regression. Before the fix the same check would have reported roughly 678 mismatches (every text file); it now reports one. But `nexus-hub verify` returns FAIL on any modification, so a user running it against a clean v3.16.7 install still sees FAIL, and that is a real user-facing defect rather than a cosmetic one.
- **Why it was not caught earlier**: the Phase 4 verification hashed against the INDEX and sampled 8 entries, all of which happened to be ordinary text files. The defect only appears when the check is run against the actual distributed artifact, which is why downloading the published tarball was worth doing and should become the standard last step of a release.
- **Suggested fix**: in `_git_blob_sha256`, batch `git check-attr eol` over the same path list and, for any path resolving to `eol: crlf`, convert LF to CRLF before hashing. An `eol: lf` path needs nothing (the blob is already LF). The more thorough alternative is to hash `git archive` output directly, which is by definition the distributed artifact; prefer that only if more attribute classes appear, since it is more machinery for one file today.
- **Suggested process fix**: add the tarball round-trip (download the published archive, run `verify_install.py`, expect `PASS`) to the release flow as the final gate, so a manifest defect is caught by the release rather than by a user.

### NI-4 - CLOSED in v3.16.8: the release flow let the model map go 11 days stale by accepting UNKNOWN

- **Target files**: `catalog/commands/update.md` (release governance step 5), `catalog/skills/ai-development/model-routing/references/last-known-model-map.json`
- **Source phase**: v3.16.7 Phase 4 / `/update release`, raised by the maintainer immediately after the release
- **What went wrong**: governance step 5 runs `check_model_prompting_freshness.py --advisory`, which is correctly non-blocking. During this release it returned `UNKNOWN: no live roster supplied, so drift cannot be determined`, and that was recorded as a documented degradation and passed over. Accepting UNKNOWN is not the same as checking. The step is designed to take an enumerated roster; nothing enumerated one, so nothing was actually verified, and `last-known-model-map.json` sat at `2026-08-03` across two releases (v3.16.6 and v3.16.7) while the release notes were being written.
- **What the deferred check would have caught, confirmed by doing it 2026-08-14**: `gemini-3.7-flash` shipped 2026-08-13 with substantial agentic and coding improvements and was absent from the map; Cursor now offers Grok 4.6 while the map named 4.5; the map's OpenAI `standard` value `gpt-5.5` is not in the current API model list. Separately, the v3.16.8 plan's own inline map (written 2026-08-13 and labeled "fresh") carried `gemini-2.5-flash` at `standard`, two generations behind, and disagreed with the reference JSON on two tiers. Anthropic was the only provider with no drift.
- **Resolution so far**: both artifacts refreshed from live first-party documentation on 2026-08-14 and reconciled with each other; `test_model_routing_map.py` green; the helper's own validator reports `{"valid": true, "verified_as_of": "2026-08-14"}`. The judgment calls (Gemini Flash overtaking a Pro-preview id at `frontier`, no observed `grok-4.6-high`, `terra` covering two OpenAI tiers) are recorded inline in both files rather than presented as fact.
- **CLOSED in v3.16.8 (2026-08-14)**: governance step 5 in `catalog/commands/update.md` now states that non-blocking is not the same as skippable. It requires the roster to be ENUMERATED and passed to the checker before the step may report, declares IN SYNC and DRIFTED the only acceptable terminal verdicts (UNKNOWN only when web access genuinely failed, and then recorded WITH that reason), and names the model map as a SEPARATE artifact that nothing else in the release flow refreshes, with the v3.16.7 evidence that the profile layer was IN SYNC while the map sat 11 days stale. Both remain non-blocking on the release; what changed is that the step must now produce a verdict rather than a shrug.
- **Verified**: run with the roster enumerated, the check reports `IN SYNC: 4 model(s) match the live roster`. The 41 tests asserting on the release-flow contract text (`test_release_staleness_step.py`, `test_check_release_capability_docs.py`) still pass, so the hardening did not break the advisory-by-design contract those tests protect.

### QG-1 - CLOSED: the capability-gate no-change declaration was mechanically invisible (checker promoted to --strict in v3.16.8)

- **Target file**: `CHANGELOG.md` (the `[3.16.7]` section), and the published GitHub Release body
- **Source phase**: `/update release` governance step 6, found by the post-release governance audit (2026-08-14)
- **What was wrong**: the declaration read "This release introduces no NEW opt-in capability, installer flag, env-var-gated surface, or managed skill." Semantically exact, and invisible to `scripts/check_release_capability_docs.py`, whose `NO_CHANGE_PATTERNS` match `no opt-in (capability|surface)` or `changes? no opt-in`. The single word "new" sits between `no` and `opt-in` and breaks every pattern, so the checker reported `FAIL: no explicit no-change declaration found`, which is its way of saying "this release looks unchecked".
- **Why it matters more than a wording nit**: the gate exists precisely to distinguish "checked and none applied" from "never checked", and the script's own comment says a false CLEAR is the failure it is built to prevent. A declaration that satisfies a human reader and fails the machine leaves the release in the same evidentiary state as one where the gate was skipped.
- **Root cause of the miss**: the mechanical companion was never run. Governance step 6 offers `check_release_capability_docs.py` as advisory support, and I wrote the declaration by hand and did not invoke it. Advisory tooling that is not run provides no signal.
- **Resolution**: reworded to "This release changes no opt-in capability, ..." which matches pattern 2. Verified with `--strict` (the promoted hard-gate mode), not just the default advisory mode: `OK ... explicit no-change declaration present`, exit 0. The published GitHub Release body was updated in place with `gh release edit` so the shipped artifact carries the same corrected text.
- **DONE in v3.16.8**: the checker is now MANDATORY and runs with `--strict` in governance step 6, which is the promotion condition the command file already stated and which this omission met. The step also now names the accepted no-change wordings verbatim, so an author does not have to reverse-engineer the patterns from the script, and says to extract the notes from the finalized CHANGELOG section so the check grades what actually ships.

### Phase 4.1 audit record (verified, not assumed)

### Post-release governance audit (2026-08-14, maintainer-requested)

Every `/update release` requirement re-checked against what was actually executed. Recorded because two gaps were found by asking rather than by the flow.

| Requirement | Verdict |
|---|---|
| docs: headline counts | PASS. 271 skills / 17 commands (+3 aliases) / 31 hooks (33 files less two shared `_` libraries) / 23 agents, all verified against the registries, no drift. |
| docs: internal MCP server list | PASS. 4 `nexus-*` servers, count and names verified. |
| docs: "What's New" narrative | PASS. v3.16.7 section added. |
| docs: removed / renamed surfaces | PASS (verified late). `git diff --diff-filter=DR` over `catalog/` and `scripts/` across the release range returns nothing, so no doc can be presenting a removed surface as current. |
| docs: per-version tree | PASS. `docs/v3/v3.16/` with `plans/` and `comparisons/`. |
| devlog | PASS (no-op). No `DEVLOG.md` in this repo. |
| gitignore: patterns + tracked index | PASS. 0 patterns needed, no tracked `__pycache__`. |
| gitignore: LFS recommendation | PASS (verified late). No tracked file exceeds 5 MB, so there is no LFS candidate. |
| version: atomic bump | PASS. All 7 surfaces, guard clean before and after. |
| changelog | PASS. `[Unreleased]` finalized to `[3.16.7]`. |
| refactor: whole-docs-tree canonicalization | PASS (verified late). `docs/` already holds only `docs/v3/v3.<minor>/`, and the archive is already `docs/archive/v<major>/v<major>.<minor>/`. No migration was needed, which is why not running `--canonicalize-layout` explicitly cost nothing here. |
| refactor: project cleanliness detectors | PASS. Run in Phase 4.1. |
| Step 1: known-gaps reconciliation | PASS. |
| Step 2: full architecture refactor | PASS. |
| Step 3: CI/CD covers + optimized | PASS. All 16 changed files covered; optimizations already present. |
| Step 4: platform read-contract (HARD gate) | PASS. Re-verified and re-stamped for v3.16.7; both `check_platform_contract_freshness.py` and `verify_platform_contracts.py` green. |
| Step 5: prompting-profile staleness (advisory) | **INITIALLY MISSED, now PASS.** Accepted `UNKNOWN` during the release; re-run with the roster enumerated returns `IN SYNC: 4 model(s) match the live roster`. Tracked as `NI-4` for the process half. Note the distinction that caused the confusion: this step grades `profiles-index.json`, which is a DIFFERENT artifact from `last-known-model-map.json`. The map was genuinely stale; the profile layer was not. |
| Step 6: capability usage gate | **INITIALLY FAILED mechanically, now PASS.** See `QG-1`; the declaration was correct prose that matched no pattern, and the advisory checker was never run. |
| Supply-chain manifest | PARTIAL. Regenerated after the bump and before the commit as required, and 8/8 sampled entries matched their blobs, but the artifact itself was wrong for one file: see `BG-2`. |
| GitHub Release publishing | PASS. Published from the changelog section, marked Latest, backfill checked (releases tracked tags through v3.16.6), body later updated for `QG-1`. |

**The pattern across all three misses is the same**: every one was a step with a runnable mechanical companion that was not run (`check_model_prompting_freshness.py` with a roster, `check_release_capability_docs.py`, and verification against the real tarball). None was a missing requirement in the command file. The requirements were adequate; execution substituted judgment for the available check.

The plan required these be recorded rather than presumed:

- **Orphan-bundle rule**: all 21 files under the presentify skill's `scripts/` / `references/` / `assets/` are referenced from `SKILL.md`, including the new `content-intent.md`. `validate_skills.py --bundles-only` PASS across 271 skills, 0 warnings.
- **Installer registration is NOT required for the new reference**: verified by reading the code path rather than trusting the rule. Neither installer names any per-skill bundled file (`grep` for `fit_map_projection` / `content-intent` / `visual_qa_score` returns 0 hits in `installer.sh` and `installer.ps1`). Distribution runs through `scripts/lib/integrations/base.py`, whose `_copy_tree` calls `shutil.copytree(src, dst, dirs_exist_ok=True)` over `catalog/skills` (line 804), so the whole tree ships. Only repo-level `scripts/<name>.py` needs the explicit-name copy step. `test_installer_smoke.py`: 33 passed.
- **Refactor detectors**: no tracked `__pycache__`; root files are all legitimate governance artifacts plus the documented `install.sh` bootstrap. Four empty directories exist (`.antigravitycli`, `.claude/worktrees`, `docs/v3/v3.17/development/history`, `docs/v3/v3.20/comparisons`); the two under `docs/` are scaffolding for OTHER versions' cycles and are left alone as out of this release's scope.
- **CI/CD**: every one of the 16 files changed across `develop..HEAD` is covered. `catalog/**`, `tests/skills/**`, and `CHANGELOG.md` reach `ci.yml` (whose `paths` is `**` minus `docs/**`) and the presentify surfaces additionally reach `presentify-extractor.yml`; `docs/**` reaches `doc-colocation.yml`. The session-history file is deliberately outside `ci.yml`'s re-included docs patterns, which is the documented intent (frozen records no test reads). No workflow edit was needed, and the presentify workflow already carries path filters, concurrency cancel-in-progress, pip caching, and a merge-gated render job.
- **Prompting-profile staleness (advisory, 9.0 step 4)**: `check_model_prompting_freshness.py --advisory` returns UNKNOWN because no live roster was enumerated in this session. That is its documented degradation and it never blocks. Recorded roster last verified 2026-07-27.
- **Platform read-contract**: `check_platform_contract_freshness.py` OK for v3.16.6. It hard-gates on the version being cut, so `/update release` must re-verify and re-stamp it for v3.16.7.

### WN-1 - CLOSED (carried from v3.16.6, root-caused here): `generate_manifest.py` hashed working-tree bytes

- **Target file**: `scripts/generate_manifest.py`
- **Source phase**: carried into v3.16.7 because this release touches `scripts/`; fixed in Phase 4.2
- **What was wrong**: the generator hashed the bytes sitting in the working tree. Confirmed empirically at the Phase 4 gate rather than inferred: this repo sets `core.autocrlf=true` and `.gitattributes` sets `* text=auto` plus `*.md text=auto`, so a probe of `references/visual-qa-rubric.md` showed 141 CRLF and 0 bare LF on disk. The release tarball carries the LF blobs, so `nexus-hub verify` would have reported a mismatch on essentially every text file. v3.16.5 shipped exactly that (~520 spurious mismatches); v3.16.6 regenerated the DATA from a clean tree but left the generator, so the defect was one Windows release away from returning.
- **Resolution** (maintainer decision, 2026-08-13, chosen from three options): hash the GIT BLOB bytes for tracked files. `compute_manifest()` now reads the index via `git ls-files -s -z` plus a single batched `git cat-file --batch`, and sha256s the blob payload; untracked covered files and any non-git tree (an installed tree, an exported tarball) fall back to file bytes exactly as before. The manifest therefore describes what is DISTRIBUTED rather than what one host happens to have checked out, from any OS with any line-ending configuration.
- **Why the blob and not newline normalization**: the tarball IS the committed blobs, so hashing them makes the manifest correct by construction instead of correct by a text-detection heuristic, and it leaves `sha256sum -c` semantics and `verify_install.py` untouched. Verification needs no matching change: it runs against an extracted tarball whose on-disk bytes are the blob bytes.
- **Residual boundary, stated rather than discovered**: because the index is the source, a tracked file with UNSTAGED edits is hashed as its staged form. `main()` now prints a warning naming the dirty covered paths so a stale manifest cannot be produced silently. Separately, a user installing from a Windows git clone with autocrlf enabled would still see line-ending mismatches; the supported install path is the tarball.
- **Tests**: 4 regression tests in `tests/validators/test_verify_install.py` build a real git repo with `core.autocrlf=true`, commit LF content, rewrite the working tree as CRLF, and assert the manifest matches the LF blob and NOT the CRLF disk bytes; plus untracked fallback, non-git-tree fallback, and the dirty-path warning.

## v3.16.8 - adoption-watermark-hygiene

Opened at Phase 1 (validator coverage + fix mode) and extended at Phase 2 (`/plan` and `/update` wiring). Sub-tasks 1.3 and 2.3, the ingested v3.16.7 `BG-2` halves, were already complete on entry and are not re-litigated here.

### NI-1 - CLOSED (by design, reconciled Phase 3): the VS16 rule deviates from the plan's literal prescription

- **Source phase**: Phase 1, sub-task 1.1.
- **Plan reference**: sub-task 1.1 prescribes `U+FE0F variation selector-16 (delete)` with no exemption.
- **What shipped instead**: VS16 immediately following a symbol (Unicode category `So` / `Sk`) or a keycap base is treated as legitimate emoji presentation and is neither reported nor rewritten. VS1 to VS15 and the `U+E0100`-`U+E01EF` supplement are covered with no exemption.
- **Reason**: measured before deciding. VS16 occurs 90 times in the scanned tree and every occurrence follows an emoji base (`U+26A0` warning sign 76, `U+1F5FA` world map 7, `U+2764` heart 7, plus `U+2328` and `U+2139`); VS1-VS15 and the supplement occur zero times. The literal rule would therefore have flagged 90 legitimate characters, caught nothing, broken the phase's own byte-identical-baseline stability gate, and (once Phase 2's release gate landed) silently rewritten emoji in `CHANGELOG.md` and the active docs tree. The user was shown the measurement and chose the exemption.
- **Suggested next step**: none required. Recorded so a future reader comparing plan text to shipped behavior finds the reason rather than an unexplained gap.

### WN-1 - OPEN (accepted): a CJK ideographic variation sequence would be reported

- **Source phase**: Phase 1, sub-task 1.1.
- **Symptom**: the emoji-base exemption covers VS16 only, so VS1-VS3 following a CJK ideograph (a legitimate ideographic variation sequence) would be reported.
- **Why accepted**: zero instances exist in the tree, the finding is a warning unless `--strict` is passed, and the alternative is an ideograph-range table maintained for a case with no observed occurrence, which the `AGENTS.md` scope-fit gate declines. The limitation is stated in the `variation_selector_is_legitimate` docstring and the module docstring rather than left for discovery.
- **Suggested next step**: extend the exemption to `Lo`-category bases if a real CJK document ever enters the scanned set.

### MT-1 - CLOSED (reconciled Phase 3): the file-mode preservation test cannot run on Windows

- **Source phase**: Phase 1, sub-task 1.2.
- **Symptom**: `test_fix_preserves_executable_bit` is `skipif sys.platform == "win32"`, so the local development host never exercises it. `atomic_write` uses `shutil.copymode` before `os.replace` specifically so a repaired `.sh` does not lose its executable bit, and that guarantee is unverified locally.
- **Mitigating coverage**: CI runs `python -m pytest tests/validators -v` on its Linux runner, where the test executes.
- **Reconciliation verdict (Phase 3)**: CLOSED. The CI leg was verified rather than assumed: `.github/workflows/ci.yml` line 497 runs `python -m pytest tests/validators -v` on the Linux runner, and line 576 runs `tests/installer tests/validators -q` on the Windows one, so the suite executes on both platforms and the mode assertion executes where file modes exist. The local skip is correct behavior, not a coverage gap.

### BG-1 - OPEN (pre-existing, not introduced here): PowerShell bootstrap tarball test

- **Source phase**: observed during Phase 1 sub-task 1.4's full-suite run, not caused by it.
- **Symptom**: `tests/installer/test_bootstrap.py::test_ps_standalone_extracts_and_hands_off` fails with `/usr/bin/tar: Unexpected end of file` / `Child returned status 128`.
- **Status**: the same failure already recorded and root-caused as v3.16.0 `BG-1` above (Git Bash's MSYS `tar` resolving ahead of the system binary on this Windows host). Reproduced again this cycle; no new information. Cross-referenced rather than re-filed.

### BG-2 - CLOSED (pre-existing, not introduced here): the model-map fallback test asserted a stale date

- **Source phase**: observed during Phase 1 sub-task 1.4's full-suite run.
- **Symptom**: `tests/plans/test_v3_15_9_model_routing_helpers.py::test_bundled_snapshot_parses_and_renders_dated_fallback` asserts the rendered string `offline fallback; stale as of 2026-08-03.` while the renderer emits `2026-08-14`.
- **Root cause**: commit `b29a0ffa` ("docs(v3.16.8): ingest BG-2 into the plan and refresh the stale model map") refreshed `catalog/skills/ai-development/model-routing/references/last-known-model-map.json` to `verified_as_of: 2026-08-14` without updating the test's expected date. Confirmed by running `model-map.py fallback` directly.
- **Evidence it is not this phase's**: neither failing test reads any of the four files this cycle modified, and the snapshot commit predates the session.
- **Fix applied**: the assertion now reads `verified_as_of` from the snapshot and interpolates it, so it enforces the CONTRACT (the fallback renders the snapshot's own date in that exact sentence) rather than a frozen calendar date. The one-line expectation bump was rejected in favour of this because it would have re-armed the same time bomb for the next map refresh, and this cycle is the second time the map has been refreshed. `tests/plans` 91 passed.
- **Why it was fixed here despite being out of scope**: it is a one-line test-only change on the same branch, for the same version, broken by a sibling commit of this very plan (`b29a0ffa`), and leaving it red would have meant handing Phase 3 a suite that cannot go green.

### QG-1 - CLOSED (reconciled Phase 3, no corrective action): Phase 1's commit gate did not run before Phase 2 began

- **Source phase**: Phase 1, step 8.10.
- **Symptom**: Phase 1 reached its quality gate with two unresolved (pre-existing) suite failures and was awaiting a gate decision when Phase 2 was requested, so Phase 1's post-phase sequence never ran independently and the two phases share one commit rather than one each.
- **Consequence**: the per-phase commit granularity the runbook aims for is lost for this pair; the changelog, known-gaps, and session-history content for both phases is present, but a bisect cannot separate them.
- **Suggested next step**: none corrective. Recorded so the combined commit is legible as a deliberate consequence rather than an oversight.

### Observations (no action)

- **The one-time `CHANGELOG.md` normalization was a design consequence, not an incident.** A changelog is a single file holding the new entry and all history, so the release gate's file-level scoping cannot spare its old sections. Seven characters in sections released between v0.8.2 and v1.2.1 were rewritten once (6 em dashes to `--`, 1 en dash to `-`), deliberately and with the diff verified character by character. The repo-wide warning count moved 1049 to 1042 accordingly. Every later run is a no-op on history.
- **Two silent-failure defects were found by testing the wiring rather than the code.** A `--path` target that did not resolve under `--root` exited 0 reporting a clean scan, and an absolute path outside root raised a bare `ValueError`. Both were found only by running the exact command Phase 2 was about to document, from a foreign project root. Neither was reachable from the phase's own unit tests, because those always pass a root that contains the target.

### Phase 3 reconciliation (terminal phase)

**Architecture refactor**: a genuine no-op, executed rather than skipped. No tracked `__pycache__` or `.pyc`. The `docs/v3/v3.16/` tree is canonical (`comparisons/`, `development/`, `plans/`, plus the two governance files), and the v3.16.8 plan is co-located with its seeding comparison per the co-location rule. Four empty directories exist and all four were deliberately left: `.antigravitycli` and `.claude/worktrees` are gitignored local runtime dirs, and `docs/v3/v3.17/development/history` + `docs/v3/v3.20/comparisons` are other versions' scaffolding (v3.17 has active work from a parallel session, so touching it would be both out of scope and disruptive). One stray root artifact, `pytest-out.log`, is gitignored, untracked, dated 2026-05-22, and absent from the manifest, so it never ships; it is a local scratch file and was left rather than deleted from the user's working tree.

**Deferred-work markers**: none. A scan of every code and instruction file this version changed found zero `TODO` / `FIXME` / `XXX` / `HACK` / `# DEVIATION:` markers.

**CI/CD**: verified, no change required. `concurrency` with `cancel-in-progress` (line 81), pip caching on both Python jobs (97, 475), and a `paths` filter of `**` minus `docs/**` with validator-input re-inclusions were all already present. Every surface this plan touched is covered: `tests/validators` runs on the Linux (497) and Windows (576) legs, `tests/skills` (500) covers the edited command and skill prose, and `tests/plans` (507) covers the model-map fix. The repo-wide detect step calls the validator with no arguments and is untouched by any change here. Deliberately NOT added: a repo-wide `--strict` CI gate, which would fail on the 1042 grandfathered warnings; strictness belongs to the pre-commit release gate over release-cycle artifacts, which is exactly how Phase 2 wired it.

**Model-prompting-profile staleness (advisory, 9.0 step 4)**: verdict **DRIFTED**, which is an acceptable terminal outcome; UNKNOWN would not have been. The roster was enumerated FIRST, from `last-known-model-map.json` as refreshed from live first-party documentation on 2026-08-14 (commit `b29a0ffa`, sources cited in the plan), and passed as 15 explicit ids rather than letting the check answer UNKNOWN about a roster it was never given. Result: the profile layer was last verified 2026-07-27 against a roster that no longer matches, with 12 live-but-unprofiled ids and 1 recorded-but-not-live.

The single "removed" entry deserves a caveat rather than action: `claude-haiku-4-5-20251001` and the map's `claude-haiku-4-5` are the SAME model, the dated id versus its alias. So that removal is a naming artifact of comparing two artifacts that spell the id differently, and it will recur on every run until one side adopts the other's form. The 12 additions are real. Per the step's contract this is ADVISORY: it does not block the release, the freshness marker was NOT re-stamped (only a real research run may write it), and the follow-up is `/tune-prompting` on its own schedule.

**Verdict**: 4 closed (NI-1 by design, MT-1 by verified CI coverage, BG-2 by the derived-date fix, QG-1 as a recorded historical fact), 2 carried (WN-1 the accepted CJK limitation with a named revisit trigger; BG-1 pre-existing, environmental, and already tracked as v3.16.0 `BG-1`). **No release blockers.**

## v3.16 Summary

| Category | Open | Resolved |
|---|---|---|
| Comparison-sourced deferrals (`CD-#`) | 3 (CD-1, CD-2, CD-3) | 0 |
| Transferred in from v3.15.14 (`TR-#`) | 2 (TR-1, TR-2) | 1 (TR-3) |
| v3.16.0 version-implementation gaps | 3 carried forward (NI-1, NI-6, BG-1) | 13 closed (DF-1, DF-2, DF-3, DF-4, NI-2, NI-3, NI-4, NI-5, QG-1, QG-2, QG-3, BG-2, BG-3, WN-1) |
| v3.16.1 version-implementation gaps (all 8 phases + release) | 3 carried forward (WN-1, BG-1 environmental; NI-6 bounded and documented) | 21 closed (DF-1..DF-5, NI-1..NI-5, BG-2..BG-8, QG-1, QG-2, WN-2, PX-1) |
| v3.16.2 version-implementation gaps (all 6 phases, reconciled) | 5 carried (MT-1 schema assertions; NI-2 size overage; NI-3 deliberate `--repair` bound; BG-2 pre-existing fail-open; WN-1 / BG-1 environmental) | 6 closed (QG-1, QG-2, BG-3, NI-1, DF-1, WN-2) |
| v3.16.3 version-implementation gaps (all 6 phases, reconciled) | 8 carried (DF-1 deferred key deletion; NI-2 unverifiable weights; MT-2 provisional runner rules; NI-4 cross-monitor policy, routed out; NI-7 deliberate divergence; WN-1 / BG-1 / BG-2 environmental) | 8 closed (NI-1, QG-2, MT-1, NI-5, NI-6, BG-3, NI-3, BG-4) |
| v3.16.4 version-implementation gaps | not recorded - the v3.16.4 cycle (GitHub Usage Monitor account-pinned sessions, shipped 2026-08-11 from a parallel session) added no section to this file. Stated as an observed absence, not as a claim that the cycle had none. | n/a |
| v3.16.5 version-implementation gaps (all 7 phases, reconciled) | 9 carried (NI-2, NI-3, NI-4, NI-5, WN-1, WN-3, WN-4 by design, each with a named place where the render loop answers it; DF-2 accepted, DF-3 declined for want of a call site) | 9 closed (MT-1, DF-1, DF-4, BG-1, BG-2, BG-3, BG-E1, plus v3.15's MT-1 and MT-2) |
| v3.16.6 version-implementation gaps (both phases + release, reconciled) | 2 carried (NI-1 verbosity contract is agent behavior, by design; WN-1 `generate_manifest.py` is generation-environment-dependent, routed to the next `scripts/`-touching cycle) | 3 closed (DF-1 the unbookkept v3.16.5 deferral; QG-1 the CI path filter missing the command file; BG-1 the shipped v3.16.5 CRLF manifest, fixed by the v3.16.6 regeneration) |
| v3.16.8 version-implementation gaps (all 3 phases, reconciled) | 2 carried (WN-1 the accepted CJK ideographic-variation limitation, with a named revisit trigger; BG-1 pre-existing and environmental, already tracked as v3.16.0 `BG-1`) | 4 closed (NI-1 the VS16 deviation, deliberate and measured; MT-1 by verified CI coverage on both legs; BG-2 the stale model-map date assertion, fixed by deriving the date from the snapshot rather than bumping it; QG-1 the combined Phase 1 + 2 commit, recorded rather than corrected) |
| v3.16.7 version-implementation gaps (all 4 phases, reconciled) | 3 (NI-2 Gates A/B/E are agent behavior by the same reasoning as criterion 10; NI-3 composition probes specified inline like the existing probes, no bundled helper yet; WN-3 legacy `typing` generics kept for module consistency, advisory only since ruff is not a CI gate) | 6 closed (BG-1 the frontmatter-breaking BOM; DF-1 the missing plan artifact; DF-2 the cross-session changelog contamination; NI-1 the open intake, closed by the VectorCAST lessons; **WN-1 the manifest generator, carried since v3.16.5 and root-caused here by hashing git blob bytes**; WN-2 the two ruff findings) |

The three comparison-sourced items remain non-blocking prose folds with named target files. Of the v3.16.0 items, BG-1 is pre-existing and reproduces without this plan's changes, WN-1 is environmental, DF-1 is a reasoned non-implementation, NI-1 is a deliberate scope boundary the plan requires, and NI-2 / NI-3 / NI-4 are Phase 2 findings that Phase 3 and Phase 5 are already scheduled to dispose of. Phase 5 dispositioned every open item: 13 closed, 3 carried forward. **None gates the v3.16.0 release.** NI-1 and NI-6 are scope decisions for cycles already touching the relevant surfaces, and BG-1 is pre-existing, reproduced on a clean `develop` worktree, and confined to a Windows host whose PATH resolves `tar` to the Git Bash binary. Of the 13 closed, three (BG-2, BG-3, and QG-3) were caught by the test suite rather than by review, which is this cycle's strongest argument for running the full suite before declaring a phase done.
