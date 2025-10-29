from dataclasses import dataclass
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()

@dataclass
class ToggleFollowResult:
    status: str  

class UserService:

    @staticmethod
    @transaction.atomic
    def toggle_follow(*, actor: User, target: User) -> ToggleFollowResult:
        if actor.id == target.id:
            raise ValueError("cannot_follow_self")
        
        if actor.is_following(target):
            deleted = actor.unfollow(target)
            return ToggleFollowResult("unfollowed" if deleted else "not_following")
        created = actor.follow(target)
        return ToggleFollowResult("followed" if created else "already_following")

    @staticmethod
    @transaction.atomic
    def update_display_and_profile(*, user: User, display_name: str | None, profile_data: dict):
        if display_name is not None:
            user.display_name = display_name
            user.save(update_fields=["display_name"])
  

    @staticmethod
    @transaction.atomic
    def deactivate_self(*, user: User):
        user.is_active = False
        user.save(update_fields=["is_active"])
