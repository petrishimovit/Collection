from django.contrib import admin

from core.admin import BaseAdmin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(BaseAdmin):
    """Notification admin configuration."""
