from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from typing import List
from PIL import Image
import pytesseract
import io
import re

app = FastAPI()

def parse_lab_report(text: str):
    results = []
    pattern = re.compile(r"(?P<name>[A-Z \(\)]+)\s+(?P<value>\d+(\.\d+)?)\s*(?P<unit>[a-zA-Z/%]+)?\s+(?P<range>\d+(\.\d+)?-\d+(\.\d+)?)")

    for match in pattern.finditer(text):
        name = match.group("name").strip()
        value = float(match.group("value"))
        unit = match.group("unit") or ""
        ref_range = match.group("range")

        ref_min, ref_max = map(float, ref_range.split("-"))
        out_of_range = value < ref_min or value > ref_max

        results.append({
            "test_name": name,
            "test_value": str(value),
            "bio_reference_range": ref_range,
            "test_unit": unit,
            "lab_test_out_of_range": out_of_range
        })

    return results

@app.get("/")
def root():
    return {"message": "FastAPI OCR Lab Test API is running"}

@app.get("/upload", response_class=HTMLResponse)
async def upload_form():
    return """
    <html>
        <head>
            <title>Upload Lab Report</title>
        </head>
        <body>
            <h2>Upload Lab Report Image</h2>
            <form action="/get-lab-tests" enctype="multipart/form-data" method="post">
                <input name="file" type="file" accept="image/*">
                <input type="submit" value="Upload">
            </form>
        </body>
    </html>
    """

@app.post("/get-lab-tests")
async def get_lab_tests(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
        lab_data = parse_lab_report(text)

        return JSONResponse(content={
            "is_success": True,
            "data": lab_data
        })

    except Exception as e:
        return JSONResponse(content={
            "is_success": False,
            "error": str(e)
        })
