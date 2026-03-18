"""Convenience constructors for similarity functions."""

from __future__ import annotations

from typing import Callable

import numpy as np

from semanticsmith.types import SimilarityFn


def from_callable(fn: Callable[[str, str], float]) -> SimilarityFn:
    """Wrap any (str, str) -> float callable as a SimilarityFn.

    This is a pass-through for type clarity; any callable already works.
    """
    return fn


def from_matrix(
    matrix: np.ndarray,
    vocab: dict[str, int] | list[str],
    default: float = -5.0,
) -> SimilarityFn:
    """Create a similarity function from a pre-computed matrix + vocabulary.

    Parameters
    ----------
    matrix : np.ndarray, shape (V, V)
        Pairwise similarity matrix.
    vocab : dict mapping word -> index, or list of words (index = position).
    default : float
        Score returned for out-of-vocabulary words.
    """
    if isinstance(vocab, list):
        vocab = {w: i for i, w in enumerate(vocab)}

    def similarity(word1: str, word2: str) -> float:
        i = vocab.get(word1)
        j = vocab.get(word2)
        if i is None or j is None:
            return default
        return float(matrix[i, j])

    return similarity


def from_gensim(
    keyed_vectors,
    default: float = -5.0,
    offset: float = -0.5,
    scale: float = 10.0,
) -> SimilarityFn:
    """Create a similarity function from a gensim KeyedVectors model.

    Replicates the original SemanticSmithWaterman scoring:
        score = (cosine_similarity - offset) * scale

    Parameters
    ----------
    keyed_vectors : gensim.models.KeyedVectors
        Pre-trained word vectors.
    default : float
        Score for OOV word pairs (unless words are identical).
    offset : float
        Subtracted from raw cosine similarity before scaling.
    scale : float
        Multiplier for adjusted similarity.
    """
    def similarity(word1: str, word2: str) -> float:
        if word1 == word2:
            return scale
        try:
            raw = keyed_vectors.similarity(word1.lower(), word2.lower())
            score = (raw + offset) * scale
            return max(score, default)
        except KeyError:
            return default

    return similarity


def constant(match: float = 10.0, mismatch: float = -5.0) -> SimilarityFn:
    """Create a constant similarity function (exact match only).

    Useful for testing and for replicating classic Smith-Waterman behavior.
    """
    def similarity(word1: str, word2: str) -> float:
        return match if word1 == word2 else mismatch

    return similarity
