---
name: docs-layout-refactor
description: Audit and reorganize a project's docs/ folder by applying a lifespan admission test, categorizing every file (Cat 1 delete / Cat 2 archive / Cat 3 stale-flag / Cat 4 active), proposing a version-first layout with a docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/ active tree and docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/ archive subtree, and applying changes only after explicit user confirmation. Use whenever the user says "clean up docs", "reorganize docs", "archive old docs", "docs folder is messy", "audit docs", "refactor docs structure", "the docs are cluttered", "review docs before release", "classify docs by lifespan", "archive prior major version", or before a version bump. SKIP for content accuracy fixes (use update-documentation), repo-root / scripts / CI/CD reorganization (use project-refactor), or CHANGELOG generation (use generate-changelog).
summary_l0: "Audit, categorize, and reorganize docs/ folders with a propose-then-apply workflow and a versioned archive subtree"
overview_l1: "Walk the docs/ tree, answer one lifespan admission question per document, then apply nine weighted heuristics to classify each file as Cat 1 (delete), Cat 2 (archive), Cat 3 (stale but load-bearing), or Cat 4 (active). Propose a version-first reorganization with topical subdirs mirroring the active layout, plus a docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/<topic>/ subtree for Cat 2 items. Default mode is propose-only: no files move until the user explicitly confirms at the gate. Ships an audit-docs.py helper for inventory, reference graphs, and lifespan-contradiction detection. Trigger phrases: clean up docs, reorganize docs, archive old docs, docs folder is messy, audit docs, refactor docs structure, classify docs by lifespan, docs cleanup, prune docs."
version: 2.0.0
---

# Docs Layout Refactor

Systematically audit a project's `docs/` folder, classify every file into one of four explicit dispositions, propose a version-first reorganization with a dedicated `docs/archives/` subtree, and apply changes only after the user confirms the full plan at a confirmation gate.

## When to Use This Skill

Use this skill when you need to:

- Clean up a `docs/` folder that has accumulated stale comparison reports, one-shot deploy checklists, superseded implementation plans, or scattered session histories.
- Audit `docs/` before a release so external reviewers do not have to wade through versions that are no longer load-bearing.
- Establish a `docs/archives/` convention in a project that does not have one yet.
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
5. **Target-layout proposal** - compute the new active tree and the archive tree under `docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/<topic>/`.
6. **Report generation** - write `docs/<next-version>/docs-cleanup-report.md` with the full disposition table.
7. **Confirmation gate** (propose-only is default) - present the plan and wait for explicit user approval.
8. **Execute** (only on approval) - create the archive, move Cat 2, delete Cat 1, leave Cat 3 in place with refresh flags.
9. **Reference repair** - apply the rename-map algorithm from [`references/link-integrity.md`](references/link-integrity.md), then gate the result with [`scripts/link-baseline.py`](scripts/link-baseline.py) or its native Windows sibling [`scripts/link-baseline.ps1`](scripts/link-baseline.ps1).
10. **Verify** - run the seven binary checks listed below; loop back up to three times on residual breakage.

## Version-directory resolution

Every artifact this skill (and the wider plan / implement workflow) reads or writes lives under a per-version directory, `<version_dir>`. Resolve it with the algorithm below so an existing project's layout is honored and a greenfield project gets the canonical one. This is the single source of truth for the docs path scheme; other skills that write per-version artifacts (`implementation-plan`, `known-gaps-tracker`, `implement-phase`) reference this section.

**Canonical layout** (all new projects, and every new version in an existing project):

```
docs/
  releases/
    v<MAJOR>/                     # major bucket: v0, v1, v2, v3, ...
      v<MAJOR>.<MINOR>/           # minor bucket: v3.10, v3.11, ... (patch releases share this)
        plans/                    # release-prefixed plan files (see naming below)
        comparisons/              # release-prefixed comparison reports
        known-gaps.md              # ONE per minor dir, multi-release aware
        analysis.md
        docs-cleanup-report.md
        development/history/       # session histories
```

