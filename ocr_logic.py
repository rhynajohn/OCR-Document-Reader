import pathlib
from pathlib import Path
import filetype
#ocr_logic.py
import skimage.filters as filters
from skimage import exposure
from pdf2image import convert_from_path
from img2table.document import Image
import easyocr
import cv2
import json
import os
from ocr_result import update_jobid_processing_status

absolute_path = str(pathlib.Path().absolute())


def read_document(path, job_id,checkboxes):
    ext = os.path.splitext(path)[-1].lower()
    file_name = Path(path).stem
    header_cells = {"data": []}
    api_result_set = {"data": []}
    if ext == ".pdf":
        pages = convert_from_path(path, 350)
        i = 1
        for page in pages:
            file_location = absolute_path + "\\filepath\\_" + file_name + "_Page_" + str(
                i) + ".PNG"
            image_name = file_location
            page.save(image_name, "JPEG")
            result = ocr_document_extraction(r"" + file_location,str(i), checkboxes)
            api_result_set["data"].append(result)
            i = i + 1
            os.remove(file_location)
        print("path: " + path)
        os.remove(path)
        json_object = json.dumps(api_result_set, indent=2)
        json_object = json_object.replace('\n', '')
        json_path = absolute_path + "\\filepath\\_" + job_id + ".json"
        with open(json_path, "w") as outfile:
            outfile.write(json_object)
        update_jobid_processing_status(json_path, job_id, 1)
    elif filetype.is_image(path):
        result_set = {}
        result_set = ocr_document_extraction(path, "1", file_name, checkboxes)
        api_result_set["data"].append(result_set)
        json_object = json.dumps(result_set, indent=2)
        json_object = json_object.replace('\n', '')
        json_path = absolute_path + "\\filepath\\_" + job_id + ".json"
        with open(json_path, "w") as outfile:
            outfile.write(json_object)
        update_jobid_processing_status(json_path, job_id, 1)

    else:
        error = path + " is an unknown file format."
        return error


def ocr_document_extraction(image_path, page_num, checkboxes):
    try:
        result = {"page": int(page_num), "ocrTables": [], "ocrLineReads": [], "ocrKeyValuePairs": []}
        for checkbox in checkboxes:
            if checkbox.label == "tables": # you only completed tables. so commented other portion.
                                           # later we need lines and key values.
                ocrTables_results = process_ocr_logic(image_path)
                result["ocrTables"]=ocrTables_results

                # if ocrTables_results:
                #     for table in ocrTables_results:
                #         result["ocrTables"].append(table)

            #______________________________DO IT LATER_______________________________
            # __________line reading and key_values reading from documents____________

            # elif checkbox.label == "lines":
            #     # ocrlines = line_extraction(image_path, page_num, file_name)
            #     ocrlines, check_same_line, ocr_lines_bounding_box = line_reading(image_path, page_num)
            #     if ocrlines:
            #         for line in ocrlines:
            #             result["ocrLineReads"].append(line)
            #
            # elif checkbox.label == "key_values":
            #     ocrKeyValue = key_value_extraction(image_path, page_num)
            #     if ocrKeyValue:
            #         for keyvalues in ocrKeyValue:
            #             result["ocrKeyValuePairs"].append(keyvalues)

        return result

    except:
        result = {"page": int(page_num), "ocrTables": [], "ocrLineReads": [], "ocrKeyValuePairs": []}
        return result


def process_ocr_logic(image_path):
    image_doc = Image(image_path)
    extracted_tables = image_doc.extract_tables()
    sorted_tables = sorted(extracted_tables, key=lambda table: table.bbox.y1)
    ocr_tables = []
    result_data = {"data": []}
    reader = easyocr.Reader(['en'], gpu=True)
    for table_index, table in enumerate(sorted_tables):
        table_data = {"tableCells": []}
        row_count = len(table.content)
        column_count = len(table.content[0])

        for row_index in range(row_count):
            for col_index in range(column_count):
                cell = table.content[row_index][col_index]

                cell_image = cv2.imread(image_path)
                cell_image = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)

                x = cell.bbox.x1
                y = cell.bbox.y1
                w = cell.bbox.x2 - cell.bbox.x1
                h = cell.bbox.y2 - cell.bbox.y1
                cell_image = cell_image[y:y + h, x:x + w]

                ocr_results = reader.readtext(cell_image)
                if len(ocr_results) == 0:
                    word = " "
                    confidence = 0
                else:
                    word = ""
                    for bbox, line_text, confidence in ocr_results:
                        word += line_text + " "

                cell_data = {
                    "word": word,
                    "columnIndex": col_index + 1,
                    "rowIndex": row_index + 1,
                    "confidence": int((confidence) * 100),
                }

                table_data["tableCells"].append(cell_data)

        ocr_tables.append(table_data)

    result_data["data"].append({
        # "page": i + 1,
        "ocrTables": ocr_tables
    })




    # result_data["data"] = json.loads(json.dumps(result_data["data"], default=lambda o: int(o) if isinstance(o, np.int64) else o))

    return result_data
