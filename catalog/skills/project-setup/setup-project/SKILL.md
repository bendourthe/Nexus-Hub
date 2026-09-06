---
name: setup-project
description: Bootstrap or repair a project's governance surfaces - git version control, a vX.Y.Z version, a develop+main branch model, the per-version docs tree, and real README / CHANGELOG / DEVLOG - detecting what already exists and creating ONLY what is missing (idempotent, safe on an inherited repo). This is the generic cross-language delegate behind /setup project. Use whenever the user says "set up this project", "bootstrap the repo", "initialize the project", "scaffold this directory", "get this repo release-ready", "add version control", "create the develop branch", "set up the docs structure", or when /describe or /review reports that setup is needed. SKIP - language-specific scaffolding with a package manifest and test runner (use the matching init-<language>-project skill), updating docs on an already-governed project (use /update docs), or describing a project without changing it (use /describe). Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/.
summary_l0: "Bootstrap git, versioning, branches, release docs, and core project documentation"
overview_l1: "The generic, language-agnostic delegate behind /setup project. It brings any new or inherited directory up to Nexus-Hub's governance baseline by detecting each surface first and creating only what is missing, so it is safe to re-run: (a) git version control - init and make an initial commit if the directory is not a repo; (b) a vX.Y.Z version - detect from tags/CHANGELOG/manifest, else set v0.1.0 and record it on the canonical version surface; (c) a develop+main branch model - create a develop integration branch when only a default branch exists, delegating the discipline to git-branching-workflow; (d) the per-version docs tree docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/ with plans/ and comparisons/ per the docs-layout-refactor scheme; (e) real README, CHANGELOG, and DEVLOG with actual content, not placeholders. Trigger phrases: set up this project, bootstrap the repo, initialize the project, scaffold this directory, create the develop branch, set up the docs structure. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
---

# Setup Project

Bring a new or inherited directory up to Nexus-Hub's governance baseline: version control, a version number, a branch model, a per-version docs tree, and the three baseline docs (README, CHANGELOG, DEVLOG). This is the generic, cross-language delegate behind `/setup project`. Every step is **detection-first**: check what already exists, then create only what is missing. Running it twice must never duplicate or clobber anything.

## When to Use This Skill

Use this skill when you need to:

- Bootstrap a brand-new project directory to a shippable governance baseline.
- Bring an inherited repo that is missing version control, a version, a branch model, or a docs structure up to that baseline without disturbing what is already there.
- Remediate the gaps that `/describe` or `/review` surfaces in their "Project health" block (they detect and recommend; this skill acts).

**Trigger phrases**: "set up this project", "bootstrap the repo", "initialize the project", "scaffold this directory", "get this repo release-ready", "add version control", "create the develop branch", "set up the docs structure".

### When NOT to Use

| Want to ... | Use this instead |
|---|---|
| Scaffold a language-specific project (manifest, test runner, lint config) | the matching `init-<language>-project` skill (e.g. `init-python-project`) |
| Update or sync docs on an already-governed project | `/update docs` |
| Describe a project without changing it | `/describe` (read-only) |
| Install the pre-commit AI review hook | `/setup hooks` |

This skill is the generic complement to the `init-<language>-project` family: use an `init-*` skill when the project has a known language and needs a full language-specific scaffold; use `setup-project` for the language-agnostic governance surfaces, on any directory including non-code ones.

## Instructions

Run the five checks in order. Each is stated as **detect, then act only if missing**. Confirm any repo-shaping action (git init, branch creation) with the user before performing it; never mutate silently.

### Step 1: Git version control

1. **Detect**: is the directory inside a git work tree (`git rev-parse --is-inside-work-tree` succeeds, or a `.git/` directory exists at the root)?
2. **Act if missing**: `git init`, add a baseline `.gitignore` if none exists, stage the initial content, and make an initial commit (`chore: initial commit`). If the directory is already a repo, take no git-init action.

### Step 2: Version number

1. **Detect** an existing version, in this order (stop at the first hit): the latest semver git tag (`git tag --sort=-v:refname`); the most recent `## [X.Y.Z]` heading in `CHANGELOG.md`; a version field in a package manifest (`package.json`, `pyproject.toml`, `Cargo.toml`, `*.csproj`, etc.).
2. **Act if missing**: set `v0.1.0` using the `vX.Y.Z` scheme and record it on the project's canonical version surface (the manifest if one exists, otherwise the `CHANGELOG.md` heading). State which surface you wrote to. Do not invent a manifest for a language the project does not use.

### Step 3: Branch model

1. **Detect** the branches: does a `develop` (or `dev`) branch exist alongside `main`/`master`? Is a model already declared in `AGENTS.md` / `CLAUDE.md`?
2. **Act if missing**: when only a default branch (or none) exists and the project has not DECLARED trunk-based, bootstrap the develop+main model - create a `develop` integration branch from the default branch and document the `feat/` `fix/` `refactor/` `ci/` `docs/` `chore/` `test/` -> `develop` -> `main` flow. Delegate the discipline (protected vs integration branch, merge style, release cut) to `[[git-branching-workflow]]` (its Step 3 "Bootstrap the integration branch when missing" is exactly this path). Confirm before creating the branch.

