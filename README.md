<p align="center"><a href="https://github.com/bendourthe/Nexus-Hub"><img src="assets/nexus-hub-banner.png" alt="Nexus-Hub" width="640" /></a></p>

<p align="center"><em>The Skill Harness for Every AI Coding Assistant.</em></p>

# Nexus-Hub

<!-- nexus-hub-version: 3.14.6 -->

Nexus-Hub is the upstream skill catalog for AI coding assistants: 267 skills, 16 commands, 28 hooks, 23 agents, and 4 language rule families. It installs in one step on Windows, macOS, and Linux, and it works the same across Claude Code, OpenAI Codex, Gemini (via Antigravity), GitHub Copilot, Cursor, GitHub CLI, and the sibling Nexus desktop app and VS Code extension. The catalog is reverse-engineering-first by policy: zero third-party data processors, zero outbound calls from skills / commands / hooks, zero telemetry.

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

- **Nexus-Hub (this repo)** is the catalog: 267 curated skills, 16 commands, 28 hooks, 23 agents, 4 rule families, plus 4 internal MCP servers (`nexus-skill-server`, `nexus-code-search`, `nexus-web-fetch`, `nexus-context-compressor`). It is content-only, platform-agnostic, and shipped via an installer that writes to `~/.nexus-hub/` and into each AI assistant's per-platform config locations.
- **Nexus** is a local-first desktop AI Studio that consumes Nexus-Hub as its skill feed. Nexus's `AGENTS.md` names this repo as "the only external project we deliberately link to" -- the upstream feed for its skill harness.

The two projects are designed to be useful independently: you can install Nexus-Hub into any supported agent platform without touching Nexus, and Nexus can run with or without the upstream catalog wired in. The combination is what gives a single curated skill set to every agent surface a developer touches: terminal, IDE, desktop app, and CLI.

---

## What's New in v3.14.6

v3.14.6 fixes the Codex Usage Monitor's auto-fetch, unifies both usage monitors' settings UX, and modernizes the installer's console output (no catalog change; counts unchanged). The **Codex Usage Monitor** now pulls your real usage automatically like the Claude monitor does: the root cause was a schema mismatch (the mapper read `rate_limits`/`primary`/`secondary`, but the live endpoint nests the windows under `rate_limit`/`primary_window`/`secondary_window`), so a weekly-only plan came up empty. The mapper now reads the verified schema and classifies each window by its real duration, and the manual-entry fallback is removed (auto-fetch is the path; a genuine failure shows an honest diagnostic). **Both monitors** drop the status-bar gear icon and render **Settings inline under the dashboard** (toggled by the dashboard gear, state-persisted, fonts unified with the dashboard) instead of opening a separate panel, and the status-bar items stay grouped (Copilot no longer wedges between them). The **installer log** is flattened to single-level `UPPERCASE` sections, "Usage Monitors" is renamed **VS CODE EXTENSIONS**, skill discovery + git hook + report templates are grouped under **CROSS-PLATFORM TOOLS**, project seeding is folded under **INSTALL VERIFICATION**, and the stray blank-line spacing is cleaned up. Catalog: **267 skills**, **16 commands**, **28 hooks**.

## What's New in v3.14.5

