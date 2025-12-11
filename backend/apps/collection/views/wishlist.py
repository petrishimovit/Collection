from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.collection.models import WishList
from apps.collection.serializers.wishlist import WishListSerializer
from apps.collection.pagination import DefaultPageNumberPagination


@extend_schema_view(
    get=extend_schema(
        summary="List user favorites",
        description="Returns a paginated list of wishlist entries for a specific user.",
        tags=["Users"],
        parameters=[
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Order by `created_at` or `-created_at`.",
            ),
        ],
        responses={200: WishListSerializer},
    )
)
class UserWishListListView(generics.ListAPIView):
    serializer_class = WishListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = DefaultPageNumberPagination
    filter_backends = (OrderingFilter,)
    ordering_fields = ("created_at",)
    ordering = ("-created_at",)

    def get_queryset(self):
        return WishList.objects.filter(user_id=self.kwargs["user_id"])


@extend_schema(
    summary="Create a wishlist entry",
    description="Create a new wishlist entry for authenticated user.",
    tags=["Users"],
    request=WishListSerializer,
    responses={201: WishListSerializer, 400: WishListSerializer},
)
class MyWishListCreateView(generics.CreateAPIView):
    serializer_class = WishListSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = WishList.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(
    summary="Delete wishlist entry",
    description="Only the owner can delete wishlist entries.",
    tags=["Users"],
    responses={204: None, 403: None},
)
class WishListDestroyView(generics.DestroyAPIView):
    serializer_class = WishListSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = WishList.objects.all()

    def perform_destroy(self, instance: WishList):
        if instance.user_id != self.request.user.id:
            raise PermissionDenied("You are not allowed to delete this favorite.")
        instance.delete()
