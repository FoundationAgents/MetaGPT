# celery_app.py
from celery import Celery

celery_app = Celery(
    "spo_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=3600,
)

# Enable Celery to automatically scan the task module
celery_app.autodiscover_tasks(['metagpt.ext.spo_api_backend'])
