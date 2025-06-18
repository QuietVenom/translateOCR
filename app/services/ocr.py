# app/ocr.py
import io
import numpy as np
from multiprocessing import Pool
from pdf2image import convert_from_bytes
import easyocr
import torch
from app.services.translator import translate_batch
from app.services.renderer import render_pdf_pages

reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())

def extract_boxes_and_images(pdf_bytes: bytes):
    # Add parallel processing
    with Pool(processes=4) as pool:
        pages = convert_from_bytes(pdf_bytes, dpi=200, thread_count=4)
        all_boxes = pool.map(process_page, pages)
    return pages, all_boxes

def process_page(page):
    img_np = np.array(page.convert('RGB'))[:, :, ::-1]
    results = reader.readtext(img_np, detail=1)
    return [{
        'bbox': [
            int(min(pt[0] for pt in box)),
            int(min(pt[1] for pt in box)),
            int(max(pt[0] for pt in box)),
            int(max(pt[1] for pt in box))
        ],
        'text': txt
    } for box, txt, _ in results]
