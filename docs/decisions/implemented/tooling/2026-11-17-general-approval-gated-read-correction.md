# Decision: General Approval-Gated Read Correction

Status: implemented - One captured decision releases a single recorded read file of an unpublished member until its ordered publication start, in any minor run.

## Problem

In a schema-2 minor run, an admitted member's recorded read claim blocks every earlier member's publication-time coordinator write to the same file, because coordinator write paths must not overlap other active members' reads. A later-published member reading a shared file such as a known-gaps ledger therefore made the earlier member's `record member-start --coordinator-claims` fail with `coordinator-scope-conflict`. The later member can only start after the earlier one is merged, so the block could never clear. Native commands could only add claims, and the one reduction round, `correct-ci-read`, is hard-coded to one member and one file.

## Decision

`record render --action correct-read` and `record correct-read` take an explicit `--member` and `--path`. The path must be an exact literal entry of that member's recorded `read_paths`, and the member must have no publication start. A genuinely captured decision appends a signed `member_read_corrections` entry beside the unchanged claims. Effective reservations subtract the path in both implementation-admission directions and in the coordinator conflict check. The member's ordered publication start restores the raw reads and is refused while another unmerged member claims the file. History is append-only, the central writer accepts only the consumed leased append and the native restore, and the signing domain is unchanged because the entry is member data.

Only an exact literal read qualifies. A file under a recorded directory read is refused, because subtracting the file would leave the directory reservation in force and the approval would change nothing.

## Alternatives considered

| Alternative | Disposition |
|---|---|
| Write a sidecar gaps file to avoid the conflict | Rejected because the completion gate would read the ledger section of the real file as empty and report the gaps as missing. |
| Wait for the later member to publish first | Rejected because the order is fixed: the later member needs the earlier one merged, so the wait never ends. |
| Extend `correct-ci-read` with a declaration row per case | Rejected because it needs a reviewed source checkpoint and a hard-coded row per case, so every new case would need a code change and a release. |
| Rewrite the member's recorded read list | Rejected because it destroys the original claim and the audit trail, and the signed record must keep raw claims. |
| Generalize with an explicit member and path under a captured decision | Chosen: no code change per case, claims stay intact, and consent is the maintainer's own whole-message reply. |

## Consequences

Each use needs a fresh maintainer decision and an owning session. The correction applies only until the member's own start, so a later conflict surfaces at that start instead of silently. A member that carries a `correct-ci-read` entry cannot also take this correction, and `permit-member-paths` refuses a corrected member, to keep each reservation change on one authenticated path.
