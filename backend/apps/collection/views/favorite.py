from rest_framework import generics, permissions, filters
from rest_framework.exceptions import PermissionDenied

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.collection.models import Favorite
from apps.collection.serializers.favorite import FavoriteSerializer
from apps.collection.pagination import FavoritePagination


@extend_schema(
    tags=["Users"],
    parameters=[
        OpenApiParameter(
            name="ordering",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description=(
                "Sort favorites by one of:\n\n"
                "- `created_at`, `-created_at`"
            ),
        ),
    ],
)
class UserFavoritesListView(generics.ListAPIView):
    """
    List favorites for a given user.

    """

    serializer_class = FavoriteSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = FavoritePagination


    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]  

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        return Favorite.objects.filter(user_id=user_id)


@extend_schema(
    tags=["Users"],
)
class MyFavoritesCreateView(generics.CreateAPIView):
    """
    Create a favorite for the authenticated user.
    """

    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Favorite.objects.all()


@extend_schema(
    tags=["Users"],
)
class FavoriteDestroyView(generics.DestroyAPIView):
    """
    Delete a favorite by id.
    """

    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Favorite.objects.all()

    def perform_destroy(self, instance: Favorite) -> None:
        if instance.user_id != self.request.user.id:
            raise PermissionDenied("You are not allowed to delete this favorite.")
        instance.delete()
