#!/usr/bin/env python3
"""Assert the five lockstep base-*.md instruction templates stay in parity.

AGENTS.md requires that the five platform-agnostic AI-instruction templates --

    templates/ai-instructions/base-claude.md
    templates/ai-instructions/base-codex.md
    templates/ai-instructions/base-cursor.md
    templates/ai-instructions/base-gemini.md
    templates/ai-instructions/base-opencode.md

-- be edited "all five in lockstep ... changes must be platform-agnostic". A
platform-agnostic edit that lands in four of the five (e.g. an MCP Registry
Policy reword applied to base-claude.md but forgotten in base-gemini.md) is a
silent drift the rest of the suite cannot see. This guard makes that whole
*class* of bug impossible to ship, the same way `check_version_sync.py` makes
version drift impossible.

This validator is stdlib-only (no PyYAML, no third-party deps) so it is
cross-platform from a single `.py` file, consistent with the other top-level
`.py`-only validators -- the NI-v24-1 convention: a Python validator needs no
`.ps1` sibling and is NOT a distributed artifact (no installer copy step).

THE PARITY CONTRACT (structural, never raw-byte whole-file)

The five templates are NOT structurally identical today: base-claude.md is the
"full" template (a separate Critical Rules section, plus
Agent Registry / Spending Controls / Environment Variables / MCP Integration),
while the other four collapse those into one Working Conventions section and
omit the optional blocks. The contract is therefore built on what the five
files actually share, not on a naive equality of the whole file.

  MUST stay identical (the guard enforces these):

    1. Required section headings -- each heading in REQUIRED_HEADINGS must be
       present in every lockstep file that exists.
    2. Required placeholder tokens -- each token in REQUIRED_PLACEHOLDERS must
       appear in every lockstep file that exists.
    3. Invariant content blocks -- the body of each section in
       INVARIANT_SECTIONS must be byte-identical (after newline + trailing-
       whitespace normalization) across every lockstep file that has it. This
       is the core lockstep enforcer: it compares the files to each other, so
       an in-lockstep edit to all five passes while an edit to a subset fails.

  ALLOWED to differ (the guard never flags these):

    * Platform names and per-platform install paths (`.claude/skills/`,
      `.codex/skills/`, `skills/`, ...).
    * Claude-only optional sections (Agent Registry, Spending Controls,
      Environment Variables, MCP Integration) and the
      Critical Rules vs Working Conventions split.
    * Context References (absent in base-gemini.md), the per-platform
      behavioral-rule bullet wording, and Output Minimization's claude-only
      5th bullet.

File semantics:

  * A lockstep file ABSENT under the scanned root is reported informationally,
    never as a finding -- so the guard works on partial trees and fixtures.
    When fewer than two lockstep files are present there is nothing to compare,
    so the run is a clean no-op (exit 0).
  * A present file that drops a required heading or placeholder, or whose
    invariant block diverges from its peers, is a FINDING.

Exit codes:
    0 - parity holds (or fewer than two lockstep files present: nothing to do)
    1 - one or more parity findings (each named on stderr)
    2 - usage / IO error (a present template file could not be read)

Usage:
    python scripts/check_base_template_parity.py
    python scripts/check_base_template_parity.py --root /path/to/repo
    python scripts/check_base_template_parity.py --json
    python scripts/check_base_template_parity.py --verbose
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path

# The five platform-agnostic templates governed by the AGENTS.md lockstep rule,
# in canonical order (the first present file is the parity reference).
TEMPLATES_REL = "templates/ai-instructions"
LOCKSTEP_FILES = [
    "base-claude.md",
    "base-codex.md",
    "base-cursor.md",
    "base-gemini.md",
    "base-opencode.md",
]

# Section headings (by text, level-agnostic) that every lockstep file must
# carry. Derived from the intersection of all five files as they stand today.
REQUIRED_HEADINGS = [
    "{{PROJECT_NAME}}",
    "Tech Stack",
    "Project Layout",
    "Key Commands",
    "Non-Obvious Tooling",
    "{{PRIMARY_LANGUAGE}} Conventions",
    "Branching",
    "Communication Contract",
    "Documentation Layout",
    "Run and Verify",
    "Output Minimization",
    "End-of-Task Summary",
    "Construction Discipline",
    "Writing Discipline",
    "Autonomous Operation",
    "Consequential Decisions",
    "MCP Registry Policy",
    "Skill Discovery",
]

# Placeholder tokens that every lockstep file must carry (the shared install-
# time substitution surface). Derived from the intersection of all five files;
# claude-only tokens ({{AGENT_REGISTRY}}, {{SPENDING_CONTROLS}},
# {{ENV_VARS_REFERENCE}}, {{MCP_STATUS}}) are intentionally excluded.
REQUIRED_PLACEHOLDERS = [
    "{{PROJECT_NAME}}",
    "{{PROJECT_DESCRIPTION}}",
    "{{PRIMARY_LANGUAGE}}",
    "{{LANGUAGE_VERSION}}",
    "{{PACKAGE_MANAGER}}",
    "{{BUILD_TOOL}}",
    "{{TEST_FRAMEWORK}}",
    "{{LINT_TOOL}}",
    "{{PROJECT_STRUCTURE_BRIEF}}",
    "{{BUILD_CMD}}",
    "{{TEST_CMD}}",
    "{{LINT_CMD}}",
    "{{NON_OBVIOUS_TOOLING}}",
    "{{LANGUAGE_CONVENTIONS}}",
    "{{SKILL_INDEX}}",
]

# Section bodies that are byte-identical (after normalization) across all five
# files today and are platform-agnostic by intent. Their bodies MUST stay
# identical across the lockstep set -- this is the heart of the guard. Output
# Minimization is deliberately NOT here: base-claude.md carries a legitimate
# 5th bullet the other four do not.
INVARIANT_SECTIONS = [
    "Tech Stack",
    "Key Commands",
    "Branching",
    # v4.0.0: the live-response communication contract is platform-agnostic by
    # intent (it points at one installed style guide rather than restating it),
    # so it belongs in BOTH lists like End-of-Task Summary below: every lockstep
    # file must carry the heading, and the body must stay byte-identical so the
    # contract cannot drift on one platform.
    "Communication Contract",
    # v4.0.0 docs-lifespan: placement by lifespan is platform-agnostic and has
    # no valid per-platform variation. Require the heading and byte-lock the
    # body across the five lockstep templates.
    "Documentation Layout",
    # v3.15.10: the end-of-task summary rule is platform-agnostic by intent and
    # has no legitimate per-platform variation, unlike Output Minimization above
    # (base-claude.md carries a 5th bullet the other four do not). It therefore
    # belongs in BOTH lists: every lockstep file must carry the heading, and the
    # body must stay byte-identical so the rule cannot drift on one platform.
    "End-of-Task Summary",
    # v4.1.2: the pre-write construction ladder is platform-agnostic by intent
    # and has no legitimate per-platform variation. Require the heading and
    # byte-lock the body across the five lockstep templates. Coverage of the
    # other seven substantive templates lives in
    # tests/validators/test_construction_discipline_rule.py.
    "Construction Discipline",
    # v4.5.0: the writing-discipline rule (cliche prohibition, ASCII punctuation,
    # chatbot-leftover ban, and the self-check that binds live replies) is
    # platform-agnostic by intent and has no legitimate per-platform variation:
    # a cliche or an em-dash is a defect on every platform, and the block
    # governs the agent's own output rather than any platform feature. Require
    # the heading and byte-lock the body across the five lockstep templates.
    # Coverage of the other seven substantive templates lives in
    # tests/validators/test_writing_discipline_rule.py.
    "Writing Discipline",
    # v4.7.0: the autonomous-operation block (proceed on covered work, stop
    # only for destructive or scope-changing actions, report-and-stop on a
    # question, finish the last paragraph's promises, targeted edits, and the
    # user-over-skill precedence with disclosed deviation) is platform-agnostic
    # by intent and names no vendor, model, or API parameter. Require the
    # heading and byte-lock the body across the five lockstep templates.
    # Coverage of the other seven substantive templates lives in
    # tests/validators/test_autonomy_block_rule.py.
    "Autonomous Operation",
    "Consequential Decisions",
    "Run and Verify",
    "MCP Registry Policy",
]

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")


class TemplateError(Exception):
    """A present template file could not be read."""


def _normalized_lines(text: str) -> list[str]:
    """Split into lines with CRLF folded to LF and trailing whitespace removed."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return [line.rstrip() for line in text.split("\n")]


