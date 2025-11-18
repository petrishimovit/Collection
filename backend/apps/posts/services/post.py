from __future__ import annotations
from typing import Literal, Dict

from django.db import transaction, models
from django.db.models import Count
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.posts.models import Post, Comment, PostReaction


ReactionLiteral = Literal["like", "dislike"]


class PostService:
    """
    Service layer for post actions.
    """
    
    @staticmethod
    def create_comment(*, post: Post, user, text: str) -> Comment:
        """
        Create a comment for a post.
        """
        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentication required.")
        return Comment.objects.create(post=post, author=user, text=text)

    @staticmethod
    def delete_comment(*, post: Post, user, comment_id: int) -> None:
        """
        Delete a user's own comment by id.
        """
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
    def toggle_reaction(
        *,
        post: Post,
        user,
        reaction_type: ReactionLiteral,
    ) -> Dict[str, int | str]:
        """
        Add, remove, or change a user's reaction on a post.

        Args:
            post: Target post.
            user: Acting user.
            reaction_type: "like" or "dislike".

        Returns:
            Dict with status and updated counters.
        """
        if reaction_type not in (PostReaction.LIKE, PostReaction.DISLIKE):
            raise ValidationError({"type": "Must be 'like' or 'dislike'."})

        reaction = (
            PostReaction.objects
            .select_for_update()
            .filter(post=post, user=user)
            .first()
        )

        if reaction is None:
            PostReaction.objects.create(
                post=post,
                user=user,
                type=reaction_type,
            )
            status = "added"
        elif reaction.type == reaction_type:
            reaction.delete()
            status = "removed"
        else:
            reaction.type = reaction_type
            reaction.save(update_fields=["type"])
            status = "changed"

        counts_by_type = {
            row["type"]: row["c"]
            for row in (
                PostReaction.objects
                .filter(post=post)
                .values("type")
                .annotate(c=Count("id"))
            )
        }

        likes = counts_by_type.get(PostReaction.LIKE, 0)
        dislikes = counts_by_type.get(PostReaction.DISLIKE, 0)

        return {
            "status": status,
            "likes": likes,
            "dislikes": dislikes,
        }
