# Known Gaps - v3.16

**Project**: Nexus-Hub
**Status**: v3.16.0 `platform-defaults-config` is in flight on `feat/platform-defaults-config` (Phase 1 of 5 complete; unreleased). The v3.16 line holds seven committed plans: v3.17.0 agent-autonomy-toggle, v3.18.2 adoption-rtk-and-meterless, v3.18.1 adoption-optmem, v3.18.0 adoption-jcodemunch, v3.16.0 platform-defaults-config, v3.19.1 adoption-interface-craft-skills, and v3.15.14 adoption-spec-driven-development.
**Last updated**: 2026-08-08 (v3.16.0 Phase 1 gaps appended)

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

#### Observations (no action)

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

### Observations (no action)

- **Local Python lint was not run**: `ruff` is not installed on this host. The repository's own `make lint` target runs ShellCheck only (which passed, on unchanged shell files), so no declared gate was bypassed. Python style was kept to the surrounding conventions by hand, and the generator emits ruff-shaped literals (magic trailing comma) so `--apply` does not fight the formatter.
- **`make` is unavailable on this host**: the `validate` steps were run individually as the equivalent, and all eight passed.
- **Only Claude is seeded, by design**: Phase 2 web-verifies the remaining fifteen registered integrations before any of them appears in the defaults file. A single-platform defaults file at the end of Phase 1 is the intended state, not an omission.

---

## v3.16 Summary

| Category | Open | Resolved |
|---|---|---|
| Comparison-sourced deferrals (`CD-#`) | 3 (CD-1, CD-2, CD-3) | 0 |
| Transferred in from v3.15.14 (`TR-#`) | 2 (TR-1, TR-2) | 1 (TR-3) |
| v3.16.0 version-implementation gaps | 4 (DF-1, NI-1, BG-1, WN-1) | 1 (DF-2) |

The three comparison-sourced items remain non-blocking prose folds with named target files. Of the v3.16.0 items, BG-1 is pre-existing and reproduces without this phase's changes, WN-1 is environmental, DF-1 is a reasoned non-implementation, and NI-1 is a deliberate scope boundary that the plan requires. None gates the v3.16.0 release.