def _iter_headings(lines: list[str]) -> Iterator[tuple[int, str]]:
    """Yield (line_index, heading_text) for every ATX heading outside code fences."""
    in_fence = False
    for idx, line in enumerate(lines):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = _HEADING_RE.match(line)
        if match:
            yield idx, match.group(2)


def heading_texts(lines: list[str]) -> set[str]:
    """Return the set of heading texts (level-agnostic) present in the file."""
    return {text for _, text in _iter_headings(lines)}


def section_body(lines: list[str], heading_text: str) -> list[str] | None:
    """Return the normalized body lines of a section, or None if it is absent.

    The body runs from the line after the matching heading to the line before
    the next heading (or EOF), with leading and trailing blank lines stripped.
    Code-fence contents are preserved verbatim as body but never treated as a
    section boundary.
    """
    headings = list(_iter_headings(lines))
    for i, (idx, text) in enumerate(headings):
        if text != heading_text:
            continue
        start = idx + 1
        end = headings[i + 1][0] if i + 1 < len(headings) else len(lines)
        body = lines[start:end]
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
        return body
    return None


class Finding:
    """One parity violation in one file."""

    def __init__(self, category: str, file: str, detail: str) -> None:
        self.category = (
            category  # "missing-heading" | "missing-placeholder" | "block-divergence"
        )
        self.file = file
        self.detail = detail


