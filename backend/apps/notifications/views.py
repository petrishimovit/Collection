from __future__ import annotations

from rest_framework import mixins, permissions, response, status, viewsets
from rest_framework.decorators import action
from drf_spectacular.utils import OpenApiParameter, extend_schema

from apps.notifications.models import Notification
from apps.notifications.serializer import NotificationSerializer
from apps.notifications.services import NotificationService
from apps.notifications.pagination import NotificationPagination

class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Notifications viewset"""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination

    @extend_schema(
        summary="List notifications",
        parameters=[
            OpenApiParameter(
                name="is_checked",
                type=bool,
                required=False,
            ),
        ],
        tags=["Notifications"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        qs = Notification.objects.filter(
            for_user=self.request.user,
        ).order_by("-created_at")

        raw = self.request.query_params.get("is_checked", "false").lower()

        if raw in {"1", "true"}:
            return qs.filter(is_checked=True)

        return qs.filter(is_checked=False)

    @extend_schema(
        summary="Mark all notifications as checked",
        responses={200: {"type": "object", "properties": {"updated": {"type": "integer"}}}},
        tags=["Notifications"]
    )
    @action(detail=False, methods=["post"], url_path="check-all")
    def check_all(self, request):
        """Mark all notifications as checked."""
        service = NotificationService()
        updated = service.check_all(for_user=request.user)
        return response.Response(
            {"updated": updated},
            status=status.HTTP_200_OK,
        )
