# Decision: The shared command mirror keeps files the user owns

Status: implemented - mirrored command files are written through the ownership manifest, so a same-named user file is kept and a user-edited stale file is not pruned

## Problem

`scripts/lib/integrations/_command_surface.py::mirror_command_surface` copies every catalog command into a platform's command folder. It is shared by Cursor (three call sites), GitHub Copilot, Pi, and Qwen Code. Adding `/visualize` in v4.13.9 raised the question of what happens when a user already has a command file of the same name. Reading the function showed two defects: it overwrote any existing file of the same name with no ownership check, and its prune deleted every tracked file that had left the catalog with no check of its content, so a mirrored file the user had since edited was deleted too. Both lose a user's work silently, on four platforms. The evidence and the user's approval of the fix (2026-10-01) are in the v4.13.9 admission record.

## Decision

Mirror writes go through `_owned.write_owned_file(..., managed_root=dst_dir)`. A file the ownership manifest does not record as Nexus-Hub's is kept and reported as `kept`; a byte-identical file is adopted. The prune deletes a stale mirrored file only when its sha256 still matches the hash recorded for the install action that wrote it. A file with no recorded hash, from an install that predates hash recording, is pruned as before.

## Alternatives considered

**Name the new command something no host already uses.** Rejected: it avoids one collision but leaves both defects in place for every future command and every file a user already has.

**Overwrite with a backup.** Rejected: a backup the user never asked for, in a folder the host reads, can itself surface as a command, and it still replaces the user's file in place.

**Skip mirroring on Cursor.** Rejected: Cursor users would lose every Nexus-Hub slash command, and the defects would remain on Copilot, Pi, and Qwen Code.

## Consequences

- On Cursor, Copilot, Pi, and Qwen Code, a user's own command file of the same name now wins over the catalog's, and the install summary reports it as kept. That user does not get the catalog's version of that command until they remove or rename their file.
- A mirrored file the user edited stays after its command leaves the catalog; removing it is the user's choice.
- Installs that predate hash recording still prune unhashed stale files, so the protection covers files written from this release on.
- Collision tests in `tests/integrations/test_global_command_surface.py` cover each path; against the old code two of them fail.
