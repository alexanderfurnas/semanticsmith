"""Alignment visualization utilities."""

from __future__ import annotations

from semanticsmith.types import AlignmentResult


def format_color(result: AlignmentResult) -> str:
    """Format alignment with ANSI colors for terminal display.

    Green = exact match, yellow = semantic match (non-identical aligned),
    red = gap.
    """
    if not result.aligned1:
        return "(no alignment)"

    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    RESET = "\033[0m"

    max_width = max(
        max((len(t) for t in result.aligned1), default=0),
        max((len(t) for t in result.aligned2), default=0),
    )
    width = max(max_width, 3)

    row1_parts = []
    mid_parts = []
    row2_parts = []

    for t1, t2 in zip(result.aligned1, result.aligned2):
        if t1 == "---" or t2 == "---":
            color = RED
            mid_char = " "
        elif t1 == t2:
            color = GREEN
            mid_char = "|"
        else:
            color = YELLOW
            mid_char = "~"

        row1_parts.append(f"{color}{t1.center(width)}{RESET}")
        mid_parts.append(f"{color}{mid_char.center(width)}{RESET}")
        row2_parts.append(f"{color}{t2.center(width)}{RESET}")

    header = (
        f"Score: {result.score:.2f}  "
        f"Identity: {result.identity:.1%}  "
        f"Length: {result.align_len}  "
        f"Gaps: {result.n_gaps}"
    )

    return (
        f"{header}\n"
        f"{' '.join(row1_parts)}\n"
        f"{' '.join(mid_parts)}\n"
        f"{' '.join(row2_parts)}"
    )


def show(result: AlignmentResult, color: bool = True) -> None:
    """Print an alignment result.

    Parameters
    ----------
    result : AlignmentResult
    color : bool
        Use ANSI colors (default True). Set False for plain text.
    """
    if color:
        print(format_color(result))
    else:
        print(result)
