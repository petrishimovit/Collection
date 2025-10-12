# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User 

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("id", "email", "display_name", "is_staff", "is_active","created_at","updated_at")
    search_fields = ("email", "display_name")
    ordering = ("email",)
    fieldsets = None