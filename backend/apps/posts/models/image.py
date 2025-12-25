from uuid import uuid4

from django.db import models

from core.models import BaseModel
from core.utils.images import compress_webp, thumb_webp


def post_image_upload_to(instance, filename: str) -> str:
    """
    Build upload path for post images.

    Example: posts/<post_id|unassigned>/<uuid>_<original_name>
    """
    stem = f"{uuid4().hex[:8]}_{filename}"
    post_part = instance.post_id or "unassigned"
    return f"posts/{post_part}/{stem}"


class PostImage(BaseModel):
    """
    Image attached to a post.
    """

    post = models.ForeignKey("posts.Post", on_delete=models.CASCADE, related_name="images")

    image = models.ImageField(
        upload_to=post_image_upload_to,
        width_field="width",
        height_field="height",
    )

    preview_sm = models.ImageField(
        upload_to=post_image_upload_to, blank=True, null=True, editable=False
    )
    preview_md = models.ImageField(
        upload_to=post_image_upload_to, blank=True, null=True, editable=False
    )

    width = models.PositiveIntegerField(editable=False, default=0)
    height = models.PositiveIntegerField(editable=False, default=0)

    class Meta:
        ordering = ["id"]
        indexes = [models.Index(fields=["post", "id"])]

    def __str__(self):
        return f"Image #{self.pk} for Post #{self.post_id}"

    def save(self, *args, **kwargs):
        if self.image and (not self.pk or not self.preview_sm or not self.preview_md):
            original_name = self.image.name

            self.image = compress_webp(
                self.image,
                original_name=original_name,
                max_size=(1600, 1600),
                quality=82,
            )
            self.preview_sm = thumb_webp(
                self.image, original_name=original_name, width=256, quality=78
            )
            self.preview_md = thumb_webp(
                self.image, original_name=original_name, width=768, quality=80
            )

        super().save(*args, **kwargs)
