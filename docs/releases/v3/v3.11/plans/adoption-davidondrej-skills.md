# Plan -- davidondrej/skills Adoption (research-brief technique + grill-me interactive mode + YouTube-transcript skill)

**Project**: Nexus-Hub
**Version**: v3.11.0
**Slug**: adoption-davidondrej-skills
**Plan Type**: Feature / Enhancement (one new skill, two enrichments of existing skills; reverse-engineer-first)
**Created**: 2026-07-06
**Goal**: Operationalize the three recommended, reverse-engineerable candidates from the davidondrej/skills comparison: enrich `prompt-engineering` with a portable research-brief authoring technique (C2, skill-native), add an explicitly user-invoked "grill me" interactive plan-stress-test mode to `idea-refine` (C3, skill-native, gated so it does not undercut the batch-not-ping-pong convention), then ship a new local YouTube-transcript skill via `yt-dlp` (C1, re-full), while recording the declined paid-API and tool-bound skills under the MCP Registry Policy.

## Overview

This plan operationalizes the prioritized adoption plan in [docs/releases/v3/v3.11/comparisons/v3.11.0-comparison-davidondrej-skills.md](../comparison-davidondrej-skills.md). The source, `davidondrej/skills`, is a flat personal skill pack of 28 skills tuned to one operator's stack (the cmux terminal multiplexer, the Pi agent, Hermes, OpenAI Codex, and the paid DeepAPI research service). Of those 28, exactly one is a clean capability gap for Nexus-Hub, and two more are light, zero-code doctrine enrichments. Everything else is tool-bound to an external stack, depends on a scraping or research-as-service API the `AGENTS.md` MCP Registry Policy forbids, encodes one person's writing voice, or is already covered (often more comprehensively) by an existing Nexus-Hub skill.

