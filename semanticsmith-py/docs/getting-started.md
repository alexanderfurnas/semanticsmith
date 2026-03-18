# Getting Started with semanticsmith (Python)

`semanticsmith` performs local text alignment using the Smith-Waterman algorithm
with any word similarity function you choose. It finds the best-matching
subsequences between two texts, accounting for insertions, deletions, and
semantic similarity between words.

## Installation

```bash
pip install "git+https://github.com/alexanderfurnas/semanticsmith.git#subdirectory=semanticsmith-py"

# With gensim support (optional):
pip install "semanticsmith[gensim] @ git+https://github.com/alexanderfurnas/semanticsmith.git#subdirectory=semanticsmith-py"
```

## Quick Start

```python
from semanticsmith import align, similarity

# Create a simple exact-match similarity function
sim = similarity.constant(match=10, mismatch=-5)

# Align two sentences
result = align("the cat sat on the mat", "the cat sat on the rug", sim)
print(result)
# AlignmentResult(score=50.00, identity=83.3%, align_len=6, gaps=0)
#  the   cat   sat    on   the   mat
#   |     |     |     |     |
#  the   cat   sat    on   the   rug
```

## Similarity Functions

The core design principle: **you provide the similarity function**. This is any
callable that takes two words and returns a numeric score. Positive scores
indicate similarity; negative scores indicate dissimilarity.

### Constant (exact match)

The simplest option — words either match or they don't:

```python
sim = similarity.constant(match=10, mismatch=-5)
sim("cat", "cat")   # 10.0
sim("cat", "dog")   # -5.0
```

### Custom callable

Write any function you like:

```python
def my_sim(a, b):
    if a == b:
        return 10.0
    # Partial credit for words starting with the same letter
    if a[0] == b[0]:
        return 2.0
    return -5.0

result = align("the cat sat", "the car set", my_sim)
```

### From gensim Word2Vec / GloVe / FastText

```python
from gensim.models import KeyedVectors

# Load pre-trained vectors (e.g., Google News Word2Vec)
wv = KeyedVectors.load_word2vec_format("GoogleNews-vectors-negative300.bin", binary=True)

# Wrap as a similarity function
sim = similarity.from_gensim(wv, offset=-0.5, scale=10.0)

# The scoring formula: score = (cosine_similarity + offset) * scale
# With offset=-0.5: cosine=1.0 → 5.0, cosine=0.5 → 0.0, cosine=0.0 → -5.0
sim("king", "queen")    # high positive score
sim("king", "banana")   # low/negative score
sim("asdfgh", "cat")    # -5.0 (OOV default)
```

Parameters:
- `offset` (default -0.5): Shifts the cosine similarity before scaling. Controls
  where the "zero point" falls. With -0.5, words need cosine > 0.5 to contribute
  positively.
- `scale` (default 10.0): Multiplier for the adjusted similarity. Larger values
  make semantic differences matter more relative to gap penalties.
- `default` (default -5.0): Score for out-of-vocabulary word pairs.

### From a pre-computed matrix

If you've already computed a pairwise similarity matrix:

```python
import numpy as np

vocab = ["cat", "dog", "fish", "bird"]
matrix = np.array([
    [10.0,  6.0, -2.0,  1.0],  # cat
    [ 6.0, 10.0, -3.0,  0.0],  # dog
    [-2.0, -3.0, 10.0, -1.0],  # fish
    [ 1.0,  0.0, -1.0, 10.0],  # bird
])

sim = similarity.from_matrix(matrix, vocab, default=-5.0)
sim("cat", "dog")    # 6.0
sim("cat", "whale")  # -5.0 (not in vocab)
```

## Alignment Details

### The `AlignmentResult` object

```python
result = align("the cat sat on the mat", "a dog sat on a rug", sim)

result.score       # Best local alignment score (float)
result.identity    # Fraction of aligned positions that are exact matches
result.align_len   # Length of the alignment (including gaps)
result.n_gaps      # Number of gap positions
result.aligned1    # Aligned tokens from text1 (list of str, '---' for gaps)
result.aligned2    # Aligned tokens from text2
result.seq1_tokens # Original tokens from text1
result.seq2_tokens # Original tokens from text2
```

### Gap penalties

The algorithm uses **affine gap penalties**: opening a gap costs `gap_open`,
and each additional position in the gap costs `gap_extend`. This means a
single long gap is cheaper than many short gaps.

```python
# Default: gap_open=-5.0, gap_extend=-2.0
result = align(text1, text2, sim)

# Strict gaps (discourage any gaps)
result = align(text1, text2, sim, gap_open=-10.0, gap_extend=-5.0)

# Lenient gaps (allow gaps freely)
result = align(text1, text2, sim, gap_open=-2.0, gap_extend=-0.5)
```

Both values should be **negative**. A larger magnitude means a harsher penalty.

### Input formats

`align()` accepts either raw strings (split by whitespace) or pre-tokenized lists:

```python
# These are equivalent:
align("the cat sat", "the dog sat", sim)
align(["the", "cat", "sat"], ["the", "dog", "sat"], sim)

# Pre-tokenize for custom tokenization (e.g., with spaCy or nltk):
import nltk
tokens1 = nltk.word_tokenize("The cat's hat.")
tokens2 = nltk.word_tokenize("A dog's collar.")
result = align(tokens1, tokens2, sim)
```

### Local alignment

This is a **local** alignment algorithm — it finds the best-matching
subsequences, ignoring unrelated text at the beginning and end:

```python
sim = similarity.constant(match=10, mismatch=-5)

result = align(
    "blah blah the cat sat blah blah",
    "noise noise the cat sat noise noise",
    sim
)
print(result.aligned1)  # ['the', 'cat', 'sat']
print(result.aligned2)  # ['the', 'cat', 'sat']
# The surrounding noise is ignored
```

## Batch Comparison

Compare multiple texts pairwise:

```python
from semanticsmith import batch_align

texts = [
    "the cat sat on the mat",
    "the dog sat on the rug",
    "a fish swam in the sea",
]

# All upper-triangle pairs (0,1), (0,2), (1,2)
results = batch_align(texts, sim)
for r in results:
    print(f"({r['i']}, {r['j']}): score={r['score']:.1f}, identity={r['identity']:.1%}")

# Specific pairs only
results = batch_align(texts, sim, pairs=[(0, 1), (0, 2)])
```

Each result dict contains `i`, `j`, `score`, `identity`, `align_len`, `n_gaps`,
and the full `alignment` (an `AlignmentResult` object).

## Visualization

### Colored terminal output

```python
from semanticsmith import show

result = align("the cat sat on the mat", "the dog sat on the rug", sim)
show(result)          # colored output (green=match, yellow=semantic, red=gap)
show(result, color=False)  # plain text
```

### Programmatic access

```python
print(result.format_alignment())  # plain text alignment grid
print(repr(result))               # one-line summary
print(str(result))                # summary + alignment grid
```

## Performance Notes

- The DP core is implemented in C (via Cython) for performance. If the C
  extension fails to compile, a pure-Python/NumPy fallback is used automatically.
- The main bottleneck for large vocabularies is building the similarity matrix
  (calling your similarity function n×m times). For gensim, this is fast; for
  API-based embeddings, consider pre-computing and using `from_matrix()`.
- `batch_align()` runs sequentially. For large batches, consider parallelizing
  with `concurrent.futures` or `multiprocessing`.
