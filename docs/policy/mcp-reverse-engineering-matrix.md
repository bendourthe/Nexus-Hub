# MCP Reverse-Engineering Matrix

**Version**: v1.0.0
**Source policy**: [AGENTS.md](../../AGENTS.md) `## MCP Registry Policy`
**Status**: authoritative

This matrix classifies every MCP server referenced by Nexus-Hub (both those kept in `catalog/mcp-configs/mcp-servers.json` and those dropped or reverted) under the MCP Registry Policy decision tree. The matrix is the permanent record of why each entry sits where it does; future registry additions must add a row here with upstream evidence. (The internal server keys were renamed from `devai-*` to `nexus-*` at v2.0.0 alongside the project rename; the original rows below preserve the new key names while the Rationale columns note the v2.0.0 rename.)

The v1.0.0 release was driven off this matrix: drops (Phase 3) and new internal MCP builds (Phases 6 and 7) flow from the `v1.0.0 action` column; deferred rebuilds flow from the `v1.1.0+ action` column into the backlog.

---

## Classification Legend

Listed in decision-tree order (from the policy in `AGENTS.md`). An entry gets the highest-precedence classification that applies:

| Classification | Meaning |
|---|---|
| `already-local` | No outbound calls. Internal Nexus-Hub or zero-outbound Anthropic-official. No action needed. |
| `skill-native` | Capability is achievable by instructing the agent's own LLM; the correct replacement is a skill, not an MCP. |
| `re-full` | Fully reverse-engineerable into a local internal MCP with no loss of function. |
| `re-partial` | Partially reverse-engineerable; some capability depends on a third-party data source; ship what's local, document the gap. |
| `vendor-intrinsic` | The third party IS the data destination (the user is already a customer). Rebuild-as-internal-MCP improves audit and supply-chain posture but does not reduce data flow. Defer to v1.1.0+ unless the audit argument is urgent. |
| `drop-outright` | Capability requires a third-party service that cannot be recreated (for example: "the web"). No local equivalent possible; not worth the trust cost. |

---

## Row Schema

Each row answers:

