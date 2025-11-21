from django.db import models
from django.db.models import Count, Q, Max

from apps.posts.models import Post, Comment, PostReaction
from apps.posts.selectors.user import following_qs


def comments_qs(post: Post):
    """
    Return queryset of comments for a given post with annotated reaction counts.
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


def base_posts_qs():
    """
    Base queryset for posts with annotated counters for likes, dislikes, and comments.
    NOTE: soft-deleted posts are excluded globally.
    """
    return (
        Post.objects
        .filter(is_deleted=False)  # ← добавлено
        .select_related("author")
        .annotate(
            _likes_count=Count(
                "reactions",
                filter=Q(reactions__type=PostReaction.LIKE),
            ),
            _dislikes_count=Count(
                "reactions",
                filter=Q(reactions__type=PostReaction.DISLIKE),
            ),
            _comments_count=Count("comments"),
        )
    )


def posts_list_qs():
    """
    Return the main posts list ordered by creation date (newest first).
    """
    return base_posts_qs().order_by("-created_at", "-id")


def feed_qs(user):
    """
    Return the personal feed for a user, limited to authors they follow.
    Posts are sorted by freshness first, then by activity metrics:
    likes, comments, and views.
    """
    followed_users = following_qs(user)

    return (
        base_posts_qs()
        .filter(author__in=followed_users)
        .order_by(
            "-created_at",
            "-_likes_count",
            "-_comments_count",
            "-views_count",
            "-id",
        )
    )


def liked_by_user_qs(user):
    """
    Return posts liked by the user.
    Sorted by the timestamp of the user's latest reaction,
    falling back to the post's creation date.
    """
    return (
        base_posts_qs()
        .filter(
            reactions__user=user,
            reactions__type=PostReaction.LIKE,
        )
        .annotate(
            reacted_at=Max(
                "reactions__created_at",
                filter=Q(
                    reactions__user=user,
                    reactions__type=PostReaction.LIKE,
                ),
            )
        )
        .order_by("-reacted_at", "-created_at", "-id")
        .distinct()
    )


def search_posts_qs(query: str):
    """
    Return posts matching the given search query.
    Currently searches in the text field (case-insensitive).
    """
    if not query:
        return base_posts_qs().none()

    return (
        base_posts_qs()
        .filter(text__icontains=query)
        .order_by("-created_at", "-id")
    )
