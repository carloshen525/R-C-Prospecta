from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery = Celery(
    "prospect_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.campaign_tasks",
        "app.tasks.extraction_tasks",
        "app.tasks.ai_tasks",
        "app.tasks.scheduler_tasks"
    ]
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.TIMEZONE,
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        # Verifica a fila de mensagens a cada 1 minuto (respeitando o horário das 07:00 às 18:30)
        "process-pending-campaign-queue": {
            "task": "app.tasks.campaign_tasks.dispatch_scheduled_campaign_messages",
            "schedule": 60.0,
        },
        # Monitora a abertura e fechamento de horário e limites
        "check-business-hours-and-daily-reset": {
            "task": "app.tasks.scheduler_tasks.monitor_daily_cycle",
            "schedule": 300.0,
        }
    }
)