| Column | What it captures |
|---|---|
| MCP key | The key used in `mcp-servers.json`. |
| Current source | Who maintains the upstream code; package or repo. |
| What it does | One sentence on the capability. |
| Outbound-call surface | Where data goes at runtime, cited with evidence. |
| Classification | Per the legend above. |
| Effort if RE'd | Small / Medium / Large, for the `re-*` rows. |
| v1.0.0 action | What this release does. |
| v1.1.0+ action | What later releases should consider. |
| Rationale / citation | The upstream evidence that supports the classification. External source names appear only in this column (per the policy's Reverse-Engineering Attribution Rule). |

---

## Matrix

### Internal and Local-Only (Always Allowed)

| MCP key | Current source | What it does | Outbound-call surface | Classification | Effort if RE'd | v1.0.0 action | v1.1.0+ action | Rationale / citation |
|---|---|---|---|---|---|---|---|---|
| `nexus-skill-server` | Nexus-Hub internal (`extensions/nexus-skill-server/`, Python 3.10+) | Skill catalog retrieval: `search_skills`, `get_skill`, `list_categories`, `list_bundles`, `get_bundle` | None - reads `data/skills.json` from local disk | `already-local` | n/a | Keep | Expand benchmark coverage in Phase 10; continue keyword-only search | Maintained in-repo; direct filesystem access only. Renamed from `devai-skill-server` at v2.0.0. |
| `filesystem` | Anthropic official (`@modelcontextprotocol/server-filesystem`) | Scoped read/write of files in a user-specified directory | None at the MCP layer; file contents flow to Claude as tool results (standard Claude Code behavior, not MCP-specific) | `already-local` | n/a | Keep | Keep | Anthropic-maintained reference server; no network activity. |
| `memory` | Anthropic official (`@modelcontextprotocol/server-memory`) | Persistent per-session memory store over a local file | None | `already-local` | n/a | Keep | Keep | Anthropic-maintained. Local JSON store. |
| `sequential-thinking` | Anthropic official (`@modelcontextprotocol/server-sequential-thinking`) | Structured step-by-step reasoning scaffold | None | `already-local` | n/a | Keep | Keep | Anthropic-maintained. No I/O beyond the tool call. |
| `sqlite` | Anthropic official (`@modelcontextprotocol/server-sqlite`) | Query a SQLite database file | None at the MCP layer; query results flow to Claude | `already-local` | n/a | Keep | Keep | Anthropic-maintained. SQLite is a local file. |

---

### Skill-native adoptions (no MCP, no outbound calls)

These rows record catalog content adopted from an external project under the `skill-native` classification: pure Markdown skills with zero code and zero runtime dependencies added to Nexus-Hub. Per the Reverse-Engineering Attribution Rule, the upstream repo is named only here, never in the distributed artifact. The action columns are version-scoped to the adopting release.

| MCP key | Current source | What it does | Outbound-call surface | Classification | Effort if RE'd | v2.2.0 action | v2.3.0+ action | Rationale / citation |
|---|---|---|---|---|---|---|---|---|
| n/a (skill, not MCP) | external SDK skill at google-antigravity/antigravity-sdk-python skills/google-antigravity-sdk/ (pinned to v0.1.1 commit observed on 2026-05-21) | Builds autonomous AI agents on the Google Antigravity backend with async agent loop, hooks, policies, MCP integration, multimodal ingestion, triggers, subagents, structured output | None at the Nexus-Hub catalog layer. The SDK itself reaches the Gemini API at user runtime, but Nexus-Hub does not execute the SDK -- the skill teaches the user to install it in their own project | `skill-native` | n/a (already skill-native) | Adopted as catalog/skills/ai-development/google-antigravity-sdk/ in this plan (sub-tasks 1.1-1.3). Source content rewritten to Nexus-Hub tone; upstream repo stripped from every user-facing line per the Reverse-Engineering Attribution Rule | Track upstream SDK releases for material changes (default-model bump, new lifecycle hooks, breaking API changes); refresh the references and examples when meaningful | Source skill at github.com/google-antigravity/antigravity-sdk-python (skills/google-antigravity-sdk/SKILL.md + 7 reference docs + 12 example docs). Apache-2.0 licensed. Classified skill-native because the entire artifact is Markdown content in Anthropic's Agent Skill format -- zero code, zero runtime dependencies in Nexus-Hub. Hard-no items (google-genai runtime dep, bundled Go local-harness binary, Vercel/Context7 skills CLI distribution) explicitly NOT adopted; see docs/archive/v2/v2.2.0/comparison-antigravity-sdk-python.md Section 13 N1-N4 |

---

### Re-full platform-integration adoptions (no MCP, no outbound calls)

These rows record platform-distribution reach adopted from an external project under the `re-full` classification: local file-transform logic rebuilt as `IntegrationBase` subclasses under `scripts/lib/integrations/`, adding no MCP, no outbound call, no dependency, and no credential. Per the Reverse-Engineering Attribution Rule, the upstream repo is named only here, never in the distributed artifact (the subclasses, templates, installer blocks, and AGENTS.md use only generic platform names). The action columns are version-scoped to the adopting release.

| MCP key | Current source | What it does | Outbound-call surface | Classification | Effort if RE'd | v3.4.0 action | v3.5.0+ action | Rationale / citation |
|---|---|---|---|---|---|---|---|---|
| n/a (integration subclasses, not MCP) | external multi-platform converter at msitarzewski/agency-agents (`convert.sh` single-canonical-source -> per-platform transform; MIT) | Extends Nexus-Hub's platform reach to Aider (project-root `CONVENTIONS.md`) and Windsurf (project-root `.windsurfrules` + global `~/.codeium/windsurf/memories/global_rules.md`) - behavioral-guidance surfaces carrying the Nexus-Hub instruction content + `{{SKILL_INDEX}}` block | None. Pure local file emission via the existing `MarkdownIntegration` base (stdlib `pathlib`/`shutil`, shared marker-merge). No network, no credential | `re-full` | Medium | Adopted as `scripts/lib/integrations/aider.py` + `windsurf.py` (Phase 2, sub-tasks 2.2-2.3), registered in `_register_builtins()`, wired into both installers' global + workspace blocks, with new `templates/ai-instructions/base-aider.md` / `base-windsurf.md`. Implemented generically; upstream repo stripped from every user-facing artifact per the Reverse-Engineering Attribution Rule | The C2 canonical-source -> declarative per-platform transform refactor remains deferred to backlog | Source converter at github.com/msitarzewski/agency-agents (`convert.sh` + per-platform target templates). MIT-licensed. Classified `re-full` because the conversion is local file-transform logic with no third-party data destination - reverse-engineering it into native `IntegrationBase` subclasses is a strict reach gain with zero new outbound surface. The platform file conventions themselves (Aider's `CONVENTIONS.md`, Windsurf's `.windsurfrules` / `global_rules.md`) are public, vendor-published conventions. Hard-no items from the same source explicitly NOT adopted: personality/vibe theater + business-division breadth (identity conflict) and multilingual catalog (ASCII-only style-guide conflict); see docs/v3.4.0/comparison-nessie-and-agency-agents.md |
| n/a (integration subclasses, not MCP) | same external multi-platform converter at msitarzewski/agency-agents (`convert.sh` per-platform transform; MIT) | A3-ext: extends platform reach to Kimi (project-local `.kimi/system.md` + `.kimi/agent.yaml`), Qwen (project-root `QWEN.md`), and OpenClaw (project-local `.openclaw/` SOUL + AGENTS + IDENTITY split) - behavioral-guidance surfaces carrying the Nexus-Hub instruction content + `{{SKILL_INDEX}}` block in the primary file | None. Pure local file emission via the existing `MarkdownIntegration` base + a shared `_write_generated` companion helper (stdlib `pathlib`, shared marker-merge for the primary file, dedicated deterministic writes for companions). No network, no credential | `re-full` | Medium | Adopted as `scripts/lib/integrations/kimi.py` + `qwen.py` + `openclaw.py` (Phase 4, sub-tasks 4.2), registered in `_register_builtins()`, wired into both installers' global + workspace blocks, with new `templates/ai-instructions/base-kimi.md` / `base-qwen.md` / `base-openclaw.md`. Reuses the Phase 2 Aider/Windsurf pattern; global scope skips-with-note unless the platform config root (`~/.kimi`, `~/.qwen`, `~/.openclaw`) is detected. Implemented generically; upstream repo stripped from every user-facing artifact per the Reverse-Engineering Attribution Rule | The C2 canonical-source -> declarative per-platform transform refactor remains deferred to backlog | Source converter at github.com/msitarzewski/agency-agents (`convert.sh` + per-platform target templates). MIT-licensed. Classified `re-full` for the same reason as the Aider/Windsurf row: local file-transform logic, no third-party data destination, strict reach gain with zero new outbound surface. The platform file conventions (Kimi's `agent.yaml` + `system.md`, Qwen's `QWEN.md`, OpenClaw's SOUL/AGENTS/IDENTITY split) are public, vendor-published conventions. See docs/v3.4.0/comparison-nessie-and-agency-agents.md |

