"""Main alignment API for semanticsmith."""

from __future__ import annotations

from typing import Callable, Sequence

import numpy as np

from semanticsmith.types import AlignmentResult, SimilarityFn

try:
    from semanticsmith._core import c_align
except ImportError:
    from semanticsmith._fallback import c_align

GAP_TOKEN = "---"


def _tokenize(text: str | list[str]) -> list[str]:
    """Convert input to a list of tokens."""
    if isinstance(text, str):
        return text.split()
    return list(text)


def _build_sim_matrix(
    tokens1: list[str],
    tokens2: list[str],
    similarity_fn: SimilarityFn,
) -> np.ndarray:
    """Build the n x m similarity matrix by calling the user's function."""
    n, m = len(tokens1), len(tokens2)
    matrix = np.empty((n, m), dtype=np.float64)
    for i in range(n):
        for j in range(m):
            matrix[i, j] = similarity_fn(tokens1[i], tokens2[j])
    return matrix


def align(
    text1: str | list[str],
    text2: str | list[str],
    similarity_fn: SimilarityFn,
    gap_open: float = -5.0,
    gap_extend: float = -2.0,
) -> AlignmentResult:
    """Align two texts using Semantic Smith-Waterman.

    Parameters
    ----------
    text1 : str or list of str
        First text (string to be tokenized by whitespace, or pre-tokenized list).
    text2 : str or list of str
        Second text.
    similarity_fn : callable (str, str) -> float
        Returns the similarity score between two words.
    gap_open : float
        Penalty for opening a gap (should be negative).
    gap_extend : float
        Penalty for extending a gap (should be negative).

    Returns
    -------
    AlignmentResult
    """
    tokens1 = _tokenize(text1)
    tokens2 = _tokenize(text2)

    if not tokens1 or not tokens2:
        return AlignmentResult(
            score=0.0, aligned1=[], aligned2=[],
            identity=0.0, n_gaps=0,
            seq1_tokens=tokens1, seq2_tokens=tokens2,
        )

    sim_matrix = _build_sim_matrix(tokens1, tokens2, similarity_fn)
    score, idx1, idx2 = c_align(sim_matrix, gap_open, gap_extend)

    aligned1 = []
    aligned2 = []
    n_gaps = 0
    matches = 0

    for i1, i2 in zip(idx1, idx2):
        t1 = tokens1[i1] if i1 >= 0 else GAP_TOKEN
        t2 = tokens2[i2] if i2 >= 0 else GAP_TOKEN
        aligned1.append(t1)
        aligned2.append(t2)
        if i1 < 0 or i2 < 0:
            n_gaps += 1
        elif tokens1[i1] == tokens2[i2]:
            matches += 1

    align_len = len(aligned1)
    identity = matches / align_len if align_len > 0 else 0.0

    return AlignmentResult(
        score=score,
        aligned1=aligned1,
        aligned2=aligned2,
        identity=identity,
        n_gaps=n_gaps,
        seq1_tokens=tokens1,
        seq2_tokens=tokens2,
    )


def batch_align(
    texts: Sequence[str | list[str]],
    similarity_fn: SimilarityFn,
    gap_open: float = -5.0,
    gap_extend: float = -2.0,
    pairs: Sequence[tuple[int, int]] | None = None,
) -> list[dict]:
    """Align multiple texts pairwise.

    Parameters
    ----------
    texts : sequence of str or list[str]
        Texts to compare.
    similarity_fn : callable (str, str) -> float
        Word similarity function.
    gap_open, gap_extend : float
        Gap penalties.
    pairs : sequence of (i, j) tuples, optional
        Specific pairs to compare. If None, computes all upper-triangle pairs.

    Returns
    -------
    list of dict with keys: i, j, score, identity, align_len, n_gaps, alignment
    """
    if pairs is None:
        n = len(texts)
        pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]

    results = []
    for i, j in pairs:
        r = align(texts[i], texts[j], similarity_fn, gap_open, gap_extend)
        results.append({
            "i": i,
            "j": j,
            "score": r.score,
            "identity": r.identity,
            "align_len": r.align_len,
            "n_gaps": r.n_gaps,
            "alignment": r,
        })

    return results
