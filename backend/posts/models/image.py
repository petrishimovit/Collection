from uuid import uuid4

from django.db import models
from core.models import BaseModel


def post_image_upload_to(instance: "PostImage", filename: str) -> str:
    
    stem = f"{uuid4().hex[:8]}_{filename}"
    post_part = instance.post_id or "unassigned"
    return f"posts/{post_part}/{stem}"


class PostImage(BaseModel):
    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(
        upload_to=post_image_upload_to,
        width_field="width",
        height_field="height",
    )
    alt = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    
    width = models.PositiveIntegerField(editable=False, default=0)
    height = models.PositiveIntegerField(editable=False, default=0)

    class Meta:
        ordering = ["order", "id"]
        indexes = [
            models.Index(fields=["post", "order"]),
        ]
        

    def __str__(self):
        return f"Image #{self.pk} for Post #{self.post_id}"