---

### Dropped in v1.0.0 (Reverse-Engineered or Drop-Outright)

| MCP key | Current source | What it does | Outbound-call surface | Classification | Effort if RE'd | v1.0.0 action | v1.1.0+ action | Rationale / citation |
|---|---|---|---|---|---|---|---|---|
| `context7` | Upstash (`@upstash/context7-mcp`) | Up-to-date library documentation lookup | Every query goes to Upstash servers; library names and search queries leave the local machine | `re-partial` | Medium | **Drop.** Ship the `local-docs-lookup` skill (Phase 7.3) covering local pydoc / go doc / vendored README patterns. Continuously-updated library index capability is documented as a gap. | Consider a local documentation cache MCP only if demand materializes; accept the staleness tradeoff explicitly. | Upstash runs a hosted indexed library corpus; the freshness aspect cannot be fully replicated locally without re-crawling and re-indexing upstream sources. Query text (often generated by the agent from local context) is the leak vector. |
| `exa-web-search` | Exa (`exa-mcp-server`) | Neural web search | Every query goes to exa.ai; full search queries (often agent-composed from local context) leave the machine | `drop-outright` | n/a | **Drop.** No replacement ships in v1.0.0; users who need web search can add the entry back to their own settings, aware of the cost. | None planned. Web search by definition requires a third-party service; the trust cost exceeds the benefit for the target regulated-industry / high-trust profile. | The web is not reverse-engineerable. Query-to-third-party is the entire capability. |
| `firecrawl` | Firecrawl (`firecrawl-mcp`) | Web scraping / site crawl with HTML extraction | URLs and optional auth sent to firecrawl.dev; scraped content returned via that intermediary | `re-full` | Medium | **Drop and replace** with the internal `nexus-web-fetch` MCP (Phase 7.1; renamed from `devai-web-fetch` at v2.0.0). HTTPS fetch goes directly to the target URL; no third-party intermediary. RFC 1918 blocked by default for SSRF safety. | Add optional Playwright-based JS rendering (currently raises `NotImplementedError`). | Scraping is fundamentally HTTP fetch + HTML extraction. Both are standard stdlib + well-known open-source libraries (`httpx`, `beautifulsoup4`, `readability-lxml`). Eliminating the Firecrawl intermediary is a strict improvement. |
| `magic-ui` | 21st.dev (`@21st-dev/magic@latest`) | UI component generation via an external LLM call | Component specs and design intent sent to 21st.dev's generation service | `skill-native` | Small | **Drop and replace** with the `ui-component-generation` skill (Phase 7.2). Zero code - the skill instructs the agent to generate components directly using its own LLM. | None planned. | The capability is "ask an LLM to generate UI code." The agent is already an LLM. The correct replacement is skill documentation, not an MCP. |

