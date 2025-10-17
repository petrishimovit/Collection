# collecting/views/collection.py
from django.db.models import Count
from rest_framework import viewsets, permissions, response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from collection.models import Collection
from collection.serializers.collection import CollectionSerializer
from collection.pagination import DefaultPageNumberPagination


class CollectionViewSet(viewsets.ModelViewSet):
    """
        GET /api/collections/      -> all collections (read)
        POST /api/collections/{id}/ -> collection by id (read)
        GET /api/collections/me/   -> only current user's collections (read)
        PUT /api/collections/{id}/ -> collection by id (update)
        PATCH /api/collections/{id}/ -> collection by id (update)
        DELETE /api/collections/{id}/ -> collection by id (delete)
    """
    serializer_class = CollectionSerializer
    pagination_class = DefaultPageNumberPagination

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

   
    def get_queryset(self):
        """
        PUT/PATCH/DELETE -> check owner/check auth
        GET/POST -> allow any
        """
        if self.action in ("list", "retrieve"):
            return (
                Collection.objects
                .all()
                .annotate(items_count=Count("items"))
                .order_by("name", "id")
            )
      
        return (
            Collection.objects
            .filter(owner=self.request.user)
            .annotate(items_count=Count("items"))
            .order_by("name", "id")
        )

  
    @action(detail=False, methods=["get"], url_path="me", pagination_class=DefaultPageNumberPagination,
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request):

        qs = (
            Collection.objects
            .filter(owner=request.user)
            .annotate(items_count=Count("items"))
            .order_by("name", "id")
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(qs, many=True)
        return response.Response(ser.data)

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication required.")
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        obj = self.get_object()
        if obj.owner_id != self.request.user.id:
            raise PermissionDenied("You can update only your collections.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.owner_id != self.request.user.id:
            raise PermissionDenied("You can delete only your collections.")
        instance.delete()
