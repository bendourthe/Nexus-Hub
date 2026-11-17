"""Status command routing and executable portable-report contract."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
IMPL = ROOT / "catalog/skills/workflow/implement-phase/references"
FORMATS = IMPL / "status-formats.md"
PROGRESS = IMPL / "progress-reporting.md"
STATUS_CMD = ROOT / "catalog/commands/status.md"
UPDATE_CMD = ROOT / "catalog/commands/update.md"
IMPLEMENT_CMD = ROOT / "catalog/commands/implement.md"


def squash(output: str) -> str:
    """Collapse the column padding so assertions read the cell content only."""
    return re.sub(r"-{3,}", "---", re.sub(r" {2,}", " ", re.sub(r" +\|", " |", output)))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@pytest.fixture
def rendered():
    script = IMPL.parent / "scripts/status_report.py"
    spec = importlib.util.spec_from_file_location("report_contract", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    snapshot = json.loads(read(IMPL / "status-snapshot.json"))
    return module, snapshot


@pytest.mark.parametrize("mode", ["compact", "full"])
def test_title_sections_spacing_and_bar_are_executable(rendered, mode):
    module, snapshot = rendered
    output = module.render(snapshot, mode)
    assert output.startswith("## Status Update\n\n" + ("### \U0001F680 Release status\n\n" if mode == "full" else "") + "| | |")
    assert "3/19" in output and "16%" in output
    assert "| **Last release** | v1.2.0 |" in squash(output)
    assert "No decisions waiting." in output and "Nothing running." in output
    bars = re.findall(r"([\u25b0\u25b1]+) \d+%", output)
    assert bars and all(len(bar) == 10 for bar in bars)
    assert not re.search(r"[\\](?:[()\[\]])|[$]", output)
    positions = [output.index(f"### {h}") for h in ("\U0001F3AF Goals", "\U0001F64B Decisions waiting", "\U0001F504 Running")]
    assert positions == sorted(positions)


def test_full_includes_all_rows_totals_and_evidence(rendered):
    module, snapshot = rendered
    output = module.render(snapshot, "full")
    assert "| Version | Goals | Progress | Tasks | Elapsed | Remaining |" in squash(output)
    assert "| Goal | Scope | Done when | State |" in squash(output)
    assert "| **Total** |" in squash(output)
    assert "Confidence:" in output and "Source:" in output and "As of" in output


def test_decision_details_only_in_full_report(rendered):
    module, snapshot = rendered
    snapshot["decisions"] = [{"id": "1", "title": "Choose packaging", "detail": "A is recommended because it preserves consumers", "options": [{"option": "A (recommended)", "effect": "Keep compatibility"}]}]
    full = module.render(snapshot, "full")
    compact = module.render(snapshot, "compact")
    assert "#### 1\ufe0f\u20e3 Decision #1: Choose packaging" in full
    assert "| Option | What it means | Effect |" in squash(full) and "preserves consumers" in full
    assert "Choose packaging" in compact and "| Option |" not in compact


def test_reporting_ownership_and_cadence():
    progress, formats = read(PROGRESS), read(FORMATS)
    assert "A tool call, tool yield, internal step or ordinary commentary message is not a reporting boundary" in progress
    assert "after 5 minutes" in progress and "suppress unchanged duplicates" in progress
    assert "new decision shows the full report" in progress
    assert "Decision numbers restart at 1" in progress
    assert "status_report.py" in progress and "status_report.py" in formats
    assert "every message that ends carries the compact footer" not in progress
    assert "exact font sizes" in progress


def test_existing_estimate_policy_is_preserved():
    formats = read(FORMATS)
    for expected in ("## Estimate rule", "remaining tasks times days per task", "median", "middle half", "CI floor", "unknown (fewer than 3 completed plans)"):
        assert expected in formats
    assert "fewer than 3 completed plans" in read(STATUS_CMD)


def test_status_command_is_read_only_dispatcher() -> None:
    text = read(STATUS_CMD)
    body = text
    match = re.match(r"---\ndescription: (.+?)\n---\n", text, flags=re.DOTALL)
    assert match, "frontmatter description missing"
    assert re.match(r"[A-Z][a-z]+ ", match.group(1)), "description starts with a verb"
    assert "SKIP" in match.group(1)
    assert "/status [vX.Y | vX.Y.Z | plan-path | plan-slug]" in body
    assert "progress-reporting.md" in body and "status-formats.md" in body
    lowered = body.lower()
    assert "starts no work" in lowered
    assert "changes no file and no run state" in lowered
    assert "spawns no worker" in lowered
    assert "runs no test" in lowered
    assert "never reads or enters the implementation driver" in lowered
    assert "always print the full report, never the compact footer" in lowered


def test_update_status_is_a_forwarding_alias() -> None:
    text = read(UPDATE_CMD)
    assert "`status`" in text.split("Recognized scopes:")[1].split("\n")[0]
    assert "status    -> /status" in text
    section = text.split("## Status scope")[1].split("\n## ")[0].strip().splitlines()
    assert len(section) <= 6
    assert "status.md" in "\n".join(section)


def test_implement_names_status_command() -> None:
    assert "`/status" in read(IMPLEMENT_CMD)


def test_command_count_matches_docs() -> None:
    commands = ROOT / "catalog" / "commands"
    active = 0
    aliases = 0
    for path in commands.glob("*.md"):
        h1 = next(
            ln for ln in read(path).splitlines() if ln.startswith("# ")
        )
        if h1.rstrip().endswith("(permanent alias)"):
            aliases += 1
        else:
            active += 1
    assert (active, aliases) == (22, 3)
    assert f"{active} commands (plus {aliases} permanent aliases)" in read(
        ROOT / "AGENTS.md"
    )
    assert f"{active} commands plus {aliases} permanent aliases" in read(
        ROOT / "README.md"
    )


def documented_example(heading: str) -> str:
    body = read(FORMATS).split(f"### {heading}\n\n````markdown\n", 1)[1]
    return body.split("````\n", 1)[0]


@pytest.mark.parametrize("mode", ["compact", "full"])
def test_documented_examples_equal_renderer_output(rendered, mode):
    module, snapshot = rendered
    assert documented_example(mode.capitalize()) == module.render(snapshot, mode)


def test_contract_states_escaping_and_layout_rules():
    formats = read(FORMATS)
    for expected in ("## Release table", "## Rendering rules", "Never emit a bare `$`", "capped at 48 characters",
                     "never `#` bars", "short italic footer", "Decisions waiting", "separated by a `---` rule"):
        assert expected in formats
