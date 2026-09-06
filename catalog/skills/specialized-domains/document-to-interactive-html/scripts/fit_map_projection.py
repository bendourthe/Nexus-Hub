#!/usr/bin/env python3
"""Fit a lat/lon -> map-image pixel projection from landmark anchors.

Supports the geo-pin overlay path in references/figure-reconstruction.md
(part 5, path 2b): a slide shows a geographic base map whose location labels
were loose text boxes, so the label positions are unrecoverable - but the
labeled places are real and geocodable. Pins are placed from public city
coordinates through a projection CALIBRATED AGAINST THE MAP IMAGE ITSELF:
read 10+ landmark anchors off the image (lake centers, coastline notches,
border corners), feed them here, and paste the emitted JS into the page.

Why quadratic is the default: country-scale reference maps are usually conic
projections (Lambert/Albers), so a plain affine fit visibly fails at the map
edges (Pacific-coast cities land in the ocean while the center fits). A
quadratic in (lon, lat) absorbs the conic curvature over a continental extent
without needing the mapmaker's actual projection parameters. Fit quality is
judged by RENDERING the pins and grading them against the map's geography,
not by residuals alone - correct individual outliers with per-site nudges.

Anchors JSON: a list of [px_x, px_y, lat, lon, "label"] rows, pixel
coordinates in the image's NATURAL size.

Usage:
    python fit_map_projection.py anchors.json --width 1160 --height 712
    python fit_map_projection.py anchors.json --model affine

Stdlib-only; no network. Exit 0 on success, 2 on bad input.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _terms(lat: float, lon: float, model: str) -> list[float]:
    if model == "affine":
        return [1.0, lon, lat]
    return [1.0, lon, lat, lon * lat, lon * lon, lat * lat]


def _solve_least_squares(rows: list[list[float]], rhs: list[float]) -> list[float]:
    """Solve min ||A c - b|| via normal equations + Gaussian elimination."""
    n = len(rows[0])
    m = [
        [sum(rows[k][i] * rows[k][j] for k in range(len(rows))) for j in range(n)]
        for i in range(n)
    ]
    v = [sum(rows[k][i] * rhs[k] for k in range(len(rows))) for i in range(n)]
    for i in range(n):
        pivot = max(range(i, n), key=lambda r: abs(m[r][i]))
        m[i], m[pivot] = m[pivot], m[i]
        v[i], v[pivot] = v[pivot], v[i]
        if abs(m[i][i]) < 1e-12:
            raise ValueError("degenerate anchor set (anchors may be collinear)")
        for r in range(i + 1, n):
            f = m[r][i] / m[i][i]
            for c in range(i, n):
                m[r][c] -= f * m[i][c]
            v[r] -= f * v[i]
    coeff = [0.0] * n
    for i in range(n - 1, -1, -1):
        coeff[i] = (v[i] - sum(m[i][j] * coeff[j] for j in range(i + 1, n))) / m[i][i]
    return coeff


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fit a lat/lon -> pixel projection from landmark anchors."
    )
    parser.add_argument(
        "anchors",
        help="JSON file: list of [px_x, px_y, lat, lon, 'label'] rows "
        "(pixels in the image's natural size).",
    )
    parser.add_argument("--width", type=float, default=None,
                        help="Image natural width (emits a percent-based JS projPct).")
    parser.add_argument("--height", type=float, default=None,
                        help="Image natural height (emits a percent-based JS projPct).")
    parser.add_argument("--model", choices=("quadratic", "affine"),
                        default="quadratic",
                        help="Fit model (default quadratic; affine fails on conic maps).")
    args = parser.parse_args(argv)

    try:
        anchors = json.loads(Path(args.anchors).read_text(encoding="utf-8"))
        rows = [_terms(float(a[2]), float(a[3]), args.model) for a in anchors]
        xs = [float(a[0]) for a in anchors]
        ys = [float(a[1]) for a in anchors]
        labels = [str(a[4]) if len(a) > 4 else f"anchor {i}" for i, a in enumerate(anchors)]
    except (OSError, ValueError, IndexError, TypeError, json.JSONDecodeError) as exc:
        print(f"[fit_map_projection] bad anchors input: {exc}", file=sys.stderr)
        return 2

    minimum = 3 if args.model == "affine" else 6
    if len(anchors) < max(minimum, 8):
        print(
            f"[fit_map_projection] {len(anchors)} anchor(s) is too few - read at "
            f"least 8 (ideally 10+) landmarks spread across the map extent.",
            file=sys.stderr,
        )
        return 2

    try:
        cx = _solve_least_squares(rows, xs)
        cy = _solve_least_squares(rows, ys)
    except ValueError as exc:
        print(f"[fit_map_projection] {exc}", file=sys.stderr)
        return 2

    print(f"model: {args.model}")
    print("CX = [" + ",".join(f"{c:.6f}" for c in cx) + "]")
    print("CY = [" + ",".join(f"{c:.6f}" for c in cy) + "]")
    print("\nper-anchor residuals (px):")
    worst = 0.0
    for row, x, y, label in zip(rows, xs, ys, labels):
        fx = sum(c * t for c, t in zip(cx, row))
        fy = sum(c * t for c, t in zip(cy, row))
        err = max(abs(fx - x), abs(fy - y))
        worst = max(worst, err)
        print(f"  {label:32s} fit ({fx:7.1f},{fy:7.1f})  err ({fx - x:+6.1f},{fy - y:+6.1f})")
    print(f"\nworst residual: {worst:.1f}px")
    if worst > 25:
        print(
            "residuals above ~25px usually mean a mis-read anchor or (for affine) "
            "a conic source map - re-read the outlier anchors or use --model quadratic.",
            file=sys.stderr,
        )

    if args.width and args.height:
        terms_js = (
            "[1, lon, lat]" if args.model == "affine"
            else "[1, lon, lat, lon*lat, lon*lon, lat*lat]"
        )
        print("\n/* paste-ready projection (percent coordinates of the map image) */")
        print("var CX = [" + ",".join(f"{c:.6f}" for c in cx) + "];")
        print("var CY = [" + ",".join(f"{c:.6f}" for c in cy) + "];")
        print("function projPct(lat,lon){")
        print(f"  var t = {terms_js}, x=0, y=0;")
        print("  for(var i=0;i<t.length;i++){ x += CX[i]*t[i]; y += CY[i]*t[i]; }")
        print(f"  return [x/{args.width:g}*100, y/{args.height:g}*100];")
        print("}")
        print("/* verify by RENDERING the pins against the map's geography; nudge outliers per-site. */")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
