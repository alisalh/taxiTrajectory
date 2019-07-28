import psycopg2
import geocoder
from shapely.geometry import LineString
from shapely import wkb

#
# conn = psycopg2.connect("host=localhost port=5432 dbname=routing user=postgres password=yan19910131")
# cur = conn.cursor()
# sql = "select gid, name, x1, y1 from ways"
# update_sql = "update ways set name = '%s' where gid = %d"
# cur.execute(sql)
# records = cur.fetchall()
# keys = []
# keys.append("ZR26Xbeo5g9xBMtoGUw7czbeO7DWE6hi")
# keys.append("3RqnWEkKD7z670OBqT1xlU1VGGLzG5OW")
# keys.append("BUDoeiO34pt4zyfYTln3kd4Hu7VGTbaI")
# keys.append("0TovjUUufyGN7KMlFu8PgsnBGlh9wGPH")
# keys.append("2tYnr3gDMTID7y1Z2b74ZHoXACGBVDsR")
# keys.append("ftnqf1pGRWrtrZ7zkyCjQfS4AHcMFKX8")
# key_iter = 0
# for record in records:
#     if record[1] is None:
#         try:
#             g = geocoder.baidu([record[3], record[2]], method="reverse", key=keys[key_iter])
#             if g.status_code == 200:
#                 street_name = g.json.get('street', None)
#                 if street_name is not None:
#                     cur.execute(update_sql%(street_name, record[0]))
#                     conn.commit()
#             else:
#                 print("geocoder error")
#                 key_iter += 1
#                 g = geocoder.baidu([record[3], record[2]], method="reverse", key=keys[key_iter])
#                 if g.status_code == 200:
#                     street_name = g.json.get('street', None)
#                     if street_name is not None:
#                         cur.execute(update_sql % (street_name, record[0]))
#                         conn.commit()
#         except:
#             print("request error")
# conn.close()


# conn = psycopg2.connect("host=localhost port=5432 dbname=routing2 user=postgres password=yan19910131")
# cur = conn.cursor()
# sql = "select gid, name, x1, y1, x2, y2 from ways"
# update_sql = "update ways set name = '%s' where gid = %d"
# cur.execute(sql)
# records = cur.fetchall()
# keys = []
# keys.append("ZR26Xbeo5g9xBMtoGUw7czbeO7DWE6hi")
# keys.append("3RqnWEkKD7z670OBqT1xlU1VGGLzG5OW")
# keys.append("BUDoeiO34pt4zyfYTln3kd4Hu7VGTbaI")
# keys.append("0TovjUUufyGN7KMlFu8PgsnBGlh9wGPH")
# keys.append("2tYnr3gDMTID7y1Z2b74ZHoXACGBVDsR")
# keys.append("ftnqf1pGRWrtrZ7zkyCjQfS4AHcMFKX8")
# key_iter = 0
# for record in records:
#     if record[1] is None:
#         try:
#             g = geocoder.baidu([record[3], record[2]], method="reverse", key=keys[key_iter])
#             if g.status_code == 200:
#                 street_name = g.json.get('street', None)
#                 if street_name is not None:
#                     cur.execute(update_sql%(street_name, record[0]))
#                     conn.commit()
#             else:
#                 print("geocoder error")
#                 key_iter += 1
#                 g = geocoder.baidu([record[3], record[2]], method="reverse", key=keys[key_iter])
#                 if g.status_code == 200:
#                     street_name = g.json.get('street', None)
#                     if street_name is not None:
#                         cur.execute(update_sql % (street_name, record[0]))
#                         conn.commit()
#         except:
#             print("request error")
# conn.close()
def save_records(cur, combine_records):
    osm_id = combine_records[0][2][1]
    tag_id = combine_records[0][2][2]
    name = combine_records[0][2][5]
    source_i = combine_records[0][2][6]
    target_i = combine_records[-1][2][7]
    source_osm = combine_records[0][2][8]
    target_osm = combine_records[-1][2][9]
    one_way = combine_records[0][2][14]
    oneway = combine_records[0][2][15]
    x1 = combine_records[0][2][16]
    y1 = combine_records[0][2][17]
    x2 = combine_records[-1][2][18]
    y2 = combine_records[-1][2][19]
    maxspeed_forward = combine_records[0][2][20]
    maxspeed_backward = combine_records[0][2][21]
    priority = combine_records[0][2][22]
    cost = 0.0
    reverse_cost = 0.0
    cost_s = 0.0
    reverse_cost_s = 0.0
    length = 0.0
    length_m = 0.0
    line_points = []
    for cm in combine_records:
        cost += cm[2][10]
        reverse_cost += cm[2][11]
        cost_s += cm[2][12]
        reverse_cost_s += cm[2][13]
        length += cm[2][3]
        length_m += cm[2][4]
        cm_points = cm[2][-1].split('(')[1].split(')')[0].split(",")
        cm_points = [p.split(" ") for p in cm_points]
        cm_points = [(float(p[0]), float(p[1])) for p in cm_points]
        line_points += cm_points
    cm_points_geo = LineString(line_points)
    cur.execute(sql_insert_2, (osm_id, tag_id, length, length_m, name, source_i, target_i, source_osm, target_osm,
                                cost, reverse_cost, cost_s, reverse_cost_s, one_way, oneway, x1, y1, x2, y2,
                                maxspeed_forward,
                                maxspeed_backward, priority, cm_points_geo.wkb_hex, 4326))


