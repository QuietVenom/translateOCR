from app.tasks.celery_app import celery
from app.pipeline import process_pdf_bytes
from app.services.ocr import extract_boxes_and_images
from app.services.translator import translate_batch
from app.services.renderer import render_pdf_pages
from celery.app.task import Task

@celery.task(bind=True, name="tasks.translate_pdf")
def translate_pdf_task(self: Task, pdf_bytes: bytes) -> bytes:
    """
    Properly implemented Celery task with correct state handling
    
    Args:
        self: The bound task instance
        pdf_bytes: Input PDF file content
        
    Returns:
        Processed PDF as bytes
    """
    # Initialize progress tracking
    current_progress = {
        'progress': 0,
        'stage': 'starting',
        'details': 'Initializing processing'
    }

    def update_progress(progress: int, stage: str, details: str = ""):
        nonlocal current_progress
        current_progress = {
            'progress': min(100, max(0, progress)),
            'stage': stage,
            'details': details
        }
        self.update_state(state='PROGRESS', meta=current_progress)

    try:
        # Stage 1: OCR Processing
        update_progress(10, 'ocr', 'Extracting text from PDF')
        pages, pages_boxes = extract_boxes_and_images(pdf_bytes)
        total_boxes = sum(len(boxes) for boxes in pages_boxes)
        update_progress(20, 'ocr', f'Found {total_boxes} text boxes')

        # Stage 2: Translation
        translations = []
        boxes_processed = 0
        
        for page_idx, boxes in enumerate(pages_boxes):
            update_progress(
                20 + (boxes_processed/total_boxes)*60,
                'translation',
                f'Page {page_idx+1}/{len(pages_boxes)}'
            )
            
            translations.append(translate_batch([b["text"] for b in boxes]))
            boxes_processed += len(boxes)
            
            update_progress(
                20 + (boxes_processed/total_boxes)*60,
                'translation',
                f'Translated {boxes_processed}/{total_boxes} boxes'
            )

        # Stage 3: Rendering
        update_progress(85, 'rendering', 'Generating output PDF')
        output_buf = render_pdf_pages(pages, pages_boxes, translations)
        
        update_progress(100, 'complete', 'Finished processing')
        return output_buf.getvalue()

    except Exception as e:
        # Proper error state with current progress
        error_state = {
            **current_progress,
            'error': str(e),
            'status': 'failed'
        }
        self.update_state(state='FAILURE', meta=error_state)
        raise