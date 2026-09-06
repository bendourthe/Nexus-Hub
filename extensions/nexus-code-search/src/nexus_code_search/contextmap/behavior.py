"""Behavior-tag inference from a source slice.

Given the text of a route handler, infer a small set of coarse behavior tags
(auth, db, cache, payment, ai, queue, email) by matching conservative,
word-boundary token patterns. Tags are enrichment, not a detection gate: the
patterns are deliberately specific (distinctive library / API tokens rather than
generic English words) so a handler is only tagged when the signal is strong.

Deterministic and language-agnostic: the same source slice always yields the
same ordered tuple of tags.
"""

from __future__ import annotations

import re

# Each tag maps to a list of distinctive tokens. Patterns are matched
# case-insensitively with word boundaries so a substring inside an unrelated
# identifier does not trigger a tag (e.g. "dbg" must not match "db"). The tokens
# are chosen to be library / API surface names, not generic verbs.
_TAG_TOKENS: dict[str, tuple[str, ...]] = {
    "auth": (
        "authenticate",
        "authorize",
        "current_user",
        "get_current_user",
        "login_required",
        "require_auth",
        "check_password",
        "verify_token",
        "jwt",
        "oauth",
        "permission_classes",
        "req.user",
        "request.user",
    ),
    "db": (
        "session.query",
        ".objects.",
        "execute(",
        "cursor.",
        "sqlalchemy",
        "prisma.",
        "find_one(",
        "insert_one(",
        "update_one(",
        "aggregate(",
        "select(",
        ".save(",
        "repository.",
    ),
    "cache": (
        "cache.get",
        "cache.set",
        "get_or_set",
        "redis",
        "memcache",
        "lru_cache",
    ),
    "payment": (
        "stripe",
        "paypal",
        "braintree",
        "create_charge",
        "checkout.session",
        "payment_intent",
        "invoice",
    ),
    "ai": (
        "openai",
        "anthropic",
        "chat.completions",
        "embeddings.create",
        "generate_text",
        "model.predict",
        "llm.",
    ),
    "queue": (
        ".delay(",
        ".apply_async(",
        "celery",
        "enqueue(",
        "bullmq",
        "kafka",
        "background_tasks",
        "sqs",
    ),
    "email": (
        "send_mail",
        "send_email",
        "sendgrid",
        "mailgun",
        "smtp",
        "nodemailer",
        "ses.send",
    ),
}


def _compile(tokens: tuple[str, ...]) -> re.Pattern[str]:
    # Escape each token; wrap alphanumeric-bounded tokens with \b so a plain
    # word token does not match inside a larger identifier. Tokens that already
    # end in a non-word char (e.g. "execute(") are matched literally.
    parts = []
    for tok in tokens:
        escaped = re.escape(tok)
        if tok[:1].isalnum():
            escaped = r"\b" + escaped
        parts.append(escaped)
    return re.compile("|".join(parts), re.IGNORECASE)


_TAG_PATTERNS: dict[str, re.Pattern[str]] = {
    tag: _compile(tokens) for tag, tokens in _TAG_TOKENS.items()
}

# Stable render order for the tags.
_TAG_ORDER = ("auth", "db", "cache", "payment", "ai", "queue", "email")


def infer_behavior_tags(source_slice: str) -> tuple[str, ...]:
    """Return the ordered tuple of behavior tags implied by ``source_slice``."""
    if not source_slice:
        return ()
    found = {
        tag for tag, pattern in _TAG_PATTERNS.items() if pattern.search(source_slice)
    }
    return tuple(tag for tag in _TAG_ORDER if tag in found)
