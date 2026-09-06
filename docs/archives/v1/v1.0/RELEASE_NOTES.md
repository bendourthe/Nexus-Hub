# Release Notes - DevAI-Hub v1.0.0

**Release Date**: 2026-04-27
**Theme**: Reverse-engineering-first security hardening
**Status**: First stable release

---

## Executive Summary

v1.0.0 is the first stable release of DevAI-Hub. The release theme is **"reverse-engineer locally first; trusted vendor wrappers only when reverse-engineering is infeasible AND the feature is extremely worth it."** The driving constraint was that the registry's existing third-party MCP entries (search-as-service, embeddings-as-service, scraping-as-service, generation-as-service) caused users' agents to ship proprietary source code, prompts, and queries to external data processors - unacceptable for the regulated-industry / high-trust profile this release primarily targets.

**Version note**: 0.9.8 is intentionally skipped. What started as a small v0.9.8 patch (an MCP registry entry addition) accumulated into a major-version security retrofit. The breadth of changes - new policy section in AGENTS.md, two new internal MCP servers, three new skills, breaking removals of 4 registry entries, command-level workflow change in /compare-project - is a major-version event.

The full plan that drove this release is at [docs/archives/v1/v1.0/plans/security-hardening-v100.md](plans/security-hardening-v100.md). The authoritative MCP classification document is [docs/policy/mcp-reverse-engineering-matrix.md](mcp-reverse-engineering-matrix.md).

---

## What's New

### MCP Registry Policy

A canonical governance policy for `catalog/mcp-configs/mcp-servers.json`, authored in [AGENTS.md](../../AGENTS.md) and distributed diff-identical to all 7 platform-instruction surfaces (5 base templates + Copilot rules + Cursor rules).

**The decision tree** (walk in order, stop at the first bucket that fits):

1. **Local-only**: internal DevAI-Hub servers or zero-outbound Anthropic-official servers. Always allowed.
2. **LLM-native skill**: capability achievable by instructing the agent's own LLM. Ship a skill, not an MCP.
3. **Reverse-engineer into a local internal MCP**: build the local equivalent under `extensions/`. Strip external attribution.
4. **Trusted vendor wrapper (your-own-account)**: acceptable only when the vendor is the intrinsic data destination AND reverse-engineering is infeasible AND the feature is extremely worth it.
5. **Otherwise**: drop.

**The 5-question audit** (required in the `_comment` of every registry entry):

1. Who runs the process?
2. What outbound calls does it make and where?
3. What API keys does it require?
4. Does it transmit source code, prompts, or query text to a third party?
5. Does the user already have a commercial relationship with the destination?

**Hard-no list**: search-as-service, embeddings-as-service, scraping-as-service, generation-as-service.

### Reverse-Engineering Matrix

[`docs/policy/mcp-reverse-engineering-matrix.md`](mcp-reverse-engineering-matrix.md) is the authoritative classification document for every MCP shipped or considered. 18 rows organized into five sections:

- **Already-local** (5): `devai-skill-server`, `filesystem`, `memory`, `sequential-thinking`, `sqlite`.
- **Dropped in v1.0.0** (4): `context7`, `exa-web-search`, `firecrawl`, `magic-ui`.
- **Vendor-intrinsic, kept** (6): `github`, `postgres`, `supabase`, `railway`, `vercel`, `cloudflare`.
- **New in v1.0.0** (2): `devai-code-search`, `devai-web-fetch`.
- **Reverted** (1): `claude-context` (was added in an aborted v0.9.8 Phase 2; never tagged).

Each row cites upstream evidence and names its v1.0.0 deliverable (for `re-*` classifications) or its 5-question-audit paragraph (for `vendor-intrinsic`).

### New Internal MCP Servers

Both: zero outbound calls, zero API keys, zero model downloads.

#### `devai-code-search` ([`extensions/devai-code-search/`](../../extensions/devai-code-search/))

Local code search over a repository. Replaces the data-leaky pattern of shipping source code to external embedding APIs.

