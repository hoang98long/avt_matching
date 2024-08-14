import argparse
import time

from utils.matching import Classification
from utils.config import *
import joblib
import json
import psycopg2

model = joblib.load(SHIP_CLASSIFICATION_MODEL_PATH)
scaler = joblib.load(SHIP_CLASSIFICATION_SCALER_PATH)


def get_task_id_list(task_type):
    conn = psycopg2.connect(
        dbname=config_data['database']['database'],
        user=config_data['database']['user'],
        password=config_data['database']['password'],
        host=config_data['database']['host'],
        port=config_data['database']['port']
    )
    cursor = conn.cursor()
    cursor.execute('SET search_path TO public')
    cursor.execute("SELECT current_schema()")
    cursor.execute("SELECT id FROM avt_task WHERE task_type = %s and task_stat < 0 ORDER BY task_stat DESC",
                   (task_type,))
    result = cursor.fetchall()
    return [res[0] for res in result]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument('--avt_task_id', type=int, required=True, help='task id')
    parser.add_argument('--config_file', type=str, required=True, help='config file')
    args = parser.parse_args()
    while True:
        config_data = json.load(open(args.config_file))
        task_type = 6
        list_task = get_task_id_list(task_type)
        if len(list_task) > 0:
            for task_id in list_task:
                classification = Classification()
                classification.process(task_id, config_data, model, scaler)
        time.sleep(5)