v3.14.5 modernizes the installer output, fixes the Codex Usage Monitor, and makes per-release platform-contract verification a hard gate (no catalog change; counts unchanged). The **installer** now prints a per-platform checklist in a fixed surface order (Core Files / Skills / Commands / Agents / Rules / Hooks / Core Settings) with real install paths, groups undetected platforms into one "NOT DETECTED (skipped)" section instead of reporting them as installed, colors every vendor, tightens end-of-run spacing, and splits the VS Code utilities into Anthropic (Claude Usage Monitor) and OpenAI (Codex Usage Monitor) sections. The **Codex Usage Monitor** gains a manual-entry fallback (so it is useful even when the undocumented usage endpoint can't be read), an honest and actionable empty state, a theme-adaptive dashboard tab icon, correct status-bar ordering across both extensions ([Claude usage][Claude gear][Codex usage][Codex gear]), and a `compactStatusBar` toggle. A new **mandatory contract-verification gate** consolidates the "expected read-paths per platform" data into one machine-readable `docs/policy/platform-read-contracts.json` (consumed by both the code-vs-contract checker and the runtime `nexus-hub verify` pass) and adds `check_platform_contract_freshness.py`, which fails `make validate` and CI unless the contract was re-verified for the release being cut. That release-time re-verification web-checked all 13 platforms and fixed three dead-path installer bugs (**OpenCode** `~/.config/opencode/`, **Kimi** `.kimi/AGENTS.md`, **OpenClaw** `~/.openclaw/workspace/`); the additive drift it surfaced (Copilot / Cursor / Codex / OpenCode have gained native skills / agents / hooks surfaces) is routed to the v3.15.0 platform-parity release. Catalog: **267 skills**, **16 commands**, **28 hooks**.

## What's New in v3.14.3

v3.14.3 fixes `/presentify` end-to-end and reworks its design intake (no catalog change; counts unchanged). First, it restores skill loading: `document-to-interactive-html` (and 46 other skills) carried an unquoted `description` frontmatter value containing a `: ` sequence that broke strict YAML parsing, so the skill silently failed to load with "Unknown skill" - the values are now quoted, a strict-YAML gate in `validate_skills.py` prevents regression, and both installers now flatten skills for Claude to the discoverable `~/.claude/skills/<name>/` layout instead of an undiscoverable category-nested copy. On top of that, `/presentify` now asks its four high-level design questions - style, layout, interactivity, imagery - in a single batched round UP FRONT before any document is read (instead of one menu at a time mid-pipeline), and never pre-answers a choice from a recalled memory or saved preference. The imagery choice now prefers real license-free stock and minimizes AI, and offers gated license-free stock video (Pexels key + consent, degrading to images-only otherwise), reconciling the old "video out of scope" wording so source-embedded media stays ignored while output-side stock video is supported. And a new guided `nexus-hub setup-media` bring-your-own-key flow stores a free Pexels key securely under `~/.nexus-hub/` (hidden prompt, mode 0600) so stock video "just works" - stock images still need no setup.

## What's New in v3.14.2

v3.14.2 is an internal convention fix (no catalog change; counts unchanged). It closes a systemic flaw where a `/compare` report and the `/plan from-comparison` plan it seeds could land in different version directories. A comparison now declares an `Adoption target: vX.Y.Z` and is versioned and placed by the release that will ADOPT it rather than the authoring cycle (Fix A); `/plan from-comparison` reads that field and co-locates the generated plan in the same version tree, degrading gracefully for comparisons authored before the convention (Fix B); and the `documentation-consistency` audit plus a dedicated CI workflow flag any comparison/plan version-directory drift so the misplacement cannot silently recur (Fix C). All edits are instruction-level (command and skill-body changes that auto-distribute via folder copy), with `docs/archive/**` and prior-major trees grandfathered.

## What's New in v3.14.4

v3.14.4 splits the usage monitor into two separate VS Code extensions. The v3.14.0 build had folded Codex monitoring into the Claude extension behind a provider switch (renaming it "Claude & Codex Usage Monitor"), which mislabeled the Claude monitor and buried Codex behind a setting. It is now two independently-installable, branded extensions that run side by side: the **Claude Usage Monitor** (`nexus-hub.claude-usage-monitor`, reverted to Claude Code only) and a new **Codex Usage Monitor** (`nexus-hub.codex-usage-monitor`) with its own identity, icon, status-bar glyph, and periwinkle `#5244BB` progress bars, tracking what Codex exposes (the plan tier in place of a model, extra rate-limit windows, a credits line) with throttle / pace / wait / rotate recommendations. The two share no extension id, command, storage key, or view, so installing one never affects the other. Both installers build and install both; each has its own path-filtered CI workflow and dependabot entry. Catalog counts unchanged: **267 skills**, **16 commands**, **28 hooks**.

## What's New in v3.14.1

v3.14.1 is an installer hotfix (no catalog change; counts unchanged). A global install run from an arbitrary working directory (including an elevated `C:\Windows\System32` prompt) no longer emits a `PermissionError [WinError 5]` traceback for each integration and now writes its install manifest under `~/.nexus-hub/` regardless of the working directory, with a manifest-write failure degrading to a warning instead of aborting the run. And re-running the installer (or `nexus-hub upgrade`) now unregisters the orphaned DevAI-Hub "Claude Code Auth Monitor" Windows scheduled task and sweeps its leftover `run-auth-monitor.vbs` launcher, stopping the recurring "Can not find script file" popup. Users who cannot re-run yet can remove the task manually with `Unregister-ScheduledTask -TaskName "Claude Code Auth Monitor" -Confirm:$false`. Both fixes are installer-side only (in `scripts/lib/integrations/`), so they auto-distribute with no installer copy-step edit and no platform-template change.

## What's New in v3.14.0

v3.14.0 is the codex-lb adoption release: it brings a directly-requested product build plus four skill-native agentic-review disciplines reverse-engineered from an external Codex workflow, with zero new outbound calls, dependencies, or credentials in the catalog. The headline build is the **Codex Usage Monitor**: the `claude-usage-monitor` VS Code extension (independently bumped to 0.7.0) is generalized behind a `UsageProvider` interface and gains a second provider for Codex (ChatGPT / OpenAI) that reads the local Codex app OAuth token and renders account usage in the same status-bar, tooltip, dashboard, and warning UI as Claude, with its single outbound call going only to the user's own account endpoint. On the catalog side, a **skill-native review and verification cluster** adds a `review-trapdoors` skill and convention (a project's curated list of recurring, project-specific review blockers, each applied as a gate) and a machine-checkable **merge-readiness contract** in `quality-gate-definitions`, and folds a PR/CI-state evidence discipline into `verification-before-completion`. A **spec/context split** convention extends `spec-driven-development` with a normative `spec.md` (testable requirements only) separated from free-form context, plus a spec-as-merge-gate rule. A **declarative skill-activation ruleset** (`skill-rules.json`) with three opt-in, fail-open hooks gives the model-judgment triggering a deterministic, suggest-by-default backstop. And a **cross-model review loop** recipe in `cross-model-orchestrator` documents a vendor-neutral, loop-until-clean review flow. Catalog: **267 skills** (+1: `review-trapdoors`), **16 commands**, **28 hooks**.

