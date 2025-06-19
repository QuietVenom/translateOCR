# tests/conftest.py
import os
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "True")
os.environ.setdefault("CELERY_TASK_EAGER_PROPAGATES_EXCEPTIONS", "True")

# provide a dummy key so translator.py can import without error
os.environ.setdefault("OPENAI_API_KEY", "test")