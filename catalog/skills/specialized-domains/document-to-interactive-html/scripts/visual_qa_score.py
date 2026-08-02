#!/usr/bin/env python3
"""visual_qa_score.py - deterministic STRUCTURAL scorer for the presentify
visual-QA gate (Phase 5).

Scores a generated presentify `.html` against the STRUCTURAL subset of
`references/visual-qa-rubric.md` - the checks that need no human eye: full-width
band width, the image-sizing caps, annotated-overlay well-formedness, imagery
integration count, and layout / offline integrity. It is the headless-optional
structural-review path the Step 9 loop degrades to when no browser (or no agent
vision) is available, and the target the Phase 5 tests seed defects against.

The AGENT-VISION criteria (crop of meaningful content, dead space, annotation
placement vs the source, imagery relevance, contrast / legibility) are NOT
scored here; they are the agent's screenshot judgment. A pass from this scorer
is a "structural-only" pass, recorded as such.

LOCAL and OFFLINE by construction: it reads a local file and computes from the
markup / computed CSS, importing no network module and making no request.

Usage:
    python visual_qa_score.py out.html
    python visual_qa_score.py out.html --expect-images 2
    python visual_qa_score.py out.html --aspect full --json

Exit codes:
    0  page passes the structural bar (no HIGH-severity finding).
    1  a HIGH-severity structural finding is open.
    2  usage error (file not found / bad arguments).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

FULL_WIDTH_MIN = 0.95
HERO_CAP = "max-height: 80vh"
OBJECT_FIT = "object-fit: contain"

_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_PAGE_MAX_RE = re.compile(r"--page-max:\s*([^;]+);")
_GUTTER_RE = re.compile(r"--gutter:\s*([^;]+);")
_ASPECT_RE = re.compile(r'data-aspect="([^"]*)"')
_ZOOM_RE = re.compile(r"\bzoom:\s*[0-9]")
# Off-host fetch constructs (mirror build_presentation.assert_no_external).
_FETCH_RE = [
    re.compile(
        r"""\b(?:src|href|poster|cite|action|formaction|xlink:href)\s*"""
        r"""=\s*["']?\s*(?:https?:)?//""",
        re.IGNORECASE,
    ),
    re.compile(r"@import\b", re.IGNORECASE),
    re.compile(r"""url\(\s*["']?\s*(?:https?:)?//""", re.IGNORECASE),
    re.compile(r"""<link\b[^>]*\brel\s*=\s*["']?stylesheet""", re.IGNORECASE),
    re.compile(r"<script\b[^>]*\bsrc\s*=", re.IGNORECASE),
]


def _len_px(token: str, viewport: int, root_font: int = 16) -> float:
    """Resolve a simple CSS length (px / rem / vw / %) or a clamp() to pixels."""
    token = token.strip()
    if token.startswith("clamp(") and token.endswith(")"):
        low, pref, high = (
            _len_px(part, viewport, root_font)
            for part in token[len("clamp(") : -1].split(",")
        )
        return max(low, min(pref, high))
    if token.endswith("px"):
        return float(token[:-2])
    if token.endswith("rem"):
        return float(token[:-3]) * root_font
    if token.endswith("vw"):
        return float(token[:-2]) / 100.0 * viewport
    if token.endswith("%"):
        return float(token[:-1]) / 100.0 * viewport
    try:
        return float(token)
    except ValueError:
        return 0.0


def band_fraction(html: str, viewport: int = 1920) -> float | None:
    """Heuristic widest-content-band fraction from the injected `--page-max` /
    `--gutter` canvas vars, or None when they are absent."""
    page_max_match = _PAGE_MAX_RE.search(html)
    gutter_match = _GUTTER_RE.search(html)
    if not page_max_match or not gutter_match:
        return None
    gutter = _len_px(gutter_match.group(1), viewport)
    available = viewport - 2 * gutter
    page_max = page_max_match.group(1).strip()
    if page_max == "100%":
        band = available
    else:
        band = min(_len_px(page_max, viewport), available)
    return band / viewport


def _finding(
    criterion: str,
    status: str,
    kind: str,
    evidence: str,
    severity: str | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "segment": "page (structural)",
        "criterion": criterion,
        "status": status,
        "kind": kind,
        "evidence": evidence,
    }
    if severity:
        entry["severity"] = severity
    return entry


