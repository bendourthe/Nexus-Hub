#!/usr/bin/env python3
"""
design_seed.py - Seeded design-entropy sampler for the
document-to-interactive-html skill.

Turns "be different this time" into a mechanical roll: samples a complete
design brief (palette, type voice, layout signature, motion personality,
signature move) from curated axis pools, constrained per preset, seeded from
os.urandom by default (reproducible with --seed), and kept DISTANT from
recent runs via a persisted history file - a candidate sharing 2 or more of
{hue family, layout signature, type voice} with any of the last 3 committed
runs is rejected outright.

The brief is a STARTING POINT the agent adapts to the content; this script
never writes HTML, makes no network call, and uses the standard library only.

Usage:
    python design_seed.py --preset technical -o brief.json
    python design_seed.py --preset surprise --seed 42 -o brief.json
    python design_seed.py --commit brief.json [--source-hash HEX]

After the run actually uses the brief, call --commit so the history advances
(default history: ~/.nexus-hub/state/presentify-design-history.json).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

DEFAULT_HISTORY = (
    Path.home() / ".nexus-hub" / "state" / "presentify-design-history.json"
)
HISTORY_CAP = 40
RECENT_WINDOW = 3  # reject against this many most-recent runs
TRIPLE_AXES = ("hue_family", "layout_signature", "type_voice")
ATTRACTOR_SURPRISE_ODDS = 0.05  # the default look is a rare deliberate pick

# --- axis pools --------------------------------------------------------------
# Each hue family carries a LIGHT and a DARK base variant plus two accents, so
# preset constraints never collapse the light/dark axis.

HUE_FAMILIES: dict = {
    "crimson": {
        "light": {"base": "#faf6f4", "surface": "#f1e4e0", "ink": "#33201d"},
        "dark": {"base": "#251316", "surface": "#331c20", "ink": "#f4e8e6"},
        "accents": ["#a62639", "#3f7d6c"],
    },
    "terracotta": {
        "light": {"base": "#faf5ef", "surface": "#f0e2d4", "ink": "#3a2a1e"},
        "dark": {"base": "#2b1d14", "surface": "#3a2a1e", "ink": "#f3e9df"},
        "accents": ["#c05b2e", "#48628a"],
    },
    "amber-ember": {
        "light": {"base": "#fbf7ee", "surface": "#f3e8cf", "ink": "#332a17"},
        "dark": {"base": "#211a0e", "surface": "#2f2716", "ink": "#f4edda"},
        "accents": ["#d99021", "#5c5470"],
    },
    "olive-moss": {
        "light": {"base": "#f8f8f0", "surface": "#e9ead6", "ink": "#282b1c"},
        "dark": {"base": "#1e2015", "surface": "#2b2e1e", "ink": "#eef0e0"},
        "accents": ["#7a8450", "#a4553f"],
    },
    "forest": {
        "light": {"base": "#f4f8f4", "surface": "#dfeadf", "ink": "#1c2b20"},
        "dark": {"base": "#12211a", "surface": "#1b2f24", "ink": "#e4efe7"},
        "accents": ["#2f6d4f", "#c98a3d"],
    },
    "teal": {
        "light": {"base": "#f2f8f8", "surface": "#dcebeb", "ink": "#173033"},
        "dark": {"base": "#0f2427", "surface": "#173438", "ink": "#dfeeef"},
        "accents": ["#2a7f83", "#b6534e"],
    },
    "cyan-slate": {
        "light": {"base": "#f4f7fa", "surface": "#e0e9f0", "ink": "#1e2b33"},
        "dark": {"base": "#14202a", "surface": "#1d2e3a", "ink": "#e4edf3"},
        "accents": ["#3a7ca5", "#c47f3d"],
    },
    "cobalt": {
        "light": {"base": "#f5f6fb", "surface": "#e2e6f4", "ink": "#1d2340"},
        "dark": {"base": "#141a33", "surface": "#1d2547", "ink": "#e6e9f6"},
        "accents": ["#3552a5", "#b8963f"],
    },
    "indigo": {
        "light": {"base": "#f6f5fb", "surface": "#e6e3f3", "ink": "#241f3d"},
        "dark": {"base": "#191430", "surface": "#241d42", "ink": "#e9e6f5"},
        "accents": ["#5246a5", "#3f8464"],
    },
    "violet": {
        "light": {"base": "#f9f5fa", "surface": "#efe2f1", "ink": "#31203a"},
        "dark": {"base": "#221430", "surface": "#301d42", "ink": "#f0e6f4"},
        "accents": ["#7d4b9e", "#98803a"],
    },
    "plum-magenta": {
        "light": {"base": "#faf4f8", "surface": "#f1e0ec", "ink": "#361f30"},
        "dark": {"base": "#28131f", "surface": "#391b2d", "ink": "#f4e6ef"},
        "accents": ["#a04476", "#3d7a70"],
    },
    "rose-blush": {
        "light": {"base": "#fbf5f5", "surface": "#f4e3e3", "ink": "#38221f"},
        "dark": {"base": "#2a1616", "surface": "#3a1f1f", "ink": "#f6e9e8"},
        "accents": ["#c26565", "#4f6d8a"],
    },
}

MOODS = [
    "warm-paper",
    "cool-clinical",
    "high-contrast-editorial",
    "muted-earthy",
    "saturated-playful",
    "duotone-graphic",
    "soft-pastel",
    "deep-luxe",
]

NEUTRAL_TEMPERATURES = ["warm", "cool", "neutral"]

TYPE_VOICES: dict = {
    "serif-display-editorial": {
        "heading": "Georgia, 'Iowan Old Style', 'Times New Roman', serif",
        "body": "Georgia, 'Times New Roman', serif",
        "mono": "Consolas, 'SF Mono', Menlo, monospace",
    },
    "geometric-sans-modern": {
        "heading": "'Segoe UI', -apple-system, 'Helvetica Neue', Arial, sans-serif",
        "body": "'Segoe UI', -apple-system, 'Helvetica Neue', Arial, sans-serif",
        "mono": "'Cascadia Code', Consolas, Menlo, monospace",
    },
    "humanist-warm": {
        "heading": "'Trebuchet MS', 'Segoe UI', Verdana, sans-serif",
        "body": "Verdana, 'Segoe UI', Geneva, sans-serif",
        "mono": "Consolas, Menlo, monospace",
    },
    "mono-technical": {
        "heading": "Consolas, 'Cascadia Code', 'SF Mono', Menlo, monospace",
        "body": "'Segoe UI', -apple-system, Arial, sans-serif",
        "mono": "Consolas, 'Cascadia Code', Menlo, monospace",
    },
    "slab-confident": {
        "heading": "Rockwell, 'Roboto Slab', 'Courier New', serif",
        "body": "'Segoe UI', Arial, sans-serif",
        "mono": "Consolas, Menlo, monospace",
    },
    "mixed-contrast": {
        "heading": "Georgia, 'Times New Roman', serif",
        "body": "'Segoe UI', -apple-system, Arial, sans-serif",
        "mono": "Consolas, Menlo, monospace",
    },
    "classical-humanist-serif": {
        "heading": "'Palatino Linotype', Palatino, 'Book Antiqua', serif",
        "body": "'Palatino Linotype', Palatino, Georgia, serif",
        "mono": "Consolas, Menlo, monospace",
    },
    "grotesk-editorial": {
        "heading": "'Arial Black', 'Segoe UI', 'Helvetica Neue', sans-serif",
        "body": "Arial, 'Helvetica Neue', 'Segoe UI', sans-serif",
        "mono": "Consolas, Menlo, monospace",
    },
}

LAYOUT_SIGNATURES: dict = {
    "asymmetric-split": "a persistent narrow rail (nav/meta) beside a wide "
    "content column; the split never centers",
    "editorial-grid-pull-elements": "a column grid with pull-quotes, margin "
    "notes, and figures breaking the measure",
    "full-bleed-bands": "alternating full-width tinted bands; content width "
    "varies per band",
    "sidebar-anchored": "a sticky sidebar carrying nav + key stats; content "
    "scrolls past it",
    "magazine-spread": "hero spreads per section with large display type and "
    "offset imagery",
    "offset-column-rhythm": "content alternates left/right of the midline "
    "section by section",
    "diagonal-stagger": "cards and figures stagger on a diagonal rhythm; "
    "whitespace carries the motion",
    "spine-timeline": "a central spine (line/dots) that sections attach to, "
    "alternating sides",
    "bento-mosaic": "a mosaic of DIFFERENTLY-sized tiles (never identical "
    "cards) packing stats, figures, and prose",
    "paper-sections": "quiet full-width paper sections separated by rules, "
    "with asymmetric two-column interiors",
}

MOTION_PERSONALITIES = ["crisp-instant", "slow-weighty", "springy", "minimal-fade"]

SIGNATURE_MOVES: dict = {
    "animated-counters": "KPI numbers count up on first reveal (exact final values)",
    "comparison-slider": "a draggable before/after or A-vs-B divider",
    "filterable-grid": "a chip-filtered grid of items/figures",
    "hotspot-annotations": "annotated hotspots over a figure or map that "
    "reveal detail on hover/focus",
    "section-color-morph": "the accent hue shifts subtly per section as the "
    "reader scrolls",
    "sticky-figure-scrollytelling": "a figure stays pinned while prose steps "
    "scroll past and update it",
    "tabbed-dossiers": "per-topic tabbed dossiers with keyboard-navigable tabs",
    "progress-spine": "a drawn line/spine that fills with scroll progress",
}

SPACING_RHYTHMS = ["airy", "compact-dense", "rhythmic-alternating"]

PRESETS: dict = {
    "corporate": {
        "moods": ["warm-paper", "cool-clinical", "muted-earthy", "deep-luxe"],
        "voices": [
            "geometric-sans-modern",
            "humanist-warm",
            "mixed-contrast",
            "classical-humanist-serif",
            "slab-confident",
        ],
        "layouts": [
            "asymmetric-split",
            "editorial-grid-pull-elements",
            "full-bleed-bands",
            "sidebar-anchored",
            "offset-column-rhythm",
            "spine-timeline",
            "paper-sections",
        ],
        "motions": ["crisp-instant", "minimal-fade", "slow-weighty"],
    },
    "creative": {
        "moods": [
            "saturated-playful",
            "duotone-graphic",
            "high-contrast-editorial",
            "soft-pastel",
            "deep-luxe",
        ],
        "voices": list(TYPE_VOICES),
        "layouts": list(LAYOUT_SIGNATURES),
        "motions": list(MOTION_PERSONALITIES),
    },
    "technical": {
        "moods": [
            "cool-clinical",
            "high-contrast-editorial",
            "muted-earthy",
            "duotone-graphic",
            "warm-paper",
            "deep-luxe",
        ],
        "voices": [
            "mono-technical",
            "geometric-sans-modern",
            "grotesk-editorial",
            "mixed-contrast",
            "slab-confident",
        ],
        "layouts": list(LAYOUT_SIGNATURES),
        "motions": ["crisp-instant", "minimal-fade", "springy"],
    },
    "surprise": {
        "moods": list(MOODS),
        "voices": list(TYPE_VOICES),
        "layouts": list(LAYOUT_SIGNATURES),
        "motions": list(MOTION_PERSONALITIES),
    },
}


# --- history -----------------------------------------------------------------


def load_history(path: Path) -> dict:
    """Load the run history; a corrupt file degrades to a fresh start."""
    if not path.is_file():
        return {"version": 1, "entries": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
            raise ValueError("unexpected history shape")  # noqa: TRY004 - caught below to degrade safely
        return data
    except (ValueError, OSError) as exc:
        print(
            f"Warning: design history at {path} is unreadable ({exc}); starting fresh.",
            file=sys.stderr,
        )
        return {"version": 1, "entries": []}


def save_history(path: Path, history: dict) -> None:
    history["entries"] = history["entries"][-HISTORY_CAP:]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


# --- rolling -----------------------------------------------------------------


def is_attractor(candidate: dict) -> bool:
    """The default 'AI-generated' look: dark + amber + mono labels."""
    return (
        candidate["base_variant"] == "dark"
        and candidate["hue_family"] == "amber-ember"
        and candidate["type_voice"] == "mono-technical"
    )


def roll_candidate(rng: random.Random, pools: dict) -> dict:
    hue_family = rng.choice(sorted(HUE_FAMILIES))
    return {
        "hue_family": hue_family,
        "base_variant": rng.choice(["light", "dark"]),
        "mood": rng.choice(sorted(pools["moods"])),
        "neutral_temperature": rng.choice(NEUTRAL_TEMPERATURES),
        "type_voice": rng.choice(sorted(pools["voices"])),
        "layout_signature": rng.choice(sorted(pools["layouts"])),
        "motion_personality": rng.choice(sorted(pools["motions"])),
        "signature_move": rng.choice(sorted(SIGNATURE_MOVES)),
        "spacing_rhythm": rng.choice(SPACING_RHYTHMS),
    }


def shares_triple(candidate: dict, entry: dict) -> int:
    return sum(1 for axis in TRIPLE_AXES if candidate.get(axis) == entry.get(axis))


def rejected(candidate: dict, recent: list) -> bool:
    return any(shares_triple(candidate, entry) >= 2 for entry in recent)


def distance(candidate: dict, recent: list) -> int:
    axes = (
        "hue_family",
        "base_variant",
        "mood",
        "type_voice",
        "layout_signature",
        "motion_personality",
        "signature_move",
    )
    return sum(
        sum(1 for axis in axes if candidate.get(axis) != entry.get(axis))
        for entry in recent
    )


def pick_brief(rng: random.Random, preset: str, recent: list, count: int) -> dict:
    """Roll candidates, reject too-similar ones, return the most distant."""

    def batch(pools: dict) -> list:
        out: list = []
        for _ in range(count):
            candidate = roll_candidate(rng, pools)
            for _ in range(12):
                if not is_attractor(candidate):
                    break
                if preset == "surprise" and rng.random() < ATTRACTOR_SURPRISE_ODDS:
                    break  # a rare deliberate pick, allowed only here
                candidate = roll_candidate(rng, pools)
            out.append(candidate)
        return out

    candidates = batch(PRESETS[preset])
    accepted = [c for c in candidates if not rejected(c, recent)]
    if not accepted:
        # Widen once to the full pools, then take the least-similar candidate.
        candidates += batch(PRESETS["surprise"])
        accepted = [c for c in candidates if not rejected(c, recent)]
        if not accepted:
            accepted = candidates
    return max(accepted, key=lambda c: distance(c, recent))


PALETTE_KEYS = ("base", "surface", "ink", "accent", "accent_2")


def load_scheme_hint(raw: str) -> dict:
    """Parse a `--scheme-hint` value: inline JSON, or a path to a JSON file.

    The hint carries the color scheme the user picked in intake ROUND 2, which is
    proposed from the extracted content and so cannot come from the sampler's
    fixed hue-family pool. Accepted keys:

      name          a label for the design record (recommended)
      base_variant  "light" or "dark" - which end of the scale the scheme sits on
      hue_family    a pool family name, as a shorthand for its palette
      base, surface, ink, accent, accent_2   explicit hexes, each optional

    Explicit hexes win over `hue_family`, and any key omitted falls through to the
    rolled palette - so a scheme may pin only its accents and let the neutrals roll.
    """
    raw = raw.strip()
    if not raw.startswith("{"):
        path = Path(raw)
        if not path.is_file():
            raise ValueError(f"scheme hint is neither JSON nor a readable file: {raw}")
        raw = path.read_text(encoding="utf-8")
    hint = json.loads(raw)
    if not isinstance(hint, dict):
        raise ValueError(  # noqa: TRY004 - caught in main() to exit 2, not crash
            "scheme hint must be a JSON object"
        )
    variant = hint.get("base_variant")
    if variant is not None and variant not in ("light", "dark"):
        raise ValueError("scheme hint base_variant must be 'light' or 'dark'")
    family = hint.get("hue_family")
    if family is not None and family not in HUE_FAMILIES:
        raise ValueError(
            f"unknown hue_family {family!r}; expected one of {sorted(HUE_FAMILIES)}"
        )
    for key in PALETTE_KEYS:
        value = hint.get(key)
        if value is not None and not (
            isinstance(value, str) and value.startswith("#") and len(value) in (4, 7, 9)
        ):
            raise ValueError(f"scheme hint {key} must be a hex color, got {value!r}")
    return hint


def apply_scheme_hint(palette: dict, hint: dict, base_variant: str) -> tuple[dict, str]:
    """Overlay a pinned scheme onto the rolled palette. Returns the palette and
    the effective base variant."""
    variant = hint.get("base_variant", base_variant)
    merged = dict(palette)
    family_name = hint.get("hue_family")
    if family_name:
        family = HUE_FAMILIES[family_name]
        merged.update(family[variant])
        merged["accent"] = family["accents"][0]
        merged["accent_2"] = family["accents"][1]
    for key in PALETTE_KEYS:
        if hint.get(key):
            merged[key] = hint[key]
    return merged, variant


def build_brief(
    candidate: dict, preset: str, seed: int, scheme_hint: dict | None = None
) -> dict:
    family = HUE_FAMILIES[candidate["hue_family"]]
    base_variant = candidate["base_variant"]
    palette = dict(family[base_variant])
    palette["accent"] = family["accents"][0]
    palette["accent_2"] = family["accents"][1]
    # A ROUND 2 scheme pins the palette only. The candidate itself is left exactly
    # as rolled - including its `hue_family`, which is one of the anti-convergence
    # axes - so the history and rejection logic keep working unchanged and two runs
    # on the same pinned palette still differ on type voice, layout, motion, and
    # the signature move. Uniqueness is preserved WITHIN the palette rather than
    # traded away for it.
    palette_source = f"rolled: {candidate['hue_family']} ({base_variant})"
    if scheme_hint:
        palette, base_variant = apply_scheme_hint(palette, scheme_hint, base_variant)
        palette_source = (
            f"pinned by intake round 2: {scheme_hint.get('name', 'unnamed scheme')}"
        )
    voice = TYPE_VOICES[candidate["type_voice"]]
    summary = (
        f"{preset}: {candidate['base_variant']} {candidate['hue_family']} / "
        f"{candidate['mood']} / {candidate['type_voice']} / "
        f"{candidate['layout_signature']} / {candidate['motion_personality']} / "
        f"move: {candidate['signature_move']} (seed {seed})"
    )
    return {
        "preset": preset,
        "seed": seed,
        "hue_family": candidate["hue_family"],
        "base_variant": base_variant,
        "palette": palette,
        # Recorded so the design record can say where the colors came from. The
        # `hue_family` above stays the ROLLED axis even when the palette is
        # pinned, because that is what the anti-convergence history compares.
        "palette_source": palette_source,
        "mood": candidate["mood"],
        "neutral_temperature": candidate["neutral_temperature"],
        "type": {
            "voice": candidate["type_voice"],
            "heading": voice["heading"],
            "body": voice["body"],
            "mono": voice["mono"],
        },
        "spacing_rhythm": candidate["spacing_rhythm"],
        "layout_signature": {
            "name": candidate["layout_signature"],
            "description": LAYOUT_SIGNATURES[candidate["layout_signature"]],
        },
        "motion_personality": candidate["motion_personality"],
        "signature_move": {
            "name": candidate["signature_move"],
            "description": SIGNATURE_MOVES[candidate["signature_move"]],
        },
        "summary": summary,
    }


def commit_brief(brief_path: Path, history_path: Path, source_hash: str) -> int:
    try:
        brief = json.loads(brief_path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        print(f"Error: cannot read brief {brief_path}: {exc}", file=sys.stderr)
        return 1
    history = load_history(history_path)
    history["entries"].append(
        {
            "timestamp": int(time.time()),
            "source_hash": source_hash,
            "preset": brief.get("preset", ""),
            "seed": brief.get("seed"),
            "hue_family": brief.get("hue_family"),
            "base_variant": brief.get("base_variant"),
            "mood": brief.get("mood"),
            "type_voice": (brief.get("type") or {}).get("voice"),
            "layout_signature": (brief.get("layout_signature") or {}).get("name"),
            "motion_personality": brief.get("motion_personality"),
            "signature_move": (brief.get("signature_move") or {}).get("name"),
        }
    )
    save_history(history_path, history)
    print(
        f"Committed brief to history ({len(history['entries'])} entries).",
        file=sys.stderr,
    )
    return 0


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Roll a seeded, history-aware design brief for the "
            "document-to-interactive-html skill (stdlib-only, local-only)."
        )
    )
    parser.add_argument(
        "--preset",
        choices=sorted(PRESETS),
        default="surprise",
        help="Design-direction preset constraining the pools (default surprise).",
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Reproducible roll seed."
    )
    parser.add_argument(
        "--history",
        default=str(DEFAULT_HISTORY),
        help="Run-history JSON path (default ~/.nexus-hub/state/...).",
    )
    parser.add_argument(
        "--candidates",
        type=int,
        default=3,
        help="Candidates rolled before the distance pick (default 3).",
    )
    parser.add_argument(
        "--scheme-hint",
        help="Pin the palette to the color scheme chosen in intake ROUND 2: "
        "inline JSON or a path to a JSON file. Keys: name, base_variant, "
        "hue_family, and/or explicit base/surface/ink/accent/accent_2 hexes. "
        "The sampler still rolls type voice, layout, motion, and the signature "
        "move, and the anti-convergence history is untouched.",
    )
    parser.add_argument("-o", "--out", help="Output brief JSON path.")
    parser.add_argument(
        "--commit",
        metavar="BRIEF_JSON",
        help="Append an already-used brief to the history instead of rolling.",
    )
    parser.add_argument(
        "--source-hash",
        default="",
        help="Optional source-content hash recorded on --commit.",
    )
    args = parser.parse_args(argv)

    history_path = Path(args.history)
    if args.commit:
        return commit_brief(Path(args.commit), history_path, args.source_hash)

    if not args.out:
        parser.error("-o/--out is required when rolling a brief")
    seed = args.seed if args.seed is not None else int.from_bytes(os.urandom(8), "big")
    rng = random.Random(seed)
    recent = load_history(history_path)["entries"][-RECENT_WINDOW:]
    scheme_hint = None
    if args.scheme_hint:
        try:
            scheme_hint = load_scheme_hint(args.scheme_hint)
        except (ValueError, OSError) as exc:
            # A malformed hint is a usage error, not a reason to silently roll an
            # unpinned palette - that would ship colors the user did not choose.
            print(f"Error: --scheme-hint: {exc}", file=sys.stderr)
            return 2
    candidate = pick_brief(rng, args.preset, recent, max(1, args.candidates))
    brief = build_brief(candidate, args.preset, seed, scheme_hint)

    out_path = Path(args.out)
    if out_path.parent and not out_path.parent.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(brief["summary"], file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
