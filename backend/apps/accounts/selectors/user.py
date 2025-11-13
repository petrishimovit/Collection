from django.db.models import Prefetch
from django.contrib.auth import get_user_model

User = get_user_model()


def user_list_qs():
    """
    Return a base queryset of active users with related profiles.
    """
    return (
        User.objects.filter(is_active=True)
        .select_related("profile")
        .prefetch_related()
    )


def user_by_pk(pk: int) -> User:
    """
    Return a single active user by primary key.
    """
    return user_list_qs().get(pk=pk)


def following_qs(user: User):
    """
    Return queryset of users that the given user follows.
    """
    return user.following.select_related("profile")


def followers_qs(user: User):
    """
    Return queryset of users who follow the given user.
    """
    return User.objects.filter(is_active=True, following__id=user.id)
