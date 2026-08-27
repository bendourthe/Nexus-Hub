# Session History - v3.9.0 adoption-looper-and-deer-flow Phase 3: Low-priority doctrine notes and consolidation

**Date**: 2026-06-25
**Plan**: [`../../plans/adoption-looper-and-deer-flow.md`](../../plans/adoption-looper-and-deer-flow.md) Phase 3 (D1 + D2 + RE-matrix declines + registry decision + CHANGELOG + known-gaps, skill-native)
**Branch**: `develop`
**Outcome**: Complete. All Phase 3 exit-checklist items satisfied; quality gate GO. Final phase of this plan, but v3.9.0 is NOT yet release-ready (a second v3.9.0 plan, `presentify-interactive-html`, is still unimplemented), so the release-readiness workflow was deliberately NOT triggered - see Next.

## Goal

Fold in the two low-priority doctrine notes the cross-model agent-runtime comparison surfaced (D1 default-deny host-execution posture in `agent-access-policy`; D2 optional typed-fact memory schema in a memory skill), record the cycle's declines and the convergent-validation finding in the reverse-engineering matrix, make the registry-edit decision, and consolidate the CHANGELOG and known-gaps. Skill-native Markdown enrichment only: no new skill, command, hook, outbound call, dependency, or credential.

## What shipped

- **`catalog/skills/orchestration/agent-access-policy/SKILL.md`** (body 266 -> 277 lines): new `## Default-Deny Host Command Execution` section placed after Step 4 and before Best Practices. Teaches that host (non-sandboxed) execution is the highest-privilege grant and is denied by default; that when execution is needed an isolated sandbox tier is preferred over the host, escalating isolation with risk (a local container for untrusted input, stronger isolation - own non-root user, explicit network mode, no host credentials - for multi-tenant / network-exposed runs); and a log-before-execute (audit-before-execute) step paired with the advisory `escalation-trigger` hook. Framed as access-policy doctrine, not a runtime. Cross-links the local-only "Sandboxing an Unattended Loop" subsection in `[[loop-engineering]]`, plus `[[containerization]]` and `[[using-git-worktrees]]`.
- **`catalog/skills/workflow/loop-engineering/SKILL.md`** (body 207 -> 209 lines): one reciprocal cross-link added at the end of the "Sandboxing an Unattended Loop" subsection, pointing back to the new "Default-Deny Host Command Execution" section in `[[agent-access-policy]]` and framing the subsection as that posture's unattended-loop application. (This is the only Phase 3 edit to this file; the Phase 2 design-first content is untouched.)
- **`catalog/skills/workflow/context-pack-builder/SKILL.md`** (body 147 -> 159 lines): new `## Optional: Typed Fact Entries` section after `## Context Pack Format`. Notes that a caller wanting auditable memory can persist each fact as a typed entry (`id` / `content` / `category` / `confidence` / `created` / `source`) so entries are filterable and provenance is inspectable; explicitly framed as an OPTIONAL shape (the prose Distilled Facts remain the default) and a schema only - it does NOT introduce an extraction runtime; any LLM-driven extraction is the caller's choice, outside this skill.
- **`docs/policy/mcp-reverse-engineering-matrix.md`**: new dated section "Declined or flagged in the v3.9.0 adoption cycle" (modeled on the v3.8.0 loop-engineering declines), recording four rows: (a) a portable thin loop runner script - `drop-outright`, citing the v3.8.0 host-driver row as direct precedent; (b) a design-spec-to-resolved-spec compile step that exists only to feed that runner - `drop-outright`, bundled with the runner; (c) advisory-only cost caps - "not recommended", flagged as weaker than the `ai-billing-safeguards` hard caps (the opposite of an adoption); (d) the convergent-design-validation finding - a separate agent runtime independently converged on the same Markdown-`SKILL.md` + three-tier-loading authoring model, recorded as a finding, not a gap. The section references both comparison reports.
- **`CHANGELOG.md`**: one `## [Unreleased]` `### Changed` entry describing the full three-phase enrichment (egress hygiene + reviewer-vs-judge + argv-array; design-first loop + verification ordering + render-and-confirm; default-deny posture + typed-fact schema; matrix declines + convergent-validation finding).
- **`docs/v3/v3.9/known-gaps.md`** (created): carries the standing Windows-dev-host warnings (WN-v33-1 make-absent, WN-v36-1 bash-space-path, WN-v37-1 live-one-liner-manual) and the reinforced DF-v36-2 (portable orchestration/loop runtime deferred), plus Notes recording the no-registry-edit decision, the declines-are-durable note, and the separate presentify plan.

## Key decisions / troubleshooting

