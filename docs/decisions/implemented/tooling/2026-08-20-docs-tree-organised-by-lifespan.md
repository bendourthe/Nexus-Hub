# Decision: Organize the documentation tree by lifespan

Status: implemented - Make lifespan the placement axis and name release containers explicitly

## Problem

The current `docs/v<M>/v<M>.<m>/` and `docs/archive/` names encode version and state unevenly, while root-level names mix subject, audience, and lifecycle. A person placing a new document must know repository history and memorize exceptions. Subject questions such as "is this about development?" do not constrain placement because almost every project document answers yes.

## Decision

The single admission question is used: "when does this document stop being true?" Every document has one answer that a reader unfamiliar with the repository can determine: living, append-only, frozen-at-close, controlled record, already-frozen, or generated. Keep living and append-only material at stable root subtrees, place release-bound material under `docs/releases/v<M>/v<M>.<m>/`, and place closed release snapshots under `docs/archives/v<M>/v<M>.<m>/`.

Patch releases continue to share their minor bucket and carry the full version in filenames. The shape below `releases/` and `archives/` is identical, so closing a release remains a directory move. The earlier tree already had the same plain `mv` property because the buckets below its active and archive containers were already identical; the rename improves admission and naming, not move mechanics.

## Alternatives considered

### Group development documentation together

Rejected. The admission test for "development" always returns yes, so the directory becomes a junk drawer that absorbs plans, decisions, evidence, investigations, and living guidance. It would need another reorganization within a year.

### Add a process directory

Rejected after checking the candidate contents. Every candidate was either a living handbook, an append-only decision, release evidence, or generated output; `process/` would have held nothing and added a category without an owner.

### Put living reference documents under releases

Rejected. A frozen copy cannot be corrected while it remains presented as current guidance. During the source release, two false statements in living references were found and fixed in place; one answered an auditor's question incorrectly in the reassuring direction. Release-scoping those references would preserve and multiply false current claims.

### File ADRs under the release that produced them

Rejected. A decision can remain in force after its originating release closes. Archiving the release would then archive a decision that still governs the system and hide it from future design work.

### Keep docs/v and docs/archive as the default with an opt-in profile

Rejected by explicit project decision. Two default schemes would make placement platform- or repository-dependent and weaken the admission rule. The migration burden would merely recur at every consumer boundary.

### Adopt `archives/` only

Rejected by explicit project decision. That improves plurality but leaves the active container as an opaque version prefix, so the paired states remain asymmetrical and the tree still does not say what the documents are.

## Consequences

- New canonical release material resolves to `docs/releases/v<M>/v<M>.<m>/` and closed material resolves to the shape-identical `docs/archives/v<M>/v<M>.<m>/` tree.
- Existing `docs/v<M>/v<M>.<m>/`, `docs/archive/`, flat version directories, and `docs/versions/` are detected as legacy and honored until an explicit canonicalization command runs.
- The canonicalization command repairs references and proves that the unresolved-link set has no new members.
- Living, append-only, controlled, and generated documentation remain outside the release lifecycle that does not apply to them.
- Every distributed platform receives the same rule and every path parser reports the detected layout explicitly.

## Risks

The breaking rename can strand links, split a repository between old and new containers, or cause downstream tools to guess the layout. Those risks are controlled by explicit legacy detection, a single migration command, rename-map reference repair, pre/post unresolved-link set comparison, mixed-layout reporting, and repository-wide contract tests before publication.
