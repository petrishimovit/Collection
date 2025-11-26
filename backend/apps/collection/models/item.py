from django.db import models

from core.models import BaseModel
from .collection import Collection


def item_image_path(instance, filename):
    return f"items/{instance.item.collection_id}/{instance.item_id}/{filename}"


class Item(BaseModel):
    """Item in Collection"""

    PRIVACY_PUBLIC = "public"
    PRIVACY_PRIVATE = "private"
    PRIVACY_FOLLOWING = "following_only"

    PRIVACY_CHOICES = (
        (PRIVACY_PUBLIC, "Public"),
        (PRIVACY_PRIVATE, "Private"),
        (PRIVACY_FOLLOWING, "Following only"),
    )

    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name="items",
    )

    pricecharting = models.ForeignKey(
        "games.PriceChartingConnect",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="items",
    )

    name = models.CharField(max_length=250)

    description = models.CharField(
        max_length=700,
        null=True,
        blank=True,
    )

    category = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
    )

    privacy = models.CharField(
        max_length=32,
        choices=PRIVACY_CHOICES,
        default=PRIVACY_PUBLIC,
        db_index=True,
    )

    quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    location = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    purchase_date = models.DateField(
        null=True,
        blank=True,
    )

    purchase_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )

    current_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )

    currency = models.CharField(
        max_length=8,
        null=True,
        blank=True,
    )

    extra = models.JSONField(
        default=dict,
        blank=True,
    )

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name
