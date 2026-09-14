#!/usr/bin/env python3
"""Validate that a build RECORDED its unmeasurable decisions. Never judge them.

Some rules in this skill cannot be checked mechanically without an authorship or
beauty detector, which this catalog forbids. Whether prose was cut enough,
whether a composition is balanced, whether a figure is conceptual or evidential:
no measurement settles any of these.

The alternative is not to drop them to prose an agent can skip in silence. It is
to require that the decision was MADE AND RECORDED. A missing or empty record
fails; a complete record passes. That gates the failure mode that actually
matters, which is silence, without fabricating a judgement the machine cannot
make.

**This script never scores content.** It does not read prose quality, count
adjectives, or rate a figure. Every check here answers "is this recorded?" and
none answers "is this good?". A future edit that adds a quality heuristic has
turned this into the beauty detector the plan forbids, and
`test_attestation_never_scores_content` exists to fail when that happens.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

EXIT_PASS = 0
EXIT_INCOMPLETE = 1
EXIT_UNREADABLE = 2

FIGURE_CLASSES = ("illustrative", "evidential")

# Each entry: the record key, and what a complete entry must name. The VALUE is
# never inspected for quality - only for presence and non-emptiness.
REQUIRED_SECTIONS = {
    "figures": "every figure classified illustrative or evidential",
    "content_cuts": "what was cut from the first draft, and why",
    "code_claims": "every claim about code behaviour, with the file and function it was verified against",
    "authorship": "the AI-tell review that cannot be measured",
}


def _nonempty(value: Any) -> bool:
    """Present and not empty. Deliberately not 'good'."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def check(record: dict[str, Any]) -> list[str]:
    """Return one finding per incomplete entry. An empty list means complete."""
    findings: list[str] = []

    for key, what in REQUIRED_SECTIONS.items():
        if key not in record:
            findings.append(f"missing section {key!r}: must record {what}")
        elif not _nonempty(record[key]):
            findings.append(f"empty section {key!r}: must record {what}")

    # --- figures: classified, and an evidential series names its computation
    figures = record.get("figures")
    if isinstance(figures, list):
        for index, figure in enumerate(figures):
            if not isinstance(figure, dict):
                findings.append(f"figures[{index}] is not an object")
                continue
            fid = figure.get("id") or f"index {index}"
            klass = figure.get("class")
            if klass not in FIGURE_CLASSES:
                findings.append(
                    f"figure {fid}: class must be one of {list(FIGURE_CLASSES)}, "
                    f"got {klass!r}"
                )
                continue
            if klass == "evidential":
                series = figure.get("series")
                if not _nonempty(series) or not isinstance(series, list):
                    findings.append(
                        f"figure {fid}: evidential figures must list their series"
                    )
                    continue
                for s_index, entry in enumerate(series):
                    if not isinstance(entry, dict) or not _nonempty(entry.get("source")):
                        findings.append(
                            f"figure {fid}: series[{s_index}] names no source; a "
                            f"series with no computation behind it is a hardcoded "
                            f"list chosen to look right"
                        )
            else:
                # An illustrative figure labels the RULE, not the number. The
                # record says so explicitly; the script does not read the labels
                # and judge them.
                if not _nonempty(figure.get("labels_the_rule_not_the_number")):
                    findings.append(
                        f"figure {fid}: an illustrative figure must attest that it "
                        f"labels the rule rather than a measured value"
                    )

    # --- code claims: each names a file AND a function, verified this session
    claims = record.get("code_claims")
    if isinstance(claims, list):
        for index, claim in enumerate(claims):
            if not isinstance(claim, dict):
                findings.append(f"code_claims[{index}] is not an object")
                continue
            missing = [f for f in ("claim", "file", "function") if not _nonempty(claim.get(f))]
            if missing:
                findings.append(
                    f"code_claims[{index}]: missing {missing}; a claim about how "
                    f"code behaves names where it was verified"
                )

    # --- shared numbers: a figure and its prose derive from ONE source
    for index, shared in enumerate(record.get("shared_numbers", []) or []):
        if not isinstance(shared, dict) or not _nonempty(shared.get("source")):
            findings.append(
                f"shared_numbers[{index}]: names no single source; a number quoted "
                f"in both a figure and its prose must come from one derivation"
            )

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="the attestation JSON to validate")
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    args = parser.parse_args(argv)

    if not args.record.is_file():
        print(f"attestation: no record at {args.record}", file=sys.stderr)
        print(
            "A build with no attestation has not made these decisions, or has "
            "not recorded them. Both fail.",
            file=sys.stderr,
        )
        return EXIT_UNREADABLE
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"attestation: unreadable record: {exc}", file=sys.stderr)
        return EXIT_UNREADABLE
    if not isinstance(record, dict):
        print("attestation: the record must be an object", file=sys.stderr)
        return EXIT_UNREADABLE

    findings = check(record)
    if args.json:
        print(json.dumps(
            {"status": "incomplete" if findings else "complete", "findings": findings},
            indent=2,
        ))
    else:
        for finding in findings:
            print(f"attestation: {finding}")
        print(
            f"attestation: {'INCOMPLETE' if findings else 'complete'} "
            f"({len(findings)} finding(s))"
        )
    return EXIT_INCOMPLETE if findings else EXIT_PASS


if __name__ == "__main__":
    sys.exit(main())
