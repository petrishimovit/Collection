from django.db import models
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
)
from drf_spectacular.types import OpenApiTypes

from apps.collection.models import Collection
from apps.collection.serializers.collection import CollectionSerializer
from apps.collection.serializers.item import ItemSerializer
from apps.collection.permissions.collection import IsCollectionOwnerOrReadOnly
from apps.collection.selectors.collection import (
    get_public_collections,
    get_collections_for_user,
    get_user_collections,
    get_collection_for_user,
    get_feed_collections_for_user,
)
from apps.collection.selectors.item import get_collection_items_for_user
from apps.collection.pagination import DefaultPageNumberPagination


@extend_schema_view(
    list=extend_schema(
        summary="List public collections",
        description=(
            "Return a paginated list of **public** collections ordered by creation date or "
            "aggregate values.\n\n"
            "This endpoint is an explore/discover view and does not include private or "
            "following-only collections."
        ),
        responses={200: CollectionSerializer},
        tags=["Collections"],
        parameters=[
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Sort collections by one of:\n\n"
                    "- `created_at`, `-created_at`\n"
                    "- `items_count`, `-items_count`\n"
                    "- `total_current_value`, `-total_current_value`\n"
                    "- `total_purchase_price`, `-total_purchase_price`"
                ),
            ),
            OpenApiParameter(
                name="is_favorite",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter collections by favorite flag: `true` or `false`.",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve a collection",
        description=(
            "Return a single collection by ID.\n\n"
            "Visibility rules:\n"
            "- Public collections are visible to everyone.\n"
            "- Following-only collections are visible to users that the owner follows.\n"
            "- Private collections are only visible to their owner."
        ),
        responses={200: CollectionSerializer},
        tags=["Collections"],
    ),
    create=extend_schema(
        summary="Create a collection",
        description=(
            "Create a new collection for the authenticated user.\n\n"
            "The `owner` field is set automatically to the current user."
        ),
        request=CollectionSerializer,
        responses={201: CollectionSerializer},
        tags=["Collections"],
    ),
    destroy=extend_schema(
        summary="Delete a collection",
        description="Delete a collection owned by the authenticated user.",
        tags=["Collections"],
    ),
    partial_update=extend_schema(
        summary="Update collection (partial)",
        description=(
            "Partially update a collection. Only the owner of the collection can update it.\n\n"
            "Full `PUT` updates are not allowed on this endpoint."
        ),
        request=CollectionSerializer,
        responses={200: CollectionSerializer},
        tags=["Collections"],
    ),
)
class CollectionViewSet(viewsets.ModelViewSet):
    """
    Collections CRUD and extra actions:
    - list public collections
    - retrieve with visibility rules
    - user-owned collections
    - collections feed from followed users
    - search
    - list/create items in a collection
    """

    serializer_class = CollectionSerializer
    permission_classes = (IsCollectionOwnerOrReadOnly,)
    pagination_class = DefaultPageNumberPagination
    filter_backends = (OrderingFilter,)
    ordering_fields = (
        "created_at",
        "items_count",
        "total_current_value",
        "total_purchase_price",
    )
    ordering = ("-created_at",)

    queryset = Collection.objects.all().select_related("owner")

    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def _apply_is_favorite_filter(self, request, queryset):
        is_favorite = request.query_params.get("is_favorite")
        if is_favorite is None:
            return queryset

        value = str(is_favorite).lower()
        if value in ("true", "1", "yes"):
            return queryset.filter(is_favorite=True)
        if value in ("false", "0", "no"):
            return queryset.filter(is_favorite=False)
        return queryset

    def get_queryset(self):
        if self.action == "list":
            return get_public_collections()
        return get_collections_for_user(self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = get_public_collections()
        queryset = self._apply_is_favorite_filter(request, queryset)
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        collection_id = kwargs.get("pk")
        instance = get_collection_for_user(request.user, collection_id)
        if instance is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        Collection.objects.filter(pk=instance.pk).update(
            views_count=models.F("views_count") + 1
        )
        instance.refresh_from_db(fields=["views_count"])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="List my collections",
        description="Return a paginated list of collections owned by the authenticated user.",
        responses={200: CollectionSerializer},
        tags=["Collections"],
        parameters=[
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Sort collections by one of:\n\n"
                    "- `created_at`, `-created_at`\n"
                    "- `items_count`, `-items_count`\n"
                    "- `total_current_value`, `-total_current_value`\n"
                    "- `total_purchase_price`, `-total_purchase_price`"
                ),
            ),
            OpenApiParameter(
                name="is_favorite",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter collections by favorite flag: `true` or `false`.",
            ),
        ],
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="my",
        permission_classes=[permissions.IsAuthenticated],
    )
    def my(self, request, *args, **kwargs):
        qs = get_user_collections(request.user)
        qs = self._apply_is_favorite_filter(request, qs)
        qs = self.filter_queryset(qs)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Collections feed",
        description=(
            "Return a feed of collections from users the authenticated user follows.\n\n"
            "Visibility rules:\n"
            "- Public collections of followed users are always included.\n"
            "- Following-only collections are included only if the follow is mutual.\n"
            "- Private collections are never included."
        ),
        responses={200: CollectionSerializer},
        tags=["Collections"],
        parameters=[
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Sort collections by one of:\n\n"
                    "- `created_at`, `-created_at`\n"
                    "- `items_count`, `-items_count`\n"
                    "- `total_current_value`, `-total_current_value`\n"
                    "- `total_purchase_price`, `-total_purchase_price`"
                ),
            ),
            OpenApiParameter(
                name="is_favorite",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter collections by favorite flag: `true` or `false`.",
            ),
        ],
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="feed",
        permission_classes=[permissions.IsAuthenticated],
    )
    def feed(self, request, *args, **kwargs):
        qs = get_feed_collections_for_user(request.user)
        qs = self._apply_is_favorite_filter(request, qs)
        qs = self.filter_queryset(qs)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Search collections",
        description=(
            "Search collections visible to the current user by name or description.\n\n"
            "Search respects collection privacy and follow rules."
        ),
        tags=["Collections"],
        parameters=[
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Case-insensitive search query for collection name or description.",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Sort collections by one of:\n\n"
                    "- `created_at`, `-created_at`\n"
                    "- `items_count`, `-items_count`\n"
                    "- `total_current_value`, `-total_current_value`\n"
                    "- `total_purchase_price`, `-total_purchase_price`"
                ),
            ),
            OpenApiParameter(
                name="is_favorite",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter collections by favorite flag: `true` or `false`.",
            ),
        ],
        responses={200: CollectionSerializer},
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="search",
    )
    def search(self, request, *args, **kwargs):
        q = request.query_params.get("q", "").strip()
        qs = get_collections_for_user(request.user)

        if q:
            qs = qs.filter(
                models.Q(name__icontains=q)
                | models.Q(description__icontains=q)
            )

        qs = self._apply_is_favorite_filter(request, qs)
        qs = self.filter_queryset(qs)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(qs, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="List or create items in a collection",
        description=(
            "GET: list items in the collection that are visible to the current user.\n\n"
            "POST: create a new item in this collection (owner only)."
        ),
        request={
            "POST": ItemSerializer,
        },
        responses={
            200: ItemSerializer(many=True),
            201: ItemSerializer,
        },
        tags=["Collections"],
        parameters=[
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Optional ordering for items in the collection, e.g.:\n\n"
                    "- `created_at`, `-created_at`\n"
                    "- `current_value`, `-current_value`"
                ),
            ),
            OpenApiParameter(
                name="for_sale",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter items in the collection by sale state: `true` or `false`.",
            ),
            OpenApiParameter(
                name="is_favorite",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter items in the collection by favorite flag: `true` or `false`.",
            ),
        ],
    )
    @action(detail=True, methods=["get", "post"], url_path="items")
    def items(self, request, pk=None, *args, **kwargs):
        collection_id = pk

        if request.method.lower() == "get":
            qs = get_collection_items_for_user(request.user, collection_id)

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

            ordering = request.query_params.get("ordering")
            if ordering:
                qs = qs.order_by(ordering)

            page = self.paginate_queryset(qs)
            if page is not None:
                serializer = ItemSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = ItemSerializer(qs, many=True)
            return Response(serializer.data)

        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        from apps.collection.models import Collection as CollectionModel

        try:
            collection = CollectionModel.objects.get(pk=collection_id)
        except CollectionModel.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if collection.owner != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data["collection"] = collection_id

        serializer = ItemSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
