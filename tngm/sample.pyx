cimport cython
import numpy as np
cimport numpy as np


def convertToIntArray(int val, int n):
    cdef np.ndarray[np.int64_t, ndim=1] result = np.zeros((n), dtype=np.int64)
    cdef unsigned int j = n-1
    cdef int i
    cdef int temp = val
    for i in range(j, -1, -1):
        if temp%2 == 0:
            result[j] = 0
        else:
            result[j] = 1
        j -= 1
        temp //= 2
    return result

def cal_p_val(int i, int K, int W, int I, int totalPermutation, int num_tokens, int num_sents, float alpha, float gamma, float beta, float sigma,
              np.ndarray[np.float64_t, ndim=1] sent_val,  np.ndarray[np.float64_t, ndim=2] q_dk,  np.ndarray[np.float64_t, ndim=3] p_kwx,
              np.ndarray[np.float64_t, ndim=2] p_kw, np.ndarray[np.float64_t, ndim=2] n_kw, np.ndarray[np.float64_t, ndim=1] n_k,
              np.ndarray[np.float64_t, ndim=3] m_kwv, np.ndarray[np.float64_t, ndim=2] m_kw):
    cdef np.ndarray[np.float64_t, ndim=2] p = np.zeros((K, totalPermutation), dtype=np.float64)
    for k in range(K):
        term1 = (alpha+q_dk[i][k])/(alpha*K+num_sents-1)
        for t in range(totalPermutation):
            indicators = convertToIntArray(t, num_tokens)
            term3 = 1.0
            for token_id in range(num_tokens):
                if token_id == 0:
                    term3 = term3*((gamma+p_kwx[k][W][indicators[token_id]])/(gamma*I+p_kw[k][W]))
                else:
                    prev_word_mapping = sent_val[token_id - 1]
                    term3 = term3*((gamma+p_kwx[k][prev_word_mapping][indicators[token_id]])/(gamma*I+p_kw[k][prev_word_mapping]))
    
            term4 = 1.0
            for token_id in range(num_tokens):
                current_word_mapping = sent_val[token_id]

                if indicators[token_id] == 0:
                    term4 = term4 * ((beta+n_kw[k][current_word_mapping])/(beta*W+n_k[k]))
                elif token_id == 0:
                    term4 *= (sigma+m_kwv[k][W][current_word_mapping])/(sigma*W+m_kw[k][W])
                else:
                    prev_word_mapping = sent_val[token_id - 1]
                    term4 *= (sigma+m_kwv[k][prev_word_mapping][current_word_mapping])/(sigma*W+m_kw[k][prev_word_mapping])
            p[k][t] = term1*term3*term4
    return p