---
name: devlog-generation
description: Maintain docs/DEVLOG.md as a bounded per-release INDEX - one line per release with a date, version, one-sentence summary, and links to that release's plan, development/history/ directory, and known-gaps file. Use this skill whenever the user says "update the devlog", "sync the devlog", "add a release to the devlog", "regenerate the devlog", "regenerate the development log", "the devlog is out of date", "the devlog index is missing a version", or when /update runs at devlog or release scope. It never writes narrative prose into DEVLOG; the rich per-phase story goes to the per-version development/history/ file instead. SKIP - a single working session's story (use session-history); the authoritative record of what changed in a release (use release-notes-writer); the reasoning behind a design choice (use architecture-decision-record); unfinished or carried-over items (use known-gaps-tracker). Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/.
summary_l0: "Maintain a release index without writing evidence into living subtrees"
overview_l1: "This skill owns docs/DEVLOG.md, which is an INDEX and not a log: a short header plus one line per release, newest first, carrying the release date, version, a one-sentence summary, and repo-relative links to that release's plan file, development/history/ directory, and known-gaps file. Use it when the user asks to update, sync, generate, or regenerate the devlog, and when /update runs at devlog or release scope. Its discovery logic is unchanged (git tags, CHANGELOG headings, the per-version docs tree) but its destination differs: the index gets one line, and any narrative found is routed to the per-version development/history/ file via session-history. It updates an existing version line in place rather than duplicating it, omits links whose targets do not exist, and never restates CHANGELOG. Trigger phrases: devlog, development log, DEVLOG, update the devlog, sync the devlog, devlog index, add a release to the devlog. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
---

# DevLog Generation

`docs/DEVLOG.md` is a **navigation index**, not a log. It answers one question at a glance: what has this project released, and where is each release's detail? It never answers "what changed" (that is `CHANGELOG.md`) or "how did this phase go" (that is the per-version `development/history/` file).

The index never writes release evidence into a living subtree. Keep `docs/handbooks/` at the docs root, regenerate its generated output from source, and snapshot it at release close to `docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/handbooks/`, named for the version the copied content describes. Narrative remains in the release-bound `development/history/` tree owned by `[[session-history]]`.

This skill maintains that index. Its discovery work is the same work a narrative devlog generator does; only the destination differs.

## When to Use This Skill

Use this skill when:

- A release has just been cut and the index needs its line (the common case, driven by `/update release`).
- The user asks to update, sync, or regenerate the devlog.
- `docs/DEVLOG.md` does not exist yet in a project and needs to be created in the index format.
- An existing narrative DEVLOG needs converting to the index format (archive the body first; see the conversion procedure below).
- An index line is stale, wrong, or missing links whose targets now exist.

**Do NOT use this skill for:**

- **A session's narrative** (what was tried, what failed, what was decided). That is `[[session-history]]`, written to `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/development/history/`.
- **The record of what changed in a release.** That is `CHANGELOG.md`, and it is authoritative. The index summary is a pointer, never a substitute, and must not restate the changelog.
- **Design reasoning and rejected alternatives.** That is `[[architecture-decision-record]]`.
- **Open, deferred, or broken work.** That is `[[known-gaps-tracker]]`.

**Trigger phrases**: "update the devlog", "sync the devlog", "add a release to the devlog", "regenerate the devlog", "the devlog is out of date". Note that "add a devlog entry" describes the format this skill replaced; an index gains a line, not an entry.

## The Output Contract

The whole file is a header plus one table. Nothing else belongs in it.

### Header

Five lines, stated once, never per release:

```markdown
# Development Log

This is an **index**, not a log. One line per release, newest first, linking to that release's plan, per-phase history, and known gaps. It is a navigation surface only: [`CHANGELOG.md`](../CHANGELOG.md) remains the authoritative record of what changed in each release.

| Date | Version | Summary | Plan | History | Gaps |
|---|---|---|---|---|---|
```

When a prior narrative body was archived, the header also links the archive and the decision record that authorized the conversion.

### One line per release

```markdown
| 2026-08-20 | v3.17.6 | CI gate hygiene: required checks made satisfiable from any PR shape | [ci-gate-and-branch-hygiene](v3/v3.17/plans/v3.17.6-ci-gate-and-branch-hygiene.md) | [history](v3/v3.17/development/history/) | [gaps](v3/v3.17/known-gaps.md) |
```

