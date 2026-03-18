#' Semantic Smith-Waterman Local Alignment
#'
#' Align two tokenized texts using the Smith-Waterman algorithm with
#' an arbitrary word similarity function and affine gap penalties.
#'
#' @param tokens1 Character vector of tokens, or a single string (split by whitespace).
#' @param tokens2 Character vector of tokens, or a single string.
#' @param sim_fn A function taking two strings and returning a numeric similarity score.
#' @param gap_open Penalty for opening a gap (should be negative). Default -5.
#' @param gap_extend Penalty for extending a gap (should be negative). Default -2.
#' @return A tibble with one row containing: score, identity, align_len, n_gaps,
#'   aligned1 (list-col), aligned2 (list-col).
#' @export
#' @examples
#' sim <- sim_from_function(function(a, b) ifelse(a == b, 10, -5))
#' ssw_align("the cat sat", "the big cat sat", sim)
ssw_align <- function(tokens1, tokens2, sim_fn,
                      gap_open = -5, gap_extend = -2) {
  tokens1 <- .tokenize(tokens1)
  tokens2 <- .tokenize(tokens2)

  n <- length(tokens1)
  m <- length(tokens2)

  if (n == 0 || m == 0) {
    return(tibble::tibble(
      score = 0, identity = 0, align_len = 0L, n_gaps = 0L,
      aligned1 = list(character(0)),
      aligned2 = list(character(0))
    ))
  }

  # Build similarity matrix
  sim_matrix <- matrix(0, nrow = n, ncol = m)
  for (i in seq_len(n)) {
    for (j in seq_len(m)) {
      sim_matrix[i, j] <- sim_fn(tokens1[i], tokens2[j])
    }
  }

  result <- c_ssw_align(sim_matrix, gap_open, gap_extend)

  # Convert indices to tokens (0 = gap in R-side result)
  aligned1 <- ifelse(result$align1 > 0, tokens1[result$align1], "---")
  aligned2 <- ifelse(result$align2 > 0, tokens2[result$align2], "---")

  n_gaps <- sum(result$align1 == 0 | result$align2 == 0)
  align_len <- length(aligned1)
  matches <- sum(aligned1 == aligned2 & aligned1 != "---")
  identity <- if (align_len > 0) matches / align_len else 0

  tibble::tibble(
    score = result$score,
    identity = identity,
    align_len = align_len,
    n_gaps = n_gaps,
    aligned1 = list(aligned1),
    aligned2 = list(aligned2)
  )
}


#' Batch Pairwise Alignment
#'
#' Align pairs of texts from a data frame. Pipe-friendly with tidyverse
#' conventions: data-first argument, tidy evaluation for column selection.
#'
#' @param .data A data frame or tibble.
#' @param col1 Column containing first texts (tidy-select, unquoted).
#' @param col2 Column containing second texts (tidy-select, unquoted).
#' @param sim_fn A similarity function (see [sim_from_function()]).
#' @param gap_open Gap opening penalty. Default -5.
#' @param gap_extend Gap extension penalty. Default -2.
#' @return The input tibble with added columns: ssw_score, ssw_identity,
#'   ssw_align_len, ssw_n_gaps, ssw_aligned1, ssw_aligned2.
#' @export
#' @examples
#' df <- tibble::tibble(
#'   text_a = c("the cat sat", "hello world"),
#'   text_b = c("the dog sat", "goodbye world")
#' )
#' sim <- sim_from_function(function(a, b) ifelse(a == b, 10, -5))
#' df |> ssw_batch_align(text_a, text_b, sim)
ssw_batch_align <- function(.data, col1, col2, sim_fn,
                            gap_open = -5, gap_extend = -2) {
  col1_name <- rlang::as_name(rlang::enquo(col1))
  col2_name <- rlang::as_name(rlang::enquo(col2))

  texts1 <- .data[[col1_name]]
  texts2 <- .data[[col2_name]]

  results <- lapply(seq_along(texts1), function(i) {
    ssw_align(texts1[[i]], texts2[[i]], sim_fn, gap_open, gap_extend)
  })

  result_tbl <- dplyr::bind_rows(results)

  .data$ssw_score <- result_tbl$score
  .data$ssw_identity <- result_tbl$identity
  .data$ssw_align_len <- result_tbl$align_len
  .data$ssw_n_gaps <- result_tbl$n_gaps
  .data$ssw_aligned1 <- result_tbl$aligned1
  .data$ssw_aligned2 <- result_tbl$aligned2

  .data
}


# Internal: split string into tokens if needed
.tokenize <- function(x) {
  if (length(x) == 1 && !is.na(x)) {
    tokens <- strsplit(x, "\\s+")[[1]]
    tokens[nchar(tokens) > 0]
  } else {
    as.character(x)
  }
}
