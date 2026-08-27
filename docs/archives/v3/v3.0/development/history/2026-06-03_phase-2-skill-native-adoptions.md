# Session History -- v3.0.0 Phase 2: skill-native adoptions (reverse-engineer-first)

**Date**: 2026-06-03
**Plan**: [`docs/releases/v3/v3.0/plans/command-consolidation-skill-security.md`](../../plans/command-consolidation-skill-security.md)
**Phase**: 2 of 10 -- skill-native adoptions (reverse-engineer-first)
**Outcome**: complete; all five sub-tasks (T005-T009) closed, all quality gates green.

## Goal

Ship the two zero-code skill replacements that close the orchestration and skill-security intent gaps before any command or engine work, and enrich the existing `multi-agent-coordinator` skill. Per the MCP Registry Policy reverse-engineer-first decision tree, both adoptions are `skill-native` (tier 2): pure catalog content with no new code, dependency, credential, or outbound call.

## Subtasks completed

1. **T005 -- Orchestration decision-guide skill.** Created `catalog/skills/orchestration/agent-orchestration-primitives/SKILL.md` (131 lines) + `references/five-patterns.md` (80 lines). The body names the four primitives (single agent / subagents / agent teams / Dynamic Workflows) with their envelopes and hard limits, a start-single escalate-on-a-measured-problem gate, a cheapest-primitive matching table, the three failure modes, the do-not-parallelize-code-writing rule, and a REQUIRED Dynamic-Workflows graceful-degradation framing. The five orchestration patterns were pushed to the tier-3 reference file and linked.
2. **T006 -- Skill-security adjudication skill.** Created `catalog/skills/security/skill-security-scan/SKILL.md` (115 lines) + `references/detection-classes.md` (80 lines). The skill adjudicates deterministic detector findings (engine arrives in Phase 6; manual findings supported until then): filter false positives (fence-aware, producer-catalog aware), explain intent, assign an install verdict. The 16 detection classes with MITRE/D3FEND/NIST identifiers + public-source URLs are documented in the companion reference. Defensive only; no bundled LLM client or key. Generic naming per the Reverse-Engineering Attribution Rule.
3. **T007 -- Enrich multi-agent-coordinator.** Added a "when NOT to go multi-agent" gate (defers the primitive choice to `agent-orchestration-primitives`, carries the do-not-parallelize-code warning), a context-centric-decomposition principle in Step 1 (split by context not role; the implementer writes the tests), and a five-pattern cross-link in Related Skills. 681 -> 685 lines (under the 800 soft cap). No script behavior changed.
4. **T008 -- Register both skills.** Hand-registered both skills in all three registries (see Key decisions for why hand-edit over generator regen): 2 entries in `data/skills.json` with recomputed statistics, 2 rows + Total in `data/SKILL_INDEX.md`, the `orchestration`/`security` counts in `data/marketplace.json`, and both pushy descriptions added to `scripts/validate_skills.allowlist.json`.
5. **T009 -- Stabilization.** Emulated `make validate` (all green) and ran the MCP skill-server suite (43 passed); confirmed cross-links resolve and registries agree.

## Key decisions

- **Hand-registration over `build_skills_catalog.py` regen.** The T008 prompt prescribed regenerating `skills.json` + `SKILL_INDEX.md` via the generator. Running it produced a ~5,500-line diff that materially rewrote existing entries (it splits categories by raw frontmatter casing -- `Developer Experience` vs `developer-experience`, `Research`, `Workflow` -- and recomputes `long_description`/`size`/ordering), revealing the committed `data/` files are maintained by a newer/different process than the generator. To keep every changed line traceable, the regeneration was reverted and registration was done by hand. A no-op load/dump round-trip of `skills.json` was confirmed byte-identical first, so the scripted insert changed exactly the two entries + statistics. The drift is recorded as WN-v30-2; `make build-catalog` is currently unsafe to run.
- **Framework-mapping accuracy.** `skill-security-scan` declares only high-confidence framework identifiers in its frontmatter, and `references/detection-classes.md` presents the per-class mapping as the *primary* mapping with an explicit instruction to verify exact sub-techniques against the linked live matrices -- chosen over asserting 64 precise sub-technique IDs that could be wrong in a security skill.
- **Tier-aware file split.** Both new skills keep their SKILL.md bodies tight (tier-2) and push bulky material (five patterns; 16 detection classes) into `references/` files (tier-3, loaded on demand), keeping always-loaded tier-1 metadata cheap across the catalog.
- **overview_l1 word budget.** `skill-security-scan`'s overview initially ran 164 words (over the 150 soft limit) because it enumerated all 16 classes; collapsed to representative examples to pass the quality heuristic, and re-synced into `skills.json`.

## Test results

- Emulated `make validate` (each validator invoked directly, `make` unavailable on host): JSON catalogs OK (247 skills); orphan-bundle audit **PASS 0/0**; quality heuristics **PASS 0 errors / 0 warnings**; no-personal-paths, unicode-safety (1560 pre-existing WARNs in legacy templates, 0 errors), supply-chain IOCs, workflow-security, solution-frontmatter all clean; `check_version_sync.py` green at 2.4.0 across all six surfaces.
- MCP skill-server pytest suite (`extensions/nexus-skill-server`): **43 passed / 0 failed** in 6.16s.
- All `[[wikilink]]` cross-links in the three edited skill files resolve to real catalog skills.
- Registry consistency: skills.json array (247) == statistics.total_skills (247); orchestration 15/15/15 and security 11/11/11 across array / statistics / marketplace; SKILL_INDEX 247 rows + Total line; no duplicate skill names.

## CI/CD edits

- None. GitHub Actions (`ci.yml`) is the active CI; its `validate` job runs the same validators emulated locally. Phase 2 added no new script command, environment variable, or dependency, and the two new skills auto-distribute via the recursive folder copy (no installer edit). 0 workflows touched, 0 proposed edits.

## Deviations

- T008 used hand-registration instead of the prescribed `build_skills_catalog.py` regeneration. Root cause (generator drift) recorded as WN-v30-2 with a suggested reconciliation step.

## Troubleshooting / environment notes

- `make` and `shellcheck` are unavailable on the Windows dev host (consistent with WN-v30-1), so `make validate` was emulated by invoking each validator directly. No shell scripts were touched this phase, so the ShellCheck pass is not applicable to the diff.
- The 1560 unicode-safety WARNs are pre-existing punctuation debt in `templates/ai-instructions/legacy/**`; the two new skill files and all edited files were verified ASCII-only (0 non-ASCII characters).

## Known gaps

See [`docs/releases/v3/v3.0/known-gaps.md`](../../known-gaps.md). One new open item this phase: WN-v30-2 (build_skills_catalog.py regenerates a materially different catalog than the committed one; hand-registration used; reconcile the generator before `make build-catalog` is safe). WN-v30-1 (Phase 1, ShellCheck deferred to CI) remains open.

## Next steps

- **Phase 3 -- core lifecycle commands I**: create the `/describe`, `/plan`, `/implement`, and `/test` thin-dispatcher commands over the retained skills (the `/test` fan-out guidance cross-links the new `agent-orchestration-primitives` skill).
