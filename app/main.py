from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse
from app.pipeline import process_pdf_bytes
import io

app = FastAPI()

@app.post("/translate")
async def translate_pdf(file: UploadFile):
    pdf_bytes = await file.read()
    result_bytes = process_pdf_bytes(pdf_bytes)
    return StreamingResponse(io.BytesIO(result_bytes), media_type="application/pdf")