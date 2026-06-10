"""Compression accuracy-regression harness for nexus-context-compressor.

A top-level harness package (sibling of ``src/`` and ``tests/``) that proves the
engine's compression preserves answer quality before aggressive ratios ship, and
gates that property in CI. See :mod:`evals.runner` for the full design.

Run from the package root::

    cd extensions/nexus-context-compressor && python -m evals --check
"""

from __future__ import annotations

from .runner import (
    BASELINE_PATH,
    FIXTURES_DIR,
    EvalReport,
    FixtureScore,
    check_baseline,
    load_baseline,
    main,
    render_json,
    render_report,
    run_eval,
)

__all__ = [
    "BASELINE_PATH",
    "FIXTURES_DIR",
    "EvalReport",
    "FixtureScore",
    "check_baseline",
    "load_baseline",
    "main",
    "render_json",
    "render_report",
    "run_eval",
]
