from rest_framework import viewsets, permissions, decorators, response
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404

from posts.models import Comment, CommentReaction
from posts.serializers import ReactionRequestSerializer

class CommentViewSet(viewsets.ViewSet):
    queryset = Comment.objects.all().select_related("author", "post")
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


    @extend_schema(
    request=ReactionRequestSerializer,
    )    
    @decorators.action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def react(self, request, pk=None):

        comment = get_object_or_404(self.queryset, pk=pk)
        reaction_type = request.data.get("type")

        if reaction_type not in [CommentReaction.LIKE, CommentReaction.DISLIKE]:
            raise ValidationError({"type": "Must be 'like' or 'dislike'."})

        reaction, created = CommentReaction.objects.get_or_create(
            comment=comment, user=request.user, defaults={"type": reaction_type}
        )

        if not created:
            if reaction.type == reaction_type:
                reaction.delete()
                return response.Response(
                    {"status": "removed", "likes": comment.likes_count, "dislikes": comment.dislikes_count}
                )
            else:
                reaction.type = reaction_type
                reaction.save()

        return response.Response(
            {"status": "added", "likes": comment.likes_count, "dislikes": comment.dislikes_count}
        )