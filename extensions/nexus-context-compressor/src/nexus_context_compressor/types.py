"""Core types for the context-compression engine.

A ``compress`` call takes a list of messages and returns a ``CompressResult``
carrying the (possibly) compressed messages plus token-accounting metrics. In
Phase 1 the pipeline is a no-op: the messages pass through unchanged and the
metrics report an identity transform (``tokens_after == tokens_before``,
``ratio == 1.0``). Later phases populate ``transforms_applied`` as deterministic
strategies (SmartCrusher, CacheAligner, ContentRouter, CodeCompressor) and the
optional ML token-dropper run.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# A message is the conversational unit the engine compresses. We keep the type
# deliberately loose for the skeleton: either a plain string or a mapping with
# at least a ``content`` field (the common ``{"role": ..., "content": ...}``
# shape). Strategies in later phases narrow this per content type.
Message = "str | dict"


@dataclass
class CompressResult:
    """The outcome of compressing a message list.

    Attributes:
        messages: the compressed messages, in the same shape as the input. For
            the Phase 1 no-op pipeline this is the input unchanged.
        tokens_before: token count of the input, via ``tokens.count_tokens``.
        tokens_after: token count of ``messages`` after compression.
        transforms_applied: ordered names of the strategies that ran. Empty for
            the no-op pipeline.
    """

    messages: list
    tokens_before: int
    tokens_after: int
    transforms_applied: list[str] = field(default_factory=list)

    @property
    def ratio(self) -> float:
        """Fraction of tokens retained: ``tokens_after / tokens_before``.

        Lower is more compressed (0.25 means the output is a quarter the size
        of the input). Returns ``1.0`` for an empty input to avoid division by
        zero (an identity transform on nothing).
        """
        if self.tokens_before <= 0:
            return 1.0
        return self.tokens_after / self.tokens_before

    @property
    def reduction(self) -> float:
        """Fraction of tokens removed: ``1 - ratio`` (higher is more compressed)."""
        return 1.0 - self.ratio
