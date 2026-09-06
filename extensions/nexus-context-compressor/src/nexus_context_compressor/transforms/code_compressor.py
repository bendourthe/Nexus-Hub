"""CodeCompressor: AST-aware code body elision.

Source code spends most of its tokens on function and method *bodies*, while the
information a reader (or an agent) needs to navigate a file lives in its
*structure*: the imports, the signatures, the decorators, the type annotations,
and the class skeleton. CodeCompressor keeps that structure verbatim and
replaces each function/method body with a single elision marker, leaving a
faithful skeleton at a fraction of the tokens. Bodies large enough to be worth
fetching back are dropped behind a reversible ``<<ccr:HASH N_rows>>`` marker (the
same CCR mechanism SmartCrusher uses) and persisted to the store, so the
compression is non-lossy; smaller bodies get a plain, non-retrievable elision
note.

Two strategies, picked automatically:

1. **AST (preferred).** Reuses the tree-sitter extractors already vendored by
   ``extensions/nexus-code-search`` -- the engine does NOT re-vendor grammars.
   ``nexus_code_search.extraction.parse_file`` returns function/method nodes with
   exact line ranges, which is the precise, string-aware way to find a body. Used
   for every language ``nexus-code-search`` covers (Python, TypeScript/TSX, Go,
   Rust, Java, C#, Ruby, PHP, C, C++, Swift, Kotlin) when the sibling package is
   importable.
2. **Regex/structural (fallback).** A deterministic, dependency-free elider for
   when the AST infra is absent (sibling not installed, tree-sitter missing) or
   the language is unsupported. Handles indentation-delimited (Python) and
   brace-delimited (C-family, TS/JS) sources; other shapes are left unchanged
   rather than risk a bad cut.

The key structural trick is that the compressor never enumerates what to *keep*.
It copies every line and removes only the interior of each innermost
function/method body. Decorators sit above a node's start line, imports are their
own lines, class headers and signatures are outside any body -- so all of them
survive automatically, and there is no "did I remember to keep X?" failure mode.

Local-first and deterministic: no outbound call, no network, no clock, no
randomness. The same source always yields the same skeleton and the same marker
hashes. Reference behavior: ``docs/releases/v3/v3.2/comparisons/v3.2.0-comparison-headroom.md`` Section 5a
item 3.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from ..ccr.marker import format_marker
from ..tokens import count_tokens

if TYPE_CHECKING:
    from ..ccr.store import CCRWriter

# Number of hex chars kept from the content hash in a CCR marker. Matches
# SmartCrusher's ``_HASH_LEN`` and the 12-char width the marker grammar expects
# (see ``ccr.marker``), so a code body and a JSON span are addressed alike.
_HASH_LEN = 12


class _Family(Enum):
    """How a language delimits a function body, which drives header/footer detection.

    * ``INDENT`` -- the body is the indented block after a ``:``-terminated header
      (Python). No closing token; the body runs to the node's last line.
    * ``BRACE`` -- the body is wrapped in ``{ ... }`` (TS/JS, Go, Rust, Java, C#,
      C/C++, PHP, Swift, Kotlin). The closing ``}`` line is kept so the skeleton
      stays balanced.
    * ``GENERIC`` -- anything else (e.g. Ruby's ``def ... end``): keep the node's
      first line as the signature and elide the rest. Only reachable on the AST
      path, which supplies trustworthy node ranges; the regex fallback declines
      GENERIC rather than guess.
    """

    INDENT = "indent"
    BRACE = "brace"
    GENERIC = "generic"


# Language name (lowercased) -> a representative file extension. The AST parser
# (``parse_file``) dispatches on a path suffix, so a bare ``"python"`` hint from a
# fenced code block is mapped to ``.py`` before parsing.
_NAME_TO_EXT: dict[str, str] = {
    "python": ".py",
    "py": ".py",
    "typescript": ".ts",
    "ts": ".ts",
    "tsx": ".tsx",
    "javascript": ".js",
    "js": ".js",
    "jsx": ".jsx",
    "go": ".go",
    "golang": ".go",
    "rust": ".rs",
    "rs": ".rs",
    "java": ".java",
    "csharp": ".cs",
    "cs": ".cs",
    "c#": ".cs",
    "c": ".c",
    "cpp": ".cpp",
    "c++": ".cpp",
    "cxx": ".cpp",
    "php": ".php",
    "swift": ".swift",
    "kotlin": ".kt",
    "kt": ".kt",
    "ruby": ".rb",
    "rb": ".rb",
}

# File extension -> body-delimiting family + the line-comment prefix used to wrap
# an elision marker so the skeleton still reads as (mostly) valid source.
_EXT_TO_FAMILY: dict[str, _Family] = {
    ".py": _Family.INDENT,
    ".pyi": _Family.INDENT,
    ".rb": _Family.GENERIC,
}
for _brace_ext in (
    ".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".go", ".rs", ".java",
    ".cs", ".csx", ".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx",
    ".php", ".swift", ".kt", ".kts",
):
    _EXT_TO_FAMILY[_brace_ext] = _Family.BRACE

_COMMENT_PREFIX: dict[_Family, str] = {
    _Family.INDENT: "#",
    _Family.BRACE: "//",
    _Family.GENERIC: "#",
}

# Indentation step appended to the header indent when a body has no detectable
# leading whitespace to copy (degenerate case).
_INDENT_STEP: dict[_Family, str] = {
    _Family.INDENT: "    ",
    _Family.BRACE: "  ",
    _Family.GENERIC: "  ",
}

# Heuristic content sniffers for the regex fallback when no language is given.
_PY_HINT_RE = re.compile(r"^\s*(?:def|class|import|from)\s", re.MULTILINE)
_BRACE_HINT_RE = re.compile(r"(?:function\s|=>|^\s*(?:public|private|func|fn)\s|{\s*$)", re.MULTILINE)


@dataclass(frozen=True)
class CodeCompressorConfig:
    """Tunables for code body elision.

    Attributes:
        min_body_lines: bodies with fewer non-blank lines than this are kept
            verbatim (too small to be worth eliding).
        ccr_min_lines: elided bodies with at least this many lines get a
            *reversible* ``<<ccr:HASH N_rows>>`` marker and are persisted to the
            store; shorter elided bodies get a plain, non-retrievable note.
    """

    min_body_lines: int = 2
    ccr_min_lines: int = 4


@dataclass(frozen=True)
class ElidedBody:
    """A function/method body that was removed, addressable by its content hash.

    The CCR store persists ``lines`` keyed by ``hash`` so a consumer can resolve
    the ``<<ccr:HASH N_rows>>`` marker back to the exact source. ``count`` is the
    number of body lines elided (the ``N_rows`` in the marker).
    """

    hash: str
    count: int
    lines: list[str]


@dataclass
class CodeCompressResult:
    """The outcome of compressing one code blob.

    Attributes:
        code: the compressed source -- structure kept, bodies elided.
        dropped: the elided bodies large enough to be reversible (CCR-marked).
        language: the resolved language name (or ``None`` if undetected).
        strategy: which path ran -- ``"ast"``, ``"regex"``, or ``"none"`` (no
            elision: language unknown/unsupported on the fallback path, or the
            source had no elidable body).
        original_lines: line count of the input.
        kept_lines: line count of the output.
    """

    code: str
    dropped: list[ElidedBody] = field(default_factory=list)
    language: str | None = None
    strategy: str = "none"
    original_lines: int = 0
    kept_lines: int = 0
    tokens_before: int = 0
    tokens_after: int = 0

    @property
    def ratio(self) -> float:
        """Fraction of tokens retained (``tokens_after / tokens_before``)."""
        if self.tokens_before <= 0:
            return 1.0
        return self.tokens_after / self.tokens_before


# --- AST path --------------------------------------------------------------


@lru_cache(maxsize=1)
def _load_ast() -> tuple[Callable, dict] | None:
    """Import ``nexus-code-search``'s extraction API, or ``None`` if unavailable.

    Reuses the sibling extension's tree-sitter extractors rather than re-vendoring
    grammars. Tries a plain import first (works when ``nexus-code-search`` is
    installed, including the editable install both Nexus-Hub installers wire up);
    on failure, discovers the sibling's ``src/`` on disk (both packages live under
    ``extensions/``) and retries, so the AST path works from a bare checkout too.
    Cached: the (possibly path-mutating) load runs once per process.

    Returns:
        ``(parse_file, LANGUAGE_EXTRACTORS)`` on success, or ``None`` when the
        sibling package or tree-sitter is absent (triggering the regex fallback).
    """
    try:
        from nexus_code_search.extraction import parse_file
        from nexus_code_search.extraction.languages import LANGUAGE_EXTRACTORS

        return parse_file, LANGUAGE_EXTRACTORS
    except ImportError:
        pass
    # Sibling discovery: .../extensions/nexus-context-compressor/src/
    # nexus_context_compressor/transforms/code_compressor.py -> extensions/.
    try:
        extensions_dir = Path(__file__).resolve().parents[4]
        sibling_src = extensions_dir / "nexus-code-search" / "src"
        if sibling_src.is_dir():
            import sys

            if str(sibling_src) not in sys.path:
                sys.path.insert(0, str(sibling_src))
            from nexus_code_search.extraction import parse_file
            from nexus_code_search.extraction.languages import LANGUAGE_EXTRACTORS

            return parse_file, LANGUAGE_EXTRACTORS
    except Exception:
        # Any failure resolving or importing the sibling degrades to the
        # dependency-free regex fallback rather than raising.
        pass
    return None


def _ast_spans(source: str, ext: str) -> list[tuple[int, int]] | None:
    """Find innermost function/method body line ranges via the reused AST parser.

    Returns 1-indexed inclusive ``(start_line, end_line)`` node ranges for every
    function/method that is not nested inside another function/method (an inner
    closure is subsumed by eliding its enclosing body). Returns ``None`` when the
    AST infra is unavailable or the extension is unsupported, so the caller can
    fall back; an empty list means "supported, but nothing to elide".
    """
    loaded = _load_ast()
    if loaded is None:
        return None
    parse_file, extractors = loaded
    if ext not in extractors:
        return None
    try:
        nodes, _edges = parse_file(Path(f"snippet{ext}"), source.encode("utf-8"))
    except Exception:
        return None
    funcs = [
        (int(n.start_line), int(n.end_line))
        for n in nodes
        if getattr(n.kind, "value", n.kind) in ("function", "method")
        and int(n.end_line) > int(n.start_line)
    ]
    return _innermost_only(funcs)


def _innermost_only(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Drop any span fully contained inside another (keep only enclosing bodies).

    Eliding an enclosing function body removes its nested closures too, so a
    contained span must not be elided a second time. Sorted by start for a
    deterministic, non-overlapping result.
    """
    kept: list[tuple[int, int]] = []
    for start, end in sorted(spans):
        if any(s <= start and end <= e for s, e in kept):
            continue
        kept.append((start, end))
    return sorted(kept)


