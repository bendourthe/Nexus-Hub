# Comparison: Nexus-Hub vs Ruflo

**Source**: [`ruvnet/ruflo`](https://github.com/ruvnet/ruflo) ("the leading agent meta-harness for Claude")
**Source type**: Git repository (full 11-dimension comparison)
**Comparison date**: 2026-06-26
**Nexus-Hub baseline**: v3.9.0 (257 skills, 16 commands, 23 hooks, 23 agents)
**Analysis target**: v3.10.0 adoption cycle
**Vendor claims**: 61.6k stars, TypeScript/JS core, MIT license. Performance numbers cited below (for example "1.3x to 1953x advantages", "89% routing accuracy") are the project's own published claims and are treated as unverified marketing in this report, not as measured facts.

---

## Executive Summary

Ruflo and Nexus-Hub are different categories of artifact, and that framing governs every conclusion below.

- **Ruflo is a runtime meta-harness.** It installs as an MCP server plus background daemons, wraps Claude Code with an always-on execution layer, and reaches outward to Anthropic, OpenAI, Gemini, Cohere, OpenRouter, Supabase, MongoDB, Ollama, and (optionally) a WireGuard mesh across machines. Its value is operational infrastructure: a persistent vector database, self-learning routing, cross-machine federation, and hosted web UIs (flo.ruv.io, goal.ruv.io).
- **Nexus-Hub is a local-first template catalog.** It ships skills, commands, hooks, agents, and rules through an installer into a user's AI assistants, with a deliberate "reverse-engineer-first, zero-outbound-by-default" MCP Registry Policy (`AGENTS.md`). It has no runtime, no daemon, and no required external service.

Because of that mismatch, the bulk of ruflo's distinctive surface (federation, GPU-accelerated vector DB, multi-provider LLM routing-as-a-service, MCP-server-as-daemon, the background-worker daemon model, the WASM agent sandbox runtime, and the two hosted web UIs) is categorically **not adoptable** into the catalog. Those land in the NOT-recommended list under the MCP Registry Policy hard-no clauses (generation-as-service, embeddings-as-service, scraping-as-service, search-as-service), not because they lack merit but because they are runtime infrastructure Nexus-Hub intentionally refuses.

What **is** adoptable is a short list of patterns and doctrine that reverse-engineer cleanly into local catalog content. The two highest-value ones:

1. **A supply-chain `verify` command.** Ruflo's `ruflo verify` proves installed bytes match a signed witness. Nexus-Hub already computes per-file SHA-256 at install time (`scripts/lib/integrations/manifest.py`), but only for idempotency and uninstall pruning, never to prove a user's disk matches the published catalog. A local `nexus-hub verify` that diffs disk against a release-published manifest closes a real supply-chain gap for an installer-distributed project, with zero outbound calls and no paid code-signing.
2. **A typed PII / egress-redaction skill.** Ruflo's federation layer runs a 14-type PII pipeline with per-policy actions (BLOCK / REDACT / HASH / PASS). Nexus-Hub has only a partial analog (the v3.9.0 "Handoff Egress Hygiene" redaction globs in `cross-model-orchestrator`). Promoting that to a typed, reusable defensive skill is a security win and is fully skill-native.

Everything else is either already covered by an existing Nexus-Hub skill (and should be preserved, not "adopted") or is a small doctrine enrichment of a skill we already ship.

---

## Step 1: Source Type and Scope

Source URL contains `github.com`, so the source classifies as a **Git repository** and the full 11-dimension comparison applies. All 11 dimensions are in scope; no dimension was excluded.

---

## Step 2 and 3: 11-Dimension Comparison and Difference Classification

Legend for the Bucket column: `+` external-only (adoption candidate), `=` current-only (strength to preserve), `~` both with a different approach, `.` both, equivalent.

| # | Dimension | Ruflo | Nexus-Hub | Bucket |
|---|-----------|-------|-----------|--------|
| 1 | **Project Identity** | Runtime meta-harness; MIT; npm/TypeScript; positions as "infrastructure / nervous system" for Claude | Template catalog for AI assistants; installer-distributed; positions as "skill harness / upstream catalog" | `~` |
| 2 | **Technology Stack** | TypeScript/JS core, Rust/Svelte/Shell, pnpm, tsconfig, `/bin` build artifacts, RVF binary memory format | Python + Bash/PowerShell installers, Markdown catalog, JSON registries, Makefile validation; no compiled runtime | `~` |
| 3 | **AI Assistant Configuration** | `.claude/`, `.claude-plugin/`, `.agents/`, 35 native plugins, ~210 MCP tools, registers as an MCP server | 257 skills, 16 commands, 23 hooks, 23 agents distributed to 14+ platforms; reverse-engineer-first MCP policy; internal-only MCP servers | `~` |
| 4 | **Project Structure** | `/.harness`, `/plugins`, `/v3`, `/verification`, `/federation`, daemon + worker layout | `catalog/`, `data/`, `scripts/`, `templates/`, `docs/<version>/`, three-tier loading model | `~` |
| 5 | **Skills and Capabilities** | 100+ runtime agents, plugin-delivered capability, self-learning routing (SONA) | 257 documented skills with binary Verification + Common Rationalizations; `continuous-learning` mints local instincts | `~` |
| 6 | **Commands and Automation** | `ruflo init/verify/eject`, `federation *`, MCP start, interactive wizard | 16 slash commands (`/plan`, `/implement`, `/review`, `/compare`, etc.) plus aliases; no daemon | `~` |
| 7 | **CI/CD and Hooks** | 27 runtime/daemon hooks auto-triggered on events; 12 background workers | 23 tool-event hooks (`secret-scan`, `git-guardrails`, `workflow-phase-notice`, etc.); `make validate/lint/test` | `~` |
| 8 | **Documentation** | STATUS.md, USERGUIDE.md, 35+ ADRs, benchmark gists, verification.md | Per-version `docs/`, CHANGELOG, DEVLOG, markdown style governance, base-template parity guard, interactive guide | `~` |
| 9 | **Testing Strategy** | `/tests` suites, `ruflo-testgen` (gap detection + generation), Playwright via `ruflo-browser` | `test-*` skills (unit/integration/e2e/property/mutation/fuzz), `make test` pytest hook suite, 80% coverage doctrine | `~` |
| 10 | **Security Posture** | AIDefence (prompt-injection block, PII detect), CVE remediation, zero-trust federation (mTLS + ed25519), crypto byte-verify, compliance modes | Reverse-engineer-first MCP policy, `secret-scan`/`large-file-guard` hooks, security + security-operations skill families, framework mapping; no outbound by default | `~` |
| 11 | **Developer Experience** | `npx ruflo init`, interactive wizard, hosted web UIs, self-hostable Docker | One-line bootstrap installer, no-prompt global install, `nexus-hub upgrade`, multi-platform parity | `~` |

Almost every dimension is bucket `~` (both, different approach) precisely because the two projects solve adjacent problems from opposite architectural stances: ruflo as a running system, Nexus-Hub as distributed instructions. The interesting analysis is therefore not the dimension table; it is the per-capability classification below.

---

## Step 4: Adoption Candidates (value/effort)

Each ruflo capability is mapped to its closest Nexus-Hub equivalent, the gap stated, and a preliminary value/effort priority assigned. The Security and Reverse-Engineering gate (Step 5) re-sequences these before they enter the plan.

| ID | Ruflo capability | Nexus-Hub equivalent (evidence) | Gap | Value | Effort | P-tier (pre-gate) |
|----|------------------|----------------------------------|-----|-------|--------|-------------------|
| A1 | `ruflo verify`: prove installed bytes match a signed witness | SHA-256 recorded for idempotency only (`scripts/lib/integrations/manifest.py:17-127`); no provenance check | Real: no post-install tamper/provenance verification | High | Medium | P1 |
| A2 | Federation 14-type PII pipeline (BLOCK/REDACT/HASH/PASS) | Partial: egress-redaction globs in `cross-model-orchestrator/SKILL.md` (v3.9.0) | Partial: no typed taxonomy or per-policy action doctrine | High | Low | P0 |
| A3 | MetaHarness: grade an agent setup 1-100, snapshot tool config for security, detect regressions | `skill-stocktake`, `skill-security-scan`, `skill-eval-loop`, `scripts/harness_audit.py` | Partial: no single numeric setup grade or cross-snapshot regression diff | Med | Med | P2 |
| A4 | AIDefence: defensive prompt-injection blocking + input validation | Offensive coverage in `ai-attack-patterns`, `advanced-attack-patterns`; defensive view scattered | Partial: no consolidated *defensive* prompt-injection skill | Med | Low | P1 |
| A5 | Arena: competitive tournaments with hill-climbing / co-evolution across rounds | `competitive-generation/SKILL.md` (parallel agents, score, pick best) | Partial: single-round only; no iterative hill-climbing doctrine | Med | Low | P2 |
| A6 | SPARC: named 5-phase guided development with quality gates | `plan` + `implement` + `spec` + `quality-gate-definitions` + `research-plan-implement` | Equivalent function, different naming; mostly covered | Low | Low | P3 |
| A7 | GOAP A* goal planner: plain-English goal to executable plan | `plan`, `implementation-plan`, `idea-refine`, `product-strategy` | Equivalent function; A* state-space search is runtime, not catalog | Low | High | Skip |
| A8 | SONA self-learning / ReasoningBank (trajectory patterns, adaptive routing) | `continuous-learning/SKILL.md` (mint local YAML instincts, evolve into skills) | Mostly covered; adaptive routing is runtime | Low | High | Skip |
| A9 | Cost tracker with budgets / token tracking | `ai-billing-safeguards` (hard caps), `/usage`, `prompt-token-optimization` | Covered | Low | n/a | Skip |
| A10 | Background workers (12 auto checks: audit, optimize, testgaps, docs, deps) | 23 tool-event hooks + `workflow-phase-notice.sh` | Different model (daemon vs tool-event); check *catalog* may inspire new hooks | Low | Med | P3 |
| A11 | AgentDB / RuVector / HNSW GPU vector DB + Graph RAG | `rag-implementation`, `code-semantic-search` (local embeddings/BM25/AST) | Doctrine covered; the GPU runtime DB is non-adoptable | n/a | n/a | Drop |
| A12 | Multi-provider LLM routing-as-a-service (Claude/GPT/Gemini/Cohere/Ollama) | `multi-provider-ai`, `model-routing` skills | Covered as skills; runtime router is non-adoptable | n/a | n/a | Drop |
| A13 | Cross-machine federation (mTLS + ed25519, behavioral trust, WireGuard mesh) | None (out of scope for a catalog) | Non-adoptable runtime infrastructure | n/a | n/a | Drop |
| A14 | Hosted web UIs (flo.ruv.io chat, goal.ruv.io planner) | None | Non-adoptable hosted services | n/a | n/a | Drop |
| A15 | WASM agent sandbox (rvagent) runtime | `agent-access-policy` (default-deny host exec, sandbox tier, v3.9.0) | Sandbox *doctrine* covered; WASM runtime is non-adoptable | n/a | n/a | Drop |
| A16 | ADR management, DDD scaffolding, observability plugins | `architecture-decision-record`, `ddd-strategic-design`, `observability-setup` | Covered as skills | . | . | None |

---

## Step 5: Security and Reverse-Engineering Assessment (MANDATORY)

This gate runs every candidate through the `AGENTS.md` MCP Registry Policy decision tree before sequencing. It is the deciding analysis: it overrides the raw P-tiers above.

### 5.1 Threat model comparison

| Factor | Ruflo (runtime harness) | Nexus-Hub (catalog) |
|--------|-------------------------|---------------------|
| New runtime dependencies | MCP server, background daemons, vector DB, optional MongoDB/Postgres/Supabase/Ollama/WireGuard | None at rest; installer is run-once Python/Bash, no daemon |
| Outbound-call destinations | Anthropic, OpenAI, Gemini, Cohere, OpenRouter, Supabase, federation peers, hosted UIs | None by default; internal MCP servers make zero outbound calls |
| Credentials / API keys required | Multiple provider keys, federation identity keys, optional DB creds | None; the catalog ships no credential and requires none to install |
| Source / prompts / query text leaves the machine | Yes: to providers, to federation peers, to hosted UIs | No: local-first by construction |
| New commercial relationship required | Yes (cloud providers, Supabase, OpenRouter) | No |

The threat-model delta is the entire story. Adopting ruflo's *runtime* would invert Nexus-Hub's foundational posture (zero-outbound, no credential, no daemon). The policy exists precisely to prevent that inversion from happening one plausible plugin at a time.

### 5.2 Per-item risk scorecard

| ID | Candidate | Risk tier | Why |
|----|-----------|-----------|-----|
| A1 | `verify` command | None | Pure local SHA-256 diff; no outbound, no key, no signing service |
| A2 | PII/egress redaction skill | None | Pure instruction text; reduces egress risk, adds none |
| A3 | Agent-setup grading doctrine | None | Local read-only analysis; extends existing `harness_audit.py` |
| A4 | Defensive prompt-injection skill | None | Instruction text only |
| A5 | Hill-climbing tournament doctrine | None | Instruction text; uses only the harness's own subagents |
| A6 | SPARC naming | None | Doctrine text |
| A10 | New hook ideas from worker catalog | Low | Each new hook is local; must stay advisory and event-driven, not a daemon |
| A11-A15 | Vector DB, multi-provider router, federation, web UIs, WASM sandbox | High | Each introduces outbound calls, credentials, a daemon, or a hosted dependency |

### 5.3 Reverse-engineering viability

| ID | Candidate | RE classification | Note |
|----|-----------|-------------------|------|
| A2 | PII/egress redaction taxonomy | `skill-native` | Achievable as a defensive skill; promote the v3.9.0 redaction-glob partial to a typed taxonomy |
| A4 | Defensive prompt-injection | `skill-native` | Consolidate scattered defensive guidance into one skill |
| A5 | Hill-climbing / co-evolution | `skill-native` | Enrich `competitive-generation` with an iterative-rounds section |
| A6 | SPARC quality-gate naming | `skill-native` | Optional doctrine note in existing planning skills; mostly redundant |
| A3 | Agent-setup grade + regression diff | `re-partial` | Extend `harness_audit.py` and `skill-stocktake`; numeric grade is local, cross-snapshot diff is local |
| A1 | `nexus-hub verify` | `re-full` | A local verify command + a release-published manifest; all hashing is local, no paid signing (consistent with the v3.7.0 "no paid code-signing" decision) |
| A10 | Worker checks as hooks | `re-partial` | Adopt the *check ideas* as advisory tool-event hooks; the daemon scheduler is dropped |
| A11 | GPU vector DB | `drop-outright` | Embeddings-as-service / heavy runtime; doctrine already covered by `rag-implementation` |
| A12 | Multi-provider router runtime | `drop-outright` | Covered as skills; the running router is non-adoptable |
| A13 | Federation | `drop-outright` | Cross-machine outbound runtime; out of scope for a catalog |
| A14 | Hosted web UIs | `drop-outright` | Hosted generation/search-as-service |
| A15 | WASM sandbox runtime | `drop-outright` | Sandbox doctrine covered by `agent-access-policy`; the runtime is non-adoptable |

### 5.4 Recommendation ordering (this IS the adoption plan)

Sequenced per the policy: skill-native first, then RE builds, then vendor-intrinsic, then drops to the NOT-recommended list. P-tier operates *within* each bucket.

1. **`skill-native` (zero-code wins first)**
   - A2: typed PII / egress-redaction defensive skill (P0)
   - A4: defensive prompt-injection skill (P1)
   - A5: hill-climbing / co-evolution enrichment of `competitive-generation` (P2)
   - A6: optional SPARC quality-gate naming note (P3, low marginal value)
2. **`re-full` / `re-partial` (build internal equivalents)**
   - A1: `nexus-hub verify` command + release-published SHA-256 manifest (P1, highest-value RE build)
   - A3: agent-setup grade + regression diff in `harness_audit.py` / `skill-stocktake` (P2)
   - A10: adopt selected worker *checks* as advisory tool-event hooks (P3)
3. **`vendor-intrinsic`**
   - None. Nexus-Hub has no intrinsic third-party data destination to justify a vendor wrapper here.
4. **`drop-outright` (moved to NOT-recommended, Step 7)**
   - A11 vector DB, A12 multi-provider router runtime, A13 federation, A14 hosted web UIs, A15 WASM sandbox runtime, plus the MCP-server-as-daemon and background-worker-daemon models themselves.

---

## Step 6: Sequenced Adoption Plan

Dependency-ordered, RE-bucket-first. When chaining into `/plan from-comparison`, pass `reverse-engineer-first=true`.

1. **A2: PII / egress-redaction defensive skill** (P0, skill-native, no dependencies). Promote the v3.9.0 `cross-model-orchestrator` redaction-glob partial into a standalone, reusable typed taxonomy (a 14-style category list with BLOCK / REDACT / HASH / PASS actions and a default policy). Cross-link from `cross-model-orchestrator`, `agent-access-policy`, and `context-pack-builder`.
2. **A4: defensive prompt-injection skill** (P1, skill-native, independent of A2). Consolidate the defensive counterpart to the existing offensive `ai-attack-patterns`.
3. **A1: `nexus-hub verify` command + published manifest** (P1, re-full, independent). Highest-value supply-chain build. Reuses the existing `manifest.py` SHA-256 machinery; adds a release step that publishes the manifest and a `verify` subcommand that diffs disk against it. Installer-aware: requires copy-step edits in both `installer.sh` and `installer.ps1`.
4. **A5: hill-climbing enrichment of `competitive-generation`** (P2, skill-native). Add an iterative-rounds section.
5. **A3: agent-setup grade + regression diff** (P2, re-partial, can build on A1's manifest plumbing). Extend `harness_audit.py` and `skill-stocktake`.
6. **A10: selected worker checks as advisory hooks** (P3, re-partial). One hook per adopted check, event-driven and advisory only.
7. **A6: SPARC quality-gate naming note** (P3, skill-native, optional). Lowest marginal value; include only if a planning-skill edit is already open.

Items A2, A4, and A1 are independent and can proceed in parallel. A3 benefits from A1 landing first (shared manifest plumbing).

---

## Step 7: Risks, Conflicts, and NOT-Recommended

### Conflicts with existing conventions

- **A1 (`verify`)** touches the installer scripts, which `AGENTS.md` flags as "ask first". It must record SHA-256 of the actual distributed tree and avoid any paid signing service (the v3.7.0 install-UX decision explicitly ruled out paid code-signing). Risk is medium because it edits installer code paths; mitigate by adding new files plus a self-contained subcommand rather than rewriting copy logic.
- **A2 / A4 (new skills)** require the three-file registry update (`data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`) and `make validate`. Low risk (additive).
- **A3 (`harness_audit.py` extension)** edits an existing script; the numeric-grade output must not become a gate that blocks installs. Keep advisory.
- **A10 (new hooks)** must register in `catalog/hooks/settings.json` and stay advisory (exit 0), matching the `workflow-phase-notice.sh` precedent. Do not import a daemon scheduler.

### NOT recommended for adoption (policy grounds cited by name)

- **Ruflo runtime harness as a whole, MCP-server-as-daemon, and the background-worker daemon model.** MCP Registry Policy: this is an always-on, multi-outbound runtime; adopting it inverts the zero-outbound-by-default posture. Dropped.
- **A11 GPU vector DB (AgentDB/RuVector/HNSW).** MCP Registry Policy hard-no: embeddings-as-service and heavy runtime. The retrieval *doctrine* is already covered by `rag-implementation` and `code-semantic-search`.
- **A12 multi-provider LLM router runtime.** MCP Registry Policy: generation-as-service via a running router. Covered as skills (`multi-provider-ai`, `model-routing`); the runtime is dropped.
- **A13 cross-machine federation (mTLS/ed25519/WireGuard).** Out of scope for a template catalog; introduces cross-machine outbound and credential sprawl. Dropped.
- **A14 hosted web UIs (flo.ruv.io, goal.ruv.io).** MCP Registry Policy hard-no: hosted generation/search-as-service. Dropped.
- **A15 WASM agent sandbox runtime.** Sandbox *doctrine* is already covered by `agent-access-policy`; the runtime engine is non-adoptable. Dropped.

### Nexus-Hub strengths to preserve (current-only, `=`)

- The reverse-engineer-first, zero-outbound MCP Registry Policy itself (the governance ruflo has no equivalent of).
- Cross-platform installer reaching 14+ AI assistants from one catalog.
- Three-tier progressive-disclosure loading model for skills (Tier 1 always-loaded, Tier 2 on trigger, Tier 3 on demand).
- Binary Verification + Common Rationalizations sections in every skill.
- `project-constitution` governance, markdown style governance, and base-template parity enforcement.

---

## Verification Checklist

- [x] Source type correctly identified (Git repository) and full 11-dimension strategy applied
- [x] Every comparison dimension evaluated for both projects
- [x] Every gap claim cites a specific Nexus-Hub file path or an existing skill
- [x] Adoption items have concrete target locations
- [x] Priority assignments follow the value/effort matrix
- [x] Conflicts with existing conventions flagged (installer "ask first", registry updates, advisory-only hooks)
- [x] Items NOT recommended include reasoning with the policy clause cited by name
- [x] Step 5 complete: threat-model table, per-item risk scorecard, per-item RE classification all present
- [x] Step 5.4 ordering used to sequence the plan (skill-native, then RE builds, then vendor-intrinsic, then drops)
- [x] MCP Registry Policy cited by name for every dropped item involving outbound calls, keys, third-party processors, or new runtime dependencies

---

## Next Step

The prioritized adoption plan above is ready to feed `/plan from-comparison` with `reverse-engineer-first=true`. The natural v3.10.0 cut would be the three independent, high-value, low-risk items: **A2 (PII/egress skill)**, **A4 (defensive prompt-injection skill)**, and **A1 (`nexus-hub verify`)**, with A3/A5/A10 as follow-on.
