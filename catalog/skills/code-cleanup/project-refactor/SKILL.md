---
name: project-refactor
description: Audit and refactor repository project artifacts (root files, scripts, configs, CI/CD, and source layout) to follow declared conventions. Move misplaced files, repair references, archive outdated prior-version artifacts, and verify behavior. Use when the user says "refactor project layout", "clean up root directory", "organize project structure", "apply layout rules", "archive prior version artifacts", "clean up scripts", "organize CI/CD configs", "find empty directories", "remove duplicate files", "find orphaned files", or "consolidate directories". Version-bound project documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/ and closed snapshots use docs/archives/. SKIP for docs/ tree reorganization (use docs-layout-refactor), content accuracy fixes (use update-documentation), or CHANGELOG generation (use generate-changelog).
summary_l0: "Refactor project artifacts with detection, archive placement, and reference repair"
overview_l1: "This skill systematically reorganizes a repository's project artifacts (everything outside the docs/ tree) to follow declared conventions, with impact analysis and reference repair before any file is moved. Scope includes root files, scripts, configs, CI/CD pipelines, and top-level source layout. It also detects prior-major-version artifacts (release notes, deploy checklists, generated reports, snapshot bundles, version-scoped CI workflows) and archives them under archive/versions/v<MAJOR>/v<SEMVER>/ when --archive-prior-versions is set. It also flags empty directories (respecting .gitkeep), duplicate/redundant files, unreferenced orphans, and overcomplicated structure for prune or consolidation, propose-only. Use it when cleaning up a cluttered project root, applying a standard layout ruleset to an existing project, migrating a repo after adopting new conventions, preparing a project for public release, archiving artifacts from a prior major version, or auditing whether a repo matches its declared layout rules. Default mode is propose-only: no files move until the user explicitly confirms at the gate. Trigger phrases: refactor project layout, clean up root directory, organize project structure, apply layout rules, archive prior version artifacts, organize CI/CD configs. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
---

# Project Refactor

Systematically reorganize a repository's project artifacts (everything outside the `docs/` tree) to follow declared conventions, with full impact analysis and reference repair before any file is moved. Also archives prior-major-version artifacts when invoked with `--archive-prior-versions`.

This skill replaces and broadens the former `project-layout-refactor`. The old name still resolves to this skill for backwards compatibility.

## When to Use This Skill

Use this skill when you need to:

- Clean up a cluttered project root with too many loose files
- Apply a standard layout ruleset to an existing project (scripts/, configs/, src/, CI/CD)
- Migrate a repo after adopting new conventions (e.g., moving DEVLOG.md to `docs/`)
- Prepare a project for public release with a clean, navigable structure
- Archive prior-major-version artifacts that live outside `docs/` (release notes, deploy checklists, snapshot bundles, generated reports, version-scoped CI workflows)
- Audit whether a repo's current layout matches its declared rules

**Trigger phrases**: "refactor project layout", "refactor repo layout", "clean up root directory", "too many files in root", "organize project structure", "apply layout rules", "move files to correct directories", "root is cluttered", "layout conventions", "project structure refactor", "archive prior version artifacts", "archive old release notes", "clean up scripts folder", "organize CI/CD configs".

### When NOT to Use

| Want to ... | Use this instead |
|---|---|
| Reorganize the `docs/` tree (audit, archive, classify docs files) | `docs-layout-refactor` |
| Check whether docs are factually accurate against the code | `update-documentation` |
| Generate release notes from changes | `generate-changelog` |
| Refresh `.gitignore` after layout changes | `/update-gitignore` |

## How to Invoke

### Claude Code

```
/refactor-project                                 # propose-only (default)
/refactor-project --apply                         # propose-then-confirm-then-apply
/refactor-project --archive-prior-versions        # also archive prior-major artifacts
/refactor-project --scope ci                      # restrict to .github/workflows/ etc.
/refactor-project-layout                          # legacy alias; routes to /refactor-project
```

### Codex / Gemini / Copilot

Reference this skill by name in the prompt: "Using the project-refactor skill, audit and reorganize this repository's project artifacts and archive prior-version files."

## Scope

This skill operates on:

