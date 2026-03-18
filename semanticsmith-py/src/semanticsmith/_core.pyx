# cython: language_level=3
"""Cython wrapper for the SSW C core."""

cimport numpy as cnp
import numpy as np

cnp.import_array()

cdef extern from "ssw_core.h":
    ctypedef struct SSWResult:
        double score
        int *align1
        int *align2
        int align_len

    SSWResult *ssw_align(
        const double *sim_matrix,
        int n, int m,
        double gap_open,
        double gap_extend
    )

    void ssw_result_free(SSWResult *result)


def c_align(double[:, ::1] sim_matrix, double gap_open, double gap_extend):
    """Call the C core alignment.

    Parameters
    ----------
    sim_matrix : 2D numpy array (n x m), float64, C-contiguous
    gap_open : float
    gap_extend : float

    Returns
    -------
    tuple: (score, align1_indices, align2_indices)
        align indices use -1 for gaps
    """
    cdef int n = sim_matrix.shape[0]
    cdef int m = sim_matrix.shape[1]

    cdef SSWResult *result = ssw_align(&sim_matrix[0, 0], n, m, gap_open, gap_extend)

    if result == NULL:
        raise MemoryError("SSW alignment failed to allocate memory")

    cdef int alen = result.align_len
    cdef double score = result.score

    a1 = np.empty(alen, dtype=np.intc)
    a2 = np.empty(alen, dtype=np.intc)

    cdef int[:] a1_view = a1
    cdef int[:] a2_view = a2
    cdef int i

    for i in range(alen):
        a1_view[i] = result.align1[i]
        a2_view[i] = result.align2[i]

    ssw_result_free(result)

    return score, a1, a2
