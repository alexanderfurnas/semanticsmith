#This software is a free software. Thus, it is licensed under GNU General Public License.
#Python implementation to Smith-Waterman Algorithm for Homework 1 of Bioinformatics class.
#Forrest Bao, Sept. 26 <http://fsbao.net> <forrest.bao aT gmail.com>
#Taken by Zander Furanas from github user alevchuk on 4/17/2017. Will be used as the starting codebase from which to create Semantic Smith-Waterman

# zeros() was origianlly from NumPy.
# This version is implemented by alevchuk 2011-04-10
from gensim.models.keyedvectors import KeyedVectors
from nltk.corpus import stopwords
stop = set(stopwords.words('english'))

def zeros(shape):
    retval = []
    for x in range(shape[0]):
        retval.append([])
        for y in range(shape[1]):
            retval[-1].append(0)
    return retval

#some things currently hardcoded here that should be parameters -- match, mismatch and gap penalties are all pegged to each other at the moment
scale = 3
match_award      = scale
mismatch_penalty = - scale
gap_penalty      = - scale # both for opening and extanding


#a couple of other hardcoded things that should be parameters -- stopword mismatch treated as half as bad as a normal mismatch
# stopwords not in the pretrained vector space. 
#Also vectors, scale and stopwords need to be passed to the function because I haven't written this with classes.

def score_match(word1, word2, word_vectors, scale, stop):
    try:
        word_sim = word_vectors.similarity(word1.lower(), word2.lower()) -.5
        match_score = word_sim * scale*2
        if match_score < 0:
            match_score = - scale
    except KeyError:
        if word1 == word2:
            match_score = scale
        elif word1 in stop and word2 in stop:
            match_score = -float(scale)/2
        else:
            match_score = - scale
        
    return match_score

def initialize_stuff(vec_source):
    word_vectors = KeyedVectors.load_word2vec_format(vec_source, binary=True)
    stop = set(stopwords.words('english'))
    return word_vectors, stops

def finalize(align1, align2, seq1, seq2, word_vec, scale, stop):
    align1 = align1[::-1]    #reverse sequence 1
    align2 = align2[::-1]    #reverse sequence 2
    
    i,j = 0,0
    
    #calcuate identity, score and aligned sequeces
    symbol = ''
    found = 0
    score = 0
    identity = 0
    for i in range(0,len(align1)):
        # if two AAs are the same, then output the letter
        if align1[i] == align2[i]:                
            symbol = symbol + align1[i]
            identity = identity + 1
            score += score_match(seq1[i-1], seq2[j-1], word_vec, scale, stop)
    
        # if they are not identical and none of them is gap
        elif align1[i] != align2[i] and align1[i] != '-' and align2[i] != '-': 
            score += score_match(seq1[i-1], seq2[j-1], word_vec, scale, stop)
            symbol += ' '
            found = 0
    
        #if one of them is a gap, output a space
        elif align1[i] == '-' or align2[i] == '-':          
            symbol += ' '
            score += gap_penalty
    
    identity = float(identity) / len(align1) * 100
    
    print 'Identity =', "%3.3f" % identity, 'percent'
    print 'Score =', score
    print align1
    print symbol
    print align2


def water(seq1, seq2, word_vec, scale, stop):
    m, n = len(seq1), len(seq2)  # length of two sequences
    
    # Generate DP table and traceback path pointer matrix
    score = zeros((m+1, n+1))      # the DP table
    pointer = zeros((m+1, n+1))    # to store the traceback path
    
    max_score = 0        # initial maximum score in DP table
    # Calculate DP table and mark pointers
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            score_diagonal = score[i-1][j-1] + score_match(seq1[i-1], seq2[j-1], word_vec, scale, stop)
            score_up = score[i][j-1] + gap_penalty
            score_left = score[i-1][j] + gap_penalty
            score[i][j] = max(0,score_left, score_up, score_diagonal)
            if score[i][j] == 0:
                pointer[i][j] = 0 # 0 means end of the path
            if score[i][j] == score_left:
                pointer[i][j] = 1 # 1 means trace up
            if score[i][j] == score_up:
                pointer[i][j] = 2 # 2 means trace left
            if score[i][j] == score_diagonal:
                pointer[i][j] = 3 # 3 means trace diagonal
            if score[i][j] >= max_score:
                max_i = i
                max_j = j
                max_score = score[i][j];
    
    align1, align2 = '', ''    # initial sequences
    
    i,j = max_i,max_j    # indices of path starting point
    
    #traceback, follow pointers
    while pointer[i][j] != 0:
        if pointer[i][j] == 3:
            align1 += seq1[i-1]
            align2 += seq2[j-1]
            i -= 1
            j -= 1
        elif pointer[i][j] == 2:
            align1 += '-'
            align2 += seq2[j-1]
            j -= 1
        elif pointer[i][j] == 1:
            align1 += seq1[i-1]
            align2 += '-'
            i -= 1

    finalize(align1, align2, seq1, seq2, word_vec, scale, stop)