## What's New in v3.13.0

v3.13.0 is the presentify reach-and-voice release: `/presentify` and its `document-to-interactive-html` skill now ingest almost anything and give the output a professional, journalistic visual voice - without ever breaking the single-file, offline, zero-external-request guarantee. **Universal ingestion**: beyond the four document formats, the extractor now reads source code and config, Markdown / plain text, CSV / TSV, and standalone images, and can take a whole directory or repository (walked recursively, with ignore rules, a best-effort `.gitignore` matcher, a binary sniff, and file / byte caps) - a repo becomes a synthesized overview, a navigable file tree, README-first ordering, and code grouped by directory. Dominant source visuals keep their **prominence** (a hero stays a hero, never flattened into a thumbnail grid), and a new `--layout` control picks the output **aspect** (full-width / standard / portrait). **Tiered imagery** gives the output its designed look: Tier 1 (the always-on, zero-outbound default) authors original procedural visuals as inline SVG / CSS (color fields, editorial devices, generative textures); Tier 2 (opt-in, consent-gated) fetches license-free, free-for-commercial-use stock images from Openverse / Wikimedia / Pexels at build time; and Tier 3 (opt-in, LOCAL-only) generates images with a local commercially-clean model (a hosted generation API is a policy hard-no). Every fetched or generated asset is license-verified, base64-embedded so the page still opens offline, and recorded in a visible credits block. A new **interactivity level** (restrained / balanced / rich scrollytelling) tunes how the page responds, always reduced-motion-guarded. Everything stays local-only with zero telemetry; catalog counts unchanged: **266 skills**, **16 commands**, **25 hooks**.

## What's New in v3.12.1

v3.12.1 makes every Nexus-Hub skill and command actually discoverable in the new ChatGPT desktop app (Chat + Work + Codex) and the Antigravity IDE, and hardens the install against future platform format drift. Codex and the desktop app discover skills one level deep, but the installer was copying the catalog two levels deep (buried under a category folder), so nothing registered; skills are now flattened into `~/.codex/skills/` and the cross-tool `~/.agents/skills/`, and every command surfaces both as a slash command and as a reusable skill (`$presentify`, `$implement`, ...). Antigravity's global content now lands where the IDE actually reads it (`~/.gemini/config/skills/`, `~/.gemini/config/global_workflows/`, `~/.gemini/GEMINI.md`) instead of an unread path. The same one-level flattening plus command-skills fix extends to Claude, Gemini, Gemini CLI, OpenCode, and Nexus-AI, whose native skill folders were silently broken by the nested layout. A new living read-contract (`docs/policy/platform-read-contracts.md`) plus a three-layer verification gate keeps it correct: a deterministic code-vs-contract check in `make validate`, a corrected `nexus-hub verify`, and a new `/update release` step that re-verifies each platform's current discovery format via web search every release. Catalog: **266 skills** (+1: `platform-contract-verification`), **16 commands**, **25 hooks**.

