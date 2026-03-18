/*
 * test_ssw_core.c — Basic tests for the SSW C core.
 * Compile: cc -o test_ssw_core test_ssw_core.c ../csrc/ssw_core.c -I../csrc -lm
 */

#include "ssw_core.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

static int tests_run = 0;
static int tests_passed = 0;

#define ASSERT(cond, msg) do { \
    tests_run++; \
    if (!(cond)) { \
        printf("FAIL: %s\n", msg); \
    } else { \
        tests_passed++; \
        printf("PASS: %s\n", msg); \
    } \
} while(0)

/* Test 1: Identical short sequences should get perfect alignment */
static void test_identical(void) {
    /* 3 tokens vs 3 tokens, all identical → sim = 10 on diagonal */
    /* sim_matrix[i*3+j]: identity matrix scaled by 10 */
    double sim[9] = {
        10, -5, -5,
        -5, 10, -5,
        -5, -5, 10,
    };

    SSWResult *r = ssw_align(sim, 3, 3, -5.0, -2.0);
    ASSERT(r != NULL, "identical: result not null");
    ASSERT(r->align_len == 3, "identical: alignment length is 3");
    ASSERT(r->score == 30.0, "identical: score is 30");
    ASSERT(r->align1[0] == 0 && r->align1[1] == 1 && r->align1[2] == 2,
           "identical: align1 indices correct");
    ASSERT(r->align2[0] == 0 && r->align2[1] == 1 && r->align2[2] == 2,
           "identical: align2 indices correct");
    ssw_result_free(r);
}

/* Test 2: Completely dissimilar → score 0, no alignment */
static void test_no_match(void) {
    double sim[4] = {
        -10, -10,
        -10, -10,
    };

    SSWResult *r = ssw_align(sim, 2, 2, -5.0, -2.0);
    ASSERT(r != NULL, "no_match: result not null");
    ASSERT(r->score == 0.0, "no_match: score is 0");
    ASSERT(r->align_len == 0, "no_match: alignment is empty");
    ssw_result_free(r);
}

/* Test 3: Gap insertion — seq2 has an extra token in the middle */
static void test_gap(void) {
    /* seq1: A B C  (3 tokens)
     * seq2: A X B C  (4 tokens)
     * Best alignment: A-BC vs AX BC with a gap or A_BC vs A_BC skipping X
     *
     * Similarity: A=A:10, B=B:10, C=C:10, others:-5
     */
    double sim[12] = {
     /* seq2: A    X    B    C  */
        10,  -5,  -5,  -5,   /* seq1[0]=A */
        -5,  -5,  10,  -5,   /* seq1[1]=B */
        -5,  -5,  -5,  10,   /* seq1[2]=C */
    };

    SSWResult *r = ssw_align(sim, 3, 4, -8.0, -2.0);
    ASSERT(r != NULL, "gap: result not null");
    ASSERT(r->score > 0, "gap: positive score");

    /* Check that A, B, C all appear aligned */
    int found_a = 0, found_b = 0, found_c = 0;
    for (int k = 0; k < r->align_len; k++) {
        if (r->align1[k] == 0 && r->align2[k] == 0) found_a = 1;
        if (r->align1[k] == 1 && r->align2[k] == 2) found_b = 1;
        if (r->align1[k] == 2 && r->align2[k] == 3) found_c = 1;
    }
    ASSERT(found_a && found_b && found_c, "gap: all matching tokens aligned");
    ssw_result_free(r);
}

/* Test 4: Local alignment — only a subsequence should match */
static void test_local(void) {
    /* seq1: X A B X  (4 tokens)
     * seq2: Y A B Y  (4 tokens)
     * Only A,B match. X/Y are dissimilar.
     */
    double sim[16] = {
     /* Y    A    B    Y   */
        -5,  -5,  -5,  -5,  /* X */
        -5,  10,  -5,  -5,  /* A */
        -5,  -5,  10,  -5,  /* B */
        -5,  -5,  -5,  -5,  /* X */
    };

    SSWResult *r = ssw_align(sim, 4, 4, -5.0, -2.0);
    ASSERT(r != NULL, "local: result not null");
    ASSERT(r->score == 20.0, "local: score is 20 (only AB matched)");
    ASSERT(r->align_len == 2, "local: alignment length is 2");
    ASSERT(r->align1[0] == 1 && r->align1[1] == 2, "local: seq1 indices are A,B");
    ASSERT(r->align2[0] == 1 && r->align2[1] == 2, "local: seq2 indices are A,B");
    ssw_result_free(r);
}

int main(void) {
    test_identical();
    test_no_match();
    test_gap();
    test_local();

    printf("\n%d/%d tests passed\n", tests_passed, tests_run);
    return tests_passed == tests_run ? 0 : 1;
}
