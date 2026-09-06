# `docs/archives/` Layout Reference

This file is the canonical reference for the archive subtree that
`docs-layout-refactor` creates. SKILL.md links here from step 8 (Execute) so
that the agent only loads this content on demand when it actually needs to
build or extend an archive.

## Layout convention

The archive mirrors the active layout (`docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/`). Every
Cat 2 file lands at:

```
docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/<topic>/<file>.md
```

- `v<MAJOR>` is the leading major of the file's source version (`v0.9.7` -> `v0`).
- `v<MAJOR>.<MINOR>` is the minor bucket of the source version (`v0.9.7` -> `v0.9`);
  patch releases collapse into the shared minor dir.
- `<topic>` is the file's topic subdirectory inside the source version
  (e.g. `plans`, `comparisons`, `reviews`, `execution/deploy-checklists`).
- If the source file sits at the version root (no topic subdir), archive it
  under `v<MAJOR>/v<MAJOR>.<MINOR>/misc/`.

For files that lived in a top-level `docs/` subdirectory rather than a
version dir (`docs/git/`, `docs/security/`, etc.), promote the subdirectory
name to the version slot:

```
docs/archives/<top-level-subdir>/<file>.md
```

This is the date-keyed-exception path. Example: `docs/git/gitignore-audit-2026-04-22.md`
archives to `docs/archives/git/gitignore-audit-2026-04-22.md`.

## Example tree

This shows the two layout modes side by side: version-keyed minor-grouped (the
default) and the date-keyed exception (top-level subdirs moved wholesale).

```
docs/archives/
├── README.md                               # the rule + the exception
│
├── v0/
│   └── v0.9/
│       ├── reviews/
│       │   └── comprehensive-review.md     # was docs/v0.9.0/development/comprehensive_review.md
│       └── comparisons/
│           └── comparison-foo.md           # was docs/v0.9.7/comparison-foo.md
│
├── v1/
│   └── v1.0/
│       ├── plans/
│       │   └── v1.0.0-implementation-plan.md  # was docs/v1.0.0/development/implementation-plan.md
│       ├── execution/
│       │   └── deploy-checklists/
│       │       ├── v0.9.13.md              # was docs/v1.0.0/deploy-checklist-v0.9.13.md
│       │       └── v0.9.14.md              # was docs/v1.0.0/deploy-checklist-v0.9.14.md
│       └── reviews/
│           └── codebase-review.md          # was docs/v1.0.0/review.md
│
└── test_and_validation/                    # date-keyed exception (moved wholesale)
    ├── baselines/
    ├── plans/
    └── test-results/
```

Note how `v0.9.0` and `v0.9.7` (two patch releases) collapse into a single
`v0/v0.9/` minor bucket, with their artifacts separated by topic subdirectory.

## `docs/archives/README.md` template

Instantiate this template the first time the archive root is created. On
subsequent runs, append new rows to the index table rather than rewriting
the file.

```markdown
# Docs Archive

Historical documentation that is no longer load-bearing for the active
release, kept for traceability. Anything in this tree was promoted by
[`/update refactor`](../../catalog/commands/update.md) as a Category 2
(archive) finding.

## Rule

Everything under `archives/` is **read-only and reversible**. Do not edit in
place. To resurface an archived file:

1. Move it back to its source location (or its modern equivalent).
2. Re-run `/refactor-docs --mode audit` and confirm the new classification.

## Exception

Top-level docs subdirs (`docs/git/`, `docs/security/`, `docs/test_and_validation/`)
move wholesale into `archive/<subdir>/`, preserving their original internal
shape rather than being version-keyed.

## Index

| Archived path | Source path | Source version | Archived on |
|---|---|---|---|
| <archive/v0/v0.9/reviews/comprehensive-review.md> | <docs/v0.9.0/development/comprehensive_review.md> | v0.9.0 | YYYY-MM-DD |
| ... | ... | ... | ... |
```

## Collision rule

Plans and comparison reports are release-prefixed (`v<MAJOR>.<MINOR>.<PATCH>-<slug>.md`),
so two patch releases sharing one minor dir do not collide even after archival:

```
docs/archives/v0/v0.8/plans/v0.8.1-implementation-plan.md
docs/archives/v0/v0.8/plans/v0.8.2-implementation-plan.md   # different release, no collision
```

If two source files still target the same archive destination (rare; a
non-prefixed filename that appears in two version dirs), suffix the older copy
with `-<source-version>`:

```
docs/archives/v0/v0.8/misc/notes-v0.8.1.md
docs/archives/v0/v0.8/misc/notes.md                          # canonical, newer
```

Never silently overwrite.

## Handbook snapshot at release close

Living `docs/handbooks/` stays at the docs root. At `/update release`, snapshot `docs/handbooks/markdown/` (and authored HTML if present) to:

```
docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/handbooks/
```

Do not move the live tree. Generated `html/` is regenerated and stale-checked; it is not the snapshot source of truth.

Name a release snapshot for the version the copied content describes, not the release that prompted the snapshot. Take the snapshot before applying a release's documentation changes only when the destination bears the preceding version. Naming that folder after the new release would assert that old content describes the new version; an auditor can reasonably misread that claim, and an explanatory README does not repair the false directory name.

## What does NOT go in `docs/archives/`

- `docs/DEVLOG.md` at root - always Cat 3 (stale-flag), never archived.
- Active-version directory contents - by definition Cat 4.
- Files cited in `CHANGELOG.md` for the upcoming release - hard floor at Cat 2,
  but those typically live in the active version dir and stay there.
- Binary assets that are orphaned (no inbound refs) - Cat 2 still applies,
  but flag them in the report so the user can confirm they should be archived
  instead of regenerated.
