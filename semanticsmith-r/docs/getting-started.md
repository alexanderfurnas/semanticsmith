Getting Started with semanticsmith
================

`semanticsmith` performs local text alignment using the Smith-Waterman
algorithm with any word similarity function you choose. It finds the
best-matching subsequences between two texts, accounting for insertions,
deletions, and semantic word similarity. The API is tidyverse-native:
results are tibbles, batch operations are pipe-friendly, and column
references use tidy evaluation.

## Installation

``` r
# From GitHub:
remotes::install_github("alexanderfurnas/semanticsmith", subdir = "semanticsmith-r")
```

``` r
library(semanticsmith)
library(dplyr)
library(tibble)
```

## Quick Start

``` r
# Create a simple exact-match similarity function
sim <- sim_from_function(function(a, b) ifelse(a == b, 10, -5))

# Align two sentences
result <- ssw_align("the cat sat on the mat", "the cat sat on the rug", sim)
result
```

``` r
# Pretty-print the alignment
ssw_print(result)
```

## Similarity Functions

The core design principle: **you provide the similarity function**. This
is any R function that takes two words (character scalars) and returns a
numeric score. Positive values indicate similarity; negative values
indicate dissimilarity.

### Constant (exact match only)

The simplest option — words either match or they don’t:

``` r
sim <- sim_from_function(function(a, b) ifelse(a == b, 10, -5))
sim("cat", "cat")   # 10
sim("cat", "dog")   # -5
```

### Custom functions

Write any similarity logic:

``` r
# Partial credit for shared first letter
my_sim <- sim_from_function(function(a, b) {
  if (a == b) return(10)
  if (substr(a, 1, 1) == substr(b, 1, 1)) return(2)
  -5
})

result <- ssw_align("the cat sat", "the car set", my_sim)
ssw_print(result)
```

### From word embeddings

Use any embedding matrix with row names as vocabulary. Works with output
from the `word2vec`, `text2vec`, or `wordVectors` packages:

``` r
# Example with the word2vec package
library(word2vec)

model <- word2vec(x = my_corpus, dim = 100, iter = 20)
emb <- as.matrix(model)

sim <- sim_from_embeddings(emb, offset = -0.5, scale = 10)
```

The scoring formula is: `score = (cosine_similarity + offset) × scale`

``` r
# Small example to demonstrate
emb <- matrix(
  c(1.0, 0.0,    # "cat"  - points along dim1
    0.9, 0.1,    # "dog"  - close to cat
    0.0, 1.0,    # "fish" - orthogonal to cat
    0.7, 0.7),   # "pet"  - between cat and fish
  nrow = 4, byrow = TRUE
)
rownames(emb) <- c("cat", "dog", "fish", "pet")

sim <- sim_from_embeddings(emb, offset = -0.5, scale = 10)

sim("cat", "cat")   # 10 (identical words always return scale)
sim("cat", "dog")   # high score (similar vectors)
sim("cat", "fish")  # low score (orthogonal vectors)
```

**Parameters:**

- `offset` (default -0.5): Shifts cosine similarity before scaling. With
  -0.5, words need cosine \> 0.5 to contribute positively to alignment.
- `scale` (default 10): Multiplier. Larger values amplify semantic
  differences relative to gap penalties.
- `default` (default -5): Score for out-of-vocabulary word pairs.
- `floor` (default = `default`): Minimum possible score (clamp).

### From a pre-computed similarity matrix

If you have a full V×V pairwise similarity matrix:

``` r
mat <- matrix(
  c(10,  6, -2,
     6, 10, -3,
    -2, -3, 10),
  nrow = 3, byrow = TRUE
)
vocab <- c("cat", "dog", "fish")

sim <- sim_from_matrix(mat, vocab, default = -5)
sim("cat", "dog")    # 6
sim("cat", "whale")  # -5 (not in vocab)
```

## Alignment Details

### Result structure

`ssw_align()` returns a single-row tibble:

``` r
sim <- sim_from_function(function(a, b) ifelse(a == b, 10, -5))
result <- ssw_align("the cat sat on the mat", "a dog sat on a rug", sim)
result
```

| Column | Type | Description |
|----|----|----|
| `score` | numeric | Best local alignment score |
| `identity` | numeric | Fraction of aligned positions with exact matches |
| `align_len` | integer | Length of the alignment (including gaps) |
| `n_gaps` | integer | Number of gap positions |
| `aligned1` | list of character | Aligned tokens from text 1 (`"---"` for gaps) |
| `aligned2` | list of character | Aligned tokens from text 2 |

