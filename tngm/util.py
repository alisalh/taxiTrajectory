import numpy as np
import random
from sklearn.datasets import fetch_20newsgroups
import re
from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS
from textblob import TextBlob
from lda import _lda
from scipy import sparse
from  matplotlib import pyplot
# from scipy import sparse


def read_doc_tngm(dir):
    """
    corpus: (# doc , # sentence, # words)
    """
    temp_corpus = []
    corpus = []
    with open(dir, 'rt') as f:
        for line in f:
            temp_corpus.append(line)
    for i in range(len(temp_corpus)):
        line = temp_corpus[i].split(',')
        corpus.append([])
        for j in range(len(line)):
            corpus[i].append(line[j].split())
    return corpus


def read_20newsgroups():
    corpus = []
    newsgroups_train = fetch_20newsgroups(subset='train')
    for i, d in enumerate(newsgroups_train.data):
        blob = TextBlob(d)
        corpus.append([])
        for j, sent in enumerate(blob.sentences):
            # if len(sent.words) > 32:
            #     print(sent)
            for word in sent.words:
                if word not in ENGLISH_STOP_WORDS:
                    corpus[i].append(word)
    print(len(corpus))
    return corpus


def initial_dictionary_tngm(corpus):
    """
    vocabulary: key: word, value: count
    """
    sum_count = 0
    vocabulary = {}
    for i in range(len(corpus)):
        for j in range(len(corpus[i])):
            if corpus[i][j] in vocabulary:
                vocabulary[corpus[i][j]] += 1
            else:
                vocabulary[corpus[i][j]] = 1
            sum_count += 1

    threshold_value = 1e-5*sum_count
    vocabulary_new = {}
    for (k, v) in vocabulary.items():
        if v >= threshold_value:
            vocabulary_new[k] = v
    return vocabulary_new


def initial_assignment_tngm(corpus, K, W, D, mapping):
    q_dk = np.zeros((D, K))
    n_kw = np.zeros((K, W))
    m_kwv = np.zeros((K, W+1, W+1))
    p_kwx = np.zeros((K+1, W+1, 2))
    assignment = []
    x = []
    for i in range(len(corpus)):
        assignment.append([])
        x.append([])
        for j in range(len(corpus[i])):
            topic = random.randint(0, K - 1)
            x_i = 0
            if j > 0:
                x_i = random.randint(0, 1)

            assignment[i].append(topic)
            x[i].append(x_i)

            word = mapping.get(corpus[i][j], 0)

            if j == 0:
                p_kwx[K, W, x_i] += 1
            else:
                prev_word = mapping.get(corpus[i][j-1], 0)
                p_kwx[assignment[i][j-1], prev_word, x_i] += 1

            if x_i == 0:
                n_kw[topic, word] += 1
            elif j == 0:
                m_kwv[topic, W, word] += 1
            else:
                prev_word = mapping.get(corpus[i][j-1], 0)
                m_kwv[topic, prev_word, word] += 1

            q_dk[i, topic] += 1

    return q_dk, n_kw, m_kwv, p_kwx, assignment, x


def convertToIntArray(val, n):
    result = np.zeros(n, dtype=np.int32)
    j = len(result)-1
    val_bin_str = "{0:b}".format(val)
    for i in range(len(val_bin_str)-1, -1, -1):
        if val_bin_str[i] == "0":
            result[j] = 0
        else:
            result[j] = 1
        j -= 1
    return result


def getSample(p):
    len1, len2 = p.shape
    num = len1*len2
    temp = np.cumsum(p.reshape(-1))
    #temp = np.roll(np.cumsum(np.roll(p.reshape(-1), 1)), -1)
    #temp[-1] = temp[-2]+p[-1]
    # temp = np.zeros(num)
    # cnt = 0
    # for i in range(len1):
    #     for j in range(len2):
    #         temp[cnt] = p[i][j]
    #         cnt += 1
    # temp = p.reshape(-1)
    # for i in range(num):
    #     temp[i] += temp[i-1]

    sample = random.uniform(0, 1)*temp[num-1]
    idx = np.searchsorted(temp, sample)
    # idx = 0
    # for idx in range(num):
    #     if sample < temp[idx]:
    #         break
    # p /= p.sum()
    # idx = sample_topic(p)
    topic = idx//len2
    indicator_val = idx%len2
    assert topic < 20
    return topic, indicator_val


def conditional_prob_z_x0(alpha,beta,q_dk,n_kw, n_k, d, n):
    """
    K: number of topics (int)
    W: size of vocabulary (int)
    D: number of documents (int)
    q_dk: number of words assigned to topic k in document d (np array (D, K))
    n_kw: number of word w assigned to topic k in all documents (np array (K, W))
    m_kwv: number of word v assigned to topic k with previous word w in all documents (np array (K, W, W))
    p_kwx: number of x_v = x with v assigned to topic k and previous word w in all documents (np array (K, W, 2))
    n_k: number of words assigned to topic k (np array (K, 1))
    m_kw: number of words assigned to topic k with previous word w (np array (K, W))

    """
    K = n_kw.shape[0]
    W = n_kw.shape[1]
    prob = np.zeros((K, 1))
    for k in range(K):
        prob[k] = (alpha + q_dk[d, k]) * (beta + n_kw[k, n]) / (n_k[k] + W * beta)
    prob = prob / np.sum(prob, axis=0)
    return prob

