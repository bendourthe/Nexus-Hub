"""nexus-code-search evaluation harness.

Synthetic small-codebase fixtures + a runner that scores each MCP tool
against ground-truth answer keys. Produces a Markdown report (recall /
precision per tool, per fixture). Local-only by policy.

Usage:
    python -m nexus_code_search.eval.runner [--fixtures path/to/fixtures] \\
        [--out report.md]
"""

from __future__ import annotations

from nexus_code_search.eval.runner import EvalResult, run_eval

__all__ = ["EvalResult", "run_eval"]
