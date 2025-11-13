import uuid
from django.conf import settings
from django.db import models
from core.models import BaseModel


def collection_image_path(instance, filename):
    return f"collections/{instance.owner_id}/{instance.id}/{filename}"


class Collection(BaseModel):
    """User`s collection"""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="collections",
    )
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to=collection_image_path, blank=True, null=True)

    class Meta:
        ordering = ("name",)
        unique_together = (("owner", "name"),)

    def __str__(self):
        return self.name
