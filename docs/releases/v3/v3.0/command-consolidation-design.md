# Command Consolidation Design -- v3.0.0

**Version**: v3.0.0 (planning; current released version is v2.4.0)
**Generated**: 2026-06-02
**Status**: design proposal (drives the v3.0.0 plan)
**Scope decisions (confirmed with maintainer)**: interactive-scope + optional positional arg; `/implement-phase` -> `/implement`; aggressive consolidation (41 -> 14); CI hotfix shipped separately.

## 1. Goals and Principles

The command surface has grown to **41 slash commands**. Past the ~10-command threshold the autocomplete menu becomes hard to scan, names collide conceptually (`review-changes` vs `review-codebase` vs `run-deep-review`), and there are six near-synonymous `update-*` / `refactor-*` commands and three `generate-*tests*` commands. This design collapses the surface to **14 verb-first commands**, each able to run a full or a focused scope, without losing a single existing behavior.

Principles:

1. **Verb-first, single-word names.** `describe`, `plan`, `implement`, `test`, `review`, `update`. Memorable, lifecycle-ordered, no `generate-`/`run-`/`update-` prefixes.
2. **Fewer commands, scoped behavior.** Each command runs comprehensively by default or focuses via an optional scope. This is the user-confirmed mechanism: **bare invocation prompts for scope; an optional positional argument skips the prompt** (e.g. `/review` asks, `/review security` runs that scope directly). Mirrors Codex's `/plan <inline prompt>` model.
3. **Thin command, fat skill.** The 41 existing rich skill bodies are NOT rewritten or deleted -- they are retained and become **scope modules**. Each new command file is a thin dispatcher that resolves scope, then delegates to the existing skill(s). This preserves every proven behavior, keeps the diff reviewable, and aligns with the 2026 Claude Code / Cursor unification of commands and skills.
4. **Backward compatibility via deprecation shims.** All 41 old command names ship for the entire v3.x line as thin alias files that print a one-line deprecation notice and forward to the new command + scope. They are removed at v4.0.0. This softens the breaking change for users with muscle memory, scripts, or docs referencing old names.
5. **Best-practice alignment.** Matches Claude Code (commands == skills, `$ARGUMENTS`, namespacing past 10 commands), Cursor (`.cursor/commands/*.md` + skills in one menu), and Codex (custom prompts deprecated in favor of skills; `/plan` plan-mode with inline arg).
6. **No registry churn for commands.** Per `AGENTS.md`, commands need no `data/*.json` registration; only `marketplace.json` `total_commands` and the `AGENTS.md` count prose update.

## 2. The 14 Commands

### Core lifecycle (6) -- the loop: describe -> plan -> implement -> test -> review -> update

| # | Command | One-line | Default (bare) behavior | Scopes (optional arg) | Delegates to (existing skills) |
|---|---------|----------|-------------------------|-----------------------|-------------------------------|
| 1 | **`/describe`** | Understand a project (any directory, software or not) | Full structured description of the selected dir | `full`, `structure`, `deps`, `architecture`, `onboarding` | `analyze-codebase` (generalized to any dir) |
| 2 | **`/plan`** | Define goals and produce a robust phased plan | Goals-first discovery -> optional multi-angle workflow drafting + parallel research -> phased plan; ingests known-gaps + strategy + constitution (see 2A) | `goals` (define/refine goal + DoD only), `new`, `feature`, `refactor`, `from-comparison`, `todos`, `issues` | `generate-plan`, `implementation-plan`, `product-strategy`, `generate-todos`, `tasks-to-issues`, `agent-orchestration-primitives` |
| 3 | **`/implement`** | Implement one plan phase end-to-end | Discover plan -> implement next/selected phase -> lint/test/troubleshoot -> per-phase docs+commit; final phase auto-runs release readiness (hands to `/update release`) | `<slug>`, `<slug> phase-N`, `next` | `implement-phase` |
| 4 | **`/test`** | Drive coverage to a standardized threshold across test tiers | Analyze coverage -> generate+run unit tests iteratively to threshold + pass-rate -> integration -> e2e -> CI/CD, each tier the same way | `unit`, `integration`, `e2e`, `ci`, `tdd`, `all` | `generate-tests`, `generate-unit-tests`, `tdd` |
| 5 | **`/review`** | Comprehensive, scope-able project review | Ask scope, then run it; `full` orchestrates all lenses | `full`, `structure`, `quality`, `coverage`, `security`, `pentest`, `changes`, `skill-scan`, `sbom`, `deps` | `review-codebase`, `review-changes`, `run-deep-review`, `run-security-audit`, `run-penetration-test`, `generate-sbom`, NEW `skill-security-scan` |
| 6 | **`/update`** | Sync the repo to current state and (at release scope) ship it | Ask scope; `release` = update docs+devlog+gitignore+version+changelog+refactor, clean up, commit, tag, push | `docs`, `devlog`, `gitignore`, `version`, `changelog`, `refactor`, `config`, `commit`, `release` (all + commit/tag/push) | `update-documentation`, `update-devlog`, `update-gitignore`, `update-version`, `generate-changelog`, `generate-devlog`, `generate-readme`, `generate-commit-message`, `refactor-docs`, `refactor-project`, `update-config` (built-in) |

