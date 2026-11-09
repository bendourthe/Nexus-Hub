# README Chinese Replacement

This change makes the concise README the single design for both languages. `README_zh.md` is now a full Simplified Chinese translation of `README.md`, and four tests that pinned facts to the old long README now read those facts from the reference guides the README links.

## Changes

- Replaced the 286-line legacy `README_zh.md` with a translation of the current README: same ten sections in the same order, same animations, and the full seven-group cheatsheet with all 24 commands. Command names, scopes, flags, and examples stay in English; descriptions are translated.
- The Chinese cheatsheet has no `readme-cheatsheet` generator markers, because `scripts/readme_cheatsheet.py` emits English only. Update the translation by hand when the English cheatsheet changes.
- Added a `[Chinese README](README_zh.md)` link to the English navigation line; the Chinese README links back to English.
- Retargeted four tests from `README.md` to the guides that now hold each fact: the version and upgrade commands and the organization guide link (`docs/guides/installation-and-platforms.md`), and the editable extension extras and `/implement <slug> full` alias (`docs/guides/development-workflows.md`). The version test also asserts that both READMEs link the installation guide.
- Added the `/implement <slug> full` (alias `in-full`) sentence to `docs/guides/development-workflows.md`; it previously lived only in the old README.

## Verification

- Before the change, all four tests failed against the concise README already committed on this branch. After it, the 20 tests in the four files pass.
- GitHub GFM rendering of both READMEs shows identical structure: 10 sections, 7 cheatsheet groups, 24 command headings, 21 tables, 7 images, and 26 code blocks.
- Both cheatsheet anchors (`#command-cheatsheet`, `#命令速查表`) resolve under GitHub's heading slug rule, and all 29 local link and image targets exist in each file.
- `develop` has not changed either README since this branch split, so integration carries both files without conflict. `git diff --check` passed.

## Release Inclusion

Include this change with the settings branch in v4.15.0. Integration and publication remain pending.
