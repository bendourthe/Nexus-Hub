"""Typed action vocabulary for installer / teardown disk operations.

Every per-integration install / uninstall call returns a `WriteResult` so the
runner can render per-file results, the dry-run / --check flags can compare
expected vs. actual state, and tests can assert on the action vocabulary
without inspecting stdout.

The six action values map to the cloned CodeGraph reference
`src/installer/targets/types.ts` `FileAction` union:

    created     A file (or directory) that did not exist was written.
    updated     A file that already existed was rewritten with different bytes.
    unchanged   A file that already existed matched the to-be-written bytes; no write occurred.
    removed     A file (or directory) was deleted (uninstall / legacy cleanup).
    not-found   The install path looked for a file that did not exist (typically a source template).
    kept        A file was found at the destination and intentionally left untouched (skip-existing).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Literal, Union

Action = Literal[
    "created",
    "updated",
    "unchanged",
    "removed",
    "not-found",
    "kept",
]

VALID_ACTIONS: frozenset[str] = frozenset(
    {"created", "updated", "unchanged", "removed", "not-found", "kept"}
)


@dataclass(frozen=True)
class FileAction:
    """One disk operation outcome.

    `path` is the absolute or repo-relative path as a string (callers should
    pass `str(Path(...))`). `action` MUST be one of `VALID_ACTIONS`.
    """

    path: str
    action: Action

    def __post_init__(self) -> None:
        if self.action not in VALID_ACTIONS:
            raise ValueError(
                f"Invalid FileAction action {self.action!r}; "
                f"must be one of {sorted(VALID_ACTIONS)}"
            )


@dataclass
class WriteResult:
    """The return shape of every lifecycle method on `IntegrationBase`.

    `files` holds one `FileAction` per disk-touching call (or per skipped call).
    `notes` holds free-form strings the runner / tests can surface alongside
    the structured action list (e.g., "skipped: no global_dir configured").
    """

    files: List[FileAction] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def add(self, path: Union[str, Path], action: Action) -> FileAction:
        """Append a `FileAction` to `files` and return it for chaining."""
        fa = FileAction(path=str(path), action=action)
        self.files.append(fa)
        return fa

    def extend(self, other: "WriteResult") -> "WriteResult":
        """Merge `other` into `self` in place and return `self`."""
        self.files.extend(other.files)
        self.notes.extend(other.notes)
        return self

    def note(self, message: str) -> None:
        """Append a free-form note."""
        self.notes.append(message)

    def actions_by_kind(self) -> dict[str, int]:
        """Return a histogram of action -> count for quick reporting."""
        counts: dict[str, int] = {}
        for fa in self.files:
            counts[fa.action] = counts.get(fa.action, 0) + 1
        return counts


__all__ = ["Action", "FileAction", "VALID_ACTIONS", "WriteResult"]
