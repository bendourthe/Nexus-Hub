"""Optional signature-rule analyzer (detection class 14: malware / web shell /
cryptominer / exploit), reverse-engineered as a self-contained pure-Python
matcher.

Rather than wrap an external native rule-matching binding (which would add a
heavyweight optional dependency and a copied-signature surface), this module
re-implements the small slice of the rule language Nexus-Hub needs -- text and
regex strings with a simple ``any of them`` / ``all of them`` / ``N of them``
(or ``$a and/or $b``) condition -- in pure Python. The rules themselves are
re-authored from public malware / web-shell / cryptominer knowledge and ship as
bundled ``.yar`` files under ``data/signature_rules/``; no signature text is
copied from any external rule set (Reverse-Engineering Attribution Rule).

The module is OPT-IN (``--yara`` / ``enable_signatures=True``) and makes no
network call. It is fence-aware on Markdown -- a web-shell example inside a
fenced code block in a SKILL.md is documentation, not a payload, so it is
suppressed exactly as the text analyzers suppress their patterns. When the
bundled rules cannot be loaded the analyzer degrades gracefully: it reports
itself skipped and the rest of the scan is unaffected.
"""

from __future__ import annotations

import importlib.resources as resources
import re
from dataclasses import dataclass

from ..fences import iter_lines_with_fence
from ..types import Finding, Severity
from .base import FileUnit, make_finding

# Directory of bundled rule files, relative to the package root.
_RULES_PACKAGE = "nexus_skill_scanner"
_RULES_SUBPATH = ("data", "signature_rules")


@dataclass(frozen=True)
class SignatureString:
    """One named string of a rule: a compiled regex (literals are escaped)."""

    identifier: str
    regex: re.Pattern[str]


@dataclass(frozen=True)
class SignatureRule:
    """A parsed rule: named strings plus a condition over which ones matched."""

    name: str
    severity: Severity
    description: str
    detection_class: int
    strings: tuple[SignatureString, ...]
    condition: str

    def string_ids(self) -> list[str]:
        return [s.identifier for s in self.strings]


# ---------------------------------------------------------------------------
# Rule parsing
# ---------------------------------------------------------------------------

_RULE_HEADER_RE = re.compile(r"^rule\s+([A-Za-z_]\w*)\s*\{?\s*$")
_STRING_DEF_RE = re.compile(r"^\$(\w+)\s*=\s*(.*)$")
_CONDITION_TOKEN_RE = re.compile(r"\$\w+|\(|\)|\band\b|\bor\b|\bnot\b|\bany\b|\ball\b|\bof\b|\bthem\b|\d+")


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _unescape(literal: str) -> str:
    return literal.replace('\\"', '"').replace("\\\\", "\\")


def _parse_string_def(text: str) -> SignatureString | None:
    """Parse a ``$id = "literal" [nocase]`` or ``$id = /regex/ [nocase]`` line."""
    m = _STRING_DEF_RE.match(text)
    if not m:
        return None
    identifier = "$" + m.group(1)
    rhs = m.group(2).strip()
    flags = 0
    if rhs.startswith('"'):
        end = rhs.rfind('"')
        if end <= 0:
            return None
        literal = _unescape(rhs[1:end])
        modifiers = rhs[end + 1:]
        if "nocase" in modifiers:
            flags |= re.IGNORECASE
        return SignatureString(identifier, re.compile(re.escape(literal), flags))
    if rhs.startswith("/"):
        end = rhs.rfind("/")
        if end <= 0:
            return None
        body = rhs[1:end]
        modifiers = rhs[end + 1:]
        if "nocase" in modifiers:
            flags |= re.IGNORECASE
        try:
            return SignatureString(identifier, re.compile(body, flags))
        except re.error:
            return None
    return None


