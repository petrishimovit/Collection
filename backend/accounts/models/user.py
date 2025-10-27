from django.db import models
from django.contrib.auth.models import AbstractUser
from core.models import BaseModel
from ..managers import UserManager


class User(BaseModel, AbstractUser):  
    username = None
    email = models.EmailField("Email", unique=True)
    display_name = models.CharField("Display name", max_length=150)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    objects = UserManager()

    def __str__(self):
        return self.display_name or self.email