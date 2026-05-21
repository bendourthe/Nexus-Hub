---
name: docs-layout-refactor
description: Audit and reorganize a project's docs/ folder by categorizing every file (Cat 1 delete / Cat 2 archive / Cat 3 stale-flag / Cat 4 active), proposing a version-first layout with a docs/versions/v<MAJOR>/ active tree and a docs/archive/versions/v<MAJOR>/ archive subtree, and applying changes only after explicit user confirmation. Use whenever the user says "clean up docs", "reorganize docs", "archive old docs", "docs folder is messy", "audit docs", "refactor docs structure", "the docs are cluttered", "review docs before release", "archive prior major version", or before a version bump. SKIP for content accuracy fixes (use update-documentation), repo-root / scripts / CI/CD reorganization (use refactor-project, formerly refactor-project-layout), or CHANGELOG generation (use generate-changelog).
summary_l0: "Audit, categorize, and reorganize docs/ folders with a propose-then-apply workflow and a versioned archive subtree"
overview_l1: "Walk the docs/ tree, score every file with eight weighted heuristics (age, inbound refs, CHANGELOG citation, filename patterns, duplication, body keywords), classify each as Cat 1 (delete), Cat 2 (archive), Cat 3 (stale but load-bearing), or Cat 4 (active). Propose a version-first reorganization with topical subdirs mirroring the active layout, plus a docs/archive/<version>/<topic>/ subtree for Cat 2 items. Default mode is propose-only: no files move until the user explicitly confirms at the gate. Ships an audit-docs.py helper that emits a JSON inventory and reference graph without being read into context. Trigger phrases: clean up docs, reorganize docs, archive old docs, docs folder is messy, audit docs, refactor docs structure, docs are cluttered, review docs before release, docs cleanup, prune docs."
---

# Docs Layout Refactor

Systematically audit a project's `docs/` folder, classify every file into one of four explicit dispositions, propose a version-first reorganization with a dedicated `docs/archive/` subtree, and apply changes only after the user confirms the full plan at a confirmation gate.

## When to Use This Skill

Use this skill when you need to:

- Clean up a `docs/` folder that has accumulated stale comparison reports, one-shot deploy checklists, superseded implementation plans, or scattered session histories.
- Audit `docs/` before a release so external reviewers do not have to wade through versions that are no longer load-bearing.
- Establish a `docs/archive/` convention in a project that does not have one yet.
- Move historical version directories into archive while preserving traceability.
- Surface stale-but-load-bearing files (Cat 3) so they can be refreshed instead of silently rotting.

**Trigger phrases**: "clean up docs", "reorganize docs", "archive old docs", "docs folder is messy", "audit docs", "refactor docs structure", "the docs are cluttered", "review docs before release", "docs cleanup", "prune docs".

### When NOT to Use

| Want to ... | Use this instead |
|---|---|
| Check whether docs are factually accurate against the code | `update-documentation` |
| Reorganize repo root files, scripts, configs, CI/CD (broader than docs) | `project-refactor` (formerly `project-layout-refactor`) |
| Generate release notes from changes | `generate-changelog` |
| Migrate Cat 3 findings into a per-version gap tracker | `known-gaps-tracker` (use `--migrate-known-gaps` to invoke from this skill) |

## How to Invoke

### Claude Code

```
/refactor-docs              # default propose-only mode
/refactor-docs --apply      # propose-then-confirm-then-apply
/refactor-docs --mode audit # used by /wrap-up-session and /run-deep-review (no gate)
```

Or activate the skill directly with any trigger phrase.

### Codex / Gemini / Copilot

Reference this skill by name in the prompt: "Using the docs-layout-refactor skill, audit my docs/ folder and propose a version-first reorganization with an archive subtree."

## What This Skill Does

1. **Resolve scope and mode** - parse flags, locate `docs/`, detect the active version from `CHANGELOG.md` or the latest `docs/v*` directory.
2. **Tree fingerprinting** - run the bundled [`scripts/audit-docs.py`](scripts/audit-docs.py) helper in `inventory` mode to emit NDJSON per file.
3. **Reference graph** - run the same helper in `refgraph` mode to map inbound references from outside `docs/`. Windows users without Python on PATH can invoke the [`scripts/audit-docs.ps1`](scripts/audit-docs.ps1) wrapper instead, which auto-detects `python` / `py -3` / `python3`.
4. **Categorization** - apply eight weighted heuristics to assign Cat 1 / Cat 2 / Cat 3 / Cat 4 to every file.
5. **Target-layout proposal** - compute the new active tree and the archive tree under `docs/archive/<source-version>/<topic>/`.
6. **Report generation** - write `docs/<next-version>/docs-cleanup-report.md` with the full disposition table.
7. **Confirmation gate** (propose-only is default) - present the plan and wait for explicit user approval.
8. **Execute** (only on approval) - create the archive, move Cat 2, delete Cat 1, leave Cat 3 in place with refresh flags.
9. **Reference repair** - update inbound links so external referrers still resolve.
10. **Verify** - run the seven binary checks listed below; loop back up to three times on residual breakage.