- **Tools**: `index_codebase(root, force=False)`, `search_code(query, mode='keyword', limit=10)`, `clear_index(root)`, `get_indexing_status(root)`.
- **Implementation**: inverted index + `rapidfuzz` fuzzy scoring; SHA-256 content-hash incremental indexing; `.gitignore` + `.devaiignore` respect; recursive character splitter with language-aware separators (600-char target, 80-char overlap); advisory file-lock for concurrent indexers; symlink-safe walker.
- **Storage**: `<repo>/.devai/code-index/{chunks.json, manifest.json}`. JSON only, no pickle.
- **v1.1.0 roadmap**: dense / hybrid retrieval via local ONNX embeddings (`fastembed`) + `sqlite-vec` vector store. Tree-sitter AST chunking starting with Python.

#### `devai-web-fetch` ([`extensions/devai-web-fetch/`](../../extensions/devai-web-fetch/))

Single-URL HTTP fetch + readability extraction. Replaces the data-leaky pattern of routing fetches through third-party scraping services.

- **Tool**: `fetch_url(url, render_js=False, extract_mode='readability'|'text'|'raw')`.
- **SSRF guard**: blocks RFC 1918, loopback, link-local, `file://` by default. Per-hop revalidation on every redirect target. DNS pinning via `pin_hostname_to_ip` context manager prevents rebinding TOCTOU.
- **Limits**: 30s timeout, 5 MB max body, no cookies, no auth headers, max 5 redirects. User-overridable via `~/.devai/web-fetch.yaml`.
- **v1.1.0 roadmap**: optional Playwright JS rendering (currently `render_js=True` raises `NotImplementedError`).

### Three New Skills

All three are de-branded - no external attribution; references point at internal artifacts only.

- **`code-semantic-search`** ([catalog/skills/ai-development/code-semantic-search/SKILL.md](../../catalog/skills/ai-development/code-semantic-search/SKILL.md)) - specialized sibling of `rag-implementation` for code corpora. References the internal `devai-code-search` MCP as the reference implementation.
- **`ui-component-generation`** ([catalog/skills/developer-experience/ui-component-generation/SKILL.md](../../catalog/skills/developer-experience/ui-component-generation/SKILL.md)) - LLM-native replacement for external component-generation services. Replaces `magic-ui`-class MCPs.
- **`local-docs-lookup`** ([catalog/skills/research/local-docs-lookup/SKILL.md](../../catalog/skills/research/local-docs-lookup/SKILL.md)) - 7-step grounding sequence for library / API questions (introspect -> vendored README -> shipped docs -> type stubs -> project docs -> man pages -> user-approved single URL via `devai-web-fetch`). Partial replacement for `context7`-class MCPs.

Total skill count: **187** (was 184 in v0.9.7).

### `/compare-project` Security & Risk Assessment

A new mandatory **Section 9** in every comparison report, with four subsections:

- **9.1 Threat Model Comparison** - side-by-side table covering runtime deps, outbound destinations, credentials, data leaving the machine, vendor relationships.
- **9.2 Per-Item Risk Scorecard** - assigns each adoption candidate from Section 5 a risk tier (None / Low / Medium / High).
- **9.3 Reverse-Engineering Viability Analysis** - classifies every candidate per the MCP Registry Policy decision tree.
- **9.4 Recommendation Ordering** - re-orders candidates: skill-native first, then RE builds, then vendor-intrinsic (with justification), then drops moved to N-item list.

Section 9 gates the adoption recommendations in Section 11. The chain into `/generate-plan` always passes `reverse-engineer-first=true`, so generated plans sequence skill-native first, then RE builds, then vendor-intrinsic.

### Internal MCP Benchmark Harness

`make benchmark` runs [`scripts/devai_mcp_benchmark.py`](../../scripts/devai_mcp_benchmark.py) against all 3 internal MCPs (`devai-skill-server`, `devai-code-search`, `devai-web-fetch`). The harness includes a no-network-guard context manager that monkeypatches `socket.socket.connect` to raise on any outbound attempt during the local-only MCP phases. Results are appended to `data/benchmarks/mcp.json` (gitignored; last 10 runs retained).

### `/run-deep-review` - Pre-Release Deep Review Orchestrator