---

### Kept as Vendor-Intrinsic Wrappers (Your-Own-Account)

For each row below, the v1.0.0 `_comment` field (Phase 3) must inline the 5-question audit from the **Rationale** column.

| MCP key | Current source | What it does | Outbound-call surface | Classification | Effort if RE'd | v1.0.0 action | v1.1.0+ action | Rationale / citation |
|---|---|---|---|---|---|---|---|---|
| `github` | Anthropic-maintained GitHub MCP (`@modelcontextprotocol/server-github`) | Interact with GitHub repositories, issues, PRs | GitHub API with a user-supplied PAT; PAT scope gates reach | `vendor-intrinsic` | Medium | Keep as vendor wrapper. `_comment` audit: (1) user's agent spawns `npx` subprocess; (2) calls github.com/api with user's PAT; (3) requires GITHUB_TOKEN / PAT; (4) transmits whatever the agent supplies (issue bodies, queries) which may include repo context; (5) user already has a GitHub account and repo. Vendor-intrinsic: GitHub is the intended destination. | Build `nexus-github` internal wrapper using `gh` CLI or `PyGithub` for audit/supply-chain improvement. Data flow unchanged. | GitHub is where the user's code already lives. The MCP gives a typed tool surface over an API the user is already paying for / bound to. Reverse-engineering changes the implementer but not the data destination. |
| `postgres` | Anthropic-maintained (`@modelcontextprotocol/server-postgres`) | Query a Postgres database via user-supplied connection string | Postgres wire protocol to the user's own database | `vendor-intrinsic` | Small | Keep. `_comment` audit: (1) `npx` subprocess; (2) Postgres connection to the user's DB at DATABASE_URL; (3) requires DATABASE_URL; (4) query results flow to Claude (not to a new third party); (5) user owns the DB. Vendor-intrinsic: the DB IS the destination. | Build `nexus-postgres` internal wrapper over `psycopg` if audit-posture demand emerges. | The DB belongs to the user. No third-party data processor is introduced. Wrapping is a convenience over the wire protocol. |
| `supabase` | Supabase official (`@supabase/mcp-server-supabase`) | Interact with a user's Supabase project | Supabase API with the user's access token | `vendor-intrinsic` | Medium | Keep. `_comment` audit: (1) `npx`; (2) supabase.com/api with user's access token; (3) requires SUPABASE_ACCESS_TOKEN; (4) transmits user-provided queries / rows; (5) user is a Supabase customer. | Build `nexus-supabase` internal wrapper over `supabase-py`. Data flow unchanged. | Supabase is the user's backend. Vendor-intrinsic. |
| `railway` | Railway official (`@railway/mcp-server`) | Manage Railway deployments | Railway API with RAILWAY_API_TOKEN | `vendor-intrinsic` | Medium | Keep. `_comment` audit: (1) `npx`; (2) railway.app/api with token; (3) RAILWAY_API_TOKEN; (4) deployment metadata and user commands; (5) user is a Railway customer. | Build `nexus-railway` internal wrapper if demand. | Vendor-intrinsic per the decision tree. |
| `vercel` | Vercel official (`@vercel/mcp-adapter`) | Interact with Vercel deployments | Vercel API with VERCEL_TOKEN | `vendor-intrinsic` | Medium | Keep. `_comment` audit: (1) `npx`; (2) vercel.com/api with token; (3) VERCEL_TOKEN; (4) deployment metadata and user commands; (5) user is a Vercel customer. | Build `nexus-vercel` internal wrapper if demand. | Vendor-intrinsic. |
| `cloudflare` | Cloudflare official (`@cloudflare/mcp-server-cloudflare`) | Manage Cloudflare resources | Cloudflare API with CLOUDFLARE_API_TOKEN / CLOUDFLARE_ACCOUNT_ID | `vendor-intrinsic` | Medium | Keep. `_comment` audit: (1) `npx`; (2) api.cloudflare.com with token; (3) CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID; (4) resource queries and user commands; (5) user is a Cloudflare customer. | Build `nexus-cloudflare` internal wrapper if demand. | Vendor-intrinsic. |

