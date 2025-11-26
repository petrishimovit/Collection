from django.db import models
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from apps.collection.models import Item
from apps.collection.serializers.item import ItemSerializer
from apps.collection.permissions.item import IsItemOwnerOrReadOnly
from apps.collection.selectors.item import (
    get_items_for_user,
    get_item_for_user,
)
from apps.collection.pagination import DefaultPageNumberPagination


class ItemViewSet(viewsets.ModelViewSet):
    
    serializer_class = ItemSerializer
    permission_classes = (IsItemOwnerOrReadOnly,)
    pagination_class = DefaultPageNumberPagination
    filter_backends = (OrderingFilter,)
    ordering_fields = ("created_at", "current_value")
    ordering = ("-created_at",)

    queryset = Item.objects.all().select_related("collection", "collection__owner")

    def get_queryset(self):
        qs = get_items_for_user(self.request.user)

        collection_id = self.request.query_params.get("collection")
        if collection_id:
            qs = qs.filter(collection_id=collection_id)

        qs = self.filter_queryset(qs)
        return qs

    def list(self, request, *args, **kwargs):
        
        queryset = self.get_queryset()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        
        instance = get_item_for_user(request.user, kwargs.get("pk"))
        if instance is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        
        collection = serializer.validated_data["collection"]
        user = self.request.user

        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentication required.")

        if collection.owner != user:
            raise PermissionDenied("You can only add items to your own collections.")

        serializer.save()

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request, *args, **kwargs):
        
        q = request.query_params.get("q", "").strip()
        qs = get_items_for_user(request.user)

        if q:
            qs = qs.filter(
                models.Q(name__icontains=q)
                | models.Q(description__icontains=q)
            )

        collection_id = request.query_params.get("collection")
        if collection_id:
            qs = qs.filter(collection_id=collection_id)

        qs = self.filter_queryset(qs)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
