"""Text-pattern analyzers (regex) for the prose-delivered detection classes.

Covers classes 1 (prompt injection), 2 (data-exfiltration directives, text
portion), 5 (excessive agency), 6 (output handling), 7 (system-prompt
leakage), 8 (memory poisoning), 9 (tool misuse), 10 (rogue agent), and 11
(trigger abuse). These classes are delivered through skill *text*, so the
analyzer runs over Markdown bodies and script comments/strings alike.

Producer-catalog discipline: every pattern here is capped at MEDIUM severity,
and Markdown matches inside fenced code blocks are suppressed entirely. A
catalog that teaches security legitimately contains these phrases in prose and
fenced examples, so the deterministic gate (which fails only on HIGH /
CRITICAL findings) must never be tripped by a text match. Genuine
text-delivered attacks surface as an elevated aggregate band and are resolved
by the ``skill-security-scan`` semantic-adjudication skill.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..fences import iter_lines_with_fence
from ..types import Finding, Severity
from .base import FileUnit, make_finding


@dataclass(frozen=True)
class TextPattern:
    detection_class: int
    severity: Severity
    title: str
    regex: re.Pattern[str]
    message: str


_I = re.IGNORECASE

# Each pattern is capped at MEDIUM so a producer catalog never trips the
# HIGH/CRITICAL gate on a prose match. Patterns are re-authored from public
# prompt-injection / LLM-security knowledge.
TEXT_PATTERNS: list[TextPattern] = [
    # ---- Class 1: Prompt Injection -------------------------------------
    TextPattern(
        1, Severity.MEDIUM, "Instruction-override directive",
        re.compile(r"\bignore\s+(?:all\s+|any\s+|the\s+)?(?:previous|prior|above|preceding|earlier)\s+instructions?\b", _I),
        "Text instructs the agent to ignore prior instructions -- an instruction-override aimed at the system prompt or the user's directives.",
    ),
    TextPattern(
        1, Severity.MEDIUM, "Instruction-override directive",
        re.compile(r"\bdisregard\s+(?:all\s+|the\s+)?(?:previous|prior|above|preceding)\s+(?:instructions?|context|messages?|directions?)\b", _I),
        "Text instructs the agent to disregard prior context -- a prompt-injection override.",
    ),
    TextPattern(
        1, Severity.MEDIUM, "Covert-action directive",
        re.compile(r"\b(?:do\s+not|don'?t|never)\s+(?:tell|inform|notify|alert|mention\s+(?:this\s+)?to)\s+the\s+user\b", _I),
        "Text instructs the agent to act without informing the user -- a covert-action directive characteristic of prompt injection.",
    ),
    TextPattern(
        1, Severity.MEDIUM, "Covert-action directive",
        re.compile(r"\bwithout\s+(?:telling|informing|notifying|alerting|the\s+knowledge\s+of)\s+the\s+user\b", _I),
        "Text instructs the agent to act without the user's knowledge -- a covert-action directive.",
    ),
    # ---- Class 7: System Prompt Leakage --------------------------------
    TextPattern(
        7, Severity.MEDIUM, "System-prompt exfiltration prompt",
        re.compile(r"\b(?:reveal|print|show|repeat|output|disclose|dump|leak)\s+(?:your|the)\s+(?:system\s+prompt|initial\s+instructions|hidden\s+instructions|system\s+message|original\s+instructions)\b", _I),
        "Text is engineered to elicit the agent's system prompt or hidden instructions.",
    ),
    TextPattern(
        7, Severity.MEDIUM, "System-prompt exfiltration prompt",
        re.compile(r"\bwhat\s+(?:is|are)\s+your\s+(?:exact\s+)?(?:system\s+prompt|initial\s+instructions|original\s+instructions|hidden\s+instructions)\b", _I),
        "Text asks the agent to disclose its system prompt.",
    ),
    # ---- Class 8: Memory Poisoning -------------------------------------
    TextPattern(
        8, Severity.LOW, "Persistent-memory directive",
        re.compile(r"\b(?:always|permanently|forever)\s+remember\s+(?:that|this|to)\b", _I),
        "Text instructs the agent to permanently remember a directive -- potential cross-session memory poisoning.",
    ),
    TextPattern(
        8, Severity.LOW, "Persistent-memory directive",
        re.compile(r"\b(?:store|save|write)\s+this\s+(?:in|to)\s+(?:your\s+)?memory\s+(?:and|so|then)\b", _I),
        "Text instructs the agent to persist content into memory it later trusts.",
    ),
    # ---- Class 2: Data Exfiltration (text directive portion) -----------
    TextPattern(
        2, Severity.LOW, "Exfiltration directive",
        re.compile(r"\b(?:send|post|upload|transmit|exfiltrate|leak)\s+(?:all\s+)?(?:the\s+)?(?:env(?:ironment)?\s+vars?|secrets?|credentials?|api[\s_-]?keys?|tokens?|\.env)\b", _I),
        "Text directs the agent to ship secrets/credentials off the machine -- a data-exfiltration directive (the executable form is detected by the AST analyzer).",
    ),
    # ---- Class 5: Excessive Agency -------------------------------------
    TextPattern(
        5, Severity.LOW, "Unrestricted-access claim",
        re.compile(r"\b(?:unrestricted|unlimited|full|root)\s+access\s+to\s+(?:all\s+)?(?:tools|the\s+system|the\s+file\s*system|everything|all\s+files)\b", _I),
        "Skill claims access beyond its stated purpose -- excessive agency / scope creep.",
    ),
    # ---- Class 6: Output Handling --------------------------------------
    TextPattern(
        6, Severity.MEDIUM, "Unsafe output sink",
        re.compile(r"\bdangerouslySetInnerHTML\b"),
        "Untrusted output rendered as HTML without sanitization (XSS sink).",
    ),
    TextPattern(
        6, Severity.MEDIUM, "Unsafe output sink",
        re.compile(r"\.innerHTML\s*\+?=\s*[^=]"),
        "Assignment to innerHTML routes output into a render sink without sanitization.",
    ),
    TextPattern(
        6, Severity.MEDIUM, "Unsafe output sink",
        re.compile(r"\bdocument\.write\s*\("),
        "document.write routes content into the DOM render sink.",
    ),
    # ---- Class 9: Tool Misuse (system-path write) ----------------------
    TextPattern(
        9, Severity.MEDIUM, "System-path write",
        re.compile(r"\b(?:open|write|copy|move|rm|del|chmod|chown)\b[^\n]{0,60}?(?:/etc/|/root/|~/\.ssh|\.ssh/|/var/spool/cron|System32|\\Windows\\)", _I),
        "A file/shell operation targets a sensitive system path -- a legitimate tool misdirected toward a harmful end.",
    ),
    # ---- Class 10: Rogue Agent -----------------------------------------
    TextPattern(
        10, Severity.MEDIUM, "Self-modification / persistence",
        re.compile(r"\b(?:modif|edit|rewrit|overwrit|append\s+to)\w*\b[^\n]{0,60}?(?:SKILL\.md|settings\.json|\.claude/|its\s+own\s+(?:description|trigger|definition))", _I),
        "Skill modifies its own definition or the agent's config -- rogue-agent self-modification.",
    ),
    TextPattern(
        10, Severity.MEDIUM, "Self-modification / persistence",
        re.compile(r"\b(?:add|install|register)\b[^\n]{0,40}?(?:crontab|cron\s+job|launchd|systemd\s+(?:unit|service)|registry\s+run\s+key|startup\s+(?:folder|item))", _I),
        "Skill establishes persistence (cron / startup / service) -- unauthorized persistence.",
    ),
    # ---- Class 11: Trigger Abuse ---------------------------------------
    TextPattern(
        11, Severity.LOW, "Over-broad trigger",
        re.compile(r"\buse\s+this\s+(?:skill\s+)?for\s+(?:everything|all\s+tasks|any\s+(?:task|request|prompt))\b", _I),
        "Trigger language baits the agent into running the skill on unrelated tasks -- trigger abuse (malicious inverse of a focused pushy description).",
    ),
    TextPattern(
        11, Severity.LOW, "Shadow / priority override",
        re.compile(r"\bignore\s+(?:all\s+)?other\s+(?:skills|commands|tools)\b", _I),
        "Trigger language tells the agent to ignore other skills -- shadowing / priority override.",
    ),
]


class TextPatternAnalyzer:
    """Runs the text-pattern catalog over a file unit, fence-aware."""

    name = "text-patterns"

    def analyze(self, unit: FileUnit) -> list[Finding]:
        findings: list[Finding] = []
        for line_no, line, in_fence in iter_lines_with_fence(unit.text):
            # In a Markdown file, suppress every text pattern inside a fenced
            # code block: such matches are documentation examples, not
            # executable behavior (the producer-catalog nuance).
            if unit.is_markdown and in_fence:
                continue
            for pat in TEXT_PATTERNS:
                if pat.regex.search(line):
                    findings.append(
                        make_finding(
                            detection_class=pat.detection_class,
                            severity=pat.severity,
                            title=pat.title,
                            message=pat.message,
                            unit=unit,
                            line=line_no,
                            snippet=line,
                            analyzer=self.name,
                        )
                    )
        return findings
