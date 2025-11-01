from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import List, Optional

from django.core.cache import cache
from django.utils import timezone

from ..integrations.pricecharting.client import PricechartingClient
from ..integrations.pricecharting.schemas import SearchItem
from ..integrations.pricecharting.types import Region


class PricechartingService:
    SEARCH_TTL = 60
    DETAILS_TTL = 60 * 10
    LOCK_TTL = 15

    @staticmethod
    def _cache_key(prefix: str, payload: dict) -> str:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return f"pc:{prefix}:{hashlib.md5(raw.encode()).hexdigest()}"

    @classmethod
    def search_items(cls, *, q: str, region: Region = "all", limit: int = 10) -> List[dict]:
        key = cls._cache_key("search", {"q": q.strip(), "region": region, "limit": limit})
        cached = cache.get(key)
        if cached is not None:
            return cached

        lock_key = key + ":lock"
        got_lock = cache.add(lock_key, timezone.now().isoformat(), timeout=cls.LOCK_TTL)
        try:
            if not got_lock:
                cached_wait = cache.get(key)
                if cached_wait is not None:
                    return cached_wait

            items: List[SearchItem] = PricechartingClient.search(q=q, region=region, limit=limit)
            result = [asdict(i) for i in items]
            cache.set(key, result, timeout=cls.SEARCH_TTL)
            return result
        finally:
            if got_lock:
                cache.delete(lock_key)

    @classmethod
    def get_item_details(cls, *, url: Optional[str] = None, slug: Optional[str] = None) -> dict:
        token = url or slug or ""
        if not token:
            return {}

        key = cls._cache_key("details", {"token": token})
        cached = cache.get(key)
        if cached is not None:
            return cached

        lock_key = key + ":lock"
        got_lock = cache.add(lock_key, timezone.now().isoformat(), timeout=cls.LOCK_TTL)
        try:
            if not got_lock:
                cached_wait = cache.get(key)
                if cached_wait is not None:
                    return cached_wait

            data = PricechartingClient.item_details(token)
            prices = data.get("prices") or {}
            payload = {
                "title": data.get("title", ""),
                "platform": data.get("platform", ""),
                "region": data.get("region", "all"),
                "url": data.get("url", ""),
                "slug": data.get("slug", ""),
                "prices": {
                    "loose": prices.get("loose"),
                    "cib": prices.get("cib"),
                    "new": prices.get("new"),
                    "graded": prices.get("graded"),
                    "box_only": prices.get("box_only"),
                    "manual_only": prices.get("manual_only"),
                },
            }
            cache.set(key, payload, timeout=cls.DETAILS_TTL)
            return payload
        finally:
            if got_lock:
                cache.delete(lock_key)
