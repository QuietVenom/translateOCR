# app/services/ocr.py

import os
import numpy as np
from multiprocessing import Pool
from pdf2image import convert_from_bytes
import easyocr
import torch

# Reader instance lives here, per process
_reader = None

def _get_reader():
    global _reader
    if _reader is None:
        # Only now do we pay the cost of loading the model
        _reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
    return _reader

def _process_page(page):
    """
    Called inside each worker process.
    """
    reader = _get_reader()
    # Convert PIL page to OpenCV‐style array
    img_np = np.array(page.convert('RGB'))[:, :, ::-1]
    # detail=1 gives bounding boxes + text
    results = reader.readtext(img_np, detail=1)
    # Transform results to your expected format…
    boxes = []
    for bbox, text, conf in results:
        boxes.append({"bbox": bbox, "text": text, "confidence": conf})
    return boxes

def extract_boxes_and_images(pdf_bytes: bytes):
    """
    1) Convert PDF to PIL pages.
    2) Spin up a Pool whose size matches Celery concurrency.
    3) OCR each page in parallel.
    """
    # 1. PDF → images
    pages = convert_from_bytes(pdf_bytes, dpi=200, thread_count=4)

    # 2. Pull pool size from the same env var that drives Celery workers
    pool_size = int(os.getenv("CELERY_WORKER_CONCURRENCY", os.cpu_count()))

    # 3. OCR pages in parallel
    with Pool(processes=pool_size) as pool:
        all_boxes = pool.map(_process_page, pages)

    return pages, all_boxes
