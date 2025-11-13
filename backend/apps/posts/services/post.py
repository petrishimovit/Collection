from __future__ import annotations
from typing import Literal, Dict

from django.db import transaction, models
from django.db.models import Count
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.posts.models import Post, Comment, PostReaction


ReactionLiteral = Literal["like", "dislike"]


class PostService:
    """Post BL"""

    @staticmethod
    def comments_qs(post: Post):
        """queryset for post counters."""
        return (
            Comment.objects
            .filter(post=post)
            .select_related("author")
            .annotate(
                _likes_count=Count("reactions", filter=models.Q(reactions__type=PostReaction.LIKE)),
                _dislikes_count=Count("reactions", filter=models.Q(reactions__type=PostReaction.DISLIKE)),
            )
            .order_by("created_at", "id")
        )

    @staticmethod
    def create_comment(*, post: Post, user, body: str) -> Comment:
        """Create a comment for a post."""
        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentication required.")
        return Comment.objects.create(post=post, author=user, body=body)

    @staticmethod
    def delete_comment(*, post: Post, user, comment_id: int) -> None:
        """Delete user's own comment by id."""
        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentication required.")
        if not comment_id:
            raise ValidationError("Missing ?id= parameter for comment deletion.")
        try:
            comment = Comment.objects.get(id=comment_id, post=post)
        except Comment.DoesNotExist:
            raise ValidationError("Comment not found.")
        if comment.author_id != user.id:
            raise PermissionDenied("You can delete only your own comments.")
        comment.delete()

    @staticmethod
    @transaction.atomic
    def toggle_reaction(*, post: Post, user, reaction_type: ReactionLiteral) -> Dict[str, int | str]:
        """Toggle user's reaction on a post and return fresh counters."""
        if reaction_type not in (PostReaction.LIKE, PostReaction.DISLIKE):
            raise ValidationError({"type": "Must be 'like' or 'dislike'."})

        qs = PostReaction.objects.select_for_update().filter(post=post, user=user)
        if qs.exists():
            reaction = qs.get()
            if reaction.type == reaction_type:
                reaction.delete()
                status = "removed"
            else:
                reaction.type = reaction_type
                reaction.save(update_fields=["type"])
                status = "changed"
        else:
            PostReaction.objects.create(post=post, user=user, type=reaction_type)
            status = "added"

        by_type = (
            PostReaction.objects
            .filter(post=post)
            .values("type")
            .annotate(c=Count("id"))
        )
        likes = next((row["c"] for row in by_type if row["type"] == PostReaction.LIKE), 0)
        dislikes = next((row["c"] for row in by_type if row["type"] == PostReaction.DISLIKE), 0)

        return {"status": status, "likes": likes, "dislikes": dislikes}