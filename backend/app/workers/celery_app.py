from celery import Celery

from app.config import settings

celery_app = Celery(
    "tdlweb",
    broker=settings.redis_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks.tdl_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    task_time_limit=settings.celery_task_time_limit,
)
