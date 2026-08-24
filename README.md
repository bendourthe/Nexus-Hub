<p align="center"><a href="https://github.com/bendourthe/Nexus-Hub"><img src="assets/nexus-hub-banner.png" alt="Nexus-Hub" width="640" /></a></p>

<p align="center"><em>The Skill Harness for Every AI Coding Assistant.</em></p>

# Nexus-Hub

<!-- nexus-hub-version: 3.20.2 -->

Nexus-Hub is the upstream skill catalog for AI coding assistants: 324 skills, 18 commands, 33 hooks, 23 agents, and 4 language rule families. It installs in one step on Windows, macOS, and Linux, and it works the same across Claude Code, OpenAI Codex, Gemini (via Antigravity), GitHub Copilot, Cursor, GitHub CLI, and the sibling Nexus desktop app and VS Code extension. The catalog is reverse-engineering-first by policy: zero third-party data processors, zero outbound calls from skills / commands / hooks, zero telemetry.

## Interactive Guide -- start here

**New to Nexus-Hub? [Open the interactive guide](guides/website/nexus-hub-guide.html).** It is a self-contained, click-through walkthrough of the entire workflow -- install, onboard an unfamiliar codebase, plan, implement, harden, and ship -- with simulated VS Code / terminal sessions and the artifact each command produces. It is the fastest way to get a teammate productive, and it doubles as a live-demo-quality presentation.

- **File:** [`guides/website/nexus-hub-guide.html`](guides/website/nexus-hub-guide.html) -- one HTML file, fully offline, no server or install required.
- **To view it:** GitHub does not render HTML inline. Open the file above and click **Download raw file** (top-right of the file view), then open the downloaded `.html` in any browser. Or clone the repo and double-click it.
- **To share it:** send that single file to anyone on the team. See [guides/website/README.md](guides/website/README.md) for maintainer notes.

