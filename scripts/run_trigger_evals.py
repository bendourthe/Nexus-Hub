#!/usr/bin/env python3
"""Catalog-wide trigger-and-routing eval: skill-description near-collision detector.

Every skill in the catalog is chosen by an agent from its one-line `description`
frontmatter field (the always-loaded Tier-1 text). When two descriptions share
too much trigger vocabulary, an agent cannot reliably tell them apart and
mis-routes -- the under/over-triggering failure mode. This tool is a
deterministic, model-free gate that flags any two skill descriptions whose
trigger vocabulary overlaps beyond a configurable threshold, so a
near-collision is caught at PR time rather than in production routing.

The metric is a containment ratio: for the token sets A and B of two
descriptions, `|A intersect B| / min(|A|, |B|)`. The `min` denominator (not the
union, as Jaccard would use) is deliberate -- it fires when one skill's
vocabulary is largely SUBSUMED by another's even if the larger description
carries extra words, which is exactly the shape of an under-triggering
collision. Descriptions are lowercased, split on non-alphanumerics, filtered
against a stopword set and a 3-character floor, and lightly suffix-stemmed
(ing/es/ed/s) so "projects"/"project" and "finished"/"finish" match.

Modes:
  * Warning-only (default): report every near-collision but always exit 0. This
    is how the gate ships first, so its findings can be triaged.
  * Gate (`--gate` / `--strict`): exit non-zero when any near-collision is NOT
    listed in the intentional-neighbor allowlist.

Intentional near-neighbors (two closely related skills in one category that
legitimately share vocabulary) are recorded in an allowlist file and downgraded
from a FAIL to an informational line, mirroring the transitional-allowlist
pattern already used by validate_skills.py.

Usage:
    python scripts/run_trigger_evals.py
    python scripts/run_trigger_evals.py --json
    python scripts/run_trigger_evals.py --threshold 0.6 --verbose
    python scripts/run_trigger_evals.py --gate            # non-zero on collisions
    python scripts/run_trigger_evals.py --path catalog/skills/workflow
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_THRESHOLD = 0.5

# The intentional-neighbor allowlist lives beside this script, mirroring the
# validate_skills.allowlist.json convention. Both are copied together by the
# installers to ~/.nexus-hub/scripts/.
ALLOWLIST_PATH = Path(__file__).resolve().parent / "run_trigger_evals.allowlist.json"

# Minimum surviving token length. Two- and one-character fragments carry no
# routing signal and inflate overlap noise.
MIN_TOKEN_LEN = 3

# Light suffix stemmer suffixes, longest-first so "-ing" wins over "-s". A
# suffix is only stripped when the remaining stem stays at or above
# MIN_TOKEN_LEN, so the stemmer never produces sub-threshold nubs.
_STEM_SUFFIXES = ("ing", "es", "ed", "s")

# Stopwords: standard English function words PLUS the scaffolding vocabulary of
# the "pushy description" authoring convention (trigger/phrases/skip/use/...),
# which appears in nearly every description and would otherwise dominate the
# overlap metric and mask real, capability-level collisions. Both base and
# common surface forms are listed so the check is robust whether or not a given
# token survives stemming. Kept deliberately generic -- capability nouns
# (dashboard, migration, forensics, ...) are never stopworded.
STOPWORDS: frozenset[str] = frozenset({
    # Articles, conjunctions, prepositions, pronouns, auxiliaries.
    "the", "and", "for", "with", "when", "not", "any", "all", "are", "was",
    "you", "your", "our", "its", "this", "that", "these", "those", "their",
    "them", "they", "from", "into", "onto", "out", "off", "over", "under",
    "than", "then", "but", "can", "could", "would", "should", "may", "might",
    "will", "shall", "must", "have", "has", "had", "been", "being", "does",
    "did", "done", "such", "each", "per", "via", "one", "two", "who", "whom",
    "how", "why", "what", "where", "which", "while", "about", "across", "also",
    "even", "just", "only", "both", "either", "neither", "same", "other",
    "another", "some", "many", "more", "most", "less", "least", "very", "too",
    "already", "yet", "still", "here", "there", "now", "before", "after",
    # Pushy-description scaffolding (base + common surface forms).
    "use", "using", "used", "uses", "skip", "make", "sure", "whenever",
    "user", "users", "mention", "mentions", "mentioned", "phrase", "phrases",
    "trigger", "triggers", "triggered", "triggering", "ask", "asks", "asked",
    "want", "wants", "wanted", "explicitly", "standalone", "look", "looks",
    "like", "instead", "rather", "kind", "type", "types", "thing", "things",
    "way", "ways", "etc", "eg", "ie",
    "skill", "skills", "task", "tasks", "step", "steps", "help", "helps",
    "need", "needs", "needed", "produce", "produces", "generate", "generates",
    "create", "creates", "creating", "run", "runs", "running", "get", "gets",
})


# ---------------------------------------------------------------------------
# YAML frontmatter parsing (mirrors scripts/validate_skills.py parse_frontmatter;
# mirrored rather than imported so this script is self-contained at its
# installed location and never adds a pyyaml dependency)
# ---------------------------------------------------------------------------

def parse_frontmatter(content: str) -> dict[str, str] | None:
    """Extract YAML frontmatter from a Markdown file (between --- delimiters).

    Tolerant line-splitter: single-line frontmatter fields (which the catalog
    enforces for name/description) are split on the first `:`. Values keep any
    later `: ` sequences intact (e.g. a `SKIP:` clause inside a description).
    """
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    raw = content[3:end].strip()
    result: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

def _stem(token: str) -> str:
    """Strip a light inflectional suffix, keeping the stem at >= MIN_TOKEN_LEN."""
    for suffix in _STEM_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= MIN_TOKEN_LEN:
            return token[: -len(suffix)]
    return token


def tokenize(description: str) -> set[str]:
    """Turn a description into its trigger-vocabulary token set.

    Lowercase, split on non-alphanumerics, drop stopwords and short fragments,
    then suffix-stem the survivors (re-checking the stopword set and length
    floor on the stem so stemmed scaffolding words like "triggers" -> "trigger"
    are still removed).
    """
    tokens: set[str] = set()
    for raw in re.split(r"[^a-z0-9]+", description.lower()):
        if len(raw) < MIN_TOKEN_LEN or raw in STOPWORDS:
            continue
        stem = _stem(raw)
        if len(stem) < MIN_TOKEN_LEN or stem in STOPWORDS:
            continue
        tokens.add(stem)
    return tokens


# ---------------------------------------------------------------------------
# Allowlist
# ---------------------------------------------------------------------------

def _canonical_pair(a: str, b: str) -> tuple[str, str]:
    """Order a skill-name pair deterministically so lookups are direction-free."""
    return (a, b) if a <= b else (b, a)


def load_allowlist(path: Path = ALLOWLIST_PATH) -> dict[tuple[str, str], str]:
    """Load intentional near-neighbor pairs -> justification.

    Each `allow` entry is either a two-element `[a, b]` list or an object
    `{"pair": [a, b], "reason": "..."}`. A missing or malformed file yields an
    empty mapping (the allowlist is optional and additive).
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    entries = data.get("allow", []) if isinstance(data, dict) else []
    result: dict[tuple[str, str], str] = {}
    for entry in entries:
        pair: object
        reason = ""
        if isinstance(entry, dict):
            pair = entry.get("pair")
            reason = str(entry.get("reason", ""))
        else:
            pair = entry
        if isinstance(pair, (list, tuple)) and len(pair) == 2:
            a, b = str(pair[0]), str(pair[1])
            result[_canonical_pair(a, b)] = reason
    return result


