from django.conf import settings
from django.db import models
from django.db.models import Q

from core.models import BaseModel


class WishList(BaseModel):
    """
    Favorite / wishlist entry in user profile.
    """

    class Kind(models.TextChoices):
        ITEM = "item", "Item"
        COLLECTION = "collection", "Collection"
        CUSTOM = "custom", "Custom / external"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="favorites",
        on_delete=models.CASCADE,
    )

    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
    )

    item = models.ForeignKey(
        "collection.Item",
        related_name="favorites",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    collection = models.ForeignKey(
        "collection.Collection",
        related_name="favorites",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    title = models.CharField(
        max_length=255,
        help_text="Display label",
    )

    external_url = models.URLField(blank=True)

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["user", "kind"]),
            models.Index(fields=["user", "created_at"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "item"],
                condition=Q(item__isnull=False),
                name="wishlist_unique_item_per_user",
            ),
            models.UniqueConstraint(
                fields=["user", "collection"],
                condition=Q(collection__isnull=False),
                name="wishlist_unique_collection_per_user",
            ),
            models.CheckConstraint(
                name="wishlist_kind_matches_target",
                check=(
                    Q(kind="item", item__isnull=False, collection__isnull=True)
                    | Q(kind="collection", collection__isnull=False, item__isnull=True)
                    | Q(kind="custom", item__isnull=True, collection__isnull=True)
                ),
            ),
        ]

    def __str__(self):
        return f"{self.user_id} :: {self.kind} :: {self.title}"
