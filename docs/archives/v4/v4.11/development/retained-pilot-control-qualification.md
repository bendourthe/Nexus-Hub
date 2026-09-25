# Retained report pilot control qualification

This record qualifies v4.11 MT-9 against the retained report pilot at `docs/releases/v4/v4.11/development/interactive-handbooks/phase-6-native-attempts/report-final/pilot.html`. It is for maintainers deciding whether every meaningful control in that artifact was exercised; it does not turn the pilot's separate whole-page visual result into a pass or reconstruct the original unretained four-button artifact.

## Artifact and inventory

- **Base revision**: `f3ee786a`, the protected `develop` merge of PR #297.
- **Artifact SHA-256**: `87A8A313851648EC6D5B393AF6666B61F4333AA0052E510946FF5D76F66E2FEA`.
- **Browser**: Playwright Chromium 151.0.7922.34 at 1366x768 for the focused control suite.
- **Census**: The independent expected map in `tests/skills/test_retained_report_pilot_controls.py` exactly matched 34 initial live-DOM controls: two reading-to-deck buttons, ten internal links, twelve chart controls across reading and presentation views, four review disclosures/enlarge buttons, and six deck controls. The chart runtime creates two axis-ceiling inputs after load; source-tag inspection alone found only 32 controls and was rejected. Two additional Close image buttons created on demand were both clicked and verified.
- **Declared scorer subset**: [retained-pilot-control-inventory.json](retained-pilot-control-inventory.json) independently declares both slide-series effects on plotted marks and a setup-dependent Reset effect. The scorer's contract is declared slide controls only; the focused browser suite covers the remaining page, slide, and deck controls.

## Browser exercise

The focused suite opened the retained file URL in a real Chromium page, blocked and asserted zero outbound requests, and asserted zero page errors. It exercised both reading-to-deck buttons; all ten links and their correct reading or slide targets; both chart series in each view against actual plotted-mark visibility; zoom in each view against SVG width; the generated axis-ceiling inputs against changed SVG axis labels and status; setup-dependent Reset in each view against restored marks and zoom; all four disclosures; both enlarged-image dialogs and their dynamic Close image buttons with focus restoration; and deck Back, Next, picker, Replay, Fullscreen, and Exit against their respective slide, animation, browser fullscreen, and reading-view states. Replay was checked by replacement of the browser Animation object, not by a button-state flag. Fullscreen was checked as a toggle from its observed starting state because a user click on Presentation Mode can itself enter fullscreen.

The stage-series negative control installed a capture listener that made the otherwise valid North toggle inert. The same plotted-mark assertion used by the positive cases then raised `plotted marks stayed visible`; the test passed only because it observed that expected failure. This demonstrates the gate detects a control whose click produces no intended chart effect.

## Results and boundary

- `NEXUS_REQUIRE_RENDER=1 python -m pytest tests/skills/test_retained_report_pilot_controls.py -q`: 31 passed, zero failed or skipped, in 8.62 seconds.
- `python -m ruff check tests/skills/test_retained_report_pilot_controls.py`: clean.
- Standalone `measure_handbook.py` CLI on the retained pilot with the archived inventory and the functional-verification detector: exit 1; whole-page `status=fail` with 629 page errors; `control_behavior_guard=pass` with three observations and zero control findings. The browser read `inline -> none` for each series and `none -> inline` for Reset. The 629 page errors are a separate visual-quality result and were not waived or reclassified by this control pass.

This qualifies the declared-control method against a complete control census for one retained real artifact. It does not claim automatic discovery for an arbitrary future handbook: any control absent from an independent inventory remains `unchecked`, and the original four-button source artifact cannot be retroactively tested. MT-9 stays open until this record, inventory, and browser test pass protected integration and post-merge verification.
