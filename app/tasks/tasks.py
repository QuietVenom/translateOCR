from app.tasks.celery_app import celery
from app.pipeline import process_pdf_bytes

@celery.task(bind=True, name="tasks.translate_pdf")
def translate_pdf_task(self, pdf_bytes: bytes) -> bytes:
    self.update_state(state="STARTED")
    return process_pdf_bytes(pdf_bytes)