# app/ocr.py
import os
import numpy as np
from multiprocessing import Pool
from pdf2image import convert_from_bytes
import easyocr
import torch

_reader = None

def _get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
    return _reader

def extract_boxes_and_images(pdf_bytes: bytes):
    # 1. Convert pages once
    pages = convert_from_bytes(pdf_bytes, dpi=200, thread_count=4)

    # 2. Pool size matches Celery concurrency (fallback to CPU count)
    pool_size = int(os.getenv("CELERY_WORKER_CONCURRENCY", os.cpu_count()))
    with Pool(processes=pool_size) as pool:
        all_boxes = pool.map(_process_page, pages)

    return pages, all_boxes

def _process_page(page):
    reader = _get_reader()
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