1. **Root files** -- `README.md`, `CHANGELOG.md`, `SECURITY.md`, AI instruction files, installer entry points, lockfiles, ignore files, any unclassified file at the repo root.
2. **Scripts and automation** -- `scripts/`, build helpers, generators.
3. **Configs** -- `package.json`, `pyproject.toml`, `tsconfig.json`, `.eslintrc`, `ruff.toml`, `Makefile`, `Dockerfile`, lint/format/test runner configs.
4. **CI/CD** -- `.github/workflows/`, `Jenkinsfile`, `.gitlab-ci.yml`, `azure-pipelines.yml`, `circleci/`.
5. **Source layout** -- top-level shape of `src/`, `lib/`, `app/`, `extensions/`, monorepo package directories.
6. **Archivable artifacts** -- release notes, deploy checklists, generated reports, snapshot bundles, version-scoped CI workflows.

**Out of scope**: anything under `docs/` (owned by `docs-layout-refactor`).

## What This Skill Does

1. **Rule Loading** -- reads layout rules from `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` / project config; falls back to Nexus-Hub defaults.
2. **Active-version Detection** -- resolves the active version from `--active-version`, `CHANGELOG.md`, latest git tag, or the `docs/v*/` version tree. The active major is the cut-off for prior-version archival.
3. **Inventory and Classification** -- every in-scope file and directory is classified Stay / Move / Archive / Prune / Consolidate / Ambiguous against the loaded rules, the prior-version heuristics, and the cleanliness detectors: empty directories, redundant/duplicate files and dirs, non-version orphans (zero inbound references), and overcomplicated structure (deep nesting, single-child chains, over-fragmentation). See "Detecting Empty and Redundant Artifacts" and "Structure-Complexity Heuristics" below.
4. **Impact Analysis** -- finds every reference to each file that will move or be archived, across all file types, before touching anything. CI/CD references are flagged HIGH risk.
5. **Confirmation Gate** -- propose-only by default; follow the active instruction template's `Consequential Decisions` rule before requesting approval, and never move a file without explicit user approval at the gate.
6. **Safe Move Protocol** -- copy + verify + delete (never deletes without confirming the copy succeeded; verifies size + sha256 prefix for files > 1 KB).
7. **Reference Repair** -- updates all auto-fixable path references in `.md`, `.py`, `.sh`, `.ps1`, `.bat`, `.json`, `.yaml`, `.toml`, and source files.
8. **Verification** -- re-scans for stale references, runs a CI/CD sanity pass, and confirms structural compliance after the refactor.

## Standard Layout Rules Reference

These are the Nexus-Hub canonical defaults. Use these when no project-specific rules are declared, or as the baseline when customizing.

| Rule | What | Where | Rationale |
|------|------|-------|-----------|
| Community files | `README.md`, `CHANGELOG.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.gitignore`, `.gitattributes`, `llms.txt` | Project root | GitHub and tooling scan the root for these; moving them breaks discovery |
| AI instruction files | `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`, `.copilot-instructions.md` | Project root | AI assistants read these from root by convention |
| Build / lint / test configs | `package.json`, `pyproject.toml`, `tsconfig.json`, `Makefile`, `Dockerfile`, `docker-compose*.yml` | Project root | Tooling discovery; do not move |
| Installer entry points | `install.bat`, `install.sh`, `install.exe`, `*.msi`, `setup.exe` | Project root | Users expect to find and run installers at root |
| Development log | `DEVLOG.md` | `docs/DEVLOG.md` | Project-specific artifact, not a root convention; belongs with other project docs |
| Machine-readable catalogs | `skills.json`, `bundles.json`, `templates.json`, `workflows.json`, `report_data.json` | `data/` | Data files are not source or docs; `data/` makes their purpose clear |
| Scripts and automation | `installer.ps1`, `installer.sh`, `generate_report.py`, build scripts | `scripts/` | Separates runnable tools from project metadata |
| CI/CD pipelines | GitHub Actions, GitLab CI, Azure Pipelines, CircleCI | `.github/workflows/`, `.gitlab-ci.yml`, `azure-pipelines.yml`, `.circleci/` | Tooling discovery; never move |
| Source code | application code, libraries | `src/` (or top-level package dirs for monorepos) | Industry-standard separation of source from project files |
| Skills catalog source | skill directories (`SKILL.md` files) | `catalog/skills/` | Distinguishes human-readable catalog source from compiled JSON in `data/` |
| Prior-version artifacts | release notes, deploy checklists, generated reports, snapshot bundles, version-scoped CI workflows for `v<M>` (M < active major) | `archive/versions/v<MAJOR>/v<SEMVER>/<topic>/` | Preserve traceability without cluttering the active tree |