def conditional_prob_z_x1(alpha,sigma,q_dk,m_kwv, m_kw, d, n, v):
    """
    K: number of topics (int)
    W: size of vocabulary (int)
    D: number of documents (int)
    q_dk: number of words assigned to topic k in document d (np array (D, K))
    n_kw: number of word w assigned to topic k in all documents (np array (K, W))
    m_kwv: number of word v assigned to topic k with previous word w in all documents (np array (K, W, W))
    p_kwx: number of x_v = x with v assigned to topic k and previous word w in all documents (np array (K, W, 2))
    n_k: number of words assigned to topic k (np array (K, 1))
    m_kw: number of words assigned to topic k with previous word w (np array (K, W))

    """
    K = m_kwv.shape[0]
    W = m_kwv.shape[1]
    prob = np.zeros((K, 1))
    for k in range(K):
        prob[k] = (alpha + q_dk[d, k] ) * (sigma + m_kwv[k, v, n]) / (m_kw[k, v] + W * sigma )
    prob = prob / np.sum(prob, axis=0)
    return prob

def conditional_prob_x_x0(gamma,beta,p_kwx, n_kw, n_k, n, v, z_i, z_i1):
    """
    K: number of topics (int)
    W: size of vocabulary (int)
    D: number of documents (int)
    q_dk: number of words assigned to topic k in document d (np array (D, K))
    n_kw: number of word w assigned to topic k in all documents (np array (K, W))
    m_kwv: number of word v assigned to topic k with previous word w in all documents (np array (K, W, W))
    p_kwx: number of x_v = x with v assigned to topic k and previous word w in all documents (np array (K, W, 2))
    n_k: number of words assigned to topic k (np array (K, 1))
    m_kw: number of words assigned to topic k with previous word w (np array (K, W))

    """

    W = n_kw.shape[1]
    prob = np.zeros((2, 1))
    for x in range(2):
        prob[x] = (gamma + p_kwx[z_i1, v, x]) * (beta + n_kw[z_i, n]) / (n_k[z_i] + W * beta )
    prob = prob / np.sum(prob, axis=0)

    return prob

def conditional_prob_x_x1(gamma, sigma, p_kwx, m_kwv, m_kw, n, v, z_i, z_i1):
    """
    K: number of topics (int)
    W: size of vocabulary (int)
    D: number of documents (int)
    q_dk: number of words assigned to topic k in document d (np array (D, K))
    n_kw: number of word w assigned to topic k in all documents (np array (K, W))
    m_kwv: number of word v assigned to topic k with previous word w in all documents (np array (K, W, W))
    p_kwx: number of x_v = x with v assigned to topic k and previous word w in all documents (np array (K, W, 2))
    n_k: number of words assigned to topic k (np array (K, 1))
    m_kw: number of words assigned to topic k with previous word w (np array (K, W))

    """
    W = m_kw.shape[1]
    prob = np.zeros((2, 1))
    for x in range(2):
        prob[x] = (gamma + p_kwx[z_i1, v, x]) * (sigma + m_kwv[z_i, v, n]) / (m_kw[z_i, v] + W * sigma)
    prob = prob / np.sum(prob, axis=0)

    return prob

#
# below for lda
#

def read_doc_lda(dir):
    """
    corpus: (# doc ,  # words)
    """
    corpus = []
    with open(dir, 'rt') as f:
        for line in f:
            corpus.append(line)
    for i in range(len(corpus)):
        corpus[i] = corpus[i].replace(',',' ')
        corpus[i] = corpus[i].split()
    return corpus


def initial_dictionary_lda(corpus):
    """
    vocabulary: key: word, value: count
    """
    vocabulary = {}
    for i in range(len(corpus)):
        for j in range(len(corpus[i])):
            if corpus[i][j] in vocabulary:
                vocabulary[corpus[i][j]] += 1
            else:
                vocabulary[corpus[i][j]] = 1
    return vocabulary


def generate_mapping(vocabulary):
    count = 1
    mapping = {}
    for key in vocabulary:
        mapping[key] = count
        count += 1
    return mapping


def initial_assignment_lda(corpus, K, W, D, mapping):
    n_dk = np.zeros((D, K))
    m_kw = np.zeros((K, W))
    assignment = []
    for i in range(len(corpus)):
        assignment.append([])
        for j in range(len(corpus[i])):
            topic = random.randint(0, K - 1)
            n_dk[i, topic] += 1
            m_kw[topic, mapping[corpus[i][j]]] += 1
            assignment[i].append(topic)

    return n_dk, m_kw, assignment


def conditional_prob(n_dk, n_d, m_kw, m_k, d, n, alpha, beta):
    """
    n_dk: number of words assigned to topic k in document d (np array (D, K))
    m_kw: number of word w assigned to topic k in document (np array (K, W))
    n_d: number of words in d (np array (D, 1))
    m_k: number of words assigned to topic k in all documents (np array (K, 1))

    """
    K = m_k.shape[0]
    W = m_kw.shape[1]
    prob = np.zeros((K, 1))
    for k in range(K):
        prob[k] = (n_dk[d, k] + alpha) / (n_d[d] + K * alpha) * (m_kw[k, n] + beta) / (m_k[k] + W * beta)

    prob = prob / np.sum(prob, axis=0)
    return prob


def sample_topic(prob):
    K = prob.shape[0]
    sample = random.uniform(0, 1)
    cumulative_prob = 0
    for i in range(K):
        cumulative_prob += prob[i]
        if sample < cumulative_prob:
            return i
    return K-1


def list_to_string(l):
    res = ''
    if len(l) == 0:
        return res
    for i in range(len(l)):
        res += str(l[i]) + '_to_'
    return res[:-4]
