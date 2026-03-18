/*
 * ssw_core.c — Gotoh-style local alignment with affine gap penalties.
 *
 * Uses three matrices:
 *   H[i][j] — best score ending with a match/mismatch at (i,j)
 *   E[i][j] — best score ending with a gap in seq1 (insertion)
 *   F[i][j] — best score ending with a gap in seq2 (deletion)
 *
 * Recurrences:
 *   E[i][j] = max(H[i][j-1] + gap_open, E[i][j-1] + gap_extend)
 *   F[i][j] = max(H[i-1][j] + gap_open, F[i-1][j] + gap_extend)
 *   H[i][j] = max(0,
 *                  H[i-1][j-1] + sim(i,j),
 *                  E[i][j],
 *                  F[i][j])
 */

#include "ssw_core.h"
#include <stdlib.h>
#include <string.h>
#include <float.h>

/* Traceback direction flags */
#define TB_NONE 0
#define TB_DIAG 1
#define TB_UP   2  /* gap in seq2 (deletion) */
#define TB_LEFT 3  /* gap in seq1 (insertion) */

/* Macro for row-major 2D indexing into flat array */
#define IDX(i, j, cols) ((i) * (cols) + (j))

static inline double dmax2(double a, double b) {
    return a > b ? a : b;
}

static inline double dmax4(double a, double b, double c, double d) {
    double ab = a > b ? a : b;
    double cd = c > d ? c : d;
    return ab > cd ? ab : cd;
}

SSWResult *ssw_align(
    const double *sim_matrix,
    int n, int m,
    double gap_open,
    double gap_extend
) {
    int rows = n + 1;
    int cols = m + 1;

    double *H = (double *)calloc((size_t)rows * cols, sizeof(double));
    double *E = (double *)calloc((size_t)rows * cols, sizeof(double));
    double *F = (double *)calloc((size_t)rows * cols, sizeof(double));
    int    *tb = (int *)calloc((size_t)rows * cols, sizeof(int));

    if (!H || !E || !F || !tb) {
        free(H); free(E); free(F); free(tb);
        return NULL;
    }

    /* Initialize E and F to -infinity so they don't win on row/col 0 */
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            E[IDX(i, j, cols)] = -DBL_MAX / 2;
            F[IDX(i, j, cols)] = -DBL_MAX / 2;
        }
    }

    double max_score = 0.0;
    int max_i = 0, max_j = 0;

    /* DP fill */
    for (int i = 1; i <= n; i++) {
        for (int j = 1; j <= m; j++) {
            /* Gap in seq1 (insertion): extending along j */
            E[IDX(i, j, cols)] = dmax2(
                H[IDX(i, j - 1, cols)] + gap_open,
                E[IDX(i, j - 1, cols)] + gap_extend
            );

            /* Gap in seq2 (deletion): extending along i */
            F[IDX(i, j, cols)] = dmax2(
                H[IDX(i - 1, j, cols)] + gap_open,
                F[IDX(i - 1, j, cols)] + gap_extend
            );

            /* Similarity score: sim_matrix is 0-indexed, DP is 1-indexed */
            double diag = H[IDX(i - 1, j - 1, cols)]
                        + sim_matrix[(i - 1) * m + (j - 1)];

            double h = dmax4(0.0, diag, E[IDX(i, j, cols)], F[IDX(i, j, cols)]);
            H[IDX(i, j, cols)] = h;

            /* Record traceback direction */
            if (h == 0.0) {
                tb[IDX(i, j, cols)] = TB_NONE;
            } else if (h == diag) {
                tb[IDX(i, j, cols)] = TB_DIAG;
            } else if (h == F[IDX(i, j, cols)]) {
                tb[IDX(i, j, cols)] = TB_UP;
            } else {
                tb[IDX(i, j, cols)] = TB_LEFT;
            }

            if (h > max_score) {
                max_score = h;
                max_i = i;
                max_j = j;
            }
        }
    }

    /* Traceback from (max_i, max_j) */
    /* Worst case alignment length is n + m */
    int capacity = n + m;
    int *a1 = (int *)malloc((size_t)capacity * sizeof(int));
    int *a2 = (int *)malloc((size_t)capacity * sizeof(int));

    if (!a1 || !a2) {
        free(H); free(E); free(F); free(tb);
        free(a1); free(a2);
        return NULL;
    }

    int len = 0;
    int ci = max_i, cj = max_j;

    while (ci > 0 && cj > 0 && H[IDX(ci, cj, cols)] > 0.0) {
        int dir = tb[IDX(ci, cj, cols)];
        if (dir == TB_NONE) break;

        if (dir == TB_DIAG) {
            a1[len] = ci - 1;  /* 0-indexed into original seq */
            a2[len] = cj - 1;
            ci--;
            cj--;
        } else if (dir == TB_UP) {
            a1[len] = ci - 1;
            a2[len] = -1;      /* gap */
            ci--;
        } else { /* TB_LEFT */
            a1[len] = -1;      /* gap */
            a2[len] = cj - 1;
            cj--;
        }
        len++;
    }

    /* Reverse the alignment (traceback goes backwards) */
    for (int k = 0; k < len / 2; k++) {
        int tmp;
        tmp = a1[k]; a1[k] = a1[len - 1 - k]; a1[len - 1 - k] = tmp;
        tmp = a2[k]; a2[k] = a2[len - 1 - k]; a2[len - 1 - k] = tmp;
    }

    free(H);
    free(E);
    free(F);
    free(tb);

    SSWResult *result = (SSWResult *)malloc(sizeof(SSWResult));
    if (!result) {
        free(a1); free(a2);
        return NULL;
    }

    result->score = max_score;
    result->align1 = a1;
    result->align2 = a2;
    result->align_len = len;

    return result;
}

void ssw_result_free(SSWResult *result) {
    if (result) {
        free(result->align1);
        free(result->align2);
        free(result);
    }
}
