from __future__ import annotations

from rest_framework import mixins, permissions, response, status, viewsets
from rest_framework.decorators import action

from apps.notifications.models import Notification
from apps.notifications.serializer import NotificationSerializer
from apps.notifications.services import NotificationService


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Notifications API: list and bulk check."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.filter(
            for_user=self.request.user
        ).order_by("-created_at")

        raw = self.request.query_params.get("is_checked")
        if raw is None:
            return qs

        val = raw.lower()
        if val in {"1", "true"}:
            return qs.filter(is_checked=True)
        if val in {"0", "false"}:
            return qs.filter(is_checked=False)

        return qs

    @action(detail=False, methods=["post"], url_path="check-all")
    def check_all(self, request):
        """Mark all notifications as checked."""
        service = NotificationService()
        updated = service.check_all(for_user=request.user)
        return response.Response(
            {"updated": updated},
            status=status.HTTP_200_OK,
        )
