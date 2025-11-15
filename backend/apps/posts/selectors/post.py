from apps.posts.models import Post , Comment , PostReaction
from django.db.models import Count
from django.db import models

def comments_qs(post: Post):
    """
    Return queryset of post comments with reaction counters.
    """
    return (
            Comment.objects
            .filter(post=post)
            .select_related("author")
            .annotate(
                _likes_count=Count(
                    "reactions",
                    filter=models.Q(reactions__type=PostReaction.LIKE),
                ),
                _dislikes_count=Count(
                    "reactions",
                    filter=models.Q(reactions__type=PostReaction.DISLIKE),
                ),
            )
            .order_by("created_at", "id")
    )