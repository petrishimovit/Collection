from __future__ import annotations
from celery import shared_task
from django.utils import timezone
from django.db import transaction

from apps.games.models import PriceChartingConnect
from apps.games.services.pricecharting import PricechartingService


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def update_all_pricecharting() -> dict:
    """
    celery task for update all games in pricecharting
    """
    
    total = 0
    ok = 0
    failed = 0
    failed_ids = []

    today = timezone.now().date().isoformat()

    qs = (
        PriceChartingConnect.objects
        .all()
        .only("id", "url", "current", "history", "last_synced_at")
    )

    for connect in qs.iterator():
        total += 1
        try:
            PricechartingService.snapshot_prices(connect=connect)
            ok += 1
        except Exception as e:
            failed += 1
            failed_ids.append(connect.id)

          
            try:
                with transaction.atomic():
                    connect.refresh_from_db(fields=["history"])
                    hist = connect.history or {}
                    hist[today] = {"_error": str(e)[:500]}  
                    connect.history = hist
                    connect.last_synced_at = timezone.now()
                    connect.save(update_fields=["history", "last_synced_at", "updated_at"])
            except Exception:
                
                pass

    return {"total": total, "ok": ok, "failed": failed, "failed_ids": failed_ids}
