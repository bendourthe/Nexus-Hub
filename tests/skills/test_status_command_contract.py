"""Contract test for the /status command and the progress footer.

The compact footer and the full report are approved layouts. This test fails
when `status-formats.md` drifts from them, when the footer rule or the decision
rules leave `progress-reporting.md`, when `/status` stops being read-only, when
`/update status` stops being a forwarding alias, or when the headline command
count disagrees with the command files.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
IMPL = ROOT / "catalog" / "skills" / "workflow" / "implement-phase" / "references"
FORMATS = IMPL / "status-formats.md"
PROGRESS = IMPL / "progress-reporting.md"
STATUS_CMD = ROOT / "catalog" / "commands" / "status.md"
UPDATE_CMD = ROOT / "catalog" / "commands" / "update.md"
IMPLEMENT_CMD = ROOT / "catalog" / "commands" / "implement.md"

NEW_DECISION_RULE = (
    "A message that asks the user for a new decision shows the full report, "
    "never the compact footer."
)
RESTART_RULE = (
    "Decision numbers restart at 1 for each new batch of open decisions; they do "
    "not continue from decisions already answered, except that a still-open "
    "decision carried over keeps its number when renumbering would confuse a "
    "reference to it."
)
FOOTER_RULE = "every message that ends carries the compact footer"
SEP = "&nbsp;&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;&nbsp;"
BAR_RE = re.compile(r"([▰▱]+)(?:\s+\*{0,2}(\d+)%\*{0,2})")

PLAN_HEADER = "| Version | Goals | Progress | Tasks | Elapsed | Remaining |"
OPTIONS_HEADER = "| Option | What it means | Effect |"
RUNNING_HEADER = "| Item | Progress | Tasks | State | Elapsed | Remaining |"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def example_blocks(text: str) -> list[str]:
    return re.findall(r"```markdown\n(.*?)\n```", text, flags=re.S)


@pytest.fixture(scope="module")
def formats() -> str:
    return read(FORMATS)


@pytest.fixture(scope="module")
def compact(formats: str) -> str:
    return example_blocks(formats)[0]


@pytest.fixture(scope="module")
def full(formats: str) -> str:
    return example_blocks(formats)[1]


def test_formats_has_exactly_two_examples(formats: str) -> None:
    assert len(example_blocks(formats)) == 2


def test_compact_first_line_layout(compact: str) -> None:
    line = next(ln for ln in compact.splitlines() if ln.startswith("**Status: v"))
    assert SEP in line
    assert "last released v" in line
    assert re.search(r"\d+ versions left", line)
    assert "time left:" in line


def test_compact_labels_pointer_and_exclusions(compact: str) -> None:
    assert "🙋" in compact and "🔄" in compact
    assert compact.rstrip().splitlines()[-1] == "*Full report: /status*"
    assert compact.startswith("---")
    assert "Decision #" not in compact
    assert "| Option |" not in compact


@pytest.mark.parametrize("which", ["compact", "full"])
def test_every_bar_has_ten_segments_and_matches_percent(
    which: str, compact: str, full: str
) -> None:
    text = compact if which == "compact" else full
    bars = BAR_RE.findall(text)
    assert bars, "no bars found"
    for bar, percent in bars:
        assert len(bar) == 10, f"{bar} is not 10 segments"
        assert bar == "▰" * bar.count("▰") + "▱" * bar.count("▱")
        assert bar.count("▰") == math.floor(int(percent) / 10), (
            f"{bar} does not match {percent}%"
        )


def test_full_headings_and_headers(full: str) -> None:
    for needle in (
        "## Status Update:",
        "## 🙋 Waiting on you",
        "## 🔄 Running now",
        PLAN_HEADER,
        OPTIONS_HEADER,
        RUNNING_HEADER,
        "### 1️⃣ Decision #1:",
    ):
        assert needle in full, needle
    assert "| Status |" not in full


def test_full_spacer_before_each_rule(full: str) -> None:
    lines = full.splitlines()
    rules = [i for i, ln in enumerate(lines) if ln == "---"]
    assert len(rules) == 2
    for i in rules:
        assert lines[i - 1] == "" and lines[i - 2] == "&nbsp;", f"rule at line {i}"


def test_full_goals_cells_have_one_escaped_pipe(full: str) -> None:
    rows = [ln for ln in full.splitlines() if ln.startswith("| **v")]
    assert rows
    for row in rows:
        goals = re.split(r"(?<!\\)\|", row)[2]
        assert goals.count("\\|") == 1, row


def test_formats_state_decision_rules_and_bar_rule(formats: str) -> None:
    assert NEW_DECISION_RULE in formats
    assert RESTART_RULE in formats
    assert "floor(percent / 10)" in formats
    assert "*Full report: /status*" in formats
    assert "time left: not measured yet" in formats
    assert "prints as `unknown`" in formats


def test_progress_reporting_links_formats_and_states_rules() -> None:
    text = read(PROGRESS)
    assert "(status-formats.md)" in text
    assert FOOTER_RULE in text
    assert NEW_DECISION_RULE in text
    assert RESTART_RULE in text
    assert "`/implement` run is in progress" in text


def test_instruction_templates_do_not_carry_the_footer() -> None:
    for path in (ROOT / "templates" / "ai-instructions").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "status-formats" not in text, path
            assert "Full report: /status" not in text, path


def test_status_command_is_read_only_dispatcher() -> None:
    text = read(STATUS_CMD)
    head, _, body = text.partition("\n---\n")[0], None, text
    match = re.match(r"---\ndescription: (.+?)\n---\n", text, flags=re.S)
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