[`/run-deep-review`](../../catalog/commands/run-deep-review.md) is the new release-readiness command. It chains every individual review/audit/pentest command DevAI-Hub ships, layers in pre-release readiness checks (known gaps from CHANGELOG / DEVLOG / plans / matrix / TODOs / memory / GitHub issues; health gates; dependency CVEs; docs and git hygiene; project validators), and synthesizes everything into a single severity-ranked report with a GO / GO-WITH-CONDITIONS / NO-GO verdict.

**12-phase run** (~30-90 minutes depending on codebase size):

| Phase | Output | Coverage |
|---|---|---|
| 1 - Known gaps collection | `00-known-gaps.md` | CHANGELOG / DEVLOG / plans / matrix / TODOs / memory / GitHub issues |
| 2 - Health gates | `01-health-gates.md` | Test execution, **80% line-coverage threshold**, lint, build |
| 3 - Dependency scan | `02-dependency-scan.md` | CVEs, license audit, version pinning |
| 4 - Docs / git / CI/CD hygiene | `03-docs-git-cicd-hygiene.md` | Broken links, CHANGELOG vs commits, working tree state, API doc staleness, **CI/CD workflow file audit, CI run history (gh run list), branch protection, version-bump consistency, tag hygiene, pending draft releases** |
| 5 - Project validators | `04-project-validators.md` | `make validate/lint/test/check/ci`, `npm run *`, pre-commit |
| 6 - `/analyze-codebase` | `05-analysis.md` | 12-section architecture report |
| 7 - `/run-security-audit` | `06-security-audit.md` (report-only) | OWASP secrets, missing auth, unvalidated inputs |
| 8 - `/run-penetration-test --depth=deep` | `07-penetration-test.md` | 6-hunter parallel pentest including business-logic + advanced-attack hunters |
| 9 - `/review-codebase` | `08-code-review.md` | Quality, SOLID, performance, testing review |
| 10 - Synthesis | `SYNTHESIS.md` | Deduplicated cross-phase findings; P0/P1/P2/P3; GO / GO-WITH-CONDITIONS / NO-GO verdict |
| 11 - `/generate-plan` | `../plans/pre-release-deep-review-remediation.md` | Phased remediation plan |
| 12 - Index | `INDEX.md` | Cross-reference + navigation |

All artifacts land under `docs/<next-version>/review/`. The synthesis dedupes findings across phases (e.g. an issue flagged by both `/run-security-audit` and `/run-penetration-test` is reported once with cross-references). Use `--scope <path>` to restrict; use `--target-version` to override the auto-computed next version. Use this command before cutting a major or minor release; use the individual review commands during day-to-day development.

### Style-Guide Files Relocated

`compile-deep-research-style-guide.md` and `generate-report-style-guide.md` were both surfacing as slash commands (`/compile-deep-research-style-guide`, `/generate-report-style-guide`), confusing users about which to invoke. Both files moved to `catalog/style-guides/` (sibling of `catalog/commands/`); installer ships them to `~/.devai-hub/style-guides/`. After v1.0.0 install, neither appears in the slash menu.