| Column | Source | Rule |
|---|---|---|
| Date | The release's `CHANGELOG.md` heading, or the tag date | `YYYY-MM-DD`, no time component |
| Version | The release | `vX.Y.Z`, matching the tag |
| Summary | Authored, from the plan slug plus the CHANGELOG lead | **One sentence.** No trailing period needed. Never a restatement of the changelog entry |
| Plan | `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/plans/v<X.Y.Z>-<slug>.md` | Link the file, labelled by its slug |
| History | `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/development/history/` | Link the directory, labelled `history` |
| Gaps | `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md` | Link the file, labelled `gaps` |

Links are **relative to `docs/DEVLOG.md`**, so they resolve both on the forge and in an editor. A root-relative `/docs/...` link does not resolve on GitHub and must not be used.

**Newest first.** A new release's line goes directly under the table header.

## Instructions

### Step 1: Determine the target release

Read the version being indexed from the release context: the `CHANGELOG.md` heading being finalized, the tag about to be cut, or the version the user named. If no release is in flight, there is nothing to add. Say so and stop rather than inventing a line for unreleased work.

An index line is added for a **release**, not for a phase, a commit, or a session. Mid-release work produces a `development/history/` file and nothing in the index.

### Step 2: Resolve the links before writing them

For version `X.Y.Z`, probe the filesystem:

```bash
ls docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/plans/v<X.Y.Z>-*.md      # plan file(s)
ls -d docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/development/history/   # history dir
ls docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md             # gaps file
```

Emit a link only when its target exists. Three fallbacks, in order:

1. **Multiple version-prefixed plan files**: link all of them, space-separated, each labelled by its slug. A release can ship more than one plan.
2. **No version-prefixed plan file**, because the project's plan filenames predate a version-prefixed convention: link the minor version's `plans/` directory instead. Do **not** guess which slug-named plan belongs to this patch release; a resolving link to the wrong plan is worse than a link to the directory.
3. **Target genuinely absent**: put a literal `-` in the cell. Never emit a link to a path that does not exist, and never leave the cell empty.

### Step 3: Write the summary

One sentence, authored. Derive it from the plan slug and the release's own framing, not by copying the CHANGELOG lead verbatim.

Mechanical extraction does not work and should not be attempted: a changelog's first bolded item is frequently a section label rather than a summary. Read enough of the release to say what it did in one clause.

If the release is a patch with a single narrow fix, say the fix. If it is a multi-phase feature release, say the theme, not the phase list.

### Step 4: Insert or update, never append blindly

Check whether a line for this version already exists:

```bash
grep -n "| v<X.Y.Z> |" docs/DEVLOG.md
```

- **Exists**: update that line in place. Re-running this skill on the same release must be idempotent; a second line for the same version is a defect.
- **Does not exist**: insert directly below the table header row (`|---|---|...`), because the table is newest-first.

### Step 5: Route the narrative elsewhere

Any rich material the discovery surfaced (decision trails, failed attempts, troubleshooting, impact analysis) does **not** go in the index. Hand it to `[[session-history]]`, which writes `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/development/history/<date>_<slug>.md`.

If that file already exists for the phase in question, the narrative belongs appended there, not duplicated into a new file.

### Step 6: Verify the file is still bounded

The index grows by exactly one line per release. If it grew by more, or if any cell now contains prose spanning multiple sentences, the format has regressed and must be corrected before finishing.

## Creating the index in a project that has no DEVLOG

Write the header from the template in **The Output Contract** above, then one line per existing release discovered from `git tag --sort=-v:refname` and the `CHANGELOG.md` headings. Resolve every link per Step 2, so a project with no per-version docs tree simply gets `-` in those three columns.

This is a valid and common end state: the index is useful with the date, version, and summary columns alone.

## Converting an existing narrative DEVLOG to the index

The conversion is destructive to the file, so it is never done implicitly:

