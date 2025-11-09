from __future__ import annotations
from typing import Literal, Dict

from django.db import transaction
from django.db.models import Count

from apps.posts.models import Comment, CommentReaction

ReactionLiteral = Literal["like", "dislike"]


class CommentService:
    """Comment BL"""

    @staticmethod
    @transaction.atomic
    def toggle_reaction(*, comment: Comment, user, reaction_type: ReactionLiteral) -> Dict[str, int | str]:
        """Toggle user's reaction on a comment and return fresh counters."""
        if reaction_type not in (CommentReaction.LIKE, CommentReaction.DISLIKE):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"type": "Must be 'like' or 'dislike'."})

        qs = CommentReaction.objects.select_for_update().filter(comment=comment, user=user)
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
            CommentReaction.objects.create(comment=comment, user=user, type=reaction_type)
            status = "added"

        by_type = (
            CommentReaction.objects
            .filter(comment=comment)
            .values("type")
            .annotate(c=Count("id"))
        )
        likes = next((row["c"] for row in by_type if row["type"] == CommentReaction.LIKE), 0)
        dislikes = next((row["c"] for row in by_type if row["type"] == CommentReaction.DISLIKE), 0)

        return {"status": status, "likes": likes, "dislikes": dislikes}