## Detecting Prior-Version Artifacts

A file is **prior-version** when any of these signals apply:

1. **Filename version**: contains a version string `v<M>.*` or `<M>.*` where `M < active_major` (e.g., `RELEASE_NOTES-v1.2.0.md`, `deploy-v0.9-checklist.md`, `report-1.0.0.docx`).
2. **Body banner**: file opens with a heading matching `# Release Notes - v<M>.<N>.<P>` or similar for a prior major.
3. **Path segment**: file path includes a numeric version segment matching a prior major, and the file is not under `docs/`.

**Never auto-classify as Archive**:

- Root community files (README, CHANGELOG, SECURITY, etc.) -- these stay at root regardless of age.
- Active-version CI/CD workflows.
- Files explicitly listed in a "Stay" rule.

Prior-version artifacts default to **Archive** when `--archive-prior-versions` is set, **Stay** otherwise.

## Detecting Empty and Redundant Artifacts

Beyond prior-version archival, the Inventory and Classification stage flags three cleanliness classes. All default to propose-only - nothing is pruned, consolidated, or removed without explicit confirmation at the gate.

### Empty directories

A directory with no files anywhere beneath it (recursively) is an **empty-directory** candidate for pruning:

- A directory containing only a `.gitkeep` (or `.keep`) placeholder is intentionally empty - **never prune it**; it is holding a path open on purpose.
- A directory that becomes empty only after this run's moves/archives is a prune candidate, but pruning it requires a second explicit confirmation (same rule as `docs-layout-refactor` empty-version dirs).
- Propose prune; never auto-delete.

### Redundant / duplicate files and dirs

Two files are **duplicates** when their full-content sha256 hashes match. Two files are **redundant** when their names and evident purpose overlap (e.g. `utils.py` next to `utilities.py`, `config.old.json` next to `config.json`, `installer copy.sh`):

- For byte-identical duplicates, propose keeping the canonical copy (the one with inbound references, or the one in the conventional location) and removing the other - flag, do not auto-remove.
- For name/purpose overlaps that are not byte-identical, flag for manual review with a one-line reason; never merge automatically (the difference may be intentional).
- A duplicate referenced by different callers is NOT safe to collapse - surface the callers.

### Non-version orphans (unreferenced files)

Invert the reference-detection machinery (see "Reference Detection Patterns"): a file with **zero inbound references** anywhere in the codebase is an **orphan** candidate:

- Maintain an allowlist of intentional standalone files that are load-bearing without inbound refs: `LICENSE`, `README.md`, `CHANGELOG.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.gitignore`, `.gitattributes`, `llms.txt`, entry-point installers, and any file matching a declared "Stay" rule. Never flag these as orphans.
- A true orphan defaults to **Ambiguous** (flag for manual review), NOT auto-archive - an unreferenced file may still be a deliberate template, fixture, or asset loaded dynamically.
- Report each orphan with the reference scan that returned zero hits, so the user can confirm.

## Structure-Complexity Heuristics

Overcomplicated structure adds navigation cost without organizational benefit. Detect and propose consolidation/flattening (propose-only):

- **Single-child directory chains**: a directory whose only child is another directory (e.g. `a/b/c/d/only.md`) - propose collapsing the chain to the shallowest level that still separates concerns (`a/only.md` or `a/d/only.md`).
- **Deep nesting**: a path nested deeper than the project's typical depth (default heuristic: more than 4 directory levels below the repo root, outside `docs/` and vendored trees) - propose flattening or justify the depth.
- **Over-fragmentation**: many sibling directories each holding a single file where a grouping directory would read better - propose consolidation.
- **Under-fragmentation** is out of scope here (splitting a large dir is a design decision, not a cleanliness fix).

Each proposal names the current path, the proposed path, and the reference-repair impact. Consolidation moves follow the same Safe Move Protocol and reference-repair steps as any other move.

## Archive Layout

Canonical archive path for prior-version artifacts (mirrors the docs-layout-refactor archive convention):

```
archive/
  README.md                           # index of archived artifacts
  versions/
    v<MAJOR>/                         # e.g., v0, v1
      v<MAJOR>.<MINOR>.<PATCH>/       # e.g., v0.9.0
        ci/                           # archived workflow files
        release-notes/
        reports/
        misc/
```

