from django.conf import settings
from django.db import models

from core.models import BaseModel
from core.utils.images import compress_webp, thumb_webp


def collection_image_path(instance, filename) -> str:
    return f"collections/{instance.owner_id}/{instance.id}/{filename}"


class Collection(BaseModel):
    """User's collection"""

    PRIVACY_PUBLIC = "public"
    PRIVACY_PRIVATE = "private"
    PRIVACY_FOLLOWING = "following_only"

    PRIVACY_CHOICES = (
        (PRIVACY_PUBLIC, "Public"),
        (PRIVACY_PRIVATE, "Private"),
        (PRIVACY_FOLLOWING, "Following only"),
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="collections",
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    image = models.ImageField(upload_to=collection_image_path, blank=True, null=True)
    preview_sm = models.ImageField(
        upload_to=collection_image_path, blank=True, null=True, editable=False
    )
    preview_md = models.ImageField(
        upload_to=collection_image_path, blank=True, null=True, editable=False
    )

    privacy = models.CharField(
        max_length=32,
        choices=PRIVACY_CHOICES,
        default=PRIVACY_PUBLIC,
        db_index=True,
    )

    views_count = models.PositiveIntegerField(default=0)
    is_favorite = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)  # ensure id exists

        if self.image and (creating or not self.preview_sm or not self.preview_md):
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

            super().save(update_fields=["image", "preview_sm", "preview_md", "updated_at"])
