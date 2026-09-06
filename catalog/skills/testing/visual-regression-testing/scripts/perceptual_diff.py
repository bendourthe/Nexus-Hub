#!/usr/bin/env python3
"""
perceptual_diff.py - Deterministic image perceptual-diff gate for the
visual-regression-testing skill.

Tier-3 bundled resource: invoked via the shell; the source is never read into the
context window. It compares a BASELINE image against a CURRENT image, optionally
writes a diff image, prints the difference score, and EXITS NON-ZERO when the
score exceeds a threshold - or when the two images differ in size, since a
dimension change is itself a visual regression (silently resizing to compare
would mask a real layout shift).

Difference metric: the mean normalized absolute pixel difference across the RGB
channels, in [0, 1] (0 = identical). Threshold defaults to 0.01 (1%).

Pillow is imported LAZILY with a clear `pip install Pillow` hint on ImportError,
so a machine without it degrades to a clear message and a non-zero exit rather
than a crash. ZERO-NETWORK: no socket / urllib / http / requests import.

Exit codes: 0 = within threshold, 1 = regression (over threshold or size
mismatch), 2 = file / decode error, 3 = Pillow not installed.

Usage:
    python perceptual_diff.py baseline.png current.png --diff out-diff.png --threshold 0.01
"""

from __future__ import annotations

import argparse
import sys


def perceptual_difference(
    baseline_path: str,
    current_path: str,
    diff_path: str | None = None,
    threshold: float = 0.01,
) -> tuple[int, float | None]:
    """Return (exit_code, score). score is None when it could not be computed."""
    try:
        from PIL import Image, ImageChops
    except ImportError:
        print(
            "error: Pillow is required. Install it with: pip install Pillow",
            file=sys.stderr,
        )
        return 3, None

    base = Image.open(baseline_path).convert("RGB")
    current = Image.open(current_path).convert("RGB")

    if base.size != current.size:
        print(
            f"SIZE MISMATCH: baseline {base.size} vs current {current.size} - "
            "a dimension change is a visual regression.",
            file=sys.stderr,
        )
        return 1, None

    diff = ImageChops.difference(base, current)
    if diff_path:
        diff.save(diff_path)

    # Mean normalized absolute difference: sum(i * count) over the per-channel
    # histograms, divided by the maximum possible total (255 per value).
    histogram = diff.histogram()
    total_abs = 0
    for channel in range(3):
        band = histogram[channel * 256 : (channel + 1) * 256]
        total_abs += sum(value * count for value, count in enumerate(band))
    num_values = base.size[0] * base.size[1] * 3
    score = total_abs / (255.0 * num_values) if num_values else 0.0

    return (1 if score > threshold else 0), score


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Perceptual image diff gate for visual regression."
    )
    parser.add_argument("baseline", help="baseline image path")
    parser.add_argument("current", help="current image path")
    parser.add_argument(
        "--diff", metavar="PATH", default=None, help="write a diff image to PATH"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.01,
        help="max mean normalized diff before failure (default 0.01 = 1%%)",
    )
    args = parser.parse_args(argv)

    try:
        code, score = perceptual_difference(
            args.baseline, args.current, args.diff, args.threshold
        )
    except (OSError, ValueError) as exc:
        print(f"error reading image: {exc}", file=sys.stderr)
        return 2

    if score is None:
        return code  # size mismatch (1) or Pillow missing (3), already reported

    status = "REGRESSED" if code == 1 else "ok"
    print(f"{status}: mean-diff {score:.5f} (threshold {args.threshold:.5f})")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
