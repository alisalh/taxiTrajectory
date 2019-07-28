import os
import sqlite3


def create_table(conn, table_name):
    cur = conn.cursor()

    sql = 'create table if not exists ' + table_name + ' (taxi_id integer, latitude float, longitude float, ' \
                                                       'status integer, taxi_license text, speed integer, angel integer, ' \
                                                       'year integer, month integer, day integer, ' \
                                                       'hour integer, minute integer, second integer)'
    cur.execute(sql)
    sql = "create index index_"+table_name+" on " + table_name + " (taxi_id)"
    cur.execute(sql)
    conn.commit()
    cur.close()


def clear_database(conn, table_name):
    cur = conn.cursor()
    sql = 'drop table if exists ' + table_name
    cur.execute(sql)
    conn.commit()
    cur.close()


def read_data_from_dir(data_dir, db_name, table_name):
    db_path = os.path.join("data/shenzhen/db", db_name)
    conn = sqlite3.connect(db_path)
    print("create and insert %s" % (db_name))
    # if os.path.exists(db_path):
    #     return
    clear_database(conn, table_name)
    create_table(conn, table_name)
    print("insert records")
    cur = conn.cursor()
    sql = "PRAGMA synchronous = OFF"
    cur.execute(sql)
    sql = "insert into " + table_name + " (taxi_id, taxi_license, speed, angel, latitude, longitude, status, year, month, day, hour, minute, second) " \
                                        "values (%d, '%s', %d, %d, %f, %f, %d, %d, %d, %d, %d, %d, %d)"
    for taxi_iter, data_file in enumerate(os.listdir(data_dir)):
        print(taxi_iter, data_file)
        with open(os.path.join(data_dir, data_file), 'r', encoding='gbk') as txt_file:
            # if taxi_iter < 11532:
            #     continue
            # #continue
            for i, line in enumerate(txt_file):
                # print(line)
                if i == 0:
                    continue
                fields = line.split(",")
                taxi_license = fields[0]
                latitude = float(fields[3])
                longitude = float(fields[2])
                taxi_status = int(fields[4])
                #print(taxi_status)
                speed = int(fields[5])
                angel = int(fields[6])
                date_str, time_str = fields[1].strip().split(" ")
                year, month, day = date_str.split("/")
                hour, minute, second = time_str.split(":")
                year = int(year)
                month = int(month)
                day = int(day)
                hour = int(hour)
                minute = int(minute)
                second = int(second)
                # datetime_field = datetime.datetime(year, month, day, hour, minute, second)
                cur.execute(sql % (taxi_iter, taxi_license, speed, angel, latitude, longitude, taxi_status, year, month, day, hour, minute, second))
                if i % 10000 == 0:
                    print("process %s records" % i)
                    conn.commit()
            conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    file_dir = read_data_from_dir("data/shenzhen/track_exp", 'shenzhen.db', 'taxi_gps')
