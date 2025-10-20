from django.conf import settings
from django.db import models
from core.models import BaseModel


class Post(BaseModel):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True,max_length=400)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.title or f"Post #{self.pk}"

    @property
    def likes_count(self):
        return self.reactions.filter(type="like").count()

    @property
    def dislikes_count(self):
        return self.reactions.filter(type="dislike").count()