def score_html(
    html: str,
    *,
    aspect: str | None = None,
    expect_images: int | None = None,
    viewport: int = 1920,
) -> dict[str, Any]:
    """Score the HTML text against the structural rubric subset. Returns a dict
    with the per-criterion findings, the high-severity count, and the binary
    page-level pass bar (no open high-severity finding)."""
    stripped = _COMMENT_RE.sub("", html)
    findings: list[dict[str, Any]] = []

    # 1. Full-width compliance (Phase 1).
    aspect_match = _ASPECT_RE.search(html)
    resolved_aspect = aspect or (aspect_match.group(1) if aspect_match else None)
    if resolved_aspect == "full":
        frac = band_fraction(html, viewport)
        if frac is None:
            findings.append(
                _finding("full-width", "fail", "structural",
                         "no --page-max/--gutter canvas vars found", "high")
            )
        elif frac < FULL_WIDTH_MIN:
            findings.append(
                _finding("full-width", "fail", "structural",
                         f"widest band {frac:.3f} of viewport (< {FULL_WIDTH_MIN})",
                         "high")
            )
        else:
            findings.append(
                _finding("full-width", "pass", "structural",
                         f"widest band {frac:.3f} of viewport")
            )
        if "transform: scale(" in stripped or _ZOOM_RE.search(stripped):
            findings.append(
                _finding("full-width", "fail", "structural",
                         "global zoom / transform:scale simulates width", "high")
            )
    else:
        findings.append(
            _finding("full-width", "n/a", "structural",
                     f"aspect={resolved_aspect or 'unknown'} (not full-width)")
        )

    # 2. Image sizing caps (Phase 2), meaningful only when images are present.
    has_figures = "<figure" in html or "data:image" in html
    if has_figures:
        missing = [cap for cap in (HERO_CAP, OBJECT_FIT) if cap not in html]
        if missing:
            findings.append(
                _finding("image-sizing", "fail", "structural",
                         f"missing image caps: {', '.join(missing)}", "high")
            )
        else:
            findings.append(
                _finding("image-sizing", "pass", "structural",
                         "hero max-height + object-fit: contain present")
            )
    else:
        findings.append(
            _finding("image-sizing", "n/a", "structural", "no images / figures")
        )

    # 3. Annotation fidelity (Phase 3), only when an annotated figure is present.
    annotated = html.count('class="fig-annotated"')
    if annotated:
        regions = html.count('class="fig-region"')
        has_toggle = 'class="fig-view-original"' in html
        if regions == 0:
            findings.append(
                _finding("annotation-fidelity", "fail", "structural",
                         f"{annotated} annotated figure(s) but 0 overlay regions "
                         "(dropped overlay)", "high")
            )
        elif not has_toggle:
            findings.append(
                _finding("annotation-fidelity", "fail", "structural",
                         "overlay present but no view-original toggle", "medium")
            )
        else:
            findings.append(
                _finding("annotation-fidelity", "pass", "structural",
                         f"{annotated} annotated figure(s), {regions} region(s), "
                         "view-original toggle present")
            )
    else:
        findings.append(
            _finding("annotation-fidelity", "n/a", "structural",
                     "no annotated figures")
        )

    # 4. Imagery integration (Phase 4), only when an expectation is supplied.
    if expect_images is not None:
        count = len(re.findall(r"data:image/", html))
        if count < expect_images:
            findings.append(
                _finding("imagery-integration", "fail", "structural",
                         f"{count} embedded image(s), expected >= {expect_images}",
                         "high")
            )
        else:
            findings.append(
                _finding("imagery-integration", "pass", "structural",
                         f"{count} embedded image(s) (>= {expect_images})")
            )
    else:
        findings.append(
            _finding("imagery-integration", "n/a", "structural",
                     "no integration expectation (procedural / non-consented run)")
        )

    # 5. Readability / layout integrity (structural subset: offline + well-formed).
    external = next((p.pattern for p in _FETCH_RE if p.search(stripped)), None)
    if external:
        findings.append(
            _finding("readability-layout", "fail", "structural",
                     "off-host fetch construct found (not offline)", "high")
        )
    elif "</html>" not in html.lower():
        findings.append(
            _finding("readability-layout", "fail", "structural",
                     "document is not well-formed (no </html>)", "high")
        )
    else:
        findings.append(
            _finding("readability-layout", "pass", "structural",
                     "offline and well-formed")
        )

    high = sum(1 for finding in findings if finding.get("severity") == "high")
    return {
        "mode": "structural",
        "findings": findings,
        "high_severity": high,
        "page_pass": high == 0,
        "note": (
            "structural-only: agent-vision criteria (crop, dead space, "
            "annotation placement vs source, imagery relevance, contrast) "
            "were not graded"
        ),
    }


def score_file(path: str | Path, **kwargs: Any) -> dict[str, Any]:
    return score_html(Path(path).read_text(encoding="utf-8"), **kwargs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic STRUCTURAL scorer for the presentify "
        "visual-QA gate (Phase 5)."
    )
    parser.add_argument("html", help="generated .html to score")
    parser.add_argument(
        "--aspect", default=None,
        help="override the resolved aspect (else read from data-aspect)"
    )
    parser.add_argument(
        "--expect-images", type=int, default=None,
        help="minimum embedded images expected (a consented stock/mix run)"
    )
    parser.add_argument("--viewport", type=int, default=1920)
    parser.add_argument("--json", action="store_true", help="emit the result as JSON")
    args = parser.parse_args(argv)

    path = Path(args.html)
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2
    result = score_file(
        path, aspect=args.aspect, expect_images=args.expect_images,
        viewport=args.viewport,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for finding in result["findings"]:
            sev = f" [{finding['severity']}]" if finding.get("severity") else ""
            print(
                f"{finding['status'].upper():4} {finding['criterion']}{sev}: "
                f"{finding['evidence']}",
                file=sys.stderr,
            )
        verdict = "PASS" if result["page_pass"] else "FAIL"
        print(
            f"{verdict} (structural-only; {result['high_severity']} high-severity)",
            file=sys.stderr,
        )
    return 0 if result["page_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