# --- Regex / structural fallback ------------------------------------------


def _regex_spans(lines: list[str], family: _Family) -> list[tuple[int, int]]:
    """Best-effort function-body ranges without an AST, for INDENT/BRACE families.

    Deterministic and intentionally conservative: it finds top-level and method
    ``def``/brace-function headers and the block each owns. GENERIC (and any
    shape it cannot read) yields no spans, so the source is returned unchanged
    rather than mis-cut.
    """
    if family is _Family.INDENT:
        return _regex_spans_indent(lines)
    if family is _Family.BRACE:
        return _regex_spans_brace(lines)
    return []


_DEF_RE = re.compile(r"^(\s*)(?:async\s+)?def\s")

# Brace-family lines that open a block but are NOT callables -- control flow whose
# body the fallback must not mistake for a function body. (The AST path needs no
# such guard; tree-sitter already knows a function from an ``if``.)
_CONTROL_RE = re.compile(r"^\s*(?:if|for|while|switch|catch|else|do|try)\b")


def _regex_spans_indent(lines: list[str]) -> list[tuple[int, int]]:
    """Indent-delimited (Python) header/body ranges by leading-whitespace width."""
    spans: list[tuple[int, int]] = []
    n = len(lines)
    i = 0
    while i < n:
        match = _DEF_RE.match(lines[i])
        if match is None:
            i += 1
            continue
        indent = len(match.group(1))
        start = i + 1  # 1-indexed
        j = i + 1
        end = i  # default: single-line def (no body)
        while j < n:
            stripped = lines[j].strip()
            if stripped == "":
                j += 1
                continue
            if len(lines[j]) - len(lines[j].lstrip()) <= indent:
                break  # dedented to the def's level or less -> body ended
            end = j  # 1-indexed end follows because j is 0-indexed and end stores it
            j += 1
        spans.append((start, end + 1))
        i = j
    return _innermost_only(spans)


