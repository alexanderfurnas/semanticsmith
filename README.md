# semanticsmith

Semantic Smith-Waterman local alignment for text similarity — available as both Python and R packages.

Adapts the [Smith-Waterman algorithm](https://en.wikipedia.org/wiki/Smith%E2%80%93Waterman_algorithm) from bioinformatics to natural language: instead of aligning character or nucleotide sequences, it aligns **word sequences** using any word similarity function you provide (Word2Vec, GloVe, sentence-transformers, or a custom function).

## Features

- **Arbitrary similarity functions** — pass any `(word1, word2) → score` callable
- **Affine gap penalties** — separate gap-open and gap-extend costs (Gotoh's algorithm)
- **C core** — performance-critical DP fill implemented in C, shared by both packages
- **Batch comparison** — pairwise alignment of multiple texts
- **Alignment visualization** — colored terminal output (Python), formatted printing (R)

## Installation

### Python

```bash
pip install git+https://github.com/alexanderfurnas/semanticsmith.git#subdirectory=python

# With optional gensim support:
pip install "semanticsmith[gensim] @ git+https://github.com/alexanderfurnas/semanticsmith.git#subdirectory=python"
```

### R

```r
# Requires C compiler (Xcode CLI tools on macOS, Rtools on Windows)
remotes::install_github("alexanderfurnas/semanticsmith", subdir = "r")
```

## Quick Start

### Python

```python
from semanticsmith import align, similarity

# Simple exact-match similarity
sim = similarity.constant(match=10, mismatch=-5)
result = align("the cat sat on the mat", "the dog sat on the rug", sim)
print(result)

# With gensim Word2Vec
from gensim.models import KeyedVectors
wv = KeyedVectors.load_word2vec_format("vectors.bin", binary=True)
sim = similarity.from_gensim(wv)
result = align("economic growth slowed", "financial expansion declined", sim)

# Batch comparison
from semanticsmith import batch_align
texts = ["the cat sat", "the dog sat", "a fish swam"]
results = batch_align(texts, sim)
```

### R

```r
library(semanticsmith)

# Create a similarity function
sim <- sim_from_function(function(a, b) ifelse(a == b, 10, -5))

# Single alignment — returns a tibble
result <- ssw_align("the cat sat on the mat", "the dog sat on the rug", sim)
ssw_print(result)

# Batch alignment — pipe-friendly, tidyverse-native
library(dplyr)
tibble(
  text_a = c("the cat sat", "hello world"),
  text_b = c("the dog sat", "hello world")
) |>
  ssw_batch_align(text_a, text_b, sim)
```

## Documentation

- **[Python Getting Started Guide](python/docs/getting-started.md)** — similarity functions, alignment options, batch comparison, visualization
- **[R Getting Started Vignette](r/vignettes/getting-started.Rmd)** — tidyverse workflows, embeddings, pipe-friendly batch alignment

## Project Structure

```
├── csrc/           # Shared C core (Gotoh's algorithm)
├── python/         # Python package (Cython wrapper)
├── r/              # R package (Rcpp wrapper, tidyverse-style)
└── legacy/         # Original scripts and notebooks
```

## Acknowledgments

The first implementation of this algorithm was developed in collaboration with [Ben Edwards](https://github.com/bjedwards). The original codebase is available at [bjedwards/SemanticSmithWaterman](https://github.com/bjedwards/SemanticSmithWaterman).

## License

GPL-3.0-or-later
