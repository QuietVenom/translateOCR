# Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system libs for pdf2image, EasyOCR, OpenCV
RUN apt-get update && apt-get install -y \
      poppler-utils \
      tesseract-ocr \
      libgl1 \
      libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy project descriptors first (for caching)
COPY pyproject.toml ./

# Install Python deps
RUN pip install --upgrade pip \
 && pip install --no-cache-dir .

# Copy the rest of your code
COPY . .

# Expose API port
EXPOSE 8000

# Default start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
