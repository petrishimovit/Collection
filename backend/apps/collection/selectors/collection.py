from typing import Optional

from django.contrib.auth import get_user_model
from django.db.models import Q, Count, QuerySet

from apps.collection.models import Collection

User = get_user_model()


def get_public_collections() -> QuerySet[Collection]:
    """
    Return public collections visible to any user.
    """
    return (
        Collection.objects
        .filter(privacy=Collection.PRIVACY_PUBLIC)
        .select_related("owner")
        .annotate(items_count=Count("items"))
    )


def get_collections_for_user(user: Optional[User]) -> QuerySet[Collection]:
    """
    Return collections visible to the given user.

    Anonymous:
        - only public collections

    Authenticated:
        - own collections
        - public collections of others
        - following-only collections of users they follow
    """
    qs = (
        Collection.objects
        .select_related("owner")
        .annotate(items_count=Count("items"))
    )

    if not user or not user.is_authenticated:
        return qs.filter(privacy=Collection.PRIVACY_PUBLIC)

    own = Q(owner=user)
    public = Q(privacy=Collection.PRIVACY_PUBLIC)
    following = Q(
        privacy=Collection.PRIVACY_FOLLOWING,
        owner__followers__follower=user,
    )

    return qs.filter(own | public | following)


def get_user_collections(user: User) -> QuerySet[Collection]:
    """
    Return all collections owned by this user.
    """
    return (
        Collection.objects
        .filter(owner=user)
        .select_related("owner")
        .annotate(items_count=Count("items"))
    )


def get_collection_for_user(user: Optional[User], collection_id: int) -> Optional[Collection]:
    """
    Return a single collection accessible to the user.
    Returns None if not permitted.
    """
    qs = get_collections_for_user(user)
    try:
        return qs.get(id=collection_id)
    except Collection.DoesNotExist:
        return None
