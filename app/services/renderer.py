import io
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

# Load a default TrueType font
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def blur_and_overlay(page_image: Image.Image, boxes: list[dict], translations: list[str]) -> Image.Image:
    """
    Args:
        page_image: PIL image of a PDF page
        boxes: list of dicts with 'bbox': [x0, y0, x1, y1]
        translations: corresponding list of translated strings

    Returns:
        A new PIL image with blurred text boxes and overlayed translations.
    """
    # Convert PIL to OpenCV image (BGR)
    cv_img = cv2.cvtColor(np.array(page_image), cv2.COLOR_RGB2BGR)

    # 1. Apply blur to each bounding box
    for box in boxes:
        x0, y0, x1, y1 = map(int, box['bbox'])
        roi = cv_img[y0:y1, x0:x1]
        if roi.size == 0:
            continue
        blurred = cv2.GaussianBlur(roi, (21, 21), 0)
        cv_img[y0:y1, x0:x1] = blurred

    # Back to PIL for text overlay
    pil_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    font = ImageFont.truetype(FONT_PATH, size=14)

    # 2. Overlay translations
    for box, text in zip(boxes, translations):
        x0, y0, x1, y1 = box['bbox']
        # Fit text inside bbox:
        text_bbox = draw.textbbox((x0, y0), text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        box_w = x1 - x0
        # Adjust font size if text too wide
        if text_w > box_w:
            ratio = box_w / text_w
            font_size = max(8, int(font.size * ratio))
            font = ImageFont.truetype(FONT_PATH, size=font_size)
        # Draw text
        draw.text((x0, y0), text, fill="black", font=font)

    return pil_img

def render_pdf_pages(page_images: list[Image.Image], page_boxes: list[list[dict]], page_translations: list[list[str]]) -> io.BytesIO:
    """
    Process all pages, apply renderer, and reassemble a PDF.

    Args:
        page_images: list of PIL images for each page
        page_boxes: per-page bounding boxes
        page_translations: per-page translated texts

    Returns:
        io.BytesIO buffer containing the final PDF.
    """
    processed_images = []
    for img, boxes, trans in zip(page_images, page_boxes, page_translations):
        processed_images.append(blur_and_overlay(img, boxes, trans))

    buffer = io.BytesIO()
    processed_images[0].save(buffer, format='PDF', save_all=True, append_images=processed_images[1:])
    buffer.seek(0)
    return buffer