The major segment is the leading major of the resolved semver (`v3.11.2` -> `v3`); the minor segment is `v<MAJOR>.<MINOR>` (`v3.11.2` -> `v3.11`). Patch releases share their minor directory: `v3.10.0`, `v3.10.1`, and `v3.10.2` all resolve to `docs/releases/v3/v3.10/`. Pre-1.0 versions use `v0` as the major bucket (`docs/releases/v0/v0.1/`). The full patch version appears in filenames, never as another directory level.

**Resolution algorithm** (apply in order, stop at the first that produces a directory):

1. **Canonical exists**: if `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/` already exists, use it.
2. **Legacy exists**: if a legacy v-bucket `docs/v<MAJOR>/v<MAJOR>.<MINOR>/`, singular archive `docs/archive/`, flat `docs/<vSEMVER>/`, or old three-level `docs/versions/v<MAJOR>/<vSEMVER>/` directory exists and is non-empty (and the canonical does not exist), use it in place and surface: `Detected legacy docs layout at <path>. Continuing in place; run /update refactor to migrate to docs/releases/ and docs/archives/.`
3. **Canonical sibling exists**: if any other `docs/releases/v<MAJOR>/v*/` directory already uses the canonical layout, use the canonical path `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/` and create it if missing.
4. **Greenfield default**: when neither layout is present anywhere under `docs/`, default to the canonical path and create the directory chain. Announce: `Creating canonical version directory at docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/.`

**Per-file naming inside a shared minor dir**: because patch releases share one minor directory, plans and comparison reports are release-prefixed so they never collide and each file's target release is visible in a bare `ls`:

- plans: `plans/v<MAJOR>.<MINOR>.<PATCH>-<slug>.md` (e.g. `plans/v3.11.0-workflow-governance-refinements.md`)
- comparison reports: `comparisons/v<MAJOR>.<MINOR>.<PATCH>-comparison-<name>.md`

Use the kebab-safe form (dots and hyphens only, no parentheses or spaces) to preserve the existing `[a-z0-9-]` slug contract and keep names quoting-free for shell, `git mv`, globs, and Markdown links. `known-gaps.md` is the deliberate exception: it stays a single per-minor file with per-patch subsections (see `[[known-gaps-tracker]]`), not a release-prefixed per-artifact file.

**Safety rules**:

- Never move or rename existing legacy directories during plan generation or a normal audit. Migration happens only in the explicit apply / `--canonicalize-layout` path (Step 8).
- `/update release` ALWAYS invokes this skill with `--canonicalize-layout` (v4.0.1), so a release always DETECTS and PROPOSES structural drift. That sets the flag; it does not bypass Step 7. Files still move only after the user approves, and declining leaves the legacy layout honoured in place while the release continues.
- Never write the same artifact into two layouts. Resolution picks exactly one `<version_dir>`.
- On a conflicting state (both legacy and canonical present), prefer the canonical path and report the inconsistency in the *Layout Inconsistencies* section of the report.

## Required living docs architecture

Versioned plans still resolve via the Version-directory algorithm above. Alongside that frozen-per-minor tree, every Nexus-Hub-driven project also keeps a **living** docs split that describes current `main`, never a past state.

**Required** (create if missing; never overwrite inherited files):

- `docs/handbooks/` - README, `markdown/` source of truth, generated `html/`, one non-technical atlas `*.html` walkthrough, technical companion `*.html` files for key components
- `docs/decisions/` - ADRs, never release-scoped
- Living `docs/README.md`, `docs/DEVLOG.md`, `docs/todos.md`

**Self-gated** (never invent):

- `docs/testing/` only if the project already tracks tests that way
- `docs/validation/` only if GxP or signed records exist

Rules:

- Handbooks are edited in place in `docs/handbooks/markdown/`. Generated `html/` is never hand-edited. If markdown and HTML disagree, markdown wins; regenerate HTML or fail `--check`.
- Point HTML walkthroughs at `[[document-to-interactive-html]]` / `/presentify`.
- A missing key-component companion lists the components the codebase has and requires a companion or a recorded known-gap.
- At release close, snapshot `docs/handbooks/markdown/` (and authored HTML if present) to `docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/handbooks/`. Name the snapshot for the version its content describes, not the release that prompted the copy; see [references/archive-layout.md](references/archive-layout.md).
- An inherited repo with a flat `docs/` is a proposed migration, not a destroy-and-replace.

See [references/archive-layout.md](references/archive-layout.md) for the handbook snapshot path inside the archive tree.

## Lifespan admission test

Ask one question for every document: **when does this document stop being true?** The question is enforceable because every document has exactly one true answer and a person who has never seen the repository can answer it from the document's role. The rejected subject-based alternative, "is this about development?", has no useful false answer: nearly every project document qualifies, the bucket absorbs anything, and it needs reorganizing again within a year.

| Answer | Lifespan | Disposition |
|---|---|---|
| Never stops being true while maintained | **Living** | Edit in place; it must describe current truth and never a past state. |
| Stops on supersession | **Append-only** | Keep the superseded record and add or link its successor. |
| Stops at release close | **Frozen-at-close** | Move after close with its shape preserved. |
| Never, because it is a signed or otherwise controlled record | **Controlled record** | Never edit after signing and never archive through this tooling. |
| It was already frozen before this audit | **Already-frozen** | Preserve in place and do not reclassify it as living. |
| It can be regenerated from an authoritative source | **Generated** | Bind it to a drift test; never archive it. |

An indeterminate answer gets the Cat 3 leave-in-place floor for manual review. The bundled `audit-docs.py` exposes the same six dispositions through `classify_lifespan`; its recognized-name table is only a shortcut to this admission test.

## Cross-cutting documentation subtrees (non-versioned)

Not every `docs/` subtree is a version-scoped artifact. Many projects keep long-lived, cross-cutting documentation at the `docs/` root that is deliberately *not* tied to a single release: architecture decision records, RFCs, specifications, governance policy, runbooks, a solutions knowledge base, and reference material. These subtrees are the companion to the version buckets above, and this skill treats them as a distinct disposition class so that a downstream `/plan` or `/implement` run has a canonical rule to follow instead of inventing one.

**Lookup fast path** (match on the directory name at the `docs/` root, case-insensitive; aliases in parentheses): this table accelerates the admission test but does not replace it.

| Class | Directories | Behavior |
|---|---|---|
| **Append-only decision logs** | `adr/` (`adrs`, `decisions`, `architecture/decisions`), `rfc/` (`rfcs`), `proposals/` | Records are *superseded*, never deleted - a superseded ADR/RFC is still part of the history. |
| **Living handbooks** | `handbooks/` | Required living tree (`markdown/` source of truth, generated `html/`). Never version-archive the live tree; snapshot at release close instead. |
| **Architecture and design** | `architecture/`, `design/` | Long-lived system documentation. Leave in place. |
| **Diataxis content** | `tutorials/`, `how-to/` (`howto`, `how-to-guides`), `reference/`, `explanation/` (`concepts`), `guides/` | Maintained against the current codebase, not a past release. |
| **Operations** | `runbooks/` (`runbook`), `playbooks/`, `troubleshooting/`, `ops/` (`operations`) | Living operational docs. |
| **Governance, policy and legal** | `policy/` (`policies`, `governance`), `security/`, `compliance/`, `legal/` (`licenses`), `constitution.md` | Load-bearing governance. |
| **Reference collections** | `specs/` (`specifications`), `api/` (`api-reference`), `solutions/`, `glossary/`, `faq/` (`faqs`), `examples/` | Leave in place; flag stale entries for refresh. |
| **Localization** | `i18n/`, `locales/`, per-language dirs (`en/`, `fr/`, `zh/`, ...) | Per-language mirrors of the above. Leave in place. |

