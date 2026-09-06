# Comparison: Nexus-Hub vs davidondrej/skills

**Source**: [`davidondrej/skills`](https://github.com/davidondrej/skills) ("David Ondrej's official Agent Skills")
**Source type**: Git repository (skills-only collection, so the 11-dimension comparison is scoped to the Skills / Capabilities dimension)
**Comparison date**: 2026-07-06
**Nexus-Hub baseline**: v3.10.0 (259 skills, 16 commands, 25 hooks, 23 agents)
**Analysis target**: v3.11.0 adoption cycle
**License**: MIT. The external repo is a flat personal collection of 28 `SKILL.md` files with no installer, no registry, and no multi-platform distribution layer.

---

## Executive Summary

The two projects are different categories of artifact, and that framing governs every conclusion below.

- **davidondrej/skills is a flat personal skill pack.** 28 skills in five category folders, each a single `SKILL.md`, tuned to one operator's personal stack: the cmux terminal multiplexer, the Pi agent, Hermes, OpenAI Codex, and a paid third-party research API (DeepAPI, `deepapi.co`). Several skills read secrets from `~/.zshrc` and make outbound calls. There is no distribution mechanism beyond a personal "push to my private GitHub repo" skill.
- **Nexus-Hub is a governed, local-first template catalog.** It ships 259 skills plus commands, hooks, agents, and rules through an installer into 14+ AI assistants, under a deliberate reverse-engineer-first, zero-outbound-by-default MCP Registry Policy (`AGENTS.md`).

Because of that mismatch, most of the 28 external skills are **not adoptable**: they are bound to tools Nexus-Hub does not target (cmux, Pi, Hermes, Codex `/goal`), they depend on a paid scraping/research API that the MCP Registry Policy categorically forbids (deepapi, deep-research), they encode one person's writing voice (copywriting), or Nexus-Hub already covers the same capability more comprehensively (skill distribution, git push, agent scheduling, browser control, skill-authoring doctrine).

What **is** adoptable is short and curated:

1. **A YouTube-transcript capability (the one clean gap).** Nexus-Hub has zero YouTube-transcript coverage today, confirmed by a catalog-wide search returning no `yt-dlp` / `youtube.com` matches. The external skill's primary path is DeepAPI (a scraping-as-service hard-no), but its **local `yt-dlp` fallback is fully reverse-engineerable**: a local CLI that pulls public captions with no API key and no query text leaving the machine. This is the flagship candidate.
2. **A single-paragraph research-brief technique.** The `research-prompt` skill is a clean, LLM-native prompt-engineering artifact (a self-contained one-paragraph brief with numbered sub-questions, a source hierarchy, contradiction handling, a completion bar, and a per-finding output format). Its execution step depends on DeepAPI (declined), but the brief-authoring method reverse-engineers to zero code and overlaps with, and could enrich, the existing `/research` flow and `prompt-engineering`.
3. **An optional interactive "grill me" plan-stress-testing mode.** A relentless one-question-at-a-time interview that walks each branch of a decision tree. It carries a genuine tension with Nexus-Hub's stated "batch, not ping-pong" clarifying-question convention, so it is a bounded interactive-mode enrichment, not a wholesale adoption.

Everything else is already covered by an existing Nexus-Hub skill (and should be preserved, not "adopted"), is tool-specific to an external stack, is a paid-API dependency the policy forbids, or is declined on policy grounds (see `fable-safe-prompt` below).

A non-adoption meta-finding worth recording: the external skills use extremely **pushy descriptions** with verbatim trigger phrases and explicit differentiators. That independently validates Nexus-Hub's own "combat undertriggering" description doctrine in `AGENTS.md`; it is convergent evidence for a rule Nexus-Hub already follows, not a new thing to adopt.

---

## Step 1: Source Type and Scope

The source URL contains `github.com`, so it classifies as a **Git repository**. Unlike a full application repo, this repository contains only a `skills/` tree (plus `README.md`, `LICENSE`, `.gitignore`). Dimensions 1 through 11 that concern stack, CI/CD, testing, and developer experience are therefore not meaningfully present in the source, so the comparison is scoped to **Dimension 5 (Skills and Capabilities)**, evaluated skill by skill. The dimension summary below records that scoping explicitly.

| # | Dimension | davidondrej/skills | Nexus-Hub | Bucket |
|---|-----------|--------------------|-----------|--------|
| 1 | Project Identity | Personal skill pack; MIT; flat `SKILL.md` collection | Governed template catalog; installer-distributed; reverse-engineer-first policy | `~` |
| 2 | Technology Stack | Markdown skills + inline bash/curl/python snippets; no build | Python + Bash/PowerShell installers, Markdown catalog, JSON registries, `make validate/lint/test` | `~` |
| 3 | AI Assistant Configuration | Targets Codex, Claude Code, Pi, Hermes via symlinked skill folders | 259 skills / 16 commands / 25 hooks / 23 agents distributed to 14+ platforms | `~` |
| 4 | Project Structure | `skills/<category>/<name>/SKILL.md`, 5 categories, 28 skills | `catalog/`, `data/`, `scripts/`, `templates/`, `docs/<version>/`, three-tier loading model | `~` |
| 5 | **Skills and Capabilities** | **28 skills, personal-stack-tuned, some paid-API-backed** | **259 documented skills with binary Verification + Common Rationalizations** | **see per-skill table** |
| 6 | Commands and Automation | None (skills only) | 16 slash commands plus permanent aliases | `=` |
| 7 | CI/CD and Hooks | None | 25 tool-event hooks; `make validate/lint/test` | `=` |
| 8 | Documentation | `README.md` only | Per-version `docs/`, CHANGELOG, DEVLOG, markdown-style governance, interactive guide | `=` |
| 9 | Testing Strategy | None | `test-*` skills, pytest hook suite, 80% coverage doctrine | `=` |
| 10 | Security Posture | Reads secrets from `~/.zshrc`; several outbound calls; one guardrail-evasion skill | Reverse-engineer-first MCP policy; `secret-scan` / `large-file-guard` hooks; security + security-operations families | `~` |
| 11 | Developer Experience | Personal "push to my private repo" workflow | One-line bootstrap installer, no-prompt global install, `nexus-hub upgrade` | `~` |

The interesting analysis is the per-skill classification below, not the dimension table.

---

## Steps 2 and 3: Per-Skill Inventory and Difference Classification

All 28 external skills, each mapped to its closest Nexus-Hub equivalent and classified. Status legend: **Missing** (Nexus-Hub lacks it), **Partial** (Nexus-Hub does something adjacent with a gap), **Covered** (Nexus-Hub already does this, often more comprehensively), **Not applicable** (tool-specific, personal, or policy-declined).

| # | External skill | Category | Closest Nexus-Hub equivalent | Status |
|---|----------------|----------|------------------------------|--------|
| 1 | `agent-self-scheduling` | agent-orchestration | `loop-engineering`, `/loop`, `temporal-orchestration`, `agent-orchestration-primitives` | Covered (platform-agnostic) |
| 2 | `cmux` | agent-orchestration | none (cmux is a macOS terminal multiplexer Nexus-Hub does not target) | Not applicable (tool-specific) |
| 3 | `codex-goal-loop` | agent-orchestration | `loop-engineering` (the plan-act-test-review loop is already platform-agnostic doctrine) | Covered (pattern), tool-specific doc |
| 4 | `fable-safe-prompt` | agent-orchestration | none by design | Not applicable (declined on policy grounds, see below) |
| 5 | `handoff` | agent-orchestration | `session-history`, `context-pack-builder`, `/session wrap` | Partial |
| 6 | `markdown-rendering` | agent-orchestration | none (cmux-specific blank-render bug workaround) | Not applicable (tool-specific) |
| 7 | `run-deep-swe` | agent-orchestration | `ai-output-evaluation`, `skill-eval-loop`, `model-routing` | Not applicable (vendor API + niche benchmark) |
| 8 | `anti-sleep` | ops-and-setup | none (macOS `caffeinate` one-liner) | Not applicable (trivial OS command) |
| 9 | `pi-custom-model` | ops-and-setup | `multi-provider-ai`, `model-routing` | Not applicable (Pi-agent-specific) |
| 10 | `setup-help` | ops-and-setup | `/setup` (project bootstrap) | Partial (guided-walkthrough UX gap) |
| 11 | `vps-server-management` | ops-and-setup | `sre-engineer`, `network-engineer`, `platform-engineer` | Partial (personal-ops, low catalog value) |
| 12 | `browser-harness` | research-and-web | `browser-testing-with-devtools`, `e2e-testing-automation` | Covered |
| 13 | `deep-research` | research-and-web | `/research`, the `deep-research` harness, `deep-research-compilation` | Covered workflow; DeepAPI dependency declined |
| 14 | `deepapi` | research-and-web | none by design | Not applicable (scraping-as-service hard-no) |
| 15 | `pi-web-search` | research-and-web | native web tools per platform | Not applicable (Pi-agent-specific) |
| 16 | `research-prompt` | research-and-web | `prompt-engineering`, `trend-research`, the `/research` prompt-build step | Partial (standalone brief artifact) |
| 17 | `youtube-transcript` | research-and-web | **none (confirmed: zero `yt-dlp` / `youtube.com` matches in the catalog)** | **Missing** |
| 18 | `distribute-skill-to-all-agents` | skill-authoring | the installer (distributes to 14+ platforms) | Covered (far more comprehensively) |
| 19 | `effective-agent-skills` | skill-authoring | `skill-create`, `skill-description-authoring`, `create-custom-command`, `AGENTS.md`, `skill-stocktake` | Covered |
| 20 | `folder-specific-claude-and-agents-md` | skill-authoring | `nexus-hub init` project surfaces, `/memory`, CLAUDE.md scaffolding | Partial (subdirectory-scoped context files) |
| 21 | `push-skill-to-github` | skill-authoring | `code-commit-workflow`, `git-branching-workflow`, `/update release` | Covered |
| 22 | `brain-to-docs` | thinking-and-docs | `doc-coauthoring`, `idea-refine`, `architecture-decision-record` | Partial (conflict, see below) |
| 23 | `copywriting` | thinking-and-docs | `brand-styling`, `writing-editing`, `technical-writer` | Not applicable (one person's voice) |
| 24 | `grill-me` | thinking-and-docs | `idea-refine`, `/spec clarify`, `ambiguity-detector`, `plan-review` | Partial (interactive-mode gap) |
| 25 | `interview-style-doc-building` | thinking-and-docs | `doc-coauthoring`, `spec-driven-development` | Partial (conflict, see below) |
| 26 | `read-all-adrs` | thinking-and-docs | `architecture-decision-record` (authoring only) | Partial (context-loading helper) |
| 27 | `short` | thinking-and-docs | `context-compression`, `context-optimization`, the CLAUDE.md output-minimization rules | Covered |
| 28 | `teach` | thinking-and-docs | `session-teach-back` (the inverse: quiz the human), `context-modes` | Partial (different angle, low value) |

Tally: 1 Missing, 9 Partial, 6 Covered, 12 Not applicable.

---

## Step 4: Adoption Candidates (value / effort, pre-gate)

Only the Missing and Partial rows are candidates. The Covered rows are Nexus-Hub strengths to preserve, and the Not-applicable rows go straight to the NOT-recommended list. Priorities here are provisional; the Step 5 security and reverse-engineering gate re-sequences them.

| ID | Candidate | Gap vs Nexus-Hub | Value | Effort | P-tier (pre-gate) |
|----|-----------|-------------------|-------|--------|-------------------|
| C1 | YouTube transcript via local `yt-dlp` | Real: no YouTube-transcript capability anywhere in the catalog | High | Med | P1 |
| C2 | Single-paragraph research-brief technique | Partial: `/research` builds prompts internally, but there is no reusable standalone brief artifact | Med | Low | P2 |
| C3 | Interactive "grill me" plan-stress-test mode | Partial: clarify/ambiguity skills exist, but no relentless interactive decision-tree grill | Med | Low | P2 |
| C4 | Guided step-by-step `setup-help` walkthrough | Partial: `/setup` bootstraps a project; no "one step now, remaining steps listed" guided mode | Low | Low | P3 |
| C5 | Folder-scoped CLAUDE.md / AGENTS.md helper | Partial: `nexus-hub init` writes root surfaces; no subdirectory-scoped context-file helper | Low | Low | P3 |
| C6 | Read-all-ADRs context loader | Partial: Nexus-Hub authors ADRs but has no "load every ADR for context" helper | Low | Low | P3 |

Deliberately curated out even though they are Partial:

- `handoff` (row 5) is already served by `session-history` plus `context-pack-builder` plus `/session wrap`; a lighter copy-paste variant is not worth a new skill.
- `vps-server-management` (row 11) is personal remote-ops with low general-catalog value and overlaps the infrastructure family.
- `teach` (row 28) overlaps `session-teach-back` from the opposite direction and adds little.
- `brain-to-docs` and `interview-style-doc-building` (rows 22, 25) are addressed as a **conflict** in Step 7 rather than as adoptions, because their one-question-at-a-time loop contradicts a stated Nexus-Hub convention.

---

## Step 5: Security and Reverse-Engineering Assessment (MANDATORY)

### 5.1 Threat model comparison

| Factor | davidondrej/skills | Nexus-Hub |
|--------|--------------------|-----------|
| New runtime dependencies | `yt-dlp`, `deno`, `python3`, `jq`, `uuidgen`, `caffeinate`, cmux, Pi, Hermes (per skill) | None required by the catalog itself |
| Outbound-call destinations | `deepapi.co` (deepapi, deep-research, youtube-transcript primary), OpenRouter (run-deep-swe) | None by default (reverse-engineer-first policy) |
| Credentials / API keys | `DEEPAPI_API_KEY`, OpenRouter key, read from `~/.zshrc` | None |
| Does source / prompt / query text leave the machine | Yes for the DeepAPI and OpenRouter skills (URLs, research queries, model prompts) | No |
| New commercial relationship required | Yes (a paid DeepAPI account for the primary research and transcript paths) | No |
| Guardrail posture | One skill (`fable-safe-prompt`) is explicitly designed to evade server-side safety classifiers | Security posture is defensive; no guardrail-evasion content |

### 5.2 Per-item risk scorecard

| ID | Candidate / notable item | Risk tier | Why |
|----|--------------------------|-----------|-----|
| C1a | youtube-transcript, `yt-dlp` local path | Low | Local CLI, no API key, pulls public captions; the only caveat is YouTube ToS and IP bot-flagging, which the skill itself flags and handles by stopping rather than retrying |
| C1b | youtube-transcript, DeepAPI path | High | Scraping-as-service: paid API, key required, target URL and cost sent to a third party |
| C2a | research-prompt, brief authoring | None | Pure LLM-native text generation, no I/O |
| C2b | research-prompt, DeepAPI execution step | High | Research-as-service: query text sent to a paid third-party endpoint |
| C3 | grill-me interactive mode | None | Pure conversational interaction, no I/O |
| C4 | setup-help walkthrough | None | Pure conversational interaction |
| C5 | folder-scoped context files | None | Local file writes only |
| C6 | read-all-ADRs loader | None | Local file reads only |
| D1 | deepapi (raw scraping + email) | High | Scraping-as-service and outbound email; hard-no |
| D2 | deep-research | High | Research-as-service via DeepAPI; hard-no |
| D3 | run-deep-swe | High | Sends model prompts to OpenRouter; vendor-bound and niche |
| D4 | fable-safe-prompt | Declined | Not a data-exfiltration risk, but its purpose is to weaken safety classifiers on dual-use topics; declined on policy and ethics grounds |

### 5.3 Reverse-engineering viability

| ID | Candidate | RE class | Note |
|----|-----------|----------|------|
| C1 | youtube-transcript | `re-full` (local path) + `drop-outright` (DeepAPI path) | Ship a skill-native skill that invokes local `yt-dlp` and flattens `json3` captions to text; document the DeepAPI path as an intentionally-omitted paid alternative |
| C2 | research-prompt | `skill-native` (authoring) + `drop-outright` (DeepAPI execution) | The brief-authoring method is zero-code; the execution step routes to Nexus-Hub's own `/research` harness, not to DeepAPI |
| C3 | grill-me | `skill-native` | An interactive-mode enrichment of an existing skill |
| C4 | setup-help | `skill-native` | An interaction pattern, no code |
| C5 | folder-scoped context files | `skill-native` | Documented file-creation pattern |
| C6 | read-all-ADRs | `skill-native` | A trivial context-loading pattern |
| D1-D3 | deepapi, deep-research, run-deep-swe | `drop-outright` | Hard-no service classes (scraping / research-as-service) or vendor-bound niche tooling |
| D4 | fable-safe-prompt | `drop-outright` | Declined on policy and ethics grounds |
| T1 | cmux, markdown-rendering, pi-custom-model, pi-web-search, codex-goal-loop | `drop-outright` | Bound to external tools Nexus-Hub does not target; the transferable patterns (agent loops) already exist in `loop-engineering` |

### 5.4 Recommendation ordering (this IS the adoption plan)

Sequenced per the MCP Registry Policy: skill-native wins first, then reverse-engineered local builds, then vendor-intrinsic (none qualify), with drops moved to the NOT-recommended list. P-tier from Step 4 orders items within each bucket.

1. **skill-native** (zero-code wins first)
   - C3 grill-me interactive mode (enrich `idea-refine` or `/spec clarify`)
   - C2 research-brief technique (enrich `prompt-engineering` and the `/research` prompt-build step)
   - C4 setup-help guided walkthrough, C5 folder-scoped context helper, C6 read-all-ADRs loader (optional light enrichments; adopt only if a maintainer wants them)
2. **re-full / re-partial** (build the internal equivalent)
   - C1 YouTube transcript via local `yt-dlp` (new skill under `research`, local path only). This is the single highest-value item overall; it sequences into this bucket by policy but is the flagship of the plan.
3. **vendor-intrinsic**: none. Every vendor path here (DeepAPI, OpenRouter) is a hard-no service class, not an intrinsic destination.
4. **drop-outright**: D1-D4 and the tool-bound set move to the NOT-recommended list below.

---

## Steps 6 and 7: Sequencing, Conflicts, and NOT-Recommended Items

### Suggested sequence

The plan is small by design (curate ruthlessly). A realistic, honest sequence:

1. **C1 youtube-transcript (`yt-dlp` local path)**: the one clean capability gap and the clear flagship. New skill in the `research` category, local-only, with `yt-dlp` lazy-invoked and a graceful message when it is absent. Independent of the others.
2. **C2 research-brief enrichment**: fold the single-paragraph brief format into `prompt-engineering` and reference it from the `/research` flow. Independent.
3. **C3 grill-me interactive mode**: add an optional interactive "grill" mode to `idea-refine` or `/spec clarify`, gated by the conflict note below. Independent.
4. **C4-C6**: optional, low-value, adopt only on explicit maintainer request.

### Conflicts and risks

- **Batch-vs-ping-pong convention (C3, and rows 22, 25).** `grill-me`, `brain-to-docs`, and `interview-style-doc-building` all use a **one-question-at-a-time** loop. Nexus-Hub's global convention is the opposite: "batch all clarifying questions into the first turn rather than asking one question per turn" (CLAUDE.md), and `doc-coauthoring` explicitly instructs "batch, not ping-pong". Any adoption of C3 must be framed as an **explicitly user-invoked interactive mode** ("grill me"), not as the default clarifying behavior, so it does not undercut the batch convention. `brain-to-docs` and `interview-style-doc-building` are therefore **not recommended** for adoption: their incremental patch-after-each-answer loop conflicts with `doc-coauthoring`'s batch model, and `doc-coauthoring` already delivers the outcome.
- **New runtime dependency (C1).** `yt-dlp` is a new external tool. It must be lazy-invoked with a clear install hint on absence (the `scripts/generate_report.py` lazy-import precedent), never a hard catalog dependency.
- **ToS caveat (C1).** Fetching YouTube captions can trip bot-flagging. The skill must carry the source's own guidance: on a 429 or "confirm you are not a bot", stop rather than retry in a loop.
- **No verbatim voice (row 23).** `copywriting` encodes one person's writing voice. The transferable pattern (a per-brand voice profile) already exists as `brand-styling`; do not import the personal voice.

### NOT-recommended items (with policy grounds)

| Item | Grounds |
|------|---------|
| `deepapi`, `deep-research` | MCP Registry Policy hard-no: scraping-as-service and research-as-service. The research *workflow* is already delivered by `/research` and the `deep-research` harness with no paid dependency. |
| `run-deep-swe` | Vendor-bound (OpenRouter) and a niche benchmark; sends prompts to a third party. Covered in spirit by `ai-output-evaluation` and `skill-eval-loop`. |
| `fable-safe-prompt` | Declined on policy and ethics grounds: its purpose is to weaken server-side safety classifiers on dual-use (cyber / bio / exploit) topics. Nexus-Hub's security posture is defensive. |
| `cmux`, `markdown-rendering` | Bound to the cmux macOS terminal multiplexer, which Nexus-Hub does not target. |
| `pi-custom-model`, `pi-web-search` | Bound to the Pi agent; covered in spirit by `multi-provider-ai` and per-platform native web tools. |
| `codex-goal-loop` | Documents an OpenAI Codex-specific feature; the underlying loop pattern is already platform-agnostic in `loop-engineering`. |
| `anti-sleep` | A trivial macOS `caffeinate` one-liner; not skill-worthy for a cross-platform catalog. |
| `distribute-skill-to-all-agents`, `push-skill-to-github` | The installer distributes to 14+ platforms and the git-workflow skills plus `/update release` cover publishing, both far beyond a 4-folder symlink and a personal push script. |
| `browser-harness` | Covered by `browser-testing-with-devtools` and `e2e-testing-automation`. |
| `effective-agent-skills` | Covered by `skill-create`, `skill-description-authoring`, `create-custom-command`, the `AGENTS.md` authoring guide, and `skill-stocktake`. |
| `agent-self-scheduling` | Covered by `loop-engineering`, `/loop`, and `temporal-orchestration`. |
| `short`, `handoff`, `teach`, `brain-to-docs`, `interview-style-doc-building` | Covered or conflicting: output-minimization, session-history / context-pack-builder, session-teach-back, and doc-coauthoring respectively already deliver these outcomes. |

---

## Verification

- [x] Source type correctly identified (Git repository) and scope established (skills-only, Dimension 5 focus)
- [x] Every one of the 28 external skills inventoried and classified with a Nexus-Hub equivalent
- [x] Every gap claim cites evidence (the confirmed zero-match search for the YouTube gap; named Nexus-Hub skills for the Covered / Partial rows)
- [x] Adoption candidates have concrete target locations in Nexus-Hub (new `research` skill; `prompt-engineering` / `idea-refine` enrichments)
- [x] Priority assignments consistent with the value/effort matrix
- [x] Conflicts with existing conventions explicitly flagged (the batch-vs-ping-pong convention)
- [x] Items NOT recommended for adoption include reasoning
- [x] **Step 5 complete**: threat-model table, per-item risk scorecard, and per-item RE classification all present
- [x] **Step 5.4 ordering used**: skill-native first, then RE builds, then vendor-intrinsic (none), then drops
- [x] **MCP Registry Policy cited by name** for every item involving an outbound call, new API key, new third-party processor, or new runtime dependency (deepapi, deep-research, run-deep-swe, youtube-transcript DeepAPI path, yt-dlp dependency)

---

## Next step

The prioritized adoption plan above is ready to feed into `/plan from-comparison`, which will produce a phased v3.11.0 implementation plan with reverse-engineer-first ordering. The realistic scope is small: one flagship skill (C1 YouTube transcript via local `yt-dlp`) plus two light enrichments (C2 research-brief, C3 grill-me interactive mode), with the optional C4-C6 items adopted only on explicit maintainer request.
