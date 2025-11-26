from typing import Optional

from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet

from apps.collection.models import Collection, Item

User = get_user_model()


def get_public_items() -> QuerySet[Item]:
    """
    Items visible to any user.

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
    Items visible to the given user.

    Anonymous:
        - items from PUBLIC collections
        - item privacy: PUBLIC

    Authenticated:
        - own items (any collection privacy, any item privacy)
        - items from PUBLIC collections of others:
            - item.PRIVACY_PUBLIC                       -> visible to all
            - item.PRIVACY_FOLLOWING_ONLY              -> visible if owner follows user
        - items from FOLLOWING_ONLY collections of others:
            - visible if owner follows user
            - items: PUBLIC or FOLLOWING_ONLY
        - items from PRIVATE collections of others:
            - not visible
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

  
    owner_follows_user = Q(collection__owner__following_relations__following=user)

    public_public = Q(
        collection__privacy=Collection.PRIVACY_PUBLIC,
        privacy=Item.PRIVACY_PUBLIC,
    )

    public_following_only_for_followed = Q(
        collection__privacy=Collection.PRIVACY_PUBLIC,
        privacy=Item.PRIVACY_FOLLOWING,
    ) & owner_follows_user

   
    following_collection_for_followed = Q(
        collection__privacy=Collection.PRIVACY_FOLLOWING,
    ) & owner_follows_user & Q(
        privacy__in=[Item.PRIVACY_PUBLIC, Item.PRIVACY_FOLLOWING],
    )

    return qs.filter(
        own_items
        | public_public
        | public_following_only_for_followed
        | following_collection_for_followed
    ).distinct()


def get_item_for_user(user: Optional[User], item_id: int) -> Optional[Item]:
    """
    Single item visible to the given user.
    """
    qs = get_items_for_user(user)
    try:
        return qs.get(id=item_id)
    except Item.DoesNotExist:
        return None


def get_collection_items_for_user(
    user: Optional[User],
    collection_id: int,
) -> QuerySet[Item]:
    """
    All items of a specific collection visible to the given user.
    """
    return get_items_for_user(user).filter(collection_id=collection_id)
