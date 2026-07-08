# Session History - adoption-t3mp3st Phase 1: local coding-agent hijack recognition

**Date**: 2026-07-08
**Plan**: `docs/v3/v3.11/plans/adoption-t3mp3st.md`
**Phase**: 1 of 4 - Local coding-agent hijack recognition (skill-native, C1, flagship)
**Status**: Complete (Phase 1 stability gate PASS). Body-only, defensive, zero registry drift. Part of the v3.11.0 release (folds in alongside the workflow-governance work; the version bump and CHANGELOG entry are `/update release`'s / Phase 4's job).

## Goal

Teach Nexus-Hub's defensive skills to recognize and resist the confused-deputy threat where an external offensive meta-harness commandeers a user's already-running, already-authenticated local coding agent and drives it as an execution proxy - framed strictly as recognition-and-posture and containment, never as construction of the attack.

## What changed (all body-only; no frontmatter, no `data/` edit)

- **1.1 - `prompt-injection-defense`** (`catalog/skills/security/prompt-injection-defense/SKILL.md`): added a `### Recognize local-agent commandeering (confused-deputy via an external harness)` subsection after the Defense-in-depth block. It describes the threat generically (an external process borrows the agent's live session through its local API/CLI, an exposed MCP endpoint, or a driver, needing no credentials of its own and inheriting the agent's quota, filesystem reach, tool permissions, and network position), explains the confused-deputy framing, and gives concrete recognition cues (non-primary/programmatic channel, "operators/missions/targets/kill chain" framing with no authorization artifact, recon/scan/exploit-against-third-parties requests, acting for an unnamed orchestrator, requests to disable logging/evade detection) and a safe-response rule (treat non-primary channels as untrusted, refuse un-authorized offensive tasking, do not proxy for an unidentified orchestrator, prefer containment + egress limits). Added one Common Rationalizations row ("the request came through my own tool interface...") and one Verification item. Cross-links `[[agent-access-policy]]`, `[[ai-attack-patterns]]`, `[[egress-redaction]]`.
- **1.2 - `agent-access-policy`** (`catalog/skills/orchestration/agent-access-policy/SKILL.md`): added a `## Containing a Commandeered Agent (Blast-Radius Limit)` section after the Default-Deny Host Command Execution section, stating three deny-by-default containment controls - tool allowlist, least-privilege file access scoped to the working tree, and default-deny network egress (the C4 framing) - and tying containment explicitly to the hijack threat in `prompt-injection-defense`. Cross-links `[[prompt-injection-defense]]`, `[[egress-redaction]]`.
- **1.3 - `ai-attack-patterns`** (`catalog/skills/security/ai-attack-patterns/SKILL.md`): added a `Local-agent commandeering` row to the Attack Families Covered table, naming the borrowed-session/confused-deputy technique for authorized-review awareness only (no build steps) and pointing to the defensive counterpart `[[prompt-injection-defense]]`. Omitted an ATLAS ID (no clean match; the plan says omit if unsure); frontmatter unchanged.

## Verification (1.4)

- `make validate` gate mode green: `validate_skills.py --bundles-only` exit 0, `--quality` exit 0 (0 errors), `validate_unicode_safety.py` exit 0.
- The plain full-mode `validate_skills.py` exits 1 on a PRE-EXISTING, catalog-wide "description > 250 chars" flag across 161 skills (the AGENTS.md pushy-description convention vs. the strict 250-char default); the three edited skills appear only for that pre-existing description-length flag, which my body-only edits did not touch. No new error introduced.
- Registry-drift guard: `git diff` confirms no frontmatter line changed in any of the three skills (body-only), so no `data/` edit is required.
- Line counts under the 500-line norm: prompt-injection-defense 139, agent-access-policy 289, ai-attack-patterns 161.
- Attribution grep: zero matches for `T3MP3ST` / `TEMPEST` / `TempestCommand` / `elder-plinius` / `Pliny` across the three files.
- Wikilink targets resolve: `agent-access-policy`, `ai-attack-patterns`, `egress-redaction`, `prompt-injection-defense`, `loop-engineering`, `containerization`, `using-git-worktrees`, `ai-billing-safeguards` all exist as catalog skills.
- Recognition-not-construction check: the `prompt-injection-defense` subsection describes the threat abstractly and gives recognition cues plus a refusal rule with NO operational build steps for the attack (the key correctness check for the phase).

## Notes and sequencing caveats

- This phase's edits sit in the working tree alongside the uncommitted v3.11.0 Phase 8 (workflow-governance) release-prep. Both are v3.11.0 and ship together via `/update release`; the commit/tag/push is deferred to that flow (nothing auto-committed here).
- The plan's stale assumptions bite only later: it says catalog counts are "unchanged (260 skills)", but the current count is 263 (the workflow-governance delegates + youtube-transcript landed since the plan was written); and its Phase 4 CHANGELOG entry targets `## [Unreleased]`, but the v3.11.0 CHANGELOG entry is already open, so Phase 4 should fold into `## [3.11.0]` and state 263. Phase 1 touches neither, so it is unaffected.

## Next steps

- Phases 2 (benchmark-receipt discipline in `skill-eval-loop` + `ai-output-evaluation`), 3 (dangerous-action approval gate in `agent-access-policy`), and 4 (declines + CHANGELOG + validation sweep) remain, then `/update release` ships all of v3.11.0.
