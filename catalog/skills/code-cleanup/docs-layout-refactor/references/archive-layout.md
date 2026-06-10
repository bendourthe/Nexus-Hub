# `docs/archive/` Layout Reference

This file is the canonical reference for the archive subtree that
`docs-layout-refactor` creates. SKILL.md links here from step 8 (Execute) so
that the agent only loads this content on demand when it actually needs to
build or extend an archive.

## Layout convention

The archive mirrors the active layout. Every Cat 2 file lands at:

```
docs/archive/<source-version>/<topic>/<file>.md
```

- `<source-version>` is the file's owning version directory (e.g. `v0.9.7`).
- `<topic>` is the file's topic subdirectory inside the source version
  (e.g. `plans`, `reviews`, `execution/deploy-checklists`).
- If the source file sits at the version root (no topic subdir),
  archive it under `<source-version>/misc/`.

For files that lived in a top-level `docs/` subdirectory rather than a
version dir (`docs/git/`, `docs/security/`, etc.), promote the subdirectory
name to the version slot:

```
docs/archive/<top-level-subdir>/<file>.md
```

This is the date-keyed-exception path. Example: `docs/git/gitignore-audit-2026-04-22.md`
archives to `docs/archive/git/gitignore-audit-2026-04-22.md`.

## Example tree

This is the example the user supplied in the original request. It shows the
two layout modes side by side: version-keyed (the default) and date-keyed
exception (top-level subdirs moved wholesale).

```
docs/archive/
├── README.md                           # the rule + the exception
│
├── v0.9.0/
│   └── reviews/
│       └── comprehensive-review.md     # was docs/v0.9.0/development/comprehensive_review.md
│
├── v1.0.0/
│   ├── plans/
│   │   └── implementation-plan.md      # was docs/v1.0.0/development/implementation-plan.md
│   ├── execution/
│   │   └── deploy-checklists/
│   │       ├── v0.9.13.md              # was docs/v1.0.0/deploy-checklist-v0.9.13.md
│   │       └── v0.9.14.md              # was docs/v1.0.0/deploy-checklist-v0.9.14.md
│   ├── reviews/
│   │   └── codebase-review.md          # was docs/v1.0.0/review.md
│   └── audits/
│       └── repo-history-audit.md       # was docs/v1.0.0/repo-history-audit.md
│
└── test_and_validation/                # date-keyed exception (moved wholesale)
    ├── baselines/
    ├── plans/
    └── test-results/
```

## `docs/archive/README.md` template

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

Everything under `archive/` is **read-only and reversible**. Do not edit in
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
| <archive/v0.9.0/reviews/comprehensive-review.md> | <docs/v0.9.0/development/comprehensive_review.md> | v0.9.0 | YYYY-MM-DD |
| ... | ... | ... | ... |
```

## Collision rule

If two source files target the same archive destination (rare; happens when
two version dirs contain a file with the same name), suffix the older copy
with `-<source-version>`:

```
docs/archive/plans/implementation-plan-v0.8.1.md
docs/archive/plans/implementation-plan.md            # canonical, newer
```

Never silently overwrite.

## What does NOT go in `docs/archive/`

- `docs/DEVLOG.md` at root - always Cat 3 (stale-flag), never archived.
- Active-version directory contents - by definition Cat 4.
- Files cited in `CHANGELOG.md` for the upcoming release - hard floor at Cat 2,
  but those typically live in the active version dir and stay there.
- Binary assets that are orphaned (no inbound refs) - Cat 2 still applies,
  but flag them in the report so the user can confirm they should be archived
  instead of regenerated.
