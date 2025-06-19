import logging.config
import yaml

with open("logging.yaml") as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)

from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from celery.result import AsyncResult
from app.tasks.celery_app import celery
from app.tasks.tasks import translate_pdf_task
import io
from typing import Dict, Any

app = FastAPI()

@app.post("/translate")
async def create_translation_task(file: UploadFile):
    """Initiate PDF translation and return task ID"""
    try:
        pdf_bytes = await file.read()
        task = translate_pdf_task.delay(pdf_bytes)
        return JSONResponse({ "task_id": task.id, "status_url": f"/tasks/{task.id}", "message": "Translation started" })
    except Exception as e:
        logging.exception("Failed to start translation")
        raise HTTPException(status_code=500, detail="Failed to initiate translation")

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = AsyncResult(task_id, app=translate_pdf_task.app)
    # base payload
    response = {
        "task_id": task_id,
        "state": task.state,
        "progress": 0
    }

    if task.state == "PENDING":
        # still queued
        return JSONResponse(status_code=202, content=response)

    if task.state == "PROGRESS":
        info = task.info or {}
        response["progress"] = info.get("progress", 0)
        return JSONResponse(status_code=202, content=response)

    if task.state == "SUCCESS":
        return JSONResponse(status_code=200, content={
            **response,
            "result_url": f"/results/{task_id}"
        })

    # FAILURE or other unexpected states
    info = task.info or {}
    error_msg = info.get("error", "An unexpected error occurred")
    return JSONResponse(status_code=500, content={
        **response,
        "error": error_msg
    })

@app.get("/tasks/{task_id}/download")
async def download_translated_pdf(task_id: str):
    """Download large result files"""
    task = AsyncResult(task_id, app=celery)
    if not task.successful():
        raise HTTPException(status_code=404, detail="Result not available")
    
    return StreamingResponse(
        io.BytesIO(task.result),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=translated.pdf"}
    )