def _regex_spans_brace(lines: list[str]) -> list[tuple[int, int]]:
    """Brace-delimited header/body ranges by tracking ``{``/``}`` depth.

    Treats any line that opens a block with ``{`` and looks like a callable header
    (contains ``(`` and ``)``) as a body start, then walks brace depth to the
    matching close. Strings/comments are not tokenized -- a known limitation of
    the dependency-free fallback; the AST path is string-aware and preferred.
    """
    spans: list[tuple[int, int]] = []
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]
        if (
            "{" in line
            and "(" in line
            and ")" in line
            and "}" not in line
            and not _CONTROL_RE.match(line)
        ):
            depth = line.count("{") - line.count("}")
            start = i + 1  # 1-indexed
            j = i + 1
            while j < n and depth > 0:
                depth += lines[j].count("{") - lines[j].count("}")
                j += 1
            end = j  # 1-indexed line of the matching close
            if end > start:
                spans.append((start, end))
            i = j
            continue
        i += 1
    return _innermost_only(spans)


# --- Shared elider ----------------------------------------------------------


def _content_hash(text: str) -> str:
    """Deterministic 12-hex-char content hash of an elided body (no salt/clock)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:_HASH_LEN]


def _strip_trailing_comment_py(line: str) -> str:
    """Drop a trailing ``# ...`` comment for the ``:``-terminator check.

    Naive (does not parse strings); a ``#`` inside a string literal on a def
    header line is rare enough to accept for the v1 deterministic heuristic, and
    the AST path avoids the question entirely.
    """
    hash_at = line.find("#")
    return line[:hash_at] if hash_at != -1 else line


def _header_end(lines: list[str], start: int, end: int, family: _Family) -> int | None:
    """1-indexed line at which the signature ends, or ``None`` if not found.

    INDENT: the first line in ``[start, end]`` ending with ``:`` (after dropping a
    trailing comment). BRACE: the first line containing the body-opening ``{``.
    GENERIC: ``start`` (keep just the first line).
    """
    if family is _Family.GENERIC:
        return start
    for idx in range(start, end + 1):
        line = lines[idx - 1]
        if family is _Family.INDENT:
            if _strip_trailing_comment_py(line).rstrip().endswith(":"):
                return idx
        else:  # BRACE
            if "{" in line:
                return idx
    return None


def _body_indent(lines: list[str], body_start: int, header_line: str, family: _Family) -> str:
    """Leading whitespace for the marker line: the first body line's, or a step in."""
    for idx in range(body_start, len(lines) + 1):
        body_line = lines[idx - 1]
        if body_line.strip():
            return body_line[: len(body_line) - len(body_line.lstrip())]
    header_indent = header_line[: len(header_line) - len(header_line.lstrip())]
    return header_indent + _INDENT_STEP[family]


def _elide(
    source: str,
    spans: list[tuple[int, int]],
    family: _Family,
    config: CodeCompressorConfig,
    store: CCRWriter | None,
) -> tuple[str, list[ElidedBody]]:
    """Rebuild ``source`` with each span's body interior replaced by one marker line.

    Walks the lines once: copies kept lines, and at each span emits the header,
    one marker line in place of the body, and (for BRACE) the closing-brace line.
    Bodies shorter than ``min_body_lines`` are kept verbatim. Returns the new
    source and the reversible (CCR-marked) bodies.
    """
    lines = source.split("\n")
    comment = _COMMENT_PREFIX[family]
    # Map body-start (1-indexed) -> (last-elided-line, marker_line, ElidedBody|None).
    actions: dict[int, tuple[int, str, ElidedBody | None]] = {}
    dropped: list[ElidedBody] = []
    for start, end in spans:
        header_end = _header_end(lines, start, end, family)
        if header_end is None:
            continue
        body_start = header_end + 1
        body_end = end - 1 if family is _Family.BRACE else end
        if body_end < body_start:
            continue  # empty body (e.g. ``def f(): pass`` on one line, ``{}``)
        body_lines = lines[body_start - 1 : body_end]
        if sum(1 for ln in body_lines if ln.strip()) < config.min_body_lines:
            continue  # too small to bother
        count = len(body_lines)
        indent = _body_indent(lines, body_start, lines[header_end - 1], family)
        if count >= config.ccr_min_lines:
            body_text = "\n".join(body_lines)
            span_hash = _content_hash(body_text)
            elided = ElidedBody(hash=span_hash, count=count, lines=list(body_lines))
            marker_line = f"{indent}{comment} {format_marker(span_hash, count)}"
            actions[body_start] = (body_end, marker_line, elided)
            dropped.append(elided)
        else:
            marker_line = f"{indent}{comment} ... ({count} lines elided)"
            actions[body_start] = (body_end, marker_line, None)

    out: list[str] = []
    idx = 1
    n = len(lines)
    while idx <= n:
        if idx in actions:
            body_end, marker_line, _ = actions[idx]
            out.append(marker_line)
            idx = body_end + 1
            continue
        out.append(lines[idx - 1])
        idx += 1

    if store is not None:
        for elided in dropped:
            store.put(elided.hash, elided.lines)
    return "\n".join(out), dropped


# --- Public entry point -----------------------------------------------------


def _resolve(language: str | None, source: str) -> tuple[str | None, str | None, _Family]:
    """Resolve ``(language_name, extension, family)`` from a hint or by sniffing.

    A hint may be a language name (``"python"``), a bare extension (``".ts"``), or
    a filename (``"app.tsx"``). With no hint, sniff Python vs brace from content;
    an unrecognized hint with no signal resolves to a ``GENERIC`` family with no
    extension (no AST, no regex elision).
    """
    if language:
        key = language.strip().lower()
        ext = None
        if key in _NAME_TO_EXT:
            ext = _NAME_TO_EXT[key]
        elif key.startswith("."):
            ext = key
        elif "." in key:
            ext = Path(key).suffix.lower()
        if ext is not None:
            return language, ext, _EXT_TO_FAMILY.get(ext, _Family.GENERIC)
        return language, None, _Family.GENERIC
    # No hint: sniff.
    if _PY_HINT_RE.search(source):
        return "python", ".py", _Family.INDENT
    if _BRACE_HINT_RE.search(source):
        return "javascript", ".js", _Family.BRACE
    return None, None, _Family.GENERIC


def compress_code(
    source: str,
    language: str | None = None,
    *,
    config: CodeCompressorConfig | None = None,
    store: CCRWriter | None = None,
) -> CodeCompressResult:
    """Compress code by eliding function/method bodies, keeping structure.

    Args:
        source: the code to compress.
        language: a language hint -- a name (``"python"``), an extension
            (``".ts"``), or a filename. Optional; sniffed from content if omitted.
        config: tunables; defaults to :class:`CodeCompressorConfig`.
        store: an optional CCR write seam (anything with ``put(hash, lines)``).
            When given, each reversibly-elided body is persisted so its
            ``<<ccr:HASH N_rows>>`` marker can be resolved back to the source; the
            returned result is identical either way. With ``store=None`` the call
            has no side effects.

    Returns:
        A :class:`CodeCompressResult`. The AST strategy is used when the reused
        ``nexus-code-search`` extractors cover the language; otherwise the
        dependency-free regex elider runs (INDENT/BRACE only). Unknown or
        unsupported shapes return the source unchanged with ``strategy="none"``.
    """
    config = config or CodeCompressorConfig()
    source = source if isinstance(source, str) else str(source)
    name, ext, family = _resolve(language, source)
    tokens_before = count_tokens(source)
    original_lines = source.count("\n") + 1 if source else 0

    spans: list[tuple[int, int]] | None = None
    strategy = "none"
    if ext is not None:
        ast_spans = _ast_spans(source, ext)
        if ast_spans is not None:
            spans = ast_spans
            strategy = "ast"
        elif family in (_Family.INDENT, _Family.BRACE):
            spans = _regex_spans(source.split("\n"), family)
            strategy = "regex"

    if not spans:
        return CodeCompressResult(
            code=source,
            dropped=[],
            language=name,
            strategy="none",
            original_lines=original_lines,
            kept_lines=original_lines,
            tokens_before=tokens_before,
            tokens_after=tokens_before,
        )

    compressed, dropped = _elide(source, spans, family, config, store)
    tokens_after = count_tokens(compressed)
    return CodeCompressResult(
        code=compressed,
        dropped=dropped,
        language=name,
        strategy=strategy if dropped or compressed != source else "none",
        original_lines=original_lines,
        kept_lines=compressed.count("\n") + 1 if compressed else 0,
        tokens_before=tokens_before,
        tokens_after=tokens_after,
    )