With `reverse-engineer-first=true`, the plan sequences by reverse-engineering bucket rather than by raw value. The two `skill-native` items (zero-code enrichments of skills Nexus-Hub already ships, carrying no new maintenance or supply-chain cost) come first, then the single `re-full` build (a new skill that reverse-engineers the source's local `yt-dlp` path while declining its paid DeepAPI primary path). The highest-value item overall (C1, the YouTube-transcript skill) therefore lands in Phase 3 rather than Phase 1, behind the skill-native enrichments, exactly as the comparison's Step 5.4 ordering directs and exactly as the v3.10.0 ruflo adoption cycle sequenced its own flagship. The declined skills (the DeepAPI scraping and research paths, the guardrail-evasion skill, and the cmux / Pi / Codex tool-bound set) are recorded as declines in the known-gaps file, not built.

Delivery spans four phases:

- **Phase 1 (skill-native, C2): research-brief authoring technique**, folded into the existing `prompt-engineering` skill and referenced from the `/research` flow. It teaches the agent to produce one self-contained paragraph a human researcher (or any deep-research tool) can act on with zero back-and-forth, distinct from Nexus-Hub's own research-execution harness. No new skill, so no registry edit.
- **Phase 2 (skill-native, C3): user-invoked "grill me" interactive mode**, added to the existing `idea-refine` skill. It is gated as an explicit, opt-in interactive mode so its one-question-at-a-time loop never becomes the default clarifying behavior and never undercuts the project-wide batch-not-ping-pong convention. No new skill, so no registry edit.
- **Phase 3 (re-full, C1): new `youtube-transcript` skill** under `catalog/skills/research/`, reverse-engineering the source's local `yt-dlp` caption path only (a bundled cross-platform caption-flattening script), with the paid DeepAPI path deliberately omitted. Includes the three-file registry update.
- **Phase 4 (consolidation): declines, CHANGELOG, and validation sweep.** Record the policy-relevant declines in `docs/v3/v3.11/known-gaps.md`, add the `## [Unreleased]` CHANGELOG entry, and run the full validator chain.

Success looks like: the research-brief technique present in `prompt-engineering` and referenced from `/research`; an explicitly opt-in grill-me mode in `idea-refine` that the verification proves cannot fire as a default; a working `youtube-transcript` skill whose local path invokes `yt-dlp` with graceful absence handling and carries the source's own ToS and bot-flagging caveat; the new skill registered consistently across the three registries (259 -> 260 skills); the declines recorded under the MCP Registry Policy; every cross-link resolving; every new or edited SKILL.md body under the 500-line norm; all content ASCII-only and conformant to the Markdown style guide; generic naming with no upstream attribution ("DeepAPI", "davidondrej", "David Ondrej", "cmux", "Pi", "Hermes", "deepapi.co" absent from every distributed artifact except where a generic public tool such as `yt-dlp` is genuinely the mechanism); and the full validator chain green.

## Constitution Check

*GATE: Must pass before Phase 1. Re-check after Phase 1 design.*

No constitution file found at `docs/v3/v3.11/constitution.md`, so the formal check is skipped. Recommend running `/constitution` to establish project principles; this is informational, not blocking. The plan is aligned with the standing governance that functions as Nexus-Hub's de-facto constitution (the `AGENTS.md` MCP Registry Policy and the Reverse-Engineering Attribution Rule): the two enrichments are `skill-native` (zero code, zero outbound), and the one new skill is a `re-full` local build over a public tool (`yt-dlp`) the user invokes locally, with no API key, no new Nexus-Hub runtime dependency, and no query text leaving the machine. Nothing introduces an outbound call, a new credential, or a third-party data processor. The declined items are dropped precisely because they would violate that governance (DeepAPI is scraping and research-as-service; the guardrail-evasion skill is contrary to Nexus-Hub's defensive posture; the tool-bound skills target stacks Nexus-Hub does not support), and they are recorded as declines rather than smuggled into the plan. No "ask first" surface is touched: no installer script is edited (a new skill folder is auto-copied by the installer), no hook logic changes, and no version bump happens inside this plan (the version bump is `/update release`'s job).

## Phases at a Glance

| Phase | Title | Outcome | Rec. model / effort |
|-------|-------|---------|---------------------|
| 1 | Research-brief authoring technique (skill-native, C2) | `prompt-engineering` gains a portable one-paragraph research-brief technique; `/research` references it; no registry edit | Strong reasoning tier, medium effort (Claude Code: Opus 4.8, medium) |
| 2 | Grill-me interactive mode (skill-native, C3) | `idea-refine` gains an explicit, opt-in "grill me" interactive stress-test mode, gated against the batch-not-ping-pong convention; no registry edit | Strong reasoning tier, medium effort (Claude Code: Opus 4.8, medium) |
| 3 | YouTube-transcript skill (re-full, C1) | New `catalog/skills/research/youtube-transcript/` skill via local `yt-dlp` plus a bundled caption-flattening script; DeepAPI path omitted; three-file registry update (259 -> 260) | Strong reasoning tier, high effort (Claude Code: Opus 4.8, high) |
| 4 | Declines, CHANGELOG, and validation sweep (consolidation) | Policy-relevant declines recorded in `docs/v3/v3.11/known-gaps.md`; `## [Unreleased]` CHANGELOG entry; full validator chain green | Strong reasoning tier, medium effort (Claude Code: Opus 4.8, medium) |

The "Rec. model / effort" column is a best-effort planning-time assessment, recorded as platform-agnostic tier intent plus the concretely-enumerated Claude Code model. Live model enumeration was not available at plan time, so the concrete name follows the v3.9.0 / v3.10.0 precedent (Opus 4.8); `/implement` re-confirms each phase's recommendation against the then-current live model set before building.

---

## Phase 1: Research-brief authoring technique (skill-native, C2)

**Goal**: Add a reusable technique to `prompt-engineering` that turns a vague research need into one self-contained paragraph a human researcher (or any deep-research tool) can act on with zero back-and-forth, and reference it from the `/research` flow, without duplicating Nexus-Hub's own research-execution harness.
**Prerequisites**: None.
**Stability Gate**: `prompt-engineering/SKILL.md` carries a research-brief technique section (single-paragraph deliverable, numbered sub-questions, source hierarchy, contradiction handling, completion bar, gap round, per-finding output format), `/research` references it, all cross-links resolve, `make validate` is green, the body stays under the 500-line norm, and no upstream attribution appears.
**Recommended model**: Strong reasoning tier, medium effort. Concrete (Claude Code): Opus 4.8, medium effort. Rationale: this is a bounded addition to an existing skill, but it must be phrased so it complements the existing `/research` execution path (producing a portable brief) rather than duplicating it, which is the failure mode to avoid. `/implement` re-confirms against the then-current models.

### Sub-tasks

#### 1.1 -- Add the research-brief technique to prompt-engineering

**Objective**: Teach the agent to author a portable, single-paragraph research brief as a distinct prompt-engineering technique.

**Prompt**:
> Edit `catalog/skills/ai-development/prompt-engineering/SKILL.md` to add a self-contained technique subsection titled "Research-brief authoring" (place it within the existing Instructions or a Techniques area, wherever the skill's structure fits best). The technique produces ONE self-contained paragraph that a researcher with zero prior knowledge of the project can act on with zero back-and-forth. Teach these rules: lead with a one-to-two-sentence plain-English explainer of what the project or product is and why it exists, for a reader who has never heard of it; then state the single question the research must answer and the decision it informs; embed all context inline (names, dates, prior known facts, constraints); number 3 to 6 sub-questions inline so coverage is explicit, one mission per brief; state include and avoid constraints; declare a source hierarchy that prefers primary sources (official docs, source repositories, papers, filings, changelogs) and treats forums and social posts as weak signal only; require contradiction handling (separate confirmed fact from inference from unresolved uncertainty rather than forcing a false consensus, and flag low-confidence claims); define a completion bar ("do not stop at the first plausible answer; corroborate each key claim with multiple independent primary sources where they exist, and say so explicitly where they do not"); require a final gap round (a self-critique pass listing gaps, contradictions, and single-source claims, then another search round to close them, repeating until clean); constrain the deliverable hard but the search method loosely; demand a fixed per-finding output (source link + specific claim + a one-line "why it matters"); and end the brief by instructing the researcher to output everything into a single detailed Markdown file. Include one short worked template paragraph showing the shape. Frame the technique explicitly as producing a PORTABLE brief to hand to a human researcher OR any external deep-research tool; add one sentence clarifying that when Nexus-Hub itself runs the research, the `/research` command and its harness execute the brief (this technique writes the brief; it does not replace the harness). Cross-link `[[trend-research]]` and `[[deep-research-compilation]]`. Apply the Reverse-Engineering Attribution Rule: describe the technique generically and choose your own wording; do NOT name "DeepAPI", "deepapi.co", "davidondrej", or "David Ondrej", and do NOT reference any paid research API as the execution path. Constraints: ASCII-only; follow `catalog/style-guides/markdown.md` (blank line before and after every heading, list, table, and code block); keep the SKILL.md body under the 500-line norm (if the addition would push it over, move the worked template into a `references/` file linked from SKILL.md). Because the frontmatter is unchanged, do NOT edit any `data/` registry file. Acceptance: the technique subsection exists with all listed rules and one worked template; the portability framing and the one-line `/research` clarification are present; both cross-links resolve; no upstream attribution appears; the body is under 500 lines.

---

#### 1.2 -- Reference the technique from the /research flow

**Objective**: Make the `/research` command point at the new technique so the brief-authoring step is discoverable from the research entry point.

**Prompt**:
> Edit `catalog/commands/research.md` to add a single concise reference to the new research-brief authoring technique in `prompt-engineering`, in whichever existing section covers preparing or scoping a research query (for example a notes or workflow section). The reference must state that when the user wants a portable brief to hand to a human researcher or an external deep-research tool, the agent should apply the `prompt-engineering` research-brief technique to produce one self-contained paragraph, and that `/research` otherwise executes the research itself. Keep it to one or two sentences; do not restructure the command file or duplicate the technique's content. Constraints: ASCII-only; Markdown style guide; no `data/` edit (a command change needs no registry update). Acceptance: `research.md` contains a single, accurate pointer to the `prompt-engineering` technique and does not duplicate it.

---

#### 1.3 -- Testing and Stabilization

**Objective**: Validate the Phase 1 edits and iterate until stable before advancing.

**Prompt**:
> Validate Phase 1. Run `make validate` if `make` is on PATH; otherwise run `python scripts/validate_skills.py --verbose` plus the catalog dangling-wikilink audit. Confirm: (1) validators exit 0; (2) `prompt-engineering/SKILL.md` still has YAML-parseable frontmatter with quoted `summary_l0` and `overview_l1` within their word limits and an unchanged frontmatter (no accidental registry drift); (3) the new cross-links (`[[trend-research]]`, `[[deep-research-compilation]]`) resolve with no dangling wikilink; (4) every edited line is ASCII-only (no em-dashes, en-dashes, curly quotes, or ellipsis characters); (5) the SKILL.md body is under 500 lines; (6) grep the diff for "DeepAPI", "deepapi", "davidondrej", and "David Ondrej" and expect zero matches; (7) `research.md` contains exactly one accurate pointer to the technique. Fix any failure and re-run until green. Then run `/session history` to document Phase 1.

---

## Phase 2: Grill-me interactive mode (skill-native, C3)

**Goal**: Add an explicitly user-invoked "grill me" interactive mode to `idea-refine` that stress-tests a plan or design by walking each branch of the decision tree one question at a time, recommending an answer per question, while gating it so this one-at-a-time loop is opt-in only and never becomes or contradicts the project-wide batch-not-ping-pong clarifying default.
**Prerequisites**: None (independent of Phase 1).
**Stability Gate**: `idea-refine/SKILL.md` carries a clearly-labelled opt-in "grill me" interactive mode with an explicit invocation trigger and an explicit statement that it does not override the default batch-clarification convention; the mode recommends an answer per question and prefers codebase exploration over asking when the answer is discoverable; cross-links to `ambiguity-detector`, `plan-review`, and the `/spec clarify` scope resolve; `make validate` is green; the body stays under the 500-line norm; no upstream attribution appears.
**Recommended model**: Strong reasoning tier, medium effort. Concrete (Claude Code): Opus 4.8, medium effort. Rationale: the addition is small, but the gating is subtle: the mode must be genuinely useful as an interactive stress-test yet be fenced so it cannot leak into the default clarifying behavior that the global convention (and `doc-coauthoring`) mandates as batched. A mode that reads as the new default is the failure mode. `/implement` re-confirms against the then-current models.

### Sub-tasks

#### 2.1 -- Add the opt-in grill-me interactive mode to idea-refine

**Objective**: Author a gated, user-invoked interactive stress-test mode within `idea-refine`.

**Prompt**:
> Edit `catalog/skills/developer-experience/idea-refine/SKILL.md` to add a subsection titled "Interactive grill mode (opt-in)". Teach: this mode is entered ONLY when the user explicitly asks for it (trigger phrases: "grill me", "stress-test this plan", "interrogate my design", "poke holes in this"); it is NOT the default behavior of `idea-refine` or of any clarifying step. In the mode, the agent interviews the user relentlessly about the plan or design, walking down each branch of the decision tree and resolving dependencies between decisions one at a time; it asks one question at a time and waits for the answer before the next; for every question it offers its own recommended answer with a one-line rationale; and when a question can be answered by exploring the codebase, it explores the codebase instead of asking. State the exit condition: the mode ends when the branches are resolved and there is shared understanding of the design, at which point the agent summarizes the resolved decisions. Add an explicit gating paragraph, prominent and unambiguous: this one-question-at-a-time loop is an opt-in interactive mode and does NOT change Nexus-Hub's default convention, which is to batch clarifying questions into a single turn (see the global batch-not-ping-pong rule and `[[doc-coauthoring]]`'s "batch, not ping-pong" instruction); outside this explicitly-invoked mode, the agent still batches. Cross-link `[[ambiguity-detector]]` (structured detection of the gaps this mode probes interactively), `[[plan-review]]` (parallel-persona plan review, the non-interactive counterpart), and the `/spec clarify` scope (spec-ambiguity resolution). Apply the Reverse-Engineering Attribution Rule: describe the mode generically; do NOT name "davidondrej", "David Ondrej", or credit any specific external author in the distributed artifact. Constraints: ASCII-only; Markdown style guide; keep the SKILL.md body under the 500-line norm. Because the frontmatter is unchanged, do NOT edit any `data/` registry file. Acceptance: the opt-in mode exists with its explicit trigger, the per-question recommendation rule, the explore-the-codebase-first rule, and the exit condition; the gating paragraph explicitly states the mode does not override the batch default and references the batch convention and `doc-coauthoring`; all three cross-links resolve; no upstream attribution appears; the body is under 500 lines.

---

#### 2.2 -- Testing and Stabilization

**Objective**: Validate the Phase 2 edit, with special attention to the gating, and iterate until stable.

**Prompt**:
> Validate Phase 2. Run `make validate` (or `python scripts/validate_skills.py --verbose` plus the dangling-wikilink audit). Confirm: (1) validators exit 0; (2) `idea-refine/SKILL.md` frontmatter is unchanged and YAML-parseable with quoted `summary_l0` and `overview_l1` within limits; (3) the cross-links (`[[ambiguity-detector]]`, `[[plan-review]]`, `[[doc-coauthoring]]`) resolve with no dangling wikilink; (4) ASCII-only throughout the diff; (5) body under 500 lines; (6) grep the diff for "davidondrej" and "David Ondrej" and expect zero matches; (7) read the gating paragraph and confirm it unambiguously states the grill mode is opt-in and does NOT override the batch-not-ping-pong default (this is the key correctness check for the phase: the mode must not read as the new default clarifying behavior). Fix any failure and re-run until green. Then run `/session history` to document Phase 2.

---

## Phase 3: YouTube-transcript skill (re-full, C1)

**Goal**: Ship a new local-only skill that fetches a YouTube video's transcript via `yt-dlp` and saves a clean text file, reverse-engineering the source's local caption path while deliberately omitting its paid DeepAPI primary path, with `yt-dlp` lazy-invoked (a graceful message when it is absent) and the source's own ToS and bot-flagging caveat carried forward.
**Prerequisites**: None (independent of Phases 1 and 2; sequenced here per the reverse-engineer-first ordering, behind the skill-native enrichments).
**Stability Gate**: `catalog/skills/research/youtube-transcript/SKILL.md` exists with conformant frontmatter and all required body sections; the local `yt-dlp` path (caption download plus the bundled flattening script) is documented; `yt-dlp` absence is handled gracefully; the ToS and 429 bot-flagging caveat (stop, do not retry in a loop) is present; the DeepAPI path is absent; the bundled `scripts/flatten_captions.py` is referenced from SKILL.md (orphan-bundle audit clean); the three registries are updated to 260 and `make validate` is green; the body is under 500 lines; no upstream attribution appears.
**Recommended model**: Strong reasoning tier, high effort. Concrete (Claude Code): Opus 4.8, high effort. Rationale: this phase designs a new skill with a bundled cross-platform script, a lazy-dependency contract, and a legal or ToS caveat that must be stated responsibly (public captions only, stop on bot-flagging), and it must omit the paid path without leaving a dangling reference. An over-broad scraping posture or an ungraceful hard dependency is the high-risk failure mode. `/implement` re-confirms against the then-current models.

### Sub-tasks

#### 3.1 -- Create the youtube-transcript skill

**Objective**: Author a new `research` skill that documents the local `yt-dlp` caption path and saves a clean transcript file.

**Prompt**:
> Create `catalog/skills/research/youtube-transcript/SKILL.md`, a new skill. Conformant frontmatter: `name: youtube-transcript`; a pushy `description` listing trigger phrases ("get the transcript of this video", "transcript of this YouTube URL", "pull the captions", "download the subtitles", "what does this YouTube video say") AND a SKIP clause (SKIP: transcribing local audio or video files with a speech-to-text model; downloading the video itself; summarizing a transcript you already have - use a writing or summarization skill for that); `summary_l0` in quotes, 15 words or fewer; `overview_l1` in quotes, 150 words or fewer. Required body sections in order: a one-paragraph intro; `## When to Use This Skill` (with explicit "When NOT to use"); `## Instructions`; `## Common Rationalizations`; `## Verification` (binary, observable); `## Related Skills`. In Instructions teach the LOCAL yt-dlp path ONLY (do NOT include any paid-API path): (1) a save-location rule (save into the current project or working directory when there is one, otherwise `~/Downloads`), and a filename rule (derive `Channel_Title` with spaces replaced by underscores and unsafe characters stripped, falling back to the video id when metadata is unavailable); (2) fetch metadata with `yt-dlp --print "%(channel)s|%(title)s" --skip-download "<URL>"`, falling back channel -> uploader -> uploader_id when channel is null; (3) download captions only with `yt-dlp --skip-download --write-subs --write-auto-subs --sub-langs "en.*" --sub-format json3 -o "<OUT>/<NAME>.%(ext)s" "<URL>"`, noting that `--write-subs` prefers manual captions and `--write-auto-subs` falls back to auto-generated, and that json3 MUST be used rather than VTT or SRT because auto VTT duplicates every line (rolling captions); for a non-English or unknown language, run `yt-dlp --list-subs "<URL>"` first, then set `--sub-langs`; (4) flatten the json3 file to clean raw text by running the bundled script `scripts/flatten_captions.py` (created in sub-task 3.2), passing the output directory; (5) report the saved path and print the text when it is short. Add a "yt-dlp availability" note: check whether `yt-dlp` is on PATH first (for example `command -v yt-dlp`), and if it is absent, do NOT attempt an install silently; instead tell the user the skill needs `yt-dlp` and give the install hint (`pipx install yt-dlp` or `pip install yt-dlp`), then stop. Add a REQUIRED caveat block: fetching captions must be limited to publicly-available captions and used in accordance with YouTube's Terms of Service; on an HTTP 429 or a "Sign in to confirm you're not a bot" response the local IP is flagged, so STOP and report it rather than retrying in a loop (retrying makes it worse); a single `yt-dlp -U` self-update then one retry is acceptable, after which stop; never fall back to downloading audio for speech-to-text unless the user explicitly asks. In `## Common Rationalizations`, include at least: "I should just retry the 429 a few times" (reality: retry loops deepen the IP flag; stop and report) and "I'll grab the audio and transcribe it instead" (reality: that is a different, heavier operation the user did not ask for; do it only on explicit request). Cross-link `[[trend-research]]` and `[[local-docs-lookup]]`. Apply the Reverse-Engineering Attribution Rule: `yt-dlp` is a generic public tool and may be named as the mechanism, but do NOT name "DeepAPI", "deepapi.co", "davidondrej", or "David Ondrej", and do NOT include the paid-API endpoint, key handling, or `~/.zshrc` secret-reading from the source skill. Constraints: ASCII-only; follow `catalog/style-guides/markdown.md`; body under the 500-line norm. Acceptance: the file exists with conformant frontmatter and all six required body sections; only the local yt-dlp path is documented (no paid path, no API key, no secret-reading); the yt-dlp-absence graceful-handling note and the ToS plus 429-stop caveat are present; the two required Common Rationalizations rows are present; both cross-links resolve; the SKILL.md references `scripts/flatten_captions.py`; no upstream attribution beyond the generic `yt-dlp` tool name appears.

---

#### 3.2 -- Add the bundled caption-flattening script

**Objective**: Ship a small, cross-platform tier-3 script that converts a yt-dlp json3 caption file into clean raw text, referenced from the SKILL.md.

**Prompt**:
> Create `catalog/skills/research/youtube-transcript/scripts/flatten_captions.py`, a small standalone Python 3 script (standard library only: `json`, `html`, `re`, `glob`, `sys`, `pathlib`). Include a module docstring and type annotations per the AGENTS.md hook and script conventions. Behavior: accept an output directory as the first CLI argument (default to the current directory when none is given); find the first `*.json3` file in that directory; if none exists, exit with a clear non-zero error message ("no json3 caption file found in <dir>"); otherwise load it, concatenate the `utf8` fragments of each event's `segs`, unescape HTML entities, collapse whitespace to single spaces, write the result to a sibling `.txt` file with the same stem, and print the written path. Keep it under about 40 lines. This is a `.py` script, so no `.ps1` sibling is required (Python is cross-platform); do not add one. Ensure `catalog/skills/research/youtube-transcript/SKILL.md` references this script by path so the orphan-bundle audit passes (the reference was added in sub-task 3.1; confirm it matches this filename exactly). Note for the installer: a per-skill `scripts/` subdirectory is auto-copied by both installers when the skill folder is copied (the recursive folder-copy path in AGENTS.md), so NO edit to `scripts/installer.sh` or `scripts/installer.ps1` is needed. Constraints: ASCII-only; the script must not make any network call, read any secret, or require any third-party package. Acceptance: `flatten_captions.py` exists, is standard-library-only, handles the missing-file case, is under about 40 lines, is referenced by exact name from SKILL.md, and needs no installer edit and no `.ps1` sibling.

---

#### 3.3 -- Register the youtube-transcript skill

**Objective**: Register the new skill in the three catalog registries so it is discoverable and the counts stay consistent.

**Prompt**:
> Register the new `youtube-transcript` skill per the AGENTS.md "Register the skill" rules. (1) In `data/SKILL_INDEX.md`, add one table row: `| youtube-transcript | Research | "<summary_l0 verbatim>" | catalog/skills/research/youtube-transcript/SKILL.md |`, placed with the other Research-category skills. (2) In `data/skills.json`, add one entry to the `"skills"` array following the existing schema (name, title, description, long_description, summary_l0, overview_l1, version 1.0.0, author, category Research, language Multi-language, tags such as youtube / transcript / captions / research, priority, based_on, tools_required including Bash, path, file, size, downloads 0, status, security scores defaulting to 100/100/95). (3) In `data/marketplace.json`, increment the Research category `skill_count` by 1 and `statistics.total_skills` by 1 (259 -> 260). Then run `make validate` (or the Windows fallback `python scripts/validate_skills.py --verbose`) and confirm JSON integrity is green, the new skill is detected, and the orphan-bundle audit is clean (the bundled `scripts/flatten_captions.py` is referenced from SKILL.md). Constraints: ASCII-only; do not edit any other `data/` field. Acceptance: all three registries are updated consistently to 260, the summary string matches `SKILL.md` verbatim, and the validator is green.

---

#### 3.4 -- Testing and Stabilization

**Objective**: Validate the Phase 3 skill, script, and registration, and iterate until stable before advancing.

**Prompt**:
> Validate Phase 3. Run `make validate` if `make` is on PATH; otherwise run `python scripts/validate_skills.py --verbose` plus the catalog dangling-wikilink audit. Confirm: (1) validators exit 0; (2) the new skill is registered consistently across `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json` (count is 260); (3) no dangling wikilinks (`[[trend-research]]`, `[[local-docs-lookup]]` resolve); (4) every line in the new SKILL.md and the new script is ASCII-only; (5) the SKILL.md body is under 500 lines; (6) grep the new files and the diff for "DeepAPI", "deepapi", "davidondrej", "David Ondrej", and any `~/.zshrc` secret-reading, and expect zero matches (only the generic `yt-dlp` tool name is allowed); (7) the skill frontmatter parses as YAML with quoted `summary_l0` and `overview_l1` within word limits; (8) `flatten_captions.py` is standard-library-only (no third-party import), handles the missing-json3 case, and is referenced from SKILL.md so the orphan-bundle audit is clean; (9) confirm no installer edit was made (a new skill folder is auto-copied) and no `.ps1` sibling was added for the `.py` script. As a lightweight functional smoke test, run `python catalog/skills/research/youtube-transcript/scripts/flatten_captions.py` against a tiny hand-written json3 fixture (two events with `segs`) in a temporary directory and confirm it writes a `.txt` with the expected collapsed text; do not call the network or yt-dlp in the test. Fix any failure and re-run until green. Then run `/session history` to document Phase 3.

---

## Phase 4: Declines, CHANGELOG, and validation sweep (consolidation)

**Goal**: Record the policy-relevant declines from the comparison so the next planning cycle does not re-propose them, add the `## [Unreleased]` CHANGELOG entry describing the three adopted items, and run the full validator chain over the whole change set.
**Prerequisites**: Phases 1, 2, and 3 complete.
**Stability Gate**: `docs/v3/v3.11/known-gaps.md` records the declined items with the MCP Registry Policy cited by name; the `## [Unreleased]` section of `CHANGELOG.md` describes the research-brief technique, the grill-me mode, and the youtube-transcript skill, with the final catalog counts (260 skills, 16 commands, 25 hooks); the full validator chain (`make validate`, `make lint`, `make test`) is green; all content is ASCII-only.
**Recommended model**: Strong reasoning tier, medium effort. Concrete (Claude Code): Opus 4.8, medium effort. Rationale: the work is largely mechanical documentation and validation, but the CHANGELOG entry and the decline record must be accurate and cite the policy correctly; a wrong count or a mis-stated decline is the failure mode. This phase could downshift on a re-assessment; `/implement` re-confirms against the then-current models.

### Sub-tasks

#### 4.1 -- Record the declines in known-gaps

**Objective**: Document the declined candidates so they are not re-proposed, with the policy grounds cited.

**Prompt**:
> Create or append to `docs/v3/v3.11/known-gaps.md` a dated section recording the davidondrej/skills comparison declines, referencing [docs/releases/v3/v3.11/comparisons/v3.11.0-comparison-davidondrej-skills.md](comparison-davidondrej-skills.md). Record, each with a one-line reason and the policy grounds cited by name: the paid-API skills (a scraping-and-email endpoint skill and a deep-research skill) declined under the MCP Registry Policy hard-no on scraping-as-service and research-as-service, noting that the research workflow is already delivered by `/research`; a model-benchmark-via-third-party-router skill declined as vendor-bound and niche; a prompt-rewriting skill declined on policy and ethics grounds because its purpose is to weaken server-side safety classifiers on dual-use topics (contrary to Nexus-Hub's defensive posture); and the tool-bound set (a terminal-multiplexer integration, two personal-agent skills, and a vendor goal-loop feature doc) declined because they target stacks Nexus-Hub does not support, with the transferable loop pattern already in `loop-engineering`. Also note the two candidates deferred as low value (a guided setup walkthrough and a folder-scoped context-file helper and a read-all-ADRs loader) as optional future items adopted only on explicit request. Apply the Reverse-Engineering Attribution Rule: describe each declined item generically by function; do NOT name "DeepAPI", "deepapi.co", "cmux", "Pi", "Hermes", "davidondrej", or "David Ondrej". Constraints: ASCII-only; Markdown style guide. Acceptance: `known-gaps.md` records every declined class with a reason and the MCP Registry Policy cited by name, using generic descriptions only.

---

#### 4.2 -- Add the CHANGELOG entry

**Objective**: Describe the three adopted items in the `## [Unreleased]` section with accurate final counts.

**Prompt**:
> Edit `CHANGELOG.md` to add entries under the existing `## [Unreleased]` section (create the `### Added` and `### Changed` subsections there if absent) describing this cycle: under Added, the new `youtube-transcript` Research skill (local `yt-dlp` path only, bundled caption-flattening script, DeepAPI path deliberately omitted, no new outbound call or credential; catalog 259 -> 260 skills); under Changed, the `prompt-engineering` research-brief authoring technique (referenced from `/research`) and the opt-in grill-me interactive mode added to `idea-refine` (gated so it does not override the batch-not-ping-pong default), noting both are skill-native with no frontmatter change and therefore no registry edit beyond the youtube-transcript registration. State the final catalog counts explicitly (260 skills, 16 commands, 25 hooks) and that there is no new outbound call, dependency, or credential (the `yt-dlp` invocation is a user-run local tool, lazy-checked, not a Nexus-Hub dependency). Reference the plan (`docs/v3/v3.11/plans/adoption-davidondrej-skills.md`) and the comparison report. Apply the Reverse-Engineering Attribution Rule (generic; no upstream product or author names beyond the generic `yt-dlp` tool). Constraints: ASCII-only (no em-dashes, en-dashes, curly quotes, or ellipsis characters); follow `catalog/style-guides/markdown.md`. Acceptance: the `## [Unreleased]` section describes all three adopted items with the correct final counts and the no-new-outbound assurance, cites the plan and comparison, and uses generic naming.

---

#### 4.3 -- Full validation sweep

**Objective**: Run the complete validator chain over the whole change set and confirm green.

**Prompt**:
> Run the full validation sweep for the v3.11.0 adoption change set. (1) `make validate` (or `python scripts/validate_skills.py --verbose`) for JSON catalog integrity and the orphan-bundle audit; confirm the skill count is 260 and consistent across `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json`. (2) `make lint` (ShellCheck) if any shell script changed; note that this cycle added a `.py` script, not a `.sh` script, so ShellCheck has nothing new to check, but run it to confirm no regression. (3) `make test` (the pytest hook suite) to confirm no regression, plus the lightweight `flatten_captions.py` fixture smoke test from sub-task 3.4 if not already run. (4) The catalog dangling-wikilink audit across all edited and new files. (5) A final ASCII-only grep across the diff (no em-dashes, en-dashes, curly quotes, or ellipsis characters) and an attribution grep (no "DeepAPI", "deepapi", "davidondrej", "David Ondrej", "cmux", "Pi", "Hermes" in any distributed artifact). Summarize the results (counts, pass or fail, any errors) rather than pasting full logs. Fix any failure and re-run until every check is green. Then run `/session history` to document Phase 4 and the completion of the plan.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | (none) | (none) |

Every Constitution Check bullet is PASS or N/A (no constitution file exists; the plan aligns with the standing `AGENTS.md` governance), so this table is intentionally empty.

---

### Phase 1 Exit Checklist

- [x] All sub-tasks completed
- [x] `prompt-engineering` carries the research-brief technique; `/research` references it
- [x] No registry drift (frontmatter unchanged, no `data/` edit)
- [x] Validators green; no dangling wikilinks; ASCII-only; body under 500 lines
- [x] Session history generated for Phase 1 (combined close-out history)
- [x] Ready to advance to Phase 2

### Phase 2 Exit Checklist

- [x] All sub-tasks completed
- [x] `idea-refine` carries the opt-in grill-me mode with the explicit batch-convention gate
- [x] Gating verified: the mode cannot read as the default clarifying behavior
- [x] Validators green; no dangling wikilinks; ASCII-only; body under 500 lines
- [x] Session history generated for Phase 2 (combined close-out history)
- [x] Ready to advance to Phase 3

### Phase 3 Exit Checklist

- [x] All sub-tasks completed
- [x] `youtube-transcript` skill created (local yt-dlp path only; DeepAPI path omitted)
- [x] Bundled `flatten_captions.py` created, standard-library-only, referenced from SKILL.md
- [x] yt-dlp-absence graceful handling and ToS / 429-stop caveat present
- [x] Three registries updated consistently (259 -> 260 at the time it landed); no installer edit; no `.ps1` sibling
- [x] Validators green; orphan-bundle audit clean; ASCII-only; body under 500 lines
- [x] Session history generated for Phase 3 (combined close-out history)
- [x] Ready to advance to Phase 4

### Phase 4 Exit Checklist

- [x] All sub-tasks completed
- [x] Declines recorded in `docs/v3/v3.11/known-gaps.md` with the MCP Registry Policy cited (added at close-out 2026-07-08)
- [x] CHANGELOG entry present under `## [3.11.0]` (the entry was authored while the section was still `## [Unreleased]`, then promoted to `[3.11.0]` in workflow-governance Phase 8); final release count is 265, not the plan's point-in-time 260
- [x] Validator chain green (`make validate` equivalent; `make lint`/full `make test` covered by CI on Linux)
- [x] No new outbound call, dependency, or credential introduced
- [x] Session history generated for Phase 4 (combined close-out history)
- [x] Plan complete; ready for `/update release` when the version's Definition of Done is met