All directory names above are matched relative to the `docs/` root (e.g. `docs/tutorials/`).

**Default disposition** for every file under a recognized subtree:

- **Hard floor at Cat 3.** These files are never auto-deleted (Cat 1) and never auto-archived (Cat 2) by the version heuristics. They rise to Cat 4 when actively referenced or in-flight. This floor sits alongside the signal 2 and signal 6 floors in Step 4.
- **Exempt from version-based archival.** Signal 1 (version-vs-active) and whole-major archival (Step 5) never apply - these subtrees live outside the canonical `docs/releases/` scheme by design.
- **Never reclassified by semantic content.** The skill does not split, rename, merge, or re-bucket these subtrees by meaning (e.g. it never partitions ADRs into "design-spec" vs "governance-policy", because it has no reference layout to validate such a split against). Structural reorganization of a recognized subtree happens only when the user explicitly requests it AND supplies the target shape.
- **Whole-subtree archival is opt-in only.** If a project genuinely retires one of these subtrees, archive it as a single unit through the Partial path at the Step 7 gate - never as an automated proposal.

**Unrecognized subtrees**: classify `docs/<name>/` by answering the lifespan admission test for its contents. A new name containing living documents is living even though the name is absent from the lookup table. Only when the answer is genuinely indeterminate does the Cat 3 leave-in-place floor apply. This preserves the signal 2 and signal 6 floors and avoids using a name list as policy.

**Documentation tooling and generated output** are not content and follow a separate rule, since most `docs/` trees are built by a static-site generator (Sphinx, MkDocs, Jekyll, Hugo, Docusaurus, VuePress):

- **Generator scaffolding** - Sphinx (`source/`, `_static/`, `_templates/`, `conf.py`), Jekyll (`_layouts/`, `_includes/`, `_data/`), MkDocs / Docusaurus / VuePress (`src/`, `static/`, `.vuepress/`): active machinery. Same leave-in-place floor as the content subtrees above; never archived or reclassified.
- **Generated build output** - Sphinx `_build/`, Jekyll `_site/`, MkDocs `site/`, Hugo `public/`, Docusaurus `.docusaurus/`, and any `dist/`: regenerable, not source. This is the one exception to the Cat 3 floor - the skill never archives it, recommends it be gitignored, and deletes it only with the explicit Cat 1 confirmation (never silently). Do not treat stale generated HTML as archivable content.
- **Media and asset dirs** - `assets/`, `images/`, `img/`, `media/`, `diagrams/`: follow the binary-asset rule in Edge Case 4 (inventory-only; orphans propose Cat 2 archive, never Cat 1).
- **Tool-managed versioned docs** - Docusaurus `versioned_docs/` and `versioned_sidebars/` are the generator's own versioning mechanism; leave them to the tool and never remap them into the canonical `docs/releases/` scheme.

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
| `version_dir` | string\|null | Version segment: `v<MAJOR>.<MINOR>` under the two-level scheme (`docs/releases/v3/v3.11/...`, and the `docs/archives/...` equivalent) or the full `vX.Y.Z` under the legacy flat layout; null if not under a version dir. |
| `topic_dir` | string\|null | Topic subdirectory under the version dir (e.g. `plans`, `comparisons`), or null when the file sits at the version-dir root. |
| `layout` | string\|null | `releases`, `v-bucket`, `flat`, or `versions`; null outside a version tree. |
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

### Step 4 - Categorization (nine weighted heuristics)

