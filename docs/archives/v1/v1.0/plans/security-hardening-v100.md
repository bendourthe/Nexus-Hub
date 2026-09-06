# Plan — v1.0.0: Reverse-Engineering-First Security Hardening

**Project**: DevAI-Hub
**Version**: v1.0.0
**Slug**: security-hardening-v100
**Plan Type**: Feature / Enhancement (security hardening + major-version release)
**Created**: 2026-04-24
**Source scratch plan**: `~/.claude/plans/recursive-yawning-willow.md`
**Supersedes**: [docs/v0.9.7/plans/adoption-claude-context.md](../../v0.9.7/plans/adoption-claude-context.md) (ABANDONED — Phases 3–5 reverse-engineered into this plan's Phases 8–10; Phase 6 absorbed here)
**Goal**: Ship a DevAI-Hub v1.0.0 that is audit-clean and safe for regulated-industry / high-trust environments — local-only MCP registry, reverse-engineering-first governance policy, 2 new internal MCPs that replace dropped third-party servers, 3 new skills that capture reverse-engineered knowledge without external attribution, and a `/compare-project` command that enforces the same ordering on every future comparison.

---

## Overview

The v0.9.7 adoption plan `adoption-claude-context.md` was halted after Phase 2 when the user flagged that DevAI-Hub must not ship MCP registry entries pointing users at third-party data processors (proprietary source code, prompts, and queries must not leak to external APIs in any regulated-industry / high-trust context). Phase 2 had added exactly such an entry (`@zilliz/claude-context-mcp`), which has now been reverted. On follow-up the user asked that the response go further than a simple drop list — apply a **reverse-engineering-first** lens to every registry entry, produce a structured matrix driving keep/strip/rebuild decisions, and bake that ordering into `/compare-project` so future adoption exercises default to "rebuild locally first."

The accumulated scope (policy bake-in with new authoritative matrix, 2 new internal MCPs, 3 new skills, breaking removals of 4 registry entries, command-level workflow change, new governance section in `AGENTS.md`) is a major-version event. The work therefore targets **v1.0.0** as the first stable release milestone. The version-bump sweep goes `0.9.7 → 1.0.0`, skipping the intermediate 0.9.8.

A Plan-agent validation earlier in the planning session flagged that shipping full dense/hybrid retrieval inside v1.0.0 is too ambitious and recommended a two-stage split: v1.0.0 ships `devai-code-search` **keyword-only** (no ML deps, no model downloads, zero C-extension compile on Windows); v1.1.0 adds dense/hybrid retrieval via `fastembed` + `sqlite-vec`. This plan adopts that split. The `v1.1.0+ Backlog` section at the end carries every deferred item forward.

**Guiding principle (from the user)**:
> Priority is always reverse-engineer and recreate locally. Trusted vendors are accepted only for parts that cannot be reverse-engineered AND where the feature is extremely worth it.

---

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 0 | Revert Phase 2 and abandon the old adoption plan | Clean working tree; abandoned-plan header; this plan file materialized |
| 1 | MCP Registry Policy with reverse-engineering-first decision tree | `AGENTS.md` policy section + 7 platform-surface inlines |
| 2 | Reverse-Engineering Matrix | `docs/policy/mcp-reverse-engineering-matrix.md` classifying every MCP |
| 3 | Apply matrix to registry + integration docs | `mcp-servers.json` at target state; guides revised |
| 4 | De-brand Phase 1 skill content | `rag-implementation/SKILL.md` without external attribution |
| 5 | `/compare-project` extension with RE-first handoff to `/generate-plan` | Command + skill updated; new Section 9 |
| 6 | Build `devai-code-search` MVP (keyword-only) | New package under `extensions/` |
| 7 | Build `devai-web-fetch` + LLM-native skill replacements for context7 / magic-ui | New package + 2 new skills |
| 8 | Reverse-engineered `code-semantic-search` skill (de-branded) | New SKILL.md + 3 registry updates |
| 9 | Cross-link `context-manager` and `context-engineering` | Two Related Skills entries |
| 10 | Internal MCP benchmark harness | Benchmark script + Makefile target + pytest + installer registration |
| 11 | Release v1.0.0 | CHANGELOG migration, 14-file version bump, RELEASE_NOTES, tag |

---

## Phase 0: Revert Phase 2 and Abandon the Old Adoption Plan

**Goal**: Restore a clean working tree and mark the prior adoption plan as superseded.
**Prerequisites**: None.
**Stability Gate**: `git status` shows only the intended new plan file under `docs/archive/v1/v1.0/plans/`; the abandoned plan carries an ABANDONED header that forward-links here.
**Status**: **Completed during planning session (2026-04-24)**. Sub-tasks 0.1–0.5 are documented below for plan completeness and reproducibility.

### Sub-tasks

#### 0.1 — Revert the `claude-context` entry in `mcp-servers.json`

**Objective**: Remove the Phase 2 registry entry that added `@zilliz/claude-context-mcp@latest` as a pointer to an external third-party data processor.

**Prompt**:
> In `catalog/mcp-configs/mcp-servers.json`, locate the `claude-context` block sitting between the `github` block and the `filesystem` block. Delete it entirely (including its `_comment` field and trailing comma placement). `mcpServers` should return to 15 entries. Verify with `python -m json.tool catalog/mcp-configs/mcp-servers.json` (exit 0) and `python -c "import json; d=json.load(open('catalog/mcp-configs/mcp-servers.json')); assert 'claude-context' not in d['mcpServers']; assert len(d['mcpServers']) == 15"`.

---

#### 0.2 — Remove the Phase 2 entry from `docs/DEVLOG.md`

**Objective**: Strip the 2026-04-24 Phase 2 DEVLOG entry that documented the behavior now being reverted.

**Prompt**:
> In `docs/DEVLOG.md`, find the top-of-file entry headed `## [2026-04-24] - v0.9.8 (in progress) Phase 2: MCP registry entry for claude-context`. Remove it entirely, including its trailing `---` separator. The file should now start at the Phase 1 entry (headed `## [2026-04-24] - v0.9.8 (in progress) Phase 1: Retrofit rag-implementation with claude-context patterns`). Do not modify any other entry. `git diff docs/DEVLOG.md` should show only deletions.

---

#### 0.3 — Delete the Phase 2 session-history file

**Objective**: Remove the uncommitted session-history artifact for work being reverted.

**Prompt**:
> Delete `docs/v0.9.7/development/history/2026-04_phase-2-mcp-registry-claude-context.md`. The file was never committed so this leaves no git diff. Confirm with `ls docs/v0.9.7/development/history/` — only `2026-04_phase-1-adopt-claude-context.md` and the earlier v0.9.7 phase history files should remain.

---

#### 0.4 — Prepend an ABANDONED header to the old adoption plan

**Objective**: Flag `adoption-claude-context.md` as superseded so anyone reading it understands the retarget to v1.0.0 and where to find the current work.

**Prompt**:
> In `docs/v0.9.7/plans/adoption-claude-context.md`, prepend an `> STATUS: ABANDONED (2026-04-24) — SUPERSEDED BY v1.0.0 SECURITY-HARDENING PLAN` blockquote header that explains: (a) Phase 2 reverted; (b) Phase 1 content de-branded in v1.0.0 Phase 4; (c) Phases 3–5 reverse-engineered into v1.0.0 Phases 8–10; (d) Phase 6 absorbed into v1.0.0 Phase 11; (e) release retarget from v0.9.8 to v1.0.0. Include a forward-link to `docs/archive/v1/v1.0/plans/security-hardening-v100.md`. Leave the rest of the file untouched — it is historical record.

---

#### 0.5 — Materialize this plan via `/generate-plan`

**Objective**: Use DevAI-Hub's canonical authoring flow to produce the durable in-repo plan rather than a raw file copy.

**Prompt**:
> Run `/generate-plan` in discovery mode with `~/.claude/plans/recursive-yawning-willow.md` as the authoritative source for every question. Slug: `security-hardening-v100`. Version: `v1.0.0`. Plan type: Feature/Enhancement. Expected output: `docs/archive/v1/v1.0/plans/security-hardening-v100.md` listing 12 phases (0 through 11) in the same order and with the same titles as the scratch plan's Phase Map. Confirm the abandoned-plan forward-link from sub-task 0.4 resolves to this output path.

---

### Phase 0 Exit Checklist

- [x] `mcp-servers.json` back to 15 entries (no `claude-context`)
- [x] `docs/DEVLOG.md` Phase 2 entry removed
- [x] `docs/v0.9.7/development/history/2026-04_phase-2-mcp-registry-claude-context.md` deleted
- [x] `docs/v0.9.7/plans/adoption-claude-context.md` carries ABANDONED header with forward-link
- [x] `docs/archive/v1/v1.0/plans/security-hardening-v100.md` exists (this file)

---

## Phase 1: MCP Registry Policy with Reverse-Engineering-First Decision Tree

**Goal**: Author and distribute the policy so every future PR walks the decision tree before proposing an MCP addition.
**Prerequisites**: Phase 0.
**Stability Gate**: `grep -c "MCP Registry Policy" AGENTS.md` returns 1; the condensed summary is diff-identical across all 7 non-import platform surfaces; the policy body explicitly orders local → LLM-native skill → reverse-engineered MCP → trusted vendor → drop.

### Sub-tasks

#### 1.1 — Author the `## MCP Registry Policy` section in `AGENTS.md`

**Objective**: Add the canonical policy body and the 5-question audit checklist, keyed off a strict decision-tree ordering.

**Prompt**:
> In `AGENTS.md`, insert a new `## MCP Registry Policy` section immediately before `## Adding a New Command` (currently around line 131). Body must contain:
>
> 1. **Decision tree** (in order — stop at the first bucket that fits):
>    1. **Local-only**: internal DevAI-Hub servers (`devai-skill-server`, `devai-code-search`, `devai-web-fetch`) or Anthropic-official servers that make zero outbound calls (`filesystem`, `memory`, `sequential-thinking`, `sqlite`). **Always allowed.**
>    2. **LLM-native skill** (zero code, zero MCP): if the capability can be achieved by instructing the agent's own LLM, ship a skill — not an MCP. **Preferred over any external wrapper.**
>    3. **Reverse-engineerable into a local internal MCP**: if the external project wraps logic that can run locally (fetch + HTML parsing, tree-sitter chunking, BM25 keyword search), build the internal equivalent under `extensions/`. Strip external attribution; use generic names.
>    4. **Trusted vendor wrapper (your-own-account)**: only when all three conditions hold — (a) the third party is the intrinsic data destination (you are already a customer of GitHub / Supabase / Railway / Vercel / Cloudflare); (b) the capability cannot be reverse-engineered locally; (c) the feature is extremely worth it. The `_comment` field must justify each condition.
>    5. **Otherwise**: drop.
>
> 2. **Five-question audit checklist** (required in the `_comment` of every new registry entry):
>    - Who runs the process?
>    - What outbound calls does it make and where?
>    - What API keys does it require?
>    - Does it transmit source code, prompts, or query text to a third party?
>    - Does the user already have a commercial relationship with the destination?
>
> 3. **Hard no list**: search-as-service, embeddings-as-service, scraping-as-service, generation-as-service. Examples: Upstash/context7, Exa, Firecrawl, 21st.dev/magic-ui, Zilliz/claude-context.
>
> 4. **Matrix requirement**: every MCP listed in `catalog/mcp-configs/mcp-servers.json` must have a row in `docs/policy/mcp-reverse-engineering-matrix.md`. Future additions must include a matrix row.
>
> Acceptance: `grep -c "MCP Registry Policy" AGENTS.md` returns 1; the section is the longest net addition to the file; line count of existing sections before line 131 is unchanged.

---

#### 1.2 — Sync the condensed policy summary to all 5 platform base templates

**Objective**: Per the project's platform-agnostic rule, distribute the same 8–10 line condensed summary to `templates/ai-instructions/base-{claude,codex,cursor,gemini,opencode}.md`.

**Prompt**:
> In each of the five files `templates/ai-instructions/base-claude.md`, `base-codex.md`, `base-cursor.md`, `base-gemini.md`, `base-opencode.md`, inline an 8–10 line condensed summary of the MCP Registry Policy authored in sub-task 1.1. The summary must:
>
> - Name the decision-tree ordering (local-only → LLM-native skill → reverse-engineered MCP → trusted vendor wrapper → drop).
> - State the hard-no list.
> - Reference the canonical full policy in `AGENTS.md` and the matrix at `docs/policy/mcp-reverse-engineering-matrix.md`.
>
> All five files must carry the same text (diff-identical). Verify with `diff <(grep -A 10 "MCP Registry Policy" templates/ai-instructions/base-claude.md) <(grep -A 10 "MCP Registry Policy" templates/ai-instructions/base-codex.md)` — expect no output. Repeat pairwise for all 10 combinations or use a single reference hash.

---

#### 1.3 — Sync the condensed summary to Copilot and Cursor rules

**Objective**: Copilot and Cursor cannot `@`-import, so their rules files need the same inlined summary.

**Prompt**:
> Inline the same 8–10 line condensed summary from sub-task 1.2 into `.github/copilot-instructions.md` and `.cursor/rules/devai-hub.mdc`. Text must be diff-identical to the five base templates (modulo the file's existing heading conventions). Verify with `grep -c "MCP Registry Policy" .github/copilot-instructions.md .cursor/rules/devai-hub.mdc` — both return 1.

---

#### 1.4 — Testing and Stabilization

**Objective**: Verify policy discoverability, platform parity, and grep audit.

**Prompt**:
> Run the following verifications on Phase 1:
>
> 1. `grep -c "MCP Registry Policy" AGENTS.md` returns 1.
> 2. `grep -l "MCP Registry Policy" templates/ai-instructions/base-claude.md base-codex.md base-cursor.md base-gemini.md base-opencode.md .github/copilot-instructions.md .cursor/rules/devai-hub.mdc` returns 7 files.
> 3. Diff-check the inlined summary across the 7 platform surfaces — text must be identical (modulo heading wrappers).
> 4. `CLAUDE.md` and `GEMINI.md` use `@AGENTS.md` import — no edit needed, but confirm the imports still resolve.
> 5. `make validate` (or its Python equivalents) clean.
>
> Fix any drift. Do not proceed to Phase 2 until all five verifications pass.

---

### Phase 1 Exit Checklist

- [ ] `AGENTS.md` has the full `## MCP Registry Policy` section with decision tree + 5-question audit
- [ ] Condensed summary present and diff-identical across 7 platform surfaces
- [ ] `CLAUDE.md` / `GEMINI.md` `@`-imports still resolve
- [ ] `make validate` clean
- [ ] Ready to advance to Phase 2

---

## Phase 2: Reverse-Engineering Matrix

**Goal**: Produce the durable classification document that drives every keep/strip/rebuild decision in Phases 3, 6, 7 and anchors future registry changes.
**Prerequisites**: Phase 1.
**Stability Gate**: `docs/policy/mcp-reverse-engineering-matrix.md` exists; every current `mcp-servers.json` entry plus the reverted `claude-context` has a row; each classification is justified with an upstream-source citation.

### Sub-tasks

#### 2.1 — Scaffold the matrix document

**Objective**: Create the file with introduction, classification legend, row schema, and a seeded row table ready for evidence-gathering in sub-task 2.2.

**Prompt**:
> Create `docs/policy/mcp-reverse-engineering-matrix.md` with the following structure:
>
> 1. Title + one-paragraph purpose statement referencing the MCP Registry Policy in `AGENTS.md`.
> 2. **Row schema** table headers: `MCP key | Current source | What it does | Outbound-call surface | Classification | Effort if RE'd | v1.0.0 action | v1.1.0+ action | Rationale`.
> 3. **Classification legend**:
>    - `already-local` — no outbound calls; no action.
>    - `skill-native` — achievable via the agent's own LLM; replace with a skill.
>    - `re-full` — fully reverse-engineerable into a local internal MCP.
>    - `re-partial` — partially reverse-engineerable; ship what's local, document the gap.
>    - `vendor-intrinsic` — third party IS the data destination; audit-rebuild only.
>    - `drop-outright` — no local equivalent possible.
> 4. **Seed table** with the 16 rows from the scratch plan's row-seed (Phase 2 of the scratch plan). Classifications only, actions only — detailed rationale prose lands in sub-task 2.2.
>
> Acceptance: file exists; 16 rows listed; the legend explicitly orders per the MCP Registry Policy decision tree.

---

#### 2.2 — Populate evidence and rationale for each row

**Objective**: For every row, cite an upstream file or documentation URL confirming the outbound-call surface, and write the rationale paragraph that justifies the classification.

**Prompt**:
> For each of the 16 rows in `docs/policy/mcp-reverse-engineering-matrix.md`:
>
> 1. Read the upstream project's README / repo structure (for 3rd-party entries) or the current DevAI-Hub code (for `devai-skill-server`). Cite one concrete file path or documentation URL per row.
> 2. Confirm the outbound-call surface matches the classification.
> 3. Where classification is `re-full` or `re-partial`, size the effort (small / medium / large) and identify the target deliverable (internal MCP name, skill name) that Phases 6 and 7 will build.
> 4. Where classification is `vendor-intrinsic`, write the justification paragraph that will be inlined into the `_comment` field of the kept registry entry in Phase 3 (must answer the 5-question audit).
>
> Acceptance: every row has at least one citation; every `re-*` row names its Phase 6 or Phase 7 deliverable; every `vendor-intrinsic` row has a 5-question-audit paragraph ready for Phase 3 reuse.

---

#### 2.3 — Testing and Stabilization

**Objective**: Verify matrix completeness and drive Phase 3 via the matrix contents.

**Prompt**:
> Verify:
>
> 1. Row count == 16 (11 kept registry entries + 4 dropped + `claude-context` reverted).
> 2. Every row has a citation.
> 3. Phase 6 and Phase 7 deliverables named in the matrix match the package / skill names planned in this plan (`devai-code-search`, `devai-web-fetch`, `ui-component-generation`, `local-docs-lookup`, `code-semantic-search`).
> 4. Markdown table renders correctly.
> 5. `make validate` clean (matrix is a new Markdown file — no JSON impact).
>
> Fix any gaps. Do not proceed to Phase 3 until the matrix is authoritative.

---

### Phase 2 Exit Checklist

- [ ] `docs/policy/mcp-reverse-engineering-matrix.md` exists with all 16 rows
- [ ] Every row cites upstream evidence
- [ ] Every `re-*` row names its Phase 6 / 7 deliverable
- [ ] Every `vendor-intrinsic` row has a 5-question-audit paragraph ready for Phase 3

---

## Phase 3: Apply the Matrix to the Registry and Integration Docs

**Goal**: Execute the matrix's v1.0.0 recommendations against `mcp-servers.json` and the two MCP-adjacent documentation surfaces.
**Prerequisites**: Phase 2.
**Stability Gate**: `mcp-servers.json` contains only the 11 matrix-approved entries; every kept `vendor-intrinsic` entry has the 5-question audit in its `_comment`; two MCP guides are policy-compliant.

### Sub-tasks

#### 3.1 — Strip unsafe entries from `mcp-servers.json`

**Objective**: Delete `context7`, `exa-web-search`, `firecrawl`, `magic-ui` per the matrix.

**Prompt**:
> In `catalog/mcp-configs/mcp-servers.json`, delete the `context7`, `exa-web-search`, `firecrawl`, and `magic-ui` blocks. Preserve surrounding formatting (2-space indent, trailing commas as needed). After edits, `mcpServers` should contain exactly 11 keys: `github`, `filesystem`, `memory`, `sequential-thinking`, `supabase`, `postgres`, `sqlite`, `railway`, `vercel`, `cloudflare`, `devai-skill-server`. Verify with `python -c "import json; d=json.load(open('catalog/mcp-configs/mcp-servers.json')); assert set(d['mcpServers']) == {'github','filesystem','memory','sequential-thinking','supabase','postgres','sqlite','railway','vercel','cloudflare','devai-skill-server'}"`.

---

#### 3.2 — Inline the 5-question audit into every kept `vendor-intrinsic` entry's `_comment`

**Objective**: Each vendor wrapper must carry the audit justification from the matrix.

**Prompt**:
> For each of the 6 kept `vendor-intrinsic` entries in `catalog/mcp-configs/mcp-servers.json` (`github`, `supabase`, `postgres`, `railway`, `vercel`, `cloudflare`), rewrite its `_comment` field to include the 5-question audit paragraph from the corresponding row of `docs/policy/mcp-reverse-engineering-matrix.md`. Keep the answers concise (one sentence per question). Preserve existing `command` / `args` / `env` fields. After edits, every `vendor-intrinsic` entry's `_comment` must explicitly reference: who runs the process, what outbound calls it makes, what API keys it requires, whether it transmits proprietary data, and whether the user has a pre-existing commercial relationship.
>
> Also update the top-level `_comment` to point at `AGENTS.md` MCP Registry Policy and `docs/policy/mcp-reverse-engineering-matrix.md`.

---

#### 3.3 — Rewrite `guides/MCP_DEVELOPMENT_SERVERS.md` to be policy-compliant

**Objective**: The current guide recommends `context7`, `deepwiki-mcp`, `tavily` — all drop-class under the new policy. Replace with policy-compliant recommendations only.

**Prompt**:
> Rewrite `guides/MCP_DEVELOPMENT_SERVERS.md`. The new version must only recommend:
>
> 1. Local-only Anthropic-official servers (`filesystem`, `memory`, `sequential-thinking`, `sqlite`).
> 2. Vendor-intrinsic wrappers with the same 5-question audit (reuse the matrix justifications).
> 3. DevAI-Hub's own internal MCPs: `devai-skill-server` (existing), `devai-code-search` (landing in Phase 6), `devai-web-fetch` (landing in Phase 7).
>
> Include a one-paragraph pointer to `docs/policy/mcp-reverse-engineering-matrix.md` explaining why some popular 3rd-party servers (context7, tavily, deepwiki-mcp) aren't recommended. Cross-reference the `AGENTS.md` MCP Registry Policy. Preserve the guide's existing "Research / Debug / Document / Test" categorization structure where it still applies.

---

#### 3.4 — Revise `infrastructure/integrations/README.md`

**Objective**: Embed a policy callout and strip template blocks for dropped servers.

**Prompt**:
> In `infrastructure/integrations/README.md`:
>
> 1. Extend the "What are MCPs?" section (lines 5–17) with a policy callout linking to `AGENTS.md` MCP Registry Policy and `docs/policy/mcp-reverse-engineering-matrix.md`.
> 2. Remove any template blocks that document the dropped servers (`context7`, `exa-web-search`, `firecrawl`, `magic-ui`).
> 3. Keep the generic MCP explanation paragraphs intact.
> 4. If the guide enumerates specific templates by number (e.g. `#### 1. GitHub Integration`), re-number after removals to keep the list sequential.

---

#### 3.5 — Testing and Stabilization

**Objective**: Verify policy-compliance grep and installer distribution.

**Prompt**:
> Run the following verifications:
>
> 1. `python -m json.tool catalog/mcp-configs/mcp-servers.json` exit 0.
> 2. `python -c "import json; d=json.load(open('catalog/mcp-configs/mcp-servers.json')); assert len(d['mcpServers']) == 11"`.
> 3. Each kept `vendor-intrinsic` entry's `_comment` contains all 5 audit-question answers (grep for each of: "outbound", "API key", "commercial", "transmit").
> 4. `grep -rn "context7\|exa-web-search\|firecrawl\|magic-ui" guides/ infrastructure/ catalog/ --include='*.md' --include='*.json'` returns matches only in CHANGELOG / DEVLOG / `docs/v0.*.*/` historical trees.
> 5. `make validate` clean.
> 6. Static installer verification: `grep -n "mcp-servers.json" scripts/installer.sh scripts/installer.ps1` — 4 matches at the documented line ranges; no installer code edits needed.
>
> Fix any drift. Do not proceed to Phase 4 until all six pass.

---

### Phase 3 Exit Checklist

- [ ] `mcp-servers.json` has exactly 11 entries
- [ ] Every vendor-intrinsic entry carries the 5-question audit in `_comment`
- [ ] `guides/MCP_DEVELOPMENT_SERVERS.md` rewritten; no 3rd-party data-processor recommendations
- [ ] `infrastructure/integrations/README.md` carries a policy callout; no dropped-server templates
- [ ] Policy-compliance grep audit clean

---

## Phase 4: De-brand Phase 1 Skill Content

**Goal**: Preserve the reverse-engineered technical knowledge already in `rag-implementation/SKILL.md` (from the abandoned plan's Phase 1) but strip every external-source attribution per the user's rename directive.
**Prerequisites**: Phase 1 (policy governs the rewording).
**Stability Gate**: `grep -i "zilliztech\|claude-context\|zilliz cloud\|voyage-code-3\|swe-bench\|8\.4k" catalog/skills/ai-development/rag-implementation/SKILL.md` returns zero matches.

### Sub-tasks

#### 4.1 — De-brand the Canonical OSS Reference paragraph

**Objective**: Rewrite the subsection added by the abandoned plan's Phase 1 sub-task 1.1 so the hybrid BM25 + dense + RRF pattern is described without naming `zilliztech/claude-context` and without citing SWE-bench-specific metrics that only apply to that evaluation.

**Prompt**:
> In `catalog/skills/ai-development/rag-implementation/SKILL.md`, locate the "Canonical OSS Reference" subsection around line 660 (added by the abandoned adoption-claude-context plan's Phase 1 sub-task 1.1). Rewrite it to:
>
> 1. Rename the subsection heading to **"Production Reference Pattern"** or **"Hybrid Retrieval in Practice"**.
> 2. Describe the hybrid BM25 + dense + RRF pattern without naming the upstream repo.
> 3. Remove the "8.4k-star MIT-licensed" attribution.
> 4. Remove the SWE-bench 39.4% / 36.3% metrics (those attach to a specific external evaluation and cannot be cited generically).
> 5. Point the one concrete reference at `extensions/devai-code-search/` — the internal MCP that Phase 6 of this plan ships. Note that v1.0.0 ships keyword-only with hybrid retrieval planned for v1.1.0.
>
> Keep the surrounding BM25 and RRF paragraphs untouched. Preserve markdown heading levels. Acceptance: the rewritten subsection contains zero matches for `zilliztech`, `claude-context`, `8.4k`, or `SWE-bench`.

---

#### 4.2 — De-brand the Vector Store Comparison table

**Objective**: Drop the `Zilliz Cloud` row (vendor managed service; not policy-compliant to name). Keep `Milvus` as an open-source option but reword to remove upstream-reference framing.

**Prompt**:
> In `catalog/skills/ai-development/rag-implementation/SKILL.md`, locate the Vector Store Comparison table around lines 444–445 (rows added by the abandoned plan's Phase 1 sub-task 1.2 part 1). Edits:
>
> 1. Delete the `Zilliz Cloud` row entirely.
> 2. Keep the `Milvus` row but rewrite its description to not reference "the upstream reference" or link to any 3rd-party repo. Present Milvus as one of several open-source self-hostable vector DB options.
>
> Do not modify the pre-existing Chroma, Pinecone, pgvector, or Qdrant rows. Acceptance: table now has one fewer row than before; the remaining `Milvus` row contains no external attribution.

---

#### 4.3 — De-brand the Embedding Model Comparison table and Code-Specialized subsection

**Objective**: Keep the neutral vendor enumeration (OpenAI, VoyageAI, Google, Ollama) as an ecosystem-level fact, but remove specific branded model names and the forward-link to a skill that now lives elsewhere in this plan.

**Prompt**:
> In `catalog/skills/ai-development/rag-implementation/SKILL.md`, locate the Embedding Model Comparison table and the "Code-Specialized Embeddings" subsection around lines 366–379 (added by the abandoned plan's Phase 1 sub-task 1.2 part 2). Edits:
>
> 1. Keep the vendor enumeration (OpenAI, VoyageAI, Google, Ollama) — these are neutral ecosystem facts.
> 2. Remove the specifically-named `voyage-code-3` model. Generalize to "code-specialized embedding families are available from commercial providers; local alternatives exist via Ollama / ONNX for environments where data cannot leave the network."
> 3. Remove any forward-link to a future `code-semantic-search` skill that was added by the abandoned Phase 1. The actual reference to that skill now lives in Phase 8 of this plan and will be cross-linked from there.
>
> Acceptance: table no longer names `voyage-code-3`; no forward-link to `code-semantic-search` from this section.

---

#### 4.4 — De-brand the AST-aware chunking and Merkle subsections

**Objective**: Keep the technical content but strip upstream-repo file-path citations and "upstream reference uses" framing.

**Prompt**:
> In `catalog/skills/ai-development/rag-implementation/SKILL.md`, locate the "AST-Aware Chunking for Source Code" and "Incremental Re-Indexing with Content-Hash Merkle Trees" subsections around lines 203–214 (added by the abandoned plan's Phase 1 sub-task 1.2 part 3). Edits:
>
> 1. Remove references to `packages/core/src/sync/merkle.ts` and `synchronizer.ts` (external repo file paths).
> 2. Remove "upstream reference uses tree-sitter for 9 languages" phrasing — reword to "tree-sitter supports AST-based chunking across common languages including Python, TypeScript, Go, Rust, Java, C++, C#, JavaScript, and Scala."
> 3. Keep the technical content about why character splitters underperform on code and why Merkle-tree content-hash diffing reduces re-embed cost.
>
> Acceptance: no external file path references remain in these subsections; the technical concepts are preserved.

---

#### 4.5 — Testing and Stabilization

**Objective**: Verify complete de-branding and data-file integrity.

**Prompt**:
> Run:
>
> 1. `grep -i "zilliztech\|claude-context\|zilliz cloud\|voyage-code-3\|swe-bench\|8\.4k" catalog/skills/ai-development/rag-implementation/SKILL.md` returns zero matches.
> 2. `wc -l catalog/skills/ai-development/rag-implementation/SKILL.md` stays within the 1100-line cap (expect a small reduction from the current 1077 lines).
> 3. All code fences balanced (even count).
> 4. `make validate` clean.
> 5. All markdown links still resolve (internal cross-references survive the edits).
>
> Fix any regressions. Do not proceed to Phase 5 until all five pass.

---

### Phase 4 Exit Checklist

- [ ] External-source attribution grep returns zero matches
- [ ] File length within 1100-line cap
- [ ] Technical patterns preserved (hybrid BM25+RRF, AST chunking, Merkle indexing, code-specialized embeddings)
- [ ] `make validate` clean

---

## Phase 5: `/compare-project` Extension with Reverse-Engineering-First `/generate-plan` Handoff

**Goal**: Every future run of `/compare-project` must surface data-leak and outbound-call risk, assess reverse-engineering viability per adoption candidate, and when it chains into `/generate-plan` emit a plan sequencing reverse-engineer-first.
**Prerequisites**: Phase 1 (policy provides the decision tree Section 9 references).
**Stability Gate**: A hand-run of `/compare-project` on any small external repo produces a report with the new Section 9 populated; the skill's Quality Checklist rejects reports missing Section 9; a chain into `/generate-plan` produces a plan whose first phase is an RE-first or skill-native deliverable.

### Sub-tasks

#### 5.1 — Add Section 9 "Security and Risk Assessment" to the `/compare-project` output template

**Objective**: Insert a new 4-subsection security analysis into the command's output schema and renumber downstream sections.

**Prompt**:
> In `catalog/commands/compare-project.md`, locate the Phase 6 ("Write the report") section where the 12 output sections are defined. Insert a new Section 9 titled **"Security and Risk Assessment"** with four subsections:
>
> - **9.1 Threat Model Comparison** — side-by-side table: runtime deps added, outbound-call destinations, credentials required, whether source code / prompts / query text leaves the local machine, whether a new commercial relationship is required.
> - **9.2 Per-Item Risk Scorecard** — for each adoption candidate from Section 5, assign a risk tier (None / Low / Medium / High) with a one-sentence justification. Gate Section 10's recommendations on these tiers.
> - **9.3 Reverse-Engineering Viability Analysis** — for each candidate, classify per the MCP Registry Policy decision tree (`re-full`, `re-partial`, `skill-native`, `vendor-intrinsic`, `drop-outright`). Reference `AGENTS.md` MCP Registry Policy.
> - **9.4 Recommendation Ordering** — rank candidates: (a) `skill-native` wins first, (b) `re-full` / `re-partial` builds, (c) `vendor-intrinsic` with explicit "extremely trusted + extremely worth it" justification, (d) `drop-outright`.
>
> Renumber existing Sections 9 → 10, 10 → 11, 11 → 12, 12 → 13.
>
> Section 13 ("Risks and Considerations") gains a new N-item block titled **"Items explicitly NOT recommended for adoption (security / policy reasons)"** following the existing N1/N2/N3 convention.

---

#### 5.2 — Update `/compare-project` Step 8 handoff into `/generate-plan`

**Objective**: The handoff must pass a `reverse-engineer-first` flag and an explicit ordered adoption list derived from Section 9.4.

**Prompt**:
> In `catalog/commands/compare-project.md` Step 8 (chain into `/generate-plan`), update the handoff so it:
>
> 1. Always passes a `reverse-engineer-first=true` flag.
> 2. Passes the Section 9.4 ordered adoption list (not just the Section 10 P0/P1/P2/P3 tiering).
> 3. Emits a clarifying note in the Step 8 prompt: "The generated plan will sequence phases in RE-first order (skill-native → RE builds → vendor integrations → drops), not P-tier order."
>
> Acceptance: the Step 8 prompt references both the flag and the ordering; sample invocation commands in the command body reflect the flag.

---

#### 5.3 — Update the cross-project-comparison skill Quality Checklist

**Objective**: Make Section 9 and Section 9.4 ordering mandatory.

**Prompt**:
> In `catalog/skills/workflow/cross-project-comparison/SKILL.md`:
>
> 1. Extend the 6 core steps to 7 core steps by inserting "perform security and reverse-engineering assessment" between "gap analysis" and "adoption plan".
> 2. Extend the Quality Checklist with: "Section 9 present; all P0/P1 items risk-tiered AND RE-classified; Section 9.4 ordering matches the MCP Registry Policy decision tree."
> 3. Add a note that the skill now gates completion on Section 9 — a report missing it fails the checklist.
>
> Preserve the skill's existing frontmatter and other body sections.

---

#### 5.4 — Update `/generate-plan` to respect the RE-first flag

**Objective**: When `/generate-plan` is invoked with `reverse-engineer-first=true` from `/compare-project`, the generated plan must group phases in Section 9.4 order.

**Prompt**:
> In `catalog/commands/generate-plan.md`:
>
> 1. Add handling for the `reverse-engineer-first=true` flag passed from `/compare-project`. When set, the generated plan's phase sequencing must follow Section 9.4 order: skill-native items in the earliest phases, `re-full` / `re-partial` builds next, `vendor-intrinsic` adoptions last (with explicit justification), and `drop-outright` items listed in an "out-of-scope / not pursued" appendix.
> 2. Add a new From-Comparison-mode sub-step (0.5f or similar) documenting the RE-first flag propagation.
> 3. The generated plan's Overview section must explicitly name the MCP Registry Policy as the ordering constraint when the flag is set.
>
> Preserve all existing `/generate-plan` behavior for non-comparison invocations.

---

#### 5.5 — Testing and Stabilization

**Objective**: Hand-run `/compare-project` and `/generate-plan` against a small external repo to confirm the new behavior.

**Prompt**:
> 1. Run `/compare-project` against a small public MIT-licensed repo (the user can pick; if none offered, use a popular utility like `zeit/ms` or similar). Verify the output includes Section 9 with all four subsections populated; verify Section 9.4 orders per the decision tree.
> 2. Chain into `/generate-plan` via Step 8. Verify the generated plan's Phase 1 is an RE-first or skill-native deliverable (NOT a vendor integration), and the plan's Overview names the MCP Registry Policy as the ordering constraint.
> 3. Verify the backing skill's Quality Checklist rejects a report that has Section 9 removed (simulate by editing a generated report and re-running the skill).
> 4. `make validate` clean.
>
> Fix any regression. Do not proceed to Phase 6 until the hand-run passes.

---

### Phase 5 Exit Checklist

- [ ] `/compare-project` output template has Section 9 with all 4 subsections
- [ ] Step 8 passes `reverse-engineer-first=true` and the Section 9.4 ordered list
- [ ] `cross-project-comparison` skill Quality Checklist enforces Section 9
- [ ] `/generate-plan` sequences phases per Section 9.4 when the flag is set
- [ ] Hand-run smoke passes end-to-end

---

## Phase 6: Build `devai-code-search` MVP (Keyword-Only)

**Goal**: Ship a new internal MCP server at `extensions/devai-code-search/` delivering local code search with zero outbound calls, zero model downloads, zero API keys. Mirror `extensions/devai-skill-server/` layout. Keyword-only in v1.0.0; dense/hybrid deferred to v1.1.0.
**Prerequisites**: Phase 1 (policy justifies why this exists), Phase 3 (registry entry goes in).
**Stability Gate**: `cd extensions/devai-code-search && python -m pytest -q` passes with 20+ tests in <2s; integration smoke indexes the skill-server tree and returns results for a keyword query; Process Monitor audit during indexing shows zero outbound TCP.

### Sub-tasks

#### 6.1 — Scaffold the package layout

**Objective**: Create the package skeleton mirroring `devai-skill-server/` conventions.

**Prompt**:
> Create `extensions/devai-code-search/` with this layout (mirroring `extensions/devai-skill-server/`):
>
> ```
> extensions/devai-code-search/
> ├── pyproject.toml
> ├── README.md
> └── src/
>     └── devai_code_search/
>         ├── __init__.py
>         ├── __main__.py
>         ├── server.py
>         ├── indexer.py
>         ├── chunker.py
>         ├── search_keyword.py
>         ├── store.py
>         ├── config.py
>         └── types.py
> └── tests/
>     └── conftest.py
> ```
>
> `pyproject.toml` dependencies (pin exactly):
> ```toml
> dependencies = [
>     "mcp>=1.0.0",
>     "rapidfuzz>=3.5.0",
>     "pathspec>=0.12.0",
> ]
> ```
> `[project.optional-dependencies]`: `dev = ["pytest>=7.0", "pytest-asyncio>=0.21"]`.
> `[project.scripts]`: `devai-code-search = "devai_code_search.__main__:main"`.
>
> No torch / transformers / sentence-transformers / faiss / tree-sitter / onnxruntime / sqlite-vec in v1.0.0. All three declared deps ship prebuilt Windows wheels (zero C-extension compile risk).
>
> `README.md` documents the keyword-only posture and notes that hybrid retrieval is planned for v1.1.0 (via `fastembed` + `sqlite-vec`).

---

#### 6.2 — Implement `types.py`, `config.py`, `store.py`

**Objective**: Pure data-plumbing layer with high test coverage; no logic besides serialization.

**Prompt**:
> Implement the three data-plumbing modules:
>
> - `types.py` (~50 LOC): `@dataclass` definitions for `Chunk` (file path, start_line, end_line, text), `IndexManifest` (root, file_hashes dict, indexed_at, total_chunks), `SearchResult` (chunk, score, rank), `IndexStatus` (state enum, files_processed, total_files, last_updated, error optional).
> - `config.py` (~60 LOC): env-var resolution for `DEVAI_HUB_ROOT`. Mirror the pattern used by `extensions/devai-skill-server/src/devai_skill_server/config.py`.
> - `store.py` (~120 LOC): pickled index + JSON manifest persistence under `<root>/.devai/code-index/`. File-lock via `msvcrt.locking` on Windows and `fcntl` on POSIX to prevent concurrent re-index corruption. Corrupt-store fallback returns an empty index rather than raising.
>
> Every function has type hints. No mutable default arguments. Module docstrings.

---

#### 6.3 — Implement `chunker.py`

**Objective**: Recursive character splitter with language-aware separators. Zero dependencies beyond stdlib + `pathspec`.

**Prompt**:
> Implement `chunker.py` (~120 LOC) as a recursive character splitter with 600-char target window and 80-char overlap. Separator preference (in order): `\n\nclass `, `\n\ndef `, `\nfunction `, `\npublic `, `{`, `}`, `\n\n`, `\n`, ` `. Handle edge cases: empty file, single-line file, file larger than 1 MB (reject), binary file (reject via UTF-8 decode attempt).
>
> Function signature: `def chunk_text(text: str, file_path: str) -> list[Chunk]` returning `types.Chunk` instances with file path and start/end line numbers.

---

#### 6.4 — Implement `indexer.py`

**Objective**: Walk a codebase, respect ignore files, hash each file, chunk, and persist.

**Prompt**:
> Implement `indexer.py` (~180 LOC):
>
> - `walk(root: Path) -> Iterator[Path]`: walks files under `root`, respects `.gitignore` and `.devaiignore` via `pathspec`. Default-excludes: `node_modules/`, `.venv/`, `dist/`, `build/`, `__pycache__/`, `*.min.js`, `*.lock`, files >1 MB, files failing UTF-8 decode.
> - `hash_file(path: Path) -> str`: SHA-256 hex.
> - `index_codebase(root: Path, force: bool = False) -> IndexStatus`: walks, hashes, skips unchanged files (hash-match with prior manifest), chunks new/modified files, persists to store. Runs in a background thread; returns an `IndexStatus` handle pollable via `get_indexing_status`. File-lock guards concurrent invocations (corrupt manifest if two clients race).
> - `get_indexing_status(root: Path) -> IndexStatus`: reads the current state from the manifest.
>
> First index on a 10k-file repo should complete in 5–20s on a cold cache on Windows. Status updates are posted every N files (tune N for responsive polling).

---

#### 6.5 — Implement `search_keyword.py`

**Objective**: Inverted-index lookup + rapidfuzz scoring. No dense vectors in v1.0.0.

**Prompt**:
> Implement `search_keyword.py` (~100 LOC) mirroring the pattern in `extensions/devai-skill-server/src/devai_skill_server/search_keyword.py`:
>
> - Build an inverted index from the chunked corpus (token → set of chunk IDs). Token = lowercase alphanumeric + underscore.
> - `search(query: str, limit: int = 10) -> list[SearchResult]`: tokenize query, compute BM25-ish score per chunk (token-frequency adjusted by chunk length), apply `rapidfuzz` fuzzy-match boost for near-misses on identifier-like tokens, return top-K.
> - Handle empty query (return empty list), multi-token AND semantics.

---

#### 6.6 — Wire `server.py` with FastMCP

**Objective**: Expose the 4 MCP tools (`index_codebase`, `search_code`, `clear_index`, `get_indexing_status`) via the `mcp` Python SDK.

**Prompt**:
> Implement `server.py` (~200 LOC) using FastMCP. Mirror the wiring in `extensions/devai-skill-server/src/devai_skill_server/server.py`. Expose exactly four tools:
>
> - `index_codebase(root: str, force: bool = False) -> IndexStatus`
> - `search_code(query: str, mode: str = "keyword", limit: int = 10) -> list[SearchResult]` — v1.0.0 accepts `mode="keyword"` only; any other mode raises `NotImplementedError` with message "Hybrid retrieval planned for v1.1.0 — use mode='keyword' for now."
> - `clear_index(root: str) -> None`
> - `get_indexing_status(root: str) -> IndexStatus`
>
> `__main__.py` (~20 LOC) is the module entrypoint. `index_codebase` kicks off a background thread and returns a status handle so the MCP event loop is never blocked.

---

#### 6.7 — Register in `mcp-servers.json` and both installers

**Objective**: Make `devai-code-search` discoverable and installed the same way `devai-skill-server` is.

**Prompt**:
> 1. In `catalog/mcp-configs/mcp-servers.json`, add a `devai-code-search` entry alongside `devai-skill-server`:
>    ```json
>    "devai-code-search": {
>      "command": "python",
>      "args": ["-m", "devai_code_search"],
>      "env": {"DEVAI_HUB_ROOT": "${DEVAI_HUB_ROOT}"},
>      "_comment": "DevAI-Hub local-only code-search MCP. Keyword search over a repo with content-hash incremental indexing. Zero outbound calls, zero API keys, zero model downloads. Index stored at <repo>/.devai/code-index/. Requires Python 3.10+. v1.0.0 keyword-only; hybrid retrieval planned for v1.1.0. 5-question audit: runs locally as a Python subprocess; makes no outbound calls; requires no API keys; transmits no source code anywhere; no vendor relationship required."
>    }
>    ```
>    `mcpServers` count goes 11 → 12.
> 2. In `scripts/installer.sh`, find the existing install block for `devai-skill-server`. Add a parallel `pip install -e extensions/devai-code-search` step.
> 3. In `scripts/installer.ps1`, add the same install step using PowerShell syntax, mirroring the `devai-skill-server` block.
> 4. Both installer edits must pass `bash -n` (.sh) and PowerShell AST parse (.ps1). Run `shellcheck --severity=warning scripts/installer.sh` expecting exit 0.

---

#### 6.8 — Testing and Stabilization

**Objective**: Comprehensive pytest suite covering correctness + regression + integration + network-audit.

**Prompt**:
> Write pytest tests under `extensions/devai-code-search/tests/`:
>
> - `test_chunker.py` — chunk-size bounds, overlap correctness, separator preference, empty file, single-line, binary rejection, oversized rejection.
> - `test_indexer.py` — first-index walks all files, second-index skips unchanged (hash match), modified file re-chunks, deleted file removed from index, `.gitignore` and `.devaiignore` respected, concurrent invocation is serialized (file lock).
> - `test_search_keyword.py` — exact match ranks first, fuzzy match finds close tokens, multi-token AND, empty query, result limit.
> - `test_store.py` — pickle round-trip, manifest JSON schema stability, corrupt store falls back to empty.
> - `test_server_integration.py` — single end-to-end: call `index_codebase` on a small fixture tree, `search_code`, assert; `clear_index`; `get_indexing_status` returns idle. Assert zero sockets opened during the run (use `mock.patch` on `socket.socket` or a `BaseHTTPServer` monkeypatch to fail-fast on any network activity).
>
> Target: 20+ tests passing in <2s. `cd extensions/devai-code-search && python -m pytest -q`.
>
> Run on a clean Windows venv: `pip install -e extensions/devai-code-search` must complete with no C-extension compilation.
>
> Process Monitor audit (manual, documented in README): indexing a 100-file fixture tree shows zero DNS lookups and zero outbound TCP connections.

---

### Phase 6 Exit Checklist

- [ ] `extensions/devai-code-search/` package exists with 8 source files + pyproject.toml + README + tests
- [ ] Pure-local: no outbound calls; no API keys; no model downloads
- [ ] 20+ pytest tests pass in <2s
- [ ] Windows venv install completes with no C-extension compile
- [ ] Registered in `mcp-servers.json` (count: 12) and both installers
- [ ] Process Monitor / strace audit shows zero outbound TCP during indexing

---

## Phase 7: `devai-web-fetch` MCP + LLM-Native Skill Replacements for `context7` / `magic-ui`

**Goal**: Reverse-engineer the remaining dropped 3rd-party capabilities into local / skill-only deliverables per the matrix.
**Prerequisites**: Phase 2 (matrix greenlights these deliverables), Phase 6 (`devai-code-search` provides the reference pattern for `devai-web-fetch`'s package layout).
**Stability Gate**: `devai-web-fetch` pytest suite passes; SSRF denylist blocks RFC 1918; both new skills pass `make validate`; skill-server MCP returns the two new skills on relevant queries; total skill count moves to 186.

### Sub-tasks

#### 7.1 — Build `devai-web-fetch` (reverse-engineered `firecrawl`)

**Objective**: New internal MCP providing HTTP fetch + readability extraction, scoped to user-specified URLs with SSRF protection.

**Prompt**:
> Create `extensions/devai-web-fetch/` mirroring the layout of `extensions/devai-code-search/`. Implementation:
>
> - `pyproject.toml` dependencies: `mcp>=1.0.0`, `httpx>=0.27.0`, `beautifulsoup4>=4.12.0`, `readability-lxml>=0.8.1`, `pyyaml>=6.0`. All ship prebuilt Windows wheels.
> - `fetcher.py`: `httpx.AsyncClient` with 30s timeout, 5 MB max response size, no cookies, no auth headers.
> - `extractor.py`: `beautifulsoup4` + `readability-lxml` for main-content extraction. Returns title, text, raw HTML (optional).
> - `ssrf_guard.py`: URL allowlist / denylist via `~/.devai/web-fetch.yaml`. Block RFC 1918 (`10/8`, `172.16/12`, `192.168/16`), localhost, link-local, and `file://` by default.
> - `server.py`: FastMCP wiring exposing `fetch_url(url: str, render_js: bool = False, extract_mode: str = "readability") -> FetchResult`. `render_js=True` raises `NotImplementedError` (Playwright deferred to v1.1.0).
>
> Registry entry in `catalog/mcp-configs/mcp-servers.json`:
> ```json
> "devai-web-fetch": {
>   "command": "python",
>   "args": ["-m", "devai_web_fetch"],
>   "env": {"DEVAI_HUB_ROOT": "${DEVAI_HUB_ROOT}"},
>   "_comment": "DevAI-Hub local-only web-fetch MCP. HTTP fetch + readability extraction. Data destination is the URL itself; no third-party processor. RFC 1918 blocked by default for SSRF safety. 5-question audit: runs locally; makes outbound HTTPS only to user-specified URLs; no API keys; transmits only the user-provided URL; no vendor relationship."
> }
> ```
> `mcpServers` count goes 12 → 13.
>
> Install-step registration in both `scripts/installer.sh` and `scripts/installer.ps1` parallel to `devai-code-search`.
>
> Pytest suite: local fixture HTTP server serving known HTML; SSRF denylist blocks `http://127.0.0.1`, `http://10.0.0.1`, `file:///etc/passwd`; integration test fetches against the fixture server and asserts extracted title.

---

#### 7.2 — Author `ui-component-generation` skill (replaces `magic-ui`)

**Objective**: LLM-native skill that instructs the agent to generate UI components directly, since the agent IS an LLM. Zero code; zero MCP.

**Prompt**:
> Create `catalog/skills/developer-experience/ui-component-generation/SKILL.md` (~150 lines) per the `AGENTS.md` "Adding a New Skill" contract:
>
> - YAML frontmatter: `name: ui-component-generation`; `description: Generate UI components by prompting the agent's own LLM — no external generation service required`; `summary_l0: "Generate framework-specific UI components with accessibility baseline via direct LLM prompting"`; `overview_l1: "…" (≤ 150 words, no external attribution)`.
> - **When to Use This Skill** with 5–7 trigger scenarios + explicit "When NOT to use" (larger architecture questions belong to `frontend-ui-engineering`).
> - **Instructions**: component-spec prompting patterns, framework-specific conventions (React, Vue, Svelte, Astro), accessibility baseline checklist (ARIA labels, keyboard nav, color contrast), handling design tokens, typed props.
> - **Common Rationalizations** table (3–5 rows).
> - **Verification** binary checklist.
> - **Related Skills**: link to `frontend-ui-engineering`, `react-expert`, `vue-expert`, `svelte-expert`, `astro-expert`.
>
> The skill explicitly notes that this reverse-engineers one common capability that was previously wrapped as an external MCP service, using only the agent's existing LLM.
>
> Register in `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`. Skill count: 184 → 185.
>
> Grep audit: `grep -i "context7\|upstash\|firecrawl\|21st.*dev\|magic-ui" catalog/skills/developer-experience/ui-component-generation/SKILL.md` returns zero matches.

---

#### 7.3 — Author `local-docs-lookup` skill (partial replacement for `context7`)

**Objective**: Patterns for grounding agent responses in local documentation without calling a 3rd-party service.

**Prompt**:
> Create `catalog/skills/research/local-docs-lookup/SKILL.md` (~120 lines) per the `AGENTS.md` contract:
>
> - YAML frontmatter with appropriate `summary_l0` and `overview_l1` (no external attribution).
> - **When to Use This Skill** covering: grounding agent answers against vendored `node_modules/.../README.md`, `python -m pydoc <module>`, `go doc`, `help()` in REPLs, project-shipped `docs/` trees, local man pages.
> - **When NOT to use**: when the docs are genuinely out-of-date locally and the user accepts the risk of grounding on stale info; for those cases, mention that the user can invoke `devai-web-fetch` on a known-public documentation URL (explicit, single-URL, user-scoped).
> - **Instructions**: structured lookup sequence (vendored READMEs → REPL introspection → local docs tree → project-shipped examples → web-fetch on a user-approved URL as a last resort).
> - **Common Rationalizations** table.
> - **Verification** binary checklist.
> - **Related Skills**: `rag-implementation`, `context-manager`.
>
> Note explicitly that this skill replaces one specific use case previously wrapped as a 3rd-party MCP (library-doc freshness) and does not recreate a continuously-updated library index — that tradeoff is acknowledged.
>
> Register in `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`. Skill count: 185 → 186.
>
> Grep audit: same as 7.2.

---

#### 7.4 — Testing and Stabilization

**Objective**: Verify web-fetch correctness + SSRF denylist + skill registration parity.

**Prompt**:
> Run:
>
> 1. `cd extensions/devai-web-fetch && python -m pytest -q` — tests pass including SSRF denylist tests.
> 2. `python -m json.tool catalog/mcp-configs/mcp-servers.json` exit 0; `mcpServers` count == 13.
> 3. `data/skills.json` skill count == 186.
> 4. `data/SKILL_INDEX.md` and `data/marketplace.json` skill counts match.
> 5. Skill-server MCP smoke: `search_skills(query="ui component generation")` returns `ui-component-generation` in top 3; `search_skills(query="local documentation lookup")` returns `local-docs-lookup` in top 3.
> 6. Process Monitor audit of `devai-web-fetch` fetch against a fixture server shows exactly one outbound connection (to the fixture server itself, not to any 3rd party).
> 7. Installer static verification: both installers register `devai-web-fetch` install step.
> 8. `make validate` clean.
>
> Fix regressions. Do not proceed to Phase 8 until all eight pass.

---

### Phase 7 Exit Checklist

- [ ] `extensions/devai-web-fetch/` package exists with SSRF protection
- [ ] Registered in `mcp-servers.json` (count: 13) and both installers
- [ ] Two new skills registered (total: 186)
- [ ] Grep audit clean on both new skills
- [ ] Skill-server MCP returns both new skills on semantic queries

---

## Phase 8: Reverse-Engineered `code-semantic-search` Skill (De-branded)

**Goal**: Salvages the abandoned plan's Phase 3 — a skill documenting the semantic-code-search pattern, re-pointed at DevAI-Hub's own `devai-code-search` as the reference implementation.
**Prerequisites**: Phase 4 (de-brand must be done before this skill references patterns from `rag-implementation`), Phase 6 (the reference-implementation link targets the Phase 6 package).
**Stability Gate**: `grep -i "zilliztech\|claude-context\|8\.4k\|SWE-bench" catalog/skills/ai-development/code-semantic-search/SKILL.md` returns zero matches; skill-server MCP returns the new skill on `search_skills(query="code semantic search")`; skill count moves to 187.

### Sub-tasks

#### 8.1 — Author the `code-semantic-search` SKILL.md

**Objective**: Full skill file with frontmatter, required body sections, and generic descriptive references.

**Prompt**:
> Create `catalog/skills/ai-development/code-semantic-search/SKILL.md` (~400 lines; cap 800). Required content per `AGENTS.md` contract:
>
> - YAML frontmatter:
>   - `name: code-semantic-search`
>   - `description: Semantic search over source-code corpora using code-specialized embeddings, AST chunking, and hybrid BM25+dense retrieval`
>   - `summary_l0: "Retrieve relevant code from large repositories using hybrid semantic search and AST-aware chunking"`
>   - `overview_l1: "..."` — a ≤150-word paragraph describing the capability with ZERO external attribution. Reference DevAI-Hub's internal `devai-code-search` MCP as the reference implementation.
> - Title + 2-paragraph intro.
> - **When to Use This Skill** + explicit "When NOT to use" ("codebase fits in context — use direct reads instead; indexing overhead is not free").
> - **Instructions** numbered steps covering:
>   (a) embedding-model selection — prefer local Ollama / ONNX in regulated environments; external embedding APIs must pass the MCP Registry Policy decision tree.
>   (b) chunking — AST where tree-sitter is available; recursive character-splitter fallback; note that `devai-code-search` ships recursive-fallback in v1.0.0 and will add tree-sitter in v1.1.0.
>   (c) vector store — local self-hosted only; FAISS / sqlite-vec / Chroma in-process; avoid managed vendor services.
>   (d) hybrid retrieval — BM25 + dense with RRF; reciprocal-rank-fusion formula.
>   (e) incremental re-indexing — content-hash Merkle-tree.
>   (f) rerank strategies.
>   (g) pitfalls — stale indexes, chunk-size misconfiguration, embedding cost at first index, language-coverage gaps in AST splitters.
> - **Common Rationalizations** table (3–5 rows): "grep is enough" / "recursive splitter works" / "re-index every commit" with concrete failure-mode rebuttals.
> - **Verification** binary checklist — embedding model documented, chunking strategy + fallback configured, vector-store index type correct, incremental indexing enabled, 3 natural-language queries return expected files.
> - **Related Skills**: `rag-implementation`, `context-manager`, `context-engineering`, and the `devai-code-search` registry entry.
>
> Acceptance: grep audit returns zero matches for `zilliztech`, `claude-context`, `8.4k`, `SWE-bench`. Only MCP reference is `devai-code-search`. Only "Reference implementation" phrase links to `extensions/devai-code-search/`.

---

#### 8.2 — Register in `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`

**Objective**: Propagate the new skill through the 3 registry files per `AGENTS.md` step 4.

**Prompt**:
> 1. `data/SKILL_INDEX.md`: add one row to the table alphabetically inside the `ai-development` category block (after `claude-agent-sdk`, before `context-engineering`).
> 2. `data/skills.json`: add an entry to the `skills` array mirroring the shape of the existing `ai-agent-development` entry — name, title, description, summary_l0, overview_l1 (verbatim from SKILL.md frontmatter), version `1.0.0`, author `Benjamin Dourthe`, category `ai-development`, language `Multi-language`, tags `["rag","retrieval","embeddings","code-search","mcp"]`, priority `MEDIUM`, path and file pointing at the new SKILL.md, size (lines, tokens_estimate), status `production`, security `{structural: 100, integrity: 100, semantic: 95}`. Increment `total_skills` top-level field if present.
> 3. `data/marketplace.json`: increment the `ai-development` category's `skill_count` by 1 and `statistics.total_skills` by 1.
>
> Acceptance: `python -c "import json; d=json.load(open('data/skills.json')); assert len(d['skills']) == 187"` passes; the three registry files agree on the skill count.

---

#### 8.3 — Testing and Stabilization

**Objective**: Verify skill registration + skill-server discoverability + grep audit.

**Prompt**:
> Run:
>
> 1. `make validate` clean.
> 2. `make test` clean.
> 3. Consistency: skill counts in `SKILL_INDEX.md` (rows − header), `skills.json` (`len(skills)`), `marketplace.json` (`total_skills`) all == 187.
> 4. Skill-server MCP smoke: `search_skills(query="code semantic search")` returns `code-semantic-search` in top 3.
> 5. Markdown link audit on the new SKILL.md: every internal `](...md)` link resolves.
> 6. Grep audit: `grep -i "zilliztech\|claude-context\|8\.4k\|SWE-bench\|zilliz cloud\|voyage-code-3" catalog/skills/ai-development/code-semantic-search/SKILL.md` returns zero matches.
>
> Do not proceed to Phase 9 until all six pass.

---

### Phase 8 Exit Checklist

- [ ] `catalog/skills/ai-development/code-semantic-search/SKILL.md` exists with all required body sections
- [ ] 3 registry files updated; counts consistent at 187
- [ ] Grep audit clean
- [ ] Skill-server MCP returns the skill on semantic query
- [ ] `make validate` + `make test` clean

---

## Phase 9: Cross-Link Existing Context Skills to `code-semantic-search`

**Goal**: Surface the new skill through two neighboring skills. Salvaged from the abandoned plan's Phase 4.
**Prerequisites**: Phase 8 (target skill must exist).
**Stability Gate**: Both edited files have exactly one Related Skills entry pointing at `code-semantic-search`; line-count caps respected (context-manager <=440, context-engineering <=158); markdown links resolve.

### Sub-tasks

#### 9.1 — Add Related Skills entry in `context-manager/SKILL.md`

**Objective**: Frame `code-semantic-search` as the primary escape valve when a repo exceeds the context window.

**Prompt**:
> In `catalog/skills/orchestration/context-manager/SKILL.md` (432 lines), locate or create the Related Skills section at the end of the body. Add:
>
> ```
> - `code-semantic-search` (`catalog/skills/ai-development/code-semantic-search/SKILL.md`) — when the repo exceeds the model's context window, retrieval over code chunks is the primary escape valve. Use `code-semantic-search` to produce a ranked chunk set; feed the top-K into the session. DevAI-Hub's internal `devai-code-search` MCP is the reference implementation (local-only, zero outbound calls).
> ```
>
> Keep file length ≤ 440. Do not touch other content. Markdown link to the Phase 8 skill must resolve.

---

#### 9.2 — Add Related Skills entry in `context-engineering/SKILL.md`

**Objective**: Frame `code-semantic-search` as retrieval-based context shaping for source-code corpora.

**Prompt**:
> In `catalog/skills/ai-development/context-engineering/SKILL.md` (148 lines), locate or create the Related Skills section. Add:
>
> ```
> - `code-semantic-search` (`catalog/skills/ai-development/code-semantic-search/SKILL.md`) — retrieval-based context shaping for source-code corpora; specialized over the general `rag-implementation` skill. Paired with DevAI-Hub's internal `devai-code-search` MCP.
> ```
>
> Keep file length ≤ 158. Link must resolve.

---

#### 9.3 — Testing and Stabilization

**Objective**: Verify both cross-links are in place.

**Prompt**:
> Run:
>
> 1. `grep -c code-semantic-search catalog/skills/orchestration/context-manager/SKILL.md` returns 1.
> 2. `grep -c code-semantic-search catalog/skills/ai-development/context-engineering/SKILL.md` returns 1.
> 3. Line-count caps: `wc -l catalog/skills/orchestration/context-manager/SKILL.md` ≤ 440; `wc -l catalog/skills/ai-development/context-engineering/SKILL.md` ≤ 158.
> 4. Markdown links to the Phase 8 skill resolve (the file exists).
> 5. `make validate` clean.

---

### Phase 9 Exit Checklist

- [ ] Both context skills have the new Related Skills entry
- [ ] Line caps respected
- [ ] `make validate` clean

---

## Phase 10: Internal MCP Benchmark Harness

**Goal**: Benchmark every internal MCP in a single harness. Pure internal, zero network. Reverse-engineered from the abandoned plan's Phase 5 with scope widened.
**Prerequisites**: Phase 6 (`devai-code-search` exists), Phase 7 (`devai-web-fetch` exists).
**Stability Gate**: `make benchmark` runs clean against all 3 internal MCPs; `data/benchmarks/mcp.json` appended with a fresh run; pytest coverage passes; network-activity guard asserts no outbound calls for the non-fetch MCPs.

### Sub-tasks

#### 10.1 — Author `scripts/devai_mcp_benchmark.py`

**Objective**: Type-hinted, network-guarded benchmark script covering all 3 internal MCPs.

**Prompt**:
> Create `scripts/devai_mcp_benchmark.py` (~300 LOC). Structure:
>
> - Module docstring + type hints throughout. No mutable default arguments.
> - Start each internal MCP as a subprocess (or in-process where simpler).
> - Fixed query suite per server:
>   - `devai-skill-server`: `search_skills` (3 queries: "code semantic search", "security audit", "test generation"), `get_skill` (2: "code-semantic-search", "rag-implementation"), `list_categories`, `list_bundles`, `get_bundle` (first bundle).
>   - `devai-code-search`: `index_codebase` (cold + warm), `search_code` (3 keyword queries), `get_indexing_status`, `clear_index`.
>   - `devai-web-fetch`: `fetch_url` against a local fixture HTTP server (deterministic; no real network).
> - `time.perf_counter()` per call; N=5 iterations; report min / median / p95 / max in ms per tool.
> - JSON output: `timestamp`, `platform`, `python_version`, `skill_count`, `code_index_file_count`, `results` (nested per server, per tool).
> - CLI flags: `--append` (writes to `data/benchmarks/mcp.json`, retains last 10 runs), `--iterations=N`, `--quiet` (emit only summary JSON), `--server=<skill-server|code-search|web-fetch|all>` (default `all`).
> - **Network-activity guard**: before running the `devai-skill-server` and `devai-code-search` portions, monkeypatch `socket.socket.connect` to raise on any call. Fail-fast if a connection is attempted during these portions. Disable the guard for the `devai-web-fetch` portion (outbound to fixture server is expected).
>
> Acceptance: script runs clean against a fresh checkout; output is valid JSON; total runtime < 20s at N=5; the network-activity guard successfully detects an attempted outbound call (test this by deliberately injecting one and asserting the guard fires).

---

#### 10.2 — Add the `benchmark` target to `Makefile`

**Objective**: `make benchmark` one-liner plus `.PHONY` registration.

**Prompt**:
> In `Makefile`, add a new target after `test`:
>
> ```
> benchmark: ## Benchmark internal MCPs
> 	@echo "Benchmarking internal MCPs..."
> 	@python scripts/devai_mcp_benchmark.py --append --quiet
> 	@echo "Benchmark complete. Results: data/benchmarks/mcp.json"
> ```
>
> Add `benchmark` to the `.PHONY` declaration at the top of the file.
>
> Acceptance: `make benchmark` executes end-to-end; `make help` shows the new target.

---

#### 10.3 — Register the script in both installers

**Objective**: Per `AGENTS.md` "Installer-Aware Changes", scripts under `scripts/*.py` MUST be registered by explicit name in both installers.

**Prompt**:
> 1. In `scripts/installer.sh`, find the existing `safe_copy` block for `generate_report.py` (around line 1395 per `AGENTS.md`). Add a parallel block for `devai_mcp_benchmark.py` targeting `~/.devai-hub/scripts/devai_mcp_benchmark.py`.
> 2. In `scripts/installer.ps1`, find the corresponding `Safe-Copy` block for `generate_report.py` (around line 1656). Add a parallel line for `devai_mcp_benchmark.py`.
> 3. Both installer edits must pass `bash -n` / PowerShell AST parse. `shellcheck --severity=warning scripts/installer.sh` exit 0.

---

#### 10.4 — Author pytest coverage

**Objective**: Test the benchmark script's shape + CLI flag behavior + network guard.

**Prompt**:
> Create `extensions/devai-skill-server/tests/test_mcp_benchmark.py` (co-located with existing tests). Tests:
>
> 1. Mock each MCP's tool calls via `monkeypatch` (preferred over `unittest.mock.patch` per the Python test rule). Assert the query suite size ≥ documented count.
> 2. Assert output JSON shape has all top-level keys.
> 3. Assert `--iterations=1` produces exactly `N_queries × 1` calls.
> 4. Assert `--append` writes to the expected path (via `tmp_path`).
> 5. Assert `--server=skill-server` filters correctly (only skill-server queries executed).
> 6. Assert the network-activity guard fires when an outbound connection is attempted during the `devai-skill-server` / `devai-code-search` portions.
>
> Target: 6+ tests passing in <3s. `make test` remains clean.

---

#### 10.5 — Testing and Stabilization

**Objective**: End-to-end verification.

**Prompt**:
> Run:
>
> 1. `python scripts/devai_mcp_benchmark.py --server=all` runs clean; output is valid JSON; total runtime < 20s.
> 2. `make benchmark` runs clean; appends to `data/benchmarks/mcp.json`.
> 3. `make test` clean (new test joins the existing suite).
> 4. `shellcheck --severity=warning scripts/installer.sh` exit 0.
> 5. `bash -n scripts/installer.sh` + PowerShell AST parse of `scripts/installer.ps1` both clean.
> 6. `make validate` clean.
> 7. `data/benchmarks/` is gitignored (if not, add `.gitignore` entry).
> 8. Static installer verification: `grep -n devai_mcp_benchmark scripts/installer.sh scripts/installer.ps1` returns matches in both files.
>
> Fix any regression. Do not proceed to Phase 11 until all eight pass.

---

### Phase 10 Exit Checklist

- [ ] `scripts/devai_mcp_benchmark.py` runs; network guard fires on any outbound call during non-fetch portions
- [ ] `make benchmark` executes and writes `data/benchmarks/mcp.json`
- [ ] Pytest test for the script passes
- [ ] Both installers register the script
- [ ] `data/benchmarks/` is gitignored

---

## Phase 11: Release v1.0.0

**Goal**: Migrate `CHANGELOG.md`, bump 14 canonical files from `0.9.7 → 1.0.0` (skipping 0.9.8), author `docs/archive/v1/v1.0/RELEASE_NOTES.md`, update memory, create the git tag.
**Prerequisites**: Phases 1–10 all merged or staged together for the release commit.
**Stability Gate**: `make validate` + `make test` + `make lint` all clean; `mcp-servers.json` count == 13; skill count == 187; all grep audits clean; tag exists locally.

### Sub-tasks

#### 11.1 — Migrate `CHANGELOG.md` `[Unreleased]` to `[1.0.0]`

**Objective**: Rename the `[Unreleased]` heading, add a fresh empty `[Unreleased]` above, and populate the new `[1.0.0]` section.

**Prompt**:
> In `CHANGELOG.md`:
>
> 1. Rename `## [Unreleased]` → `## [1.0.0] - <release-date>` using today's date.
> 2. Insert a new empty `## [Unreleased]` section immediately above.
> 3. Under `[1.0.0]`, organize by the existing `### Added` / `### Changed` / `### Removed (Breaking)` convention:
>    - **Added**: MCP Registry Policy with reverse-engineering-first decision tree; Reverse-Engineering Matrix at `docs/policy/mcp-reverse-engineering-matrix.md`; new internal MCPs `devai-code-search` (keyword-only MVP) and `devai-web-fetch` (SSRF-guarded); three new skills `code-semantic-search`, `ui-component-generation`, `local-docs-lookup`; `/compare-project` Security & Risk Assessment section + RE-first `/generate-plan` handoff; `scripts/devai_mcp_benchmark.py` + `make benchmark` + pytest coverage.
>    - **Changed**: `rag-implementation` skill de-branded; `context-manager` and `context-engineering` cross-linked to `code-semantic-search`; `infrastructure/integrations/README.md` policy-compliant; `guides/MCP_DEVELOPMENT_SERVERS.md` rewritten; 7 platform-template surfaces carry the MCP Registry Policy in lockstep; `mcp-servers.json` kept-entries' `_comment` fields now include the 5-question audit.
>    - **Removed (Breaking)**: four 3rd-party MCP registry entries (`context7`, `exa-web-search`, `firecrawl`, `magic-ui`); the Phase 2 `claude-context` registry entry (reverted); the v0.9.7 `adoption-claude-context` plan Phases 3–6 (superseded by this plan).
>
> Preserve Keep-a-Changelog format. ASCII-only (no em-dashes, curly quotes, etc.).

---

#### 11.2 — Version-bump sweep across the 14 canonical files

**Objective**: Replace `0.9.7` → `1.0.0` in the version-holding positions of the 14 canonical files identified in `MEMORY.md`.

**Prompt**:
> Per `MEMORY.md` (`project_release_v097`), update exactly 14 files from `0.9.7` → `1.0.0`:
>
> 1. `.claude-plugin/plugin.json`
> 2. `.claude-plugin/marketplace.json`
> 3. `data/templates.json`
> 4. `data/marketplace.json`
> 5. `scripts/installer.ps1` (version variable near top)
> 6. `scripts/installer.sh` (version variable near top)
> 7. `catalog/hooks/session-start.sh` (banner)
> 8. `catalog/skills/README.md`
> 9. `infrastructure/tools/README.md`
> 10. `infrastructure/hooks/README.md`
> 11. `infrastructure/integrations/README.md`
> 12. `guides/SUBAGENTS_GUIDE.md`
> 13. `README.md`
> 14. `README_zh.md`
>
> Rules:
> - Update only at version-reference sites (not in changelog history or `docs/v0.*.*/` historical references).
> - If the count diverges from 14, update the `MEMORY.md` `project_release_v097` entry and annotate the discrepancy.
>
> Verification: `grep -rn '0\.9\.7' --include='*.md' --include='*.json' --include='*.sh' --include='*.ps1'` post-change shows only historical references (in `CHANGELOG.md` prior entries, `docs/v0.9.*/` directories, `docs/DEVLOG.md` prior entries).

---

#### 11.3 — Author `docs/archive/v1/v1.0/RELEASE_NOTES.md`

**Objective**: Release notes explaining the reverse-engineering-first posture, breaking removals, new MCPs, new skills, migration steps, and v1.1.0 roadmap.

**Prompt**:
> Create `docs/archive/v1/v1.0/RELEASE_NOTES.md` (~150–250 lines). Sections:
>
> 1. **Executive summary** — v1.0.0 is a reverse-engineering-first security-hardening release and the first stable milestone for DevAI-Hub. Call out the breaking MCP registry removals.
> 2. **MCP Registry Policy summary** — decision tree + 5-question audit, linked to the full `AGENTS.md` section.
> 3. **Reverse-Engineering Matrix** — pointer to `docs/policy/mcp-reverse-engineering-matrix.md` + headline counts (11 kept + 2 new internal + 4 dropped + 5 deferred to v1.1.0+).
> 4. **New internal MCPs** — `devai-code-search` and `devai-web-fetch` with install instructions + tool surfaces + policy-compliance notes.
> 5. **New skills** — `code-semantic-search`, `ui-component-generation`, `local-docs-lookup`.
> 6. **De-branded `rag-implementation`** skill.
> 7. **`/compare-project` extension** with Section 9 + RE-first `/generate-plan` handoff.
> 8. **Benchmark harness**.
> 9. **Migration notes** — re-run installer; dropped registry entries require manual re-add if user still wants them.
> 10. **v1.1.0 roadmap** — dense/hybrid retrieval on `devai-code-search`; Playwright rendering in `devai-web-fetch`; vendor-wrapper reverse-engineering per matrix.

---

#### 11.4 — Update `MEMORY.md`

**Objective**: Add `project_release_v100` entry; forward-link from `project_release_v097`.

**Prompt**:
> In `~/.claude/projects/<project-key>/memory/` (the auto-memory directory for this project):
>
> 1. Create `project_release_v100.md` following the existing memory-file schema (frontmatter: name, description, type: project). Body summarizes this release: reverse-engineering-first security hardening; breaking removal of 4 registry entries; 2 new internal MCPs; 3 new skills; 14-file version-bump; release notes path.
> 2. Update `project_release_v097.md` with a forward-link noting v0.9.8 was skipped and v1.0.0 absorbed all v0.9.8 scope.
> 3. Add a line to `MEMORY.md` index file pointing at the new memory.
>
> Acceptance: `MEMORY.md` index shows both `project_release_v097` and `project_release_v100` entries with cross-references.

---

#### 11.5 — Final validation sweep

**Objective**: Gate the release on a complete verification suite.

**Prompt**:
> Run the full validation sweep:
>
> 1. `make validate` clean.
> 2. `make test` clean.
> 3. `make lint` clean.
> 4. `make benchmark` runs; `data/benchmarks/mcp.json` has a fresh entry.
> 5. `python -m json.tool catalog/mcp-configs/mcp-servers.json` exit 0; `mcpServers` count == 13 (11 kept + 2 new internal).
> 6. `data/skills.json` skill count == 187; `data/SKILL_INDEX.md` row count matches; `data/marketplace.json` `total_skills` matches.
> 7. `grep -rn "context7\|exa-web-search\|firecrawl\|magic-ui\|claude-context\|zilliztech\|zilliz cloud\|voyage-code-3\|8\.4k\|swe-bench" catalog/ guides/ infrastructure/ AGENTS.md CLAUDE.md GEMINI.md --include='*.md' --include='*.json'` returns matches only in `CHANGELOG.md` historical entries and `docs/v0.*.*/` historical directories.
> 8. `shellcheck --severity=warning scripts/installer.sh install.sh` exit 0.
> 9. `bash -n scripts/installer.sh` clean + PowerShell AST parse of `scripts/installer.ps1` clean.
> 10. Policy parity: condensed MCP Registry Policy summary is diff-identical across all 7 platform surfaces.
> 11. Smoke-invoke one or two v0.9.7 skills (`/compile-deep-research`, `/run-penetration-test`, `deep-research-compilation`) to confirm no regressions.
> 12. `docs/v0.9.7/plans/adoption-claude-context.md` forward-link resolves to `docs/archive/v1/v1.0/plans/security-hardening-v100.md`.
>
> Fix any failure. Do not tag until all 12 checks pass.

---

#### 11.6 — Create the git tag `v1.0.0` (local; gated on user confirmation to push)

**Objective**: Tag the release locally; defer the push until the user explicitly confirms.

**Prompt**:
> Once sub-task 11.5 passes:
>
> 1. Stage all changes across Phases 0–10 + the Phase 11 sub-tasks.
> 2. Commit with a message following the project's ASCII-only convention: summary line "release: v1.0.0 - reverse-engineering-first security hardening" + a body enumerating Phases 0–11 with one-line descriptions each. Do NOT include `Co-Authored-By` or AI attribution footers (per the repo's CLAUDE.md rule).
> 3. `git tag -a v1.0.0 -m "v1.0.0 - reverse-engineering-first security hardening; first stable release"`.
> 4. Do NOT push. Confirm with the user that the tag is correct before `git push origin main && git push origin v1.0.0`. Per the destructive-command rule, pushing requires explicit user confirmation.
>
> Acceptance: tag exists locally (`git tag | grep v1.0.0`); user has confirmed push (or explicitly deferred it).

---

### Phase 11 Exit Checklist

- [ ] `CHANGELOG.md` shows `## [1.0.0] - <date>` with the full Added / Changed / Removed summary
- [ ] 14 canonical files bumped `0.9.7` → `1.0.0`
- [ ] `docs/archive/v1/v1.0/RELEASE_NOTES.md` authored
- [ ] `MEMORY.md` has `project_release_v100` entry
- [ ] `make validate` + `make test` + `make lint` + `make benchmark` all clean
- [ ] `git tag v1.0.0` created locally
- [ ] Push gated on user confirmation

---

## End-to-End Verification (Post-Release Gate)

1. **Policy discoverable**: `AGENTS.md` has the reverse-engineering-first decision tree; same condensed summary diff-identical across all 7 platform surfaces.
2. **Matrix authoritative**: `docs/policy/mcp-reverse-engineering-matrix.md` has a row for every current and dropped registry entry; each row cites upstream evidence.
3. **Registry policy-compliant**: 13 entries (11 kept + 2 new internal); no drop-class key or repo name appears outside historical trees.
4. **De-branding complete**: `rag-implementation/SKILL.md`, `code-semantic-search/SKILL.md`, `ui-component-generation/SKILL.md`, `local-docs-lookup/SKILL.md` all clean under the external-attribution grep.
5. **`/compare-project` enforces policy**: Section 9 required; Section 9.4 orders per decision tree; `/generate-plan` chain emits RE-first phases.
6. **Internal MCPs work**: `devai-code-search` keyword queries return results; `devai-web-fetch` fetches + extracts; both pass the network-activity guard.
7. **Skill replacements function**: `ui-component-generation` produces working components; `local-docs-lookup` grounds answers against vendored READMEs.
8. **Cross-links present**: `code-semantic-search` is referenced by `context-manager` and `context-engineering`.
9. **Benchmark operational**: `make benchmark` clean; `data/benchmarks/mcp.json` has a fresh entry.
10. **Installer parity**: both installers install the 2 new MCPs and the benchmark script; reference no dropped entries.
11. **Release artifacts**: `CHANGELOG.md` `[1.0.0]` populated; `docs/archive/v1/v1.0/RELEASE_NOTES.md` exists; 14 canonical files bumped; `MEMORY.md` has `project_release_v100`; `git tag v1.0.0` created locally.

---

## v1.1.0+ Backlog

Surfaced by the Reverse-Engineering Matrix but not in v1.0.0:

- Dense / hybrid retrieval on `devai-code-search` (ONNX embeddings via `fastembed`; `sqlite-vec` vector store; RRF; `mode="hybrid"` becomes callable).
- Tree-sitter AST chunking in `devai-code-search` (start with Python grammar only; extend per-language per demand).
- Merkle-tree incremental indexing upgrade (from flat content-hash manifest to directory-keyed tree for huge repos).
- Playwright-based JS rendering in `devai-web-fetch` (`render_js=True` becomes callable).
- Vendor-wrapper reverse-engineering: `devai-github`, `devai-postgres`, `devai-supabase`, `devai-railway`, `devai-vercel`, `devai-cloudflare`. These do not reduce data-flow surface (the vendor IS the intended destination) but they improve audit / supply-chain posture by replacing Anthropic- / vendor-maintained code with DevAI-Hub-maintained code. Scope each per demand signal.

---

## How to Begin

Run `/implement-phase security-hardening-v100` to start. Phase 0 is marked complete (executed during the planning session); Phase 1 is the first phase to execute from scratch.
