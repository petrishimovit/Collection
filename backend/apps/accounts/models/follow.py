from django.db import models
from django.db.models import F, Q

from core.models import BaseModel


class Follow(BaseModel):
    """
    Follow relationship between users.

    Defines a one-way link where one user (`follower`)
    subscribes to another (`following`).
    """

    follower = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="following_relations",
    )
    following = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="follower_relations",
    )

    class Meta:
        db_table = "accounts_follow"

        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="uq_follow_unique"),
            models.CheckConstraint(check=~Q(follower=F("following")), name="chk_no_self_follow"),
        ]

    def __str__(self):
        return f"{self.follower_id} -> {self.following_id}"
