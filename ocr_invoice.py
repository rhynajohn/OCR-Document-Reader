import os
import pathlib
from pathlib import Path
from pdf2image import convert_from_path
import json
import filetype
import easyocr
from ocr_result import update_jobid_processing_status
import cv2
import re

absolute_path = str(pathlib.Path().absolute())

def read_invoice(path, job_id):
    ext = os.path.splitext(path)[-1].lower()
    file_name = Path(path).stem
    api_result_set = {"data": []}

    if ext == ".pdf":
        pages = convert_from_path(path, 350)
        i = 1
        for page in pages:
            file_location = absolute_path + "\\filepath\\_" + file_name + "_Page_" + str(i) + ".PNG"
            image_name = file_location
            page.save(image_name, "JPEG")
            result = invoice_extraction(r"" + file_location)
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
        result_set = invoice_extraction(path)
        api_result_set["data"].append(result_set)
        json_object = json.dumps(result_set, indent=2)
        json_object = json_object.replace('\n', '')
        json_path = absolute_path + "\\filepath\\json\\_" + job_id + ".json"
        with open(json_path, "w") as outfile:
            outfile.write(json_object)
        update_jobid_processing_status(json_path, job_id, 1)
    else:
        error = path + " is an unknown file format."
        return error

def invoice_extraction(path):
    print("Performing invoice extraction. Extracting key-value pairs and lines.")

    # Initialize EasyOCR reader
    reader = easyocr.Reader(['en'])

    # Read the image using OpenCV
    image = cv2.imread(path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Perform OCR on the image
    ocr_results = reader.readtext(gray_image)

    # Extract text line by line
    extracted_data = {"lines": []}
    for result in ocr_results:
        text = result[1]
        bounding_box = result[0]

        # Extracting text line by line
        extracted_data["lines"].append(text)

    important_data = extract_important_data(extracted_data)

    # Display the extracted key-value pairs
    for key, value in important_data.items():
        print(f"{key}: {value}")

    return extracted_data

def extract_important_data(extracted_data):
    important_data = {}

    keys_of_interest = [
        "Sender",
        "GSTIN",
        "Phone",
        "PAN NO",
        "Invoice No.",
        "DATE",
        "Buyer Name",
        "Delivery Add,",
        "P.ONO",
        "OD-",
        "State",
        "GSTIN",
        "Challan No.",
        "PAN"
       
    ]

    lines = extracted_data["lines"]
    current_key = None
    for line in lines:
   
        if any(key in line for key in keys_of_interest):
            current_key = next((key for key in keys_of_interest if key in line), None)
        else:
            
            if current_key:
                important_data[current_key] = line
                current_key = None  

    return important_data