Signals 2 and 6 are **hard floors**: they can only raise a category, never lower it. Files under a recognized cross-cutting subtree carry an additional hard floor at Cat 3 - see [Cross-cutting documentation subtrees (non-versioned)](#cross-cutting-documentation-subtrees-non-versioned).

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
| 9 | **Lifespan contradiction**: the canonical rule in [references/link-integrity.md](references/link-integrity.md) finds a frozen-at-close document changed after release close. | Finding only; never move automatically. Add it to the report with both dates. |

Aggregate the weighted signals, then apply the hard floors. The four categories:

| Category | Disposition |
|---|---|
| **Cat 1** | Safe to delete outright. |
| **Cat 2** | Archive under `docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/<topic>/<file>.md`. |
| **Cat 3** | Stale but load-bearing - leave in place, flag for refresh in the report. |
| **Cat 4** | Transient or currently active - revisit in a later run. |

### Step 5 - Target-layout proposal

For each Cat 2 file, compute the archive destination using the canonical layout:

```
docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/<topic>/<file>.md
```

- `v<MAJOR>` is the leading major segment of the file's `version_dir` (e.g., `v3.11.2` -> `v3`).
- `v<MAJOR>.<MINOR>` is the minor bucket of the source version (`v3.11.2` -> `v3.11`); patch releases collapse into it.
- `<topic>` is its `topic_dir`, or `misc` if it sits directly at the version-dir root.

Legacy archive sources `docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/`, `docs/archive/<vSEMVER>/`, and `docs/archive/versions/v<MAJOR>/<vSEMVER>/` are honored in place. An approved `/refactor-docs --canonicalize-layout` pass migrates them to `docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/`. Mixed layouts are reported from the helper's `layout` field rather than guessed.

Resolve archive-path collisions by suffixing with `-<source-version>` (e.g., `plans/v0.8.1-implementation-plan.md`).

For the active tree, the canonical layout is `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/` (patch releases share the minor dir), with `plans/` and `comparisons/` subdirs - see [Version-directory resolution](#version-directory-resolution) for the full algorithm and per-file naming. Propose any renames or topical regroupings that bring older version dirs in line with the active layout. Mirror the active version's directory shape (e.g., if `<active_version_dir>/` uses `plans/` and `review/` subdirs, propose the same subdirs inside each archived version).

**Working-version awareness**: when the active major version is `vN`, this skill treats any `docs/releases/v<M>/` bucket with `M < N` as a candidate for *whole-major archival* into `docs/archives/v<M>/`. Whole-major archival is triggered only via `/refactor-docs --auto-archive-older-versions` or explicit user opt-in at the Phase 7 gate; never implicitly. The current version is always preserved. Cross-cutting non-versioned subtrees are never swept; see [Cross-cutting documentation subtrees (non-versioned)](#cross-cutting-documentation-subtrees-non-versioned).

Build a target-tree preview as a Markdown tree block for the report.

### Step 6 - Report generation

Write `docs/<next-version>/docs-cleanup-report.md` (or the path resolved in step 1). Required sections:

```markdown
# Docs Cleanup Report -- <project> -- <YYYY-MM-DD>

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
| docs/releases/v0/v0.8/comparison-foo.md | Cat 2 | 1, 3 | docs/archives/v0/v0.8/comparisons/comparison-foo.md | |
| docs/v0.9.5/comparison-orphan.md | Cat 1 | 4, 8 | (delete) | mtime 220d, no inbound refs |
| docs/v1.1.5/known-gaps.md | Cat 4 | 2 | (keep) | inbound refs from AGENTS.md |
| ... |

## Cat 3 refresh queue

| Path | Why stale | Suggested action |
|---|---|---|
| ... |

## Lifespan contradictions

| File | Bucket | Release close date | Offending commit date |
|---|---|---|---|
| ... | ... | ... | ... |

## Target tree preview

\`\`\`
docs/
├── DEVLOG.md
├── archive/
│   ├── README.md
│   ├── v0/
│   │   └── v0.8/
│   │       └── comparisons/comparison-foo.md
│   └── v1/
│       └── v1.0/
└── v2/
    ├── v2.0/          # kept (active minor - 1)
    │   ├── plans/
    │   └── comparisons/
    └── v2.1/          # kept (active minor)
        ├── plans/
        └── comparisons/
\`\`\`

## Self-classification

This report classifies itself as Cat 4 (transient/active). A future run will promote it to Cat 2 once the version it documents is no longer active.
```

The report is always written, regardless of mode. It is the deliverable in propose-only mode and the audit trail in apply mode.

### Step 7 - Confirmation gate (only when --apply or --mode full)

In propose-only mode, stop here and tell the user where the report lives.

In apply mode, follow the active instruction template's `Consequential Decisions` rule, then present the plan:

```
Docs cleanup plan:

  Archive (Cat 2):    N files -> docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/<topic>/
  Delete  (Cat 1):    N files
  Flag    (Cat 3):    N files (refresh-only, no move)
  Keep    (Cat 4):    N files (active, no change)

  Archive root will be created at: docs/archives/

Proceed?
  1. Yes - apply all changes
  2. Partial - let me select which categories to apply
  3. No  - cancel (report already written)
```

Wait for explicit Y / Partial / N. On Partial, walk the user through Cat 1 and Cat 2 separately.

### Step 8 - Execute (only after the user confirms)

In this order:

1. **Create archive root**: ensure `docs/archives/` exists. Create `docs/archives/README.md` if absent, using the template from [`references/archive-layout.md`](references/archive-layout.md). Append rows to the existing index if the README already exists.
2. **Move Cat 2 files**: for each, use the **copy + verify + delete** protocol from `project-refactor` - never use atomic move across directories.
3. **Delete Cat 1 files**: one by one. Empty version directories left after a sweep require a second explicit user confirmation before removal.
4. **Cat 3**: take no file action. The report already lists them for refresh.
5. **Canonicalize layout** (only when `--canonicalize-layout` was set): run `audit-docs.py canonicalize-layout --root ./docs` after approval to migrate the legacy v-bucket `docs/v<MAJOR>/v<MAJOR>.<MINOR>/`, flat `docs/<vSEMVER>/`, and `docs/versions/v<MAJOR>/<vSEMVER>/` sources into `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/`. Migrate legacy singular `docs/archive/` sources to `docs/archives/` with the same minor bucketing. Refuse destination collisions, queue every rename for Step 9, and never merge silently.
6. **Whole-major archival** (only when `--auto-archive-older-versions` was set): move entire `docs/releases/v<M>/` buckets (where `M < active_major` and the bucket has at least one tag or CHANGELOG entry) into `docs/archives/v<M>/`. Never include the in-flight version.
7. **`--migrate-known-gaps`** (only when flag was set): append a `## Stale documentation flagged by /refactor-docs` section to `<next_version_dir>/known-gaps.md`, one bullet per Cat 3 entry. Match by file path to avoid duplicates.

### Step 9 - Reference repair

This step is REQUIRED when any file moves. Before the move, run `link-baseline.py baseline --root . --out <baseline>`; after the move and repair, capture `<current>` the same way and run `link-baseline.py diff --before <baseline> --after <current>`. Follow [`references/link-integrity.md`](references/link-integrity.md): derive file renames from `git diff --name-status -M`, resolve links from each source's pre-move location, map the resolved target, and re-express it from the post-move source. Apply a separate directory-prefix map because git detects file renames, not directory links.

Re-run `audit-docs.py refgraph` against the new tree for non-Markdown inbound paths. For Cat 1 deletions, refgraph must report zero remaining inbound references. If any persist, surface them in the final report and revert the deletion - never leave dangling references.

### Step 10 - Verify

Run the seven binary checks (see Verification section below). On any FAIL, loop back to step 9 up to three times. Surface unresolved items to the user.

## Categorization Heuristics - Worked Examples

| File | Signals matched | Resulting category | Why |
|---|---|---|---|
| `docs/releases/v0/v0.8/comparison-x.md` | 1, 3 (filename pattern) | Cat 2 | Old version, comparison report, no external refs. |
| `docs/v0.9.5/comparison-orphan.md` | 4 (age > 180d), 8 (no inbound) | Cat 1 | Old, no refs, comparison report tied to rejected dep. |
| `docs/v1.0.0/RELEASE_NOTES.md` | 3, 6 (CHANGELOG citation) | Cat 2 | CHANGELOG floor prevents Cat 1; release artifact. |
| `docs/v1.1.5/plans/foo.md` | 2 (inbound refs from active), Cat 4 floor | Cat 4 | Active version + inbound refs = always Cat 4. |
| `docs/DEVLOG.md` | 2 (inbound from AGENTS.md), age < 60d | Cat 3 | Edge case: always Cat 3 at root; never archived or deleted. |
| `docs/git/gitignore-audit-2026-04-22.md` | 3 (date-stamped one-shot), 4 (age) | Cat 2 | Date-keyed audit; archive for traceability. |
| `docs/adr/0007-use-postgres.md` | cross-cutting subtree (append-only log) | Cat 3 | ADR: superseded records are kept as part of the decision history, never deleted or version-archived. |
| `docs/policy/mcp-reverse-engineering-matrix.md` | cross-cutting subtree (governance) | Cat 3 | Governance policy; leave in place regardless of age, even with no inbound docs links. |

## Edge Cases

| # | Case | Rule |
|---|---|---|
| 1 | `docs/DEVLOG.md` at root | Cat 3 if mtime within 60 days. Never archive or delete. Flag for "candidate split by version" if size > 200 KB. |
| 2 | In-flight (active) version dir | `--keep-current-version` default ON -> skip entirely. The active dir is by definition Cat 4. |
| 3 | File referenced by a skill or command outside `docs/` | Force to Cat 3 regardless of age. Emit "blocked: external reference at `<path>:<line>`" in the report. |
| 4 | Binary asset (`.png`, `.pdf`, `.xlsx`) | Inventory-only. Orphan binaries -> propose Cat 2 archive, never Cat 1. |
| 5 | No version directories | Fall back to topic-based layout. Skip the archive proposal but still emit the Cat 1 deletion list. |
| 6 | `docs/archives/` already exists | Treat as authoritative. Never re-classify anything inside. Append to `docs/archives/README.md`. |
| 7 | File appears in `CHANGELOG.md` as a delivered artifact | Auto-Cat 2. Never Cat 1. |
| 8 | Symlinks under `docs/` | Skip with warning. Never move or delete. |
| 9 | Empty version directory | Cat 1 candidate. Require explicit user confirmation; do not auto-delete in `--apply`. |
| 10 | Archive-path collision | Suffix with `-<source-version>`. Never silently overwrite. |
| 11 | Cross-cutting non-versioned subtree, including a name absent from the lookup fast path | Answer the [lifespan admission test](#lifespan-admission-test). Apply the Cat 3 floor only if the answer is genuinely indeterminate; whole-subtree archival still requires explicit opt-in at the gate. |
| 12 | Doc-generator output dir (`docs/_build/`, `_site/`, `site/`, `public/`, `.docusaurus/`, `dist/`) | Regenerable, not content. Never archived; recommend gitignoring; delete only with explicit Cat 1 confirmation. Generator scaffolding (`source/`, `_static/`, `_templates/`) gets the Cat 3 leave-in-place floor instead. |

See [references/archive-layout.md](references/archive-layout.md) for the canonical archive tree shape and the `docs/archives/README.md` template that step 8 instantiates.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This version dir is only a year old, leave it." | The archive is reversible. Anything older than `active_version - 2` belongs in archive for traceability. Cat 2 keeps the file readable; it does not delete it. |
| "The file has no inbound refs, so I can delete it." | Check CHANGELOG citation first (signal 6 is a hard floor at Cat 2). A file the CHANGELOG cites is part of the release record even if nothing currently links to it. |
| "Let me just apply the changes since they look obvious." | Propose-only is the default for a reason. Misclassifications are easier to catch in a report than to undo from git. The confirmation gate is the safety mechanism. |
| "DEVLOG.md is huge, let me archive it." | Edge case 1: `DEVLOG.md` at root is always Cat 3, never archived or deleted. Flag for "candidate split by version" instead. |
| "The active version dir has some stale-looking files, let me clean them up." | The active version dir is by definition Cat 4. `--keep-current-version` is default ON. Run again after the next version bump promotes those files to Cat 2 candidates. |
| "I'll just delete the Cat 1 files directly with rm; the script is overkill." | The script's deletion path runs the verification step (no broken inbound refs). Skipping it risks leaving dangling references in skills, commands, or `CHANGELOG.md`. |
| "We can skip handbooks until the v4.0 rename." | Living docs do not need the container rename. Required `docs/handbooks/` and `docs/decisions/` sit on the current path scheme; v4.0 only snapshots and renames the archive later. |

## Verification

Run after step 9. Each check is binary; FAIL on any item loops back up to three times.

- [ ] **No newly broken internal Markdown links** - `link-baseline.py diff --before <baseline> --after <current>` reports zero `newly_broken` and exits 0.
- [ ] **All originals accounted for** - set equality: every file in the pre-move inventory now exists at its destination, was deleted per Cat 1, or is unchanged (Cat 3 / Cat 4).
- [ ] **`docs/archives/README.md` exists** and lists every archived path.
- [ ] **No external references to deleted files** - refgraph confirms zero inbound refs from outside `docs/` to any Cat 1 path.
- [ ] **`git status --porcelain` count equals (moves + deletes + report write + archive README)** - surprise mutations halt with a diff dump for user review.
- [ ] **Active-version dir untouched** - diff against pre-move state for `docs/<next-version>/` shows only the new `docs-cleanup-report.md`.
- [ ] **Report self-classified as Cat 4** - sanity check that the report does not claim to be ready for archival immediately.
- [ ] **No lifespan contradiction was auto-moved** - every Signal 9 result appears under *Lifespan contradictions* with the bucket, release close date, and offending commit date.
- [ ] **Snapshot names assert their content version** - each frozen snapshot directory names the version described by the copied content.

## Related Skills

- [[project-refactor]] -- reorganize repo root files, scripts, configs, and CI/CD artifacts (not under `docs/`). Run this before `docs-layout-refactor` if root layout is also messy.
- [[documentation-consistency]] -- link-integrity sweep. Run after this skill's apply phase to catch any references that survived `refgraph`.
- [[known-gaps-tracker]] -- per-version unfinished work tracker. Invoke with `--migrate-known-gaps` to auto-promote Cat 3 findings.
- **Same-page anchors need re-pointing on every move.** A `](#heading)` link is a same-page reference until its content moves to another file, at which point it dangles and no link checker sees it (a `#` target reads as same-page by definition). Grep each moved block for `](#` and repoint to `](../path/to/origin.md#heading)`. This bit the v3.18.0 Phase 3 relocation: three anchors moved, the link check passed, and they were found by reading the file.
- `docs/policy/docs-retention.md` -- the retention rule this skill EXECUTES. `scripts/check_docs_retention.py` reports which `development/` subtrees are due (two or more minors behind current) and names the destination; this skill performs the move and the reference repair, propose-then-apply.
- [[version-upgrade]] -- the parent release workflow. `/refactor-docs` is invoked as Step B4 of `/update-version`.
- `/update-documentation` -- companion command that checks whether docs are factually accurate against the code; that command checks **content**, this skill checks **structure**.

---

## Migration from 1.x

Version 2.0.0 renames the canonical active container from the legacy `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` shape to `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/` and the legacy singular `docs/archive/` container to `docs/archives/`. Run `/refactor-docs --canonicalize-layout` once, approve the proposed map, and let Step 9 repair references. The Phase 1 rename-map algorithm plus pre/post unresolved-link set diff is the proof: zero `newly_broken` is required before the migration completes.

**Version**: 2.0.0
**Last Updated**: August 2026