The `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, and `.cursor/rules/devai-hub.mdc` rule for new commands was updated: future commands needing a style-guide reference put it in `catalog/style-guides/`, not in `catalog/commands/`.

### De-Branded `rag-implementation` Skill

Phase 1 of the abandoned `adoption-claude-context` plan added technical content about hybrid BM25+dense retrieval, AST chunking, and Merkle-tree incremental indexing. v1.0.0 keeps the technical patterns but strips every external-source attribution (`zilliztech/claude-context`, `Zilliz Cloud`, `voyage-code-3`, SWE-bench metrics, upstream file-path citations). The "Canonical OSS Reference" subsection was renamed to "Hybrid Retrieval in Practice" and re-points at the internal `devai-code-search` MCP.

---

## Breaking Changes

### Removed Third-Party MCP Registry Entries

Four entries deleted from [`catalog/mcp-configs/mcp-servers.json`](../../catalog/mcp-configs/mcp-servers.json):

| Removed entry | Why | Replacement under v1.0.0 policy |
|---|---|---|
| `context7` (Upstash library docs) | Search-as-service; query text leaves the local machine | `local-docs-lookup` skill (partial - acknowledges the freshness gap) |
| `exa-web-search` (Exa web search) | Search-as-service; query text leaves the local machine | None. The web is not reverse-engineerable. Drop-outright under the policy. |
| `firecrawl` (web scraping) | Scraping-as-service; URLs and target content go through firecrawl.dev | `devai-web-fetch` MCP |
| `magic-ui` (21st.dev UI generation) | Generation-as-service; component specs go to 21st.dev | `ui-component-generation` skill (LLM-native; zero MCP) |

**Migration**: users who relied on these can re-add them to their own `.claude/settings.json`; DevAI-Hub no longer ships the snippets. The matrix at [docs/policy/mcp-reverse-engineering-matrix.md](mcp-reverse-engineering-matrix.md) documents the decision per-row.

### Removed Slash Commands

- `/compile-deep-research-style-guide` and `/generate-report-style-guide` no longer surface in the slash menu (moved to `catalog/style-guides/`). The parent commands `/compile-deep-research` and `/generate-report` are unaffected and still reference their style guides at the new path.

### Removed v0.9.7 Forwarding Shim

- `/generate-implementation-plan` was a deprecation alias for `/generate-plan` carried for one release. Removed in v1.0.0 along with all textual references that described the alias as preserved. Users must now invoke `/generate-plan` directly.

---

## Migration Guide

### From v0.9.7 -> v1.0.0

1. **Re-run the installer** (`./install.sh` on macOS/Linux, `install.bat` on Windows) to:
   - Pick up the new `~/.devai-hub/style-guides/` directory.
   - Install the two new internal MCPs (`devai-code-search`, `devai-web-fetch`) into the existing `~/.devai-hub/mcp-server-venv/`.
   - Update `~/.claude/settings.json` `mcpServers` to register the new internal MCPs.

2. **Audit your `.claude/settings.json`**: if you copied any of the four removed entries (`context7`, `exa-web-search`, `firecrawl`, `magic-ui`) from a previous version of DevAI-Hub, decide whether to keep them locally:
   - If you had explicit reasons to use them and accept the third-party data flow, leave them in your personal settings. DevAI-Hub will not remove them; the registry change applies only to the curated source-of-truth.
   - If you adopted them by default, consider migrating to the v1.0.0 replacements (skills `ui-component-generation` and `local-docs-lookup`, plus the new `devai-web-fetch` MCP).

3. **Review the [MCP Registry Policy](../../AGENTS.md#mcp-registry-policy)** in `AGENTS.md`. Future MCP additions you propose to DevAI-Hub must walk the decision tree.

4. **No code-level migration required** for skills or commands - they continue to work. The `rag-implementation` skill content was de-branded but retains all technical guidance. Cross-references to `code-semantic-search` from `context-manager` and `context-engineering` are additive.

### Upgrading internal MCP servers

If you previously installed `devai-skill-server` from v0.9.7, the same shared venv at `~/.devai-hub/mcp-server-venv/` is reused. The installer adds the two new packages alongside it. No conflict.

---

## Security

### Pre-Release Security Review

Two-pass security review performed before tag:

- **`/security-review`** (first pass) found 3 HIGH-severity findings, all fixed:
  - Pickle deserialization RCE in `devai-code-search/store.py` -> replaced with JSON; regression tests added.
  - SSRF via `follow_redirects=True` in `devai-web-fetch/fetcher.py` -> manual redirect loop with per-hop revalidation; regression tests added.
  - SSRF via DNS rebinding in `ssrf_guard.py` -> new `pin_hostname_to_ip` context manager; regression tests added.

- **`/run-penetration-test --depth=deep`** (second pass) verified the 3 HIGH fixes hold and identified one new MEDIUM finding, also fixed:
  - Symlink-following in `devai-code-search/indexer.py` -> walker now skips `entry.is_symlink()`; regression test added (skipped on Windows where symlink creation requires elevation, runs on POSIX CI).

The full pen test report is at [docs/security/penetration-test-2026-04-27.md](../security/penetration-test-2026-04-27.md). Three informational items are documented as known limitations, deferred to v1.0.1:

1. README prompt-injection caveat for `devai-web-fetch` and `devai-code-search` (architectural risk inherent to any tool that returns external content).
2. Port allowlist in `GuardConfig` for `devai-web-fetch` (defense-in-depth).
3. File-lock TOCTOU on networked filesystems for `devai-code-search` (operational reliability, no security boundary crossed).

### v1.0.0 Net Security Posture

- No outbound calls from internal MCPs (`devai-skill-server`, `devai-code-search`).
- `devai-web-fetch` makes outbound HTTPS only to user-specified URLs, with SSRF guard + DNS pinning + redirect re-validation.
- No third-party intermediary in the data path of any internal MCP.
- Pickle deserialization eliminated from the codebase.
- Vendor-intrinsic registry entries (`github`, `postgres`, `supabase`, `railway`, `vercel`, `cloudflare`) carry the 5-question audit in their `_comment` fields and are gated on the user already being a customer of the vendor.

---

## Test Coverage

| Surface | Tests | Notes |
|---|---|---|
| `extensions/devai-skill-server` | 37 | +13 over v0.9.7 (benchmark coverage) |
| `extensions/devai-code-search` | 36 + 1 platform-skip | New in v1.0.0 |
| `extensions/devai-web-fetch` | 23 | New in v1.0.0 |
| `catalog/hooks/tests/` | 179 | +N for v1.0.0 (installer smoke + version-constant) |
| **Total** | **275+** | All green at tag time |

CI runs the full suite plus `make validate` (JSON catalog integrity), `make lint` (ShellCheck on installers), and ShellCheck `--severity=warning`.

---

## Roadmap

### v1.0.1 (planned, no fixed date)

- README prompt-injection caveat in `devai-code-search` and `devai-web-fetch`.
- Port allowlist for `devai-web-fetch` (`{80, 443}` default).
- Networked-filesystem documentation note for `devai-code-search`.

### v1.1.0 (matrixed)

- Dense / hybrid retrieval on `devai-code-search` (local ONNX embeddings via `fastembed`; `sqlite-vec` vector store; RRF fusion).
- Tree-sitter AST chunking on `devai-code-search` (Python first; expand per language demand).
- Directory-keyed Merkle-tree incremental indexing (upgrade from flat content-hash manifest).
- Optional Playwright JS rendering on `devai-web-fetch`.

### v1.1.0+ (gated on demand signal)

- Vendor-wrapper reverse-engineering: `devai-github`, `devai-postgres`, `devai-supabase`, `devai-railway`, `devai-vercel`, `devai-cloudflare`. These don't reduce data-flow surface (the vendor is the intended destination) but they replace Anthropic- / vendor-maintained code with DevAI-Hub-maintained code, improving audit and supply-chain posture.

See the [Reverse-Engineering Matrix backlog](mcp-reverse-engineering-matrix.md) for per-row v1.1.0+ scope.

---

## Acknowledgements

The reverse-engineering-first policy and the matrix structure were forged through a multi-turn back-and-forth that started as a v0.9.8 patch addition and grew into the v1.0.0 retrofit. The discipline of stripping external-source attribution while keeping the technical patterns - documented in the policy's Reverse-Engineering Attribution Rule - is the lesson the release crystallizes.

---

## References

- **Plan**: [docs/archives/v1/v1.0/plans/security-hardening-v100.md](plans/security-hardening-v100.md)
- **Matrix**: [docs/policy/mcp-reverse-engineering-matrix.md](mcp-reverse-engineering-matrix.md)
- **Pen test**: [docs/security/penetration-test-2026-04-27.md](../security/penetration-test-2026-04-27.md)
- **Policy**: [AGENTS.md - MCP Registry Policy](../../AGENTS.md#mcp-registry-policy)
- **CHANGELOG**: [CHANGELOG.md - [1.0.0]](../../CHANGELOG.md)
- **Abandoned predecessor plan**: [docs/v0.9.7/plans/adoption-claude-context.md](../v0.9.7/plans/adoption-claude-context.md) (superseded; kept for historical record)
