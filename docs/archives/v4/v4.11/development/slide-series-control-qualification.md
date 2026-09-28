# Slide series control qualification

**Scope**: The v4.11 MT-9 follow-up checks the generated handbook's slide chart-series toggles, not arbitrary controls. The browser measurement already visits every inventoried slide and calls `DECK_INTEGRITY` while each slide is current.

The original proposal to inspect click listeners through CDP is insufficient here. `dual-view-figures.js` attaches a click listener to `document`, and `dual-view-runtime.js` attaches another to the deck. Both are present in the ancestor chain even when a series button has been moved outside the chart figure and neither handler can complete the intended mark update. A broad listener-presence rule would therefore miss the reported defect.

The targeted contract asks whether each slide `button[data-dv-series]` has a nearest `figure[data-dv-figure]`, which the shipped figure handler requires. The negative fixture moves a generated Alpha toggle after its closing figure. Before the check, measurement did not report its missing owner. With the check, it reports `series-control-outside-figure`; the normal figure is not reported. Chromium interaction confirms the normal toggle hides its plotted series, while the detached button leaves those marks visible even though its own `aria-pressed` attribute changes. The owning measurement module passes 53 tests.

This is a structural precondition, not a generic proof that every visible control performs its intended action. A button inside the figure can still be miswired, and controls with other event contracts are outside this rule. MT-9 remains open for a future control-specific interaction oracle or another bounded contract with a negative control; listener presence alone is not that oracle.
