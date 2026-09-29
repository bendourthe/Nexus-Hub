# Plain-language Home examples

Updated the two requested Home figures in `guides/website/nexus-hub-guide.html` while preserving the other sections and their content.

## Completed

- Added Claude, ChatGPT, Cursor, and Gemini marks below Platform Permissions and Claude Code/Codex marks beside the illustrated session titles. Artwork is cloned from the existing platform figure, with unique IDs for gradient references.
- Replaced technical hook labels with readable descriptions of password checks, project history protection, oversized-file checks, and keeping AI memory out of shared project files. Invisible metadata retains the mapping to shipped hooks for validation.
- Replaced the action examples with updating a welcome message, saving a password in project settings, and erasing saved project history. Both safety columns stretch to the same height.
- Renamed the handoff heading, enlarged its subtitle and dialogue, and used an appointment-booking example with natural User prompts, a three-phase Nexus Hub plan, concrete completed work, a usage-limit interruption, and Codex continuation.

## Verified

- 28 browser layout checks: both figures at 320, 420, 760, 999, 1000, 1024, and 1440 pixels in dark and light themes. No page errors, horizontal overflow, clipped text, or desktop column-height differences. See `layout-checks.json` and the PNG captures beside this file.
- 169 distinct focused tests passed, with one skipped. The initial run passed 167 tests; its two wording/alignment failures were corrected, and all 22 tests in the affected modules passed on the final retest. Logs: `focused-tests.txt` and `final-retests.txt`.
- Focused coverage includes the shipped-hook mapping, platform artwork, responsive containment, animation lifecycle and reduced motion, heading contracts, and offline file-size contract.
- Browser comparison confirms unchanged section order, all content outside the two figures preserved, and identical CSSOM for unrelated rules. SVG IDs remain unique, and all JavaScript parses. See `preservation-checks.json`.
- The guide is 399,265 normalized UTF-8 bytes, below its existing 400,000-byte test gate. Only insignificant CSS comment/indentation and Home block-boundary whitespace was compacted to accommodate the requested additions; approved SVG artwork was preserved.

## Open

Nothing outstanding in these two figures. The previously recorded two-pixel Foundations Agentic Platforms internal overflow at 320 pixels remains outside this change; the full guide suite was not rerun.

## Publication

Local commit only. No push or release.
