from typing import Type
from django.db.models import Count, QuerySet
from rest_framework import viewsets, permissions
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from apps.collection.models import Collection
from apps.collection.serializers.collection import CollectionSerializer
from apps.collection.pagination import DefaultPageNumberPagination
from apps.collection.permissions.collection import IsCollectionOwnerOrReadOnly


class CollectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user collections.

    This ViewSet provides full CRUD functionality for the `Collection` model:
      - **GET /api/collections/** — list all collections (public)
      - **GET /api/collections/{id}/** — retrieve a specific collection
      - **GET /api/collections/me/** — list collections owned by the current user
      - **POST /api/collections/** — create a new collection (authenticated users only)
      - **PUT /api/collections/{id}/** — update a collection (owner only)
      - **PATCH /api/collections/{id}/** — partially update a collection (owner only)
      - **DELETE /api/collections/{id}/** — delete a collection (owner only)

    Access control:
      - Read operations (GET) are public.
      - Write operations (POST, PUT, PATCH, DELETE) are restricted to the collection owner.
    """

    serializer_class: Type[Serializer] = CollectionSerializer
    pagination_class = DefaultPageNumberPagination
    permission_classes = [IsCollectionOwnerOrReadOnly]

    def get_public_queryset(self) -> QuerySet[Collection]:
        """
        Return a queryset of all collections available for public read operations.

        The queryset is annotated with an `items_count` field and includes
        related owners and items for efficiency.

        Returns:
            QuerySet[Collection]: A queryset containing all public collections.
        """
        return (
            Collection.objects
            .select_related("owner")
            .prefetch_related("items")
            .annotate(items_count=Count("items", distinct=True))
            .order_by("name", "id")
        )

    def get_private_queryset(self) -> QuerySet[Collection]:
        """
        Return a queryset of collections owned by the authenticated user.

        Used for private operations and the `/me` endpoint.

        Returns:
            QuerySet[Collection]: A queryset containing collections
                                  owned by the current user.
        """
        if not self.request.user.is_authenticated:
            return Collection.objects.none()
        return (
            Collection.objects
            .filter(owner=self.request.user)
            .annotate(items_count=Count("items", distinct=True))
            .order_by("name", "id")
        )

    def get_queryset(self) -> QuerySet[Collection]:
        """
        Determine which queryset to use based on the current action.

        - For read actions (`list`, `retrieve`), returns the public queryset.
        - For write actions, returns only collections belonging to the current user.

        Returns:
            QuerySet[Collection]: The appropriate queryset for the action.
        """
        if self.action in ("list", "retrieve"):
            return self.get_public_queryset()
        return self.get_private_queryset()

    def get_permissions(self) -> list[BasePermission]:
        """
        Return permission instances depending on the current action.

        - Public read actions (`list`, `retrieve`) are open to everyone.
        - Write actions require authentication and ownership verification.
        """
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [perm() for perm in self.permission_classes]

    def perform_create(self, serializer) -> None:
        """
        Assign the authenticated user as the owner when creating a new collection.

        Raises:
            PermissionDenied: If the user is not authenticated.
        """
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
        Retrieve only collections belonging to the authenticated user.

        Endpoint:
            **GET /api/collections/me/**

        Returns:
            Response: Paginated or full list of the user's own collections.
        """
        qs = self.get_private_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)
