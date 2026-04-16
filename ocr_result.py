import json
import os
import pathlib
from os.path import exists
import psycopg2
from database import connection_params

def read_documents(job_id):
    result = {"text": ""}
    json_path = str(pathlib.Path().absolute()) + "\\filepath\\_" + job_id + ".json"
    processing_status = check_processing_status(job_id)
    if processing_status[0] == 0:
        result["text"] = "Document is processing. Please wait to complete."
        return result
    else:
        file_exists = exists(json_path)
        if file_exists:
            f = open(json_path, "r")
            data = json.loads(f.read())
            # os.remove(json_path)
            return data


def check_processing_status(job_id):
    conn = psycopg2.connect(**connection_params)
    conn.autocommit = True
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("select processing_status from ocr_request where job_id='" + job_id + "'")
            column_names = [row[0] for row in cursor]
            return column_names


def update_jobid_processing_status(json_path, job_id,status):
    try:
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
        update_query = """ UPDATE ocr_request SET processing_status = %s,json_path=%s WHERE job_id = %s"""
        record_to_insert = (status,json_path, job_id)
        cursor.execute(update_query, record_to_insert)
        conn.commit()
    except (Exception, psycopg2.Error) as error:
        print("Failed to update", error)

    finally:
        if conn:
            cursor.close()
            conn.close()
