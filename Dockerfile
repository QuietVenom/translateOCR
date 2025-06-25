# Use NVIDIA’s CUDA runtime image
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# 1) Install system dependencies
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      python3.13 python3-pip python3-distutils \
      poppler-utils \
      tesseract-ocr \
      libgl1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# 2) Symlink python3.13 -> python and pip3 -> pip
RUN ln -s /usr/bin/python3.13 /usr/bin/python \
 && ln -s /usr/bin/pip3 /usr/bin/pip

WORKDIR /app

# 3) Copy your project’s pyproject.toml (or requirements.txt)
COPY pyproject.toml ./

# 4) Install Python deps:
#    - First, get a CUDA-enabled PyTorch build
#    - Then install the rest of your app (including easyocr)
RUN pip install --upgrade pip \
 && pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu118 \
 && pip install --no-cache-dir .

# 5) Pre-download EasyOCR models with GPU enabled
RUN python - <<EOF
import easyocr
_ = easyocr.Reader(['en'], gpu=True)
EOF

# 6) Copy in your application code
COPY . .

# 7) Expose and run
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
