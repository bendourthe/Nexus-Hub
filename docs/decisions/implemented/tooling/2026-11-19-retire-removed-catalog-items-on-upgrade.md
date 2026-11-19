# Decision: An install removes copies of catalog items the catalog no longer ships

Status: implemented - `scripts/lib/integrations/_retired.py`, called by the install runner after every platform install.
Date: 2026-11-19
Author: Ben Dourthe
Template: Nygard

## Problem

When a command, skill or agent leaves the catalog, a refresh install drops it from folders the installers sync wholesale, such as Claude Code's `commands/`. The integrations render most other copies one file at a time, and nothing ever removed those. Removing `/status` in v4.15.5 showed the size of the gap: an isolated install of `develop` followed by an install of the removal branch removed 6 of 18 copies and left 12. Those were the command-skill `skills/status/SKILL.md` on nine surfaces, Codex `prompts/status.md`, and the Antigravity and Windsurf `workflows/status.md`. So the removed command kept working on most platforms while saying it was removed. Every earlier rename or removal left the same kind of copy behind.

## Decision

After each platform installs, the runner compares the files the previous install recorded for that platform (the manifest `actions`, each with a SHA-256) with the files this install produced. A recorded file this install did not produce is removed only when all of these hold:

- Nexus-Hub wrote it (recorded `created`, `updated` or `unchanged`; a `kept` file was the user's).
- Its bytes still match the recorded hash. An edited copy is kept, and the install output says why.
- It is `skills/<name>/...` or a file directly inside `commands/`, `prompts/`, `workflows/` or `agents/`, and `<name>` is no longer a catalog command, skill or agent. The name set comes from command and agent file stems and from folders holding a `SKILL.md`. Other file stems do not count, so a skill's `examples/status.md` cannot keep `/status` alive.
- It is a regular file inside the install target, reached without a symlink or junction.

Nothing is removed on a dry run or an instruction-only install. Folders emptied by a removal are removed with `rmdir`, never past the content folder itself. Removed paths are untracked in the manifest.

## Alternatives considered

- **Remove everything recorded last time but not produced now.** Rejected: an item still in the catalog but skipped this time (a narrower `--skills` selection, an opt-in surface such as the Copilot skills wrapper turned off, an instruction-only run) would be deleted without being asked for. Tying removal to "no longer in the catalog" limits it to retired items.
- **A fixed list of retired names, like the retired-hook cleanup.** Rejected by the maintainer on 2026-11-19 in favor of fixing the cause: every future rename would need a new list entry, and missing one repeats the defect.
- **Ship the `/status` removal and document a manual cleanup.** Rejected for the same reason: users would carry stale copies of every future removal.
- **Reuse the stale-platform name check in `_stale.py`.** Rejected: it counts every file stem in the catalog, so `internal-comms/examples/status.md` makes `status` look shipped.

## Consequences

- An upgrade now removes stale copies of removed commands, skills and agents on every rendered surface, as long as the copy is unchanged.
- A copy edited by the user stays. It is reported once, then dropped from the record, so later installs do not report it again.
- A bundled file removed from a skill that still exists is not covered; only whole items are retired.
- Skill folders an integration records as a directory, with no per-file hash, are not touched.
- Tests: `tests/integrations/test_retired_items.py`. End-to-end, an isolated workspace install of `develop` followed by an install of the change removes every `/status` copy.
