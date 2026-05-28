#!/usr/bin/env python3
"""nexus-hub consult -- match a natural-language need to catalog components.

Usage:

    python scripts/nexus_hub_consult.py "I need to debug a flaky test"
    python scripts/nexus_hub_consult.py --top 5 --json "design a REST API"
    python scripts/nexus_hub_consult.py --kind profile "minimal setup"

The matcher reads `data/skills.json`, `data/bundles.json` (profiles + modules
+ bundles), and `data/SKILL_INDEX.md` to score every candidate component
against the user's natural-language need. The top matches print to stdout,
each with the install command line the user should run.

Local-only, read-only, zero-outbound. No API keys, no network, no external
service. This is the local reverse-engineering of ECC's `consult.js`.

Design: the heavy lifting (loading the catalog, splitting tokens, filtering
by kind, picking the top N, formatting output, exit codes) is here. The
ranking math itself is intentionally small (`score_candidate`) so it stays
auditable and easy to tune.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Set

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_JSON = REPO_ROOT / "data" / "skills.json"
BUNDLES_JSON = REPO_ROOT / "data" / "bundles.json"


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #


@dataclass
class Candidate:
    """One scorable catalog entry (skill / bundle / profile / module)."""

    kind: str  # "skill" | "bundle" | "profile" | "module"
    id: str
    name: str
    description: str
    tags: List[str] = field(default_factory=list)
    install_hint: str = ""


@dataclass
class ScoredCandidate:
    candidate: Candidate
    score: float
    matched_tokens: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Catalog loading
# --------------------------------------------------------------------------- #


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Catalog file missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_candidates(kinds: Set[str]) -> List[Candidate]:
    """Return one Candidate per catalog entry of the requested `kinds`.

    `kinds` is a set drawn from {"skill", "bundle", "profile", "module"}.
    """
    out: List[Candidate] = []
    if "skill" in kinds and SKILLS_JSON.exists():
        skills = _load_json(SKILLS_JSON).get("skills", [])
        for s in skills:
            description = s.get("description") or s.get("summary_l0") or ""
            out.append(
                Candidate(
                    kind="skill",
                    id=str(s.get("name", "")),
                    name=str(s.get("title", s.get("name", ""))),
                    description=str(description),
                    tags=list(s.get("tags", []) or []),
                    install_hint=(
                        f"installer.sh --modules <module-id>  "
                        f"# skill: {s.get('name')}"
                    ),
                )
            )
    if any(k in kinds for k in ("bundle", "profile", "module")) and BUNDLES_JSON.exists():
        bundles_doc = _load_json(BUNDLES_JSON)
        if "bundle" in kinds:
            for b in bundles_doc.get("bundles", []):
                out.append(
                    Candidate(
                        kind="bundle",
                        id=str(b.get("id", "")),
                        name=str(b.get("name", b.get("id", ""))),
                        description=str(b.get("description", "")),
                        tags=list(b.get("skills", []) or []),
                        install_hint=f"installer.sh --bundle {b.get('id')}",
                    )
                )
        if "profile" in kinds:
            for p in bundles_doc.get("profiles", []):
                out.append(
                    Candidate(
                        kind="profile",
                        id=str(p.get("id", "")),
                        name=str(p.get("name", p.get("id", ""))),
                        description=str(p.get("description", "")),
                        tags=list(p.get("bundles", []) or [])
                        + list(p.get("modules", []) or []),
                        install_hint=f"installer.sh --profile {p.get('id')}",
                    )
                )
        if "module" in kinds:
            for m in bundles_doc.get("modules", []):
                out.append(
                    Candidate(
                        kind="module",
                        id=str(m.get("id", "")),
                        name=str(m.get("name", m.get("id", ""))),
                        description=str(m.get("description", "")),
                        tags=[str(m.get("capability", ""))]
                        + list(m.get("skills", []) or []),
                        install_hint=f"installer.sh --modules {m.get('id')}",
                    )
                )
    return out


# --------------------------------------------------------------------------- #
# Tokenizer + stoplist
# --------------------------------------------------------------------------- #


_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+-]{1,}")
_STOPWORDS: Set[str] = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "for", "from", "have",
    "i", "in", "is", "it", "my", "need", "of", "on", "or", "that", "the", "their",
    "this", "to", "use", "want", "with", "you", "your", "how", "can", "should",
    "would", "will",
}


def tokenize(text: str) -> List[str]:
    """Return the meaningful lowercase tokens in `text`, with stopwords removed."""
    if not text:
        return []
    return [
        t.lower()
        for t in _TOKEN_RE.findall(text)
        if t.lower() not in _STOPWORDS and len(t) > 1
    ]


# --------------------------------------------------------------------------- #
# Scoring (user-contribution slot)
# --------------------------------------------------------------------------- #


def score_candidate(query_tokens: List[str], candidate: Candidate) -> ScoredCandidate:
    """Score one candidate against the user's tokenized need.

    TODO (Phase 4 / T011 -- user contribution slot, ~5-10 lines):
        Implement the ranking heuristic that decides how strongly a catalog
        entry matches the user's natural-language need. The function MUST:

        * Return a `ScoredCandidate` with a non-negative `score` (higher is
          better; ``score == 0`` means "no match" and is filtered out).
        * Populate `matched_tokens` with the unique query tokens that
          contributed to the score.

        Trade-offs to consider:
            * Token overlap (simple, fast, biased toward long descriptions).
            * IDF-style weighting (favors rare tokens; better for distinguishing
              between similar skills like "unit-tests" vs "edge-case-generator").
            * Field weighting (a hit in `id`/`name` should outweigh a hit in
              `description`).
            * Tag boosting (a hit in `candidate.tags` means the user named a
              skill or capability directly).

        Suggested starting point: token overlap + a 2x boost when a token
        matches `candidate.id` exactly or appears as a tag. Keep it small;
        future iteration can add IDF or embeddings.

    The scaffolding below (`searchable`, `query_set`, `matched`) is provided
    so the contribution stays at the math layer.
    """
    searchable = " ".join(
        [
            candidate.id,
            candidate.name,
            candidate.description,
            " ".join(candidate.tags),
        ]
    ).lower()
    searchable_tokens = set(tokenize(searchable))
    query_set = set(query_tokens)
    matched = sorted(query_set & searchable_tokens)

    # ----- BEGIN user-contribution slot -------------------------------------
    # TODO: replace this baseline with your chosen ranking heuristic.
    score = float(len(matched))
    if candidate.id.lower() in query_set:
        score += 2.0
    for tag in candidate.tags:
        if tag.lower() in query_set:
            score += 1.0
    # ----- END user-contribution slot ---------------------------------------

    return ScoredCandidate(candidate=candidate, score=score, matched_tokens=matched)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def consult(
    need: str,
    kinds: Optional[Iterable[str]] = None,
    top: int = 5,
) -> List[ScoredCandidate]:
    """Return the top `top` matching candidates for `need`."""
    kinds_set: Set[str] = (
        set(kinds) if kinds else {"skill", "bundle", "profile", "module"}
    )
    candidates = load_candidates(kinds_set)
    tokens = tokenize(need)
    if not tokens:
        return []
    scored = [score_candidate(tokens, c) for c in candidates]
    scored = [s for s in scored if s.score > 0]
    scored.sort(key=lambda s: (-s.score, s.candidate.kind, s.candidate.id))
    return scored[: max(1, top)]


def _format_text(results: List[ScoredCandidate]) -> str:
    if not results:
        return "No matching components.\n"
    lines: List[str] = []
    for r in results:
        c = r.candidate
        matched = ", ".join(r.matched_tokens) if r.matched_tokens else "(no tokens)"
        lines.append(f"[{c.kind}] {c.id} -- {c.name}  (score={r.score:.1f})")
        if c.description:
            short = c.description.replace("\n", " ").strip()
            if len(short) > 200:
                short = short[:197] + "..."
            lines.append(f"  {short}")
        lines.append(f"  matched: {matched}")
        lines.append(f"  install: {c.install_hint}")
        lines.append("")
    return "\n".join(lines)


def _format_json(results: List[ScoredCandidate]) -> str:
    payload = [
        {
            "kind": r.candidate.kind,
            "id": r.candidate.id,
            "name": r.candidate.name,
            "description": r.candidate.description,
            "tags": r.candidate.tags,
            "install_hint": r.candidate.install_hint,
            "score": r.score,
            "matched_tokens": r.matched_tokens,
        }
        for r in results
    ]
    return json.dumps(payload, indent=2)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nexus-hub-consult",
        description=(
            "Match a natural-language need to Nexus-Hub catalog components "
            "(skills, bundles, profiles, modules). Local, read-only, zero "
            "outbound."
        ),
    )
    parser.add_argument("need", help='Natural-language description of the need.')
    parser.add_argument(
        "--kind",
        choices=["skill", "bundle", "profile", "module", "all"],
        default="all",
        help="Restrict to one component kind (default: all).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Maximum number of results to print (default: 5).",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args(argv)
    kinds = None if args.kind == "all" else {args.kind}
    try:
        results = consult(args.need, kinds=kinds, top=args.top)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(_format_json(results))
    else:
        sys.stdout.write(_format_text(results))
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
