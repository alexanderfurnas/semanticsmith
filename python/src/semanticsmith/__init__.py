"""semanticsmith — Semantic Smith-Waterman local alignment for text."""

from semanticsmith.types import AlignmentResult
from semanticsmith.align import align, batch_align
from semanticsmith import similarity
from semanticsmith.viz import show

__all__ = ["align", "batch_align", "AlignmentResult", "similarity", "show"]
__version__ = "0.1.0"
