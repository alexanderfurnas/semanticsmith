"""Tests for semanticsmith alignment."""

import numpy as np
import pytest

from semanticsmith.align import align, batch_align
from semanticsmith.similarity import constant, from_matrix
from semanticsmith.types import AlignmentResult
from semanticsmith.viz import format_color


# --- Similarity fixtures ---

@pytest.fixture
def exact_sim():
    """Constant similarity: 10 for match, -5 for mismatch."""
    return constant(match=10.0, mismatch=-5.0)


# --- align() tests ---

class TestAlign:
    def test_identical_strings(self, exact_sim):
        r = align("the cat sat", "the cat sat", exact_sim)
        assert r.score == 30.0
        assert r.identity == 1.0
        assert r.aligned1 == ["the", "cat", "sat"]
        assert r.aligned2 == ["the", "cat", "sat"]
        assert r.n_gaps == 0

    def test_no_match(self, exact_sim):
        r = align("aaa bbb", "ccc ddd", exact_sim)
        assert r.score == 0.0
        assert r.align_len == 0

    def test_partial_match(self, exact_sim):
        r = align("xx the cat xx", "yy the cat yy", exact_sim)
        assert r.score == 20.0
        assert r.aligned1 == ["the", "cat"]
        assert r.aligned2 == ["the", "cat"]

    def test_gap_insertion(self, exact_sim):
        r = align("the cat sat", "the big cat sat", exact_sim, gap_open=-8.0, gap_extend=-2.0)
        assert r.score > 0
        assert "---" in r.aligned1 or "---" in r.aligned2

    def test_accepts_token_lists(self, exact_sim):
        r = align(["the", "cat"], ["the", "cat"], exact_sim)
        assert r.score == 20.0

    def test_empty_input(self, exact_sim):
        r = align("", "hello", exact_sim)
        assert r.score == 0.0
        assert r.align_len == 0

    def test_single_token_match(self, exact_sim):
        r = align("hello", "hello", exact_sim)
        assert r.score == 10.0
        assert r.aligned1 == ["hello"]

    def test_semantic_similarity(self):
        """Test with a similarity function that gives partial credit."""
        def sem_sim(a, b):
            if a == b:
                return 10.0
            # "cat" and "dog" are semantically similar
            if {a, b} == {"cat", "dog"}:
                return 5.0
            return -5.0

        r = align("the cat sat", "the dog sat", sem_sim)
        assert r.score > 0
        assert r.aligned1 == ["the", "cat", "sat"]
        assert r.aligned2 == ["the", "dog", "sat"]


# --- from_matrix() tests ---

class TestFromMatrix:
    def test_basic(self):
        vocab = ["cat", "dog", "fish"]
        matrix = np.array([
            [10.0, 5.0, -5.0],
            [5.0, 10.0, -5.0],
            [-5.0, -5.0, 10.0],
        ])
        sim = from_matrix(matrix, vocab)
        assert sim("cat", "cat") == 10.0
        assert sim("cat", "dog") == 5.0
        assert sim("cat", "unknown") == -5.0  # default

    def test_dict_vocab(self):
        vocab = {"a": 0, "b": 1}
        matrix = np.array([[10.0, -5.0], [-5.0, 10.0]])
        sim = from_matrix(matrix, vocab, default=-10.0)
        assert sim("a", "a") == 10.0
        assert sim("a", "z") == -10.0


# --- batch_align() tests ---

class TestBatchAlign:
    def test_all_pairs(self, exact_sim):
        texts = ["the cat", "the dog", "the cat"]
        results = batch_align(texts, exact_sim)
        assert len(results) == 3  # C(3,2) = 3
        assert all("score" in r for r in results)

    def test_specific_pairs(self, exact_sim):
        texts = ["aaa", "bbb", "aaa"]
        results = batch_align(texts, exact_sim, pairs=[(0, 2)])
        assert len(results) == 1
        assert results[0]["score"] == 10.0

    def test_result_contains_alignment(self, exact_sim):
        texts = ["hello world", "hello world"]
        results = batch_align(texts, exact_sim)
        assert isinstance(results[0]["alignment"], AlignmentResult)


# --- AlignmentResult tests ---

class TestAlignmentResult:
    def test_repr(self, exact_sim):
        r = align("a b", "a b", exact_sim)
        s = repr(r)
        assert "score=" in s
        assert "identity=" in s

    def test_str(self, exact_sim):
        r = align("a b", "a b", exact_sim)
        s = str(r)
        assert "a" in s and "b" in s

    def test_format_alignment(self, exact_sim):
        r = align("cat dog", "cat dog", exact_sim)
        fmt = r.format_alignment()
        assert "cat" in fmt
        assert "|" in fmt


# --- Visualization tests ---

class TestViz:
    def test_format_color(self, exact_sim):
        r = align("the cat", "the cat", exact_sim)
        colored = format_color(r)
        assert "\033[32m" in colored  # green for matches

    def test_format_color_gaps(self, exact_sim):
        r = align("a b c", "a c", exact_sim, gap_open=-3.0, gap_extend=-1.0)
        if r.n_gaps > 0:
            colored = format_color(r)
            assert "\033[31m" in colored  # red for gaps

    def test_format_color_empty(self, exact_sim):
        r = align("", "", exact_sim)
        assert format_color(r) == "(no alignment)"
