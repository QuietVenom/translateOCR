import gc
from app.services.ocr import extract_boxes_and_images
from app.services.translator import translate_batch
from app.services.renderer import render_pdf_pages

def process_pdf_bytes(pdf_bytes: bytes) -> bytes:
    # PRE-INITIALIZE so they always exist
    pages = pages_boxes = pages_translations = None

    try:
        pages, pages_boxes = extract_boxes_and_images(pdf_bytes)
        pages_translations = [
            translate_batch([b["text"] for b in boxes])
            for boxes in pages_boxes
        ]
        output_buf = render_pdf_pages(pages, pages_boxes, pages_translations)
        return output_buf.getvalue()

    finally:
        # Only delete if they were actually set
        if pages is not None:
            del pages
        if pages_boxes is not None:
            del pages_boxes
        if pages_translations is not None:
            del pages_translations
        gc.collect()
