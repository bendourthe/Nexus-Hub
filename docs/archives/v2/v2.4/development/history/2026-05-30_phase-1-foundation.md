# Session History - v2.4.0 (adoption-compound-engineering-plugin) Phase 1: Foundation - knowledge base + scoring discipline

**Date**: 2026-05-30
**Plan**: [docs/archives/v2/v2.4/plans/adoption-compound-engineering-plugin.md](../../plans/adoption-compound-engineering-plugin.md)
**Phase**: 1 of 8 - Foundation: knowledge base + scoring discipline (A1, A4, WN-v23-1, BG-v23-1)
**Sub-tasks**: T001 (solution-knowledge-base skill + schema), T002 (solution-refresh skill), T003 (validate_solution_frontmatter.py + tests + installers), T004 (confidence-anchored-scoring reference), T005 (WN-v23-1 registry reconciliation), T006 (BG-v23-1 fenced-code-aware secret scan), T007 (testing + stabilization)
**Outcome**: Two new local zero-outbound skills shipped and registered; a stdlib parser-safety validator added and wired into both installers + make validate; a confidence-anchored scoring reference linked from two code-review skills; the two validation-blocking ingested gaps resolved (WN-v23-1 count drift root-caused as a three-way registry-vs-disk divergence and reconciled to 239 skills / 21 categories; BG-v23-1 secret-scan false positives eliminated with CommonMark fence tracking). All validators green; tests/validators 71 passed, tests/installer + tests/integrations 260 passed. Live skill-eval-loop run deferred (DF-v24-1). Ready to advance to Phase 2.

---

## Goal

Ship the solved-problems knowledge base + capture/refresh skills (comparison item A1) and the confidence-anchored scoring reference (A4), and clear the two validation-blocking ingested v2.3.0 known-gaps (WN-v23-1 count drift, BG-v23-1 secret-scan false positives) so new-skill additions validate cleanly. Every adopted item is local catalog content reusing only local processing: zero new outbound calls, zero new credentials, zero new dependencies.

## Steps taken

1. **Pre-implementation review**: read the full plan and the Phase-1 sub-tasks; an exemplar workflow skill (`continuous-learning/SKILL.md`) for the SKILL.md contract and the hand-curated skills.json style; `validate_skills.py` (the validator being modified) and the Makefile / ci.yml to learn which gates actually run; the v2.3.0 known-gaps to understand WN-v23-1 and BG-v23-1; an existing validator (`validate_no_personal_paths.py`) + its test + the `runner` conftest fixture for CLI / test parity; the installer copy-block region for the v2.3.0 validators; the marker-merge convention (`instruction_merge.merge_marker_section`, `<!-- NEXUS_HUB_START/END -->`); and the code-quality / security-review skills the A4 reference links from.

2. **T001 - solution-knowledge-base** (`catalog/skills/workflow/solution-knowledge-base/SKILL.md` + `references/schema.md`): a capture skill that documents a solved problem into `docs/solutions/<category>/<slug>.md`. Two-track frontmatter (bug: symptoms / root_cause / resolution_type; knowledge: applies_when), a generic framework-agnostic component taxonomy, parallel read-only research (context analyzer / solution extractor / related-docs finder return text only; one orchestrator write), a 5-dimension overlap score (update-vs-create), and a Discoverability Check using a dedicated `<!-- NEXUS_SOLUTIONS_START/END -->` marker block (distinct from the installer-managed `NEXUS_HUB` block). The field contract + YAML-safety quoting rule live in `references/schema.md`, linked on demand. Re-authored generically; no source-repo attribution in the artifact.

3. **T002 - solution-refresh** (`catalog/skills/workflow/solution-refresh/SKILL.md`): the lifecycle half (Keep / Update / Consolidate / Replace / Delete) with interactive + autofix modes (only Keep + pure-frontmatter Update auto-apply; the three destructive verdicts always confirm). Reuses `solution-knowledge-base/references/schema.md` rather than duplicating it; cross-links the capture skill, known-gaps-tracker, continuous-learning, and refactor-docs.

4. **T003 - parser-safety validator** (`scripts/validate_solution_frontmatter.py` + `tests/validators/test_validate_solution_frontmatter.py`): stdlib-only line-level linter detecting malformed `---` delimiters, unquoted ` #` (comment truncation), unquoted `: ` (mapping confusion), and reserved-indicator sequence items / scalars; exit 0 / 1 / 2; `--root` / `--path` / `--verbose` CLI matching the existing validators. Wired into `make validate` (no-op when `docs/solutions` is absent) and registered as an explicit-name copy step in BOTH `scripts/installer.sh` and `scripts/installer.ps1`. 11 pytest cases.

5. **T004 - confidence-anchored-scoring reference** (`catalog/skills/code-review/code-quality/references/confidence-anchored-scoring.md`): the 5 discrete anchors (0/25/50/75/100), fingerprint dedup, cross-reviewer promotion, mode-aware demotion, late suppression gate. Linked from `code-quality/SKILL.md` (new subsection) and forward-referenced from `security-review/SKILL.md` for the Phase-2 pipeline (A2) and run-penetration-test synthesis.

