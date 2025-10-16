import uuid
from django.db import models
from core.models import BaseModel
from .collection import Collection


def item_image_path(instance, filename):
    return f"items/{instance.item.collection_id}/{instance.item_id}/{filename}"


class Item(BaseModel):
    """Item in Collection"""

    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name="items",
    )
    name = models.CharField(max_length=250)

    description = models.CharField(max_length=700,default="No description")

    purchase_date = models.DateField(blank=True, null=True)

    purchase_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    current_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class ItemImage(BaseModel):
    """Image from Item"""

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to=item_image_path)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "created_at")

    def __str__(self):
        return f"Image for {self.item.name}"