## Instructions

### Step 1 - Resolve scope and mode

Parse the invocation for these flags:

| Flag | Behavior |
|---|---|
| *(none)* | Propose-only. Runs steps 1-7 and stops at the gate. **Default.** |
| `--apply` | After the gate, run steps 8-10. Requires explicit Y. |
| `--mode audit\|full` | `audit` skips the gate entirely. `full` is equivalent to `--apply`. |
| `--scope <subpath>` | Restrict to `docs/<subpath>` (e.g., `--scope v0.8.1`). |
| `--output <path>` | Override the report path. |
| `--keep-current-version` | Never touch the in-flight version directory. **Default ON.** |
| `--migrate-known-gaps` | After step 8, append Cat 3 entries to `docs/<next-version>/known-gaps.md`. |

Detect the active version in this order, stop at the first that succeeds:

1. Most recent version heading in `CHANGELOG.md` (e.g., `## [1.2.1]` -> `v1.2.1`). Skip `## [Unreleased]`.
2. Latest git tag: `git tag --sort=-v:refname | head -n 1`.
3. Latest `docs/v*/` directory by mtime.
4. Fallback `vUnknown` only with explicit user confirmation.

Compute the next version (default: bump MINOR, reset PATCH to 0) and set the report path to `docs/<next-version>/docs-cleanup-report.md`. If `<next-version>` cannot be resolved, fall back to `docs/docs-cleanup-<YYYY-MM-DD>.md`.

### Step 2 - Tree fingerprinting (inventory)

Invoke the bundled helper:

```bash
python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py \
    inventory \
    --root ./docs
```

The helper emits one NDJSON record per file with these fields:

| Field | Type | Notes |
|---|---|---|
| `path` | string | Path relative to `--repo-root` (defaults to `.`). |
| `size` | int | Bytes. |
| `mtime` | string | ISO 8601. |
| `mtime_age_days` | int | Days since mtime. |
| `sha256_prefix` | string | First 12 hex chars of sha256 (used for duplicate detection). |
| `version_dir` | string\|null | The `vX.Y.Z` segment if the path starts with `docs/v*/`. |
| `topic_dir` | string\|null | The first sub-directory under the version dir, if any. |
| `extension` | string | File extension (lowercase, with leading dot). |
| `line_count` | int\|null | Null for binary files. |
| `is_binary` | bool | True for non-text content. |

Pipe to a working file you can re-read between steps, or parse line-by-line as you go.

### Step 3 - Reference graph

```bash
python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py \
    refgraph \
    --root ./docs --repo-root .
```

The helper scans `.md`, `.json`, `.yaml`, `.yml`, `.toml`, `.sh`, `.ps1`, `.py` files outside `docs/` for inbound references to each `docs/` file (markdown links, raw paths, and `CHANGELOG.md` mentions). Output is a single JSON object: `{docs_path: [{referrer, line}, ...]}`.

### Step 4 - Categorization (eight weighted heuristics)

Signals 2 and 6 are **hard floors**: they can only raise a category, never lower it.

| # | Signal | Effect |
|---|---|---|
| 1 | **Version-vs-active**: file lives in a version dir older than `active_version - 2`. | Strong Cat 2 candidate. |
| 2 | **External reference count** (refgraph): > 0 inbound refs from outside `docs/`. | **Hard floor at Cat 3** (Cat 4 if the file is in the active version dir). |
| 3 | **Filename pattern**: `RELEASE_NOTES.md`, `known-gaps.md`, `comparison-*.md`, `implementation-plan.md`, `session-*.md`, `deploy-checklist-*.md`. | Cat 2 once the owning version is stable. |
| 4 | **Age**: `mtime_age_days > 180` and no inbound refs. | +Cat 1 weight. `mtime_age_days < 30` -> +Cat 4 weight. |
| 5 | **Duplication**: identical `sha256_prefix` as another file. | Older copy -> Cat 1. Canonical -> Cat 3. |
| 6 | **CHANGELOG citation**: file or owning directory cited in `CHANGELOG.md`. | **Hard floor at Cat 2** (never Cat 1). |
| 7 | **Body keywords**: `DRAFT` / `WIP` / `scratch` / `tmp` with `mtime_age_days > 30`. | Cat 1 candidate. `TODO` / `FIXME` in the active-version dir -> Cat 4. |
| 8 | **Inbound link count from other docs**: 0 inbound from the active version dir. | +Cat 1/2 weight. >= 1 -> hold at current category. |

