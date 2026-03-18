#' Create a Similarity Function from a Matrix
#'
#' Build a similarity function from a pre-computed pairwise similarity matrix
#' and a vocabulary vector.
#'
#' @param matrix A numeric matrix where `matrix[i, j]` is the similarity
#'   between `vocab[i]` and `vocab[j]`.
#' @param vocab A character vector of vocabulary words (row/column names).
#' @param default Similarity score for out-of-vocabulary words. Default -5.
#' @return A function `(word1, word2) -> numeric`.
#' @export
#' @examples
#' mat <- matrix(c(10, 5, 5, 10), nrow = 2,
#'               dimnames = list(c("cat", "dog"), c("cat", "dog")))
#' sim <- sim_from_matrix(mat, c("cat", "dog"))
#' sim("cat", "dog")  # 5
sim_from_matrix <- function(matrix, vocab, default = -5) {
  lookup <- stats::setNames(seq_along(vocab), vocab)

  function(word1, word2) {
    i <- lookup[word1]
    j <- lookup[word2]
    if (is.na(i) || is.na(j)) return(default)
    matrix[i, j]
  }
}


#' Create a Similarity Function from an Arbitrary Function
#'
#' Wraps any R function `(word1, word2) -> numeric` for use with
#' [ssw_align()] and [ssw_batch_align()].
#'
#' @param fn A function taking two character scalars and returning a numeric score.
#' @return The same function (pass-through for API consistency).
#' @export
#' @examples
#' sim <- sim_from_function(function(a, b) ifelse(a == b, 10, -5))
#' sim("hello", "hello")  # 10
sim_from_function <- function(fn) {
  fn
}


#' Create a Similarity Function from Word Embeddings
#'
#' Build a similarity function from a word embedding matrix (e.g., from the
#' `word2vec`, `text2vec`, or `wordVectors` packages). Computes cosine
#' similarity on the fly, with configurable offset and scale to convert
#' cosine similarity (typically 0–1) into alignment scores.
#'
#' The scoring formula is:
#' \deqn{score = (cosine\_sim + offset) \times scale}
#'
#' Scores below `floor` are clamped to `floor`.
#'
#' @param embeddings A numeric matrix where each row is a word vector.
#'   Row names must be the vocabulary words.
#' @param default Score for out-of-vocabulary word pairs (unless identical). Default -5.
#' @param offset Added to raw cosine similarity before scaling. Default -0.5
#'   (so cosine=0.5 maps to score 0).
#' @param scale Multiplier applied after offset. Default 10.
#' @param floor Minimum score (clamp). Default same as `default`.
#' @return A function `(word1, word2) -> numeric`.
#' @export
#' @examples
#' # Tiny example embeddings
#' emb <- matrix(c(1, 0, 0, 1, 0.9, 0.1), nrow = 3, byrow = TRUE)
#' rownames(emb) <- c("cat", "dog", "fish")
#' sim <- sim_from_embeddings(emb)
#' sim("cat", "cat")   # 10 (identical words always get scale)
#' sim("cat", "dog")   # cosine-based score
sim_from_embeddings <- function(embeddings, default = -5, offset = -0.5,
                                scale = 10, floor = default) {
  if (is.null(rownames(embeddings))) {
    stop("`embeddings` must have row names (vocabulary words)")
  }

  # Pre-compute L2 norms for cosine similarity
  norms <- sqrt(rowSums(embeddings^2))
  vocab <- rownames(embeddings)
  lookup <- stats::setNames(seq_along(vocab), vocab)

  function(word1, word2) {
    if (word1 == word2) return(scale)

    i <- lookup[word1]
    j <- lookup[word2]
    if (is.na(i) || is.na(j)) return(default)

    cosine_sim <- sum(embeddings[i, ] * embeddings[j, ]) /
      (norms[i] * norms[j])
    score <- (cosine_sim + offset) * scale
    max(score, floor)
  }
}
