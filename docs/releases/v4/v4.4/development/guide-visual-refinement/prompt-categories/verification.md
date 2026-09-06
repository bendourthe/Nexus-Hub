# Consistent prompt categories and chat attachments

Updated the two requested Foundations prompt figures in the canonical offline guide.

## Completed

- Moved the clickable image, PDF, and context-folder tiles above the checkout prompt, matching the reading order of an agentic chat.
- Renamed the image to `checkout-layout.png`. The built-in illustration is rasterized once with the browser canvas and displayed as a PNG in both the thumbnail and enlarged preview; no network or additional file is required.
- Split the checkout prompt and its matching legend into Request, Attachments, Goal, and Context. The folder reference belongs to Context; the image and PDF references belong to Attachments; the expected repair belongs to Goal.
- Renamed Query to Request in the contract prompt, its explanatory sentence, and the corresponding vague-prompt diagnosis.
- Kept shared category colors identical across both figures: teal Request, amber Goal, and blue Context. Attachments uses purple, while the contract example retains cyan Format.
- Gave both legends a shared responsive layout: four columns on desktop, two on tablets, one on phones. Phone labels use 20-pixel type to prevent Attachments clipping.

## Verified

- 144 focused tests passed; one skipped. See `focused-tests.txt`. Coverage includes annotations, document-order animation, reduced motion, preview interaction, shared heading size, static guide contracts, and the offline byte gate.
- 12 browser layout/color cases passed: 320, 420, 760, 900, 1024, and 1440 pixels in dark and light themes. No page errors, external requests, horizontal overflow, or clipped prompt/legend text. Both figures' shared category colors and every legend swatch match their highlights.
- 36 keyboard-operated previews passed: actual PNG decoding, image/PDF/folder opening, Escape close, focus return, folder expansion, and containment within the viewport. See `checks.json`.
- Desktop and mobile screenshots in both themes were visually reviewed, including the enlarged PNG. PNG, PDF, and folder preview captures are included beside this note.
- Home and Training markup and the section order are unchanged. All JavaScript parses. The guide is 399,794 normalized UTF-8 bytes, below the existing 400,000-byte test gate. See `preservation.json`.

## Open

Nothing outstanding in these two figures. The previously documented Foundations Agentic Platforms internal overflow remains outside this change; the full guide suite was not rerun.

## Publication

Local commit only. No push or release.
