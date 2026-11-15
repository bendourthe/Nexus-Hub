# README Section Order

This refinement reorders the README so readers meet the latest release note first, then follow installation, daily use, platforms, and reference material. License is now the final section. Section bodies, animations, and the generated cheatsheet are unchanged.

## Changes

- New order: What's New in v4.14.8, Installation, Development Workflow, Centralized IDE Settings, Usage Monitors, Handoffs, Platforms, Command Cheatsheet, Documentation, License.
- Command Cheatsheet now follows Platforms. Handoffs follows Usage Monitors because a usage limit is the usual reason to hand off.
- Removed the sentence "**4.15.0 preview:** optional Nexus Hub controls inside your IDE." from Centralized IDE Settings.
- The intro navigation link `#command-cheatsheet` still resolves; no other in-page anchors exist.

## Verification

- A scripted split on top-level headings (outside code fences) moved each section byte-for-byte; the diff is 33 moved lines plus the 2 removed lines.
- GitHub GFM rendering lists the ten sections in the new order, with 7 cheatsheet groups and 24 command headings between the generated-content markers.
- Rendered HTML of the edited and committed README both contain 21 tables, 7 images, and 43 links.
- All 28 local link and image targets exist. No script or test pins README heading order. `git diff --check` passed.
- No animation, poster, generator, or extension file changed, so the corrected Claude orange is unaffected.

## Release Inclusion

Include this refinement with the settings branch in v4.15.0. Integration and publication remain pending.
