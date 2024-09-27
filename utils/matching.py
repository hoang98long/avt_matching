import ftplib
from utils.matching_image import Matching_Image
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, timedelta
import ast
import threading
import time
import json


def connect_ftp(config_data):
    ftp = ftplib.FTP()
    ftp.connect(config_data['ftp']['host'], config_data['ftp']['port'])
    ftp.set_pasv(True)
    ftp.login(user=config_data['ftp']['user'], passwd=config_data['ftp']['password'])
    return ftp


def check_and_create_directory(ftp, directory):
    try:
        ftp.cwd(directory)
    except ftplib.error_perm as e:
        if str(e).startswith('550'):
            ftp.mkd(directory)
        else:
            print(f"Error changing to directory '{directory}': {e}")


def download_file(ftp, ftp_file_path, local_file_path):
    try:
        with open(local_file_path, 'wb') as file:
            ftp.retrbinary(f"RETR {ftp_file_path}", file.write)
        print(f"Downloaded '{ftp_file_path}' to '{local_file_path}'")
    except ftplib.all_errors as e:
        print(f"FTP error: {e}")


def route_to_db(cursor):
    cursor.execute('SET search_path TO public')
    cursor.execute("SELECT current_schema()")


def update_database(id, task_stat_value, conn):
    cursor = conn.cursor()
    # Update the task_stat field
    cursor.execute('UPDATE avt_task SET task_stat = %s WHERE id = %s', (task_stat_value, id))
    conn.commit()
    # Select and print the updated row
    # cursor.execute('SELECT * FROM avt_task WHERE id = %s', (id,))
    # row = cursor.fetchone()
    # print(row)


def check_and_update(id, task_stat_value_holder, conn, stop_event):
    start_time = time.time()
    while not stop_event.is_set():
        time.sleep(5)
        if stop_event.is_set():
            break
        elapsed_time = time.time() - start_time
        task_stat_value_holder['value'] = max(2, int(elapsed_time))
        update_database(id, task_stat_value_holder['value'], conn)


def get_time():
    now = datetime.now()
    current_datetime = datetime(now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond)
    return current_datetime


class Matching:
    def __init__(self):
        pass

    def match(self, conn, id, task_param):
        time_detected = datetime.now()
        detections = json.loads(task_param[1:-1])['detections']
        try:
            matching_image = Matching_Image()
            for ship_object in detections:
                (latitude_detected, longitude_detected, width_detected,
                 height_detected, cog_detected) = ship_object['coords'][0:6]
                cursor = conn.cursor(cursor_factory=DictCursor)
                cursor.execute('SET search_path TO public')
                cursor.execute("SELECT current_schema()")
                query = """
                    SELECT *
                    FROM avt_adsb_data
                    WHERE import_at BETWEEN %s AND %s;
                """
                cursor.execute(query, (time_detected - timedelta(seconds=10), time_detected + timedelta(seconds=10)))
                records = cursor.fetchall()
                list_possible_ship = []
                for record in records:
                    ship_id = record['id']
                    longitude_ais = record['lng']
                    latitude_ais = record['lat']
                    width_ais = record['width']
                    height_ais = record['height']
                    cog_ais = record['cog']
                    if not matching_image.position_check(latitude_detected, longitude_detected, longitude_ais,
                                                         latitude_ais, time_detected):
                        continue
                    list_possible_ship.append([ship_id, matching_image.likelihood(cog_detected, cog_ais, width_detected,
                                                                                  width_ais, height_detected,
                                                                                  height_ais, latitude_detected,
                                                                                  longitude_detected, latitude_ais,
                                                                                  longitude_ais, time_detected)])
                if len(list_possible_ship) == 0:
                    print("no ship match")
                    continue
                max_likelihood_ship = max(list_possible_ship, key=lambda x: x[1])
                print("id ship matching: ", max_likelihood_ship[0])
            print("Connection closed")
            return True
        except ftplib.all_errors as e:
            print(f"FTP error: {e}")
            return False

    def process(self, id, config_data):
        conn = psycopg2.connect(
            dbname=config_data['database']['database'],
            user=config_data['database']['user'],
            password=config_data['database']['password'],
            host=config_data['database']['host'],
            port=config_data['database']['port']
        )
        task_stat_value_holder = {'value': 2}
        stop_event = threading.Event()
        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute('SET search_path TO public')
        cursor.execute("SELECT current_schema()")
        cursor.execute("SELECT task_param FROM avt_task WHERE id = %s", (id,))
        result = cursor.fetchone()
        task_param = ast.literal_eval(result[0])
        if len(task_param) == 0:
            task_stat_value_holder['value'] = 0
            update_database(id, task_stat_value_holder['value'], conn)
            return
        checker_thread = threading.Thread(target=check_and_update, args=(id, task_stat_value_holder, conn, stop_event))
        checker_thread.start()
        try:

            return_flag = self.match(conn, id, task_param)
            cursor.close()
            if return_flag:
                task_stat_value_holder['value'] = 1
            else:
                task_stat_value_holder['value'] = 0
        except Exception as e:
            task_stat_value_holder['value'] = 0
        stop_event.set()
        update_database(id, task_stat_value_holder['value'], conn)
        checker_thread.join()
