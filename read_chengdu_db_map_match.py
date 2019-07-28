import os
import sqlite3
import datetime
import numpy as np
import gzip
import pickle
from scipy import interpolate, stats
from scipy import sparse
from sklearn.decomposition import LatentDirichletAllocation
import matplotlib.pyplot as plt
from math import radians, cos, sin, asin, sqrt
import simplejson as json
from apriori import runApriori
from map_matcher import map_match
import psycopg2
from sklearn import manifold
from tngm.TNGM_new import TopicalNGramModel
import multiprocessing
import math
from tsne import tsne
#from osgeo import ogr, osr, gdal
# from coord_convert import gcj02_to_wgs84, bd09_to_wgs84
from coord_convert.utils import Transform
from multiprocessing import Pool


def create_clean_table(conn, table_name):
    cur = conn.cursor()

    sql = 'create table if not exists ' + table_name + ' (taxi_id integer, latitude float, longitude float, ' \
                                                       ' edge_gid integer, mlatitude float, mlongitude float, ' \
                                                       'status integer, year integer, month integer, day integer, ' \
                                                       'hour integer, minute integer, second integer, edge_name text,' \
                                                       'east float, north float)'

    cur.execute(sql)
    sql = "create index index_" + table_name + " on " + table_name + " (taxi_id)"
    cur.execute(sql)
    conn.commit()
    cur.close()


def clear_database(conn, table_name):
    cur = conn.cursor()
    sql = 'drop table if exists ' + table_name
    cur.execute(sql)
    conn.commit()
    cur.close()