def load_present(root: Path) -> dict[str, list[str]]:
    """Read every lockstep file that exists, keyed by filename in canonical order."""
    files: dict[str, list[str]] = {}
    for name in LOCKSTEP_FILES:
        path = root / TEMPLATES_REL / name
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:  # pragma: no cover - exercised only on IO failure
            raise TemplateError(f"cannot read {path}: {exc}") from exc
        files[name] = _normalized_lines(text)
    return files


def check_required_headings(files: dict[str, list[str]]) -> list[Finding]:
    """Flag any present file missing a required shared section heading."""
    findings: list[Finding] = []
    for name in LOCKSTEP_FILES:
        if name not in files:
            continue
        present = heading_texts(files[name])
        for required in REQUIRED_HEADINGS:
            if required not in present:
                findings.append(
                    Finding(
                        "missing-heading",
                        name,
                        f"missing required section heading: '{required}'",
                    )
                )
    return findings


def check_required_placeholders(files: dict[str, list[str]]) -> list[Finding]:
    """Flag any present file missing a required shared placeholder token."""
    findings: list[Finding] = []
    for name in LOCKSTEP_FILES:
        if name not in files:
            continue
        text = "\n".join(files[name])
        for token in REQUIRED_PLACEHOLDERS:
            if token not in text:
                findings.append(
                    Finding(
                        "missing-placeholder",
                        name,
                        f"missing required placeholder token: '{token}'",
                    )
                )
    return findings


def check_invariant_sections(files: dict[str, list[str]]) -> list[Finding]:
    """Flag any present file whose invariant-section body diverges from its peers."""
    findings: list[Finding] = []
    for section in INVARIANT_SECTIONS:
        bodies: dict[str, str] = {}
        for name in LOCKSTEP_FILES:
            if name not in files:
                continue
            body = section_body(files[name], section)
            if body is None:
                continue  # absence is reported by check_required_headings
            bodies[name] = "\n".join(body)
        if len(bodies) < 2:
            continue
        reference_name = next(n for n in LOCKSTEP_FILES if n in bodies)
        reference_body = bodies[reference_name]
        for name, body in bodies.items():
            if body != reference_body:
                findings.append(
                    Finding(
                        "block-divergence",
                        name,
                        (
                            f"section '{section}' body differs from "
                            f"{reference_name} (must stay identical across the "
                            "lockstep templates)"
                        ),
                    )
                )
    return findings


def run_checks(files: dict[str, list[str]]) -> list[Finding]:
    """Run every parity check and return the aggregated findings."""
    return [
        *check_required_headings(files),
        *check_required_placeholders(files),
        *check_invariant_sections(files),
    ]


def _emit_json(files: dict[str, list[str]], findings: list[Finding]) -> None:
    payload = {
        "in_parity": not findings,
        "present": list(files.keys()),
        "missing": [n for n in LOCKSTEP_FILES if n not in files],
        "findings": [
            {"category": f.category, "file": f.file, "detail": f.detail}
            for f in findings
        ],
    }
    print(json.dumps(payload, indent=2))


def _emit_text(
    files: dict[str, list[str]], findings: list[Finding], verbose: bool
) -> None:
    missing = [n for n in LOCKSTEP_FILES if n not in files]
    for finding in findings:
        print(f"DRIFT: {finding.file}: {finding.detail}", file=sys.stderr)
    if verbose or not findings:
        stream = sys.stderr if findings else sys.stdout
        print(
            f"base-template parity: {len(files)} of {len(LOCKSTEP_FILES)} "
            f"lockstep templates present ({TEMPLATES_REL})",
            file=stream,
        )
        for name in LOCKSTEP_FILES:
            state = "present" if name in files else "missing"
            print(f"  [{state:>7}] {name}", file=stream)
    if missing:
        print(
            f"note: {len(missing)} lockstep template(s) not present "
            f"({', '.join(missing)}); checked only the present files.",
            file=sys.stderr if findings else sys.stdout,
        )
    if findings:
        print(
            f"\ncheck_base_template_parity: {len(findings)} parity finding(s) "
            f"across {len(files)} present template(s). The five base-*.md files "
            "must stay in lockstep (AGENTS.md): apply the platform-agnostic edit "
            "to every one of them.",
            file=sys.stderr,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root to scan (default: the repo containing this script).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report on stdout (for CI).",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print every template's status."
    )
    args = parser.parse_args()

    root: Path = args.root.resolve()

    try:
        files = load_present(root)
    except TemplateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if len(files) < 2:
        if args.json:
            _emit_json(files, [])
        else:
            print(
                f"base-template parity: fewer than two lockstep templates "
                f"present under {TEMPLATES_REL} -- nothing to compare.",
                file=sys.stdout,
            )
        return 0

    findings = run_checks(files)

    if args.json:
        _emit_json(files, findings)
    else:
        _emit_text(files, findings, args.verbose)

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
