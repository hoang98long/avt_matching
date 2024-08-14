import ftplib
from utils.config import *
from utils.matching_image import Matching_Image
import psycopg2
import json
from datetime import datetime
import os
import ast
import threading
import time


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

    def match(self, conn, id, task_param, config_data):
        input_files = []
        for ship_object in task_param:
            input_files.append(ship_object['path'])
        try:
            # filename = src_img_path.split("/")[-1]
            # local_file_path = LOCAL_SRC_CLASSIFY_IMAGE_PATH + filename
            # ftp = connect_ftp(config_data)
            # download_file(ftp, src_img_path, local_file_path)
            ftp = connect_ftp(config_data)
            input_files_local = []
            task_output = {

            }
            for input_file in input_files:
                filename = input_file.split("/")[-1]
                local_file_path = os.path.join(LOCAL_SRC_MATCHING_IMAGE_PATH, filename)
                input_files_local.append(local_file_path)
                if not os.path.isfile(local_file_path):
                    download_file(ftp, input_file, local_file_path)
            matching_image = Matching_Image()
            for input_file, input_file_local in zip(input_files, input_files_local):
                result = matching_image.matching(input_file_local, model, scaler)
                task_output[input_file] = result
            task_output = str(task_output).replace("'", "\"")
            # result = classification_image.classify(local_file_path, model, scaler)
            # task_output = str({
            #     "output_class": result
            # })
            print("Connection closed")
            cursor = conn.cursor()
            route_to_db(cursor)
            cursor.execute("UPDATE avt_task SET task_stat = 1, task_output = %s, updated_at = %s WHERE id = %s", (task_output, get_time(), id,))
            conn.commit()
            return True
        except ftplib.all_errors as e:
            cursor = conn.cursor()
            route_to_db(cursor)
            cursor.execute("UPDATE avt_task SET task_stat = 0 WHERE id = %s", (id,))
            conn.commit()
            print(f"FTP error: {e}")
            return False

    def process(self, id, config_data, model, scaler):
        conn = psycopg2.connect(
            dbname=config_data['database']['database'],
            user=config_data['database']['user'],
            password=config_data['database']['password'],
            host=config_data['database']['host'],
            port=config_data['database']['port']
        )
        task_stat_value_holder = {'value': 2}
        stop_event = threading.Event()
        cursor = conn.cursor()
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

            return_flag = self.match(conn, id, task_param, config_data)
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
