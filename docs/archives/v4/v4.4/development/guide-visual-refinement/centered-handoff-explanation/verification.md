# Centered handoff explanation

Moved the handoff explanation from below the sessions into the center callout, shortened it, and added a subtle divider beneath the usage-reset message. The explanation retains the shared commands, project-file persistence, and continuation from saved progress.

## Verified

- 34 existing focused regression tests passed; no new test was needed for this text/layout adjustment.
- Twelve browser checks passed across six widths from 320 to 1440 pixels in both themes. Exactly one explanation exists, inside the center callout. No page errors or horizontal overflow; desktop session panels remain aligned and equal in height.
- Inspected the desktop dark and mobile light screenshots; final screenshots are saved in both themes at 420 and 1440 pixels.
- Unrelated markup and CSS declarations are preserved. The offline guide is 399,921 normalized UTF-8 bytes, below the inherited 400,000-byte gate.
- No outstanding work for this change; previously tracked unrelated issues remain outside scope. No publication performed.

## Reproduce

```powershell
python -m pytest -q tests/guides/test_v444_phase12_home.py tests/guides/test_v441_phase1_contract.py tests/guides/test_guide_animation_lifecycle.py
```
