from rest_framework import viewsets, permissions, decorators, response
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404

from posts.models import Comment, CommentReaction
from posts.serializers import ReactionRequestSerializer
from posts.services.comment import CommentService


class CommentViewSet(viewsets.ViewSet):
    """Comment viewset"""

    queryset = Comment.objects.all().select_related("author", "post")
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="Toggle comment reaction",
        request=ReactionRequestSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["added", "removed", "changed"]},
                    "likes": {"type": "integer"},
                    "dislikes": {"type": "integer"},
                },
                "required": ["status", "likes", "dislikes"],
            }
        },
    )
    @decorators.action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def react(self, request, pk=None):
        """Toggle like/dislike on a comment."""
        comment = get_object_or_404(self.queryset, pk=pk)
        reaction_type = request.data.get("type")
        if reaction_type not in [CommentReaction.LIKE, CommentReaction.DISLIKE]:
            raise ValidationError({"type": "Must be 'like' or 'dislike'."})

        data = CommentService.toggle_reaction(
            comment=comment,
            user=request.user,
            reaction_type=reaction_type,
        )
        return response.Response(data)
