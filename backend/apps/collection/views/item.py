from django.db import models
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
)
from drf_spectacular.types import OpenApiTypes

from apps.collection.models import Item
from apps.collection.serializers.item import ItemSerializer
from apps.collection.permissions.item import IsItemOwnerOrReadOnly
from apps.collection.selectors.item import (
    get_items_for_user,
    get_item_for_user,
)
from apps.collection.pagination import DefaultPageNumberPagination

from apps.notifications.services import NotificationService



@extend_schema_view(
    list=extend_schema(
        summary="List items",
        description=(
            "Return a paginated list of items visible to the current user.\n\n"
            "Visibility rules:\n"
            "- Anonymous users see only public items in public collections.\n"
            "- Authenticated users also see their own items and items shared with them "
            "via following and visibility rules."
        ),
        responses={200: ItemSerializer},
        tags=["Collections"],
        parameters=[
            OpenApiParameter(
                name="collection",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter items by collection ID.",
            ),
            OpenApiParameter(
                name="for_sale",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter items by sale state: `true` or `false`.",
            ),
            OpenApiParameter(
                name="is_favorite",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter items by favorite flag: `true` or `false`.",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Sort items by one of:\n\n"
                    "- `created_at`, `-created_at`\n"
                    "- `current_value`, `-current_value`"
                ),
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve an item",
        description=(
            "Return a single item by ID if it is visible to the current user.\n\n"
            "Visibility is determined by the item's privacy and its collection's privacy."
        ),
        responses={200: ItemSerializer},
        tags=["Collections"],
    ),
    create=extend_schema(
        summary="Create an item",
        description=(
            "Create a new item in a collection owned by the authenticated user.\n\n"
            "The user must be the owner of the collection referenced in the request."
        ),
        request=ItemSerializer,
        responses={201: ItemSerializer},
        tags=["Collections"],
    ),
    destroy=extend_schema(
        summary="Delete an item",
        description="Delete an item from a collection owned by the authenticated user.",
        tags=["Collections"],
    ),
    partial_update=extend_schema(
        summary="Update item (partial)",
        description=(
            "Partially update an item. Only the owner of the item's collection can update it.\n\n"
            "Full `PUT` updates are not allowed on this endpoint."
        ),
        request=ItemSerializer,
        responses={200: ItemSerializer},
        tags=["Collections"],
    ),
)
class ItemViewSet(viewsets.ModelViewSet):
    """
    Items CRUD and extra actions:
    - list items visible to the user
    - retrieve with visibility rules
    - create items in own collections
    - search
    """

    serializer_class = ItemSerializer
    permission_classes = (IsItemOwnerOrReadOnly,)
    pagination_class = DefaultPageNumberPagination
    filter_backends = (OrderingFilter,)
    ordering_fields = ("created_at", "current_value")
    ordering = ("-created_at",)

    queryset = Item.objects.all().select_related("collection", "collection__owner")

    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        qs = get_items_for_user(self.request.user)

        collection_id = self.request.query_params.get("collection")
        if collection_id:
            qs = qs.filter(collection_id=collection_id)

        for_sale = self.request.query_params.get("for_sale")
        if for_sale is not None:
            value = str(for_sale).lower()
            if value in ("true", "1"):
                qs = qs.filter(for_sale=True)
            elif value in ("false", "0"):
                qs = qs.filter(for_sale=False)

        is_favorite = self.request.query_params.get("is_favorite")
        if is_favorite is not None:
            value = str(is_favorite).lower()
            if value in ("true", "1", "yes"):
                qs = qs.filter(is_favorite=True)
            elif value in ("false", "0", "no"):
                qs = qs.filter(is_favorite=False)

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

        item = serializer.save()

        NotificationService().create_item_for_followers(item=item)


    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Search items",
        description=(
            "Search items visible to the current user by name or description.\n\n"
            "Search respects item and collection privacy rules."
        ),
        tags=["Collections"],
        parameters=[
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Case-insensitive search query for item name or description.",
            ),
            OpenApiParameter(
                name="collection",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Optionally filter search results by collection ID.",
            ),
            OpenApiParameter(
                name="for_sale",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter items by sale state: `true` or `false`.",
            ),
            OpenApiParameter(
                name="is_favorite",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter items by favorite flag: `true` or `false`.",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Sort items by one of:\n\n"
                    "- `created_at`, `-created_at`\n"
                    "- `current_value`, `-current_value`"
                ),
            ),
        ],
        responses={200: ItemSerializer},
    )
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

        for_sale = request.query_params.get("for_sale")
        if for_sale is not None:
            value = str(for_sale).lower()
            if value in ("true", "1"):
                qs = qs.filter(for_sale=True)
            elif value in ("false", "0"):
                qs = qs.filter(for_sale=False)

        is_favorite = request.query_params.get("is_favorite")
        if is_favorite is not None:
            value = str(is_favorite).lower()
            if value in ("true", "1", "yes"):
                qs = qs.filter(is_favorite=True)
            elif value in ("false", "0", "no"):
                qs = qs.filter(is_favorite=False)

        qs = self.filter_queryset(qs)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(qs, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
