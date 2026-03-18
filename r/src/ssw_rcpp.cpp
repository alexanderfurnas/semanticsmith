// ssw_rcpp.cpp — Rcpp wrapper for the SSW C core.

#include <Rcpp.h>

extern "C" {
#include "ssw_core.h"
}

//' Perform SSW alignment on a pre-computed similarity matrix
//'
//' @param sim_matrix Numeric matrix (n x m) of pairwise similarities
//' @param gap_open Gap opening penalty (negative)
//' @param gap_extend Gap extension penalty (negative)
//' @return List with score, align1 (1-indexed, 0=gap), align2 (1-indexed, 0=gap)
//' @keywords internal
// [[Rcpp::export]]
Rcpp::List c_ssw_align(
    Rcpp::NumericMatrix sim_matrix,
    double gap_open,
    double gap_extend
) {
    int n = sim_matrix.nrow();
    int m = sim_matrix.ncol();

    // R matrices are column-major; C core expects row-major.
    // Copy to row-major.
    std::vector<double> row_major(n * m);
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < m; j++) {
            row_major[i * m + j] = sim_matrix(i, j);
        }
    }

    SSWResult *result = ssw_align(row_major.data(), n, m, gap_open, gap_extend);

    if (!result) {
        Rcpp::stop("SSW alignment failed to allocate memory");
    }

    // Convert to 1-indexed (R convention), using 0 for gaps
    Rcpp::IntegerVector a1(result->align_len);
    Rcpp::IntegerVector a2(result->align_len);

    for (int k = 0; k < result->align_len; k++) {
        a1[k] = result->align1[k] >= 0 ? result->align1[k] + 1 : 0;
        a2[k] = result->align2[k] >= 0 ? result->align2[k] + 1 : 0;
    }

    double score = result->score;
    ssw_result_free(result);

    return Rcpp::List::create(
        Rcpp::Named("score") = score,
        Rcpp::Named("align1") = a1,
        Rcpp::Named("align2") = a2
    );
}
