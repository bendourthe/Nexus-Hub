# Development Workflows

Detailed workflows for new and inherited projects, phase verification, release preparation, and local checks. Read this when the short README workflow needs project-level detail.

## Recommended Workflows

Nexus-Hub provides two opinionated end-to-end workflows. Use these as a starting point and adapt to your project.

### New Project Workflow (5 phases)

Build from scratch with an AI coding agent as your primary partner.

#### 1. Planning

Open an AI chatbot (Claude.ai or ChatGPT) and brainstorm: problem, users, core features, tech stack, constraints. End the session by asking the chatbot to produce a structured Markdown implementation plan -- phases with subtasks, each subtask carrying a self-contained prompt the agent can execute.

#### 2. Project setup

1. Create the Git repo with a three-tier branching model: `main` / `develop` / `feature/*`.
2. Install the Nexus-Hub toolkit -- paste the one-line install command for your OS (see [Installation](../../README.md#installation)).
3. In Claude Code, run `/setup project` -- bootstraps `CLAUDE.md`, the directory structure, `.gitignore`, `README.md`, `DEVLOG.md`, and `CHANGELOG.md` in 8 guided phases.
4. Save the implementation plan from step 1 to `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/plans/v<version>-<slug>.md`.
5. Commit with `/commit`.

#### 3. Development (core loop)

Run `/implement <slug>` once. It asks every approval the run needs in one upfront round, then runs the whole plan in its own worktree: every subtask of every phase, tests and fixes, `/update gitignore` + `/update docs`, a session-history file, and a local commit per phase, then the single publication, the release, and cleanup. It stops only when the completion checker reports a terminal verdict, on a named blocker, or when you run `/implement pause`; `/implement <slug>` resumes.

To work one phase at a time instead, run `/implement <slug> phase <N>` (or `next`) in a fresh session per phase, or `/implement <slug> phase-by-phase` to review and commit after each phase.

**Non-final phases do not push** (v4.0.0). A remote pipeline run per phase bills to validate work the plan itself calls incomplete, and a red check on incomplete work teaches you to stop reading red checks. One branch, one commit per phase, all local.

The final phase does the rest in order: it reconciles your pipeline against the canonical CI/CD contract via `[[cicd-architect]]`, completes the full local gate, then pushes ONCE with your explicit approval and opens the integration pull request. That pull request is the plan's first remote validation, and it tests the merge result rather than the branch tip. A red required check reopens the final phase and is reproduced locally before any re-push; release work starts only after the merge lands green.

If you do want to push mid-plan (to share work in progress, say), just ask -- the rule removes the default, not your authority.

Each `/implement` phase runs a best-effort model-routing pre-flight before building: it re-confirms the model and reasoning effort `/plan` recorded for the phase, re-assessing against the currently-available models so a plan built before a new release picks up the newer or cheaper option. It is platform-agnostic and never blocks (it degrades to the plan's recommendation when routing is unavailable). Run `/route` to route any task or phase on demand.

#### 4. Quality assurance (pre-release)

1. Run `/review full` -- a 12-phase orchestrator that chains known-gaps collection, health gates, dependency scan, docs / git hygiene, project validators, codebase description (`/describe full`), and the `security`, `pentest`, and full codebase-review scopes.
2. Read the synthesis report -- it produces a P0 / P1 / P2 / P3 ranked list of findings with a GO / GO-WITH-CONDITIONS / NO-GO verdict.
3. Address all P0 and P1 findings before release. P2 findings can be deferred to a follow-up patch release; P3 findings are advisory.
4. Run `/review sbom` for compliance documentation.

#### 5. Release

1. Run `/update release` -- orchestrates version detection, layout cleanup, `.gitignore` audit, version-bump across all configuration files, CHANGELOG migration, doc sync, and the DEVLOG index line.
2. Merge `develop` into `main`, tag the release, and push.

### Inherited Project Workflow (2 phases)

For projects you have inherited or need to audit.

#### 1. Primary analysis and deep review

1. Clone the repo, open it in VS Code, start a Claude Code session.
2. Run `/review full` -- the same 12-phase orchestrator from Phase 4 of the New Project Workflow. The synthesis report's prioritized roadmap (P0 / P1 / P2 / P3) becomes your initial backlog.
3. If documentation is sparse, backfill it: `/update docs` (README, if missing), `/update changelog` (from git history), `/update devlog`, `/update refactor` (only when the repo has structural issues).
4. Establish the `develop` branch if not already present.
5. Commit the analysis artifacts.

#### 2. Making changes

For each change:

1. Brainstorm in a chatbot, then run `/plan` to produce a structured implementation plan saved to `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/plans/v<version>-<slug>.md`.
2. Run `/implement <slug>` to run the whole plan, or `/implement <slug> phase <N>` per phase -- identical to the New Project Workflow's development loop.
3. (Optional) Use git worktrees for parallel work:

    ```bash
    git worktree add ../project-fix feature/security-fix
    # work in a separate Claude Code session, then:
    git worktree remove ../project-fix
    ```

4. After all changes land on `develop`, run `/review full` again to verify nothing regressed, then `/update release` and merge to `main`.

The QA and release steps are identical to the New Project Workflow.

---

## Development setup

For contributors working *on* Nexus-Hub (not consumers of the installer), the repo ships a [`.devcontainer/`](../../.devcontainer/) at the root. Open the repo in VS Code with the Dev Containers extension installed (or click "Reopen in Container" when prompted) and the post-create hook will install Python tooling (`pytest`, `ruff`), the GitHub CLI (`gh`), and the Claude Code CLI (`claude`). Authenticate `gh` and `claude` once the container is up, then run `make validate` to confirm the catalog is clean.

The devcontainer is opt-in -- the standard Quick Start above does not require it. It exists for first-touch contributor onboarding and for reproducing the maintainer's environment across machines.

Maintainers can opt into the [repository attribution hook](../../.githooks/README.md). The normal validation profile also checks full Git history; use a complete clone. This repository-specific policy is not distributed by the installers.

### Running the checks locally

Validation logic lives in the repository, not in the workflow files, so what CI runs is exactly what you can run:

Before running `make test` on a fresh clone, run `make dev` to install all six extension development extras. On a Windows host without `make`, run the same install directly:

```powershell
python -m pip install --quiet -e "extensions/nexus-skill-server/[dev]" -e "extensions/nexus-code-search/[dev]" -e "extensions/nexus-web-fetch/[dev]" -e "extensions/nexus-skill-scanner/[dev]" -e "extensions/nexus-context-compressor/[dev]" -e "extensions/nexus-memory/[dev]"
```

```bash
make ci-fast       # seconds: parses, hygiene, workflow security, version sync
make ci-full       # minutes: every validator, the whole test tree, extensions
make ci-platform   # shell lint, PowerShell AST parse, Windows PowerShell 5.1 legs
```

Each target is a one-line delegation to `python scripts/ci/run.py --profile <name>`, which needs no CI provider and no network. Add `--list` to print what a profile would run without running it, or `--base origin/develop` to scope the run to what changed. Reports land in `reports/` (gitignored): a readable `summary.md`, plus JUnit, `summary.json`, and environment metadata.

Full guide, including how to add a check: [`docs/guides/repository-native-ci-profiles.md`](../../docs/guides/repository-native-ci-profiles.md).

---
