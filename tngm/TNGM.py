import numpy as np
from .util import *
import pickle
import gzip
import math


class TopicalNGramModel:
    """

    K: number of topics (int)
    W: size of vocabulary (int)
    D: number of documents (int)
    corpus: corpus (list of list)
    vocabulary: different words (dictionary)
    mapping: map from words to a unique number (dictionary)
    q_dk: number of words assigned to topic k in document d (np array (D, K))
    n_kw: number of word w assigned to topic k in all documents (np array (K, W))
    m_kwv: number of word v assigned to topic k with previous word w in all documents (np array (K, W, W))
    p_kwx: number of x_v = x with v assigned to topic k and previous word w in all documents (np array (K, W, 2))
    n_k: number of words assigned to topic k (np array (W, 1))
    m_kw: number of words assigned to topic k with previous word w (np array (K, W))
    assignment: assignment of topics for each word


    """
    def __init__(self, data, corpus_time, n_topics, alpha, beta, gamma, sigma):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.sigma = sigma
        self.K = n_topics
        self.I = 2
        self.corpus_time = corpus_time
        self.corpus = data #read_doc_tngm(dir)
        self.D = len(self.corpus)
        self.vocabulary = initial_dictionary_tngm(self.corpus)
        self.mapping = generate_mapping(self.vocabulary)
        self.W = len(self.vocabulary)+1
        self.q_dk, self.n_kw, self.m_kwv, self.p_kwx, self.assignment, self.x \
            = initial_assignment_tngm(self.corpus, self.K, self.W, self.D, self.mapping)
        self.n_k = np.sum(self.n_kw, axis=1)
        self.m_kw = np.sum(self.m_kwv, axis=2)
        self.p_kw = np.sum(self.p_kwx, axis=2)
        print("TNGM with vocabulary size %s, topic num %s, corpus size %s"%(self.W, self.K, self.D))


    def log_likehood(self):
        log_likehood_sum = 0
        count = 0

        for i in range(self.D):
            termCnt = len(self.corpus[i])
            for j in range(len(self.corpus[i])):
                k = self.assignment[i][j]
                s = self.x[i][j]
                ###############################################################
                current_word = self.corpus[i][j]
                current_word_mapping = self.mapping.get(current_word, 0)

                p = 1.0
                if s == 0:
                    if j == 0:
                        p = (self.alpha + self.q_dk[i][k]) / (self.K * self.alpha + termCnt - 1)
                        p *= (
                        (self.beta + self.n_kw[k][current_word_mapping]) / (self.beta * self.W + self.n_k[k]))
                        p *= ((self.gamma + self.p_kwx[self.K][self.W][s]) / (
                        self.gamma * self.I + self.p_kw[self.K][self.W]))
                    else:
                        prev_word = self.corpus[i][j - 1]
                        prev_word_mapping = self.mapping.get(prev_word, 0)
                        pre_topic = self.assignment[i][j - 1]

                        p = (self.alpha + self.q_dk[i][k]) / (self.K * self.alpha + termCnt - 1)
                        p *= (
                        (self.beta + self.n_kw[k][current_word_mapping]) / (self.beta * self.W + self.n_k[k]))
                        p *= ((self.gamma + self.p_kwx[pre_topic][prev_word_mapping][s]) / (
                            self.gamma * self.I + self.p_kw[pre_topic][prev_word_mapping]))
                else:
                    if j == 0:
                        p = (self.alpha + self.q_dk[i][k]) / (self.K * self.alpha + termCnt - 1)
                        p *= (self.sigma + self.m_kwv[k][self.W][current_word_mapping]) / (
                        self.sigma * self.W + self.m_kw[k][self.W])
                        p *= ((self.gamma + self.p_kwx[self.K][self.W][s]) / (
                            self.gamma * self.I + self.p_kw[self.K][self.W]))
                    else:
                        prev_word = self.corpus[i][j - 1]
                        prev_word_mapping = self.mapping.get(prev_word, 0)
                        pre_topic = self.assignment[i][j - 1]

                        p = (self.alpha + self.q_dk[i][k]) / (self.K * self.alpha + termCnt - 1)
                        p *= (self.sigma + self.m_kwv[k][prev_word_mapping][
                            current_word_mapping]) / (
                                   self.sigma * self.W + self.m_kw[k][prev_word_mapping])
                        p *= ((self.gamma + self.p_kwx[pre_topic][prev_word_mapping][s]) / (
                            self.gamma * self.I + self.p_kw[pre_topic][prev_word_mapping]))
                log_likehood_sum += np.log(p)
                count += 1
        return log_likehood_sum/count

    def log_likehood_lda(self):
        log_likehood_sum = 0
        count = 0

        for i in range(self.D):
            termCnt = len(self.corpus[i])
            for j in range(len(self.corpus[i])):
                k = self.assignment[i][j]
                ###############################################################
                current_word = self.corpus[i][j]
                current_word_mapping = self.mapping.get(current_word, 0)

                p = (self.alpha + self.q_dk[i][k]) / (self.K * self.alpha + termCnt - 1)
                p *= (
                    (self.beta + self.n_kw[k][current_word_mapping]) / (self.beta * self.W + self.n_k[k]))

                log_likehood_sum += np.log(p)
                count += 1
        return log_likehood_sum / count


    def sample(self, i, j):
        termCnt = len(self.corpus[i])
        current_topic = self.assignment[i][j]
        current_x = self.x[i][j]
        self.q_dk[i, current_topic] -= 1
        ###############################################################
        current_word = self.corpus[i][j]
        current_word_mapping = self.mapping.get(current_word, 0)

        if j == 0:
            self.p_kwx[self.K, self.W, current_x] -= 1
            self.p_kw[self.K, self.W] -= 1
            if j < termCnt-1:
                x_next = self.x[i][j+1]
                self.p_kwx[current_topic, current_word_mapping, x_next] -= 1
                self.p_kw[current_topic, current_word_mapping] -= 1

        else:
            prev_word = self.corpus[i][j-1]
            prev_word_mapping = self.mapping.get(prev_word, 0)
            pre_topic = self.assignment[i][j-1]
            self.p_kwx[pre_topic, prev_word_mapping, current_x] -= 1
            self.p_kw[pre_topic, prev_word_mapping] -= 1
            if j < termCnt-1:
                x_next = self.x[i][j+1]
                self.p_kwx[current_topic, current_word_mapping, x_next] -= 1
                self.p_kw[current_topic, current_word_mapping] -= 1

        if current_x == 0:
            self.n_kw[current_topic, current_word_mapping] -= 1
            self.n_k[current_topic] -= 1
        elif j == 0:
            self.m_kwv[current_topic, self.W, current_word_mapping] -= 1
            self.m_kw[current_topic, self.W] -= 1

        else:
            prev_word = self.corpus[i][j - 1]
            prev_word_mapping = self.mapping.get(prev_word, 0)

            self.m_kwv[current_topic, prev_word_mapping, current_word_mapping] -= 1
            self.m_kw[current_topic, prev_word_mapping] -= 1

        p = np.zeros((self.K, self.I))
        for s in range(self.I):
            if s == 0:
                if j == 0:
                    p[:, s] = (self.alpha+self.q_dk[i]) #/(self.K*self.alpha+termCnt-1)
                    p[:, s] *= ((self.beta+self.n_kw[:, current_word_mapping])/(self.beta*self.W+self.n_k))
                    p[:, s] *= ((self.gamma+self.p_kwx[self.K][self.W][s])/(self.gamma*self.I+self.p_kw[self.K][self.W]))
                else:
                    prev_word = self.corpus[i][j - 1]
                    prev_word_mapping = self.mapping.get(prev_word, 0)
                    pre_topic = self.assignment[i][j - 1]

                    p[:, s] = (self.alpha+self.q_dk[i]) #/(self.K*self.alpha+termCnt-1)
                    p[:, s] *= ((self.beta+self.n_kw[:, current_word_mapping])/(self.beta*self.W+self.n_k))
                    p[:, s] *= ((self.gamma + self.p_kwx[pre_topic][prev_word_mapping][s]) / (
                    self.gamma * self.I + self.p_kw[pre_topic][prev_word_mapping]))
            else:
                if j == 0:
                    p[:, s] = (self.alpha + self.q_dk[i]) #/ (self.K * self.alpha + termCnt - 1)
                    #p[:, s] *= ((self.beta + self.n_kw[:, current_word_mapping]) / (self.beta * self.W + self.n_k))
                    p[:, s] *= (self.sigma+self.m_kwv[:, self.W, current_word_mapping])/(self.sigma*self.W+self.m_kw[:, self.W])
                    p[:, s] *= ((self.gamma + self.p_kwx[self.K, self.W, s]) / (
                    self.gamma * self.I + self.p_kw[self.K, self.W]))
                else:
                    prev_word = self.corpus[i][j - 1]
                    prev_word_mapping = self.mapping.get(prev_word, 0)
                    #pre_topic = self.assignment[i][j - 1]

                    p[:, s] = (self.alpha + self.q_dk[i]) #/ (self.K * self.alpha + termCnt - 1)
                    #p[:, s] *= ((self.beta+self.n_kw[:, current_word_mapping])/(self.beta*self.W+self.n_k))

                    p[:, s] *= (self.sigma+self.m_kwv[:, prev_word_mapping, current_word_mapping])/(self.sigma*self.W+self.m_kw[:, prev_word_mapping])
                    p[:, s] *= ((self.gamma + self.p_kwx[pre_topic][prev_word_mapping][s]) / (
                        self.gamma * self.I + self.p_kw[pre_topic][prev_word_mapping]))

        new_topic, new_x = getSample(p)
        #print(current_topic, new_topic)

        self.q_dk[i][new_topic] += 1

        if j == 0:
            self.p_kwx[self.K, self.W, new_x] += 1
            self.p_kw[self.K, self.W] += 1
            if j < termCnt - 1:
                x_next = self.x[i][j + 1]
                self.p_kwx[new_topic, current_word_mapping, x_next] += 1
                self.p_kw[new_topic, current_word_mapping] += 1

        else:
            prev_word = self.corpus[i][j - 1]
            prev_word_mapping = self.mapping.get(prev_word, 0)
            pre_topic = self.assignment[i][j - 1]
            self.p_kwx[pre_topic, prev_word_mapping, new_x] += 1
            self.p_kw[pre_topic, prev_word_mapping] += 1
            if j < termCnt - 1:
                x_next = self.x[i][j + 1]
                self.p_kwx[new_topic, current_word_mapping, x_next] += 1
                self.p_kw[new_topic, current_word_mapping] += 1

        if new_x == 0:
            self.n_kw[new_topic, current_word_mapping] += 1
            self.n_k[new_topic] += 1
        elif j == 0:
            self.m_kwv[new_topic, self.W, current_word_mapping] += 1
            self.m_kw[new_topic, self.W] += 1

        else:
            prev_word = self.corpus[i][j - 1]
            prev_word_mapping = self.mapping.get(prev_word, 0)

            self.m_kwv[new_topic, prev_word_mapping, current_word_mapping] += 1
            self.m_kw[new_topic, prev_word_mapping] += 1
        return new_topic, new_x

    def lda_sample(self, i, j):
        termCnt = len(self.corpus[i])
        current_topic = self.assignment[i][j]
        current_x = self.x[i][j]
        self.q_dk[i, current_topic] -= 1
        ###############################################################
        current_word = self.corpus[i][j]
        current_word_mapping = self.mapping.get(current_word, 0)

        if j == 0:
            self.p_kwx[self.K, self.W, current_x] -= 1
            self.p_kw[self.K, self.W] -= 1
            if j < termCnt - 1:
                x_next = self.x[i][j + 1]
                self.p_kwx[current_topic, current_word_mapping, x_next] -= 1
                self.p_kw[current_topic, current_word_mapping] -= 1

        else:
            prev_word = self.corpus[i][j - 1]
            prev_word_mapping = self.mapping.get(prev_word, 0)
            pre_topic = self.assignment[i][j - 1]
            self.p_kwx[pre_topic, prev_word_mapping, current_x] -= 1
            self.p_kw[pre_topic, prev_word_mapping] -= 1
            if j < termCnt - 1:
                x_next = self.x[i][j + 1]
                self.p_kwx[current_topic, current_word_mapping, x_next] -= 1
                self.p_kw[current_topic, current_word_mapping] -= 1

        if current_x == 0:
            self.n_kw[current_topic, current_word_mapping] -= 1
            self.n_k[current_topic] -= 1
        elif j == 0:
            self.m_kwv[current_topic, self.W, current_word_mapping] -= 1
            self.m_kw[current_topic, self.W] -= 1

        else:
            prev_word = self.corpus[i][j - 1]
            prev_word_mapping = self.mapping.get(prev_word, 0)

            self.m_kwv[current_topic, prev_word_mapping, current_word_mapping] -= 1
            self.m_kw[current_topic, prev_word_mapping] -= 1

        #p = np.zeros((self.K))
        p = (self.alpha + self.q_dk[i])  # /(self.K*self.alpha+termCnt-1)
        p *= ((self.beta + self.n_kw[:, current_word_mapping]) / (self.beta * self.W + self.n_k))
            # p[k][s] *= ((self.gamma+self.p_kwx[self.K][self.W][s])/(self.gamma*self.I+self.p_kw[self.K][self.W]))

        new_topic, _ = getSample(p.reshape(-1, 1))
        # print(current_topic, new_topic)
        new_x = random.randint(0, 1)

        self.q_dk[i][new_topic] += 1

        if j == 0:
            self.p_kwx[self.K, self.W, new_x] += 1
            self.p_kw[self.K, self.W] += 1
            if j < termCnt - 1:
                x_next = self.x[i][j + 1]
                self.p_kwx[new_topic, current_word_mapping, x_next] += 1
                self.p_kw[new_topic, current_word_mapping] += 1

        else:
            prev_word = self.corpus[i][j - 1]
            prev_word_mapping = self.mapping.get(prev_word, 0)
            pre_topic = self.assignment[i][j - 1]
            self.p_kwx[pre_topic, prev_word_mapping, new_x] += 1
            self.p_kw[pre_topic, prev_word_mapping] += 1
            if j < termCnt - 1:
                x_next = self.x[i][j + 1]
                self.p_kwx[new_topic, current_word_mapping, x_next] += 1
                self.p_kw[new_topic, current_word_mapping] += 1

        if new_x == 0:
            self.n_kw[new_topic, current_word_mapping] += 1
            self.n_k[new_topic] += 1
        elif j == 0:
            self.m_kwv[new_topic, self.W, current_word_mapping] += 1
            self.m_kw[new_topic, self.W] += 1

        else:
            prev_word = self.corpus[i][j - 1]
            prev_word_mapping = self.mapping.get(prev_word, 0)

            self.m_kwv[new_topic, prev_word_mapping, current_word_mapping] += 1
            self.m_kw[new_topic, prev_word_mapping] += 1
        return new_topic, new_x


    def gibbs_sampler_lda(self, n_burn_in=10):
        for i in range(n_burn_in):
            print('iteration ' + str(i))
            if i % 1 == 0:
                # self.check()
                likehood = self.log_likehood_lda()
                print("iter %s: log likehood: %s" % (i, likehood))
            for j in range(self.D):
                for k in range(len(self.corpus[j])):
                    new_topic, new_x = self.lda_sample(j, k)
                    self.assignment[j][k] = new_topic
                    self.x[j][k] = new_x


    def gibbs_sampler(self, n_burn_in=10):
        for i in range(n_burn_in):
            print('iteration ' + str(i))
            if i % 1 == 0:
                #self.check()
                likehood = self.log_likehood()
                print("iter %s: log likehood: %s"%(i, likehood))
            for j in range(self.D):
                for k in range(len(self.corpus[j])):
                    new_topic, new_x = self.sample(j, k)
                    self.assignment[j][k] = new_topic
                    self.x[j][k] = new_x


    def print_topics(self, num_words=50):
        vocabulary_inv = ["" for i in range(self.W)]
        for (k, v) in self.mapping.items():
            vocabulary_inv[v] = k
        topic_dist = self.n_kw / self.n_kw.sum(axis=1).reshape(-1, 1)
        for topic_id, topic in enumerate(self.n_kw):
            word_ids = np.argsort(topic)[::-1][:num_words]
            topic_word_list = []
            for word_id in word_ids:
                topic_word_list.append(vocabulary_inv[word_id])
            topic_word_list = [str(word) for word in topic_word_list]
            topic_str = ", ".join(topic_word_list)
            topic_str = "topic %s: %s" % (topic_id, topic_str)
            print(topic_str)

    def get_words(self):
        vocabulary_inv = ["" for i in range(self.W)]
        for (k, v) in self.mapping.items():
            vocabulary_inv[v] = k
        return vocabulary_inv, self.n_kw

    def get_phrase(self):
        ngramdocs = []
        phrase_vocab = []
        phrase_vocab_inverse = {}
        phrase = []
        for i in range(self.D):
            ngramdoc = []
            for j in range(len(self.corpus[i])):
                if j == 0:
                    phrase = []
                    phrase.append(self.corpus[i][j])
                if self.x[i][j] == 0:
                    if len(phrase) > 3:
                        phrase_str = [str(p) for p in phrase]
                        phrase_str = " ".join(phrase_str)
                        phrase_index = phrase_vocab_inverse.get(phrase_str, -1)
                        if phrase_index == -1:
                            phrase_vocab_inverse[phrase_str] = len(phrase_vocab)
                            phrase_vocab.append(phrase)
                        ngramdoc.append((self.corpus[i][j-1], self.assignment[i][j-1], phrase, self.corpus_time[i]))
                    phrase = []
                    phrase.append(self.corpus[i][j])
                else:
                    phrase.append(self.corpus[i][j])
            if len(phrase) > 3:
                phrase_str = [str(p) for p in phrase]
                phrase_str = " ".join(phrase_str)
                phrase_index = phrase_vocab_inverse.get(phrase_str, -1)
                if phrase_index == -1:
                    phrase_vocab_inverse[phrase_str] = len(phrase_vocab)
                    phrase_vocab.append(phrase)
                ngramdoc.append((self.corpus[i][j - 1], self.assignment[i][j - 1], phrase, self.corpus_time[i]))
            ngramdocs.append(ngramdoc)

        phrase_df_count = np.zeros(len(phrase_vocab), dtype=np.float)
        phrase_topic_count = np.zeros((self.K, len(phrase_vocab)), dtype=np.float)
        phrase_tf_count = np.zeros(len(phrase_vocab), dtype=np.float)
        topic_hour = np.zeros((self.K, 18), dtype=np.float)
        topic_count = np.zeros(self.K, dtype=np.float)
        for ngramdoc in ngramdocs:
            phrase_index_set = set()
            for word, topic, terms, time in ngramdoc:
                phrase_str = [str(p) for p in terms]
                phrase_str = " ".join(phrase_str)
                phrase_index = phrase_vocab_inverse.get(phrase_str, -1)
                if phrase_index == -1:
                    print("phrase vocab error ")
                phrase_topic_count[topic, phrase_index] += 1
                topic_count[topic] += 1
                topic_hour[topic, time-6] += 1
                phrase_tf_count[phrase_index] += 1
                phrase_index_set.add(phrase_index)
            for phrase_index in phrase_index_set:
                phrase_df_count[phrase_index] += 1

        #phrase_topic_dist = (self.beta+phrase_topic_count)/(self.beta*self.W+topic_count).reshape(-1, 1)
        phrase_topic_dist = phrase_topic_count/(topic_count).reshape(-1, 1)
        phrase_count_df = np.log(self.D/phrase_df_count)
        phrase_tf_count = phrase_tf_count/phrase_tf_count.sum()
        phrase_tfidf = phrase_tf_count*phrase_df_count
        #phrase_topic_dist *= phrase_count_df.reshape((1, -1))

        return phrase_vocab, phrase_topic_dist, phrase_tfidf, topic_count

    def get_sequence(self):
        sequence_dic = {}
        for i in range(self.D):
            for j in range(len(self.corpus[i])):
                sequence = []
                for k in range(len(self.corpus[i][j])):
                    if k == 0:
                        sequence.append(self.assignment[i][j][k])
                    elif self.x[i][j][k-1] == 0:
                        word = list_to_string(sequence)

                        if word in sequence_dic:
                            sequence_dic[word] += 1
                            sequence = [self.assignment[i][j][k]]
                        else:
                            sequence_dic[word] = 1
                            sequence = [self.assignment[i][j][k]]
                    else:
                        sequence.append(self.assignment[i][j][k])
                word = list_to_string(sequence)
                if word == '':
                    continue
                elif word in sequence_dic:
                    sequence_dic[word] += 1
                else:
                    sequence_dic[word] = 1

        print(sequence_dic)
        f = open('sequence_tngm_all.txt', 'wt')
        for sequence in sorted(sequence_dic.keys()):
            # for i in range(sequence_dic[sequence]):
            #     f.write(sequence+' ')
            f.write(sequence+' '+str(sequence_dic[sequence]))
            f.write('\n')
        f.close()
        return sequence_dic

    def check(self):
        q_dk = np.zeros((self.D, self.K))
        n_kw = np.zeros((self.K, self.W))
        m_kwv = np.zeros((self.K, self.W+1, self.W+1))
        p_kwx = np.zeros((self.K+1, self.W + 1, self.I))

        for i in range(len(self.corpus)):
            for j in range(len(self.corpus[i])):
                topic = self.assignment[i][j]

                word = self.mapping.get(self.corpus[i][j], 0)
                x_i = self.x[i][j]

                if j == 0:
                    p_kwx[self.K, self.W, x_i] += 1
                else:
                    prev_word = self.mapping.get(self.corpus[i][j - 1], 0)
                    p_kwx[self.assignment[i][j - 1], prev_word, x_i] += 1

                if x_i == 0:
                    n_kw[topic, word] += 1
                elif j == 0:
                    m_kwv[topic, self.W, word] += 1
                else:
                    prev_word = self.mapping.get(self.corpus[i][j - 1], 0)
                    m_kwv[topic, prev_word, word] += 1
                q_dk[i, topic] += 1

        # print(total_words, total_connection)
        # for i in range(m_kwv.shape[0]):
        #     for j in range(m_kwv.shape[1]):
        #         for k in range(m_kwv.shape[2]):
        #             if m_kwv[i, j, k] != self.m_kwv[i, j, k]:
        #                 print("%s, %s, %s: %s. %s"%(i, j, k, m_kwv[i, j, k], self.m_kwv[i, j, k]))
        print("q_dk:%s"%np.array_equal(self.q_dk, q_dk))
        print("n_kw:%s"%np.array_equal(self.n_kw, n_kw))
        print("m_kwv:%s"%np.array_equal(self.m_kwv, m_kwv))
        print("p_kwx:%s"%np.array_equal(self.p_kwx, p_kwx))

        print("n_k:%s"%np.array_equal(self.n_k, self.n_kw.sum(axis=1)))
        print("m_kw:%s"%np.array_equal(self.m_kw, self.m_kwv.sum(axis=2)))
        print("p_kwx:%s"%np.array_equal(self.p_kw, self.p_kwx.sum(axis=2)))

        print("check done")




#
# model = TopicalNGramModel(read_20newsgroups(), 20, 10, 0.01, 0.01, 0.01)
# model.gibbs_sampler(100)
# #model.get_sequence()
# #model.check()
# # with gzip.open("model.pkl.gz", 'wb') as gzip_file:
# #     pickle.dump(model, gzip_file, protocol=4)
#
# # with gzip.open("model.pkl.gz", 'rb') as gzip_file:
# #     model = pickle.load(gzip_file, protocol=4)
#
# model.print_topics()
# model.get_phrase()
