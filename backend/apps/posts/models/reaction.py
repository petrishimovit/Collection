from django.conf import settings
from django.db import models
from core.models import BaseModel


class PostReaction(BaseModel):
    """
    Reaction (like/dislike) left by a user on a post.
    """
    LIKE = "like"
    DISLIKE = "dislike"

    REACTION_TYPES = [
        (LIKE, "Like"),
        (DISLIKE, "Dislike"),
    ]

    post = models.ForeignKey("posts.Post", on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="post_reactions")
    type = models.CharField(max_length=10, choices=REACTION_TYPES)

    class Meta:
        unique_together = ("post", "user")
        indexes = [models.Index(fields=["post", "type"])]

    def __str__(self):
        return f"{self.user_id} → {self.get_type_display()} Post {self.post_id}"


class CommentReaction(BaseModel):
    """
    Reaction (like/dislike) left by a user on a comment.
    """
    LIKE = "like"
    DISLIKE = "dislike"

    REACTION_TYPES = [
        (LIKE, "Like"),
        (DISLIKE, "Dislike"),
    ]

    comment = models.ForeignKey("posts.Comment", on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comment_reactions")
    type = models.CharField(max_length=10, choices=REACTION_TYPES)

    class Meta:
        unique_together = ("comment", "user")
        indexes = [models.Index(fields=["comment", "type"])]

    def __str__(self):
        return f"{self.user_id} → {self.get_type_display()} Comment {self.comment_id}"
