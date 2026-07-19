# Security and Safety

Nexus-Hub is built on a **reverse-engineering-first** principle: the catalog ships zero third-party data processors, zero outbound calls from skills / commands / hooks, and zero telemetry. This document describes what Nexus-Hub does and does not do at the data-flow layer, who can safely use it, and what stays out of its threat model.

For the formal MCP Registry Policy that drives every governance decision, see [`AGENTS.md`](AGENTS.md). For the authoritative classification of every MCP server ever shipped or considered, see [`docs/policy/mcp-reverse-engineering-matrix.md`](docs/policy/mcp-reverse-engineering-matrix.md).

## 1. Industry Compatibility Matrix

| Industry / Use Case | Safe to use Nexus-Hub? | Notes |
|---|---|---|
| Open-source / hobby / personal projects | Full green | No restrictions. Everything ships local-only. |
| Internal commercial software (SaaS, web apps, internal tooling, agencies) | Green | Same trust profile as your existing development environment. Your usual code-handling and credential-handling rules apply unchanged. |
| Regulated industries -- healthcare / life sciences / medical devices | Green WITH caveats | Nexus-Hub itself adds zero outbound third-party calls. **Caveat**: your chosen LLM provider is where prompts go. Use a regulated-cloud LLM (Anthropic via AWS Bedrock or GCP Vertex AI, Azure OpenAI, or a self-hosted model) consistent with your data-protection obligations (HIPAA, GDPR, MDR, FDA). Nexus-Hub does not change that obligation; it does not introduce new ones either. |
| Regulated industries -- finance / banking / insurance | Green WITH caveats | Same as above. SOC 2 / PCI-DSS / regional banking-data rules apply to your LLM provider, not to Nexus-Hub itself. |
| Regulated industries -- government / public sector | Green WITH caveats | Same as above. FedRAMP / IL-rated cloud LLM hosting is your responsibility; Nexus-Hub does not constrain or expand that scope. |
| Regulated industries -- automotive / industrial / safety-critical software | Green WITH caveats | Nexus-Hub does not generate certified output; it generates code and documentation that your existing certification process must still validate (ISO 26262, IEC 61508, IEC 62304, etc.). Use the same way you would use any other code-assistance tool inside that process. |
| Defense, classified, or air-gapped environments | Outside Nexus-Hub's threat model | Not because Nexus-Hub leaks, but because: (a) any LLM use requires its own classification review; (b) Nexus-Hub installs from a public GitHub repository, so requires its own supply-chain review against your environment's vetting rules; (c) air-gap-compatible LLM hosting is outside Nexus-Hub's scope. Do your own assessment. |

## 2. What Nexus-Hub Itself Does NOT Do

These are properties of the catalog as shipped. Every change to the catalog is gated against them:

- **No telemetry.** No analytics. No usage reporting. No phone-home in any skill, command, hook, agent, rule, or installer script.
- **No outbound calls from catalog content.** Skills are prompt instructions; commands are prompt instructions; hooks are local scripts. None of them initiate network requests to third-party services.
- **No third-party data processors.** The MCP Registry Policy ([`AGENTS.md`](AGENTS.md) section "MCP Registry Policy") categorically rejects four classes of third-party service: search-as-service, embeddings-as-service, scraping-as-service, generation-as-service.
- **No API keys collected, stored, or required by Nexus-Hub.** The internal MCP servers (`nexus-skill-server`, `nexus-code-search`, `nexus-web-fetch`) all run locally with zero credentials.
- **No model downloads.** No embeddings models, no scoring models, no anything. The internal MCPs use deterministic local algorithms (inverted index + rapidfuzz for code search; readability-lxml for web extraction).
- **No source code, no prompts, no query text leaves the local machine through the Nexus-Hub layer.** The only network surface from any internal MCP is `nexus-web-fetch`'s direct HTTPS call to a user-specified URL (single-URL scope, SSRF-guarded by default).
- **The MCP Registry Policy is enforced.** Every `mcp-servers.json` entry must answer five audit questions (who runs the process, outbound destinations, API keys required, data transmitted, vendor relationship) in its `_comment` field, and each entry must have a corresponding row in [`docs/policy/mcp-reverse-engineering-matrix.md`](docs/policy/mcp-reverse-engineering-matrix.md).

## 3. What Is OUT of Nexus-Hub's Control (Caveats)

These are properties of your environment, not of Nexus-Hub. They apply equally regardless of which AI tooling you use; Nexus-Hub neither weakens nor strengthens them.

