"""Celery application configuration — Redis as broker (no RabbitMQ)."""
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "agent_engine",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    broker_transport_options={
        "visibility_timeout": 3600,
        "fanout_prefix": True,
        "fanout_patterns": True,
    },
    task_routes={
        "app.tasks.document_tasks.*": {"queue": "document"},
        "app.tasks.model_tasks.*": {"queue": "model"},
        "app.tasks.cleanup_tasks.*": {"queue": "cleanup"},
        "app.tasks.marketplace_tasks.*": {"queue": "cleanup"},
    },
    task_default_queue="default",
    beat_schedule={
        "cleanup-expired-memory": {
            "task": "app.tasks.cleanup_tasks.cleanup_expired_memory",
            "schedule": 3600.0,
        },
        "cleanup-temp-files": {
            "task": "app.tasks.cleanup_tasks.cleanup_temp_files",
            "schedule": 7200.0,
        },
        "check-model-health": {
            "task": "app.tasks.model_tasks.check_model_health",
            "schedule": 300.0,
        },
        "aggregate-usage-daily": {
            "task": "app.tasks.model_tasks.aggregate_usage_daily",
            "schedule": 86400.0,
        },
        "marketplace-cleanup-bottom-performers": {
            "task": "app.tasks.marketplace_tasks.cleanup_bottom_performers",
            "schedule": crontab(hour=2, minute=0),
        },
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