Collisions are resolved by suffixing with `-<source-version>` (never silently overwrite). Reference repair (after move) rewrites paths in `.md`, `.py`, `.sh`, `.ps1`, `.json`, `.yaml`, `.toml`.

## Reference Detection Patterns

Use these grep patterns to find all references to a file that is about to move or be archived. Run against the full codebase (not just the root).

### Markdown

```bash
grep -rn "DEVLOG\.md" --include="*.md" .
```

### Python

```bash
grep -rn "DEVLOG\.md" --include="*.py" .
```

### Shell scripts

```bash
grep -rn "DEVLOG\.md" --include="*.sh" --include="*.bash" .
```

### PowerShell

```bash
grep -rn "DEVLOG\.md" --include="*.ps1" --include="*.psm1" .
```

### JSON / YAML / TOML

```bash
grep -rn "DEVLOG\.md" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.toml" .
```

### CI/CD

```bash
grep -rn "DEVLOG\.md" --include="*.yml" .github/workflows/ Jenkinsfile azure-pipelines.yml .gitlab-ci.yml .circleci/ 2>/dev/null
```

CI/CD hits are always **HIGH priority** for manual review -- automated pipeline failures are hard to diagnose remotely.

**Tip**: Use `\.` to escape the dot in regex patterns so it matches a literal period.

## Safe Move Protocol

Never move a file without following these steps in order. Skipping any step risks data loss.

```
1. Determine destination path
   └─ Create destination directory if it does not exist

2. Copy source → destination
   └─ Verify: file exists at destination AND byte size matches source
   └─ For files > 1 KB: also verify sha256 prefix matches

3. If verification passes:
   └─ Delete source
   └─ Log: ✓ Moved: source → destination
       (or ✓ Archived: source → destination for archive operations)

4. If verification fails:
   └─ Do NOT delete source
   └─ Log error and stop this file's move
   └─ Continue with next file (do not abort entire refactor)
```

### .gitignore pre-flight

Before the first move, inspect every destination with `git check-ignore -v <new-path>`. A bare directory pattern such as `test-results/` or `data/` matches that directory name at any depth. Existing files beneath the source stay tracked because git ignores only untracked files, but a rename makes the destination untracked: `git add -A` can then skip the new path while staging the old path as a deletion, producing a clean-looking change that silently drops content.

After staging, pair every deletion with its expected addition or rename. For any staged deletion without a paired addition, run `git check-ignore -v` against the intended new path and stop if it matches. Fix the ignore rule by re-including the directory before its contents; git cannot re-include a file while its parent directory remains excluded.

**Never use a rename/move operation as an atomic action** when operating across directories -- on networked drives or certain filesystems, a move can fail silently. Copy + verify + delete is always safe.

## Reference Fix Patterns

### Markdown Links

```markdown
# Before
[Development Log](DEVLOG.md)
[Notes](./RELEASE_NOTES-v1.2.0.md)

# After
[Development Log](docs/DEVLOG.md)
[Notes](./archive/versions/v1/v1.2.0/release-notes/RELEASE_NOTES.md)
```

### Python String Literals

```python
# Before
path = "DEVLOG.md"
devlog = root / "DEVLOG.md"

# After
path = "docs/DEVLOG.md"
devlog = root / "docs" / "DEVLOG.md"
```

### Shell Variable Assignments

```bash
# Before
DEVLOG="$GIT_ROOT/DEVLOG.md"

# After
DEVLOG="$GIT_ROOT/docs/DEVLOG.md"
```

### JSON Path Strings

```json
{ "devlog": "DEVLOG.md" }
→
{ "devlog": "docs/DEVLOG.md" }
```

### PowerShell

```powershell
# Before
$devlog = Join-Path $root "DEVLOG.md"

# After
$devlog = Join-Path $root "docs\DEVLOG.md"
```

### CI/CD (GitHub Actions example)

```yaml
# Before
- run: cat DEVLOG.md

# After
- run: cat docs/DEVLOG.md
```

CI/CD substitutions ALWAYS require Manual review before applying.

## Platform-Specific Tool Usage

### Claude Code

- Use `Glob` to list root files (do not use Bash `ls`)
- Use `Grep` for reference scanning (do not use Bash `grep`)
- Use `Read` before any `Edit`; use `Edit` for targeted fixes (not `Write`)
- Use `Bash` only for the copy + verify + delete sequence and `git status`

