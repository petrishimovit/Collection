from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.notifications.models import Notification


class NotificationService:
    """Notification domain service."""

    @transaction.atomic
    def create(self, *, for_user, type: str) -> Notification:
        """Create a notification for a user."""
        return Notification.objects.create(
            for_user=for_user,
            type=type,
        )

    @transaction.atomic
    def check_all(self, *, for_user) -> int:
        """Mark all user notifications as checked."""
        return Notification.objects.filter(
            for_user=for_user,
            is_checked=False,
        ).update(
            is_checked=True,
            updated_at=timezone.now(),
        )