1. **Archive first.** Move the entire current body to `docs/archives/DEVLOG-<range>.md` under a short provenance header naming the archive date and the authorizing decision record.
2. **Prove content preservation.** Hash the original and the archived body and compare. Do not report the archive as verified on the strength of a successful copy; a copy can silently rewrite line endings.
3. **Record the decision.** The conversion changes a documentation policy, so it needs a decision record with its rejected alternatives (see `[[architecture-decision-record]]`).
4. **Rewrite** `docs/DEVLOG.md` per the contract, deriving lines from the archived body's entry headings and the release set.
5. **Bound the pre-canonical era.** Releases that predate the project's per-version docs layout have no plan, history, or gaps file to link. Collapse them into one line per **minor** version pointing at the archive, rather than one line per release. This is what keeps a line-count ceiling holding as the project ages instead of merely satisfied on the day it is set.
6. **Fix the references.** Grep the repo for anything describing DEVLOG as a narrative log and correct it. Leave historical records alone: past session histories, plans, and changelog entries recorded what was true when written and must not be retconned.

## Failure Modes

| Situation | Correct behavior |
|---|---|
| The release has no plan file yet | Emit the line with `-` in the Plan column, and note the omission to the user. Never a broken link. |
| The release has no `development/history/` directory | Same: `-` in that column. A patch release with no phases legitimately has none. |
| `docs/DEVLOG.md` does not exist | Create it from the header template, then add the line. Do not fail. |
| A line for this version already exists | Update it in place. Never append a duplicate. |
| The project has no `docs/v*` tree at all | Emit date, version, and summary; put `-` in all three link columns. |
| An existing DEVLOG is narrative, not an index | Stop and run the conversion procedure above, with the user's confirmation. Never silently overwrite a narrative body. |
| The user asks to record a phase, not a release | Route to `[[session-history]]` and add nothing to the index. |

## Verification

- [ ] `docs/DEVLOG.md` contains exactly one line per release, and no line for an unreleased version
- [ ] The target version appears exactly once: `grep -c "| v<X.Y.Z> |" docs/DEVLOG.md` returns `1`
- [ ] Every link in the file resolves to an existing path (resolve each relative to `docs/`)
- [ ] No cell in the table contains more than one sentence
- [ ] The table is in descending version order, newest first
- [ ] No narrative section, per-release heading, or `<details>` block exists anywhere in the file
- [ ] The narrative that would have gone into a devlog entry exists in `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/development/history/`
- [ ] No devlog or release-evidence write targeted a living subtree; handbook snapshots, when present, use the described version under `docs/archives/`
- [ ] The file grew by exactly the number of releases added
- [ ] Markdown conventions hold per `catalog/style-guides/markdown.md` (blank line before and after the table, one H1, ASCII-only in English docs)

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This release deserves more than one line, it was a big one" | The one-line rule is what keeps the file loadable; the exception is how a 99-line index becomes a 5,615-line file nobody can read. A big release earns a richer `development/history/` file, not a longer index cell. |
| "I will append the new line at the bottom, it is faster" | The table is newest-first, so a bottom append puts the newest release below releases from years earlier and silently breaks the ordering readers depend on to find recent work. |
| "The plan file does not exist yet, I will link where it will be" | A link to a path that does not exist reads as a resolving link until someone clicks it, and link checkers flag it as breakage in a file that is supposed to be pure navigation. Use `-` and say so. |
| "I will copy the CHANGELOG lead as the summary, it is already written" | Changelog leads are frequently section labels rather than summaries, so this yields cells reading "Activation:" or "None." The summary must be authored from the release's actual theme. |
| "The version line already exists but re-adding is harmless" | Two lines for one version means a reader cannot tell which is current, and the duplicate survives every future edit because nothing looks obviously wrong. Update in place. |
| "The narrative context is valuable, I will keep it in DEVLOG as well as the history file" | Duplicated narrative diverges the moment one copy is edited, and the index is exactly where nobody will look for it. One home per fact. |
| "This project has no docs/v* tree, so the skill does not apply" | The index is still useful with date, version, and summary; the link columns take `-`. Refusing to write anything leaves the project with no chronology at all. |

## Related Skills

- [[session-history]] -- owns the per-phase narrative this skill deliberately does not write; the index links its directory
- [[known-gaps-tracker]] -- owns the per-version open-work file the index links
- [[release-notes-writer]] -- owns `CHANGELOG.md`, the authoritative change record the index must never restate
- [[architecture-decision-record]] -- where design reasoning and rejected alternatives go, including the decision to convert a DEVLOG
- [[docs-layout-refactor]] -- owns the per-version docs tree and archive conventions the index's links depend on
- [[code-commit-workflow]] -- commit conventions that feed the release discovery this skill reads

---

**Version**: 2.0.0
**Last Updated**: August 2026
