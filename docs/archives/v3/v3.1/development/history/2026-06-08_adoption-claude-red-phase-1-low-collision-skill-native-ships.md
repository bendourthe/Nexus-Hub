# Session History -- v3.1.0 adoption-claude-red Phase 1: Low-collision skill-native ships

**Date**: 2026-06-08
**Plan**: [`docs/releases/v3/v3.1/plans/adoption-claude-red.md`](../../plans/adoption-claude-red.md)
**Phase**: 1 of 5 -- low-collision skill-native ships
**Branch**: `feat/adoption-claude-red` (fast-forwarded to `develop` tip `d55c5c6` before starting)
**Outcome**: complete; all four sub-tasks (T001-T004) closed, all quality gates green.

## Goal

Ship the two highest-value, lowest-collision offensive-knowledge skills (`security/ai-attack-patterns` and `security/pentest-reporting`), re-authored generically to Nexus-Hub's body contract and registered across all three catalog files. Per the MCP Registry Policy reverse-engineer-first decision tree, both are `skill-native` (tier 2): pure catalog content with no new code, dependency, credential, or outbound call. This phase deliberately precedes the Phase 2 scanner-allowlist tuning, so the work had to stay below the HIGH scanner gate without depending on an allowlist that does not yet exist.

## Subtasks completed