def parse_rules(text: str) -> list[SignatureRule]:
    """Parse the bundled rule mini-syntax into ``SignatureRule`` objects.

    The syntax is a deliberately small subset: a ``rule NAME { ... }`` block
    with ``meta:`` key/value lines, ``strings:`` definitions, and a single
    ``condition:`` expression. Anything the parser cannot make sense of is
    skipped rather than raised -- a malformed rule never aborts a scan.
    """
    rules: list[SignatureRule] = []
    lines = text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        header = _RULE_HEADER_RE.match(lines[i].strip())
        if not header:
            i += 1
            continue
        name = header.group(1)
        i += 1
        if i < n and lines[i].strip() == "{":
            i += 1
        section: str | None = None
        meta: dict[str, str] = {}
        strings: list[SignatureString] = []
        condition_parts: list[str] = []
        while i < n:
            stripped = lines[i].strip()
            if stripped == "}":
                i += 1
                break
            if stripped in ("meta:", "strings:", "condition:"):
                section = stripped[:-1]
            elif not stripped or stripped.startswith("//"):
                pass
            elif section == "meta":
                key, _, val = stripped.partition("=")
                meta[key.strip()] = _unquote(val)
            elif section == "strings":
                parsed = _parse_string_def(stripped)
                if parsed is not None:
                    strings.append(parsed)
            elif section == "condition":
                condition_parts.append(stripped)
            i += 1
        try:
            severity = Severity.from_label(meta.get("severity", "high"))
        except ValueError:
            severity = Severity.HIGH
        try:
            detection_class = int(meta.get("detection_class", "14"))
        except ValueError:
            detection_class = 14
        rules.append(
            SignatureRule(
                name=name,
                severity=severity,
                description=meta.get("description", name.replace("_", " ")),
                detection_class=detection_class,
                strings=tuple(strings),
                condition=" ".join(condition_parts).strip() or "any of them",
            )
        )
    return rules


class _ConditionError(Exception):
    """Raised when a condition cannot be parsed; the caller degrades safely."""


def _tokenize_condition(condition: str) -> list[tuple[str, object]]:
    """Lex a condition into ``(kind, value)`` tokens.

    The multi-word quantifiers ``any of them`` / ``all of them`` / ``N of them``
    are collapsed into a single ``("quant", "any" | "all" | <int>)`` token so the
    parser sees them as atoms.
    """
    raw = _CONDITION_TOKEN_RE.findall(condition.lower())
    tokens: list[tuple[str, object]] = []
    i, n = 0, len(raw)
    while i < n:
        tok = raw[i]
        # Collapse "<any|all|NUMBER> of them" into one quantifier atom.
        if (tok in ("any", "all") or tok.isdigit()) and i + 2 < n and raw[i + 1] == "of" and raw[i + 2] == "them":
            value: object = int(tok) if tok.isdigit() else tok
            tokens.append(("quant", value))
            i += 3
            continue
        if tok.startswith("$"):
            tokens.append(("id", tok))
        elif tok in ("and", "or", "not"):
            tokens.append(("op", tok))
        elif tok in ("(", ")"):
            tokens.append((tok, tok))
        else:
            # A bare "any"/"all"/number/"of"/"them" outside the quantifier form
            # is malformed -- signal it so the caller falls back safely.
            raise _ConditionError(f"unexpected token: {tok!r}")
        i += 1
    return tokens


class _ConditionParser:
    """Recursive-descent evaluator for a rule condition.

    Grammar (precedence low to high)::

        expr    := or_expr
        or_expr := and_expr ("or" and_expr)*
        and_expr:= unary ("and" unary)*
        unary   := "not" unary | atom
        atom    := "(" expr ")" | quantifier | "$id"
    """

    def __init__(self, tokens: list[tuple[str, object]], matched: set[str], all_ids: set[str]) -> None:
        self._tokens = tokens
        self._pos = 0
        self._matched = matched
        self._all_ids = all_ids

    def _peek(self) -> tuple[str, object] | None:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _advance(self) -> tuple[str, object]:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def parse(self) -> bool:
        value = self._or_expr()
        if self._pos != len(self._tokens):
            raise _ConditionError("trailing tokens")
        return value

    def _or_expr(self) -> bool:
        value = self._and_expr()
        while self._peek() == ("op", "or"):
            self._advance()
            value = self._and_expr() or value
        return value

    def _and_expr(self) -> bool:
        value = self._unary()
        while self._peek() == ("op", "and"):
            self._advance()
            value = self._unary() and value
        return value

    def _unary(self) -> bool:
        if self._peek() == ("op", "not"):
            self._advance()
            return not self._unary()
        return self._atom()

    def _atom(self) -> bool:
        tok = self._peek()
        if tok is None:
            raise _ConditionError("unexpected end of condition")
        kind, value = tok
        if kind == "(":
            self._advance()
            inner = self._or_expr()
            if self._peek() != (")", ")"):
                raise _ConditionError("missing closing parenthesis")
            self._advance()
            return inner
        if kind == "id":
            self._advance()
            return value in self._matched
        if kind == "quant":
            self._advance()
            if value == "any":
                return len(self._matched) >= 1
            if value == "all":
                return bool(self._all_ids) and self._matched >= self._all_ids
            return len(self._matched) >= int(value)  # type: ignore[arg-type]
        raise _ConditionError(f"unexpected token: {tok!r}")


