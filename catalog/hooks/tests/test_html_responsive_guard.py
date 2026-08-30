"""Tests for catalog/hooks/html-responsive-guard.{sh,ps1}.

Every behavior runs against both implementations so each assertion also proves
cross-platform exit-code parity.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_HOOK_SH = _HOOKS_DIR / "html-responsive-guard.sh"
_HOOK_PS1 = _HOOKS_DIR / "html-responsive-guard.ps1"
_BLOCK_MARKER = "[html-responsive-guard] BLOCKED"
_RULE_PATH = "catalog/rules/html/responsive-layout.md"


@pytest.fixture(params=["sh", "ps1"])
def run(request):
    """Invoke either implementation with an isolated environment."""
    if request.param == "sh":
        prefix = [request.getfixturevalue("bash_bin"), str(_HOOK_SH)]
    else:
        prefix = [
            request.getfixturevalue("powershell_bin"),
            "-NoProfile",
            "-File",
            str(_HOOK_PS1),
        ]

    def _run(
        payload: str = "", env_extra: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        env = {**os.environ}
        env.pop("NEXUS_DISABLED_HOOKS", None)
        env.pop("NEXUS_HOOK_PROFILE", None)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            prefix,
            input=payload,
            text=True,
            capture_output=True,
            env=env,
            timeout=120,
        )

    return _run


def _payload(path: str, content: str | None = None, key: str = "content") -> str:
    tool_input = {"file_path": path}
    if content is not None:
        tool_input[key] = content
    return json.dumps({"tool_input": tool_input})


def test_write_content_blocks_fixed_text_cap(run) -> None:
    proc = run(_payload("site/report.html", "<style>.hero-copy { max-width: 60ch; }</style>"))
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr
    assert "max-width: 60ch" in proc.stderr
    assert "site/report.html" in proc.stderr
    assert _RULE_PATH in proc.stderr


def test_edit_new_string_blocks_css_fragment(run) -> None:
    proc = run(_payload("site/report.html", ".report-description { max-width: 640px; }", key="new_string"))
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr


def test_css_file_blocks_text_selector(run) -> None:
    proc = run(_payload("assets/report.css", ".prose { max-width: 72ch; }"))
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr


def test_inline_text_style_blocks(run) -> None:
    proc = run(_payload("site/report.html", '<p style="max-width: 560px">Text</p>'))
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr


@pytest.mark.parametrize("selector", ["p.container", ".copy-container"])
def test_text_evidence_wins_over_container_name(run, selector: str) -> None:
    proc = run(_payload("site/report.html", f"<style>{selector} {{ max-width: 60ch; }}</style>"))
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr


def test_media_query_condition_is_not_a_declaration(run) -> None:
    content = "<style>@media (max-width: 720px) { .hero-copy { font-size: 1rem; } }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 0
    assert _BLOCK_MARKER not in proc.stderr


def test_fixed_text_cap_inside_media_query_still_blocks(run) -> None:
    content = "<style>@media (max-width: 720px) { .hero-copy { max-width: 60ch; } }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr


def test_responsive_container_bound_is_allowed(run) -> None:
    content = "<style>.page-container { width: min(100%, 1200px); max-width: 1200px; margin-inline: auto; }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 0
    assert _BLOCK_MARKER not in proc.stderr


def test_bounded_media_is_allowed(run) -> None:
    content = "<style>img.hero-artwork { width: 100%; max-width: 640px; height: auto; }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 0
    assert _BLOCK_MARKER not in proc.stderr


def test_direct_media_tag_remains_allowed_with_text_named_class(run) -> None:
    content = "<style>img.caption { width: 100%; max-width: 640px; height: auto; }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 0
    assert _BLOCK_MARKER not in proc.stderr


def test_media_query_in_comment_is_ignored(run) -> None:
    content = "<style>/* .hero-copy { max-width: 60ch; } */ .hero-copy { color: black; }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 0
    assert _BLOCK_MARKER not in proc.stderr


def test_non_html_path_is_irrelevant(run) -> None:
    proc = run(_payload("docs/report.md", ".hero-copy { max-width: 60ch; }"))
    assert proc.returncode == 0
    assert _BLOCK_MARKER not in proc.stderr


def test_absent_content_fails_open(run) -> None:
    proc = run(_payload("site/report.html"))
    assert proc.returncode == 0
    assert _BLOCK_MARKER not in proc.stderr


@pytest.mark.parametrize("payload", ["", "not json", "{}", '{"tool_input":{}}'])
def test_malformed_or_incomplete_payload_fails_open(run, payload: str) -> None:
    proc = run(payload)
    assert proc.returncode == 0
    assert _BLOCK_MARKER not in proc.stderr


@pytest.mark.parametrize(
    "control,env_extra",
    [
        ("disabled hook", {"NEXUS_DISABLED_HOOKS": "other,html-responsive-guard"}),
        ("minimal profile", {"NEXUS_HOOK_PROFILE": "minimal"}),
    ],
)
def test_runtime_control_bypasses_offending_payload(run, control: str, env_extra: dict[str, str]) -> None:
    proc = run(_payload("site/report.html", ".hero-copy { max-width: 60ch; }"), env_extra)
    assert proc.returncode == 0, control
    assert _BLOCK_MARKER not in proc.stderr
