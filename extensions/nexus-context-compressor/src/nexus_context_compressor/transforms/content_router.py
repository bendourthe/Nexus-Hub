"""ContentRouter: detect content type and dispatch to the right compressor.

A single message or tool output is rarely homogeneous: an agent transcript
interleaves prose with fenced code blocks, a tool dump may be a JSON array of
records, a log stream is line-oriented text. Compressing all of it with one
strategy wastes the gains -- SmartCrusher is built for record arrays,
CodeCompressor for source. ContentRouter classifies each segment and sends it to
the strategy that fits, leaving everything else untouched, then reassembles the
pieces in order.

What it routes (Phase 3):

* **JSON array** -> :func:`~nexus_context_compressor.transforms.smart_crusher.smart_crush`
  (deterministic record dedup), reserialized in place.
* **Code** -> :func:`~nexus_context_compressor.transforms.code_compressor.compress_code`
  (AST-aware body elision). Fenced blocks carry a language hint; unfenced code is
  sniffed. CodeCompressor no-ops on anything that is not really code, so an
  over-eager code classification can never mangle prose.
* **JSON object, log, plain text** -> passed through unchanged. (Free-text token
  dropping is the optional, default-off Phase 6 ML module, not this router.)

Mixed content is split on fenced code blocks (`````lang ... `````),
each segment routed independently, and the original text between and around the
fences preserved byte-for-byte so non-code prose is never disturbed.

Local-first and deterministic: no outbound call, no clock, no randomness. The CCR
``store`` seam is threaded through to whichever strategy drops data, so routed
compression stays reversible exactly as the direct strategies are.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from ..tokens import count_tokens
from .code_compressor import CodeCompressorConfig, compress_code
from .smart_crusher import SmartCrusherConfig, smart_crush

if TYPE_CHECKING:
    from ..ccr.store import CCRWriter


class ContentType(str, Enum):
    """The content classes the router distinguishes.

    A ``str`` enum so a value compares equal to its name string in reports and
    tests (``ContentType.CODE == "code"``).
    """

    JSON_ARRAY = "json_array"
    JSON_OBJECT = "json_object"
    CODE = "code"
    LOG = "log"
    TEXT = "text"


@dataclass(frozen=True)
class RouterConfig:
    """Tunables for routing, delegating to each strategy's own config.

    Attributes:
        smart_crusher: config passed to SmartCrusher for JSON arrays.
        code_compressor: config passed to CodeCompressor for code.
    """

    smart_crusher: SmartCrusherConfig = field(default_factory=SmartCrusherConfig)
    code_compressor: CodeCompressorConfig = field(default_factory=CodeCompressorConfig)


@dataclass
class Segment:
    """One routed slice of the input.

    Attributes:
        content_type: how the slice was classified.
        is_code_fence: whether the slice came from a fenced code block.
        language: the code language (fence hint or sniffed), when applicable.
        tokens_before / tokens_after: per-segment token accounting.
    """

    content_type: ContentType
    is_code_fence: bool = False
    language: str | None = None
    tokens_before: int = 0
    tokens_after: int = 0


@dataclass
class RouteResult:
    """The outcome of routing one blob.

    Attributes:
        text: the reassembled, compressed text.
        segments: per-segment classification + metrics, in order.
        tokens_before / tokens_after: whole-blob token accounting.
    """

    text: str
    segments: list[Segment] = field(default_factory=list)
    tokens_before: int = 0
    tokens_after: int = 0

    @property
    def ratio(self) -> float:
        """Fraction of tokens retained (``tokens_after / tokens_before``)."""
        if self.tokens_before <= 0:
            return 1.0
        return self.tokens_after / self.tokens_before


# Fenced code block: ``` or ~~~ with an optional language word, body, close fence.
# DOTALL so the body spans lines; non-greedy so adjacent fences do not merge.
_FENCE_RE = re.compile(
    r"(?P<fence>```|~~~)(?P<lang>[^\n`]*)\n(?P<body>.*?)(?P=fence)",
    re.DOTALL,
)

# A line that looks like a log entry: a leading level token or a leading
# timestamp/date. Used only to *classify* (logs pass through unchanged in Phase 3).
_LOG_LINE_RE = re.compile(
    r"^\s*(?:"
    r"\[?(?:TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\]?\b"
    r"|\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}"
    r"|\d{2}:\d{2}:\d{2}\b"
    r")",
    re.IGNORECASE,
)

# Strong code signals for an UNFENCED plain segment. Conservative on purpose;
# CodeCompressor is the backstop if a non-code segment slips through.
_CODE_HINT_RE = re.compile(
    r"^\s*(?:def|class|import|from|func|fn|public|private|export)\s"
    r"|function\s+\w+\s*\(|=>",
    re.MULTILINE,
)


def classify(text: str) -> ContentType:
    """Classify a (non-fenced) text blob into a :class:`ContentType`.

    Order matters: a well-formed JSON array/object wins first (it is unambiguous),
    then log streams (line-oriented level/timestamp prefixes), then code (strong
    structural signals), else plain text. Never raises.
    """
    if not isinstance(text, str):
        return ContentType.TEXT
    stripped = text.strip()
    if not stripped:
        return ContentType.TEXT
    if stripped[0] in "[{":
        try:
            parsed = json.loads(stripped)
        except (ValueError, TypeError):
            parsed = None
        if isinstance(parsed, list):
            return ContentType.JSON_ARRAY
        if isinstance(parsed, dict):
            return ContentType.JSON_OBJECT
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) >= 3:
        log_like = sum(1 for ln in lines if _LOG_LINE_RE.match(ln))
        if log_like >= max(3, int(0.6 * len(lines))):
            return ContentType.LOG
    if _CODE_HINT_RE.search(text):
        return ContentType.CODE
    return ContentType.TEXT


def _route_json_array(text: str, config: RouterConfig, store: CCRWriter | None) -> str:
    """Crush a JSON-array segment and reserialize it; pass through on any error."""
    try:
        records = json.loads(text)
    except (ValueError, TypeError):
        return text
    if not isinstance(records, list):
        return text
    result = smart_crush(records, config.smart_crusher, store=store)
    # 2-space indent: readable and stable; the crushed array interleaves kept
    # records with ``{"_ccr_dropped": "<<ccr:...>>"}`` markers, which serialize fine.
    return json.dumps(result.records, indent=2, ensure_ascii=False)


def _route_code(
    text: str, language: str | None, config: RouterConfig, store: CCRWriter | None
) -> str:
    """Compress a code segment; CodeCompressor returns it unchanged if not code."""
    return compress_code(
        text, language, config=config.code_compressor, store=store
    ).code


def _route_by_type(
    text: str,
    ctype: ContentType,
    lang: str | None,
    config: RouterConfig,
    store: CCRWriter | None,
) -> str:
    """Dispatch one segment to the strategy for its type; passthrough otherwise."""
    if ctype is ContentType.JSON_ARRAY:
        return _route_json_array(text, config, store)
    if ctype is ContentType.CODE:
        return _route_code(text, lang, config, store)
    return text


def _classify_fence(lang: str | None, body: str) -> ContentType:
    """Classify a fenced block: JSON when the hint or body says so, else code.

    A ```` ```json ```` block (or a fence whose body is a JSON array) routes to
    SmartCrusher; every other fence routes to CodeCompressor, which no-ops if the
    body is not actually code.
    """
    if lang and lang.strip().lower() in ("json", "json5", "jsonc"):
        if classify(body) is ContentType.JSON_ARRAY:
            return ContentType.JSON_ARRAY
        return ContentType.JSON_OBJECT
    if classify(body) is ContentType.JSON_ARRAY:
        return ContentType.JSON_ARRAY
    return ContentType.CODE


def route(
    content: str,
    *,
    config: RouterConfig | None = None,
    store: CCRWriter | None = None,
) -> RouteResult:
    """Split ``content`` on fenced code blocks, route each segment, reassemble.

    Args:
        content: the message or tool output to compress.
        config: tunables; defaults to :class:`RouterConfig`.
        store: an optional CCR write seam, threaded to SmartCrusher and
            CodeCompressor so routed drops stay reversible. ``None`` keeps the
            call side-effect-free.

    Returns:
        A :class:`RouteResult` with the reassembled compressed text, per-segment
        classification + metrics, and whole-blob token accounting. Prose between
        and around fences is preserved exactly.
    """
    config = config or RouterConfig()
    content = content if isinstance(content, str) else str(content)
    tokens_before = count_tokens(content)

    out: list[str] = []
    segments: list[Segment] = []
    cursor = 0

    def handle_plain(chunk: str) -> None:
        """Route a non-fenced chunk classified as a whole (JSON array / code / text).

        A standalone JSON array or a code dump that is the entire chunk is routed;
        prose (and a JSON array buried inside prose) passes through untouched. The
        whole-chunk rule is deliberately conservative: it never risks cutting prose
        apart, and the common shapes (a tool dump that *is* a JSON array, a fenced
        block) are handled exactly.
        """
        if not chunk:
            return
        ctype = classify(chunk)
        seg_before = count_tokens(chunk)
        routed = _route_by_type(chunk, ctype, None, config, store)
        out.append(routed)
        segments.append(
            Segment(
                content_type=ctype,
                is_code_fence=False,
                language=None,
                tokens_before=seg_before,
                tokens_after=count_tokens(routed),
            )
        )

    for match in _FENCE_RE.finditer(content):
        handle_plain(content[cursor : match.start()])
        fence = match.group("fence")
        lang = match.group("lang").strip() or None
        body = match.group("body")
        seg_before = count_tokens(body)
        ctype = _classify_fence(lang, body)
        compressed = _route_by_type(body, ctype, lang, config, store)
        # Re-wrap with the original fence + language so the block round-trips.
        out.append(f"{fence}{match.group('lang')}\n{compressed}{fence}")
        segments.append(
            Segment(
                content_type=ctype,
                is_code_fence=True,
                language=lang,
                tokens_before=seg_before,
                tokens_after=count_tokens(compressed),
            )
        )
        cursor = match.end()

    handle_plain(content[cursor:])

    text = "".join(out)
    return RouteResult(
        text=text,
        segments=segments,
        tokens_before=tokens_before,
        tokens_after=count_tokens(text),
    )
