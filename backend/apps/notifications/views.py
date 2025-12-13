from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, permissions, response, status, viewsets
from rest_framework.decorators import action

from apps.notifications.models import Notification
from apps.notifications.pagination import NotificationPagination
from apps.notifications.serializer import NotificationSerializer
from apps.notifications.services import NotificationService


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Notifications viewset"""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination

    @extend_schema(
        summary="List notifications",
        description=(
            "Returns notifications for current user.\n\n"
            "Available filters:\n"
            "- `is_checked`: true | false (default: false)\n"
            "- `types`: comma-separated list of notification types\n\n"
            "Allowed types:\n"
            "- follow\n"
            "- post\n"
            "- comment_create\n"
            "- item_create\n"
        ),
        parameters=[
            OpenApiParameter(
                name="is_checked",
                type=bool,
                required=False,
                description="Filter by checked status",
            ),
            OpenApiParameter(
                name="types",
                type=str,
                required=False,
                description="Comma-separated notification types",
                enum=[choice for choice, _ in Notification.Type.choices],
            ),
        ],
        tags=["Notifications"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        qs = Notification.objects.filter(
            for_user=self.request.user,
        ).order_by("-created_at")

        raw_checked = self.request.query_params.get("is_checked", "false").lower()
        if raw_checked in {"1", "true"}:
            qs = qs.filter(is_checked=True)
        else:
            qs = qs.filter(is_checked=False)

        raw_types = self.request.query_params.get("types", "").strip()
        if raw_types:
            types = [t.strip() for t in raw_types.split(",") if t.strip()]
            qs = qs.filter(type__in=types)

        return qs

    @extend_schema(
        summary="Mark all notifications as checked",
        description="Marks all unread notifications for current user as checked.",
        responses={200: {"type": "object", "properties": {"updated": {"type": "integer"}}}},
        tags=["Notifications"],
    )
    @action(detail=False, methods=["post"], url_path="check-all")
    def check_all(self, request):
        service = NotificationService()
        updated = service.check_all(for_user=request.user)
        return response.Response({"updated": updated}, status=status.HTTP_200_OK)
