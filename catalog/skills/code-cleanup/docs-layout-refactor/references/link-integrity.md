# Link Integrity During Documentation Moves

Capture a pre-move unresolved-link baseline with `link-baseline.py baseline` before changing paths. After the move and reference repair, capture a second baseline and run `link-baseline.py diff`; zero `newly_broken` is the gate, while the absolute unresolved total is context only.

## Rename-map repair

1. Run `git diff --name-status -M` and collect every `R<score>` row as an old-file to new-file rename map.
2. For each broken relative link, resolve its target against the referring file's pre-move location. Do not count `../` segments by eye.
3. Map the resolved pre-move target through the file rename map, then re-express the mapped target as a relative path from the referring file's post-move location.
4. Repair the link and resolve it again from the post-move source path. A substitution count is not evidence that the repaired path exists.
5. Capture the post-move baseline and require `link-baseline.py diff --before <baseline> --after <current>` to report zero `newly_broken`.

Git detects file renames only. A link that names a directory, such as `../development/`, therefore needs a separate directory-prefix map. Apply the longest matching old directory prefix to the resolved target before re-expressing the relative link.

This algorithm replaces manual `../` depth counting. In the source refactor, hand-counting path depth produced 30 dead links even though the substitutions themselves completed successfully.
