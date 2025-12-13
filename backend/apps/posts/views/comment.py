from rest_framework import viewsets, permissions, decorators, response
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.shortcuts import get_object_or_404

from apps.posts.models import Comment, CommentReaction
from apps.posts.serializers import ReactionRequestSerializer
from apps.posts.services.comment import CommentService

from apps.notifications.services import NotificationService


@extend_schema_view(
    react=extend_schema(
        summary="Toggle reaction",
        description="Like or dislike a comment.",
        request=ReactionRequestSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["added", "removed", "changed"]},
                    "likes": {"type": "integer"},
                    "dislikes": {"type": "integer"},
                },
            }
        },
        tags=["Posts"]
    ),
    
)
class CommentViewSet(viewsets.ViewSet):
    """Comment endpoints."""

    queryset = Comment.objects.all().select_related("author", "post")
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @decorators.action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
 )
    def react(self, request, pk=None):
        """Toggle reaction."""
        comment = get_object_or_404(self.queryset, pk=pk)
        reaction_type = request.data.get("type")

        if reaction_type not in [CommentReaction.LIKE, CommentReaction.DISLIKE]:
            raise ValidationError({"type": "Must be 'like' or 'dislike'."})

        data = CommentService.toggle_reaction(
            comment=comment,
            user=request.user,
            reaction_type=reaction_type,
        )

        if reaction_type == CommentReaction.LIKE and data.get("status") in {"added", "changed"}:
            NotificationService().create_comment_like(
                comment=comment,
                actor=request.user,
            )

        return response.Response(data)