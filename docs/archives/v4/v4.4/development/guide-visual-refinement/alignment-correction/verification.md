# Screenshot alignment correction

Date: 2026-09-05

## Changes

- Stretch the left safety boundary to the height of the three example boxes, with its internal elements spaced across the available height.
- Center the One install heading and explanation within the top box; stack the document icon above the text on narrow screens.
- Remove platform connector dots and their animation. Retain the finite handoff animation and safety demonstration.
- Account for grid gaps when positioning the horizontal connector endpoints and join every vertical stem to its arrowhead.

## Verification

- 45 affected guide tests pass, including platform layout, safety structure, animation lifecycle, reduced motion, and the strict 400,000-byte gate. See [test output](tests.txt).
- [Geometry checks](geometry.json) cover 320, 420, 700, 999, 1000, 1024, and 1440 pixels in dark and light themes: no horizontal overflow or page errors; centered source text at every width; aligned safety boundaries and continuous four-platform connectors at desktop widths.
- Inspected desktop dark and mobile dark/light screenshots. The existing mobile layout retains its single connector to the platform group.
- [Content parity](content-parity.json) confirms all v4.4.5 text, 27 sections in their original order, and original IDs remain unchanged.
- Guide size: 399,724 normalized UTF-8 bytes. Full repository CI was outside this focused correction.

## Screenshots

- [Desktop safety](safety-dark-1440.png)
- [Desktop platforms](platforms-dark-1440.png)
- [Mobile safety](safety-dark-420.png)
- [Mobile platforms](platforms-light-420.png)