- **Memory-skill target (3.2): `context-pack-builder`, not `continuous-learning`.** The plan said to prefer `context-pack-builder` "if it already discusses durable memory entries". It does: its context packs are committed, source-attributed artifacts in `docs/context/`, and its "Distilled Facts" map directly onto the typed-fact shape. `continuous-learning` writes ephemeral in-session instincts to gitignored `.nexus/`, a weaker fit for "durable, auditable, source-attributed memory entries". Chose `context-pack-builder`.
- **Registry-edit decision (3.4): NO edit needed.** Read the final `summary_l0` / `overview_l1` of all four enriched skills. Each still accurately describes its skill at the one-line / paragraph level: the egress hygiene and reviewer-vs-judge rule are facets of cross-model orchestration with QA gates; the design-first pass is part of loop assembly; default-deny execution is a facet of least-privilege access control (the skill already covered `Bash(...)` permissions); the typed-fact schema is an optional format note. No headline capability changed, so the three registries and the `cross-model-orchestrator` footer version were left unchanged. This follows the direct v3.8.0 precedent (the comparable loop-engineering enrichment added an entire Exit-Signal Protocol with no frontmatter / `data/` change) and the Phase 1-2 pattern in this plan (both recorded "frontmatter unchanged"). Recorded explicitly in the known-gaps Notes per the plan.
- **Matrix wikilink convention.** The matrix references skills in backticks (e.g. `` `containerization` ``), not `[[wikilinks]]`. An initial `[[ai-billing-safeguards]]` in the advisory-cost-cap row was changed to the backtick form to match the file's own convention and avoid introducing a skill-style wikilink into a policy doc.
- **Section placement matched each file's heading idiom.** Default-Deny went in as an H2 peer of the existing access-policy sections (after Step 4, before Best Practices); the typed-fact note went in as an H2 right after Context Pack Format (so it reads as a variant of the format). No heading-hierarchy violation.
- **Did NOT trigger the release-readiness workflow.** Phase 3 is the final phase of THIS plan, which would normally route to `/update release`. But v3.9.0 has other in-flight work in `## [Unreleased]` (the Foundations guide page) and a second unimplemented plan (`presentify-interactive-html`), so cutting a v3.9.0 release now would be premature. Surfaced the release-readiness status to the user instead of auto-running it (release stays confirmation-gated regardless).

## Verification (quality gate: GO)

- `make` is not on PATH (WN-v33-1), so the gate was run via its documented equivalents:
  - **JSON catalog integrity**: `data/skills.json` OK (256 skills); `data/marketplace.json` OK.
  - **Orphan-bundle audit** (`python scripts/validate_skills.py --bundles-only`): PASS, 0 errors (1 pre-existing unrelated warning). No new bundle files added.
  - **Quality heuristics** (`python scripts/validate_skills.py --quality`): PASS, 0 errors, 0 warnings; none of the four edited skills flagged.
  - **Unicode-safety** (`python scripts/validate_unicode_safety.py`): exit 0; none of the edited skill / matrix / known-gaps files appear in the report, and the new CHANGELOG entry (line 18) is not flagged (the CHANGELOG warnings are all pre-existing historical entries at lines 758+).
  - **Dangling-wikilink audit**: all four new cross-link targets resolve - `loop-engineering` (workflow), `containerization` (infrastructure), `using-git-worktrees` (workflow), `agent-access-policy` (orchestration).
  - **Body sizes**: agent-access-policy 277, context-pack-builder 159, cross-model-orchestrator 310, loop-engineering 209 - all under the 500-line norm.
  - **Attribution grep** over the full diff: zero matches for `Looper`, `ksimback`, `DeerFlow`, `ByteDance`, `loop.yaml`, `loop.resolved.json`, `run-loop.py`, `ensure_consent`, `RUN_IN_SESSION`, `allow_host_bash`, `memory.json`, `SandboxAuditMiddleware`, `topOfMind`, `workContext`, `definition_of_done`, `privacy.egress`, `redact_prompt_for_member`.
  - **Cross-file consistency**: the reciprocal cross-links (agent-access-policy <-> loop-engineering sandbox) agree both ways; the egress-hygiene discipline (Phase 1, a data-egress boundary) and the default-deny posture (Phase 3, a command-execution boundary) cover different boundaries and reinforce rather than contradict; nothing implies a shipped loop runtime or a new dependency.

## Files changed

- `catalog/skills/orchestration/agent-access-policy/SKILL.md`
- `catalog/skills/workflow/loop-engineering/SKILL.md`
- `catalog/skills/workflow/context-pack-builder/SKILL.md`
- `docs/policy/mcp-reverse-engineering-matrix.md`
- `CHANGELOG.md`
- `docs/v3/v3.9/known-gaps.md` (created)
- `docs/v3/v3.9/plans/adoption-looper-and-deer-flow.md` (Phase 3 exit checklist checked off)
- `docs/archive/v3/v3.9/development/history/2026-06-25_adoption-looper-and-deer-flow-phase-3-low-priority-doctrine-notes-and-consolidation.md` (this file)

## Next

This plan (`adoption-looper-and-deer-flow`) is COMPLETE: all three phases shipped, every exit checklist satisfied, Definition of Done met. v3.9.0 is NOT yet release-ready - the second v3.9.0 plan [`presentify-interactive-html`](../../plans/presentify-interactive-html.md) is still unimplemented and the Foundations guide page sits in `## [Unreleased]`. When all v3.9.0 workstreams are done, run `/update release` (it bumps every version-carrying surface via `check_version_sync.py`, finalizes the changelog, commits, merges `develop` -> `main`, tags `v3.9.0`, pushes, and publishes the GitHub Release). The DEVLOG entry is deferred to that release step, consistent with Phases 1-2 (which added session histories, not DEVLOG entries).
