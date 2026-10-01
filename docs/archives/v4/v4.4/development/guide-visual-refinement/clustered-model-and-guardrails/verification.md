# Clustered model illustration and six guardrail pills

## Completed

Replaced the Model SVG with a transparent irregular network of differently sized coral, amber, and teal nodes joined by thicker pale edges. Added past documents and layout checks to the existing four guardrail pills. The six pills use two rows of three when the figure is wider than 380 pixels and three rows of two in narrower figures to preserve legibility.

The added labels map to registered hooks: old-version-docs-guard warns before edits to historical release documents, while html-responsive-guard blocks fixed text-width patterns. Existing action examples, platform logos, floating Nexus logo, and equal-height desktop panels remain intact.

## Verified

- 59 focused tests passed; two existing Python escape-sequence warnings remain. See focused-tests.txt.
- Twelve browser layout checks passed: 320, 420, 760, 1000, 1024, and 1440 pixels, in both themes. No page errors, horizontal overflow, or wrapped/clipped pills. Desktop columns remain equal in height and aligned at the top.
- Visually inspected the saved 420-pixel and 1440-pixel screenshots in both themes. The 1440-pixel figure has exactly two rows of three pills.
- Unrelated markup and CSS declarations match the preceding commit. Two long source comments were shortened to accommodate the richer SVG within the inherited 400,000-byte gate; normalized UTF-8 guide size is 399,917 bytes. See preservation.json.
- Local verification only; no publication performed. The previously tracked Foundations 320-pixel internal overflow remains outside this change.

## Reproduce

```powershell
python -m pytest -q tests/guides/test_v443_phase2_guardrails.py tests/guides/test_v444_phase12_home.py tests/guides/test_v441_phase2_home.py tests/guides/test_v441_phase1_contract.py tests/guides/test_guide_animation_lifecycle.py
```
