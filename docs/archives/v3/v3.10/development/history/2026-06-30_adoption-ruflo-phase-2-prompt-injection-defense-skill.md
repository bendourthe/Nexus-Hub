# Session History - v3.10.0 adoption-ruflo Phase 2: Prompt-injection-defense skill

**Date**: 2026-06-30
**Plan**: [`../../plans/adoption-ruflo.md`](../../plans/adoption-ruflo.md) Phase 2 (A4 prompt-injection-defense skill; skill-native, P1)
**Branch**: `develop`
**Outcome**: Complete. All Phase 2 exit-checklist items satisfied; quality gate GO. Phase 2 of 6; not the final phase, so no release-readiness run.

## Goal

Ship a new defensive `prompt-injection-defense` skill that consolidates how an agent recognizes and resists prompt injection and tool-output poisoning - the defender's-seat counterpart to the offensive `ai-attack-patterns`. Skill-native: pure agent-instruction content, no new outbound call, dependency, credential, or third-party processor. Plus the three-file registry update (skills count 258 -> 259) and the allowlist grandfather.

## What shipped

- **`catalog/skills/security/prompt-injection-defense/SKILL.md`** (new, 118 lines): a recognition-and-posture skill whose pivot is provenance, not plausibility - the only sources that may instruct the agent are the user and the system prompt; everything the agent reads while doing a task (a fetched page, a file, a tool result, another agent's handoff) is untrusted data to be analyzed, never a principal that can issue commands.
    - Conformant frontmatter: `name: prompt-injection-defense`; a pushy `description` listing the plan's five trigger phrases plus a SKIP clause (offensive red-team methodology -> `ai-attack-patterns`; model-provider safety tuning); quoted `summary_l0` (12 words) and `overview_l1` (142 words); optional `atlas_techniques: [AML.T0051]`.
    - Six required body sections in order: intro; `## When to Use This Skill` (with "When NOT to use"); `## Instructions`; `## Common Rationalizations` (five rows, each a concrete failure mode); `## Verification` (binary checklist); `## Related Skills`.
    - Instructions teach the mandated five-part defensive playbook: (1) instruction-origin discipline (imperative grammar in data is not a command to the agent); (2) untrusted-content fencing (tag provenance, quote-don't-adopt, never let a block silently escalate privilege or redirect the goal); (3) tool-output skepticism (trust the channel, not the payload; a result that asks the agent to run a command, reveal a secret, disable a check, or contact an endpoint is a red flag to surface, not obey); (4) indirect-injection recognition cues (imperative shift, "ignore previous instructions", base64/homoglyph/zero-width obfuscation, instructions embedded in data fields, exfiltration requests); (5) the safe response (stop, do not perform the side effect, report what + where, hand the decision back to the user). Closes with a defense-in-depth note (sandboxing, least privilege, egress redaction) and states plainly it is posture, not a guarantee.
    - Cross-links `[[ai-attack-patterns]]` (the offensive counterpart), `[[agent-access-policy]]`, `[[egress-redaction]]`, `[[advanced-attack-patterns]]`, and `[[security-framework-mapping]]` (for the standards mapping); `[[security-review]]` is also referenced in "When NOT to use".
- **`catalog/skills/security/prompt-injection-defense/references/standards.md`** (new): documents the `atlas_techniques: [AML.T0051]` mapping (framework, short title, rationale, public source) in the same format as the offensive skill's standards file, and records why D3FEND is intentionally not mapped.
- **Registration (three registries + allowlist)**:
    - `data/SKILL_INDEX.md`: appended the `prompt-injection-defense` security row; bumped the footer total 258 -> 259.
    - `data/skills.json`: appended a full schema entry (version 1.0.0, category security, priority MEDIUM, security scores 100/100/95, downloads 0); updated the `statistics` block (total_skills 258 -> 259, categories.security 14 -> 15, priorities.MEDIUM 254 -> 255).
    - `data/marketplace.json`: incremented the Security category `skill_count` 14 -> 15 (category sum now 259).
    - `scripts/validate_skills.allowlist.json`: added `prompt-injection-defense` to the security cluster (alphabetical) so the deliberately pushy combat-undertriggering description (709 chars) is grandfathered like every existing security skill.

## Key decisions / troubleshooting

- **Optional ATLAS mapping added (the optionality call).** The plan's sub-task 2.1 makes security-framework mapping optional ("MAY be added"). I added `atlas_techniques: [AML.T0051]` with a companion `references/standards.md`, because (a) the direct counterpart `ai-attack-patterns` already maps AML.T0051, so adding the defensive side gives clean offensive<->defensive symmetry in the framework-coverage matrix; (b) AML.T0051 is the precise, verified technique this skill defends against (zero overclaim risk); and (c) the Phase 1 session history explicitly flagged Phase 2 as the place for it. D3FEND was deliberately omitted: the catalog's existing D3FEND IDs are all host/network forensics techniques, none of which names LLM-prompt-injection defense, and asserting a loose match would contradict the skill's own anti-overclaim thesis. The omission rationale is recorded in `standards.md`.
- **Complement, not duplicate, `ai-attack-patterns`.** The offensive methodology (authorization and scope, the probe phases, live payloads, Phases 0-7) stays in `ai-attack-patterns`. This skill is the agent's own recognition-and-posture as a *consumer* of untrusted content. The "When NOT to use" section routes offensive testing to `ai-attack-patterns` and end-to-end product-architecture defense to `ai-attack-patterns` Phase 7 / `security-review`, keeping the two non-overlapping.
- **Hand-edit lineage confirmed against the generator.** `data/skills.json` is generated by `infrastructure/tools/build_skills_catalog.py`, but the committed registries follow a hand-edited lineage (egress-redaction's committed `tokens_estimate` 3223 = chars/4, which the generator's own estimator does not produce; the committed `SKILL_INDEX.md` order and category casing also differ from generator output). A backup-generate-compare-restore check verified this: running the generator reordered/reformatted every entry (out of scope) and emitted different `based_on` (empty), `long_description` (the SKILL.md intro), and `size` values for my entry. I restored the surgical manual edit and matched egress-redaction's method exactly (lines 118 via `splitlines`, characters 12100, tokens 3025 = chars/4, `based_on` "v3.10.0 catalog addition", hand-written `long_description`). No active local pre-commit hook exists and CI skips `build-catalogs`, so the manual entry is not auto-regenerated on commit.
- **`statistics.total_skills` lives in skills.json (Phase 1 precedent).** The plan's sub-task 2.2 again attributed `statistics.total_skills` to `marketplace.json`; that field is in `skills.json`. The marketplace machine-count is the per-category `skill_count` sum. Incremented each where the count actually lives, keeping all three machine-truth counts consistent at 259.
- **Cosmetic prose counts deferred to Phase 6.** The marketplace `plugin.description` ("257 curated skills") and README / AGENTS prose counts are tied to the released version and validated by no script (`check_version_sync` checks only semver). Per the plan (sub-task 6.3 reconciles to 259 at release) and the Phase 1 precedent, I left those cosmetic strings untouched; the machine-count (259) leading the prose-count (257) is the normal mid-cycle state.
- **CHANGELOG / known-gaps deferred to Phase 6.** Per the plan's phasing, `CHANGELOG.md ## [Unreleased]` and `docs/v3/v3.10/known-gaps.md` are consolidated in Phase 6; Phase 2 does not touch them.

## Verification (quality gate: GO)

`make` is not on PATH (WN-v33-1), so the gate ran via its documented Windows equivalents - ALL GREEN:

- **JSON integrity**: `skills.json` loads, 259 skills, total_skills 259, security 15; `marketplace.json` security skill_count 15, category sum 259; bundles / workflows / templates / allowlist load.
- **Bundle audit** (`validate_skills.py --bundles-only`): PASS. `references/standards.md` is referenced from `SKILL.md`, so no orphan for this skill (the single global warning is a pre-existing stale `.pyc` under `demo-capture`, unrelated).
- **Quality heuristics** (`validate_skills.py --quality`): PASS, 0 warnings (Common Rationalizations present, binary Verification checklist, Tier-1 fields within budget, Related Skills cross-links present).
- **Skill-security scan** (`scan_skill_security.py --fail-on high`): exit 0; critical=0, high=0. The 2 MEDIUM findings are expected false positives - a prompt-injection-*defense* skill must quote the "ignore previous instructions" pattern it teaches the agent to recognize, exactly as `ai-attack-patterns` carries live payload examples and still passes.
- **Unicode / ASCII safety** (`validate_unicode_safety.py`): PASS; the new SKILL.md and standards.md are ASCII-clean.
- **No-personal-paths / supply-chain-IOC / workflow-security**: exit 0.
- **Version sync** (`check_version_sync.py`): all surfaces match (no version-carrying surface touched).
- **Dangling-wikilink audit**: all six cross-link targets resolve (`ai-attack-patterns`, `egress-redaction`, `advanced-attack-patterns`, `security-framework-mapping` under security; `agent-access-policy` under orchestration; `security-review` under code-review).
- **Body size**: 118 lines, under the 500-line norm.
- **YAML parse**: PyYAML `safe_load` of the frontmatter OK; quoted summary_l0 (12 words) and overview_l1 (142 words) within limits; `atlas_techniques` parses as a list.
- **Attribution grep**: zero matches in the distributed artifacts for `ruflo`, `AIDefence`, `AgentDB`, `RuVector`, `SONA`, `ReasoningBank`, `MetaHarness`, `SPARC`, `rvf`, `rvagent`, `ruv.io`.

No `make test` run is warranted: the phase adds no code or tests; the validator chain is the test surface. CI runs the JSON-integrity checks, the v2.3.0 validators, base-template parity (untouched), `scan_skill_security --fail-on high` (replicated green), ShellCheck (no shell added), and the pytest suites (no Python added) - so CI will be green for this change. CI does NOT run the strict `--allow-existing` pass.

### Pre-existing, out-of-scope findings (not introduced by and not fixed in this phase)

Surfaced during validation and left for Phase 6 / maintainer follow-up, per scope discipline:

- The strict `validate_skills.py --allow-existing` pass FAILS on `catalog/skills/specialized-domains/document-to-interactive-html/SKILL.md` (984-char description, never added to the allowlist). That skill predates Phase 1 (last touched in `ad89a47`); the failure is not a CI gate.
- The bundle audit warns on `catalog/skills/workflow/demo-capture/scripts/__pycache__/capture-demo.cpython-312.pyc` (a committed compiled artifact, not referenced from SKILL.md). Pre-existing; unrelated to this skill.

## Files changed

- `catalog/skills/security/prompt-injection-defense/SKILL.md` (new)
- `catalog/skills/security/prompt-injection-defense/references/standards.md` (new)
- `data/SKILL_INDEX.md` (row added; footer total 258 -> 259)
- `data/skills.json` (entry added; statistics counts updated)
- `data/marketplace.json` (Security category skill_count 14 -> 15)
- `scripts/validate_skills.allowlist.json` (prompt-injection-defense grandfathered)
- `docs/v3/v3.10/plans/adoption-ruflo.md` (Phase 2 exit checklist checked off)
- `docs/DEVLOG.md` (Phase 2 entry)
- `docs/archive/v3/v3.10/development/history/2026-06-30_adoption-ruflo-phase-2-prompt-injection-defense-skill.md` (this file)

## Next

Phase 3: Competitive-generation enrichment + SPARC-note decision (skill-native, P2 / optional P3). Add an iterative hill-climbing / co-evolution section to `catalog/skills/orchestration/competitive-generation/SKILL.md` (A5), and make and record an explicit build-or-skip decision on the optional named-phased-development quality-gate note (A6; recommended default: skip to `docs/v3/v3.10/known-gaps.md`). No registry edit expected unless a `summary_l0` changes. CHANGELOG `## [Unreleased]` and `docs/v3/v3.10/known-gaps.md` remain consolidated in Phase 6 per the plan's phasing.
