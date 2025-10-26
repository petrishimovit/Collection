from django.conf import settings
from django.db import models
from core.models import BaseModel


class Comment(BaseModel):
    post = models.ForeignKey("posts.Post", on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField(max_length=200)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"Comment #{self.pk} on Post #{self.post_id}"

    @property
    def likes_count(self):
        return self.reactions.filter(type="like").count()

    @property
    def dislikes_count(self):
        return self.reactions.filter(type="dislike").count()
