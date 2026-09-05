# Phase 1 platform handoff

## Completed

Replaced the booking plan list with a three-phase table containing a description and illustrative model-tier/effort recommendation. Claude starts Phase 1, saves tasks 1 and 2 as complete with tasks 3 and 4 pending, and reaches its usage limit. Codex identifies booking.md and Phase 1, shows the identical saved checklist, resumes work, then shows all four tasks complete. Its final message asks the user to run /implement Phase 2 next.

Styled the checkboxes for clear checked/pending states in both themes. They are disabled, labeled native inputs because these are illustrated sessions. Phase labels stay on one line. No new animation or runtime dependency was introduced.

## Verification

- Twelve responsive/theme checks passed: 320, 420, 760, 1000, 1024, and 1440 pixels in dark and light themes. No page errors or horizontal overflow; table cells and checklist labels fit. Desktop session panels have identical top positions and heights.
- Inspected all four saved screenshots at 420 and 1440 pixels in both themes.
- The focused suite passed 52 checks and found one obsolete 240-word ceiling. The requested table and three checklist states bring the illustration to 300 words; its ceiling is now 320. The affected test passed on rerun. The original Home prose ceilings remain unchanged. See focused-suite.txt and word-budget-retest.txt; the rerun reports two existing Python escape-sequence warnings.
- Updated the existing handoff test to verify three table rows, matching task labels, saved states [complete, complete, pending, pending], and the final completed checklist and Phase 2 instruction.
- Unrelated markup and CSS declarations are unchanged. Three historical source comments were compacted to keep the richer illustration below the inherited 400,000-byte gate. The guide is 399,931 normalized UTF-8 bytes. See preservation.json and source-comment-compaction.json.
- Previously tracked Foundations overflow is outside this change. No publication performed.

## Reproduce

```powershell
python -m pytest -q tests/guides/test_v444_phase12_home.py tests/guides/test_v441_phase2_home.py tests/guides/test_v441_phase1_contract.py tests/guides/test_guide_animation_lifecycle.py
```
