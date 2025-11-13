# apps/games/services/pricecharting.py
from __future__ import annotations
from urllib.parse import urlparse
from typing import List, Optional
from dataclasses import asdict
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from ..integrations.pricecharting.client import PricechartingClient
from ..integrations.pricecharting.schemas import SearchItem
from ..integrations.pricecharting.types import Region
from ..models import PriceChartingConnect


class PricechartingService:

    @staticmethod
    def _norm_url(url: str) -> str:
        
        p = urlparse((url or "").strip())
        if not p.scheme or not p.netloc:
            return ""
        return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/")

  

    @classmethod
    def search_items(cls, *, q: str, region: Region = "all", limit: int = 10) -> List[dict]:
        
        items: List[SearchItem] = PricechartingClient.search(q=q, region=region, limit=limit)
        return [asdict(i) for i in items]

    @classmethod
    def get_item_details(cls, *, url: Optional[str] = None, slug: Optional[str] = None) -> dict:
        
        token = url or slug or ""
        if not token:
            return {}
        data = PricechartingClient.item_details(token)
        return {
            "title": data.get("title", ""),
            "platform": data.get("platform", ""),
            "region": data.get("region", "all"),
            "url": data.get("url", ""),
            "slug": data.get("slug", ""),
            "prices": data.get("prices") or {},
        }

    @classmethod
    @transaction.atomic
    def upsert_connect(cls, *, url: str) -> Optional[PriceChartingConnect]:
        
        norm = cls._norm_url(url)
        if not norm:
            return None

        obj, created = PriceChartingConnect.objects.get_or_create(url=norm)
        if created or not obj.current:
            data = cls.get_item_details(url=norm)
            obj.current = data
            obj.last_synced_at = None
            obj.save(update_fields=["current", "last_synced_at", "updated_at"])
        return obj

    @classmethod
    @transaction.atomic
    def bind_item(cls, *, item, url: str) -> Optional[PriceChartingConnect]:
        
        obj = cls.upsert_connect(url=url)
        if not obj:
            return None
        if item.pricecharting_id != obj.id:
            item.pricecharting = obj
            item.save(update_fields=["pricecharting"])
        return obj

    @staticmethod
    def unbind_item(item):
        
        item.pricecharting = None
        item.save(update_fields=["pricecharting"])

    @staticmethod
    def public_qs():
        
        return (
            PriceChartingConnect.objects
            .annotate(items_count=Count("items"))
            .order_by("-created_at")
            .distinct()
        )
    

    @classmethod
    @transaction.atomic
    def snapshot_prices(cls, *, connect: PriceChartingConnect, token: Optional[str] = None) -> dict:
        
        token = token or connect.url or (connect.current or {}).get("slug") or ""
        if not token:
            return {}

        data = PricechartingClient.item_details(token)
        prices = data.get("prices") or {}
        now = timezone.now()
        date_key = now.date().isoformat()  # "YYYY-MM-DD"

        
        connect.current = {
            "title": data.get("title", ""),
            "platform": data.get("platform", ""),
            "region": data.get("region", "all"),
            "url": data.get("url", ""),
            "slug": data.get("slug", ""),
            "prices": prices,
        }
        connect.last_synced_at = now

        
        hist = connect.history or {}
        if isinstance(hist, list):
            
            migrated = {}
            for i, entry in enumerate(hist, start=1):
                if isinstance(entry, dict):
                 
                    at = entry.get("at") or entry.get("date")
                    p = entry.get("prices") or {}
                    key = (at[:10] if isinstance(at, str) and len(at) >= 10 else f"_old_{i}")
                    migrated[key] = p
                else:
                    migrated[f"_old_{i}"] = entry
            hist = migrated

        
        hist[date_key] = prices

        connect.history = hist
        connect.save(update_fields=["current", "history", "last_synced_at", "updated_at"])

        return {"date": date_key, "prices": prices}
