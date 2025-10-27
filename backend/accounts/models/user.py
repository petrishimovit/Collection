from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from core.models import BaseModel
from ..managers import UserManager


class User(BaseModel, AbstractUser):
    username = None
    email = models.EmailField("Email", unique=True)
    display_name = models.CharField("Display name", max_length=150)

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

    def __str__(self):
        return self.display_name or self.email

    
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
        """Check if this user follows another user."""
        from .follow import Follow
        return Follow.objects.filter(follower=self, following=other).exists()

    @property
    def followers_count(self) -> int:
        return self.followers.count()

    @property
    def following_count(self) -> int:
        return self.following.count()