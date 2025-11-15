from __future__ import annotations
from typing import Literal, Dict

from django.db import transaction
from django.db.models import Count
from rest_framework.exceptions import ValidationError

from apps.posts.models import Comment, CommentReaction

ReactionLiteral = Literal["like", "dislike"]


class CommentService:
    """
    Service layer for comment actions.
    """

    @staticmethod
    @transaction.atomic
    def toggle_reaction(
        *,
        comment: Comment,
        user,
        reaction_type: ReactionLiteral,
    ) -> Dict[str, int | str]:
        """
        Add, remove, or change a user's reaction on a comment.

        Args:
            comment: Target comment.
            user: Acting user.
            reaction_type: "like" or "dislike".

        Returns:
            Dict with status and updated counters.
        """
        if reaction_type not in (CommentReaction.LIKE, CommentReaction.DISLIKE):
            raise ValidationError({"type": "Must be 'like' or 'dislike'."})

        reaction_qs = CommentReaction.objects.select_for_update().filter(
            comment=comment,
            user=user,
        )
        reaction = reaction_qs.first()

        if reaction is None:
            CommentReaction.objects.create(
                comment=comment,
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
                CommentReaction.objects
                .filter(comment=comment)
                .values("type")
                .annotate(c=Count("id"))
            )
        }

        likes = counts_by_type.get(CommentReaction.LIKE, 0)
        dislikes = counts_by_type.get(CommentReaction.DISLIKE, 0)

        return {
            "status": status,
            "likes": likes,
            "dislikes": dislikes,
        }