### Knowledge and catalog (3)

| # | Command | One-line | Default behavior | Scopes | Delegates to |
|---|---------|----------|------------------|--------|--------------|
| 7 | **`/compare`** | Compare the project to an external source -> adoption plan | Resolve source type (repo/article/local), analyze, write comparison report, offer `/plan from-comparison` | `repo`, `article`, `local` (auto-detected) | `compare-project` |
| 8 | **`/research`** | Deep research, report compilation, and export | Ask scope | `deep` (fan-out research), `compile` (merge reports), `report` (markdown -> docx/pptx) | `deep-research`, `compile-deep-research`, `generate-report` |
| 9 | **`/skills`** | Browse, search, create, import, and scan catalog skills/commands | Ask scope | `search`, `list` (cheatsheet of skills + commands), `create`, `import`, `scan` (security-scan a skill before install) | `search-skills`, `commands-cheatsheet`, `create-skill-or-command`, `import-skills`, NEW `skill-security-scan` |

### Spec, session, project, meta (5)

| # | Command | One-line | Default behavior | Scopes | Delegates to |
|---|---------|----------|------------------|--------|--------------|
| 10 | **`/spec`** | Specification and governance workflow | Ask scope | `clarify`, `analyze`, `constitution` | `clarify-spec`, `analyze-spec`, `constitution` |
| 11 | **`/session`** | Manage the development session | Ask scope | `continue`, `wrap-up`, `history` | `continue-session`, `wrap-up-session`, `generate-session-history` |
| 12 | **`/setup`** | Bootstrap and configure a project/repo | Bootstrap CLAUDE.md, scaffolding, README/DEVLOG/CHANGELOG; can add hooks | `project` (default), `hooks` (install pre-commit review hook) | `setup-project`, `install-pre-commit-review-hook` |
| 13 | **`/memory`** | Audit, prune, and manage memory + CLAUDE.md | Audit and propose memory cleanup | (none) | `manage-memory` |
| 14 | **`/usage`** | Check usage limits + model-switch advice | Show usage + recommendation | (none) | `check-usage` |

### 2A. The `/plan` command in depth (generate-plan + goals + dynamic workflows)

`/plan` is the most heavily-used command, so v3.0.0 makes it the most robust by merging three lineages:

1. **Everything `generate-plan` did.** The guided discovery interview (greenfield / feature / refactor question sets), from-comparison mode (reverse-engineer-first ordering), prior-version known-gaps ingest, knowledge-base + strategy grounding, the Constitution Check + Complexity Tracking gates, and the strict `T###` task-line file format. None of this is lost.

2. **Goals framing (OpenAI Codex `/plan` + Anthropic plan-mode goals).** A `goals` scope, plus a goals-first step at the top of every other scope, establishes the target problem, persona, and observable success criteria / definition-of-done *before* decomposition - seeded from the `product-strategy` STRATEGY anchor. Like Codex's `/plan <inline prompt>`, `/plan goals <one-liner>` accepts an inline goal and returns a crisp goal + DoD without producing a full phased plan. This prevents the most common planning failure: a detailed plan for the wrong objective.

