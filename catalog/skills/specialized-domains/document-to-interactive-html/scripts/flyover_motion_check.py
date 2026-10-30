#!/usr/bin/env python3
"""Optical-flow gate for the fly-over flight (0 to 8.2s) on the 30fps preview.

usage: python flyover_motion_check.py RUN      (reads RUN/out/preview from flyover_render.py preview)

Features are tracked frame to frame (Shi-Tomasi corners, pyramidal Lucas-Kanade) and the page
plane's motion is fitted as a homography with RANSAC, so lifted pieces moving on their own are
outliers rather than noise. From each homography:
  - speed down the page: the frame center's vertical displacement, converted to page px/s with
    the camera's distance and tilt from camera.json;
  - zoom: the local area scale at frame center (det of the Jacobian); above 1 = a zoom-in.
A median of raw flow is the wrong instrument: it reads 0 on any flat, textureless region and
reports a lifted piece's own growth as a zoom.

Exit 0 pass, 1 findings (a dip in the glide or a zoom-in), 2 unverified (missing dependency or frames).
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

FOCAL = 1880.0
CENTER = (720.0, 576.0)
FLIGHT_END = 8.2
CRUISE = (1.7, 7.2)
DIP = 0.05  # a frame more than 5% below its +-0.5s median is a dip
ZOOM_IN = 1.0005


def jacobian(hm, p):
    """Mapped point and 2x2 Jacobian of homography `hm` at point `p`."""
    import numpy as np  # noqa: PLC0415 - lazy

    x = np.array([p[0], p[1], 1.0])
    u = hm @ x
    q = u[:2] / u[2]
    return q, (hm[:2, :2] - np.outer(q, hm[2, :2])) / u[2]


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    try:
        import cv2  # noqa: PLC0415 - lazy
        import numpy as np  # noqa: PLC0415 - lazy
    except ImportError:
        print("UNVERIFIED: needs opencv-python-headless and numpy (install them in a project virtual environment)")
        return 2
    prev_dir = Path(argv[0]) / "out" / "preview"
    cams = json.loads((prev_dir / "camera.json").read_text(encoding="utf-8")) if (prev_dir / "camera.json").is_file() else None
    frames = sorted(prev_dir.glob("f*.png"))
    if not cams or len(frames) < 2:
        print(f"UNVERIFIED: no preview frames or camera.json in {prev_dir}")
        return 2
    fps = round(1 / (cams[1]["t"] - cams[0]["t"]))
    end = min(len(frames) - 1, int(FLIGHT_END * fps))
    rows = []
    prev = cv2.imread(str(frames[0]), cv2.IMREAD_GRAYSCALE)
    for i in range(1, end + 1):
        cur = cv2.imread(str(frames[i]), cv2.IMREAD_GRAYSCALE)
        pts = cv2.goodFeaturesToTrack(prev, maxCorners=3000, qualityLevel=0.005, minDistance=6, blockSize=7)
        speed, area = math.nan, math.nan
        if pts is not None and len(pts) >= 20:
            nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, cur, pts, None, winSize=(31, 31), maxLevel=4)
            good = st.ravel() == 1
            a, b = pts[good].reshape(-1, 2), nxt[good].reshape(-1, 2)
            if np.linalg.norm(b - a, axis=1).max() <= 0.05:
                speed, area = 0.0, 1.0
            else:
                hm, _ = cv2.findHomography(a, b, cv2.RANSAC, 1.0)
                if hm is not None:
                    q, jac = jacobian(hm, CENTER)
                    c = cams[i]
                    speed = -(q[1] - CENTER[1]) * c["d"] / (FOCAL * math.cos(c["th"])) * fps
                    area = float(np.linalg.det(jac))
        rows.append((i / fps, speed, area))
        prev = cur
    t, sp, ar = (np.array(col, dtype=float) for col in zip(*rows))
    findings = []
    cruise = (t >= CRUISE[0]) & (t <= CRUISE[1])
    for k in np.where(cruise)[0]:
        local = np.nanmedian(sp[max(0, k - fps // 2): k + fps // 2 + 1])
        if sp[k] < (1 - DIP) * local:
            findings.append(f"glide dips at {t[k]:.2f}s ({sp[k]:.0f} vs local {local:.0f} page px/s)")
    if np.nanmax(ar) > ZOOM_IN:
        k = int(np.nanargmax(ar))
        findings.append(f"zoom-in at {t[k]:.2f}s (center area scale {ar[k]:.5f})")
    print(f"flight 0-{FLIGHT_END}s at {fps}fps: cruise {np.nanmin(sp[cruise]):.0f}-{np.nanmax(sp[cruise]):.0f} "
          f"page px/s (median {np.nanmedian(sp[cruise]):.0f}); max center area scale {np.nanmax(ar):.5f}; "
          f"{int(np.isnan(sp).sum())} unmeasured frames")
    for f in findings[:12]:
        print("FINDING:", f)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
