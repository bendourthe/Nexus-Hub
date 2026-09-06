# Link Integrity During Documentation Moves

Capture a pre-move unresolved-link baseline with `link-baseline.py baseline` before changing paths. After the move and reference repair, capture a second baseline and run `link-baseline.py diff`; zero `newly_broken` is the gate, while the absolute unresolved total is context only.

## Rename-map repair

1. Run `git diff --name-status -M` and collect every `R<score>` row as an old-file to new-file rename map.
2. For each broken relative link, resolve its target against the referring file's pre-move location. Do not count `../` segments by eye.
3. Map the resolved pre-move target through the file rename map, then re-express the mapped target as a relative path from the referring file's post-move location.
4. Repair the link and resolve it again from the post-move source path. A substitution count is not evidence that the repaired path exists.
5. Capture the post-move baseline and require `link-baseline.py diff --before <baseline> --after <current> --rename-map <map.tsv>` to report zero `newly_broken`.

## Pass the rename map whenever referring files moved

`--rename-map` takes `old<TAB>new` pairs and accepts `git diff --name-status -M` output verbatim. Supply it for any change that MOVED the referring files, not just their targets.

Without it the comparison keys each entry on `(source, link, resolved_target)`, so a moved file changes its `source` and every broken link it already contained is reported as `newly_broken` while its old entry is reported as `fixed`. On this repository's own migration that read **873 newly_broken** where the true number of links broken by the move was 444 - a gate nobody can act on. With the map, the before-baseline is projected into post-move coordinates and identity drops `link`, because a correct repair necessarily rewrites the link text.

Directory renames are inferred from the file pairs, since git records file renames only. A candidate directory rule is kept only when nearly every mapped file beneath it agrees, so a container holding two differently-relocated subtrees is rejected rather than applied to its unrelated siblings.

Git detects file renames only. A link that names a directory, such as `../development/`, therefore needs a separate directory-prefix map. Apply the longest matching old directory prefix to the resolved target before re-expressing the relative link.

This algorithm replaces manual `../` depth counting. In the source refactor, hand-counting path depth produced 30 dead links even though the substitutions themselves completed successfully.

## Lifespan contradiction rule

A lifespan contradiction is a tracked document whose frozen-at-close location conflicts with its edit history. For each file under `releases/v<M>/v<M>.<m>/`, or under the pre-rename `docs/v<M>/v<M>.<m>/` form, compare the newest file commit from `git log -1 --format=%cI -- <path>` with the earliest matching release tag's creation date. When the newest commit post-dates release close, record the file, bucket, release close date, and offending commit date under `## Lifespan contradictions`.

Run `audit-docs.py lifespan-contradictions --root ./docs --repo-root .` for the standalone check. Exit 0 means no contradictions; exit 1 means findings exist; exit 2 means the check could not run. A finding never authorizes an automatic move: inspect intent and either relocate the living document or revert the post-close edit.