def find_start_point(network_dict, point_count):
    start_point = None
    v_index = 0
    for (pc, pv) in point_count.items():
        if pv%2 == 1 and network_dict[pc][0][3] == 0:
            start_point = pc
    if start_point is None:
        for (k, vs) in network_dict.items():
            for vi, v in enumerate(vs):
                if v[3] == 0:
                    start_point = v[2][6]
                    v_index = vi
                    break
            if start_point is not None:
                break
    return start_point, v_index

def decrease_edge(edge, network_dict, point_count):
    source = edge[6]
    target = edge[7]
    point_count[source] -= 1
    point_count[target] -= 1
    for vi, v in enumerate(network_dict[source]):
        if v[2][6] == source and v[2][7] == target:
            del network_dict[source][vi]
            break
    for vi, v in enumerate(network_dict[target]):
        if v[2][6] == source and v[2][7] == target:
            del network_dict[target][vi]
            break

conn = psycopg2.connect("host=localhost port=5432 dbname=shenzhen user=postgres password=yan19910131")
sql = "select distinct osm_id from ways"
cur = conn.cursor()
cur.execute(sql)
osm_ids = cur.fetchall()
sql_2 = "select gid, osm_id, tag_id, length, length_m, name, source, target, source_osm, target_osm, " \
             "cost, reverse_cost, cost_s, reverse_cost_s, one_way, oneway, x1, y1, x2, y2, maxspeed_forward, " \
             "maxspeed_backward, priority, the_geom, st_astext(the_geom) from ways where osm_id=%s"
# sql_3 = "select count(gid) from ways where target=%s"
sql_3 = "select gid, name from ways where target=%s"
sql_4 = "select * from ways where source=%s"
sql_insert = "insert into ways_new (osm_id, tag_id, length, length_m, name, source, target, source_osm, target_osm, " \
             "cost, reverse_cost, cost_s, reverse_cost_s, one_way, oneway, x1, y1, x2, y2, maxspeed_forward, " \
             "maxspeed_backward, priority, the_geom) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
              "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
# sql_insert_2 = "insert into ways_new (osm_id, tag_id, length, length_m, name, source, target, source_osm, target_osm, " \
#              "cost, reverse_cost, cost_s, reverse_cost_s, one_way, oneway, x1, y1, x2, y2, maxspeed_forward, " \
#              "maxspeed_backward, priority, the_geom) VALUES (%d, %d, %f, %f, '%s', %d, %d, %d, %d, %f, %f, %f, %f, " \
#              "%d, '%s', %f, %f, %f, %f, %f, %f, %f, ST_SetSRID('%s'::geometry, %s))"
sql_insert_2 = "insert into ways_new (osm_id, tag_id, length, length_m, name, source, target, source_osm, target_osm, " \
             "cost, reverse_cost, cost_s, reverse_cost_s, one_way, oneway, x1, y1, x2, y2, maxspeed_forward, " \
             "maxspeed_backward, priority, the_geom) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
             "%s, %s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(%s::geometry, %s))"
for osm_id in osm_ids:
    cur.execute(sql_2%osm_id)
    records = cur.fetchall()
    if records[0][5] is None:
        continue
    num_records = len(records)
    if num_records == 1:
        cur.execute(sql_insert, records[0][1:-1])
        conn.commit()
        continue
    network_dict = {}
    point_count = {}
    for record in records:
        network_dict[record[6]] = network_dict.get(record[6], [])
        network_dict[record[6]].append((record[6], record[7], record, 0))
        network_dict[record[7]] = network_dict.get(record[7], [])
        network_dict[record[7]].append((record[7], record[6], record, 1))
        point_count[record[6]] = point_count.get(record[6], 0) + 1
        point_count[record[7]] = point_count.get(record[7], 0) + 1
    start_point, v_index = find_start_point(network_dict, point_count)
    combine_records = [network_dict[start_point][v_index]]
    decrease_edge(network_dict[start_point][v_index][2], network_dict, point_count)
    road_count = 1
    # print("start")
    while True:
        edge = combine_records[-1]
        if edge[3]:
            source = edge[1]
            target = edge[0]
        else:
            source = edge[0]
            target = edge[1]
        next_edge = None
        can_next_edges = network_dict[target]
        for c_n_e in can_next_edges:
            if c_n_e[1] == source:
                continue
            next_edge = c_n_e
        if next_edge is None:
            if len(combine_records) == 1:
                cur.execute(sql_insert, combine_records[0][2][1:-1])
            else:
                save_records(cur, combine_records)
            conn.commit()
            if road_count == num_records:
                break
            start_point, v_index = find_start_point(network_dict, point_count)
            combine_records = [network_dict[start_point][v_index]]
            decrease_edge(network_dict[start_point][v_index][2], network_dict, point_count)
            road_count += 1
            continue
        else:
            decrease_edge(next_edge[2], network_dict, point_count)

        tmp_count = 0
        cur.execute(sql_3%target)
        #road_count = cur.fetchone()[0]
        temp_records = cur.fetchall()
        for t_r in temp_records:
            if t_r[1] is not None:
                tmp_count += 1
        cur.execute(sql_4%target)
        temp_records = cur.fetchall()
        for t_r in temp_records:
            if t_r[1] is not None:
                tmp_count += 1
        if tmp_count < 2:
            print("error")
        if tmp_count == 2:
            combine_records.append(next_edge)
        else:
            save_records(cur, combine_records)
            conn.commit()
            combine_records = []
            combine_records.append(next_edge)
        road_count += 1
    # if road_count == 0:
    #     for record in records:
    #         cur.execute(sql_insert % record[1:-1])
    #         conn.commit()
    #         road_count += 1
    print(road_count, num_records)
    assert road_count == num_records