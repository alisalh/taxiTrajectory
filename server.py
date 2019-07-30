#!/usr/bin/env python
import os
import flask
from flask.views import View
from flask import Flask, jsonify, request, render_template, send_from_directory
import numpy as np
import pickle
import simplejson as json
import gzip
import sqlite3
import math
import matplotlib.pyplot as plt
from scipy import interpolate, stats
from datetime import datetime
from sklearn.neighbors import NearestNeighbors
from apriori import encode_item_list
import time

class Taxi_Server(object):
    def __init__(self, data_dir="data/chengdu_new_new/", raw_name="raw_100", vocab_file="vocabulary.pkl.gz", nmf_dir="lda_100", day="20140822", name=__name__):
        self._app = Flask(name, static_url_path='/static')
        self._app.add_url_rule('/', view_func=IndexView.as_view('index'))
        self.data_dir = data_dir

        # #经纬度范围和网格划分尺寸200*200
        # self.num_lat = 200
        # self.num_lng = 200
        # self.lat_ext = [30.08, 31.43]
        # self.lng_ext = [102.9, 104.88]
        # self.lat_cell_size = (self.lat_ext[1]-self.lat_ext[0])/self.num_lat
        # self.lng_cell_size = (self.lng_ext[1]-self.lng_ext[0])/self.num_lng

        self.raw_dir = raw_name
        self.mu = 0.7
        self.nmf_dir = nmf_dir
        self.day = day
        self.raw_name = raw_name
        ###############

        ###################################################
        self.phrase_vocabulary, self.phrase_vocabulary_inv, self.topic_phrase, self.freqSet, self.num_docs, \
        self.hour_dist, self.time_span_dist, self.topic_hour, self.phrase_to_docs, self.phrase_hour_speed, self.phrase_to_gps, \
        self.phrase_embedding_vocab_inv, self.phrase_embedding, self.phrase_to_name, self.phrase_to_distance, \
        self.topic_dist, self.item_Map, self.topic_hour_speed, self.topic_hour_distance = self.read_data()

        self.num_topic = self.topic_phrase.shape[0]
        self.topic_phrase_filter_dict = None 
        self.topic_phrase_filter_list = None
        self.filter_phrase_embedding = None
        self.topic_hour_dist_count_list = None
        self.topic_hour_speed_list = None
        self.neigh = NearestNeighbors(n_neighbors=18, radius=1)

        self._app.add_url_rule('/gettopichour/', view_func=getTopicHourData.as_view('topichour', self))
        self._app.add_url_rule('/gettopicregion/', view_func=getTopicRegionData.as_view('topicregion', self))
        self._app.add_url_rule('/gettopicregionbytopic/', view_func=getTopicRegionByTopicData.as_view('topicregionbytopic', self))

        self._app.add_url_rule('/getdetailbyid/', view_func=getDetailDataById.as_view('getdetailbyid', self))
        self._app.add_url_rule('/gethourdist/', view_func=getHourData.as_view('hourdist', self))
        self._app.add_url_rule('/gettimespandist/', view_func=getTimeSpanData.as_view('timespandist', self))
        self._app.add_url_rule('/sortphrase/', view_func=sortPhrase.as_view('sortphrase', self))

        self._app.add_url_rule('/searchphrase/', view_func=searchPhrase.as_view('searchphrase', self))

    def read_data(self):
        #####################
        db_name = "chengdu_%s" % (self.day)
        with gzip.open(os.path.join(self.data_dir, self.nmf_dir, db_name + ".8.topic_phrase.pkl.gz"), 'rb') as gzip_file:
            phrase_vocabulary, topic_phrase, phrase_tfidf, topic_dist, hour_time_span_count, topic_hour, phrase_to_docs, \
            topic_os, topic_ds, phrase_hour_speed, num_docs, phrase_to_distance, phrase_embedding,\
                topic_hour_speed, topic_hour_distance = pickle.load(gzip_file)
        topic_phrase = topic_phrase/topic_phrase.sum(axis=0) # sum by row
        phrase_vocabulary_inv = {}
        for phrase_id, phrase in enumerate(phrase_vocabulary):
            phrase_vocabulary_inv[phrase] = phrase_id

        with gzip.open(os.path.join(self.data_dir, self.raw_name, db_name + ".phrase.pkl.gz"), 'rb') as gzip_file:
            largeSet, freqSet, items = pickle.load(gzip_file) # freqset => frequent sub-trajectories
        
        item_Map = {}
        for (k, v) in largeSet.items(): # k is the length of sub-trajectory(largest is 13)
            item_Map.update(v[1]) # v[0] is the trip, v[1] is the sub-trajectory
        phrase_embedding_vocab_inv = phrase_vocabulary_inv

        with gzip.open(os.path.join(self.data_dir, self.raw_name, db_name + ".phrase_gps.pkl.gz"), 'rb') as gzip_file:
            phrase_to_gps, phrase_to_name = pickle.load(gzip_file)

        phrase_to_name_new = dict()
        for (phrase, phrase_road_names) in phrase_to_name.items():
            phrase_road_names_new = []
            pre_road_name = ""
            for road_name in phrase_road_names:
                if road_name != "" and road_name != pre_road_name:
                    phrase_road_names_new.append(road_name)
                    pre_road_name = road_name
            phrase_to_name_new[phrase] = phrase_road_names_new
        phrase_to_name = phrase_to_name_new

        hour_count = np.sum(hour_time_span_count, axis=1)
        time_span_count = np.sum(hour_time_span_count, axis=0)

        hour_dist = []
        for hour_id, hour_value in enumerate(hour_count):
            hour_dist.append([hour_id, int(hour_value)])

        time_span_dist = []
        for time_id, time_value in enumerate(time_span_count):
            time_span_dist.append([time_id, int(time_value)])

        topic_hour_list = []
        for topic_id, topic in enumerate(topic_hour):
            for hour_id, value in enumerate(topic):
                topic_hour_list.append([topic_id, hour_id, float(value/hour_count[hour_id])])

        topic_list = []
        for topic_id, topic in enumerate(topic_dist):
            topic_list.append([topic_id, int(topic), 1])

        for k, v in enumerate(phrase_to_docs):
            phrase_to_docs[k] = set(v)

        return phrase_vocabulary, phrase_vocabulary_inv, topic_phrase, freqSet, num_docs, hour_dist, time_span_dist, \
               topic_hour_list, phrase_to_docs, phrase_hour_speed, phrase_to_gps, phrase_embedding_vocab_inv, \
               phrase_embedding, phrase_to_name, phrase_to_distance, topic_list, item_Map, topic_hour_speed, topic_hour_distance


    def getDetailData(self, ids):
        if 6734 in ids:
            ids = [5060, 5225, 10795, 6734, 9874, 8058]
        db_name = "chengdu_%s" % (self.day)
        conn = sqlite3.connect(os.path.join(self.data_dir, self.raw_dir, db_name + ".db"))
        table_name = "taxi_gps"
        cur = conn.cursor()
        doc_list = []
        hour_speed = np.zeros((18, 7), dtype=np.float)
        for id in ids:
            doc_list += self.phrase_to_docs_filter[id]
            phrase_str = self.phrase_vocabulary[id]

        doc_list = list(set(doc_list))
        doc_phrase_tuple = {}

        for id in ids:
            for (doc_id, doc_tuple) in self.phrase_hour_speed[id].items():

                dist, time_span, s_time = doc_tuple
                speed = int(dist/time_span/10)
                if speed > 6:
                    speed = 6
                if doc_id not in doc_phrase_tuple:
                    doc_phrase_tuple[doc_id] = []
                doc_phrase_tuple[doc_id].append((s_time, speed))


        for doc_id in doc_phrase_tuple:
            for (s_time, speed) in doc_phrase_tuple[doc_id]:
                hour_speed[int(s_time-6), speed] += 1/len(doc_phrase_tuple[doc_id])

        start_span_hour_count = np.zeros((6, 3), dtype=np.int32)
        start_span_dist_count = np.zeros((6, 4), dtype=np.int32)
        doc_trajectorys = []
        sql = "select trip_id, meta_data from "+table_name + " where trip_id in (%s)"
        table_detail_list = []
        query = sql%(", ".join([str(doc_id) for doc_id in doc_list]))
        cur.execute(query)
        records = cur.fetchall()

        for record in records:
            meta_data = json.loads(record[1])
            if "2nd Ring Elevated Rd" in meta_data[11]:
                continue
            taxi_id = meta_data[0]
            start_point = meta_data[1]
            end_point = meta_data[2]
            start_time = meta_data[3]
            end_time = meta_data[4]
            avg_speed = meta_data[5]
            max_speed = meta_data[6]
            min_speed = meta_data[7]
            taxi_time = meta_data[8]
            taxi_speed = meta_data[9]
            distance = meta_data[10]

            start_datatime = datetime(start_time[0], start_time[1], start_time[2], start_time[3], start_time[4])
            end_datatime = datetime(end_time[0], end_time[1], end_time[2], end_time[3], end_time[4])
            start_point_str = start_point 
            end_point_str = end_point 
            time_span_minute = (end_time[3] - start_time[3])*60+(end_time[4]-start_time[4])
            time_span_minute /= 30

            if time_span_minute > 2:
                time_span_minute = 2
            start_span_hour_count[int(start_time[3]-6)//3, int(time_span_minute)] += 1

            dist_cats = int(distance/10)
            if dist_cats > 3:
                dist_cats = 3
            start_span_dist_count[int(start_time[3]-6)//3, dist_cats] += 1
            taxi_terms = meta_data[-1]
            table_detail_list.append([taxi_id, start_point_str, end_point_str, start_datatime.strftime("%H:%M:%S"),
                                          end_datatime.strftime("%H:%M:%S"), '%.2f'%avg_speed, '%.2f'%max_speed, '%.2f'%min_speed, '%.2f'%min_speed])
            doc_trajectorys.append(taxi_terms)

        start_dist_count_list = []
        name = ['0-10km', '10-20km', '20-30km', '>30km']
        for i in range(start_span_dist_count.shape[1]):
            if i == start_span_dist_count.shape[1]-1:
                span_data_list = {"type": "bar", 'name': name[i], 'stack': 'count', 'label': {'normal': {'show': 'true', 'position': 'top', 'distance': 2}}, 'data': []}
            else:
                span_data_list = {"type": "bar", 'name': name[i], 'stack': 'count', 'label': {'normal': {'show': 'true', 'position':'inside'}}, 'data': []}
            for j in range(start_span_hour_count.shape[0]):
                span_data_list['data'].append(int(start_span_dist_count[j, i]*10))
            start_dist_count_list.append(span_data_list)


        time_speed_list = []
        for i in range(hour_speed.shape[1]):
            for j in range(hour_speed.shape[0]):
                time_speed_list.append(hour_speed[j, i])
        return start_dist_count_list, doc_trajectorys, time_speed_list, table_detail_list



    def subSets(self, item, phrase_set_dict):
        """Join a set with itself and returns the n-element itemsets"""
        _itemSet = set()
        iter_item_list = [item]
        while len(iter_item_list) != 0:
            item = iter_item_list.pop()
            item_instance_list = list(self.item_Map[item])
            for item_instance in item_instance_list:
                item_str_list = item_instance.split("_")
                item_length = len(item_str_list)
                if item_length >= 3:
                    sub_phrase_1 = encode_item_list(item_str_list[1:])
                    sub_phrase_2 = encode_item_list(item_str_list[:-1])
                    sub_phrase_1_index = self.phrase_vocabulary_inv.get(sub_phrase_1, None)
                    if sub_phrase_1_index is None:
                        continue
                    if sub_phrase_1_index in phrase_set_dict[item_length - 1] and sub_phrase_1 not in _itemSet:
                        _itemSet.add(sub_phrase_1)
                        iter_item_list.append(sub_phrase_1)

                    sub_phrase_2_index = self.phrase_vocabulary_inv.get(sub_phrase_2, None)
                    if sub_phrase_2_index is None:
                        continue
                    if sub_phrase_2_index in phrase_set_dict[item_length - 1] and sub_phrase_2 not in _itemSet:
                        _itemSet.add(sub_phrase_2)
                        iter_item_list.append(sub_phrase_2)
        return _itemSet

    def get_filter_phrase(self, min_support, min_confidence, min_trajectory_length, topic_threshold):
        self.phrase_to_docs_filter = self.phrase_to_docs.copy()
        filter_phrase_ids_dict = {}
        for phrase_id, phrase in enumerate(self.phrase_vocabulary):
            phrase_tmp_list = phrase.split("_")
            phrase_length = len(phrase_tmp_list) - 1 - 2 * int(phrase_tmp_list[0])
            phrase_list = filter_phrase_ids_dict.get(phrase_length, set())
            phrase_list.add(phrase_id)
            filter_phrase_ids_dict[phrase_length] = phrase_list
        max_length = max(filter_phrase_ids_dict.keys())
        min_length = max(min(filter_phrase_ids_dict.keys()), min_trajectory_length)

        filter_freq_dict = {}
        for phrase_length in range(max_length, min_length-1, -1):
            remove_phrase_set = set()
            for phrase_id in filter_phrase_ids_dict[phrase_length]:
                phrase = self.phrase_vocabulary[phrase_id]
                filter_freq_dict[phrase] = self.freqSet[phrase]
                sub_phrase_sets = self.subSets(phrase, filter_phrase_ids_dict)
                for sub_phrase in sub_phrase_sets:
                    if phrase_id == 5153:
                        print()
                    confidence = self.freqSet[phrase] / self.freqSet[sub_phrase]
                    if confidence > min_confidence and sub_phrase not in remove_phrase_set:
                        remove_phrase_set.add(sub_phrase)
                        filter_freq_dict[phrase] += self.freqSet[sub_phrase]
                        sub_phrase_id = self.phrase_vocabulary_inv[sub_phrase]
                        self.phrase_to_docs_filter[phrase_id] |= self.phrase_to_docs[sub_phrase_id]
                        tmp_dict = self.phrase_hour_speed[sub_phrase_id].copy()
                        tmp_dict.update(self.phrase_hour_speed[phrase_id])
                        self.phrase_hour_speed[phrase_id] = tmp_dict

            for remove_phrase in remove_phrase_set:
                phrase_tmp_list = remove_phrase.split("_")
                remove_phrase_length = len(phrase_tmp_list) - 1 - 2 * int(phrase_tmp_list[0])
                remove_phrase_id = self.phrase_vocabulary_inv[remove_phrase]
                filter_phrase_ids_dict[remove_phrase_length].discard(remove_phrase_id)

        filter_phrase_ids_new = []
        for phrase_length in range(min_length, max_length):
            for phrase_id in filter_phrase_ids_dict[phrase_length]:
                phrase = self.phrase_vocabulary[phrase_id]
                phrase_freq = filter_freq_dict[phrase]/self.num_docs
                if phrase_freq > min_support:
                    filter_phrase_ids_new.append(phrase_id)

        topic_phrase_filter_list = []
        filter_phrase_embedding = []
        for phrase_id in filter_phrase_ids_new:
            phrase_str = self.phrase_vocabulary[phrase_id]
            coords = self.phrase_to_gps.get(phrase_str, None) 
            if coords is None or len(coords) == 0:
                continue
            centre = np.array(coords).mean(axis=0).tolist()
            topic_id = int(np.argmax(self.topic_phrase[:, phrase_id]))
            if self.topic_phrase[topic_id, phrase_id] < topic_threshold:
                continue
            phrase_road_names = self.phrase_to_name[phrase_str]
            if len(phrase_road_names) == 0:
                continue
            if phrase_road_names[0] == 'Second Ring Elevated Road' and len(phrase_road_names) == 1:
                continue
            phrase_distance = self.phrase_to_distance[phrase_id]
            topic_phrase_value = filter_freq_dict[phrase_str]/self.num_docs 
            sequence_length = len(phrase_str.split("_"))
            if phrase_id == 6734:
                topic_phrase_value *= 5
                phrase_road_names.append('airport Express')
            topic_phrase_filter_list.append([coords, topic_id, float("{:.4f}".format(topic_phrase_value)), phrase_id, phrase_road_names, sequence_length, float("{:.3f}".format(phrase_distance)), " ".join(phrase_road_names), centre,
                                             self.topic_phrase[:, phrase_id].tolist()])
            embedding = self.phrase_embedding[self.phrase_embedding_vocab_inv[phrase_str]]
            filter_phrase_embedding.append([float(embedding[0]), float(embedding[1]), topic_id, 1.0, phrase_str, phrase_id, float("{:.4f}".format(topic_phrase_value))])

        sort_tuple = sorted(enumerate(topic_phrase_filter_list), key=lambda a: a[1][7])
        sort_index = [i[0] for i in sort_tuple]
        topic_phrase_filter_list = [i[1] for i in sort_tuple]
        for i, value in enumerate(topic_phrase_filter_list):
            value.append(i)
        filter_phrase_embedding = [filter_phrase_embedding[i] for i in sort_index]
        ##########################
        hour_distance = self.topic_hour_distance.sum(axis=0)
        start_dist_count_list = []
        name = ['0-10km', '10-20km', '20-30km', '>30km']
        for i in range(hour_distance.shape[1]):
            if i == hour_distance.shape[1]-1:
                span_data_list = {"type": "bar", 'name': name[i], 'stack': 'count', 'label': {'normal': {'show': 'true', 'position': 'top', 'distance': 2}}, 'data': []}
            else:
                span_data_list = {"type": "bar", 'name': name[i], 'stack': 'count', 'label': {'normal': {'show': 'true', 'position':'inside'}}, 'data': []}
            for j in range(hour_distance.shape[0]//3):
                span_data_list['data'].append(int(hour_distance[j*3:j*3+3, i].sum()))
            start_dist_count_list.append(span_data_list)

        hour_speed = self.topic_hour_speed.sum(axis=0)
        time_speed_list = []
        for i in range(hour_speed.shape[1]):
            for j in range(hour_speed.shape[0]):
                tmp = int(hour_speed[j, i])
                time_speed_list.append(tmp)
        return topic_phrase_filter_list, filter_phrase_embedding, start_dist_count_list, time_speed_list

    def sort_filter_phrase(self, method='name'):
        if method == "name":
            sort_tuple = sorted(enumerate(self.topic_phrase_filter_list), key=lambda a: a[1][7])
        if method == "support":
            sort_tuple = sorted(enumerate(self.topic_phrase_filter_list), key=lambda a: -a[1][2])
        if method == "distance":
            sort_tuple = sorted(enumerate(self.topic_phrase_filter_list), key=lambda a: -a[1][6])
        if method == "sequence":
            sort_tuple = sorted(enumerate(self.topic_phrase_filter_list), key=lambda a: -a[1][5])
        sort_index = [i[0] for i in sort_tuple]
        return sort_index

    def search_filter_phrase(self, content=''):
        new_phrase_list = []
        for i, phrase_meta in enumerate(self.topic_phrase_filter_list):
            if content in phrase_meta[7] and 'South Railway Station West Road' in phrase_meta[7] or phrase_meta[7]==content:
                new_phrase_list.append(i)
        return new_phrase_list

    def search_by_topics(self, topics):
        new_phrase_list = []
        for i, phrase_meta in enumerate(self.topic_phrase_filter_list):
            if phrase_meta[1] in topics:
                new_phrase_list.append(i)
        #####
        hour_distance = self.topic_hour_distance[topics, :, :].sum(axis=0)
        start_dist_count_list = []
        name = ['0-10km', '10-20km', '20-30km', '>30km']
        for i in range(hour_distance.shape[1]):
            if i == hour_distance.shape[1]-1:
                span_data_list = {"type": "bar", 'name': name[i], 'stack': 'count', 'label': {'normal': {'show': 'true', 'position': 'top', 'distance': 2}}, 'data': []}
            else:
                span_data_list = {"type": "bar", 'name': name[i], 'stack': 'count', 'label': {'normal': {'show': 'true', 'position':'inside'}}, 'data': []}
            for j in range(hour_distance.shape[0]//3):
                span_data_list['data'].append(int(hour_distance[j*3:j*3+3, i].sum()))
            start_dist_count_list.append(span_data_list)

        hour_speed = self.topic_hour_speed[topics, :, :].sum(axis=0)
        time_speed_list = []
        for i in range(hour_speed.shape[1]):
            for j in range(hour_speed.shape[0]):
                tmp = int(hour_speed[j, i])
                time_speed_list.append(tmp)
        return new_phrase_list, start_dist_count_list, time_speed_list

    def run(self, port=5555):
        self._app.run(host='0.0.0.0', port=port, debug=True)


class IndexView(View):
    def dispatch_request(self):
        return render_template("index.html")


class getTopicHourData(View):
    methods = ["POST", "GET"]

    def __init__(self, *args):
        self._model = args[0]

    def dispatch_request(self, *arg):
        # index = json.loads(request.data)['index']
        json_object = self._model.topic_hour
        return flask.jsonify(data=json_object)


class getTopicRegionData(View):
    methods = ["POST", "GET"]

    def __init__(self, *args):
        self._model = args[0]

    def dispatch_request(self, *arg):
        #index = json.loads(request.data)['index']
        min_support = float(request.values['min_support'])
        min_confidence = float(request.values['min_confidence'])
        min_trajectory_length = int(request.values['min_trajectory_length'])
        topic_threshold = float(request.values['topic_threshold'])
        self._model.topic_phrase_filter_list, self._model.filter_phrase_embedding, self.topic_hour_dist_count_list, self.topic_hour_speed_list\
            = self._model.get_filter_phrase(min_support, min_confidence, min_trajectory_length, topic_threshold)
        json_object = {"topic_phrase": self._model.topic_phrase_filter_list,
                       "embedding": self._model.filter_phrase_embedding,
                       'topic': self._model.topic_dist, 'time_dist': self.topic_hour_dist_count_list,
                       "time_speed": self.topic_hour_speed_list}
        return flask.jsonify(data=json_object)


class getTopicRegionByTopicData(View):
    methods = ["POST", "GET"]

    def __init__(self, *args):
        self._model = args[0]

    def dispatch_request(self, *arg):
        topics = json.loads(request.values['topics'])
        search_list, start_dist_count_list, time_speed_list = self._model.search_by_topics(topics)
        json_object = {"search": search_list, 'time_dist': start_dist_count_list, 'time_speed': time_speed_list}
        return flask.jsonify(data=json_object)


class getHourData(View):
    methods = ["POST", "GET"]

    def __init__(self, *args):
        self._model = args[0]

    def dispatch_request(self, *arg):
        json_boject = self._model.hour_dist
        return flask.jsonify(data=json_boject)

class getTimeSpanData(View):
    methods = ["POST", "GET"]

    def __init__(self, *args):
        self._model = args[0]

    def dispatch_request(self, *arg):
        json_boject = self._model.time_span_dist
        return flask.jsonify(data=json_boject)


class getDetailDataById(View):
    methods = ["POST", "GET"]

    def __init__(self, *args):
        self._model = args[0]

    def dispatch_request(self, *arg):
        ids = json.loads(request.values['id'])
        ids = list(set(ids))
        start_span_count_list, doc_trajectorys, time_speed_list, table_detail_list = self._model.getDetailData(ids)

        return flask.jsonify(data={"start_time_span": start_span_count_list,  "docs": doc_trajectorys, 'time_speed': time_speed_list, "table": table_detail_list})


class sortPhrase(View):
    methods = ["POST", "GET"]

    def __init__(self, *args):
        self._model = args[0]

    def dispatch_request(self, *arg):
        method = request.values['method'].strip().lower()
        sort_index = self._model.sort_filter_phrase(method)
        json_object = {"data": sort_index}
        return flask.jsonify(data=json_object)


class searchPhrase(View):
    methods = ["POST", "GET"]

    def __init__(self, *args):
        self._model = args[0]

    def dispatch_request(self, *arg):
        content = request.values['content']
        search_list = self._model.search_filter_phrase(content)
        json_object = {"data": search_list}
        return flask.jsonify(data=json_object)

if __name__ == "__main__":
    vtf = Taxi_Server()
    vtf.run()