# Wider Model illustration and guardrail pills

Updated the Home safety figure in `guides/website/nexus-hub-guide.html`.

## Completed

- Widened the Model box to 90 percent of the platform panel's inner width and included a static neural-network illustration with connected input, hidden, and output layers.
- Replaced the four descriptions with highlighted rounded pills in the requested order: project history, exposed passwords, oversized files, data retention. Existing hook metadata remains attached to each corresponding label.
- Kept the Nexus Hub logo, platform logos, right-hand action examples, and existing animations unchanged.

## Verified

- 59 focused tests passed. Coverage includes safety containment, shipped-hook mapping, Home contracts, the offline byte gate, and animation lifecycle. See `focused-tests.txt`.
- 12 layout checks passed: 320, 420, 760, 1000, 1024, and 1440 pixels in both dark and light themes. The Model box is wider than 100 pixels at every width; the neural-network SVG is present; each pill stays on one line; no horizontal overflow or page errors. Desktop left and right panels retain matching top edges and heights. See `layout-checks.json`.
- Desktop and mobile screenshots were visually reviewed in both themes. The drawing stays legible and the pills wrap between boxes without splitting their labels.
- Markup outside the Model box and pill list is preserved, apart from insignificant whitespace between tags in the safety figure. See `preservation.json`.
- The static drawing and compact labels keep the guide at 399,999 normalized UTF-8 bytes, below its existing 400,000-byte test gate. No external assets or runtime dependency was added.

## Open

Nothing outstanding for the requested figure. The previously recorded Foundations internal overflow remains outside this change; the full guide suite was not rerun.

## Publication

Local commit only. No push or release.