### Step 4: Per-version docs tree

1. **Detect** whether a per-version docs directory exists for the resolved version under the canonical scheme.
2. **Act if missing**: create `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/` (for the version resolved in Step 2) with `plans/` and `comparisons/` subdirectories, per the `[[docs-layout-refactor]]` Version-directory resolution algorithm. For `v0.1.0` that is `docs/v0/v0.1/{plans,comparisons}/`. Honor an existing legacy layout in place rather than migrating it (migration is `/update refactor`).

3. **Detect** the required living tree: `docs/handbooks/{README.md,markdown/,html/}` and `docs/decisions/`. Also detect living `docs/README.md` and `docs/todos.md` (`docs/DEVLOG.md` is Step 5).
4. **Act if missing**: scaffold only the missing pieces. Create `docs/handbooks/README.md`, empty `markdown/` and `html/` dirs (with `.gitkeep` if the VCS would drop empty dirs), and `docs/decisions/` (the ADR tree; do not invent records). Create `docs/README.md` and `docs/todos.md` with real content if absent. Never overwrite inherited files. Never invent `docs/testing/` or `docs/validation/`.

### Step 5: README, CHANGELOG, DEVLOG

1. **Detect** each of `README.md`, `CHANGELOG.md`, and `DEVLOG.md` (the latter conventionally at `docs/DEVLOG.md`).
2. **Act if missing**: create each with **real content**, not just a heading: `README.md` (project name, one-line purpose, install/run, layout); `CHANGELOG.md` (Keep-a-Changelog header with an `## [Unreleased]` section and the resolved version heading); `DEVLOG.md` (the **index-format header plus an empty table**, not a narrative entry - see `[[devlog-generation]]`; the index carries one line per release, so a project with no release yet legitimately has a header and no rows). Do not overwrite an existing file - if it exists but is a bare placeholder, offer to enrich it rather than replacing it. If an existing `DEVLOG.md` is a narrative log rather than an index, leave it alone here and offer the conversion procedure in `[[devlog-generation]]`, which archives the body first.

### Step 6: Report what was done

Summarize per surface: **detected (unchanged)** vs **created**, with the exact path or branch. This makes the idempotent behavior visible and lets the user confirm nothing was clobbered.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The repo already has some of this, so I will just re-scaffold everything cleanly." | Re-scaffolding an inherited repo overwrites the maintainer's README, resets their CHANGELOG, or creates a second version surface. Every step is detection-first for exactly this reason: act only on what is missing, and report detected-vs-created. |
| "I will create the develop branch without asking - it is the recommended model." | Branch creation is a repo-shaping action. A project may have deliberately chosen trunk-based; auto-creating `develop` there is wrong. Confirm first, and skip when trunk-based is declared (see `[[git-branching-workflow]]` Step 3). |
| "A README with just a title is good enough to tick the box." | The check is for a *usable* baseline. An empty README/CHANGELOG/DEVLOG passes a shallow existence test but fails the real goal - a contributor who can orient and a release record that starts at v0.1.0. Write real content. |
| "There is no manifest, so I will add a package.json to store the version." | Do not impose a language ecosystem the project does not use. Record the version on a surface the project already has (CHANGELOG heading) rather than inventing a manifest. |
| "I will put docs in a flat docs/ folder; the versioned tree is overkill for v0.1.0." | The per-version tree is the contract every later plan, comparison, and known-gaps file writes into. Establishing `docs/v0/v0.1/` now means the first `/plan` and `/compare` land in the right place with no migration later. |

## Verification

- [ ] `git rev-parse --is-inside-work-tree` succeeds and there is at least one commit (`git rev-list --count HEAD` >= 1).
- [ ] A version is resolvable from a tag, `CHANGELOG.md`, or a manifest, and equals `v0.1.0` for a freshly-bootstrapped project.
- [ ] Unless the project declared trunk-based, a `develop` branch exists (`git branch --list develop` is non-empty) alongside the default branch.
- [ ] `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/plans/` and `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/comparisons/` exist for the resolved version.
- [ ] `docs/handbooks/{README.md,markdown/,html/}` and `docs/decisions/` exist; `docs/testing/` and `docs/validation/` were not invented.
- [ ] `README.md`, `CHANGELOG.md`, and `DEVLOG.md` exist and contain real content (more than a bare heading).
- [ ] The final report lists each surface as detected-or-created; re-running the skill reports every surface as detected with no new writes.

## Related Skills

- [[git-branching-workflow]] -- owns the branch discipline this skill bootstraps (protected vs integration branch, naming, merge, release); Step 3 there is the develop-when-missing path.
- [[docs-layout-refactor]] -- defines the Version-directory resolution scheme this skill creates the docs tree from, and migrates a legacy layout when one is found.
- [[known-gaps-tracker]] -- the per-minor `known-gaps.md` that later phases append to, living under the docs tree this skill scaffolds.
- `init-python-project` (and the other `init-<language>-project` skills) -- the language-specific complement; run one of those for a full manifest/test/lint scaffold, and this skill for the language-agnostic governance surfaces.
- `/update docs` -- keeps the baseline docs accurate against the code once the project has grown past bootstrap.

---

**Version**: 1.0.0
**Last Updated**: July 2026
