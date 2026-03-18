from csv import reader
import os
import uuid
from fastapi import UploadFile
import fitz 
from docx import Document
import base64
from easyocr import Reader 

UPLOAD_DIR = "app/uploads/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

reader = Reader(lang_list=["en"])

def save_image(file: UploadFile) -> str:
    ext = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return file_path

def extract_text_fast(file_path: str) -> str:
    ext = file_path.split(".")[-1].lower()

    if ext == "pdf":
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text

    elif ext == "docx":
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])

    elif ext == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    return ""

def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()
    
def extract_text_easyocr(file_path: str) -> str:
    result = reader.readtext(file_path)
    return " ".join([item[1] for item in result])