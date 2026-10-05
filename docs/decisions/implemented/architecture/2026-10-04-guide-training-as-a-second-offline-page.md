# Decision: The guide's Training becomes a second offline page, with one source for the parts both pages share

Status: implemented - v4.13.10 splits the guide into `nexus-hub-guide.html` and `training.html`, inlines shared fragments from `guides/website/shared/` with a drift check, and redirects old Training hashes.

## Problem

The interactive guide is one offline HTML file with a 500,000-byte release ceiling, and at v4.13.9 it measured 487,805 bytes. The maintainer's review of the v4.13.4 Training page asked for a full-width drawn game with power-ups, three levels, a boss, structured agent sessions, and a stage tracker. That cannot fit in about 12 KB of headroom, and the existing Training already uses about 104 KB. Training needs its own page.

A second page breaks assumptions the guide was built on. The guide "travels alone" as one file, so its footer attribution, theme, menu, and the `NexusSeq` animation engine exist exactly once. Its router owns every hash in one namespace. And its tests assume one document.

## Decision

The guide becomes two self-contained offline files, `guides/website/nexus-hub-guide.html` and `guides/website/training.html`. Each works from `file://`, loads no external script, font, or image, and has its own byte ceiling: 500,000 bytes for the guide and 400,000 for Training, both measured with LF line endings.

Pieces both files carry (design tokens, the theme switch with its `portfolio-theme` key, the top menu, the footer attribution, the `NexusSeq` engine, and the page-opening and outline components) live once in `guides/website/shared/`. `scripts/stamp_guide_shared.py` inlines each fragment between `<!-- shared:<name> -->` and `<!-- /shared:<name> -->` markers in both files. Its `--check` mode fails when a page's copy differs from the source, so a fix made in only one page is caught as drift.

Hashes are split by file. The guide keeps its page hashes and gains an `EXTERNAL_ROUTES` table that runs before `HASH_REWRITES`. It maps `#training` and every v4.13.4 section id to a stage and calls `location.replace('training.html#<stage>')`. `training.html` uses structured stage hashes (`#intro`, `#loop1/<step>`, `#loop2/<step>`, and `#play-buggy`, `#play-partial`, `#play-fixed`); in-stage anchors use the `#s-` prefix so an outline jump never changes the stage. A missing `training.html` beside the guide shows a short notice on the Training tab instead of a browser error page.

Sharing the guide now means sending both files together with `assets/`; the website README, the repository README, and the portfolio copy instructions say so.

## Alternatives considered

**Keep one file and raise the ceiling.** The maintainer rejected this. The ceiling exists because the guide is shared by email and opened on phones; one file of 600 KB or more would be slow on a phone and would keep growing with every Training change.

**Load a shared external script from both pages.** Breaks the no-`script src` rule the publication check enforces. It also breaks opening a page as a single email attachment, because the script would be missing. Rejected.

**Keep separate copies in each page, guarded only by a parity test.** A parity test can say that two copies differ, but not which one is right. Every fix then has to be made twice by hand. One source plus a stamping step keeps the page files self-contained and makes the right copy unambiguous. Rejected.

**Put Training in an `<iframe>` inside the guide.** An iframe pointing at a local file is blocked or inconsistent across browsers on `file://`. It also gives the outline and theme two documents to keep in step. Rejected.

## Consequences

- `scripts/stamp_guide_shared.py` is a repository-internal guard: listed in `DEV_ONLY_SCRIPTS`, with no installer copy step. Its `--check` joins `stamp_guide_counts.py --check` in the CI profiles in the plan's final phase.
- The footer-attribution decision (`docs/decisions/implemented/policy/2026-09-02-platform-mark-attribution-in-footer.md`) is amended: attribution travels inside each of the two files, through the shared footer fragment.
- The tests that assume one document either retarget to both files or retire with the old Training (inventory: `docs/releases/v4/v4.13/development/v4.13.10-inventory.md`).
- The guide's size falls by roughly 104 KB when the old Training is removed.

## Amendment (2026-10-04, maintainer review)

The maintainer asked for the finished game to be presented as the reward for completing Training, with a hint that clearing every level holds a surprise, and for defeating the Nexus boss to offer Nexus AI Studio. Training therefore gains two outbound links, both inside the reward panel shown only after the boss falls: the Windows installer at `https://github.com/bendourthe/Nexus-AI/releases/latest/download/NexusSetup.exe` and the release page. The offline rule is unchanged: the page still loads nothing over the network; a link is followed only when the reader clicks it. The trailer is drawn in the page (no video file), so it adds no download and works offline. The visible "Jump to the boss" button (decision 10) was removed, because a shortcut would give the surprise away; the engine keeps `jumpToBoss()` for tests.

**Alternatives considered**: embedding a video trailer (rejected: a remote video breaks the offline rule, and a bundled one would exceed the page's byte ceiling); linking only the repository (rejected: the maintainer asked for a direct download); keeping the jump button (rejected: it contradicts the hinted surprise).

