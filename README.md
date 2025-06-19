# QuietVenom TranslateOCR

A Dockerized FastAPI service that accepts PDFs, performs OCR on each page using EasyOCR, translates extracted text with OpenAI API, and re-renders a translated PDF. Orchestrated with Celery and Redis, complete with CI testing.

## Features

- **OCR**: Converts PDF pages to images and extracts text using EasyOCR with lazy initialization per worker.
- **Translation**: Uses OpenAI API to translate extracted text via a background Celery task.
- **PDF Rendering**: Renders translated text back onto PDF pages.
- **Asynchronous Processing**: Task queue powered by Celery + Redis, configurable worker concurrency.
- **Dockerized**: Run the entire stack (API + worker + Redis) via Docker Compose.
- **CI Pipeline**: GitHub Actions workflow for linting and testing with pytest in eager Celery mode.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Environment Variables](#environment-variables)
4. [Running Locally with Docker Compose](#running-locally-with-docker-compose)
5. [API Endpoints](#api-endpoints)
6. [Testing](#testing)
7. [Continuous Integration](#continuous-integration)
8. [License](#license)

## Prerequisites

- Docker >= 20.10
- Docker Compose >= 1.29 (or Docker Compose V2)
- Make sure ports `8000` (API) and `6379` (Redis) are available

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/quietvenom-translateocr.git
   cd quietvenom-translateocr
   ```
2. **Copy and fill your environment file**:
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

## Environment Variables

Copy `.env.example` to `.env` and set the following:

```dotenv
REDIS_URL=redis://redis:6379/0
OPENAI_API_KEY=your_openai_api_key_here
FONT_PATH=./app/assets/fonts/DejaVuSans-Bold.ttf
CELERY_WORKER_CONCURRENCY=4        # Number of Celery workers and OCR processes
```

## Running Locally with Docker Compose

Start the full stack (API, worker, Redis):

```bash
docker-compose up --build
```

- **API**: [http://localhost:8000](http://localhost:8000)
- **Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

To run only the API (no worker):

```bash
docker-compose up --build web
```

## API Endpoints

### POST `/translate`

- **Description**: Upload a PDF to start a translation job.
- **Request**: Multipart form with field `file`.
- **Response**:
  ```json
  {
    "task_id": "<uuid>",
    "status_url": "/tasks/<task_id>",
    "message": "Translation started"
  }
  ```

### GET `/tasks/{task_id}`

- **Description**: Check status of a translation job.
- **Response** (202 Pending/Progress):
  ```json
  {
    "task_id": "<uuid>",
    "state": "PENDING|PROGRESS",
    "progress": 0
  }
  ```
- **Response** (200 Success):
  ```json
  {
    "task_id": "<uuid>",
    "state": "SUCCESS",
    "progress": 100,
    "result_url": "/results/<task_id>"
  }
  ```
- **Response** (500 Failure):
  ```json
  {
    "task_id": "<uuid>",
    "state": "FAILURE",
    "progress": 0,
    "error": "<message>"
  }
  ```

### GET `/tasks/{task_id}/download`

- **Description**: Download the translated PDF result for a completed task.
- **Response**: Returns the translated PDF file with `Content-Type: application/pdf`.

## Testing

Run tests locally (requires Python 3.13 and dependencies installed):

```bash
pip install .
pip install pytest httpx pytest-asyncio
pytest
```

## Continuous Integration

Configured via GitHub Actions in `.github/workflows/ci.yml`. Key steps:

- Checkout code
- Setup Python 3.13
- Install application (`pip install .`)
- Install test deps (`pytest`, `httpx`, `pytest-asyncio`)
- Configure Celery for eager mode
- Run `pytest`

## License

MIT License. See [LICENSE](LICENSE) for details.

