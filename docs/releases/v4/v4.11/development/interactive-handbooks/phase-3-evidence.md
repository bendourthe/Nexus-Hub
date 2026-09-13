# v4.11.0 interactive handbooks - Phase 3 evidence

Retained assembly now preserves authored page/slide fragments, independent depth selections, saved themes, shared figures and source/build fingerprints. This is an assembly and real-boundary verification result; Phase 6 still owns one-invocation authoring qualification and comparative visual quality.

## Implemented contract

The existing builder CLI routes models containing `presentation` through the narrow `dual_view.py` sibling. Legacy plain drafts retain their original path. Read-only `--check` validates the existing HTML and build record without modifying either; repeated builds are byte-identical. Validation precedes replacement and covers stable IDs, source-unit coverage and omission reasons, slide ceilings, theme policy, passive markup, root-contained paths including Windows junctions and hard links, source/build changes, unowned output/records, and concurrent edits. Each output file is replaced atomically; an interrupted two-file pair remains detectably stale.

Simple Cartesian figures preserve signed values, zero lines, missing samples, source labels and exact data tables. Specialized geometry is retained as authored SVG or an enhanced original instead of silently simplified. SVG instances rewrite root/descendant IDs and local references. Map directory labels must match the retained geometry. Real-browser tests exercise independent filters/zoom/reset, source-resolution image enlargement, offline behavior, map search/keyboard selection, duplicate IDs and measured chart text; an intentionally displaced label is detected by the measured probe. Shared authoring references retain the figure worksheet, asset ledger, annotation geometry rules and positive cross-format design comparisons.

## Verification

- Broad affected presentify/extractor suite: 357 passed, 2 slow installer cases deselected. This includes existing layout, reconstruction, source coverage, annotation, scorer and runtime contracts.
- Final affected retained-builder suite after the last specialized-geometry guard: 69 passed; coverage.py reports 89.4% (see phase-3-coverage.json). No test skipped. The Windows link test exercises a real junction when unprivileged symbolic-link creation is unavailable; a separate real hard-link test passes.
- Final installed-bundle smoke: both Git Bash and Windows PowerShell installer paths pass into isolated temporary Claude workspaces. Installed builder/runtime/figure bytes match their source bundle; the installed builder builds and checks the retained fixture and its browser output enters, advances and exits.
- Ruff passes for the changed Python files; both JavaScript assets parse with Node. Bundle validation: 336 skills, zero errors, 64 unchanged existing warnings. git diff --check passes.
- Fresh final fixture HTML hash: `fdd1f5a6aba296a188d4321579912858a3f9384b4e4d0537aff471d094774769`. The retained build record lists source/dependency hashes; the actual HTML was built in a temporary workspace. Fresh build followed by read-only check passed. No screenshots or historical authoring runs are reused as new qualification evidence.

## Resolved failures and limits

The first coverage invocation collected no data because the module was imported under an alias; a normal module import fixed measurement. A photo-dialog assertion raced the queued close event; it now waits for detachment. Browser map search exposed CSS overriding hidden regions; an explicit hidden rule fixed the real visibility defect. The broad suite was rerun successfully after that fix. The deterministic baseline is not a generic design generator, and structural/geometry probes do not certify source fidelity or aesthetic quality. Source-specific complex chart placement remains authored and measured through the shared SVG seam.

## CI impact and post-phase sequence

Existing tests/skills discovery and the explicit slow installer selection cover the new paths. No dependency, environment variable, secret, service, pipeline edit, push or remote CI run was added. Phase 7 owns terminal CI reconciliation. Gitignore: zero patterns added; transient builds/logs remain outside the worktree. The docs inventory audit made no moves or deletions; durable runbooks remain with their skills and release evidence remains in this release tree. Product version metadata is unchanged. No gate was waived and no new deferred gap was accepted.