# ---------------------------------------------------------------------------
# Discovery + scoring
# ---------------------------------------------------------------------------

def find_skill_descriptions(root: Path) -> dict[str, str]:
    """Map each skill name to its description across the skill tree.

    The skill name is the frontmatter `name`, or the SKILL.md parent directory
    name when `name` is absent (the validator's default-name rule). Skills with
    an empty or unparseable description are skipped -- absent descriptions are
    the validator's concern, not this tool's.
    """
    descriptions: dict[str, str] = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        if "SKILL.md" not in filenames:
            continue
        skill_dir = Path(dirpath)
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(content)
        if not fm:
            continue
        name = fm.get("name") or skill_dir.name
        description = fm.get("description", "").strip()
        if description:
            descriptions[name] = description
    return descriptions


def overlap_ratio(a: set[str], b: set[str]) -> float:
    """Containment overlap: |A intersect B| / min(|A|, |B|); 0 when either is empty."""
    smaller = min(len(a), len(b))
    if smaller == 0:
        return 0.0
    return len(a & b) / smaller


def find_collisions(
    descriptions: dict[str, str],
    threshold: float,
    allowlist: dict[tuple[str, str], str],
) -> list[dict[str, object]]:
    """Return every skill pair whose description overlap meets or exceeds threshold.

    Reported meets-or-exceeds the threshold (a pair sitting exactly at the
    threshold is a collision, the safer gate semantics). Each result carries the
    canonical pair, the ratio and rounded percentage, and whether the pair is
    allowlisted (with its justification). Results are sorted by descending ratio
    then name so output is deterministic.
    """
    tokens = {name: tokenize(desc) for name, desc in descriptions.items()}
    names = sorted(tokens)
    collisions: list[dict[str, object]] = []
    for i, name_a in enumerate(names):
        for name_b in names[i + 1:]:
            ratio = overlap_ratio(tokens[name_a], tokens[name_b])
            if ratio < threshold:
                continue
            pair = _canonical_pair(name_a, name_b)
            allowlisted = pair in allowlist
            collisions.append({
                "a": pair[0],
                "b": pair[1],
                "ratio": round(ratio, 4),
                "pct": round(ratio * 100),
                "allowlisted": allowlisted,
                "reason": allowlist.get(pair, ""),
            })
    collisions.sort(key=lambda c: (-float(c["ratio"]), c["a"], c["b"]))
    return collisions


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect skill-description trigger-vocabulary near-collisions",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("catalog/skills"),
        help="Root directory to scan for skills (default: catalog/skills)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Shared-vocabulary ratio at or above which a pair collides "
             f"(default: {DEFAULT_THRESHOLD})",
    )
    parser.add_argument(
        "--allowlist",
        type=Path,
        default=ALLOWLIST_PATH,
        help="Path to the intentional-neighbor allowlist JSON "
             "(default: scripts/run_trigger_evals.allowlist.json)",
    )
    parser.add_argument(
        "--gate", "--strict",
        dest="gate",
        action="store_true",
        help="Gate mode: exit non-zero when un-allowlisted collisions exist "
             "(default: warning-only, always exit 0)",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Emit a structured JSON report instead of human-readable lines",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Also print allowlisted (informational) near-neighbor pairs",
    )
    args = parser.parse_args()

    if not args.path.exists():
        print(f"ERROR: path does not exist: {args.path}", file=sys.stderr)
        return 1

    descriptions = find_skill_descriptions(args.path)
    allowlist = load_allowlist(args.allowlist)
    collisions = find_collisions(descriptions, args.threshold, allowlist)
    unallowlisted = [c for c in collisions if not c["allowlisted"]]

    if args.as_json:
        report = {
            "scanned": len(descriptions),
            "threshold": args.threshold,
            "gate": args.gate,
            "collisions": collisions,
            "unallowlisted_count": len(unallowlisted),
        }
        print(json.dumps(report, indent=2))
        return 1 if (args.gate and unallowlisted) else 0

    mode = "gate" if args.gate else "warning-only"
    print(
        f"Scanned {len(descriptions)} skill descriptions under {args.path} "
        f"(threshold {args.threshold}, {mode} mode)"
    )

    for c in collisions:
        if c["allowlisted"]:
            if args.verbose:
                reason = f" - {c['reason']}" if c["reason"] else ""
                print(
                    f"  INFO (allowlisted) descriptions near-collide: "
                    f"{c['a']} vs {c['b']} ({c['pct']}% shared vocabulary){reason}"
                )
        else:
            print(
                f"  FAIL descriptions near-collide: "
                f"{c['a']} vs {c['b']} ({c['pct']}% shared vocabulary)"
            )

    allowlisted_count = len(collisions) - len(unallowlisted)
    if unallowlisted:
        print(
            f"\nRESULT: {len(unallowlisted)} un-allowlisted near-collision(s), "
            f"{allowlisted_count} allowlisted"
        )
        if args.gate:
            return 1
        print("(warning-only mode: not failing; run with --gate to enforce)")
        return 0

    print(f"\nRESULT: PASS (0 un-allowlisted collisions, {allowlisted_count} allowlisted)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
