"""
Configuration de Celery pour les tâches asynchrones.
"""
from celery import Celery

from app.config import settings

celery_app = Celery(
    "gestion_clinique",
    broker=settings.celery_broker_url,
    backend=settings.redis_url,
    include=[
        # Les modules de tâches seront ajoutés au fur et à mesure
        # "app.core.notifications.tasks",
        # "app.modules.rendez_vous.tasks",
        # "app.modules.facturation.tasks",
    ],
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Routes des tâches
celery_app.conf.task_routes = {
    "app.core.notifications.tasks.*": {"queue": "notifications"},
    "app.modules.rendez_vous.tasks.*": {"queue": "appointments"},
    "app.modules.facturation.tasks.*": {"queue": "billing"},
}

# Tâches périodiques (beat)
# À activer quand les tâches seront implémentées
# celery_app.conf.beat_schedule = {
#     "check-upcoming-appointments": {
#         "task": "app.modules.rendez_vous.tasks.send_appointment_reminders",
#         "schedule": 300.0,  # Toutes les 5 minutes
#     },
#     "process-pending-invoices": {
#         "task": "app.modules.facturation.tasks.process_pending_invoices",
#         "schedule": 3600.0,  # Toutes les heures
#     },
# }
