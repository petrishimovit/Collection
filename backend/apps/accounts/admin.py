from django.contrib import admin, messages
from django.utils.translation import ngettext

from apps.accounts.services.user import UserService
from core.admin import BaseAdmin

from .models.follow import Follow
from .models.profile import Profile
from .models.user import User


@admin.register(User)
class UserAdmin(BaseAdmin):
    list_display = ("id", "email", "is_active")
    list_filter = ("is_active",)

    @admin.action(description="Soft delete (ban) selected users")
    def soft_delete_users(self, request, queryset):
        """
        Soft-Delete Users from admin
        """
        changed = 0

        for user in queryset:
            if user.is_active:  # не трогаем уже неактивных
                UserService.deactivate_self(user=user)
                changed += 1

        if changed:
            self.message_user(
                request,
                ngettext(
                    "%d user was soft deleted.",
                    "%d users were soft deleted.",
                    changed,
                )
                % changed,
                level=messages.WARNING,
            )
        else:
            self.message_user(
                request,
                "No users were soft deleted (they are already inactive).",
                level=messages.INFO,
            )

    @admin.action(description="Unban (reactivate) selected users")
    def reactivate_users(self, request, queryset):
        """
        Reactivate Users from admin
        """
        changed = 0

        for user in queryset:
            if not user.is_active:
                UserService.reactivate_self(user=user)
                changed += 1

        if changed:
            self.message_user(
                request,
                ngettext(
                    "%d user was reactivated.",
                    "%d users were reactivated.",
                    changed,
                )
                % changed,
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "No users were reactivated (they are already active).",
                level=messages.INFO,
            )

    actions = ("soft_delete_users", "reactivate_users")


@admin.register(Follow)
class FollowAdmin(BaseAdmin):
    """
    Follow admin Register
    """

    pass


@admin.register(Profile)
class ProfileAdmin(BaseAdmin):
    """
    Profile admin Register
    """

    pass
