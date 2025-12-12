from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.notifications.models import Notification


class NotificationService:
    """Notification domain service."""

    @transaction.atomic
    def create(self, *, for_user, type: str, info: dict | None = None) -> Notification:
        """Create a notification for a user."""
        return Notification.objects.create(
            for_user=for_user,
            type=type,
            info=info or {},
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
    
    @transaction.atomic
    def create_follow(self, *, target_user, follower_user) -> Notification:
        """Create a follow notification for target user."""
        return self.create(
            for_user=target_user,
            type=Notification.Type.FOLLOW,
            info={"user_id": str(follower_user.pk)},
        )