3. **Dynamic-workflows robustness (Claude Code workflows, https://code.claude.com/docs/en/workflows).** When dynamic workflows are available in the harness, `/plan` can use them as a *quality* mechanism, not just for speed:
    - **Multi-angle drafting**: the workflows doc names "a hard plan worth drafting from several independent angles before you commit to one" as a prime use case. For a large or high-stakes plan, `/plan` offers to draft the plan from several independent angles (e.g., MVP-first, risk-first, architecture-first), have independent agents adversarially weigh them, and synthesize the strongest - a more trustworthy plan than a single pass.
    - **Parallel research at scale**: the research step fans out across sources and subsystems concurrently (up to 16 concurrent / 1,000 total agents per run), keeping intermediate findings out of the planning context and returning only the converged grounding.
    - **Workflow-aware phase prompts**: when a generated phase is a large fan-out task (audit every endpoint, migrate N files, generate tests for every unit), `/plan` writes that phase's executable prompt to *recommend running it as a dynamic workflow*, cross-linking `[[agent-orchestration-primitives]]` and carrying the scope-first token caution.
    - **Reusable**: a plan-drafting or plan-review process you repeat can be saved as a `.claude/workflows/` command.

**Graceful degradation (required).** Dynamic workflows are a plan-gated research-preview feature (Pro / Max / Team / Enterprise, Claude Code v2.1.154+, toggleable in `/config`). `/plan` MUST detect availability and fall back to single-agent planning when workflows are off or unavailable - it never assumes they are present, never hard-depends on them, and always offers the workflow path as an opt-in with the token-cost caution (calibrate on a small slice first). MCP Registry Policy impact: none - dynamic workflows are an Anthropic-runtime feature, so this is `skill-native` guidance plus command behavior, with zero new outbound calls, dependencies, or credentials.

The net effect: `/plan` is the merge point of phased planning, goal-setting, and at-scale orchestration - robust by default, workflow-accelerated when available.

## 3. Full 41 -> 14 Mapping (every old command accounted for)

| Old command | New command | New scope | Notes |
|-------------|-------------|-----------|-------|
| analyze-codebase | describe | full | generalized to any directory, software or not |
| generate-plan | plan | new/feature/refactor/from-comparison | renamed; from-comparison mode retained |
| generate-todos | plan | todos | bootstrap docs/todos.md |
| tasks-to-issues | plan | issues | fan tasks.md -> GitHub issues |
| implement-phase | implement | (positional slug/phase) | renamed single-word |
| generate-tests | test | all | |
| generate-unit-tests | test | unit | merged with iterative coverage loop |
| tdd | test | tdd | red-green-refactor |
| review-codebase | review | full / structure / quality | |
| review-changes | review | changes | multi-agent persona diff review |
| run-deep-review | review | full (orchestration) | deep orchestrates all lenses |
| run-security-audit | review | security | |
| run-penetration-test | review | pentest | |
| generate-sbom | review | sbom | security/supply-chain artifact |
| update-documentation | update | docs | |
| update-devlog | update | devlog | |
| generate-devlog | update | devlog | merged generate+update |
| generate-readme | update | docs (readme) | |
| update-gitignore | update | gitignore | |
| update-version | update | version | systemic version-sync (see CI fix) |
| generate-changelog | update | changelog | |
| generate-commit-message | update | commit | also part of release flow |
| refactor-docs | update | refactor | |
| refactor-project | update | refactor | |
| (update-config skill) | update | config | delegates to built-in update-config skill |
| compare-project | compare | (auto) | renamed |
| compile-deep-research | research | compile | |
| (deep-research skill) | research | deep | |
| generate-report | research | report | markdown -> docx/pptx export |
| search-skills | skills | search | |
| commands-cheatsheet | skills | list | unified skills+commands cheatsheet |
| create-skill-or-command | skills | create | |
| import-skills | skills | import | |
| analyze-spec | spec | analyze | |
| clarify-spec | spec | clarify | |
| constitution | spec | constitution | thin `/constitution` alias retained (heavily cross-referenced) |
| continue-session | session | continue | |
| wrap-up-session | session | wrap-up | |
| generate-session-history | session | history | |
| setup-project | setup | project | |
| install-pre-commit-review-hook | setup | hooks | |
| manage-memory | memory | (none) | |
| check-usage | usage | (none) | |

**New in v3.0.0 (not a rename)**: `skill-security-scan` skill + `nexus-skill-scanner` engine (SkillSpector adoption), surfaced via `/skills scan` and `/review skill-scan`; `agent-orchestration-primitives` skill (PDF adoption). These are skills/engines, not new commands.

## 4. Interactive-Scope Mechanism (uniform across all scoped commands)

Every scoped command follows this contract in its body:

1. **Parse the first positional argument** (`$ARGUMENTS`). If it matches a known scope token for this command, set `SCOPE` and skip the prompt. If it is a path/slug (for `/implement`, `/compare`, `/plan from-comparison`), route accordingly.
2. **If no recognized scope arg**, present a short numbered scope menu (the command's scope list) with a one-line description each, and a recommended default marked. Wait for the user's selection.
3. **`full` / comprehensive scope** runs every focused scope in the right order (e.g. `/review full` = structure -> quality -> coverage -> security -> changes, then synthesizes). For `/test all`, run unit -> integration -> e2e -> ci in sequence, each driven to its threshold.
4. **Delegate** to the resolved scope module (the retained skill body), passing any remaining args.
5. **Scope can also be inferred** where unambiguous (e.g. `/compare <github-url>` infers `repo`; `/test` with an existing failing suite starts at `unit`).

Authoring note: the scope menu text, the recognized scope tokens, and the delegation target live in the thin command file; the actual work lives in the retained skill. This keeps each command file well under 150 lines.

Example skeleton (illustrative):

```
# /review

Resolve SCOPE from $ARGUMENTS (one of: full, structure, quality, coverage,
security, pentest, changes, skill-scan, sbom, deps). If absent, ask:

  "What scope? 1) full (recommended)  2) structure  3) quality
   4) coverage  5) security  6) pentest  7) changes  8) skill-scan"

Then dispatch:
  full       -> run review-codebase + review-changes synthesis + security pass
  security   -> run-security-audit skill
  pentest    -> run-penetration-test skill
  skill-scan -> skill-security-scan skill (NEW)
  ...
```

## 5. Migration and Deprecation Plan

1. **Ship the 14 new command files** under `catalog/commands/`.
2. **Convert the 41 old files into deprecation shims** (do not delete): each old file becomes a 3-5 line body that prints `"/<old> is deprecated and will be removed in v4.0.0. Forwarding to /<new> <scope>."` and then performs the same delegation. This keeps every old invocation working through v3.x.
3. **Update `marketplace.json` `total_commands`** and the `AGENTS.md` / README count prose (41 -> 14 active + 41 deprecated aliases, or state "14 commands" with a note).
4. **Update the 5 platform instruction templates** (`templates/ai-instructions/base-*.md`) in lockstep where they enumerate commands.
5. **Document the rename map** in `CHANGELOG.md` (a clear old -> new table) and in a short `docs/v3/v3.0/command-migration.md` for users.
6. **Remove the shims at v4.0.0** (tracked as a known-gap / future plan).

## 6. Platform and Installer Impact

- **Auto-distribution**: command files in `catalog/commands/` are copied recursively by both installers -- no installer copy-step edit needed (per `AGENTS.md` distribution table). The new `nexus-skill-scanner` entry point script (`scripts/scan_skill_security.py`) DOES need an explicit copy step in BOTH `installer.sh` and `installer.ps1` (it is a `scripts/<name>.py` artifact).
- **Slash surface per platform**: Claude / Gemini / Codex get the `/name` slash surface (Codex via `prompts/`, though Codex now prefers skills -- the thin-command model aligns). Cursor / OpenCode / Copilot see the command body via the instruction file, not a slash menu.
- **`marketplace.json` `total_commands`** and **`AGENTS.md` "Current catalog"** prose must update (same class of count-drift that caused WN-v24-1).

## 7. Decisions Made and Rationale

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Scope mechanism | Interactive prompt + optional positional arg | Maintainer-confirmed; best UX, fewest files; matches Codex `/plan <arg>`. |
| `implement-phase` rename | `implement` | Pairs with `/plan`; `ship`/`build` mislead (release/compile). |
| Aggressiveness | ~14 (aggressive) | Maintainer-confirmed; collapses all `generate-*`/`update-*`/`refactor-*`/`run-*` families. |
| Architecture | Thin command -> retained skill scope-modules | Preserves all behavior; reviewable diff; 2026 platform alignment. |
| Back-compat | 41 deprecated alias shims through v3.x, removed v4.0.0 | Softens the breaking rename for muscle memory / scripts / docs. |
| Version | v3.0.0 (major) | Renaming/removing the public command surface is a breaking interface change -> SemVer MAJOR. |
| SkillSpector surface | `/skills scan` + `/review skill-scan` (no standalone `/scan`) | Keeps the 14-command target; scanning is both a pre-install action (skills) and an audit lens (review). |

## 8. Open Questions (for plan review)

- Should `/constitution` remain a permanent first-class alias (not just a v3.x deprecation shim) given how many skills cross-reference it? Recommendation: yes -- keep `/constitution` as a permanent alias to `/spec constitution`.
- Should `/commit` exist as a permanent thin alias to `/update commit` for high-frequency mid-dev use? Recommendation: yes -- keep `/commit` as a permanent convenience alias (note the built-in commit-commands `/commit` may also be present).
- `/test` threshold defaults: confirm the standardized coverage threshold (recommend 80% line per the repo's global testing rules) and pass-rate (recommend 100% of generated tests green before advancing a tier).