6. **T005 - WN-v23-1 registry reconciliation**: ran a three-way audit (disk vs skills.json vs SKILL_INDEX) that revealed the drift was far larger than the planned "1-skill" estimate - 6 conformant on-disk skills unregistered in skills.json, 3 mis-cased category values, and marketplace.json missing the `research` category. Wrote a one-shot reconcile script (importing `build_skills_catalog` for schema-faithful entry construction of the missing skills; curated tags + based_on for the 2 new skills) that registered all 8 missing entries, normalized categories to the lowercase directory ids, recomputed statistics + marketplace per-category counts (adding `research`), and appended the 6 missing SKILL_INDEX rows with a corrected Total line. Verified all three files agree at 239 skills / 21 categories and deleted the throwaway scripts. Added the 2 new pushy descriptions to `validate_skills.allowlist.json` for consistency with the 137 already-grandfathered ones.

7. **T006 - BG-v23-1 fenced-code-aware secret scan**: refactored `scan_for_secrets` to delegate to a new `scan_text_for_secrets` with CommonMark fence tracking; suppressed the low-confidence "Generic secret assignment" pattern inside Markdown fences while keeping high-confidence credential patterns active everywhere; added 5 pytest cases including the nested-fence regression.

8. **T007 - stabilization**: ran the validators directly (make unavailable on the host), `tests/validators`, `tests/installer` + `tests/integrations`, the strict-with-allowlist validator, `bash -n` on installer.sh, and a PowerShell parse of installer.ps1; did the static trigger-surface check for the two new skills and recorded the live-eval deferral; ran the post-phase documentation sequence.

## Troubleshooting

- **A literal BOM landed in `validate_solution_frontmatter.py`**: the first draft of `_strip_bom` embedded a literal U+FEFF in source. Replaced it on disk with an ASCII `ord(text[0]) == 0xFEFF` check and rewrote the file UTF-8-without-BOM, keeping the source ASCII-only.
- **2 of the 7 secret false positives survived the first fence fix**: a naive fence toggle was inverted by `user-documentation/SKILL.md`, which contains a Markdown code block that itself shows nested shell snippets. Root cause: an opening fence with an info string and a bare closing fence must be distinguished. Switched to CommonMark semantics (opening fence may carry an info string; a closing fence must be the same char, at least as long, and carry no info string). After the fix all 7 false positives are gone and a nested-fence regression test locks it in.
- **PowerShell heredoc + `bash -n` via WSL both unavailable on the host**: the audit/reconcile logic was run from temp `.py` files instead of a heredoc, and installer.sh was syntax-checked with the Bash tool (`bash -n`) rather than the PowerShell `bash` shim (which hit a distro-less WSL).

## Assumptions

- The on-disk `catalog/skills/` tree is the authoritative source of truth for the registry reconciliation (per AGENTS.md), so the 6 unregistered-but-shipping skills were registered rather than the statistic merely patched - this is the root-cause fix WN-v23-1's acceptance ("the three data files agree") requires.
- The transitional 250-char description rule (insight I-03) is superseded in practice by the AGENTS.md pushy-description guidance (137 of 239 skills are allowlisted); the 2 new skills follow the pushy-description directive and were allowlisted for consistency. CI does not enforce the strict rule.
- The `.ps1` parity rule applies to `.sh` scripts, not `.py` validators (which are cross-platform and copied by both installers); the T003 `.ps1` sibling was intentionally not created (NI-v24-1).
- `make` / `shellcheck` are unavailable on this Windows host, so validators / lint were invoked directly (same as prior phases).

## Testing results

- `tests/validators`: 71 passed (incl. 16 in test_validate_skills.py, 11 in test_validate_solution_frontmatter.py).
- `tests/installer` + `tests/integrations`: 260 passed (confirms the installer copy-block edits regress nothing).
- `make validate` equivalent (direct): skills.json OK (239), bundle audit PASS 0/0, quality pass 0 new warnings, no-personal-paths / unicode-safety / supply-chain-iocs / workflow-security / solution-frontmatter all exit 0; every new file ASCII-clean and bundle-referenced.
- `validate_skills.py --allow-existing`: PASS (0 errors, warnings only); strict secret scan reports 0 generic-secret false positives (was 7).
- `make lint` equivalent: `bash -n scripts/installer.sh` OK; `installer.ps1` parses clean (ShellCheck unavailable on the host).

## Deviations

- **NI-v24-1**: `scripts/validate_solution_frontmatter.ps1` intentionally not created (see Assumptions; recorded in known-gaps).
- **T005 scope expansion**: the WN-v23-1 fix grew from a statistic patch into a full three-registry reconciliation because the root cause was 6 unregistered skills + 3 mis-cased categories + a missing marketplace category. This is the root-cause resolution; recorded in the DEVLOG and known-gaps.
- **DF-v24-1**: the live skill-eval-loop trigger run was deferred (no model CLI on PATH; token-intensive), with a static trigger-surface check substituted - mirroring the v2.3.0 DF-v23-7 precedent.

## Next steps

- Phase 2: persona review pipeline (A2 / A3 / A8) backed by a re-authored generic persona agent library; it consumes the T004 confidence-anchored scoring reference shipped here.
- Fold the two new skills into the Phase-8 T037 live skill-eval-loop run (clears DF-v24-1).
- At the v2.4.0 version bump, refresh the AGENTS.md / README catalog-count prose to 239 skills / 21 categories (WN-v24-1) and update the CHANGELOG (T040).
