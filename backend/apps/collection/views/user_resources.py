from rest_framework import generics, permissions, filters
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.collection.serializers.collection import CollectionSerializer
from apps.collection.serializers.item import ItemSerializer
from apps.collection.pagination import DefaultPageNumberPagination
from apps.collection.selectors.collection import get_collections_for_user_profile
from apps.collection.selectors.item import get_user_items_for_viewer


@extend_schema(
    summary="List collections of a user",
    description=(
        "Return a paginated list of collections owned by the given user, "
        "filtered by visibility rules relative to the current viewer."
    ),
    tags=["Users"],
    parameters=[
        OpenApiParameter(
            name="ordering",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description=(
                "Sort collections by one of:\n\n"
                "- `created_at`, `-created_at`\n"
                "- `items_count`, `-items_count`\n"
                "- `total_current_value`, `-total_current_value`\n"
                "- `total_purchase_price`, `-total_purchase_price`"
            ),
        ),
    ],
    responses={200: CollectionSerializer},
)
class UserCollectionsListView(generics.ListAPIView):
    """
    List collections of a specific user with privacy rules applied for the viewer.
    """

    serializer_class = CollectionSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = DefaultPageNumberPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = (
        "created_at",
        "items_count",
        "total_current_value",
        "total_purchase_price",
    )
    ordering = ("-created_at",)

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        qs = get_collections_for_user_profile(self.request.user, user_id)
        qs = self.filter_queryset(qs)
        return qs


@extend_schema(
    summary="List items of a user",
    description=(
        "Return a paginated list of items belonging to collections of the given user, "
        "filtered by collection and item privacy relative to the current viewer."
    ),
    tags=["Users"],
    parameters=[
        OpenApiParameter(
            name="for_sale",
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Filter items by sale state: `true` or `false`.",
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
class UserItemsListView(generics.ListAPIView):
    """
    List items of a specific user with collection/item privacy rules applied.
    """

    serializer_class = ItemSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = DefaultPageNumberPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ("created_at", "current_value")
    ordering = ("-created_at",)

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        qs = get_user_items_for_viewer(self.request.user, user_id)

        for_sale = self.request.query_params.get("for_sale")
        if for_sale is not None:
            value = str(for_sale).lower()
            if value in ("true", "1"):
                qs = qs.filter(for_sale=True)
            elif value in ("false", "0"):
                qs = qs.filter(for_sale=False)

        qs = self.filter_queryset(qs)
        return qs
