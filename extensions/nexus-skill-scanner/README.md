# nexus-skill-scanner

Local-only static skill-security scanner. The deterministic first stage of a two-stage skill-security scan: it runs regex, Python-AST, taint-tracking, and MCP-declaration checks over a skill's `SKILL.md`, its bundled scripts, and any MCP config it ships, and emits machine findings across 16 vulnerability classes with a severity-banded risk score.

The engine is deterministic and self-contained: standard library only, zero outbound calls by default, no bundled LLM client, and no API key. The intent adjudication of borderline findings is the `skill-security-scan` skill, run by the user's own agent.

## Why it exists

Nexus-Hub produces and distributes exactly the artifact this scans (`SKILL.md` files and MCP configs). The scanner lets Nexus-Hub gate its own catalog before distribution (CI dogfooding) and lets users scan any third-party skill before importing it. It unifies three previously fragmented validators (`validate_skills.py` secret scan, `scan_supply_chain_iocs.py`, `validate_workflow_security.py`) behind one tool.

## Detection classes

The scanner covers 16 classes (prompt injection, data exfiltration, privilege escalation, supply chain, excessive agency, output handling, system-prompt leakage, memory poisoning, tool misuse, rogue agent, trigger abuse, behavioral AST, taint tracking, YARA signatures, MCP least privilege, MCP tool poisoning). Class 14 (YARA) and the live OSV.dev dependency lookup are optional Phase 7 modules. Each finding is tagged with its primary MITRE ATT&CK / ATLAS / D3FEND / NIST CSF identifiers; the full taxonomy lives in `catalog/skills/security/skill-security-scan/references/detection-classes.md`.

## Producer-catalog discipline

A catalog that teaches security legitimately contains dangerous-looking constructs (`eval(`, "ignore previous instructions", `password = "..."`) inside fenced examples. The scanner is fence-aware: low-confidence text patterns inside Markdown fences are suppressed, and prose-delivered classes are capped at MEDIUM. The deterministic CI gate fails only on HIGH/CRITICAL findings, with the semantic-adjudication skill as the false-positive filter.

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
- `--osv` - (Phase 7) opt-in OSV.dev dependency lookup; reported as skipped until then.

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
