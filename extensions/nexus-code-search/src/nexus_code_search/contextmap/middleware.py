"""Middleware detection and categorization.

Detects middleware registrations across the supported web frameworks and
categorizes each by a conservative name match into one of the plan's categories
(auth, rate-limit, cors, validation, logging, error-handling) or `other`:

- Express: `app.use(...)` / `router.use(...)` (optional leading path string).
- FastAPI: `app.add_middleware(XxxMiddleware, ...)`.
- Django: entries of the `MIDDLEWARE = [...]` list in a `settings` module.

Detection is precise (only real registration forms) so it does not emit a
middleware where there is none; an unrecognized name is categorized `other`
rather than dropped.
"""

from __future__ import annotations

import re
from pathlib import Path

from nexus_code_search.contextmap.model import MiddlewareInfo

# Express: `<obj>.use(` with an optional leading path-string arg, then the
# middleware callee identifier (possibly dotted, e.g. express.json).
_EXPRESS_USE = re.compile(
    r"""\b[A-Za-z_]\w*\.use\(\s*(?:["'][^"']*["']\s*,\s*)?([A-Za-z_][\w.]*)\s*[(),]"""
)
# FastAPI: `add_middleware(ClassName`.
_FASTAPI_ADD = re.compile(r"""\badd_middleware\(\s*([A-Za-z_]\w*)""")
# Django MIDDLEWARE list: capture the whole bracketed block, then its strings.
_DJANGO_BLOCK = re.compile(r"""MIDDLEWARE\s*=\s*\[(.*?)\]""", re.DOTALL)
_DJANGO_ITEM = re.compile(r"""["']([\w.]+)["']""")

# (substring token, category) checked in order; first match wins. Matched
# against the lowercased middleware name.
_CATEGORY_RULES = (
    ("cors", "cors"),
    ("ratelimit", "rate-limit"),
    ("rate-limit", "rate-limit"),
    ("rate_limit", "rate-limit"),
    ("throttle", "rate-limit"),
    ("slowdown", "rate-limit"),
    ("authenticat", "auth"),
    ("authoriz", "auth"),
    ("passport", "auth"),
    ("jwt", "auth"),
    ("csrf", "validation"),
    ("valid", "validation"),
    ("schema", "validation"),
    ("zod", "validation"),
    ("joi", "validation"),
    ("celebrate", "validation"),
    ("morgan", "logging"),
    ("winston", "logging"),
    ("pino", "logging"),
    ("logg", "logging"),
    ("error", "error-handling"),
    ("exception", "error-handling"),
    # "auth" last so it does not shadow "authorization"/"authentication" nuance
    # above, and so "author" in unrelated names is less likely (kept specific).
    ("auth", "auth"),
)

_PY_LANGS = frozenset({"python"})
_JS_LANGS = frozenset({"typescript", "tsx", "javascript", "jsx"})


def categorize_middleware(name: str) -> str:
    """Return the category for a middleware name (default `other`)."""
    lowered = name.lower()
    for token, category in _CATEGORY_RULES:
        if token in lowered:
            return category
    return "other"


def detect_middleware(
    root: Path, code_files: list[tuple[str, str]]
) -> list[MiddlewareInfo]:
    """Detect middleware across ``code_files`` (list of (rel_path, language))."""
    found: dict[tuple[str, str], MiddlewareInfo] = {}

    def add(name: str, framework: str, source: str) -> None:
        key = (name, source)
        if key not in found:
            found[key] = MiddlewareInfo(
                name=name,
                category=categorize_middleware(name),
                framework=framework,
                source_file=source,
            )

    for rel_path, language in sorted(code_files):
        text = _read(root / rel_path)
        if not text:
            continue
        if language in _JS_LANGS:
            for match in _EXPRESS_USE.finditer(text):
                add(match.group(1), "express", rel_path)
        elif language in _PY_LANGS:
            for match in _FASTAPI_ADD.finditer(text):
                add(match.group(1), "fastapi", rel_path)
            if _is_settings_module(rel_path):
                for block in _DJANGO_BLOCK.finditer(text):
                    for item in _DJANGO_ITEM.finditer(block.group(1)):
                        dotted = item.group(1)
                        add(dotted.split(".")[-1], "django", rel_path)

    return sorted(found.values(), key=lambda m: (m.source_file, m.category, m.name))


def _is_settings_module(rel_path: str) -> bool:
    name = rel_path.rsplit("/", 1)[-1]
    return name == "settings.py" or "settings" in rel_path.split("/")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
