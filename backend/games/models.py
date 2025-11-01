# apps/games/models/pricecharting_integration.py
from __future__ import annotations
from urllib.parse import urlparse
from django.db import models
from django.utils import timezone
from core.models import BaseModel


def normalize_url(url: str) -> str:
    p = urlparse((url or "").strip())
    if not p.scheme or not p.netloc:
        return ""
    return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/")


class PricechartingIntegration(BaseModel):
    """
    Shared integration record for PriceCharting.
    One URL -> Many Items.
    """

    url = models.URLField(unique=True)
    current = models.JSONField(default=dict, blank=True)
    history = models.JSONField(default=list, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "PriceCharting Integration"
        verbose_name_plural = "PriceCharting Integrations"
        indexes = [
            models.Index(fields=["url"]),
        ]

    def append_daily_point(self, *, date=None, prices=None, currency="USD") -> bool:
        d = (date or timezone.now().date()).isoformat()
        hist = list(self.history or [])
        for row in hist:
            if row.get("date") == d:
                if prices and row.get("prices") != prices:
                    row["prices"] = prices
                    row["currency"] = currency
                    self.history = hist
                    self.save(update_fields=["history", "updated_at"])
                    return True
                return False
        hist.append({"date": d, "prices": prices or {}, "currency": currency})
        self.history = hist
        self.save(update_fields=["history", "updated_at"])
        return True

    def __str__(self):
        return f"{self.url}"