Access the aligned sequences:

``` r
result$aligned1[[1]]
result$aligned2[[1]]
```

### Gap penalties

The algorithm uses **affine gap penalties**: opening a gap costs
`gap_open`, and each additional position costs `gap_extend`. This means
a single long gap is cheaper than many short gaps.

``` r
# Default: gap_open = -5, gap_extend = -2
result_default <- ssw_align("the cat sat", "the big furry cat sat", sim)

# Strict: discourage gaps
result_strict <- ssw_align("the cat sat", "the big furry cat sat", sim,
                           gap_open = -10, gap_extend = -5)

# Lenient: allow gaps freely
result_lenient <- ssw_align("the cat sat", "the big furry cat sat", sim,
                            gap_open = -2, gap_extend = -0.5)

tibble(
  mode = c("default", "strict", "lenient"),
  score = c(result_default$score, result_strict$score, result_lenient$score),
  gaps = c(result_default$n_gaps, result_strict$n_gaps, result_lenient$n_gaps)
)
```

Both values should be **negative**. Larger magnitude = harsher penalty.

### Input formats

`ssw_align()` accepts either a single string (split by whitespace) or a
character vector of pre-tokenized words:

``` r
# These are equivalent:
ssw_align("the cat sat", "the dog sat", sim)
ssw_align(c("the", "cat", "sat"), c("the", "dog", "sat"), sim)
```

For custom tokenization (e.g., with `tidytext` or `tokenizers`):

``` r
library(tidytext)
tokens1 <- tibble(text = "The cat's hat.") |>
  unnest_tokens(word, text) |>
  pull(word)
tokens2 <- tibble(text = "A dog's collar.") |>
  unnest_tokens(word, text) |>
  pull(word)
ssw_align(tokens1, tokens2, sim)
```

### Local alignment

This is a **local** alignment algorithm — it finds the best-matching
subsequences, ignoring unrelated text at the boundaries:

``` r
result <- ssw_align(
  "blah blah the cat sat blah blah",
  "noise noise the cat sat noise noise",
  sim
)
result$aligned1[[1]]  # Just "the", "cat", "sat"
```

## Batch Comparison

`ssw_batch_align()` takes a data frame with text columns and adds
alignment results. It’s pipe-friendly and uses tidy evaluation for
column selection:

``` r
df <- tibble(
  speaker = c("Alice", "Bob", "Carol"),
  text_a = c("the cat sat on the mat",
             "she sells sea shells",
             "how much wood would"),
  text_b = c("the dog sat on the rug",
             "she sells shore shells",
             "how much could would")
)

df |>
  ssw_batch_align(text_a, text_b, sim) |>
  select(speaker, ssw_score, ssw_identity, ssw_n_gaps)
```

### Filtering and analyzing results

Since output is a tibble, standard dplyr works naturally:

``` r
df |>
  ssw_batch_align(text_a, text_b, sim) |>
  filter(ssw_identity > 0.5) |>
  arrange(desc(ssw_score))
```

### All-pairs comparison

To compare every text against every other text, first expand into pairs:

``` r
texts <- c(
  "the cat sat on the mat",
  "the dog sat on the rug",
  "a fish swam in the sea"
)

pairs <- tidyr::expand_grid(i = seq_along(texts), j = seq_along(texts)) |>
  filter(i < j) |>
  mutate(text_a = texts[i], text_b = texts[j])

pairs |>
  ssw_batch_align(text_a, text_b, sim) |>
  select(i, j, ssw_score, ssw_identity)
```

## Visualization

``` r
result <- ssw_align("the cat sat on the mat", "the dog sat on the rug", sim)
ssw_print(result)
```

`ssw_print()` shows a three-line view:

- Line 1: aligned tokens from text 1
- Line 2: `|` for exact match, `~` for semantic match, space for gap
- Line 3: aligned tokens from text 2

A header line shows the score, identity percentage, alignment length,
and gap count.

## Performance Notes

- The DP core is implemented in C (via Rcpp) for performance.
- The main bottleneck is building the similarity matrix (calling your
  function n × m times). `sim_from_embeddings()` computes cosine
  similarity efficiently with pre-computed norms.
- `ssw_batch_align()` runs sequentially over rows. For very large
  batches, consider using `furrr::future_map()` or
  `parallel::mclapply()` to parallelize.
