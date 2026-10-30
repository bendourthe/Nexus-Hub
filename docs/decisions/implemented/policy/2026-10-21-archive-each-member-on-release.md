# Decision: Archive each member of a minor-scope run as soon as it is released

Status: implemented - an optional `archive-member` approval moves each released member's own records to the archive early, under a signed archived identity beside the frozen plan hash

## Problem

A minor-scope run (`/implement vX.Y`) archives its whole active tree only at the minor close, after the last member's release. A long minor such as v4.14 therefore keeps every released member's plan, receipts, and session histories in the active tree for weeks, beside the members still in progress. The active tree is the working directory an agent reads first, so released work crowds out live work, and a later member's plan, gaps, and evidence are harder to find among finished records.

Moving a member's files early is not a plain `git mv`. The minor record freezes each member's plan by path and hash, and every reader that verifies the record (the loader, the controller handoff, the worker projection, the planned follow-on reconstruction) would read a moved and link-repaired plan as `record-tampered`. Several checker rules also assumed a plan's own folder holds its minor's ledger and evidence, which is false for a member archived while its minor is open: `gaps.version` would find no ledger in the archive folder and read every open gap as met.

## Decision

A minor record may carry an optional, unbound, minor-level `archive-member` approval, valid only beside `archive-minor`. A record created before this change gains it only by a genuine decision of its own: `record render --action add-class --class archive-member` shows a page stating the changed archive timing, and `record add-class` records the class from the user's captured paste, with provenance, and re-signs. A record without the class behaves exactly as before, byte for byte, including its verdict output and score.

With the class, `minor_close.py archive-member` moves one released member's own records (its frozen plan, and its exactly `vX.Y.Z-`-prefixed entries under `development/`, `development/history/`, `research/`, and `analysis/`) to the same paths the final archive would use, repairs links and per-prefix mentions, proves zero newly broken links, and commits once, as the final archive does. Shared files stay until the minor close. Before that commit it signs into the member an `archived` identity (`plan_path`, `plan_sha256`, `from`, `original_sha256`, `moved`, `at`); the frozen `plan_path` and `plan_sha256` never change. Every verifier accepts a member whose plan matches either its frozen hash or its signed archived identity. The member's original text for follow-on reconstruction is read from git at its signed original path and must hash to its signed original hash.

A per-member `archive.member` predicate (reported only with the class) is met once the archive lands on the integration branch or once the final archive does; it is required for `MINOR COMPLETE` and never gates the next member's publication. The minor close composes with it: it merges file by file into the existing archive directory, treats plans already in its own archive tree as mention-eligible, and records `archived.from` and `archived.original_sha256` before it re-freezes.

## Alternatives considered

- **Archive only at the minor close (status quo).** Simple and already proven, but it keeps every released member's records in the active tree until the last member ships, which is the retrieval problem this solves. Kept as the default: without `archive-member` nothing changes.
- **Per-member archive without an approval class.** Move a released member's files under the existing `archive-minor` approval. Rejected: `archive-minor` was approved as one move at the close, so moving files mid-run, opening extra pull requests, and repairing other files' links would be an action the user never saw on the approval page. A running record such as v4.14 must not change behavior without a genuine decision, so the timing change is its own class with its own page.
- **Replace the frozen hash instead of adding an archived identity.** Re-freeze `plan_path` and `plan_sha256` at each member archive, as the final archive does. Rejected: the frozen hash is the record's binding to what the user approved, and every later reader (follow-on reconstruction, worker identity, handoff) keys on it. Overwriting it mid-run loses the original identity while the run is still live and makes a rolled-back archive unverifiable. A signed identity beside the frozen one keeps both checkable, and a hand edit of either fails the HMAC.

## Consequences

- During an open minor with the class, one minor lives in both trees on purpose: released members in `docs/archives/`, the rest in `docs/releases/` (docs retention state 1b).
- Each member archive is one extra branch (`chore/archive-<member>`), commit, and pull request, covered by the `archive-member` approval.
- `gaps.version` and `evidence.file` resolve an archived member's ledger and shared evidence across both trees, which also closes the fail-open read of an empty archive folder; non-archived plans read exactly as before.
- Archive commits are identified by content (one parent, exactly the files and blob ids one signed `moved` set names, or a merge bringing only such commits) and the close commit by its signed id. Once any member carries `archived`, every member's task lines drop those commits while keeping git pathspec matching, so no archive ever satisfies any member's task, and a later member's claim audit leaves out only paths that verified archive commits alone changed. A squash-merged closing pull request would not carry the signed close commit; Nexus-Hub merges with merge commits.
- The command refuses rather than guesses: an incomplete member, a branch carrying anything but archive commits, an unmerged branch touching a moved path, an unreleased member, the last member, a dirty member worktree, a changed git attribute, a repair that would rewrite another member's frozen plan, or a collision each stop it with a fixed reason id, and any failure restores both the tree and the record.
- A crash after the commit cannot leave the record unverifiable, because the identity is signed before the commit and removed again when the commit fails.
