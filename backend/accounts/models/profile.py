from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from core.models import BaseModel

class Profile(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
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
