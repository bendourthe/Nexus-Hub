"""MCP-configuration analyzer.

Covers class 15 (MCP least privilege: wildcard / over-broad scopes) and class
16 (MCP tool poisoning: remote-code-fetch commands, hardcoded credentials,
hidden override instructions in descriptions). The analyzer parses JSON files
that declare an ``mcpServers`` object (a ``.claude`` settings snippet or the
Nexus-Hub MCP registry) and reasons about each server's declared command,
args, env, and comment.

Producer-catalog discipline: the only HIGH findings are a genuinely hardcoded
credential (a non-placeholder secret value) and a remote-code-fetch command
(``curl ... | bash``), neither of which appears in the curated registry (which
uses ``${ENV}`` placeholders and registry-installed commands). Moving version
refs and honest-but-broad declarations stay LOW/MEDIUM.
"""

from __future__ import annotations

import json
import re

from ..types import Finding, Severity
from .base import FileUnit, make_finding

# A value that is an environment-variable placeholder, not a literal secret.
_PLACEHOLDER_RE = re.compile(r"^\$\{?[A-Za-z_][A-Za-z0-9_]*\}?$")
# Keys that name a credential.
_SECRET_KEY_RE = re.compile(r"(token|secret|password|passwd|api[_-]?key|access[_-]?key|credential|pat)\b", re.IGNORECASE)
# High-confidence literal secret formats (reused conceptually from the catalog
# secret scanner) -- a value matching one of these is a credential regardless
# of its key name.
_SECRET_VALUE_RE = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9\-]{20,}|ghp_[A-Za-z0-9]{36}|AKIA[0-9A-Z]{16})"
)
# Remote-code-fetch / shell-out patterns in a command or arg.
_REMOTE_EXEC_RE = re.compile(
    r"(curl\s|wget\s|\|\s*(?:bash|sh|zsh|python)\b|(?:bash|sh|zsh)\s+-c\b)", re.IGNORECASE
)
# Moving version refs in an npx/uvx package coordinate.
_MOVING_REF_RE = re.compile(r"@(?:latest|main|master|next|canary|HEAD)\b")
# Over-broad / dangerous CLI flags.
_DANGEROUS_FLAG_RE = re.compile(r"^(?:\*|--allow-all|--yolo|--dangerously[-\w]*|--no-sandbox)$", re.IGNORECASE)
# Filesystem roots that grant over-broad access.
_FS_ROOT_RE = re.compile(r"^(?:/|~|\$\{?HOME\}?|[A-Za-z]:\\?|/root|/home)$")
# Override / hidden-instruction phrases embedded in a description or comment.
_HIDDEN_INSTRUCTION_RE = re.compile(
    r"\b(?:ignore\s+(?:previous|prior|all)\s+instructions?|do\s+not\s+tell\s+the\s+user|reveal\s+(?:your|the)\s+system\s+prompt|disregard\s+(?:the\s+)?(?:above|previous))\b",
    re.IGNORECASE,
)


def _line_of(text: str, needle: str) -> int:
    idx = text.find(needle)
    if idx == -1:
        return 0
    return text.count("\n", 0, idx) + 1


class MCPConfigAnalyzer:
    """Analyzes MCP server declarations in a JSON config file."""

    name = "mcp-config"

    def analyze(self, unit: FileUnit) -> list[Finding]:
        if unit.suffix != ".json":
            return []
        try:
            data = json.loads(unit.text)
        except (json.JSONDecodeError, ValueError):
            return []
        if not isinstance(data, dict) or "mcpServers" not in data:
            return []
        servers = data.get("mcpServers")
        if not isinstance(servers, dict):
            return []

        findings: list[Finding] = []
        for server_name, cfg in servers.items():
            if not isinstance(cfg, dict):
                continue
            line = _line_of(unit.text, f'"{server_name}"')
            findings.extend(self._check_server(unit, server_name, cfg, line))
        return findings

    def _check_server(self, unit: FileUnit, name: str, cfg: dict, line: int) -> list[Finding]:
        out: list[Finding] = []
        command = cfg.get("command", "")
        args = cfg.get("args", []) if isinstance(cfg.get("args"), list) else []
        env = cfg.get("env", {}) if isinstance(cfg.get("env"), dict) else {}
        comment = " ".join(
            str(v) for k, v in cfg.items() if k in ("_comment", "description")
        )
        arg_strs = [str(a) for a in args]
        joined = " ".join([str(command), *arg_strs])

        # Class 16: remote-code-fetch / shell-out command.
        if _REMOTE_EXEC_RE.search(joined):
            out.append(make_finding(
                detection_class=16, severity=Severity.HIGH,
                title=f"MCP server '{name}' fetches/executes remote code",
                message="The server's command pipes a download into a shell or runs an inline shell command -- it can execute attacker-controlled code at spawn time.",
                unit=unit, line=line, snippet=joined, analyzer=self.name,
            ))

        # Class 16 / 3: hardcoded credential in env.
        for key, value in env.items():
            if not isinstance(value, str) or not value:
                continue
            if _PLACEHOLDER_RE.match(value):
                continue
            if _SECRET_VALUE_RE.search(value) or (_SECRET_KEY_RE.search(str(key)) and len(value) >= 8):
                out.append(make_finding(
                    detection_class=16, severity=Severity.HIGH,
                    title=f"MCP server '{name}' has a hardcoded credential",
                    message=f"env['{key}'] holds a literal secret instead of a ${{PLACEHOLDER}} -- a leaked credential shipped in config.",
                    unit=unit, line=_line_of(unit.text, str(key)) or line,
                    snippet=f"{key}=<redacted>", analyzer=self.name,
                ))

        # Class 15: over-broad / dangerous flags and filesystem roots.
        for a in arg_strs:
            if _DANGEROUS_FLAG_RE.match(a.strip()):
                out.append(make_finding(
                    detection_class=15, severity=Severity.MEDIUM,
                    title=f"MCP server '{name}' uses an over-broad flag",
                    message=f"arg '{a}' grants unrestricted capability -- declare the minimum scope the server needs.",
                    unit=unit, line=line, snippet=a, analyzer=self.name,
                ))
            elif _FS_ROOT_RE.match(a.strip()):
                out.append(make_finding(
                    detection_class=15, severity=Severity.MEDIUM,
                    title=f"MCP server '{name}' is granted a filesystem root",
                    message=f"arg '{a}' exposes a top-level directory; scope the server to the specific project path it needs.",
                    unit=unit, line=line, snippet=a, analyzer=self.name,
                ))

        # Class 16: moving version ref (supply-chain hygiene).
        for a in arg_strs:
            if _MOVING_REF_RE.search(a):
                out.append(make_finding(
                    detection_class=16, severity=Severity.LOW,
                    title=f"MCP server '{name}' pins a moving package ref",
                    message=f"'{a}' resolves a moving tag at spawn time; pin a version for a reproducible, auditable supply chain.",
                    unit=unit, line=line, snippet=a, analyzer=self.name,
                ))
                break

        # Class 16: hidden override instructions in the description/comment.
        if _HIDDEN_INSTRUCTION_RE.search(comment):
            out.append(make_finding(
                detection_class=16, severity=Severity.MEDIUM,
                title=f"MCP server '{name}' description contains override text",
                message="The server description/comment embeds instruction-override language that could reach the agent as a hidden directive (tool poisoning).",
                unit=unit, line=line, snippet=comment[:120], analyzer=self.name,
            ))

        return out
