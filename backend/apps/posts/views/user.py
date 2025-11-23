from rest_framework import mixins, viewsets, permissions
from rest_framework.filters import OrderingFilter
from drf_spectacular.utils import extend_schema

from apps.posts.pagination import PostPagination
from apps.posts.serializers import PostListSerializer
from apps.posts.selectors.post import user_posts_qs


class UserPostsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Read-only endpoint that returns posts authored by a given user.
    """

    serializer_class = PostListSerializer
    pagination_class = PostPagination
    permission_classes = [permissions.AllowAny]

    filter_backends = (OrderingFilter,)

   
    ordering_fields = (
        "created_at",
        "views_count",
        "likes_count",
    )

    ordering = ("-created_at",)

    def get_queryset(self):
        """Return posts authored by the user from the URL."""
        user_id = self.kwargs["id"]
        return user_posts_qs(author_id=user_id)

    @extend_schema(
        summary="List posts by user",
        description=(
            "Return a paginated list of posts authored by the given user.\n\n"
            "Ordering options via `?ordering=`:\n"
            "- `-created_at` (default)\n"
            "- `created_at`\n"
            "- `views_count`, `-views_count`\n"
            "- `likes_count`, `-likes_count`\n"
        ),
        tags=["Posts"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
