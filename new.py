
import os
import sys
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File
import time
from datetime import datetime, timezone, timedelta
import cv2 as cv
import numpy as np
import fitz
import requests
import tempfile
import json





app=FastAPI()
def process_pdf_and_upload(input_file_path: str):
    try:
        doc = fitz.open(input_file_path)
        output_string = ""

        # Create a temporary directory to store the output images
        with tempfile.TemporaryDirectory() as temp_dir:
            output_d_path = os.path.join(temp_dir, 'output')
            os.mkdir(output_d_path)

            page_count = 1
            for page in doc:
                _pix = page.get_pixmap()
                pixmap_height = _pix.height
                pixmap_width = _pix.width


                margin_percentage = 0.05
                main_body_x_left = margin_percentage*pixmap_width
                main_body_x_right = pixmap_width - margin_percentage*pixmap_width
                main_body_y_top = margin_percentage*pixmap_height
                main_body_y_bottom = pixmap_height - margin_percentage*pixmap_height


                block_l = page.get_text('blocks')
        #print(f'Page No.: {page_count:04d}')
                block_row_cord_l = []
                for block in block_l:
            #print(f'{block[6]}: {block[0]:04.0f} {block[1]:04.0f} {block[2]:04.0f} {block[3]:04.0f}')
                    block_row_cord_l.append(block[1])

                row_indexes = np.argsort(block_row_cord_l)

                delimiter = '-'
        #print(f'{16*delimiter}')
        #print(row_indexes)
                block_l = [block_l[idx] for idx in row_indexes]
                image_count = 1
                for block in block_l:
            #print(f'{block[6]}: {block[0]:04.0f} {block[1]:04.0f} {block[2]:04.0f} {block[3]:04.0f}')

                    if block[6] == 0:
                        if block[0] > main_body_x_left and block[1] > main_body_y_top and block[2] < main_body_x_right and block[3] < main_body_y_bottom:
                            output_string += f'{block[4]} '

                    elif block[6] == 1:
                        clip = fitz.Rect(block[0], block[1], block[2], block[3])
                        pix = page.get_pixmap(clip=clip)
                       
                        output_image_name = f'{page_count:02d}-{image_count:02d}.png'
                        output_image_path = os.path.join(output_d_path, output_image_name)
                        pix.save(output_image_path)
                
                #input_image = cv.imread(output_image_path)
                #imshow(input_image)
                #print(f'=============Dummy URL Link: {output_image_path}=============')
                        with open(output_image_path, 'rb') as image_file:
                            files = {'file': (output_image_name, image_file, 'image/png')}

                            headers = {
                            'Cookie': 'connect.sid=s%3Ausgf57whSODsQf2BzYMsFyfwg_dXGn-_.H1476KPvzTQR6evQlKXPx%2BRlmTEvg3OKrZOnUIESahY'
                            }

                            url = "https://ocdev.oneclick.info:3200/fileUpload"
                            #print("helo")
                            response = requests.post(url, headers=headers, files=files)

                            if response.status_code == 200:
                                server_response = response.json()
                                original_file_name = server_response.get("orignalFileName")
                                file_path = server_response.get("filePath")
                                if original_file_name and file_path:
                                    output_string += f'[{original_file_name}], ({file_path}) '
                                else:
                                    print('Error: Missing "orignalFileName" or "filePath" in server response')
                            else:
                                print('Error uploading image to the server')
                        image_count += 1

                page_count += 1
        return {"message": "PDF processed and images uploaded successfully","output_string": output_string}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process-pdf/")
async def process_pdf(input_file: UploadFile):
    try:
        # Create a temporary directory to store the uploaded PDF
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file_path = os.path.join(temp_dir, input_file.filename)
            with open(input_file_path, "wb") as temp_file:
                shutil.copyfileobj(input_file.file, temp_file)
            return process_pdf_and_upload(input_file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))