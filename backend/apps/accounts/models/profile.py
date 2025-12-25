from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.models import BaseModel
from core.utils.images import compress_webp, thumb_webp


class Profile(BaseModel):
    """
    User profile with personal information.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    avatar_sm = models.ImageField(upload_to="avatars/", blank=True, null=True, editable=False)
    avatar_md = models.ImageField(upload_to="avatars/", blank=True, null=True, editable=False)

    bio = models.TextField(blank=True, default="", max_length=400)
    website = models.URLField(blank=True, default="")
    social_links = models.JSONField(blank=True, default=dict)
    collection_focus = models.CharField(max_length=128, blank=True, default="")

    MAX_SOCIAL_LINKS = 5

    def clean(self):
        if self.social_links and len(self.social_links) > self.MAX_SOCIAL_LINKS:
            raise ValidationError({"social_links": f"Max {self.MAX_SOCIAL_LINKS} links"})

    class Meta:
        db_table = "accounts_profile"

    def __str__(self):
        return f"Profile of {self.user.username}"

    def save(self, *args, **kwargs):
        if self.avatar and (not self.pk or not self.avatar_sm or not self.avatar_md):
            original_name = self.avatar.name

            self.avatar = compress_webp(
                self.avatar,
                original_name=original_name,
                max_size=(512, 512),
                quality=82,
            )
            self.avatar_sm = thumb_webp(
                self.avatar, original_name=original_name, width=128, quality=78
            )
            self.avatar_md = thumb_webp(
                self.avatar, original_name=original_name, width=256, quality=80
            )

        super().save(*args, **kwargs)
