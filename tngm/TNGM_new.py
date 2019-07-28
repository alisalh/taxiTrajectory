import numpy as np
from .util import *
import pickle
import gzip
import math
from scipy import sparse
from sklearn import manifold
from apriori import encode_item_list
import collections


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
    def __init__(self, data, n_topics, alpha, beta, gamma, sigma):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.sigma = sigma
        self.K = n_topics
        # self.corpus_time = corpus_time
        self.corpus = data #read_doc_tngm(dir)
        self.D = len(self.corpus)
        self.vocabulary = initial_dictionary_tngm(self.corpus)
        self.mapping = generate_mapping(self.vocabulary)
        self.W = len(self.vocabulary)+1
        self.q_dk, self.m_kwv, self.assignment\
            = self.initial_assignment_tngm(self.corpus, self.K, self.W, self.D, self.mapping)
        self.m_kw = np.array([a.sum(axis=1) for a in self.m_kwv]).T
        print("TNGM with vocabulary size %s, topic num %s, corpus size %s"%(self.W, self.K, self.D))


    def initial_assignment_tngm(self, corpus, K, W, D, mapping):
        q_dk = np.zeros((D, K))
        m_kwv = [np.zeros((K, W+1)) for i in range(W+1)]
        assignment = []
        for i in range(len(corpus)):
            assignment.append([])
            for j in range(len(corpus[i])):
                topic = random.randint(0, K - 1)

                assignment[i].append(topic)

                word = mapping.get(corpus[i][j], 0)

                if j == 0:
                    m_kwv[W][topic, word] += 1
                else:
                    prev_word = mapping.get(corpus[i][j-1], 0)
                    m_kwv[prev_word][topic, word] += 1
                    #m_kwv[W][topic, word] += 1

                q_dk[i, topic] += 1
        #m_kwv = [sparse.lil_matrix(a) for a in m_kwv]
        return q_dk, m_kwv, assignment

    def log_likehood(self):
        log_likehood_sum = 0
        count = 0

        for i in range(self.D):
            termCnt = len(self.corpus[i])
            for j in range(len(self.corpus[i])):
                k = self.assignment[i][j]
                ###############################################################
                current_word = self.corpus[i][j]
                current_word_mapping = self.mapping.get(current_word, 0)
                p = 1.0
                if j == 0:
                    # try:
                    kwv_value = self.m_kwv[self.W][k][current_word_mapping]
                    # except:
                    #     kwv_value = 0
                    p = (self.alpha + self.q_dk[i][k]) / (self.K * self.alpha + termCnt - 1)
                    p *= (self.sigma + kwv_value) / (
                    self.sigma * self.W + self.m_kw[k][self.W])

                else:
                    prev_word = self.corpus[i][j - 1]
                    prev_word_mapping = self.mapping.get(prev_word, 0)
                    # pre_topic = self.assignment[i][j - 1]

                    # try:
                    kwv_value = self.m_kwv[prev_word_mapping][k][current_word_mapping]
                    # except:
                    #     kwv_value = 0
                    p = (self.alpha + self.q_dk[i][k]) / (self.K * self.alpha + termCnt - 1)
                    p *= (self.sigma + kwv_value) / (
                               self.sigma * self.W + self.m_kw[k][prev_word_mapping])
                log_likehood_sum += np.log(p)
                count += 1
        return log_likehood_sum/count

    # def log_likehood_lda(self):
    #     log_likehood_sum = 0
    #     count = 0
    #
    #     for i in range(self.D):
    #         termCnt = len(self.corpus[i])
    #         for j in range(len(self.corpus[i])):
    #             k = self.assignment[i][j]
    #             ###############################################################
    #             current_word = self.corpus[i][j]
    #             current_word_mapping = self.mapping.get(current_word, 0)
    #
    #             p = (self.alpha + self.q_dk[i][k]) / (self.K * self.alpha + termCnt - 1)
    #             p *= (
    #                 (self.beta + self.m_kwv[self.W][k][current_word_mapping]) / (self.beta * self.W + self.m_kw[k][self.W]))
    #
    #             log_likehood_sum += np.log(p)
    #             count += 1
    #     return log_likehood_sum / count


    # def lda_sample(self, i, j):
    #     termCnt = len(self.corpus[i])
    #     current_topic = self.assignment[i][j]
    #     self.q_dk[i, current_topic] -= 1
    #     ###############################################################
    #     current_word = self.corpus[i][j]
    #     current_word_mapping = self.mapping.get(current_word, 0)
    #
    #     self.m_kwv[self.W][current_topic, current_word_mapping] -= 1
    #     self.m_kw[current_topic, self.W] -= 1
    #
    #     # p = np.zeros((self.K))
    #     p = (self.alpha + self.q_dk[i])  # /(self.K*self.alpha+termCnt-1)
    #     p *= ((self.beta + self.m_kwv[self.W][:, current_word_mapping]) / (self.beta * self.W + self.m_kw[:, self.W]))
    #     # p[k][s] *= ((self.gamma+self.p_kwx[self.K][self.W][s])/(self.gamma*self.I+self.p_kw[self.K][self.W]))
    #
    #     new_topic, _ = getSample(p.reshape(-1, 1))
    #     # print(current_topic, new_topic)
    #
    #     self.q_dk[i][new_topic] += 1
    #     self.m_kwv[self.W][new_topic, current_word_mapping] += 1
    #     self.m_kw[new_topic, self.W] += 1
    #
    #     return new_topic
    #
    # def gibbs_sampler_lda(self, n_burn_in=10):
    #     for i in range(n_burn_in):
    #         print('iteration ' + str(i))
    #         if i % 1 == 0:
    #             # self.check()
    #             likehood = self.log_likehood_lda()
    #             print("iter %s: log likehood: %s" % (i, likehood))
    #         for j in range(self.D):
    #             for k in range(len(self.corpus[j])):
    #                 new_topic = self.lda_sample(j, k)
    #                 self.assignment[j][k] = new_topic

    def sample(self, i, j):
        # termCnt = len(self.corpus[i])
        current_topic = self.assignment[i][j]
        self.q_dk[i, current_topic] -= 1
        ###############################################################
        current_word = self.corpus[i][j]
        current_word_mapping = self.mapping.get(current_word, 0)

        if j == 0:
            self.m_kwv[self.W][current_topic, current_word_mapping] -= 1
            self.m_kw[current_topic, self.W] -= 1

        else:
            prev_word = self.corpus[i][j - 1]
            prev_word_mapping = self.mapping.get(prev_word, 0)

            self.m_kwv[prev_word_mapping][current_topic, current_word_mapping] -= 1
            self.m_kw[current_topic, prev_word_mapping] -= 1

        p = np.zeros(self.K)
        if j == 0:
            # try:
            kwv_value = self.m_kwv[self.W][:, current_word_mapping]
            #kwv_value = np.squeeze(kwv_value, axis=-1)
            # except:
            #     kwv_value = 0
            p = (self.alpha + self.q_dk[i]) #/ (self.K * self.alpha + termCnt - 1)
            #p[:, s] *= ((self.beta + self.n_kw[:, current_word_mapping]) / (self.beta * self.W + self.n_k))
            p *= (self.sigma+kwv_value)/(self.sigma*self.W+self.m_kw[:, self.W])
        else:
            prev_word = self.corpus[i][j - 1]
            prev_word_mapping = self.mapping.get(prev_word, 0)
            #pre_topic = self.assignment[i][j - 1]

            kwv_value = self.m_kwv[prev_word_mapping][:, current_word_mapping]
                # kwv_value = np.squeeze(kwv_value, axis=-1)
            p = (self.alpha + self.q_dk[i]) #/ (self.K * self.alpha + termCnt - 1)
            #p[:, s] *= ((self.beta+self.n_kw[:, current_word_mapping])/(self.beta*self.W+self.n_k))

            p *= (self.sigma+kwv_value)/(self.sigma*self.W+self.m_kw[:, prev_word_mapping])

        new_topic, _ = getSample(p.reshape(-1, 1))
        #print(current_topic, new_topic)

        self.q_dk[i][new_topic] += 1

        if j == 0:
            self.m_kwv[self.W][new_topic, current_word_mapping] += 1
            self.m_kw[new_topic, self.W] += 1

        else:
            prev_word = self.corpus[i][j - 1]
            prev_word_mapping = self.mapping.get(prev_word, 0)

            self.m_kwv[prev_word_mapping][new_topic, current_word_mapping] += 1
            self.m_kw[new_topic, prev_word_mapping] += 1
        return new_topic


    def gibbs_sampler(self, n_burn_in=10):
        #self.m_kwv = [a.toarray() for a in self.m_kwv]
        for i in range(n_burn_in):
            print('iteration ' + str(i))
            if i % 1 == 0:
                # self.check()
                likehood = self.log_likehood()
                print("iter %s: log likehood: %s"%(i, likehood))
            for j in range(self.D):
                for k in range(len(self.corpus[j])):
                    new_topic = self.sample(j, k)
                    self.assignment[j][k] = new_topic
        #self.m_kwv = [sparse.lil_matrix(a) for a in self.m_kwv]


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

    def get_phrase(self, items, docs_meta):
        def gaussian(x, mu, sig):
            return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))
        phrase_vocab = []
        phrase_vocab_inverse = {}
        phrase_support = {}
        max_item_length = -1
        for item in items:
            tmp = item[0]
            tmp_list = tmp.split("_")
            item_length = len(tmp_list) - 1 - 2 * int(tmp_list[0])
            #item_length = len(item[0].split("_"))
            if item_length < 2:
                # if max_item_value < int(item[0]):
                #     max_item_value = int(item[0])
                continue
            phrase_vocab_inverse[item[0]] = len(phrase_vocab)
            phrase_vocab.append(item[0])
            phrase_support[item[0]] = item[1]
            if item_length > max_item_length:
                max_item_length = item_length
        phrase_vocab_set = set(phrase_vocab)
        #print(phrase_vocab_set)

        phrase_to_docs = [[] for i in phrase_vocab]
        ngramdocs = []
        for i in range(self.D):
            ngramdoc = []
            #terms_doc = []
            for k in range(max_item_length, 1, -1):
                for j in range(len(self.corpus[i])-k+1):
                    phrase = self.corpus[i][j:j+k]
                    phrase_str = [str(p).replace("_", "--") for p in phrase]
                    #print(phrase_str)
                    phrase_str = encode_item_list(phrase_str)#"_".join(phrase_str)
                    #phrase_index = phrase_vocab_inverse.get(phrase_str, -1)
                    if phrase_str in phrase_vocab_set:
                    # if phrase_index != -1:
                    #     bool_sub_phrase = False
                    #     for term in terms_doc:
                    #         if term[0] <= j and term[1] >= j+k:
                    #             bool_sub_phrase =True
                    #     if bool_sub_phrase:
                    #         continue
                    #     terms_doc.append([j, j+k])
                        topic_list = self.assignment[i][j:j+k]
                        #print(phrase_str, topic_list)
                        weight_x = np.linspace(0, 1, num=len(topic_list), endpoint=True)
                        topic_weight = 1 - gaussian(weight_x, 0.5, 1)
                        topic_count = np.zeros(self.K)
                        for term_topic, term_weight in zip(topic_list, topic_weight):
                            topic_count[term_topic] += 1.0 #term_weight
                        phrase_topic = topic_count/topic_count.sum() #np.argmax(topic_count)
                        distance_phrase = docs_meta[i][13][j+k-1] - docs_meta[i][13][j]
                        time_phrase = docs_meta[i][8][j+k-1] - docs_meta[i][8][j]
                        time_phrase = time_phrase.seconds
                        phrase_speed = distance_phrase/(time_phrase/3600)
                        #print(docs_meta[i][13][-1] - docs_meta[i][13][0])
                        ngramdoc.append((phrase_str, phrase, phrase_topic, docs_meta[i][8][j].hour, docs_meta[i][8][j+k-1].hour, phrase_speed, distance_phrase, time_phrase/3600))
                        phrase_id = phrase_vocab_inverse[phrase_str]
                        phrase_to_docs[phrase_id].append(i)
            ngramdocs.append(ngramdoc)
            if i%1000 == 0:
                print("process %s docs"%i)
        terms_set = set()
        for i in range(self.D):
            for j in range(len(self.corpus[i])):
                terms_set.add(str(self.corpus[i][j]).replace("_", "--"))
        terms_vocab = list(terms_set)
        terms_vocab_inv = {}
        for term_index, term in enumerate(terms_vocab):
            terms_vocab_inv[term] = term_index
        num_terms = len(terms_vocab)
        topic_os = np.zeros((self.K, num_terms), dtype=np.int32)
        topic_ds = np.zeros((self.K, num_terms), dtype=np.int32)
        topic_hour = np.zeros((self.K, 18), dtype=np.float)
        for i in range(self.D):
            topic_list = self.assignment[i][:len(self.corpus)]
            topic_count = np.zeros(self.K)
            for term_topic in topic_list:
                topic_count[term_topic] += 1.0  # term_weight
            doc_topic = np.argmax(topic_count)
            start_time = docs_meta[i][8][0].hour
            topic_hour[doc_topic, start_time-6] += 1
            topic_os[doc_topic, terms_vocab_inv[str(self.corpus[i][0].replace("_", "--"))]] += 1
            topic_ds[doc_topic, terms_vocab_inv[str(self.corpus[i][-1]).replace("_", "--")]] += 1

        phrase_df_count = np.zeros(len(phrase_vocab), dtype=np.float)
        phrase_topic_count = np.zeros((self.K, len(phrase_vocab)), dtype=np.float)
        phrase_tf_count = np.zeros(len(phrase_vocab), dtype=np.float)
        phrase_hour_speed =  collections.defaultdict({}) #np.zeros((len(phrase_vocab), 18, 7))
        phrase_distance = np.zeros(len(phrase_vocab), dtype=np.float)
        phrase_distance_count = np.zeros(len(phrase_vocab), dtype=np.float)+1e-15

        for doc_id, ngramdoc in enumerate(ngramdocs):
            phrase_index_set = set()
            for phrase_str, terms, topic, start_time, end_time, speed, distance, time_span in ngramdoc:
                #phrase_str = [str(p) for p in terms]
                #phrase_str = " ".join(phrase_str)
                phrase_index = phrase_vocab_inverse.get(phrase_str, -1)
                phrase_distance[phrase_index] += distance
                phrase_distance_count[phrase_index] += 1
                if phrase_index == -1:
                    print("phrase vocab error %s"%phrase_str)
                phrase_topic_count[:, phrase_index] += topic
                # topic_hour[topic, start_time-6] += 1
                phrase_tf_count[phrase_index] += 1
                phrase_index_set.add(phrase_index)
                phrase_hour_speed[phrase_index][doc_id] = (distance, time_span, start_time)
                # if speed < 10:
                #     phrase_hour_speed[phrase_index, start_time-6, 0] += 1
                # if speed < 20:
                #     phrase_hour_speed[phrase_index, start_time - 6, 1] += 1
                # if speed < 30:
                #     phrase_hour_speed[phrase_index, start_time - 6, 2] += 1
                # if speed < 40:
                #     phrase_hour_speed[phrase_index, start_time - 6, 3] += 1
                # if speed < 50:
                #     phrase_hour_speed[phrase_index, start_time - 6, 4] += 1
                # if speed < 60:
                #     phrase_hour_speed[phrase_index, start_time - 6, 5] += 1
                # if speed >= 60:
                #     phrase_hour_speed[phrase_index, start_time - 6, 6] += 1
                ###########
            for phrase_index in phrase_index_set:
                phrase_df_count[phrase_index] += 1

        #phrase_topic_dist = (self.beta+phrase_topic_count)/(self.beta*self.W+topic_count).reshape(-1, 1)
        phrase_topic_dist = phrase_topic_count/(phrase_topic_count.sum(axis=1)).reshape(-1, 1)
        #phrase_topic_score = phrase_topic_dist/phrase_tf_count.reshape(1, -1)
        #phrase_topic_score = (1+0.7/(self.K-1))*phrase_topic_score-(0.7/(self.K-1))*phrase_topic_score.sum(axis=0)
        topic_count = np.zeros(self.K, dtype=np.float)
        topic_hour_speed = np.zeros((self.K, 18, 7), dtype=np.float)
        topic_hour_span = np.zeros((self.K, 18, 4), dtype=np.float)
        for i in range(self.D):
            topic_list = np.array(self.assignment[i])
            unique, counts = np.unique(topic_list, return_counts=True)
            topic = np.zeros(self.K, dtype=np.float)
            for k, v in zip(unique, counts):
                topic[k] = v
            topic /= topic.sum()
            topic_count += topic
            start_time = docs_meta[i][8][0]
            end_time = docs_meta[i][8][-1]
            span_time = (end_time-start_time).seconds/3600
            distance_trip = docs_meta[i][13][-1] - docs_meta[i][13][0]
            speed = distance_trip/span_time
            #print(distance_trip)
            distance_id = int(distance_trip/10)
            if distance_id > 3:
                distance_id = 3
            speed_id = int(speed/10)
            if speed_id > 6:
                speed_id = 6
            topic_hour_speed[:, start_time.hour-6, speed_id] += topic
            topic_hour_span[:, start_time.hour-6, distance_id] += topic

        tsne = manifold.TSNE(n_components=2)
        phrase_embedding = tsne.fit_transform(phrase_topic_dist.T)
        print(phrase_embedding.shape)

        phrase_count_df = np.log(self.D/phrase_df_count)
        phrase_tf_count = phrase_tf_count/phrase_tf_count.sum()
        phrase_tfidf = phrase_tf_count*phrase_df_count
        #phrase_topic_dist *= phrase_count_df.reshape((1, -1))
        phrase_distance /= phrase_distance_count

        return phrase_vocab, phrase_topic_dist, phrase_tfidf, topic_count, topic_hour, phrase_to_docs, topic_os, topic_ds, phrase_hour_speed, phrase_distance, phrase_embedding, topic_hour_speed, topic_hour_span

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
        m_kwv = [np.zeros((self.K, self.W + 1)) for i in range(self.W + 1)]

        for i in range(len(self.corpus)):
            for j in range(len(self.corpus[i])):
                topic = self.assignment[i][j]

                word = self.mapping.get(self.corpus[i][j], 0)

                if j == 0:
                    m_kwv[self.W][topic, word] += 1
                else:
                    prev_word = self.mapping.get(self.corpus[i][j - 1], 0)
                    m_kwv[prev_word][topic, word] += 1
                q_dk[i, topic] += 1

        # print(total_words, total_connection)
        # for i in range(m_kwv.shape[0]):
        #     for j in range(m_kwv.shape[1]):
        #         for k in range(m_kwv.shape[2]):
        #             if m_kwv[i, j, k] != self.m_kwv[i, j, k]:
        #                 print("%s, %s, %s: %s. %s"%(i, j, k, m_kwv[i, j, k], self.m_kwv[i, j, k]))
        #m_kwv = [sparse.csr_matrix(a) for a in m_kwv]

        print("q_dk:%s"%np.array_equal(self.q_dk, q_dk))
        for i in range(self.K+1):
            print("m_kwv:%s"%np.array_equal(self.m_kwv[i], m_kwv[i]))

        # print("m_kw:%s"%np.array_equal(self.m_kw, self.m_kwv.sum(axis=2)))

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
