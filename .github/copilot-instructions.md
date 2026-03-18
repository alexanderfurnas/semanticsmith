# Copilot Instructions

## Project Overview

Monorepo implementing **Semantic Smith-Waterman (SSW)** — a text similarity algorithm that adapts Smith-Waterman local sequence alignment from bioinformatics to natural language. Available as both Python and R packages sharing a C core.

## Architecture

- **`csrc/`** — Shared C implementation of Gotoh's algorithm (affine gap penalties, O(nm)). Operates on a pre-computed similarity matrix passed from the language wrappers.
- **`python/`** — Python package using Cython to wrap the C core. Falls back to pure-Python `_fallback.py` if the C extension isn't compiled.
- **`r/`** — R package using Rcpp to wrap the C core. Tidyverse-native: tibble outputs, pipe-friendly API, tidy eval column references.
- **`legacy/`** — Original scripts, notebooks, and analysis from the research project.

## Build & Test

### Python
```bash
cd python
pip install ".[dev]"         # install with dev dependencies
python -m pytest tests/ -v   # run all tests
python -m pytest tests/test_align.py::TestAlign::test_identical_strings  # single test
```

The `setup.py` copies `csrc/*.{c,h}` into `src/semanticsmith/_csrc/` at build time so setuptools sees only relative paths.

### R
```r
devtools::install("r/")      # build and install
devtools::test("r/")         # run testthat suite
```

### C core (standalone)
```bash
cd csrc
cc -o test_ssw_core test_ssw_core.c ssw_core.c -I. -lm -Wall
./test_ssw_core
```

## Key Conventions

- **Similarity functions are callables**: `(str, str) → float` in Python, `function(a, b)` in R. The packages never import a specific embedding library — users wrap their own.
- **Pre-computed similarity matrix pattern**: Language wrappers build the full n×m similarity matrix by calling the user's function, then pass the flat array to C. This avoids cross-language callback overhead.
- **Gap penalties are negative**: `gap_open` and `gap_extend` should be negative values.
- **Alignment indices**: C core uses -1 for gaps (0-indexed); R wrapper converts to 0 for gaps (1-indexed).
- **Python fallback**: `_fallback.py` mirrors `_core.pyx` exactly in pure Python/NumPy for environments without a C compiler.
- **R outputs are tibbles**: `ssw_align()` returns a single-row tibble, `ssw_batch_align()` adds columns to the input data frame.
