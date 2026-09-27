# Distribution handbook content review - widened AI-attribution ban

**Handbook:** `docs/handbooks/distribution.html` (id `distribution`)
**Reviewed on:** 2026-09-26
**Trigger:** v4.13.1 Phase 2 changed one declared code input, `catalog/style-guides/git-attribution.md`. It widened the footer bullet into a ban on any reference to AI contributions across commits, tags, pull requests, issues, comments, release notes, changelogs, and documents, with an override clause and a subject-is-not-attribution clause.

## Claim review

The handbook's attribution claims, in the "Generated and user-owned files differ" section:

- **"Both installers activate user-attribution Git hooks from a digest-checked copy that survives the installer checkout."** Unchanged: no hook or installer copy path moved.
- **"Run nexus-hub attribution check before commits, tags and pushes."** Unchanged: the preflight rule and its command are the same.
- **"Human identity and existing hooks are preserved; direct hosting API writes need separate verification."** Unchanged: the widened bullet adds surfaces the ban covers and does not alter identity handling or hook preservation.

The handbook does not state which surfaces the footer ban covers, so the widening makes no handbook claim false. No visible content change is required. Describing the wider surface list is a coverage choice for the next handbook refresh.

## Qualification

`build_presentation.py docs/handbooks/_sources/distribution/model.json --out docs/handbooks/distribution.html --root . --check` reproduced the committed output hash `25ffd7b98de194f81f0a33035b4b184546c394214843318bec54573a2d22efb5` without changing the handbook. The existing build and Chromium rendered receipts attest to those exact bytes and remain applicable. Only the `git-attribution.md` input hash and this content receipt are refreshed.

## Phase 6 addendum - agent-hook scan subcommand

**Trigger:** v4.13.1 Phase 6 changed a second declared code input, `scripts/nexus_git_attribution.py`, by adding a `scan` subcommand that the new `attribution-guard` agent hook calls. The existing `install`, `uninstall`, `check`, `context`, `tag`, and `hook` subcommands and their identity checks are unchanged.

- **"Both installers activate user-attribution Git hooks from a digest-checked copy that survives the installer checkout."** Unchanged: the Git hook wrappers and the copy path are untouched.
- **"Run nexus-hub attribution check before commits, tags and pushes."** Unchanged.
- **"Human identity and existing hooks are preserved; direct hosting API writes need separate verification."** Still true: the new agent hook checks gh and GitHub MCP bodies on hook-capable platforms, which is a separate verification layer, not a change to the Git hooks.

No visible content change is required. `build_presentation.py ... --check` again reproduced output hash `25ffd7b98de194f81f0a33035b4b184546c394214843318bec54573a2d22efb5`, so the build and rendered receipts still apply. Only the `nexus_git_attribution.py` input hash and this content receipt are refreshed.

## Phase 9 addendum - deep-pass hardening of the scan

**Trigger:** the v4.13.1 Phase 9 deep pass changed `scripts/nexus_git_attribution.py` again, inside the agent-hook `scan` path only: footer normalization and end anchoring, agent-identity checks for co-author trailers (reusing the existing `human()` rule), and more recognized publishing routes. The Git hook wrappers, `install`, `check`, `tag`, and identity enforcement are unchanged, so the handbook's three attribution claims stay true and no visible content change is needed. `build_presentation.py ... --check` again reproduced output hash `25ffd7b98de194f81f0a33035b4b184546c394214843318bec54573a2d22efb5`; only the input hash and this content receipt are refreshed.
