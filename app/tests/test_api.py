import io
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_translate_endpoint():
    sample_pdf = io.BytesIO(b"%PDF-1.4...")  # minimal valid PDF bytes
    async with AsyncClient(app=app, base_url="http://test") as ac:
        files = {"file": ("test.pdf", sample_pdf, "application/pdf")}
        r = await ac.post("/translate", files=files)
    assert r.status_code == 200
    assert "task_id" in r.json()