Aggregate the weighted signals, then apply the hard floors. The four categories:

| Category | Disposition |
|---|---|
| **Cat 1** | Safe to delete outright. |
| **Cat 2** | Archive under `docs/archive/<source-version>/<topic>/<file>.md`. |
| **Cat 3** | Stale but load-bearing - leave in place, flag for refresh in the report. |
| **Cat 4** | Transient or currently active - revisit in a later run. |

### Step 5 - Target-layout proposal

For each Cat 2 file, compute the archive destination using the canonical layout:

```
docs/archive/versions/v<MAJOR>/v<MAJOR>.<MINOR>.<PATCH>/<topic>/<file>.md
```

- `v<MAJOR>` is the leading major segment of the file's `version_dir` (e.g., `v2.1.0` -> `v2`).
- `v<MAJOR>.<MINOR>.<PATCH>` is the full source version directory name.
- `<topic>` is its `topic_dir`, or `misc` if it sits directly at the version-dir root.

Legacy projects that already use the flat layout `docs/archive/v<SEMVER>/<topic>/...` are honored (no `versions/` segment); a future canonicalization pass via `/refactor-docs --canonicalize-layout` migrates them when the user opts in. Mixed layouts within the same project are flagged in the *Layout Inconsistencies* section of the report.

Resolve archive-path collisions by suffixing with `-<source-version>` (e.g., `plans/implementation-plan-v0.8.1.md`).

For the active tree, the canonical layout is `docs/versions/v<MAJOR>/v<MAJOR>.<MINOR>.<PATCH>/`. Propose any renames or topical regroupings that bring older version dirs in line with the active layout. Mirror the active version's directory shape (e.g., if `<active_version_dir>/` uses `plans/` and `review/` subdirs, propose the same subdirs inside each archived version).

**Working-version awareness**: when the active major version is `vN`, this skill treats any major bucket `v<M>` with `M < N` as a candidate for *whole-major archival* into `docs/archive/versions/v<M>/`. Whole-major archival is triggered only via `/refactor-docs --auto-archive-older-versions` or explicit user opt-in at the Phase 7 gate; never implicitly. The current (in-flight) version directory is always preserved per `--keep-current-version`.

Build a target-tree preview as a Markdown tree block for the report.

### Step 6 - Report generation

Write `docs/<next-version>/docs-cleanup-report.md` (or the path resolved in step 1). Required sections:

```markdown
# Docs Cleanup Report — <project> — <YYYY-MM-DD>

**Active version:** <vX.Y.Z>
**Mode:** <propose-only | --apply | audit>
**Scope:** <docs/ | docs/<subpath>>

## Summary

| Category | Count |
|---|---|
| Cat 1 (delete) | N |
| Cat 2 (archive) | N |
| Cat 3 (stale-flag) | N |
| Cat 4 (active) | N |
| **Total** | **N** |

## Dispositions

| Path | Category | Heuristics | Destination | Notes |
|---|---|---|---|---|
| docs/v0.8.1/comparison-foo.md | Cat 2 | 1, 3 | docs/archive/v0.8.1/comparison-foo.md | |
| docs/v0.9.5/comparison-orphan.md | Cat 1 | 4, 8 | (delete) | mtime 220d, no inbound refs |
| docs/v1.1.5/known-gaps.md | Cat 4 | 2 | (keep) | inbound refs from AGENTS.md |
| ... |

## Cat 3 refresh queue

| Path | Why stale | Suggested action |
|---|---|---|
| ... |

## Target tree preview

\`\`\`
docs/
├── DEVLOG.md
├── archive/
│   ├── README.md
│   └── versions/
│       ├── v0/
│       │   └── v0.8.1/
│       │       └── misc/comparison-foo.md
│       └── v1/
│           └── v1.0.0/
└── versions/
    └── v2/
        ├── v2.0.0/        # kept (active - 1)
        └── v2.1.0/        # kept (active)
\`\`\`

## Self-classification

This report classifies itself as Cat 4 (transient/active). A future run will promote it to Cat 2 once the version it documents is no longer active.
```

