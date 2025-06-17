# app/ocr.py
import io
import numpy as np
from pdf2image import convert_from_bytes, pdfinfo_from_bytes
import easyocr
from app.services.translator import translate_batch
from app.services.renderer import render_pdf_pages

reader = easyocr.Reader(['en'], gpu=False)

def extract_boxes_and_images(pdf_bytes: bytes):
    info = pdfinfo_from_bytes(pdf_bytes)
    orig_dpi = int(info.get("dpi", 200))
    pages = convert_from_bytes(pdf_bytes, dpi=orig_dpi, thread_count=1)
    
    all_boxes = []
    for page in pages:
        img_np = np.array(page.convert('RGB'))[:, :, ::-1]
        results = reader.readtext(img_np, detail=1)
        boxes = [{
            'bbox': [
                int(min(pt[0] for pt in box)),
                int(min(pt[1] for pt in box)),
                int(max(pt[0] for pt in box)),
                int(max(pt[1] for pt in box))
            ],
            'text': txt
        } for box, txt, _ in results]
        all_boxes.append(boxes)

    return pages, all_boxes
