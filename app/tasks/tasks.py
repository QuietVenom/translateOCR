# app/tasks/tasks.py

import celery
from app.pipeline import process_pdf_bytes
from celery.app.task import Task

@celery.task(bind=True, name="tasks.translate_pdf")
def translate_pdf_task(self: Task, pdf_bytes: bytes) -> bytes:
    """
    Delegates the heavy lifting to process_pdf_bytes,
    but still updates task state.
    """
    try:
        # Optionally track start
        self.update_state(state="PROGRESS", meta={"stage":"start","progress":0})

        result = process_pdf_bytes(pdf_bytes)

        # Mark completion
        self.update_state(state="PROGRESS", meta={"stage":"complete","progress":100})
        return result

    except Exception:
        # Let FastAPI / get_task_status handle FAILURE state
        raise
