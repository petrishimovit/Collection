from __future__ import annotations

from urllib.parse import urlparse

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from core.models import BaseModel


def normalize_url(url: str) -> str:
    """
    normalize external url for consistent storage/comparison.
    """
    p = urlparse((url or "").strip())
    if not p.scheme or not p.netloc:
        return ""
    return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/")


class PriceChartingConnect(BaseModel):
    """
    link between a local Item and a pricecharting game entry.
    """

    url = models.URLField(unique=True)
    current = models.JSONField(
        default=dict,
        blank=True,
        encoder=DjangoJSONEncoder,
        help_text="Latest snapshot fetched from PriceCharting.",
    )
    history = models.JSONField(
        default=dict,
        blank=True,
        encoder=DjangoJSONEncoder,
        help_text="Historical price snapshots keyed by date (YYYY-MM-DD).",
    )
    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When data was last synced from PriceCharting.",
    )

    class Meta(BaseModel.Meta):
        verbose_name = "PriceCharting Connect"
        verbose_name_plural = "PriceCharting Connects"
        indexes = [
            models.Index(fields=["url"]),
        ]

    def __str__(self) -> str:
        return self.url

    @property
    def title(self) -> str:
        """
        Shortcut for current['title'].

        Returns empty string if current snapshot is missing or invalid.
        """
        return (self.current or {}).get("title") or ""

    @property
    def platform(self) -> str:
        """Shortcut for current['platform']."""
        return (self.current or {}).get("platform") or ""

    @property
    def region(self) -> str:
        """Shortcut for current['region'], defaulting to 'all'."""
        return (self.current or {}).get("region") or "all"

    @property
    def prices(self) -> dict:
        """
        Shortcut for current
        """
        return (self.current or {}).get("prices") or {}