> **Renamed from DevAI-Hub at v2.0.0** to align with the sibling project [Nexus](https://github.com/bendourthe/Nexus-AI), a local-first desktop AI Studio that consumes Nexus-Hub as its upstream skill feed. Existing `~/.devai-hub/` installs are migrated in place by the v2.0.0 installer on first run; see [docs/archive/v2/v2.0/RELEASE_NOTES.md](docs/archive/v2/v2.0/RELEASE_NOTES.md) for the full migration story.

---

## How Nexus-Hub fits with Nexus

<p align="center">
<a href="https://github.com/bendourthe/Nexus-Hub"><img src="assets/nexus-hub-banner.png" alt="Nexus-Hub" width="360" align="middle" /></a>
<img src="assets/sibling_arrow.svg" alt="↔" width="80" align="middle" />
<a href="https://github.com/bendourthe/Nexus-AI"><img src="assets/nexus-ai-banner.png" alt="Nexus" width="360" align="middle" /></a>
</p>

Nexus-Hub and [Nexus](https://github.com/bendourthe/Nexus-AI) are two halves of the same idea, split along a deliberate seam.

- **Nexus-Hub (this repo)** is the catalog: 324 curated skills, 18 commands, 33 hooks, 23 agents, 4 rule families, plus 4 internal MCP servers (`nexus-skill-server`, `nexus-code-search`, `nexus-web-fetch`, `nexus-context-compressor`) and the local `nexus-memory` CLI store. It is content-only, platform-agnostic, and shipped via an installer that writes to `~/.nexus-hub/` and into each AI assistant's per-platform config locations.
- **Nexus** is a local-first desktop AI Studio that consumes Nexus-Hub as its skill feed. Nexus's `AGENTS.md` names this repo as "the only external project we deliberately link to" -- the upstream feed for its skill harness.

The two projects are designed to be useful independently: you can install Nexus-Hub into any supported agent platform without touching Nexus, and Nexus can run with or without the upstream catalog wired in. The combination is what gives a single curated skill set to every agent surface a developer touches: terminal, IDE, desktop app, and CLI.

---

## What's New in v3.20.2

**Interface-craft is now a first-class cluster, not a hole in the catalog.** Six skills (net +6, polish merged into `hallmark-design` rather than a seventh skill) cover accessibility, layout, in-product copy, typography, color systems, and a coordinating `interface-review`. Overlapping rules have one owner; a missing delegate is named instead of reconstructed. Recipe-level elevation, radius, icon stroke, and motion values land in `hallmark-design` after its anti-slop gates. Catalog is **321 skills** across **23 categories**.

This release changes no opt-in capability, installer flag, or host surface.

## Previously, in v3.20.1

**Security coverage doubled, with the gates to keep it honest.** Forty independently authored cybersecurity skills (OT, mobile, API abuse, applied crypto, intel ops, zero trust, deception, firmware, smart contracts, wireless, SSVC/SLSA, purple team) plus two categories (`ot-security`, `mobile-security`). Dual-use skills open with an authorization gate. MITRE F3 mapping, an ATT&CK Navigator export, an agentskills.io conformance guard, a committed coverage map, and an 800-line SKILL.md body cap. Catalog is **315 skills** across **23 categories**.

This release changes no opt-in capability, installer flag, or host surface.

## Previously, in v3.20.0

**Agent execution now has an OS-level isolation skill.** `agent-execution-isolation` teaches Landlock, seccomp, network namespaces, per-session ephemeral containers, placeholder credentials, and an out-of-process egress proxy (static rules, optional LLM judge, SSRF/RFC-1918 blocks, human escalation). `/review security` engages it when the reviewed project spawns agents, holds agent credentials, or makes agent-driven egress calls.

**Existing skills now point at that model instead of duplicating it.** `agentic-endpoint-hardening` documents credential brokering (placeholders in the agent, real keys at a broker). `egress-redaction` states that typed BLOCK/REDACT/HASH/PASS is skippable content policy, not a network perimeter. `ai-agent-governance` records the three-question triage (sandbox, broker, egress) under Pillar 3.

Catalog counts are **275 skills**, **18 commands**, **33 hooks**, and **23 agents**. This release adds no installer flag, opt-in host surface, or outbound call.

## Previously, in v3.19.2

**Agents now have a durable, cross-platform memory store.** `nexus-memory` is a local append-only log of lasting facts, decisions, and events. An agent reads it at session start within a fixed line budget, records as it works, and summarizes older ranges itself. The store never calls a model, never starts a background process, and never leaves the machine. Default root is `~/.nexus-hub/memory/`.

**A read that the harness would silently truncate is no longer acceptable.** Shared output paging splits agent-consumed script output by both a byte cap and a line cap (defaults: 16,000 bytes and 256 lines, the minimum across surfaces verified on 2026-08-23). Printed next-step commands resolve to the script's own path, so they work when the script is not on PATH.

**A relocated store is no longer documentation-only.** Creating or appending inside a git working tree is refused, POSIX permissions are owner-only, and the `memory-store-guard` hook blocks Write, Edit, and git staging of store artifacts unless `NEXUS_MEMORY_ALLOW_IN_REPO=1`.

**The new `agent-memory` skill is the routing home for this store.** It is distinct from `session-query`, `context-pack-builder`, `continuous-learning`, and `solution-knowledge-base`, which stay on-demand and topic-scoped. Spawned subagents are told not to write. Catalog count is now **275 skills**, **18 commands**, **32 hooks**, and **23 agents**.

`nexus-memory` is a local CLI package, not a fifth MCP server. The four internal MCP servers are unchanged. The package is stdlib-only: **zero outbound calls, zero API keys, zero model downloads**.

## Previously, in v3.19.0

**Code intelligence is now cheaper to expose, safer to act on, and still fully offline.** `nexus-code-search` adds `minimal`, `standard`, and `full` tool profiles so a session can expose 7, 16, or 20 tools instead of paying the full definition cost every time. Full remains the compatibility default, and profiles change visibility only - they grant no additional authority.

**Repository searches can route through the local index.** A cross-platform `PreToolUse` hook recognizes Grep, Glob, and equivalent shell searches, then points the agent toward `nexus-code-search`. Its default `soft` mode is advisory; `NEXUS_CODE_SEARCH_ROUTING=block` makes matched searches fail with exit 2, while unrelated commands remain untouched.

**Every MCP tool can return compact responses.** Set `response_format=auto` to use the versioned `NEXUS-CW/1` format only when it clears the measured savings threshold, or use `compact` to force it. JSON remains the default and the fail-open fallback, and `nexus-context-compressor` recognizes the marker so it does not compress the same payload twice.

**Mutation planning gains evidence-backed preflights.** `code_edit_safety`, `code_delete_safety`, and `code_rename_safety` return ordered verdicts with the indexed callers, importers, and references behind them. `insufficient_data` stays distinct from safe, and each result states the graph's cross-repository visibility boundary.

**The local index now understands more than code.** A provider seam ships with a Markdown provider for headings and hierarchy, plus optional hybrid retrieval through pre-placed ONNX weights. Dense retrieval is off by default, never downloads a model, and degrades to keyword search with a precise local hint when its extra, weights, or encoder are unavailable.

The deterministic benchmark records retrieval quality, response bytes, estimated tokens, definition cost, and latency against unique temporary workspaces. CI runs the full extension suite in a container with `--network none`, and the server now supports both MCP SDK 1.x and 2.x schema attribute names. See the [code-search README](extensions/nexus-code-search/README.md) for activation and rollback guidance.

Catalog counts are unchanged at **273 skills**, **18 commands**, **31 hooks**, and **23 agents**. The extension preserves its published guarantee: **zero outbound calls, zero API keys, zero model downloads**.

## Previously, in v3.18.3

**`/presentify` can now produce a slide deck.** Pass `--nav slides` (or pick "Slide deck" in the canvas question) and the output becomes viewport-fitted slides advanced by keyboard arrows, rather than a page you scroll. Everything else about the output is unchanged: still one self-contained offline HTML file, still real interactive charts, still commercial-use-safe imagery.

```bash
/presentify report.pdf --nav slides --interactivity rich
```

Forward is ArrowRight / ArrowDown / PageDown / Space, back is ArrowLeft / ArrowUp / PageUp, Home and End jump to the first and last slide, touch swipes, and on-screen zones click. `scroll` remains the default and the non-interactive fallback, so nothing changes for anyone who does not ask for slides.

**The intake stayed at four questions.** The interactive question surface caps at four per round, so navigation rides on the existing output-aspect question rather than adding a fifth. `--layout` binds the aspect half and `--nav` the navigation half: name both and the question disappears, name one and it narrows to what is still unresolved. The two compose rather than conflict, so `--layout portrait --nav slides` is portrait-ratio slides, and no pair of flags can deadlock the intake.

**The interesting problem was animation, not navigation.** Slide mode has no scroll, so every scroll-triggered effect the balanced, rich, and cinematic levels ship had to be re-expressed or it would simply never fire, leaving content permanently hidden. There are now three slide-native trigger classes and a mapping table covering every pattern in the catalog: effects that run once when a slide activates, effects stepped by arrow key within a slide (PowerPoint-style builds), and permanent ambient loops for atmosphere. One rule is binary and load-bearing: **only non-data-bearing motion may loop.** A chart build or a numeric transition must be entry-triggered or stepped, because looping data motion fabricates the impression of live data.

Cinematic survives too. The scroll-scrubbed camera becomes a fragment-stepped camera - one keyframe per arrow press, using the easing the scrub curve would have applied, with a subtle drift while a keyframe holds. Slide mode changes the trigger, never the asset policy: the size gate, the no-hosted-generation boundary, and the stills-only reduced-motion path all apply unchanged.

**The QA loop grades slides as strictly as pages.** The visual-QA rubric gains a twelfth criterion covering per-slide fit at all four viewports, fragment integrity including deep-link state, ambient-loop discipline, and navigation chrome. The structural scorer gains seven deterministic checks that skip cleanly on a scrolling page, so every page authored before this release stays out of the failure set. One of the seven deliberately runs *outside* that skip: it fails when a page's design record says slides but the markup lost its `data-nav` attribute, which would otherwise skip all six other checks and score a confident green.

Under `prefers-reduced-motion: reduce` a deck is a sequence of settled, fully-legible stages: transitions become instant cuts and ambient loops are removed entirely rather than slowed. Without JavaScript it degrades to ordinary stacked sections in source order, and it prints one slide per page.

Catalog counts are unchanged at **273 skills**, **18 commands**, **31 hooks**, and **23 agents**: this release adds one reference file to an existing skill's bundle rather than a new skill.

## Previously, in v3.18.2

**The GitHub Usage Monitor has been withdrawn.** It is deleted from the catalog, and upgrading uninstalls it from both VS Code and Cursor. Unshipping alone would not have been enough: an extension already installed keeps running, and this one could report a confident **0% used against an allowance GitHub showed as fully exhausted**.

**Why it could not be fixed.** The extension existed to mirror the Included usage bars on `github.com/settings/billing`. That figure is not served by any API. The endpoint that once returned it (`/{scope}/settings/billing/actions`, carrying `included_minutes` and `total_minutes_used`) was [closed down on 2025-09-26](https://github.blog/changelog/2025-09-26-product-specific-billing-apis-are-closing-down/); re-verified 2026-08-22, the Budgets API exposes only budget amounts, `/usage` and `/usage/summary` carry no allowance field, and GraphQL has no billing surface at all.

So the number had to be reconstructed, and the reconstruction needs one input GitHub does not provide. The billing page discounts cover *"Actions usage in public repositories **and** included usage for Actions minutes and storage"* -- two reasons summed into one figure, with no discount-reason field and no visibility field on any line item. The only discriminator is the repository, and GitHub reports visibility **as of now** while billing items are **historical**. A repository that was private when its minutes ran and is public today has its whole month retroactively reclassified as free, which is exactly how a saturated allowance renders as 0%. That gap is a property of what is missing from the data, not something an implementation can close.

The mechanism also moves underneath any reconstruction: runner prices were cut on 2026-01-01, and from 2026-03-01 self-hosted runners began consuming the quota "based on list price". The second change silently falsified two statements v3.18.1 itself shipped.

**The Claude, Codex, and Cursor monitors are unaffected and stay.** They do not share the problem: each reads a *served* usage figure from its vendor's own first-party endpoint and reconstructs nothing. That is the difference, and it is why only this one was withdrawn.

Settings under `githubUsageMonitor.*` are left in place rather than deleted; they are inert and harmless. Full reasoning, including the four alternatives rejected and the one thing that would reopen the decision, is at [`docs/decisions/implemented/architecture/2026-08-22-withdraw-the-github-usage-monitor.md`](docs/decisions/implemented/architecture/2026-08-22-withdraw-the-github-usage-monitor.md).

Catalog counts are unchanged at **273 skills**, **18 commands**, **31 hooks**, and **23 agents**. Nexus-Hub now ships **three** usage monitor extensions instead of four.

---

## Supported Agentic Platforms

| Platform | Install target | Path | Per-platform surface |
|---|---|---|---|
| Claude Code (Anthropic) | `~/.claude/` + project `.claude/` | legacy + registry | Full: skills, commands, hooks, agents, rules, MCP configs |
| OpenAI Codex CLI | `~/.codex/` + project `.codex/` + `AGENTS.md` | legacy + registry | Full: skills (under `skills/`), commands (under `prompts/`), agents, rules |
| Gemini (IDE / Antigravity 1.0) | `~/.gemini/` + project `.gemini/GEMINI.md` | legacy + registry | Full: skills, commands (under `workflows/`), agents, rules |
| **Gemini CLI (Google, ENTERPRISE-ONLY post-2026-06-18)** | `~/.gemini/commands/*.toml` + project `.gemini/commands/*.toml` | **registry (new in v2.1.0; gated behind `--enterprise` / `-Enterprise` flag in v2.2.0)** | TOML-format custom commands generated from `catalog/commands/*.md`. Non-enterprise users transition to Antigravity CLI before 2026-06-18 per the 2026-05-21 Google announcement. |
| **Antigravity 2.0 + CLI (Google)** | `~/.gemini/antigravity-cli/` + project `.agents/` | **registry (new in v2.1.0, CLI coverage added v2.2.0; paths verified v2.3.0)** | Full: skills, commands (under `workflows/`), subagents, rules. Single integration covers both the desktop IDE and the standalone Antigravity CLI (`agy` binary), verified 2026-05-29 against Google's public Antigravity CLI docs. |
| GitHub Copilot (VS Code) | project `.github/copilot-instructions.md` | legacy + registry | Behavioral guardrails (skill index embedded as text); merge semantics if the file already exists |
| Cursor | project `.cursor/rules/*.mdc` + `AGENTS.md` | registry | Per-rule `.mdc` files + behavioral guardrails (skill index embedded as text) |
| OpenCode | project `AGENTS.md` + `.opencode/` | registry | Behavioral guardrails + skills mirror |
| **Nexus-AI (Local Studio)** | `~/.nexus-ai/catalog/` + project `.nexus-ai/catalog/` | **registry (new in v2.1.0)** | Full mirror: skills, commands, agents, rules, hooks, MCP configs, templates, plus a `nexus-hub-version.json` manifest. Isolated under `catalog/` so the app's own data at the `~/.nexus-ai/` root stays outside a catalog refresh. |
| GitHub CLI (`gh`) | via `gh copilot` extension | indirect | Skill / command references via `AGENTS.md` open standard |
| Nexus desktop app | upstream consumer | indirect | Reads the same catalog as its skill feed |
| Nexus VS Code extension | upstream consumer | indirect | Reads the same catalog as its skill feed |

**Coverage caveat**: the **registry** path (introduced in v2.1.0 Phase 10) dispatches install / teardown through `scripts/lib/integrations/runner.py` and supports a `--dry-run` mode. The **legacy** path (the long-standing in-installer copy blocks) continues to be the canonical install for Claude / Gemini / Codex / Copilot until v2.2.0 parity migration (tracked as DF-001 in `docs/archive/v2/v2.1/known-gaps.md`). Both paths produce the same end-state on disk for those platforms; the per-platform installer logic lives in [`scripts/installer.sh`](scripts/installer.sh), [`scripts/installer.ps1`](scripts/installer.ps1), and the per-platform subclasses under [`scripts/lib/integrations/`](scripts/lib/integrations/). Per-platform capability specs (install surface, distributed content, instruction file, quirks) are documented under [`docs/specs/`](docs/specs/).

**Branch-based install** (v2.4.0): pass `--branch <name>` (Bash) or `-Branch <name>` (PowerShell) to install the catalog from a pushed branch instead of the current checkout. The installer shallow-clones the repo at `<name>` into a deterministic cache directory (`~/.nexus-hub/branches/<sanitized-name>/`) and runs the install from that checkout, so the user's working copy is never touched. The branch name is sanitized for filesystem safety (path-traversal sequences are neutralized). Combine with `--check` / `-Check` for a clone-free probe that prints the resolved cache path and clone source.

---

## Quick Start (one command)

Open a terminal and paste the line for your system. It downloads the catalog from this repo and runs the installer -- no clone, no unzip, no `cd`.

**macOS / Linux** (paste into Terminal):

```bash
curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash
```

No `curl` on the box? Use `wget`:

```bash
wget -qO- https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash
```

**Windows** (paste into PowerShell):

```powershell
irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex
```

That is the whole setup -- no prompts. The installer prechecks its dependencies (and tells you exactly what to install if one is missing), then performs a global install across every supported assistant it detects; assistants you do not have are skipped with a note, never an error. Your customizations are preserved (marker-merge), and on a re-install it asks once only if it finds a managed file you changed that it would overwrite, naming the file.

**Done.** The installer writes to `~/.nexus-hub/` (the user-global catalog) and into each supported assistant's per-platform config locations. If a legacy `~/.devai-hub/` install is detected, you will see a single migration prompt at the top of the run -- answer `Y` (default) to migrate in place.

After the installer completes:

- **Globally**: your user profile has all 324 skills, 18 commands, 33 hooks, 23 agents, plus Gemini and Codex instructions.
- **Locally**: your project has `copilot-instructions.md` and `AGENTS.md` tailored to your language.

**Power-user flags**: `--workspace <path>` installs into a single repo instead of globally; `--platforms <comma-list>` limits the install to a subset of assistants; `--yes` runs fully unattended (refreshes managed files with no prompt -- ideal for CI). Prefer to clone first? `git clone` the repo and run `./install.sh` (macOS / Linux) or `install.bat` (Windows) -- the in-repo path still works exactly as before.

### Claude Code plugin (subscribe-style alternative)

The installer above is the primary path: every platform, hooks, and `nexus-hub upgrade`. Claude Code users who only want the catalog as a plugin can subscribe instead:

```
/plugin marketplace add bendourthe/Nexus-Hub
/plugin install nexus-hub@nexus-hub
```

This is not a replacement for the installer. It does not install hooks, other platforms, or the `nexus-hub` CLI.

If Anthropic later lists Nexus-Hub in `claude-plugins-official`, that listing is pinned to a git SHA that can lag tagged releases. Marketplace users may trail `main`. Prefer the installer, or this repo's marketplace added from a release tag, when you need the current release. The maintainer submission draft is [`docs/v3/v3.20/development/claude-marketplace-submission.md`](docs/v3/v3.20/development/claude-marketplace-submission.md).

### Installing a subset (selective installation)

By default you get the whole catalog. If you want a smaller install, pick a **profile**, one or more **capability modules**, or one or more **role bundles**. Selectors combine by union.

```bash
# macOS / Linux
bash scripts/installer.sh --profile core
bash scripts/installer.sh --modules ai-engineering,testing
bash scripts/installer.sh --bundles ai-engineer
bash scripts/installer.sh --profile core --modules security-operations   # union
```

```powershell
# Windows
.\scripts\installer.ps1 -Profile core
.\scripts\installer.ps1 -Modules ai-engineering,testing
.\scripts\installer.ps1 -Bundles ai-engineer
```

Profiles are `minimal`, `core`, and `full`. Modules group skills by capability (one per catalog category, so every skill is reachable through at least one). Role bundles are curated cross-category sets like `ai-engineer` or `devops-engineer`. List what is available with `python scripts/lib/installer/selection.py --repo-root . --profile core` , which prints the resolved plan without installing anything.

Three things worth knowing before you narrow an install:

- **Hooks, rules, templates, and settings always install**, under every selection including `minimal`. Narrowing your skill set asks for fewer capabilities, never for fewer guardrails.
- **Commands and agents follow their skills.** A command that is a thin pointer over one skill (for example `/implement` over `implement-phase`) installs only when that skill is selected; everything else installs regardless. So a focused install stays coherent instead of leaving commands that cannot do anything.
- **No selector means the full catalog**, byte-for-byte identical to what you would have got before selective installation existed.

`nexus-hub upgrade` re-applies whatever you selected, so an upgrade never quietly widens a focused install back to everything. To change scope, pass a new selector; to go back to everything, pass `--profile full`.

Selectors need Python to resolve. A full install does not.

### Keeping it current

Run `nexus-hub upgrade` -- it reports your installed version against the latest, shows a short what's-new summary, and updates in place on confirmation. Re-running the install command above works too; the installer is idempotent.

### Verifying your install

Run `nexus-hub verify` to confirm your installed catalog matches the published release. It recomputes the SHA-256 of every file in the catalog tree and diffs the result against the `MANIFEST.sha256` that ships with each release, reporting any file that is modified, missing, or unexpected, then a single `verify: PASS` or `verify: FAIL` line. It is strictly local: it reads only local files, makes no network call, needs no credential, and adds no dependency.

What this does and does not prove: `verify` detects on-disk tampering or corruption AFTER install, relative to the published catalog. It is trustworthy to the extent the manifest itself came from the release you trust (it rides inside the same signed release tag the installer pulls from). It is NOT a code signature and NOT a substitute for verifying the download channel -- an attacker who can rewrite both a file and the manifest in the same tree defeats it. Use it to catch accidental corruption and post-install drift, not to establish first-trust in the bytes.

### Add organization standards

Connect a validated local-directory or Git bundle with `nexus-hub org connect <path-or-url>`, inspect it with `nexus-hub org status`, and then reinstall or repair the target workspace. Nexus-Hub projects the organization's concise core and rule files into existing platform surfaces without uploading the bundle or claiming policy enforcement. See the [Organization Knowledge Layer guide](guides/ORG_KNOWLEDGE_LAYER.md) for the bundle contract, lifecycle commands, precedence model, authoring workflow, and rollback procedure.

---

## What is Nexus-Hub?

Most AI assistants are generic by default: they know a lot but specialize in nothing. Nexus-Hub is the layer that turns a generic assistant into a specialist for the work you actually do.

It does three things:

1. **Behavioral rules** -- per-language code-style and security rules that tell the assistant how to write code in your project (not just whether the code compiles).
2. **Autonomous skills** -- 208 curated capability prompts grouped into 22 categories. Each skill has a 3-tier loading model (always-loaded summary, body on trigger, deeper references on demand) so context cost stays proportional to what the agent actually needs.
3. **Workflow awareness** -- 36 slash commands that chain skills into multi-step processes (plan generation, phase implementation, deep review, version bump, release notes, session history).

The catalog itself is content; the harness around it is the per-platform installer plus a small set of local MCP servers that surface the catalog to any agent that speaks MCP.

---

## Recommended Workflows

Nexus-Hub provides two opinionated end-to-end workflows. Use these as a starting point and adapt to your project.

### New Project Workflow (5 phases)

Build from scratch with an AI coding agent as your primary partner.

#### 1. Planning

Open an AI chatbot (Claude.ai or ChatGPT) and brainstorm: problem, users, core features, tech stack, constraints. End the session by asking the chatbot to produce a structured Markdown implementation plan -- phases with subtasks, each subtask carrying a self-contained prompt the agent can execute.

#### 2. Project setup

1. Create the Git repo with a three-tier branching model: `main` / `develop` / `feature/*`.
2. Install the Nexus-Hub toolkit -- paste the one-line install command for your OS (see [Quick Start](#quick-start-one-command)).
3. In Claude Code, run `/setup project` -- bootstraps `CLAUDE.md`, the directory structure, `.gitignore`, `README.md`, `DEVLOG.md`, and `CHANGELOG.md` in 8 guided phases.
4. Save the implementation plan from step 1 to `docs/<version>/plans/<slug>.md`.
5. Commit with `/commit`.

#### 3. Development (core loop)

For each plan phase:

1. Create a feature branch: `feature/phase-N-short-description`.
2. Open a fresh Claude Code session.
3. Run `/implement <slug> <phase>` -- walks every subtask, generates and runs tests, applies fixes, runs `/update gitignore` + `/update docs`, generates a session-history file, and produces a commit message.
4. Commit and push the feature branch.
5. Merge into `develop`. Repeat for the next phase.

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

1. Brainstorm in a chatbot, then run `/plan` to produce a structured implementation plan saved to `docs/<version>/plans/<slug>.md`.
2. Run `/implement <slug> <phase>` per phase -- identical to the New Project Workflow's development loop.
3. (Optional) Use git worktrees for parallel work:

    ```bash
    git worktree add ../project-fix feature/security-fix
    # work in a separate Claude Code session, then:
    git worktree remove ../project-fix
    ```

4. After all changes land on `develop`, run `/review full` again to verify nothing regressed, then `/update release` and merge to `main`.

The QA and release steps are identical to the New Project Workflow.

---

## Manual setup (if you do not want to run the installer)

If you prefer to copy things yourself, here is how the repo is organized.

### Claude Code (Anthropic)

The most powerful integration -- adds **autonomous agent capabilities**.

- **CLAUDE.md**: the "brain". Copy `catalog/CLAUDE.md` to your project root and customize.
- **Skills**: the "hands". Copy folders from `catalog/skills/` to your project's `.claude/skills/` folder.

    *Example*: copy `catalog/skills/research/trend-research` to enable the trend-research skill.

### Gemini (Google) and Antigravity

Optimized instructions for Google's Gemini models, including the Antigravity workspace layout.

- **Gemini instructions**: copy `templates/ai-instructions/base-gemini.md` (or `templates/ai-instructions/generic-instructions.md` for the legacy template) to `.gemini/GEMINI.md` in your project or user profile.
- **Skills and workflows**: the installer mirrors these to `.gemini/skills/` and `.gemini/antigravity/global_workflows/` so they appear globally in Antigravity.

### GitHub Copilot (Microsoft)

Instructions for VS Code's Copilot Chat.

- Copy `templates/ai-instructions/coding-instructions/{language}.md` to `.github/copilot-instructions.md`.

### Codex (OpenAI)

OpenAI Codex CLI integration. Codex reads `AGENTS.md` at the project root (the open standard, also honored by Cursor / Aider / Jules) plus its user-level config in `~/.codex/`.

- **AGENTS.md**: copy `templates/ai-instructions/base-codex.md` content into your project's `AGENTS.md`.
- **Skills and prompts**: the installer mirrors `catalog/skills/` to `~/.codex/skills/` and `catalog/commands/` to `~/.codex/prompts/`. For manual setup, copy each tree to those destinations.

### Cursor

Cursor IDE integration.

- **Project rules**: copy `templates/ai-instructions/base-cursor.md` content into `.cursor/rules/nexus-hub.mdc` at your project root. Use `alwaysApply: true` in the frontmatter so Cursor applies the rule on every prompt.
- **Open-standard `AGENTS.md`**: Cursor also reads `AGENTS.md` at the project root, so the Codex setup above covers Cursor too.

### OpenCode

OpenCode IDE integration. OpenCode reads `AGENTS.md` per the open standard.

- Copy `templates/ai-instructions/base-opencode.md` content into your project's `AGENTS.md`.

---

## Development setup

For contributors working *on* Nexus-Hub (not consumers of the installer), the repo ships a [`.devcontainer/`](.devcontainer/) at the root. Open the repo in VS Code with the Dev Containers extension installed (or click "Reopen in Container" when prompted) and the post-create hook will install Python tooling (`pytest`, `ruff`), the GitHub CLI (`gh`), and the Claude Code CLI (`claude`). Authenticate `gh` and `claude` once the container is up, then run `make validate` to confirm the catalog is clean.

The devcontainer is opt-in -- the standard Quick Start above does not require it. It exists for first-touch contributor onboarding and for reproducing the maintainer's environment across machines.

---

## Featured Skills

| Skill | What it does |
|-------|--------------|
| **Architecture Design** | System decomposition, ADRs, C4 diagrams, and fitness functions. |
| **AI Agent Development** | Build agents with tool use, memory systems, and multi-agent orchestration. |
| **RAG Implementation** | End-to-end RAG pipelines with chunking, embeddings, and evaluation. |
| **API Design** | REST, GraphQL, and gRPC design with versioning and error handling. |
| **Code Review** | A 6-step deep dive (security, performance, logic) before you merge. |
| **Test Gen** | Writes comprehensive unit tests using AAA pattern and mocks. |
| **E2E Testing** | Playwright / Cypress automation with page objects and CI integration. |
| **Compliance** | Checks code against SOC2, GDPR, and ISO standards. |
| **Trend Research** | Researches Reddit / X for the last 30 days to find trends and write prompts. |

The full catalog is at [data/SKILL_INDEX.md](data/SKILL_INDEX.md). Per-category landing pages live under [catalog/skills/](catalog/skills/).

---

## Usage Monitoring

Three complementary ways to track your AI coding usage limits.

### CLI Usage Display (Automatic)

A Stop hook that shows your usage limits directly in the terminal after each Claude Code response. Color-coded and silent when usage is healthy (below 50%).

```
Usage: Session 72% | Weekly 15% | Sonnet 3%  (Session resets in 28m)
```

Installed automatically by the Nexus-Hub installer. Requires `curl` and `jq`.

### VS Code and Cursor Extensions

Monitor your AI coding usage from the editor status bar with a full dashboard. Three separate, independently-installable extensions - one per tool - that install and run side by side:

- **Claude Usage Monitor** (`nexus-hub.claude-usage-monitor`): Claude Code (Anthropic) session and weekly limits, with model and effort recommendations. See [extensions/claude-usage-monitor/](extensions/claude-usage-monitor/).
- **Codex Usage Monitor** (`nexus-hub.codex-usage-monitor`): Codex (ChatGPT / OpenAI) usage, with the plan tier, extra rate-limit windows, a credits line, and throttle / pacing recommendations (periwinkle `#5244BB` progress bars). See [extensions/codex-usage-monitor/](extensions/codex-usage-monitor/).
- **Cursor Usage Monitor** (`nexus-hub.cursor-usage-monitor`): personal Cursor Models and Other Models included-usage meters with on-demand spend context (steel-blue `#4682B4` progress bars), for the Cursor IDE only. This release ships with live fetch disabled entirely - cached or manually-entered dashboard values drive the UI until a bounded, authorized session-reuse probe verifies a safe live path. See [extensions/cursor-usage-monitor/](extensions/cursor-usage-monitor/).

Each shows usage in the status bar with a theme-aware hover and a full dashboard, and makes at most a single outbound call only to your own account. Each reads a usage figure its vendor actually serves, rather than reconstructing one: the Claude and Codex monitors read your local OAuth token and query the vendor's own usage endpoint. None of them scrape a billing website or read browser cookies. A fourth monitor for GitHub billing was withdrawn in v3.18.2 because GitHub serves no such figure and the reconstruction could not be made reliable; see the decision record for the full reasoning. The installer isolates extensions by editor host: the Claude and Codex monitors install only through the VS Code CLI, and the Cursor monitor installs only through the Cursor CLI - never cross-installed. Install any one alone by pointing `code --install-extension` (or `cursor --install-extension`) at its VSIX.

### `/usage` Command

On-demand detailed usage report with model-switching recommendations. Auto-fetches from the API (falls back to manual entry if credentials are unavailable).

---

## Safety and Use in Regulated Industries

Nexus-Hub is built on a **reverse-engineering-first** principle: the catalog ships zero third-party data processors, zero outbound calls from skills / commands / hooks, and zero telemetry. The full threat-model breakdown, industry compatibility matrix, and reporting policy is in [SECURITY.md](SECURITY.md).

Short version:

- **Open-source / hobby / internal commercial software**: green. No restrictions.
- **Regulated industries (healthcare, finance, government, life sciences, automotive, industrial)**: green WITH caveats. Nexus-Hub itself is safe; the caveat is that your chosen LLM provider is where prompts go (use a regulated-cloud option like AWS Bedrock, GCP Vertex AI, Azure OpenAI, or a self-hosted model consistent with your data-protection obligations).
- **Defense / classified / air-gapped**: outside Nexus-Hub's threat model. Do your own assessment.

What Nexus-Hub does NOT do: telemetry, analytics, phone-home, third-party data processors, model downloads, API-key requirements. The MCP Registry Policy in [AGENTS.md](AGENTS.md) categorically rejects search-as-service, embeddings-as-service, scraping-as-service, and generation-as-service. The authoritative classification of every MCP server ever shipped or considered is at [docs/policy/mcp-reverse-engineering-matrix.md](docs/policy/mcp-reverse-engineering-matrix.md).

What is OUT of Nexus-Hub's control: your chosen LLM provider, any MCP server you add outside the Nexus-Hub registry, user-initiated outbound calls (`gh`, `git push`, `curl`), and your own user-authored hooks and rules. See [SECURITY.md](SECURITY.md) section 3 for the full caveats.

To report a security issue: email [benjamin.dourthe@gmail.com](mailto:benjamin.dourthe@gmail.com) or open a private security advisory at [github.com/bendourthe/Nexus-Hub/security](https://github.com/bendourthe/Nexus-Hub/security).

---

## Roadmap

Nexus-Hub evolves in versioned slices. Each upcoming line item below traces to a concrete plan file under `docs/<version>/plans/` (the durable source) and resolves once its `[<version>]` block lands in [CHANGELOG.md](CHANGELOG.md). No star gates, no sponsor tiers, no paid features -- the catalog is reverse-engineering-first and stays that way.

| Focus | Target | Status | Source |
|-------|--------|--------|--------|
| Rename DevAI-Hub to Nexus-Hub, modernize installer with ASCII banner, integrate Nexus brand linkage | v2.0.0 | In progress | [docs/archive/v2/v2.0/plans/nexus-hub-rename.md](docs/archive/v2/v2.0/plans/nexus-hub-rename.md) |
| Cross-OS CI matrix for installer smoke tests (closes the cumulative DF-003 / DF-005 / DF-006 / DF-007 / DF-008 cluster from v1.1.5 known-gaps) | v2.1.0 | Planned | [docs/archive/v1/v1.1/](docs/archive/v1/v1.1/) known-gaps cluster |
| Skill-eval-loop integration into pre-commit (assertion-graded regression guard for high-traffic skills before they ship) | v2.1.0 | Planned | [catalog/skills/workflow/skill-eval-loop/SKILL.md](catalog/skills/workflow/skill-eval-loop/SKILL.md) |
| MCP registry expansion under the existing 5-step policy (reverse-engineer-first; hard-no on search / embeddings / scraping / generation as a service) | continuous | In progress | [docs/policy/mcp-reverse-engineering-matrix.md](docs/policy/mcp-reverse-engineering-matrix.md) |

For a per-release navigation index linking each release to its plan, per-phase history, and known gaps, see [docs/DEVLOG.md](docs/DEVLOG.md); the pre-conversion narrative body is archived at [docs/archive/DEVLOG-v0-v3.17.md](docs/archive/DEVLOG-v0-v3.17.md). For the authoritative Keep-a-Changelog record of what changed in every release, see [CHANGELOG.md](CHANGELOG.md). For the per-version unfinished-work tracker that the next plan reads to decide what carries forward, see `docs/<version>/known-gaps.md`.

---

## Collaboration

Nexus-Hub is a curated open-source project. While pull requests are typically not accepted from outside contributors, suggestions, feedback, and recommendations are more than welcomed. If you have a better prompt, a smarter rule, or a pattern you would like to see in the catalog, please reach out directly:

- **Email**: [benjamin.dourthe@gmail.com](mailto:benjamin.dourthe@gmail.com)
- **GitHub**: [@bendourthe](https://github.com/bendourthe)

I am happy to discuss skill / command / hook proposals, integration ideas for new platforms, or specific use cases -- especially when the proposal aligns with the policy direction of this project (reverse-engineering-first, no third-party data leaks).

---

## License

See [LICENSE](LICENSE).