---

### New in v1.0.0 (Reverse-Engineered Internal MCPs)

These land via Phases 6 and 7 of the plan. Registry entries are added by Phase 3 (for the `_comment` audit template structure) and Phase 6/7 (for the entry body itself).

| MCP key | Current source | What it does | Outbound-call surface | Classification | Effort if RE'd | v1.0.0 action | v1.1.0+ action | Rationale / citation |
|---|---|---|---|---|---|---|---|---|
| `nexus-code-search` | Nexus-Hub internal (new; `extensions/nexus-code-search/`, Python 3.10+) | Local code search over a repo: `index_codebase`, `search_code`, `clear_index`, `get_indexing_status`. Keyword-only in v1.0.0 (inverted index + rapidfuzz). Content-hash incremental re-indexing. | None. Indexes are persisted under `<repo>/.nexus/code-index/`. No network. | `already-local` | n/a (this IS the reverse-engineering target) | Build and ship as keyword-only MVP. | Add dense retrieval (ONNX embeddings via `fastembed` + `sqlite-vec` vector store) + RRF hybrid mode; add tree-sitter AST chunking; upgrade the flat manifest to a directory-keyed Merkle tree. | Reverse-engineers one common "semantic code search" pattern into fully local code. No external attribution in the shipped artifact per the policy. Renamed from `devai-code-search` at v2.0.0 (index path also moved from `.devai/code-index/` to `.nexus/code-index/`). |
| `nexus-web-fetch` | Nexus-Hub internal (new; `extensions/nexus-web-fetch/`, Python 3.10+) | Local web fetch: `fetch_url(url, render_js, extract_mode)`. `httpx` for fetch; `beautifulsoup4` + `readability-lxml` for extraction. SSRF guard blocks RFC 1918 / loopback / link-local / `file://` by default. | HTTPS only, to user-specified URLs. No third-party intermediary. | `already-local` (as reverse-engineered target; see also: `firecrawl` row above) | n/a (this IS the reverse-engineering target) | Build and ship. `render_js=True` reserved for v1.1.0 (raises `NotImplementedError`). | Add optional Playwright-based JS rendering. Consider adding per-domain rate limiting. | Scraping-as-service is replaced with fetch-to-target-URL. Data destination is the URL itself, not a third-party processor. Renamed from `devai-web-fetch` at v2.0.0 (config path moved from `~/.devai/web-fetch.yaml` to `~/.nexus/web-fetch.yaml`). |

---

### New in v3.2.0 (Reverse-Engineered Internal MCP)

Added by the v3.2.0 `adoption-headroom` plan (Phase 4). Registry entry lives in `catalog/mcp-configs/mcp-servers.json` with the 5-question audit inlined in its `_comment`.

