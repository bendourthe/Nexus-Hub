# Repository attribution policy

Maintainer-only allowlist and rewrite policy for Nexus-Hub v4.12. The checker and rewrite operator use this policy with the [dated inventory](attribution-inventory.md). It governs Git identity fields and attribution trailers, not file content or ordinary message prose.

## Allowed identities

| Field | Allowed identity |
|---|---|
| Author | Ben Dourthe <50595044+bendourthe@users.noreply.github.com> |
| Committer | Ben Dourthe <50595044+bendourthe@users.noreply.github.com> |
| Committer | GitHub <noreply@github.com> |
| Attribution trailer | Ben Dourthe <50595044+bendourthe@users.noreply.github.com> |

Names must match exactly; email comparison is case-insensitive. GitHub's own committer is preserved for both web commits and merges. Every other identity is rejected, including new identities absent from the inventory. The implementation keeps this closed allowlist in `scripts/check_commit_attribution.py`; moving release documentation cannot weaken enforcement. New agent-generated commits do not add attribution footers.

## Observed identities to canonicalize or strip

- `Ben Dourthe <benjamin.dourthe@gmail.com>` and `Benjamin Dourthe <benjamin.dourthe@gmail.com>` currently map to bendourthe. Canonicalize both author and committer fields to the target above.
- `dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>` is an observed bot author. Canonicalize it under the explicit all-authors rewrite scope. This changes historical authorship metadata; it does not claim the bot's work was originally authored by the maintainer.
- `Cursor <cursoragent@cursor.com>` maps to cursoragent. Strip its attribution trailers.
- `Claude Opus 5 <noreply@anthropic.com>` and `Claude Opus 5 (1M context) <noreply@anthropic.com>` map to claude. Strip their attribution trailers.

Rewrite every non-allowlisted author or committer to the target, after checking the complete inventory for ambiguity. Preserve author and committer timestamps, file trees, parent relationships and ref names. Preserve GitHub's committer. Strip forbidden `Co-authored-by` and `Made-with` fields rather than substituting a maintainer co-author. Treat folded continuation lines as part of the field. Unknown or malformed attribution fields fail the checker. Ordinary prose mentioning these products or accounts remains intact.

## Enforcement and publication

The checker is stdlib-only and maintainer-only. Exit 0 means clean, 1 means attribution findings, and 2 means an incomplete or invalid scan. A missing Git executable, non-repository root, shallow repository, unreadable message or malformed Git output cannot pass. Every requested operation runs; one clean input cannot hide another operation's findings. The local hook combines pending author/committer validation with message-file validation.

Phase 1 tests synthetic histories and records the expected dirty live scan. Phase 2 rewrites only a separate clone derived from a verified mirror backup. Phase 3 enables the live gate and a repository-local hook. Installers never distribute this checker or hook. Publication requires review of the exact ref set and explicit approval of the force-push, with per-ref expected old SHAs and a tested recovery backup. Local preparation does not authorize rewriting GitHub refs.

The local all-ref scan covers every ref fetched into that repository. Public publication covers captured writable branches and tags; GitHub read-only PR refs remain outside normal push authority. See [the final evidence](last-phase-evidence.md) and [QG-1](../../../../releases/v4/v4.12/known-gaps.md). This is a declared proof limit, not an exception that silently accepts dirty fetched history.
