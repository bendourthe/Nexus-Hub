# Archive a Closed Minor

The detail behind the "Archive a closed minor" section of `docs-layout-refactor`: what `minor_close.py archive` refuses, which references it repairs and how, what it leaves byte-exact, and how a failure is undone. Read it when an archive refuses, when a repair looks wrong, or before changing the helper. Which minor counts as closed for a minor run, and when `archive.minor` is met, are owned by the completion contract ("Minor gaps and archive"); this file describes the procedure only.

## Authority

`--apply` runs only when the minor record for `vX.Y` carries the `archive-minor` class, or, when there is no minor record at all, with `--confirmed` after this skill's Step 7 confirmation gate. A verified record without `archive-minor` is the user's answer for this minor, so `--confirmed` cannot override it. `--confirmed` is only as strong as that confirmation: pass it only after the user answered the gate for this minor. A record that is tampered, paused, or blocked prints its verdict and exits 3. `--dry-run` (the default) needs no authority and writes nothing.

## Refusals

Every failing condition is printed as its own `REFUSED: <reason> (<detail>)` line, exit 3, with nothing moved.

| Reason | Condition |
|---|---|
| `no-register` / `register-unreadable` | The tree has no readable `known-gaps.md`, so there is no closure proof |
| `register-unparsed` | The register has a parse problem as the completion contract defines it (an unclosed fence, an item-like heading or row that is not an item, or a header `**Open items**` count that disagrees with the items) |
| `open-gap` | An item in the register is neither resolved nor migrated |
| `unverified-migration` | A ` - MIGRATED to vX.Y.Z` item fails the migration check (missing target entry, id not approved, created during the run) |
| `open-items-not-zero` | The register's header (before its first `## ` heading) does not state `**Open items**: 0` |
| `register-not-finalized` / `register-status-open` | No header Status line says finalized or closed, or one still says in-progress or open |
| `register-unchecked-box` | The register holds a `- [ ]` line |
| `unchecked-task` | A plan of the minor holds an unchecked `T###` task line |
| `queued-plan-outside-members` | A plan whose Status is not complete, shipped, or superseded is not a frozen member |
| `unreleased-member` / `cannot-verify-shipped` | A plan's tag is missing locally or on `origin`, or its GitHub Release is not published |
| `live-worktree` | A worktree other than this one holds a `feat/vX.Y.*` branch or a member's source branch |
| `unmerged-branch-touches-tree` | A branch on `origin` not merged into the integration branch changes a file under the tree |
| `cannot-verify` | git or the remote could not answer one of the checks above |
| `dirty-worktree` | `git status --porcelain` is not empty; rollback needs a clean tree |
| `not-on-closing-branch` | The current branch is not `chore/close-vX.Y` (or `--closing-branch`) |
| `archive-collision` | A file would land on a path that already exists in the archive |
| `plan-bound-by-another-run` | The repair would rewrite a plan that another live run froze by hash, which would leave that run `record-tampered` |
| `multiple-active-trees` | The minor has more than one active layout directory |
| `link-checker-unavailable` | No `link-baseline.py` was found (installed skill copy first, then this repository's) |
| `approval-not-covered` | `--apply` without `archive-minor`: a record lacks it, or there is no record and no `--confirmed` |

## Reference classes

The repair covers the seven classes the `plan-queue-assessment` renumber procedure lists, applied to a path change rather than a version change:

1. **Intra-tree strings**: plain mentions of the old tree path in body prose are rewritten to the archive path.
2. **Relative links from sibling trees**: a link such as `../../v0.5/plans/x.md` from `docs/releases/v0/v0.6/` is resolved from its file's location and re-expressed to the archive.
3. **Link-reference definitions** (`[label]: path`) get the same resolution as inline links.
4. **Self-referential task-line paths** inside the moved plans are plain mentions and are rewritten, so a later `task.T###` check reads the archived path.
5. **Tracker dashboard rows** (for example `docs/todos.md` table links) are links and are resolved.
6. **Tracker prose and headings** are plain mentions and are rewritten.
7. **Committed evidence under the moved tree**: its Markdown links are re-expressed from the new location, so a link from the archive back to a sibling active minor still resolves.

Links are always resolved against the referring file's pre-move location and re-expressed from its post-move location, never by counting `../`; every tracked Markdown file gets the link pass. Plain mentions are replaced only as a whole path (`docs/releases/v0/v0.5` never matches `docs/releases/v0/v0.50`), in forward-slash and backslash form, and only in files where a path is live data: known-gaps trackers, plans, `docs/todos.md`, README-style indexes under `docs/` (`README.md`, `INDEX.md`, `index.md`), and scripts and tests under `scripts/` and `tests/` (Python, shell, PowerShell, JavaScript, TypeScript, JSON, YAML, TOML, CSV, text).

## Left byte-exact

- Nothing under `docs/archives/` gets a plain-mention rewrite: another archive's evidence records the tree as it was. Outside the allowlist above (for example `CHANGELOG.md`, a development note, or captured JSON, HTML, or CSV), mentions stay as written.
- HTML anywhere is generated output and is not edited; regenerate it from its source.
- A mention inside a URL (a scheme or `//` before it, such as a pinned permalink) is never rewritten.
- Links and mentions inside fenced code and inline code spans are not edited. Fences follow CommonMark, shared with the ledger parser; a fence left open keeps the rest of the file as code.

## Proof and rollback

The helper captures `link-baseline.py baseline` before the move, moves and repairs, captures it again, and runs `link-baseline.py diff --rename-map` with the staged renames. Zero `newly_broken` is the gate. On a newly broken link, a failed stage or commit, a failed `git mv` (a locked directory from OneDrive or antivirus), or any other error mid-way (a `PermissionError` on a write, an interrupt), it restores every repaired file it had written to its original bytes and moves the tree back, so the move and the repair land in one commit or not at all. An unexpected error is reported as `REFUSED: rolled-back (<error type>)`. A failed rollback prints `REFUSED: rollback-failed`; restore the tree with `git mv` before anything else.

After the commit, a record-authorized archive re-freezes each member's `plan_path` and `plan_sha256` at its archived path and re-signs the record; the record was verified before the move, so the new values bind only this commit's repairs. `members vX.Y` still resolves the archived plans, because membership searches the archive layouts by version.