### Codex (OpenAI CLI)

- Use the `computer` tool for file reads and writes
- Run grep via shell for reference scanning
- Prefer shell `cp` + `test -s` for copy+verify, then `rm` for delete

### Gemini CLI

- Use `read_file` / `write_file` for file operations
- Use `run_shell_command` for grep-based reference scanning
- Apply targeted edits with `replace_in_file` rather than full rewrites

### GitHub Copilot (Chat / Workspace)

- Use `#file:` to reference specific files for reading
- Use `@workspace /search` for codebase-wide reference scanning
- Copilot cannot move files directly: generate a shell script (`move-files.sh` or `move-files.ps1`) for the user to run, then repair references in the files you can edit

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just move the file and fix references as they break" | CI/CD breakages are hard to diagnose remotely. The propose-then-apply gate catches references the agent missed in the first pass. |
| "DEVLOG.md is huge, let me archive it" | `DEVLOG.md` is a root community-adjacent file; this skill never archives it. Use `docs-layout-refactor` Edge Case 1 (split by version) instead. |
| "These prior-version release notes still get traffic, leave them" | Archive is reversible. Archived files keep their full content readable under `archive/versions/v<M>/`. Surfacing them in the active tree just adds noise. |
| "I'll skip CI/CD reference repair, it's just YAML" | Workflow paths fail silently on the next CI run, which is the worst time to discover them. CI/CD refs are HIGH risk on purpose. |
| "Let me just bulk-archive everything that mentions v0" | Filename match is necessary but not sufficient. Verify the body banner or path segment too -- otherwise you archive files that reference the prior version without being scoped to it. |
| "The destination files will stay tracked because their sources are tracked" | A move makes each destination untracked before staging, so a bare directory ignore can omit the additions while staging only deletions. This fired three times in one release and would have deleted three validation records; run the `.gitignore` pre-flight and pair every deletion with an addition. |

## Verification

Run after Phase 7. Each check is binary; FAIL on any item loops back up to 3 times.

- [ ] **All files moved/archived exist at their new path** and no longer exist at their old path.
- [ ] **Stale reference scan returns zero hits** against the old paths.
- [ ] **`archive/README.md` exists and lists every archived path** (when any archive operation ran).
- [ ] **CI/CD references re-read and confirmed substituted** -- every workflow/pipeline file touched is read post-edit.
- [ ] **`git status --porcelain` count matches the planned mutations** -- surprise mutations halt with a diff dump for user review.
- [ ] **Active-version artifacts untouched** -- diff against pre-refactor state for the active version is empty (no incidental edits).
- [ ] **Manual-review items documented** and handed off to the user.
- [ ] **No move destination is ignored** -- `git check-ignore -v` is clean for every intended new path, and every staged deletion has a paired addition or an explicit approved deletion disposition.
- [ ] **Empty directories detected and proposed for prune** (respecting `.gitkeep` / `.keep`); none auto-deleted without the second confirmation.
- [ ] **Duplicate and redundant files flagged** (byte-identical duplicates plus name/purpose overlaps), callers surfaced; none auto-merged or auto-removed.
- [ ] **Orphans (zero inbound references) flagged as Ambiguous**, allowlist honored (LICENSE / README / CHANGELOG / entry points never flagged); none auto-archived.
- [ ] **Structure-complexity proposals emitted** for single-child chains, deep nesting, and over-fragmentation, each naming current path, proposed path, and reference-repair impact.

## Related Skills

- [[docs-layout-refactor]] -- sister skill for the `docs/` tree. Run in any order; they touch disjoint scopes.
- [[documentation-consistency]] -- audit documentation accuracy after a layout change.
- [[version-upgrade]] -- update version references and CHANGELOG as part of a release that includes layout changes.
- [[code-commit-workflow]] -- commit the refactor with a clear, structured commit message.

---

**Version**: 2.1.0
**Last Updated**: July 2026

### Iterative Refinement Strategy

This skill is optimized for an iterative approach:
1. **Execute**: Classify files, run impact analysis, execute approved moves/archives and reference fixes.
2. **Review**: Re-scan for stale references; check structural compliance; re-read CI/CD files post-edit.
3. **Refine**: If stale references remain or a CI/CD substitution failed, apply targeted fixes and re-scan.
4. **Loop**: Continue until the stale-reference scan is clean (up to 3 iterations).
