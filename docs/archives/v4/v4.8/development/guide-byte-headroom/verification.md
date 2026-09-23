# v4.8 guide byte-headroom verification

This release-scoped record qualifies the v4.8 WN-A guide-size repair for maintainers reviewing protected integration. It covers normalized HTML bytes, approved platform artwork, local `file://` browser rendering, and the rejected Gemini symbol experiment.

## Decision and change

The user chose to preserve the strict 500,000-byte ceiling. The guide was 498,735 normalized UTF-8 bytes before this change. Its Claude and ChatGPT SVGs each appeared twice with identical source; Cursor appeared twice and already had an identical hidden symbol (`hxm2`). Sharing those three local vectors reduced the guide to 495,467 bytes, saving 3,268 bytes and raising headroom from 1,265 to 4,533 bytes. The room photo remains inline because the WebGL `file://` texture path requires it.

Gemini also had duplicate geometry, but moving its mask and filters inside a shared `<symbol>` made the icon invisible in Chromium. Native-size screenshot inspection caught this even though the full-page mean pixel difference was below the permissive 1% threshold. Both Gemini SVGs were restored byte-for-byte. The final renders have slight Cursor edge antialiasing differences under `<use>`, without a visible shape change; Claude, ChatGPT, Gemini, and GitHub Copilot match in the inspected native-size row.

## Local evidence

- `tests/guides/test_nexus_hub_guide.py::test_home_lists_the_five_approved_platforms_from_ledger_bytes` passed after resolving local symbols to the staged approved SVG bytes. Gemini and GitHub Copilot remain direct byte matches.
- `tests/guides/tools/render_guide.py` produced dark and light Home renders at 420 and 1440 px with reduced motion before and after the final edit. `perceptual_diff.py` rounded each mean image difference to `0.00000`; PNG hashes and pixel bounding boxes differ, so these are near-zero-difference renders, not identical files. Gemini and Cursor were inspected at native size.
- The archived [before](platform-before.png) and [after](platform-after.png) crops show the Home platform row at native resolution on the dark 1440 px render. They are review evidence for visible logo integrity, not a claim that the PNGs are identical.
- The focused guide suite passed with 160 tests and one skip; 61 documentation validator tests and the Windows fast profile (17/17 with Git Bash first on PATH) passed. `git diff --check` passed. Hosted CI and post-merge results remain the publication gate.

## Closure gate

Keep WN-A open until the protected pull request passes required checks, merges to `develop`, and its post-merge smoke and provenance jobs pass. Do not archive the whole v4.8 release tree while other gaps remain open.
