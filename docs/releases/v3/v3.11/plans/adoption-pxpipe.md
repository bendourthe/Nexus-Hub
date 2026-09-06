# Plan -- pxpipe Adoption (optical / image-token compression doctrine, mechanism declined)

**Project**: Nexus-Hub
**Version**: v3.11.0
**Slug**: adoption-pxpipe
**Plan Type**: Enhancement (skill-native doctrine only; the source's runtime mechanism is declined under the MCP Registry Policy)
**Created**: 2026-07-06
**Goal**: Capture the token-economics doctrine surfaced by the pxpipe optical-compression debate as grounded skill-native content that steers Nexus-Hub users toward the lossless token-reduction techniques the catalog already ships, and record the imaging-proxy mechanism as a deliberate decline. Ship a grounded optical / image-token compression subsection in `prompt-token-optimization` (with the silent-exact-string caution folded in), a one-line model-specificity note in `model-routing`, and a `drop-outright` row in the reverse-engineering matrix, while introducing no new outbound call, dependency, credential, or runtime.

## Overview

This plan operationalizes the prioritized Adoption Plan in [docs/releases/v3/v3.11/comparisons/v3.11.0-comparison-pxpipe.md](../comparison-pxpipe.md). The source is a transport-layer reverse-proxy that lossily re-renders bulky static context as dense PNG images before the request reaches the API, exploiting Anthropic's per-patch image billing to cut input-token cost. The comparison found the mechanism to be real, freshly-validated 2025 research (optical context compression) but lossy by construction: it preserves gist and silently corrupts exact strings (hashes, hex, IDs), with self-reported 0% exact-hex recall on Opus-class models and token savings that invert to a loss on the high-resolution image tier those models use. That mechanism is categorically non-adoptable into a local-first, correctness-first catalog: it is an always-on runtime component in the API critical path that mutates requests lossily and handles credentials, exactly the runtime class the `AGENTS.md` MCP Registry Policy declines, and the same class declined in the v3.10.0 ruflo cycle (the MCP-server-as-daemon and standalone-loop-runtime precedents).

The adoptable substance is therefore doctrine, not capability. With `reverse-engineer-first=true`, the plan sequences by reverse-engineering bucket: every adoptable item here is `skill-native` (there is no `re-full` / `re-partial` build, because the one buildable artifact, the imaging proxy, is precisely the thing being declined), so ordering is by value within the skill-native bucket. The highest-value item (C1 + C2, the grounded doctrine that prevents users chasing a lossy hack) lands first; the low-value note (C4) and the decline bookkeeping land second.

Delivery spans two phases:

- **Phase 1 (skill-native, P2): optical / image-token compression doctrine in `prompt-token-optimization`.** Add a subsection that explains the technique and its research grounding, states Anthropic's per-patch image billing and the high-resolution tier, gives the worked example showing images cost more than text at legible resolution on strong models, names the silent-exact-string-confabulation failure and the byte-exact-stays-text rule (C2), and directs users to the lossless defaults the catalog already ships. Cross-link the adjacent skills. Decide and record whether the frontmatter summary changes (registry update only if it does).
- **Phase 2 (skill-native, P3 + consolidation): model-specificity note + decline bookkeeping.** Add a one-line note to `model-routing` that some cost techniques are vision-encoder-specific and degrade on stronger reasoning models (C4); add a dated `drop-outright` row for the imaging-proxy mechanism to the reverse-engineering matrix with the MCP Registry Policy and the ruflo precedent cited by name; write the CHANGELOG `[Unreleased]` entry and a `known-gaps.md` revisit trigger; run the validator chain.

Success looks like: `prompt-token-optimization` carrying a grounded, non-overclaiming optical-compression subsection with the silent-failure caution and the lossless-first rule; `model-routing` noting the model-specificity of image-token techniques; a `drop-outright` matrix row recording the declined mechanism with the policy cited by name; every cross-link resolving; every edited SKILL.md body under the 500-line norm; all content ASCII-only and conformant to the Markdown style guide; generic naming with no upstream attribution (no "pxpipe" or "teamchong" literal in any installer-distributed artifact; the source may be named only in the non-distributed `docs/` report and matrix); no new outbound call, dependency, credential, or runtime anywhere; and the full validator chain green.

## Constitution Check

*GATE: Must pass before Phase 1. Re-check after Phase 1 design.*

No constitution file found at `docs/v3/v3.11/constitution.md` - skipping the formal check (informational, not blocking; `/constitution` would establish project principles). The plan is aligned with the standing governance that functions as Nexus-Hub's de-facto constitution (the `AGENTS.md` MCP Registry Policy, the correctness-first skill doctrine, and the Reverse-Engineering Attribution Rule): every adopted item is `skill-native` doctrine over owned artifacts; nothing introduces an outbound call, a dependency, a credential, or a runtime; the one buildable artifact (the imaging proxy) is deliberately declined rather than smuggled in, and is recorded as a decline. The distributed skill text must name the technique generically and must NOT contain the "pxpipe" or "teamchong" literals (Reverse-Engineering Attribution Rule); the source name appears only in the non-distributed `docs/` report and the matrix rationale. No "ask first" surface is touched: this plan edits only skill Markdown, the policy matrix, the CHANGELOG, and a known-gaps file. No installer, hook-logic, or version-bump change is in scope (the version bump happens later at release via `/update release`).

## Phases at a Glance

| Phase | Title | Outcome | Rec. model / effort |
|-------|-------|---------|---------------------|
| 1 | Optical-compression doctrine in `prompt-token-optimization` (skill-native, P2) | A grounded subsection covering the mechanism, the per-patch billing math and resolution trap, the silent-exact-string failure (C2), and the lossless-first rule; cross-links to `context-compression`, `context-engineering`, `model-routing`, `egress-redaction`, `ai-billing-safeguards`; a Common Rationalizations row and a Verification item; registry update only if the summary changes | Strong reasoning tier, medium effort (Claude Code: Opus 4.8, medium) |
| 2 | Model-specificity note + decline bookkeeping (skill-native, P3) | A one-line `model-routing` note (C4); a `drop-outright` matrix row for the imaging proxy citing the MCP Registry Policy and the ruflo precedent; CHANGELOG `[Unreleased]` entry; `docs/v3/v3.11/known-gaps.md` revisit trigger; validator chain green | Moderate reasoning tier (Sonnet-class), low-to-medium effort (Claude Code: Sonnet 5, medium) |

The "Rec. model / effort" column is a best-effort planning-time assessment, recorded as platform-agnostic tier intent plus a concretely-named Claude Code model. Live model enumeration was not available at plan time, so the concrete names follow the current release baseline; `/implement` re-confirms each phase's recommendation against the then-current live model set before building. Phase 1 carries the higher tier because the doctrine must be technically precise (the per-patch billing math and the reconciliation of "68% savings" against "images cost more") and must not overclaim safety; Phase 2 is mechanical bookkeeping over pre-derived content.

---

## Phase 1: Optical-compression doctrine in `prompt-token-optimization` (skill-native, P2)

**Goal**: Add a grounded, non-overclaiming subsection to `prompt-token-optimization` that teaches optical / image-token context compression: what it is, when it can help versus when it hurts, why it inverts on strong-model image billing, the silent-exact-string-confabulation failure mode and the byte-exact-stays-text rule (C2), and the rule that lossless prompt caching and context pruning are the correct default for the same static content.
**Prerequisites**: None. Source content is fully derived in [docs/releases/v3/v3.11/comparisons/v3.11.0-comparison-pxpipe.md](../comparison-pxpipe.md) Part A and Step 6.
**Stability Gate**: `catalog/skills/orchestration/prompt-token-optimization/SKILL.md` contains an optical / image-token compression subsection covering the mechanism, the per-patch billing formula and the high-resolution-tier cost inversion, the silent-exact-string failure and the byte-exact-stays-text rule, and the lossless-first directive; a Common Rationalizations row and a binary Verification item are added; cross-links `[[context-compression]]`, `[[context-engineering]]`, `[[model-routing]]`, `[[egress-redaction]]`, `[[ai-billing-safeguards]]` resolve; the body stays under the 500-line norm; the frontmatter registry decision is made and recorded (registries updated iff `summary_l0` / `overview_l1` change); `make validate` is green; the distributed artifact is ASCII-only and contains no "pxpipe" or "teamchong" literal.
**Recommended model**: Strong reasoning tier, medium effort. Concrete (Claude Code): Opus 4.8, medium effort. Rationale: the subsection makes quantitative claims (the `ceil(w/28) * ceil(h/28)` patch formula, the high-resolution-tier cap, the worked text-vs-image token comparison, the reconciliation of the vendor "68%" against "images cost more at legible resolution") that must be correct and must not overclaim safety; the failure mode is a technically-wrong or over-reassuring subsection. Content is pre-derived, so effort is medium rather than high. `/implement` re-confirms against the then-current models and may downshift to a Sonnet-class tier if it judges the transcription low-risk.

### Sub-tasks

#### 1.1 -- Author the optical / image-token compression subsection

**Objective**: Add the doctrine subsection to the skill body, covering mechanism, economics, the silent-failure caution (C2), and the lossless-first rule.

**Prompt**:
> Edit `catalog/skills/orchestration/prompt-token-optimization/SKILL.md`. Add a new subsection (choose a heading such as `## Optical / image-token context compression` placed after the existing token-reduction guidance and before Related Skills). Teach, concisely and generically (this is an installer-distributed artifact, so do NOT name "pxpipe" or "teamchong" - refer to "a class of proxy tools that render bulky static context as images" and to the research by name): (1) The mechanism: rendering text as a raster image so the model reads it back through its vision head, which can be token-efficient because images are billed by pixel dimensions, not character count. (2) The research grounding, generically citable: DeepSeek-OCR "Contexts Optical Compression" (arXiv 2510.18234, about 97% decode precision at roughly 10x compression, collapsing to about 60% near 20x) and Glyph (arXiv 2510.17800, roughly 3-4x at parity accuracy), and the honest note that these are 2025 results at research-preview maturity for general long-context, production-grade only for OCR/document extraction. (3) The economics on Anthropic: images are billed per 28x28-pixel patch (`ceil(width/28) * ceil(height/28)` visual tokens), with a high-resolution tier for strong models (Opus-class, Sonnet 5, Fable 5) that roughly triples image cost; at any resolution where code stays legible, a page rendered as an image costs roughly 1.5x to 5x more than the same text (about 2,700-4,784 image tokens versus about 750-1,050 text tokens on an Opus-class model). State that reported large savings come from rendering illegibly dense and from vision encoders that tolerate that density, and that the savings and the fidelity are the same dial turned in opposite directions. (4) The failure mode (C2): the technique is lossy, and its misses are silent confabulations, not errors - the model returns a confident, plausible-but-wrong value (a flipped hex digit, a 0/O or 1/l substitution) with no low-confidence signal. This is worst-case for a coding assistant: hashes, hex, base64, version pins, and near-identical identifiers must be byte-exact, and a silent one-character error passes human review and lint. State the rule plainly: byte-exact content (IDs, hashes, secrets, precise numbers, literal code to edit) must stay as text; pixels also forfeit verbatim reproduction, exact diffs, and exact search. (5) The lossless-first directive: for the same large, static context, prefer the lossless techniques the catalog already ships - prompt caching, context pruning/hygiene, and the local `nexus-context-compressor` engine (`guides/reference/RTK_CONTEXT_COMPRESSION.md`) - and prefer choosing the cheapest capable model (see `[[model-routing]]`) over lossily compressing context for an expensive one. Add cross-links `[[context-compression]]`, `[[context-engineering]]`, `[[model-routing]]`, `[[egress-redaction]]`, and `[[ai-billing-safeguards]]`. Constraints: ASCII-only; follow `catalog/style-guides/markdown.md` (blank line before and after every heading, list, table, and code block); keep the total body under the 500-line norm (if it would exceed, push the worked example into a `references/` file linked from the SKILL.md and keep the body summary tight). Acceptance: the subsection is present with all five elements; the byte-exact-stays-text rule and the lossless-first directive are stated explicitly; all five cross-links resolve; no "pxpipe" or "teamchong" literal appears.

---

#### 1.2 -- Add a Common Rationalizations row and a Verification item

**Objective**: Wire the new doctrine into the skill's required behavioral-guard sections so it triggers correctly.

**Prompt**:
> In the same `catalog/skills/orchestration/prompt-token-optimization/SKILL.md`, add one row to the `## Common Rationalizations` table and one item to the `## Verification` checklist that reflect the new subsection. The rationalization row must cite a concrete failure mode, for example: Rationalization "Rendering the big files as images will cut my token bill with no downside" / Reality "It is lossy: exact strings are silently corrupted (0% hex recall on strong models in published tests), and on the high-resolution image tier a legible page costs more tokens than the text - use lossless caching/pruning and keep byte-exact content as text." The Verification item must be binary and observable, for example: "- [ ] Any proposed image-token / optical-compression tactic keeps byte-exact content (IDs, hashes, secrets, code to edit) as text and prefers a lossless alternative (prompt caching, context pruning) for static bulk." Constraints: ASCII-only; Markdown style guide; do not duplicate an existing row/item. Acceptance: one new Rationalizations row citing a concrete failure mode and one new binary Verification item are present and consistent with the 1.1 subsection.

---

#### 1.3 -- Frontmatter / registry decision

**Objective**: Decide whether the Tier-1 frontmatter changes, and update the three registries only if it does.

**Prompt**:
> Review whether the 1.1 subsection changes the skill's `summary_l0` or `overview_l1` in `catalog/skills/orchestration/prompt-token-optimization/SKILL.md`. The default expectation is NO change (this is an additive body enrichment, matching the v3.8.0/v3.9.0 body-only refinement precedent), in which case make no `data/` edit and record "body-only, no registry change" in the phase notes. Only if you judge the frontmatter should mention optical/image-token compression to improve triggering, update it AND then update all three registries consistently per the AGENTS.md rules: the `data/SKILL_INDEX.md` row (summary verbatim), the matching `data/skills.json` entry fields, and confirm `data/marketplace.json` counts are unchanged (no new skill is added, so `total_skills` stays 259). Constraints: ASCII-only; never edit unrelated `data/` fields; if any registry field changes, run `make validate` and confirm green. Acceptance: an explicit recorded decision (changed or not); if changed, the three registries are consistent and the summary matches `SKILL.md` verbatim; the skill count stays 259.

---

#### 1.4 -- Testing and Stabilization

**Objective**: Validate the Phase 1 edit and iterate until stable before advancing.

**Prompt**:
> Validate Phase 1. Run `make validate` if `make` is on PATH; otherwise run `python scripts/validate_skills.py --verbose` (JSON catalog integrity plus orphan-bundle audit) and the catalog dangling-wikilink audit. Confirm: (1) validators exit 0; (2) the five cross-links (`[[context-compression]]`, `[[context-engineering]]`, `[[model-routing]]`, `[[egress-redaction]]`, `[[ai-billing-safeguards]]`) all resolve; (3) every changed line is ASCII-only (no em-dashes, en-dashes, curly quotes, or ellipsis characters); (4) the body is under the 500-line norm (and if a `references/` file was added, it is linked and the orphan-bundle audit is clean); (5) grep the changed SKILL.md for "pxpipe" and "teamchong" and expect zero matches (Reverse-Engineering Attribution Rule); (6) the frontmatter still parses as YAML with quoted `summary_l0` / `overview_l1` within word limits; (7) the skill count is unchanged at 259 unless 1.3 deliberately changed the summary. Fix any failure and re-run until green. Then run `/session history` to document Phase 1.

---

## Phase 2: Model-specificity note + decline bookkeeping (skill-native, P3)

**Goal**: Record that image-token cost techniques are vision-encoder-specific and degrade on stronger reasoning models (C4), document the deliberate decline of the imaging-proxy mechanism (C3) in the reverse-engineering matrix, and complete the release bookkeeping (CHANGELOG, known-gaps).
**Prerequisites**: Phase 1 landed (so the CHANGELOG entry can describe the full change set). C4 and the matrix row are independent of Phase 1 and could proceed in parallel, but are grouped here as the low-value consolidation phase.
**Stability Gate**: `model-routing/SKILL.md` carries a one-line note on the model-specificity of image-token techniques with a cross-link back to `prompt-token-optimization`; `docs/policy/mcp-reverse-engineering-matrix.md` has a dated `drop-outright` row for the imaging-proxy mechanism citing the MCP Registry Policy and the v3.10.0 ruflo runtime-decline precedent by name; a CHANGELOG `[Unreleased]` entry describes the change set; `docs/v3/v3.11/known-gaps.md` records the revisit trigger; validators are green; distributed artifacts contain no "pxpipe" / "teamchong" literal (the matrix and known-gaps are non-distributed `docs/` and may name the source).
**Recommended model**: Moderate reasoning tier (Sonnet-class), low-to-medium effort. Concrete (Claude Code): Sonnet 5, medium effort. Rationale: this phase is mechanical bookkeeping over content already derived in the comparison report (a one-line skill note, a matrix row, a changelog entry, a known-gaps line); no new doctrine design. The failure mode is a policy citation that is imprecise or a matrix row that omits the precedent, both low-severity. `/implement` re-confirms and may upshift only if the note authoring proves subtler than expected.

### Sub-tasks

#### 2.1 -- Add the model-specificity note to `model-routing` (C4)

**Objective**: Note that some cost techniques are vision-encoder-specific and are not a universal lever.

**Prompt**:
> Edit `catalog/skills/ai-development/model-routing/SKILL.md`. Add a concise note (one to three sentences, in the most fitting existing section, for example where cost trade-offs are discussed) that some token-cost techniques are vision-encoder-specific and can degrade sharply on stronger reasoning models: rendering context as images to save tokens works only on encoders that tolerate dense rendering and inverts on the high-resolution image-billing tier that strong models use, so choosing the cheapest capable model for a task is the more reliable, lossless cost lever than lossily compressing context for an expensive one. Cross-link `[[prompt-token-optimization]]` for the full treatment. Constraints: ASCII-only; Markdown style guide; do NOT name "pxpipe" or "teamchong"; keep it to a note, not a new section; body stays under the 500-line norm. Acceptance: the note is present, accurate, generic, and cross-links `[[prompt-token-optimization]]`; no upstream literal appears.

---

#### 2.2 -- Add the drop-outright row to the reverse-engineering matrix (C3)

**Objective**: Record the declined imaging-proxy mechanism as a policy decision with precedent.

**Prompt**:
> Edit `docs/policy/mcp-reverse-engineering-matrix.md`. Add a dated row (or a short dated subsection, matching the file's existing structure) recording the optical / image-token compression proxy mechanism as `drop-outright`. This file is NOT installer-distributed, so it MAY name the source (pxpipe / teamchong) and link the comparison report. The rationale must state: it is an always-on transport-layer runtime in the API critical path that lossily mutates requests and handles credentials; it is declined under the `AGENTS.md` MCP Registry Policy on the same grounds as the v3.10.0 ruflo runtime declines (the MCP-server-as-daemon and standalone-loop-runtime precedents, cited by name); and it is independently declined on correctness grounds (a correctness-first coding catalog must not ship or endorse a lossy context transform whose errors are silent confabulations) and on economics (the savings invert on the high-resolution image tier used by strong models). Reference [docs/releases/v3/v3.11/comparisons/v3.11.0-comparison-pxpipe.md](../v3.11.0/comparison-pxpipe.md) (adjust the relative path to the matrix file's location). Note that the adoptable doctrine was imported as the skill-native items in this cycle. Constraints: ASCII-only; Markdown style guide; match the matrix's existing column/section format. Acceptance: a dated `drop-outright` row exists citing the MCP Registry Policy and the ruflo precedent by name, linking the comparison report, with the correctness and economics grounds stated.

---

#### 2.3 -- CHANGELOG entry and known-gaps revisit trigger

**Objective**: Record the change set under `[Unreleased]` and capture the deliberate decline as a revisit trigger for a future cycle.

**Prompt**:
> (1) Edit `CHANGELOG.md`: under `## [Unreleased]`, add entries describing this cycle in the established style: a `### Changed` entry for the `prompt-token-optimization` optical/image-token compression doctrine enrichment (Phase 1) and the `model-routing` model-specificity note (Phase 2), and a `### Changed` entry for the reverse-engineering-matrix decline of the imaging-proxy mechanism. State plainly: no new skill/command/hook (catalog stays 259 skills / 16 commands / 25 hooks unless 1.3 changed a summary), and no new outbound call, dependency, credential, or runtime. Reference [docs/releases/v3/v3.11/comparisons/v3.11.0-comparison-pxpipe.md](docs/v3/v3.11/comparisons/v3.11.0-comparison-pxpipe.md). ASCII-only (no Unicode punctuation - this prevents Windows encoding corruption). (2) Create `docs/v3/v3.11/known-gaps.md` (or append if it exists) with a revisit trigger entry, for example DF-v311-pxpipe-C3: the optical/image-token compression proxy mechanism was declined this cycle; revisit only if Anthropic changes image-token billing to make legible renders cheaper than text on strong models, or if a lossless-fidelity variant (verified anchor sidecar for exact strings) becomes proven - otherwise keep declined. Constraints: ASCII-only; Markdown style guide. Acceptance: the `[Unreleased]` CHANGELOG entries are present and accurate; `known-gaps.md` records the revisit trigger with an explicit condition.

---

#### 2.4 -- Testing and Stabilization

**Objective**: Validate Phase 2 and the whole change set and iterate until stable.

**Prompt**:
> Validate Phase 2. Run `make validate` (or `python scripts/validate_skills.py --verbose` plus the dangling-wikilink audit). Confirm: (1) validators exit 0; (2) the `[[prompt-token-optimization]]` cross-link in `model-routing` resolves and Phase 1's five cross-links still resolve; (3) all changed lines across both skills, the matrix, the CHANGELOG, and known-gaps are ASCII-only; (4) grep the two changed SKILL.md files (the installer-distributed artifacts) for "pxpipe" and "teamchong" and expect zero matches; the matrix and known-gaps MAY name the source; (5) catalog counts are unchanged (259 / 16 / 25) unless 1.3 deliberately changed a summary; (6) both edited skill bodies are under the 500-line norm. Fix any failure and re-run until green. Then run `/session history` to document Phase 2, and note the plan is release-ready (the version bump and CHANGELOG finalization happen later via `/update release`, which merges develop into main and tags v3.11.0).

---

## Risks and Notes

- **Attribution discipline is the main correctness risk.** The two edited SKILL.md files are installer-distributed, so they must teach the technique generically and must not contain "pxpipe" or "teamchong". The source is named only in the non-distributed `docs/` report, the matrix rationale, and the CHANGELOG. Sub-tasks 1.4 and 2.4 grep for the literals as a gate.
- **Quantitative precision.** The patch-billing formula, the high-resolution-tier cost inversion, and the vendor-savings reconciliation must be stated correctly and must not overclaim safety. All figures are pre-derived in the comparison report Part A; transcribe from there, do not re-derive from memory.
- **Branching.** This is v3.11.0 work: land it on `develop` (directly or via a short-lived `feat/adoption-pxpipe` branch merged back into `develop`), never on `main`. The develop -> main merge and the `vX.Y.Z` tag happen only at release via `/update release`.
- **No scope creep.** This plan touches only two skill bodies, the policy matrix, the CHANGELOG, and a known-gaps file. The imaging mechanism is declined, not built; no installer, hook-logic, script, or version-bump change is in scope.
