/*
 * ssw_core.h — Semantic Smith-Waterman core algorithm
 *
 * Implements local sequence alignment with affine gap penalties
 * using Gotoh's optimization. Operates on a pre-computed similarity
 * matrix so the caller handles word embedding lookups.
 */

#ifndef SSW_CORE_H
#define SSW_CORE_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Result of a single alignment */
typedef struct {
    double score;          /* Best local alignment score */
    int   *align1;         /* Indices into seq1 (-1 = gap) */
    int   *align2;         /* Indices into seq2 (-1 = gap) */
    int    align_len;      /* Length of the alignment */
} SSWResult;

/*
 * ssw_align — Local alignment via Gotoh's algorithm.
 *
 * sim_matrix: row-major n x m matrix of pairwise similarity scores
 *             sim_matrix[i * m + j] = similarity(seq1[i], seq2[j])
 * n, m:       lengths of seq1, seq2
 * gap_open:   penalty for opening a gap (should be negative)
 * gap_extend: penalty for extending a gap (should be negative)
 *
 * Returns heap-allocated SSWResult. Caller must call ssw_result_free().
 */
SSWResult *ssw_align(
    const double *sim_matrix,
    int n, int m,
    double gap_open,
    double gap_extend
);

/*
 * ssw_result_free — Free an SSWResult and its arrays.
 */
void ssw_result_free(SSWResult *result);

#ifdef __cplusplus
}
#endif

#endif /* SSW_CORE_H */
