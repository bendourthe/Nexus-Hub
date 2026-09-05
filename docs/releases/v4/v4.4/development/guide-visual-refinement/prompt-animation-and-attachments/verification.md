# Readable prompt animation and compact attachments

Updated the two Foundations prompt figures and the checkout attachment cards.

## Completed

- Inactive prompt segments have no background highlight or underline. Inline filenames also have transparent backgrounds and borders. Each segment gains its colored highlight and dotted underline when the corresponding legend box activates.
- Preserved the cumulative shared sequence and reduced-motion behavior. Both prompts now use 1.8-second steps; the contract's final step uses 2.2 seconds. The completed-state hold increased from 2.4 to 3.2 seconds.
- Replaced the large previews with compact PNG, PDF, and folder thumbnails to the right of their labels and filenames. Each thumbnail follows the height of its own text, including when a filename wraps.
- Removed the helper sentence below the attachment cards. All three preview buttons remain operable.

## Verified

- 145 focused tests passed; one skipped. New behavioral checks prove that both prompts remain plain before activation, the first step lasts longer than a second, and text and legend boxes activate together. Existing checks cover full sequence order, reduced motion, preview behavior, and offline size. See `focused-tests.txt`.
- 12 responsive checks passed at 320, 420, 760, 900, 1024, and 1440 pixels in both themes. Thumbnails sit to the right of their text and match its height. No clipped labels, page errors, or horizontal overflow. All 36 preview-open/close interactions and focus-return checks passed. See `layout-checks.json`.
- Four live timing cases passed across both prompts and themes: plain state, first segment after one second, and second segment after two seconds. All text and legend states match. See `animation-checks.json` and the plain/active screenshots.
- Desktop and mobile layouts and both prompt animation states were visually inspected. Home and Training markup, section order, and the shared sequence engine are unchanged. See `preservation.json`.
- The guide is 399,752 normalized UTF-8 bytes, below its existing 400,000-byte test gate.

## Open

Nothing outstanding for these requested changes. The previously recorded Foundations internal overflow remains outside this change; the full guide suite was not rerun.

## Publication

Local commit only. No push or release.
