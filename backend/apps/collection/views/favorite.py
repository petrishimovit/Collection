from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
)
from drf_spectacular.types import OpenApiTypes

from apps.collection.models import Favorite
from apps.collection.serializers.favorite import FavoriteSerializer
from apps.collection.pagination import DefaultPageNumberPagination


@extend_schema_view(
    get=extend_schema(
        summary="List user favorites",
        description=(
            "Return a paginated list of favorites belonging to the specified user.\n\n"
            "Supports ordering by creation date."
        ),
        tags=["Users"],
        parameters=[
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Order results by `created_at` or `-created_at`.",
            ),
        ],
        responses={200: FavoriteSerializer},
    )
)
class UserFavoritesListView(generics.ListAPIView):
    """
    List favorites for a given user.

    GET /users/{user_id}/favorites

    Pagination is handled by DRF pagination class.
    """

    serializer_class = FavoriteSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = DefaultPageNumberPagination
    filter_backends = (OrderingFilter,)
    ordering_fields = ("created_at",)
    ordering = ("-created_at",)

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        return Favorite.objects.filter(user_id=user_id)


@extend_schema(
    summary="Create a favorite",
    description=(
        "Create a favorite entry for the authenticated user.\n\n"
        "Supports favorite types: `item`, `collection`, `custom`."
    ),
    tags=["Users"],
    request=FavoriteSerializer,
    responses={
        201: FavoriteSerializer,
        400: FavoriteSerializer,
    },
)
class MyFavoritesCreateView(generics.CreateAPIView):
    """
    Create a favorite for the authenticated user.

    POST /users/me/favorites
    """

    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Favorite.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(
    summary="Delete a favorite",
    description=(
        "Delete a favorite entry.\n\n"
        "Only the owner of the favorite may delete it."
    ),
    tags=["Users"],
    responses={
        204: None,
        403: None,
        404: None,
    },
)
class FavoriteDestroyView(generics.DestroyAPIView):
    """
    Delete a favorite by id.

    DELETE /favorites/{id}

    Only the owner of the favorite is allowed to delete it.
    """

    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Favorite.objects.all()

    def perform_destroy(self, instance: Favorite) -> None:
        if instance.user_id != self.request.user.id:
            raise PermissionDenied("You are not allowed to delete this favorite.")
        instance.delete()
