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
def _repo_root(start: Path) -> Path:
    """Walk up to the repository root instead of hand-counting parent depth.

    A fixed ``parents[N]`` silently breaks whenever the file moves a level, and
    the v4.0.0 docs migration moved this tree one level deeper. Anchoring on a
    marker that only the root carries makes the location irrelevant.
    """
    for candidate in [start, *start.parents]:
        if (candidate / "AGENTS.md").is_file() and (candidate / "catalog").is_dir():
            return candidate
    raise RuntimeError(f"repository root not found above {start}")

REPO = _repo_root(HERE)
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
    # Hue spread is asserted further down, over the 60 seeded rolls, NOT over
    # these five. Five unseeded draws from 12 families land on 3-or-fewer
    # distinct families about 14% of the time (200k-trial simulation), and the
    # divergence rule above does not prevent it -- it only forbids sharing 2+ of
    # {hue, layout, voice} with the last three, so a hue may legitimately repeat.
    # This check therefore failed roughly one run in seven while claiming the
    # engine's hue spread was broken. It is the only distributional property in
    # this file that was measured on a sample too small to support it.

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

    # 7-8. Preset subsets + light/dark coverage + hue spread over 60 seeded rolls.
    tech_ok, variants, hues = True, set(), set()
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
        hues.add(brief["hue_family"])
        if brief["mood"] not in allowed_moods:
            tech_ok = False
        if brief["type"]["voice"] not in allowed_voices:
            tech_ok = False
    check("technical preset stays within its mood/voice subsets (60 rolls)", tech_ok)
    # Reuses the rolls above, so this costs no extra subprocess. Seeded 0..59, so
    # it is deterministic rather than merely large: the same 60 briefs every run.
    # Measured spread is 12 of 12 families, so the >=8 threshold leaves four
    # families of slack -- enough that adding or reweighting a family does not
    # trip it, while still failing if the engine collapses toward a few hues.
    # Note this samples the CONSTRAINED "technical" preset, which makes it the
    # stricter claim: even a preset-restricted sample reaches every family.
    check(
        "60 seeded rolls span 8+ hue families",
        len(hues) >= 8,
        f"{len(hues)} distinct: {sorted(hues)}",
    )
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
