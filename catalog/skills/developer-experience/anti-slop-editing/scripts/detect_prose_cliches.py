#!/usr/bin/env python3
"""Find cliche patterns in prose deterministically, offline, with the standard library only.

The detector is a floor, not a ceiling: it catches the patterns it encodes and the
model still owns the rest. It is advisory by default (exit 0 whatever it finds) so
that it informs an edit rather than blocking one; callers that want a gate pass
`--fail-on defect`.

Findings carry one of two classes, matching `references/cliche-patterns.md`:

- ``defect``: text with no legitimate place in a shipped document. Chatbot
  leftovers ("as an AI language model", "I hope this helps") and the Unicode
  punctuation the Writing Discipline block forbids (em-dashes, en-dashes, curly
  quotes, the ellipsis character), which the repository's unicode gate also rejects.
- ``advisory``: a register or move a writer may legitimately intend, or a rule whose
  legacy footprint is too large to fail a document on. The reflective register, the
  faux reveal, emphatic negation, performative honesty, the stranded auxiliary, the
  high-frequency body-catalog patterns, the three countable rhythm rules from the
  skill's ``Robotic rhythm`` entry, and the clause-joining spaced hyphen. The spaced
  hyphen is advisory rather than defect on purpose: it was the sanctioned ASCII
  replacement for an em-dash in this project's own prose for years, so a first scan
  of any existing document finds hundreds, and a defect class that fires hundreds of
  times on legitimate history is a class nobody gates on.

Mannered prose is deliberately not attempted: it has no reliable lexical
signature, and a regex that guessed at metaphor would fire on legitimate voice.
That class stays with the model's judgment.

Markdown awareness is minimal on purpose. Fenced code blocks, headings, and table
rows are skipped entirely, and a lexical match that sits inside straight double
quotes or backticks is ignored, because a document that quotes a pattern (this
skill's own catalog, a review that names a finding) is not committing it. List items are scanned lexically but excluded from the
three rhythm rules, because consecutive bullets are parallel by design and would
otherwise read as a run of same-opener sentences. Rhythm runs also reset at a blank
line, so two paragraphs never combine into one run. Sentences are split on ``.``,
``!`` and ``?`` followed by whitespace, which is good enough for the rhythm rules.

Usage:
    python detect_prose_cliches.py FILE
    python detect_prose_cliches.py - < FILE
    python detect_prose_cliches.py FILE --json
    python detect_prose_cliches.py FILE --fail-on defect

Exit codes:
    0  Ran to completion. The default regardless of findings.
    1  A finding of the class named by ``--fail-on`` was present.
    2  Invalid input or arguments (missing file, undecodable bytes).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

DEFECT = "defect"
ADVISORY = "advisory"

# --- lexical patterns -------------------------------------------------------------
# Each entry: (pattern id, class, compiled regex). Every regex here was written for
# this skill from the behavior each pattern describes; none is copied from any tool.
_FLAGS = re.IGNORECASE
LEXICAL: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    # defect: chatbot leftovers
    (
        "chatbot-leftover",
        DEFECT,
        re.compile(r"\bas an AI(?: language model)?\b", _FLAGS),
    ),
    (
        "chatbot-leftover",
        DEFECT,
        re.compile(
            r"\bhere(?:'s| is) (?:the|your) (?:revised|updated|corrected) (?:version|draft|text)\b",
            _FLAGS,
        ),
    ),
    ("chatbot-leftover", DEFECT, re.compile(r"\bI hope (?:this|that) helps\b", _FLAGS)),
    ("chatbot-leftover", DEFECT, re.compile(r"(?:^|(?<=[.!?]\s))Certainly!", _FLAGS)),
    ("chatbot-leftover", DEFECT, re.compile(r"\bgreat question\b", _FLAGS)),
    (
        "chatbot-leftover",
        DEFECT,
        re.compile(r"\blet me know if you (?:need|have|want)\b", _FLAGS),
    ),
    # defect: Unicode punctuation the Writing Discipline block forbids
    ("em-dash", DEFECT, re.compile("\u2014")),
    ("en-dash", DEFECT, re.compile("\u2013")),
    ("curly-quote", DEFECT, re.compile("[\u2018\u2019\u201c\u201d]")),
    ("ellipsis-character", DEFECT, re.compile("\u2026")),
    # advisory: the clause-joining spaced hyphen (see the module docstring for why)
    ("spaced-hyphen-connector", ADVISORY, re.compile(r"(?<=\w) - (?=\w)")),
    # advisory: labelled closing-summary markers (slop-wordlist.md, closing-summary family; v4.7.0)
    (
        "closing-summary-marker",
        ADVISORY,
        re.compile(r"^\W{0,4}(?:bottom line|in short)\s*:", _FLAGS | re.MULTILINE),
    ),
    # advisory: the reflective register (cliche-patterns.md cluster 1)
    (
        "dwelling-instruction",
        ADVISORY,
        re.compile(
            r"\b(?:sit with (?:that|this|it)|let that (?:land|sink in))\b", _FLAGS
        ),
    ),
    (
        "naming-ceremony",
        ADVISORY,
        re.compile(r"\b(?:worth naming|deserves to be (?:said|named))\b", _FLAGS),
    ),
    (
        "understated-significance",
        ADVISORY,
        re.compile(
            r"\b(?:is|was|that's|that is) (?:not nothing|no small thing)\b", _FLAGS
        ),
    ),
    ("presumed-knowledge", ADVISORY, re.compile(r"\byou already know\b", _FLAGS)),
    (
        "isolated-part",
        ADVISORY,
        re.compile(r"\b(?:that|this) is the part (?:that|people|most)\b", _FLAGS),
    ),
    (
        "lone-trusted-source",
        ADVISORY,
        re.compile(r"\bthe only \w+(?: \w+){0,3} I trust\b", _FLAGS),
    ),
    (
        "mock-humility",
        ADVISORY,
        re.compile(r"\bdo(?:n't| not) (?:just )?take my word\b", _FLAGS),
    ),
    # advisory: the faux reveal (cluster 2)
    (
        "announced-punchline",
        ADVISORY,
        re.compile(r"\b(?:the punchline is|here(?:'s| is) the twist)\b", _FLAGS),
    ),
    (
        "discovery-frame",
        ADVISORY,
        re.compile(r"(?:^|(?<=[.!?]\s))(?:Turns out|As it happens),", _FLAGS),
    ),
    (
        "retroactive-significance",
        ADVISORY,
        re.compile(r"\bthat(?:'s| is) why \w+(?: \w+){0,5} mattered\b", _FLAGS),
    ),
    ("obituary", ADVISORY, re.compile(r"\b[A-Z][\w-]*(?: [\w-]+){0,2} is dead\.", 0)),
    ("head-sized-praise", ADVISORY, re.compile(r"\bfits? in your head\b", _FLAGS)),
    # advisory: emphatic negation and totality (cluster 3)
    (
        "negation-chain",
        ADVISORY,
        re.compile(r"\bno \w+(?: \w+)?,\s*no \w+(?: \w+)?,\s*no \w+", _FLAGS),
    ),
    (
        "negation-chain",
        ADVISORY,
        re.compile(
            r"\bdid(?:n't| not) \w+(?: \w+)?,\s*did(?:n't| not) \w+(?: \w+)?,\s*did(?:n't| not) \w+",
            _FLAGS,
        ),
    ),
    (
        "verb-reversal",
        ADVISORY,
        re.compile(
            r"(?i:\bdo(?:n't| not)) \w+ (?:the |your |a |an )?\w+\.\s+[A-Z]\w+ (?:it|them)\.",
            0,
        ),
    ),
    (
        "totality-claim",
        ADVISORY,
        re.compile(
            r"\bis the (?:whole|entire) (?:game|point|product|story|thing|job)\b",
            _FLAGS,
        ),
    ),
    # advisory: performative honesty (cluster 4)
    (
        "performative-honesty",
        ADVISORY,
        re.compile(
            r"\b(?:I(?:'ll| will) be honest|let(?:'s| us) be real|to be honest|if I(?:'m| am) being honest)\b",
            _FLAGS,
        ),
    ),
    (
        "performative-honesty",
        ADVISORY,
        re.compile(r"(?:^|(?<=[.!?]\s))(?:Honestly|Look),", 0),
    ),
    # advisory: high-frequency body-catalog patterns
    (
        "throat-clearing-opener",
        ADVISORY,
        re.compile(
            r"\b(?:in today's (?:fast-paced )?world|when it comes to|at its core),",
            _FLAGS,
        ),
    ),
    (
        "faux-insight-setup",
        ADVISORY,
        re.compile(
            r"\b(?:here(?:'s| is) the thing|the truth is|what most people miss)\b",
            _FLAGS,
        ),
    ),
    (
        "importance-puffery",
        ADVISORY,
        re.compile(
            r"\bit(?:'s| is) (?:important|worth) (?:to note|noting|to remember)\b",
            _FLAGS,
        ),
    ),
    (
        "weasel-attribution",
        ADVISORY,
        re.compile(
            r"\b(?:experts say|studies show|many believe|it is widely (?:known|believed))\b",
            _FLAGS,
        ),
    ),
    (
        "binary-contrast",
        ADVISORY,
        re.compile(
            r"\bnot (?:just|only|merely) \w+(?: \w+){0,6}, (?:but|it's|it is) \b",
            _FLAGS,
        ),
    ),
)

# --- structural rules ---------------------------------------------------------------
ECHO_RUN_MIN = 2  # consecutive sentences sharing a four-word skeleton
OPENER_RUN_MIN = 3  # consecutive sentences opening on the same non-function word
QUESTION_RUN_MIN = 2  # consecutive question sentences
SKELETON_LEN = 4
_ARTICLES = {"a", "an", "the"}
_FUNCTION_WORDS = {
    "a",
    "an",
    "the",
    "and",
    "but",
    "or",
    "so",
    "it",
    "this",
    "that",
    "there",
    "we",
    "i",
    "you",
    "they",
    "he",
    "she",
}

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
_FENCE = re.compile(r"^\s*(```|~~~)")
_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")


@dataclass(frozen=True)
class Finding:
    id: str
    cls: str
    line: int
    col: int
    span: str
    rule: str

    def as_dict(self) -> dict[str, object]:
        d = asdict(self)
        d["class"] = d.pop("cls")
        return d


@dataclass(frozen=True)
class Sentence:
    text: str
    line: int
    col: int


_BREAK = Sentence(
    "", -1, -1
)  # sentinel: a run boundary (paragraph break, list item, end of input)


def _prose_lines(text: str) -> list[tuple[int, str]]:
    """Return (1-based line number, line) for prose lines, skipping code fences, headings, tables.

    Blank lines are returned as ("", n) markers so the structural pass can reset runs at
    paragraph boundaries; the lexical pass ignores them.
    """
    out: list[tuple[int, str]] = []
    in_fence = False
    for i, line in enumerate(text.splitlines(), 1):
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = line.lstrip()
        if not stripped:
            out.append((i, ""))
            continue
        if stripped.startswith(("#", "|")):
            continue
        out.append((i, line))
    return out


_QUOTED = re.compile(r'"[^"\n]*"|`[^`\n]*`')


def _quoted_spans(line: str) -> list[tuple[int, int]]:
    """Ranges inside straight double quotes or backticks: a document that QUOTES a pattern is not committing it."""
    return [(m.start(), m.end()) for m in _QUOTED.finditer(line)]


def _inside(spans: list[tuple[int, int]], start: int, end: int) -> bool:
    return any(a <= start and end <= b for a, b in spans)


def _lexical_findings(lines: list[tuple[int, str]]) -> list[Finding]:
    findings: list[Finding] = []
    for lineno, line in lines:
        if not line:
            continue
        quoted = _quoted_spans(line)
        for pid, cls, rx in LEXICAL:
            for m in rx.finditer(line):
                if _inside(quoted, m.start(), m.end()):
                    continue
                findings.append(
                    Finding(pid, cls, lineno, m.start() + 1, m.group(0), "lexical")
                )
    return findings


def _sentences(lines: list[tuple[int, str]]) -> list[Sentence]:
    """Split prose into sentences, inserting a run boundary at blank lines and around list items."""
    sentences: list[Sentence] = []
    for lineno, line in lines:
        if not line or _LIST_ITEM.match(line):
            sentences.append(_BREAK)
            continue
        pos = 0
        for chunk in _SENTENCE_END.split(line.strip()):
            chunk = chunk.strip()
            if not chunk:
                continue
            col = line.find(chunk, pos) + 1 if chunk in line else 1
            pos = max(pos, col)
            sentences.append(Sentence(chunk, lineno, col))
    sentences.append(_BREAK)
    return sentences


def _skeleton(sentence: str) -> tuple[str, ...]:
    words = [w.lower() for w in _WORD.findall(sentence) if w.lower() not in _ARTICLES]
    return tuple(words[:SKELETON_LEN])


def _opener(sentence: str) -> str | None:
    words = _WORD.findall(sentence)
    if not words:
        return None
    first = words[0].lower()
    return None if first in _FUNCTION_WORDS else first


def _structural_findings(lines: list[tuple[int, str]]) -> list[Finding]:
    sentences = _sentences(lines)
    findings: list[Finding] = []

    # Rule 1: echoing sentence runs. Only sentences that carry a full skeleton count.
    run: list[Sentence] = []
    prev_skel: tuple[str, ...] | None = None
    for s in sentences:
        skel = _skeleton(s.text) if s is not _BREAK else None
        if skel is not None and len(skel) == SKELETON_LEN and skel == prev_skel:
            run.append(s)
        else:
            if len(run) >= ECHO_RUN_MIN:
                findings.append(
                    Finding(
                        "echoing-run",
                        ADVISORY,
                        run[0].line,
                        run[0].col,
                        " | ".join(x.text for x in run),
                        f"rhythm rule 1: {len(run)} consecutive sentences share the skeleton {' '.join(prev_skel or ())!r}",
                    )
                )
            run = [s] if skel is not None else []
            prev_skel = skel

    # Rule 2: repeated sentence openers on a non-function word.
    run = []
    prev_open: str | None = None
    for s in sentences:
        op = _opener(s.text) if s is not _BREAK else None
        if op is not None and op == prev_open:
            run.append(s)
        else:
            if len(run) >= OPENER_RUN_MIN:
                findings.append(
                    Finding(
                        "repeated-opener",
                        ADVISORY,
                        run[0].line,
                        run[0].col,
                        " | ".join(x.text for x in run),
                        f"rhythm rule 2: {len(run)} consecutive sentences open on {prev_open!r}",
                    )
                )
            run = [s] if op is not None else []
            prev_open = op

    # Rule 3: stacked rhetorical questions.
    run = []
    for s in sentences:
        if s is not _BREAK and s.text.endswith("?"):
            run.append(s)
        else:
            if len(run) >= QUESTION_RUN_MIN:
                findings.append(
                    Finding(
                        "stacked-questions",
                        ADVISORY,
                        run[0].line,
                        run[0].col,
                        " | ".join(x.text for x in run),
                        f"rhythm rule 3: {len(run)} consecutive question sentences",
                    )
                )
            run = []
    return findings


def detect(text: str) -> list[Finding]:
    """Return every finding in reading order (line, then column)."""
    lines = _prose_lines(text)
    found = _lexical_findings(lines) + _structural_findings(lines)
    return sorted(found, key=lambda f: (f.line, f.col, f.id))


def _read_input(arg: str) -> tuple[str, str]:
    if arg == "-":
        return "<stdin>", sys.stdin.read()
    path = Path(arg)
    if not path.is_file():
        raise FileNotFoundError(arg)
    return str(path), path.read_text(encoding="utf-8")


def _counts(findings: list[Finding]) -> dict[str, int]:
    return {
        DEFECT: sum(f.cls == DEFECT for f in findings),
        ADVISORY: sum(f.cls == ADVISORY for f in findings),
    }


def _render_human(source: str, findings: list[Finding]) -> str:
    if not findings:
        return f"{source}: no findings"
    out = [
        f"{source}:{f.line}:{f.col}: [{f.cls}] {f.id}: {f.span}"
        + (f"  ({f.rule})" if f.rule != "lexical" else "")
        for f in findings
    ]
    counts = _counts(findings)
    out.append(f"{source}: {counts[DEFECT]} defect, {counts[ADVISORY]} advisory")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect prose cliche patterns offline (stdlib only, advisory by default)."
    )
    parser.add_argument("source", help="file to scan, or - for stdin")
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit one JSON document on stdout instead of the human list",
    )
    parser.add_argument(
        "--fail-on",
        choices=(DEFECT, ADVISORY, "any"),
        default=None,
        help="exit 1 when a finding of this class is present (default: never)",
    )
    args = parser.parse_args(argv)
    try:
        source, text = _read_input(args.source)
    except FileNotFoundError as e:
        print(f"detect_prose_cliches: no such file: {e}", file=sys.stderr)
        return 2
    except UnicodeDecodeError as e:
        print(
            f"detect_prose_cliches: cannot decode input as UTF-8: {e}", file=sys.stderr
        )
        return 2
    findings = detect(text)
    counts = _counts(findings)
    if args.json:
        print(
            json.dumps(
                {
                    "source": source,
                    "counts": counts,
                    "findings": [f.as_dict() for f in findings],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(_render_human(source, findings))
    if args.fail_on == "any" and findings:
        return 1
    if args.fail_on in (DEFECT, ADVISORY) and counts[args.fail_on]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
