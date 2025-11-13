from django.contrib import admin
from .models.user import User
from .models.follow import Follow
from .models.profile import Profile


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    User admin Register
    """
    pass

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """
    Follow admin Register
    """
    pass

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Profile admin Register
    """
    pass