| MCP key | Current source | What it does | Outbound-call surface | Classification | Effort if RE'd | v3.2.0 action | v3.3.0+ action | Rationale / citation |
|---|---|---|---|---|---|---|---|---|
| `nexus-context-compressor` | Nexus-Hub internal (new; `extensions/nexus-context-compressor/`, Python 3.10+) | Local-first, reversible context compression: `context_compress(payload, persist)` compresses structured tool output (JSON arrays, code) and leaves logs/prose untouched; `context_retrieve(marker)` resolves a `<<ccr:HASH N_rows>>` marker back to the exact dropped records. Also a PreToolUse hook (`catalog/hooks/compress-output.sh`) and a CLI (`python -m nexus_context_compressor compress`). | None. Deterministic stdlib strategies; payloads are compressed in-process and dropped spans persist to a local SQLite CCR store under `~/.nexus-hub/cache/`. No network. | `re-full` | Medium | Build and ship as the owned replacement for the external `rtk` context-compression recommendation. Deterministic strategies (SmartCrusher / CacheAligner / ContentRouter / CodeCompressor) + reversible CCR retrieval. The optional ML token-dropper (default-off) lands in Phase 6. | Free-text/log compression via the optional Phase 6 ML token-dropper; an accuracy-regression gate (Phase 5). | Replaces a "trust a third-party GitHub binary installed via `cargo install --git`" posture (the external `rtk` Rust proxy) with an owned, audited, fully-local engine. rtk is command-output-only and lossy; this engine is reversible (CCR store) and routes by content type. The compression logic is pure Python + stdlib, so reverse-engineering it locally is a strict supply-chain improvement with no data-flow change (there was never an outbound call to remove -- rtk is local too -- but the trust surface of an unaudited external binary is eliminated). Upstream name appears only in this column per the Reverse-Engineering Attribution Rule. |

---

### Reverted in v1.0.0

| MCP key | Current source | What it does | Outbound-call surface | Classification | Effort if RE'd | v1.0.0 action | v1.1.0+ action | Rationale / citation |
|---|---|---|---|---|---|---|---|---|
| `claude-context` | Zilliz (`@zilliz/claude-context-mcp`) | Semantic code search over a user's codebase | Ships code chunks to OpenAI's embedding API; vectors stored in Milvus (local) or Zilliz Cloud (managed) | `re-partial` | Large | **Reverted** (was added in an aborted v0.9.8 Phase 2, now undone). The knowledge pattern is reverse-engineered into `nexus-code-search` (Phase 6; renamed from `devai-code-search` at v2.0.0) + the `code-semantic-search` skill (Phase 8). | v1.1.0 adds dense/hybrid retrieval to `nexus-code-search` using a fully-local embedding backend (`fastembed` ONNX), closing the capability gap without the upstream's third-party data flow. | This entry is the entire reason the v1.0.0 plan exists. The upstream is an 8.4k-star MIT project whose default flow ships source code to OpenAI for embedding; that is the hard-no case. The knowledge is valuable and can be reverse-engineered; the external MCP cannot be shipped. |

---

### Declined in v3.6.0 (Drop-Outright under the MCP Registry Policy)

These rows record two GitHub Spec Kit extensibility systems that the v3.6.0 re-comparison evaluated and **deliberately declined** under the policy decision tree. They are not MCPs; they are recorded here so the decline is durable -- a future comparison reads these rows and recognizes the candidates as already-adjudicated rather than re-surfacing them as fresh gaps (the same discipline that closed the v2.0.0 G1-G12 series). Both are `drop-outright` because each crosses the trust boundary the policy exists to govern (third-party code or plaintext credentials), and neither can be reverse-engineered into a local-first equivalent without re-introducing exactly the surface that triggers the decline. The action columns are version-scoped to the declining release.

