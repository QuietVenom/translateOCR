from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from celery.result import AsyncResult
from app.tasks.celery_app import celery
from app.tasks.tasks import translate_pdf_task
import io
from typing import Dict, Any

app = FastAPI()

@app.post("/translate")
async def create_translation_task(file: UploadFile) -> Dict[str, Any]:
    """Initiate PDF translation and return task ID"""
    try:
        pdf_bytes = await file.read()
        task = translate_pdf_task.delay(pdf_bytes)
        return JSONResponse({
            "task_id": task.id,
            "status_url": f"/tasks/{task.id}",
            "message": "Translation started"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Check translation task status and get results when complete"""
    task = AsyncResult(task_id, app=celery)
    
    response = {
        "task_id": task_id,
        "status": task.state,
    }
    
    if task.state == 'PROGRESS':
        response.update({
            "progress": task.info.get('progress', 0),
            "stage": task.info.get('stage', 'unknown'),
            "details": task.info.get('details', '')
        })
    elif task.state == 'SUCCESS':
        # For small results, return directly
        if isinstance(task.result, bytes) and len(task.result) < 1_000_000:  # 1MB limit
            return StreamingResponse(
                io.BytesIO(task.result),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=translated.pdf",
                    "X-Task-Status": "complete"
                }
            )
        else:
            response.update({
                "download_url": f"/tasks/{task_id}/download",
                "message": "Translation complete"
            })
    elif task.state == 'FAILURE':
        response.update({
            "error": task.info.get('error', 'Unknown error'),
            "progress": task.info.get('progress', 0),
            "failed_stage": task.info.get('stage', 'unknown')
        })
        raise HTTPException(status_code=500, detail=response)
    
    return JSONResponse(response)

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