## What's New in v3.12.0

v3.12.0 is the presentify fidelity-and-variety overhaul: `/presentify` and its `document-to-interactive-html` skill no longer drop source visuals, no longer guess at figures, no longer ship static-feeling pages, and no longer converge to one look. The extractor now captures PDF embedded images (with repeated-asset dedup and caption pairing), detects and rasterizes vector-figure regions (plots, maps, diagrams - the norm in decks exported to PDF), reads scanned / image-only PDFs through a two-tier path (local OCR via optional `rapidocr-onnxruntime`/`pytesseract` with per-block confidence, plus an always-on full-page image for agent-vision reading - zero installed OCR engines still means zero content loss), recurses PPTX grouped shapes, extracts native PPTX/DOCX chart objects with their real series values, and emits a per-source coverage manifest that the new COVERAGE RECONCILIATION gate audits: every visual must end rendered, reconstructed, or explicitly skipped with a reason. Data-bearing figures go through a new figure-reconstruction protocol - classification, an auditable read-the-figure worksheet, fidelity cross-checks, and a three-tier confidence gate under which low-confidence figures ship as pan/zoom originals, never invented numbers. Every run now carries a five-point minimum interaction budget (active-state nav, scroll reveals, hover/focus affordances, lightboxes on every non-decorative image, one signature interaction), and a new stdlib design-entropy engine (`design_seed.py`: 12 hue families x light/dark, preset-constrained pools, seeded rolls, a persisted run history with a 2-of-3-axes rejection rule) makes same-preset reruns provably different. A committed worked example replays the original failing case (a PDF saved from PowerPoint) twice with the same preset: ground-truth-exact reconstruction, 0 unaccounted visuals, and two unmistakably different designs. A path-filtered CI workflow now guards the extractor. Catalog counts unchanged: **265 skills**, **16 commands**, **25 hooks**.

v3.11.4 is a small catalog patch bundling two changes. The Nexus-AI integration now installs the entire catalog under `~/.nexus-ai/catalog/` instead of the `~/.nexus-ai/` root - reserving the root for the Nexus-AI app's own data home (settings, MCP config, model weights, sessions, credentials) so a catalog refresh can wipe-and-refetch its own subtree without risking app data - and writes a timestamp-free `nexus-hub-version.json` at the catalog root that gives the desktop app a first-class update-detection contract (installed version plus the public releases endpoints). Separately, the `docs-layout-refactor` skill (1.2.0 -> 1.3.0) gains universal handling for cross-cutting, non-versioned documentation subtrees: it now recognizes the widely-adopted standards (architecture decision records, RFCs, specifications, governance policy, the Diataxis content quartet, runbooks, and static-site-generator output) as one conservative disposition class that is never version-archived or reclassified by semantic content, giving `/plan` and `/implement` a canonical rule instead of inventing one. No catalog change; the v3.11.0 feature set below ships unchanged.

v3.11.3 is an extension-only patch: it relabels the Claude Usage Monitor usage-warning's primary dismiss button from "Cancel" to "OK", which reads correctly as acknowledging and closing the warning. The warning itself (added in v3.11.2) is a compact WebviewView in its own narrow activity-bar container that reveals automatically when a usage threshold is crossed - polling tightens to about once a minute as usage nears a threshold, so the warning is timely - and dismisses cleanly, rather than a notification toast or a full editor tab. Extension 0.6.1 -> 0.6.2. No catalog change; the v3.11.0 feature set below ships unchanged.

v3.11.0 turns a set of implicit good practices into command-enforced workflow defaults across the catalog. It standardizes the per-version docs layout on a canonical `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` scheme, adds project-bootstrap governance, makes every generated plan end with a mandatory architecture-refactor + known-gaps + CI/CD phase, hardens `/compare` and `/presentify`, verifies that every install actually surfaces the catalog on every platform, and migrates the Nexus-Hub repo itself to follow all of it. It also lands four reverse-engineer-first skill-pack adoptions (six new skills plus several skill-native enrichments). Catalog: **265 skills**, **16 commands**, **25 hooks**.