def evaluate_condition(condition: str, matched: set[str], all_ids: list[str]) -> bool:
    """Evaluate a rule condition over the set of matched string identifiers.

    Supports ``and`` / ``or`` / ``not`` with parentheses and the ``any of them``
    / ``all of them`` / ``N of them`` quantifiers. A condition the parser cannot
    make sense of degrades to the safe ``any of them`` default rather than
    raising -- a malformed rule never aborts a scan.
    """
    try:
        tokens = _tokenize_condition(condition)
        if not tokens:
            return len(matched) >= 1
        return _ConditionParser(tokens, matched, set(all_ids)).parse()
    except _ConditionError:
        return len(matched) >= 1


# ---------------------------------------------------------------------------
# Rule loading
# ---------------------------------------------------------------------------


def load_bundled_rules() -> list[SignatureRule]:
    """Load every ``.yar`` rule file bundled under ``data/signature_rules/``.

    Returns an empty list (rather than raising) if the directory is missing or
    unreadable; the analyzer then reports itself skipped.
    """
    rules: list[SignatureRule] = []
    try:
        root = resources.files(_RULES_PACKAGE)
        for part in _RULES_SUBPATH:
            root = root / part
        if not root.is_dir():
            return []
        for entry in sorted(root.iterdir(), key=lambda e: e.name):
            if entry.name.endswith(".yar"):
                rules.extend(parse_rules(entry.read_text(encoding="utf-8")))
    except (FileNotFoundError, ModuleNotFoundError, OSError, NotADirectoryError):
        return []
    return rules


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------


class SignatureAnalyzer:
    """Runs the bundled signature rules over a file unit, fence-aware.

    Only instantiated when the optional module is enabled (``--yara``); the
    default scan never constructs it, so the deterministic Phase 6 gate is
    unaffected. Exposes ``skipped`` so the scanner can surface a graceful-degrade
    note when no rules could be loaded.
    """

    name = "signatures"

    def __init__(self, rules: list[SignatureRule] | None = None) -> None:
        self.skipped: list[str] = []
        self._rules = load_bundled_rules() if rules is None else rules
        if not self._rules:
            self.skipped.append("yara (no signature rules available)")

    def analyze(self, unit: FileUnit) -> list[Finding]:
        if not self._rules:
            return []
        # Per-rule accumulator: matched string ids and the earliest match line.
        matched: list[set[str]] = [set() for _ in self._rules]
        first_line = [0] * len(self._rules)
        first_snippet = [""] * len(self._rules)
        for line_no, line, in_fence in iter_lines_with_fence(unit.text):
            # Suppress fenced Markdown -- a documented payload example is not a
            # payload (the producer-catalog nuance shared with the text analyzers).
            if unit.is_markdown and in_fence:
                continue
            for idx, rule in enumerate(self._rules):
                for string in rule.strings:
                    if string.identifier in matched[idx]:
                        continue
                    if string.regex.search(line):
                        matched[idx].add(string.identifier)
                        if first_line[idx] == 0:
                            first_line[idx] = line_no
                            first_snippet[idx] = line
        findings: list[Finding] = []
        for idx, rule in enumerate(self._rules):
            if evaluate_condition(rule.condition, matched[idx], rule.string_ids()):
                findings.append(
                    make_finding(
                        detection_class=rule.detection_class,
                        severity=rule.severity,
                        title=f"Signature match: {rule.name}",
                        message=rule.description,
                        unit=unit,
                        line=first_line[idx],
                        snippet=first_snippet[idx],
                        analyzer=self.name,
                    )
                )
        return findings
