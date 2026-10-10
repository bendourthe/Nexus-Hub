"""Guard two catalog-text contracts closed in v4.13.11 T015.

1. ``ai-agent-governance`` and ``agentic-endpoint-hardening`` are mutually
   fenced: each description's SKIP clause defers the other's territory, so a
   router reading either description alone sends local endpoint hardening and
   deployed-service governance to different skills (v3.15.6 DF-1).
2. The prompt-engineering reasoning reference never asks a native-thinking
   model to write its private reasoning into the reply. Written-reasoning
   examples are labelled for models without native thinking, and a
   native-thinking variant enables thinking and asks only for the answer
   (v4.13.8 WN-1 / WN-2).
"""
from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SKILLS = _ROOT / "catalog" / "skills"
_GOVERNANCE = _SKILLS / "compliance" / "ai-agent-governance" / "SKILL.md"
_HARDENING = _SKILLS / "security-operations" / "agentic-endpoint-hardening" / "SKILL.md"
_REASONING = (
    _SKILLS
    / "ai-development"
    / "prompt-engineering"
    / "references"
    / "step-2-apply-reasoning-techniques.md"
)
_SKIP = re.compile(r"SKIP\s*[:\-]", re.IGNORECASE)


def _description(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
    assert match, f"{path} has no single-line description"
    return match.group(1).strip().strip('"')


def _skip_clause(description: str) -> str:
    match = _SKIP.search(description)
    assert match, f"description has no SKIP clause: {description!r}"
    return description[match.end() :]


def test_governance_skip_defers_endpoint_hardening() -> None:
    clause = _skip_clause(_description(_GOVERNANCE))
    assert "agentic-endpoint-hardening" in clause
    assert "endpoint" in clause.lower()


def test_hardening_skip_defers_governance() -> None:
    clause = _skip_clause(_description(_HARDENING))
    assert "governance" in clause.lower()


def test_governance_body_routes_to_endpoint_hardening() -> None:
    text = _GOVERNANCE.read_text(encoding="utf-8")
    related = text[text.index("\n## Related Skills") :]
    assert "[[agentic-endpoint-hardening]]" in related
    assert "Do NOT use this skill for" in text


def _code_blocks(text: str) -> list[tuple[str, str]]:
    """Return (preceding label line, code) for every fenced python block."""
    blocks = []
    for match in re.finditer(r"```python\n(.*?)```", text, re.DOTALL):
        before = text[: match.start()].rstrip().splitlines()
        label = next((ln for ln in reversed(before) if ln.startswith("**")), "")
        blocks.append((label, match.group(1)))
    return blocks


_WRITTEN_REASONING = re.compile(r"step-by-step|<thinking>", re.IGNORECASE)


def test_written_reasoning_examples_target_models_without_native_thinking() -> None:
    blocks = [
        (label, code)
        for label, code in _code_blocks(_REASONING.read_text(encoding="utf-8"))
        if _WRITTEN_REASONING.search(code)
    ]
    assert blocks, "expected at least one written-reasoning example"
    for label, code in blocks:
        assert "NO_NATIVE_THINKING_MODEL" in code, (
            f"written-reasoning example under {label!r} is not bound to a model "
            "without native thinking"
        )
        assert "thinking=" not in code, (
            f"example under {label!r} enables native thinking AND asks for "
            "written reasoning in the reply"
        )


def test_native_thinking_example_requests_no_private_reasoning() -> None:
    blocks = [
        code
        for _, code in _code_blocks(_REASONING.read_text(encoding="utf-8"))
        if "NATIVE_THINKING_MODEL" in code and "NO_NATIVE" not in code
    ]
    assert blocks, "the native-thinking variant is missing"
    for code in blocks:
        assert "thinking=" in code
        assert not _WRITTEN_REASONING.search(code), (
            "the native-thinking example asks the model to write out its reasoning"
        )
