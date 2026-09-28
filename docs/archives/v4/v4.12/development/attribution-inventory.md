# Attribution inventory

Inventory of every reachable commit author, committer and attribution trailer for the v4.12 maintainer rewrite. Read with [the policy](attribution-policy.md) before rewriting any ref. Observed 2026-09-14 on develop `89758d824a92bc7c801dd9c913640c759ac1d6ce`, after PRs #214, #215 and #216 merged and merged-branch cleanup finished.

## Scope and method

`git log --all -z --format='%H%x00%an%x00%ae%x00%cn%x00%ce%x00%B'` enumerated **1,696 unique commits**, including branches, tags, remote-tracking refs and the retained stash ref. Counts are occurrences per field, not distinct people. Raw output and queue inventory are retained outside the checkout in `../Nexus-Hub-backups/2026-09-14-pre-v4.12-cleanup/`. Seven historical stashes and unmerged historical branches were preserved. The complete pre-cleanup history is independently recoverable from that directory's verified `all-refs.bundle`.

## Authors

| Identity | Count | Sample SHA | Current GitHub mapping |
|---|---|---|---|
| Ben Dourthe <50595044+bendourthe@users.noreply.github.com> | 170 | `89758d824a92bc7c801dd9c913640c759ac1d6ce` | bendourthe |
| Ben Dourthe <benjamin.dourthe@gmail.com> | 1,432 | `669e369ca8cb385052aac85f326fe5a0b0373ecc` | bendourthe |
| Benjamin Dourthe <benjamin.dourthe@gmail.com> | 86 | `a25020a5617d26aa6dd5392baad23f5e2ac74842` | bendourthe |
| dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com> | 8 | `7cc2226f70a667c1972fb2d07869b73defbda0c6` | dependabot[bot] |

## Committers

| Identity | Count | Current GitHub mapping |
|---|---|---|
| GitHub <noreply@github.com> | 170 | web-flow |
| Ben Dourthe <benjamin.dourthe@gmail.com> | 1,440 | bendourthe |
| Benjamin Dourthe <benjamin.dourthe@gmail.com> | 86 | bendourthe |

Author sample SHAs above cover each committer identity. Commit REST responses verified the account mappings, including GitHub's web-flow committer.

## Attribution trailers

| Trailer value | Count | Sample SHA | Current GitHub mapping |
|---|---|---|---|
| Cursor <cursoragent@cursor.com> | 114 | `89e8e3dcc70becf1743ca30c4a5135ba33f6cebe` | cursoragent |
| Claude Opus 5 <noreply@anthropic.com> | 46 | `4d15b8ceffa0a16daba1a2dddaa1d95d0cc3ee82` | claude |
| Claude Opus 5 (1M context) <noreply@anthropic.com> | 22 | `e86c3193a5f425644f680d70fdfd22c7f1c07bd3` | Same email; sample for preceding row confirms its mapping |

All 182 occurrences are `Co-authored-by` trailers. No `Made-with` trailer was observed. GitHub GraphQL `Commit.authors(first:100) { nodes { name email user { login } } }` on the Cursor and Claude samples confirmed their co-author accounts; the REST contributors list alone was not used as proof.

## Corrections to the planning snapshot

No author or committer currently maps to `benjamin-dourthe` in the sampled distinct identities. The old Gmail identity now maps to `bendourthe`; changing it remains part of the requested canonicalization, not an account-mapping repair proven necessary today. Cursor and Claude co-author accounts remain present.

A broad `git log --all --grep=cursoragent` also matches explanatory prose in planning commits, for example `a243c17880ccc9a8acb65e69b666a2df4fa5c6d7`. Phase 2 must prove zero forbidden identity fields and attribution trailers, rather than remove unrelated prose to make that broad grep empty. Historical inventory documents intentionally retain the original identities and SHAs as recovery evidence.