1. **T001 -- AI-attack-patterns skill.** Created `catalog/skills/security/ai-attack-patterns/SKILL.md` (160 lines) + `references/standards.md`. Offensive AI-security methodology (direct/indirect prompt injection, jailbreaking, RAG/knowledge-base poisoning, tool/agent abuse, unsafe-output handling), re-authored generically per the Reverse-Engineering Attribution Rule. Pushy `description` (trigger phrases + SKIP clause), `summary_l0` (12 words), `overview_l1` (<150 words), and the full body contract: When to Use (with authorized-use "When NOT to use"), a 7-phase Instructions methodology gated on a mandatory Phase 0 authorization step, Common Rationalizations, a binary Verification checklist with authorized-engagement preconditions, and Related Skills cross-linking `[[skill-security-scan]]` + the ai-development category. Optional `atlas_techniques` (AML.T0051/T0054/T0020) + `nist_ai_rmf` (MEASURE-2.6/2.7) frontmatter ship with the companion `references/standards.md` (each ID's quoted short title, rationale, public source URL).
2. **T002 -- Pentest-reporting skill.** Created `catalog/skills/security/pentest-reporting/SKILL.md` (169 lines). Pentest report-writing methodology: report + finding anatomy, consistent CVSS base/temporal/environmental scoring, reproducible redacted evidence capture, risk-led executive summary, prioritized remediation, a retest-to-closure workflow, and a markdown report skeleton. Full frontmatter + body contract, cross-linking `[[final-report]]`, `[[incident-postmortem]]`, `[[exploitability-analyzer]]`, `[[security-review]]`, `[[security-patch-advisor]]` and the `/review pentest` command. No payloads.
3. **T003 -- Register both skills + reconcile counts.** Hand-registered both in all three registries (hand-edit over generator regen -- see Key decisions): 2 rows in `data/SKILL_INDEX.md`, 2 full entries in `data/skills.json` (schema-matched to `exploitability-analyzer`; security 100/100/95), and the `security` `skill_count` 11 -> 13 + description refresh in `data/marketplace.json`. The headline catalog total was reconciled to 250 across every prose surface, closing a pre-existing multi-surface drift.
4. **T004 -- Stabilization.** Emulated `make validate` (all green) and ran the skill-security scanner gate (clean, 0 HIGH/CRITICAL). Confirmed cross-links resolve, the new `references/standards.md` is referenced from SKILL.md (no orphan), and registries agree at 250.

## Key decisions

- **Hand-registration over `build_skills_catalog.py` regen.** Per the v3.0.0 WN-v30-2 finding, the generator rewrites curated `data/` (category casing, `long_description`/`size`/ordering), so registration was done by hand to keep every changed line traceable. The two `skills.json` entries were inserted adjacent to the existing security cluster.
- **Count reconciliation to the truthful post-add total (250).** The catalog `skill_count` sum was 248 (= marketplace.json description), but AGENTS.md read 247 and README read 245 (catalog bullet) / 247 (tagline + post-install). Adding 2 skills makes the truthful total 250, so every catalog-total surface was set to 250 -- this is the T003-mandated count-prose reconciliation, which incidentally closed the pre-existing 245/247/248 drift. The CATALOG-COVERAGE.md role matrix is not a headline-total surface and was left unchanged.
- **Payload discipline ahead of the Phase 2 allowlist.** Because Phase 1 ships before the scanner allowlist exists, `ai-attack-patterns` keeps example payloads to benign prompt-injection text in fenced blocks and describes data-exfiltration-via-injection conceptually (reserved `attacker.example` placeholder) rather than as a runnable exfil command. The scanner confirmed this: a single MEDIUM prose match, no HIGH/CRITICAL.
- **Authoritative gate vs. default-mode lint.** `validate_skills.py` default mode flags descriptions > 250 chars as errors (150 catalog-wide, incl. both new skills), but neither `make validate` nor CI runs default mode, and the cap conflicts with the mandatory pushy-description rule. The long descriptions were kept intentionally (WN-v31cr-1) rather than mutilated to chase a non-gate.
- **Framework-mapping accuracy.** `ai-attack-patterns` declares only high-confidence ATLAS / NIST AI RMF identifiers (ATLAS prompt-injection AML.T0051 is in-repo-validated via `skill-security-scan`), with `references/standards.md` quoting each framework's short title and linking the public source rather than asserting uncertain sub-technique IDs.

## Test results

- Emulated `make validate` (each validator invoked directly; `make` unavailable on host): JSON catalogs OK (**skills.json 250 skills**); orphan-bundle audit **PASS (0 errors, 1 pre-existing warning)**; quality heuristics **0 errors / 0 warnings on the two new skills**; no-personal-paths, unicode-safety (both new files ASCII-clean; 1051 pre-existing WARNs elsewhere, 0 errors), supply-chain-iocs, workflow-security, solution-frontmatter all clean; `check_version_sync.py` green.
- Skill-security scanner gate (`scan_skill_security.py catalog/skills catalog/mcp-configs --fail-on high`): **exit 0, clean**. The two new skills together: 3 files scanned, score **10/100 (LOW)**, one MEDIUM finding (class 7 system-prompt-leakage) on an `ai-attack-patterns` prose line, **0 findings on `pentest-reporting`**. Fence-aware prose capping confirmed empirically -- the fenced injection examples did not fire.
- All `[[wikilink]]` cross-links in the two new skill files resolve to real catalog skills.
- Registry consistency: skills.json array == 250; security `skill_count` 13 in marketplace; SKILL_INDEX gained 2 security rows; no duplicate skill names.

## CI/CD edits

- None. GitHub Actions (`ci.yml`) is the active CI; its `validate` job loads `skills.json` and runs the scanner gate over `catalog/skills` + `catalog/mcp-configs`, so the two new skills auto-discover. The phase added no new script command, environment variable, or dependency, and skills auto-distribute via the installer's recursive folder copy (no installer edit). 0 workflows touched, 0 proposed edits.

## Deviations

- None. The plan was followed exactly (T001-T004 as written).

## Troubleshooting / environment notes

- `make` and `shellcheck` are unavailable on the Windows dev host (consistent with prior phases' WN), so `make validate` and `make scan` were emulated by invoking each validator and the scanner directly. `make lint` is not applicable -- the phase added only Markdown + JSON, no shell surface (WN-v31cr-2, covered by CI).
- `data/marketplace.json` has no `statistics.total_skills` field; the catalog total lives in the `plugin.description` string (bumped 248 -> 250).

## Known gaps

See [`docs/releases/v3/v3.1/known-gaps.md`](../../known-gaps.md). Three new open items this phase, all WN: WN-v31cr-1 (the default-mode 250-char description cap is not a gate and conflicts with the pushy-description rule; long descriptions kept by design), WN-v31cr-2 (local make/shellcheck absent, covered by CI), WN-v31cr-3 (both v3.1.0 feature branches write `docs/v3/v3.1/known-gaps.md`, so the file needs a manual merge at develop-integration; IDs namespaced `-v31cr-` to avoid entry collisions). 0 resolved (Phase 1 is the first phase).

## Next steps

- **Phase 2 -- scanner allowlist prerequisite gate**: tune the `nexus-skill-scanner` producer-catalog allowlist so authorized red-team payloads inside `catalog/skills/security/` skills are capped below HIGH, reusing the existing fence-aware/prose-capping mechanism (not a blanket suppression), scoped to the `security` category and fenced/prose contexts only. Ship regression tests proving the planted-malicious fixture still scores CRITICAL, the known-clean fixture still scores LOW, an authorized-payload security skill scores below HIGH, and the same payload in a non-security/third-party skill is NOT allowlisted. This gate is the prerequisite for the payload-bearing Phase 3-4 fold-ins.
