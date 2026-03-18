test_that("ssw_align returns correct tibble for identical strings", {
  sim <- sim_from_function(function(a, b) ifelse(a == b, 10, -5))
  result <- ssw_align("the cat sat", "the cat sat", sim)

  expect_s3_class(result, "tbl_df")
  expect_equal(result$score, 30)
  expect_equal(result$identity, 1)
  expect_equal(result$align_len, 3L)
  expect_equal(result$n_gaps, 0L)
  expect_equal(result$aligned1[[1]], c("the", "cat", "sat"))
  expect_equal(result$aligned2[[1]], c("the", "cat", "sat"))
})

test_that("ssw_align returns zero for no match", {
  sim <- sim_from_function(function(a, b) ifelse(a == b, 10, -5))
  result <- ssw_align("aaa bbb", "ccc ddd", sim)

  expect_equal(result$score, 0)
  expect_equal(result$align_len, 0L)
})

test_that("ssw_align handles empty input", {
  sim <- sim_from_function(function(a, b) ifelse(a == b, 10, -5))
  result <- ssw_align("", "hello", sim)

  expect_equal(result$score, 0)
})

test_that("ssw_align detects local alignment", {
  sim <- sim_from_function(function(a, b) ifelse(a == b, 10, -5))
  result <- ssw_align("xx the cat xx", "yy the cat yy", sim)

  expect_equal(result$score, 20)
  expect_equal(result$aligned1[[1]], c("the", "cat"))
})

test_that("ssw_align accepts character vectors", {
  sim <- sim_from_function(function(a, b) ifelse(a == b, 10, -5))
  result <- ssw_align(c("the", "cat"), c("the", "cat"), sim)

  expect_equal(result$score, 20)
})

test_that("ssw_batch_align adds columns to data frame", {
  sim <- sim_from_function(function(a, b) ifelse(a == b, 10, -5))
  df <- tibble::tibble(
    text_a = c("the cat sat", "hello world"),
    text_b = c("the dog sat", "hello world")
  )

  result <- ssw_batch_align(df, text_a, text_b, sim)

  expect_s3_class(result, "tbl_df")
  expect_true("ssw_score" %in% names(result))
  expect_true("ssw_identity" %in% names(result))
  expect_equal(nrow(result), 2)
  # Second pair is identical
  expect_equal(result$ssw_score[2], 20)
})

test_that("ssw_batch_align works with pipes", {
  sim <- sim_from_function(function(a, b) ifelse(a == b, 10, -5))
  result <- tibble::tibble(
    a = c("hello world"),
    b = c("hello world")
  ) |>
    ssw_batch_align(a, b, sim)

  expect_equal(result$ssw_score, 20)
})

test_that("sim_from_matrix works", {
  mat <- matrix(c(10, 5, 5, 10), nrow = 2)
  vocab <- c("cat", "dog")
  sim <- sim_from_matrix(mat, vocab)

  expect_equal(sim("cat", "cat"), 10)
  expect_equal(sim("cat", "dog"), 5)
  expect_equal(sim("cat", "unknown"), -5)
})

test_that("sim_from_embeddings gives scale for identical words", {
  emb <- matrix(c(1, 0, 0, 1), nrow = 2, byrow = TRUE)
  rownames(emb) <- c("cat", "dog")
  sim <- sim_from_embeddings(emb, scale = 10)

  expect_equal(sim("cat", "cat"), 10)
})

test_that("sim_from_embeddings computes cosine similarity", {
  emb <- matrix(c(1, 0, 1, 0), nrow = 2, byrow = TRUE)
  rownames(emb) <- c("cat", "dog")
  # cosine(cat, dog) = 0, score = (0 + -0.5) * 10 = -5
  sim <- sim_from_embeddings(emb, offset = -0.5, scale = 10)

  expect_equal(sim("cat", "dog"), -5)
})

test_that("sim_from_embeddings returns default for OOV", {
  emb <- matrix(c(1, 0), nrow = 1)
  rownames(emb) <- "cat"
  sim <- sim_from_embeddings(emb, default = -8)

  expect_equal(sim("cat", "unknown"), -8)
})

test_that("sim_from_embeddings parallel vectors give max score", {
  emb <- matrix(c(1, 2, 2, 4), nrow = 2, byrow = TRUE)
  rownames(emb) <- c("a", "b")
  # cosine = 1.0, score = (1.0 + -0.5) * 10 = 5
  sim <- sim_from_embeddings(emb, offset = -0.5, scale = 10)

  expect_equal(sim("a", "b"), 5)
})

test_that("sim_from_embeddings integrates with ssw_align", {
  emb <- matrix(c(1, 0, 0.9, 0.1, 0, 1), nrow = 3, byrow = TRUE)
  rownames(emb) <- c("the", "a", "fish")
  sim <- sim_from_embeddings(emb)

  result <- ssw_align(c("the", "fish"), c("a", "fish"), sim)
  expect_gt(result$score, 0)
})

test_that("ssw_print runs without error", {
  sim <- sim_from_function(function(a, b) ifelse(a == b, 10, -5))
  result <- ssw_align("the cat", "the cat", sim)

  expect_output(ssw_print(result), "Score:")
})
