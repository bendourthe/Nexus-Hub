# Known Gaps -- v2.3.0

This file tracks per-version unfinished work, deferred items, deviations from plan, and bugs discovered during phase implementation. The next phase plan and the version-bump checklist read this file to decide what carries forward.

**Plan**: [docs/v2.3.0/plans/adoption-ecc-cybersec-skills.md](plans/adoption-ecc-cybersec-skills.md)
**Status**: Phases 1-2 of 9 closed (skill-native foundations + CI validators); Phases 3-9 pending
**Last updated**: 2026-05-28 (Phase 2 close -- four standalone CI validators shipped under `scripts/`: `validate_no_personal_paths.py`, `validate_unicode_safety.py`, `scan_supply_chain_iocs.py`, `validate_workflow_security.py`. Wired into the `make validate` target with sensible exclusions for archived prior-version docs (`docs/v2.0.0`, `docs/v2.1.0`, `docs/v2.2.0`) and one pre-existing template directory (`templates/ai-instructions`, BOMs). Registered as explicit-name copy steps in both `scripts/installer.sh` (~line 1493) and `scripts/installer.ps1` (~line 1911) per the AGENTS.md installer-aware-changes rule. Covered by 31 pytest cases under `tests/validators/` (new subdirectory) exercising clean-passes and dirty-fails invariants. `.github/workflows/ci.yml` updated to invoke all four validators and the new pytest suite. Zero runtime dependencies added; all four validators are local, read-only, zero-outbound. Full test sweep: 31 (validators) + 254 (integrations + installer) + 370 (catalog/hooks) = 655 passed, 3 skipped.)

## Summary

| Category | Open | Resolved this version |
|---|---|---|
| NI -- Not implemented (skipped subtask) | 0 | 0 |
| DF -- Deferred (intentionally) | 1 | 0 |
| BG -- Bug or unresolved test failure | 1 | 0 |
| MT -- Missing tests / coverage gap | 0 | 0 |
| WN -- Warning or suppressed lint rule | 3 | 0 |
| QG -- Quality gate bypassed | 0 | 0 |
| **Total** | **5** | **0** |

## Open Items

