"""Pure-Python fallback for the C core when Cython extension is not available."""

import numpy as np


def c_align(sim_matrix, gap_open, gap_extend):
    """Pure-Python Gotoh local alignment (fallback when C extension unavailable).

    Parameters
    ----------
    sim_matrix : 2D numpy array (n x m)
    gap_open : float
    gap_extend : float

    Returns
    -------
    tuple: (score, align1_indices, align2_indices)
    """
    n, m = sim_matrix.shape

    H = np.zeros((n + 1, m + 1))
    E = np.full((n + 1, m + 1), -np.inf)
    F = np.full((n + 1, m + 1), -np.inf)
    tb = np.zeros((n + 1, m + 1), dtype=np.int32)

    TB_NONE, TB_DIAG, TB_UP, TB_LEFT = 0, 1, 2, 3

    max_score = 0.0
    max_i = max_j = 0

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            E[i, j] = max(H[i, j - 1] + gap_open, E[i, j - 1] + gap_extend)
            F[i, j] = max(H[i - 1, j] + gap_open, F[i - 1, j] + gap_extend)

            diag = H[i - 1, j - 1] + sim_matrix[i - 1, j - 1]
            h = max(0.0, diag, E[i, j], F[i, j])
            H[i, j] = h

            if h == 0.0:
                tb[i, j] = TB_NONE
            elif h == diag:
                tb[i, j] = TB_DIAG
            elif h == F[i, j]:
                tb[i, j] = TB_UP
            else:
                tb[i, j] = TB_LEFT

            if h > max_score:
                max_score = h
                max_i, max_j = i, j

    # Traceback
    align1 = []
    align2 = []
    ci, cj = max_i, max_j

    while ci > 0 and cj > 0 and H[ci, cj] > 0:
        d = tb[ci, cj]
        if d == TB_NONE:
            break
        elif d == TB_DIAG:
            align1.append(ci - 1)
            align2.append(cj - 1)
            ci -= 1
            cj -= 1
        elif d == TB_UP:
            align1.append(ci - 1)
            align2.append(-1)
            ci -= 1
        else:
            align1.append(-1)
            align2.append(cj - 1)
            cj -= 1

    align1.reverse()
    align2.reverse()

    return max_score, np.array(align1, dtype=np.intc), np.array(align2, dtype=np.intc)
