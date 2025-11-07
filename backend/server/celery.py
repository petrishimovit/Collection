import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

app = Celery("server")


app.config_from_object("django.conf:settings", namespace="CELERY")


app.conf.broker_url = "redis://127.0.0.1:6379/0"

app.conf.result_backend = "redis://localhost:6379/1"


app.conf.beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"


app.conf.update(
    timezone="Europe/Saratov",
    enable_utc=True,           
    task_track_started=True,
    task_time_limit=30 * 60,
)

app.autodiscover_tasks()