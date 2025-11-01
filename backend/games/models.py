from __future__ import annotations
from urllib.parse import urlparse
from django.db import models
from django.utils import timezone
from core.models import BaseModel
from django.core.serializers.json import DjangoJSONEncoder


def normalize_url(url: str) -> str:
    p = urlparse((url or "").strip())
    if not p.scheme or not p.netloc:
        return ""
    return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/")


class PriceChartingConnect(BaseModel):
    

    url = models.URLField(unique=True)
    current = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)
    history = models.JSONField(default=list, blank=True, encoder=DjangoJSONEncoder)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        verbose_name = "PriceCharting Connect"
        verbose_name_plural = "PriceCharting Connects"
        indexes = [models.Index(fields=["url"])]

    def __str__(self):
        return self.url