Highlights:

- **Command-enforced workflow governance** (v3.11.0): `/setup` detects and bootstraps git, a `vX.Y.Z` version, a `develop` + feat/fix/refactor>develop>main branch model, and the per-version docs tree; `/describe` and `/review` report a Project-health block and offer a `/setup` handoff. Backed by two reconstituted delegate skills (`setup-project`, `analyze-codebase`) and the reconstituted `implement-phase` skill.
- **Mandatory final refactor phase** (v3.11.0): every plan `/plan` generates now ends with an architecture-refactor + known-gaps-reconciliation + CI/CD-optimize phase, which `/implement` runs on a plan's final phase (even for plans that predate the rule) and `/update release` enforces. `project-refactor` gains empty-dir, duplicate, orphan, and structure-complexity detection.
- **Canonical docs-layout scheme** (v3.11.0): active docs at `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` and archive at `docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/`, each with `plans/` and `comparisons/` subdirs; patch releases share their minor dir with release-prefixed artifact filenames.
- **Command robustness** (v3.11.0): `/compare` runs a source-security scan (prompt-injection / malicious-instruction / supply-chain) before ingesting any external source and files reports under `comparisons/`; `/presentify` renders, screenshots, and visually assesses its own output, iterating on graphic defects.
- **Cross-platform distribution robustness** (v3.11.0): every install is verified against each platform's real read-path (not assumed from a successful copy), project-only surfaces auto-seed, a post-install `nexus-hub doctor` reports PASS / NEEDS-ACTION per platform, and a cross-OS CI `install-smoke` job fails a PR if any read-path would go empty.
- **Skill-pack adoptions** (v3.11.0): four reverse-engineer-first adoptions land six new skills and several enrichments - `implementation-convergence` (post-implementation code-vs-plan gap check behind a new `/spec converge` scope) and `label-gated-agent-pipelines` (human-gated CI agent pipeline) from the spec-kit adoption; `youtube-transcript` (local `yt-dlp` captions) plus a portable research-brief technique and an opt-in grill-me mode from the davidondrej adoption; local-agent-hijack recognition across `prompt-injection-defense` / `agent-access-policy` / `ai-attack-patterns` and a reproducible-benchmark-receipt discipline from the t3mp3st adoption; and an optical / image-token compression doctrine from the pxpipe adoption. GitHub Copilot also gains an opt-in native `.github/skills/` project surface.
- **Claude Usage Monitor v0.5.5 -- Extra Credits in the hover tooltip** (v3.10.3): the status-bar hover tooltip shows an Extra Credits section in the same order as the dashboard. When extra credit is available it renders a utilization bar plus "$X / $Y used this month" and the monthly reset date; when the account has no extra-credit limit it reads "No extra credit available on your account".
- **`egress-redaction` defensive skill**: a typed sensitive-data / PII taxonomy with a per-category policy action (BLOCK / REDACT / HASH / PASS) applied before any artifact crosses a trust boundary (a cross-model handoff, a context pack, a log, an external send), with a default-policy table and a per-egress-event rule.
- **`prompt-injection-defense` defensive skill**: the recognition-and-posture counterpart to `ai-attack-patterns` -- instruction-origin discipline, untrusted-content fencing, tool-output skepticism, indirect-injection recognition cues, and a safe-response rule.
- **`nexus-hub verify` supply-chain command**: recomputes installed-file SHA-256 and diffs against a release-published `MANIFEST.sha256`, reporting OK / MODIFIED / MISSING / EXTRA per file with a single PASS / FAIL. Strictly local and read-only (stdlib only) -- no network call, no credential, no new dependency.
- **Agent-setup grade + regression diff**: `harness_audit.py` gains an explainable 1-100 setup grade across six weighted dimensions and a cross-snapshot regression diff (advisory by default; gates only with `--fail-on-regression`), surfaced through `skill-stocktake`.
- **Iterative competitive-generation**: `competitive-generation` gains a hill-climbing / co-evolution section -- run the competition over multiple rounds seeded by the previous winner, with a no-progress stopping rule and a token caution.
- **Two advisory worker-check hooks**: `test-gap-notice` (flags source edits with no companion test) and `dependency-staleness-notice` (flags dependency-manifest edits with the matching audit command) -- event-driven, advisory-only, disableable, never a daemon.

