from django.conf import settings
from django.db import models

from core.models import BaseModel


def collection_image_path(instance, filename):
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
    image = models.ImageField(
        upload_to=collection_image_path,
        blank=True,
        null=True,
    )

    privacy = models.CharField(
        max_length=32,                      
        choices=PRIVACY_CHOICES,
        default=PRIVACY_PUBLIC,
        db_index=True,
    )

    views_count = models.PositiveIntegerField(  
        default=0,
    )

    is_favorite = models.BooleanField(
        default=False,
        db_index=True,
    )

    class Meta:
        ordering = ("name",)
        unique_together = (("owner", "name"),)

    def __str__(self):
        return self.name
