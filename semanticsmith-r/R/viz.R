#' Format an SSW Alignment Result
#'
#' Pretty-print the alignment from an [ssw_align()] result tibble.
#'
#' @param x A tibble returned by [ssw_align()] (single row).
#' @param width Minimum column width for token display. Default 0 (auto).
#' @return Invisibly returns `x`. Called for side effect of printing.
#' @export
#' @examples
#' sim <- sim_from_function(function(a, b) ifelse(a == b, 10, -5))
#' result <- ssw_align("the cat sat", "the dog sat", sim)
#' ssw_print(result)
ssw_print <- function(x, width = 0L) {
  if (nrow(x) == 0 || x$align_len[1] == 0) {
    cat("(no alignment)\n")
    return(invisible(x))
  }

  a1 <- x$aligned1[[1]]
  a2 <- x$aligned2[[1]]

  if (width == 0L) {
    width <- max(nchar(c(a1, a2)), 3L)
  }

  pad <- function(s) formatC(s, width = width, flag = "-")

  row1 <- paste(vapply(a1, pad, character(1)), collapse = " ")
  row2 <- paste(vapply(a2, pad, character(1)), collapse = " ")
  mid <- paste(vapply(seq_along(a1), function(i) {
    if (a1[i] == "---" || a2[i] == "---") {
      pad(" ")
    } else if (a1[i] == a2[i]) {
      pad("|")
    } else {
      pad("~")
    }
  }, character(1)), collapse = " ")

  cat(sprintf("Score: %.2f  Identity: %.1f%%  Length: %d  Gaps: %d\n",
              x$score[1], x$identity[1] * 100, x$align_len[1], x$n_gaps[1]))
  cat(row1, "\n")
  cat(mid, "\n")
  cat(row2, "\n")

  invisible(x)
}
