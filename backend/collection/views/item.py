from typing import Type
from django.db.models import QuerySet
from rest_framework import viewsets, permissions
from rest_framework.permissions import BasePermission
from rest_framework.serializers import Serializer
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from collection.models import Item
from collection.serializers.item import ItemSerializer
from collection.permissions.item import IsItemOwnerOrReadOnly
from collection.pagination import DefaultPageNumberPagination


class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing items (`Item`) within user collections.

    Provides standard CRUD operations for the `Item` model:
      - **GET /api/items/** — list all items (public)
      - **GET /api/items/{id}/** — retrieve a single item
      - **POST /api/items/** — create a new item (only collection owner)
      - **PUT /api/items/{id}/** — fully update an item (only collection owner)
      - **PATCH /api/items/{id}/** — partially update an item (only collection owner)
      - **DELETE /api/items/{id}/** — delete an item (only collection owner)

    Access control:
      - Read operations (GET) are public.
      - Write operations (POST/PUT/PATCH/DELETE) are restricted to the
        owner of the item's collection.
    """

    serializer_class: Type[Serializer] = ItemSerializer
    permission_classes: list[type[BasePermission]] = [IsItemOwnerOrReadOnly]
    pagination_class = DefaultPageNumberPagination

    def get_queryset(self) -> QuerySet[Item]:
        """
        Return a queryset based on the current action.

        For public actions (`list`, `retrieve`), return all items.
        For write actions, return only items belonging to collections
        owned by the authenticated user.

        Returns:
            QuerySet[Item]: A filtered queryset of items.
        """
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
        """
        Return a list of permission instances depending on the current action.

        - For read actions (`list`, `retrieve`), anonymous access is allowed.
        - For write actions, ownership is verified through
          :class:`IsItemOwnerOrReadOnly`.
        """
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [perm() for perm in self.permission_classes]

    def perform_create(self, serializer) -> None:
        """
        Ensure that items can only be created in collections
        owned by the authenticated user.

        Raises:
            PermissionDenied: If the user tries to add an item
                              to someone else's collection.
        """
        collection = serializer.validated_data.get("collection")

        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication required.")

        if collection.owner != self.request.user:
            raise PermissionDenied("You can add items only to your own collections.")

        serializer.save()

    def destroy(self, request, *args, **kwargs) -> Response:
        """
        Delete an item if it belongs to a collection owned by the current user.

        Returns:
            Response: The default DRF response after successful deletion.
        """
        return super().destroy(request, *args, **kwargs)
