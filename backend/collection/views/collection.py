from typing import Type
from django.db.models import Count, QuerySet
from rest_framework import viewsets, permissions
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from collection.models import Collection
from collection.serializers.collection import CollectionSerializer
from collection.pagination import DefaultPageNumberPagination
from collection.permissions import IsOwnerOrReadOnly

class CollectionViewSet(viewsets.ModelViewSet):
    """
        GET   /api/collections/        -> all collections (read)
        GET   /api/collections/{id}/   -> collection by id (read)
        GET   /api/collections/me/     -> only current user's collections (read)
        POST  /api/collections/        -> create (auth)
        PUT   /api/collections/{id}/   -> update (owner)
        PATCH /api/collections/{id}/   -> update (owner)
        DELETE /api/collections/{id}/  -> delete (owner)
    """
    serializer_class: Type[Serializer] = CollectionSerializer
    pagination_class = DefaultPageNumberPagination
    permission_classes = [IsOwnerOrReadOnly]

    def get_public_queryset(self) -> QuerySet[Collection]:
        return (
            Collection.objects
            .select_related("owner")
            .prefetch_related("items")
            .annotate(items_count=Count("items", distinct=True))
            .order_by("name", "id")
        )

    def get_private_queryset(self) -> QuerySet[Collection]:
        if not self.request.user.is_authenticated:
            return Collection.objects.none()
        return (
            Collection.objects
            .filter(owner=self.request.user)
            .annotate(items_count=Count("items", distinct=True))
            .order_by("name", "id")
        )

    def get_queryset(self) -> QuerySet[Collection]:
        if self.action in ("list", "retrieve"):
            return self.get_public_queryset()
        return self.get_private_queryset()

    def get_permissions(self) -> list[BasePermission]:
       
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        
        return [perm() for perm in self.permission_classes]

    def perform_create(self, serializer) -> None:
        user = self.request.user
        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentication required.")
        serializer.save(owner=user)

    @action(
        detail=False,
        methods=["get"],
        url_path="me",
        pagination_class=DefaultPageNumberPagination,
        permission_classes=[permissions.IsAuthenticated],
    )
    def me(self, request) -> Response:
        """
        GET /api/collections/me/ -> only current user's collections (read)
        """
        qs = self.get_private_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)
