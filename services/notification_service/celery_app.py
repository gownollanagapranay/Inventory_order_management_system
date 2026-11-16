import os
from celery import Celery

# Read Redis configuration from environment variables
REDIS_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    "redis://localhost:6379/0"
)

REDIS_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND",
    "redis://localhost:6379/1"
)

celery_app = Celery(
    "notification_service",
    broker=REDIS_BROKER_URL,
    backend=REDIS_RESULT_BACKEND,
    include=["services.notification_service.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=False
)
