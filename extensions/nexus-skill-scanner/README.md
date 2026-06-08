# nexus-skill-scanner

Local-only static skill-security scanner. The deterministic first stage of a two-stage skill-security scan: it runs regex, Python-AST, taint-tracking, and MCP-declaration checks over a skill's `SKILL.md`, its bundled scripts, and any MCP config it ships, and emits machine findings across 16 vulnerability classes with a severity-banded risk score.

The engine is deterministic and self-contained: standard library only, zero outbound calls by default, no bundled LLM client, and no API key. The intent adjudication of borderline findings is the `skill-security-scan` skill, run by the user's own agent.

## Why it exists

Nexus-Hub produces and distributes exactly the artifact this scans (`SKILL.md` files and MCP configs). The scanner lets Nexus-Hub gate its own catalog before distribution (CI dogfooding) and lets users scan any third-party skill before importing it. It unifies three previously fragmented validators (`validate_skills.py` secret scan, `scan_supply_chain_iocs.py`, `validate_workflow_security.py`) behind one tool.

## Detection classes

The scanner covers 16 classes (prompt injection, data exfiltration, privilege escalation, supply chain, excessive agency, output handling, system-prompt leakage, memory poisoning, tool misuse, rogue agent, trigger abuse, behavioral AST, taint tracking, signature rules, MCP least privilege, MCP tool poisoning). Class 14 (signature rules, `--yara`) and the live portion of class 4 (OSV.dev dependency lookup, `--osv`) are optional, default-off modules: both are opt-in, both degrade gracefully when unavailable, and the default scan stays stdlib-only and offline. The signature module is a self-contained pure-Python rule engine (no native binding); the OSV lookup is offline-first against a bundled advisory DB. Each finding is tagged with its primary MITRE ATT&CK / ATLAS / D3FEND / NIST CSF identifiers; the full taxonomy lives in `catalog/skills/security/skill-security-scan/references/detection-classes.md`.

## Producer-catalog discipline

A catalog that teaches security legitimately contains dangerous-looking constructs (`eval(`, "ignore previous instructions", `password = "..."`) inside fenced examples. The scanner is fence-aware: low-confidence text patterns inside Markdown fences are suppressed, and prose-delivered classes are capped at MEDIUM. The deterministic CI gate fails only on HIGH/CRITICAL findings, with the semantic-adjudication skill as the false-positive filter.

### Security-category allowlist

The `security` skill category goes one step further than fence-aware text capping: its `SKILL.md` bodies carry authorized red-team methodology (example credentials / tokens, attack directives, and payloads shown inside fenced blocks to teach defenders what a system must withstand). The clearest case is a fenced example `Authorization: Bearer <token>`, which the secret analyzer flags HIGH **even inside a fence** (a genuinely leaked key must never be suppressed). To keep the CI gate from failing on authorized teaching content, a documented policy layer (`allowlist.py`) caps such findings at MEDIUM.

This is a policy cap, not a detection change: every analyzer still reports the real detection class and severity, the construct still surfaces (at MEDIUM) for the `skill-security-scan` adjudication skill, and the cap is applied at exactly one place. A finding is capped only when **all** of these hold:

1. **Trusted producer catalog.** The scan is rooted at a real Nexus-Hub checkout (`repo_root` resolved) AND the host file resolves to a path under `<repo_root>/catalog/skills/security/`. A third-party skill scanned via `/skills import` is not under the trusted repo's security tree, so it is never allowlisted -- its findings score at their real class.
2. **Prose / fenced context only.** The host file is a Markdown skill body (`.md` / `.markdown`). Bundled executable scripts (`.py`, `.sh`, `.ps1`, ...) are real code, not teaching prose, and are never capped -- a payload that actually runs is detected at full severity even inside a `security` skill.
3. **Not a never-relax class.** The cap never applies to data exfiltration (class 2), excessive agency (class 5), behavioral dynamic code execution (class 12), taint-to-sink code injection (class 13), or signature / live-malware (class 14). These keep their real severity even inside a trusted security-skill body.

The net effect: authorized methodology in a reviewed `security` skill body passes the gate at MEDIUM, while a malicious skill (a bundled exfil script, a code-execution payload, the same credential in any other category, or any third-party skill) still trips the HIGH/CRITICAL gate.

## Usage

```bash
# Scan a skill directory (terminal output)
python -m nexus_skill_scanner path/to/skill

# Scan and fail (exit 1) on any HIGH/CRITICAL finding
python -m nexus_skill_scanner path/to/skill --fail-on high

# Emit SARIF for GitHub code scanning
python -m nexus_skill_scanner path/to/skill --format sarif --output scan.sarif

# Dogfood the Nexus-Hub catalog (the CI gate)
python scripts/scan_skill_security.py catalog/skills catalog/mcp-configs --fail-on high
```

Options:

- `--format {terminal,json,markdown,sarif}` - output format (default: terminal).
- `--output PATH` - write the report to a file instead of stdout.
- `--fail-on {none,low,medium,high,critical}` - exit 1 if any finding meets or exceeds this severity.
- `--no-llm` - documented no-op: the engine is always deterministic; the semantic pass is the `skill-security-scan` skill.
- `--yara` - opt-in local signature-rule engine (class 14: malware / web shell / cryptominer / exploit). Pure-Python, no native binding, no network. Degrades to skipped if the bundled rules cannot be loaded.
- `--osv` - opt-in dependency-vulnerability lookup (class 4). Offline-first against a bundled advisory DB; the live OSV.dev query (single opt-in outbound call) sends only the `{ecosystem, package, version}` tuple and degrades to the offline DB on any network failure.

Exit codes: `0` clean / below threshold, `1` findings at or above `--fail-on`, `2` usage or IO error.

## Install

```bash
pip install -e "extensions/nexus-skill-scanner/[dev]"
```

The Nexus-Hub installer also copies the thin launcher `scripts/scan_skill_security.py` to `~/.nexus-hub/scripts/`, which locates the bundled package automatically.

## Tests

```bash
cd extensions/nexus-skill-scanner && python -m pytest -q
```

The suite includes a planted-malicious fixture (must score HIGH/CRITICAL), a known-clean fixture (must score LOW), per-analyzer unit tests, emitter tests, and behavior-preservation tests for the subsumed validators.
