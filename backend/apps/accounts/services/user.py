from dataclasses import dataclass
from django.db import transaction
from django.contrib.auth import get_user_model



User = get_user_model()


@dataclass
class ToggleFollowResult:
    """
    Result object for follow/unfollow actions.
    """
    status: str 

class UserService:
    """
    Service layer for user-related business logic.
    """

    @staticmethod
    @transaction.atomic
    def toggle_follow(*, actor: User, target: User) -> ToggleFollowResult:
        """
        Follow or unfollow another user.

        Args:
            actor: The user performing the action.
            target: The user to follow or unfollow.

        Returns:
            ToggleFollowResult: Status of the action.
        """
        if actor.id == target.id:
            raise ValueError("cannot_follow_self")

        if actor.is_following(target):
            deleted = actor.unfollow(target)
            return ToggleFollowResult("unfollowed" if deleted else "not_following")

        created = actor.follow(target)
        return ToggleFollowResult("followed" if created else "already_following")

    @staticmethod
    @transaction.atomic
    def update_display_and_profile(
        *, user: User, display_name: str | None, profile_data: dict
    ):
        """
        Update display name and profile fields for a user.
        """
        if display_name is not None:
            user.display_name = display_name
            user.save()



    @staticmethod
    @transaction.atomic
    def change_active(*, user: User, is_active: bool) -> None:
        
        """
        Universal method to soft-activate or soft-deactivate a user
        and all related BaseModel entities.
        """

        from apps.collection.models import Collection , Item ,ItemImage
        from apps.accounts.models import Profile,Follow
        from apps.posts.models import Post,Comment,PostReaction,CommentReaction

        
        user.is_active = is_active
        user.save(update_fields=["is_active"])

        Profile.all_objects.filter(user=user).update(is_active=is_active)

        Follow.all_objects.filter(follower=user).update(is_active=is_active)
        Follow.all_objects.filter(following=user).update(is_active=is_active)

        Collection.all_objects.filter(owner=user).update(is_active=is_active)
        Item.all_objects.filter(collection__owner=user).update(is_active=is_active)
        ItemImage.all_objects.filter(item__collection__owner=user).update(is_active=is_active)

     
        Post.all_objects.filter(author=user).update(is_active=is_active)
        Comment.all_objects.filter(author=user).update(is_active=is_active)
        PostReaction.all_objects.filter(user=user).update(is_active=is_active)
        CommentReaction.all_objects.filter(user=user).update(is_active=is_active)

    @staticmethod
    def deactivate_self(*, user: User) -> None:
        return UserService.change_active(user=user, is_active=False)

    @staticmethod
    def reactivate_self(*, user: User) -> None:
        return UserService.change_active(user=user, is_active=True)


