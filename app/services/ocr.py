# app/services/ocr.py

import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor
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
    # detail=1 + paragraph=True groups words into lines; may return (bbox, text) or (bbox, text, conf)
    results = reader.readtext(img_np, detail=1, paragraph=True)
    # Transform results to your expected format…
    boxes = []
    for item in results:
        # EasyOCR may return 2-tuple or 3-tuple depending on paragraph grouping
        if len(item) == 3:
            bbox, text, conf = item
        else:
            bbox, text = item
            conf = None
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
    
    # Use threads instead of processes to avoid daemon‐forking issues
    with ThreadPoolExecutor(max_workers=pool_size) as executor:
        all_boxes = list(executor.map(_process_page, pages))

    return pages, all_boxes
