# Plan — Adopt `zilliztech/claude-context` Patterns into DevAI-Hub

> **STATUS: ABANDONED (2026-04-24) — SUPERSEDED BY v1.0.0 SECURITY-HARDENING PLAN**
>
> This plan was started and halted after Phase 2. The user flagged a policy concern: DevAI-Hub must not ship MCP registry entries that point users at third-party data processors (in any regulated-industry / high-trust context, proprietary source code, prompts, and query text cannot leak to external APIs). Phase 2 had added exactly such an entry (`@zilliz/claude-context-mcp`), which has now been **reverted** before any commit.
>
> **Outcomes**:
>
> - **Phase 1** (merged as commit `3e9a202`): the `rag-implementation/SKILL.md` content additions are kept as reverse-engineered pattern knowledge, but every external-source attribution (`zilliztech/claude-context`, `Zilliz Cloud`, `voyage-code-3`, SWE-bench metric citations, upstream repo file paths) is being **de-branded** under v1.0.0 Phase 4. Generic descriptive names replace specific product/repo references.
> - **Phase 2**: fully reverted. The `claude-context` entry in `catalog/mcp-configs/mcp-servers.json` is gone, the Phase 2 DEVLOG entry is removed, and the Phase 2 session-history file has been deleted (none of the Phase 2 work was ever committed, so the revert is clean).
> - **Phases 3–5** (original: new `code-semantic-search` skill, cross-links, skill-server benchmark): reverse-engineered into v1.0.0 Phases 8–10. Every new artifact is de-branded (no external attribution) and re-points references at DevAI-Hub's own internal MCPs (`devai-code-search`, to be built in v1.0.0 Phase 6).
> - **Phase 6** (original release): absorbed into v1.0.0 Phase 11.
>
> **Release retarget**: the work originally scoped for v0.9.8 grew into a major-version event (MCP Registry Policy bake-in, a new authoritative reverse-engineering matrix, 2 new internal MCPs, 3 new skills, `/compare-project` command-level workflow change, breaking registry removals). It now targets **v1.0.0** as the first stable release milestone. The version-bump sweep therefore goes `0.9.7 → 1.0.0`, skipping the intermediate 0.9.8.
>
> **Successor plan**: [`docs/archives/v1/v1.0/plans/security-hardening-v100.md`](../../v1.0.0/plans/security-hardening-v100.md) (generated via `/generate-plan` from the v1.0.0 scratch plan — see that file's Phase 0 for the authoring trail).
>
> This file is kept unchanged below for historical record. The body content does NOT reflect current project direction; refer to the successor plan.

---

**Project**: DevAI-Hub
**Version**: v0.9.7 (target release: v0.9.8)
**Slug**: adoption-claude-context
**Plan Type**: Feature / Enhancement
**Created**: 2026-04-23
**Source**: [docs/v0.9.7/comparison-claude-context.md](../comparison-claude-context.md) — scope filter `all` (P0 + P1 + P2 + P3, 6 items)
**Goal**: Land all 6 adoption items from the comparison report (A1, A2, B1, B2, C1, D1), verify the changes distribute correctly to every supported AI-assistant platform via both installers, and release the work as v0.9.8.

---

## Overview

This plan executes the full adoption scope identified by the `/compare-project` run against `https://github.com/zilliztech/claude-context`. None of the 6 items involve adopting runtime code from claude-context; all are documentation, registry, and benchmark-scaffolding additions that fold claude-context's production-tested retrieval patterns (hybrid BM25 + dense retrieval, AST chunking, Merkle-tree incremental indexing, Milvus/Zilliz as a named backend) into DevAI-Hub's existing skill catalog, MCP registry, and skill-server benchmarking surface.

The work lands in five content phases followed by a release phase. Phases 1–2 are parallelizable (independent files). Phase 3 (the new `code-semantic-search` skill) depends on Phases 1–2 for terminology alignment and to reference the new MCP registry entry. Phase 4 (cross-links) depends on Phase 3. Phase 5 (benchmark + unit test) is independent and could run at any point. Phase 6 gates the release and must come last.

Each of Phases 1–5 ends with a stabilization sub-task that both validates the change (JSON integrity, skill counts, markdown link health, pytest results) **and** performs a cross-platform installer dry-run to confirm the change reaches every target platform profile. This replaces what would otherwise be a dedicated "installer verification" phase — per the user's direction. Phase 6 then performs the v0.9.8 release: `CHANGELOG.md` migration, the 14-canonical-file version-bump sweep documented in `MEMORY.md` (`project_release_v097`), `docs/v0.9.8/RELEASE_NOTES.md` authoring, and the git tag.

Success looks like: all 6 adoption items merged to `main`; `make validate` + `make test` clean; `search_skills` MCP returns the new `code-semantic-search` skill; `make benchmark` executes the new script against the skill-server and emits timing data; both `scripts/installer.sh` and `scripts/installer.ps1` dry-run cleanly against a throwaway target; `CHANGELOG.md` shows `## [0.9.8] - <release-date>`; `docs/v0.9.8/RELEASE_NOTES.md` exists; `git tag v0.9.8` is pushed.

---

## Phases at a Glance

| Phase | Title | Adoption Items | Outcome |
|-------|-------|----------------|---------|
| 1 | Retrofit `rag-implementation` skill | A1 + A2 (P0) | Skill names Milvus/Zilliz, VoyageAI/Ollama/Gemini, AST chunking, Merkle incremental indexing, and hybrid BM25+RRF with `claude-context` cited as canonical OSS reference |
| 2 | MCP registry entry for claude-context | B1 (P1) | `catalog/mcp-configs/mcp-servers.json` has a new `claude-context` entry matching the existing `github` shape |
| 3 | Create `code-semantic-search` skill | B2 (P1) | New SKILL.md + registry updates in 3 data files; skill count 186 → 187; MCP server returns the skill on `search_skills` |
| 4 | Cross-link context skills | C1 (P2) | `context-manager` and `context-engineering` have a Related Skills entry pointing to `code-semantic-search` |
| 5 | Skill-server MCP benchmark + unit test | D1 (P3) | `scripts/skill_server_benchmark.py` + `Makefile` `benchmark` target + pytest test; script registered in both installers |
| 6 | Release v0.9.8 | DoD | `CHANGELOG.md` moves `[Unreleased]` to `[0.9.8]`; 14-file version bump; `docs/v0.9.8/RELEASE_NOTES.md`; `git tag v0.9.8` |

---

## Phase 1: Retrofit `rag-implementation` Skill

**Goal**: Extend `catalog/skills/ai-development/rag-implementation/SKILL.md` to name hybrid BM25+dense retrieval with Reciprocal Rank Fusion as a concrete pattern, add Milvus and Zilliz Cloud to the vector-store roster, add VoyageAI/Ollama/Gemini as named embedding providers (alongside OpenAI), and add AST-aware code chunking + Merkle-tree incremental indexing to the chunking-strategy taxonomy. Cite `zilliztech/claude-context` as the canonical OSS reference for all four techniques.

**Prerequisites**: None.

**Stability Gate**: `make validate` clean; `rag-implementation/SKILL.md` line count remains ≤ 1100 (current 1054; budget ~50 additional lines); dry-run of both installers copies the updated file to every platform skill directory.

### Sub-tasks

#### 1.1 — A1: Add hybrid BM25 + dense retrieval + RRF reference

**Objective**: Augment the existing hybrid-search discussion (currently at `rag-implementation/SKILL.md` lines 581 and 639) with a concrete implementation reference naming `zilliztech/claude-context` as an 8.4k-star MIT-licensed OSS implementation of the pattern.

**Prompt**:
> Read `docs/v0.9.7/comparison-claude-context.md` Section 5a first (adoption item A1) and Section 10 (P0 row A1) for full context, plus `catalog/skills/ai-development/rag-implementation/SKILL.md` lines 570–650 for existing hybrid-search content.
>
> In `catalog/skills/ai-development/rag-implementation/SKILL.md`, locate the hybrid-search subsection (around line 581) and the Reciprocal Rank Fusion paragraph (around line 639). Add a short subsection (8–15 lines) titled **"Canonical OSS reference"** immediately after the RRF paragraph. In it, name `zilliztech/claude-context` as a production reference implementation of hybrid BM25 + dense retrieval with rerank strategies, link to the GitHub URL, and briefly cite the reported 39.4% token reduction and 36.3% tool-call reduction vs. grep baseline from its SWE-bench evaluation (source: `evaluation/run_evaluation.py` and `analyze_and_plot_mcp_efficiency.py` in the upstream repo). Mention that the upstream implementation lives in its core package and exposes `hybridSearch` as a boolean flag on its `search_code` MCP tool.
>
> Do not edit the existing BM25 or RRF paragraphs; only add the new subsection after them. Preserve all existing markdown heading levels, anchor links, and line numbering downstream of the insertion.
>
> Acceptance criteria: new subsection present; existing content unchanged; `make validate` passes; total file length ≤ 1100 lines. No changes to frontmatter.

---

#### 1.2 — A2: Broaden vector-store and embedding-provider tables

**Objective**: Expand the vector-store enumeration (currently lists only Chroma, Pinecone, pgvector, Qdrant at lines 439–443) to include Milvus (native and REST) and Zilliz Cloud. Add VoyageAI, Ollama, and Gemini to the embedding-provider enumeration alongside the existing OpenAI content. Note `voyage-code-3` as a code-specialized embedding option.

**Prompt**:
> Read `docs/v0.9.7/comparison-claude-context.md` Section 5a (adoption item A2 and the embedding/vector-DB table rows) and Section 10 (P0 row A2) for the exact providers and dimensions to cite.
>
> In `catalog/skills/ai-development/rag-implementation/SKILL.md`:
>
> 1. Locate the vector-store section (around lines 439–443). Extend the existing list with two new rows:
>    - **Milvus** — open-source, self-hostable, native gRPC and REST clients available; used in production by `zilliztech/claude-context`.
>    - **Zilliz Cloud** — managed Milvus with a free tier; same client API as Milvus.
>    Keep each row in the same format as the existing Chroma/Pinecone/pgvector/Qdrant entries. Do not reorder the existing rows.
>
> 2. Locate the embedding-providers section. Add a short subsection or table (whichever matches the existing formatting) naming **OpenAI** (`text-embedding-3-small`, 1536 dim — default), **VoyageAI** (`voyage-code-3`, 1024 dim — code-specialized), **Ollama** (local, typical 768 dim), and **Google Gemini** (`gemini-embedding-001`, up to 3072 dim with Matryoshka). Call out that `voyage-code-3` is the right default when the corpus is source code. Cite `zilliztech/claude-context` as the reference integration for all four providers.
>
> 3. If the existing AST-chunking / Merkle-tree content is missing from the chunking-strategy taxonomy (check lines 191–358), add **AST-aware chunking** as a named chunking strategy, noting that the upstream reference uses tree-sitter for 9 languages (JavaScript, TypeScript, Python, Java, C++, Go, Rust, C#, Scala) with a LangChain recursive-character splitter as a fallback. Add **Merkle-tree content-hash incremental indexing** as a named technique under an "Incremental re-indexing" subheading — cite the upstream files `packages/core/src/sync/merkle.ts` and `packages/core/src/sync/synchronizer.ts` as reference.
>
> Acceptance criteria: the three content additions land; existing content unchanged; `make validate` passes; total file length ≤ 1100 lines; at least one markdown link to `https://github.com/zilliztech/claude-context` exists in the file.

---

#### 1.3 — Testing & cross-platform verification

**Objective**: Validate the edited skill, confirm the file distributes correctly to each supported platform via both installers.

**Prompt**:
> Run the following verifications on the `rag-implementation` skill edits from sub-tasks 1.1 and 1.2:
>
> 1. `python -c "import json; d = json.load(open('data/skills.json')); print(len(d['skills']))"` — expect 184 (unchanged — edit is content-only).
> 2. `python -c "import json; json.load(open('data/bundles.json')); json.load(open('data/workflows.json'))"` — no errors.
> 3. `python -c "import json; json.load(open('data/templates.json', encoding='utf-8'))"` — no errors. (Use explicit `encoding='utf-8'` to bypass the Windows cp1252 quirk documented in `MEMORY.md`.)
> 4. `wc -l catalog/skills/ai-development/rag-implementation/SKILL.md` — expect ≤ 1100.
> 5. Markdown link audit: grep the file for `](http` and verify the new `github.com/zilliztech/claude-context` URL is well-formed.
> 6. Cross-platform installer dry-run:
>    - Create a throwaway target directory, e.g. `/tmp/devai-dryrun-p1` (Linux/Mac) or `$env:TEMP\devai-dryrun-p1` (Windows).
>    - Run `scripts/installer.sh --target /tmp/devai-dryrun-p1` (or the equivalent Windows command for `installer.ps1`).
>    - After install, verify the updated `rag-implementation/SKILL.md` appears under the Claude Code profile (`~/.claude/skills/ai-development/rag-implementation/SKILL.md`), Gemini profile, and Codex profile. Behavioral-only platforms (Cursor, Copilot, OpenCode) do not receive per-skill file copies; verify their instruction files (`AGENTS.md`, `.cursor/rules/`, `.github/copilot-instructions.md`) still embed the `{{SKILL_INDEX}}` placeholder or equivalent row.
>    - Delete the throwaway target.
> 7. If installer is not available in the current environment, document the skip in a commit note and open a follow-up issue for verification on a CI runner that has both Bash and PowerShell.
>
> Do not advance to Phase 2 until all 6 checks pass.

---

### Phase 1 Exit Checklist

- [ ] A1 subsection added (hybrid BM25 + RRF canonical reference)
- [ ] A2 vector-store and embedding-provider rosters extended
- [ ] AST-aware chunking and Merkle-tree incremental indexing named in the chunking taxonomy
- [ ] `make validate` clean; file ≤ 1100 lines
- [ ] Installer dry-run distributes updated skill to Claude, Gemini, Codex profiles
- [ ] `AGENTS.md` platform-agnostic rule respected (no per-platform template edits needed; change is additive to auto-copied `catalog/skills/`)

---

## Phase 2: MCP Registry Entry for `claude-context`

**Goal**: Add a ready-to-use MCP server configuration entry for `@zilliz/claude-context-mcp` to `catalog/mcp-configs/mcp-servers.json` so that DevAI-Hub users can register claude-context with their AI assistant in one step. No installer edits are required because both `scripts/installer.sh` (lines 705, 1108) and `scripts/installer.ps1` (lines 978, 1369) already copy `mcp-servers.json` to each platform's MCP-config directory.

**Prerequisites**: None. (This phase is parallelizable with Phase 1 but is sequenced second for clarity.)

**Stability Gate**: `mcp-servers.json` parses as valid JSON; new entry follows the same key/shape convention as the existing `github` entry; `make validate` clean; dry-run installers copy the updated JSON to each platform's mcp-configs directory.

### Sub-tasks

#### 2.1 — Add `claude-context` entry to the MCP registry

**Objective**: Register the upstream MCP server so users can wire it into their AI assistant configuration without hunting down the snippet.

**Prompt**:
> Read `docs/v0.9.7/comparison-claude-context.md` Section 10 (P1 row B1) and Section 4.3 for the exact shape and env-var requirements. Also read `catalog/mcp-configs/mcp-servers.json` in full (101 lines) to see the existing entry conventions.
>
> In `catalog/mcp-configs/mcp-servers.json`, add a new top-level key `"claude-context"` as a sibling to the existing `"github"` entry. Use the same JSON shape:
>
> ```json
> "claude-context": {
>   "_comment": "Semantic code search MCP server by Zilliz. Requires OpenAI API key and a Milvus/Zilliz Cloud endpoint. See https://github.com/zilliztech/claude-context for setup.",
>   "command": "npx",
>   "args": ["-y", "@zilliz/claude-context-mcp@latest"],
>   "env": {
>     "OPENAI_API_KEY": "${OPENAI_API_KEY}",
>     "MILVUS_ADDRESS": "${MILVUS_ADDRESS}",
>     "MILVUS_TOKEN": "${MILVUS_TOKEN}"
>   }
> }
> ```
>
> Place the entry in the file immediately after the `github` block. Preserve the JSON indentation (2 spaces) used by the surrounding file. If the existing file already uses an `_comment` pattern on entries, match it exactly; if not, drop the `_comment` field to remain consistent.
>
> Acceptance criteria: JSON is valid (`python -m json.tool catalog/mcp-configs/mcp-servers.json > /dev/null` exits 0); new entry present; existing entries unchanged; `make validate` passes.

---

#### 2.2 — Testing & cross-platform verification

**Objective**: Confirm the edited MCP registry distributes to each platform's mcp-configs directory via both installers.

**Prompt**:
> Run the following verifications:
>
> 1. `python -m json.tool catalog/mcp-configs/mcp-servers.json > /dev/null` — exit code 0.
> 2. `python -c "import json; d = json.load(open('catalog/mcp-configs/mcp-servers.json')); assert 'claude-context' in d; assert d['claude-context']['command'] == 'npx'"` — no assertion error.
> 3. `make validate` — clean.
> 4. Cross-platform installer dry-run:
>    - Throwaway target `/tmp/devai-dryrun-p2`.
>    - Run `scripts/installer.sh` (or `.ps1` on Windows).
>    - Verify the new entry appears at the destinations listed in `scripts/installer.sh:705` (global Claude) and `scripts/installer.sh:1108` (workspace Claude), and the corresponding PowerShell destinations (`installer.ps1:978` and `:1369`).
>    - Delete the throwaway target.
> 5. Confirm the entry is also documented in the adoption commit message so reviewers understand the env-var requirement (no secrets get bundled — only placeholders).
>
> Do not advance to Phase 3 until all 5 checks pass.

---

### Phase 2 Exit Checklist

- [ ] New `claude-context` entry in `catalog/mcp-configs/mcp-servers.json`
- [ ] JSON valid; existing entries untouched
- [ ] Dry-run installer copies updated JSON to global + workspace Claude MCP-config directories on both Bash and PowerShell code paths
- [ ] No installer code edits required (confirmed by checking that `mcp-configs/` is explicitly copied, not conditionally)

---

## Phase 3: Create `code-semantic-search` Skill

**Goal**: Author a new skill at `catalog/skills/ai-development/code-semantic-search/SKILL.md` documenting the capability of semantic code search as a peer-but-distinct skill from `rag-implementation` (which remains the general-purpose RAG skill). Register it in all three data files per `AGENTS.md` "Adding a New Skill" step 4.

**Prerequisites**: Phases 1–2 landed (so the new skill can reference the retrofitted `rag-implementation` content and the new MCP registry entry).

**Stability Gate**: New SKILL.md file ≤ 800 lines; three registry files updated consistently (skill count goes from 186 to 187 everywhere); `make validate` clean; `make test` clean; the skill-server MCP returns the new skill on `search_skills("code semantic search")`.

### Sub-tasks

#### 3.1 — Author `code-semantic-search` SKILL.md

**Objective**: Write the new skill file following DevAI-Hub's SKILL.md conventions (YAML frontmatter with `name`, `description`, `summary_l0`, `overview_l1`; body with When to Use This Skill, Instructions, Common Rationalizations, Verification, Related Skills).

**Prompt**:
> Read `AGENTS.md` "Adding a New Skill" (sections 2–4) for the file-format contract. Read `catalog/skills/ai-development/rag-implementation/SKILL.md` (after Phase 1 edits land) for neighbor-skill tone and reference shape. Read `docs/v0.9.7/comparison-claude-context.md` Section 10 (P1 row B2) for scope guidance.
>
> Create `catalog/skills/ai-development/code-semantic-search/SKILL.md` with:
>
> 1. YAML frontmatter:
>    ```yaml
>    ---
>    name: code-semantic-search
>    description: Semantic search over source-code corpora using code-specialized embeddings, AST chunking, and hybrid BM25+dense retrieval
>    summary_l0: "Retrieve relevant code from large repositories using hybrid semantic search and AST-aware chunking"
>    overview_l1: "This skill covers semantic search specifically for source-code corpora, which differs from general RAG in three ways: code-specialized embedding models (voyage-code-3) outperform generic text embeddings; AST-aware chunking preserves function and class boundaries that character-based splitters shred; and incremental re-indexing via content-hash Merkle trees avoids re-embedding unchanged subtrees on each commit. Use this skill when the AI agent must answer questions about a codebase larger than the model's context window, when grep/ripgrep produces too many false positives for natural-language queries, or when a team wants to eliminate 'where do we handle X?' spelunking. Reference implementation: zilliztech/claude-context (8.4k stars, MIT, MCP server + VS Code extension)."
>    ---
>    ```
>
> 2. Body sections in this order (each section is required per `AGENTS.md`):
>    - **Title** + 2-paragraph intro framing the skill.
>    - **When to Use This Skill** with 5–8 bullet trigger scenarios and explicit **When NOT to use** guidance (e.g. "when the codebase fits in context, use direct file reads instead — indexing overhead is not free").
>    - **Instructions** with numbered steps covering: (a) embedding-model selection (prefer code-specialized `voyage-code-3`; cite the 4 providers from Phase 1 A2), (b) chunking strategy (AST with tree-sitter ≫ recursive char splitter), (c) vector store choice (Milvus/Zilliz for production; FAISS/Chroma for local experimentation), (d) hybrid retrieval (BM25 for identifier-exact matches + dense for semantic), (e) incremental re-indexing (Merkle tree over file hashes), (f) rerank strategies, (g) pitfalls (stale indexes after merges, chunk-size misconfiguration causing token-limit overruns, embedding cost at first index, language-coverage gaps in AST splitters).
>    - **Common Rationalizations** table with 3–5 entries. Each rationalization must cite a concrete failure mode. Example rows:
>      - "grep is fast enough" → "grep returns 200 lines for 'payment processing'; the agent still has to read each to filter. Semantic search returns 5 chunks ranked by relevance."
>      - "We don't need AST chunking; recursive splitter works" → "Recursive splitters shred function bodies across chunk boundaries; the dense vector for the chunk stops representing the function and retrieval quality collapses on language-specific queries."
>      - "We'll re-index on every commit" → "Re-embedding 50 MB of TypeScript costs ~$2 and takes 3 minutes with OpenAI; Merkle-tree diffing only re-embeds the actually-changed chunks, amortizing cost."
>    - **Verification** — binary checklist including: (a) chosen embedding model is documented, (b) chunking strategy is AST-aware for supported languages + character-based fallback is configured, (c) vector store has the correct index type (HNSW for Milvus), (d) incremental indexing is enabled for the expected commit cadence, (e) a spot-check of 3 natural-language queries returns the expected files.
>    - **Related Skills** — link to:
>      - `rag-implementation` — "general-purpose RAG over non-code corpora; this skill is the code-corpus specialization"
>      - `context-manager` — "for session-level context budgeting; use code-semantic-search as the escape valve when the repo exceeds the context window"
>      - `context-engineering` — "deliberate context shaping; semantic search is one of the primary retrieval-based context sources"
>      - The new MCP registry entry (`catalog/mcp-configs/mcp-servers.json`'s `claude-context` key) — "ready-to-use MCP server for the capability"
>
> Target file length: 300–600 lines. Do not exceed 800 lines per `AGENTS.md` guidance.
>
> Acceptance criteria: frontmatter is YAML-valid (`python -c "import yaml; yaml.safe_load(open('catalog/skills/ai-development/code-semantic-search/SKILL.md').read().split('---')[1])"` succeeds); all five body sections present; at least one link to `rag-implementation` SKILL.md; at least one link to `github.com/zilliztech/claude-context`; file length within target.

---

#### 3.2 — Register in `data/SKILL_INDEX.md`

**Objective**: Add a single row to the skill index table.

**Prompt**:
> In `data/SKILL_INDEX.md`, add one row to the main table following the existing format:
>
> ```
> | code-semantic-search | ai-development | "Retrieve relevant code from large repositories using hybrid semantic search and AST-aware chunking" | catalog/skills/ai-development/code-semantic-search/SKILL.md |
> ```
>
> Insert the row alphabetically within the `ai-development` category block (after `claude-agent-sdk`, before `context-engineering`). Do not reorder other rows.
>
> Acceptance criteria: table row count goes from 186 to 187 (184 skills + 1 header + misc; verify the exact current count first with `grep -c '^|' data/SKILL_INDEX.md`, then confirm it increments by 1); Markdown table syntax is valid.

---

#### 3.3 — Register in `data/skills.json`

**Objective**: Add one skill entry to the `skills` array matching the existing JSON schema.

**Prompt**:
> Read `data/skills.json` and extract the existing `ai-agent-development` entry (around lines 53–85) as a shape template.
>
> Add a new entry to the `skills` array in `data/skills.json`:
>
> ```json
> {
>   "name": "code-semantic-search",
>   "title": "code-semantic-search",
>   "description": "Semantic search over source-code corpora using code-specialized embeddings, AST chunking, and hybrid BM25+dense retrieval",
>   "summary_l0": "\"Retrieve relevant code from large repositories using hybrid semantic search and AST-aware chunking\"",
>   "overview_l1": "\"<copy the full overview_l1 from the SKILL.md frontmatter verbatim, escaped appropriately>\"",
>   "version": "1.0.0",
>   "author": "Benjamin Dourthe",
>   "category": "ai-development",
>   "language": "Multi-language",
>   "tags": ["rag", "retrieval", "embeddings", "code-search", "mcp"],
>   "priority": "MEDIUM",
>   "path": "catalog/skills/ai-development/code-semantic-search/",
>   "file": "catalog/skills/ai-development/code-semantic-search/SKILL.md",
>   "size": {"lines": <actual line count>, "tokens_estimate": <lines × 3.5>},
>   "status": "production",
>   "security": {"structural": 100, "integrity": 100, "semantic": 95}
> }
> ```
>
> Insert the entry alphabetically within the array. Recompute `total_skills` in the `statistics` or `summary` object if such a top-level field exists in `skills.json` (read the whole file first to check).
>
> Acceptance criteria: `python -c "import json; d = json.load(open('data/skills.json')); print(len(d['skills']))"` returns 185 (was 184); the new entry's `file` path points to a file that exists; JSON remains valid.

---

#### 3.4 — Register in `data/marketplace.json`

**Objective**: Increment the relevant category and total counts.

**Prompt**:
> Read `data/marketplace.json` and find the category entry for `ai-development`. Increment its `skill_count` field by 1. Find the top-level `statistics` object (or equivalent; the exact field name varies — read the file first) and increment `total_skills` by 1.
>
> Acceptance criteria: both counters incremented by exactly 1; no other fields changed; JSON remains valid.

---

#### 3.5 — Testing & cross-platform verification

**Objective**: Validate the skill + all three registry updates land consistently, and the skill distributes to every platform.

**Prompt**:
> Run the following verifications:
>
> 1. `make validate` — clean; `skills.json` shows 185 skills, `bundles.json` unchanged, `workflows.json` unchanged.
> 2. `make test` — clean (pytest suite in `catalog/hooks/tests/` and `extensions/devai-skill-server/tests/`).
> 3. Consistency check: skill count in `data/SKILL_INDEX.md` (rows — header), `data/skills.json` (`len(skills)`), and `data/marketplace.json` (`total_skills`) all match and equal 185.
> 4. Skill-server MCP smoke: start `extensions/devai-skill-server/` locally (`cd extensions/devai-skill-server && python -m devai_skill_server`) and confirm the MCP tool call `search_skills(query="code semantic search")` returns the new skill within the top 3 results. If MCP invocation tooling is not locally available, invoke the underlying search function directly in a Python REPL.
> 5. Markdown link audit on the new SKILL.md: every internal `]( ... .md)` link resolves to a file that exists.
> 6. Cross-platform installer dry-run:
>    - Throwaway target `/tmp/devai-dryrun-p3`.
>    - Run `scripts/installer.sh` and `scripts/installer.ps1` (whichever is available; note any skip for follow-up).
>    - Verify `code-semantic-search/SKILL.md` lands under Claude, Gemini, and Codex skill directories. Verify the `{{SKILL_INDEX}}` placeholder in each platform's instruction file is re-rendered to include the new row (since the installer regenerates the index from `data/SKILL_INDEX.md`).
>    - Delete the throwaway target.
>
> Do not advance to Phase 4 until all 6 checks pass.

---

### Phase 3 Exit Checklist

- [ ] `catalog/skills/ai-development/code-semantic-search/SKILL.md` exists with all 5 required body sections
- [ ] Three registry files updated; skill counts consistent at 185 everywhere
- [ ] `make validate` + `make test` clean
- [ ] Skill-server MCP returns the new skill on semantic search
- [ ] Installer dry-run distributes the new skill to Claude, Gemini, Codex

---

## Phase 4: Cross-Link Context Skills to `code-semantic-search`

**Goal**: Add Related Skills entries in `context-manager/SKILL.md` and `context-engineering/SKILL.md` that point to the new `code-semantic-search` skill as the escape valve for "codebase larger than context window" scenarios.

**Prerequisites**: Phase 3 landed (target skill exists).

**Stability Gate**: Both edited files remain within their prior line budgets (context-manager 432 → ≤ 440; context-engineering 148 → ≤ 158); markdown links resolve; `make validate` clean; installer dry-run copies updated files.

### Sub-tasks

#### 4.1 — Add Related Skills entry in `context-manager/SKILL.md`

**Objective**: Surface `code-semantic-search` as a sibling skill for users shaping context over large repos.

**Prompt**:
> In `catalog/skills/orchestration/context-manager/SKILL.md` (432 lines), locate or create the "Related Skills" section at the end of the body. Add this entry:
>
> ```markdown
> - `code-semantic-search` (`catalog/skills/ai-development/code-semantic-search/SKILL.md`) — when the repo exceeds the model's context window, semantic retrieval over code is the primary escape valve. Use `code-semantic-search` to produce a ranked chunk set; feed the top-K into the session.
> ```
>
> If a Related Skills section does not exist, create it immediately before any trailing "References" or terminal content. Maintain the existing markdown style used in the file. Do not touch any other content.
>
> Acceptance criteria: the entry appears exactly once; link resolves to the Phase 3 file; file line count ≤ 440.

---

#### 4.2 — Add Related Skills entry in `context-engineering/SKILL.md`

**Objective**: Same as 4.1, for the context-engineering skill.

**Prompt**:
> In `catalog/skills/ai-development/context-engineering/SKILL.md` (148 lines), locate or create the Related Skills section. Add:
>
> ```markdown
> - `code-semantic-search` (`catalog/skills/ai-development/code-semantic-search/SKILL.md`) — retrieval-based context shaping for source-code corpora; specialized RAG with code-aware embeddings and AST chunking.
> ```
>
> Acceptance criteria: entry appears exactly once; link resolves; file line count ≤ 158.

---

#### 4.3 — Testing & cross-platform verification

**Prompt**:
> Verifications:
>
> 1. Both files have the new Related Skills entry; `grep -c code-semantic-search catalog/skills/orchestration/context-manager/SKILL.md` returns 1; same for context-engineering.
> 2. Markdown link audit: both `catalog/skills/ai-development/code-semantic-search/SKILL.md` references resolve.
> 3. Line-count caps (440 and 158) respected.
> 4. `make validate` clean.
> 5. Installer dry-run: throwaway target `/tmp/devai-dryrun-p4`; run both installers; verify both edited files land at each platform skill directory.
>
> Do not advance to Phase 5 until all 5 checks pass.

---

### Phase 4 Exit Checklist

- [ ] Both context skills have a new Related Skills entry pointing to `code-semantic-search`
- [ ] Line-count caps respected
- [ ] `make validate` clean
- [ ] Installer dry-run distributes both files

---

## Phase 5: Skill-Server MCP Benchmark + Unit Test

**Goal**: Add a benchmark script for the DevAI-Hub skill-server MCP (`extensions/devai-skill-server/`) modeled after claude-context's `scripts/build-benchmark.js`. Register the script in both installers per the "any new `scripts/<name>.py` must be registered" rule from `AGENTS.md`. Author a pytest test for the benchmark script (per the user's DoD answer requiring a new unit test for D1).

**Prerequisites**: Phase 3 landed (the new skill serves as one of the test queries for the benchmark).

**Stability Gate**: Benchmark script runs against a local skill-server and emits JSON timing output; pytest test passes; script lands at `~/.devai-hub/scripts/skill_server_benchmark.py` in installer dry-run; `make benchmark` target works.

### Sub-tasks

#### 5.1 — Author `scripts/skill_server_benchmark.py`

**Objective**: Measure round-trip latency of the skill-server MCP's core tools (`search_skills`, `get_skill`, `list_categories`, `list_bundles`, `get_bundle`) across a fixed set of queries.

**Prompt**:
> Read `extensions/devai-skill-server/README.md` (tool list is on lines 15–21) and the server's main entry file to understand how to invoke the MCP tools directly. Read the upstream reference `scripts/build-benchmark.js` from the claude-context repo (or re-clone it to `/tmp` if cleanup already deleted it) for output-shape inspiration — specifically the JSON structure with timestamp, platform, runtime version, and per-operation timing.
>
> Create `scripts/skill_server_benchmark.py` following the DevAI-Hub Python and Bash rule files:
>
> 1. Module docstring and type hints throughout.
> 2. Start the skill-server as a subprocess (or import it in-process if simpler and still representative), ensuring it is running against the repo's current `data/skills.json`.
> 3. Run a fixed query suite:
>    - `search_skills(query="code semantic search")`
>    - `search_skills(query="security audit")`
>    - `search_skills(query="test generation")`
>    - `get_skill(name="code-semantic-search")`
>    - `get_skill(name="rag-implementation")`
>    - `list_categories()`
>    - `list_bundles()`
>    - `get_bundle(name="<first bundle from data/bundles.json>")`
> 4. Time each call (use `time.perf_counter()`). Run each query N=5 times and report min / median / p95 / max in milliseconds.
> 5. Emit a JSON result to stdout, and optionally append to `data/benchmarks/skill-server.json` (create the file if missing; keep only the last 10 runs to prevent unbounded growth). JSON shape:
>
>    ```json
>    {
>      "timestamp": "2026-04-23T14:30:00Z",
>      "platform": "<uname>",
>      "python_version": "3.12.2",
>      "skill_count": 185,
>      "results": {
>        "search_skills_code_semantic_search": {"min_ms": 1.2, "median_ms": 1.8, "p95_ms": 3.1, "max_ms": 4.0},
>        ...
>      }
>    }
>    ```
> 6. Command-line flags: `--append` (write to `data/benchmarks/skill-server.json`), `--iterations=N` (override N=5), `--quiet` (suppress per-call output, only emit the summary JSON).
>
> Acceptance criteria: script runs without errors against the current repo; produces valid JSON output; total runtime < 10 seconds with default N=5; all tools return non-error responses; no mutable default arguments (per the Python rule file).

---

#### 5.2 — Register in `scripts/installer.sh`

**Prompt**:
> In `scripts/installer.sh`, locate the existing copy block for `generate_report.py` (around line 1395 per `AGENTS.md` "Installer-Aware Changes"). Add a parallel block copying `scripts/skill_server_benchmark.py` to `~/.devai-hub/scripts/skill_server_benchmark.py`, using `safe_copy` with the same error-handling and logging pattern as the existing block.
>
> Acceptance criteria: file syntax remains valid (`bash -n scripts/installer.sh` exits 0); ShellCheck passes (`shellcheck --severity=warning scripts/installer.sh`).

---

#### 5.3 — Register in `scripts/installer.ps1`

**Prompt**:
> In `scripts/installer.ps1`, locate the corresponding `Safe-Copy` block for `generate_report.py` (around line 1656 per `AGENTS.md`). Add a parallel `Safe-Copy` line for `skill_server_benchmark.py` pointing to the same `~/.devai-hub/scripts/` destination. Match the existing style (double-quoted paths, `$RepoRoot` variable, `-CustomMessage` parameter).
>
> Acceptance criteria: PowerShell parses the file without errors (`powershell -NoProfile -Command "& { Get-Command -Syntax .\scripts\installer.ps1 }"` or equivalent validation).

---

#### 5.4 — Add `benchmark` target to `Makefile`

**Prompt**:
> In `Makefile`, add a new target after `test`:
>
> ```
> benchmark: ## Benchmark skill-server MCP latency
> 	@echo "Benchmarking skill-server..."
> 	@python scripts/skill_server_benchmark.py --append --quiet
> 	@echo "Benchmark complete. Results in data/benchmarks/skill-server.json."
> ```
>
> Add `benchmark` to the `.PHONY` declaration at the top of the file.
>
> Acceptance criteria: `make benchmark` executes the script end-to-end; `make help` shows the new target with its description.

---

#### 5.5 — Author pytest test for the benchmark script

**Prompt**:
> Create `extensions/devai-skill-server/tests/test_benchmark.py` (or if that tests directory organizes differently, place it at `catalog/hooks/tests/test_skill_server_benchmark.py` — match whatever convention is already in use).
>
> The test should:
>
> 1. Import the benchmark module (`scripts/skill_server_benchmark.py` — add `sys.path` manipulation if needed).
> 2. Assert that the query suite contains at least 8 entries (catches accidental deletions).
> 3. Mock the skill-server calls (`monkeypatch` preferred over `unittest.mock.patch` per the Python test rule file) and assert the output JSON shape has `timestamp`, `platform`, `python_version`, `skill_count`, and `results` keys.
> 4. Assert `--iterations` flag is respected (run with `--iterations=1` and verify the mock was called exactly 8 times, once per query).
> 5. Assert `--append` writes to `data/benchmarks/skill-server.json` (use `tmp_path` to redirect via monkeypatch).
>
> Follow the Python testing rule file: pytest (not unittest), AAA pattern, one assertion per test where possible, `tmp_path` fixture for filesystem writes.
>
> Acceptance criteria: `cd extensions/devai-skill-server && python -m pytest -q tests/test_benchmark.py` passes with at least 3 test cases.

---

#### 5.6 — Testing & cross-platform verification

**Prompt**:
> Verifications:
>
> 1. `python scripts/skill_server_benchmark.py` runs clean; output is valid JSON.
> 2. `make benchmark` runs clean; appends to `data/benchmarks/skill-server.json`.
> 3. `make test` runs clean (the new pytest test joins the existing suite).
> 4. ShellCheck: `shellcheck --severity=warning scripts/installer.sh` clean.
> 5. Cross-platform installer dry-run:
>    - Throwaway target `/tmp/devai-dryrun-p5`.
>    - Run `scripts/installer.sh` (and `.ps1` on Windows).
>    - Verify `skill_server_benchmark.py` lands at `<target>/scripts/skill_server_benchmark.py` (or wherever `generate_report.py` already lands; match that destination).
> 6. `make validate` — clean (the new `data/benchmarks/` directory is generated-output; verify it is gitignored; if not, add the path to `.gitignore`).
>
> Do not advance to Phase 6 until all 6 checks pass.

---

### Phase 5 Exit Checklist

- [ ] `scripts/skill_server_benchmark.py` runs; emits valid JSON; `--append`, `--iterations`, `--quiet` flags work
- [ ] Both installers register the script (per `AGENTS.md` rule)
- [ ] `Makefile` has a `benchmark` target in `.PHONY` list
- [ ] `pytest` test for the script passes; `make test` remains clean
- [ ] Installer dry-run copies the script to `~/.devai-hub/scripts/`
- [ ] `data/benchmarks/` is gitignored (or the convention is explicit)

---

## Phase 6: Release v0.9.8

**Goal**: Cut the v0.9.8 release. Migrate `CHANGELOG.md` `[Unreleased]` content to `[0.9.8]`; bump the version across the 14 canonical files (per `MEMORY.md` `project_release_v097`); author `docs/v0.9.8/RELEASE_NOTES.md`; create the git tag.

**Prerequisites**: Phases 1–5 all merged to `main`; all exit checklists passed.

**Stability Gate**: `make validate` + `make test` + `make lint` all clean; both installers dry-run successfully against a clean target; `git tag v0.9.8` exists; `docs/v0.9.8/RELEASE_NOTES.md` exists.

### Sub-tasks

#### 6.1 — Migrate `CHANGELOG.md` to `[0.9.8]`

**Prompt**:
> In `CHANGELOG.md`, rename the `## [Unreleased]` heading to `## [0.9.8] - <YYYY-MM-DD>` using today's date. Immediately above it, create a new empty `## [Unreleased]` section for future work.
>
> Add the adoption summary bullets under the new `[0.9.8]` heading, organized by the existing `### Added` / `### Changed` / `### Removed` convention:
>
> - **Added**: `code-semantic-search` skill; `claude-context` MCP registry entry; `skill_server_benchmark.py` script and `benchmark` Makefile target; pytest coverage for the benchmark.
> - **Changed**: `rag-implementation/SKILL.md` now names Milvus/Zilliz vector stores, VoyageAI/Ollama/Gemini embedding providers, AST-aware chunking, and Merkle-tree incremental indexing, with `zilliztech/claude-context` cited as the canonical OSS reference. `context-manager/SKILL.md` and `context-engineering/SKILL.md` cross-link to `code-semantic-search`.
>
> Reference the triggering comparison report: "Adoption derived from [docs/v0.9.7/comparison-claude-context.md](docs/v0.9.7/comparison-claude-context.md) (6 items, P0 through P3)."
>
> Acceptance criteria: `## [Unreleased]` is empty; `## [0.9.8] - <date>` has all bullets; Keep-a-Changelog format preserved.

---

#### 6.2 — Version-bump across the 14 canonical files

**Prompt**:
> Per `MEMORY.md` (`project_release_v097`), the version-bump surface is 14 canonical files. Identify them by grepping the repo for the current version and triaging:
>
> 1. Run: `grep -rn '0\.9\.7' --include='*.md' --include='*.json' --include='*.sh' --include='*.ps1' --include='*.yml'` (or equivalent) to list every file referencing v0.9.7.
> 2. Triage into three groups:
>    - **Canonical version-holding files** (update to 0.9.8): typically `README.md`, `README_zh.md`, `scripts/installer.sh` (version variable near top), `scripts/installer.ps1` (version variable), `data/skills.json` (`version` field), `data/marketplace.json` (`version`), `data/templates.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/CATALOG-COVERAGE.md`, `catalog/hooks/session-start.sh` (banner), and ~3 others. Verify count = 14.
>    - **Historical references** (leave alone): `docs/v0.8.*/`, `docs/v0.9.*/development/history/`, prior `CHANGELOG.md` entries, `docs/v0.9.7/comparison-claude-context.md`, `docs/v0.9.7/RELEASE_NOTES.md`, `docs/v0.9.7/implementation-plan.md`.
>    - **Documentation mentioning v0.9.7 as context** (review case-by-case): `README.md` body text, `docs/DEVLOG.md`, etc. — update only where the mention is "current version".
>
> 3. Edit each canonical file, replacing `0.9.7` → `0.9.8` only at version-reference sites (not in changelog history or historical references).
>
> 4. If the count comes out different from 14, update the `MEMORY.md` entry `project_release_v097` accordingly and annotate the discrepancy. Do not silently accept a wrong count.
>
> Acceptance criteria: exactly 14 files touched (or documented divergence with explanation); no historical references changed; `make validate` clean; `grep -rn '0\.9\.7' --include='*.md' --include='*.json'` shows only historical references post-change.

---

#### 6.3 — Author `docs/v0.9.8/RELEASE_NOTES.md`

**Prompt**:
> Create `docs/v0.9.8/` and author `docs/v0.9.8/RELEASE_NOTES.md` following the pattern of `docs/v0.9.7/RELEASE_NOTES.md` (131 lines). The v0.9.8 release notes should:
>
> 1. Open with a 2-paragraph summary framing v0.9.8 as an "adoption release" driven by the claude-context comparison.
> 2. List the 6 adoption items with a 1–2 sentence description of each, grouped by tier (P0 / P1 / P2 / P3). Cross-link each item to its source section in `docs/v0.9.7/comparison-claude-context.md`.
> 3. Include a "Migration notes" section: users upgrading from v0.9.7 should re-run the installer to pick up the new `claude-context` MCP entry and the new `code-semantic-search` skill; no breaking changes.
> 4. List the updated skill count (185) and any updated catalog totals.
> 5. Link the plan file: `docs/v0.9.7/plans/adoption-claude-context.md`.
>
> Target length: 100–200 lines.
>
> Acceptance criteria: file exists; all 6 adoption items referenced; cross-links resolve.

---

#### 6.4 — Final full-repo validation

**Prompt**:
> Run the full validation sweep:
>
> 1. `make validate` — clean.
> 2. `make test` — clean.
> 3. `make lint` — clean (ShellCheck on installers).
> 4. Cross-platform installer dry-run (both `.sh` and `.ps1`) against a clean target directory. Verify the target receives the new skill, the new MCP entry, the benchmark script, and the updated context-skill cross-links.
> 5. Confirm no regressions: prior v0.9.7 artifacts (e.g. `compile-deep-research` command and skill, `run-penetration-test`, `deep-research-compilation` skill) remain functional by smoke-invoking one or two.
> 6. Confirm the skill-server MCP starts cleanly and returns 185 skills on `list_categories()` (or whatever aggregate returns skill count).
>
> Acceptance criteria: all 6 checks pass.

---

#### 6.5 — Create the git tag

**Prompt**:
> Once the full validation sweep in 6.4 passes, create the release tag:
>
> 1. `git add -A` (or staged list of the changed files) and `git commit` with a message following the repo's commit style: a short summary line like "release: v0.9.8 — adopt claude-context patterns (6 items)" plus a body enumerating the phases.
> 2. `git tag -a v0.9.8 -m "v0.9.8 — claude-context adoption"`.
> 3. Push (only with explicit user confirmation per the DevAI-Hub destructive-command rule): `git push origin main && git push origin v0.9.8`.
>
> Do NOT push without user confirmation. Do NOT use `--force` or `--no-verify`.
>
> Acceptance criteria: tag exists locally; user has confirmed push (or explicitly deferred it).

---

### Phase 6 Exit Checklist

- [ ] `CHANGELOG.md` shows `## [0.9.8] - <date>` with the 6-item summary
- [ ] 14 canonical files bumped to 0.9.8
- [ ] `docs/v0.9.8/RELEASE_NOTES.md` authored
- [ ] `make validate` + `make test` + `make lint` all clean
- [ ] Cross-platform installer dry-run distributes all v0.9.8 artifacts
- [ ] `git tag v0.9.8` created; push is gated on user confirmation
- [ ] `MEMORY.md` `project_release_v097` entry updated to reflect v0.9.8 (or a new `project_release_v098` entry added)

---

## How to Begin

Run `/implement-phase adoption-claude-context` to start with Phase 1, or paste the prompt from sub-task 1.1 into a fresh Claude Code session.
