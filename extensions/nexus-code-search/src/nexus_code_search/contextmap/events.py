"""Background-work / event extraction.

Detects declaration-strong background-work surfaces, chosen so an invocation
that merely looks similar does not produce a false positive:

- Celery: a `@shared_task` / `@app.task` / `@celery.task` decorator on a def.
- BullMQ: `new Queue('name')` / `new Worker('name')`.
- Kafka: `new Kafka(` (kafkajs) or `KafkaProducer(` / `KafkaConsumer(` (Python).
- Node EventEmitter: `new EventEmitter()` (capturing the bound variable name).

Invocation-only patterns (`.delay(`, `.emit(`, `.publish(` / `.subscribe(`) are
deferred - they are too common to detect without false positives here.
"""

from __future__ import annotations

import re
from pathlib import Path

from nexus_code_search.contextmap.model import EventInfo

_PY_LANGS = frozenset({"python"})
_JS_LANGS = frozenset({"typescript", "tsx", "javascript", "jsx"})

# Celery: a task decorator immediately preceding a def (allow decorator args).
_CELERY_TASK = re.compile(
    r"@(?:shared_task|\w+\.task)(?:\([^)]*\))?\s*(?:\n\s*@[^\n]*)*\s*\n\s*def\s+(\w+)"
)
_KAFKA_PY = re.compile(r"\bKafka(?:Producer|Consumer)\s*\(")

_BULLMQ = re.compile(r"""\bnew\s+(?:Queue|Worker)\s*\(\s*["']([^"']+)["']""")
_KAFKA_JS = re.compile(r"\bnew\s+Kafka\s*\(")
_EVENT_EMITTER = re.compile(
    r"""(?:const|let|var)\s+(\w+)\s*=\s*new\s+EventEmitter\s*\("""
)


def detect_events(root: Path, code_files: list[tuple[str, str]]) -> list[EventInfo]:
    """Detect background-work surfaces across ``code_files``."""
    found: dict[tuple[str, str, str], EventInfo] = {}

    def add(name: str, kind: str, source: str) -> None:
        key = (name, kind, source)
        if key not in found:
            found[key] = EventInfo(name=name, kind=kind, source_file=source)

    for rel_path, language in sorted(code_files):
        text = _read(root / rel_path)
        if not text:
            continue
        if language in _PY_LANGS:
            for match in _CELERY_TASK.finditer(text):
                add(match.group(1), "celery-task", rel_path)
            if _KAFKA_PY.search(text):
                add("kafka", "kafka", rel_path)
        elif language in _JS_LANGS:
            for match in _BULLMQ.finditer(text):
                add(match.group(1), "bullmq-queue", rel_path)
            if _KAFKA_JS.search(text):
                add("kafka", "kafka", rel_path)
            for match in _EVENT_EMITTER.finditer(text):
                add(match.group(1), "event-emitter", rel_path)

    return sorted(found.values(), key=lambda e: (e.source_file, e.kind, e.name))


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
