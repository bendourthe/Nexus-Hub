"""Gate records recompute: every worked example in Step 5 re-derives its outcome and its digest.

The quality-gate-definitions skill promises that a logged verdict can be recomputed from the
record and git alone. This test performs that recomputation for each ```gate-record example:
the criterion outcomes from the measured value, comparison, and threshold; the gate outcome from
the Step 3 precedence; and the definition digest from the canonical form of the gate block in
the same file. It reads repository files only.
"""

from __future__ import annotations

import hashlib
import operator
import re
from dataclasses import dataclass
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SKILL_REL = "catalog/skills/orchestration/quality-gate-definitions/SKILL.md"
_SKILL = _ROOT / _SKILL_REL

_COMPARE = {
    "<=": operator.le,
    ">=": operator.ge,
    "<": operator.lt,
    ">": operator.gt,
    "==": operator.eq,
    "!=": operator.ne,
}
_FENCE_RE = re.compile(r"^```gate-record\n(.*?)^```", re.MULTILINE | re.DOTALL)
_NUMBER_RE = re.compile(r"^-?\d+(\.\d+)?$")
_ROW_RE = re.compile(r"^[RO]\d+ \|")
_HEX64_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _lf(text: str) -> str:
    return text.replace("\r\n", "\n")


def canonical_form(text: str, heading: str) -> str:
    """Return the canonical form of the block that starts at `heading`.

    The block runs to the next heading of equal or higher level, or to the end of the enclosing
    code fence or file. Lines end in LF with trailing whitespace stripped, trailing blank lines
    are dropped, and the result ends with one LF.
    """
    lines = _lf(text).split("\n")
    starts = [i for i, line in enumerate(lines) if line.rstrip() == heading]
    assert len(starts) == 1, (
        f"expected exactly one {heading!r} heading, found {len(starts)}"
    )
    level = len(heading) - len(heading.lstrip("#"))
    block: list[str] = []
    for line in lines[starts[0] :]:
        if block and line.startswith("```"):
            break
        match = re.match(r"^(#+)\s", line)
        if block and match and len(match.group(1)) <= level:
            break
        block.append(line.rstrip())
    while block and not block[-1]:
        block.pop()
    return "\n".join(block) + "\n"


