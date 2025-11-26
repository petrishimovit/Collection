from typing import Optional

from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet

from apps.collection.models import Collection, Item

User = get_user_model()


def get_public_items() -> QuerySet[Item]:
    """
    Return items visible to any user (feed/search for anonymous).

    Rules:
        - collection is public
        - item is public
    """
    return (
        Item.objects
        .filter(
            collection__privacy=Collection.PRIVACY_PUBLIC,
            privacy=Item.PRIVACY_PUBLIC,
        )
        .select_related("collection", "collection__owner")
        .prefetch_related("images")
    )


def get_items_for_user(user: Optional[User]) -> QuerySet[Item]:
    """
    Return items visible to the given user.
    """
    qs = (
        Item.objects
        .select_related("collection", "collection__owner")
        .prefetch_related("images")
    )

    if not user or not user.is_authenticated:
        return qs.filter(
            collection__privacy=Collection.PRIVACY_PUBLIC,
            privacy=Item.PRIVACY_PUBLIC,
        )



    own_items = Q(collection__owner=user)

    public_public_items = Q(
        collection__privacy=Collection.PRIVACY_PUBLIC,
        privacy=Item.PRIVACY_PUBLIC,
    )

  
    public_following_items = Q(
        collection__privacy=Collection.PRIVACY_PUBLIC,
        privacy=Item.PRIVACY_FOLLOWING,
        collection__owner__followers__follower=user,
    )


    following_collection_items = Q(
        collection__privacy=Collection.PRIVACY_FOLLOWING,
        collection__owner__followers__follower=user,
        privacy__in=[Item.PRIVACY_PUBLIC, Item.PRIVACY_FOLLOWING],
    )

    return qs.filter(
        own_items
        | public_public_items
        | public_following_items
        | following_collection_items
    )


def get_item_for_user(user: Optional[User], item_id: int) -> Optional[Item]:
    """
    Return a single item accessible to the given user.
    Returns None if access is not permitted.
    """
    qs = get_items_for_user(user)
    try:
        return qs.get(id=item_id)
    except Item.DoesNotExist:
        return None
