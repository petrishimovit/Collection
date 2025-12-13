from __future__ import annotations

from pathlib import Path

from django.apps import AppConfig
from django.conf import settings

from .services.registry import REGISTRY


class GamesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.games"
    label = "games"

    def ready(self):
        if getattr(settings, "GAMES_DB_AUTOLOAD", True):
            db_dir = Path(
                getattr(settings, "GAMES_DB_DIR", Path(__file__).resolve().parent / "gamesdb")
            )
            REGISTRY.load_from_dir(db_dir)
