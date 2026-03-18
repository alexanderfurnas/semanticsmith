"""Type definitions for semanticsmith."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol, Sequence, runtime_checkable


@runtime_checkable
class SimilarityFn(Protocol):
    """Protocol for word similarity functions.

    Any callable with signature (str, str) -> float satisfies this.
    """

    def __call__(self, word1: str, word2: str) -> float: ...


@dataclass(frozen=True)
class AlignmentResult:
    """Result of a local sequence alignment."""

    score: float
    aligned1: list[str]
    aligned2: list[str]
    identity: float
    n_gaps: int
    seq1_tokens: list[str]
    seq2_tokens: list[str]

    @property
    def align_len(self) -> int:
        return len(self.aligned1)

    def format_alignment(self) -> str:
        """Return a human-readable alignment string."""
        if not self.aligned1:
            return "(no alignment)"

        max_width = max(
            max((len(t) for t in self.aligned1), default=0),
            max((len(t) for t in self.aligned2), default=0),
        )
        width = max(max_width, 3)

        row1 = " ".join(t.center(width) for t in self.aligned1)
        mid = " ".join(
            "|".center(width) if a == b else " " * width
            for a, b in zip(self.aligned1, self.aligned2)
        )
        row2 = " ".join(t.center(width) for t in self.aligned2)

        return f"{row1}\n{mid}\n{row2}"

    def __repr__(self) -> str:
        return (
            f"AlignmentResult(score={self.score:.2f}, "
            f"identity={self.identity:.1%}, "
            f"align_len={self.align_len}, "
            f"gaps={self.n_gaps})"
        )

    def __str__(self) -> str:
        header = repr(self)
        body = self.format_alignment()
        return f"{header}\n{body}"