The report is always written, regardless of mode. It is the deliverable in propose-only mode and the audit trail in apply mode.

### Step 7 - Confirmation gate (only when --apply or --mode full)

In propose-only mode, stop here and tell the user where the report lives.

In apply mode, present the plan:

```
Docs cleanup plan:

  Archive (Cat 2):    N files -> docs/archive/<source-version>/<topic>/
  Delete  (Cat 1):    N files
  Flag    (Cat 3):    N files (refresh-only, no move)
  Keep    (Cat 4):    N files (active, no change)

  Archive root will be created at: docs/archive/

Proceed?
  1. Yes - apply all changes
  2. Partial - let me select which categories to apply
  3. No  - cancel (report already written)
```

Wait for explicit Y / Partial / N. On Partial, walk the user through Cat 1 and Cat 2 separately.

### Step 8 - Execute (only after the user confirms)

In this order:

1. **Create archive root**: ensure `docs/archive/` and `docs/archive/versions/` exist. Create `docs/archive/README.md` if absent, using the template from [`references/archive-layout.md`](references/archive-layout.md). Append rows to the existing index if the README already exists.
2. **Move Cat 2 files**: for each, use the **copy + verify + delete** protocol from `project-refactor` - never use atomic move across directories.
3. **Delete Cat 1 files**: one by one. Empty version directories left after a sweep require a second explicit user confirmation before removal.
4. **Cat 3**: take no file action. The report already lists them for refresh.
5. **Canonicalize layout** (only when `--canonicalize-layout` was set): migrate legacy `docs/v<SEMVER>/` directories into the canonical `docs/versions/v<MAJOR>/v<SEMVER>/` layout, and legacy `docs/archive/v<SEMVER>/` into `docs/archive/versions/v<MAJOR>/v<SEMVER>/`. Per-file copy + verify + delete. Queue reference-repair entries for step 9.
6. **Whole-major archival** (only when `--auto-archive-older-versions` was set): move entire `docs/versions/v<M>/` buckets (where `M < active_major` and the bucket has at least one tag or CHANGELOG entry) into `docs/archive/versions/v<M>/`. Never include the in-flight version.
7. **`--migrate-known-gaps`** (only when flag was set): append a `## Stale documentation flagged by /refactor-docs` section to `<next_version_dir>/known-gaps.md`, one bullet per Cat 3 entry. Match by file path to avoid duplicates.

### Step 9 - Reference repair

Re-run `audit-docs.py refgraph` against the new tree. For each moved file, update inbound references:

- Markdown links: `[label](docs/v0.8.1/foo.md)` -> `[label](docs/archive/v0.8.1/foo.md)`.
- Raw paths in `.json`, `.yaml`, `.toml`, `.sh`, `.ps1`, `.py`: same substitution.

For Cat 1 deletions, refgraph should report zero remaining inbound references. If any persist, surface them in the final report and revert the deletion - never leave dangling references.

### Step 10 - Verify

Run the seven binary checks (see Verification section below). On any FAIL, loop back to step 9 up to three times. Surface unresolved items to the user.

## Categorization Heuristics - Worked Examples

| File | Signals matched | Resulting category | Why |
|---|---|---|---|
| `docs/v0.8.1/comparison-x.md` | 1, 3 (filename pattern) | Cat 2 | Old version, comparison report, no external refs. |
| `docs/v0.9.5/comparison-orphan.md` | 4 (age > 180d), 8 (no inbound) | Cat 1 | Old, no refs, comparison report tied to rejected dep. |
| `docs/v1.0.0/RELEASE_NOTES.md` | 3, 6 (CHANGELOG citation) | Cat 2 | CHANGELOG floor prevents Cat 1; release artifact. |
| `docs/v1.1.5/plans/foo.md` | 2 (inbound refs from active), Cat 4 floor | Cat 4 | Active version + inbound refs = always Cat 4. |
| `docs/DEVLOG.md` | 2 (inbound from AGENTS.md), age < 60d | Cat 3 | Edge case: always Cat 3 at root; never archived or deleted. |
| `docs/git/gitignore-audit-2026-04-22.md` | 3 (date-stamped one-shot), 4 (age) | Cat 2 | Date-keyed audit; archive for traceability. |

## Edge Cases