def get_taxi_ids(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    sql = "select distinct taxi_id from " + table_name
    cur.execute(sql)
    taxi_ids = cur.fetchall()
    cur.close()
    taxi_ids = [taxi_id[0] for taxi_id in taxi_ids]
    taxi_ids.sort()
    return taxi_ids


# Haversine(lon1, lat1, lon2, lat2)的参数代表：经度1，纬度1，经度2，纬度2（十进制度数）
def Haversine(lon1, lat1, lon2, lat2):
    # 将十进制度数转化为弧度
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # Haversine公式
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # 地球平均半径，单位为公里
    d = c * r
    # print("该两点间距离={0:0.3f} km".format(d))
    return d


# def lonlat_to_xy(gcs, pcs, lon, lat):
#     ct = osr.CoordinateTransformation(gcs, pcs)
#     coordinates = ct.TransformPoint(lon ,lat)
#     return coordinates[0], coordinates[1], coordinates[2]


def read_data_from_db(db_path, table_name, taxi_ids, day):
    # input SpatialReference
    # inSpatialRef = osr.SpatialReference()
    # inSpatialRef.ImportFromEPSG(4214)
    #
    # # output SpatialReference
    # outSpatialRef = osr.SpatialReference()
    # outSpatialRef.ImportFromEPSG(4326)
    #
    # # create the CoordinateTransformation
    # coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
    transform = Transform()
    psy_conn = psycopg2.connect("host=localhost port=5432 dbname=routing5 user=postgres password=yan19910131")
    psy_cur = psy_conn.cursor()
    psy_cur.execute("select gid, name, x1, y1, x2, y2, osm_id from ways")
    rs = psy_cur.fetchall()
    none_name_count = 0
    id_to_name = {}
    for r in rs:
        id_to_name[r[0]] = r
        if r[1] is None:
            none_name_count += 1
    print(none_name_count)
    psy_cur.close()

    conn_clean = sqlite3.connect(db_path.split(".")[0] + ".map_match.db")
    clear_database(conn_clean, table_name)
    create_clean_table(conn_clean, table_name)
    conn = sqlite3.connect(db_path)
    cur_clean = conn_clean.cursor()
    cur = conn.cursor()
    sql = "select taxi_id, latitude, longitude, status, year, month, day, hour, minute, second from " + table_name + \
          " where taxi_id=%s"

    sql_clean = "insert into " + table_name + " (taxi_id, latitude, longitude, edge_gid, mlatitude, mlongitude," \
                                              " status, year, month, day, hour, minute, second, edge_name, east, north) " \
                                              "values (%d, %f, %f, %d, %f, %f, %d, %d, %d, %d, %d, %d, %d, '%s', %f, %f)"

    sql_edge = "select gid, name, x1, y1, x2, y2 from ways where gid = %s"
    error_trips_count = 0
    correct_trips_count = 0
    # c = corpus()
    taxi_docs = []
    # taxi_mats = []
    taxi_docs_times = []

    for taxi_iter, taxi_id in enumerate(taxi_ids):
        # print(sql%taxi_id)
        print("processing %s" % taxi_id)
        cur.execute(sql % (taxi_id))
        records = cur.fetchall()
        records = [[record[0], record[1], record[2], record[3],
                    datetime.datetime(2014, 8, record[6], record[7], record[8], record[9])]
                   for record in records]
        records.sort(key=lambda d: d[4])
        ts = []
        xs = []
        ys = []
        status_list = []
        false_taxi = False
        for record_id, record in enumerate(records):
            if record_id != 0:
                d_t = records[record_id][4] - records[record_id - 1][4]
                d_t = d_t.seconds
                if d_t > 600:
                    print("during time: %s" % d_t)
                    false_taxi = True
                    break
                if d_t == 0:
                    continue
                distance_cur_2 = (records[record_id][2] - records[record_id - 1][2]) ** 2 + (records[record_id][1] -
                                                                                             records[record_id - 1][
                                                                                                 1]) ** 2
                distance_cur = np.sqrt(distance_cur_2)
                distance_cur = distance_cur * 111
                speed = distance_cur / (d_t / 3600)
                if speed > 1000:
                    if len(ts) < len(records) / 5:
                        ts = []
                        xs = []
                        ys = []
                        status_list = []
                        continue
                    else:
                        print("speed: %s" % speed)
                        false_taxi = True
                        break
            t = record[4]
            t = (t.hour * 60 + t.minute) * 60 + t.second
            ts.append(t)
            xs.append(record[1])
            ys.append(record[2])
            status_list.append(record[3])

        if false_taxi:
            error_trips_count += 1
            continue
        correct_trips_count += 1
        # print(ts)
        # continue
        # print(error_trips_count, correct_trips_count)
        if len(ts) <= 3:
            print(ts)
            continue
        # fs = interpolate.interp1d(ts, status_list, kind='cubic')
        # fx = interpolate.interp1d(ts, xs, kind='cubic')
        # fy = interpolate.interp1d(ts, ys, kind='cubic')
        # t_new = np.linspace(ts[0],  ts[-1], num=18*60*5, endpoint=True)
        # t_new = t_new.astype(np.int32)
        # xs = fx(t_new)
        # ys = fy(t_new) #lon
        # status_list = fs(t_new) #lat
        # ts = t_new

        east_dirs = [ys[yi] - ys[yi - 1] for yi in range(1, len(ys))]
        north_dirs = [xs[xi] - xs[xi - 1] for xi in range(1, len(xs))]
        east_dirs.insert(0, east_dirs[1])
        north_dirs.insert(0, north_dirs[1])

        # sequence = [[y, x] for x, y in zip(xs, ys)]
        # sequence = coordTrans.TransformPoints(sequence)
        # geom = ogr.Geometry(ogr.wkbLineString)
        # for x, y in zip(xs, ys):
        #     geom.AddPoint(y, x)
        #     # print(geom.GetPointCount())
        # geom.Transform(coordTrans)
        # # candidates = []
        # # ids = []
        # # for start_index in range(0, len(sequence), 100):
        # #     candidates_tmp = map_match(psy_conn, 'ways', sequence[start_index:start_index+100], 30, 2000)
        # #     for c in candidates_tmp:
        # #         ids.append(c.measurement.id + start_index)
        # #     candidates.extend(candidates_tmp)
        # sequence = [geom.GetPoint(gi) for gi in range(0, geom.GetPointCount())]
        # sequence = [[s[0], s[1]] for s in sequence]
        sequence = [(y, x) for x, y in zip(xs, ys)]
        sequence_new = [transform.gcj2wgs(y, x) for x, y in zip(xs, ys)]
        candidates = map_match(psy_conn, 'ways', sequence_new, 30, 2000)
        candidates_map = {}
        for c_i, c in enumerate(candidates):
            # if (c_i+1) < len(candidates):
            #     if Haversine(sequence[candidates[c_i+1].measurement.id-1][0], sequence[candidates[c_i+1].measurement.id-1][1], sequence[candidates[c_i].measurement.id][0], sequence[candidates[c_i].measurement.id][1]) > 0.06:
            #         candidates_map[c.measurement.id] = c
            # else:
            candidates_map[c.measurement.id] = c

        pre_candidate = None
        # sql_insert_list = []
        for seq_id in range(len(sequence)):
            status = int(status_list[seq_id] > 0.5)
            time = ts[seq_id]
            hour = time // 3600
            minute = time // 60 % 60
            second = time % 60
            east_dir = east_dirs[seq_id]
            north_dir = north_dirs[seq_id]
            if seq_id in candidates_map.keys():
                candidate = candidates_map[seq_id]
                pre_candidate = candidate
            elif pre_candidate is not None:
                candidate = pre_candidate
            else:
                continue

            edge_id = candidate.edge.id
            mlon, mlat = sequence[seq_id]  # candidate.measurement.lon, candidate.measurement.lat
            lon, lat = candidate.lon, candidate.lat
            record = id_to_name[edge_id]
            edge_gid = edge_id * 100
            edge_name = ""
            if record[1] is not None:
                edge_name = record[1]
            osm_id = record[6]
            sql_clean_str = sql_clean % (
                taxi_id, lat, lon, osm_id, mlat, mlon, status, 2014, 8, day, hour, minute, second, edge_name, east_dir,
                north_dir)
            # print(sql_clean_str)
            cur_clean.execute(sql_clean_str)
            # sql_insert_list.append((edge_name ,edge_id))
        conn_clean.commit()
        print("process taxi: %s" % taxi_iter)
    cur_clean.close()
    cur.close()
    conn_clean.close()
    conn.close()
    psy_conn.close()


def process_lda_data(db_path, table_name, taxi_ids, day):
    #####################################################
    latitude_min = 30.4
    latitude_max = 31
    longitude_min = 103.8
    longitude_max = 104.3
    latitude_num = 100
    longitude_num = 100
    latitude_unit = (latitude_max - latitude_min) / latitude_num
    longitude_unit = (longitude_max - longitude_min) / longitude_num
    #####################################################
    taxi_vocab = {}
    taxi_vocab_inv = []
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    #
    sql = "select taxi_id, latitude, longitude, status, year, month, day, hour, minute, second, edge_gid, edge_name from " + table_name + \
          " where taxi_id=%d"
    taxi_docs = []
    taxi_docs_times = []
    for taxi_iter, taxi_id in enumerate(taxi_ids):
        # print(sql%taxi_id)
        cur.execute(sql % (taxi_id))
        records = cur.fetchall()
        records = [[record[0], record[1], record[2], record[3],
                    datetime.datetime(2014, 8, record[6], record[7], record[8], record[9]), record[10], record[11]]
                   for record in records]
        records.sort(key=lambda d: d[4])
        # print(len(records))
        #################################################################
        taxi_doc = []
        taxi_time = []
        taxi_road_names = []
        taxi_record_ids = []
        taxi_distances = []
        taxi_speed = []
        current_speed = 0
        pre_word_id = -1
        pre_location = None
        pre_time = None
        max_speed = -1
        min_speed = 1000
        distance_length = 0
        start_point = None
        start_time = None
        for record_id, record in enumerate(records):

            if record[3] == 0:
                if len(taxi_doc) > 1:
                    end_point = records[record_id - 1][6]  # [records[record_id-1][2], records[record_id-1][1]]
                    end_i = 2
                    while end_point == "":
                        if record_id - end_i < 0 or record_id - end_i >= len(records):
                            break
                        else:
                            end_point = records[record_id - end_i][6]
                            end_i += 1
                    end_time = records[record_id - 1][4]
                    avg_speed = distance_length / ((end_time - start_time).seconds / 3600 + 1e-15)
                    taxi_docs.append(taxi_doc)
                    taxi_docs_times.append([record[0], start_point, end_point, start_time, end_time, avg_speed,
                                            max_speed, min_speed, taxi_time, taxi_speed, distance_length,
                                            taxi_road_names, taxi_record_ids, taxi_distances])
                taxi_doc = []
                taxi_time = []
                taxi_speed = []

                taxi_road_names = []
                taxi_record_ids = []
                taxi_distances = []
                pre_word_id = -1
                max_speed = -1
                min_speed = 1000
                distance_length = 0
                start_point = None
                start_time = None
                pre_location = [record[2], record[1]]
                pre_time = record[4]
                continue

            latitude_index = max(min(int((record[1] - latitude_min) / latitude_unit), latitude_num), 0)
            longitude_index = max(min(int((record[2] - longitude_min) / longitude_unit), longitude_num), 0)
            word_id = (latitude_index * longitude_num + longitude_index) + 1  # word_id + 1 0 hour staus change

            word_id = record[6]+"_"+str(word_id)  # int(record[5])

            if pre_word_id != -1:
                distance_step = Haversine(record[2], record[1], records[record_id - 1][2], records[record_id - 1][1])
                time_step = ((record[4] - records[record_id - 1][4]).seconds / 3600)
                if time_step != 0:
                    speed_step = distance_step / time_step
                    if speed_step > max_speed:
                        max_speed = speed_step
                    if speed_step < min_speed:
                        min_speed = speed_step
                    distance_length += distance_step
                    current_speed = speed_step
                    # else:
                    #     print(record_id, len(records))
                    #     print(record[4], records[record_id-1][4])

            if pre_word_id != -1 and len(taxi_doc) == 1 and start_time == None:
                start_time = records[record_id - 1][4]

            if pre_word_id != -1 and len(taxi_doc) == 1 and start_point == None:
                if records[record_id - 1][6] != "":
                    start_point = records[record_id - 1][6]

            if word_id != pre_word_id and record[6] != "":
                taxi_doc.append(word_id)
                taxi_time.append(record[4])
                # if record[6] != "":
                taxi_road_names.append(record[6])
                taxi_record_ids.append(record_id)
                taxi_distances.append(distance_length)
                if pre_location is None:
                    taxi_speed.append(current_speed)
                else:
                    distance_step = Haversine(record[2], record[1], pre_location[0],
                                              pre_location[1])
                    time_step = ((record[4] - pre_time).seconds / 3600)
                    if time_step == 0:
                        taxi_speed.append(current_speed)
                    else:
                        speed_step = distance_step / time_step
                        taxi_speed.append(speed_step)
                pre_location = [record[2], record[1]]
                pre_time = record[4]
                pre_word_id = word_id
        if taxi_iter % 100 == 0:
            print("processed %s" % taxi_iter)
        if len(taxi_doc) > 1:
            end_point = [records[-1][2], records[-1][1]]
            end_time = records[-1][4]
            if start_time == None:
                print(taxi_doc)
            avg_speed = distance_length / ((end_time - start_time).seconds / 3600 + 1e-15)
            taxi_docs.append(taxi_doc)
            taxi_docs_times.append(
                [records[-1][0], start_point, end_point, start_time, end_time, avg_speed, max_speed, min_speed,
                 taxi_time, taxi_speed, distance_length, taxi_road_names, taxi_record_ids, taxi_distances])

            assert len(taxi_doc) == len(taxi_time)

    assert len(taxi_docs) == len(taxi_docs_times)
    with gzip.open(os.path.join(raw_path, os.path.basename(db_path).split(".")[0] + ".doc.pkl.gz"), 'wb') as gzip_file:
        pickle.dump((taxi_docs, taxi_docs_times), gzip_file)


def subSets(item, phrase_set_dict, phrase_vocabulary_inv):
    """Join a set with itself and returns the n-element itemsets"""
    _itemSet = set()
    iter_item_list = [item]
    while len(iter_item_list) != 0:
        item = iter_item_list.pop()
        item_str_list = item.split("_")
        item_length = len(item_str_list)
        if item_length >= 3:
            sub_phrase_1 = "_".join(item_str_list[1:])
            sub_phrase_2 = "_".join(item_str_list[:-1])
            sub_phrase_1_index = phrase_vocabulary_inv[sub_phrase_1]
            sub_phrase_2_index = phrase_vocabulary_inv[sub_phrase_2]
            if sub_phrase_1_index in phrase_set_dict[item_length - 1] and sub_phrase_1 not in _itemSet:
                _itemSet.add(sub_phrase_1)
                iter_item_list.append(sub_phrase_1)
            if sub_phrase_2_index in phrase_set_dict[item_length - 1] and sub_phrase_2 not in _itemSet:
                _itemSet.add(sub_phrase_2)
                iter_item_list.append(sub_phrase_2)
    return _itemSet


def filter_phrase_confidence(phrase_vocabulary, freqSet, num_docs, min_support, min_confidence, min_trajectory_length):
    filter_phrase_ids_dict = {}
    phrase_vocabulary_inv = {}
    for phrase_id, phrase in enumerate(phrase_vocabulary):
        phrase_vocabulary_inv[phrase] = phrase_id
        phrase_freq = freqSet[phrase] / num_docs
        if phrase_freq > min_support:
            phrase_length = len(phrase.split("_"))
            phrase_list = filter_phrase_ids_dict.get(phrase_length, set())
            phrase_list.add(phrase_id)
            filter_phrase_ids_dict[phrase_length] = phrase_list
    max_length = max(filter_phrase_ids_dict.keys())
    min_length = max(min(filter_phrase_ids_dict.keys()), min_trajectory_length)

    for phrase_length in range(max_length, min_length, -1):
        remove_phrase_set = set()
        for phrase_id in filter_phrase_ids_dict[phrase_length]:
            phrase = phrase_vocabulary[phrase_id]
            sub_phrase_sets = subSets(phrase, filter_phrase_ids_dict, phrase_vocabulary_inv)
            bool_remove_sub_phrase = True
            for sub_phrase in sub_phrase_sets:
                confidence = freqSet[phrase] / freqSet[sub_phrase]
                if confidence < min_confidence:
                    bool_remove_sub_phrase = False
                    break
            if bool_remove_sub_phrase:
                remove_phrase_set.update(sub_phrase_sets)
        for remove_phrase in remove_phrase_set:
            remove_phrase_length = len(remove_phrase.split("_"))
            remove_phrase_id = phrase_vocabulary_inv[remove_phrase]
            filter_phrase_ids_dict[remove_phrase_length].discard(remove_phrase_id)
    return filter_phrase_ids_dict


if __name__ == "__main__":
    db_name = "chengdu_%s.db"
    table_name = "taxi_gps"
    raw_path = "data/chengdu_new_new/raw_100"
    hdp_dir = "data/chengdu_new_new/lda_100"
    num_topic = 8
    day_start = 22
    day_end = 23
    if not os.path.exists(raw_path):
        os.mkdir(raw_path)
    if not os.path.exists(hdp_dir):
        os.mkdir(hdp_dir)
        # # ################################################################
        # for db_file in os.listdir("data/chengdu_new/db"):
        #     #db_file = db_name%"20140810"
        #     if "map_match" in db_file:
        #         continue
        #     db_path = os.path.join("data/chengdu_new/db", db_file)
        #     print("reading %s"%db_path)
        #     day = int(db_file[14:16])
        #     if day != 22:
        #         continue
        #     # doc_path = os.path.join(raw_path, os.path.basename(db_path).split(".")[0] + "_6.bow.pkl.gz")
        #     # if os.path.exists(doc_path):
        #     #     continue
        #     taxi_ids = get_taxi_ids(db_path, table_name)
        #     p = Pool()
        #     num_process = 7
        #     num_slice = len(taxi_ids)//num_process+1
        #     for i in range(num_process):
        #         p.apply_async(read_data_from_db, args=(db_path, table_name, taxi_ids[num_slice*i:num_slice*(i+1)], day))
        #     print('Waiting for all subprocesses done...')
        #     p.close()
        #     p.join()
        #     print('All subprocesses done.')
        #     #read_data_from_db(db_path, table_name, taxi_ids, day)
        # # #########################################################################
    # for db_file in os.listdir("data/chengdu_new/db"):
    #     # db_file = db_name%"20140810"
    #     if "map_match" in db_file:
    #         db_path = os.path.join("data/chengdu_new/db", db_file)
    #         print("reading %s" % db_path)
    #         day = int(db_file[14:16])
    #         if day != 22:
    #             continue
    #         taxi_ids = get_taxi_ids(db_path, table_name)
    #         print(taxi_ids)
    #         process_lda_data(db_path, table_name, taxi_ids, day)
        # # # ###########################################################################
    #     for day in range(day_start, day_end):
    #         db_name = "chengdu_%s" % ("201408{:02}".format(day))
    #         with gzip.open(os.path.join(raw_path, db_name + ".phrase.pkl.gz"), 'rb') as gzip_file:
    #             largeSet, freqSet, items = pickle.load(gzip_file)
    #         with gzip.open(os.path.join(raw_path, db_name + ".doc.pkl.gz"), 'rb') as gzip_file:
    #             taxi_docs, taxi_docs_times = pickle.load(gzip_file)

    #         doc_index = 0
    #         taxi_doc = taxi_docs[doc_index]
    #         conn = sqlite3.connect(os.path.join("data/chengdu_new/db", db_name + ".map_match.db"))
    #         cur = conn.cursor()
    #         sql = "select mlatitude, mlongitude, year, month, day, hour, minute, second from " + table_name + \
    #               " where taxi_id=%d"
    #         taxi_meta = taxi_docs_times[doc_index]
    #         taxi_id = taxi_meta[0]
    #         cur.execute(sql % taxi_id)
    #         trajectory_start = taxi_meta[12][0]
    #         trajectory_end = taxi_meta[12][21]
    #         taxi_records = cur.fetchall()

    #         taxi_records = [[record[0], record[1],
    #                          datetime.datetime(2014, 8, record[4], record[5], record[6], record[7])]
    #                         for record in taxi_records]
    #         taxi_records.sort(key=lambda d: d[2])
    #         print(len(taxi_records))
    #         taxi_phrase_records = taxi_records[trajectory_start:trajectory_end]
    #         trajectory_gps = [[float(tr[1]), float(tr[0])] for tr in taxi_phrase_records]
    #         # trajectory_mgps = [[float(tr[3]), float(tr[2])] for tr in taxi_phrase_records]
    #         road_names = taxi_meta[11][0:21]
    #         taxi_phrase = [trajectory_gps, 0, 0.001, 0, road_names, len(road_names), 1.0, " ".join(road_names), [104, 30]]
    #         # taxi_phrase2 = [trajectory_mgps, 0, 0.001, 0, road_names, len(road_names), 1.0, " ".join(road_names), [104, 30]]
    #         print(road_names)
    #         taxi_embedding = [0.1, 0.1, 0, 1.0, "_".join(map(str, taxi_doc)), 0]
    #         with open("test.json", 'w') as json_file:
    #             json.dump({'topic_phrase': [taxi_phrase], "embedding": [taxi_embedding]}, json_file)

    # #########################################################################
    # for day in range(day_start, day_end):
    #     db_name = "chengdu_%s" % ("201408{:02}".format(day))
    #     with gzip.open(os.path.join(raw_path, db_name + ".doc.pkl.gz"), 'rb') as gzip_file:
    #         taxi_docs, taxi_docs_times = pickle.load(gzip_file)
    #
    #         # with gzip.open(os.path.join(hdp_dir, db_name + ".model.pkl.gz"), 'rb') as gzip_file:
    #         #     model = pickle.load(gzip_file)
    #         model = TopicalNGramModel(taxi_docs, num_topic, 1, 0.01, 0.01, 0.01)
    #         for i in range(10):
    #             model.gibbs_sampler(10)
    #             with gzip.open(os.path.join(hdp_dir, db_name+".%s0.%s.model.pkl.gz"%(i+1, num_topic)), 'wb') as gzip_file:
    #                 pickle.dump(model, gzip_file)
    # ##########################################################
    # for day in range(day_start, day_end):
    #     db_name = "chengdu_%s" % ("201408{:02}".format(day))
    #     with gzip.open(os.path.join(raw_path, db_name + ".doc.pkl.gz"), 'rb') as gzip_file:
    #         taxi_docs, taxi_docs_times = pickle.load(gzip_file)
    #     taxi_docs = [[word.replace("_", "--") for word in doc] for doc in taxi_docs]
    #     road_to_road_map = {}
    #     for taxi_doc in taxi_docs:
    #         for word_iter, word in enumerate(taxi_doc):
    #             cur_word_nei = road_to_road_map.get(word, [])
    #             if word_iter != 0:
    #                 pre_word = taxi_doc[word_iter-1]
    #                 if pre_word not in cur_word_nei:
    #                     cur_word_nei.append(pre_word)
    #             if word_iter != len(taxi_doc) - 1:
    #                 next_word = taxi_doc[word_iter+1]
    #                 if next_word not in cur_word_nei:
    #                     cur_word_nei.append(next_word)
    #             road_to_road_map[word] = cur_word_nei
    #     with gzip.open(os.path.join(raw_path, db_name+".road_map.pkl.gz"), 'wb') as gzip_file:
    #         pickle.dump(road_to_road_map, gzip_file)
    # ##############################################################
    # for day in range(day_start, day_end):
    #     db_name = "chengdu_%s" % ("201408{:02}".format(day))
    #     with gzip.open(os.path.join(raw_path, db_name + ".doc.pkl.gz"), 'rb') as gzip_file:
    #         taxi_docs, taxi_docs_times = pickle.load(gzip_file)
    #     with gzip.open(os.path.join(raw_path, db_name + ".road_map.pkl.gz"), 'rb') as gzip_file:
    #         road_to_road_map = pickle.load(gzip_file)
    #      taxi_docs = [[word.replace("_", "--") for word in doc] for doc in taxi_docs]
    #     minSupport = 0.001
    #     largeSet, freqSet, items = runApriori(taxi_docs, minSupport, road_to_road_map)
    #     largeSet.pop(1, None)
    #     with gzip.open(os.path.join(raw_path, db_name + ".phrase.pkl.gz"), 'wb') as gzip_file:
    #         pickle.dump([largeSet, freqSet, items], gzip_file, protocol=4)
    #####################################################################################
    #
    # # minSupport = 0.0004
    # # for day in range(day_start, day_end):
    # #     db_name = "chengdu_%s" % ("201408{:02}".format(day))
    # #     with gzip.open(os.path.join(raw_path, db_name + ".phrase.pkl.gz"), 'rb') as gzip_file:
    # #         largeSet, freqSet, items = pickle.load(gzip_file)
    # #     with gzip.open(os.path.join(raw_path, db_name + ".doc.pkl.gz"), 'rb') as gzip_file:
    # #         taxi_docs, taxi_docs_times = pickle.load(gzip_file)
    #     phrase_vocab = []
    #     for key, value in largeSet.items():
    #         phrase_vocab.extend(value)
    #     print(len(phrase_vocab))
    # #     largeSet = filter_phrase_confidence(phrase_vocab, freqSet, len(taxi_docs), minSupport, 0.5, 2)
    # #     phrase_vocab = []
    # #     for key, value in largeSet.items():
    # #         phrase_vocab.extend(value)
    # #     print(len(phrase_vocab))
    # #     with gzip.open(os.path.join(raw_path, db_name + ".phrase.filter.pkl.gz"), 'wb') as gzip_file:
    # #         pickle.dump([largeSet, freqSet, items], gzip_file, protocol=4)
    # # # ########################################################################
    # from apriori import encode_item_list
    # for day in range(day_start, day_end):
    #     db_name = "chengdu_%s" % ("201408{:02}".format(day))
    #     with gzip.open(os.path.join(raw_path, db_name + ".phrase.pkl.gz"), 'rb') as gzip_file:
    #         largeSet, freqSet, items = pickle.load(gzip_file)
    #     # print("")
    #     # for key, value in largeSet.items():
    #     #     for phrase in value[0]:
    #     #         if "机场高速" in phrase:
    #     #             print(key, phrase)
    #     with gzip.open(os.path.join(raw_path, db_name + ".doc.pkl.gz"), 'rb') as gzip_file:
    #         taxi_docs, taxi_docs_times = pickle.load(gzip_file)
    #     with gzip.open(os.path.join(raw_path, db_name + ".road_translate.pkl.gz"), 'rb') as gzip_file:
    #         cn_to_en_map = pickle.load(gzip_file)
    #     taxi_docs = [[word.replace("_", "--") for word in doc] for doc in taxi_docs]
    #     print("load data done")
    #     phrase_set = []
    #     for key, value in largeSet.items():
    #         phrase_set.extend(value[0])
    #     phrase_set = set(phrase_set)
    #
    #     conn = sqlite3.connect(os.path.join("data/chengdu_new/db", db_name+".map_match.db"))
    #     cur = conn.cursor()
    #     sql = "select mlatitude, mlongitude, year, month, day, hour, minute, second from " + table_name + \
    #           " where taxi_id=%d"
    #     min_phrase = 2
    #     phrase_to_name = {}
    #     phrase_to_gps = {}
    #     phrase_max_length = max(largeSet.keys())
    #     for taxi_doc, taxi_meta in zip(taxi_docs, taxi_docs_times):
    #         for start_index in range(0, len(taxi_doc)):
    #             for phrase_length in range(min_phrase, min(phrase_max_length + 1, len(taxi_doc)-start_index+1)):
    #                 phrase = taxi_doc[start_index:start_index + phrase_length]
    #                 phrase_str = [str(p) for p in phrase]
    #                 phrase_str = encode_item_list(phrase_str) #"_".join(phrase_str)
    #                 # phrase_index = phrase_vocab_inverse.get(phrase_str, -1)
    #                 if phrase_str in phrase_set:
    #                     if phrase_to_gps.get(phrase_str, None) is None:
    #                         assert len(taxi_meta[12]) == len(taxi_doc)
    #                         trajectory_start = taxi_meta[12][start_index]
    #                         try:
    #                             trajectory_end = taxi_meta[12][start_index+phrase_length]
    #                         except:
    #                             phrase_to_gps[phrase_str] = None
    #                             continue
    #                         taxi_id = taxi_meta[0]
    #                         cur.execute(sql%taxi_id)
    #                         taxi_records = cur.fetchall()
    #                         taxi_records = [[record[0], record[1],
    #                                     datetime.datetime(2014, 8, record[4], record[5], record[6], record[7])]
    #                                    for record in taxi_records]
    #                         taxi_records.sort(key=lambda d: d[2])
    #                         taxi_phrase_records = taxi_records[trajectory_start:trajectory_end]
    #                         trajectory_gps = [[float(tr[1]), float(tr[0])] for tr in taxi_phrase_records]
    #                         road_names = taxi_meta[11][start_index:start_index+phrase_length]
    #                         road_names = [cn_to_en_map[r] for r in road_names]
    #                         road_names_new = []
    #                         pre_road_name = None
    #                         for road_name in road_names:
    #                             if road_name != pre_road_name:
    #                                 road_names_new.append(road_name)
    #                                 pre_road_name = road_name
    #                         road_names = road_names_new
    #                         if len(trajectory_gps) == 0:
    #                             print(phrase_str)
    #                         phrase_to_name[phrase_str] = road_names
    #                         phrase_to_gps[phrase_str] = trajectory_gps
    #     conn.close()
    #     with gzip.open(os.path.join(raw_path, db_name + ".phrase_gps.pkl.gz"), 'wb') as gzip_file:
    #         pickle.dump([phrase_to_gps, phrase_to_name], gzip_file, protocol=4)
    # # # ############################################################
    # for day in range(22, 23):
    #     db_name = "chengdu_%s" % ("201408{:02}".format(day))
    #     with gzip.open(os.path.join(raw_path, db_name + ".phrase_gps.pkl.gz"), 'rb') as gzip_file:
    #         phrase_to_gps, phrase_to_name = pickle.load(gzip_file)
    #         #print(phrase_to_gps)
    #         for (k, v) in phrase_to_gps.items():
    #             if v is None:
    #                 print(k)
    # #########################################################################
    # ############################################################################
    # for day in range(day_start, day_end):
    #     db_name = "chengdu_%s" % ("201408{:02}".format(day))
    #     with gzip.open(os.path.join(raw_path, db_name + ".phrase.pkl.gz"), 'rb') as gzip_file:
    #         largeSet, freqSet, items = pickle.load(gzip_file)
    #     # with gzip.open(os.path.join(raw_path, db_name + ".doc.pkl.gz"), 'rb') as gzip_file:
    #     #     taxi_docs, taxi_docs_times = pickle.load(gzip_file)
    #     with gzip.open(os.path.join(raw_path, db_name + ".doc.pkl.gz"), 'rb') as gzip_file:
    #         taxi_docs, taxi_docs_times = pickle.load(gzip_file)
    #
    #     phrase_vocab = []
    #     for key, value in largeSet.items():
    #         phrase_vocab.extend(value[0])
    #     phrase_set = set(phrase_vocab)
    #     vocab_inverse = {}
    #     for vocab_index, value in enumerate(phrase_vocab):
    #         vocab_inverse[value] = vocab_index
    #     print(len(phrase_vocab))
    #     phrase_to_gps = {}
    #     phrase_max_length = max(largeSet.keys())
    #
    # phrase_distance = np.zeros((len(phrase_vocab), len(phrase_vocab)), dtype=np.float32)
    # phrase_count = np.zeros(len(phrase_vocab), dtype=np.float32)
    # for taxi_doc_iter, (taxi_doc, taxi_meta) in enumerate(zip(taxi_docs, taxi_docs_times)):
    #     doc_phrase_list = []
    #     for start_index in range(0, len(taxi_doc)):
    #         for phrase_length in range(1, min(phrase_max_length + 1, len(taxi_doc)-start_index+1)):
    #             phrase = taxi_doc[start_index:start_index + phrase_length]
    #             phrase_str = [str(p) for p in phrase]
    #             phrase_str = "_".join(phrase_str)
    #             # phrase_index = phrase_vocab_inverse.get(phrase_str, -1)
    #             if phrase_str in phrase_set:
    #                 doc_phrase_list.append(phrase_str)
    #             else:
    #                 break
    #     doc_phrase_list = set(doc_phrase_list)
    #     doc_phrase_list = list(doc_phrase_list)
    #     for pi_i, pi in enumerate(doc_phrase_list):
    #         for pj_i, pj in enumerate(doc_phrase_list):
    #             phrase_distance[vocab_inverse[pi], vocab_inverse[pj]] += 1
    #         phrase_count[vocab_inverse[pi]] += 1
    #     if taxi_doc_iter % 1000 == 0:
    #         print("process %s"%taxi_doc_iter)
    # phrase_distance /= (phrase_count.reshape((-1, 1))+1e-12)
    # phrase_distance = 1-phrase_distance
    # # phrase_distance = phrase_distance.multiply(1/(phrase_count.reshape((-1, 1))+1e-12))
    # # phrase_distance = phrase_distance.tocsr()
    # # random_indexes = np.random.permutation(len(phrase_distance))
    # # phrase_distance_sample = phrase_distance[random_indexes[:0.1*len(random_indexes)], random_indexes[:0.1*len(random_indexes)]]
    # # phrase_distance_row = []
    # # for i in range(phrase_distance.shape[0]):
    # #     tmp = sparse.csr_matrix(1-phrase_distance[i, :].todense())
    # #     phrase_distance_row.append(tmp)
    # # # phrase_distance = 1-phrase_distance
    # # phrase_distance = sparse.hstack(phrase_distance_row)
    # tsne = manifold.TSNE(n_components=2, metric='precomputed')
    # #phrase_embedding = tsne(phrase_distance, 2, 50, 20.0)
    # phrase_embedding = tsne.fit_transform(phrase_distance)
    # #plt.scatter(phrase_embedding[:, 0], phrase_embedding[:, 1], 2)
    # #plt.show()
    # with gzip.open(os.path.join(raw_path, db_name + ".phrase_embedding.pkl.gz"), 'wb') as gzip_file:
    #     pickle.dump([phrase_vocab, phrase_embedding], gzip_file, protocol=4)
# # #####################################################################################
#     for day in range(day_start, day_end):
#         db_name = "chengdu_%s" % ("201408{:02}".format(day))
#         with gzip.open(os.path.join(raw_path, db_name + ".doc.pkl.gz"), 'rb') as gzip_file:
#             taxi_docs, taxi_docs_times = pickle.load(gzip_file)
#         print("load taxi docs")
#         with gzip.open(os.path.join(hdp_dir, db_name + ".100.%s.model.pkl.gz"%num_topic), 'rb') as gzip_file:
#             model = pickle.load(gzip_file)
#             print(model)
#         with gzip.open(os.path.join(raw_path, db_name + ".phrase.pkl.gz"), 'rb') as gzip_file:
#             largeSet, freqSet, items = pickle.load(gzip_file)
#
#         print("data loading done")
#         # hour_count = np.zeros(18, np.int64)
#         # time_span_count = np.zeros(13, dtype=np.int32)
#         hour_time_span_count = np.zeros((18, 13), dtype=np.int32)
#         for taxi_id, taxi_doc in enumerate(taxi_docs):
#             hour = taxi_docs_times[taxi_id][8][0].hour-6
#             #hour_count[hour] += 1
#             time_span = taxi_docs_times[taxi_id][8][-1]-taxi_docs_times[taxi_id][8][0]
#             time_span = time_span.seconds
#             time_span_minute = time_span // 60 // 10
#             if time_span_minute > 12:
#                 time_span_minute = 12
#             #time_span_count[time_span_minute] += 1
#             hour_time_span_count[hour, time_span_minute] += 1
#         #     word_vocabulary, word_dist = model.get_words()
#         # with gzip.open(os.path.join(hdp_dir, db_name + ".topic_word.pkl.gz"), 'wb') as gzip_file:
#         #     pickle.dump([word_vocabulary, word_dist], gzip_file)
#         #     #model.print_topics()
#         phrase_vocabulary, topic_phrase_dist, phrase_tfidf, topic_dist, topic_hour, phrase_to_docs, topic_os, topic_ds, \
#         phrase_hour_speed, phrase_distance, phrase_embedding, topic_hour_speed, topic_hour_span = model.get_phrase(items, taxi_docs_times)
#         print("saving")
#         with gzip.open(os.path.join(hdp_dir, db_name + ".%s.topic_phrase.pkl.gz"%num_topic), 'wb') as gzip_file:
#             pickle.dump([phrase_vocabulary, topic_phrase_dist, phrase_tfidf, topic_dist, hour_time_span_count,
#                          topic_hour, phrase_to_docs, topic_os, topic_ds, phrase_hour_speed, model.D, phrase_distance,
#                          phrase_embedding, topic_hour_speed, topic_hour_span], gzip_file)
# # # # ##################################################################################################
#     for day in range(day_start, day_end):
#         db_name = "chengdu_%s" % ("201408{:02}".format(day))
#         with gzip.open(os.path.join(raw_path, db_name + ".doc.pkl.gz"), 'rb') as gzip_file:
#             taxi_docs, taxi_docs_times = pickle.load(gzip_file)

#
#         with gzip.open(os.path.join(raw_path, db_name + ".road_translate.pkl.gz"), 'rb') as gzip_file:
#             cn_to_en_map = pickle.load(gzip_file)
#
#
#         conn = sqlite3.connect(os.path.join(raw_path, db_name+".db"))
#         #table_name_new = "taxi_trip"
#         clear_database(conn, table_name)
#         cur = conn.cursor()
#         ##########################################################
#         sql = 'create table if not exists ' + table_name + ' (trip_id integer, meta_data text)'
#         cur.execute(sql)
#         sql = "create index index_" + table_name + " on " + table_name + " (trip_id)"
#         cur.execute(sql)
#         conn.commit()
#         ##########################################################
#         sql = "insert into " + table_name + " (trip_id, meta_data) " \
#                                             "values (?, ?)"
#
#         taxi_conn = sqlite3.connect(os.path.join("data/chengdu_new/db", db_name + ".map_match.db"))
#         taxi_cur = taxi_conn.cursor()
#         taxi_sql = "select mlatitude, mlongitude, year, month, day, hour, minute, second from " + table_name + \
#               " where taxi_id=%d"
#
#         for doc_id, doc in enumerate(taxi_docs):
#             random_number = np.random.rand(1)[0]
#             if random_number > 0.1:
#                 continue
#             taxi_meta = taxi_docs_times[doc_id]
#             trajectory_start = taxi_meta[12][0]
#             trajectory_end = taxi_meta[12][-1]
#             taxi_id = taxi_meta[0]
#             taxi_cur.execute(taxi_sql%taxi_id)
#             taxi_records = taxi_cur.fetchall()
#
#             taxi_records = [[record[0], record[1],
#                      datetime.datetime(2014, 8, record[4], record[5], record[6], record[7])]
#                     for record in taxi_records]
#             taxi_records.sort(key=lambda d: d[2])
#
#             trajectory_gps = taxi_records[trajectory_start:trajectory_end+1]
#             trajectory_gps = [[float(tr[1]), float(tr[0])] for tr in trajectory_gps]
#
#             taxi_docs_times[doc_id].append(trajectory_gps)
#             taxi_docs_times[doc_id][3] = [taxi_docs_times[doc_id][3].year, taxi_docs_times[doc_id][3].month, taxi_docs_times[doc_id][3].day, taxi_docs_times[doc_id][3].hour, taxi_docs_times[doc_id][3].minute, taxi_docs_times[doc_id][3].second]
#             taxi_docs_times[doc_id][4] = [taxi_docs_times[doc_id][4].year, taxi_docs_times[doc_id][4].month, taxi_docs_times[doc_id][4].day, taxi_docs_times[doc_id][4].hour, taxi_docs_times[doc_id][4].minute, taxi_docs_times[doc_id][4].second]
#
#             # taxi_docs_times[doc_id][1] = cn_to_en_map[taxi_docs_times[doc_id][1]]
#             # taxi_docs_times[doc_id][2] = cn_to_en_map[taxi_docs_times[doc_id][2]]
#             taxi_docs_times[doc_id][11] = [cn_to_en_map[road_name] for road_name in  taxi_docs_times[doc_id][11]]
#             taxi_docs_times[doc_id][1] = taxi_docs_times[doc_id][11][0]
#             taxi_docs_times[doc_id][2] = taxi_docs_times[doc_id][11][-1]
#             pre_road_name = None
#             new_road_names = []
#             for road_name in taxi_docs_times[doc_id][2]:
#                 if road_name != pre_road_name:
#                     new_road_names.append(road_name)
#                     pre_road_name = road_name
#             taxi_docs_times[doc_id][11] = new_road_names
#             for time_id, time_value in enumerate(taxi_docs_times[doc_id][8]):
#                 taxi_docs_times[doc_id][8][time_id] = [time_value.year, time_value.month, time_value.day, time_value.hour, time_value.minute, time_value.second]
#             cur.execute(sql, (doc_id, json.dumps(taxi_docs_times[doc_id])))
#             if doc_id % 1000 == 0:
#                 print("process %s records" % doc_id)
#                 conn.commit()
#         conn.commit()
#         cur.close()
#         conn.close()
#         taxi_cur.close()
#         taxi_conn.close()
########################################################################################################
# from translate import Translator
# translator = Translator(to_lang='en', from_lang='ZH-CN')
# for day in range(day_start, day_end):
#     db_name = "chengdu_%s" % ("201408{:02}".format(day))
#     with gzip.open(os.path.join(raw_path, db_name + ".doc.pkl.gz"), 'rb') as gzip_file:
#         taxi_docs, taxi_docs_times = pickle.load(gzip_file)
#
#     cn_to_en_map = {}
#     for taxi_iter, taxi_doc in enumerate(taxi_docs):
#         for word_iter, word in enumerate(taxi_doc):
#             road_name = taxi_docs_times[taxi_iter][11][word_iter]
#             road_tr_name = cn_to_en_map.get(road_name, None)
#             if road_tr_name is None:
#                 try:
#                     road_tr_name = translator.translate(road_name)
#                     print(road_name, road_tr_name)
#                     cn_to_en_map[road_name] = road_tr_name
#                 except:
#                     print(road_name, road_tr_name)
#                 # cur_word_nei = road_to_road_map.get(word, [])
#                 # if word_iter != 0:
#                 #     pre_word = taxi_doc[word_iter-1]
#                 #     if pre_word not in cur_word_nei:
#                 #         cur_word_nei.append(pre_word)
#                 # if word_iter != len(taxi_doc) - 1:
#                 #     next_word = taxi_doc[word_iter+1]
#                 #     if next_word not in cur_word_nei:
#                 #         cur_word_nei.append(next_word)
#                 # road_to_road_map[word] = cur_word_nei
#     with gzip.open(os.path.join(raw_path, db_name + ".road_translate.pkl.gz"), 'wb') as gzip_file:
#         pickle.dump(cn_to_en_map, gzip_file)
#     for day in range(day_start, day_end):
#         db_name = "chengdu_%s" % ("201408{:02}".format(day))
#         with gzip.open(os.path.join(raw_path, db_name + ".road_translate.pkl.gz"), 'rb') as gzip_file:
#             cn_to_en_map = pickle.load(gzip_file)
#             en_to_cn_map = {}
#             match_str = 'San Huan Lu' #'Second Ring Elevated Road' #"Second Ring Road"
#             replace_str = '3rd Ring Rd'#'2nd Ring Elevated Rd'
#             for (k, v) in cn_to_en_map.items():
#                 start_index = v.find(match_str)
#                 if start_index != -1:
#                     new_v = v[:start_index]+replace_str+v[start_index+len(match_str):]
#                     cn_to_en_map[k] = new_v
#                     #v[start_index:start_index+len(match_str)] = replace_str
#                 # en_to_cn_map[v] = k
#
#             # cn_to_en_map[en_to_cn_map['Second Ring Elevated Road']] = '2nd Ring Elevated Rd'
#             # cn_to_en_map[en_to_cn_map['Second Ring Road']] = '2nd Ring Elevated Rd'
#         # '2nd Ring Elevated Rd'
#         with gzip.open(os.path.join(raw_path, db_name + ".road_translate.pkl.gz"), 'wb') as gzip_file:
#             pickle.dump(cn_to_en_map, gzip_file)
