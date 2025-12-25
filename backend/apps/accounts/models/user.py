from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from core.models import BaseModel

from ..managers import UserManager


class User(BaseModel, AbstractUser):
    """
    User model using email as the unique identifier.

    Supports following other users via the Follow model.
    """

    username = None
    email = models.EmailField("Email", unique=True)
    display_name = models.CharField("Display name", max_length=150)

    is_active = models.BooleanField("Is active", default=True)

    following = models.ManyToManyField(
        "self",
        through="accounts.Follow",
        through_fields=("follower", "following"),
        related_name="followers",
        symmetrical=False,
        blank=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    objects = UserManager()

    def __str__(self) -> str:
        """Return the display name or email."""
        return self.display_name or self.email

    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False
        self.save(update_fields=["is_active"])

    def follow(self, other: "User") -> bool:
        """Follow another user. Returns True if a new relation was created."""
        if other.id == self.id:
            raise ValidationError("Cannot follow yourself.")
        from .follow import Follow

        obj, created = Follow.objects.get_or_create(follower=self, following=other)
        return created

    def unfollow(self, other: "User") -> int:
        """Unfollow another user. Returns number of deleted relations."""
        from .follow import Follow

        return Follow.objects.filter(follower=self, following=other).delete()[0]

    def is_following(self, other: "User") -> bool:
        """Check if the user follows another user."""
        from .follow import Follow

        return Follow.objects.filter(follower=self, following=other).exists()

    @property
    def followers_count(self) -> int:
        """Return number of followers."""
        return self.followers.count()

    @property
    def following_count(self) -> int:
        """Return number of users this user follows."""
        return self.following.count()