def digest(text: str, gate: str) -> str:
    return hashlib.sha256(
        canonical_form(text, f"## Gate: {gate}").encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class Criterion:
    ident: str
    kind: str
    measured: str
    comparison: str
    threshold: str
    output_hash: str
    outcome: str


@dataclass(frozen=True)
class Record:
    gate: str
    path: str
    published_digest: str
    criteria: tuple[Criterion, ...]
    outcome: str
    stands_because: str | None


def _field(blob: str, key: str) -> str:
    for part in re.split(r"[\n|]", blob):
        name, _, value = part.strip().partition(":")
        if name == key:
            return value.strip()
    raise AssertionError(f"record lacks the {key!r} field")


def parse_records(text: str) -> list[Record]:
    records: list[Record] = []
    for blob in _FENCE_RE.findall(_lf(text)):
        rows = [line for line in blob.split("\n") if _ROW_RE.match(line)]
        criteria = []
        for row in rows:
            cells = [cell.strip() for cell in row.split("|")]
            assert len(cells) == 8, (
                f"criterion row has {len(cells)} cells, expected 8: {row!r}"
            )
            criteria.append(
                Criterion(
                    cells[0], cells[1], cells[2], cells[3], cells[4], cells[6], cells[7]
                )
            )
        definition = _field(blob, "definition")
        path, _, _sha = definition.partition("@")
        try:
            stands = _field(blob, "stands-because")
        except AssertionError:
            stands = None
        records.append(
            Record(
                gate=_field(blob, "gate"),
                path=path,
                published_digest=_field(blob, "sha256"),
                criteria=tuple(criteria),
                outcome=_field(blob, "outcome"),
                stands_because=stands,
            )
        )
    return records


def criterion_outcome(c: Criterion) -> str:
    """Recompute one criterion. A missing value or threshold is never inferred."""
    if c.measured == "-" or c.threshold == "-":
        return "not measured"
    value: float | bool
    if c.measured in ("true", "false"):
        value = c.measured == "true"
        threshold: float | bool = c.threshold == "true"
    else:
        value, threshold = float(c.measured), float(c.threshold)
    return "met" if _COMPARE[c.comparison](value, threshold) else "not met"


def gate_outcome(criteria: tuple[Criterion, ...]) -> str:
    """Apply the Step 3 precedence: FAIL > UNGATED > PARTIAL > PASS (fixable or blocking is a judgment)."""
    if not any(c.kind == "required" for c in criteria):
        return "UNGATED"
    results = [(c.kind, criterion_outcome(c)) for c in criteria]
    if any(kind == "required" and res == "not met" for kind, res in results):
        return "FAIL"
    if any(kind == "required" and res == "not measured" for kind, res in results):
        return "UNGATED"
    if any(kind == "optional" and res != "met" for kind, res in results):
        return "PARTIAL"
    return "PASS"


_TEXT = _lf(_SKILL.read_text(encoding="utf-8"))
_RECORDS = parse_records(_TEXT)


def test_step_5_publishes_worked_examples() -> None:
    # A skill whose examples cannot be found must fail loudly, never skip.
    assert len(_RECORDS) >= 3, (
        f"{_SKILL_REL}: Step 5 must carry at least three gate-record examples"
    )


@pytest.mark.parametrize(
    "n", range(len(_RECORDS)), ids=lambda n: f"{_RECORDS[n].gate}-{n}"
)
def test_each_worked_example_recomputes(n: int) -> None:
    record = _RECORDS[n]
    name = f"{record.gate} (example {n + 1})"
    assert record.path == _SKILL_REL, (
        f"{name}: definition path {record.path!r} is not {_SKILL_REL}"
    )
    assert record.published_digest == digest(_TEXT, record.gate), (
        f"{name}: published digest does not match the canonical form of the '## Gate: {record.gate}' block"
    )
    for c in record.criteria:
        assert c.comparison in _COMPARE, (
            f"{name}: {c.ident} has unknown comparison {c.comparison!r}"
        )
        assert (
            c.measured == "-"
            or c.measured in ("true", "false")
            or _NUMBER_RE.match(c.measured)
        ), f"{name}: {c.ident} measured value {c.measured!r} is not a number or boolean"
        assert _HEX64_RE.match(c.output_hash), (
            f"{name}: {c.ident} lacks an output sha256"
        )
        assert criterion_outcome(c) == c.outcome, (
            f"{name}: {c.ident} outcome {c.outcome!r} does not recompute"
        )
    assert record.outcome.startswith(gate_outcome(record.criteria)), (
        f"{name}: outcome {record.outcome!r} does not recompute to {gate_outcome(record.criteria)}"
    )


def test_a_rerun_that_stands_states_why() -> None:
    runs: dict[str, int] = {}
    for record in _RECORDS:
        runs[record.gate] = runs.get(record.gate, 0) + 1
        if runs[record.gate] > 1:
            assert record.stands_because, (
                f"{record.gate}: a later record must state why it stands"
            )


def test_crlf_and_lf_versions_of_a_gate_block_hash_equally() -> None:
    crlf = _TEXT.replace("\n", "\r\n")
    for gate in {r.gate for r in _RECORDS}:
        assert digest(crlf, gate) == digest(_TEXT, gate), (
            f"{gate}: CRLF changed the digest"
        )


def test_trailing_whitespace_and_blank_lines_do_not_change_the_digest() -> None:
    gate = _RECORDS[0].gate
    noisy = _TEXT.replace(f"## Gate: {gate}", f"## Gate: {gate}   ", 1)
    assert digest(noisy, gate) == digest(_TEXT, gate)


def test_a_changed_threshold_changes_the_digest() -> None:
    gate = "lint-passes"
    changed = _TEXT.replace(
        "Linter reports zero errors", "Linter reports at most one error", 1
    )
    assert changed != _TEXT, "scratch edit did not apply"
    assert digest(changed, gate) != digest(_TEXT, gate)