| MCP key | Current source | What it does | Outbound-call surface | Classification | Effort if RE'd | v3.6.0 action | v3.7.0+ action | Rationale / citation |
|---|---|---|---|---|---|---|---|---|
| n/a (external auth framework, not MCP) | GitHub Spec Kit authentication framework (`src/specify_cli/authentication/{base,github,azure_devops,http,config}.py`); a pluggable provider registry (GitHub Bearer, Azure DevOps Basic-PAT) injecting auth headers for private remote template / extension / workflow catalog fetches, opt-in via `~/.specify/auth.json` | Stores GitHub / Azure DevOps PAT credentials to authenticate fetches of private remote catalogs | Authenticated HTTPS requests to GitHub / Azure DevOps; the PAT is stored in **plaintext** in a user dotfile, reachable by any co-resident extension or shell step | `drop-outright` | n/a (no local-first equivalent is possible without re-introducing the credential surface) | **Dropped.** Not adopted in any form -- no auth provider, no credential store, no remote-catalog fetch added. v3.6.0 introduces zero new credential surface. | None planned. Reconsider only in the architecturally-absent event that Nexus-Hub ever ships a private *remote* catalog (today the catalog IS the repo, installed locally), and even then only with a secrets-manager / OS-keychain backend, never plaintext-dotfile storage. | Plaintext PAT storage directly contradicts the secret-handling rules in `catalog/rules/*/security.md` (no plaintext long-lived credentials in committed or dotfile config), and remote credentialed catalog fetch is N/A for a local-first catalog that ships in the repo and installs locally. Upstream evidence: `src/specify_cli/authentication/{github,azure_devops}.py`. Full analysis: [docs/v3.6.0/comparison-spec-kit.md](../v3.6.0/comparison-spec-kit.md) Section 6.3 + Bucket D (candidate N5). |
| n/a (external extension-install channel, not MCP) | GitHub Spec Kit third-party extension system (`extensions/RFC-EXTENSION-SYSTEM.md`, `extensions/EXTENSION-API-REFERENCE.md`, `src/specify_cli/extensions.py`); installs unsandboxed community-catalog plugin code (commands / hooks / templates) into `.specify/extensions/`, layered at runtime with agent privileges | A code-distribution channel that fetches and runs third-party plugin code from a dual curated / community catalog | Remote catalog fetch of third-party code; the installed code runs with agent privileges (no sandbox), can read env / config, and is an exfiltration surface | `drop-outright` (the *capability* is already reverse-engineered into the local skill catalog) | n/a -- the local-first equivalent already exists and is safer | **Dropped.** No unsandboxed third-party-code install path is added. The capability (extend the agent with new commands / skills) is already met by Nexus-Hub's skill catalog (`data/marketplace.json` + `data/bundles.json` + `nexus-skill-server` + `/skills import`) WITH a pre-install scanner (`skill-security-scan` skill + `nexus-skill-scanner` MCP) that the upstream lacks. The v3.6.0 N6 work (Phase 4) further hardened that import path (HTTPS-only + discovery-only flag + hash-on-import). | None planned. The scanned local skill mechanism is the reverse-engineered answer; adopting an unsandboxed community-catalog code-install would be a net **regression** in trust posture, not a gain. | Code-distribution-as-service is on the MCP Registry Policy hard-no spectrum. The upstream trust model is catalog curation + an `install_allowed` flag with **no** pre-install scanner; Nexus-Hub already exceeds it (Section 8 of the comparison). Upstream evidence: `extensions/RFC-EXTENSION-SYSTEM.md`, `src/specify_cli/extensions.py`. Full analysis: [docs/v3.6.0/comparison-spec-kit.md](../v3.6.0/comparison-spec-kit.md) Section 6.3 + Bucket D (candidate N1b). |

---

### Adopted in v3.7.0 (previously deferred -- N4 self-upgrade)

This row records N4 (a self-upgrade CLI), deferred in v3.6.0 as low-ROI (DF-v36-1) and reprioritized by the maintainer as part of the v3.7.0 install-UX overhaul. It is policy-clean because the only outbound call it adds is to the project's OWN GitHub (the same posture the installer/bootstrap already has) -- no third-party data processor, credential, or new dependency. The action columns are version-scoped to the adopting release.