| ID | Title | Category | Source phase | Plan reference | Reason | Suggested next step |
|---|---|---|---|---|---|---|
| BG-v23-1 | `scripts/validate_skills.py` reports 7 pre-existing "Generic secret assignment" false positives in unrelated skills | BG | v2.3.0 Phase 1 (sub-task T003) | [adoption-ecc-cybersec-skills](plans/adoption-ecc-cybersec-skills.md) | The strict validator flags 7 lines across `ai-development/google-antigravity-sdk/SKILL.md`, `documentation/user-documentation/SKILL.md` (2), `infrastructure/cd-pipeline-generator/SKILL.md` (2), and `infrastructure/rollback-strategy-advisor/SKILL.md` (2) as potential generic-secret assignments. Manual inspection confirms each is a documentation example, not a real secret (e.g., `password = "..."` inside a fenced code block teaching against the pattern). The Phase 1 work did not introduce any of these; they predate the phase. They block the strict-mode validator but not `make validate` (which runs `--bundles-only`). | Either (a) refine `SECRET_PATTERNS` in `scripts/validate_skills.py` to ignore matches inside fenced code blocks in `.md` files, or (b) add an in-skill suppression mechanism. Track as a quality-tooling pass; non-blocking for Phase 2. |
| WN-v23-1 | `data/skills.json` skill entry count drifted from `statistics.total_skills` before Phase 1 | WN | v2.3.0 Phase 1 (sub-task T003) | [adoption-ecc-cybersec-skills](plans/adoption-ecc-cybersec-skills.md) | At Phase 1 start, the array contained 207 skill entries while `statistics.total_skills` was `206`. The Phase 1 work added 2 entries (now 209) and bumped the statistic from `206` -> `208` per the plan's explicit instruction, leaving the same 1-skill drift behind. Drift was not introduced by Phase 1; the rebaseline in v2.2.0 known-gaps line 6 set `total_skills` to 207, and `data/skills.json` was bumped one entry beyond that without updating the statistic. | At the next `make build-catalog` / data rebaseline (likely Phase 5 or 6 of this plan), reconcile `statistics.total_skills` against `len(d['skills'])` and re-derive the per-category counts; the build script under `infrastructure/tools/build_skills_catalog.py` is the natural home. |
| WN-v23-2 | `templates/ai-instructions/**/*.md` ship with a UTF-8 BOM | WN | v2.3.0 Phase 2 (sub-task T006) | [adoption-ecc-cybersec-skills](plans/adoption-ecc-cybersec-skills.md) | The new `validate_unicode_safety.py` flags 15 `.md` files under `templates/ai-instructions/coding-instructions/` and `templates/ai-instructions/legacy/coding-instructions/` plus `templates/ai-instructions/generic-instructions.md` as starting with a `U+FEFF` (UTF-8 BOM). BOM is exempted for `.ps1` (Windows PowerShell convention) but not for Markdown; these files predate Phase 2 and a BOM in distributed Markdown can confuse renderers. To unblock Phase 2 the Makefile excludes the whole `templates/ai-instructions` subtree from the Unicode pass. | Strip the BOMs (`python -c "p=open('file','rb').read(); open('file','wb').write(p.lstrip(b'\\xef\\xbb\\xbf'))"` per file), drop the `--exclude templates/ai-instructions` from the Makefile call, and re-run `make validate`. Out of scope for Phase 2; aim for Phase 5/6 (skill-quality tooling) or earlier as a stand-alone cleanup. |
| WN-v23-3 | `templates/development/compliance-review/**/*.md` ship with non-ASCII punctuation (em-dashes) | WN | v2.3.0 Phase 2 (sub-task T006) | [adoption-ecc-cybersec-skills](plans/adoption-ecc-cybersec-skills.md) | The new `validate_unicode_safety.py` emits ~1034 WARN-level findings on em-dashes and curly quotes across English Markdown in `templates/development/compliance-review/` and elsewhere. Warnings are not blocking (exit 0) but they violate the CLAUDE.md "Critical Rules" ASCII-only constraint for English Markdown. | Run `validate_unicode_safety.py --strict --path templates/development/compliance-review/` to enumerate, then bulk-replace em-dashes with `--` and curly quotes with straight ASCII via a one-shot script. Out of scope for Phase 2 (per the user-CLAUDE.md "every changed line must trace to the user's request" rule). |
| DF-v23-1 | `catalog/hooks/tests/test_classification_audit.py` contains real personal paths in test fixtures | DF | v2.3.0 Phase 2 (sub-task T006) | [adoption-ecc-cybersec-skills](plans/adoption-ecc-cybersec-skills.md) | The new `validate_no_personal_paths.py` correctly flags 8 occurrences of `/Users/bdour/...` in this test file. These are legitimate user-reported real-world test cases (the file's docstring records them as "User-reported mislabeled commands"). Redacting them in place would require modifying upstream test fixtures, which is out of scope for Phase 2 and risks invalidating the audit. The Makefile excludes `catalog/hooks/tests/` from the no-personal-paths pass to unblock the gate. | Either (a) replace the real username `bdour` with a placeholder (`<user>`) in the test fixtures and confirm the classification logic still parses them correctly, or (b) leave the fixtures as-is and keep the exclusion. Decide as part of Phase 5/6 skill-quality work. |

## Resolved

| ID | Title | Category | Resolved in | Detail |
|---|---|---|---|---|

(none yet -- Phase 1 introduced no regressions to resolve, and no v2.2.0 carryover items map onto Phase 1's skill-native foundations work; the v2.2.0 carryovers begin landing in Phases 7-9.)

---

**File lifecycle**: This file is appended by `/implement-phase` Phase 8 step 8.4 (per-phase append), swept by `/wrap-up-session` Phase 6 (catch-all from live conversation), and finalized by `/update-version` at the v2.3.0 -> next-version bump. After finalization, the next plan run by `/generate-plan` will read this file to decide which items carry forward.
