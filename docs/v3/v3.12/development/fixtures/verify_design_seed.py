#!/usr/bin/env python3
"""Verify the Phase 4 design-entropy engine (scripts/design_seed.py).

Checks: sequential same-preset divergence (the 2-of-3-axes rejection rule),
hue spread, light/dark coverage, --seed reproducibility, --commit round-trip
with the history cap, corrupt-history recovery, preset pool subsets, and
attractor unreachability. Prints PASS/FAIL per check; exits non-zero on any
failure. Uses a temp directory - never touches the real user history.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
SCRIPT = (
    REPO
    / "catalog"
    / "skills"
    / "specialized-domains"
    / "document-to-interactive-html"
    / "scripts"
    / "design_seed.py"
)

FAILURES: list = []


def check(name: str, condition: bool, detail: str = "") -> None:
    print(
        f"{'PASS' if condition else 'FAIL'}  {name}"
        + (f"  [{detail}]" if detail and not condition else "")
    )
    if not condition:
        FAILURES.append(name)


def run(args: list) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        check=False,
    )


def roll(
    out: Path, history: Path, preset: str = "technical", seed: int | None = None
) -> dict:
    args = ["--preset", preset, "--history", str(history), "-o", str(out)]
    if seed is not None:
        args += ["--seed", str(seed)]
    result = run(args)
    assert result.returncode == 0, result.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def triple(brief: dict) -> tuple:
    return (
        brief["hue_family"],
        brief["layout_signature"]["name"],
        brief["type"]["voice"],
    )


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="design-seed-verify-"))
    history = tmp / "history.json"

    # 1-3. Five sequential committed same-preset runs: divergence rule holds.
    briefs: list = []
    for index in range(5):
        out = tmp / f"brief{index}.json"
        brief = roll(out, history, "technical")
        result = run(["--commit", str(out), "--history", str(history)])
        assert result.returncode == 0, result.stderr
        briefs.append(brief)
    ok = True
    for index in range(1, 5):
        recent = briefs[max(0, index - 3) : index]
        candidate = briefs[index]
        for prior in recent:
            shared = sum(1 for a, b in zip(triple(candidate), triple(prior)) if a == b)
            if shared >= 2:
                ok = False
    check("sequential runs never share 2+ of {hue, layout, voice}", ok)
    hues = {b["hue_family"] for b in briefs}
    check("5 runs span 4+ hue families", len(hues) >= 4, str(hues))

    # 4. Seed reproducibility (fresh histories so state matches).
    h_a, h_b = tmp / "ha.json", tmp / "hb.json"
    brief_a = roll(tmp / "a.json", h_a, "creative", seed=42)
    brief_b = roll(tmp / "b.json", h_b, "creative", seed=42)
    check("--seed 42 reproduces an identical brief", brief_a == brief_b)
    brief_c = roll(tmp / "c.json", h_b, "creative", seed=43)
    check("a different seed yields a different brief", brief_b != brief_c)

    # 5. History cap: 45 commits keep only the newest 40.
    for _ in range(40):
        result = run(["--commit", str(tmp / "brief0.json"), "--history", str(history)])
        assert result.returncode == 0
    entries = json.loads(history.read_text(encoding="utf-8"))["entries"]
    check("history capped at 40 entries", len(entries) == 40, str(len(entries)))

    # 6. Corrupt history degrades to a fresh start (warning, exit 0).
    bad = tmp / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    result = run(
        ["--preset", "corporate", "--history", str(bad), "-o", str(tmp / "d.json")]
    )
    check(
        "corrupt history: warning + fresh roll (exit 0)",
        result.returncode == 0 and "starting fresh" in result.stderr,
        result.stderr[-200:],
    )

    # 7-8. Preset subsets + light/dark coverage over 60 seeded rolls.
    tech_ok, variants = True, set()
    allowed_moods = {
        "cool-clinical",
        "high-contrast-editorial",
        "muted-earthy",
        "duotone-graphic",
        "warm-paper",
        "deep-luxe",
    }
    allowed_voices = {
        "mono-technical",
        "geometric-sans-modern",
        "grotesk-editorial",
        "mixed-contrast",
        "slab-confident",
    }
    for seed in range(60):
        brief = roll(tmp / "s.json", tmp / f"hs{seed}.json", "technical", seed=seed)
        variants.add(brief["base_variant"])
        if brief["mood"] not in allowed_moods:
            tech_ok = False
        if brief["type"]["voice"] not in allowed_voices:
            tech_ok = False
    check("technical preset stays within its mood/voice subsets (60 rolls)", tech_ok)
    check(
        "both light and dark bases appear across the sample",
        variants == {"light", "dark"},
        str(variants),
    )

    # 9. Attractor unreachable outside surprise: dark + amber-ember +
    # mono-technical never rolls together under the three named presets.
    attractor_seen = False
    for seed in range(80):
        for preset in ("technical", "corporate", "creative"):
            brief = roll(
                tmp / "t.json", tmp / f"ht{preset}{seed}.json", preset, seed=seed
            )
            if (
                brief["base_variant"] == "dark"
                and brief["hue_family"] == "amber-ember"
                and brief["type"]["voice"] == "mono-technical"
            ):
                attractor_seen = True
    check(
        "attractor combo unreachable under named presets (240 rolls)",
        not attractor_seen,
    )

    # 10. Palette integrity: every brief carries concrete hexes + CSS stacks.
    brief = roll(tmp / "p.json", tmp / "hp.json", "surprise", seed=7)
    palette_ok = all(
        isinstance(brief["palette"].get(key), str)
        and brief["palette"][key].startswith("#")
        for key in ("base", "surface", "ink", "accent", "accent_2")
    )
    check(
        "brief carries concrete hex palette + type stacks + summary",
        palette_ok and "," in brief["type"]["heading"] and brief["summary"],
    )

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) FAILED: {', '.join(FAILURES)}")
        return 1
    print("Design-entropy engine: all checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
