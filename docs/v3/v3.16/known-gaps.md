# Known Gaps - v3.16

**Project**: Nexus-Hub
**Status**: No v3.16 release has been implemented yet (latest tag `v3.15.5`; `v3.15.6 adoption-sandbox-escapes` is in flight on `feat/adoption-sandbox-escapes`). The v3.16 line currently holds seven committed plans and no implementations: v3.17.0 agent-autonomy-toggle, v3.18.2 adoption-rtk-and-meterless, v3.18.1 adoption-optmem, v3.18.0 adoption-jcodemunch, v3.16.0 platform-defaults-config, v3.19.1 adoption-interface-craft-skills, and v3.15.14 adoption-spec-driven-development.
**Last updated**: 2026-07-29 (seeded by the no-mistakes delta comparison; no version-implementation entries yet)

> **File-lifecycle note**: this ledger was created ahead of any v3.16 implementation, by a comparison that deliberately claimed no release slot. It therefore contains ONLY the `## Comparison-Sourced Deferrals` section below. The first v3.16 version-implementation phase to reconcile its gaps should **append** its own `## v3.16.N - <slug>` section rather than replacing this file, and should keep its own `DF-#` / `NI-#` / `QG-#` numbering, which is namespaced separately from the `CD-#` ids used here (see the numbering note in that section).

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

## v3.16 Summary

| Category | Open | Resolved |
|---|---|---|
| Comparison-sourced deferrals (`CD-#`) | 3 (CD-1, CD-2, CD-3) | 0 |
| Version-implementation gaps (`DF-#` / `NI-#` / `QG-#`) | n/a (no v3.16 version implemented yet) | n/a |

All three open items are non-blocking prose folds with named target files. None gates any v3.16 release.
