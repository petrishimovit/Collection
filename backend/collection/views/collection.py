from django.db.models import Count
from rest_framework import viewsets, permissions, response
from rest_framework.decorators import action

from collection.models import Collection
from collection.serializers.collection import CollectionSerializer


class CollectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    /api/collections/      -> all collections
    /api/collections/me/   -> only current user's collections
    """
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # все коллекции (например, публичные)
        return (
            Collection.objects
            .all()
            .annotate(items_count=Count("items"))
            .order_by("name")
        )

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """Return only current user's collections."""
        qs = (
            Collection.objects
            .filter(owner=request.user)
            .annotate(items_count=Count("items"))
            .order_by("name")
        )
        serializer = self.get_serializer(qs, many=True)
        return response.Response(serializer.data)