| # | Case | Rule |
|---|---|---|
| 1 | `docs/DEVLOG.md` at root | Cat 3 if mtime within 60 days. Never archive or delete. Flag for "candidate split by version" if size > 200 KB. |
| 2 | In-flight (active) version dir | `--keep-current-version` default ON -> skip entirely. The active dir is by definition Cat 4. |
| 3 | File referenced by a skill or command outside `docs/` | Force to Cat 3 regardless of age. Emit "blocked: external reference at `<path>:<line>`" in the report. |
| 4 | Binary asset (`.png`, `.pdf`, `.xlsx`) | Inventory-only. Orphan binaries -> propose Cat 2 archive, never Cat 1. |
| 5 | No version directories | Fall back to topic-based layout. Skip the archive proposal but still emit the Cat 1 deletion list. |
| 6 | `docs/archive/` already exists | Treat as authoritative. Never re-classify anything inside. Append to `docs/archive/README.md`. |
| 7 | File appears in `CHANGELOG.md` as a delivered artifact | Auto-Cat 2. Never Cat 1. |
| 8 | Symlinks under `docs/` | Skip with warning. Never move or delete. |
| 9 | Empty version directory | Cat 1 candidate. Require explicit user confirmation; do not auto-delete in `--apply`. |
| 10 | Archive-path collision | Suffix with `-<source-version>`. Never silently overwrite. |

See [references/archive-layout.md](references/archive-layout.md) for the canonical archive tree shape and the `docs/archive/README.md` template that step 8 instantiates.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This version dir is only a year old, leave it." | The archive is reversible. Anything older than `active_version - 2` belongs in archive for traceability. Cat 2 keeps the file readable; it does not delete it. |
| "The file has no inbound refs, so I can delete it." | Check CHANGELOG citation first (signal 6 is a hard floor at Cat 2). A file the CHANGELOG cites is part of the release record even if nothing currently links to it. |
| "Let me just apply the changes since they look obvious." | Propose-only is the default for a reason. Misclassifications are easier to catch in a report than to undo from git. The confirmation gate is the safety mechanism. |
| "DEVLOG.md is huge, let me archive it." | Edge case 1: `DEVLOG.md` at root is always Cat 3, never archived or deleted. Flag for "candidate split by version" instead. |
| "The active version dir has some stale-looking files, let me clean them up." | The active version dir is by definition Cat 4. `--keep-current-version` is default ON. Run again after the next version bump promotes those files to Cat 2 candidates. |
| "I'll just delete the Cat 1 files directly with rm; the script is overkill." | The script's deletion path runs the verification step (no broken inbound refs). Skipping it risks leaving dangling references in skills, commands, or `CHANGELOG.md`. |

## Verification

Run after step 9. Each check is binary; FAIL on any item loops back up to three times.

- [ ] **No broken internal markdown links** - rerun `refgraph` against the new tree; zero dangling `](docs/...)` targets.
- [ ] **All originals accounted for** - set equality: every file in the pre-move inventory now exists at its destination, was deleted per Cat 1, or is unchanged (Cat 3 / Cat 4).
- [ ] **`docs/archive/README.md` exists** and lists every archived path.
- [ ] **No external references to deleted files** - refgraph confirms zero inbound refs from outside `docs/` to any Cat 1 path.
- [ ] **`git status --porcelain` count equals (moves + deletes + report write + archive README)** - surprise mutations halt with a diff dump for user review.
- [ ] **Active-version dir untouched** - diff against pre-move state for `docs/<next-version>/` shows only the new `docs-cleanup-report.md`.
- [ ] **Report self-classified as Cat 4** - sanity check that the report does not claim to be ready for archival immediately.

## Related Skills

- [`project-refactor`](../project-refactor/SKILL.md) (formerly `project-layout-refactor`) - reorganize repo root files, scripts, configs, and CI/CD artifacts (not under `docs/`). Run this before `docs-layout-refactor` if root layout is also messy.
- `update-documentation` - check whether docs are factually accurate against the code. Complementary: that skill checks **content**, this skill checks **structure**.
- `known-gaps-tracker` - per-version unfinished work tracker. Invoke with `--migrate-known-gaps` to auto-promote Cat 3 findings.
- `documentation-consistency` - link-integrity sweep. Run after this skill's apply phase to catch any references that survived `refgraph`.
- `version-upgrade` - the parent release workflow. `/refactor-docs` is invoked as Step B4 of `/update-version`.

---

**Version**: 1.1.0
**Last Updated**: May 2026
