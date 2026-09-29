# Handoff callout and plan filename

## Completed

Renamed all five example references to booking-feature-plan.md. Emphasized Example: with bold teal text. Made the No need to wait message a centered amber callout with larger text and a fixed clock icon. Removed the prior sideways icon motion so the clock stays centered. Inline command and filename chips stay together when they fit the available line.

## Verified

- 34 focused regression checks passed. The animation lifecycle test now verifies that the centered clock stays still across visibility and reduced-motion states.
- Twelve browser checks passed across 320, 420, 760, 1000, 1024, and 1440 pixels in both themes: no page errors, page overflow, or clipped table/checklist content; desktop panels remain aligned and equal in height. All five plan references match the new filename.
- Reviewed desktop screenshots in both themes and the mobile layout. Saved final screenshots at 420 and 1440 pixels.
- Unrelated markup and styling preserved; normalized UTF-8 guide size is 399,948 bytes, below the inherited 400,000-byte gate. No new dependencies or source-comment compaction.
- No outstanding issue for this change. The previously tracked Foundations overflow remains outside scope. No publication performed.

## Reproduce

```powershell
python -m pytest -q tests/guides/test_v444_phase12_home.py tests/guides/test_v441_phase1_contract.py tests/guides/test_guide_animation_lifecycle.py
```
