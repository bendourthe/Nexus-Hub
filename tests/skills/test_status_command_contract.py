"""Status command routing and executable portable-report contract."""

from __future__ import annotations

import importlib.util
import copy
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
IMPL = ROOT / "catalog/skills/workflow/implement-phase/references"
FORMATS = IMPL / "status-formats.md"
PROGRESS = IMPL / "progress-reporting.md"
STATUS_CMD = ROOT / "catalog/commands/progress.md"
STATUS_SHIM = ROOT / "catalog/commands/status.md"
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
    assert output.startswith("Waiting for you: Capture the installed application result\n\n")
    assert "## Progress Update\n\n" in output
    assert output.index("### Required actions") < output.index("### \U0001F3AF Goals")
    assert "3/19" in output and "16%" in output
    assert "| **Last release** | v1.2.0 |" in squash(output)
    assert "Capture the installed application result" in output
    assert "Expected result: A fresh installed application receipt" in output
    assert "Paste the resulting receipt path in this conversation" in output
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
    assert "Source:" in output and "Confidence" not in output and "As of" not in output


def test_decision_details_only_in_full_report(rendered):
    module, snapshot = rendered
    snapshot["decisions"] = [{"id": "1", "title": "Choose packaging", "detail": "A is recommended because it preserves consumers", "options": [{"option": "A (recommended)", "effect": "Keep compatibility"}, {"option": "B", "effect": "Require migration"}], "reply": "Reply A or B"}]
    full = module.render(snapshot, "full")
    compact = module.render(snapshot, "compact")
    assert "#### 1\ufe0f\u20e3 Decision #1: Choose packaging" in full
    assert "| Option | What it means | Effect |" in squash(full) and "preserves consumers" in full
    assert "#### 1\ufe0f\u20e3 Decision #1: Choose packaging" in compact
    assert "| Option | What it means | Effect |" in squash(compact) and "preserves consumers" not in compact


@pytest.mark.parametrize("mode", ["compact", "full"])
@pytest.mark.parametrize("fresh_ids", [("9",), ("runtime-prerequisite-source-expansion",), ("9", "another-source-decision")])
def test_fresh_decision_display_restarts_without_reusing_resolved_request_ids(rendered, mode, fresh_ids):
    """Private descriptive proofs exercise retirement, not genuine approval capture."""
    module, snapshot = rendered
    def decision(identity, title):
        return {"id": identity, "kind": "decision", "title": title, "detail": "A preserves the approved scope",
                "options": [{"option": "A (recommended)", "effect": "Continue within scope"},
                            {"option": "B", "effect": "Keep work pending"}], "reply": "Reply A or B"}
    def observation(requests, resolutions=None):
        return {"objective": "Finish the complete approved objective", "remaining_tasks": 16,
                "requests": requests, "resolutions": resolutions or [], "completion": {"verified": False}}
    old_requests = [decision(str(n), "Previous choice " + str(n)) for n in (1, 2)]
    old_state = module._STATE.reconcile(observation(old_requests))
    resolutions = [{"request_id": item["id"], "verified": True, "evidence": "Private reply verified",
                    "authority_receipt": "private-unit-proof-" + item["id"]} for item in old_requests]
    fresh = [decision(identity, "Fresh choice " + str(n)) for n, identity in enumerate(fresh_ids, 1)]
    settled = module._STATE.reconcile(observation(fresh, resolutions), old_state)
    current = module._STATE.reconcile(observation(fresh), settled)
    assert current["requests"] == fresh and current["resolved_requests"] == resolutions
    with pytest.raises(ValueError, match="fulfilled request id cannot be reused"):
        module._STATE.reconcile(observation([old_requests[0]]), settled)
    snapshot["decisions"] = []
    snapshot["continuation"] = old_state
    old_receipt = module.select_report(snapshot, None, "start")["receipt"]
    prior_receipt = copy.deepcopy(old_receipt)
    snapshot["continuation"] = current
    original_snapshot = copy.deepcopy(snapshot)
    output = module.render(snapshot, mode)
    for number, request in enumerate(fresh, 1):
        assert f"Decision #{number}: {request['title']}" in output
        assert f"Decision #{request['id']}:" not in output
    assert "Previous choice" not in output
    selected = module.select_report(snapshot, old_receipt, "checkpoint")
    assert selected["mode"] == "full"
    assert [request["id"] for request in selected["receipt"]["decisions"]] == list(fresh_ids)
    assert [request["id"] for request in old_receipt["decisions"]] == ["1", "2"]
    assert snapshot == original_snapshot and old_receipt == prior_receipt
    assert module.continuation(snapshot)["requests"] == fresh


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
    for expected in ("## Estimate rule", "remaining tasks times days per task", "median", "middle half", "one effective lane", "no parallel discount", "N/A (no history yet)"):
        assert expected in formats
    assert "status_snapshot.py" in read(STATUS_CMD) and "never prints `unknown`" in read(STATUS_CMD)


def test_status_command_is_read_only_dispatcher() -> None:
    text = read(STATUS_CMD)
    body = text
    match = re.match(r"---\ndescription: (.+?)\n---\n", text, flags=re.DOTALL)
    assert match, "frontmatter description missing"
    assert re.match(r"[A-Z][a-z]+ ", match.group(1)), "description starts with a verb"
    assert "SKIP" in match.group(1)
    assert "/progress [vX.Y | vX.Y.Z | plan-path | plan-slug]" in body
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
    assert "status    -> /progress" in text
    section = text.split("## Status scope")[1].split("\n## ")[0].strip().splitlines()
    assert len(section) <= 6
    assert "progress.md" in "\n".join(section)


def test_implement_names_status_command() -> None:
    assert "`/progress" in read(IMPLEMENT_CMD)


def test_command_count_matches_docs() -> None:
    commands = ROOT / "catalog" / "commands"
    active = 0
    aliases = 0
    for path in commands.glob("*.md"):
        if re.search(r"^description: DEPRECATED", read(path), re.M):
            continue
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


COMPACT_DECISION = {
    "id": "1", "title": "Keep the Claude Code and Codex split across restarts", "detail": "unused in compact", "reply": "Reply A, B or C",
    "options": [
        {"option": "A (recommended)", "meaning": "Experiment, then build the opt-in restore",
         "effect": "Split survives restarts, if a public API allows it (~2-3 h)"},
        {"option": "B", "meaning": "Experiment only", "effect": "Written finding, no code"},
        {"option": "C", "meaning": "Defer", "effect": "Recorded as a v4.15.8 follow-up"},
    ],
}


def test_documented_compact_decision_example_equals_renderer_output(rendered):
    module, snapshot = rendered
    snapshot["decisions"] = [COMPACT_DECISION]
    assert documented_example("Compact with a decision") == module.render(snapshot, "compact")


def test_contract_states_escaping_and_layout_rules():
    formats = read(FORMATS)
    for expected in ("## Release table", "## Rendering rules", "Never emit a bare `$`", "capped at 48 characters",
                     "never `#` bars", "short italic footer", "Decisions waiting", "separated by a `---` rule", "Options not supplied", "No output contains `&nbsp;`", "Verbatim output rule"):
        assert expected in formats


def test_status_shim_is_removed() -> None:
    """The v4.15.4 notes announced /status removal in v4.15.5; /progress replaces it."""
    assert not STATUS_SHIM.exists()
