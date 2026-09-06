"""Tests for catalog/hooks/html-responsive-guard.{sh,ps1}.

Every behavior runs against both implementations so each assertion also proves
cross-platform exit-code parity.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
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
            check=False,
        )

    return _run


def _payload(path: str, content: str | None = None, key: str = "content") -> str:
    tool_input = {"file_path": path}
    if content is not None:
        tool_input[key] = content
    return json.dumps({"tool_input": tool_input})


def _edit_payload(
    path: str, old_string: str, new_string: str, *, replace_all: bool = False
) -> str:
    return json.dumps(
        {
            "tool_input": {
                "file_path": path,
                "old_string": old_string,
                "new_string": new_string,
                "replace_all": replace_all,
            }
        }
    )


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


@pytest.mark.parametrize(
    "content",
    [
        "<style>:root { --measure: 60ch; } .hero-copy { max-width: var(--measure); }</style>",
        "<style>:root { --base: 58ch; --measure: calc(var(--base) + 2px); } .hero-copy { max-width: var(--measure); }</style>",
        "<style>.hero-copy { max-width: calc(60ch + 2px); }</style>",
    ],
)
def test_custom_property_and_calc_text_caps_block(run, content: str) -> None:
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr


def test_unrelated_definition_cannot_mask_fixed_root_default(run) -> None:
    content = "<style>:root { --measure: 60ch; } .unrelated { --measure: 100%; } .hero-copy { max-width: var(--measure); }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr


def test_ambiguous_ancestor_with_possible_fixed_value_blocks(run) -> None:
    content = "<style>html { --measure: 100%; } .possible-ancestor { --measure: 60ch; } .hero-copy { max-width: var(--measure); }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr


def test_same_rule_nonfixed_override_wins_over_fixed_default(run) -> None:
    content = "<style>:root { --measure: 60ch; } .hero-copy { --measure: 100%; max-width: var(--measure); }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 0
    assert _BLOCK_MARKER not in proc.stderr


def test_more_specific_matching_selector_fixed_definition_blocks(run) -> None:
    content = "<style>.hero-copy { --measure: 100%; max-width: var(--measure); } .theme .hero-copy { --measure: 60ch; }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr


def test_truly_unrelated_selector_does_not_override_local_fluid(run) -> None:
    content = "<style>.hero-copy { --measure: 100%; max-width: var(--measure); } .unrelated { --measure: 60ch; }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 0
    assert _BLOCK_MARKER not in proc.stderr


def test_defined_fluid_variable_ignores_fixed_fallback(run) -> None:
    content = "<style>:root { --measure: 100%; } .hero-copy { max-width: var(--measure, 60ch); }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 0
    assert _BLOCK_MARKER not in proc.stderr


def test_important_fixed_local_definition_wins_over_later_fluid_value(run) -> None:
    content = "<style>.hero-copy { --measure: 60ch !important; --measure: 100%; max-width: var(--measure); }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr


def test_last_ordinary_local_definition_wins(run) -> None:
    content = "<style>.hero-copy { --measure: 60ch; --measure: 100%; max-width: var(--measure); }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 0
    assert _BLOCK_MARKER not in proc.stderr


def test_later_exact_selector_fixed_definition_applies(run) -> None:
    content = "<style>.hero-copy { --measure: 100%; max-width: var(--measure); } .hero-copy { --measure: 60ch; }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr


def test_later_exact_selector_fluid_definition_overrides_earlier_fixed(run) -> None:
    content = "<style>.hero-copy { --measure: 60ch; max-width: var(--measure); } .hero-copy { --measure: 100%; }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 0
    assert _BLOCK_MARKER not in proc.stderr


def test_important_exact_selector_definition_survives_later_ordinary_value(run) -> None:
    content = "<style>.hero-copy { --measure: 60ch !important; max-width: var(--measure); } .hero-copy { --measure: 100%; }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr


def test_unrelated_candidate_does_not_suppress_fixed_fallback(run) -> None:
    content = "<style>.unrelated { --measure: 100%; } .hero-copy { max-width: var(--measure, 60ch); }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr


def test_css_wide_invalid_value_keeps_fixed_fallback_reachable(run) -> None:
    content = "<style>.hero-copy { --measure: initial; max-width: var(--measure, 60ch); }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr


def test_nested_fluid_definition_suppresses_unreachable_fixed_fallback(run) -> None:
    content = "<style>:root { --b: 100%; } .hero-copy { max-width: var(--a, var(--b, 60ch)); }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 0
    assert _BLOCK_MARKER not in proc.stderr


def test_cyclic_definition_keeps_fixed_use_site_fallback_reachable(run) -> None:
    content = "<style>:root { --measure: var(--measure); } .hero-copy { max-width: var(--measure, 60ch); }</style>"
    proc = run(_payload("site/report.html", content))
    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr


def test_many_ambiguous_variables_short_circuit_without_cartesian_expansion(run) -> None:
    definitions = []
    references = []
    for index in range(24):
        definitions.append(f".candidate-a-{index} {{ --v{index}: 100%; }}")
        second_value = "60ch" if index == 23 else "100%"
        definitions.append(f".candidate-b-{index} {{ --v{index}: {second_value}; }}")
        references.append(f"var(--v{index})")
    content = (
        "<style>"
        + " ".join(definitions)
        + f" .hero-copy {{ max-width: calc({' + '.join(references)}); }}"
        + "</style>"
    )

    started = time.perf_counter()
    proc = run(_payload("site/report.html", content))
    elapsed = time.perf_counter() - started

    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr
    assert elapsed < 5.0, f"scope resolution took {elapsed:.2f}s"


def test_edit_reconstruction_uses_fixed_definition_outside_new_string(
    run, tmp_path: Path
) -> None:
    target = tmp_path / "report.html"
    old = "<main>Before</main>"
    target.write_text(
        f"<style>:root {{ --measure: 60ch; }}</style>{old}", encoding="utf-8"
    )
    new = "<style>.hero-copy { max-width: var(--measure); }</style><main>After</main>"

    proc = run(_edit_payload(str(target), old, new))

    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr


def test_edit_reconstruction_allows_fluid_definition_outside_new_string(
    run, tmp_path: Path
) -> None:
    target = tmp_path / "report.html"
    old = "<main>Before</main>"
    target.write_text(
        f"<style>:root {{ --measure: 100%; }}</style>{old}", encoding="utf-8"
    )
    new = "<style>.hero-copy { max-width: var(--measure); }</style><main>After</main>"

    proc = run(_edit_payload(str(target), old, new))

    assert proc.returncode == 0
    assert _BLOCK_MARKER not in proc.stderr


def test_unreadable_edit_with_unresolved_text_variable_fails_closed(
    run, tmp_path: Path
) -> None:
    target = tmp_path / "missing.html"
    new = ".hero-copy { max-width: var(--measure); }"

    proc = run(_edit_payload(str(target), "missing", new))

    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr
    assert "could not reconstruct" in proc.stderr.lower()


def test_oversized_edit_with_fixed_custom_property_fails_closed(
    run, tmp_path: Path
) -> None:
    target = tmp_path / "oversized.html"
    target.write_bytes(b"x" * (5 * 1024 * 1024 + 1))

    proc = run(_edit_payload(str(target), "missing", "--measure: 60ch;"))

    assert proc.returncode == 2
    assert _BLOCK_MARKER in proc.stderr
    assert "could not reconstruct" in proc.stderr.lower()


@pytest.mark.parametrize(
    ("new_string", "expected_returncode"),
    [("--measure: var(--base);", 2), ("--measure: 100%;", 0)],
)
def test_failed_edit_reconstruction_classifies_custom_property_value(
    run, tmp_path: Path, new_string: str, expected_returncode: int
) -> None:
    target = tmp_path / "missing.html"

    proc = run(_edit_payload(str(target), "missing", new_string))

    assert proc.returncode == expected_returncode
    assert (_BLOCK_MARKER in proc.stderr) is (expected_returncode == 2)


@pytest.mark.parametrize(
    ("replace_all", "expected_returncode"),
    [(False, 0), (True, 2)],
)
def test_edit_reconstruction_respects_replace_all(
    run, tmp_path: Path, replace_all: bool, expected_returncode: int
) -> None:
    target = tmp_path / "report.html"
    target.write_text(
        "<style>.hero-artwork { max-width: 100%; } .hero-copy { max-width: 100%; }</style>",
        encoding="utf-8",
    )

    proc = run(
        _edit_payload(
            str(target),
            "max-width: 100%",
            "max-width: 60ch",
            replace_all=replace_all,
        )
    )

    assert proc.returncode == expected_returncode
    assert (_BLOCK_MARKER in proc.stderr) is replace_all


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


def test_custom_property_container_bound_is_allowed(run) -> None:
    content = "<style>:root { --page-bound: 1200px; } .page-container { max-width: var(--page-bound); }</style>"
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


def _run_bash_without_python(
    bash_bin: str, payload: str
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PATH": ""}
    env.pop("NEXUS_DISABLED_HOOKS", None)
    env.pop("NEXUS_HOOK_PROFILE", None)
    return subprocess.run(
        [bash_bin, str(_HOOK_SH)],
        input=payload,
        text=True,
        capture_output=True,
        env=env,
        timeout=120,
        check=False,
    )


def test_bash_without_python_allows_clearly_irrelevant_path(bash_bin: str) -> None:
    proc = _run_bash_without_python(
        bash_bin,
        _payload("docs/report.md", ".hero-copy { max-width: 60ch; }"),
    )
    assert proc.returncode == 0
    assert "CANNOT RUN" not in proc.stderr


def test_bash_without_python_allows_empty_stdin(bash_bin: str) -> None:
    proc = _run_bash_without_python(bash_bin, "")
    assert proc.returncode == 0
    assert "CANNOT RUN" not in proc.stderr


@pytest.mark.parametrize("path", ["site/report.html", "assets/report.CSS"])
def test_bash_without_python_fails_closed_for_relevant_path(
    bash_bin: str, path: str
) -> None:
    proc = _run_bash_without_python(
        bash_bin,
        _payload(path, ".hero-copy { max-width: 60ch; }"),
    )
    assert proc.returncode == 3
    assert "[html-responsive-guard] CANNOT RUN" in proc.stderr
    assert "Python 3" in proc.stderr
    assert path in proc.stderr


@pytest.mark.parametrize(
    "payload",
    [
        '{"tool_input":{"file_path":"site/report\\u002ehtml","content":".hero-copy { max-width: 60ch; }"}}',
        "not json",
        "{}",
        '{"tool_input":{"content":".hero-copy { max-width: 60ch; }"}}',
    ],
)
def test_bash_without_python_fails_closed_for_unclassifiable_payload(
    bash_bin: str, payload: str
) -> None:
    proc = _run_bash_without_python(bash_bin, payload)
    assert proc.returncode == 3
    assert "[html-responsive-guard] CANNOT RUN" in proc.stderr
    assert "Python 3" in proc.stderr


def test_bash_without_python_uses_only_tool_input_path(bash_bin: str) -> None:
    payload = json.dumps(
        {
            "meta": {"file_path": "docs/report.md"},
            "tool_input": {
                "file_path": "site/report.html",
                "content": ".hero-copy { max-width: 60ch; }",
            },
        }
    )
    proc = _run_bash_without_python(bash_bin, payload)
    assert proc.returncode == 3
    assert "[html-responsive-guard] CANNOT RUN" in proc.stderr
    assert "site/report.html" in proc.stderr
