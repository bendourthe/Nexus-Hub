<p align="center"><a href="https://github.com/bendourthe/Nexus-Hub"><img src="assets/nexus-hub-banner.png" alt="Nexus Hub" width="640" /></a></p>

# Nexus-Hub

<!-- nexus-hub-version: 4.14.8 -->

Nexus Hub is a backend harness for AI coding tools: skills, commands, rules, hooks, guardrails, and best practices. The installer configures the supported platforms on your machine. Agents use the harness through their existing IDE, terminal, or configured app.

**Catalog:** 340 skills across 23 categories, 21 commands plus 3 permanent aliases, 37 registered hooks, and 23 agents.

[Chinese README](README_zh.md) | [Interactive guide and training](https://www.benjamindourthe.com/nexus-hub/index.html) | [Skills](data/SKILL_INDEX.md) | [Command cheatsheet](#command-cheatsheet) | [Platform coverage](docs/policy/platform-read-contracts.md)

## What's New in v4.14.8

- Plain-English guidance and source-labeled hook messages.
- A settings status-bar entry for saved defaults.
- Persistent usage-limit choices and handoffs that continue on another platform without waiting for the old limit to reset.

[Release details and earlier versions](CHANGELOG.md#4148---2026-11-04)

## Installation

**Windows PowerShell**

```powershell
irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex
```

**macOS / Linux Terminal**

```bash
curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash
```

The installer detects supported tools, copies the harness files, and verifies the installation. Reopen your IDE or start a new agent session afterward.

<img src="assets/readme/nexus-hub-installation.gif" alt="Compact terminal: paste the installation command, run the installer, and review verification on Windows, macOS, and Linux" width="900" />

[Static preview](assets/readme/nexus-hub-installation.png) | [Install options, updates, and verification](docs/guides/installation-and-platforms.md)

## Development Workflow

| Step | Command | Result |
| --- | --- | --- |
| 1 | `/describe` | Project map and dependencies |
| 2 | `/review` | Prioritized findings |
| 3 | `/plan` | Phases and acceptance checks |
| 4 | `/implement` | Changes verified against the plan |
| 5 | `/test` | Regression and boundary checks |
| 6 | `/update release` | Version, release notes, and release checks |

![Guided IDE tour with an animated cursor and spotlights through the six-command development workflow](assets/readme/nexus-hub-workflow.gif)

[Static preview](assets/readme/nexus-hub-workflow.png) | [Detailed workflows](docs/guides/development-workflows.md)

## Centralized IDE Settings

| Control | Behavior |
| --- | --- |
| Global effort level | Updates supported open sessions and sets the default for new sessions |
| Apply to all | Reapplies the default after a manual session override |
| Fast mode | Updates supported providers; disabled where unavailable |
| Guardrails | Enables checks for supported tool calls |
| Usage alerts | Controls popups while status-bar colors stay active |
| Extensions | VS Code controls for Claude Code and Codex recovery, tabs, and history |

Manual session choices remain until the next global change or **Apply to all**.

![Nexus Hub settings inside VS Code: change effort and Fast mode, manage guardrails and alerts, and access supported provider controls](assets/readme/nexus-hub-settings.gif)

[Static preview](assets/readme/nexus-hub-settings.png) | [Extension controls](extensions/nexus-hub-settings/README.md)

## Usage Monitors

- **Hover:** usage bars, quotas, and reset countdowns.
- **Click:** the provider's full dashboard in an editor tab.
- **Alerts:** one master switch, plus individual monitors in VS Code. Status colors remain active.

![Three portrait VS Code desktops: Claude Code, Codex, and Copilot hover and open their dashboards together](assets/readme/nexus-hub-usage.gif)

[Static preview](assets/readme/nexus-hub-usage.png) | [Interactive tour](guides/website/readme-showcase.html?tour=usage)

## Handoffs

1. **Choose:** Wait for reset, Hand off, or Continue on credits.
2. **Transfer:** copy the generated resume prompt into the receiving app.
3. **Continue:** send it with the project files and resume the recorded next step.

![Dark desktop tour: select Hand off in Claude, copy the full Nexus prompt, paste and send it in ChatGPT, then continue the unfinished test](assets/readme/nexus-hub-continuity.gif)

Provide the relevant project files to the receiving app. In installed agent integrations, `/handoff` prints in chat unless you explicitly request a file.

[Static preview](assets/readme/nexus-hub-continuity.png) | [Handoff command](catalog/commands/handoff.md)

## Platforms

| Platform | Nexus Hub integration |
| --- | --- |
| VS Code: Claude Code | Skills, commands, hooks, shared controls, and Claude usage monitor |
| VS Code: Codex | Skills, commands, hooks, shared controls, tabs/history, and Codex usage monitor |
| VS Code: GitHub Copilot | Supported instructions and commands, plus Copilot usage monitor; effort stays native |
| Cursor | Project harness, native Agent effort/Fast controls, and Cursor usage monitor |
| Antigravity | Project harness, supported IDE controls, and Gemini usage monitor |
| Claude desktop | Supplied project guidance and files, reusable procedures, and chat handoffs |
| ChatGPT desktop | Supplied project guidance and files, reusable procedures, and chat handoffs |

![Cursor and Antigravity IDE mockups showing Nexus Hub beside their native Agents and platform-specific controls](assets/readme/nexus-hub-platforms.gif)

[Static preview](assets/readme/nexus-hub-platforms.png) | [Interactive platform tour](guides/website/readme-showcase.html?tour=platforms)

Terminal agents also use the [supported integrations](docs/guides/installation-and-platforms.md#supported-agentic-platforms). File access, permissions, and hook coverage depend on the host. Project files and explicit handoffs carry work across tools and models.

## Command Cheatsheet

Command scopes, flags, and examples from the HTML guide. Run **`/skills list`** for the installed catalog.

<!-- readme-cheatsheet:start -->

### Codebase Understanding

Read-only commands. They write reports; they never edit the code.

#### `/describe`

Produce a structured description of any directory, software or not.

| Scope | Behavior |
| --- | --- |
| `full` | Complete structured description. The default. |
| `structure` | Layout, modules, and how the pieces are organized. |
| `deps` | Dependencies, external services, and version constraints. |
| `architecture` | Design, data flow, and key components, with diagrams. |
| `onboarding` | Fast start: what to read first and how to run it. |

```text
/describe full
```

A directory path may follow the scope. [See it in Training](guides/website/training.html#describe)

#### `/review`

Scope-able read-only review across every review lens.

| Scope | Behavior |
| --- | --- |
| `full` | Runs every lens in order, then one synthesized verdict. |
| `structure` | Module boundaries, layering, and the dependency map. |
| `quality` | SOLID, complexity, maintainability, code smells. |
| `coverage` | Test-coverage analysis and gap identification. |
| `security` | Secrets, auth, input validation, dangerous patterns. |
| `pentest` | Deep penetration test with proof-of-concept findings. |
| `changes` | Multi-persona review of the pending diff, or one commit with `changes <sha>`. Can draft review comments to the chat or to a named file; it never posts them. |
| `skill-scan` | Security-scan a skill, or the catalog, before install. |
| `sbom` | Generate a Software Bill of Materials. |
| `deps` | Dependency CVE, license, and supply-chain scan. |

```text
/review changes
```

Flags: `--scope <glob>` and depth flags pass through unchanged.

[See it in Training](guides/website/training.html#review)

#### `/compare`

Compare this project to an external source; produce a gap analysis and an adoption plan.

| Scope | Behavior |
| --- | --- |
| `repo` | Clone a Git repo; compare structure, dependencies, patterns. |
| `article` | Fetch a web article; compare its claims and recommendations. |
| `local` | Compare against a path already on disk. |

```text
/compare ../some-reference-repo
```

Scope is inferred from the source, never prompted. Chains into `/plan from-comparison`.

---

### Planning and Specification

These write plans, specs, and governing principles: the artifacts the build commands read.

#### `/plan`

Define goals and produce a phased plan for any multi-step effort.

| Scope | Behavior |
| --- | --- |
| `feature` | Plan a feature or enhancement on an existing project. |
| `goals` | Fix the problem, persona, and definition-of-done only. |
| `new` | Greenfield v0.1.0 build, with the full discovery interview. |
| `refactor` | Plan a refactor or cleanup campaign. |
| `from-comparison` | Seed a plan from a /compare adoption report. |
| `grill` | Re-run the critique-and-grill gate on an existing plan. |
| `todos` | Bootstrap docs/todos.md as a living progress tracker. |
| `issues` | Fan a plan's task lines out to GitHub issues. |

```text
/plan feature
```

`/plan goals <one-liner>` takes an inline goal. [See it in Training](guides/website/training.html#plan)

#### `/spec`

Specification and governance workflow.

| Scope | Behavior |
| --- | --- |
| `clarify` | A five-question loop that resolves spec ambiguities. |
| `analyze` | Cross-artifact consistency, coverage, and ambiguity audit. |
| `converge` | Post-build code-vs-plan gap check; appends the remaining work. |
| `constitution` | Author or amend the project's governing principles. |

```text
/spec clarify
```

#### `/constitution`

Author or amend the versioned project constitution.

| Scope | Behavior |
| --- | --- |
| `(bare)` | Author, or amend if a constitution already exists. |
| `amend` | Explicit amend mode. |
| `check <path>` | Read-only Constitution Check against a plan or spec. |

```text
/constitution check
```

---

### Implementation

The only commands here that write source. Non-final phases commit locally and never push.

#### `/implement`

Implement a whole plan, or every queued plan in a minor, end to end. One approval paste starts the run and sets the native goal where the platform supports it; the run stops only on a checker verdict, a named blocker, or a pause.

| Scope | Behavior |
| --- | --- |
| `<plan>` | Run the whole plan by default: every phase, then publish, release, and clean up. A slug, a plan file path, or a vX.Y.Z version. |
| `vX.Y` | Run every queued plan in that minor, in version order, under one approval. |
| `(bare)` | Run the whole next queued plan. |
| `<plan> phase <N>` | Step mode: run exactly one phase (also phase-N). |
| `<plan> next` | Step mode: run the first phase not yet complete. |
| `<plan> phase-by-phase` | Step mode: the full loop, pausing for a choice after each phase. |
| `<plan> full` | Accepted alias for the default (also in-full). |
| `pause` | Pause the current run at the next safe point. |

```text
/implement v0.5
/implement my-plan
```

[See it in Training](guides/website/training.html#implement)

#### `/route`

Score the task and recommend the cheapest sufficient model and reasoning effort.

| Scope | Behavior |
| --- | --- |
| `(bare)` | Assess the task currently in flight. |
| `phase N of <plan>` | Assess one specific plan phase. |
| `"<task text>"` | Assess a quoted task description directly. |

```text
/route
```

---

### Testing and Review



#### `/test`

Drive coverage to a threshold across test tiers until it and a 100% pass rate are met.

| Scope | Behavior |
| --- | --- |
| `all` | Unit, then integration, then e2e, then CI, each to threshold. |
| `unit` | Drive unit-test coverage to threshold. |
| `integration` | Drive integration-test coverage to threshold. |
| `e2e` | Drive end-to-end coverage to threshold. |
| `ci` | Verify the pipeline runs the suite and gates coverage. |
| `tdd` | Red-green-refactor cycle for one feature or bug. |

```text
/test unit
```

Flags: `--threshold` overrides the 80% line-coverage target; `--pass-rate` overrides the 100% pass gate.

[See it in Training](guides/website/training.html#test)

---

### Release and Governance



#### `/update`

Check progress, sync the repo, or run the release flow.

| Scope | Behavior |
| --- | --- |
| `release` | The full ship flow: commit, tag, push, publish the release. After the last release of a minor run, one closing pull request, then a checked cleanup that removes only merged, idle branches and worktrees. |
| `docs` | Sync README, API docs, architecture docs, inline guides. |
| `devlog` | Refresh the DEVLOG index line for this release. |
| `gitignore` | Audit .gitignore, clean the index, recommend LFS. |
| `version` | Bump the version atomically across every surface. |
| `changelog` | Regenerate or extend CHANGELOG.md from git history. |
| `refactor` | Reorganize docs and project artifacts to conventions. |
| `config` | Validate and repair installed platform configs. |
| `commit` | Generate a structured message for the staged changes. |
| `status` | Read-only progress, workers, elapsed time, estimates and dependencies. |

```text
/update status v0.5
```

[See it in Training](guides/website/training.html#update)

#### `/grill`

Interrogate a plan, design, or decision until nothing is left silently assumed.

```text
/grill
```

#### `/commit`

Generate a structured commit message for the staged changes.

```text
/commit
```

#### `/org`

Connect, sync, inspect, or author an organization knowledge bundle.

| Scope | Behavior |
| --- | --- |
| `status` | Inspect the current connection and per-platform posture. |
| `connect` | Validate and connect a directory or a git URL. |
| `sync` | Refresh the currently connected organization source. |
| `author` | Build a valid standards bundle through a guided flow. |

```text
/org status
```

---

### Communication and Reporting



#### `/presentify`

Turn documents, code, or a whole folder into one self-contained offline interactive website.

| Scope | Behavior |
| --- | --- |
| `deck` | One .pptx: keep the source flow as an interactive site. |
| `report` | One .docx, .pdf, or .xlsx, with structure and charts. |
| `compile` | Two or more files, or a folder: each source a labeled, attributed area. |

```text
/presentify ./docs --nav slides
```

Modes are auto-detected; override with `--mode`. Design: `--style`, `--theme`, `--layout`, `--nav` (scroll or slides), `--interactivity`, `--images`, `--verbosity`, `--qa-depth`, `--out`.

#### `/research`

Multi-source research, report compilation, and document export.

| Scope | Behavior |
| --- | --- |
| `deep` | Fan-out web research, verified adversarially, then cited. |
| `compile` | Merge several reports into one deduplicated document. |
| `report` | Export Markdown to .docx or .pptx via a template. |

```text
/research deep
```

#### `/visualize`

Turn data or a described structure into the smallest chart or diagram that answers the question.

| Scope | Behavior |
| --- | --- |
| `auto` | Infer chart or diagram from the input. |
| `chart` | Data to a chart: bar, line, scatter, distribution. |
| `diagram` | A flow, a dependency graph, or an architecture diagram. |
| `diff` | Explain a change set as a changed-modules diagram. |

```text
/visualize data.csv
```

Ends with a tier line naming the rung used: table, Mermaid, or an offline inline-SVG page. Never fabricates data or calls the network.

---

### Harness and Session Management



#### `/skills`

Browse, search, create, import, and scan the skill and command catalog.

| Scope | Behavior |
| --- | --- |
| `search` | Find skills by keyword, category, or role. |
| `list` | The unified cheatsheet of every skill and command. |
| `create` | Scaffold a new skill or command interactively. |
| `import` | Import catalog skills into a project, with a hygiene gate. |
| `scan` | Security-scan a skill, or the catalog, before install. |

```text
/skills list
```

#### `/commands`

Show the command cheatsheet, derived at runtime from the command files.

```text
/commands
```

#### `/session`

Manage the session boundary: resume, wrap up, or write history.

| Scope | Behavior |
| --- | --- |
| `continue` | Resume: what was in progress, and what comes next. |
| `wrap-up` | End-of-session sequence: history, cleanup, docs, commit. |
| `history` | Generate a standalone session-history document. |

```text
/session continue
```

#### `/setup`

Bootstrap a project, or install the opt-in pre-commit review hook.

| Scope | Behavior |
| --- | --- |
| `project` | Bootstrap instructions, scaffolding, .gitignore, core docs. |
| `hooks` | Install the opt-in pre-commit AI review hook. |

```text
/setup project
```

#### `/tune-prompting`

Refresh how the catalog prompts each current model.

| Scope | Behavior |
| --- | --- |
| `(bare)` | Full flow across every model needing research. |
| `<model-id>` | Restrict the run to one model. |

```text
/tune-prompting --dry-run
```

Flags: `--dry-run` proposes without applying; `--profiles-only` skips the shared-body stage entirely.

#### `/memory`

Audit, prune, and reorganize the instruction and memory files.

```text
/memory
```

#### `/usage`

Check usage limits and get a model-switching recommendation.

```text
/usage
```

#### `/handoff`

Print a paste-ready resume prompt in chat so another agent can continue. Write a file only when requested.

```text
/handoff
```

<!-- readme-cheatsheet:end -->

[Interactive cheatsheet](https://www.benjamindourthe.com/nexus-hub/index.html#cheatsheets) | [Command catalog](catalog/commands/)

## Documentation

- [Installation and platform reference](docs/guides/installation-and-platforms.md)
- [Development workflows and local checks](docs/guides/development-workflows.md)
- [Skill catalog](data/SKILL_INDEX.md) and [command catalog](catalog/commands/)
- [Security, privacy, and regulated-use considerations](SECURITY.md)
- [Contributing](CONTRIBUTING.md) and [project progress](docs/todos.md)
- [Editable animation sources](assets/readme/README.md)

## License

[MIT](LICENSE). Maintained by [Benjamin Dourthe](https://www.benjamindourthe.com/).
