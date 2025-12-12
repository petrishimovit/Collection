from django.conf import settings
from django.db import models

from core.models import BaseModel  


class Notification(BaseModel):
    
    """
    Notification model for User`s
    """

    class Type(models.TextChoices):
        FOLLOW = "follow"
        POST_CREATE = "post"
        COMMENT_CREATE = "comment_create"
        ITEM_CREATE = "item_create"
        

    for_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=True,
    )

    type = models.CharField(
        max_length=32,
        choices=Type.choices,
        db_index=True,
    )


    is_checked = models.BooleanField(
        default=False,
        db_index=True,
    )

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=["for_user", "is_checked", "-created_at"]),
            models.Index(fields=["for_user", "-created_at"]),
        ]
