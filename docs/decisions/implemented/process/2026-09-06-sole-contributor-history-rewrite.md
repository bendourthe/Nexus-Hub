# Decision: Sole-contributor history rewrite

Status: implemented - Local isolated rewrite and maintainer enforcement are implemented; remote publication is pending explicit approval.

Repository-maintenance decision for the owner reviewing v4.12 publication. Covers canonical identity, all-ref rewriting, local prevention, backups and GitHub contributor-page verification. Evidence refreshed 2026-09-14 in the [inventory](../../../releases/v4/v4.12/development/attribution-inventory.md).

## Problem

Historical commits include Cursor and Claude co-author identities and Dependabot authors. The requested public result is one contributor account, bendourthe. Older maintainer emails already map to bendourthe today but differ from the requested canonical noreply identity.

## Decision

Use `Ben Dourthe <50595044+bendourthe@users.noreply.github.com>` for all non-allowlisted historical author and committer fields on every branch and tag. Preserve `GitHub <noreply@github.com>` as committer and preserve dates and file contents. Strip forbidden attribution trailers. Perform the rewrite in a separate clone from a verified mirror, retain the original mirror, and publish only after explicit approval of the exact ref changes. Enforce the policy through a stdlib repository checker, existing CI validate job and maintainer-local Git hook.

## Alternatives considered

| Alternative | Disposition |
|---|---|
| Claim maintainer email only | Does not remove mapped agent co-authors; the Gmail identity already maps to bendourthe. |
| Squash future merges only | Leaves historical extra accounts and tags intact. |
| Rewrite only the default branch | Leaves forbidden identities reachable from other requested refs. |
| Distributed catalog hook | Imposes this repository's personal attribution policy on users; outside scope. |
| Keep the existing history | Preserves original authorship metadata but does not meet the requested public contributor result. |

## Consequences

- Every rewritten ref passes the fail-closed identity and trailer checker.
- Original refs remain recoverable in a verified external mirror; names, dates and file trees are preserved.
- A shallow scan fails and fixture histories demonstrate author, committer and trailer rejection.
- The existing unconditional validate job gates attribution without adding a required-check context.
- After approved publication, GitHub Code and Insights contributor surfaces show only bendourthe, or the cache delay remains an explicitly owned pending observation.

### Risks and remaining conditions

Rewriting changes SHAs, invalidates commit and annotated-tag signatures, and requires collaborator resynchronization. Bot authorship metadata is deliberately reassigned under the requested all-author scope; the original backup preserves provenance. Open PR heads change if any remain at publication. Branch protection may reject force-pushes; the operator must resolve that without deleting protections. GitHub contributor caches may lag. An origin change after backup invalidates the publication snapshot and requires reconciliation before approval.

GitHub advertises 212 read-only pull-request refs outside the captured writable branch/tag set. A normal push cannot rewrite them. The all-ref local proof remains valid for its 139 captured refs, while the literal public all-ref Goal is partial until the owner accepts or resolves that limitation. See [QG-1 and publication conditions](../../../releases/v4/v4.12/known-gaps.md). Public contributor views, the one-time protected-branch exception and fresh remote CI remain pending; this status does not authorize them.
