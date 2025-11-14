from typing import Type
from django.db.models import QuerySet
from rest_framework import viewsets, permissions
from rest_framework.permissions import BasePermission
from rest_framework.serializers import Serializer
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied


from apps.collection.models import Item
from apps.collection.serializers.item import ItemSerializer
from apps.collection.permissions.item import IsItemOwnerOrReadOnly
from apps.collection.pagination import DefaultPageNumberPagination

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

@extend_schema_view(
    list=extend_schema(
        summary="List public items",
        description="Return all public items with related collection info.",
        responses={200: ItemSerializer},
    ),
    retrieve=extend_schema(
        summary="Retrieve an item",
        description="Get detailed info about a specific public item.",
        responses={200: ItemSerializer, 404: OpenApiResponse(description="Not found")},
    ),
    create=extend_schema(
        summary="Create an item",
        description="Create a new item in one of the user's own collections.",
        responses={201: ItemSerializer, 403: OpenApiResponse(description="Forbidden")},
    ),
    update=extend_schema(
        summary="Update an item",
        description="Update item data. Owner only.",
        responses={200: ItemSerializer, 403: OpenApiResponse(description="Forbidden")},
    ),
    partial_update=extend_schema(
        summary="Partially update an item",
        description="Partially update item fields. Owner only.",
        responses={200: ItemSerializer, 403: OpenApiResponse(description="Forbidden")},
    ),
    destroy=extend_schema(
        summary="Delete an item",
        description="Delete an item. Owner only.",
        responses={204: OpenApiResponse(description="Deleted"), 403: OpenApiResponse(description="Forbidden")},
    ),
)
class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing items (`Item`) within user collections.
    """

    serializer_class: Type[Serializer] = ItemSerializer
    permission_classes: list[type[BasePermission]] = [IsItemOwnerOrReadOnly]
    pagination_class = DefaultPageNumberPagination

    def get_queryset(self) -> QuerySet[Item]:
        if self.action in ("list", "retrieve"):
            return Item.objects.select_related("collection", "collection__owner").order_by("name", "id")

        if not self.request.user.is_authenticated:
            return Item.objects.none()

        return (
            Item.objects
            .select_related("collection", "collection__owner")
            .filter(collection__owner=self.request.user)
            .order_by("name", "id")
        )

    def get_permissions(self):
        if self.action in ("list", "retrieve"): 
            return [permissions.AllowAny()]
        return [perm() for perm in self.permission_classes]

    def perform_create(self, serializer) -> None:
        collection = serializer.validated_data.get("collection")

        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication required.")

        if collection.owner != self.request.user:
            raise PermissionDenied("You can add items only to your own collections.")

        serializer.save()

    def destroy(self, request, *args, **kwargs) -> Response:
        return super().destroy(request, *args, **kwargs)
