from app.services.ocr import extract_boxes_and_images
from app.services.translator import translate_batch
from app.services.renderer import render_pdf_pages

def process_pdf_bytes(pdf_bytes: bytes) -> bytes:
    pages, pages_boxes = extract_boxes_and_images(pdf_bytes)
    pages_translations = [
        translate_batch([b["text"] for b in boxes])
        for boxes in pages_boxes
    ]
    output_buf = render_pdf_pages(pages, pages_boxes, pages_translations)
    return output_buf.getvalue()