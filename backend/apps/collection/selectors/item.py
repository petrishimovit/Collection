from typing import Optional

from django.db import models
from django.db.models import Q

from apps.accounts.models import Follow
from apps.collection.models import Collection, Item


def _base_items_qs():
    """
    Base queryset for items with useful selects/prefetches.
    """
    return Item.objects.select_related("collection", "collection__owner").prefetch_related("images")


def get_items_for_user(user) -> models.QuerySet[Item]:
    """
    Return items visible to the given user across all collections.

    Rules:

    - Anonymous:
        * Only items with:
            - collection.privacy = PUBLIC
            - item.privacy = PUBLIC

    - Authenticated user:
        * Always sees items in their own collections.
        * For other users' PUBLIC collections:
            - item.privacy = PUBLIC  -> visible
            - item.privacy = FOLLOWING_ONLY -> visible if collection.owner follows user (owner -> user)
            - item.privacy = PRIVATE -> not visible
        * For other users' FOLLOWING_ONLY collections:
            - collection visible only if owner follows user (owner -> user)
            - within such collection:
                - item.privacy in {PUBLIC, FOLLOWING_ONLY} -> visible
                - item.privacy = PRIVATE -> not visible
        * PRIVATE collections of other users -> never visible.
    """
    qs = _base_items_qs()

    if not user or not getattr(user, "is_authenticated", False):
        return qs.filter(
            collection__privacy=Collection.PRIVACY_PUBLIC,
            privacy=Item.PRIVACY_PUBLIC,
        )

    owner_follows_user_q = Q(collection__owner__following_relations__following=user)

    own_items_q = Q(collection__owner=user)

    public_collections_q = Q(collection__privacy=Collection.PRIVACY_PUBLIC) & (
        Q(privacy=Item.PRIVACY_PUBLIC) | (Q(privacy=Item.PRIVACY_FOLLOWING) & owner_follows_user_q)
    )

    following_collections_q = (
        Q(collection__privacy=Collection.PRIVACY_FOLLOWING)
        & owner_follows_user_q
        & (Q(privacy=Item.PRIVACY_PUBLIC) | Q(privacy=Item.PRIVACY_FOLLOWING))
    )

    visible_q = own_items_q | public_collections_q | following_collections_q

    return qs.filter(visible_q).distinct()


def get_item_for_user(user, item_id: Optional[str]) -> Optional[Item]:
    """
    Return a single item by ID if it is visible to the user, otherwise None.
    """
    if not item_id:
        return None

    return get_items_for_user(user).filter(id=item_id).first()


def get_collection_items_for_user(user, collection_id: Optional[str]) -> models.QuerySet[Item]:
    """
    Return items from a specific collection that are visible to the given user.

    This simply scopes `get_items_for_user(user)` by `collection_id`.
    If the collection itself is not visible to the user, the result will be empty.
    """
    if not collection_id:
        return Item.objects.none()

    return get_items_for_user(user).filter(collection_id=collection_id)


def get_user_items_for_viewer(viewer, owner_id: str) -> models.QuerySet[Item]:
    """
    Return items belonging to collections of the given user
    that are visible to the viewer.

    - viewer: user who is requesting the data (may be anonymous)
    - owner_id: target user ID whose items we want to list
    """
    return get_items_for_user(viewer).filter(collection__owner_id=owner_id)
