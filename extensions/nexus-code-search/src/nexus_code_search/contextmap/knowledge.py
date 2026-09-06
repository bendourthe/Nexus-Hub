"""Knowledge-map extractor.

Scans a folder of Markdown notes and compiles a committed `.nexus/KNOWLEDGE.md`
primer: key decisions, open questions, and a categorized note index. Each note
is classified by deterministic filename / heading / body heuristics into one of
decision (ADR), meeting, retrospective, spec, or research (else a plain note).

This is the mechanical half only - the same split the map / lint use. Narrative
synthesis (summarizing what a decision *means*) stays with the LLM-native
`solution-knowledge-base` skill; this ships no new catalog skill. Independent of
the code graph (it reads `.md` files, not `codegraph.db`), deterministic, and
writes only under `<root>/.nexus/`.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from nexus_code_search.contextmap.generator import _document, _read_source_hash
from nexus_code_search.contextmap.model import compute_source_hash

KNOWLEDGE_FILENAME = "KNOWLEDGE.md"
_EXCLUDE_DIRS = frozenset(
    {"node_modules", ".git", ".nexus", ".venv", "venv", "dist", "build", "__pycache__"}
)

# Discriminative signals per category: filename tokens (weight 3), heading
# phrases (weight 2), body phrases (weight 1). Highest total wins; 0 -> "note".
_CATEGORY_SIGNALS: dict[str, dict[str, tuple[str, ...]]] = {
    "decision": {
        "filename": ("adr", "decision"),
        "heading": ("decision", "consequences", "status"),
        "body": ("decided to", "chose ", "we will "),
    },
    "retro": {
        "filename": ("retro", "retrospective", "postmortem", "post-mortem"),
        "heading": ("what went well", "what went badly", "stop doing", "start doing"),
        "body": ("went well", "stop doing"),
    },
    "meeting": {
        "filename": ("meeting", "standup", "1-1", "one-on-one", "sync", "minutes"),
        "heading": ("attendees", "agenda", "action items"),
        "body": ("attendees:",),
    },
    "spec": {
        "filename": ("spec", "prd", "rfc", "design-doc", "design"),
        "heading": ("requirements", "goals", "non-goals", "user stories"),
        "body": ("acceptance criteria",),
    },
    "research": {
        "filename": ("research", "spike", "investigation"),
        "heading": ("findings", "references", "conclusion"),
        "body": ("investigated",),
    },
}
_CATEGORY_TITLES = {
    "decision": "Decisions",
    "meeting": "Meetings",
    "retro": "Retrospectives",
    "spec": "Specs",
    "research": "Research",
    "note": "Notes",
}
_CATEGORY_ORDER = ("decision", "meeting", "retro", "spec", "research", "note")

_HEADING_RE = re.compile(r"^#{1,6}\s+(.*\S)\s*$", re.MULTILINE)
_DECISION_STMT_RE = re.compile(
    r"(?im)^\s*(?:we\s+)?(?:decided to|chose\b.*|will\b.*|adopt(?:ed)?\b.*)"
)
_OPEN_Q_HEADINGS = ("open questions", "questions", "unresolved", "open issues")
_STANDALONE_Q_RE = re.compile(
    r"(?im)^\s*[-*]?\s*(?:TODO|TBD|FIXME|open question)\b[:\-]?\s*(.+)"
)


@dataclass(frozen=True)
class KnowledgeNote:
    path: str
    title: str
    category: str


@dataclass(frozen=True)
class Decision:
    title: str
    statement: str
    source: str


@dataclass(frozen=True)
class OpenQuestion:
    text: str
    source: str


@dataclass
class KnowledgeResult:
    root: str
    knowledge_path: str
    skipped: bool = False
    note_count: int = 0
    decision_count: int = 0
    open_question_count: int = 0
    source_hash: str = ""
    tokens: int = 0
    categories: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "root": self.root,
            "knowledge_path": self.knowledge_path,
            "skipped": self.skipped,
            "note_count": self.note_count,
            "decision_count": self.decision_count,
            "open_question_count": self.open_question_count,
            "source_hash": self.source_hash,
            "tokens": self.tokens,
            "categories": self.categories,
        }


def generate_knowledge_map(
    root: Path | str, notes_path: Path | str | None = None, *, force: bool = False
) -> KnowledgeResult:
    """Compile `<root>/.nexus/KNOWLEDGE.md` from the `.md` notes under
    ``notes_path`` (default: ``root``)."""
    root_path = Path(root).resolve()
    scan_root = Path(notes_path).resolve() if notes_path else root_path

    note_files = _find_notes(scan_root)
    source_hash = compute_source_hash(
        [(_relative(root_path, p), f"note:{_hash_file(p)}") for p in note_files]
    )

    knowledge_path = root_path / ".nexus" / KNOWLEDGE_FILENAME
    if (
        not force
        and knowledge_path.exists()
        and _read_source_hash(knowledge_path) == source_hash
    ):
        return _skip_result(root_path, knowledge_path, source_hash, note_files)

    notes, decisions, questions = _parse_notes(root_path, note_files)
    body = _render_body(notes, decisions, questions)
    document = _document("# Knowledge Map", body, source_hash)
    _write(knowledge_path, document, root_path)

    categories = {
        _CATEGORY_TITLES[cat]: sum(1 for n in notes if n.category == cat)
        for cat in _CATEGORY_ORDER
        if any(n.category == cat for n in notes)
    }
    return KnowledgeResult(
        root=str(root_path),
        knowledge_path=str(knowledge_path),
        skipped=False,
        note_count=len(notes),
        decision_count=len(decisions),
        open_question_count=len(questions),
        source_hash=source_hash,
        tokens=_token_header(knowledge_path),
        categories=categories,
    )


# --- Scanning + parsing -----------------------------------------------------


def _find_notes(scan_root: Path) -> list[Path]:
    if scan_root.is_file():
        return [scan_root] if scan_root.suffix.lower() == ".md" else []
    found = [
        p
        for p in scan_root.rglob("*.md")
        if not any(part in _EXCLUDE_DIRS for part in p.parts)
    ]
    return sorted(found)


def _parse_notes(
    root: Path, note_files: list[Path]
) -> tuple[list[KnowledgeNote], list[Decision], list[OpenQuestion]]:
    notes: list[KnowledgeNote] = []
    decisions: list[Decision] = []
    questions: list[OpenQuestion] = []
    seen_questions: set[str] = set()

    for path in note_files:
        text = _read(path)
        rel = _relative(root, path)
        frontmatter, body = _split_frontmatter(text)
        headings = _HEADING_RE.findall(body)
        title = frontmatter.get("title") or (headings[0] if headings else path.stem)
        category = _classify(path.name, headings, body)
        notes.append(KnowledgeNote(path=rel, title=title, category=category))

        if category == "decision":
            decisions.append(
                Decision(title=title, statement=_decision_statement(body), source=rel)
            )
        for question in _open_questions(body):
            key = question.lower()
            if key not in seen_questions:
                seen_questions.add(key)
                questions.append(OpenQuestion(text=question, source=rel))

    notes.sort(key=lambda n: (n.category, n.path))
    return notes, decisions, questions


def _classify(filename: str, headings: list[str], body: str) -> str:
    fname = filename.lower()
    heading_text = "\n".join(h.lower() for h in headings)
    body_l = body.lower()
    best, best_score = "note", 0
    for category, signals in _CATEGORY_SIGNALS.items():
        score = 3 * sum(1 for t in signals["filename"] if t in fname)
        score += 2 * sum(1 for t in signals["heading"] if t in heading_text)
        score += sum(1 for t in signals["body"] if t in body_l)
        if score > best_score:
            best, best_score = category, score
    return best


def _decision_statement(body: str) -> str:
    """The paragraph under a `## Decision` heading, else a decision-verb line."""
    lines = body.splitlines()
    for idx, line in enumerate(lines):
        heading = _HEADING_RE.match(line)
        if heading and heading.group(1).strip().lower().startswith("decision"):
            for follow in lines[idx + 1 :]:
                if follow.strip() and not follow.lstrip().startswith("#"):
                    return follow.strip()
                if follow.lstrip().startswith("#"):
                    break
    match = _DECISION_STMT_RE.search(body)
    return match.group(0).strip() if match else ""


def _open_questions(body: str) -> list[str]:
    found: list[str] = []
    lines = body.splitlines()
    in_section = False
    for line in lines:
        heading = _HEADING_RE.match(line)
        if heading:
            in_section = heading.group(1).strip().lower() in _OPEN_Q_HEADINGS
            continue
        if in_section:
            item = re.match(r"^\s*[-*]\s+(.*\S)", line)
            if item:
                found.append(item.group(1).strip())
    for match in _STANDALONE_Q_RE.finditer(body):
        found.append(match.group(1).strip())
    return found


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block = text[3:end]
    body = text[end + 4 :]
    meta: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip().lower()] = value.strip().strip("\"'")
    return meta, body


# --- Rendering --------------------------------------------------------------


def _render_body(
    notes: list[KnowledgeNote],
    decisions: list[Decision],
    questions: list[OpenQuestion],
) -> list[str]:
    lines = [
        "A deterministic knowledge primer compiled from the project's Markdown "
        "notes by `nexus-code-search`. Regenerate with `nexus-hub map --knowledge`.",
        "",
        "## Key Decisions",
        "",
    ]
    if decisions:
        for decision in decisions:
            statement = f": {decision.statement}" if decision.statement else ""
            lines.append(f"- **{decision.title}**{statement} (`{decision.source}`)")
    else:
        lines.append("No decision records detected.")

    lines.extend(["", "## Open Questions", ""])
    if questions:
        for question in questions:
            lines.append(f"- {question.text} (`{question.source}`)")
    else:
        lines.append("No open questions detected.")

    lines.extend(["", "## Notes by Category", ""])
    if not notes:
        lines.append("No Markdown notes found.")
        return lines
    for category in _CATEGORY_ORDER:
        in_category = [n for n in notes if n.category == category]
        if not in_category:
            continue
        lines.append(f"### {_CATEGORY_TITLES[category]}")
        lines.append("")
        for note in in_category:
            lines.append(f"- [{note.title}](../{note.path})")
        lines.append("")
    return lines


# --- Helpers ----------------------------------------------------------------


def _skip_result(
    root: Path, knowledge_path: Path, source_hash: str, note_files: list[Path]
) -> KnowledgeResult:
    return KnowledgeResult(
        root=str(root),
        knowledge_path=str(knowledge_path),
        skipped=True,
        note_count=len(note_files),
        source_hash=source_hash,
        tokens=_token_header(knowledge_path),
    )


def _write(path: Path, content: str, root: Path) -> None:
    nexus_dir = (root / ".nexus").resolve()
    if not path.resolve().is_relative_to(nexus_dir):
        raise RuntimeError(f"refusing to write outside .nexus/: {path.resolve()}")
    nexus_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _token_header(path: Path) -> int:
    for line in _read(path).splitlines():
        if line.startswith("<!-- nexus-context-map"):
            match = re.search(r"tokens:\s*(\d+)", line)
            if match:
                return int(match.group(1))
    return 0


def _hash_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except OSError:
        return "0"


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
