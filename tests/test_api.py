# tests/test_api.py

import io
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_translate_endpoint():
    sample_pdf = io.BytesIO(b"%PDF-1.4...")  # minimal PDF stub
    files = {"file": ("test.pdf", sample_pdf, "application/pdf")}
    response = client.post("/translate", files=files)
    assert response.status_code == 200
    payload = response.json()
    assert "task_id" in payload
    assert payload["status_url"].startswith("/tasks/")