- **Your chosen LLM provider IS where prompts go.** When the agent processes your code, the agent's underlying model receives that code. Nexus-Hub does not control whether you use Anthropic API, AWS Bedrock, GCP Vertex AI, Azure OpenAI, OpenAI, a self-hosted model, or anything else. Your provider's terms of service, data-retention policies, regional hosting, and compliance posture are your responsibility. For regulated-industry use, prefer a regulated-cloud hosting option (Bedrock, Vertex AI, Azure) or a self-hosted model.
- **MCP servers configured outside the Nexus-Hub registry can leak.** Nexus-Hub governs the entries it ships in `catalog/mcp-configs/mcp-servers.json`. Any third-party MCP server you add to your own `~/.claude/settings.json` or per-project `.claude/settings.json` outside that registry is not covered by this policy. You are responsible for vetting any MCP server you add.
- **User-initiated outbound calls go where you configure them.** When the agent runs `gh issue create`, `git push`, `curl`, `npm install`, or similar at your direction, the data goes to the destination you configured. Nexus-Hub does not route or proxy these.
- **Supply-chain trust.** Nexus-Hub installs from a public GitHub repository (`github.com/bendourthe/Nexus-Hub`). Verify the repo URL, tag signing, and installer-script integrity per your environment's supply-chain rules before installing in a high-trust setting.
- **Hooks and rules you write yourself.** Nexus-Hub provides 13 built-in hooks (`catalog/hooks/`) and 4 language rule sets (`catalog/rules/`), but the framework supports user-authored hooks and rules. Anything you author yourself is your responsibility to review.

## 4. Threat Model Summary

Nexus-Hub's threat model is "the catalog itself does not introduce new third-party data processors or new outbound network surfaces." This is a property of *what gets installed*, not of *how you use the installed tooling*. Out of scope explicitly:

- The trust posture of your LLM provider (your decision).
- The trust posture of any MCP server you add outside the Nexus-Hub registry (your decision).
- The trust posture of your own scripts, hooks, and rules (your code, your review).
- The trust posture of `gh`, `git`, `npm`, or any other developer tool the agent operates (your dev environment).
- Compliance certifications that require formal validation of generated artifacts (ISO 26262, IEC 62304, FDA software-as-a-medical-device, etc.). Nexus-Hub generates code and documentation; certification still requires your existing process.

## 5. Specific Surfaces and Considerations

### Hook scripts

The hooks in `catalog/hooks/` run inside Claude Code sessions with the permissions of the current user. Before installing hooks, review each script to confirm it meets your organization's security requirements. Notable hooks:

- `git-guardrails.sh` -- PreToolUse, blocks 12 dangerous git command patterns (`git push --force`, `git reset --hard`, `git clean -f`, etc.).
- `secret-scan.sh` -- PreToolUse on Write/Edit, scans file content for common secret patterns before disk write. Local-only; does not transmit data.
- `large-file-guard.sh` -- PreToolUse, blocks accidental large-file commits.
- `format-bash-description.py` -- PreToolUse, formats Bash command descriptions consistently.

### OAuth token access (usage-monitor extensions)

The VS Code extension `extensions/claude-usage-monitor/` and the `usage-display.sh` hook read your Claude Code OAuth token from `~/.claude/.credentials.json` to query usage data. This token is sent only to `api.anthropic.com`; never to any other destination.

The separate VS Code extension `extensions/codex-usage-monitor/` reads your local Codex-app (ChatGPT) OAuth token from `~/.codex/auth.json` (or a configured path) and sends it only to `chatgpt.com/backend-api/wham/usage` to query your own account usage; never to any other destination. Each extension reads only its own provider's token and calls only that provider's account endpoint.

### Internal MCP servers

The three internal MCPs (under `extensions/`) all default to local-only operation:

- `nexus-skill-server` -- serves skills from the local catalog. Zero outbound.
- `nexus-code-search` -- inverted-index keyword search over the local repo. Zero outbound. JSON-persisted indexes (no pickle, so a malicious index file cannot execute code at load time). Symlink-safe walker prevents indexing files outside the repo root.
- `nexus-web-fetch` -- direct HTTPS fetch of a user-specified URL. SSRF-guarded by default (RFC 1918, loopback, link-local, `file://` blocked). Per-hop validation on every redirect target. DNS pinning to prevent rebinding.

### Supported versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |
| 0.9.x   | Best-effort (no new patches; will fix critical issues on request) |
| < 0.9   | No        |

## 6. Reporting Vulnerabilities

If you find a security issue in Nexus-Hub itself (a skill that emits an outbound call, a hook that leaks data, an installer script with a privilege bug, an MCP server that behaves outside its documented surface, etc.), report it directly:

- **Email**: [benjamin.dourthe@gmail.com](mailto:benjamin.dourthe@gmail.com)
- **GitHub**: open a private security advisory at [github.com/bendourthe/Nexus-Hub/security](https://github.com/bendourthe/Nexus-Hub/security)

Please include: a description of the issue, the file path or registry entry involved, a reproducer if possible, and the version (`CHANGELOG.md` heading) you observed it on.

There is currently no formal SLA for Nexus-Hub responses. The project is maintained by a single author. Reports are acknowledged on a best-effort basis and prioritized by severity (critical issues targeted for fix within 7 days; lower severity on a slower cadence).

## 7. Pre-release Security Reviews

Every major release runs through a `/run-deep-review` orchestrator that includes a `/run-security-audit` and a `/run-penetration-test --depth=deep` pass. The latest report is at [`docs/security/penetration-test-2026-04-27.md`](docs/security/penetration-test-2026-04-27.md). The v1.0.0 review found 3 HIGH and 1 MEDIUM-severity findings; all were fixed with regression tests before tag.
