import os
from celery import Celery
import logging.config
import yaml
from logging import getLogger

# Load logging configuration early (before Celery starts)
with open("logging.yaml") as f:
    logging_config = yaml.safe_load(f)
    logging.config.dictConfig(logging_config)

logger = getLogger(__name__)  # Get logger for this module

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Initialize Celery
celery = Celery(
    "translateOCR",
    broker=redis_url,
    backend=redis_url,
)

# Celery Configuration
celery.conf.update(
    task_track_started=True,  # Useful for tracking task progress
    worker_max_tasks_per_child=10,  # Helps prevent memory leaks
    task_serializer="json",
    result_serializer="json",  # Explicitly set result serializer
    accept_content=["json"],  # Only allow JSON messages
    broker_connection_retry_on_startup=True,  # Avoid startup connection errors
    task_default_queue="default",  # Explicit default queue
)

# Log Celery initialization
logger.info("Celery app configured with broker: %s", redis_url)