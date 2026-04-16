from http.client import HTTPException
import pathlib
import psycopg2
import typing
from fastapi import FastAPI, File, Form, UploadFile, BackgroundTasks

import asyncio
from pydantic import BaseModel
from typing import List
import random
import string
from database import connection_params
from ocr_logic import read_document
from ocr_invoice import read_invoice
from ocr_result import read_documents
app = FastAPI()



def random_number_generation(numb):
    N = numb
    res = ''.join(random.choices(string.digits + string.ascii_letters +
                                 string.digits, k=N))
    return res


class CheckboxItem(BaseModel):
    label: str
    checked: bool
def create_tables():
    """ create tables in the PostgreSQL database"""
    command = """CREATE TABLE ocr_request (_id SERIAL PRIMARY KEY,file_name VARCHAR(255) NOT NULL,processing_status INTEGER NOT NULL,job_id VARCHAR(255) NOT NULL,json_path VARCHAR(255))"""
    conn = None
    conn = psycopg2.connect(**connection_params)
    try:
        cur = conn.cursor()
        cur.execute(command)
        cur.close()
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

def exist_table():
    conn = psycopg2.connect(**connection_params)
    conn.autocommit = True
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM information_schema. tables WHERE table_catalog='ocr_service' AND table_schema='public' AND table_name='ocr_request')")
            column_names = [row[0] for row in cursor]
            if column_names[0] == False:
                    create_tables()


#    This is the background running task . This function use in step 2.
#  read_ocr is the function for extract tables, key values and lines.
async def run_background_task(file_path: str, jobId: str,checkboxes): # document processing
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, read_document, file_path, jobId,checkboxes)
    return result


async def run_background_invoice_processing(file_path: str, jobId: str): # invoice processing
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, read_invoice, file_path, jobId)
    return result

# Step 1 : for sending request. Here only save path of the current document.
# here generate random number for saving unique file path.
@app.api_route("/file/upload", methods=["POST"])
def send_request(file: UploadFile = File(...)):
    try:
        result = {"file_path": ""}
        random_no = random_number_generation(35)
        file_name = f"{str(random_no) + file.filename}"
        file_location=str(pathlib.Path().absolute()) + "/filepath/" +file_name
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        result["file_path"] = file_name
        return result
    except HTTPException as ex:
        print(ex.detail)
        raise HTTPException(status_code=ex.status_code, detail=ex.detail)


# Step 2: here save file name ,processing status and jobid to database.
# And run the background task and also return jobid for the user.
@app.post("/ocr/analyzeDocument") # This is for document processing
async def submit_task(background_tasks: BackgroundTasks, file_path: str, checkboxes: List[CheckboxItem]):

    exist_table()
    random_no = random_number_generation(35)
    conn = psycopg2.connect(**connection_params)
    cursor = conn.cursor()
    file_loc=str(pathlib.Path().absolute()) + "/filepath/" +file_path

    postgres_insert_query = """ INSERT INTO ocr_request (file_name, processing_status,job_id) VALUES (%s,%s,%s)"""
    record_to_insert = (file_loc, 0, str(random_no))
    cursor.execute(postgres_insert_query, record_to_insert)

    conn.commit()
    background_tasks.add_task(run_background_task, file_loc, str(random_no),checkboxes)
    return {"job_id": str(random_no)}


@app.post("/ocr/analyzeExpenseDoc") # This is for invoice processing
async def invoice_processing(background_tasks: BackgroundTasks, file_path: str):
    exist_table()
    random_no = random_number_generation(35)
    conn = psycopg2.connect(**connection_params)
    cursor = conn.cursor()
    file_loc=str(pathlib.Path().absolute()) + "/filepath/" +file_path
    postgres_insert_query = """ INSERT INTO ocr_request (file_name, processing_status,job_id) VALUES (%s,%s,%s)"""
    record_to_insert = (file_loc, 0, str(random_no))
    cursor.execute(postgres_insert_query, record_to_insert)

    conn.commit()
    background_tasks.add_task(run_background_invoice_processing, file_loc, str(random_no))
    return {"job_id": str(random_no)}

#  Step 3: Here check result is ready for current job id .
#  when the json result is ready in folder,it will return the output
@app.api_route("/ocr/getReadResults", methods=["GET"])
def read_ocr_tables(job_id: str):
    try:
        data = read_documents(job_id)
        return data

    except HTTPException as ex:
        print(ex.detail)
        raise HTTPException(status_code=ex.status_code, detail=ex.detail)