See [CHANGELOG.md](CHANGELOG.md) for the full v3.11.0 entry and the complete release history.

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

- **Globally**: your user profile has all 267 skills, 16 commands, 28 hooks, 23 agents, plus Gemini and Codex instructions.
- **Locally**: your project has `copilot-instructions.md` and `AGENTS.md` tailored to your language.

**Power-user flags**: `--workspace <path>` installs into a single repo instead of globally; `--platforms <comma-list>` limits the install to a subset of assistants; `--yes` runs fully unattended (refreshes managed files with no prompt -- ideal for CI). Prefer to clone first? `git clone` the repo and run `./install.sh` (macOS / Linux) or `install.bat` (Windows) -- the in-repo path still works exactly as before.

### Keeping it current

Run `nexus-hub upgrade` -- it reports your installed version against the latest, shows a short what's-new summary, and updates in place on confirmation. Re-running the install command above works too; the installer is idempotent.

### Verifying your install

Run `nexus-hub verify` to confirm your installed catalog matches the published release. It recomputes the SHA-256 of every file in the catalog tree and diffs the result against the `MANIFEST.sha256` that ships with each release, reporting any file that is modified, missing, or unexpected, then a single `verify: PASS` or `verify: FAIL` line. It is strictly local: it reads only local files, makes no network call, needs no credential, and adds no dependency.

What this does and does not prove: `verify` detects on-disk tampering or corruption AFTER install, relative to the published catalog. It is trustworthy to the extent the manifest itself came from the release you trust (it rides inside the same signed release tag the installer pulls from). It is NOT a code signature and NOT a substitute for verifying the download channel -- an attacker who can rewrite both a file and the manifest in the same tree defeats it. Use it to catch accidental corruption and post-install drift, not to establish first-trust in the bytes.

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

1. Run `/update release` -- orchestrates version detection, layout cleanup, `.gitignore` audit, version-bump across all configuration files, CHANGELOG migration, doc sync, and DEVLOG entry.
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

Three complementary ways to track your Claude Code usage limits.

### CLI Usage Display (Automatic)

A Stop hook that shows your usage limits directly in the terminal after each Claude Code response. Color-coded and silent when usage is healthy (below 50%).

```
Usage: Session 72% | Weekly 15% | Sonnet 3%  (Session resets in 28m)
```

Installed automatically by the Nexus-Hub installer. Requires `curl` and `jq`.

### VS Code Extensions

Monitor your AI coding usage from the VS Code status bar with a full dashboard. Two separate, independently-installable extensions - one per tool - that install and run side by side:

- **Claude Usage Monitor** (`nexus-hub.claude-usage-monitor`): Claude Code (Anthropic) session and weekly limits, with model and effort recommendations. See [extensions/claude-usage-monitor/](extensions/claude-usage-monitor/).
- **Codex Usage Monitor** (`nexus-hub.codex-usage-monitor`): Codex (ChatGPT / OpenAI) usage, with the plan tier, extra rate-limit windows, a credits line, and throttle / pacing recommendations (periwinkle `#5244BB` progress bars). See [extensions/codex-usage-monitor/](extensions/codex-usage-monitor/).

Both read your local OAuth token, show usage in the status bar with a theme-aware SVG hover tooltip and a full dashboard, and make a single outbound call only to your own account. The installer builds and installs both; install either one alone by pointing `code --install-extension` at its VSIX.

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

For narrative-style updates on what changed and why, see [docs/DEVLOG.md](docs/DEVLOG.md). For the formal Keep-a-Changelog log of every release, see [CHANGELOG.md](CHANGELOG.md). For the per-version unfinished-work tracker that the next plan reads to decide what carries forward, see `docs/<version>/known-gaps.md`.

---

## Collaboration

Nexus-Hub is a curated open-source project. While pull requests are typically not accepted from outside contributors, suggestions, feedback, and recommendations are more than welcomed. If you have a better prompt, a smarter rule, or a pattern you would like to see in the catalog, please reach out directly:

- **Email**: [benjamin.dourthe@gmail.com](mailto:benjamin.dourthe@gmail.com)
- **GitHub**: [@bendourthe](https://github.com/bendourthe)

I am happy to discuss skill / command / hook proposals, integration ideas for new platforms, or specific use cases -- especially when the proposal aligns with the policy direction of this project (reverse-engineering-first, no third-party data leaks).

---

## License

See [LICENSE](LICENSE).