| MCP key | Current source | What it does | Outbound-call surface | Classification | Effort if RE'd | v3.7.0 action | v3.8.0+ action | Rationale / citation |
|---|---|---|---|---|---|---|---|---|
| n/a (local self-upgrade CLI, not MCP) | GitHub Spec Kit `specify self upgrade` (a packaged-CLI in-place updater) | Ships a local `nexus-hub` CLI on PATH (`~/.nexus-hub/bin/nexus-hub` POSIX + `nexus-hub.cmd` Windows, thin shims over the stdlib-only `scripts/nexus_hub_cli.py` core). `nexus-hub --version` reads the installer-written `~/.nexus-hub/VERSION`; `nexus-hub upgrade` compares it to the latest `.claude-plugin/plugin.json` version on the project's own GitHub, prints the matching CHANGELOG block as a what's-new summary, and on confirmation re-runs the Phase 1 install bootstrap to upgrade in place | One version-check fetch to the project's OWN GitHub (`raw.githubusercontent.com` / `github.com`), preferring `curl`, falling back to `wget`, then stdlib `urllib`; the upgrade itself re-runs the existing bootstrap (also project-GitHub-only). No third-party processor, credential, or new dependency | `re-full` | Medium | **Adopted** in the install-ux-overhaul plan Phase 3 (sub-tasks 3.1-3.3): the `nexus-hub` launcher + version marker are installed by both installers (`install_cli_launcher` / `Install-CliLauncher`); offline / fetch-failure is handled with a clear message and a non-zero exit (no partial state). Implemented generically; the upstream is named only in this column per the Reverse-Engineering Attribution Rule | None planned. Revisit only if a richer self-management surface (channel pinning, rollback) becomes a stated goal | Reverse-engineers the *intent* of `specify self upgrade`, not its packaging: Nexus-Hub is a template catalog consumed from the repo (not a `uv`/`pip`-installed CLI), so the local equivalent is a launcher over the existing bootstrap, and the version check reuses the installer's existing project-GitHub posture rather than introducing a new data destination. Deferred as DF-v36-1 in v3.6.0; reprioritized for v3.7.0. Full analysis: [docs/v3.6.0/comparison-spec-kit.md](../v3.6.0/comparison-spec-kit.md) Bucket C (candidate N4) + [docs/v3.7.0/plans/install-ux-overhaul.md](../v3.7.0/plans/install-ux-overhaul.md) Phase 3. |

---

## Summary

| Bucket | Count | Notes |
|---|---:|---|
| Kept: internal or local-only | 5 | `nexus-skill-server`, `filesystem`, `memory`, `sequential-thinking`, `sqlite` |
| Kept: vendor-intrinsic (your-own-account) | 6 | `github`, `postgres`, `supabase`, `railway`, `vercel`, `cloudflare` - each with a 5-question audit in its `_comment` |
| Dropped in v1.0.0 | 4 | `context7` (replaced by `local-docs-lookup` skill), `exa-web-search` (drop-outright), `firecrawl` (replaced by `nexus-web-fetch`), `magic-ui` (replaced by `ui-component-generation` skill) |
| New internal MCPs in v1.0.0 | 2 | `nexus-code-search` (keyword-only MVP), `nexus-web-fetch` (SSRF-guarded HTTP fetch + readability) |
| Reverted in v1.0.0 | 1 | `claude-context` (reverse-engineered into `nexus-code-search` + the `code-semantic-search` skill) |
| Deferred to v1.1.0+ | 5+ | dense/hybrid retrieval on `nexus-code-search`; Playwright rendering in `nexus-web-fetch`; vendor-wrapper rebuilds (`nexus-github`, `nexus-postgres`, `nexus-supabase`, `nexus-railway`, `nexus-vercel`, `nexus-cloudflare`) |

**Post-v1.0.0 registry size**: 13 entries (5 already-local + 6 vendor-intrinsic + 2 new internal).

**Post-v3.2.0 registry size**: 14 entries (adds `nexus-context-compressor`, the third new internal MCP, via the `adoption-headroom` plan).

---

## How to Add a New Row

1. Walk the [decision tree](../../AGENTS.md#decision-tree-stop-at-the-first-bucket-that-fits) in `AGENTS.md` and pick the highest-precedence bucket that applies.
2. Cite upstream evidence in the Rationale column (a file path in the upstream repo, a docs URL, or a README section).
3. For `re-full` / `re-partial` classifications, name the internal deliverable (package name, skill name) and the target release.
4. For `vendor-intrinsic` classifications, write the 5-question audit paragraph that Phase 3 copies into the entry's `_comment`.
5. Record the row before opening a PR that touches `catalog/mcp-configs/mcp-servers.json`. No MCP is added without a matrix row.
