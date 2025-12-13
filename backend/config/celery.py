import os
from pathlib import Path

from celery import Celery
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("server")


app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.broker_url = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
app.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1")

app.conf.beat_scheduler = os.getenv(
    "CELERY_BEAT_SCHEDULER",
    "django_celery_beat.schedulers:DatabaseScheduler",
)

app.conf.update(
    timezone=os.getenv("TZ", os.getenv("CELERY_TIMEZONE", "Europe/Saratov")),
    enable_utc=os.getenv("CELERY_ENABLE_UTC", "1") == "1",
    task_track_started=True,
    task_time_limit=int(os.getenv("CELERY_TASK_TIME_LIMIT", str(30 * 60))),
)

app.autodiscover_tasks()
